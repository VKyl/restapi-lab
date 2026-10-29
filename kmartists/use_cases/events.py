from datetime import date as calendar_date
from uuid import UUID

from kmartists.domain.errors import ConflictError, NotFoundError
from kmartists.domain.events import Event, EventDetails, EventSummary
from kmartists.interfaces.events import EventRepository
from kmartists.utils.pagination import Page


class EventUseCases:
    def __init__(self, events: EventRepository) -> None:
        self._events = events

    def list_events(
        self,
        take: int,
        skip: int,
        search_query: str | None,
        location: str | None,
        on_date: calendar_date | None,
    ) -> Page[EventSummary]:
        return self._events.list_summaries(take, skip, search_query, location, on_date)

    def get_event(self, event_id: UUID) -> EventDetails:
        event = self._events.find_details(event_id)
        if event is None:
            raise NotFoundError(f"Event {event_id} does not exist.")
        return event

    def create_event(self, event: Event) -> UUID:
        event.validate()
        return self._events.create_event(event)

    def update_event(self, event_id: UUID, event: Event) -> None:
        if self.get_event(event_id).has_taken_place():
            raise ConflictError("Events that have already taken place cannot be changed.")
        event.validate()
        self._events.update_event(event_id, event)

    def delete_event(self, event_id: UUID) -> None:
        self.get_event(event_id)
        self._events.delete_event(event_id)
