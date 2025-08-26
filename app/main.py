from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.database import connect_to_mongo, close_mongo_connection
from app.routers import auth, admin, threads, chat
from app.config import settings
import os

# Create FastAPI app
app = FastAPI(
    title="RAG Chatbot API",
    description="A role-based RAG chatbot platform with FastAPI",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(threads.router)
app.include_router(chat.router)


@app.on_event("startup")
async def startup_event():
    """Initialize database connection on startup."""
    await connect_to_mongo()


@app.on_event("shutdown")
async def shutdown_event():
    """Close database connection on shutdown."""
    await close_mongo_connection()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "RAG Chatbot API",
        "version": "1.0.0"
    }


# Create uploads directory if it doesn't exist
os.makedirs("uploads", exist_ok=True)

# Mount static files for frontend
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    """Root endpoint - serve the main application."""
    from fastapi.responses import FileResponse
    return FileResponse("static/index.html")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )
