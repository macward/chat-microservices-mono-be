# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment Setup

**IMPORTANT: All installations and executions must be done in the .aienv environment.**

```bash
# Load the Python virtual environment
source .aienv/bin/activate
```

The project uses Python with FastAPI as a microservice for message processing and LLM integration.

## Project Overview

This is the **Message Service** - a FastAPI-based microservice that handles message processing, storage, and LLM integration within the Character Chat API ecosystem.

**Key Responsibilities:**
- Message processing, validation, and sanitization
- LLM provider integration (LM Studio, OpenAI, Anthropic)
- Real-time analytics and token tracking
- Content safety and moderation
- High-volume message storage with MongoDB

**Architecture:**
- **Port**: 8009
- **Database**: MongoDB with Beanie ODM
- **Cache/Queue**: Redis
- **Framework**: FastAPI with async/await
- **LLM Integration**: Multiple providers with circuit breaker pattern

## Development Setup

Since the codebase is currently documentation-only, follow this structure for implementation:

### Directory Structure (To Be Implemented)
```
message-service/
├── app/
│   ├── main.py                    # FastAPI application entry point
│   ├── config.py                  # Configuration management
│   ├── database.py                # MongoDB connection setup
│   ├── api/                       # API layer
│   │   ├── v1/
│   │   │   ├── messages.py        # Message endpoints
│   │   │   ├── llm.py            # LLM processing endpoints
│   │   │   └── analytics.py       # Analytics endpoints
│   ├── services/                  # Business logic
│   │   ├── message_service.py     # Core message operations
│   │   ├── llm_service.py         # LLM integration
│   │   └── content_service.py     # Content processing
│   ├── repositories/              # Data access layer
│   │   └── message_repository.py  # MongoDB operations
│   ├── models/                    # Data models
│   │   ├── message.py            # Pydantic models
│   │   └── database.py           # Beanie ODM models
│   ├── workers/                   # Background processors
│   │   ├── message_processor.py  # Async message processing
│   │   └── llm_worker.py         # LLM processing worker
│   └── core/                     # Core utilities
│       ├── security.py           # Security utilities
│       ├── cache.py              # Redis cache wrapper
│       └── exceptions.py         # Custom exceptions
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   └── conftest.py               # Pytest configuration
├── scripts/                      # Utility scripts
│   └── setup_indexes.py          # MongoDB index setup
├── requirements.txt              # Production dependencies
├── requirements-dev.txt          # Development dependencies
├── requirements-workers.txt      # Worker dependencies
└── .env.example                  # Environment template
```

## Development Commands

### Environment Management
```bash
# Activate virtual environment (REQUIRED)
source .aienv/bin/activate

# Install dependencies (when requirements.txt exists)
pip install -r requirements.txt
pip install -r requirements-dev.txt
pip install -r requirements-workers.txt
```

### Development Server
```bash
# Start the FastAPI development server
python -m app.main

# Alternative using uvicorn directly
uvicorn app.main:app --host 0.0.0.0 --port 8009 --reload
```

### Background Workers
```bash
# Start message processing worker
python workers/message_processor.py

# Start LLM processing worker  
python workers/llm_worker.py

# Start analytics worker
python workers/analytics_worker.py
```

### Database Operations
```bash
# Setup MongoDB indexes
python scripts/setup_indexes.py

# Run database migrations
python scripts/migrate_data.py
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test types
pytest tests/unit/
pytest tests/integration/
```

### Code Quality
```bash
# Format code
black app/ tests/

# Sort imports
isort app/ tests/

# Type checking
mypy app/

# Linting
flake8 app/
ruff app/

# Run all quality checks
./scripts/check-code-quality.sh
```

## Docker Development

```bash
# Build and run with Docker Compose
docker-compose up -d

# View service logs
docker-compose logs -f message-service

# Scale workers
docker-compose up -d --scale llm-worker=5

# Run tests in container
docker-compose exec message-service pytest
```

## Key Technical Details

### Database Schema
- **Primary Collection**: `messages` (sharded by `conversation_id`)
- **Analytics**: `message_analytics` (precomputed aggregations)  
- **Search**: `message_search_index` (full-text search optimization)
- **Queue**: `processing_queue` (async job management)

### LLM Integration
- **Providers**: LM Studio (primary), OpenAI, Anthropic
- **Circuit Breaker**: Fault tolerance for provider failures
- **Rate Limiting**: 100 messages/minute per user
- **Token Tracking**: Cost analysis and usage metrics

### Performance Optimizations
- **Caching Strategy**: Multi-level (in-memory, Redis, MongoDB)
- **Connection Pooling**: MongoDB (20-100 connections), Redis (50 connections)
- **Async Processing**: Background workers for LLM requests
- **Sharding**: Horizontal scaling by conversation_id

### Security Features
- **Content Filtering**: Multi-stage safety pipeline
- **Rate Limiting**: Per-user and per-endpoint limits
- **Input Validation**: Pydantic models with custom validators
- **JWT Authentication**: Bearer token validation

## External Dependencies

The service requires these external services to be running:

| Service | Port | Purpose |
|---------|------|---------|
| MongoDB | 27017 | Primary database |
| Redis | 6379 | Cache and message queue |
| Auth Service | 8001 | User authentication |
| Conversation Service | 8003 | Conversation metadata |
| Characters Service | 8002 | Character data |
| LLM Service | 8005 | AI processing |

## Environment Variables

Key configuration (copy from `.env.example`):

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

# LLM
DEFAULT_LLM_PROVIDER=lmstudio
DEFAULT_MODEL=google/gemma-3-12b
MAX_TOKENS_PER_REQUEST=2048

# External Services
AUTH_SERVICE_URL=http://localhost:8001
CONVERSATION_SERVICE_URL=http://localhost:8003
CHARACTERS_SERVICE_URL=http://localhost:8002
LLM_SERVICE_URL=http://localhost:8005
```

## Important Implementation Notes

- **Async-First**: Use `async/await` throughout for scalability
- **Error Handling**: Implement comprehensive exception handling with custom exceptions
- **Logging**: Use structured logging with correlation IDs for tracing
- **Health Checks**: Include dependency health monitoring in `/health` endpoint
- **Metrics**: Implement Prometheus metrics for monitoring
- **Message Immutability**: Messages cannot be modified once created (only archived)
- **Idempotency**: Support client message IDs for duplicate prevention

## Testing Strategy

- **Unit Tests**: Service layer business logic
- **Integration Tests**: Database and external service interactions
- **Contract Tests**: API endpoint behavior
- **Performance Tests**: Load testing for high-volume scenarios

Remember to always work within the `.aienv` virtual environment for all development activities.