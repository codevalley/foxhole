# Foxhole CLI

Foxhole CLI is a comprehensive command-line interface for interacting with the Foxhole Backend API. It provides a user-friendly way to manage your account, send messages, and interact with other users in the Foxhole system.

## Features

- User authentication (login and registration)
- Session management (save and resume sessions)
- Send broadcast messages to all users
- Send direct messages to specific users
- View and update user profile information
- Real-time message reception using WebSocket connection
- File upload and download functionality
- List files stored on the server

## Installation

See the [GettingStarted.md](GettingStarted.md) file for detailed installation and setup instructions.

## Usage

After installation, you can run the Foxhole CLI by executing:

```
python -m cli.py
```

### Available Commands

- `login`: Log in to your account
- `register`: Create a new account
- `logout`: Log out of your account
- `shout <message>`: Send a message to all users
- `dm <user_id> <message>`: Send a direct message to a user
- `whoami`: Display your user information
- `update <field> <value>`: Update your profile information
- `upload`: Upload a file to the server
- `list`: List files on the server
- `download`: Download a file from the server
- `help`: Show the help message
- `exit`: Exit the application

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License. See the [LICENSE](../LICENSE) file for details.
