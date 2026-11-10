from dataclasses import dataclass

import jwt
from django.conf import settings

from kmartists.domain.errors import AuthenticationError

MICROSOFT_KEYS_URL = "https://login.microsoftonline.com/common/discovery/v2.0/keys"
MICROSOFT_ISSUER = "https://login.microsoftonline.com/{tenant_id}/v2.0"
MICROSOFT_TOKEN_ALGORITHM = "RS256"

microsoft_keys = jwt.PyJWKClient(MICROSOFT_KEYS_URL)


@dataclass(frozen=True)
class MicrosoftIdentity:
    id: str
    email: str


def read_microsoft_token(token: str) -> MicrosoftIdentity:
    try:
        payload = jwt.decode(
            token,
            microsoft_keys.get_signing_key_from_jwt(token),
            algorithms=[MICROSOFT_TOKEN_ALGORITHM],
            audience=settings.MICROSOFT_CLIENT_ID,
            options={"require": ["sub", "tid", "iss", "aud", "exp"]},
        )
    except jwt.PyJWTError as error:
        raise AuthenticationError(f"Microsoft token is invalid: {error}") from error
    if payload["iss"] != MICROSOFT_ISSUER.format(tenant_id=payload["tid"]):
        raise AuthenticationError("Microsoft token is invalid: Invalid issuer")
    email = payload.get("email") or payload.get("preferred_username")
    if not email:
        raise AuthenticationError("Microsoft account has no email address.")
    return MicrosoftIdentity(id=payload["sub"], email=email)
