from uuid import UUID

from kmartists.domain.errors import AuthenticationError, ConflictError
from kmartists.domain.users import MicrosoftRegistration, PasswordRegistration, Registration, UserReference
from kmartists.interfaces.users import UserRepository


class UserUseCases:
    def __init__(self, users: UserRepository) -> None:
        self._users = users

    def register(self, registration: PasswordRegistration) -> UserReference:
        self._ensure_can_register(registration)
        return self._users.create_user(registration)

    def register_with_microsoft(self, registration: MicrosoftRegistration) -> UserReference:
        if self._users.microsoft_account_exists(registration.microsoft_id):
            raise ConflictError("This Microsoft account is already registered.")
        self._ensure_can_register(registration)
        return self._users.create_microsoft_user(registration)

    def log_in(self, username: str, password: str) -> UserReference:
        user = self._users.authenticate(username, password)
        if user is None:
            raise AuthenticationError("Invalid username or password.")
        return user

    def refresh(self, user_id: UUID) -> UserReference:
        user = self._users.find_reference(user_id)
        if user is None:
            raise AuthenticationError("User no longer exists.")
        return user

    def _ensure_can_register(self, registration: Registration) -> None:
        registration.validate()
        if self._users.username_exists(registration.username):
            raise ConflictError(f"Username {registration.username} is already taken.")
        if self._users.email_exists(registration.email):
            raise ConflictError(f"Email {registration.email} is already registered.")
