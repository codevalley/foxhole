# Project Progress

## Current activity

1. Simplifying Code Structure:
   (All items are completed)

2. Cleaning up Logs/Error Handling:

   a) Replace print statements with proper logging:
      - Use the logging module consistently across the application. (Partially completed)
      - Set up different log levels (DEBUG, INFO, ERROR) as appropriate. (Partially completed)

   (Other items are completed)

Plan of Action:
(All items are completed except for item 3)

3. Implement proper logging throughout the auth router. (Partially completed)

### Pending

1. Ensure robust input validation using Pydantic models for all API endpoints. (Partially completed)
2. Setup consistent logging configuration for the entire application, and have centralized management (log levels, formatting, integrations etc.) (Partially completed)

## Pick up next

- [x] Set up Docker and Kamal configuration for deployment
- [ ] Add more logging statements throughout the application for better debugging and monitoring (In progress)
- [ ] Expand test coverage, especially for dependencies.py, auth.py and websocket.py (Partially completed)

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
