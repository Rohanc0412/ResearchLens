install:
	uv sync --all-packages --group dev
	pnpm install

lint:
	uv run --package researchlens-backend ruff check .
	pnpm lint

typecheck:
	uv run --package researchlens-backend mypy apps/api/src apps/worker/src packages/backend/src packages/backend/tests
	pnpm typecheck

test:
	uv run --package researchlens-backend pytest packages/backend/tests
	pnpm test

architecture:
	uv run --package researchlens-backend lint-imports --config .importlinter

db-upgrade:
	uv run --package researchlens-backend alembic -c packages/backend/alembic.ini upgrade head

build:
	pnpm build

format:
	uv run --package researchlens-backend ruff format .
	pnpm format

clean:
	pnpm clean

dev-api:
	uv run --package researchlens-api python -m researchlens_api.main

dev-worker:
	uv run --package researchlens-worker python -m researchlens_worker.main

dev-web:
	pnpm --filter web dev
