# Repository Style Guide (Helssa/Medogram/Soapify)
- Prefer `JSONField` for schemaless extras; validate before save.
- **DRF Views (MUST)**

- Always set `permission_classes` and `authentication_classes` explicitly.
- Validate serializers; avoid `serializer.save()` without `validated_data` checks.
- Paginate list views; limit queryset and protect against mass assignment.
- **Security (MUST)**

- Enforce CSRF where session auth is used. For token/JWT, ensure HTTPS and short‑lived tokens.
- For file storage (e.g., MinIO/S3): use presigned URLs; never expose bucket keys.
- **Migrations (SHOULD)**

- keep migrations reversible and human‑reviewable.

**Python style**

- Black/ruff (or flake8) for formatting/lint; 4‑space indents; max line length 100.
- Docstrings: Google style; include Args/Returns/Raises for non‑trivial functions.

---

## TypeScript/React

- **Components (SHOULD)**

- prefer function components + hooks; memoize expensive computations.
- 
- **State (SHOULD)**

- co-locate state; derive state where possible; avoid prop drilling via context where appropriate.
  
- **Safety (MUST)**

- no `any` in public APIs; strict mode; narrow types via guards.
  
- **Data Fetching (MUST)**

- handle loading/error states; abort stale requests; cache via SWR/RTK Query.

- **XSS (MUST)**

- never render unsanitized HTML; use `dangerouslySetInnerHTML` only with sanitization.

- **Accessibility (MUST)**

- semantic elements/labels; keyboard navigation; focus management.

---

## Dart/Flutter

- **Architecture (SHOULD)**
  
- use BLoC/Provider/Riverpod; separate UI, state, and services.

- **Performance (SHOULD)**
  
- prefer const widgets; avoid rebuilds; profile heavy lists.

- **Null Safety (MUST)**
  
- embrace non‑nullable types; avoid `!` unless justified.

- **Networking (MUST)**
  
- timeouts, retry/backoff policies; handle offline gracefully.

---

## API & Contracts

- **Versioning (MUST)**
  
- avoid breaking changes; document in `CHANGELOG.md`.

- **Validation (MUST)**
  
- validate request/response against schemas; return consistent error shapes.

- **Pagination & Filtering (SHOULD)**
  
- standardize params; enforce limits.

---

## PR Checklist (what Gemini should look for)

- **Security**
  
- authz on every protected endpoint; no secrets; correct CORS.
  
- **Tests**
  
- new/changed logic has tests; coverage thresholds met.
  
- **Docs**
  
- public APIs and complex modules have docstrings/README updates.
  
- **Performance**
  
- obvious N+1s eliminated; pagination in place.
  
- **Style**
  
- lints pass; no dead code; no TODOs in production paths.

---

## Commit Messages

- **Conventional Commits (SHOULD)**
  
- `feat:`, `fix:`, `docs:`, `refactor:`, `perf:`, `test:`, `build:`, `ci:`
  
- Reference issues in body; include migration and backward‑compatibility notes.
