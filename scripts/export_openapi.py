from __future__ import annotations

import argparse
import json
from pathlib import Path

from researchlens_api.create_app import create_app


def main() -> None:
    parser = argparse.ArgumentParser(description="Export the FastAPI OpenAPI schema.")
    parser.add_argument(
        "--output",
        type=Path,
        required=True,
        help="Path to the output JSON file.",
    )
    args = parser.parse_args()

    app = create_app()
    schema = app.openapi()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
