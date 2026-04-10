class ResearchLensError(Exception):
    code = "internal_error"
    message = "An unexpected error occurred."

    def __init__(self, message: str | None = None) -> None:
        super().__init__(message or self.message)
        self.message = message or self.message
