import re
from collections.abc import Iterable

from kmartists.domain.errors import ValidationError

EMAIL_PATTERN = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def require_text(field: str, value: str, max_length: int) -> None:
    if not value.strip():
        raise ValidationError(field, "This field must not be blank.")
    limit_text(field, value, max_length)


def limit_text(field: str, value: str, max_length: int) -> None:
    if len(value) > max_length:
        raise ValidationError(field, f"Ensure this field has no more than {max_length} characters.")


def is_email(value: str) -> bool:
    return EMAIL_PATTERN.fullmatch(value) is not None


def has_duplicates(values: Iterable[str]) -> bool:
    normalized = [value.casefold() for value in values]
    return len(normalized) != len(set(normalized))
