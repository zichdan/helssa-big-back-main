# Helssa — Intelligent Telemedicine Platform

![Helssa logo](images/logo.png)

*End-to-end, agent-assisted, FHIR-ready telemedicine suite for clinicians and patients.*
![Math & Med](images/mm.png)

---

## Table of Contents

- [What is Helssa?](#what-is-helssa)
- [Architecture Overview](#architecture-overview)
- [Core Modules](#core-modules)
- [Clinical Data Model & Standards](#clinical-data-model--standards)
- [Security & Compliance](#security--compliance)
- [Agent Governance](#agent-governance)
- [Local Development](#local-development)
- [Configuration (.env)](#configuration-env)
- [Run & Services](#run--services)
- [Testing & QA](#testing--qa)
- [Logging & Observability](#logging--observability)
- [CI/CD](#cicd)
- [Contributing](#contributing)
- [License](#license)

---

## What is Helssa?

Helssa is a comprehensive telemedicine platform designed for **safe, structured, and efficient** online medical visits. It combines intelligent agents, strict SOP-driven workflows, and FHIR-based data standards to create a scalable, secure, and clinician-friendly digital clinic.

Key features:

- Agent-assisted patient intake and SOAP note generation
- Versioned clinical records with auditability
- AI guardrails for safety and compliance
- Flutter-based patient and doctor frontends
- Django + DRF backend with modular micro‑apps

---

## Architecture Overview

**Backend (Django + DRF):** Encounters, SOAP notes, triage, AI orchestration, search, storage, notifications, payments, audit, and privacy.

**Frontends:**

- `helssa_patient_app` (Flutter Web/Mobile)
- `helssa_doctor_dashboard` (Flutter Web)
- `medogram_site` (React/Next for marketing & blog)

**Infrastructure:** PostgreSQL (+pgvector/FTS), Redis (queues/cache), MinIO/S3 (file storage), Celery (jobs), structured logging, optional Kafka/Streams for event processing.

A standard deployment: Nginx → `api_gateway` → Django services; Celery workers for background jobs; MinIO/S3 for file exports.

---

## Core Modules

- **Authentication & RBAC:** `auth_otp`, `rbac`
- **Clinical:** `encounters`, `soap`, `triage`, `checklist`
- **Communication:** `chat`, `notifications`
- **AI/Agents:** `ai_helsabrain`, `ai_guardrails`, `stt`
- **Data & Files:** `files`, `exports`, `search`, `fhir_adapter`
- **Operations:** `payments`, `billing`, `analytics`, `audit`, `privacy`, `scheduler`, `webhooks`, `admin_portal`, `api_gateway`, `compliance`, `devops`

---

## Clinical Data Model & Standards

- **SOAP Schema:** Canonical JSON schema (`schema/soap.schema.yaml`)
- **FHIR Mapping:** Condition, Observation, ImagingStudy, CarePlan (see `docs/fhir_mapping.md`)
- **Versioning:** Every SOAP update = new immutable version with UUID encounter IDs

---

## Security & Compliance

- OTP via Kavenegar with throttling & temporary lockouts
- Role-based access control with strict least‑privilege
- Mandatory PII/PHI redaction (`security/privacy/redactor.py`)
- HMAC-signed artifacts and tamper‑evident audit logs
- TLS encryption, secret management via environment variables

---

## Agent Governance

- **MOM Spec** (`docs/agent_mom_spec.md`)
- **SOPs:** Operational & Safety (`docs/SOP-operational.md`, `docs/SOP-safety.md`)
- **Prompt Contracts:** Schema validation, guardrails, stop & escalate on violations
- **Event Bus:** Significant agent events emitted for monitoring

---

## Local Development

### Requirements

- Python 3.11+, PostgreSQL 14+, Redis 6+, MinIO/S3, Flutter 3.35+, Node.js 18+

### Quickstart (Backend)

```bash
git clone <repo-url> helssa && cd helssa
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver
```

### Workers & Frontends

```bash
celery -A helssa worker -l info
celery -A helssa beat -l info
flutter pub get && flutter run -d chrome
```

---

## Configuration (.env)

```dotenv
DJANGO_SECRET_KEY=changeme
DEBUG=false
ALLOWED_HOSTS=api.helssa.local,localhost
DATABASE_URL=postgres://user:pass@localhost:5432/helssa
REDIS_URL=redis://localhost:6379/0
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=helssa-media
KAVENEGAR_API_KEY=xxxxx
TALKBOT_API=xxxxx
```

---

## Run & Services

- Django API (`python manage.py runserver`)
- Celery workers & beat (STT, exports, cleanup)
- MinIO for object storage
- Nginx for reverse proxy & static serving

---

## Testing & QA

- Unit/Integration: `pytest -q`
- Contract Tests: `tests/contract/`
- Clinical Eval Suite: `eval/medical_eval_suite.md`
- Coverage: `pytest --cov=.`

---

## Logging & Observability

- Structured JSON logs: `timestamp, trace_id, session_id, agent_id, step, decision`
- Metrics: latency, error rates, token usage, escalations
- Tracing: propagate `trace_id` across async tasks

---

## CI/CD

- GitHub Actions: lint → test → contract tests → build → release
- Secrets: `DJANGO_SECRET_KEY`, `DATABASE_URL`, `REDIS_URL`, `MINIO_*`, `KAVENEGAR_API_KEY`, `TALKBOT_API`

---

## Contributing

1. Fork and clone
2. Create feature branch (`feat/<name>`)
3. Add tests & docs
4. Submit PR and ensure green checks

---

## License

Proprietary — © Helssa/Medogram. All rights reserved.
