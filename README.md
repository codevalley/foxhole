# Foxhole Backend API

![CI](https://github.com/codevalley/foxhole/workflows/CI/badge.svg)
[![codecov](https://codecov.io/gh/codevalley/foxhole/branch/main/graph/badge.svg)](https://codecov.io/gh/codevalley/foxhole)

Foxhole Backend API is a comprehensive starter kit for building robust Python-based API systems with real-time communication capabilities. It provides a solid foundation with integrated logging, storage, caching, database management, WebSocket support, and a fully-featured CLI.

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
- Comprehensive testing framework with pytest
- Command-line interface (CLI) for easy interaction with the API
- Rate limiting for API endpoints using slowapi and Redis
- Sidekick service with AI-powered assistance and entity management (topics, tasks, people, notes)

## Getting Started

See the [GettingStarted.md](GettingStarted.md) file for detailed setup and usage instructions for both the backend API and CLI.

## Quick Start

1. Clone the repository:

   ```bash
   git clone https://github.com/codevalley/foxhole.git
   cd foxhole
   ```

2. Create a virtual environment and install dependencies:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   pip install -r requirements.txt
   ```

3. Run the application:

   ```bash
   uvicorn main:app --reload
   ```

4. Open your browser and navigate to `http://localhost:8000/docs` to see the API documentation.

5. To use the CLI:

   ```bash
   python -m cli.main
   ```

## Authentication

Foxhole uses a unique authentication approach:

1. Users register with a screen name.
2. The system generates a `user_secret` for each user.
3. Users authenticate using their `user_secret` to obtain a JWT token.

Example:

```python
# Register a new user
response = requests.post("/auth/register", json={"screen_name": "testuser"})
user_secret = response.json()["user_secret"]

# Login
response = requests.post("/auth/token", data={"user_secret": user_secret})
access_token = response.json()["access_token"]
```

## Development

- For local development of the backend, use `uvicorn main:app --reload`
- For the CLI, run `python -m cli.main`
- Utilize the provided Dockerfile and docker-compose.yml for containerized deployment

## Testing

Run tests using pytest:

```bash
pytest
```

## CLI Features

The Foxhole CLI provides a user-friendly interface to interact with the API. Key features include:

- User authentication (login and registration)
- Session management (save and resume sessions)
- Send broadcast and direct messages
- View and update user profile information
- Real-time message reception using WebSocket connection
- File upload, download, and listing functionality

For more details on CLI usage, refer to the [CLI README](cli/README.md).

## Project Structure

```markdown
foxhole/
├── app/            # Core application logic
├── cli/            # Command-line interface
├── tests/          # Test files
├── utils/          # Utility functions and helpers
├── main.py         # Application entry point
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

For a more detailed explanation of the project structure and components, see [GettingStarted.md](GettingStarted.md).

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for more details.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Rate Limiting

The API implements rate limiting using slowapi and Redis to prevent abuse and ensure fair usage. The following rate limits are applied:

- **Login endpoint**: 5 requests per minute
- **Registration endpoint**: 10 requests per minute

Rate limit information is included in the response headers:

- `X-RateLimit-Limit`: The maximum number of requests allowed in the current time window
- `X-RateLimit-Remaining`: The number of requests remaining in the current time window
- `X-RateLimit-Reset`: The time at which the current rate limit window resets
