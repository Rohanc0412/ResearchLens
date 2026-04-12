# Compose

The development compose file is a local convenience scaffold with Postgres plus installed-package API, worker, and test execution. It remains intentionally lightweight and is not a production topology.

Secrets are expected to arrive from Doppler-backed runtime injection, not from checked-in `.env` files. Run compose from a Doppler context so API and worker containers receive the same env surface as local installed-package commands:

```bash
doppler run -- docker compose -f infra/compose/docker-compose.dev.yml up --build
```

`DATABASE_URL`, `LLM_API_KEY`, and `EMBEDDINGS_API_KEY` are read from the process environment passed into compose. `.env.example` remains a shape reference only.
