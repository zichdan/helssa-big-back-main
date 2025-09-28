# Helssa Apps List

## Backend Apps

- `auth_otp` — accounts, OTP authentication with Kavenegar, token management
- `rbac` — Roles and permissions, least-privilege model
- `patient` — Patient profile, medical records, prescriptions, consent forms
- `doctor` — Doctor profile, schedules, shifts, dashboard, auto-generate-pdf-prescription-auto-generate-pdf-certificate
- `visit-extensions` — patient options for save repeat prescription, drug reminders
- `encounters` — Visit/session management, session state machine
- `soap` — Versioned SOAP notes with HMAC signatures
- `triage` — Symptom triage, initial differential diagnosis
- `chatbot` — Patient–doctor, separate chatbot app for patient and doctor
- `stt` — Speech-to-text (Whisper), quality control
- `ai_helsabrain` — Agent orchestrator, prompts/guardrails
- `ai_guardrails` — Policy enforcement, safety SOPs, red-flag detection
- `search` — Full-text and compatible with MySQL
- `files` — Uploads, MinIO/S3, documents/attachments
- `exports` — Generating MD/PDF outputs, secure sharing
- `notifications` — SMS/Push/Email, templates and queues
- `payments` — Wallet/BoxMoney, subscriptions and billing
- `billing` — Invoices, transactions, financial reports
- `analytics` — Metrics, performance and quality reporting
- `audit` — Structured logs, audit trail, signatures
- `privacy` — PII/PHI redaction, data policies
- `integrations` — External integrations (TalkBot/LLM, Kavenegar, others)
- `fhir_adapter` — FHIR mapping, standard input/output
- `feedback` — Session rating and survey forms
- `checklist` — Dynamic checklists during visits, real-time alerts
- `scheduler` — Jobs, Celery/Redis, task scheduling
- `webhooks` — Event ingestion and dispatch, signatures
- `admin_portal` — Internal support and operator tools
- `api_gateway` — Unified API, versioning, rate-limiting
- `compliance` — SOPs/policies, documentation and compliance
- `devops` — Environment/secrets configuration, CI/CD
