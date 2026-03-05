# Repository Analysis and Production Refactoring Plan

## 1) Current Architecture

### High-level structure
- **Entrypoints**: `app.py` and `run.py` both instantiate the Flask app via `create_app()`, with `run.py` starting Flask in debug mode. This creates duplicated launch behavior and environment-specific startup logic in source code. 
- **Application factory**: `app/__init__.py` defines `create_app()` and wires routes from a single `register_routes()` function.
- **Routing layer**: `app/routes.py` contains nearly all behavior (auth, profile, exam flow, admin dashboards, reporting, OTP email, CSV export) in one monolithic file.
- **Configuration**: `app/config.py` contains env-backed config values, but route code still includes merge-conflicted hardcoded credential branches.
- **Persistence**: Direct MySQL access via `mysql.connector` with inline SQL in routes.
- **Presentation**: Server-rendered Jinja templates in `templates/`; all admin/student pages are handled from the same route module.
- **Assets**: CSS/JS/images under `static/`.

### Functional architecture currently implemented
- **Student flow**: signup + OTP verification, login, attempt test from random question set, submit answers, view result summary.
- **Admin flow**: dashboard metrics and charts, student drill-down, attempt detail view, question-set and question creation, CSV export.
- **Support flow**: help form submission + outbound email.

## 2) Problems in the Project

### Critical codebase health problems
1. **Unresolved Git merge conflicts in production files** (`app/__init__.py`, `app/routes.py`) break Python parsing and app startup.
2. **Monolithic route file** (~1000+ lines) mixes concerns: HTTP handlers, DB access, email transport, authorization, exam business logic, and reporting.
3. **No automated tests** (unit/integration/e2e absent).
4. **Minimal documentation** (`README.md` has no setup, architecture, deployment, or operations guidance).
5. **Inconsistent/unused imports and dead paths** (e.g., libraries imported but not consistently used, duplicated comments/legacy blocks).
6. **Template-data contract mismatches** in exam page (`question.question` / `opt.text`) vs SQL fields (`question_text` / `option_text`).
7. **Schema/runtime mismatch risk**: app writes to `help_requests`, but that table is not present in `website.sql`.

### Operational/engineering maturity gaps
- No linting/formatting/type checks.
- No migration framework (raw SQL dump only).
- No structured logging.
- No error monitoring / observability.
- No dependency pinning strategy.

## 3) Missing Professional Features

### Product features missing for a production exam platform
- **Role lifecycle management**: no admin user management UX for role assignment, activation/deactivation, lockout.
- **Exam lifecycle controls**: scheduling windows, attempt limits, exam duration enforcement, anti-cheat controls, question randomization policies, retake rules.
- **Question bank maturity**: tagging, difficulty, versioning, bulk import/export, soft delete, audit history.
- **Analytics maturity**: cohort analytics, item analysis (question discrimination/difficulty), trend segmentation by course/batch/date.
- **Result publication workflow**: reviewed/released statuses and notification workflows.

### Platform-level features missing
- CI/CD pipeline, environment promotion strategy, rollback process.
- Background worker for email and heavy reporting.
- Caching for dashboards and high-read endpoints.
- API surface (currently tightly coupled server-rendered app).
- Backup/restore and DR runbook.

## 4) Security Issues

1. **Hardcoded secrets/default credentials in source config defaults** (secret key, DB creds, email credentials) create immediate credential exposure risk.
2. **Unresolved conflict branch in routes includes plaintext email app password path**, increasing accidental secret leakage.
3. **Flask debug mode enabled in `run.py`** is unsafe in production.
4. **No CSRF protection visible** for forms handling auth, settings, and exam submission.
5. **OTP security weaknesses**:
   - OTP stored in session only, no explicit expiry/attempt throttling.
   - No brute-force protection / rate limiting around OTP verify/reset.
6. **File upload handling is weak**:
   - Extension-based check only (no MIME validation/content scanning/size limits).
   - File naming from user email can cause collisions and enumeration.
7. **Potential information leakage in user-facing error messages** (raw exception strings flashed in help flow).
8. **No visible session hardening flags** (secure cookie, httponly, samesite, session lifetime policy).
9. **No account lockout / login rate limits / MFA for admin accounts**.
10. **PII exposure in SQL dump** (real-looking emails and user profile paths checked into repository data).

## 5) Scalability Issues

1. **Synchronous request path for email sending and heavy DB operations** increases request latency and failure coupling.
2. **No connection pooling abstraction**; each handler opens/closes direct DB connections manually.
3. **Monolithic route module blocks team parallelism** and increases deploy risk.
4. **N+1 query patterns** in exam question loader (per-question option query loop).
5. **`ORDER BY RAND()` for random question set selection** is expensive at scale.
6. **Server-side session payload stores full question objects**, which can bloat cookies/session store depending configuration.
7. **Analytics queries executed live on each admin dashboard load** without caching/materialization.
8. **No pagination strategy on admin listing/reporting endpoints.**

---

## Proposed Professional Architecture (Production Flask)

## A) Target architecture overview

Use a **modular monolith** first (faster to stabilize than microservices), with clear bounded modules and clean interfaces:

- `app/core` - config, extensions, logging, security, error handling
- `app/auth` - registration/login/password reset/OTP/MFA
- `app/users` - profile + role management
- `app/exams` - question bank, exam delivery, attempt processing
- `app/results` - result views, exports
- `app/analytics` - dashboard and reporting APIs
- `app/admin` - admin-facing orchestration routes
- `app/infrastructure` - repositories, mail adapters, cache adapters, background job adapters

Adopt **Blueprints + service layer + repository layer**:
- Controllers (Blueprint routes) do validation + HTTP concerns only.
- Services implement business rules.
- Repositories handle SQLAlchemy queries.

## B) Recommended technology baseline

- Flask + Blueprints
- Flask-SQLAlchemy (or SQLAlchemy 2.0 core + ORM)
- Alembic/Flask-Migrate for schema migrations
- Flask-Login for auth session management
- Flask-WTF or CSRFProtect for CSRF
- Redis for cache + rate-limits + Celery broker
- Celery/RQ for async email/report tasks
- Gunicorn + Nginx (or containerized ingress)
- Pytest for tests
- Sentry/OpenTelemetry for monitoring

## C) Domain and access model

### Roles
- `admin`
- `student`

### Core domain entities
- User
- Role/Permission (optional RBAC tables for future growth)
- QuestionBankItem
- QuestionOption
- Exam
- ExamQuestion (exam snapshot/versioned mapping)
- Attempt
- AttemptAnswer
- AnalyticsSnapshot (optional pre-aggregates)

### Access policies
- Decorator/policy-based authorization per module.
- Admin-only endpoints separated under `/admin/*` blueprint.
- Service-level authorization checks (not template-only checks).

## D) Production-grade feature design (requested scope)

### Admin features
1. **Manage question bank**
   - CRUD + versioning + tags/difficulty
   - bulk CSV upload with validation pipeline
2. **View student exam results**
   - paginated results with filters (date, exam, student, pass/fail)
3. **Analytics dashboard**
   - cached aggregates, trend charts, pass/fail, top weak topics

### Student features
1. **Register/login**
   - verified email, secure password policy, optional MFA
2. **Take exams**
   - exam session object with timer and attempt controls
3. **View results**
   - attempt history + detailed question-wise review (policy controlled)

## E) Data architecture improvements

- Move from SQL dump to managed migrations.
- Add indexes for common filters: `(user_id, attempted_at)`, `(exam_id, attempted_at)`, `(role, created_at)`.
- Avoid runtime `ORDER BY RAND()`; precompute randomized exam forms or random IDs via sampling strategy.
- Add audit tables for admin actions.
- Add soft-delete columns where needed.

## F) Security hardening baseline

- Secrets only via env/secret manager (no defaults for production).
- CSRF enabled globally for form POSTs.
- Rate limiting: login, OTP request, OTP verify, password reset.
- OTP stored server-side with expiry and retry counters.
- Session hardening: secure, httponly, samesite, rotation after login.
- Strict upload controls: size limits, MIME sniffing, extension whitelist, random filenames, isolated storage.
- Secure headers (CSP, HSTS, X-Frame-Options, etc.).
- Centralized error handling and sanitized user messages.

## G) Scalability baseline

- Add Redis cache for dashboard aggregates and read-heavy pages.
- Async tasks for email and exports.
- Query optimization + pagination everywhere.
- Connection pooling via SQLAlchemy engine.
- Optional read replicas for analytics if load grows.

---

## Refactoring Plan (Phased)

## Phase 0 - Stabilize (1-2 days)
1. Resolve merge conflicts and restore runnable app.
2. Remove hardcoded secrets; enforce `.env` + config validation.
3. Add basic health endpoint and structured logging.
4. Add minimal README (setup, run, env vars).

## Phase 1 - Foundation (3-5 days)
1. Introduce app factory with extension registry (`db`, `login_manager`, `csrf`, `migrate`).
2. Split `routes.py` into Blueprints: `auth`, `student`, `admin`, `analytics`.
3. Introduce SQLAlchemy models matching existing schema.
4. Add Alembic migrations and baseline migration script.

## Phase 2 - Security & correctness (3-5 days)
1. CSRF + rate limiting + secure session config.
2. OTP redesign with expiry + retry limits + audit logs.
3. Fix template/data contract mismatches and validation errors.
4. Replace raw exception flashes with standardized error responses.

## Phase 3 - Feature parity uplift (5-8 days)
1. Question bank CRUD with validation and pagination.
2. Results module with filtering/export and attempt drill-down.
3. Analytics service with cached aggregate queries.
4. Student attempt history with robust exam workflow state machine.

## Phase 4 - Quality gates (3-5 days)
1. Add pytest suites:
   - unit tests for services
   - integration tests for DB flows
   - route tests for role access control
2. Add lint/format/type checks (ruff/black/mypy optional).
3. CI pipeline (test + lint + migration check).

## Phase 5 - Production readiness (3-5 days)
1. Containerize app + Gunicorn config.
2. Add observability (Sentry/OpenTelemetry + metrics).
3. Backup/restore and incident runbook.
4. Performance baseline and load test report.

## Suggested target directory structure

```text
exam/
  app/
    __init__.py
    core/
      config.py
      extensions.py
      logging.py
      security.py
    auth/
      routes.py
      service.py
      schemas.py
    admin/
      routes.py
      service.py
    student/
      routes.py
      service.py
    exams/
      models.py
      repository.py
      service.py
    analytics/
      routes.py
      service.py
    templates/
    static/
  migrations/
  tests/
    unit/
    integration/
    e2e/
  wsgi.py
  requirements/
    base.txt
    prod.txt
    dev.txt
  Dockerfile
  docker-compose.yml
  README.md
```

## Immediate next 10 actions (practical)
1. Fix merge conflicts in `app/__init__.py` and `app/routes.py`.
2. Remove all plaintext secrets from repository history and rotate compromised credentials.
3. Add `Flask-WTF` + CSRF protection.
4. Add request rate limiting for auth/OTP endpoints.
5. Introduce Blueprint split: `auth`, `admin`, `student`.
6. Replace per-route DB connection boilerplate with SQLAlchemy session management.
7. Normalize exam question payload keys (`question_text`, `option_text`) across templates and route logic.
8. Add migration for missing `help_requests` table (or remove route dependency).
9. Add test coverage for login/signup/test submission/admin-only endpoints.
10. Add CI workflow + production run command (`gunicorn`).
