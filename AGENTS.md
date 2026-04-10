# AGENTS.md

This file contains repo-wide engineering rules only.
Phase-specific scope, deliverables, and handoff requirements should come from the active prompt.

## Source of truth

- Follow the repository docs and the current task prompt.
- If prompt instructions conflict with repo docs, resolve the conflict explicitly in the same change instead of inventing parallel rules.
- Do not create new rule systems in code comments, ad hoc notes, or local conventions.

## Repository rules

1. The cloned repository root is the project root.
   - Never create a nested `ResearchLens/` directory.
   - Create files and folders directly under the existing repo root.

2. Treat the old repository as a requirements reference only.
   - Do not use it as a code template.
   - Do not port large files or old structure by default.

3. Keep the backend installable.
   - Use `src/` layout and installed-package imports.
   - Never use `PYTHONPATH`, `sys.path.insert`, or cwd-dependent import tricks.

## Architecture rules

4. Preserve modular boundaries.
   - Backend modules use `domain`, `application`, `infrastructure`, and `presentation`.
   - Use `orchestration` only when a module truly owns staged execution, and keep it thin.
   - Route handlers stay thin.
   - Repositories stay narrow.
   - Domain code must not depend on web frameworks, ORM models, or provider SDKs.
   - Infrastructure must not contain business policy.

5. Keep shared code generic.
   - Do not place business-specific logic in shared code.
   - If code clearly belongs to a module, keep it in that module.

6. Keep frontend structure disciplined.
   - Pages compose widgets.
   - Widgets compose features and entities.
   - Features own user actions.
   - Entities own domain presentation.
   - Shared frontend code stays generic.
   - Prefer typed or generated API integration over ad hoc transport code.

## Code quality rules

7. Keep names clear and specific.
   - Use purpose-first names.
   - Avoid vague names like `utils`, `helpers`, `manager`, `common`, or unclear `service`.

8. Keep files focused.
   - Split files before they become oversized or mixed-responsibility.
   - Do not let one file become the hidden center of a module.

9. Make behavior explicit.
   - Do not add silent fallbacks.
   - Do not hide important logic inside routes, repositories, or shared helpers.

10. Keep public contracts explicit.
    - Request and response models must be strict and intentional.
    - Do not introduce inconsistent field names for the same concept across endpoints.

11. Keep changes aligned with existing standards.
    - Follow current coding, naming, testing, and architecture patterns already established in the repo.
    - Extend existing patterns cleanly instead of introducing competing ones.

## Security rules

12. Do not log secrets or sensitive values.
    - Never log passwords, raw tokens, reset tokens, secrets, or full credential material.
    - Prefer safe, human-readable operational logs.

## Data rules

13. Keep schema changes explicit.
    - Database changes must go through migrations.
    - Do not rely on implicit schema drift or manual local-only fixes.

## Validation rules

14. Update tests with behavior changes.
    - Add or update the appropriate level of tests when behavior changes.

15. Update docs with contract or structure changes.
    - Update relevant docs in the same work when structure, contracts, configuration, or developer-facing behavior changes.

## Decision rule

If speed conflicts with correctness, modularity, or clean boundaries, choose correctness and clean boundaries.
