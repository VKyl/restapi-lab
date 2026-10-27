from typing import Protocol
from uuid import UUID

from kmartists.domain.articles import Article, ArticleDetails, ArticleSummary
from kmartists.utils.pagination import Page


class ArticleRepository(Protocol):
    def list_summaries(
        self, take: int, skip: int, genre: str | None, search_query: str | None
    ) -> Page[ArticleSummary]: ...

    def find_details(self, article_id: UUID) -> ArticleDetails | None: ...

    def artist_exists(self, artist: str) -> bool: ...

    def create_article(self, article: Article) -> UUID: ...

    def update_article(self, article_id: UUID, article: Article) -> None: ...

    def delete_article(self, article_id: UUID) -> None: ...
