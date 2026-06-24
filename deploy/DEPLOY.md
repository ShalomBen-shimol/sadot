# פריסה — aiserver (Docker)

המערכת רצה ב-Docker Compose על שרת ה-aiserver, מאחורי nginx, בכתובת `https://sadot.lavit.io`.
השרת מארח גם את ה-CRM הקיים (`crm.lavit.io`), לכן הפריסה מבודדת בפורטים מקומיים בלבד.

## טופולוגיה

```
האינטרנט → nginx (443) sadot.lavit.io
              ├── /        → 127.0.0.1:3001  (frontend, Next.js בקונטיינר)
              └── /api/    → 127.0.0.1:8001  (backend, FastAPI בקונטיינר)
backend → db (Postgres ייעודי, פנימי לרשת ה-compose, לא חשוף לשרת)
```

פורטים מקומיים נבחרו כדי לא להתנגש בשירותים הקיימים (CRM על 8000, Postgres מערכת על 5432).

## קבצים

- `docker-compose.yml` — בסיס.
- `docker-compose.prod.yml` — override לפרודקשן (binding ל-127.0.0.1, פורטים 8001/3001, DB פנימי, סודות מ-`.env`).
- `deploy/nginx-sadot.conf` — vhost ל-nginx.
- `.env` (בשורש, לא ב-git) — סודות: `POSTGRES_PASSWORD`, `SECRET_KEY`, `FIRST_ADMIN_*`.

## שלבים

1. **DNS**: רשומת A עבור `sadot.lavit.io` → `84.95.242.166`.
2. התקנת Docker + compose plugin.
3. `git clone https://github.com/ShalomBen-shimol/sadot.git ~/projects/sadot`
4. יצירת `.env` בשורש ו-`backend/.env` (ראו דוגמאות).
5. `docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build`
6. העתקת `deploy/nginx-sadot.conf` ל-`/etc/nginx/sites-available/sadot`, symlink ל-`sites-enabled`, `nginx -t && systemctl reload nginx`.
7. `sudo certbot --nginx -d sadot.lavit.io` (לאחר שה-DNS התעדכן).

## עדכון גרסה

```
cd ~/projects/sadot && git pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```
