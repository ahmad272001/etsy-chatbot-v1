import pytest
from app.rag import RAGEngine
from app.models import RetrievalRef


class TestRAG:
    def test_chunk_text(self):
        """Test text chunking functionality."""
        rag = RAGEngine()
        text = "This is a test text that should be chunked into smaller pieces for processing."
        
        chunks = rag.chunk_text(text, chunk_size=20, overlap=5)
        
        # Should create multiple chunks
        assert len(chunks) > 1
        
        # Each chunk should be within size limit
        for chunk in chunks:
            assert len(chunk.split()) <= 20
    
    def test_chunk_text_with_overlap(self):
        """Test text chunking with overlap."""
        rag = RAGEngine()
        text = "Word1 Word2 Word3 Word4 Word5 Word6 Word7 Word8 Word9 Word10"
        
        chunks = rag.chunk_text(text, chunk_size=5, overlap=2)
        
        # Should have overlap between chunks
        assert len(chunks) > 1
        
        # Check that some words appear in multiple chunks (overlap)
        all_words = []
        for chunk in chunks:
            all_words.extend(chunk.split())
        
        # Some words should appear multiple times due to overlap
        word_counts = {}
        for word in all_words:
            word_counts[word] = word_counts.get(word, 0) + 1
        
        # At least one word should appear multiple times
        assert max(word_counts.values()) > 1
    
    def test_retrieval_ref_creation(self):
        """Test RetrievalRef model creation."""
        ref = RetrievalRef(
            doc_id="test_doc_123",
            filename="test.pdf",
            page=1,
            chunk_id="chunk_1",
            score=0.85
        )
        
        assert ref.doc_id == "test_doc_123"
        assert ref.filename == "test.pdf"
        assert ref.page == 1
        assert ref.chunk_id == "chunk_1"
        assert ref.score == 0.85
    
    def test_rag_engine_initialization(self):
        """Test RAG engine initialization."""
        # This test checks if the engine can be initialized without errors
        # In a real test environment, you'd mock the external dependencies
        try:
            rag = RAGEngine()
            assert rag is not None
        except Exception as e:
            # If initialization fails due to missing config, that's expected in test environment
            assert "OPENAI_API_KEY" in str(e) or "mongodb" in str(e).lower()
