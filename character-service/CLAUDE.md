# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment Setup

**IMPORTANT**: Always activate the Python virtual environment before running any commands:
```bash
source .aienv/bin/activate
```

## Development Commands

### Running the Application
- **Start server**: `python run.py` (runs on port 8020)
- **Alternative start**: `uvicorn app.main:app --host 0.0.0.0 --port 8020 --reload`

### Testing
- **Run all tests**: `python -m pytest`
- **Run specific test file**: `python -m pytest app/characters/tests/test_models.py`
- **Run with coverage**: `python -m pytest --cov=app`
- **Run specific test**: `python -m pytest app/characters/tests/test_service.py::test_create_character`

### Database
- **Database URL**: `postgresql://postgres:secret@localhost:5431/chatbot`
- Database tables are auto-created on application startup via `create_db_tables()` in `app/main.py:13`

## Architecture Overview

### High-Level Structure
This is a **character management microservice** built with FastAPI that provides CRUD operations for virtual characters in a conversational AI system. The service follows a **layered architecture** pattern:

1. **API Layer** (`app/main.py`, `app/characters/router.py`) - FastAPI endpoints and request handling
2. **Service Layer** (`app/characters/service.py`) - Business logic, caching, and validation
3. **Repository Layer** (`app/characters/repository.py`) - Data access abstraction
4. **Model Layer** (`app/characters/models.py`) - SQLAlchemy ORM models and Pydantic schemas

### Key Components

#### Configuration System (`app/core/config.py`)
- **Comprehensive configuration management** using Pydantic Settings
- **Environment-specific settings** (development, staging, production, testing)
- **Security configurations** including JWT, password hashing, CORS, rate limiting
- **Centralized validation** with production security requirements
- **Configuration sections**: Security, API, LM Studio, Logging, Application

#### Character Management (`app/characters/`)
- **PostgreSQL persistence** with SQLAlchemy ORM
- **In-memory caching** with configurable TTL (default 15 minutes)
- **Repository pattern** for clean data access separation
- **Version tracking** for character updates
- **Soft delete mechanism** (is_active flag)
- **Case-insensitive character lookups**

#### Database Integration
- **PostgreSQL** as primary database (configured in `app/database.py:6`)
- **SQLAlchemy ORM** with synchronous operations
- **Session management** through dependency injection
- **Auto-table creation** on startup

### Business Logic Patterns

#### Character Lifecycle
1. **Creation**: Validates uniqueness, normalizes name to lowercase, sets version to 1
2. **Retrieval**: Cache-first lookup, case-insensitive matching
3. **Updates**: Version increment, cache invalidation, conflict detection
4. **Deletion**: Soft delete (sets is_active=False), cache invalidation

#### Error Handling
- **Centralized exceptions** in `app/core/exceptions.py`
- **Specific error types**: ValidationError, NotFoundError, ConflictError, CharacterServiceError
- **Legacy compatibility** with aliased exception names in service layer
- **Detailed logging** for audit trails

#### Security Implementation
- **Production security validation** enforces HTTPS, secure cookies, disables debug mode
- **Environment-based configuration** with different security requirements
- **JWT configuration** with secure defaults and key strength validation
- **Rate limiting** and CORS protection

### Dependencies and Integration Points

#### External Services
- **LM Studio integration** configured for LLM interactions (`app/core/config.py:296-371`)
- **PostgreSQL database** for persistence
- **Logging system** with audit trails and security event tracking

#### Key Libraries
- **FastAPI** for API framework
- **SQLAlchemy** for ORM and database operations
- **Pydantic** for data validation and settings management
- **Uvicorn** as ASGI server
- **pytest** for testing framework

## Important Notes

- The service expects **PostgreSQL** to be running on `localhost:5431`
- **Cache TTL** is configurable via `APPLICATION.cache_ttl_minutes` setting
- All character names are **normalized to lowercase** for consistency
- **Version numbers** auto-increment on character updates
- **Comprehensive logging** is configured for debugging and audit trails