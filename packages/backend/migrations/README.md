# Migrations

Alembic lives here and imports the installed `researchlens` package directly. Migrations load metadata from backend module infrastructure rows and must run from installed-package context without `PYTHONPATH` or cwd-dependent import tricks.
