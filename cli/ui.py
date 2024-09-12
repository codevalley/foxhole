from colorama import Fore, Style, init
import sys
import os

# Initialize colorama with strip=False to keep ANSI codes if the terminal supports it
init(strip=False)


def supports_color() -> bool:
    """
    Returns True if the running system's terminal supports color,
    and False otherwise.
    """
    plat = sys.platform
    supported_platform = plat != "Pocket PC" and (
        plat != "win32" or "ANSICON" in os.environ
    )
    is_a_tty = hasattr(sys.stdout, "isatty") and sys.stdout.isatty()
    return supported_platform and is_a_tty


use_color = supports_color()


def print_header() -> None:
    header = f"{'=' * 50}\n{'Foxhole CLI':^50}\n{'=' * 50}"  # noqa : E231
    if use_color:
        print(f"{Fore.CYAN}{header}{Style.RESET_ALL}")
    else:
        print(header)


def print_message(message: str, message_type: str = "info") -> None:
    color = Fore.WHITE
    if message_type == "error":
        color = Fore.RED
    elif message_type == "success":
        color = Fore.GREEN
    elif message_type == "info":
        color = Fore.CYAN

    if use_color:
        print(f"{color}{message}{Style.RESET_ALL}")
    else:
        print(message)
