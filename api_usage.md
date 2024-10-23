# API Usage Guide

This document provides an overview of the available endpoints in the Foxhole Backend API and how to use them.

## Authentication

### Register a new user

- **Endpoint**: `POST /auth/register`
- **Body**:  ```json
  {
    "screen_name": "your_username"
  }  ```
- **Response**: Returns a `user_secret` which is used for authentication.

### Get access token

- **Endpoint**: `POST /auth/token`
- **Body**:  ```json
  {
    "user_secret": "your_user_secret"
  }  ```
- **Response**: Returns an `access_token` which is used for authenticated requests.

## Sidekick Service

### Ask Sidekick

- **Endpoint**: `POST /api/v1/sidekick/ask`
- **Headers**: `Authorization: Bearer your_access_token`
- **Body**:  ```json
  {
    "user_input": "Your question or command",
    "thread_id": "optional_thread_id"
  }  ```
- **Response**: Returns Sidekick's response and updated context information.

### Topics

#### List Topics

- **Endpoint**: `GET /api/v1/sidekick/topics`
- **Headers**: `Authorization: Bearer your_access_token`
- **Query Parameters**: `page` (default: 1), `page_size` (default: 10)
- **Response**: Returns a paginated list of topics.

#### Create Topic

- **Endpoint**: `POST /api/v1/sidekick/topics`
- **Headers**: `Authorization: Bearer your_access_token`
- **Body**:  ```json
  {
    "topic_id": "unique_topic_id",
    "name": "Topic Name",
    "description": "Topic Description",
    "keywords": ["keyword1", "keyword2"],
    "related_people": ["person_id1", "person_id2"],
    "related_tasks": ["task_id1", "task_id2"]
  }  ```
- **Response**: Returns the created topic.

#### Update Topic

- **Endpoint**: `PUT /api/v1/sidekick/topics/{topic_id}`
- **Headers**: `Authorization: Bearer your_access_token`
- **Body**: Same as Create Topic
- **Response**: Returns the updated topic.

#### Delete Topic

- **Endpoint**: `DELETE /api/v1/sidekick/topics/{topic_id}`
- **Headers**: `Authorization: Bearer your_access_token`
- **Response**: Confirmation of deletion.

### Tasks

(Similar CRUD operations as Topics)

### People

(Similar CRUD operations as Topics)

### Notes

(Similar CRUD operations as Topics)

## WebSocket

### Connect to WebSocket

- **Endpoint**: `ws://your_domain/ws/{client_id}`
- **Query Parameters**: `token=your_access_token`
- **Usage**: Use this connection to receive real-time updates and messages.

## File Operations

### Upload File

- **Endpoint**: `POST /files/upload`
- **Headers**: `Authorization: Bearer your_access_token`
- **Body**: `multipart/form-data` with file
- **Response**: Returns information about the uploaded file.

### Download File

- **Endpoint**: `GET /files/download/{file_id}`
- **Headers**: `Authorization: Bearer your_access_token`
- **Response**: File download.

### List Files

- **Endpoint**: `GET /files/list`
- **Headers**: `Authorization: Bearer your_access_token`
- **Response**: Returns a list of files associated with the user.

## Rate Limiting

The API implements rate limiting to prevent abuse. The current limits are:

- Login endpoint: 5 requests per minute
- Registration endpoint: 10 requests per minute

Rate limit information is included in the response headers:

- `X-RateLimit-Limit`: The maximum number of requests allowed in the current time window
- `X-RateLimit-Remaining`: The number of requests remaining in the current time window
- `X-RateLimit-Reset`: The time at which the current rate limit window resets

When a rate limit is exceeded, the API will respond with a 429 (Too Many Requests) status code.

## Error Handling

The API uses standard HTTP status codes for error responses. Common error codes include:

- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 429: Too Many Requests
- 500: Internal Server Error

Error responses will include a JSON body with more details about the error.

For more detailed information about the API, including request and response schemas, please refer to the OpenAPI documentation available at `http://your_domain/docs` when the server is running.
