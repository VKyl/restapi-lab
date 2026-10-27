from collections.abc import Iterable

from kmartists.domain.errors import ValidationError


def require_text(field: str, value: str, max_length: int) -> None:
    if not value.strip():
        raise ValidationError(field, "This field must not be blank.")
    if len(value) > max_length:
        raise ValidationError(field, f"Ensure this field has no more than {max_length} characters.")


def has_duplicates(values: Iterable[str]) -> bool:
    normalized = [value.casefold() for value in values]
    return len(normalized) != len(set(normalized))
