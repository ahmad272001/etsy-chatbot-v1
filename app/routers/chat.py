from fastapi import APIRouter, HTTPException, status, Depends
from app.models import ChatRequest, ChatResponse, MessageResponse, MessageRole
from app.auth import get_current_user
from app.database import get_collection
from app.chat import chat_service
from app.rag import rag_engine
from typing import List, Optional
from datetime import datetime, timezone
from bson import ObjectId

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/{thread_id}/message", response_model=ChatResponse)
async def send_message(
    thread_id: str,
    chat_request: ChatRequest,
    current_user = Depends(get_current_user)
):
    """Send a message in a thread and get RAG-powered response."""
    threads_collection = get_collection("threads")
    messages_collection = get_collection("messages")
    
    # Verify thread exists and user has access
    thread = await threads_collection.find_one({"_id": ObjectId(thread_id)})
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )
    
    # Check if user owns the thread or is admin
    if thread["owner_user_id"] != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Save user message
    user_message_doc = {
        "thread_id": thread_id,
        "role": MessageRole.USER,
        "content": chat_request.message,
        "created_at": datetime.now(timezone.utc),
        "retrieval_refs": None
    }
    
    await messages_collection.insert_one(user_message_doc)
    
    # Process message with RAG
    chat_response = await chat_service.process_chat_message(chat_request.message)
    
    # Save assistant message
    assistant_message_doc = {
        "thread_id": thread_id,
        "role": MessageRole.ASSISTANT,
        "content": chat_response.message,
        "created_at": datetime.now(timezone.utc),
        "retrieval_refs": [ref.model_dump() for ref in chat_response.retrieval_refs] if chat_response.retrieval_refs else []
    }
    
    await messages_collection.insert_one(assistant_message_doc)
    
    # Update thread timestamp
    await threads_collection.update_one(
        {"_id": ObjectId(thread_id)},
        {"$set": {"updated_at": datetime.now(timezone.utc)}}
    )
    
    return chat_response


@router.get("/{thread_id}/messages", response_model=List[MessageResponse])
async def get_messages(
    thread_id: str,
    skip: int = 0,
    limit: int = 50,
    current_user = Depends(get_current_user)
):
    """Get paginated messages from a thread."""
    threads_collection = get_collection("threads")
    messages_collection = get_collection("messages")
    
    # Verify thread exists and user has access
    thread = await threads_collection.find_one({"_id": ObjectId(thread_id)})
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )
    
    # Check if user owns the thread or is admin
    if thread["owner_user_id"] != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Get messages with pagination
    cursor = messages_collection.find(
        {"thread_id": thread_id}
    ).sort("created_at", 1).skip(skip).limit(limit)
    
    messages = []
    async for message in cursor:
        messages.append(MessageResponse(
            id=str(message["_id"]),
            thread_id=message["thread_id"],
            role=message["role"],
            content=message["content"],
            created_at=message["created_at"],
            retrieval_refs=message.get("retrieval_refs")
        ))
    
    return messages


@router.delete("/messages/{message_id}")
async def delete_message(
    message_id: str,
    current_user = Depends(get_current_user)
):
    """Delete a specific message (owner or admin only)."""
    threads_collection = get_collection("threads")
    messages_collection = get_collection("messages")
    
    # Get message
    message = await messages_collection.find_one({"_id": ObjectId(message_id)})
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    # Get thread to check ownership
    thread = await threads_collection.find_one({"_id": ObjectId(message["thread_id"])})
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )
    
    # Check permissions (thread owner or admin)
    if thread["owner_user_id"] != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Delete message
    result = await messages_collection.delete_one({"_id": ObjectId(message_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete message"
        )
    
    return {"message": "Message deleted successfully"}


@router.get("/{thread_id}/messages/count")
async def get_message_count(
    thread_id: str,
    current_user = Depends(get_current_user)
):
    """Get total message count for a thread."""
    threads_collection = get_collection("threads")
    messages_collection = get_collection("messages")
    
    # Verify thread exists and user has access
    thread = await threads_collection.find_one({"_id": ObjectId(thread_id)})
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )
    
    # Check if user owns the thread or is admin
    if thread["owner_user_id"] != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Count messages
    count = await messages_collection.count_documents({"thread_id": thread_id})
    
    return {"count": count}
