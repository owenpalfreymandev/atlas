import typer

from app.services import auth

app = typer.Typer()

@app.command()
def login():
    """Login to GitHub using the device flow."""
    auth.login()

@app.command()
def logout():
    """Logout of GitHub."""
    auth.logout()