from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.columns import Columns

from app.ui.avatar import get_profile_picture

console = Console()


def display_user(user: dict):
    """Display a GitHub profile with avatar."""

    title = user.get("name") or user["login"]
    subtitle = f"@{user['login']}"

    profile = Table(show_header=False, box=None, pad_edge=False)
    profile.add_column("Field", style="cyan")
    profile.add_column("Value")

    profile.add_row("Repositories", str(user["public_repos"]))
    profile.add_row("Followers", str(user["followers"]))
    profile.add_row("Following", str(user["following"]))
    profile.add_row("Location", user.get("location") or "—")
    profile.add_row("Company", user.get("company") or "—")
    profile.add_row("Joined", user["created_at"][:10])

    profile_panel = Panel(
        profile,
        title=f"[bold]{title}[/bold]",
        subtitle=subtitle,
        expand=False,
    )

    avatar_panel = Panel(
        get_profile_picture(user),
        # Pixels does not report its natural width to Rich, so constrain this
        # panel to the 28-column thumbnail plus its border and horizontal padding.
        width=32,
        padding=(0, 1),
        expand=False,
    )

    console.print(
        Columns(
            [
                profile_panel,
                avatar_panel,
            ],
            expand=False,
            equal=False,
        )
    )
