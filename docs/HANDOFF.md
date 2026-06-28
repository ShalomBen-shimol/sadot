# HANDOFF — Autonomous Build Session (`feat/autonomous-build`)

מסמך מסירה לסשן הבנייה האוטונומי של מערכת ה‑CRM "פנסיון בשדות".
Handoff notes for the autonomous build session. Branch: `feat/autonomous-build` (ahead of `main`).

---

## 1. Scope of this session / מה נבנה בסשן הזה

Built on top of the existing phase‑1 MVP (data model, CRUD, surrender/adoption/ownership
workflows, mock adapters, public adoption pages, basic back‑office). This session added the
**on‑site QR intake, document/storage layer, signature lifecycle, aggregate back‑office APIs,
a fully typed frontend API client, the QR smart‑intake forms, the back‑office CRM screens,
and the adoption catalog**.

Commits (`git log --oneline main..HEAD`):

```
ca27e12 Add pytest suite for CRM workflows + CI test gate; add spec docs
649683d Backend: QR code intake-link endpoints
fcdeedb Backend: document upload + local storage adapter
6a95c5f Backend: signature mock lifecycle advancing adoption case
29be505 Backend: back-office aggregate case-file endpoints + filters
3f7db24 Frontend: expand typed API client
c684f1e Frontend: QR smart intake forms (surrender/adopt) + consent + upload
14d262b Frontend: back-office CRM case-file screens
d85b7e8 Frontend: adoption catalog + dog profile polish
0e4f273 Frontend: static review fixes
```

Diff size vs `main`: ~6,080 insertions across 59 files.

---

## 2. Backend — what was built / מה נבנה ב‑Backend

Architecture preserved strictly: `models -> repositories -> services -> api/v1 routers`,
external integrations behind `app/adapters/*` with a Mock default + `get_*()` factory,
sensitive actions logged via `app/services/audit.py`, enums centralized in `app/models/enums.py`.

### QR on‑site intake — `app/api/v1/qr.py`
- Admin‑protected endpoints that generate printable QR codes pointing at the **public** intake forms:
  - `GET /api/v1/qr/links` — returns the encoded URLs (`surrender`, `adopt`, optional `dog_id` deep‑link).
  - `GET /api/v1/qr/surrender.png` — PNG QR of the public surrender form.
  - `GET /api/v1/qr/adopt.png?dog_id=` — PNG QR of the public adoption form (optionally deep‑linked).
- Base URL from new setting `public_site_url` (default `https://sadot.lavit.io`).
- New dependency `qrcode[pil]==8.2` (added to `requirements.txt` and installed in the venv).

### Uploads / storage — `app/adapters/storage.py`, `app/api/v1/documents.py`
- New `StorageProvider` abstraction + `LocalStorageProvider` (filesystem under `MEDIA_ROOT`,
  default `media/`), with path‑traversal protection. Factory `get_storage_provider()` (S3/GCS later).
  Registered in `app/adapters/__init__.py`.
- `documents.py` replaces the generic CRUD router for documents:
  - `POST /api/v1/documents` — multipart upload (file + entity_type/entity_id/document_type), routed
    through the storage adapter, filename sanitized, audit‑logged, sensitive types flagged.
  - `GET /api/v1/documents`, `GET /api/v1/documents/{id}` — list/filter by related entity.
- New config: `media_root`.

### Signatures lifecycle — `app/services/signatures.py`, `app/api/v1/signatures.py`
- Mock signing callback flow:
  - `GET /api/v1/signatures` (filter by entity), `GET /api/v1/signatures/{id}`.
  - `POST /api/v1/signatures/{id}/mark-signed` — simulates the provider webhook: sets
    `status=signed`, audit logs, then advances the related adoption case state machine. Idempotent.
- `app/services/adoption.py` gained `advance_after_signatures()`: once **all** signature requests for
  a case are signed, moves `waiting_for_signatures -> waiting_for_documents` (no‑op while outstanding).

### Back‑office aggregate case files — `app/api/v1/backoffice.py`, `app/services/backoffice.py`, `app/schemas/backoffice.py`
- Single‑request "case file" reads for the CRM screens (auth‑protected; admin‑level fields allowed,
  never used by the public API):
  - `GET /api/v1/people/{id}/file` -> `PersonFile` (person + dogs owned, surrender/adoption cases,
    leads, documents, recent messages).
  - `GET /api/v1/dogs/{id}/file` -> `DogFile` (dog + owner, cases, leads, transfers, documents, photos).
  - `GET /api/v1/ownership-transfers/{id}/detail` -> `OwnershipTransferDetail` (resolved parties,
    authority names, required docs + `documents_complete`, signature requests).
- Generic CRUD routers / surrender / adoption / crud got additional list filters (see diffs).

### Tests + CI
- `backend/tests/` expanded; `pytest.ini` added; `requirements-dev.txt` added (`pytest==8.3.4`).
- CI gate in `.github/workflows/deploy.yml` runs pytest before deploy.
- Spec docs added under `docs/` (DOCX).

---

## 3. Frontend — what was built / מה נבנה ב‑Frontend

Next.js 14 App Router + React 18 + Tailwind, full RTL Hebrew. **Not compiled in this environment**
(no node/npm/docker) — written type‑correct against the real API contract.

### Typed API client — `frontend/src/lib/api.ts`
- Expanded to ~940 lines: helpers `authGet/authPost/authPatch/authDelete/authUpload/postForm`, and
  typed functions for the full surface — public dogs/leads, auth, dashboard, dogs (+`getDogFile`),
  people (+`getPersonFile`), surrender cases (subscriptions/charges/facility transfer), adoption
  leads/cases (create/approve/complete/status), ownership transfers (required docs, detail, send to
  authority, confirm, stop, run follow‑ups), documents (list/get/upload), signatures (list/get/
  mark‑signed), and `getQrLinks`.

### QR smart intake forms — `app/surrender/page.tsx`, `app/adopt/`, components
- Public surrender form heavily expanded (multi‑section intake).
- `components/AdoptionForm.tsx` expanded; `ConsentNotice.tsx` (privacy/consent) and
  `DocumentUpload.tsx` added; QR/`src`/`dog_id` deep‑link aware.

### Adoption catalog — `components/DogCatalog.tsx`, `DogGallery.tsx`, `DogCard.tsx`, `lib/dogLabels.ts`
- Catalog with filtering + dog gallery; adoption profile page (`app/adopt/[id]/page.tsx`) polished
  with loading states.

### Back‑office CRM screens — `app/admin/**`
- Shared `_components/ui.tsx` + `_components/labels.ts` (Hebrew enum labels).
- List + detail screens for: dogs, surrender‑cases, adoption‑cases, ownership‑transfers; admin
  layout and dashboard updates.

---

## 4. VERIFIED vs UNVERIFIED

### VERIFIED — Backend
- `pytest` is **GREEN**: **59 passed** (run now from `backend/`).
- Command:
  ```bash
  cd backend
  PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe -m pytest
  ```

### UNVERIFIED — Frontend (needs a build to verify)
- The frontend was **NOT compiled** — node/npm/docker are unavailable in this environment.
  TypeScript was written against the API contract but has **not** been type‑checked or built.
- To verify:
  ```bash
  cd frontend && npm install && npm run build
  # or, full stack via Docker:
  docker compose up --build
  ```

---

## 5. How to run locally / הרצה מקומית

```bash
cp backend/.env.example backend/.env
docker compose up --build
```
- API:      http://localhost:8000  (docs at `/docs`)
- Frontend: http://localhost:3000
- Postgres: localhost:5432
- Seeded admin: `admin@sadot.local` / `admin1234`

Backend only (no Docker):
```bash
cd backend
python -m venv .venv
. .venv/Scripts/activate        # Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

### Where things live
- Backend service: `backend/app/` — `adapters/` (integrations + mocks), `services/` (workflows),
  `api/v1/` (routers), `models/` (SQLModel + `enums.py`), `repositories/`, `schemas/`.
- Frontend: `frontend/src/` — `lib/api.ts` (typed client), `app/` (routes incl. `admin/`,
  `surrender/`, `adopt/`), `components/`.
- Specs: `docs/ARCHITECTURE.md` and the Hebrew DOCX spec/open‑questions files.
- Storage default: local FS under `backend/media/` (`MEDIA_ROOT`).

---

## 6. Known issues / בעיות ידועות

- **Frontend unbuilt** — no compile/type‑check ran here; treat as "needs a build to verify".
- **All external integrations are mocks** — payments, WhatsApp, e‑signature, email, monday, OCR.
  Signing is simulated via `POST /signatures/{id}/mark-signed`, not a real provider webhook.
- **Local storage only** — no S3/GCS, no auth‑gated media serving route yet; uploaded files are
  stored on the app filesystem (not persisted across container rebuilds unless volume‑mounted).
- **`public_site_url`** must be set correctly per environment for QR links to point at the live site.

---

## 7. Pick up from here — prioritized next steps / המשך מכאן

### Immediate (engineering)
1. **Build & type‑check the frontend** (`cd frontend && npm install && npm run build`); fix any
   type drift against the API contract; wire the new admin screens to navigation.
2. Add an **auth‑gated media download route** (currently `url_for` returns `/media/<key>` with no
   serving/authorization endpoint) so sensitive documents stay protected.
3. End‑to‑end smoke test of the QR -> public form -> case‑file -> signature -> document flow.

### Phase‑0 blockers (product/legal decisions required before real launch)
1. **Digital signature format with the authorities** — confirm the exact accepted signed‑document
   format/standard for ownership transfer to municipalities, then choose & integrate a real
   e‑signature provider behind the existing `SignatureProvider` adapter.
2. **WhatsApp / Meta BSP decision** — pick a Business Solution Provider (or Cloud API) for the
   `MessagingProvider` adapter; defines templates, opt‑in, and costs.
3. **Payment gateway** — choose the Israeli gateway/PSP and implement the `PaymentProvider` adapter
   (subscriptions/monthly charges already modeled).
4. **7000‑vs‑7200 pricing rule** — clarify and encode the surrender pricing logic (which fee applies
   when), then enforce it in the surrender service + tests.
5. **DPA / privacy** — finalize the Data Processing Agreement and data‑retention/consent handling
   (consent notice UI exists; backend retention policy still TBD).

---

_Backend test status at handoff: **59 passed** (`pytest`)._
