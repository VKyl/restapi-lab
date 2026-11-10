from uuid import UUID, uuid4

from django.contrib.auth.hashers import check_password, make_password
from django.db import IntegrityError, models

from kmartists.domain.errors import ConflictError
from kmartists.domain.users import (
    MAX_EMAIL_LENGTH,
    MAX_FIRST_NAME_LENGTH,
    MAX_LAST_NAME_LENGTH,
    MAX_MICROSOFT_ID_LENGTH,
    MAX_USERNAME_LENGTH,
    MicrosoftRegistration,
    PasswordRegistration,
    UserIdentity,
    UserReference,
)

PLACEHOLDER_AUTHOR_NAME = "guest"


class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=MAX_USERNAME_LENGTH, unique=True)
    first_name = models.CharField(max_length=MAX_FIRST_NAME_LENGTH, blank=True)
    last_name = models.CharField(max_length=MAX_LAST_NAME_LENGTH, blank=True)
    email = models.EmailField(max_length=MAX_EMAIL_LENGTH, unique=True, null=True)
    password = models.CharField(max_length=128, blank=True)
    microsoft_id = models.CharField(max_length=MAX_MICROSOFT_ID_LENGTH, unique=True, null=True)
    looking_for_band = models.BooleanField(default=False)
    location = models.CharField(max_length=200, blank=True)
    instruments = models.JSONField(default=list)
    favorite_bands = models.JSONField(default=list)

    class Meta:
        db_table = "users"

    @classmethod
    def placeholder_author(cls) -> "User":
        return cls.objects.get(name=PLACEHOLDER_AUTHOR_NAME)

    @classmethod
    def username_exists(cls, username: str) -> bool:
        return cls.objects.filter(name__iexact=username).exists()

    @classmethod
    def email_exists(cls, email: str) -> bool:
        return cls.objects.filter(email__iexact=email).exists()

    @classmethod
    def microsoft_account_exists(cls, microsoft_id: str) -> bool:
        return cls.objects.filter(microsoft_id=microsoft_id).exists()

    @classmethod
    def create_user(cls, registration: PasswordRegistration) -> UserIdentity:
        try:
            record = cls.objects.create(
                name=registration.username,
                first_name=registration.first_name,
                last_name=registration.last_name,
                email=registration.email,
                password=make_password(registration.password),
            )
        except IntegrityError as error:
            raise ConflictError("A user with this username or email already exists.") from error
        return record.to_identity()

    @classmethod
    def create_microsoft_user(cls, registration: MicrosoftRegistration) -> UserIdentity:
        try:
            record = cls.objects.create(
                name=registration.username,
                first_name=registration.first_name,
                last_name=registration.last_name,
                email=registration.email,
                microsoft_id=registration.microsoft_id,
            )
        except IntegrityError as error:
            raise ConflictError("A user with this username, email or Microsoft account already exists.") from error
        return record.to_identity()

    @classmethod
    def authenticate(cls, username: str, password: str) -> UserIdentity | None:
        user = cls.objects.filter(name=username).first()
        return user.to_identity() if user and check_password(password, user.password) else None

    @classmethod
    def find_identity(cls, user_id: UUID) -> UserIdentity | None:
        user = cls.objects.filter(id=user_id).first()
        return user.to_identity() if user else None

    def to_reference(self) -> UserReference:
        return UserReference(id=self.id, name=self.name)

    def to_identity(self) -> UserIdentity:
        return UserIdentity(id=self.id, username=self.name, first_name=self.first_name, last_name=self.last_name)
