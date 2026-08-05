from asyncio import exceptions

from fastapi import FastAPI, HTTPException, Request, status, Response
from fastapi.exceptions import ResponseValidationError
from fastapi.responses import JSONResponse


class FastShipError(Exception):
    """Base exception for all exceptions is fastship api"""
    status = status.HTTP_400_BAD_REQUEST

class EntityNotFound(FastShipError):
    """Entity not found in database"""
    status = status.HTTP_404_NOT_FOUND

class BadPassword(FastShipError):
    """Password is not strong enough or invalid"""
    status = status.HTTP_400_BAD_REQUEST

class ClientNotAuthorized(FastShipError):
    """Client is not authorized to perform the action"""
    status = status.HTTP_403_FORBIDDEN

class ClientNotVerified(FastShipError):
    """Client is not verified"""
    status = status.HTTP_403_FORBIDDEN

class NothingToUpdate(FastShipError):
    """No data provided to update"""
    status = status.HTTP_400_BAD_REQUEST

class BadCredentials(FastShipError):
    """User email or password is incorrect"""
    status = status.HTTP_401_UNAUTHORIZED

class InvalidToken(FastShipError):
    """Access token is invalid or expired"""
    status = status.HTTP_401_UNAUTHORIZED

class DeliveryPartnerNotAvailable(FastShipError):
    """Delivery Partner/s do not serve this location"""
    status = status.HTTP_404_NOT_FOUND

class DeliveryPartnerCapacityExceeded(FastShipError):
    """Delivery partner has reached their max handeling capacity"""
    status = status.HTTP_409_CONFLICT

def _get_handler(status: int, detail: str):
    def handler(request: Request, exception: Exception) -> Response:
        from rich import print, panel
        print(panel.Panel(f"Handled: {exception.__class__.__name__}"))
        raise HTTPException(
            status_code=status,
            detail=detail,
        )
    return handler

def add_exception_handlers(app: FastAPI):
    exception_classes = FastShipError.__subclasses__()
    for exception_class in exception_classes:
        app.add_exception_handler(
            exception_class,
            _get_handler(
                status = exception_class.status, 
                detail = exception_class.__doc__,
        ),
    )

    @app.exception_handler(status.HTTP_500_INTERNAL_SERVER_ERROR)
    def internal_server_error_handler(request, exception):
        return JSONResponse(
            content = {"detail": "Something went wrong ..."},
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR,
            headers = {
                "X-Error" : f"{exceptions}",
            }
        )
