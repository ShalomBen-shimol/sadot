# פריסה — aiserver (Docker)

המערכת רצה ב-Docker Compose על שרת ה-aiserver, מאחורי nginx, בכתובת `https://sadot.lavit.io`.
השרת מארח גם את ה-CRM הקיים (`crm.lavit.io`), לכן הפריסה מבודדת בפורטים מקומיים בלבד.

## טופולוגיה

```
האינטרנט → ראוטר מעבדה (192.168.50.1)
   ├── :443 SNI passthrough  sadot.lavit.io → aiserver:443  (nginx מסיים TLS)
   └── :80  Host proxy       sadot.lavit.io → aiserver:8080 (HTTP; ACME + redirect ל-https)
aiserver nginx → /        → 127.0.0.1:3001  (frontend, Next.js בקונטיינר)
                 /api/     → 127.0.0.1:8001  (backend, FastAPI בקונטיינר)
backend → db (Postgres ייעודי, פנימי לרשת ה-compose, לא חשוף לשרת)
```

פורטים מקומיים נבחרו כדי לא להתנגש בשירותים הקיימים (CRM על 8000, Postgres מערכת על 5432).
**חשוב:** השרת אינו מקבל תעבורה ישירה על :80 — הראוטר ממפה :80 חיצוני ל-`aiserver:8080`,
לכן vhost ה-HTTP מאזין על 8080 (ולא 80). ראו `deploy/nginx-sadot.conf` (תואם ל-vhost של crm.lavit.io).
הסטטוס נכון ל-2026-06-24: **חי ב-`https://sadot.lavit.io`** (cert של Let's Encrypt, חידוש אוטומטי).

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
6. nginx — בשני שלבים (כי בלוק ה-443 דורש שה-cert כבר קיים):
   א. תחילה vhost עם בלוק ה-**8080 בלבד** (ACME + redirect), `nginx -t && systemctl reload nginx`.
   ב. `sudo certbot certonly --webroot -w /var/www/html -d sadot.lavit.io` (HTTP-01; הראוטר כבר מפנה :80→:8080).
   ג. הוספת בלוק ה-**443 ssl** מ-`deploy/nginx-sadot.conf`, `nginx -t && systemctl reload nginx`.
   (אין להשתמש ב-`certbot --nginx` — הוא מניח :80 ועלול לבלבל את ה-vhosts בשרת המשותף.)
7. אימות חיצוני: `curl -I https://sadot.lavit.io` ו-`openssl s_client -servername sadot.lavit.io -connect 84.95.242.166:443` → CN של ה-cert = sadot.lavit.io.

## עדכון גרסה

```
cd ~/projects/sadot && git pull
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```
