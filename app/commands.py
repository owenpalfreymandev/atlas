import os
import secrets
import threading
import socketserver
import webbrowser
from http.server import BaseHTTPRequestHandler
from urllib import parse as urlparse
import requests
import typer
from dotenv import load_dotenv
from app.services import oauth

# Load environment from .env if present
load_dotenv()

app = typer.Typer()

@app.command()
def hello(name: str):
    typer.echo(f"Hello, {name}")


@app.command()
def login(port: int = 8000, scopes: str = "read:user,user:email", no_browser: bool = False):
    """Sign in with GitHub using OAuth.

    Reads GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET from the environment or a .env file.
    """
    client_id = os.environ.get("GITHUB_CLIENT_ID")
    client_secret = os.environ.get("GITHUB_CLIENT_SECRET")
    if not client_id or not client_secret:
        typer.secho(
            "GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET must be set in environment or .env",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    state = secrets.token_urlsafe(16)
    redirect_uri = f"http://localhost:{port}/callback"
    scope_list = [s.strip() for s in scopes.split(",") if s.strip()]

    auth_url = oauth.get_authorize_url(client_id, redirect_uri, state, scope_list)

    if no_browser:
        typer.secho("Open the following URL in your browser to authorize:", fg=typer.colors.GREEN)
        typer.echo(auth_url)
    else:
        typer.secho("Opening browser for GitHub sign-in...", fg=typer.colors.GREEN)
        webbrowser.open(auth_url)

    typer.secho("Waiting for response from GitHub...", fg=typer.colors.BLUE)
    try:
        token, user = oauth.complete_oauth_flow(client_id, client_secret, state, redirect_uri, port=port, timeout=120)
    except RuntimeError as exc:
        # Map service errors to exit codes similar to previous behavior
        msg = str(exc)
        if "timeout" in msg:
            raise typer.Exit(code=2)
        if "invalid_state" in msg:
            typer.secho("OAuth failed: invalid state", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=3)
        if "no_code_received" in msg:
            typer.secho("No code received", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=4)
        if "failed_to_obtain_access_token" in msg:
            typer.secho("Failed to obtain access token", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=5)
        typer.secho(f"Failed to obtain access token: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=5)
    except Exception as exc:
        typer.secho(f"Failed to obtain access token: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=5)

    typer.secho(f"Signed in as: {user.get('login')}", fg=typer.colors.GREEN)
    oauth.save_credentials(token, user)
    typer.secho(f"Credentials saved to {oauth.CREDENTIALS_FILE}", fg=typer.colors.CYAN)


@app.command()
def logout():
    """Sign out by revoking the GitHub access token.

    Reads stored credentials from ~/.atlas/credentials.json and requires
    GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET from the environment or a .env file.
    """
    access_token = oauth.load_credentials()
    if not access_token:
        typer.secho("Not signed in. No credentials found.", fg=typer.colors.YELLOW)
        raise typer.Exit(code=0)

    client_id = os.environ.get("GITHUB_CLIENT_ID")
    client_secret = os.environ.get("GITHUB_CLIENT_SECRET")
    if not client_id or not client_secret:
        typer.secho(
            "GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET must be set in environment or .env",
            fg=typer.colors.RED,
            err=True,
        )
        raise typer.Exit(code=1)

    try:
        oauth.revoke_token(client_id, client_secret, access_token)
    except requests.HTTPError as exc:
        if exc.response.status_code == 404:
            typer.secho("Token not found or already revoked", fg=typer.colors.YELLOW)
        else:
            typer.secho(f"Failed to revoke token: {exc}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)
    except Exception as exc:
        typer.secho(f"Failed to revoke token: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    oauth.clear_credentials()
    typer.secho("Successfully signed out", fg=typer.colors.GREEN)
