from ui import print_message
from websocket_client import WebSocketClient
from session_manager import SessionManager


async def handle_command(
    command, session_manager: SessionManager, ws_client: WebSocketClient, prompt_session
):
    parts = command.split()
    cmd = parts[0].lower()
    args = parts[1:]

    if cmd == "login":
        await login(session_manager, ws_client, prompt_session)
    elif cmd == "register":
        await register(session_manager, ws_client, prompt_session)
    elif cmd == "logout":
        await logout(session_manager, ws_client)
    elif cmd == "shout":
        await shout(ws_client, " ".join(args))
    elif cmd == "dm":
        if len(args) < 2:
            print_message("Usage: dm <user_id> <message>", "error")
        else:
            await dm(ws_client, args[0], " ".join(args[1:]))
    elif cmd == "whoami":
        whoami(session_manager)
    elif cmd == "update":
        if len(args) < 2:
            print_message("Usage: update <field> <value>", "error")
        else:
            await update_profile(
                session_manager, ws_client, args[0], " ".join(args[1:])
            )
    elif cmd == "help":
        show_help()
    elif cmd == "exit":
        await exit_cli(session_manager, ws_client)
    else:
        print_message(f"Unknown command: {cmd}", "error")


async def login(session_manager, ws_client, prompt_session):
    user_secret = await prompt_session.prompt_async("Enter your user secret: ")
    success = await session_manager.login(user_secret)
    if success:
        await ws_client.connect(session_manager.current_user["access_token"])
        print_message("Logged in successfully", "success")
    else:
        print_message("Login failed", "error")


async def register(session_manager, ws_client, prompt_session):
    screen_name = await prompt_session.prompt_async("Enter your screen name: ")
    success, user_info = await session_manager.register(screen_name)
    if success:
        print_message(
            f"Registered successfully. Your user secret is: {user_info['user_secret']}",
            "success",
        )
        await ws_client.connect(user_info["access_token"])
    else:
        print_message("Registration failed", "error")


async def logout(session_manager, ws_client):
    await ws_client.disconnect()
    session_manager.logout()
    print_message("Logged out successfully", "success")


async def shout(ws_client, message):
    await ws_client.send_message("broadcast", message)


async def dm(ws_client, recipient_id, message):
    await ws_client.send_message("personal", message, recipient_id)


def whoami(session_manager):
    user_info = session_manager.current_user
    if user_info:
        print_message(f"User ID: {user_info['id']}", "info")
        print_message(f"Screen Name: {user_info['screen_name']}", "info")
    else:
        print_message("You are not logged in", "error")


async def update_profile(session_manager, ws_client, field, value):
    success = await session_manager.update_profile(field, value)
    if success:
        print_message(f"Updated {field} successfully", "success")
    else:
        print_message(f"Failed to update {field}", "error")


def show_help():
    commands = [
        ("login", "Log in to your account"),
        ("register", "Create a new account"),
        ("logout", "Log out of your account"),
        ("shout <message>", "Send a message to all users"),
        ("dm <user_id> <message>", "Send a direct message to a user"),
        ("whoami", "Display your user information"),
        ("update <field> <value>", "Update your profile information"),
        ("help", "Show this help message"),
        ("exit", "Exit the application"),
    ]
    print_message("Available commands:", "info")
    for cmd, desc in commands:
        print_message(f"  {cmd:<30} {desc}", "info")


async def exit_cli(session_manager, ws_client):
    await ws_client.disconnect()
    # session_manager.save_session()
    print_message("Goodbye!", "info")
    raise SystemExit
