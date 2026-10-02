"""
SmartCampus AI — Complaint REST API & AI Triage Test Suite

Tests for:
  - AI Triage Analysis (classification, urgency, confidence, ETA, duplicates)
  - Complaint Creation API (DB insertion, initial timeline, AI fields)
  - Filtering & Querying Complaints (status, priority, department, student_id)
  - Complaint Status Updates & Timeline History
  - Officer Reassignment
  - Integration with Email Notification System
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# MUST import models before Base metadata initialization
import app.models.email_log
import app.models.complaint

from app.db.database import Base, get_db
from app.models.complaint import ComplaintModel, ComplaintStatus, ComplaintPriority
from app.main import app
from app.services.ai_triage_service import AITriageService


from sqlalchemy.pool import StaticPool

# In-memory SQLite for isolated tests (using StaticPool to share connection across threads)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


class TestAITriageService:
    def test_electrical_triage(self):
        result = AITriageService.analyze(
            title="No power in Block C Room 304",
            description="There is a burning smell from the switchboard and sparking sounds."
        )
        assert result["category"] == "Electrical"
        assert result["department"] == "Electrical Maintenance"
        assert result["urgency"] == ComplaintPriority.CRITICAL
        assert result["confidence"] >= 90
        assert "burning" in result["keywords"] or "power" in result["keywords"]

    def test_plumbing_triage(self):
        result = AITriageService.analyze(
            title="Water leakage in washroom",
            description="Continuous water overflow onto the corridor floor."
        )
        assert result["category"] == "Plumbing"
        assert result["department"] == "Plumbing & Water"
        assert result["urgency"] in [ComplaintPriority.HIGH, ComplaintPriority.CRITICAL]

    def test_duplicate_detection(self):
        existing = [
            {"id": "CMP-2026-0001", "title": "No power in Block C Room 304", "description": "Switchboard sparking and burning smell"}
        ]
        result = AITriageService.analyze(
            title="No power in Block C 304",
            description="Switchboard sparking and burning smell",
            existing_complaints=existing
        )
        assert len(result["duplicates"]) > 0
        assert result["duplicates"][0]["id"] == "CMP-2026-0001"


class TestComplaintAPI:
    def test_instant_triage_endpoint(self):
        payload = {
            "title": "WiFi dead in library 2nd floor",
            "description": "None of us can access the assignment submission portal due today.",
            "location": "Central Library Floor 2"
        }
        res = client.post("/api/v1/complaints/triage", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["category"] == "Network & WiFi"
        assert data["department"] == "IT & Network Services"
        assert data["urgency"] == "High"

    def test_create_complaint_endpoint(self):
        payload = {
            "title": "No power in Block C Room 304",
            "description": "Lights and fans stopped working last night and there is a burning smell from the switchboard.",
            "building": "Block C",
            "room": "Room 304",
            "student_name": "Aarav Sharma",
            "student_id": "STU-2023-1847",
            "student_email": "aarav.sharma@northbridge.edu"
        }
        res = client.post("/api/v1/complaints", json=payload)
        assert res.status_code == 201
        data = res.json()
        assert data["id"].startswith("CMP-")
        assert data["category"] == "Electrical"
        assert data["department"] == "Electrical Maintenance"
        assert data["priority"] == "Critical"
        assert data["assignee_name"] == "Rahul Verma"
        assert len(data["timeline"]) == 1
        assert data["timeline"][0]["title"] == "Submitted"

    def test_list_and_filter_complaints(self):
        c1 = {
            "title": "No power in Block C",
            "description": "Power outage in electrical line.",
            "building": "Block C",
            "student_name": "Aarav Sharma",
            "student_id": "STU-2023-1847",
            "student_email": "aarav.sharma@northbridge.edu"
        }
        c2 = {
            "title": "WiFi down in Hostel B",
            "description": "Router dead since morning.",
            "building": "Hostel B",
            "student_name": "Priya Patel",
            "student_id": "STU-2024-0999",
            "student_email": "priya.patel@northbridge.edu"
        }
        client.post("/api/v1/complaints", json=c1)
        client.post("/api/v1/complaints", json=c2)

        res = client.get("/api/v1/complaints?student_id=STU-2023-1847")
        assert res.status_code == 200
        items = res.json()
        assert len(items) == 1
        assert items[0]["student_name"] == "Aarav Sharma"

    def test_update_status_and_timeline(self):
        c1 = {
            "title": "No power in Block C",
            "description": "Power outage in electrical line.",
            "building": "Block C",
            "student_name": "Aarav Sharma",
            "student_id": "STU-2023-1847",
            "student_email": "aarav.sharma@northbridge.edu"
        }
        res = client.post("/api/v1/complaints", json=c1)
        cid = res.json()["id"]

        update_payload = {
            "status": "In Progress",
            "note": "Technician dispatched to replace switchboard.",
            "updated_by_name": "Rahul Verma",
            "updated_by_role": "staff"
        }
        res_patch = client.patch(f"/api/v1/complaints/{cid}/status", json=update_payload)
        assert res_patch.status_code == 200
        updated_data = res_patch.json()
        assert updated_data["status"] == "In Progress"
        assert len(updated_data["timeline"]) == 2
        assert updated_data["timeline"][1]["title"] == "In Progress"

    def test_reassign_officer(self):
        c1 = {
            "title": "No power in Block C",
            "description": "Power outage in electrical line.",
            "building": "Block C",
            "student_name": "Aarav Sharma",
            "student_id": "STU-2023-1847",
            "student_email": "aarav.sharma@northbridge.edu"
        }
        res = client.post("/api/v1/complaints", json=c1)
        cid = res.json()["id"]

        reassign_payload = {
            "assignee_name": "Deepak Yadav",
            "assignee_email": "deepak.yadav@northbridge.edu",
            "reassigned_by_name": "Dr. Meera Nair"
        }
        res_reassign = client.post(f"/api/v1/complaints/{cid}/reassign", json=reassign_payload)
        assert res_reassign.status_code == 200
        data = res_reassign.json()
        assert data["assignee_name"] == "Deepak Yadav"
        assert data["assignee_email"] == "deepak.yadav@northbridge.edu"
