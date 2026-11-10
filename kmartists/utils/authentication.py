from uuid import UUID

from rest_framework.authentication import get_authorization_header
from rest_framework.request import Request

from kmartists.domain.errors import AuthenticationError
from kmartists.utils.tokens import read_access_token

AUTHORIZATION_SCHEME = "Bearer"


def authenticated_user_id(request: Request) -> UUID:
    user_id = optional_user_id(request)
    if user_id is None:
        raise AuthenticationError("Authentication credentials were not provided.")
    return user_id


def optional_user_id(request: Request) -> UUID | None:
    header = get_authorization_header(request).decode()
    if not header:
        return None
    scheme, _, token = header.partition(" ")
    if scheme != AUTHORIZATION_SCHEME or not token:
        raise AuthenticationError(f"Authorization header must look like: {AUTHORIZATION_SCHEME} <token>.")
    return read_access_token(token)
