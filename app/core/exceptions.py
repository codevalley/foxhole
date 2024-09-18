from fastapi import HTTPException
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR, HTTP_401_UNAUTHORIZED


class AuthenticationError(HTTPException):
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(status_code=HTTP_401_UNAUTHORIZED, detail=detail)


class DatabaseOperationError(HTTPException):
    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(status_code=HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)
