"""Authentication: OAuth flow, token management, and credentials storage."""
import json
import threading
import socketserver
from http.server import BaseHTTPRequestHandler
from pathlib import Path
from typing import Iterable, Optional
from urllib import parse as urlparse
from urllib.parse import urlencode

import requests

from app.config import (
    GITHUB_AUTHORIZE,
    GITHUB_ACCESS_TOKEN,
    GITHUB_API_USER,
    GITHUB_REVOKE_TOKEN,
    CREDENTIALS_DIR,
    CREDENTIALS_FILE,
)

__all__ = [
    "get_authorize_url",
    "exchange_code_for_token",
    "get_user",
    "revoke_token",
    "complete_oauth_flow",
    "save_credentials",
    "load_credentials",
    "clear_credentials",
    "is_logged_in",
    "CREDENTIALS_FILE",
]


# OAuth flow functions
def get_authorize_url(client_id: str, redirect_uri: str, state: str, scopes: Iterable[str]) -> str:
    """Build GitHub authorization URL."""
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "scope": " ".join(scopes),
    }
    return f"{GITHUB_AUTHORIZE}?{urlencode(params)}"


def exchange_code_for_token(client_id: str, client_secret: str, code: str, redirect_uri: str) -> Optional[str]:
    """Exchange authorization code for access token."""
    headers = {"Accept": "application/json"}
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri,
    }
    resp = requests.post(GITHUB_ACCESS_TOKEN, data=payload, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.json().get("access_token")


def get_user(access_token: str) -> dict:
    """Fetch authenticated user's GitHub profile."""
    headers = {
        "Authorization": f"token {access_token}",
        "Accept": "application/vnd.github.v3+json",
    }
    resp = requests.get(GITHUB_API_USER, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()


def revoke_token(client_id: str, client_secret: str, access_token: str) -> bool:
    """Revoke an access token with GitHub."""
    url = GITHUB_REVOKE_TOKEN.format(client_id=client_id)
    headers = {"Accept": "application/vnd.github.v3+json"}
    payload = {"access_token": access_token}
    resp = requests.delete(url, auth=(client_id, client_secret), json=payload, headers=headers, timeout=10)
    resp.raise_for_status()
    return True


def complete_oauth_flow(
    client_id: str, client_secret: str, state: str, redirect_uri: str, port: int = 8000, timeout: int = 120
) -> tuple[str, dict]:
    """Run OAuth flow: start callback server, handle response, exchange code for token.
    
    Returns (access_token, user_dict). Raises RuntimeError on failure.
    """
    result = {}
    done = threading.Event()

    class CallbackHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            parsed = urlparse.urlparse(self.path)
            if parsed.path != urlparse.urlparse(redirect_uri).path:
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
            pass

    server = socketserver.TCPServer(("", port), CallbackHandler)
    server.allow_reuse_address = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        if not done.wait(timeout):
            raise RuntimeError("timeout waiting for OAuth callback")
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=1)

    if "error" in result:
        raise RuntimeError("invalid_state")

    code = result.get("code")
    if not code:
        raise RuntimeError("no_code_received")

    token = exchange_code_for_token(client_id, client_secret, code, redirect_uri)
    if not token:
        raise RuntimeError("failed_to_obtain_access_token")

    user = get_user(token)
    return token, user


# Credential storage functions
def save_credentials(token: str, user: dict) -> None:
    """Save token and user to ~/.atlas/credentials.json with secure permissions."""
    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "access_token": token,
        "user": user.get("login"),
    }
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(data, f)
    CREDENTIALS_FILE.chmod(0o600)


def load_credentials() -> Optional[str]:
    """Load stored access token. Returns None if not found."""
    if not CREDENTIALS_FILE.exists():
        return None
    try:
        with open(CREDENTIALS_FILE, "r") as f:
            data = json.load(f)
        return data.get("access_token")
    except (json.JSONDecodeError, IOError):
        return None


def clear_credentials() -> None:
    """Delete stored credentials."""
    if CREDENTIALS_FILE.exists():
        CREDENTIALS_FILE.unlink()


def is_logged_in() -> bool:
    """Check if user has valid stored credentials."""
    return load_credentials() is not None
