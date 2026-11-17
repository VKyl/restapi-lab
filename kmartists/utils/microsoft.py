import logging
from dataclasses import dataclass

import jwt
from django.conf import settings

from kmartists.domain.errors import AuthenticationError

MICROSOFT_KEYS_URL = "https://login.microsoftonline.com/common/discovery/v2.0/keys"
MICROSOFT_ISSUER = "https://login.microsoftonline.com/{tenant_id}/v2.0"
MICROSOFT_TOKEN_ALGORITHM = "RS256"

microsoft_keys = jwt.PyJWKClient(MICROSOFT_KEYS_URL)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class MicrosoftIdentity:
    id: str
    email: str


def read_microsoft_token(token: str) -> MicrosoftIdentity:
    if not settings.MICROSOFT_CLIENT_ID:
        logger.error("MICROSOFT_CLIENT_ID is not set, Microsoft tokens cannot be verified")
    try:
        payload = jwt.decode(
            token,
            microsoft_keys.get_signing_key_from_jwt(token),
            algorithms=[MICROSOFT_TOKEN_ALGORITHM],
            audience=settings.MICROSOFT_CLIENT_ID,
            options={"require": ["sub", "tid", "iss", "aud", "exp"]},
        )
    except jwt.PyJWKClientError as error:
        logger.error("Could not get Microsoft signing keys: %s", error)
        raise AuthenticationError(f"Microsoft token is invalid: {error}") from error
    except jwt.PyJWTError as error:
        logger.warning("Rejected Microsoft token: %s", error)
        raise AuthenticationError(f"Microsoft token is invalid: {error}") from error
    if payload["iss"] != MICROSOFT_ISSUER.format(tenant_id=payload["tid"]):
        logger.warning("Rejected Microsoft token: issuer does not match tenant %s", payload["tid"])
        raise AuthenticationError("Microsoft token is invalid: Invalid issuer")
    email = payload.get("email") or payload.get("preferred_username")
    if not email:
        logger.warning("Rejected Microsoft token: account %s has no email address", payload["sub"])
        raise AuthenticationError("Microsoft account has no email address.")
    return MicrosoftIdentity(id=payload["sub"], email=email)
