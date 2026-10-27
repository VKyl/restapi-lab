from typing import Any
from uuid import UUID

from rest_framework import serializers, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from kmartists import models
from kmartists.domain.articles import Article, Section
from kmartists.use_cases.articles import ArticleUseCases
from kmartists.utils.pagination import PageQuery

article_use_cases = ArticleUseCases(articles=models.Article)


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
        page = article_use_cases.list_articles(**query.validated_data)
        return Response(page.serialize())

    def post(self, request: Request) -> Response:
        body = CreateArticleRequest(data=request.data)
        body.is_valid(raise_exception=True)
        article_id = article_use_cases.create_article(body.validated_data)
        return Response({"id": article_id}, status=status.HTTP_201_CREATED)


class ArticleController(APIView):
    def get(self, request: Request, article_id: UUID) -> Response:
        return Response(article_use_cases.get_article(article_id).serialize())

    def put(self, request: Request, article_id: UUID) -> Response:
        body = UpdateArticleRequest(data=request.data)
        body.is_valid(raise_exception=True)
        article_use_cases.edit_article(article_id, **body.validated_data)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def delete(self, request: Request, article_id: UUID) -> Response:
        article_use_cases.delete_article(article_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
