import re

from pydantic import BaseModel, Field, constr, HttpUrl, field_validator
from typing import Optional, List
from datetime import datetime


class WalletBase(BaseModel):
    id: int
    web3_address: str
    wallet_network: str

    class Config:
        from_attributes = True


class UsernameSchema(BaseModel):
    username: str

    @field_validator('username')
    def check_username_length(cls, v):
        if len(v) < 5:
            raise ValueError('Username must be at least 5 characters long')
        if len(v) > 50:
            raise ValueError('Username must be less than 50 characters long')
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username can only contain letters, numbers, and underscores')
        return v


class UserBase(UsernameSchema):
    id: str
    wallets: List[WalletBase] = []  # Добавляем список кошельков
    xp: int
    rang_id: int
    registered_at: datetime
    avatar: str

    max_docs_streak: int
    curr_docs_streak: int
    previous_docs_streak: int
    docs_grabbed_at: Optional[datetime] = None  # Это поле опционально и по умолчанию None

    class Config:
        from_attributes = True


class UserPatchRequest(BaseModel):
    username: str = None
    base64_image: Optional[constr(min_length=2, max_length=1400000)] = None


class UserPatchResponse(BaseModel):
    status: str
    user: UserBase


class IdModel(BaseModel):
    id: int


class TaskBase(BaseModel):
    id: int
    title: str
    description: str
    button_text: str
    button_link: HttpUrl
    image: HttpUrl
    quest_id: int


class QuestShortData(IdModel):
    quest_image: Optional[str] = None
    title: str = Field(..., max_length=70)
    task_count: int = 0
    xp: int = 0

    chain_image: Optional[str] = None
    chain_name: Optional[str] = None
    project_image: Optional[str] = None
    project_name: Optional[str] = None


class QuestBase(QuestShortData):
    created_at: datetime = None
    description: str
    tasks: List[TaskBase] = []

class ProjectBase(IdModel):
    name: str = Field(..., max_length=50)
    image: str


class ChainBase(IdModel):
    name: str = Field(..., max_length=50)
    image: str


class TimeLeft(BaseModel):
    hours: int
    minutes: int
    seconds: int


class CanGrabDocs(BaseModel):
    can_grab: bool
    time_left: TimeLeft


class GrabDocs(BaseModel):
    success: bool
    detail: str
    curr_docs_streak: int = None
    max_docs_streak: int = None
    previous_docs_streak: int = None
    time_left: TimeLeft


class CountUsers(BaseModel):
    count: int