# Getting Started with Foxhole CLI

This guide will help you set up and run the Foxhole CLI on your local machine.

## Prerequisites

- Python 3.7 or higher
- pip (Python package installer)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-repo/foxhole.git
   cd foxhole
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On macOS and Linux:
     ```
     source venv/bin/activate
     ```

4. Install the required packages:
   ```
   pip install -r cli/requirements.txt
   ```

## Configuration

1. Open `cli/config.py` and update the `API_URL` and `WEBSOCKET_HOST` if your Foxhole Backend API is running on a different host or port.

## Running the CLI

1. Ensure your Foxhole Backend API is running.

2. From the root directory of the project, run:
   ```
   python -m cli.main
   ```

3. You should see the Foxhole CLI welcome message. Use the `help` command to see available commands.

## Basic Usage

1. Register a new account using the `register` command.
2. Log in using the `login` command with your user secret.
3. Use `shout` to send a message to all users.
4. Use `dm` to send a direct message to a specific user.
5. Use `whoami` to view your profile information.
6. Use `update` to modify your profile information.
7. Use `logout` to log out of your account.
8. Use `exit` to close the CLI.

Enjoy using Foxhole CLI!