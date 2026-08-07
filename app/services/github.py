import time
import requests

from app.services.storage import get_token
from app.services.github_errors import (
    github_headers,
    raise_for_github_error,
)


GITHUB_API = "https://api.github.com"

TOP_CONTRIBUTORS = 10
STATS_POLL_ATTEMPTS = 5
STATS_POLL_INTERVAL_SECONDS = 1


def _get_auth_headers():
    token = get_token()

    if not token:
        raise RuntimeError(
            "Not authenticated with GitHub. Run `auth login`."
        )

    return github_headers(token)


def get_authenticated_user():
    response = requests.get(
        f"{GITHUB_API}/user",
        headers=_get_auth_headers(),
        timeout=10,
    )

    raise_for_github_error(response)

    return response.json()


def get_user_repos():
    response = requests.get(
        f"{GITHUB_API}/user/repos",
        headers=_get_auth_headers(),
        timeout=10,
    )

    raise_for_github_error(response)

    return response.json()


def get_repo_details(owner: str, repo: str):
    response = requests.get(
        f"{GITHUB_API}/repos/{owner}/{repo}",
        headers=_get_auth_headers(),
        timeout=10,
    )

    raise_for_github_error(response)

    return response.json()


def get_languages(owner: str, repo: str):
    response = requests.get(
        f"{GITHUB_API}/repos/{owner}/{repo}/languages",
        headers=_get_auth_headers(),
        timeout=10,
    )

    raise_for_github_error(response)

    return response.json()


def get_top_contributors(
    owner: str,
    repo: str,
    limit: int = TOP_CONTRIBUTORS,
) -> list[dict[str, str | int | None]]:
    """
    Return contributors ranked by commit count.

    GitHub may return 202 while it calculates statistics,
    so we retry until the data is available.
    """

    if limit < 1:
        raise ValueError("limit must be at least 1")

    url = (
        f"{GITHUB_API}/repos/"
        f"{owner}/{repo}/stats/contributors"
    )

    for attempt in range(STATS_POLL_ATTEMPTS):
        response = requests.get(
            url,
            headers=_get_auth_headers(),
            timeout=10,
        )

        if response.status_code == 202:
            if attempt < STATS_POLL_ATTEMPTS - 1:
                time.sleep(STATS_POLL_INTERVAL_SECONDS)
                continue

            raise RuntimeError(
                "GitHub is still computing contributor statistics. "
                "Try again shortly."
            )

        raise_for_github_error(response)

        contributors = sorted(
            response.json(),
            key=lambda contributor: contributor["total"],
            reverse=True,
        )[:limit]

        return [
            {
                "login": contributor["author"]["login"],
                "commits": contributor["total"],
                "profile_url": contributor["author"]["html_url"],
                "avatar_url": contributor["author"]["avatar_url"],
            }
            for contributor in contributors
            if contributor["author"] is not None
        ]

    return []