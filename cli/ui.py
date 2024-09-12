from prompt_toolkit import print_formatted_text
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.styles import Style
from typing import Optional

style = Style.from_dict(
    {
        "header": "#00ffff bold",
        "info": "#00ffff",
        "success": "#00ff00",
        "error": "#ff0000",
        "prefix": "#00ffff",
        "suffix": "#ffffff",
    }
)


def print_header() -> None:
    header = f"{'=' * 50}\n{'Foxhole CLI':^50}\n{'=' * 50}"  # noqa E231
    print_formatted_text(FormattedText([("class:header", header)]), style=style)


def print_message(
    message: str, message_type: str = "info", prefix: Optional[str] = None
) -> None:
    if prefix:
        formatted_text = [
            (f"class:{message_type}", f"{prefix}: "),
            ("class:suffix", message),
        ]
    else:
        formatted_text = [(f"class:{message_type}", message)]

    print_formatted_text(FormattedText(formatted_text), style=style)


def print_command_help(command: str, description: str) -> None:
    formatted_text = [
        ("class:info", f"  {command:<30}"),  # noqa E231
        ("class:suffix", description),
    ]  # noqa E231
    print_formatted_text(FormattedText(formatted_text), style=style)
