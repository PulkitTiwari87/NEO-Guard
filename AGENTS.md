# AGENTS.md — Instructions for Future Antigravity Sessions

## Before Starting

1. Inspect the current repository state. Do not assume a blank project.
2. Read `docs/HANDOFF.md` for the latest status.
3. Read `docs/AGENT_WORKFLOW.md` for responsibilities.
4. Read `docs/ARCHITECTURE.md` for the current architecture.

## Rules

- Preserve Claude Code's work. Do not overwrite backend or ML implementations without justification.
- Use Stitch for the frontend design phase.
- Maintain API compatibility with `docs/API_CONTRACT.md`.
- Do not fabricate data, metrics, or scientific claims.
- Do not claim successful deployment without verification.
- Final Git operations must be deliberate and documented.

## Frontend Phase (Phase 3)

- Read `docs/FRONTEND_CONTRACT.md` and `docs/DESIGN_SYSTEM.md`.
- Use Stitch to generate the design system.
- Implement React + Vite + Tailwind frontend.
- Apply Apple-inspired design principles.
- Consume the backend API defined in `docs/API_CONTRACT.md`.
- Test against the running backend.

## Deployment Phase (Phase 5)

- Read `docs/DEPLOYMENT.md`.
- Verify all tests pass.
- Configure Vercel (frontend) and Render (backend).
- Set environment variables.
- Run production smoke test.
- Update `docs/HANDOFF.md` and `docs/CHANGELOG.md`.
- Commit with a clear, descriptive message.

## Handoff

Update `docs/HANDOFF.md` with:
- What was completed
- What changed
- Tests performed
- Known issues
- Next agent and actions
