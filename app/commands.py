import os
import secrets
import threading
import socketserver
import webbrowser
from http.server import BaseHTTPRequestHandler
from urllib import parse as urlparse

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
def signin(port: int = 8000, scopes: str = "read:user,user:email", no_browser: bool = False):
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

    # Lightweight HTTP server to receive the OAuth callback
    result = {}
    done = threading.Event()

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urlparse.urlparse(self.path)
            if parsed.path != "/callback":
                self.send_response(404)
                self.end_headers()
                return
            qs = urlparse.parse_qs(parsed.query)
            code = qs.get("code", [None])[0]
            recv_state = qs.get("state", [None])[0]
            if recv_state != state:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Invalid state parameter")
                result["error"] = "invalid_state"
                done.set()
                return
            result["code"] = code
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(
                b"<html><body><h1>Authentication complete</h1><p>You can close this window and return to the CLI.</p></body></html>"
            )
            done.set()

        def log_message(self, format, *args):
            # silence access logs
            return

    # Start server in background thread
    server = socketserver.TCPServer(("", port), CallbackHandler)
    server.allow_reuse_address = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    if no_browser:
        typer.secho("Open the following URL in your browser to authorize:", fg=typer.colors.GREEN)
        typer.echo(auth_url)
    else:
        typer.secho("Opening browser for GitHub sign-in...", fg=typer.colors.GREEN)
        webbrowser.open(auth_url)

    typer.secho("Waiting for response from GitHub...", fg=typer.colors.BLUE)
    if not done.wait(120):
        server.shutdown()
        server.server_close()
        raise typer.Exit(code=2)

    # teardown server
    server.shutdown()
    server.server_close()
    thread.join(timeout=1)

    if "error" in result:
        typer.secho("OAuth failed: invalid state", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=3)

    code = result.get("code")
    if not code:
        typer.secho("No code received", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=4)

    try:
        token = oauth.exchange_code_for_token(client_id, client_secret, code, redirect_uri)
    except Exception as exc:
        typer.secho(f"Failed to obtain access token: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=5)

    if not token:
        typer.secho("Failed to obtain access token", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=5)

    user = oauth.get_user(token)
    typer.secho(f"Signed in as: {user.get('login')}", fg=typer.colors.GREEN)
    typer.echo(f"access_token={token}")
