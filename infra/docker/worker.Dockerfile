FROM python:3.12-slim

WORKDIR /workspace

RUN pip install uv

COPY . .

RUN uv sync --all-packages --group dev --frozen

CMD ["uv", "run", "--package", "researchlens-worker", "python", "-m", "researchlens_worker.main"]
