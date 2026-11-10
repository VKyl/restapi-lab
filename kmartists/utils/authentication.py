from typing import Any

from rest_framework.authentication import BaseAuthentication, get_authorization_header
from rest_framework.permissions import SAFE_METHODS, BasePermission
from rest_framework.request import Request

from kmartists import models
from kmartists.domain.errors import AuthenticationError
from kmartists.domain.users import UserIdentity
from kmartists.use_cases.users import UserUseCases
from kmartists.utils.tokens import read_access_token

AUTHORIZATION_SCHEME = "Bearer"

user_use_cases = UserUseCases(users=models.User)


class AccessTokenAuthentication(BaseAuthentication):
    def authenticate(self, request: Request) -> tuple[UserIdentity, str] | None:
        header = get_authorization_header(request).decode()
        if not header:
            return None
        scheme, _, token = header.partition(" ")
        if scheme != AUTHORIZATION_SCHEME or not token:
            raise AuthenticationError(f"Authorization header must look like: {AUTHORIZATION_SCHEME} <token>.")
        return user_use_cases.get_identity(read_access_token(token)), token

    def authenticate_header(self, request: Request) -> str:
        return AUTHORIZATION_SCHEME


class IsAuthenticatedOrReadOnly(BasePermission):
    def has_permission(self, request: Request, view: Any) -> bool:
        return request.method in SAFE_METHODS or request.user is not None
