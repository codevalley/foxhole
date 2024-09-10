# FastAPI Backend Scaffold

![CI](https://github.com/codevalley/foxhole/workflows/CI/badge.svg)
[![codecov](https://codecov.io/gh/codevalley/foxhole/branch/main/graph/badge.svg)](https://codecov.io/gh/codevalley/foxhole)

This project is a scaffold for a FastAPI backend application with WebSocket support, SQLite database, Redis caching, and MinIO object storage. It's designed to provide a robust starting point for building scalable and maintainable API services.

## Key Features

- FastAPI web framework for high-performance API development
- WebSocket support for real-time communication
- Asynchronous SQLite database with SQLAlchemy ORM
- Redis caching for improved performance
- MinIO integration for object storage
- Secure authentication using user_secret
- Structured logging
- Global error handling
- Docker and docker-compose setup for easy deployment
- Comprehensive testing framework with pytest

## Getting Started

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

## Authentication

This project uses a unique authentication approach:

1. Users register with a screen name.
2. The system generates a `user_secret` for each user.
3. Users authenticate using their `user_secret` instead of a traditional username/password combination.

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

- For local development, use `uvicorn main:app --reload`
- For deployment, utilize the provided Dockerfile and docker-compose.yml
- Customize the deployment process using Kamal (configuration to be added)

## Testing

Run tests using pytest:
```bash
pytest
```

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for more details.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
