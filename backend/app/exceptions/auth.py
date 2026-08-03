class UserAlreadyExistsError(Exception):
    """Raised when attempting to register an email that already exists."""

    pass


class InvalidCredentialsError(Exception):
    """Raised when login credentials are invalid."""

    pass