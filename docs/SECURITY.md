# Security Policy

> **Status: PLANNED — NOT IMPLEMENTED**

## Environment Variables

- All secrets must be stored in environment variables.
- `.env` files must never be committed to version control.
- `.env.example` contains only placeholder keys with no real values.

## Secret Management

- API keys (e.g., NASA API key) must come from environment variables.
- Database credentials must come from environment variables.
- No hardcoded secrets in source code.

## API Authentication

- TBD — authentication strategy will be decided during implementation.
- At minimum, rate limiting must be applied to public endpoints.

## CORS

- CORS origins must be configurable via environment variables (`CORS_ORIGINS`).
- Default to restrictive origins in production.

## Rate Limiting

- Public API endpoints should implement rate limiting.
- NASA API calls must respect NASA's rate limits.

## Input Validation

- All API inputs must be validated (type, range, format).
- Use Pydantic models (FastAPI) for request validation.

## SQL Injection Prevention

- Use parameterised queries or an ORM (SQLAlchemy).
- Never construct SQL strings from user input.

## XSS Prevention

- React's default JSX escaping handles most cases.
- Never use `dangerouslySetInnerHTML` without sanitisation.

## Dependency Security

- Pin dependency versions.
- Regularly audit dependencies for known vulnerabilities.
- Use `pip audit` or equivalent for Python; `npm audit` for Node.

## Container Security

- Use minimal base images.
- Do not run containers as root.
- Do not include unnecessary tools in production images.

## Logging

- Never log secrets, API keys, or passwords.
- Log request metadata (method, path, status) without sensitive payloads.

## Error Handling

- Return generic error messages to clients.
- Log detailed errors server-side.
- Never expose stack traces in production.

## Never Commit

```
.env
API keys
Tokens
Passwords
Private credentials
```

## Production Security Checklist

- [ ] CORS configured
- [ ] Rate limiting enabled
- [ ] HTTPS enforced
- [ ] Secrets in environment variables
- [ ] Dependencies audited
- [ ] Error messages sanitised
- [ ] Logging reviewed
- [ ] Container hardened
