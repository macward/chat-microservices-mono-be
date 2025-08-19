# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment Setup

Always activate the Python virtual environment before running any commands:
```bash
source .aienv/bin/activate
```

## Development Commands

### Setup and Installation
```bash
# Setup environment and install dependencies
source .aienv/bin/activate
pip install -r requirements.txt

# Environment configuration
cp .env.example .env
# Edit .env with your MongoDB URL and settings
```

### Running the Service
```bash
# Development server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8003

# Production-like run
python -m app.main

# With custom environment
ENVIRONMENT=development python -m app.main
```

### Testing Commands
```bash
# Run all tests (when implemented)
pytest

# Run with coverage (when implemented)  
pytest --cov=app tests/

# Test specific modules (when implemented)
pytest tests/test_conversation_service.py
```

### API Testing
```bash
# Health check
curl http://localhost:8003/health

# API documentation
# Navigate to http://localhost:8003/docs
```

## Architecture Overview

This is a **microservice for conversation management** in the Character Chat API ecosystem, following a **3-layer architecture pattern**:

### Core Architecture Layers
1. **API Layer** (`app/api/`) - FastAPI routers and endpoints
2. **Service Layer** (`app/services/`) - Business logic and external service integration  
3. **Repository Layer** (`app/repositories/`) - Data access and MongoDB operations

### Key Components
- **FastAPI Application** (`app/main.py`) - Entry point with startup events
- **Configuration Management** (`app/config.py`) - Environment-based settings with pydantic-settings
- **Database Connection** (`app/database.py`) - MongoDB initialization with Beanie ODM
- **Data Models** (`app/models/`) - Pydantic models for validation and Beanie models for MongoDB

### Technology Stack
- **Framework**: FastAPI (async Python web framework)
- **Database**: MongoDB with Beanie ODM (async Pydantic-based)
- **Validation**: Pydantic v2 with typed models
- **Server**: Uvicorn ASGI server

### Development Approach
The project follows an **MVP + Incremental Scaling** methodology:
- **MVP Phase**: Basic CRUD operations with minimal features
- **Scaling Phases**: Authentication → Validation → External Services → Advanced Features → Production

### Service Integration Points
This microservice integrates with:
- **Auth Service** (port 8001) - JWT token validation and user management
- **Characters Service** (port 8002) - Character validation and metadata
- **Message Service** (port 8009) - Message statistics and conversation metrics

### Database Schema
Uses MongoDB with collections:
- `conversations` - Main conversation documents with user ownership, character association, and metadata

### Configuration
Environment variables are managed through `.env` file:
- `MONGODB_URL` - Database connection string
- `MONGODB_DATABASE` - Database name (default: conversation_service)
- `PORT` - Service port (default: 8003)
- `ENVIRONMENT` - Runtime environment (development/production)

### Current Implementation Status
**MVP Phase**: ✅ Completed
- Basic project structure with 3-layer architecture
- MongoDB connection with Beanie ODM
- Core conversation models (simplified)
- Basic CRUD endpoints for conversations
- Health check endpoint

**Next Phases**: Authentication, enhanced validation, external service integration

### Development Notes
- Uses async/await throughout for better performance
- Implements repository pattern for clean data access
- Configuration via pydantic-settings for type safety
- Designed for horizontal scaling in container environments