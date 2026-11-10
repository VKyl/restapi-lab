from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from kmartists.domain.errors import ValidationError
from kmartists.utils.serialization import SerializableMixin
from kmartists.utils.validation import is_email, limit_text, require_text, require_text_list

MAX_USERNAME_LENGTH = 50
MAX_FIRST_NAME_LENGTH = 100
MAX_LAST_NAME_LENGTH = 100
MAX_EMAIL_LENGTH = 254
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128
MAX_MICROSOFT_ID_LENGTH = 255
MAX_LOCATION_LENGTH = 200
MAX_INSTRUMENTS = 20
MAX_INSTRUMENT_LENGTH = 50
MAX_FAVORITE_BANDS = 20
MAX_FAVORITE_BAND_LENGTH = 100


@dataclass(frozen=True)
class UserReference:
    id: UUID
    name: str


@dataclass(frozen=True)
class UserIdentity:
    id: UUID
    username: str
    first_name: str
    last_name: str


@dataclass(frozen=True)
class Registration:
    username: str
    first_name: str
    last_name: str
    email: str

    def validate(self) -> None:
        require_text("username", self.username, MAX_USERNAME_LENGTH)
        if "@" in self.username:
            raise ValidationError("username", "Username must not contain @.")
        limit_text("first_name", self.first_name, MAX_FIRST_NAME_LENGTH)
        limit_text("last_name", self.last_name, MAX_LAST_NAME_LENGTH)
        require_text("email", self.email, MAX_EMAIL_LENGTH)
        if not is_email(self.email):
            raise ValidationError("email", "Enter a valid email address, e.g. name@example.com.")


@dataclass(frozen=True)
class PasswordRegistration(Registration):
    password: str
    password_confirmation: str

    def validate(self) -> None:
        super().validate()
        self._validate_password()

    def _validate_password(self) -> None:
        require_text("password", self.password, MAX_PASSWORD_LENGTH)
        if len(self.password) < MIN_PASSWORD_LENGTH:
            raise ValidationError("password", f"Ensure this field has at least {MIN_PASSWORD_LENGTH} characters.")
        if not any(char.islower() for char in self.password):
            raise ValidationError("password", "Password must contain at least one lowercase letter.")
        if not any(char.isupper() for char in self.password):
            raise ValidationError("password", "Password must contain at least one uppercase letter.")
        if not any(char.isdigit() for char in self.password):
            raise ValidationError("password", "Password must contain at least one digit.")
        if self.password != self.password_confirmation:
            raise ValidationError("password_confirmation", "Passwords do not match.")


@dataclass(frozen=True)
class MicrosoftRegistration(Registration):
    microsoft_id: str


@dataclass(frozen=True)
class Profile(SerializableMixin):
    name: str
    instruments: Sequence[str]
    favorite_bands: Sequence[str]
    looking_for_band: bool
    location: str

    def validate(self) -> None:
        require_text("name", self.name, MAX_USERNAME_LENGTH)
        if "@" in self.name:
            raise ValidationError("name", "Name must not contain @.")
        require_text_list("instruments", self.instruments, MAX_INSTRUMENTS, MAX_INSTRUMENT_LENGTH)
        require_text_list("favorite_bands", self.favorite_bands, MAX_FAVORITE_BANDS, MAX_FAVORITE_BAND_LENGTH)
        limit_text("location", self.location, MAX_LOCATION_LENGTH)


@dataclass(frozen=True)
class ProfileDetails(Profile):
    id: UUID

    def serialize(self) -> dict[str, Any]:
        return {"id": self.id, **super().serialize()}


@dataclass(frozen=True)
class MusicianSummary(SerializableMixin):
    id: UUID
    name: str
    instruments: Sequence[str]
    favorite_bands: Sequence[str]
    location: str
