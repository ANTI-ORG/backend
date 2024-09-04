from pydantic import BaseModel


class UserTempAuth(BaseModel):
    temp_token: str


class UserAuth(BaseModel):
    access_token: str
    message: str


class TokenValid(BaseModel):
    is_valid: bool


class VerifySignatureRequest(BaseModel):
    temp_token: str
    signature: str
