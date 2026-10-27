from datetime import date as calendar_date
from typing import Protocol
from uuid import UUID

from kmartists.domain.events import Event, EventDetails, EventSummary
from kmartists.utils.pagination import Page


class EventRepository(Protocol):
    def list_summaries(
        self,
        take: int,
        skip: int,
        search_query: str | None,
        location: str | None,
        on_date: calendar_date | None,
    ) -> Page[EventSummary]: ...

    def find_details(self, event_id: UUID) -> EventDetails | None: ...

    def create_event(self, event: Event) -> UUID: ...

    def update_event(self, event_id: UUID, event: Event) -> None: ...

    def delete_event(self, event_id: UUID) -> None: ...
