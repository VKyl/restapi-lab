from collections.abc import Sequence
from dataclasses import replace
from uuid import UUID

from kmartists.domain.articles import Article, ArticleDetails, ArticleSummary, Section
from kmartists.domain.errors import ConflictError, ForbiddenError, NotFoundError
from kmartists.interfaces.articles import ArticleRepository
from kmartists.use_cases.users import UserUseCase
from kmartists.utils.pagination import Page


class ArticleUseCase:
    def __init__(self, articles: ArticleRepository, users: UserUseCase) -> None:
        self._articles = articles
        self._users = users

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

    def create_article(self, article: Article, author_id: UUID) -> UUID:
        self._users.get_identity(author_id)
        article.validate()
        if self._articles.artist_exists(article.artist):
            raise ConflictError(f"An article about {article.artist} already exists.")
        return self._articles.create_article(article, author_id)

    def edit_article(
        self, article_id: UUID, contributor_id: UUID, genres: Sequence[str], body: Sequence[Section]
    ) -> None:
        self._users.get_identity(contributor_id)
        article = replace(self.get_article(article_id), genres=genres, body=body)
        article.validate()
        self._articles.update_article(article_id, article, contributor_id)

    def delete_article(self, article_id: UUID, user_id: UUID) -> None:
        article = self.get_article(article_id)
        if all(contributor.id != user_id for contributor in article.contributors):
            raise ForbiddenError("Only article contributors can delete this article.")
        self._articles.delete_article(article_id)
