from collections.abc import Sequence
from dataclasses import replace
from uuid import UUID

from kmartists.domain.articles import Article, ArticleDetails, ArticleSummary, Section
from kmartists.domain.errors import ConflictError, NotFoundError
from kmartists.interfaces.articles import ArticleRepository
from kmartists.utils.pagination import Page


class ArticleUseCases:
    def __init__(self, articles: ArticleRepository) -> None:
        self._articles = articles

    def list_articles(
        self, take: int, skip: int, genre: str | None, search_query: str | None
    ) -> Page[ArticleSummary]:
        return self._articles.list_summaries(take, skip, genre, search_query)

    def get_article(self, article_id: UUID) -> ArticleDetails:
        article = self._articles.find_details(article_id)
        if article is None:
            raise NotFoundError(f"Article {article_id} does not exist.")
        return article

    def list_genres(self) -> list[str]:
        return self._articles.all_genres()

    def create_article(self, article: Article) -> UUID:
        article.validate()
        if self._articles.artist_exists(article.artist):
            raise ConflictError(f"An article about {article.artist} already exists.")
        return self._articles.create_article(article)

    def edit_article(self, article_id: UUID, genres: Sequence[str], body: Sequence[Section]) -> None:
        article = replace(self.get_article(article_id), genres=genres, body=body)
        article.validate()
        self._articles.update_article(article_id, article)

    def delete_article(self, article_id: UUID) -> None:
        self.get_article(article_id)
        self._articles.delete_article(article_id)
