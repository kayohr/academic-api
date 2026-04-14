from fastapi import HTTPException, status


class AppException(HTTPException):
    def __init__(self, status_code: int, code: str, message: str):
        super().__init__(status_code=status_code, detail={"error": code, "message": message})


class NotFoundError(AppException):
    def __init__(self, resource: str = "Resource"):
        super().__init__(404, "NOT_FOUND", f"{resource} not found")


class UnauthorizedError(AppException):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(401, "UNAUTHORIZED", message)


class ForbiddenError(AppException):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(403, "FORBIDDEN", message)


class ConflictError(AppException):
    def __init__(self, message: str):
        super().__init__(409, "CONFLICT", message)


class ValidationError(AppException):
    def __init__(self, message: str):
        super().__init__(422, "VALIDATION_ERROR", message)
