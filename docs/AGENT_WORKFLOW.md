# Agent Workflow

## Antigravity

**Responsible for:**
- Repository orchestration
- Project structure
- Documentation
- Frontend orchestration (Stitch + Apple-inspired design)
- Design implementation phase
- Final Git operations
- Deployment preparation
- Commit management

## Claude Code

**Responsible for:**
- Backend implementation (FastAPI)
- ML implementation (training, evaluation, explainability)
- Data pipeline implementation (ingestion, validation, preprocessing, features)
- Database integration (PostgreSQL)
- Testing (unit, integration, ML)
- Verification and debugging
- Backend documentation updates

## Human

**Responsible for:**
- Approving major architectural changes
- API credentials (NASA API key, database credentials)
- External service accounts
- Deployment credentials
- Final scientific interpretation
- Final project acceptance

---

## Agent Handoff Protocol

Every agent must:

1. Inspect existing files before making changes.
2. Read relevant documentation (`docs/` directory).
3. Never assume a blank repository.
4. Never delete working functionality without justification.
5. Update documentation when architecture changes.
6. Keep implementation consistent with API contracts.
7. Run available tests before declaring completion.
8. Record unresolved issues.
9. Never fabricate successful results.

At the end of its work, an agent must update `docs/HANDOFF.md` with:

```
Completed:
Changed:
Tests performed:
Known issues:
Next agent:
Required next actions:
```
