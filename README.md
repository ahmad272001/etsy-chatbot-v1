# RAG Chatbot Platform

A production-ready, role-based RAG (Retrieval-Augmented Generation) chatbot platform built with FastAPI, featuring document upload, vector search, and role-based access control.

## Features

- **Role-Based Access Control**: Admin and User roles with different permissions
- **RAG Pipeline**: PDF document processing, chunking, and vector search using ChromaDB
- **OpenAI Integration**: Uses text-embedding-3-small for embeddings and configurable chat models
- **MongoDB Atlas**: Persistent storage for users, threads, messages, and document metadata
- **JWT Authentication**: Secure token-based authentication
- **Modern Frontend**: Clean HTML/JS interface with Bootstrap styling
- **Strict Grounding**: Only answers based on uploaded knowledge base content

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI       │    │   MongoDB       │
│   (HTML/JS)     │◄──►│   Backend       │◄──►│   Atlas         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   ChromaDB      │
                       │   (Vector Store)│
                       └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │   OpenAI API    │
                       │   (Embeddings)  │
                       └─────────────────┘
```

## Tech Stack

- **Backend**: Python 3.11+, FastAPI, Uvicorn
- **Database**: MongoDB Atlas
- **Vector Store**: ChromaDB (embedded)
- **AI**: OpenAI API (text-embedding-3-small, configurable chat model)
- **Authentication**: JWT with bcrypt password hashing
- **Frontend**: HTML5, JavaScript, Bootstrap 5
- **Testing**: pytest

## Quick Start

### Prerequisites

- Python 3.11 or higher
- MongoDB Atlas account and connection string
- OpenAI API key
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd etsychatbot-v1
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your actual values
   ```

5. **Configure environment variables**
   ```bash
   # Required variables
   MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/database
   MONGODB_DBNAME=rag_chatbot
   OPENAI_API_KEY=your_openai_api_key_here
   JWT_SECRET=your_super_secret_jwt_key_here
   
   # Optional variables (have defaults)
   OPENAI_CHAT_MODEL=gpt-4o-mini
   EMBEDDING_MODEL=text-embedding-3-small
   RETRIEVAL_TOP_K=5
   RETRIEVAL_SCORE_MIN=0.7
   ```

6. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

7. **Access the application**
   - Frontend: http://localhost:8000/static/
   - API Docs: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

## Initial Setup

### Create First Admin User

Since the system starts with no users, you'll need to create the first admin user directly in MongoDB:

```javascript
// Connect to your MongoDB Atlas cluster
// Insert the first admin user
db.users.insertOne({
  email: "admin@example.com",
  password_hash: "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj4J/8KqjqGm", // "admin123"
  role: "admin",
  is_active: true,
  created_at: new Date()
})
```

**Default admin credentials:**
- Email: `admin@example.com`
- Password: `admin123`

**⚠️ Important**: Change these credentials immediately after first login!

## API Endpoints

### Authentication
- `POST /auth/login` - User login
- `POST /auth/signup` - Create new user (admin only)

### Admin Operations
- `GET /admin/users` - List all users
- `POST /admin/users` - Create new user
- `PATCH /admin/users/{user_id}` - Update user
- `DELETE /admin/users/{user_id}` - Delete user
- `POST /admin/documents/upload` - Upload PDF document
- `GET /admin/documents` - List all documents
- `DELETE /admin/documents/{doc_id}` - Delete document

### Thread Management
- `POST /threads` - Create new thread
- `GET /threads` - List threads (users see own, admins see all)
- `PATCH /threads/{thread_id}` - Rename thread
- `DELETE /threads/{thread_id}` - Delete thread

### Chat
- `POST /chat/{thread_id}/message` - Send message and get RAG response
- `GET /chat/{thread_id}/messages` - Get thread messages
- `GET /chat/{thread_id}/messages/count` - Get message count

### System
- `GET /health` - Health check
- `GET /` - API information

## Usage Examples

### Upload a Document (Admin)

```bash
curl -X POST "http://localhost:8000/admin/documents/upload" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -F "file=@document.pdf"
```

### Create a Chat Thread

```bash
curl -X POST "http://localhost:8000/threads" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "My Chat Thread"}'
```

### Send a Message

```bash
curl -X POST "http://localhost:8000/chat/THREAD_ID/message" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "What is the main topic of the uploaded documents?"}'
```

## RAG Pipeline

1. **Document Upload**: Admin uploads PDF documents
2. **Text Extraction**: PDF text is extracted and normalized
3. **Chunking**: Text is split into ~800 token chunks with 120 token overlap
4. **Embedding**: Chunks are embedded using OpenAI's text-embedding-3-small
5. **Storage**: Embeddings stored in ChromaDB with metadata
6. **Retrieval**: User queries are embedded and similar chunks retrieved
7. **Generation**: LLM generates responses based on retrieved context
8. **Grounding**: Strict enforcement ensures responses only use retrieved content

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `MONGODB_URI` | MongoDB Atlas connection string | - | Yes |
| `MONGODB_DBNAME` | Database name | - | Yes |
| `OPENAI_API_KEY` | OpenAI API key | - | Yes |
| `JWT_SECRET` | JWT signing secret | - | Yes |
| `OPENAI_CHAT_MODEL` | Chat model name | `gpt-4o-mini` | No |
| `EMBEDDING_MODEL` | Embedding model | `text-embedding-3-small` | No |
| `RETRIEVAL_TOP_K` | Number of chunks to retrieve | `5` | No |
| `RETRIEVAL_SCORE_MIN` | Minimum similarity score | `0.7` | No |
| `CHROMA_PERSIST_DIR` | ChromaDB storage directory | `./chroma_db` | No |

### RAG Settings

- **Chunk Size**: 800 tokens with 120 token overlap
- **Similarity Metric**: Cosine similarity
- **Score Threshold**: Configurable minimum similarity score
- **Top-K Retrieval**: Configurable number of chunks to retrieve

## Testing

Run the test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=app
```

## Security Features

- **JWT Authentication**: Secure token-based authentication
- **Password Hashing**: bcrypt with salt
- **Role-Based Access Control**: Admin and User roles
- **Input Validation**: Pydantic models with validation
- **CORS Configuration**: Configurable cross-origin settings

## Production Deployment

### Docker (Recommended)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Environment Setup

1. Set production environment variables
2. Use strong JWT secrets
3. Configure CORS appropriately
4. Set up MongoDB Atlas with proper security
5. Use HTTPS in production
6. Configure logging and monitoring

### Scaling Considerations

- **MongoDB Atlas**: Use appropriate cluster tier
- **ChromaDB**: Consider external ChromaDB server for production
- **Load Balancing**: Use reverse proxy (nginx) for multiple instances
- **Caching**: Implement Redis for session management
- **Monitoring**: Add health checks and metrics

## Troubleshooting

### Common Issues

1. **MongoDB Connection Failed**
   - Check connection string format
   - Verify network access and IP whitelist
   - Check credentials

2. **OpenAI API Errors**
   - Verify API key is valid
   - Check API quota and billing
   - Ensure model names are correct

3. **ChromaDB Issues**
   - Check disk space
   - Verify directory permissions
   - Restart application if corrupted

4. **Authentication Errors**
   - Check JWT secret configuration
   - Verify token expiration settings
   - Check user status in database

### Logs

Check application logs for detailed error information:

```bash
uvicorn app.main:app --reload --log-level debug
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review API documentation at `/docs`
3. Open an issue on GitHub
4. Check application logs for errors

## Changelog

### v1.0.0
- Initial release
- Role-based access control
- RAG pipeline with ChromaDB
- MongoDB Atlas integration
- JWT authentication
- Modern web interface
- Comprehensive testing suite
