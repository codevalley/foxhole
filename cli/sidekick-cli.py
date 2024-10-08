import asyncio
from prompt_toolkit import PromptSession
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.text import Text
from session_manager import SessionManager
from cli_config import CliConfig
import aiohttp
from typing import Optional, Any

config = CliConfig()
console = Console()


async def login_or_register(session_manager: SessionManager) -> bool:
    while not session_manager.current_user:
        action = input("Choose action (login/register): ")
        if action == "login":
            user_secret = input("Enter your user secret: ")
            success = await session_manager.login(user_secret)
        elif action == "register":
            screen_name = input("Enter your screen name: ")
            success, user_info = await session_manager.register(screen_name)
            if success:
                print(f"Your user secret is: {user_info['user_secret']}")
                success = await session_manager.login(user_info["user_secret"])
        else:
            print("Invalid action. Please choose 'login' or 'register'.")
            continue

        if success:
            print("Logged in successfully!")
            return True
        else:
            print("Login failed. Please try again.")
    return False


async def call_sidekick_api(
    session_manager: SessionManager, user_input: str, thread_id: Optional[str] = None
) -> Optional[Any]:
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {session_manager.current_user['access_token']}"
        }
        data = {"user_input": user_input, "thread_id": thread_id}
        with console.status("[bold green]Thinking...", spinner="dots"):
            async with session.post(
                f"{config.API_URL}/sidekick", headers=headers, json=data
            ) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    console.print(
                        f"[bold red]Error:[/bold red] {await response.text()}"
                    )
                    return None


async def main() -> None:
    session_manager = SessionManager(config)
    if session_manager.has_session():
        if await session_manager.load_session():
            print("Session restored successfully!")
        else:
            print("Failed to restore session. Please log in again.")
            if not await login_or_register(session_manager):
                return
    else:
        if not await login_or_register(session_manager):
            return

    console.print(
        Panel.fit(
            Text("Welcome to Sidekick!", style="bold magenta")
            + Text("\nYour personal executive assistant", style="italic"),
            title="Sidekick",
            subtitle="Type 'exit' to quit",
        )
    )

    # Fetch initial task summary
    console.print("Fetching task summary...")
    summary_response = await call_sidekick_api(
        session_manager,
        "Provide an overview of all tasks, people, and knowledge entries.",
    )
    if summary_response:
        markdown_summary = Markdown(summary_response["response"])
        console.print(
            Panel(markdown_summary, title="Task Summary", border_style="blue")
        )

    style = Style.from_dict(
        {
            "prompt": "ansicyan bold",
        }
    )

    session: PromptSession = PromptSession(style=style)
    thread_id: Optional[str] = None

    while True:
        thread_indicator = f"[{thread_id}] " if thread_id else ""
        user_input = await session.prompt_async(f"{thread_indicator}You: ")

        if user_input.lower() == "exit":
            break

        response = await call_sidekick_api(session_manager, user_input, thread_id)

        if response:
            # Create a list to store all the parts of the response
            response_parts = []

            # Add updated entities information
            if response["updated_entities"]:
                entity_updates = []
                for entity, count in response["updated_entities"].items():
                    if count > 0:
                        entity_updates.append(f"* {count} new {entity} added")
                if entity_updates:
                    response_parts.append("\n".join(entity_updates))

            # Add followup text
            response_parts.append(response["response"])

            # Add thread completion message if applicable
            if response["is_thread_complete"]:
                response_parts.append("Thread finished!")

            # Add new prompt if available
            if response.get("new_prompt"):
                response_parts.append(response["new_prompt"])

            # Join all parts with newlines and create a Markdown object
            markdown_response = Markdown("\n\n".join(response_parts))
            console.print(
                Panel(markdown_response, title="Sidekick", border_style="blue")
            )

            thread_id = response["thread_id"]

    session_manager.save_session()
    print("Session saved. Goodbye!")


if __name__ == "__main__":
    asyncio.run(main())
