from fastapi import APIRouter, HTTPException, status, Depends
from app.models import ThreadCreate, ThreadUpdate, ThreadResponse
from app.auth import get_current_user, get_current_admin_user
from app.database import get_collection
from typing import List, Optional
from datetime import datetime
from bson import ObjectId

router = APIRouter(prefix="/threads", tags=["Threads"])


@router.post("", response_model=ThreadResponse)
async def create_thread(
    thread_data: ThreadCreate,
    current_user = Depends(get_current_user)
):
    """Create a new chat thread."""
    threads_collection = get_collection("threads")
    
    # Generate title if not provided
    title = thread_data.title
    if not title:
        from datetime import timezone
        title = f"New Chat {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}"
    
    # Create thread document
    from datetime import timezone
    current_time = datetime.now(timezone.utc)
    thread_doc = {
        "title": title,
        "owner_user_id": current_user.id,
        "created_at": current_time,
        "updated_at": current_time
    }
    
    # Insert thread
    result = await threads_collection.insert_one(thread_doc)
    
    return ThreadResponse(
        id=str(result.inserted_id),
        title=title,
        owner_user_id=current_user.id,
        created_at=thread_doc["created_at"],
        updated_at=thread_doc["updated_at"]
    )


@router.get("", response_model=List[ThreadResponse])
async def list_threads(
    current_user = Depends(get_current_user)
):
    """List threads (users see their own, admins see all)."""
    threads_collection = get_collection("threads")
    
    # Build query based on user role
    if current_user.role == "admin":
        # Admin sees all threads
        query = {}
    else:
        # Regular user sees only their threads
        query = {"owner_user_id": current_user.id}
    
    # Get threads
    cursor = threads_collection.find(query).sort("updated_at", -1)
    threads = []
    
    async for thread in cursor:
        threads.append(ThreadResponse(
            id=str(thread["_id"]),
            title=thread["title"],
            owner_user_id=thread["owner_user_id"],
            created_at=thread["created_at"],
            updated_at=thread["updated_at"]
        ))
    
    return threads


@router.patch("/{thread_id}", response_model=ThreadResponse)
async def update_thread(
    thread_id: str,
    thread_update: ThreadUpdate,
    current_user = Depends(get_current_user)
):
    """Update thread title (owner or admin only)."""
    threads_collection = get_collection("threads")
    
    # Get thread
    thread = await threads_collection.find_one({"_id": ObjectId(thread_id)})
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )
    
    # Check permissions (owner or admin)
    if thread["owner_user_id"] != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Update thread
    from datetime import timezone
    result = await threads_collection.update_one(
        {"_id": ObjectId(thread_id)},
        {
            "$set": {
                "title": thread_update.title,
                "updated_at": datetime.now(timezone.utc)
            }
        }
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update thread"
        )
    
    # Get updated thread
    updated_thread = await threads_collection.find_one({"_id": ObjectId(thread_id)})
    
    return ThreadResponse(
        id=str(updated_thread["_id"]),
        title=updated_thread["title"],
        owner_user_id=updated_thread["owner_user_id"],
        created_at=updated_thread["created_at"],
        updated_at=updated_thread["updated_at"]
    )


@router.delete("/{thread_id}")
async def delete_thread(
    thread_id: str,
    current_user = Depends(get_current_user)
):
    """Delete thread (owner or admin only)."""
    threads_collection = get_collection("threads")
    messages_collection = get_collection("messages")
    
    # Get thread
    thread = await threads_collection.find_one({"_id": ObjectId(thread_id)})
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )
    
    # Check permissions (owner or admin)
    if thread["owner_user_id"] != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Delete all messages in the thread
    await messages_collection.delete_many({"thread_id": thread_id})
    
    # Delete thread
    result = await threads_collection.delete_one({"_id": ObjectId(thread_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete thread"
        )
    
    return {"message": "Thread deleted successfully"}
