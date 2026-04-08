# AGENTS.md

## Read first

Before making changes, read these in order:

1. `README.md`
2. `docs/codex/phase_workflow.md`
3. `docs/coding_rules.md`
4. `docs/architecture/module-boundaries.md`
5. `docs/architecture/system-overview.md`
6. The latest file in `docs/phase_reports/`

If a task conflicts with these docs, stop and resolve the conflict explicitly in the same change instead of inventing parallel rules.

---

## Hard rules

1. Work only within the active phase.
   - Restate scope, deliverables, out-of-scope items, and dependencies before changing files.
   - Do not implement later-phase work unless it is strictly required to complete the current phase safely.

2. The cloned repository root is the project root.
   - Never create a nested `ResearchLens/` directory.
   - Create all files and folders directly under the existing repo root.

3. Treat the old repository as a requirements reference only.
   - Do not use it as a code template.
   - Do not port large files or old structure by default.

4. Follow current coding standards from the docs.
   - Do not duplicate or invent parallel rules inside code changes.
   - Keep architecture, naming, and testing aligned with `docs/coding_rules.md` and `docs/architecture/module-boundaries.md`.

5. Keep backend packaging installable.
   - Use `src/` layout and installed-package imports.
   - Never use `PYTHONPATH`, `sys.path.insert`, or cwd-dependent import tricks.

6. Preserve modular boundaries.
   - Backend modules use `domain`, `application`, `infrastructure`, and `presentation`.
   - Use `orchestration` only when a module truly owns staged execution, and keep it thin.
   - Route handlers stay thin.
   - Repositories stay narrow.
   - Domain code must not depend on web frameworks, ORM models, or provider SDKs.
   - Infrastructure must not contain business policy.

7. Keep shared code generic.
   - Do not place business-specific logic in shared code.
   - If code clearly belongs to a module, keep it in that module.

8. Keep frontend structure disciplined.
   - Pages compose widgets.
   - Widgets compose features and entities.
   - Features own user actions.
   - Entities own domain presentation.
   - Shared frontend code stays generic.
   - Prefer typed or generated API integration over ad hoc transport code.

9. Keep names and files clear.
   - Use purpose-specific names.
   - Avoid vague names like `utils`, `helpers`, `manager`, `common`, or unclear `service`.
   - Split files before they become mixed-responsibility or oversized.

10. Make behavior explicit.
    - Do not add silent fallbacks.
    - Do not hide important logic inside routes, repositories, or shared helpers.

11. Update tests and docs with the change.
    - If behavior changes, add or update the right level of tests.
    - If structure, contracts, or rules change, update the relevant docs in the same work.

12. End every phase with a handoff.
    - Summarize what changed.
    - List tests added or updated.
    - List docs added or updated.
    - Create or update `docs/phase_reports/phase_[X]_completion.md`.

---

## Decision rule

If speed conflicts with correctness, modularity, or clean boundaries, choose correctness and clean boundaries.
