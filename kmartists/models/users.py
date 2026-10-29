from uuid import uuid4

from django.db import models

from kmartists.domain.users import UserReference

PLACEHOLDER_AUTHOR_NAME = "guest"


class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=50, unique=True)
    looking_for_band = models.BooleanField(default=False)
    location = models.CharField(max_length=200, blank=True)
    instruments = models.JSONField(default=list)
    favorite_bands = models.JSONField(default=list)

    class Meta:
        db_table = "users"

    @classmethod
    def placeholder_author(cls) -> "User":
        return cls.objects.get(name=PLACEHOLDER_AUTHOR_NAME)

    def to_reference(self) -> UserReference:
        return UserReference(id=self.id, name=self.name)
