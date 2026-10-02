"""
SmartCampus AI — Complaint API Routes

REST endpoints for:
  - POST /api/v1/complaints/triage : Instant AI analysis (category, urgency, ETA, duplicates)
  - POST /api/v1/complaints        : Create complaint + initial AI triage + email alert
  - GET  /api/v1/complaints        : Query list with filtering (status, priority, department, student)
  - GET  /api/v1/complaints/{id}   : Get detailed complaint + full timeline
  - PATCH /api/v1/complaints/{id}/status: Update status + add timeline event + trigger email
  - POST /api/v1/complaints/{id}/reassign: Reassign complaint officer + update timeline + trigger email
"""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.complaint import (
    ComplaintModel,
    ComplaintStatus,
    ComplaintPriority,
    ComplaintTimelineModel,
)
from app.schemas.complaint import (
    AITriageRequest,
    AITriageResponse,
    ComplaintCreate,
    ComplaintUpdateStatus,
    ComplaintReassign,
    ComplaintResponse,
)
from app.services.ai_triage_service import AITriageService
from app.services.email_service import EmailService

router = APIRouter(prefix="/api/v1/complaints", tags=["Complaints"])


def _generate_complaint_id(db: Session) -> str:
    year = datetime.now(timezone.utc).year
    count = db.query(ComplaintModel).count() + 1
    return f"CMP-{year}-{count:04d}"


@router.post("/triage", response_model=AITriageResponse, summary="Analyze complaint text with AI")
def triage_complaint(req: AITriageRequest, db: Session = Depends(get_db)):
    """Runs instant NLP triage analysis without saving to the database."""
    recent_records = db.query(ComplaintModel).order_by(ComplaintModel.created_at.desc()).limit(50).all()
    existing_list = [{"id": c.id, "title": c.title, "description": c.description} for c in recent_records]
    
    analysis = AITriageService.analyze(req.title, req.description, req.location or "", existing_list)
    return analysis


@router.post("", response_model=ComplaintResponse, status_code=status.HTTP_201_CREATED, summary="Submit a new complaint")
def create_complaint(
    req: ComplaintCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Submits a complaint, applies AI triage, saves to DB, and sends confirmation email."""
    # Fetch recent complaints for duplicate checking
    recent_records = db.query(ComplaintModel).order_by(ComplaintModel.created_at.desc()).limit(50).all()
    existing_list = [{"id": c.id, "title": c.title, "description": c.description} for c in recent_records]
    
    # Perform AI Triage
    location_str = f"{req.building} {req.room or ''}".strip()
    ai_result = AITriageService.analyze(req.title, req.description, location_str, existing_list)
    
    complaint_id = _generate_complaint_id(db)
    now = datetime.now(timezone.utc)
    
    new_complaint = ComplaintModel(
        id=complaint_id,
        title=req.title,
        description=req.description,
        category=ai_result["category"],
        department=ai_result["department"],
        building=req.building,
        room=req.room,
        status=ComplaintStatus.SUBMITTED,
        priority=ai_result["urgency"],
        student_name=req.student_name,
        student_id=req.student_id,
        student_email=req.student_email,
        assignee_name=ai_result["assigned_officer"],
        ai_summary=ai_result["summary"],
        ai_confidence=ai_result["confidence"],
        sentiment=ai_result["sentiment"],
        predicted_eta=ai_result["eta"],
        ai_action=ai_result["suggested_action"],
        created_at=now,
        updated_at=now
    )
    
    db.add(new_complaint)
    db.flush()
    
    # Create initial timeline entry
    initial_timeline = ComplaintTimelineModel(
        complaint_id=complaint_id,
        title="Submitted",
        description=f"AI triaged as {ai_result['urgency'].value} • {ai_result['category']} • routed to {ai_result['department']}",
        actor_name="System AI Engine",
        actor_role="system",
        created_at=now
    )
    db.add(initial_timeline)
    db.commit()
    db.refresh(new_complaint)

    # Trigger background email notification
    email_service = EmailService(db)
    background_tasks.add_task(
        email_service.send_complaint_submitted_email,
        to_email=new_complaint.student_email,
        student_name=new_complaint.student_name,
        complaint_id=complaint_id,
        category=new_complaint.category,
        summary=new_complaint.ai_summary or new_complaint.title,
        status=new_complaint.status.value,
        priority=new_complaint.priority.value,
        submitted_at=now.strftime("%Y-%m-%d %H:%M")
    )

    return new_complaint


@router.get("", response_model=List[ComplaintResponse], summary="List complaints with filters")
def list_complaints(
    status_filter: Optional[ComplaintStatus] = Query(None, alias="status"),
    priority_filter: Optional[ComplaintPriority] = Query(None, alias="priority"),
    department: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    student_id: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    """Retrieves a list of complaints filtered by optional parameters."""
    query = db.query(ComplaintModel)
    
    if status_filter:
        query = query.filter(ComplaintModel.status == status_filter)
    if priority_filter:
        query = query.filter(ComplaintModel.priority == priority_filter)
    if department:
        query = query.filter(ComplaintModel.department.ilike(f"%{department}%"))
    if category:
        query = query.filter(ComplaintModel.category.ilike(f"%{category}%"))
    if student_id:
        query = query.filter(ComplaintModel.student_id == student_id)
        
    return query.order_by(ComplaintModel.created_at.desc()).all()


@router.get("/{complaint_id}", response_model=ComplaintResponse, summary="Get complaint by ID")
def get_complaint(complaint_id: str, db: Session = Depends(get_db)):
    """Retrieves detailed complaint object by ID."""
    c = db.query(ComplaintModel).filter(ComplaintModel.id == complaint_id).first()
    if not c:
        raise HTTPException(status_code=404, detail=f"Complaint {complaint_id} not found.")
    return c


@router.patch("/{complaint_id}/status", response_model=ComplaintResponse, summary="Update complaint status")
def update_complaint_status(
    complaint_id: str,
    req: ComplaintUpdateStatus,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Updates complaint status, logs timeline event, and notifies the student via email."""
    c = db.query(ComplaintModel).filter(ComplaintModel.id == complaint_id).first()
    if not c:
        raise HTTPException(status_code=404, detail=f"Complaint {complaint_id} not found.")

    old_status = c.status.value
    new_status = req.status
    now = datetime.now(timezone.utc)
    
    c.status = new_status
    c.updated_at = now

    note_text = f"Status changed from '{old_status}' to '{new_status.value}' by {req.updated_by_name}."
    if req.note:
        note_text += f" Note: {req.note}"

    timeline_event = ComplaintTimelineModel(
        complaint_id=complaint_id,
        title=new_status.value,
        description=note_text,
        actor_name=req.updated_by_name,
        actor_role=req.updated_by_role,
        created_at=now
    )
    db.add(timeline_event)
    db.commit()
    db.refresh(c)

    # Trigger background email notification
    email_service = EmailService(db)
    background_tasks.add_task(
        email_service.send_status_update_email,
        to_email=c.student_email,
        student_name=c.student_name,
        complaint_id=c.id,
        title=c.title,
        old_status=old_status,
        new_status=new_status.value,
        update_note=req.note or ""
    )

    return c


@router.post("/{complaint_id}/reassign", response_model=ComplaintResponse, summary="Reassign officer")
def reassign_complaint(
    complaint_id: str,
    req: ComplaintReassign,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Reassigns the assigned officer for a complaint."""
    c = db.query(ComplaintModel).filter(ComplaintModel.id == complaint_id).first()
    if not c:
        raise HTTPException(status_code=404, detail=f"Complaint {complaint_id} not found.")

    old_assignee = c.assignee_name
    now = datetime.now(timezone.utc)
    
    c.assignee_name = req.assignee_name
    if req.assignee_email:
        c.assignee_email = str(req.assignee_email)
    
    if c.status == ComplaintStatus.SUBMITTED:
        c.status = ComplaintStatus.ASSIGNED

    c.updated_at = now

    timeline_event = ComplaintTimelineModel(
        complaint_id=complaint_id,
        title="Assigned",
        description=f"Reassigned from '{old_assignee}' to '{req.assignee_name}' by {req.reassigned_by_name}.",
        actor_name=req.reassigned_by_name,
        actor_role="admin",
        created_at=now
    )
    db.add(timeline_event)
    db.commit()
    db.refresh(c)

    # If assignee email provided, trigger staff notification email
    if req.assignee_email:
        email_service = EmailService(db)
        background_tasks.add_task(
            email_service.send_complaint_assigned_email,
            to_email=str(req.assignee_email),
            recipient_name=req.assignee_name,
            complaint_id=c.id,
            title=c.title,
            category=c.category,
            priority=c.priority.value,
            assigned_to=req.assignee_name,
            department=c.department,
            is_staff=True
        )

    return c
