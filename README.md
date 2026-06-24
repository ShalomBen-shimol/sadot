# פנסיון בשדות — מערכת CRM ואוטומציה

מערכת CRM לניהול תהליכי מסירה, ויתור, אימוץ והעברת בעלות של כלבים עבור "פנסיון בשדות".
נבנתה כבסיס מודולרי שניתן להרחיב בעתיד (פנסיון חופשות, חנות דיגיטלית, חשבונאות, סוכני AI ועוד).

## טכנולוגיה

- **Backend**: Python 3.12, FastAPI, SQLModel, PostgreSQL, Alembic, JWT.
- **Frontend**: Next.js (App Router), React, Tailwind, RTL מלא בעברית.
- **Infra**: Docker Compose (backend, frontend, postgres).

כל אינטגרציה חיצונית (WhatsApp / תשלומים / חתימה / Email / monday) ממומשת בשלב זה כ-**Mock adapter** מאחורי abstraction.

## מבנה

```
backend/    FastAPI service
frontend/   Next.js app
docker-compose.yml
```

## הרצה מקומית (Docker)

```bash
cp backend/.env.example backend/.env
docker compose up --build
```

- API:        http://localhost:8000  (docs: /docs)
- Frontend:   http://localhost:3000
- Postgres:   localhost:5432

## הרצת backend בלבד (ללא Docker)

```bash
cd backend
python -m venv .venv
. .venv/Scripts/activate      # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
# אם אין Postgres זמין, אפשר להשתמש ב-SQLite דרך DATABASE_URL ב-.env
uvicorn app.main:app --reload
```

ראה `docs/ARCHITECTURE.md` לפירוט הארכיטקטורה והרחבות עתידיות.

## סטטוס שלב 1 (MVP)

מיושם: מודל נתונים מלא, CRUD לישויות מרכזיות, workflows למסירה/אימוץ/העברת בעלות,
מנגנון follow-up, mock adapters, seed data, public adoption pages, back-office בסיסי.

לא בשלב זה (stubs/abstraction בלבד): סליקה אמיתית, WhatsApp אמיתי, חתימה אמיתית,
Email אמיתי, monday אמיתי, OCR, חנות, חשבונאות, משפטי, פנסיון חופשות.
