# Project Progress

## Completed
- [x] Basic FastAPI application structure
- [x] Health check endpoint
- [x] Authentication router (skeleton)
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

## Issues and Improvements
- [x] Complete implementation of `authenticate_user` and `get_current_user` functions in `routers/auth.py`
- [x] Wrap Minio client in a custom class implementing the `StorageService` interface in `app/dependencies.py`
- [x] Replace `print` statements with proper logging in `app/services/storage_service.py`
- [x] Consolidate configuration files: remove `config.py` and use `app/core/config.py` throughout the application
- [x] Consolidate `User` model definitions in `app/models.py` and remove `models` folder
- [x] Implement proper error handling and validation in file upload and retrieval endpoints in `app/routers/files.py`
- [x] Add authentication to the WebSocket endpoint if required
- [x] Implement file listing logic in the `list_files` endpoint in `app/routers/files.py`
- [x] Add more comprehensive test coverage in `tests/test_main.py`
- [x] Ensure all sensitive information (like `SECRET_KEY`) is properly secured and not hardcoded in configuration files


## In Progress
- [ ] Implement more comprehensive test coverage
- [ ] Set up Docker andKamal configuration for deployment

## To Do
- [ ] Implement rollback and monitoring strategies
- [ ] Enhance documentation
- [ ] Implement data isolation strategy for chambers
- [ ] Design and implement offline message queueing
- [ ] Add rate limiting for API endpoints to prevent abuse
- [ ] Implement database migrations for easier schema management
- [ ] Implement logging throughout the application for better debugging and monitoring
- [ ] Add API versioning to make future updates easier
