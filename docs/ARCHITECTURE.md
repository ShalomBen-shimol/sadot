# ארכיטקטורה — פנסיון בשדות

## עקרונות

- הפרדת שכבות נקייה: `models` (DB) → `repositories` → `services` (לוגיקה עסקית) → `api` (HTTP).
- כל אינטגרציה חיצונית מאחורי `adapters/` עם abstraction ומימוש Mock. החלפה למימוש אמיתי = הוספת מחלקה + הגדרת env var, ללא שינוי בלוגיקה.
- הפרדה בין מידע ציבורי לרגיש: ה-public API מחזיר schema מצומצם בלבד (`DogPublic`), ללא ת.ז/כתובת/הערות פנימיות.
- כל פעולה רגישה נרשמת ב-`AuditLog`.

## שכבות (backend)

```
app/
  core/          config, database (engine/session), security (JWT+bcrypt), logging
  models/        SQLModel tables + enums (כל הסטטוסים מרוכזים ב-enums.py)
  schemas/       Pydantic I/O (כולל public schemas מסוננים)
  repositories/  CRUDRepository גנרי
  services/      workflows: surrender, adoption, ownership, leads, notifications, audit, municipality
  adapters/      messaging, payment, signature, email, monday (Mock)
  api/v1/        routers: auth, public, dashboard, dogs, surrender, adoption, ownership + CRUD גנרי
  tasks/         scheduler ל-follow-up (asyncio; ניתן להחלפה ב-Celery/RQ)
  db/seed.py     admin + רשויות + כלבי דמו
  alembic/       migrations
```

## ישויות מרכזיות

`User, Person, Dog, DogPhoto, SurrenderCase, SubscriptionPayment, AdoptionLead, AdoptionCase, OwnershipTransfer, Document, SignatureRequest, Task, Message, Municipality, AuditLog`.

## API מרכזי

- `POST /api/v1/auth/login`, `GET /api/v1/auth/me`, `POST /api/v1/auth/users` (admin)
- Public: `GET /public/dogs`, `GET /public/dogs/{id}`, `POST /public/leads/surrender`, `POST /public/leads/adoption`
- `GET /dashboard/summary`
- `dogs`: CRUD + `/status` + `/photos`
- `surrender-cases`: CRUD + `/activate-home-subscription` + `/charge-month` + `/payments` + `/start-facility-transfer` + `/convert-to-facility`
- `adoption-leads`, `adoption-cases` (CRUD + `/approve` + `/complete` + `/status`)
- `ownership-transfers`: CRUD + `/required-documents` + `/send-to-authority` + `/confirm` + `/stop` + `/run-followups`
- CRUD גנרי: `people`, `municipalities`, `tasks`, `documents`, `signatures`, `messages`

## Workflows מרכזיים

### מסירה מהבית (home subscription)
ליד → `SurrenderCase(home_subscription)` → `activate-home-subscription` יוצר תשלום חודשי (mock) והכלב הופך `available_for_adoption` עם מיקום `home`. כל `charge-month` מגדיל את `accumulated_credit`. אחרי ~7 חודשים (7,000 ₪) ניתן `convert-to-facility`.

### מסירה לפנסיון
`start-facility-transfer` → `OwnershipTransfer(surrender_to_facility)`, איסוף מסמכים, `send-to-authority` (מייל mock) + פתיחת משימת follow-up.

### אימוץ
`AdoptionCase` → `approve` (פותח `OwnershipTransfer` + בקשות חתימה mock) → השלמת מסמכים → `send-to-authority` → `confirm` → `complete` (הכלב `adopted`, הודעת בקשת סרטון + הצעת חנות).

### מנגנון follow-up מול הרשות
שליחת מייל אינה מספיקה: `send-to-authority` קובע `next_followup_at = today + FOLLOWUP_DAYS` ופותח משימה. ה-scheduler (או `POST /ownership-transfers/run-followups`) סורק תיקים שתאריך המעקב שלהם הגיע, פותח תזכורת ומתזמן את הבא — עד `confirm` או `stop`.

## רשויות וטרינריות
`Municipality` נפתרת לפי יישוב (`resolve_by_city`). בהעברת בעלות נשמרות `from_authority_id` (רשות המוסר) ו-`to_authority_id` (רשות המקבל), ושתיהן מקבלות התראה.

## מה Mock בשלב 1
WhatsApp, תשלומים, חתימה דיגיטלית, Email, monday — כולם מאחורי adapters. ברירת המחדל היא Mock; כאשר מוגדר token/מפתח אמיתי ב-`.env`, יש להוסיף את מימוש ה-Provider האמיתי במקום ה-`pass` הקיים.

## הרחבות עתידיות (לא ב-Scope, מתוכננות)
- סוכן AI על גבי `Message` (intent / suggested next action / human handoff).
- חנות דיגיטלית, חשבונאות, מודול משפטי, פנסיון חופשות — כמודולי services/adapters נוספים.
- monday/WordPress sync דרך ה-adapters וה-public API.

## פריסה
Docker Compose (db + backend + frontend). בפרודקשן יש להריץ `alembic upgrade head` במקום יצירת טבלאות אוטומטית, ולהגדיר `SECRET_KEY` חזק ו-`DATABASE_URL` ל-Postgres של Lavie.
