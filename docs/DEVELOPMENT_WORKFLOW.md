# Development Workflow

## Phases

### Phase 1 — Foundation (Antigravity)
- Repository structure
- Documentation and contracts
- Agent handoff instructions
- Data, ML, API, and frontend policies

### Phase 2 — Backend + ML (Claude Code)
- Data ingestion from NASA/JPL
- Validation, preprocessing, feature engineering
- ML training, evaluation, explainability
- FastAPI inference API
- PostgreSQL integration
- Unit and integration tests

### Phase 3 — Frontend (Antigravity)
- Stitch design system
- React + Vite + Tailwind implementation
- Apple-inspired design principles
- Dashboard, explorer, prediction UI

### Phase 4 — Verification (Claude Code)
- End-to-end testing
- Integration testing
- Bug fixing
- Performance verification
- Security review

### Phase 5 — Deployment (Antigravity)
- Final Git commit
- Deployment preparation (Vercel, Render)
- Production configuration
- Documentation finalisation

## Rules
- No agent should overwrite another agent's work without checking the current state first.
- Every agent must read `docs/HANDOFF.md` before starting.
- Every agent must update `docs/HANDOFF.md` when finishing.
- Tests must pass before declaring a phase complete.
- Documentation must stay consistent with implementation.
