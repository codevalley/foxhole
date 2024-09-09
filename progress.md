# Project Progress

## Completed
- [x] Basic FastAPI application structure
- [x] Health check endpoint
- [x] Authentication router (implemented)
- [x] WebSocket support
- [x] Database abstraction with SQLAlchemy
- [x] Redis caching setup
- [x] Dockerfile and docker-compose configuration
- [x] Structured logging
- [x] Error handling middleware
- [x] Secure URL generation and secret code mechanism
- [x] Basic testing framework
- [x] Implement simplified user registration and authentication flow
- [x] Develop additional data models and schemas
- [x] Implement CRUD operations for main entities
- [x] Enhance WebSocket functionality for real-time updates
- [x] Implement MinIO integration for object storage
- [x] Complete implementation of `authenticate_user` and `get_current_user` functions in `routers/auth.py`
- [x] Wrap Minio client in a custom class implementing the `StorageService` interface in `app/dependencies.py`
- [x] Replace `print` statements with proper logging in `app/services/storage_service.py`
- [x] Implement proper error handling and validation in file upload and retrieval endpoints in `app/routers/files.py`
- [x] Add authentication to the WebSocket endpoint
- [x] Implement file listing logic in the `list_files` endpoint in `app/routers/files.py`
- [x] Update WebSocket tests to use FastAPI TestClient instead of Starlette TestClient
- [x] Implement `WebSocketManager` from `/app/services/websocket_manager.py` in the main application (`/app/app.py`)
- [x] Fix WebSocket connection handling for invalid tokens
- [x] Resolve WebSocket manager initialization issues in tests and main application
- [x] Correct import issues in test configuration for WebSocket tests
- [x] Improve WebSocket broadcast test to handle potential disconnections
- [x] Enhance WebSocketManager to handle failed message sends
- [x] Fix WebSocket multiple messages test to account for both broadcast and personal messages
- [x] Update WebSocket broadcast test to use synchronous TestClient API
- [x] Fix WebSocket broadcast test to account for both broadcast and personal confirmation messages
- [x] Refine WebSocket broadcast test to handle timeouts and ensure proper connection closure
- [x] Refactor WebSocket broadcast test to use synchronous TestClient API
- [x] Add detailed logging to WebSocketManager and WebSocket tests
- [x] Implement timeouts in WebSocket broadcast test to prevent indefinite hanging
- [x] Fix logging import issues in test files and conftest.py
- [x] Fix WebSocket broadcast test to use synchronous TestClient approach
- [x] Update WebSocket unauthorized test to handle new error message format
- [x] Ensure use of FastAPI TestClient instead of Starlette TestClient in tests
- [x] Fix linting and type checking issues in WebSocket-related files
- [x] Address mypy type checking issues in WebSocket-related files
- [x] Fix MINIO_SECURE setting in app configuration
- [x] Correct WebSocket test type annotations
- [x] Fix string indexing issue in WebSocket unauthorized test
- [x] Align CI checks with local pre-commit hooks for consistency
- [x] Update pre-commit configuration to ensure all checks are in "check-only" mode
- [x] Run pre-commit install to apply new pre-commit configuration
- [x] Implement asynchronous WebSocket manager with proper connection handling and disconnection events
- [x] Update WebSocket endpoint to use the new WebSocketManager features
- [x] Refactor WebSocket tests to use asynchronous operations and proper connection closure checks
- [x] Implement wait_for_disconnect method in WebSocketManager to ensure proper disconnection in tests
- [x] Add more detailed logging in WebSocketManager for better debugging
- [x] Update test_websocket_disconnect to use the new wait_for_disconnect method
- [x] Ensure proper cleanup of WebSocket connections in tests, even in case of failures

## In Progress
- [ ] Set up Docker and Kamal configuration for deployment
- [ ] Add more logging statements throughout the application for better debugging and monitoring
- [ ] Expand test coverage, especially for dependencies.py, auth.py and websocket.py

## To Do
- [ ] Implement rollback and monitoring strategies
- [ ] Enhance documentation
- [ ] Design and implement offline message queueing
- [ ] Add rate limiting for API endpoints to prevent abuse
- [ ] Implement database migrations for easier schema management
- [ ] Add API versioning to make future updates easier
- [ ] Debug and fix WebSocket broadcast test

## Issues and Improvements
- [ ] Investigate and resolve issues with WebSocket broadcast functionality
- [ ] Consider implementing a more robust WebSocket connection management system
- [ ] Evaluate and improve the current authentication mechanism for scalability
- [ ] Implement a more comprehensive error handling and reporting system
- [ ] Consider adding integration tests to cover end-to-end scenarios
- [ ] Optimize database queries for better performance, especially for file operations
- [ ] Implement a caching strategy to reduce database load for frequently accessed data
- [ ] Consider implementing a background task queue for handling long-running operations

## Current Problem
- The `test_websocket_disconnect` test is still failing with the error: "AssertionError: WebSocket connection not closed properly"
- The WebSocket connection is not being removed from the `active_connections` dictionary in the `WebSocketManager` after the connection is closed
- Possible causes:
  1. The `disconnect` method in `WebSocketManager` is not being called when the WebSocket connection is closed
  2. The `disconnect` method is not properly removing the connection from `active_connections`
  3. The test is not giving enough time for the asynchronous disconnect operation to complete
  4. The `close_all_connections` method in `WebSocketManager` might not be working as expected
  5. The WebSocket connection might be staying open longer than expected in the test environment
- Next steps:
  1. Review the `WebSocketManager.disconnect` method implementation and ensure it's being called when the WebSocket closes
  2. Add more detailed logging in the `disconnect` and `close_all_connections` methods to track their execution
  3. Investigate if we need to use an event or a different synchronization mechanism in the test to ensure the disconnect operation completes before asserting
  4. Review the `close_all_connections` method in `WebSocketManager` and ensure it's properly closing all connections
  5. Consider adding a delay or retry mechanism in the test to allow for asynchronous operations to complete
  6. Verify that the `WebSocketManager` instance used in the test is the same one used by the application
  7. Implement a cleanup mechanism in the test to ensure all connections are closed, even if the test fails
  8. Add more granular assertions to track the state of the WebSocket connection throughout the test

New issue:
- The test is using a synchronous `TestClient` for WebSocket connections, which may not properly handle asynchronous operations
- This could lead to race conditions where the connection is not fully closed before the assertions are made
- To address this:
  1. Consider using an asynchronous WebSocket client for testing, such as `websockets` or `aiohttp`
  2. Implement proper asynchronous context managers for WebSocket connections in the tests
  3. Ensure that all asynchronous operations, including connection closure, are properly awaited

Note: When implementing these fixes, we need to be careful not to regress on previously fixed issues, such as the SQLAlchemy error handling and the WebSocket manager initialization problems.
