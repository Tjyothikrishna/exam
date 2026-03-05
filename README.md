# Exam System (Flask)

Production-ready starter setup for an exam platform with:
- Role-based auth (admin/student)
- Admin exam/question management
- Student exam flow and results
- Admin analytics dashboard

## 1) Prerequisites
- Python 3.11+
- Docker + Docker Compose (recommended for production-like local setup)

## 2) Environment Variables
Create a `.env` file (already included for local defaults):

```env
SECRET_KEY=change-me-in-production
DATABASE_URL=postgresql+psycopg2://exam_user:exam_pass@db:5432/exam_db
```

Required variables:
- `SECRET_KEY`
- `DATABASE_URL`
- `EMAIL_USER`
- `EMAIL_PASS`

Optional SMTP variables:
- `SMTP_HOST` (default: `smtp.gmail.com`)
- `SMTP_PORT` (default: `587`)

## 3) Local Development (without Docker)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export SECRET_KEY="change-me"
export DATABASE_URL="postgresql+psycopg2://exam_user:exam_pass@localhost:5432/exam_db"
python app.py
```

App starts on `http://127.0.0.1:5000`.

## 4) Docker Deployment

### Build and run
```bash
docker compose up --build
```

Services:
- `web`: Flask app on port `5000`
- `db`: PostgreSQL on port `5432`

### Stop
```bash
docker compose down
```

## 5) Production Notes
- Replace `.env` values with secure secrets.
- Use managed PostgreSQL and secret manager in production.
- Replace Flask dev server with Gunicorn/Uvicorn behind Nginx/Ingress.
- Add DB migrations (`flask db upgrade`) in deployment pipeline.

## 6) CI/CD (GitHub Actions)
Workflow: `.github/workflows/ci-cd.yml`

Pipeline steps:
1. Install dependencies
2. Run tests/checks (`pytest`, Python compile)
3. Build Docker image

## 7) Project Structure

```text
app/
  models/
  routes/
  services/
templates/
static/
app.py
Dockerfile
docker-compose.yml
```
