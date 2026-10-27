from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from kmartists.domain.errors import ValidationError
from kmartists.domain.users import UserReference
from kmartists.utils.serialization import SerializableMixin
from kmartists.utils.validation import require_text

MAX_NAME_LENGTH = 200
MAX_LOCATION_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 5_000
MAX_CONTACT_INFO_LENGTH = 255


@dataclass(frozen=True)
class Event(SerializableMixin):
    name: str
    date: datetime
    location: str
    description: str
    contact_info: str

    def validate(self) -> None:
        require_text("name", self.name, MAX_NAME_LENGTH)
        if self.has_taken_place():
            raise ValidationError("date", "The event date must be in the future.")
        require_text("location", self.location, MAX_LOCATION_LENGTH)
        require_text("description", self.description, MAX_DESCRIPTION_LENGTH)
        require_text("contact_info", self.contact_info, MAX_CONTACT_INFO_LENGTH)

    def has_taken_place(self) -> bool:
        return self.date <= datetime.now(UTC)


@dataclass(frozen=True)
class EventSummary(SerializableMixin):
    id: UUID
    name: str
    date: datetime
    location: str


@dataclass(frozen=True)
class EventDetails(Event):
    id: UUID
    creator: UserReference
    created_at: datetime
    updated_at: datetime

    def serialize(self) -> dict[str, Any]:
        return {"id": self.id, **super().serialize()}
