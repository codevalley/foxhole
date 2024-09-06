# FastAPI Backend Scaffold

![CI](https://github.com/codevalley/foxhole/workflows/CI/badge.svg)
[![codecov](https://codecov.io/gh/codevalley/foxhole/branch/main/graph/badge.svg)](https://codecov.io/gh/codevalley/foxhole)

This project is a scaffold for a FastAPI backend application with WebSocket support, SQLite database, Redis caching, and MinIO object storage. It's designed to provide a robust starting point for building scalable and maintainable API services.

## Requirements

- Python 3.12 or higher
- pip (Python package manager)

## Getting Started

1. Clone the repository:
   ```bash
   git clone https://github.com/codevalley/foxhole.git
   cd foxhole
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   uvicorn main:app --reload
   ```

5. Open your browser and navigate to `http://localhost:8000/docs` to see the API documentation.

## Features

- FastAPI web framework for high-performance API development
- WebSocket support for real-time communication
- Asynchronous SQLite database with SQLAlchemy ORM
- Redis caching for improved performance
- MinIO integration for object storage
- JWT-based authentication
- Structured logging
- Global error handling
- Docker and docker-compose setup for easy deployment
- Comprehensive testing framework with pytest

## Project Structure

For a detailed explanation of the project structure and components, please refer to the [GettingStarted.md](GettingStarted.md) file.

## Development

- For local development, use `uvicorn main:app --reload`
- For deployment, utilize the provided Dockerfile and docker-compose.yml
- Customize the deployment process using Kamal (configuration to be added)

## Deployment

[Include instructions for deploying the application using Docker and Kamal]

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
