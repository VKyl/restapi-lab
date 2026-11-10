from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from django.conf import settings

from kmartists.domain.errors import AuthenticationError
from kmartists.domain.users import UserIdentity
from kmartists.utils.serialization import SerializableMixin

TOKEN_ALGORITHM = "HS256"
ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"
ACCESS_TOKEN_LIFETIME = timedelta(minutes=15)
REFRESH_TOKEN_LIFETIME = timedelta(days=7)


@dataclass(frozen=True)
class TokenPair(SerializableMixin):
    token: str
    refresh_token: str


def issue_tokens(user: UserIdentity) -> TokenPair:
    return TokenPair(
        token=encode_token(user, ACCESS_TOKEN_TYPE, ACCESS_TOKEN_LIFETIME),
        refresh_token=encode_token(user, REFRESH_TOKEN_TYPE, REFRESH_TOKEN_LIFETIME),
    )


def encode_token(user: UserIdentity, token_type: str, lifetime: timedelta) -> str:
    issued_at = datetime.now(UTC)
    payload = {
        "id": str(user.id),
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "type": token_type,
        "iat": issued_at,
        "exp": issued_at + lifetime,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=TOKEN_ALGORITHM)


def read_refresh_token(token: str) -> UUID:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[TOKEN_ALGORITHM])
    except jwt.InvalidTokenError as error:
        raise AuthenticationError("Refresh token is invalid or expired.") from error
    if payload.get("type") != REFRESH_TOKEN_TYPE:
        raise AuthenticationError("Refresh token is invalid or expired.")
    return UUID(payload["id"])
