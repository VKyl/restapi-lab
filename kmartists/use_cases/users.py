from uuid import UUID

from kmartists.domain.errors import AuthenticationError, ConflictError, NotFoundError
from kmartists.domain.users import MicrosoftRegistration, PasswordRegistration, Registration, UserIdentity
from kmartists.interfaces.users import UserRepository


class UserUseCases:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

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
