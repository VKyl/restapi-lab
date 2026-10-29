from dataclasses import dataclass
from uuid import UUID


@dataclass(frozen=True)
class UserReference:
    id: UUID
    name: str
