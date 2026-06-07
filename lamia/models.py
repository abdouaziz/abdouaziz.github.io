from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenRefresh(BaseModel):
    access_token: str
    token_type: str


class CreditInfo(BaseModel):
    remaining_credit: float
    total_credit: Optional[float] = None
    consumed_credit: Optional[float] = None


class GetPost(BaseModel):
    text: str
    to_lang: str
    post_created_at: datetime
    translated_text: Optional[str] = None
    path_audio: Optional[str] = None


class Post(BaseModel):
    text: str
    to_lang: str
    translated_text: str
    post_created_at: datetime


class PostVocalized(BaseModel):
    text: str
    to_lang: str
    path_audio: str
    post_created_at: datetime
    duration: Optional[float] = None


class AudioToText(BaseModel):
    transcription: str
    to_lang: str
    post_created_at: datetime
    duration: Optional[float] = None


class Statistic(BaseModel):
    date: datetime
    success_requests: int
    failed_requests: int
    total_requests: int
