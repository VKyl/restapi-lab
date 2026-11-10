from uuid import UUID, uuid4

from django.contrib.auth.hashers import check_password, make_password
from django.db import IntegrityError, models
from django.db.models.functions import Lower

from kmartists.domain.errors import ConflictError, NotFoundError
from kmartists.domain.users import (
    MAX_EMAIL_LENGTH,
    MAX_FIRST_NAME_LENGTH,
    MAX_LAST_NAME_LENGTH,
    MAX_LOCATION_LENGTH,
    MAX_MICROSOFT_ID_LENGTH,
    MAX_USERNAME_LENGTH,
    MicrosoftRegistration,
    MusicianSummary,
    PasswordRegistration,
    Profile,
    ProfileDetails,
    UserIdentity,
    UserReference,
)
from kmartists.utils.pagination import Page, paginate


class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=MAX_USERNAME_LENGTH, unique=True)
    first_name = models.CharField(max_length=MAX_FIRST_NAME_LENGTH, blank=True)
    last_name = models.CharField(max_length=MAX_LAST_NAME_LENGTH, blank=True)
    email = models.EmailField(max_length=MAX_EMAIL_LENGTH, unique=True, null=True)
    password = models.CharField(max_length=128, blank=True)
    microsoft_id = models.CharField(max_length=MAX_MICROSOFT_ID_LENGTH, unique=True, null=True)
    looking_for_band = models.BooleanField(default=False)
    location = models.CharField(max_length=MAX_LOCATION_LENGTH, blank=True)
    instruments = models.JSONField(default=list)
    favorite_bands = models.JSONField(default=list)

    class Meta:
        db_table = "users"

    @classmethod
    def list_musicians(
        cls, take: int, skip: int, location: str | None, excluded_user_id: UUID | None
    ) -> Page[MusicianSummary]:
        queryset = cls.objects.filter(looking_for_band=True).order_by(Lower("name"))
        if excluded_user_id:
            queryset = queryset.exclude(id=excluded_user_id)
        if location:
            queryset = queryset.filter(location__icontains=location)
        return paginate(queryset, take, skip, cls.to_musician)

    @classmethod
    def find_profile(cls, user_id: UUID) -> ProfileDetails | None:
        user = cls.objects.filter(id=user_id).first()
        return user.to_profile() if user else None

    @classmethod
    def update_profile(cls, user_id: UUID, profile: Profile) -> None:
        try:
            updated = cls.objects.filter(id=user_id).update(
                name=profile.name,
                instruments=list(profile.instruments),
                favorite_bands=list(profile.favorite_bands),
                looking_for_band=profile.looking_for_band,
                location=profile.location,
            )
        except IntegrityError as error:
            raise ConflictError(f"Username {profile.name} is already taken.") from error
        if not updated:
            raise NotFoundError(f"User {user_id} does not exist.")

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
    def authenticate(cls, login: str, password: str) -> UserIdentity | None:
        lookup = {"email__iexact": login} if "@" in login else {"name": login}
        user = cls.objects.filter(**lookup).first()
        return user.to_identity() if user and check_password(password, user.password) else None

    @classmethod
    def find_identity(cls, user_id: UUID) -> UserIdentity | None:
        user = cls.objects.filter(id=user_id).first()
        return user.to_identity() if user else None

    @classmethod
    def find_microsoft_identity(cls, microsoft_id: str) -> UserIdentity | None:
        user = cls.objects.filter(microsoft_id=microsoft_id).first()
        return user.to_identity() if user else None

    def to_reference(self) -> UserReference:
        return UserReference(id=self.id, name=self.name)

    def to_identity(self) -> UserIdentity:
        return UserIdentity(id=self.id, username=self.name, first_name=self.first_name, last_name=self.last_name)

    def to_musician(self) -> MusicianSummary:
        return MusicianSummary(
            id=self.id,
            name=self.name,
            instruments=tuple(self.instruments),
            favorite_bands=tuple(self.favorite_bands),
            location=self.location,
        )

    def to_profile(self) -> ProfileDetails:
        return ProfileDetails(
            id=self.id,
            name=self.name,
            instruments=tuple(self.instruments),
            favorite_bands=tuple(self.favorite_bands),
            looking_for_band=self.looking_for_band,
            location=self.location,
        )
