# Project Progress

## Current activity

1. Simplifying Code Structure:

   a) ~~Standardize database session handling:~~
      ~~- Use a single approach for database operations across all endpoints.~~
      ~~- Leverage FastAPI's dependency injection system consistently.~~

   b) ~~Refactor the login_for_access_token function:~~
      ~~- Remove the complex session type checking.~~
      ~~- Use a single, consistent method to query the database.~~

   c) ~~Extract common database operations into utility functions:~~
      ~~- Create a separate module for database operations.~~
      ~~- Implement functions for common queries (e.g., get_user_by_id).~~

   d) ~~Use more descriptive variable names:~~
      ~~- Rename 'user_id' to 'secret_code' for clarity.~~

   e) ~~Simplify error handling:~~
      ~~- Use try-except blocks consistently.~~
      ~~- Create custom exceptions for specific error cases.~~

2. Cleaning up Logs/Error Handling:

   a) Replace print statements with proper logging:
      - Use the logging module consistently across the application.
      - Set up different log levels (DEBUG, INFO, ERROR) as appropriate.

   b) ~~Implement structured error responses:~~
      ~~- Create a standard error response format.~~
      ~~- Use custom exception classes for different types of errors.~~

   c) ~~Improve exception handling:~~
      ~~- Catch specific exceptions rather than using broad except clauses.~~
      ~~- Provide more informative error messages to clients.~~

   d) Add request ID to logs:
      - Implement a middleware to assign a unique ID to each request.
      - Include this ID in all log messages for better traceability.

Plan of Action:

1. ~~Create a new module for database operations (e.g., `app/db/operations.py`).~~
2. ~~Refactor the auth router to use the new database operations module.~~
3. Implement proper logging throughout the auth router.
4. ~~Create custom exceptions for auth-related errors.~~
5. ~~Update the login_for_access_token function to use the simplified approach.~~
6. ~~Update error responses to use a consistent format.~~

### Pending
1. Ensure robust input validation using Pydantic models for all API endpoints.
2. Setup consistent logging configuration for the entire application, and have centralized management (log levels, formatting, integrations etc.)
3. Evaluate middlewares (Unique request ID per request, error handling, logging etc.).

## Pick up next
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

## Issues and Improvements
- [ ] Implement a more comprehensive error handling and reporting system
- [ ] Consider adding integration tests to cover end-to-end scenarios
- [ ] Optimize database queries for better performance, especially for file operations
- [ ] Implement a caching strategy to reduce database load for frequently accessed data
- [ ] Consider implementing a background task queue for handling long-running operations
