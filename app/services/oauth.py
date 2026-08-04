"""Minimal GitHub OAuth helpers used by the CLI commands.

This module performs the HTTP calls for the OAuth flow so that CLI command code
stays focused on user interaction and the temporary callback server.
"""
from typing import Iterable, Optional
from urllib.parse import urlencode

import requests

GITHUB_AUTHORIZE = "https://github.com/login/oauth/authorize"
GITHUB_ACCESS_TOKEN = "https://github.com/login/oauth/access_token"
GITHUB_API_USER = "https://api.github.com/user"


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
