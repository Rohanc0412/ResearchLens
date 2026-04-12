install:
	python -m uv sync --all-packages --group dev
	corepack pnpm install

lint:
	python -m uv run --package researchlens-backend ruff check .
	corepack pnpm lint

typecheck:
	python -m uv run --package researchlens-backend mypy apps/api/src apps/worker/src packages/backend/src packages/backend/tests
	corepack pnpm typecheck

test:
	python -m uv run --package researchlens-backend pytest packages/backend/tests
	corepack pnpm test

architecture:
	python -m uv run --package researchlens-backend lint-imports --config .importlinter

db-upgrade:
	python -m uv run --package researchlens-backend alembic -c packages/backend/alembic.ini upgrade head

build:
	corepack pnpm build

format:
	python -m uv run --package researchlens-backend ruff format .
	corepack pnpm format

clean:
	corepack pnpm clean

dev-api:
	python -m uv run --package researchlens-api python -m researchlens_api.main

dev-worker:
	python -m uv run --package researchlens-worker python -m researchlens_worker.main

dev-web:
	corepack pnpm --filter web dev

doppler-dev-api:
	doppler run -- python -m uv run --package researchlens-api python -m researchlens_api.main

doppler-dev-worker:
	doppler run -- python -m uv run --package researchlens-worker python -m researchlens_worker.main

doppler-test-backend:
	doppler run -- python -m uv run --package researchlens-backend pytest packages/backend/tests

doppler-db-upgrade:
	doppler run -- python -m uv run --package researchlens-backend alembic -c packages/backend/alembic.ini upgrade head
