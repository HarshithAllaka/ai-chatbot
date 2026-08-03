from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(
        description="Current health status of the application",
        example="healthy",
    )

    service: str = Field(
        description="Application name",
        example="AI Chatbot",
    )

    version: str = Field(
        description="Current application version",
        example="0.1.0",
    )