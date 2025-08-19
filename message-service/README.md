# Message Service - Implementation

FastAPI microservice for message processing and LLM integration within the Character Chat API ecosystem.

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- MongoDB 6.0+
- Redis 7.0+

### Development Setup

1. **Activate the virtual environment** (REQUIRED):
   ```bash
   source .aienv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your local configuration
   ```

4. **Start the development server**:
   ```bash
   python run_dev.py
   ```

The service will be available at http://localhost:8009

## 📋 Implementation Status

### ✅ Phase 1: MVP Core Infrastructure (COMPLETED)
- [x] FastAPI project structure
- [x] Environment configuration management
- [x] Structured logging with correlation IDs
- [x] MongoDB connection with Beanie ODM
- [x] Message models and database schema
- [x] Repository pattern for data access
- [x] MongoDB indexes for performance
- [x] Core message API endpoints
- [x] Request/response validation
- [x] Content sanitization
- [x] In-memory rate limiting
- [x] Redis connection and caching
- [x] Basic queuing infrastructure

### 🔄 Next Phases
- Phase 2: LLM and Processing Enhancements
- Phase 3: Advanced Features and Optimization  
- Phase 4: Extended Integrations and Robustness

## 🛠️ API Endpoints

### Messages
- `POST /api/v1/messages` - Create new message
- `GET /api/v1/messages/{message_id}` - Get message by ID
- `GET /api/v1/conversations/{conversation_id}/messages` - Get conversation messages
- `PATCH /api/v1/messages/{message_id}/metadata` - Update message metadata
- `DELETE /api/v1/messages/{message_id}` - Archive message

### System
- `GET /health` - Health check
- `GET /` - Service information
- `GET /docs` - Interactive API documentation

## 🗄️ Database Schema

The service uses MongoDB with the following collections:

### messages
Main collection storing all messages with:
- Core identifiers (message_id, conversation_id, user_id)
- Content with sanitization metadata
- Role and status tracking
- Timestamps for audit trail
- Custom extensible metadata
- Full-text search capability

Indexes optimized for:
- Conversation-based queries (most frequent)
- User-based queries
- Temporal sorting and pagination
- Text search
- Analytics aggregations

## 🔧 Development Commands

```bash
# Start development server with auto-reload
python run_dev.py

# Setup MongoDB indexes
python scripts/setup_indexes.py

# Run tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=html

# Format code
black app/ tests/
isort app/ tests/

# Type checking
mypy app/

# Linting
flake8 app/
```

## 🏗️ Architecture

### Project Structure
```
app/
├── main.py              # FastAPI application
├── database.py          # MongoDB connection
├── core/                # Core utilities
│   ├── config.py        # Configuration management
│   ├── logging.py       # Structured logging
│   ├── exceptions.py    # Custom exceptions
│   ├── rate_limiter.py  # Rate limiting logic
│   ├── redis_client.py  # Redis wrapper
│   └── cache.py         # Caching layer
├── models/              # Data models
│   ├── database.py      # Beanie ODM models
│   └── message.py       # Pydantic API models
├── repositories/        # Data access layer
│   └── message_repository.py
├── services/            # Business logic
│   └── message_service.py
└── api/v1/              # API endpoints
    └── messages.py
```

### Key Features
- **Async-first**: Built on FastAPI with async/await throughout
- **Structured logging**: JSON logging with correlation IDs
- **Configuration management**: Environment-based with validation
- **Error handling**: Custom exceptions with structured responses
- **Rate limiting**: Per-user limits with Redis backing
- **Content sanitization**: HTML/XSS protection with bleach
- **Database optimization**: Proper indexing for query patterns
- **Caching**: Multi-level caching with Redis
- **Testing**: Unit tests with pytest and async support

## 🔧 Configuration

Key environment variables:

```bash
# Service
SERVICE_NAME=message-service
PORT=8009
ENVIRONMENT=development

# Database
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=message_service_dev

# Cache
REDIS_URL=redis://localhost:6379

# External Services  
AUTH_SERVICE_URL=http://localhost:8001
CONVERSATION_SERVICE_URL=http://localhost:8003
CHARACTERS_SERVICE_URL=http://localhost:8002

# Rate Limiting
MAX_MESSAGES_PER_MINUTE=100
MAX_MESSAGES_PER_HOUR=1000
MAX_MESSAGES_PER_DAY=10000
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test files
pytest tests/unit/test_message_service.py
```

## 🚀 Next Steps

1. **Phase 2 Implementation**: LLM provider integration and async processing
2. **Authentication**: Integrate with Auth Service for JWT validation
3. **LLM Integration**: Add multiple provider support (OpenAI, Anthropic)
4. **Background Workers**: Implement async message processing
5. **Analytics**: Add token usage tracking and performance metrics
6. **Search**: Implement full-text search with Elasticsearch
7. **Monitoring**: Add Prometheus metrics and health checks

## 📚 Documentation

- [Integration Plan](documents/Plan_Integracion.md) - Complete implementation roadmap
- [API Specification](documents/API_SPECIFICATION.md) - Detailed API documentation
- [Database Design](documents/DATABASE_DESIGN.md) - MongoDB schema and optimization
- [Architecture](documents/ARCHITECTURE.md) - System architecture and patterns
- [Deployment](documents/DEPLOYMENT.md) - Production deployment guide

## 🤝 Development

This service is part of the larger Character Chat API ecosystem. It integrates with:
- **Auth Service** (port 8001) - User authentication
- **Conversation Service** (port 8003) - Conversation management  
- **Characters Service** (port 8002) - Character data
- **LLM Service** (port 8005) - AI processing

Always remember to work within the `.aienv` virtual environment for consistency.