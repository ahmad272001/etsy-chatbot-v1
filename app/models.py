from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from enum import Enum


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class UserBase(BaseModel):
    email: EmailStr
    role: UserRole = UserRole.USER
    is_active: bool = True


class UserCreate(UserBase):
    password: str


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class User(UserBase):
    id: str = Field(alias="_id")
    created_at: datetime
    updated_at: datetime
    hashed_password: str

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class UserResponse(UserBase):
    id: str
    created_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ThreadBase(BaseModel):
    title: str


class ThreadCreate(BaseModel):
    title: Optional[str] = None


class ThreadUpdate(BaseModel):
    title: str


class Thread(ThreadBase):
    id: str = Field(alias="_id")
    owner_user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ThreadResponse(ThreadBase):
    id: str
    owner_user_id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


class RetrievalRef(BaseModel):
    doc_id: str
    filename: str
    page: int
    chunk_id: str
    score: float


class MessageBase(BaseModel):
    content: str


class MessageCreate(MessageBase):
    pass


class Message(MessageBase):
    id: str = Field(alias="_id")
    thread_id: str
    role: MessageRole
    created_at: datetime
    retrieval_refs: Optional[List[RetrievalRef]] = None

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class MessageResponse(MessageBase):
    id: str
    thread_id: str
    role: MessageRole
    created_at: datetime
    retrieval_refs: Optional[List[RetrievalRef]] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DocumentBase(BaseModel):
    filename: str
    size_bytes: int
    page_count: int


class Document(DocumentBase):
    id: str = Field(alias="_id")
    created_at: datetime

    class Config:
        populate_by_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class DocumentResponse(DocumentBase):
    id: str
    doc_id: str  # Add the doc_id field needed for RAG operations
    created_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    message: str
    retrieval_refs: Optional[List[RetrievalRef]] = None


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    email: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class SignupRequest(BaseModel):
    email: EmailStr
    password: str
    role: UserRole = UserRole.USER
