from typing import Any
from uuid import UUID

from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, PolymorphicProxySerializer, extend_schema
from rest_framework import serializers, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from kmartists import models
from kmartists.domain.articles import ArticleSummary
from kmartists.domain.users import (
    MicrosoftRegistration,
    MusicianSummary,
    PasswordRegistration,
    Profile,
    ProfileDetails,
    UserIdentity,
)
from kmartists.use_cases.users import UserUseCase
from kmartists.utils.authentication import authenticated_user_id, optional_user_id
from kmartists.utils.microsoft import read_microsoft_token
from kmartists.utils.openapi import (
    ACCEPTS_TOKEN,
    NOT_FOUND,
    REQUIRES_TOKEN,
    UNAUTHENTICATED,
    VALIDATION_FAILED,
    error_example,
    error_response,
)
from kmartists.utils.pagination import Page, PageQuery
from kmartists.utils.tokens import TokenPair, issue_tokens, read_refresh_token

user_use_case = UserUseCase(users=models.User, articles=models.Article)


class RegisterRequest(serializers.Serializer):
    username = serializers.CharField()
    first_name = serializers.CharField(allow_blank=True, default="")
    last_name = serializers.CharField(allow_blank=True, default="")
    email = serializers.CharField()
    password = serializers.CharField(trim_whitespace=False)
    password_confirmation = serializers.CharField(trim_whitespace=False)

    def to_internal_value(self, data: Any) -> PasswordRegistration:
        return PasswordRegistration(**super().to_internal_value(data))


class MicrosoftRegisterRequest(serializers.Serializer):
    username = serializers.CharField()
    first_name = serializers.CharField(allow_blank=True, default="")
    last_name = serializers.CharField(allow_blank=True, default="")
    microsoft_token = serializers.CharField()


class LoginRequest(serializers.Serializer):
    login = serializers.CharField()
    password = serializers.CharField(trim_whitespace=False)


class MicrosoftLoginRequest(serializers.Serializer):
    microsoft_token = serializers.CharField()


class RefreshRequest(serializers.Serializer):
    refresh_token = serializers.CharField()


class ListMusiciansRequest(PageQuery):
    location = serializers.CharField(default=None, help_text="Case-insensitive search in musician location.")


class UpdateProfileRequest(serializers.Serializer):
    name = serializers.CharField()
    instruments = serializers.ListField(child=serializers.CharField(allow_blank=True))
    favorite_bands = serializers.ListField(child=serializers.CharField(allow_blank=True))
    looking_for_band = serializers.BooleanField()
    location = serializers.CharField(allow_blank=True)

    def to_internal_value(self, data: Any) -> Profile:
        return Profile(**super().to_internal_value(data))


TOKENS_ISSUED = OpenApiResponse(
    TokenPair, description="`token` is an access token valid for 15 minutes, `refresh_token` is valid for 7 days."
)
USER_ID = OpenApiParameter("user_id", UUID, OpenApiParameter.PATH, description="User id.")


class RegisterController(APIView):
    @extend_schema(
        tags=["Auth"],
        operation_id="register",
        summary="Register",
        description=(
            "Registers with username, email and password, or with a Microsoft ID token. "
            "Username must not contain @. Password needs 8+ characters with a lowercase letter, "
            "an uppercase letter and a digit."
        ),
        request=PolymorphicProxySerializer(
            component_name="RegisterBody",
            serializers=[RegisterRequest, MicrosoftRegisterRequest],
            resource_type_field_name=None,
        ),
        responses={
            201: TOKENS_ISSUED,
            400: VALIDATION_FAILED,
            401: error_response(
                "Microsoft token is invalid.",
                error_example(
                    "Invalid Microsoft token", "invalid_credentials", "Microsoft token is invalid: Invalid issuer"
                ),
            ),
            409: error_response(
                "Username, email or Microsoft account is already registered.",
                error_example("Username taken", "conflict", "Username metalhead is already taken."),
            ),
        },
    )
    def post(self, request: Request) -> Response:
        if "microsoft_token" in request.data:
            user = self._register_with_microsoft(request)
        else:
            body = RegisterRequest(data=request.data)
            body.is_valid(raise_exception=True)
            user = user_use_case.register(body.validated_data)
        return Response(issue_tokens(user).serialize(), status=status.HTTP_201_CREATED)

    def _register_with_microsoft(self, request: Request) -> UserIdentity:
        body = MicrosoftRegisterRequest(data=request.data)
        body.is_valid(raise_exception=True)
        fields = dict(body.validated_data)
        identity = read_microsoft_token(fields.pop("microsoft_token"))
        registration = MicrosoftRegistration(**fields, email=identity.email, microsoft_id=identity.id)
        return user_use_case.register_with_microsoft(registration)


class LoginController(APIView):
    @extend_schema(
        tags=["Auth"],
        operation_id="log_in",
        summary="Log in",
        description="`login` is treated as an email when it contains @, otherwise as a username.",
        request=PolymorphicProxySerializer(
            component_name="LoginBody",
            serializers=[LoginRequest, MicrosoftLoginRequest],
            resource_type_field_name=None,
        ),
        responses={
            200: TOKENS_ISSUED,
            400: VALIDATION_FAILED,
            401: error_response(
                "Wrong login or password, or invalid Microsoft token.",
                error_example("Wrong credentials", "invalid_credentials", "Invalid login or password."),
            ),
            404: error_response(
                "No user is registered with this Microsoft account.",
                error_example(
                    "Unknown Microsoft account", "not_found", "No user is registered with this Microsoft account."
                ),
            ),
        },
    )
    def post(self, request: Request) -> Response:
        if "microsoft_token" in request.data:
            user = self._log_in_with_microsoft(request)
        else:
            body = LoginRequest(data=request.data)
            body.is_valid(raise_exception=True)
            user = user_use_case.log_in(**body.validated_data)
        return Response(issue_tokens(user).serialize())

    def _log_in_with_microsoft(self, request: Request) -> UserIdentity:
        body = MicrosoftLoginRequest(data=request.data)
        body.is_valid(raise_exception=True)
        identity = read_microsoft_token(body.validated_data["microsoft_token"])
        return user_use_case.log_in_with_microsoft(identity.id)


class RefreshController(APIView):
    @extend_schema(
        tags=["Auth"],
        operation_id="refresh",
        summary="Refresh tokens",
        request=RefreshRequest,
        responses={
            200: TOKENS_ISSUED,
            400: VALIDATION_FAILED,
            401: error_response(
                "Refresh token is invalid, expired, or belongs to a deleted user.",
                error_example("Deleted user", "invalid_credentials", "User no longer exists."),
            ),
        },
    )
    def post(self, request: Request) -> Response:
        body = RefreshRequest(data=request.data)
        body.is_valid(raise_exception=True)
        user = user_use_case.get_identity(read_refresh_token(body.validated_data["refresh_token"]))
        return Response(issue_tokens(user).serialize())


class MusicianCollectionController(APIView):
    @extend_schema(
        tags=["Users"],
        operation_id="list_musicians",
        summary="List musicians looking for a band",
        description="Public. When the request carries an access token, the requesting user is not included.",
        auth=ACCEPTS_TOKEN,
        parameters=[ListMusiciansRequest],
        responses={
            200: Page[MusicianSummary],
            400: VALIDATION_FAILED,
            401: UNAUTHENTICATED,
        },
    )
    def get(self, request: Request) -> Response:
        query = ListMusiciansRequest(data=request.query_params)
        query.is_valid(raise_exception=True)
        page = user_use_case.list_musicians(**query.validated_data, requester_id=optional_user_id(request))
        return Response(page.serialize())


class UserController(APIView):
    @extend_schema(
        tags=["Users"],
        operation_id="get_profile",
        summary="Get user profile",
        parameters=[USER_ID],
        responses={200: ProfileDetails, 404: NOT_FOUND},
    )
    def get(self, request: Request, user_id: UUID) -> Response:
        return Response(user_use_case.get_profile(user_id).serialize())

    @extend_schema(
        tags=["Users"],
        operation_id="update_profile",
        summary="Update user profile",
        description="Only the profile owner can change it. `name` must be unique.",
        auth=REQUIRES_TOKEN,
        parameters=[USER_ID],
        request=UpdateProfileRequest,
        responses={
            204: OpenApiResponse(description="Profile updated."),
            400: VALIDATION_FAILED,
            401: UNAUTHENTICATED,
            403: error_response(
                "The requester is not the profile owner.",
                error_example("Not owner", "forbidden", "Only the profile owner can change this profile."),
            ),
            404: NOT_FOUND,
            409: error_response(
                "The name is taken by another user.",
                error_example("Name taken", "conflict", "Username metalhead is already taken."),
            ),
        },
    )
    def put(self, request: Request, user_id: UUID) -> Response:
        requester_id = authenticated_user_id(request)
        body = UpdateProfileRequest(data=request.data)
        body.is_valid(raise_exception=True)
        user_use_case.update_profile(user_id, body.validated_data, requester_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserArticleCollectionController(APIView):
    @extend_schema(
        tags=["Users"],
        operation_id="list_user_articles",
        summary="List articles the user contributed to",
        parameters=[USER_ID, PageQuery],
        responses={
            200: Page[ArticleSummary],
            400: VALIDATION_FAILED,
            404: NOT_FOUND,
        },
    )
    def get(self, request: Request, user_id: UUID) -> Response:
        query = PageQuery(data=request.query_params)
        query.is_valid(raise_exception=True)
        page = user_use_case.list_user_articles(user_id, **query.validated_data)
        return Response(page.serialize())
