import requests
import websockets
import asyncio
import json
from colorama import init, Fore, Style
import os
import pickle
import aioconsole


# Initialize colorama for cross-platform color support
init()

BASE_URL = "http://127.0.0.1:8000"
SESSION_FILE = "foxhole_session.pkl"

websocket_connection = None
exit_flag = False


def print_verbose(message):
    print(f"{Fore.CYAN}[INFO] {message}{Style.RESET_ALL}")


def print_success(message):
    print(f"{Fore.GREEN}[SUCCESS] {message}{Style.RESET_ALL}")


def print_warning(message):
    print(f"{Fore.YELLOW}[WARNING] {message}{Style.RESET_ALL}")


def print_error(message):
    print(f"{Fore.RED}[ERROR] {message}{Style.RESET_ALL}")


def save_session(user_secret):
    with open(SESSION_FILE, "wb") as f:
        pickle.dump(user_secret, f)
    print_success("Session saved successfully.")


def load_session():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, "rb") as f:
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
    print_verbose("Requesting access token for user")
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


async def connect_websocket(access_token):
    global websocket_connection
    uri = f"ws://127.0.0.1:8000/ws?token={access_token}"
    print_verbose(f"Connecting to WebSocket at {uri}")
    try:
        websocket_connection = await websockets.connect(uri)
        print_success("Connected to WebSocket")
        return websocket_connection
    except Exception as e:
        print_error(f"Failed to connect to WebSocket: {e}")
        return None


async def handle_incoming_messages():
    global websocket_connection, exit_flag
    while not exit_flag:
        try:
            if websocket_connection:
                message = await asyncio.wait_for(
                    websocket_connection.recv(), timeout=1.0
                )
                parsed_message = json.loads(message)
                sender = parsed_message.get("sender", {})
                content = parsed_message.get("content", "")
                message_type = parsed_message.get("type", "")

                if message_type == "broadcast":
                    print(
                        f"\n{Fore.YELLOW}{sender.get('screen_name', 'Unknown')}: {content}{Style.RESET_ALL}"
                    )
                elif message_type == "personal":
                    print(
                        f"\n{Fore.MAGENTA}[DM from {sender.get('screen_name', 'Unknown')}]: {content}{Style.RESET_ALL}"
                    )
                elif message_type == "system":
                    print(f"\n{Fore.CYAN}[SYSTEM]: {content}{Style.RESET_ALL}")
        except asyncio.TimeoutError:
            # This is normal, just continue the loop
            continue
        except websockets.exceptions.ConnectionClosed as e:
            if e.code == 1000:  # Normal closure
                print_verbose("WebSocket connection closed normally.")
            else:
                print_error(f"\nWebSocket connection closed unexpectedly: {e}")
            break
        except Exception as e:
            print_error(f"\nError receiving message: {e}")
            break

    print_verbose("Message handling stopped")


async def send_message(message_type, content, recipient_id=None):
    global websocket_connection
    if websocket_connection:
        message = {"type": message_type, "content": content}
        if recipient_id:
            message["recipient_id"] = recipient_id

        await websocket_connection.send(json.dumps(message))
        print_verbose("Message sent")
    else:
        print_error("WebSocket is not connected")


async def update_profile(access_token):
    new_screen_name = input("Enter new screen name: ")
    response = requests.put(
        f"{BASE_URL}/auth/users/me",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"screen_name": new_screen_name},
    )
    if response.status_code == 200:
        print_success(
            f"Profile updated. New screen name: {response.json()['screen_name']}"
        )
    else:
        print_error(f"Failed to update profile: {response.text}")


def get_updated_user_info(access_token):
    response = requests.get(
        f"{BASE_URL}/auth/users/me", headers={"Authorization": f"Bearer {access_token}"}
    )
    if response.status_code == 200:
        return response.json()
    else:
        print_error(f"Failed to get updated user information: {response.text}")
        return None


async def main_menu(user_info, access_token):
    global exit_flag
    while not exit_flag:
        try:
            print(f"\n{Fore.MAGENTA}Foxhole CLI Menu:{Style.RESET_ALL}")
            print("1. Send broadcast message")
            print("2. Send personal message")
            print("3. View profile")
            print("4. Edit profile")
            print("5. Exit")

            choice = await aioconsole.ainput(
                f"{Fore.GREEN}Enter your choice (1-5): {Style.RESET_ALL}"
            )

            if choice == "1":
                message = await aioconsole.ainput(
                    f"{Fore.GREEN}Enter your broadcast message: {Style.RESET_ALL}"
                )
                await send_message("broadcast", message)
            elif choice == "2":
                recipient_id = await aioconsole.ainput(
                    f"{Fore.GREEN}Enter recipient's user ID: {Style.RESET_ALL}"
                )
                message = await aioconsole.ainput(
                    f"{Fore.GREEN}Enter your personal message: {Style.RESET_ALL}"
                )
                await send_message("personal", message, recipient_id)
            elif choice == "3":
                updated_user_info = get_updated_user_info(access_token)
                if updated_user_info:
                    print(f"{Fore.CYAN}Profile Information:{Style.RESET_ALL}")
                    print(f"User ID: {updated_user_info['id']}")
                    print(f"Screen Name: {updated_user_info['screen_name']}")
                else:
                    print_error("Failed to retrieve updated user information")
            elif choice == "4":
                await update_profile(access_token)
            elif choice == "5":
                exit_flag = True
                print("Exiting...")
            else:
                print_error("Invalid choice. Please try again.")
        except Exception as e:
            print_error(f"An error occurred in the main menu: {e}")
            exit_flag = True


async def main():
    global websocket_connection, exit_flag
    print(f"{Fore.MAGENTA}Welcome to the Foxhole CLI!{Style.RESET_ALL}")

    saved_secret = load_session()
    if saved_secret:
        resume = (
            input("Do you want to resume your last session? (y/n): ").lower() == "y"
        )
        if resume:
            user_secret = saved_secret
        else:
            user_secret = None
    else:
        user_secret = None

    if not user_secret:
        while True:
            choice = input(
                "Choose an option:\n1. Sign up\n2. Login\n3. Exit\nYour choice: "
            )
            if choice == "1":
                screen_name = input("Enter your screen name: ")
                user_data = register_user(screen_name)
                if user_data:
                    user_secret = user_data["user_secret"]
                    print_success(f"User registered with ID: {user_data['id']}")
                    print_success(f"Screen name: {user_data['screen_name']}")
                    print_warning(f"Your user secret is: {user_secret}")
                    save = (
                        input(
                            "Do you want to save this session for future logins? (y/n): "
                        ).lower()
                        == "y"
                    )
                    if save:
                        save_session(user_secret)
                break
            elif choice == "2":
                user_secret = input("Enter your user secret: ")
                break
            elif choice == "3":
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

                websocket_connection = await connect_websocket(access_token)
                if websocket_connection:
                    message_handler = asyncio.create_task(handle_incoming_messages())
                    try:
                        await main_menu(user_info, access_token)
                    except Exception as e:
                        print_error(f"An error occurred in the main loop: {e}")
                    finally:
                        exit_flag = True
                        if websocket_connection and not websocket_connection.closed:
                            await websocket_connection.close(
                                code=1000, reason="Client disconnecting"
                            )
                        await message_handler

    print(f"{Fore.MAGENTA}Thank you for using Foxhole CLI!{Style.RESET_ALL}")


if __name__ == "__main__":
    asyncio.run(main())
