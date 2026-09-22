# Security Policy

> **Status: IMPLEMENTED for the backend (development configuration). Not audited for production.**
> Items marked ✅ exist and are covered by tests or were verified live; ⬜ are open. The frontend and
> deployment platform are not built yet.

## Implemented controls

| Area | Control | Status |
|---|---|---|
| Secrets | All configuration from environment variables (`backend/app/core/config.py`); `DATABASE_URL` has **no default**; `.env` git-ignored; `.env.example` holds placeholders only; the local DB password is randomly generated | ✅ |
| NASA key | Not needed — the JPL SBDB/CAD APIs are keyless, so no key is stored anywhere | ✅ |
| CORS | Origins from `CORS_ORIGINS`; methods GET/POST; no credentials; `*` is **refused at startup in production** (`MODEL_ENV=production`); tested allowed vs disallowed origin | ✅ |
| Input validation | Pydantic on every input: types, ranges, `extra="forbid"` on prediction features, `per_page ≤ 100`, `search ≤ 100`, integer path ids bounded to int64 | ✅ |
| SQL injection | SQLAlchemy ORM only; `sort` is a whitelist (400 otherwise); `LIKE` search uses `autoescape` (`%`/`_` literal); tested with `id; DROP TABLE …` | ✅ |
| Error handling | Generic messages only (`Internal server error`, `Database unavailable`, `Model artifact unavailable`); details in server logs; 422 bodies do not echo submitted values; tested that no path/secret text leaks | ✅ |
| Logging | Structured JSON to stdout; request **path only** (no query string), status, duration, request id; no secrets, keys or bodies logged | ✅ |
| Security headers | `X-Content-Type-Options`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, `Cache-Control: no-store` on every response | ✅ |
| Rate limiting | In-process sliding window per client IP (default 120/min, `RATE_LIMIT_PER_MINUTE`; `/api/health` exempt; 429 + `Retry-After`). **Per process** — not shared across workers/replicas and not a substitute for edge limiting. Behind a proxy run uvicorn with `--proxy-headers` and `FORWARDED_ALLOW_IPS` (the Dockerfile enables `--proxy-headers`) | ✅ (basic) |
| Outbound calls | JPL client: timeouts, bounded retries with backoff, ≥ 1 s between requests, 24 h cache — no uncontrolled polling | ✅ |
| Containers | Slim base image, **non-root user** (`neoguard`, verified), DB port bound to `127.0.0.1`, `.dockerignore` excludes `.env`, data, tests | ✅ |
| Model loading | Artifacts are loaded with `joblib` (**pickle**): only from the trusted `MODEL_DIR`; registry paths that resolve outside `MODEL_DIR` are refused (tested) | ✅ |
| Prediction storage | Anonymous predictions are not stored; stored ones require a valid `neo_id` (bounds table growth from unauthenticated calls) | ✅ |

## Known gaps

* ⬜ **No authentication/authorisation.** All endpoints, including `POST /api/predict`, are public.
  Acceptable for a read-only research API; add auth before exposing anything that writes or is costly.
* ✅ **Dependency audit (Phase 5, 2026-09-22).** `pip-audit`: no known vulnerabilities. `npm audit
  --omit=dev`: 2 moderate `react-router-dom` advisories (open redirect via backslash in
  `<Link>`/`useNavigate`; arbitrary constructor injection in SSR-hydration `deserializeErrors()`).
  **Decision: not upgrading.** Both are not exploitable here: every `Link to=`/`navigate()` call in
  `frontend/src` targets a hardcoded internal route or an `encodeURIComponent`-escaped query
  parameter (`frontend/src/components/layout/CommandHeader.tsx`,
  `frontend/src/components/dashboard/CloseApproachMatrix.tsx`) — none passes a raw, attacker-controlled
  path capable of a backslash-based host escape — and the SSR advisory does not apply to this
  client-only Vite SPA (confirmed: no SSR build target). The fix requires a v6→v7 major version bump
  of `react-router-dom`, which is a breaking change out of proportion to non-exploitable advisories;
  revisit if the app ever adds SSR or user-controlled redirect targets.
* ⬜ **HTTPS** is not handled by the app; terminate TLS at the platform/proxy.
* ⬜ Rate limiter is per-process (above). Prediction with explanations costs ~1.5 s on first use
  of a model (load + SHAP explainer), then milliseconds.
* ⬜ Pickle risk: never point `MODEL_DIR` at untrusted storage.
* ⬜ No penetration test / external review.

## Production checklist

- [x] CORS configured (env-driven, wildcard rejected in production)
- [x] Rate limiting enabled (basic, in-process)
- [ ] HTTPS enforced (platform)
- [x] Secrets in environment variables
- [x] Dependencies audited (`pip-audit` clean; `npm audit` — 2 moderate advisories reviewed and not upgraded, see above)
- [x] Error messages sanitised
- [x] Logging reviewed (no secrets, no query strings)
- [x] Container hardened (non-root, slim); [ ] image scanning not run

## Reporting

There is no dedicated security contact yet; raise issues with the project owner.
