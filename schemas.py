from typing import Optional
from pydantic import BaseModel, Field


class User(BaseModel):
    uuid: str
    api_key: str


class Message(BaseModel):
    uuid: str
    body: str
    to: str
    from_: str = Field(..., alias="from")
    created_at: str

    class Config:
        populate_by_name = True
