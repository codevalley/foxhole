from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


def setup_error_handlers(app: FastAPI) -> None:
    """
    Sets up global error handlers for the FastAPI application.
    """

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """
        Generic exception handler that returns a 500 Internal Server Error
        for any unhandled exceptions.
        """
        return JSONResponse(
            status_code=500,
            content={"message": "An unexpected error occurred"},
        )

    # Add more specific exception handlers here
