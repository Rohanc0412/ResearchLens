from researchlens.shared.errors.base import ResearchLensError


class ValidationError(ResearchLensError):
    code = "validation_error"


class ConflictError(ResearchLensError):
    code = "conflict"


class NotFoundError(ResearchLensError):
    code = "not_found"


class AuthenticationError(ResearchLensError):
    code = "authentication_error"


class ForbiddenError(ResearchLensError):
    code = "forbidden"


class InfrastructureError(ResearchLensError):
    code = "infrastructure_error"
