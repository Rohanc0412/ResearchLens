install:
	uv sync --all-packages --group dev
	pnpm install

lint:
	uv run ruff check .
	pnpm lint

typecheck:
	uv run mypy .
	pnpm typecheck

test:
	uv run pytest
	pnpm test

build:
	pnpm build

format:
	uv run ruff format .
	pnpm format

clean:
	pnpm clean

dev-api:
	uv run --package researchlens-api uvicorn researchlens_api.main:app --factory --reload --host 127.0.0.1 --port 8000

dev-worker:
	uv run --package researchlens-worker python -m researchlens_worker.main

dev-web:
	pnpm --filter web dev

