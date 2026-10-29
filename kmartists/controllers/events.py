from typing import Any
from uuid import UUID

from rest_framework import serializers, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from kmartists import models
from kmartists.domain.events import Event
from kmartists.use_cases.events import EventUseCases
from kmartists.utils.pagination import PageQuery

event_use_cases = EventUseCases(events=models.Event)


class ListEventsRequest(PageQuery):
    search_query = serializers.CharField(default=None)
    location = serializers.CharField(default=None)
    date = serializers.DateField(default=None, source="on_date")


class SaveEventRequest(serializers.Serializer):
    name = serializers.CharField(allow_blank=True)
    date = serializers.DateTimeField()
    location = serializers.CharField(allow_blank=True)
    description = serializers.CharField(allow_blank=True)
    contact_info = serializers.CharField(allow_blank=True)

    def to_internal_value(self, data: Any) -> Event:
        return Event(**super().to_internal_value(data))


class EventCollectionController(APIView):
    def get(self, request: Request) -> Response:
        query = ListEventsRequest(data=request.query_params)
        query.is_valid(raise_exception=True)
        page = event_use_cases.list_events(**query.validated_data)
        return Response(page.serialize())

    def post(self, request: Request) -> Response:
        body = SaveEventRequest(data=request.data)
        body.is_valid(raise_exception=True)
        event_id = event_use_cases.create_event(body.validated_data)
        return Response({"id": event_id}, status=status.HTTP_201_CREATED)


class EventController(APIView):
    def get(self, request: Request, event_id: UUID) -> Response:
        return Response(event_use_cases.get_event(event_id).serialize())

    def put(self, request: Request, event_id: UUID) -> Response:
        body = SaveEventRequest(data=request.data)
        body.is_valid(raise_exception=True)
        event_use_cases.update_event(event_id, body.validated_data)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request: Request, event_id: UUID) -> Response:
        event_use_cases.delete_event(event_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
