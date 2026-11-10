from typing import Any
from uuid import UUID

from rest_framework import serializers, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from kmartists import models
from kmartists.domain.events import Event
from kmartists.use_cases.events import EventUseCase
from kmartists.use_cases.users import UserUseCase
from kmartists.utils.authentication import authenticated_user_id
from kmartists.utils.pagination import PageQuery

event_use_case = EventUseCase(events=models.Event, users=UserUseCase(users=models.User, articles=models.Article))


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
        page = event_use_case.list_events(**query.validated_data)
        return Response(page.serialize())

    def post(self, request: Request) -> Response:
        user_id = authenticated_user_id(request)
        body = SaveEventRequest(data=request.data)
        body.is_valid(raise_exception=True)
        event_id = event_use_case.create_event(body.validated_data, user_id)
        return Response({"id": event_id}, status=status.HTTP_201_CREATED)


class EventController(APIView):
    def get(self, request: Request, event_id: UUID) -> Response:
        return Response(event_use_case.get_event(event_id).serialize())

    def put(self, request: Request, event_id: UUID) -> Response:
        user_id = authenticated_user_id(request)
        body = SaveEventRequest(data=request.data)
        body.is_valid(raise_exception=True)
        event_use_case.update_event(event_id, body.validated_data, user_id)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request: Request, event_id: UUID) -> Response:
        event_use_case.delete_event(event_id, authenticated_user_id(request))
        return Response(status=status.HTTP_204_NO_CONTENT)
