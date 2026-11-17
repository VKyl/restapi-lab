from typing import Any
from uuid import UUID

from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import serializers, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from kmartists import models
from kmartists.domain.articles import Article, ArticleDetails, ArticleSummary, Section
from kmartists.use_cases.articles import ArticleUseCase
from kmartists.use_cases.users import UserUseCase
from kmartists.utils.authentication import authenticated_user_id
from kmartists.utils.openapi import (
    NOT_FOUND,
    REQUIRES_TOKEN,
    UNAUTHENTICATED,
    VALIDATION_FAILED,
    CreatedResponse,
    error_example,
    error_response,
)
from kmartists.utils.pagination import Page, PageQuery

article_use_case = ArticleUseCase(
    articles=models.Article, users=UserUseCase(users=models.User, articles=models.Article)
)


class ListArticlesRequest(PageQuery):
    genre = serializers.CharField(default=None, help_text="Only articles with this genre.")
    search_query = serializers.CharField(default=None, help_text="Case-insensitive search in artist name.")


class SectionRequest(serializers.Serializer):
    title = serializers.CharField(allow_blank=True)
    content = serializers.CharField(allow_blank=True)

    def to_internal_value(self, data: Any) -> Section:
        return Section(**super().to_internal_value(data))


class UpdateArticleRequest(serializers.Serializer):
    genres = serializers.ListField(child=serializers.CharField(allow_blank=True))
    body = SectionRequest(many=True)


class CreateArticleRequest(serializers.Serializer):
    artist = serializers.CharField(allow_blank=True)
    genres = serializers.ListField(child=serializers.CharField(allow_blank=True))
    body = SectionRequest(many=True)

    def to_internal_value(self, data: Any) -> Article:
        return Article(**super().to_internal_value(data))


class GenreListResponse(serializers.Serializer):
    items = serializers.ListField(child=serializers.CharField())


ARTICLE_ID = OpenApiParameter("article_id", UUID, OpenApiParameter.PATH, description="Article id.")


class ArticleCollectionController(APIView):
    @extend_schema(
        tags=["Artists"],
        operation_id="list_articles",
        summary="List artist articles",
        parameters=[ListArticlesRequest],
        responses={200: Page[ArticleSummary], 400: VALIDATION_FAILED},
    )
    def get(self, request: Request) -> Response:
        query = ListArticlesRequest(data=request.query_params)
        query.is_valid(raise_exception=True)
        page = article_use_case.list_articles(**query.validated_data)
        return Response(page.serialize())

    @extend_schema(
        tags=["Artists"],
        operation_id="create_article",
        summary="Create artist article",
        description="The requester becomes the author and the first contributor.",
        auth=REQUIRES_TOKEN,
        request=CreateArticleRequest,
        responses={
            201: CreatedResponse,
            400: VALIDATION_FAILED,
            401: UNAUTHENTICATED,
            409: error_response(
                "An article about this artist already exists.",
                error_example("Duplicate", "conflict", "An article about Metallica already exists."),
            ),
        },
    )
    def post(self, request: Request) -> Response:
        user_id = authenticated_user_id(request)
        body = CreateArticleRequest(data=request.data)
        body.is_valid(raise_exception=True)
        article_id = article_use_case.create_article(body.validated_data, user_id)
        return Response({"id": article_id}, status=status.HTTP_201_CREATED)


class GenreCollectionController(APIView):
    @extend_schema(
        tags=["Artists"],
        operation_id="list_genres",
        summary="List genres",
        description="All unique genres used in artist articles, sorted alphabetically.",
        responses={200: GenreListResponse},
    )
    def get(self, request: Request) -> Response:
        return Response({"items": article_use_case.list_genres()})


class ArticleController(APIView):
    @extend_schema(
        tags=["Artists"],
        operation_id="get_article",
        summary="Get artist article",
        parameters=[ARTICLE_ID],
        responses={200: ArticleDetails, 404: NOT_FOUND},
    )
    def get(self, request: Request, article_id: UUID) -> Response:
        return Response(article_use_case.get_article(article_id).serialize())

    @extend_schema(
        tags=["Artists"],
        operation_id="update_article",
        summary="Edit artist article",
        description="Any signed-in user can edit; the editor is added to contributors.",
        auth=REQUIRES_TOKEN,
        parameters=[ARTICLE_ID],
        request=UpdateArticleRequest,
        responses={
            204: OpenApiResponse(description="Article updated."),
            400: VALIDATION_FAILED,
            401: UNAUTHENTICATED,
            404: NOT_FOUND,
        },
    )
    def put(self, request: Request, article_id: UUID) -> Response:
        user_id = authenticated_user_id(request)
        body = UpdateArticleRequest(data=request.data)
        body.is_valid(raise_exception=True)
        article_use_case.edit_article(article_id, user_id, **body.validated_data)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @extend_schema(
        tags=["Artists"],
        operation_id="delete_article",
        summary="Delete artist article",
        description="Only the article author can delete it.",
        auth=REQUIRES_TOKEN,
        parameters=[ARTICLE_ID],
        responses={
            204: OpenApiResponse(description="Article deleted."),
            401: UNAUTHENTICATED,
            403: error_response(
                "The requester is not the article author.",
                error_example("Not author", "forbidden", "Only the article author can delete this article."),
            ),
            404: NOT_FOUND,
        },
    )
    def delete(self, request: Request, article_id: UUID) -> Response:
        article_use_case.delete_article(article_id, authenticated_user_id(request))
        return Response(status=status.HTTP_204_NO_CONTENT)
