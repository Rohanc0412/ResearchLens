# Configuration

Configuration documentation for typed backend settings lives in this folder. The current settings surface is grouped by subsystem in [settings.md](settings.md), and `.env.example` mirrors the active environment variable names used by `researchlens.shared.config`.

Runtime secrets are expected to be injected through Doppler-backed environment execution. Application code still reads plain environment variables only.
