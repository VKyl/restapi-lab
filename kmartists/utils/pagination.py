import math
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Any

from django.db.models import Model, QuerySet
from rest_framework import serializers

from kmartists.utils.serialization import SerializableMixin

DEFAULT_TAKE = 20
MAX_TAKE = 100


@dataclass(frozen=True)
class Page[T: SerializableMixin]:
    items: Sequence[T]
    total_records: int
    take: int
    skip: int

    @property
    def current_page(self) -> int:
        return self.skip // self.take + 1

    @property
    def total_pages(self) -> int:
        return math.ceil(self.total_records / self.take)

    def serialize(self) -> dict[str, Any]:
        return {
            "items": [item.serialize() for item in self.items],
            "pagination": {
                "current_page": self.current_page,
                "total_pages": self.total_pages,
                "total_records": self.total_records,
            },
        }


class PageQuery(serializers.Serializer):
    take = serializers.IntegerField(min_value=1, max_value=MAX_TAKE, default=DEFAULT_TAKE)
    skip = serializers.IntegerField(min_value=0, default=0)


def paginate[M: Model, T: SerializableMixin](
    queryset: QuerySet[M], take: int, skip: int, to_entity: Callable[[M], T]
) -> Page[T]:
    return Page(
        items=[to_entity(record) for record in queryset[skip : skip + take]],
        total_records=queryset.count(),
        take=take,
        skip=skip,
    )

