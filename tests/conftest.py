from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from kmartists import models
from kmartists.utils.tokens import issue_tokens


@pytest.fixture(autouse=True)
def empty_database(db: None) -> None:
    models.Article.objects.all().delete()
    models.Event.objects.all().delete()
    models.User.objects.all().delete()


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def make_user(db: None) -> Callable[..., models.User]:
    def make(name: str) -> models.User:
        return models.User.objects.create(name=name, email=f"{name}@example.com")

    return make


@pytest.fixture
def creator(make_user: Callable[..., models.User]) -> models.User:
    return make_user("creator")


@pytest.fixture
def stranger(make_user: Callable[..., models.User]) -> models.User:
    return make_user("stranger")


@pytest.fixture
def client_for() -> Callable[[models.User], APIClient]:
    def authorize(user: models.User) -> APIClient:
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {issue_tokens(user.to_identity()).token}")
        return client

    return authorize


@pytest.fixture
def creator_client(client_for: Callable[[models.User], APIClient], creator: models.User) -> APIClient:
    return client_for(creator)


@pytest.fixture
def stranger_client(client_for: Callable[[models.User], APIClient], stranger: models.User) -> APIClient:
    return client_for(stranger)


@pytest.fixture
def future_date() -> datetime:
    return (datetime.now(UTC) + timedelta(days=30)).replace(microsecond=0)


@pytest.fixture
def event_payload(future_date: datetime) -> dict[str, Any]:
    return {
        "name": "Rock Night",
        "date": future_date.isoformat(),
        "location": "Kyiv, Atlas",
        "description": "Local bands play all night.",
        "contact_info": "rock@example.com",
    }


@pytest.fixture
def make_event(creator: models.User, future_date: datetime) -> Callable[..., models.Event]:
    def make(**fields: Any) -> models.Event:
        defaults = {
            "creator": creator,
            "name": "Jazz Evening",
            "date": future_date,
            "location": "Lviv, Opera",
            "description": "Smooth jazz under the stars.",
            "contact_info": "jazz@example.com",
        }
        return models.Event.objects.create(**{**defaults, **fields})

    return make


@pytest.fixture
def event(make_event: Callable[..., models.Event]) -> models.Event:
    return make_event()


@pytest.fixture
def past_event(make_event: Callable[..., models.Event]) -> models.Event:
    return make_event(name="Past Gig", date=datetime.now(UTC) - timedelta(days=1))


@pytest.fixture
def events_url() -> str:
    return reverse("event-collection")


@pytest.fixture
def event_url() -> Callable[[Any], str]:
    return lambda event_id: reverse("event-detail", kwargs={"event_id": event_id})
