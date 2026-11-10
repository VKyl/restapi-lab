from rest_framework.authentication import get_authorization_header
from rest_framework.request import Request

from kmartists import models
from kmartists.domain.errors import AuthenticationError
from kmartists.domain.users import UserIdentity
from kmartists.use_cases.users import UserUseCases
from kmartists.utils.tokens import read_access_token

AUTHORIZATION_SCHEME = "Bearer"

user_use_cases = UserUseCases(users=models.User)


def authenticated_user(request: Request) -> UserIdentity:
    header = get_authorization_header(request).decode()
    if not header:
        raise AuthenticationError("Authentication credentials were not provided.")
    scheme, _, token = header.partition(" ")
    if scheme != AUTHORIZATION_SCHEME or not token:
        raise AuthenticationError(f"Authorization header must look like: {AUTHORIZATION_SCHEME} <token>.")
    return user_use_cases.get_identity(read_access_token(token))
