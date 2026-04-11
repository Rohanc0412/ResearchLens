# Coding Rules

## Naming

Use business-first, purpose-first names. Avoid vague names such as `utils`, `helpers`, `manager`, `common`, or ambiguous `service`.

## File size

- Python target under 250 lines, hard cap 300.
- TS and TSX target under 220 lines, hard cap 280.
- Functions target under 40 logical lines, hard cap 60.
- React components target under 120 lines.

Generated code, migrations, fixtures, and snapshots are the main exemptions.

## No dumping grounds

Do not create generic catch-all files or folders. Split responsibilities before a file becomes a mixed-purpose bucket.

## Packaging

- Use installable packages with `src/` layout.
- Do not use `PYTHONPATH`, `sys.path.insert`, or folder-dependent imports.
- Use absolute imports from installed package roots where relevant.
- Pytest, Alembic, API startup, worker startup, Docker, and CI must run from installed-package context.

## Async

Use async when I/O dominates, such as database access, HTTP provider calls, SSE, queue work, storage access, and fan-out coordination. Do not use async as a style choice when work is CPU-bound or purely local.

## Testing

Every phase should add or update tests when behavior changes. The repository supports smoke, unit, integration, contract, end-to-end, architecture, regression, and targeted property-style tests where they fit the changed behavior.

## Documentation

Update architecture docs when structure changes, configuration docs when settings change, ADRs when major design choices are made, and the phase completion report before handoff.

## Config

- Use `pydantic-settings` under `researchlens.shared.config`.
- Keep settings grouped by subsystem.
- Validate incompatible startup combinations explicitly.
- Do not scatter direct environment access across the codebase.
