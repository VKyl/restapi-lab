from dataclasses import asdict
from datetime import UTC, datetime
from datetime import date as calendar_date
from uuid import UUID, uuid4

from django.db import models
from django.db.models import Q

from kmartists.domain.errors import NotFoundError
from kmartists.domain.events import Event as EventEntity
from kmartists.domain.events import (
    EventDetails,
    EventSummary,
    MAX_CONTACT_INFO_LENGTH,
    MAX_LOCATION_LENGTH,
    MAX_NAME_LENGTH,
)
from kmartists.models.users import User
from kmartists.utils.pagination import Page, paginate


class Event(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name="events")
    name = models.CharField(max_length=MAX_NAME_LENGTH)
    date = models.DateTimeField(db_index=True)
    location = models.CharField(max_length=MAX_LOCATION_LENGTH)
    description = models.TextField()
    contact_info = models.CharField(max_length=MAX_CONTACT_INFO_LENGTH)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "events"

    @classmethod
    def list_summaries(
        cls,
        take: int,
        skip: int,
        search_query: str | None,
        location: str | None,
        on_date: calendar_date | None,
    ) -> Page[EventSummary]:
        queryset = cls.objects.order_by("date", "name")
        if search_query:
            queryset = queryset.filter(Q(name__icontains=search_query) | Q(description__icontains=search_query))
        if location:
            queryset = queryset.filter(location__icontains=location)
        if on_date:
            queryset = queryset.filter(date__date=on_date)
        return paginate(queryset, take, skip, cls.to_summary)

    @classmethod
    def find_details(cls, event_id: UUID) -> EventDetails | None:
        event = cls.objects.select_related("creator").filter(id=event_id).first()
        return event.to_details() if event else None

    @classmethod
    def create_event(cls, event: EventEntity) -> UUID:
        return cls.objects.create(creator=User.placeholder_author(), **asdict(event)).id

    @classmethod
    def update_event(cls, event_id: UUID, event: EventEntity) -> None:
        updated = cls.objects.filter(id=event_id).update(**asdict(event), updated_at=datetime.now(UTC))
        if not updated:
            raise NotFoundError(f"Event {event_id} does not exist.")

    @classmethod
    def delete_event(cls, event_id: UUID) -> None:
        cls.objects.filter(id=event_id).delete()

    def to_summary(self) -> EventSummary:
        return EventSummary(id=self.id, name=self.name, date=self.date, location=self.location)

    def to_details(self) -> EventDetails:
        return EventDetails(
            id=self.id,
            name=self.name,
            date=self.date,
            location=self.location,
            description=self.description,
            contact_info=self.contact_info,
            creator=self.creator.to_reference(),
            created_at=self.created_at,
            updated_at=self.updated_at,
        )
