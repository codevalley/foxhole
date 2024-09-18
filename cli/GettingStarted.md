# Getting Started with Foxhole CLI

This guide will help you set up and run the Foxhole CLI on your local machine.

## Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

## Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/your-repo/foxhole.git
   cd foxhole
   ```

2. Create a virtual environment:

   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - On Windows:

     ```bash
     venv\Scripts\activate
     ```

   - On macOS and Linux:

     ```bash
     source venv/bin/activate
     ```

4. Install the required packages:

   ```bash
   pip install -r cli/requirements.txt
   ```

## Configuration

1. Open `cli/config.py` and update the `API_URL` and `WEBSOCKET_HOST` if your Foxhole Backend API is running on a different host or port.

## Running the CLI

1. Ensure your Foxhole Backend API is running.

2. From the root directory of the project, run:

   ```bash
   python -m main.py
   ```

3. You should see the Foxhole CLI welcome message.
the `help` command to see available commands.

## Basic Usage

1. **Register a new account**: Choose the "Sign up" option and enter a screen name.
2. **Login**: Use the "Login" option and enter your user secret.
3. **Send a broadcast message**: Use the "Send broadcast message" option.
4. **Send a direct message**: Use the "Send personal message" option and provide the recipient's user ID.
5. **View your profile**: Select the "View profile" option.
6. **Update your profile**: Choose the "Edit profile" option to update your screen name.
7. **Upload a file**: Use the "Upload" option and provide the file path.
8. **List files**: Select the "List" option to see files on the server.
9. **Download a file**: Use the "Download" option and specify the file name.
10. **Logout**: Choose the "Exit" option to log out and close the CLI.

## Session Management

The CLI supports saving and resuming sessions. When you log in or register, you'll be asked if you want to save the session. On subsequent runs, you can choose to resume your last session.

## Troubleshooting

- If you encounter connection issues, ensure that the Foxhole Backend API is running and that the `API_URL` and `WEBSOCKET_HOST` in `config.py` are correct.
- For any other issues, check the error messages displayed in the CLI for guidance.

Enjoy using Foxhole CLI!
