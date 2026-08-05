import requests

from app.services.storage import get_token

GITHUB_API = "https://api.github.com"


def get_authenticated_user():
    token = get_token()

    if not token:
        raise RuntimeError("Not authenticated with GitHub. Run `auth login`.")

    headers = {
        "Authorization": f"token {token}", # This header is used to authenticate the request with the GitHub API using the personal access token
        "Accept": "application/vnd.github.v3+json" # This header is used to specify the version of the GitHub API we want to use
    }

    response = requests.get(f"{GITHUB_API}/user", headers=headers, timeout=10)
    response.raise_for_status() # Raises an exception if the request was unsuccessful

    return response.json()


def get_user_repos():
    token = get_token()

    if not token:
        raise RuntimeError("Not authenticated with GitHub. Run `auth login`.")

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    response = requests.get(f"{GITHUB_API}/user/repos", headers=headers, timeout=10) 
    response.raise_for_status()

    return response.json()


def get_repo_details(owner: str, repo: str):
    token = get_token()

    if not token:
        raise RuntimeError("Not authenticated with GitHub. Run `auth login`.")

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    response = requests.get(f"{GITHUB_API}/repos/{owner}/{repo}", headers=headers, timeout=10)
    response.raise_for_status()

    return response.json())


def get_languages(owner: str, repo: str):
    token = get_token()

    if not token:
        raise RuntimeError("Not authenticated with GitHub. Run `auth login`.")

    headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }

    response = requests.get(f"{GITHUB_API}/repos/{owner}/{repo}/languages", headers=headers, timeout=10)
    response.raise_for_status()

    return response.json()
