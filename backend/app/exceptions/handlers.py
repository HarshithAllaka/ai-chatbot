from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.exceptions.auth import (
    InvalidCredentialsError,
    UserAlreadyExistsError,
)


def register_exception_handlers(
    app: FastAPI,
) -> None:

    @app.exception_handler(UserAlreadyExistsError)
    async def user_exists_handler(
        request: Request,
        exc: UserAlreadyExistsError,
    ):
        return JSONResponse(
            status_code=400,
            content={
                "detail": "Email already registered",
            },
        )

    @app.exception_handler(
        InvalidCredentialsError
    )
    async def invalid_credentials_handler(
        request: Request,
        exc: InvalidCredentialsError,
    ):
        return JSONResponse(
            status_code=401,
            content={
                "detail": "Invalid email or password",
            },
        )