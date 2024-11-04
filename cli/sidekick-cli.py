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
from typing import Optional, Any, Dict, cast
from rich.table import Table


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
) -> Optional[Dict[str, Any]]:
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {session_manager.current_user['access_token']}"
        }
        data = {"user_input": user_input, "thread_id": thread_id}
        with console.status("[bold green]Thinking...", spinner="dots"):
            async with session.post(
                f"{config.API_URL}/api/v1/sidekick/ask", headers=headers, json=data
            ) as response:
                if response.status == 200:
                    return cast(Dict[str, Any], await response.json())
                else:
                    console.print(
                        f"[bold red]Error:[/bold red] {await response.text()}"
                    )
                    return None


async def fetch_tasks(session_manager: SessionManager) -> None:
    """Fetch and display tasks from the API"""
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {session_manager.current_user['access_token']}"
        }
        async with session.get(
            f"{config.API_URL}/api/v1/sidekick/tasks", headers=headers
        ) as response:
            if response.status == 200:
                data = await response.json()
                tasks = data["items"]

                # Create a table to display tasks
                table = Table(title="Tasks")
                table.add_column("ID", style="cyan")
                table.add_column("Type", style="magenta")
                table.add_column("Description", style="green")
                table.add_column("Status", style="yellow")
                table.add_column("Priority", style="red")

                for task in tasks:
                    table.add_row(
                        task["task_id"],
                        task["type"],
                        task["description"],
                        task["status"],
                        task["priority"],
                    )

                console.print(table)
            else:
                console.print(f"[bold red]Error:[/bold red] {await response.text()}")


async def fetch_people(session_manager: SessionManager) -> None:
    """Fetch and display people from the API"""
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {session_manager.current_user['access_token']}"
        }
        async with session.get(
            f"{config.API_URL}/api/v1/sidekick/people", headers=headers
        ) as response:
            if response.status == 200:
                data = await response.json()
                people = data["items"]

                # Create a table to display people
                table = Table(title="People")
                table.add_column("ID", style="cyan")
                table.add_column("Name", style="magenta")
                table.add_column("Designation", style="green")
                table.add_column("Relation", style="yellow")
                table.add_column("Importance", style="red")

                for person in people:
                    table.add_row(
                        person["person_id"],
                        person["name"],
                        person["designation"],
                        person["relation_type"],
                        person["importance"],
                    )

                console.print(table)
            else:
                console.print(f"[bold red]Error:[/bold red] {await response.text()}")


async def fetch_topics(session_manager: SessionManager) -> None:
    """Fetch and display topics from the API"""
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {session_manager.current_user['access_token']}"
        }
        async with session.get(
            f"{config.API_URL}/api/v1/sidekick/topics", headers=headers
        ) as response:
            if response.status == 200:
                data = await response.json()
                topics = data["items"]

                # Create a table to display topics
                table = Table(title="Topics")
                table.add_column("ID", style="cyan")
                table.add_column("Name", style="magenta")
                table.add_column("Description", style="green")

                for topic in topics:
                    table.add_row(
                        topic["topic_id"], topic["name"], topic["description"]
                    )

                console.print(table)
            else:
                console.print(f"[bold red]Error:[/bold red] {await response.text()}")


async def fetch_notes(session_manager: SessionManager) -> None:
    """Fetch and display notes from the API"""
    async with aiohttp.ClientSession() as session:
        headers = {
            "Authorization": f"Bearer {session_manager.current_user['access_token']}"
        }
        async with session.get(
            f"{config.API_URL}/api/v1/sidekick/notes", headers=headers
        ) as response:
            if response.status == 200:
                data = await response.json()
                notes = data["items"]

                # Create a table to display notes
                table = Table(title="Notes")
                table.add_column("ID", style="cyan")
                table.add_column("Content", style="green")
                table.add_column("Created", style="yellow")

                for note in notes:
                    table.add_row(note["note_id"], note["content"], note["created_at"])

                console.print(table)
            else:
                console.print(f"[bold red]Error:[/bold red] {await response.text()}")


async def handle_command(command: str, session_manager: SessionManager) -> bool:
    """Handle CLI commands starting with /"""
    command = command.lower()

    if command == "/tasks":
        await fetch_tasks(session_manager)
        return True
    elif command == "/people":
        await fetch_people(session_manager)
        return True
    elif command == "/topics":
        await fetch_topics(session_manager)
        return True
    elif command == "/notes":
        await fetch_notes(session_manager)
        return True
    elif command == "/help":
        console.print(
            Panel(
                "Available commands:\n"
                "/tasks - List all tasks\n"
                "/people - List all people\n"
                "/topics - List all topics\n"
                "/notes - List all notes\n"
                "/help - Show this help message",
                title="Help",
                border_style="blue",
            )
        )
        return True

    return False


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
            + Text(
                "\nYour personal executive assistant \n",
                style="italic",
            ),
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

        # Handle commands
        if user_input.startswith("/"):
            command_handled = await handle_command(user_input, session_manager)
            if command_handled:
                continue

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
                    response_parts.append("Updates:\n" + "\n".join(entity_updates))

            # Add main response
            response_parts.append(response["response"])

            # Add thread completion message if applicable
            if response["is_thread_complete"]:
                response_parts.append("Thread finished! Starting a new conversation.")

            # Add new prompt if available
            if response.get("new_prompt"):
                response_parts.append(f"New suggested prompt: {response['new_prompt']}")

            # Add token usage information
            token_usage = response["token_usage"]
            response_parts.append(
                f"Token usage: {token_usage['prompt_tokens']} (prompt) + "
                f"{token_usage['completion_tokens']} (completion) = "
                f"{token_usage['total_tokens']} (total)"
            )

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
