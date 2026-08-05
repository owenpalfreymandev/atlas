"""Minimal GitHub OAuth helpers used by the CLI commands.

This module performs the HTTP calls for the OAuth flow so that CLI command code
stays focused on user interaction and the temporary callback server.
"""
from typing import Iterable, Optional
from urllib.parse import urlencode
import json
import os
from pathlib import Path

import requests

GITHUB_AUTHORIZE = "https://github.com/login/oauth/authorize"
GITHUB_ACCESS_TOKEN = "https://github.com/login/oauth/access_token"
GITHUB_API_USER = "https://api.github.com/user"
GITHUB_REVOKE_TOKEN = "https://api.github.com/applications/{client_id}/token"

CREDENTIALS_DIR = Path.home() / ".atlas"
CREDENTIALS_FILE = CREDENTIALS_DIR / "credentials.json"


def get_authorize_url(client_id: str, redirect_uri: str, state: str, scopes: Iterable[str]):
    """Build the GitHub authorization URL.

    scopes is an iterable of scope strings.
    """
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "scope": " ".join(scopes),
    }
    return f"{GITHUB_AUTHORIZE}?{urlencode(params)}"


def exchange_code_for_token(client_id: str, client_secret: str, code: str, redirect_uri: str) -> Optional[str]:
    """Exchange an authorization code for an access token.

    Returns the access token string on success, or None on failure.
    May raise requests.HTTPError for non-2xx responses.
    """
    headers = {"Accept": "application/json"}
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": code,
        "redirect_uri": redirect_uri,
    }
    resp = requests.post(GITHUB_ACCESS_TOKEN, data=payload, headers=headers, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return data.get("access_token")


def get_user(access_token: str) -> dict:
    """Fetch the authenticated user's profile from the GitHub API.

    Raises on HTTP errors.
    """
    headers = {
        "Authorization": f"token {access_token}",
        "Accept": "application/vnd.github.v3+json",
    }
    resp = requests.get(GITHUB_API_USER, headers=headers, timeout=10)
    resp.raise_for_status()
    return resp.json()


def revoke_token(client_id: str, client_secret: str, access_token: str) -> bool:
    """Revoke an access token with GitHub.

    Returns True on success, False on failure.
    May raise requests.HTTPError for non-2xx responses.
    """
    url = GITHUB_REVOKE_TOKEN.format(client_id=client_id)
    headers = {"Accept": "application/vnd.github.v3+json"}
    payload = {
        "access_token": access_token,
    }
    resp = requests.delete(url, auth=(client_id, client_secret), json=payload, headers=headers, timeout=10)
    resp.raise_for_status()
    return True


def save_credentials(token: str, user: dict) -> None:
    """Save credentials to local storage.

    Creates ~/.atlas directory if it doesn't exist.
    """
    CREDENTIALS_DIR.mkdir(parents=True, exist_ok=True)
    data = {
        "access_token": token,
        "user": user.get("login"),
    }
    with open(CREDENTIALS_FILE, "w") as f:
        json.dump(data, f)
    os.chmod(CREDENTIALS_FILE, 0o600)


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


# Higher-level helper to handle the local callback server and complete the flow.
# This moves the HTTP server and waiting logic out of CLI command code.
def complete_oauth_flow(client_id: str, client_secret: str, state: str, redirect_uri: str, port: int = 8000, timeout: int = 120):
    """Start a temporary local HTTP server to receive the OAuth callback, exchange the
    code for a token, and fetch the user. Returns (access_token, user_dict).

    Raises RuntimeError on invalid state, missing code, or timeout. May raise
    requests.HTTPError for HTTP errors during token exchange or user fetch.
    """
    import threading
    import socketserver
    from http.server import BaseHTTPRequestHandler
    from urllib import parse as urlparse

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
            # silence access logs
            return

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
