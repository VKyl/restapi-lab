from dataclasses import asdict
from typing import Any


class SerializableMixin:
    def serialize(self) -> dict[str, Any]:
        return asdict(self)
