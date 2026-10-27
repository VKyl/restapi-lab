from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from uuid import UUID

from kmartists.domain.errors import ValidationError
from kmartists.domain.users import UserReference
from kmartists.utils.serialization import SerializableMixin
from kmartists.utils.validation import has_duplicates, require_text

MAX_ARTIST_LENGTH = 200
MAX_GENRES = 10
MAX_GENRE_LENGTH = 50
MAX_SECTIONS = 50
MAX_SECTION_TITLE_LENGTH = 200
MAX_SECTION_CONTENT_LENGTH = 20_000


@dataclass(frozen=True)
class Section:
    title: str
    content: str


@dataclass(frozen=True)
class Article(SerializableMixin):
    artist: str
    genres: Sequence[str]
    body: Sequence[Section]

    def validate(self) -> None:
        require_text("artist", self.artist, MAX_ARTIST_LENGTH)
        self._validate_genres()
        self._validate_body()

    def _validate_genres(self) -> None:
        if not self.genres:
            raise ValidationError("genres", "Provide at least one genre.")
        if len(self.genres) > MAX_GENRES:
            raise ValidationError("genres", f"Provide no more than {MAX_GENRES} genres.")
        for index, genre in enumerate(self.genres):
            require_text(f"genres[{index}]", genre, MAX_GENRE_LENGTH)
        if has_duplicates(self.genres):
            raise ValidationError("genres", "Genres must be unique.")

    def _validate_body(self) -> None:
        if not self.body:
            raise ValidationError("body", "Provide at least one section.")
        if len(self.body) > MAX_SECTIONS:
            raise ValidationError("body", f"Provide no more than {MAX_SECTIONS} sections.")
        for index, section in enumerate(self.body):
            require_text(f"body[{index}].title", section.title, MAX_SECTION_TITLE_LENGTH)
            require_text(f"body[{index}].content", section.content, MAX_SECTION_CONTENT_LENGTH)
        if has_duplicates(section.title for section in self.body):
            raise ValidationError("body", "Section titles must be unique.")


@dataclass(frozen=True)
class ArticleSummary(SerializableMixin):
    id: UUID
    artist: str
    genres: Sequence[str]


@dataclass(frozen=True)
class ArticleDetails(Article):
    id: UUID
    contributors: Sequence[UserReference]
    created_at: datetime
    updated_at: datetime

    def serialize(self) -> dict[str, Any]:
        return {"id": self.id, **super().serialize()}
