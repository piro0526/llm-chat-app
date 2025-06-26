from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
import uuid


# User schemas
class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class User(BaseModel):
    id: uuid.UUID
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


# Project schemas
class ProjectCreate(BaseModel):
    title: str
    description: Optional[str] = None


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class Project(BaseModel):
    id: uuid.UUID
    title: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# Chat Session schemas
class ChatSessionCreate(BaseModel):
    title: Optional[str] = "New Chat"


class ChatSessionUpdate(BaseModel):
    title: Optional[str] = None


class ChatSession(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatSessionWithStats(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int
    last_message_preview: Optional[str] = None

    class Config:
        from_attributes = True


# Chat schemas
class ChatMessage(BaseModel):
    role: str  # 'user' or 'assistant'
    content: str


class ChatRequest(BaseModel):
    message: str
    session_id: uuid.UUID
    provider: str = "openai"
    model: Optional[str] = None


class ChatResponse(BaseModel):
    message: str
    chat_log_id: uuid.UUID


class ChatLog(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


# LLM Settings schemas
class LLMSettingCreate(BaseModel):
    provider: str
    api_key: str
    model: str


class LLMSettingUpdate(BaseModel):
    api_key: Optional[str] = None
    model: Optional[str] = None


class LLMSetting(BaseModel):
    provider: str
    model: str
    # Note: api_key is not included for security

    class Config:
        from_attributes = True


# Token schema
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None