from typing import Any

from rest_framework import serializers, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from kmartists import models
from kmartists.domain.users import MicrosoftRegistration, PasswordRegistration, UserReference
from kmartists.use_cases.users import UserUseCases
from kmartists.utils.microsoft import read_microsoft_token
from kmartists.utils.tokens import issue_tokens, read_refresh_token

user_use_cases = UserUseCases(users=models.User)


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
    username = serializers.CharField()
    password = serializers.CharField(trim_whitespace=False)


class RefreshRequest(serializers.Serializer):
    refresh_token = serializers.CharField()


class RegisterController(APIView):
    def post(self, request: Request) -> Response:
        if "microsoft_token" in request.data:
            user = self._register_with_microsoft(request)
        else:
            body = RegisterRequest(data=request.data)
            body.is_valid(raise_exception=True)
            user = user_use_cases.register(body.validated_data)
        return Response(issue_tokens(user).serialize(), status=status.HTTP_201_CREATED)

    def _register_with_microsoft(self, request: Request) -> UserReference:
        body = MicrosoftRegisterRequest(data=request.data)
        body.is_valid(raise_exception=True)
        fields = dict(body.validated_data)
        identity = read_microsoft_token(fields.pop("microsoft_token"))
        registration = MicrosoftRegistration(**fields, email=identity.email, microsoft_id=identity.id)
        return user_use_cases.register_with_microsoft(registration)


class LoginController(APIView):
    def post(self, request: Request) -> Response:
        body = LoginRequest(data=request.data)
        body.is_valid(raise_exception=True)
        user = user_use_cases.log_in(**body.validated_data)
        return Response(issue_tokens(user).serialize())


class RefreshController(APIView):
    def post(self, request: Request) -> Response:
        body = RefreshRequest(data=request.data)
        body.is_valid(raise_exception=True)
        user = user_use_cases.refresh(read_refresh_token(body.validated_data["refresh_token"]))
        return Response(issue_tokens(user).serialize())
