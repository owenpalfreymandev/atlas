from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def display_user(user: dict):
    """Display a basic GitHub profile."""

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

    console.print(
        Panel(
            profile,
            title=f"[bold]{title}[/bold]",
            subtitle=subtitle,
            expand=False,
        )
    )