from typing import Any
from uuid import UUID

from rest_framework import serializers, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from kmartists import models
from kmartists.domain.users import MicrosoftRegistration, PasswordRegistration, Profile, UserIdentity
from kmartists.use_cases.users import UserUseCase
from kmartists.utils.authentication import authenticated_user_id, optional_user_id
from kmartists.utils.microsoft import read_microsoft_token
from kmartists.utils.pagination import PageQuery
from kmartists.utils.tokens import issue_tokens, read_refresh_token

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
    location = serializers.CharField(default=None)


class UpdateProfileRequest(serializers.Serializer):
    name = serializers.CharField()
    instruments = serializers.ListField(child=serializers.CharField(allow_blank=True))
    favorite_bands = serializers.ListField(child=serializers.CharField(allow_blank=True))
    looking_for_band = serializers.BooleanField()
    location = serializers.CharField(allow_blank=True)

    def to_internal_value(self, data: Any) -> Profile:
        return Profile(**super().to_internal_value(data))


class RegisterController(APIView):
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
    def post(self, request: Request) -> Response:
        body = RefreshRequest(data=request.data)
        body.is_valid(raise_exception=True)
        user = user_use_case.get_identity(read_refresh_token(body.validated_data["refresh_token"]))
        return Response(issue_tokens(user).serialize())


class MusicianCollectionController(APIView):
    def get(self, request: Request) -> Response:
        query = ListMusiciansRequest(data=request.query_params)
        query.is_valid(raise_exception=True)
        page = user_use_case.list_musicians(**query.validated_data, requester_id=optional_user_id(request))
        return Response(page.serialize())


class UserController(APIView):
    def get(self, request: Request, user_id: UUID) -> Response:
        return Response(user_use_case.get_profile(user_id).serialize())

    def put(self, request: Request, user_id: UUID) -> Response:
        requester_id = authenticated_user_id(request)
        body = UpdateProfileRequest(data=request.data)
        body.is_valid(raise_exception=True)
        user_use_case.update_profile(user_id, body.validated_data, requester_id)
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserArticleCollectionController(APIView):
    def get(self, request: Request, user_id: UUID) -> Response:
        query = PageQuery(data=request.query_params)
        query.is_valid(raise_exception=True)
        page = user_use_case.list_user_articles(user_id, **query.validated_data)
        return Response(page.serialize())
