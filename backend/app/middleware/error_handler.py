from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from app.core.exceptions import BaseAppException
from app.core.logger import logger
from app.schemas.response import ErrorResponse

async def base_app_exception_handler(request: Request, exc: BaseAppException):
    request_id = getattr(request.state, "request_id", "N/A")
    logger.error(f"Application error: {exc.message}", extra={"request_id": request_id})
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            success=False,
            message=exc.message,
            error_code=exc.__class__.__name__,
            details=exc.details
        ).model_dump()
    )

async def validation_exception_handler(request: Request, exc: RequestValidationError):
    request_id = getattr(request.state, "request_id", "N/A")
    logger.warning(f"Validation error: {exc.errors()}", extra={"request_id": request_id})
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            success=False,
            message="Request validation failed",
            error_code="ValidationError",
            details={"errors": exc.errors()}
        ).model_dump()
    )

async def generic_exception_handler(request: Request, exc: Exception):
    request_id = getattr(request.state, "request_id", "N/A")
    logger.critical(f"Unhandled server error: {str(exc)}", exc_info=True, extra={"request_id": request_id})
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            success=False,
            message="An unexpected internal server error occurred",
            error_code="InternalServerError"
        ).model_dump()
    )
