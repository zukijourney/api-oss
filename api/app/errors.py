import traceback
from dataclasses import dataclass
from typing import Dict, Any, Callable, Awaitable, Type, Optional
from fastapi import FastAPI, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from slowapi.errors import RateLimitExceeded
from .responses import PrettyJSONResponse

@dataclass
class ErrorResponse:
    message: str
    error_type: str
    code: int
    status_code: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            'error': {
                'message': self.message,
                'type': self.error_type,
                'code': self.code
            }
        }

class ExceptionHandler:
    def __init__(self):
        self.handlers: Dict[
            Type[Exception],
            Callable[[Request, Exception], Awaitable[PrettyJSONResponse]]
        ] = {}
        self._register_default_handlers()

    def _register_default_handlers(self) -> None:
        self.handlers.update({
            404: self._handle_not_found,
            405: self._handle_method_not_allowed,
            Exception: self._handle_generic_exception,
            HTTPException: self._handle_http_exception,
            RequestValidationError: self._handle_validation_exception,
            RateLimitExceeded: self._handle_rate_limit_exceeded
        })

    @staticmethod
    def _create_error_response(
        message: str,
        error_type: str = 'invalid_request_error',
        code: int = 400,
        status_code: Optional[int] = None
    ) -> ErrorResponse:
        return ErrorResponse(
            message=message,
            error_type=error_type,
            code=code,
            status_code=status_code or code
        )

    @staticmethod
    def _create_json_response(error_response: ErrorResponse) -> PrettyJSONResponse:
        return PrettyJSONResponse(
            status_code=error_response.status_code,
            content=error_response.to_dict()
        )

    async def _handle_generic_exception(
        self,
        _: Request,
        exc: Exception
    ) -> PrettyJSONResponse:
        traceback_str = ''.join(
            traceback.format_exception(type(exc), exc, exc.__traceback__)
        )
        error_response = self._create_error_response(
            message=traceback_str,
            error_type='internal_server_error',
            code=500,
            status_code=500
        )
        return self._create_json_response(error_response)

    async def _handle_validation_exception(
        self,
        _: Request,
        exc: Exception
    ) -> PrettyJSONResponse:
        error_response = self._create_error_response(
            message=exc.errors()[0]['msg'].replace('Value error, ', '', 1),
            error_type='invalid_request_error',
            code=400,
            status_code=400
        )
        return self._create_json_response(error_response)

    async def _handle_http_exception(
        self,
        _: Request,
        exc: HTTPException
    ) -> PrettyJSONResponse:
        error_response = self._create_error_response(
            message=exc.detail,
            error_type='invalid_request_error',
            code=exc.status_code,
            status_code=exc.status_code
        )
        return self._create_json_response(error_response)

    async def _handle_rate_limit_exceeded(
        self,
        _: Request,
        exc: RateLimitExceeded
    ) -> PrettyJSONResponse:
        error_response = self._create_error_response(
            message=f'Rate limit exceeded: {exc.detail}',
            error_type='invalid_request_error',
            code=400,
            status_code=exc.status_code
        )
        return self._create_json_response(error_response)

    def _handle_not_found(
        self,
        request: Request,
        _: Exception
    ) -> PrettyJSONResponse:
        error_response = self._create_error_response(
            message=f'Invalid URL ({request.method} {request.url.path})',
            error_type='invalid_request_error',
            code=404,
            status_code=404
        )
        return self._create_json_response(error_response)

    def _handle_method_not_allowed(
        self,
        request: Request,
        _: Exception
    ) -> PrettyJSONResponse:
        error_response = self._create_error_response(
            message=f'Invalid Method ({request.method} {request.url.path})',
            error_type='invalid_request_error',
            code=405,
            status_code=405
        )
        return self._create_json_response(error_response)

    def register_handler(
        self,
        exception_class: Type[Exception],
        handler: Callable[[Request, Exception], Awaitable[PrettyJSONResponse]]
    ) -> None:
        self.handlers[exception_class] = handler

    @classmethod
    def setup(cls, app: FastAPI) -> None:
        instance = cls()
        for exception_class, handler in instance.handlers.items():
            app.add_exception_handler(exception_class, handler)