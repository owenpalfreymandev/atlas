"""Application configuration and constants."""
from pathlib import Path

# GitHub OAuth URLs
GITHUB_AUTHORIZE = "https://github.com/login/oauth/authorize"
GITHUB_ACCESS_TOKEN = "https://github.com/login/oauth/access_token"
GITHUB_API_USER = "https://api.github.com/user"
GITHUB_REVOKE_TOKEN = "https://api.github.com/applications/{client_id}/token"

# Credentials storage
CREDENTIALS_DIR = Path.home() / ".atlas"
CREDENTIALS_FILE = CREDENTIALS_DIR / "credentials.json"
