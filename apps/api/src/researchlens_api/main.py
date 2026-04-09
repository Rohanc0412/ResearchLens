import uvicorn


def main() -> None:
    from researchlens.shared.config import get_settings

    settings = get_settings()
    uvicorn.run(
        "researchlens_api.create_app:create_app",
        factory=True,
        host=settings.app.api_host,
        port=settings.app.api_port,
        reload=False,
    )


if __name__ == "__main__":
    main()
