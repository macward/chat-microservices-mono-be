# Fase 2: Validaciones (Robustez) - Detailed Implementation Plan

## Overview
- **Objective**: Improve service quality, reliability, and input validation
- **Estimated Total Time**: 2-3 hours
- **Target Components**: Conversation model, API endpoints, error handling

## Task Breakdown

### 1. Input Validation for Conversation Creation Model
- **File**: `/app/models/conversation.py`
- **Estimated Time**: 45 minutes
- **Acceptance Criteria**:
  - Add Pydantic v2 validation rules for all conversation fields
  - Implement strict type checking
  - Add custom validation for user_id and character_id formats
- **Technical Considerations**:
  - Use Pydantic's `@validator` decorators for complex validations
  - Enforce constraints like:
    - `title`: 3-100 characters, no special characters
    - `user_id`: UUID or ObjectId format
    - `character_id`: UUID or ObjectId format
    - Prevent empty or whitespace-only inputs
- **Validation Checks**:
  ```python
  class ConversationCreate(BaseModel):
      title: str = Field(
          min_length=3, 
          max_length=100, 
          pattern=r'^[a-zA-Z0-9\s]+$'
      )
      user_id: str = Field(
          description="User identifier", 
          min_length=24, 
          max_length=36
      )
      # Additional field validations
  ```

### 2. Custom Validation Error Handlers
- **File**: `/app/api/exceptions.py` (create if not exists)
- **Estimated Time**: 30 minutes
- **Acceptance Criteria**:
  - Create custom exception classes for different validation scenarios
  - Implement global exception handler for validation errors
  - Standardize error response format
- **Technical Implementation**:
  ```python
  from fastapi import HTTPException, Request
  from fastapi.responses import JSONResponse

  class ValidationErrorException(HTTPException):
      def __init__(self, detail: str):
          super().__init__(status_code=422, detail=detail)

  @app.exception_handler(ValidationError)
  async def validation_exception_handler(request: Request, exc: ValidationError):
      return JSONResponse(
          status_code=422,
          content={
              "error": "Validation Failed",
              "details": exc.errors(),
              "timestamp": datetime.now().isoformat()
          }
      )
  ```

### 3. Structured Error Response Mechanism
- **File**: `/app/api/responses.py`
- **Estimated Time**: 30 minutes
- **Acceptance Criteria**:
  - Create a consistent error response structure
  - Include error code, message, and optional details
  - Support multiple error types (validation, not found, permission)
- **Implementation Notes**:
  ```python
  from enum import Enum

  class ErrorCode(str, Enum):
      VALIDATION_ERROR = "VALIDATION_001"
      NOT_FOUND = "NOT_FOUND_001"
      PERMISSION_DENIED = "PERMISSION_001"

  def create_error_response(
      code: ErrorCode, 
      message: str, 
      details: Optional[Dict] = None
  ) -> Dict:
      return {
          "error_code": code,
          "message": message,
          "details": details or {},
          "timestamp": datetime.now().isoformat()
      }
  ```

### 4. Comprehensive Field Validation Rules
- **File**: `/app/services/conversation_service.py`
- **Estimated Time**: 30 minutes
- **Acceptance Criteria**:
  - Add service-level validation for conversation attributes
  - Implement business logic validations
  - Prevent invalid state transitions
- **Validation Examples**:
  ```python
  def validate_conversation_creation(conversation: ConversationCreate):
      # Check user existence
      user = await UserService.get_user(conversation.user_id)
      if not user:
          raise ValidationErrorException("Invalid user")
      
      # Limit conversations per user
      existing_conversations = await ConversationRepo.count_user_conversations(user.id)
      if existing_conversations >= MAX_USER_CONVERSATIONS:
          raise ValidationErrorException("Conversation limit exceeded")
  ```

### 5. Error Event Logging
- **File**: `/app/services/logging_service.py`
- **Estimated Time**: 15 minutes
- **Acceptance Criteria**:
  - Implement structured logging for validation errors
  - Log error details without sensitive information
  - Use contextual logging with request metadata
- **Implementation**:
  ```python
  import logging
  from structlog import get_logger

  logger = get_logger()

  def log_validation_error(error: ValidationError, context: Dict):
      logger.error(
          "Validation failed", 
          error_type="validation",
          error_details=error.errors(),
          request_context=context
      )
  ```

## Dependencies and Execution Order
1. Update Conversation Model Validations
2. Create Error Response Mechanisms
3. Implement Service-Level Validations
4. Add Custom Error Handlers
5. Configure Error Logging

## Recommended Tools and Libraries
- Pydantic v2 for model validation
- structlog for advanced logging
- FastAPI's built-in exception handling

## Testing Recommendations
- Unit test each validation rule
- Create integration tests for error scenarios
- Verify error response consistency
- Test edge cases and boundary conditions

## Potential Risks and Mitigations
- Over-validation might impact performance
- Complex validation logic can introduce bugs
- Ensure error messages are informative but not revealing sensitive details

## Next Steps
- Conduct thorough testing of validation mechanisms
- Review and potentially refine validation rules
- Monitor service performance after implementation