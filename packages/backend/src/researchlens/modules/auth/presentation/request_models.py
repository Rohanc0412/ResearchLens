from pydantic import BaseModel, ConfigDict, EmailStr


class RegisterRequestDto(BaseModel):
    username: str
    email: EmailStr
    password: str

    model_config = ConfigDict(extra="forbid")


class LoginRequestDto(BaseModel):
    identifier: str
    password: str

    model_config = ConfigDict(extra="forbid")


class PasswordResetRequestDto(BaseModel):
    email: EmailStr

    model_config = ConfigDict(extra="forbid")


class PasswordResetConfirmRequestDto(BaseModel):
    token: str
    password: str

    model_config = ConfigDict(extra="forbid")
