"""Authentication commands: login and logout."""
import os
import secrets
import webbrowser

import requests
import typer
from dotenv import load_dotenv

from app.services import auth

load_dotenv()


def login(port: int = 8000, scopes: str = "read:user,user:email", no_browser: bool = False):
    """Sign in with GitHub using OAuth."""
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

    auth_url = auth.get_authorize_url(client_id, redirect_uri, state, scope_list)

    if no_browser:
        typer.secho("Open the following URL in your browser to authorize:", fg=typer.colors.GREEN)
        typer.echo(auth_url)
    else:
        typer.secho("Opening browser for GitHub sign-in...", fg=typer.colors.GREEN)
        webbrowser.open(auth_url)

    typer.secho("Waiting for response from GitHub...", fg=typer.colors.BLUE)
    try:
        token, user = auth.complete_oauth_flow(client_id, client_secret, state, redirect_uri, port=port, timeout=120)
    except RuntimeError as exc:
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
    auth.save_credentials(token, user)
    typer.secho(f"Credentials saved to {auth.CREDENTIALS_FILE}", fg=typer.colors.CYAN)


def logout():
    """Sign out and revoke GitHub access token."""
    load_dotenv()

    access_token = auth.load_credentials()
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
        auth.revoke_token(client_id, client_secret, access_token)
    except requests.HTTPError as exc:
        if exc.response.status_code == 404:
            typer.secho("Token not found or already revoked", fg=typer.colors.YELLOW)
        else:
            typer.secho(f"Failed to revoke token: {exc}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1)
    except Exception as exc:
        typer.secho(f"Failed to revoke token: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1)

    auth.clear_credentials()
    typer.secho("Successfully signed out", fg=typer.colors.GREEN)

