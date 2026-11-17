from collections.abc import Sequence
from dataclasses import fields, is_dataclass
from inspect import isclass
from types import NoneType, UnionType
from typing import Any, Union, get_args, get_origin, get_type_hints

from drf_spectacular.extensions import OpenApiSerializerExtension
from drf_spectacular.openapi import AutoSchema
from drf_spectacular.plumbing import build_array_type, build_object_type, resolve_type_hint
from drf_spectacular.utils import Direction, OpenApiExample, OpenApiResponse
from rest_framework import serializers

from kmartists.utils.pagination import Page

BEARER_AUTH = "BearerAuth"
REQUIRES_TOKEN = [{BEARER_AUTH: []}]
ACCEPTS_TOKEN = [{}, {BEARER_AUTH: []}]


class ErrorDetailResponse(serializers.Serializer):
    code = serializers.CharField(help_text="Machine-readable error code.")
    message = serializers.CharField(help_text="Human-readable description of the first error found.")
    field = serializers.CharField(required=False, help_text="Path of the invalid field, only for validation errors.")


class ErrorResponse(serializers.Serializer):
    error = ErrorDetailResponse()


class PaginationResponse(serializers.Serializer):
    current_page = serializers.IntegerField()
    total_pages = serializers.IntegerField()
    total_records = serializers.IntegerField()


class CreatedResponse(serializers.Serializer):
    id = serializers.UUIDField(help_text="Id of the created resource.")


def schema_of(auto_schema: AutoSchema, hint: Any, direction: Direction) -> dict[str, Any]:
    origin, args = get_origin(hint), get_args(hint)
    if isclass(hint) and is_dataclass(hint):
        return auto_schema.resolve_serializer(hint, direction).ref
    if origin in (list, Sequence):
        return build_array_type(schema_of(auto_schema, args[0], direction))
    if origin in (Union, UnionType) and NoneType in args:
        (value_hint,) = [arg for arg in args if arg is not NoneType]
        schema = schema_of(auto_schema, value_hint, direction)
        return {"allOf": [schema], "nullable": True} if "$ref" in schema else {**schema, "nullable": True}
    return resolve_type_hint(hint)


class DomainEntityExtension(OpenApiSerializerExtension):
    target_class = object

    @classmethod
    def _matches(cls, target: Any) -> bool:
        return (isclass(target) and is_dataclass(target)) or get_origin(target) is Page

    def get_name(self, auto_schema: AutoSchema, direction: Direction) -> str:
        if get_origin(self.target) is Page:
            return f"{get_args(self.target)[0].__name__}Page"
        return self.target.__name__

    def map_serializer(self, auto_schema: AutoSchema, direction: Direction) -> dict[str, Any]:
        if get_origin(self.target) is Page:
            (item,) = get_args(self.target)
            properties = {
                "items": build_array_type(schema_of(auto_schema, item, direction)),
                "pagination": auto_schema.resolve_serializer(PaginationResponse, direction).ref,
            }
        else:
            hints = get_type_hints(self.target)
            id_first = sorted(fields(self.target), key=lambda field: field.name != "id")
            properties = {field.name: schema_of(auto_schema, hints[field.name], direction) for field in id_first}
        return build_object_type(properties=properties, required=properties)


def error_example(name: str, code: str, message: str, field: str | None = None) -> OpenApiExample:
    error: dict[str, Any] = {"code": code, "message": message}
    if field:
        error["field"] = field
    return OpenApiExample(name, value={"error": error}, response_only=True)


def error_response(description: str, *examples: OpenApiExample) -> OpenApiResponse:
    return OpenApiResponse(ErrorResponse, description=description, examples=list(examples))


VALIDATION_FAILED = error_response(
    "Malformed JSON, invalid query parameters or a body that breaks validation rules.",
    error_example("Invalid field", "validation_error", "This field must not be blank.", "name"),
    error_example("Malformed JSON", "parse_error", "JSON parse error - Expecting value: line 1 column 1 (char 0)"),
)
UNAUTHENTICATED = error_response(
    "Access token is missing, malformed, expired, or belongs to a deleted user.",
    error_example("Missing token", "invalid_credentials", "Authentication credentials were not provided."),
)
NOT_FOUND = error_response(
    "The resource does not exist or the id is not a valid UUID.",
    error_example("Not found", "not_found", "The requested resource was not found."),
)
