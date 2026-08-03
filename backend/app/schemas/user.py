from pydantic import BaseModel, EmailStr, Field

class UserBase(BaseModel):
    email: EmailStr
    full_name: str = Field(
        min_length=2,
        max_length=100,
    )

class UserCreate(UserBase):
    password: str = Field(
        min_length=8,
        max_length=128,
    )

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int