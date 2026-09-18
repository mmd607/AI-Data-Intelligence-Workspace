# Deployment

**Marker Legend:** ✅ CONFIRMED · 🟡 ASSUMED · ❓ OPEN QUESTION · 🔴 BLOCKED

Created in Phase 08. Documents local (non-Docker) startup — already in `README.md` — and
the containerized, production-oriented path added this phase. This is **local/self-hosted
deployment documentation**, not a public cloud hosting guide: an actual public deployment
target was never selected and remains explicitly out of scope
(`PRODUCT_SPEC.md` "Non-Goals"; `decisions/DECISIONS_LOG.md` ADR-017 "Alternatives
Considered").

---

## 1. Prerequisites

- Docker Engine with the `docker compose` plugin (Docker Desktop on Windows/macOS, or
  `docker` + `docker-compose-plugin` on Linux).
- No Python or Node.js installation required for the Docker path — both are bundled inside
  the images.

## 2. Quick Start

```bash
git clone <this-repository>
cd AI-Data-Intelligence-Workspace
docker compose up --build
```

- Frontend: `http://localhost:8080`
- Backend: `http://localhost:8000` (`/health`, `/docs`)

No `.env` file is required — every value has a working default (see `.env.example`).

## 3. Configuration

Copy `.env.example` to `.env` in the repo root only if you need to change a default —
`docker compose` reads it automatically. Common overrides:

| Variable | Default | Purpose |
|---|---|---|
| `BACKEND_PORT` | `8000` | Host port the backend is published on. |
| `FRONTEND_PORT` | `8080` | Host port the frontend is published on. |
| `APP_AI_PROVIDER` | `offline` | `offline` (zero config, zero network) / `anthropic` (real LLM, needs `APP_AI_API_KEY`) / `disabled`. |
| `APP_AI_API_KEY` | *(empty)* | Only needed if `APP_AI_PROVIDER=anthropic`. Never commit a real key. |
| `APP_MAX_UPLOAD_SIZE_BYTES` | `52428800` (50 MB) | Upload size ceiling. |
| `VITE_API_BASE_URL` | `http://localhost:8000` | **Build-time only** — where the browser reaches the backend. Must be updated if you change `BACKEND_PORT` (see §5). |

Full variable-by-variable documentation: `backend/.env.example`, `frontend/.env.example`,
root `.env.example`.

## 4. Health Checks

Both containers define a Docker `HEALTHCHECK`:

- **Backend:** `GET /health` returns `{"status": "ok", ...}` — no dependency on external
  services, since there are none (filesystem storage only, per ADR-005).
- **Frontend:** nginx responds on `/`.

`docker compose ps` shows both statuses; `frontend` only starts once `backend` reports
`healthy` (`depends_on: condition: service_healthy` in `docker-compose.yml`).

## 5. A Static Frontend's One Real Constraint

The frontend is a pre-built static SPA — there is no server-side process to read an
environment variable from at container start. `VITE_API_BASE_URL` is baked into the
JavaScript bundle at **image build time** (`docker compose build` / `up --build`). If you
change `BACKEND_PORT`, you must also set `VITE_API_BASE_URL` to match and rebuild the
frontend image — changing it in a running container's environment does nothing.

## 6. Data Persistence

Uploaded datasets live in the named Docker volume `backend-data` (mounted at `/app/data`
in the backend container), not a host bind mount. They survive `docker compose down` and
`up`, but are removed by `docker compose down -v`. There is no database and no migration
step — consistent with the non-Docker local-dev storage model (`ARCHITECTURE.md`, ADR-005).

## 7. Local (Non-Docker) Development

Unchanged from Phases 01–07 — see the root `README.md` "Local Development" section. Docker
is the release/production-like path; running the two processes directly is still the
fastest local development loop (hot reload on both sides).

## 8. Verification Performed

- ✅ `docker compose config` — not run locally (Docker unavailable in the agent's
  environment this phase; see `SECURITY_NOTES.md` §4 and `decisions/DECISIONS_LOG.md`
  ADR-017 for the full accounting).
- ✅ Backend smoke-tested locally under the exact non-reload `uvicorn app.main:app --host
  0.0.0.0 --port 8000` invocation the Dockerfile's `CMD` uses — `/health` returned 200,
  `/docs` returned 200.
- ✅ `npm run build` produces `frontend/dist/` correctly (code-split, ~215 KB main bundle +
  a lazily-loaded ~1.05 MB Universe/Three.js chunk, per Phase 07's own measurement).
- 🟡 The `docker` job in `.github/workflows/ci.yml` performs the first actual `docker
  compose up --build` + health-check + HTTP verification, on GitHub Actions' Docker-
  equipped runners — check that CI run before treating the containerized path as fully
  verified end-to-end.

## 9. Non-Goals (Explicit)

- A public cloud hosting/deployment target (AWS/GCP/Azure/Vercel/etc.) was never selected
  and is not provided here — out of scope per `PRODUCT_SPEC.md`.
- TLS termination, a reverse proxy, autoscaling, and multi-instance orchestration are not
  addressed — this is a local-first, single-user, self-hosted tool.

---
*Related: [SECURITY_NOTES.md](SECURITY_NOTES.md) ·
[decisions/DECISIONS_LOG.md](decisions/DECISIONS_LOG.md) ADR-009, ADR-017 ·
[../README.md](../README.md) · [../docker-compose.yml](../docker-compose.yml)*
