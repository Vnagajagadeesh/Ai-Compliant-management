"""
SmartCampus AI — Complaint Database Models

Models for:
  - Department: Campus departments (Electrical, Plumbing, IT, etc.)
  - Complaint: Core complaint record with AI analysis fields
  - ComplaintTimeline: Step-by-step history of status changes and notes
  - ComplaintAttachment: Image/file attachments for evidence
"""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional, List

from sqlalchemy import (
    Column, String, Integer, DateTime, Text, Float, Boolean, ForeignKey, Enum as SQLEnum
)
from sqlalchemy.orm import relationship

from app.db.database import Base


class ComplaintStatus(str, PyEnum):
    SUBMITTED = "Submitted"
    UNDER_REVIEW = "Under Review"
    ASSIGNED = "Assigned"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    ESCALATED = "Escalated"
    CLOSED = "Closed"


class ComplaintPriority(str, PyEnum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class DepartmentModel(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    short_code = Column(String(20), nullable=False)
    open_tickets = Column(Integer, default=0)
    sla_percentage = Column(Float, default=95.0)
    color = Column(String(20), default="#3B82F6")
    icon = Column(String(10), default="📋")
    default_assignee = Column(String(100), nullable=True)

    complaints = relationship("ComplaintModel", back_populates="department_rel")


class ComplaintModel(Base):
    __tablename__ = "complaints"

    id = Column(String(50), primary_key=True, index=True)  # e.g., CMP-2026-0142
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(100), nullable=False, index=True)
    department = Column(String(100), nullable=False, index=True)
    building = Column(String(150), nullable=False)
    room = Column(String(50), nullable=True)
    
    status = Column(SQLEnum(ComplaintStatus), default=ComplaintStatus.SUBMITTED, nullable=False, index=True)
    priority = Column(SQLEnum(ComplaintPriority), default=ComplaintPriority.MEDIUM, nullable=False, index=True)
    
    student_name = Column(String(100), nullable=False)
    student_id = Column(String(50), nullable=False)
    student_email = Column(String(255), nullable=False)
    
    assignee_name = Column(String(100), default="Unassigned")
    assignee_email = Column(String(255), nullable=True)
    
    upvotes = Column(Integer, default=1)
    
    # AI Analysis Fields
    ai_summary = Column(Text, nullable=True)
    ai_confidence = Column(Integer, default=90)
    sentiment = Column(String(50), default="Neutral")
    predicted_eta = Column(String(50), default="~2 days")
    ai_action = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    department_rel = relationship("DepartmentModel", back_populates="complaints")
    timeline = relationship("ComplaintTimelineModel", back_populates="complaint", cascade="all, delete-orphan", order_by="ComplaintTimelineModel.created_at")


class ComplaintTimelineModel(Base):
    __tablename__ = "complaint_timelines"

    id = Column(Integer, primary_key=True, index=True)
    complaint_id = Column(String(50), ForeignKey("complaints.id"), nullable=False, index=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=False)
    actor_name = Column(String(100), default="System AI")
    actor_role = Column(String(50), default="system")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    complaint = relationship("ComplaintModel", back_populates="timeline")
