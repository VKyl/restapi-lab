from typing import Any

from django.http import HttpRequest, JsonResponse
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler

from kmartists.domain.errors import ConflictError, DomainError, NotFoundError, ValidationError

STATUS_BY_ERROR_TYPE: dict[type[DomainError], int] = {
    ValidationError: status.HTTP_400_BAD_REQUEST,
    NotFoundError: status.HTTP_404_NOT_FOUND,
    ConflictError: status.HTTP_409_CONFLICT,
    DomainError: status.HTTP_400_BAD_REQUEST,
}


def serialize_error(code: str, message: str, field: str | None = None) -> dict[str, Any]:
    error: dict[str, Any] = {"code": code, "message": message}
    if field:
        error["field"] = field
    return {"error": error}


def status_for(error: DomainError) -> int:
    return next(code for error_type, code in STATUS_BY_ERROR_TYPE.items() if isinstance(error, error_type))


def field_path(parent: str, key: str | int) -> str:
    if isinstance(key, int):
        return f"{parent}[{key}]"
    return f"{parent}.{key}" if parent else key


def first_field_error(detail: Any, path: str = "") -> tuple[str, str]:
    if isinstance(detail, list) and all(isinstance(item, str) for item in detail):
        return path, str(detail[0])
    entries = detail.items() if isinstance(detail, dict) else enumerate(detail)
    key, nested = next((key, nested) for key, nested in entries if nested)
    return first_field_error(nested, field_path(path, key))


def handle_exception(exc: Exception, context: dict[str, Any]) -> Response | None:
    if isinstance(exc, DomainError):
        field = exc.field if isinstance(exc, ValidationError) else None
        return Response(serialize_error(exc.code, exc.message, field), status=status_for(exc))
    response = exception_handler(exc, context)
    if isinstance(exc, exceptions.ValidationError):
        field, message = first_field_error(exc.detail)
        response.data = serialize_error(ValidationError.code, message, field)
    elif response is not None and isinstance(exc, exceptions.APIException):
        response.data = serialize_error(exc.default_code, str(exc.detail))
    return response


def not_found(request: HttpRequest, exception: Exception) -> JsonResponse:
    return JsonResponse(serialize_error("not_found", "The requested resource was not found."), status=404)


def server_error(request: HttpRequest) -> JsonResponse:
    return JsonResponse(serialize_error("server_error", "An unexpected error occurred."), status=500)
