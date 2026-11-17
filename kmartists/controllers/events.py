from typing import Any
from uuid import UUID

from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import serializers, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from kmartists import models
from kmartists.domain.events import (
    MAX_CONTACT_INFO_LENGTH,
    MAX_DESCRIPTION_LENGTH,
    MAX_LOCATION_LENGTH,
    MAX_NAME_LENGTH,
    Event,
    EventDetails,
    EventSummary,
)
from kmartists.use_cases.events import EventUseCase
from kmartists.use_cases.users import UserUseCase
from kmartists.utils.authentication import authenticated_user_id
from kmartists.utils.openapi import (
    REQUIRES_TOKEN,
    UNAUTHENTICATED,
    VALIDATION_FAILED,
    CreatedResponse,
    error_example,
    error_response,
)
from kmartists.utils.pagination import Page, PageQuery

event_use_case = EventUseCase(events=models.Event, users=UserUseCase(users=models.User, articles=models.Article))


class ListEventsRequest(PageQuery):
    search_query = serializers.CharField(
        default=None, help_text="Case-insensitive search in event name and description."
    )
    location = serializers.CharField(default=None, help_text="Case-insensitive search in event location.")
    date = serializers.DateField(default=None, source="on_date", help_text="Only events taking place on this day.")


class SaveEventRequest(serializers.Serializer):
    name = serializers.CharField(allow_blank=True, help_text=f"Required, at most {MAX_NAME_LENGTH} characters.")
    date = serializers.DateTimeField(help_text="ISO 8601 date and time, must be in the future.")
    location = serializers.CharField(
        allow_blank=True, help_text=f"Required, at most {MAX_LOCATION_LENGTH} characters."
    )
    description = serializers.CharField(
        allow_blank=True, help_text=f"Required, at most {MAX_DESCRIPTION_LENGTH} characters."
    )
    contact_info = serializers.CharField(
        allow_blank=True, help_text=f"Required, at most {MAX_CONTACT_INFO_LENGTH} characters."
    )

    def to_internal_value(self, data: Any) -> Event:
        return Event(**super().to_internal_value(data))


EVENT_ID = OpenApiParameter("event_id", UUID, OpenApiParameter.PATH, description="Event id.")
EVENT_EXAMPLE = {
    "name": "Metal Fest",
    "date": "2027-06-20T18:00:00Z",
    "location": "Kyiv, Atlas",
    "description": "Open-air metal festival with local bands.",
    "contact_info": "tickets@metalfest.example",
}
SAVE_EVENT_EXAMPLE = OpenApiExample("Event", value=EVENT_EXAMPLE, request_only=True)
NOT_EVENT_CREATOR = error_response(
    "The requester is not the event creator.",
    error_example("Not creator", "forbidden", "Only the event creator can change this event."),
)
EVENT_NOT_FOUND = error_response(
    "The event does not exist or the id is not a valid UUID.",
    error_example("Not found", "not_found", "Event 3fa85f64-5717-4562-b3fc-2c963f66afa6 does not exist."),
)


class EventCollectionController(APIView):
    @extend_schema(
        tags=["Events"],
        operation_id="list_events",
        summary="List events",
        description="Public. Returns events ordered by date, soonest first.",
        parameters=[ListEventsRequest],
        responses={
            200: OpenApiResponse(
                Page[EventSummary],
                description="A page of events.",
                examples=[
                    OpenApiExample(
                        "Page",
                        value={
                            "items": [
                                {
                                    "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                                    "name": EVENT_EXAMPLE["name"],
                                    "date": EVENT_EXAMPLE["date"],
                                    "location": EVENT_EXAMPLE["location"],
                                }
                            ],
                            "pagination": {"current_page": 1, "total_pages": 1, "total_records": 1},
                        },
                    )
                ],
            ),
            400: VALIDATION_FAILED,
        },
    )
    def get(self, request: Request) -> Response:
        query = ListEventsRequest(data=request.query_params)
        query.is_valid(raise_exception=True)
        page = event_use_case.list_events(**query.validated_data)
        return Response(page.serialize())

    @extend_schema(
        tags=["Events"],
        operation_id="create_event",
        summary="Create event",
        description="Creates a music event announcement owned by the requester.",
        auth=REQUIRES_TOKEN,
        request=SaveEventRequest,
        examples=[SAVE_EVENT_EXAMPLE],
        responses={
            201: OpenApiResponse(
                CreatedResponse,
                description="Event created.",
                examples=[
                    OpenApiExample("Created", value={"id": "3fa85f64-5717-4562-b3fc-2c963f66afa6"}, response_only=True)
                ],
            ),
            400: VALIDATION_FAILED,
            401: UNAUTHENTICATED,
        },
    )
    def post(self, request: Request) -> Response:
        user_id = authenticated_user_id(request)
        body = SaveEventRequest(data=request.data)
        body.is_valid(raise_exception=True)
        event_id = event_use_case.create_event(body.validated_data, user_id)
        return Response({"id": event_id}, status=status.HTTP_201_CREATED)


class EventController(APIView):
    @extend_schema(
        tags=["Events"],
        operation_id="get_event",
        summary="Get event",
        description="Public. Returns detailed info about one event.",
        parameters=[EVENT_ID],
        responses={
            200: OpenApiResponse(
                EventDetails,
                description="Event details.",
                examples=[
                    OpenApiExample(
                        "Event",
                        value={
                            "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
                            **EVENT_EXAMPLE,
                            "creator": {"id": "6f1c2a2e-8a5b-4b8e-9d1e-2f7d4c3b1a00", "name": "creator"},
                            "created_at": "2026-11-17T10:00:00Z",
                            "updated_at": "2026-11-17T10:00:00Z",
                        },
                    )
                ],
            ),
            404: EVENT_NOT_FOUND,
        },
    )
    def get(self, request: Request, event_id: UUID) -> Response:
        return Response(event_use_case.get_event(event_id).serialize())

    @extend_schema(
        tags=["Events"],
        operation_id="update_event",
        summary="Update event",
        description="Replaces all event fields. Only the event creator can do this, and only before the event.",
        auth=REQUIRES_TOKEN,
        parameters=[EVENT_ID],
        request=SaveEventRequest,
        examples=[SAVE_EVENT_EXAMPLE],
        responses={
            204: OpenApiResponse(description="Event updated."),
            400: VALIDATION_FAILED,
            401: UNAUTHENTICATED,
            403: NOT_EVENT_CREATOR,
            404: EVENT_NOT_FOUND,
            409: error_response(
                "The event has already taken place.",
                error_example("Past event", "conflict", "Events that have already taken place cannot be changed."),
            ),
        },
    )
    def put(self, request: Request, event_id: UUID) -> Response:
        user_id = authenticated_user_id(request)
        body = SaveEventRequest(data=request.data)
        body.is_valid(raise_exception=True)
        event_use_case.update_event(event_id, body.validated_data, user_id)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        tags=["Events"],
        operation_id="delete_event",
        summary="Delete event",
        description="Deletes the event. Only the event creator can do this; past events can be deleted too.",
        auth=REQUIRES_TOKEN,
        parameters=[EVENT_ID],
        responses={
            204: OpenApiResponse(description="Event deleted."),
            401: UNAUTHENTICATED,
            403: NOT_EVENT_CREATOR,
            404: EVENT_NOT_FOUND,
        },
    )
    def delete(self, request: Request, event_id: UUID) -> Response:
        event_use_case.delete_event(event_id, authenticated_user_id(request))
        return Response(status=status.HTTP_204_NO_CONTENT)
