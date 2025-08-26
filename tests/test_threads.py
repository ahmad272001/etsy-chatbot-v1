import pytest
from app.models import ThreadCreate, ThreadUpdate, ThreadResponse
from datetime import datetime


class TestThreads:
    def test_thread_create_model(self):
        """Test ThreadCreate model."""
        thread_data = ThreadCreate(title="Test Thread")
        
        assert thread_data.title == "Test Thread"
        
        # Test with no title
        thread_data_no_title = ThreadCreate()
        assert thread_data_no_title.title is None
    
    def test_thread_update_model(self):
        """Test ThreadUpdate model."""
        thread_update = ThreadUpdate(title="Updated Thread Title")
        
        assert thread_update.title == "Updated Thread Title"
    
    def test_thread_response_model(self):
        """Test ThreadResponse model."""
        now = datetime.utcnow()
        thread_response = ThreadResponse(
            id="thread_123",
            title="Test Thread",
            owner_user_id="user_456",
            created_at=now,
            updated_at=now
        )
        
        assert thread_response.id == "thread_123"
        assert thread_response.title == "Test Thread"
        assert thread_response.owner_user_id == "user_456"
        assert thread_response.created_at == now
        assert thread_response.updated_at == now
    
    def test_thread_models_validation(self):
        """Test thread model validation."""
        # Valid thread creation
        valid_thread = ThreadCreate(title="Valid Thread")
        assert valid_thread.title == "Valid Thread"
        
        # Valid thread update
        valid_update = ThreadUpdate(title="Valid Update")
        assert valid_update.title == "Valid Update"
        
        # Thread response with all required fields
        now = datetime.utcnow()
        valid_response = ThreadResponse(
            id="test_id",
            title="Test Title",
            owner_user_id="test_owner",
            created_at=now,
            updated_at=now
        )
        assert valid_response.id == "test_id"
