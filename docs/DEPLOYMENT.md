# Deployment

> **Status: NOT IMPLEMENTED — Sections are placeholders for future deployment configuration.**

## Target Platforms (Planned)

| Service | Platform | Status |
|---------|----------|--------|
| Frontend | Vercel | NOT IMPLEMENTED |
| Backend | Render | NOT IMPLEMENTED |
| Database | PostgreSQL provider (TBD) | NOT IMPLEMENTED |

## Frontend

```
Build command: TBD (likely `npm run build`)
Output directory: TBD (likely `dist/`)
Framework: Vite + React
```

## Backend

```
Build command: TBD
Start command: TBD (likely `uvicorn main:app`)
Runtime: Python 3.11+
```

## Database

```
Provider: TBD
Connection string: via DATABASE_URL env var
Migrations: TBD
```

## Environment Variables

See [.env.example](../.env.example) for the list of expected variables.

| Variable | Required | Description |
|----------|----------|-------------|
| NASA_API_KEY | Yes | API key for NASA data access |
| DATABASE_URL | Yes | PostgreSQL connection string |
| MODEL_ENV | No | Environment flag (development/production) |
| CORS_ORIGINS | No | Allowed CORS origins |

## Build Commands

TBD

## Start Commands

TBD

## Health Checks

```
GET /api/health
```

## CORS

Configured via `CORS_ORIGINS` environment variable.

## Production Configuration

TBD — will be determined during the deployment phase.

> Do not claim deployment works until it has been verified with a production smoke test.
