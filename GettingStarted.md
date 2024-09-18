# Getting Started with Foxhole Backend API

## Project Overview

Foxhole Backend API is a comprehensive starter kit for building robust Python-based API systems with real-time communication capabilities. It provides a solid foundation with integrated logging, storage, caching, database management, WebSocket support, and a fully-featured CLI. This project aims to accelerate the development of scalable and maintainable backend services.

## Key Features

- FastAPI web framework for high-performance API development
- WebSocket support for real-time communication
- Asynchronous SQLite database with SQLAlchemy ORM
- Redis caching for improved performance
- MinIO integration for object storage
- JWT-based authentication with unique user secrets
- Structured logging
- Global error handling
- Docker and docker-compose setup for easy deployment
- Comprehensive testing framework
- Command-line interface (CLI) for easy interaction with the API

## Architecture and Components

### Folder Structure

```markdown
foxhole/
├── app/
│   ├── core/
│   │   └── config.py
│   ├── routers/
│   │   ├── auth.py
│   │   ├── files.py
│   │   ├── health.py
│   │   └── websocket.py
│   ├── schemas/
│   │   └── user_schema.py
│   ├── services/
│   │   ├── storage_service.py
│   │   └── websocket_manager.py
│   ├── app.py
│   ├── dependencies.py
│   ├── exceptions.py
│   └── models.py
├── cli/
│   ├── commands.py
│   ├── config.py
│   ├── main.py
│   ├── session_manager.py
│   ├── ui.py
│   └── websocket_client.py
├── tests/
│   ├── conftest.py
│   └── test_*.py
├── utils/
│   ├── cache.py
│   ├── database.py
│   ├── error_handlers.py
│   ├── logging.py
│   ├── security.py
│   └── token.py
├── main.py
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

### Code Organization Philosophy

Our code organization follows a modular and separation-of-concerns approach:

- **app/**: Contains the core application logic
  - **core/**: Central configurations and settings
  - **routers/**: API route definitions, separated by functionality
  - **schemas/**: Pydantic models for request/response validation
  - **services/**: Business logic and external service integrations
- **cli/**: Command-line interface for interacting with the API
- **tests/**: Holds all test files, mirroring the structure of the `app/` directory
- **utils/**: Utility functions and helpers used across the application

This structure promotes:

1. **Modularity**: Each component has a clear responsibility
2. **Scalability**: Easy to add new features or modify existing ones
3. **Maintainability**: Clear separation of concerns makes the codebase easier to understand and maintain
4. **Testability**: Organized structure facilitates comprehensive testing

### Component Overview

1. **Main Application (`main.py`):**
   - Entry point of the application
   - Sets up FastAPI app, routers, and lifecycle management

2. **Core Application (`app/app.py`):**
   - Defines the main FastAPI application
   - Includes routers and dependency injections

3. **Configuration (`app/core/config.py`):**
   - Manages application settings using Pydantic

4. **Routers:**
   - `auth.py`: Handles authentication and user-related endpoints
   - `health.py`: Provides a health check endpoint
   - `websocket.py`: Manages WebSocket connections
   - `files.py`: Handles file upload and retrieval

5. **Database Management (`utils/database.py`):**
   - Sets up SQLAlchemy for async database operations

6. **Caching (`utils/cache.py`):**
   - Implements Redis caching functionality

7. **Models (`app/models.py`):**
   - Defines SQLAlchemy ORM models for the application

8. **Services:**
   - `websocket_manager.py`: Manages WebSocket connections
   - `storage_service.py`: Handles file storage operations

9. **Dependencies (`app/dependencies.py`):**
   - Defines dependency injection for services

10. **Error Handling (`utils/error_handlers.py`):**
    - Sets up global error handlers for the application

11. **Logging (`utils/logging.py`):**
    - Configures structured logging for the application

12. **Testing (`tests/`):**
    - Contains unit tests and test configurations

13. **CLI (`cli/`):**
    - Provides a command-line interface for interacting with the API
    - Includes session management, WebSocket client, and user interface components

## Unique Approaches and Design Choices

### User Identification and Authentication

We've implemented a unique approach to user identification:

- Users are identified by a randomly generated userID
- The userID serves as both the identifier and the access key for authentication
- No traditional username/password combination is used
- Users can optionally set a screen name (handle) for display purposes
- The user model is easily extensible for additional fields

This approach simplifies user management and enhances security by eliminating the need for password storage and management.

### Asynchronous Operations

The project leverages FastAPI's asynchronous capabilities, coupled with SQLAlchemy's async support, to provide high-performance, non-blocking operations throughout the application.

### Modular Service Architecture

The application is designed with a modular service architecture, allowing easy extension and modification of core functionalities like storage (currently using MinIO) and caching (using Redis).

### Comprehensive Testing Setup

The project includes a robust testing framework using pytest, with fixtures for database and application setup, ensuring high code quality and reliability.

### CLI Integration

The CLI provides a user-friendly interface to interact with the API, supporting all major functionalities including user management, messaging, and file operations.

## Getting Started

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up environment variables or use default values in `app/core/config.py`
4. Run the application: `python main.py`
5. Access the API documentation at `http://localhost:8000/docs`
6. For CLI usage, run: `python -m cli.main`

## Docker Setup

To run the application using Docker:

1. Build the Docker image:

   ```bash
   docker build -t foxhole-backend .
   ```

2. Run the container:

   ```bash
   docker run -p 8000:8000 foxhole-backend
   ```

The application will be available at `http://localhost:8000`

## Development and Deployment

- For local development, use `uvicorn main:app --reload`
- For deployment, utilize the provided Dockerfile and docker-compose.yml
- Customize the deployment process using Kamal (configuration to be added)

## Contributing

We welcome contributions to the Foxhole Backend API project! Here are some guidelines to help you get started:

1. Fork the repository and create your branch from `main`.
2. If you've added code that should be tested, add tests.
3. Ensure the test suite passes.
4. Make sure your code lints.
5. Issue that pull request!

Please refer to the [GitHub Flow](https://guides.github.com/introduction/flow/) for more details on the contribution process.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
