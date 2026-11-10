from typing import Any
from uuid import UUID

from rest_framework import serializers, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from kmartists import models
from kmartists.domain.articles import Article, Section
from kmartists.use_cases.articles import ArticleUseCase
from kmartists.use_cases.users import UserUseCase
from kmartists.utils.authentication import authenticated_user_id
from kmartists.utils.pagination import PageQuery

article_use_case = ArticleUseCase(
    articles=models.Article, users=UserUseCase(users=models.User, articles=models.Article)
)


class ListArticlesRequest(PageQuery):
    genre = serializers.CharField(default=None)
    search_query = serializers.CharField(default=None)


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


class ArticleCollectionController(APIView):
    def get(self, request: Request) -> Response:
        query = ListArticlesRequest(data=request.query_params)
        query.is_valid(raise_exception=True)
        page = article_use_case.list_articles(**query.validated_data)
        return Response(page.serialize())

    def post(self, request: Request) -> Response:
        user_id = authenticated_user_id(request)
        body = CreateArticleRequest(data=request.data)
        body.is_valid(raise_exception=True)
        article_id = article_use_case.create_article(body.validated_data, user_id)
        return Response({"id": article_id}, status=status.HTTP_201_CREATED)


class GenreCollectionController(APIView):
    def get(self, request: Request) -> Response:
        return Response({"items": article_use_case.list_genres()})


class ArticleController(APIView):
    def get(self, request: Request, article_id: UUID) -> Response:
        return Response(article_use_case.get_article(article_id).serialize())

    def put(self, request: Request, article_id: UUID) -> Response:
        user_id = authenticated_user_id(request)
        body = UpdateArticleRequest(data=request.data)
        body.is_valid(raise_exception=True)
        article_use_case.edit_article(article_id, user_id, **body.validated_data)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request: Request, article_id: UUID) -> Response:
        article_use_case.delete_article(article_id, authenticated_user_id(request))
        return Response(status=status.HTTP_204_NO_CONTENT)
