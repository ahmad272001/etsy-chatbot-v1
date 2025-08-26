from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form
from app.models import UserResponse, UserUpdate, DocumentResponse
from app.auth import get_current_admin_user, get_current_user
from app.database import get_collection
from app.rag import rag_engine
from typing import List, Optional
import os
import tempfile
from datetime import datetime, timezone
from bson import ObjectId

router = APIRouter(prefix="/admin", tags=["Admin"])


# User Management Endpoints
@router.get("/users", response_model=List[UserResponse])
async def list_users(
    search: Optional[str] = None,
    current_admin: UserResponse = Depends(get_current_admin_user)
):
    """List all users (admin only)."""
    users_collection = get_collection("users")
    
    # Build query
    query = {}
    if search:
        query["email"] = {"$regex": search, "$options": "i"}
    
    # Get users
    cursor = users_collection.find(query)
    users = []
    
    async for user in cursor:
        users.append(UserResponse(
            id=str(user["_id"]),
            email=user["email"],
            role=user["role"],
            is_active=user["is_active"],
            created_at=user["created_at"]
        ))
    
    return users


@router.get("/users/{user_id}/chat-history")
async def get_user_chat_history(
    user_id: str,
    current_admin: UserResponse = Depends(get_current_admin_user)
):
    """Get chat history for a specific user (admin only)."""
    threads_collection = get_collection("threads")
    messages_collection = get_collection("messages")
    
    # Get all threads for the user
    cursor = threads_collection.find({"owner_user_id": user_id}).sort("created_at", -1)
    threads = []
    
    async for thread in cursor:
        # Get messages for this thread (limit to last 50 for preview)
        messages_cursor = messages_collection.find(
            {"thread_id": str(thread["_id"])}
        ).sort("created_at", 1).limit(50)
        
        messages = []
        async for message in messages_cursor:
            messages.append({
                "id": str(message["_id"]),
                "role": message["role"],
                "content": message["content"],
                "created_at": message["created_at"]
            })
        
        threads.append({
            "id": str(thread["_id"]),
            "title": thread["title"],
            "created_at": thread["created_at"],
            "updated_at": thread["updated_at"],
            "messages": messages
        })
    
    return threads


@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: dict,
    current_admin = Depends(get_current_admin_user)
):
    """Create a new user (admin only)."""
    from app.auth import get_password_hash
    
    users_collection = get_collection("users")
    
    # Validate required fields
    if not user_data.get("email"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required"
        )
    
    if not user_data.get("password"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is required"
        )
    
    # Check if user already exists
    existing_user = await users_collection.find_one({"email": user_data["email"]})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Hash password
    password_hash = get_password_hash(user_data["password"])
    
    # Create user document
    user_doc = {
        "email": user_data["email"],
        "hashed_password": password_hash,  # Use consistent field name
        "role": user_data.get("role", "user"),
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc)  # Add missing updated_at field
    }
    
    # Insert user
    result = await users_collection.insert_one(user_doc)
    
    # Return user response
    return UserResponse(
        id=str(result.inserted_id),
        email=user_doc["email"],
        role=user_doc["role"],
        is_active=user_doc["is_active"],
        created_at=user_doc["created_at"]
    )


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_admin: UserResponse = Depends(get_current_admin_user)
):
    """Update user (admin only)."""
    users_collection = get_collection("users")
    
    # Check if user exists
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Build update data
    update_data = {}
    if user_update.email is not None:
        update_data["email"] = user_update.email
    if user_update.role is not None:
        update_data["role"] = user_update.role
    if user_update.is_active is not None:
        update_data["is_active"] = user_update.is_active
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    # Update user
    result = await users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )
    
    if result.modified_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to update user"
        )
    
    # Get updated user
    updated_user = await users_collection.find_one({"_id": ObjectId(user_id)})
    
    return UserResponse(
        id=str(updated_user["_id"]),
        email=updated_user["email"],
        role=updated_user["role"],
        is_active=updated_user["is_active"],
        created_at=updated_user["created_at"]
    )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: str,
    current_admin: UserResponse = Depends(get_current_admin_user)
):
    """Delete user (admin only)."""
    users_collection = get_collection("users")
    
    # Check if user exists
    user = await users_collection.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Delete user
    result = await users_collection.delete_one({"_id": ObjectId(user_id)})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete user"
        )
    
    return {"message": "User deleted successfully"}


# Document Management Endpoints
@router.post("/documents/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    current_admin: UserResponse = Depends(get_current_admin_user)
):
    """Upload PDF or Word document (admin only)."""
    # Validate file type
    file_extension = file.filename.lower()
    if not (file_extension.endswith('.pdf') or file_extension.endswith('.docx')):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF (.pdf) and Word (.docx) files are allowed"
        )
    
    # Save file temporarily with appropriate extension
    file_extension = '.pdf' if file.filename.lower().endswith('.pdf') else '.docx'
    with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_file_path = temp_file.name
    
    try:
        # Process document with RAG engine
        doc_id = None
        page_count = 0
        rag_success = False
        
        try:
            doc_id, page_count = rag_engine.add_document(temp_file_path, file.filename)
            rag_success = True
        except Exception as rag_error:
            # Generate a fallback doc_id if RAG fails
            import uuid
            doc_id = str(uuid.uuid4())
            
            # Try to get page count from file directly
            try:
                if file.filename.lower().endswith('.pdf'):
                    import PyPDF2
                    with open(temp_file_path, 'rb') as pdf_file:
                        pdf_reader = PyPDF2.PdfReader(pdf_file)
                        page_count = len(pdf_reader.pages)
                elif file.filename.lower().endswith('.docx'):
                    from docx import Document
                    doc = Document(temp_file_path)
                    page_count = len(doc.paragraphs) // 50 + 1  # Rough estimate
                else:
                    page_count = 1
            except Exception as file_error:
                page_count = 1  # Default to 1 page
        
        # Save document metadata to MongoDB
        documents_collection = get_collection("documents")
        doc_doc = {
            "doc_id": doc_id,
            "filename": file.filename,
            "size_bytes": len(content),
            "page_count": page_count,
            "rag_processed": rag_success,  # Track if RAG processing was successful
            "created_at": datetime.now(timezone.utc)
        }
        
        try:
            result = await documents_collection.insert_one(doc_doc)
        except Exception as db_error:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to save document metadata: {str(db_error)}"
            )
        
        return DocumentResponse(
            id=str(result.inserted_id),
            doc_id=doc_doc["doc_id"],  # Add doc_id field
            filename=file.filename,
            size_bytes=len(content),
            page_count=page_count,
            created_at=doc_doc["created_at"]
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PDF upload failed: {str(e)}"
        )
    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_file_path)
        except Exception as cleanup_error:
            pass


@router.get("/documents", response_model=List[DocumentResponse])
async def list_documents(
    current_admin: UserResponse = Depends(get_current_admin_user)
):
    """List all documents (admin only)."""
    documents_collection = get_collection("documents")
    
    cursor = documents_collection.find({})
    documents = []
    
    async for doc in cursor:
        # Handle missing fields gracefully
        documents.append(DocumentResponse(
            id=str(doc["_id"]),
            doc_id=doc.get("doc_id", "unknown"),  # Add doc_id field
            filename=doc.get("filename", "Unknown"),
            size_bytes=doc.get("size_bytes", 0),
            page_count=doc.get("page_count", 0),
            created_at=doc.get("created_at", datetime.now(timezone.utc))
        ))
    
    return documents


@router.delete("/documents/{doc_id}")
async def delete_document(
    doc_id: str,
    current_admin: UserResponse = Depends(get_current_admin_user)
):
    """Delete document (admin only)."""
    documents_collection = get_collection("documents")
    
    # Validate doc_id
    if not doc_id or doc_id == "None":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid document ID"
        )
    
    # Get document metadata
    doc = await documents_collection.find_one({"doc_id": doc_id})
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Delete from Qdrant vector store
    success = rag_engine.delete_document(doc_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete document from vector store"
        )
    
    # Delete from MongoDB
    result = await documents_collection.delete_one({"doc_id": doc_id})
    
    if result.deleted_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to delete document metadata"
        )
    
    return {"message": "Document deleted successfully"}
