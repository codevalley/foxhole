import asyncio
from prompt_toolkit import PromptSession, HTML
from prompt_toolkit.styles import Style
from prompt_toolkit.patch_stdout import patch_stdout
from commands import handle_command
from ui import print_header, print_message
from websocket_client import WebSocketClient
from session_manager import SessionManager
from commands import exit_cli
from cli.config import Config


async def main() -> None:
    config = Config()
    session_manager = SessionManager(config)
    ws_client = WebSocketClient(config)
    prompt_session = PromptSession()

    print_header()

    while True:
        if not session_manager.current_user:
            await handle_load_session(session_manager, ws_client)
            await handle_auth(session_manager, ws_client, prompt_session)
        else:
            await handle_main_loop(session_manager, ws_client, prompt_session)


async def handle_load_session(
    session_manager: SessionManager, ws_client: WebSocketClient
) -> None:
    # Load saved session
    if session_manager.has_session():
        resume = (
            input("Do you want to resume your last session? (y/n): ").lower() == "y"
        )
        if resume:
            if await session_manager.load_session():
                await ws_client.connect(session_manager.current_user["access_token"])
                print_message("Logged in successfully", "success")
            else:
                print_message("Failed to resume session", "error")


async def handle_auth(
    session_manager: SessionManager,
    ws_client: WebSocketClient,
    prompt_session: PromptSession,
) -> None:
    while not session_manager.current_user:
        action = await prompt_session.prompt_async(
            "Choose action (login/register/exit): "
        )
        if action == "exit":
            await exit_cli(session_manager, ws_client)
            return
        elif action in ["login", "register"]:
            await handle_command(action, session_manager, ws_client, prompt_session)

            if session_manager.current_user and action == "register":
                save = (
                    input(
                        "Do you want to save this session for future logins? (y/n): "
                    ).lower()
                    == "y"
                )
                if save:
                    session_manager.save_session()
                    print_message("Session saved successfully.", "success")


async def handle_main_loop(
    session_manager: SessionManager,
    ws_client: WebSocketClient,
    prompt_session: PromptSession,
) -> None:
    style = Style.from_dict(
        {
            "username": "#ansiyellow",
            "at": "#ansigreen",
            "colon": "#ansigreen",
            "pound": "#ansigreen",
            "host": "#ansiblue",
            "command": "bold",
        }
    )

    with patch_stdout():
        while session_manager.current_user:
            try:
                prompt_html = HTML(
                    f"<username>{session_manager.get_name()}</username>"
                    f"<at>@</at><host>foxhole</host><pound>#</pound> "
                )
                user_input = await prompt_session.prompt_async(prompt_html, style=style)
                await handle_command(
                    user_input, session_manager, ws_client, prompt_session
                )
            except asyncio.CancelledError:
                break
            except Exception as e:
                print_message(f"An error occurred: {str(e)}", "error")
                break


if __name__ == "__main__":
    asyncio.run(main())
