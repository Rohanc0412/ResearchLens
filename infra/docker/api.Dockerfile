FROM python:3.12-slim

WORKDIR /workspace

RUN pip install uv

COPY . .

RUN uv sync --all-packages --group dev

CMD ["uv", "run", "--package", "researchlens-api", "uvicorn", "researchlens_api.main:app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
