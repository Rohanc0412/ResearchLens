# Compose

The development compose file is a local convenience scaffold with Postgres plus installed-package API, worker, web, and test execution. It remains intentionally lightweight and is not a production topology.

Compose is Doppler-first. Checked-in files do not provide runtime authority for local containers.

If Doppler and `.env.example` disagree, Doppler wins.

Use a compose-specific Doppler config, for example `compose-dev`, so container networking values stay correct:

```bash
doppler run --config compose-dev -- docker compose -f infra/compose/docker-compose.dev.yml up --build
```

Required compose Doppler values:

```bash
APP_ENVIRONMENT=development
APP_API_HOST=0.0.0.0
APP_API_PORT=8000
APP_CORS_ALLOWED_ORIGINS=http://127.0.0.1:4173,http://localhost:4173
AUTH_REFRESH_COOKIE_SECURE=false
DATABASE_URL=postgresql+psycopg://researchlens:researchlens@postgres:5432/researchlens
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Expected ports and URLs:

- API: `http://127.0.0.1:8000`
- Web: `http://127.0.0.1:4173`
- Postgres: `localhost:5432`

The compose file passes runtime settings through from the Doppler process environment. It does not silently rewrite `DATABASE_URL` or host binding values inside YAML.
