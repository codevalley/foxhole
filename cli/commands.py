from ui import print_message, print_command_help
from websocket_client import WebSocketClient
from session_manager import SessionManager
from prompt_toolkit import PromptSession
import aiofiles
import aiohttp
import os


async def handle_command(
    command: str,
    session_manager: SessionManager,
    ws_client: WebSocketClient,
    prompt_session: PromptSession,
) -> None:
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
    elif cmd == "upload":
        await upload_file(session_manager, ws_client, prompt_session)
    elif cmd == "list":
        await list_files(session_manager, ws_client, prompt_session)
    elif cmd == "download":
        await download_file(session_manager, ws_client, prompt_session)
    else:
        print_message(f"Unknown command: {cmd}", "error")


async def login(
    session_manager: SessionManager,
    ws_client: WebSocketClient,
    prompt_session: PromptSession,
) -> None:
    user_secret = await prompt_session.prompt_async("Enter your user secret: ")
    success = await session_manager.login(user_secret)
    if success:
        await ws_client.connect(session_manager.current_user["access_token"])
        print_message("Logged in successfully", "success")
    else:
        print_message("Login failed", "error")


async def register(
    session_manager: SessionManager,
    ws_client: WebSocketClient,
    prompt_session: PromptSession,
) -> None:
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


async def logout(session_manager: SessionManager, ws_client: WebSocketClient) -> None:
    await ws_client.disconnect()
    session_manager.logout()
    print_message("Logged out successfully", "success")


async def shout(ws_client: WebSocketClient, message: str) -> None:
    await ws_client.send_message("broadcast", message)


async def dm(ws_client: WebSocketClient, recipient_id: str, message: str) -> None:
    await ws_client.send_message("personal", message, recipient_id)


def whoami(session_manager: SessionManager) -> None:
    user_info = session_manager.current_user
    if user_info:
        print_message(user_info["id"], "info", "User ID")
        print_message(user_info["screen_name"], "info", "Screen Name")
    else:
        print_message("You are not logged in", "error")


async def update_profile(
    session_manager: SessionManager, ws_client: WebSocketClient, field: str, value: str
) -> None:
    success = await session_manager.update_profile(field, value)
    if success:
        print_message(f"Updated {field} successfully", "success")
    else:
        print_message(f"Failed to update {field}", "error")


def show_help() -> None:
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
        ("upload", "Upload a file to the server"),
        ("list", "List files on the server"),
        ("download", "Download a file from the server"),
    ]
    print_message("Available commands:", "info")
    for cmd, desc in commands:
        print_command_help(cmd, desc)


async def exit_cli(session_manager: SessionManager, ws_client: WebSocketClient) -> None:
    await ws_client.disconnect()
    # session_manager.save_session()
    print_message("Goodbye!", "info")
    raise SystemExit


async def upload_file(
    session_manager: SessionManager,
    ws_client: WebSocketClient,
    prompt_session: PromptSession,
) -> None:
    if not session_manager.current_user:
        print_message("You must be logged in to upload files", "error")
        return

    file_path = await prompt_session.prompt_async(
        "Enter the path of the file to upload: "
    )
    if not os.path.exists(file_path):
        print_message("File not found", "error")
        return

    print_message(f"{file_path} is getting uploaded", "info")
    async with aiofiles.open(file_path, "rb") as file:
        file_name = os.path.basename(file_path)
        file_content = await file.read()
        print_message(f"{file_name} is {len(file_content)} bytes", "info")

    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {session_manager.current_user['access_token']}"
        }
        data = aiohttp.FormData()
        data.add_field("file", file_content, filename=file_name)

        async with session.post(
            f"{session_manager.config.API_URL}/files/upload", headers=headers, data=data
        ) as response:
            if response.status == 200:
                print_message("File uploaded successfully", "success")
            else:
                print_message(
                    f"Failed to upload file: {await response.text()}", "error"
                )


async def list_files(
    session_manager: SessionManager,
    ws_client: WebSocketClient,
    prompt_session: PromptSession,
) -> None:
    if not session_manager.current_user:
        print_message("You must be logged in to list files", "error")
        return

    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {session_manager.current_user['access_token']}"
        }
        async with session.get(
            f"{session_manager.config.API_URL}/files/", headers=headers
        ) as response:
            if response.status == 200:
                files = await response.json()
                if files["files"]:
                    print_message("Files:", "info")
                    for file in files["files"]:
                        print_message(file, "info")
                else:
                    print_message("No files found", "info")
            else:
                print_message(f"Failed to list files: {await response.text()}", "error")


async def download_file(
    session_manager: SessionManager,
    ws_client: WebSocketClient,
    prompt_session: PromptSession,
) -> None:
    if not session_manager.current_user:
        print_message("You must be logged in to download files", "error")
        return

    file_name = await prompt_session.prompt_async(
        "Enter the name of the file to download: "
    )

    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {session_manager.current_user['access_token']}"
        }
        async with session.get(
            f"{session_manager.config.API_URL}/files/file/{file_name}", headers=headers
        ) as response:
            if response.status == 200:
                file_url = await response.json()
                async with session.get(file_url["url"]) as file_response:
                    if file_response.status == 200:
                        content = await file_response.read()
                        async with aiofiles.open(file_name, "wb") as f:
                            await f.write(content)
                        print_message(
                            f"File {file_name} downloaded successfully", "success"
                        )
                    else:
                        print_message(
                            f"Failed to download file: {await file_response.text()}",
                            "error",
                        )
            else:
                print_message(
                    f"Failed to get file URL: {await response.text()}", "error"
                )
