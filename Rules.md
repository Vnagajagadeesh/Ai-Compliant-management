# SmartCampus AI — Project Rules

## 1. Product Rules
- The product is an AI-assisted campus complaint management system.
- It must support Student, Staff, and Administrator roles.
- Every complaint must have a traceable lifecycle.
- Complaint status changes must be auditable.
- Critical issues must be visually distinguishable and eligible for escalation.

## 2. AI Rules
- AI provides recommendations, not unquestionable decisions.
- Users with permission can override AI classification or routing.
- Display AI confidence where applicable.
- Do not present fictional AI accuracy as a verified real-world metric.
- AI-generated responses must be reviewed before sensitive communication.
- Duplicate detection is advisory.
- Never fabricate complaint evidence, student information, or institutional facts.

## 3. Data Rules
- Use fictional demo data in prototypes.
- Never hard-code passwords, API keys, tokens, or secrets.
- Validate all user input.
- Store timestamps consistently.
- Keep audit records for important administrative actions.
- Uploaded files must be validated and access-controlled.

## 4. Access Rules
### Student
Can create and view their own complaints and related conversations/feedback.

### Staff
Can access complaints assigned to their department or explicitly assigned to them.

### Administrator
Can manage campus-wide complaints, users, departments, analytics, and settings.

## 5. UI Rules
- Maintain one consistent design system.
- Use clear hierarchy and readable typography.
- Do not overcrowd dashboards.
- Use status and priority badges consistently.
- Keep destructive actions behind confirmation.
- Provide loading, empty, success, and error states.
- Design mobile-first responsive behavior.

## 6. Development Rules
- Prefer reusable components.
- Keep business logic out of UI components where practical.
- Use typed interfaces/models.
- Keep API contracts documented.
- Use meaningful names.
- Avoid duplicated logic.
- Keep environment-specific configuration outside source code.

## 7. Accessibility Rules
- Keyboard navigation should work.
- Form fields need labels.
- Buttons must have understandable names.
- Maintain sufficient contrast.
- Do not rely only on color to communicate status.
- Provide accessible error messages.

## 8. Demo Rules
- Clearly distinguish prototype/demo analytics from real institutional data.
- Use realistic but fictional names and complaint IDs.
- Simulate AI behavior only when a real AI service is not connected.
- Never claim the prototype is production-ready without security and deployment validation.
