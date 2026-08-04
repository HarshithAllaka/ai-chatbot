from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str = Field(
        json_schema_extra={
            "example": "healthy"
        }
    )

    service: str = Field(
        json_schema_extra={
            "example": "AI Chatbot API"
        }
    )

    version: str = Field(
        json_schema_extra={
            "example": "1.0.0"
        }
    )