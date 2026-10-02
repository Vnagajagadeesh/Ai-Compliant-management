# SmartCampus AI — System Architecture

## 1. Architecture Goal
Build a modular, scalable web application with clear separation between frontend, backend, AI services, database, authentication, and notifications.

## 2. Recommended Stack
### Frontend
- React
- TypeScript
- Tailwind CSS
- Component library such as shadcn/ui
- Recharts or equivalent for analytics
- React Router

### Backend
- Python
- FastAPI
- Pydantic
- SQLAlchemy

### Database
- PostgreSQL for production
- SQLite for local prototype development

### AI Layer
- LLM API for classification, summarization, response suggestions, and semantic analysis.
- Embedding/vector search can be added for duplicate detection.

### Infrastructure
- REST API
- Object storage for uploaded evidence
- Background jobs for asynchronous AI/notifications
- Environment variables for secrets

## 3. High-Level Flow
Student UI
→ Frontend API client
→ FastAPI backend
→ Authentication / authorization
→ Complaint service
→ AI service
→ Database
→ Notification service

Staff and Admin dashboards use the same backend with role-based permissions.

## 4. Major Backend Modules
- auth
- users
- departments
- complaints
- ai
- notifications
- messages
- feedback
- analytics
- reports
- audit

## 5. Core Entities
### User
id, name, email, role, department_id, status, created_at

### Department
id, name, description, contact, status

### Complaint
id, student_id, title, description, category, urgency, status, location, department_id, assigned_staff_id, ai_confidence, created_at, updated_at, resolved_at

### Attachment
id, complaint_id, file_url, file_type, created_at

### AIAnalysis
id, complaint_id, category, urgency, suggested_department, confidence, summary, sentiment, duplicate_candidates, created_at

### ComplaintMessage
id, complaint_id, sender_id, message, created_at

### Notification
id, user_id, type, title, message, read_at, created_at

### Feedback
id, complaint_id, student_id, rating, comment, created_at

### AuditLog
id, actor_id, action, entity_type, entity_id, metadata, created_at

## 6. API Examples
POST /api/auth/login
GET /api/complaints
POST /api/complaints
GET /api/complaints/{id}
PATCH /api/complaints/{id}
POST /api/complaints/{id}/analyze
POST /api/complaints/{id}/messages
POST /api/complaints/{id}/feedback
GET /api/admin/analytics
GET /api/departments
POST /api/departments

## 7. AI Service Contract
Input:
- Complaint title
- Complaint description
- Location
- Optional attachment metadata

Output:
- category
- urgency
- suggested_department
- confidence
- summary
- sentiment
- possible_duplicate_ids
- suggested_response

AI output must be validated by the backend before persistence.

## 8. Security
- Role-based access control.
- Password hashing.
- Secure session/JWT strategy.
- Input validation.
- File type/size validation.
- Rate limiting for sensitive endpoints.
- Audit logs for administrative actions.
- Never expose API keys to the frontend.
- Restrict users to complaints they are authorized to access.

## 9. Scalability
Start as a modular monolith. Separate AI processing and notification workers when load increases. Add Redis/background queues and object storage when required.

## 10. Deployment
Frontend and backend should be independently deployable. PostgreSQL should be managed separately. Secrets must be supplied through environment configuration.

## 11. Error Handling
Use consistent API errors:
{ code, message, details, request_id }

The UI should provide understandable recovery actions without exposing internal errors.
