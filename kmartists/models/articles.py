import json
from collections.abc import Sequence
from dataclasses import asdict
from uuid import UUID, uuid4

from django.db import IntegrityError, models
from django.db.models import Prefetch, TextField
from django.db.models.functions import Cast, Lower

from kmartists.domain.articles import Article as ArticleEntity
from kmartists.domain.articles import MAX_ARTIST_LENGTH, ArticleDetails, ArticleSummary, Section
from kmartists.domain.errors import ConflictError, NotFoundError
from kmartists.models.users import User
from kmartists.utils.pagination import Page, paginate


class Article(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    artist = models.CharField(max_length=MAX_ARTIST_LENGTH)
    genres = models.JSONField(default=list)
    body = models.JSONField(default=list)
    contributors = models.ManyToManyField(User, related_name="articles", db_table="user_article")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "articles"
        constraints = [
            models.UniqueConstraint(Lower("artist"), name="unique_article_artist_case_insensitive"),
        ]

    @classmethod
    def list_summaries(
        cls, take: int, skip: int, genre: str | None, search_query: str | None
    ) -> Page[ArticleSummary]:
        queryset = cls.objects.order_by(Lower("artist"))
        if genre:
            queryset = queryset.annotate(genres_text=Cast("genres", TextField())).filter(
                genres_text__icontains=json.dumps(genre)
            )
        if search_query:
            queryset = queryset.filter(artist__icontains=search_query)
        return paginate(queryset, take, skip, cls.to_summary)

    @classmethod
    def find_details(cls, article_id: UUID) -> ArticleDetails | None:
        contributors = User.objects.order_by(Lower("name"))
        article = (
            cls.objects.prefetch_related(Prefetch("contributors", queryset=contributors)).filter(id=article_id).first()
        )
        return article.to_details() if article else None

    @classmethod
    def all_genres(cls) -> list[str]:
        unique_genres: dict[str, str] = {}
        for genres in cls.objects.values_list("genres", flat=True):
            for genre in genres:
                unique_genres.setdefault(genre.casefold(), genre)
        return sorted(unique_genres.values(), key=str.casefold)

    @classmethod
    def artist_exists(cls, artist: str) -> bool:
        return cls.objects.filter(artist__iexact=artist).exists()

    @classmethod
    def create_article(cls, article: ArticleEntity) -> UUID:
        try:
            record = cls.objects.create(
                artist=article.artist,
                genres=list(article.genres),
                body=serialize_body(article.body),
            )
        except IntegrityError as error:
            raise ConflictError(f"An article about {article.artist} already exists.") from error
        record.contributors.add(User.placeholder_author())
        return record.id

    @classmethod
    def update_article(cls, article_id: UUID, article: ArticleEntity) -> None:
        record = cls.objects.filter(id=article_id).first()
        if record is None:
            raise NotFoundError(f"Article {article_id} does not exist.")
        record.genres = list(article.genres)
        record.body = serialize_body(article.body)
        record.save()
        record.contributors.add(User.placeholder_author())

    @classmethod
    def delete_article(cls, article_id: UUID) -> None:
        cls.objects.filter(id=article_id).delete()

    def to_summary(self) -> ArticleSummary:
        return ArticleSummary(id=self.id, artist=self.artist, genres=tuple(self.genres))

    def to_details(self) -> ArticleDetails:
        return ArticleDetails(
            id=self.id,
            artist=self.artist,
            genres=tuple(self.genres),
            body=tuple(Section(**section) for section in self.body),
            contributors=tuple(contributor.to_reference() for contributor in self.contributors.all()),
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


def serialize_body(body: Sequence[Section]) -> list[dict[str, str]]:
    return [asdict(section) for section in body]
