# Docker

These Dockerfiles remain development-oriented. They install and execute workspace packages through `uv` instead of relying on path hacks or requirements files, matching the backend installed-package boundary used by local commands and CI.

Secrets are not baked into images. Run containers through Doppler-backed env injection and pass the resulting environment into `docker run` or `docker compose`.
