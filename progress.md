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

## In Progress
- [ ] Implement more comprehensive test coverage
- [ ] Set up Kamal configuration for deployment

## To Do
- [ ] Implement rollback and monitoring strategies
- [ ] Enhance documentation
- [ ] Implement data isolation strategy for chambers
- [ ] Design and implement offline message queueing

## Issues and Improvements
- [ ] Complete implementation of `authenticate_user` and `get_current_user` functions in `routers/auth.py`
- [ ] Wrap Minio client in a custom class implementing the `StorageService` interface in `app/dependencies.py`
- [ ] Replace `print` statements with proper logging in `app/services/storage_service.py`
- [ ] Consolidate configuration files: remove `config.py` and use `app/core/config.py` throughout the application
- [ ] Consolidate `User` model definitions in `app/models.py` and `models/user.py`
- [ ] Implement proper error handling and validation in file upload and retrieval endpoints in `app/routers/files.py`
- [ ] Add authentication to the WebSocket endpoint if required
- [ ] Implement file listing logic in the `list_files` endpoint in `app/routers/files.py`
- [ ] Add more comprehensive test coverage in `tests/test_main.py`
- [ ] Ensure all sensitive information (like `SECRET_KEY`) is properly secured and not hardcoded in configuration files