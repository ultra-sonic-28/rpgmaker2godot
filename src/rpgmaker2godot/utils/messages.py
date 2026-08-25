"""User-facing console messages for the CLI."""

from importlib.metadata import PackageNotFoundError
from importlib.metadata import metadata

from rich.console import Console
from rich.panel import Panel

_PACKAGE_NAME = "rpgmaker2godot"


def display_title(
    message: str,
) -> None:
    """Display a title inside a panel with a blue background.

    The panel is rendered with a bright white text on a blue
    background and a blue border, expanded to the full console
    width.

    Args:
        message: The message to display inside the panel.
    """
    console = Console()

    title = Panel(
        message,
        style="bright_white on blue",  # White text on blue background
        title="",  # Panel title
        border_style="blue",  # Blue border
        expand=True,  # Expand to full width
    )

    console.print("")
    console.print(title)
    console.print("")


def display_program_banner() -> None:
    """Display the program name, version and description as a banner.

    The values are read from the installed package metadata so that
    they always stay in sync with pyproject.toml.
    """

    try:
        package_metadata = metadata(_PACKAGE_NAME)

        name = package_metadata["Name"]
        version = package_metadata["Version"]
        summary = package_metadata["Summary"] or ""
    except PackageNotFoundError:
        # Running from an uninstalled source tree.
        name = _PACKAGE_NAME
        version = "unknown"
        summary = ""

    display_title(f"{name} v{version}\n{summary}")