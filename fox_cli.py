import requests
import websockets
import asyncio
import json
from colorama import init, Fore, Style

# Initialize colorama for cross-platform color support
init()

BASE_URL = "http://127.0.0.1:8000"


def print_verbose(message):
    print(f"{Fore.CYAN}[INFO] {message}{Style.RESET_ALL}")


def print_success(message):
    print(f"{Fore.GREEN}[SUCCESS] {message}{Style.RESET_ALL}")


def print_error(message):
    print(f"{Fore.RED}[ERROR] {message}{Style.RESET_ALL}")


def register_user(screen_name):
    print_verbose(f"Registering user with screen name: {screen_name}")
    response = requests.post(
        f"{BASE_URL}/auth/register", json={"screen_name": screen_name}
    )
    if response.status_code == 200:
        print_success("User registered successfully")
        return response.json()
    else:
        print_error(f"Failed to register user: {response.text}")
        return None


def get_access_token(user_id):
    print_verbose(f"Requesting access token for user ID: {user_id}")
    response = requests.post(f"{BASE_URL}/auth/token", data={"user_id": user_id})
    if response.status_code == 200:
        print_success("Access token obtained successfully")
        return response.json()["access_token"]
    else:
        print_error(f"Failed to get access token: {response.text}")
        return None


def upload_file(access_token):
    file_path = input("Enter the path of the file to upload: ")
    print_verbose(f"Uploading file: {file_path}")
    with open(file_path, "rb") as file:
        files = {"file": file}
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.post(
            f"{BASE_URL}/files/upload", files=files, headers=headers
        )
    if response.status_code == 200:
        print_success("File uploaded successfully!")
        print(json.dumps(response.json(), indent=2))
    else:
        print_error(f"Failed to upload file: {response.text}")


async def connect_websocket(access_token):
    uri = f"ws://127.0.0.1:8000/ws?token={access_token}"
    print_verbose(f"Connecting to WebSocket at {uri}")
    async with websockets.connect(uri) as websocket:
        print_success("Connected to WebSocket. Type your messages (or 'quit' to exit):")

        async def receive_messages():
            while True:
                try:
                    message = await websocket.recv()
                    print(f"{Fore.YELLOW}Received: {message}{Style.RESET_ALL}")
                except websockets.exceptions.ConnectionClosed:
                    print_error("WebSocket connection closed")
                    break

        receive_task = asyncio.create_task(receive_messages())

        while True:
            message = input(f"{Fore.GREEN}You: {Style.RESET_ALL}")
            if message.lower() == "quit":
                break
            await websocket.send(message)
            print_verbose("Message sent. Waiting for acknowledgement...")

        receive_task.cancel()
    print_verbose("WebSocket connection closed")


async def main():
    print(f"{Fore.MAGENTA}Welcome to the Foxhole CLI!{Style.RESET_ALL}")
    screen_name = input("Enter your screen name: ")
    user_data = register_user(screen_name)

    if user_data:
        print_success(f"User registered with ID: {user_data['id']}")
        access_token = get_access_token(user_data["id"])

        if access_token:
            print_success(f"Access Token obtained: {access_token[:10]}...")

            upload_option = input("Do you want to upload a file? (y/n): ").lower()
            if upload_option == "y":
                upload_file(access_token)

            websocket_option = input(
                "Do you want to connect to WebSocket? (y/n): "
            ).lower()
            if websocket_option == "y":
                await connect_websocket(access_token)

    print(f"{Fore.MAGENTA}Thank you for using Foxhole CLI!{Style.RESET_ALL}")


if __name__ == "__main__":
    asyncio.run(main())
