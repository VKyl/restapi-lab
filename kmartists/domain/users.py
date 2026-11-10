from dataclasses import dataclass
from uuid import UUID

from kmartists.domain.errors import ValidationError
from kmartists.utils.validation import is_email, limit_text, require_text

MAX_USERNAME_LENGTH = 50
MAX_FIRST_NAME_LENGTH = 100
MAX_LAST_NAME_LENGTH = 100
MAX_EMAIL_LENGTH = 254
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 128


@dataclass(frozen=True)
class UserReference:
    id: UUID
    name: str


@dataclass(frozen=True)
class Registration:
    username: str
    first_name: str
    last_name: str
    email: str
    password: str
    password_confirmation: str

    def validate(self) -> None:
        require_text("username", self.username, MAX_USERNAME_LENGTH)
        limit_text("first_name", self.first_name, MAX_FIRST_NAME_LENGTH)
        limit_text("last_name", self.last_name, MAX_LAST_NAME_LENGTH)
        require_text("email", self.email, MAX_EMAIL_LENGTH)
        if not is_email(self.email):
            raise ValidationError("email", "Enter a valid email address, e.g. name@example.com.")
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
