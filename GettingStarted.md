# Getting Started with Foxhole Backend API

## Unique User Identification Concept

Our platform uses a unique approach to user identification:

- Users are identified by a unique, randomly generated userID.
- This userID serves as both the identifier and the access key for authentication.
- No traditional username/password combination is used.
- Users can optionally set a screen name (handle) for display purposes.
- The user model can be easily extended with additional fields as needed.

## User Registration and Authentication

1. Registration: Users receive a unique userID upon registration.
2. Authentication: Users use their userID to obtain an access token.
3. Profile: Additional user information can be added to enrich the user profile.

## Components of the Codebase

1. **Main Application (`main.py`):**
   - Entry point of the application
   - Sets up FastAPI app, routers, and lifecycle management

2. **Core Application (`app/app.py`):**
   - Defines the main FastAPI application
   - Includes routers and dependency injections

3. **Configuration (`app/core/config.py`):**
   - Manages application settings using Pydantic

4. **Routers:**
   - `app/routers/auth.py`: Handles authentication and user-related endpoints
   - `app/routers/health.py`: Provides a health check endpoint
   - `app/routers/websocket.py`: Manages WebSocket connections
   - `app/routers/files.py`: Handles file upload and retrieval

5. **Database Management (`utils/database.py`):**
   - Sets up SQLAlchemy for async database operations

6. **Caching (`utils/cache.py`):**
   - Implements Redis caching functionality

7. **Models (`app/models.py`):**
   - Defines SQLAlchemy ORM models for the application

8. **Services:**
   - `app/services/websocket_manager.py`: Manages WebSocket connections
   - `app/services/storage_service.py`: Handles file storage operations

9. **Dependencies (`app/dependencies.py`):**
   - Defines dependency injection for services

10. **Error Handling (`utils/error_handlers.py`):**
    - Sets up global error handlers for the application

11. **Logging (`utils/logging.py`):**
    - Configures application logging

12. **Testing (`tests/test_main.py`):**
    - Contains unit tests for the application

## Setup and Running the Application

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Set up environment variables or use the default values in `app/core/config.py`

3. Run the application:
   ```
   python main.py
   ```

4. Access the API documentation at `http://localhost:8000/docs`

## Key Features

- FastAPI web framework with automatic OpenAPI documentation
- WebSocket support for real-time communication
- SQLite database with SQLAlchemy ORM (async)
- Redis caching
- MinIO object storage integration
- JWT-based authentication
- File upload and retrieval functionality