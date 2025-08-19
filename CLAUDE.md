# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **microservices-based backend ecosystem** for a Character Chat API system. The project contains multiple independent Python FastAPI microservices that work together to provide conversational AI functionality.

### Microservices Architecture

The system consists of 5 microservices, each running on different ports:

| Service | Port | Database | Purpose |
|---------|------|----------|---------|
| **user-service** | 8024 | PostgreSQL | JWT authentication, user management, credits system |
| **character-service** | 8020 | PostgreSQL | Character CRUD operations, metadata management |
| **conversation-service** | 8003 | MongoDB | Conversation management, session handling |
| **message-service** | 9 | MongoDB + Redis | Message processing, LLM integration, analytics |
| **llm-service** | 8022 | N/A | LM Studio API wrapper, model interaction |

### Environment Setup

**CRITICAL**: All microservices use a shared Python virtual environment:

```bash
# ALWAYS activate before any operation
source .aienv/bin/activate
```

### Common Development Commands

#### Starting Services

Each service has its own startup script in its directory:

```bash
# Individual service startup (from service directory)
python run.py

# Alternative uvicorn startup
uvicorn app.main:app --reload --host 0.0.0.0 --port <SERVICE_PORT>
```

#### Testing Commands

Most services use pytest for testing:

```bash
# Basic testing (from service directory)
python -m pytest

# Coverage testing
pytest --cov=app --cov-report=html

# Service-specific test variations:
# - character-service: pytest app/characters/tests/
# - llm-service: make test (has comprehensive Makefile)
```

#### Code Quality (LLM Service has full implementation)

```bash
# From llm-service directory
make lint      # Run all linting (flake8, mypy, black, isort)
make format    # Auto-format code
make clean     # Clean temporary files
```

## Architecture Patterns

### Technology Stack
- **Framework**: FastAPI (async Python web framework)
- **Databases**: PostgreSQL (user/character data), MongoDB (conversations/messages)
- **Cache/Queue**: Redis (message service)
- **Authentication**: JWT tokens with OAuth2 Bearer scheme
- **ORM/ODM**: SQLAlchemy (PostgreSQL), Beanie ODM (MongoDB)
- **Validation**: Pydantic v2 models
- **Testing**: pytest with httpx for API testing

### Layered Architecture

All services follow a consistent 3-layer pattern:

```
app/
├── main.py                    # FastAPI application entry point
├── config.py                  # Configuration management
├── database.py                # Database connection setup
├── api/                       # API layer
│   └── v1/                    # Version 1 endpoints
├── services/                  # Business logic layer
├── repositories/              # Data access layer
├── models/                    # Data models (Pydantic/SQLAlchemy/Beanie)
└── core/                      # Core utilities (exceptions, security)
```

### Service Communication

Services communicate via HTTP APIs:

- **Authentication Flow**: user-service → JWT tokens → other services
- **Character Validation**: conversation-service → character-service
- **Message Processing**: message-service → llm-service → LM Studio
- **Mock Services**: conversation-service includes mock auth/character services for development

### Database Configuration

#### PostgreSQL Services (user-service, character-service)
```
Connection: postgresql://postgres:secret@localhost:5431/chatbot
```

#### MongoDB Services (conversation-service, message-service)
```
Connection: mongodb://localhost:27017
Database: <service_name>_dev
```

### Key Integration Points

#### LM Studio Integration
- **LLM Service** acts as API wrapper for LM Studio (localhost:1234)
- **Message Service** processes requests through LLM Service
- Local `lmstudio-client` package required for llm-service

#### External Dependencies
Services require these external systems:
- **PostgreSQL** (port 5431) for user/character data
- **MongoDB** (port 27017) for conversation/message data  
- **Redis** (port 6379) for message service caching
- **LM Studio** (port 1234) for AI model inference

### Development Workflow

#### Service Independence
Each microservice can be developed and tested independently:
- Individual CLAUDE.md files in each service directory
- Separate requirements.txt and configuration
- Independent database schemas and port allocation

#### Docker Support
Conversation service includes complete Docker Compose setup:
```bash
# From conversation-service directory
docker-compose up -d    # Start all services with dependencies
```

#### Testing Strategy
- **Unit Tests**: Service layer business logic
- **Integration Tests**: Database and external service interactions
- **Mock Services**: conversation-service provides auth/character mocks

### Security Implementation
- **JWT Authentication**: 30-minute token expiration, bcrypt password hashing
- **Environment-based Configuration**: Development vs production settings
- **Input Validation**: Comprehensive Pydantic models
- **Rate Limiting**: Implemented in message-service

### Configuration Management
Each service uses environment-specific configuration:
- **Development**: `.env` files with local database connections
- **Production**: Environment variables with security validation
- **Testing**: Isolated test configurations

## Important Notes

- **Virtual Environment**: ALWAYS use `.aienv` virtual environment for all operations
- **Port Allocation**: Each service has fixed port assignments to avoid conflicts
- **Database Isolation**: PostgreSQL and MongoDB services use separate databases
- **Async-First**: All services use async/await for scalability
- **Service Discovery**: Services communicate via hardcoded localhost URLs (development)
- **Error Handling**: Centralized exception handling with custom exception classes
- **Logging**: Structured logging with correlation IDs for request tracing

### Development Best Practices

- **Start Dependencies First**: Ensure databases and external services are running
- **Service-Specific Commands**: Use individual service CLAUDE.md files for detailed commands
- **Integration Testing**: Use conversation-service Docker Compose for full system testing
- **Code Quality**: Follow llm-service Makefile patterns for linting and formatting