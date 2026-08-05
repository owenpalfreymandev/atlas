"""Atlas CLI application entry point."""
import typer
from app import commands

app = typer.Typer()


@app.command()
def hello(name: str):
    """Say hello to someone."""
    commands.hello(name)


@app.command()
def login(port: int = 8000, scopes: str = "read:user,user:email", no_browser: bool = False):
    """Sign in with GitHub using OAuth."""
    commands.login(port=port, scopes=scopes, no_browser=no_browser)


@app.command()
def logout():
    """Sign out and revoke GitHub access token."""
    commands.logout()


def main():
    """Run the Atlas CLI."""
    app()


if __name__ == "__main__":
    main()
