import re
from collections.abc import Iterable, Sequence

from kmartists.domain.errors import ValidationError

EMAIL_PATTERN = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")


def require_text(field: str, value: str, max_length: int) -> None:
    if not value.strip():
        raise ValidationError(field, "This field must not be blank.")
    limit_text(field, value, max_length)


def limit_text(field: str, value: str, max_length: int) -> None:
    if len(value) > max_length:
        raise ValidationError(field, f"Ensure this field has no more than {max_length} characters.")


def require_text_list(field: str, values: Sequence[str], max_items: int, max_length: int) -> None:
    if len(values) > max_items:
        raise ValidationError(field, f"Provide no more than {max_items} items.")
    for index, value in enumerate(values):
        require_text(f"{field}[{index}]", value, max_length)
    if has_duplicates(values):
        raise ValidationError(field, "Items must be unique.")


def is_email(value: str) -> bool:
    return EMAIL_PATTERN.fullmatch(value) is not None


def has_duplicates(values: Iterable[str]) -> bool:
    normalized = [value.casefold() for value in values]
    return len(normalized) != len(set(normalized))
