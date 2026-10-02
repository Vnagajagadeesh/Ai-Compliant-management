"""
SmartCampus AI — Complaint Pydantic Schemas

Schemas for API request/response validation:
  - ComplaintCreate: Student submission payload
  - ComplaintUpdateStatus: Staff status change payload
  - ComplaintReassign: Reassignment payload
  - ComplaintResponse: Full complaint detail payload
  - AITriageRequest: Instant triage input
  - AITriageResponse: AI analysis output
  - TimelineEventResponse: Timeline event detail
"""

from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.models.complaint import ComplaintStatus, ComplaintPriority


# ── AI Triage Schemas ────────────────────────────────────────────────────────

class AITriageRequest(BaseModel):
    title: str = Field(..., min_length=5, max_length=255, json_schema_extra={"example": "No power in Block C Room 304"})
    description: str = Field(..., min_length=10, json_schema_extra={"example": "Lights and fans stopped working last night and there is a burning smell from the switchboard."})
    location: Optional[str] = Field(default="", json_schema_extra={"example": "Block C — Room 304"})


class DuplicateReportInfo(BaseModel):
    id: str
    title: str
    similarity_score: float


class AITriageResponse(BaseModel):
    category: str
    department: str
    urgency: ComplaintPriority
    confidence: int
    duplicates: List[DuplicateReportInfo] = []
    summary: str
    keywords: List[str] = []
    sentiment: str
    eta: str
    suggested_action: str
    reason: str
    assigned_officer: str


# ── Complaint CRUD Schemas ───────────────────────────────────────────────────

class TimelineEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    actor_name: str
    actor_role: str
    created_at: datetime


class ComplaintCreate(BaseModel):
    title: str = Field(..., min_length=5, max_length=255)
    description: str = Field(..., min_length=10)
    building: str = Field(..., min_length=2, json_schema_extra={"example": "Block C"})
    room: Optional[str] = Field(default=None, json_schema_extra={"example": "Room 304"})
    
    student_name: str = Field(..., json_schema_extra={"example": "Aarav Sharma"})
    student_id: str = Field(..., json_schema_extra={"example": "STU-2023-1847"})
    student_email: EmailStr = Field(..., json_schema_extra={"example": "aarav.sharma@northbridge.edu"})


class ComplaintUpdateStatus(BaseModel):
    status: ComplaintStatus
    note: Optional[str] = Field(default=None, description="Optional note for timeline")
    updated_by_name: str = Field(default="Department Officer")
    updated_by_role: str = Field(default="staff")


class ComplaintReassign(BaseModel):
    assignee_name: str = Field(..., json_schema_extra={"example": "Rahul Verma"})
    assignee_email: Optional[EmailStr] = Field(default=None)
    reassigned_by_name: str = Field(default="Admin")


class ComplaintResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: str
    category: str
    department: str
    building: str
    room: Optional[str] = None
    
    status: ComplaintStatus
    priority: ComplaintPriority
    
    student_name: str
    student_id: str
    student_email: EmailStr
    
    assignee_name: str
    assignee_email: Optional[str] = None
    upvotes: int = 1
    
    ai_summary: Optional[str] = None
    ai_confidence: int = 90
    sentiment: str = "Neutral"
    predicted_eta: str = "~2 days"
    ai_action: Optional[str] = None
    
    created_at: datetime
    updated_at: datetime
    
    timeline: List[TimelineEventResponse] = []
