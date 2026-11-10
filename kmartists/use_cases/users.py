from uuid import UUID

from kmartists.domain.articles import ArticleSummary
from kmartists.domain.errors import AuthenticationError, ConflictError, ForbiddenError, NotFoundError
from kmartists.domain.users import (
    MicrosoftRegistration,
    MusicianSummary,
    PasswordRegistration,
    Profile,
    ProfileDetails,
    Registration,
    UserIdentity,
)
from kmartists.interfaces.articles import ArticleRepository
from kmartists.interfaces.users import UserRepository
from kmartists.utils.pagination import Page


class UserUseCase:
    def __init__(self, users: UserRepository, articles: ArticleRepository) -> None:
        self._users = users
        self._articles = articles

    def list_musicians(
        self, take: int, skip: int, location: str | None, requester_id: UUID | None
    ) -> Page[MusicianSummary]:
        return self._users.list_musicians(take, skip, location, requester_id)

    def get_profile(self, user_id: UUID) -> ProfileDetails:
        profile = self._users.find_profile(user_id)
        if profile is None:
            raise NotFoundError(f"User {user_id} does not exist.")
        return profile

    def list_user_articles(self, user_id: UUID, take: int, skip: int) -> Page[ArticleSummary]:
        self.get_profile(user_id)
        return self._articles.list_contributed_summaries(user_id, take, skip)

    def update_profile(self, user_id: UUID, profile: Profile, requester_id: UUID) -> None:
        if user_id != requester_id:
            raise ForbiddenError("Only the profile owner can change this profile.")
        current = self.get_profile(user_id)
        profile.validate()
        if profile.name.casefold() != current.name.casefold() and self._users.username_exists(profile.name):
            raise ConflictError(f"Username {profile.name} is already taken.")
        self._users.update_profile(user_id, profile)

    def register(self, registration: PasswordRegistration) -> UserIdentity:
        self._ensure_can_register(registration)
        return self._users.create_user(registration)

    def register_with_microsoft(self, registration: MicrosoftRegistration) -> UserIdentity:
        if self._users.microsoft_account_exists(registration.microsoft_id):
            raise ConflictError("This Microsoft account is already registered.")
        self._ensure_can_register(registration)
        return self._users.create_microsoft_user(registration)

    def log_in(self, login: str, password: str) -> UserIdentity:
        user = self._users.authenticate(login, password)
        if user is None:
            raise AuthenticationError("Invalid login or password.")
        return user

    def log_in_with_microsoft(self, microsoft_id: str) -> UserIdentity:
        user = self._users.find_microsoft_identity(microsoft_id)
        if user is None:
            raise NotFoundError("No user is registered with this Microsoft account.")
        return user

    def get_identity(self, user_id: UUID) -> UserIdentity:
        user = self._users.find_identity(user_id)
        if user is None:
            raise AuthenticationError("User no longer exists.")
        return user

    def _ensure_can_register(self, registration: Registration) -> None:
        registration.validate()
        if self._users.username_exists(registration.username):
            raise ConflictError(f"Username {registration.username} is already taken.")
        if self._users.email_exists(registration.email):
            raise ConflictError(f"Email {registration.email} is already registered.")
