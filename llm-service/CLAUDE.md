# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Starting the Application
```bash
# Start with uvicorn directly (recommended for development)
uvicorn app.main:app --reload

# Alternative: Use the run.py script (runs on 0.0.0.0:8022)
python run.py
```

### Dependencies
```bash
# Install all dependencies including local lmstudio-client package
pip install -r requirements.txt

# Install lmstudio-client manually if needed
pip install -e /Users/maxward/Developer/LLMS/Packages/lmstudio-python-client
```

## Architecture Overview

This is a FastAPI-based microservice that acts as an API wrapper for LM Studio's LLM client. The service provides a REST endpoint to interact with large language models hosted in LM Studio.

### Key Components

- **FastAPI Application** (`app/main.py`): Main service with `/llm/message` endpoint
- **LM Studio Integration**: Uses local `lmstudio-client` package to communicate with LM Studio server
- **Pydantic Models**: `LLMRequest` and `Message` models for request validation

### Service Configuration

- **LM Studio URL**: Configured in `app/main.py:25` as `http://localhost:1234`
- **Default Model**: Set to a specific GGUF model in `app/main.py:26`
- **Server Port**: Default 8000 (uvicorn) or 8022 (run.py)

### API Structure

The main endpoint `/llm/message` accepts:
- `model`: LLM model identifier 
- `messages`: Array of conversation messages with role/content
- `temperature`, `max_tokens`, `top_p`: Optional generation parameters
- `stream`: Parameter accepted but not currently implemented

### Dependencies

- **FastAPI**: Web framework
- **Pydantic**: Data validation
- **Uvicorn**: ASGI server
- **lmstudio-client**: Local package for LM Studio integration (required dependency)

### Development Notes

- Service expects LM Studio to be running on localhost:1234
- Response parsing handles multiple potential response formats from LM Studio
- Error handling returns JSON error responses for LLM communication failures
- The service is documented in Spanish (README.md)