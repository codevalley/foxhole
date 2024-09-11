import requests
import websockets
import asyncio
import json
from colorama import init, Fore, Style
import os
import pickle

# Initialize colorama for cross-platform color support
init()

BASE_URL = "http://127.0.0.1:8000"
SESSION_FILE = "foxhole_session.pkl"


def print_verbose(message):
    print(f"{Fore.CYAN}[INFO] {message}{Style.RESET_ALL}")


def print_success(message):
    print(f"{Fore.GREEN}[SUCCESS] {message}{Style.RESET_ALL}")


def print_warning(message):
    print(f"{Fore.YELLOW}[WARNING] {message}{Style.RESET_ALL}")


def print_error(message):
    print(f"{Fore.RED}[ERROR] {message}{Style.RESET_ALL}")


def save_session(user_secret):
    with open(SESSION_FILE, 'wb') as f:
        pickle.dump(user_secret, f)
    print_success("Session saved successfully.")


def load_session():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, 'rb') as f:
            return pickle.load(f)
    return None


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


def get_access_token(user_secret):
    print_verbose(f"Requesting access token for user")
    response = requests.post(
        f"{BASE_URL}/auth/token", data={"user_secret": user_secret}
    )
    if response.status_code == 200:
        print_success("Access token obtained successfully")
        return response.json()["access_token"]
    else:
        print_error(f"Failed to get access token: {response.text}")
        return None


def get_user_info(access_token):
    print_verbose("Fetching user information")
    response = requests.get(
        f"{BASE_URL}/auth/users/me", headers={"Authorization": f"Bearer {access_token}"}
    )
    if response.status_code == 200:
        print_success("User information retrieved successfully")
        return response.json()
    else:
        print_error(f"Failed to get user information: {response.text}")
        return None


def update_user_profile(access_token, new_screen_name):
    print_verbose(f"Updating user profile with new screen name: {new_screen_name}")
    response = requests.put(
        f"{BASE_URL}/auth/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"screen_name": new_screen_name},
    )
    if response.status_code == 200:
        print_success("User profile updated successfully")
        return response.json()
    else:
        print_error(f"Failed to update user profile: {response.text}")
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


def list_files(access_token):
    print_verbose("Listing files")
    headers = {"Authorization": f"Bearer {access_token}"}
    response = requests.get(f"{BASE_URL}/files/", headers=headers)
    if response.status_code == 200:
        print_success("Files retrieved successfully")
        files = response.json()["files"]
        for file in files:
            print(f"- {file}")
    else:
        print_error(f"Failed to list files: {response.text}")


def get_file_url(access_token, object_name):
    print_verbose(f"Getting URL for file: {object_name}")
    response = requests.get(f"{BASE_URL}/files/file/{object_name}")
    if response.status_code == 200:
        print_success("File URL retrieved successfully")
        return response.json()["url"]
    else:
        print_error(f"Failed to get file URL: {response.text}")
        return None


async def connect_websocket(access_token):
    uri = f"ws://127.0.0.1:8000/ws?token={access_token}"
    print_verbose(f"Connecting to WebSocket at {uri}")
    async with websockets.connect(uri) as websocket:
        print_success("Connected to WebSocket. Type your messages (or 'quit' to exit):")

        async def receive_messages():
            while True:
                try:
                    message = await websocket.recv()
                    if message.startswith("ACK:"):
                        print(
                            f"\r{Fore.GREEN}Server acknowledged: {message[4:]}{Style.RESET_ALL}"
                        )
                    else:
                        try:
                            sender, content = message.split(": ", 1)
                            parsed_content = json.loads(content)
                            if parsed_content.get("type") == "personal":
                                print(f"\r{Fore.MAGENTA}{sender} [private]: {parsed_content['message']}{Style.RESET_ALL}")
                            else:
                                print(f"\r{Fore.YELLOW}{sender}: {parsed_content['message']}{Style.RESET_ALL}")
                        except (json.JSONDecodeError, ValueError):
                            print(f"\r{Fore.YELLOW}Received: {message}{Style.RESET_ALL}")
                    print(f"{Fore.GREEN}You: {Style.RESET_ALL}", end="", flush=True)
                except websockets.exceptions.ConnectionClosed:
                    print_error("\rWebSocket connection closed")
                    break
                except Exception as e:
                    print_error(f"\rError receiving message: {e}")
                    break

        receive_task = asyncio.create_task(receive_messages())

        try:
            while True:
                message = await asyncio.get_event_loop().run_in_executor(
                    None, input, f"{Fore.GREEN}You: {Style.RESET_ALL}"
                )
                if message.lower() == "quit":
                    break
                try:
                    await websocket.send(message)
                    print_verbose("Message sent. Waiting for acknowledgement...")
                except Exception as e:
                    print_error(f"Error sending message: {e}")
                    break
        finally:
            receive_task.cancel()
            try:
                await receive_task
            except asyncio.CancelledError:
                pass

    print_verbose("WebSocket connection closed")

def view_profile(access_token):
    print_verbose("Fetching user profile")
    response = requests.get(
        f"{BASE_URL}/auth/users/me", headers={"Authorization": f"Bearer {access_token}"}
    )
    if response.status_code == 200:
        user_info = response.json()
        print_success("User profile retrieved successfully")
        print(f"{Fore.CYAN}Profile Information:{Style.RESET_ALL}")
        print(f"User ID: {user_info['id']}")
        print(f"Screen Name: {user_info['screen_name']}")
        # Add any other profile information here
    else:
        print_error(f"Failed to retrieve user profile: {response.text}")


async def send_personal_message(access_token, recipient_id, message):
    uri = f"ws://127.0.0.1:8000/ws?token={access_token}"
    print_verbose(f"Connecting to WebSocket at {uri}")
    async with websockets.connect(uri) as websocket:
        print_success("Connected to WebSocket for personal message")
        try:
            personal_message = json.dumps({
                "type": "personal",
                "recipient_id": recipient_id,
                "message": message
            })
            await websocket.send(personal_message)
            print_verbose("Personal message sent. Waiting for acknowledgement...")
            
            ack = await websocket.recv()
            if ack.startswith("ACK:"):
                print_success(f"Server acknowledged: {ack[4:]}")
            else:
                print_warning(f"Unexpected response: {ack}")
        except Exception as e:
            print_error(f"Error sending personal message: {e}")


async def main():
    print(f"{Fore.MAGENTA}Welcome to the Foxhole CLI!{Style.RESET_ALL}")
    
    # Check for existing session
    saved_secret = load_session()
    if saved_secret:
        resume = input("Do you want to resume your last session? (y/n): ").lower() == 'y'
        if resume:
            user_secret = saved_secret
        else:
            user_secret = None
    else:
        user_secret = None

    if not user_secret:
        while True:
            choice = input("Choose an option:\n1. Sign up\n2. Login\n3. Exit\nYour choice: ")
            if choice == '1':
                screen_name = input("Enter your screen name: ")
                user_data = register_user(screen_name)
                if user_data:
                    user_secret = user_data['user_secret']
                    print_success(f"User registered with ID: {user_data['id']}")
                    print_success(f"Screen name: {user_data['screen_name']}")
                    print_warning(f"Your user secret is: {user_secret}")
                    save = input("Do you want to save this session for future logins? (y/n): ").lower() == 'y'
                    if save:
                        save_session(user_secret)
                break
            elif choice == '2':
                user_secret = input("Enter your user secret: ")
                break
            elif choice == '3':
                print("Goodbye!")
                return
            else:
                print_error("Invalid choice. Please try again.")

    if user_secret:
        access_token = get_access_token(user_secret)

        if access_token:
            print_success(f"Access Token obtained: {access_token[:10]}...")

            user_info = get_user_info(access_token)
            if user_info:
                print_success(
                    f"Logged in as: {user_info['screen_name']} (ID: {user_info['id']})"
                )

            while True:
                print(f"\n{Fore.MAGENTA}Foxhole CLI Menu:{Style.RESET_ALL}")
                print("1. Upload a file")
                print("2. List files")
                print("3. Get file URL")
                print("4. View profile")
                print("5. Update profile")
                print("6. Connect to WebSocket")
                print("7. Send personal message")
                print("8. Exit")
                choice = input("Enter your choice (1-8): ")

                if choice == "1":
                    upload_file(access_token)
                elif choice == "2":
                    list_files(access_token)
                elif choice == "3":
                    object_name = input("Enter the object name: ")
                    file_url = get_file_url(access_token, object_name)
                    if file_url:
                        print_success(f"File URL: {file_url}")
                elif choice == "4":
                    view_profile(access_token)
                elif choice == "5":
                    new_screen_name = input("Enter new screen name: ")
                    updated_profile = update_user_profile(access_token, new_screen_name)
                    if updated_profile:
                        print_success(f"Profile updated. New screen name: {updated_profile['screen_name']}")
                elif choice == "6":
                    await connect_websocket(access_token)
                elif choice == "7":
                    recipient_id = input("Enter recipient's user ID: ")
                    message = input("Enter your message: ")
                    await send_personal_message(access_token, recipient_id, message)
                elif choice == "8":
                    break
                else:
                    print_error("Invalid choice. Please try again.")

    print(f"{Fore.MAGENTA}Thank you for using Foxhole CLI!{Style.RESET_ALL}")

if __name__ == "__main__":
    asyncio.run(main())