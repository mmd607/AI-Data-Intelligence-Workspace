# Security Notes

**Marker Legend:** ✅ CONFIRMED · 🟡 ASSUMED · ❓ OPEN QUESTION · 🔴 BLOCKED

Created in Phase 08 (`01_PHASES/PHASE_08_TESTING_DOCKER_DEPLOYMENT/PHASE_PROMPT.md`
"Documentation Requirements"). Records the actual security review performed on the
application as it exists after Phases 01–07, what was found, what was fixed, and what
remains a documented, conscious limitation. Every claim below is backed by a real test or
an explicit manual check — nothing here is asserted without one.

---

## 1. Threat Model

This is a **local-first, single-user tool**, not a multi-tenant hosted service.
`PRODUCT_SPEC.md` "Non-Goals" excludes authentication, authorization, and multi-user
isolation from scope — anyone who can reach the backend process can use the whole API.
The realistic threats this review targets are:

1. A malicious or malformed **uploaded file** crashing the backend or corrupting storage.
2. A malicious **URL/path parameter** (dataset id, column name) reaching the filesystem.
3. **Prompt injection** via dataset content reaching the AI provider as an instruction.
4. **Secret leakage** — API keys, internal paths, stack traces — into responses, logs, or
   the frontend bundle.
5. Standard web hygiene — CORS, XSS, unsafe HTML rendering.

Out of scope by design (see `PRODUCT_SPEC.md`): auth/authorization, multi-tenant data
isolation, rate limiting against a hostile network client, DDoS protection.

## 2. Findings & Fixes

### 2.1 ✅ FIXED — Dataset-ID path traversal (`app/ingestion/storage.py`)

**Severity:** High (arbitrary-file-shaped read primitive, narrow in practice — see below —
but structurally real).

`dataset_id` is server-generated on upload (`uuid4()`), but every *read* endpoint
(`GET /datasets/{id}`, and every nested profiling/ML/AI route) takes it straight from the
URL path and previously joined it directly onto the storage base directory with no format
check. Because `pathlib` doesn't collapse `..` itself but the OS does at the syscall level,
and backslash is not a URL path separator (so `..\some-dir` reaches a single-segment route
parameter unmodified, unlike a literal `/..`), this was a genuine path-traversal primitive —
confirmed empirically with `TestClient` against a real target directory before the fix, and
disproven the same way after it. Practical exploitability was narrow (the storage layout
requires an exact `metadata.json`/`original.csv` filename inside whatever directory is
traversed to), but "narrow" is not "safe," and defense-in-depth doesn't get to assume the
narrow case never lines up.

**Fix:** `StorageService._dataset_dir` now rejects any id containing anything other than
letters, digits, hyphens, or underscores *before* it is ever joined into a filesystem path,
treating a rejected id exactly like "dataset not found." Full detail and alternatives
considered: `decisions/DECISIONS_LOG.md` ADR-018. Regression tests:
`backend/tests/test_datasets_api.py::TestDatasetIdTraversal`.

### 2.2 ✅ CONFIRMED SAFE — Upload filename never used for storage paths

The client-supplied upload filename is sanitized (`ingestion/validation.py:
sanitize_filename`) for *display only* — storage always uses the server-generated
`dataset_id`, never the filename, so a filename like `../../../etc/passwd.csv` cannot
influence where the file is written. Verified by
`tests/test_datasets_api.py::TestPathTraversalFilename` (pre-existing, Phase 02).

### 2.3 ✅ CONFIRMED SAFE — No secrets in frontend code or responses

- `frontend/src/vite-env.d.ts`/`api-client/http.ts` expose exactly one env var,
  `VITE_API_BASE_URL` — a public backend URL, not a secret. Grepped the whole frontend
  source tree for `dangerouslySetInnerHTML`, `eval(`, `innerHTML`, `document.write`: none
  found (`AIExplanationBlock.tsx` explicitly documents rendering AI text as plain text
  only, for exactly this reason).
- The backend's `ai_api_key` field is a Pydantic `SecretStr` (`app/config.py`) — never
  logged, never serialized into a response. `GET /api/v1/ai/status` reports availability
  and provider name only, never the key itself (`tests/test_ai_security.py`,
  pre-existing).
- The global exception handler (`app/main.py: unhandled_exception_handler`) logs the full
  exception server-side but always returns the same generic `{"error": {"code":
  "internal_error", "message": "An unexpected error occurred."}}` body — no stack trace,
  file path, or exception type ever reaches the client. Every domain-specific error
  handler (`IngestionError`/`ProfilingError`/`MLError`/`AIError`) returns a structured
  `{code, message}` body with no internal detail beyond what the message was deliberately
  written to say.

### 2.4 ✅ CONFIRMED SAFE — Prompt-injection defense

`app/ai/security.py` builds a system-instruction/user-prompt split that explicitly labels
all dataset-derived content as untrusted data, instructs the model to never treat it as a
command, and to never reveal secrets regardless of what the evidence or the request asks.
More importantly, this is **not just a prompt-level ask** — `tests/test_ai_grounding.py`
proves structurally that a fabricating/adversarial provider (a `FakeProvider` returning
deliberately wrong numbers or injected instructions) can never alter the response's
`computed` field, which is built directly from real evidence regardless of what the
provider returns. `tests/test_ai_security.py` additionally proves injection payloads in
column names/cell values reach the provider only as inert data.

### 2.5 ✅ CONFIRMED SAFE — CORS

`app/main.py` configures `CORSMiddleware` from `settings.cors_origin_list`, an explicit
comma-separated allowlist (`.env`'s `APP_CORS_ORIGINS`) — never a `*` wildcard alongside
`allow_credentials=True` (which browsers reject anyway, but the config never attempts it).
Default covers the Vite dev server origins; the Docker Compose default additionally covers
the containerized frontend's published port (`docker-compose.yml`).

### 2.6 ✅ CONFIRMED SAFE — Upload validation / malformed-input handling

Already covered by the existing (pre-Phase-08) test suite, re-verified as part of this
review, not re-litigated: empty files (`empty_file`, 400), oversized files
(`file_too_large`, 413, configurable via `APP_MAX_UPLOAD_SIZE_BYTES`), non-`.csv` extensions
(`unsupported_file_type`, 400), malformed CSV content (`malformed_csv`, 400), and a rejected
upload persists nothing to disk (`TestUploadErrors::test_nothing_is_persisted_after_a_
rejected_upload`). Every failure returns a structured 4xx body, never a 500 or a stack
trace.

### 2.7 🟡 ASSUMED, DOCUMENTED — Dependency-pin drift is a reproducibility risk, not a code bug

While establishing this phase's baseline, the ambient/global Python environment on the
development machine had `pandas 3.0.5` installed (vs. the pinned `pandas==2.2.3` in
`requirements.txt`), which broke 3 tests due to a real behavioral change in pandas 3.0's
default string dtype. Re-running against the project's own `.venv` (correctly pinned)
passed all 342 tests — **this was environment drift, not an application bug**, but it is
exactly the class of problem Docker (§30) exists to eliminate: the backend image installs
only from the pinned `requirements.txt`, so this drift class cannot occur inside the
container regardless of what's on the host.

## 3. Docker/Container Security

- Both images run as **non-root** (`app` user for the backend; `nginx-unprivileged`'s
  built-in non-root user for the frontend).
- Backend image: `python:3.12-slim`, two-stage (build tools never ship in the runtime
  image); dependencies installed *only* from the pinned `requirements.txt` (§2.7).
- Frontend image: static assets only in the runtime stage — no Node.js, no dev server, no
  source maps of concern beyond what Vite's default production build already omits.
- No secrets baked into either image; `APP_AI_API_KEY` is supplied at container **runtime**
  via `docker-compose.yml`'s `environment:` (from the host's `.env`/shell, never from a
  file copied into the image).
- `.dockerignore` in both `backend/` and `frontend/` excludes `.env*` (except `.env.example`),
  `.git/`, virtualenvs/`node_modules/`, and caches from the build context.

## 4. Known Limitations (honestly recorded, not release blockers)

- **Docker build/runtime not locally verified in the agent's environment** — Docker is not
  installed here. See `decisions/DECISIONS_LOG.md` ADR-017 for the full accounting and what
  substitute verification was actually performed. The `docker` job in
  `.github/workflows/ci.yml` performs the real build+runtime verification on every push.
- **No authentication/authorization** — by design, out of scope (`PRODUCT_SPEC.md`
  "Non-Goals"); anyone who can reach the backend can use it. Acceptable for a local-first,
  single-user tool; would need to be revisited before any multi-user or public deployment.
- **No rate limiting** — a hostile network client could still send an unbounded number of
  requests. Acceptable for the same reason as above; not addressed this phase since it is a
  multi-user/public-deployment concern outside current scope.
- **File-size limit is enforced after the full body is read into memory** (`await
  file.read()` in `app/api/datasets.py`, then `validate_size`), not streamed — bounded in
  practice by `APP_MAX_UPLOAD_SIZE_BYTES` (default 50 MB), but a very large
  `Content-Length`-mismatched request could momentarily consume more memory than the
  limit before rejection. Acceptable at the current 50 MB default for a local-first tool;
  would need streaming validation before raising that default significantly.

---
*Related: [decisions/DECISIONS_LOG.md](decisions/DECISIONS_LOG.md) ADR-017, ADR-018 ·
[TESTING_STRATEGY.md](TESTING_STRATEGY.md) · [DEPLOYMENT.md](DEPLOYMENT.md) ·
[../01_PHASES/PHASE_08_TESTING_DOCKER_DEPLOYMENT/PHASE_PROMPT.md](../01_PHASES/PHASE_08_TESTING_DOCKER_DEPLOYMENT/PHASE_PROMPT.md)*
