from datetime import date as calendar_date
from uuid import UUID

from kmartists.domain.errors import ConflictError, ForbiddenError, NotFoundError
from kmartists.domain.events import Event, EventDetails, EventSummary
from kmartists.interfaces.events import EventRepository
from kmartists.use_cases.users import UserUseCase
from kmartists.utils.pagination import Page


class EventUseCase:
    def __init__(self, events: EventRepository, users: UserUseCase) -> None:
        self._events = events
        self._users = users

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

    def create_event(self, event: Event, creator_id: UUID) -> UUID:
        self._users.get_identity(creator_id)
        event.validate()
        return self._events.create_event(event, creator_id)

    def update_event(self, event_id: UUID, event: Event, user_id: UUID) -> None:
        if self._get_own_event(event_id, user_id).has_taken_place():
            raise ConflictError("Events that have already taken place cannot be changed.")
        event.validate()
        self._events.update_event(event_id, event)

    def delete_event(self, event_id: UUID, user_id: UUID) -> None:
        self._get_own_event(event_id, user_id)
        self._events.delete_event(event_id)

    def _get_own_event(self, event_id: UUID, user_id: UUID) -> EventDetails:
        event = self.get_event(event_id)
        if event.creator.id != user_id:
            raise ForbiddenError("Only the event creator can change this event.")
        return event
