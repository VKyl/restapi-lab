from collections.abc import Callable
from datetime import datetime, timedelta
from typing import Any
from uuid import uuid4

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from kmartists import models
from kmartists.utils.tokens import ACCESS_TOKEN_TYPE, encode_token, issue_tokens

DETAIL_KEYS = [
    "id",
    "name",
    "date",
    "location",
    "description",
    "contact_info",
    "creator",
    "created_at",
    "updated_at",
]


def error_of(response: Any) -> dict[str, Any]:
    return response.json()["error"]


@pytest.mark.django_db
class TestListEvents:
    def test_is_public_and_returns_page(self, api_client: APIClient, events_url: str, event: models.Event) -> None:
        response = api_client.get(events_url)

        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert body["items"] == [
            {
                "id": str(event.id),
                "name": event.name,
                "date": event.date.isoformat().replace("+00:00", "Z"),
                "location": event.location,
            }
        ]
        assert body["pagination"] == {"current_page": 1, "total_pages": 1, "total_records": 1}

    def test_returns_empty_page_without_events(self, api_client: APIClient, events_url: str) -> None:
        response = api_client.get(events_url)

        assert response.status_code == status.HTTP_200_OK
        assert response.json() == {
            "items": [],
            "pagination": {"current_page": 1, "total_pages": 0, "total_records": 0},
        }

    def test_orders_by_date(
        self, api_client: APIClient, events_url: str, make_event: Callable[..., models.Event], future_date: datetime
    ) -> None:
        later = make_event(name="Later", date=future_date + timedelta(days=1))
        sooner = make_event(name="Sooner", date=future_date)

        response = api_client.get(events_url)

        assert [item["id"] for item in response.json()["items"]] == [str(sooner.id), str(later.id)]

    def test_paginates(self, api_client: APIClient, events_url: str, make_event: Callable[..., models.Event]) -> None:
        for index in range(5):
            make_event(name=f"Event {index}")

        response = api_client.get(events_url, {"take": 2, "skip": 2})

        body = response.json()
        assert [item["name"] for item in body["items"]] == ["Event 2", "Event 3"]
        assert body["pagination"] == {"current_page": 2, "total_pages": 3, "total_records": 5}

    @pytest.mark.parametrize(
        ("params", "expected_names"),
        [
            ({"search_query": "metal"}, ["Metal Fest"]),
            ({"search_query": "UNPLUGGED"}, ["Folk Day"]),
            ({"location": "odesa"}, ["Folk Day"]),
        ],
    )
    def test_filters(
        self,
        api_client: APIClient,
        events_url: str,
        make_event: Callable[..., models.Event],
        params: dict[str, str],
        expected_names: list[str],
    ) -> None:
        make_event(name="Metal Fest", location="Kyiv", description="Loud guitars.")
        make_event(name="Folk Day", location="Odesa", description="Unplugged songs.")

        response = api_client.get(events_url, params)

        assert [item["name"] for item in response.json()["items"]] == expected_names

    def test_filters_by_date(
        self, api_client: APIClient, events_url: str, make_event: Callable[..., models.Event], future_date: datetime
    ) -> None:
        make_event(name="Today", date=future_date)
        make_event(name="Tomorrow", date=future_date + timedelta(days=1))

        response = api_client.get(events_url, {"date": future_date.date().isoformat()})

        assert [item["name"] for item in response.json()["items"]] == ["Today"]

    @pytest.mark.parametrize(
        ("params", "field"),
        [
            ({"take": 0}, "take"),
            ({"take": 101}, "take"),
            ({"skip": -1}, "skip"),
            ({"date": "not-a-date"}, "date"),
        ],
    )
    def test_rejects_invalid_query(
        self, api_client: APIClient, events_url: str, params: dict[str, Any], field: str
    ) -> None:
        response = api_client.get(events_url, params)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert error_of(response)["code"] == "validation_error"
        assert error_of(response)["field"] == field


@pytest.mark.django_db
class TestGetEvent:
    def test_is_public_and_returns_details(
        self, api_client: APIClient, event_url: Callable[[Any], str], event: models.Event, creator: models.User
    ) -> None:
        response = api_client.get(event_url(event.id))

        assert response.status_code == status.HTTP_200_OK
        body = response.json()
        assert list(body) == DETAIL_KEYS
        assert body["id"] == str(event.id)
        assert body["description"] == event.description
        assert body["contact_info"] == event.contact_info
        assert body["creator"] == {"id": str(creator.id), "name": creator.name}

    def test_returns_404_for_unknown_event(self, api_client: APIClient, event_url: Callable[[Any], str]) -> None:
        response = api_client.get(event_url(uuid4()))

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert error_of(response)["code"] == "not_found"

    def test_returns_404_for_malformed_id(self, api_client: APIClient, events_url: str) -> None:
        response = api_client.get(f"{events_url}not-a-uuid/")

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestCreateEvent:
    def test_creates_event_owned_by_requester(
        self, creator_client: APIClient, events_url: str, event_payload: dict[str, Any], creator: models.User
    ) -> None:
        response = creator_client.post(events_url, event_payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert list(response.json()) == ["id"]
        saved = models.Event.objects.get(id=response.json()["id"])
        assert saved.creator_id == creator.id
        assert saved.name == event_payload["name"]
        assert saved.date.isoformat() == event_payload["date"]

    def test_created_event_is_readable(
        self,
        creator_client: APIClient,
        api_client: APIClient,
        events_url: str,
        event_url: Callable[[Any], str],
        event_payload: dict[str, Any],
    ) -> None:
        event_id = creator_client.post(events_url, event_payload, format="json").json()["id"]

        response = api_client.get(event_url(event_id))

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["name"] == event_payload["name"]

    def test_requires_authentication(
        self, api_client: APIClient, events_url: str, event_payload: dict[str, Any]
    ) -> None:
        response = api_client.post(events_url, event_payload, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert error_of(response)["code"] == "invalid_credentials"
        assert not models.Event.objects.exists()

    def test_rejects_token_of_deleted_user(
        self,
        client_for: Callable[[models.User], APIClient],
        make_user: Callable[..., models.User],
        events_url: str,
        event_payload: dict[str, Any],
    ) -> None:
        ghost = make_user("ghost")
        client = client_for(ghost)
        ghost.delete()

        response = client.post(events_url, event_payload, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert not models.Event.objects.exists()

    @pytest.mark.parametrize(
        ("changes", "field"),
        [
            ({"name": None}, "name"),
            ({"name": "   "}, "name"),
            ({"name": "x" * 201}, "name"),
            ({"date": "tomorrow"}, "date"),
            ({"date": "2000-01-01T10:00:00Z"}, "date"),
            ({"location": ""}, "location"),
            ({"description": "x" * 5_001}, "description"),
            ({"contact_info": "x" * 256}, "contact_info"),
        ],
    )
    def test_rejects_invalid_data(
        self,
        creator_client: APIClient,
        events_url: str,
        event_payload: dict[str, Any],
        changes: dict[str, Any],
        field: str,
    ) -> None:
        payload = {key: value for key, value in {**event_payload, **changes}.items() if value is not None}

        response = creator_client.post(events_url, payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert error_of(response)["code"] == "validation_error"
        assert error_of(response)["field"] == field
        assert not models.Event.objects.exists()

    def test_rejects_malformed_json(self, creator_client: APIClient, events_url: str) -> None:
        response = creator_client.post(events_url, "{not json", content_type="application/json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
class TestUpdateEvent:
    def test_creator_updates_event(
        self,
        creator_client: APIClient,
        event_url: Callable[[Any], str],
        event: models.Event,
        event_payload: dict[str, Any],
    ) -> None:
        response = creator_client.put(event_url(event.id), event_payload, format="json")

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not response.content
        event.refresh_from_db()
        assert event.name == event_payload["name"]
        assert event.location == event_payload["location"]
        assert event.updated_at > event.created_at

    def test_requires_authentication(
        self,
        api_client: APIClient,
        event_url: Callable[[Any], str],
        event: models.Event,
        event_payload: dict[str, Any],
    ) -> None:
        response = api_client.put(event_url(event.id), event_payload, format="json")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        event.refresh_from_db()
        assert event.name == "Jazz Evening"

    def test_forbids_other_users(
        self,
        stranger_client: APIClient,
        event_url: Callable[[Any], str],
        event: models.Event,
        event_payload: dict[str, Any],
    ) -> None:
        response = stranger_client.put(event_url(event.id), event_payload, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert error_of(response)["code"] == "forbidden"
        event.refresh_from_db()
        assert event.name == "Jazz Evening"

    def test_returns_404_for_unknown_event(
        self, creator_client: APIClient, event_url: Callable[[Any], str], event_payload: dict[str, Any]
    ) -> None:
        response = creator_client.put(event_url(uuid4()), event_payload, format="json")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_rejects_changes_to_past_event(
        self,
        creator_client: APIClient,
        event_url: Callable[[Any], str],
        past_event: models.Event,
        event_payload: dict[str, Any],
    ) -> None:
        response = creator_client.put(event_url(past_event.id), event_payload, format="json")

        assert response.status_code == status.HTTP_409_CONFLICT
        assert error_of(response)["code"] == "conflict"
        past_event.refresh_from_db()
        assert past_event.name == "Past Gig"

    def test_rejects_moving_event_to_past(
        self,
        creator_client: APIClient,
        event_url: Callable[[Any], str],
        event: models.Event,
        event_payload: dict[str, Any],
    ) -> None:
        payload = {**event_payload, "date": "2000-01-01T10:00:00Z"}

        response = creator_client.put(event_url(event.id), payload, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert error_of(response)["field"] == "date"

    def test_rejects_incomplete_body(
        self,
        creator_client: APIClient,
        event_url: Callable[[Any], str],
        event: models.Event,
    ) -> None:
        response = creator_client.put(event_url(event.id), {"name": "Only name"}, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert error_of(response)["code"] == "validation_error"


@pytest.mark.django_db
class TestDeleteEvent:
    def test_creator_deletes_event(
        self, creator_client: APIClient, event_url: Callable[[Any], str], event: models.Event
    ) -> None:
        response = creator_client.delete(event_url(event.id))

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not models.Event.objects.filter(id=event.id).exists()

    def test_creator_can_delete_past_event(
        self, creator_client: APIClient, event_url: Callable[[Any], str], past_event: models.Event
    ) -> None:
        response = creator_client.delete(event_url(past_event.id))

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_requires_authentication(
        self, api_client: APIClient, event_url: Callable[[Any], str], event: models.Event
    ) -> None:
        response = api_client.delete(event_url(event.id))

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert models.Event.objects.filter(id=event.id).exists()

    def test_forbids_other_users(
        self, stranger_client: APIClient, event_url: Callable[[Any], str], event: models.Event
    ) -> None:
        response = stranger_client.delete(event_url(event.id))

        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert models.Event.objects.filter(id=event.id).exists()

    def test_returns_404_for_unknown_event(self, creator_client: APIClient, event_url: Callable[[Any], str]) -> None:
        response = creator_client.delete(event_url(uuid4()))

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert error_of(response)["code"] == "not_found"

    def test_returns_404_when_deleted_twice(
        self, creator_client: APIClient, event_url: Callable[[Any], str], event: models.Event
    ) -> None:
        creator_client.delete(event_url(event.id))

        response = creator_client.delete(event_url(event.id))

        assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
class TestAuthorizationHeader:
    @pytest.fixture
    def expired_token(self, creator: models.User) -> str:
        return encode_token(creator.to_identity(), ACCESS_TOKEN_TYPE, timedelta(minutes=-1))

    @pytest.fixture
    def refresh_token(self, creator: models.User) -> str:
        return issue_tokens(creator.to_identity()).refresh_token

    @pytest.mark.parametrize(
        "header",
        [
            "Token abc",
            "Bearer",
            "Bearer not-a-jwt",
            "Bearer {expired_token}",
            "Bearer {refresh_token}",
        ],
    )
    def test_rejects_bad_credentials(
        self,
        api_client: APIClient,
        event_url: Callable[[Any], str],
        event: models.Event,
        expired_token: str,
        refresh_token: str,
        header: str,
    ) -> None:
        api_client.credentials(
            HTTP_AUTHORIZATION=header.format(expired_token=expired_token, refresh_token=refresh_token)
        )

        response = api_client.delete(event_url(event.id))

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert error_of(response)["code"] == "invalid_credentials"
        assert models.Event.objects.filter(id=event.id).exists()

    def test_tokens_from_login_grant_access(
        self,
        api_client: APIClient,
        events_url: str,
        event_payload: dict[str, Any],
    ) -> None:
        registration = api_client.post(
            "/kmartists/register/",
            {
                "username": "drummer",
                "email": "drummer@example.com",
                "password": "Secret123",
                "password_confirmation": "Secret123",
            },
            format="json",
        )
        assert registration.status_code == status.HTTP_201_CREATED
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {registration.json()['token']}")

        response = api_client.post(events_url, event_payload, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert models.Event.objects.get().creator.name == "drummer"

