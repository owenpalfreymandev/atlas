from requests import Response


def github_headers(token: str) -> dict[str, str]:
    """Build headers for GitHub REST API requests."""
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2026-03-10",
    }


def raise_for_github_error(response: Response) -> None:
    """Raise a useful error message for failed GitHub API requests."""
    if response.ok:
        return

    try:
        message = response.json().get("message", response.reason)
    except ValueError:
        message = response.text or response.reason

    details = [
        f"GitHub API returned {response.status_code}: {message}"
    ]

    request_id = response.headers.get("X-GitHub-Request-Id")
    if request_id:
        details.append(f"request ID: {request_id}")

    if response.status_code in {403, 429}:
        remaining = response.headers.get("X-RateLimit-Remaining")

        if remaining == "0":
            details.append("primary API rate limit exhausted")

        retry_after = response.headers.get("Retry-After")
        if retry_after:
            details.append(
                f"retry after {retry_after} seconds"
            )

    raise RuntimeError("; ".join(details))