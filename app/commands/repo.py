import typer

app = typer.Typer()

units = ["KB", "MB", "GB", "TB", "PB" ]


def format_topics(topics: list[str], max_topics: int = 5) -> str:
    shown = topics[:max_topics]
    remaining = len(topics) - len(shown)
    rendered = ", ".join(shown)
    if remaining > 0:
        rendered = f"{rendered} + {remaining} more..."
    return rendered


def format_description(description: str, max_chars: int = 90) -> str:
    if len(description) <= max_chars:
        return description

    # Truncate at or after max_chars, but never in the middle of a word.
    cutoff = description.find(" ", max_chars)
    if cutoff == -1:
        cutoff = len(description)

    shown = description[:cutoff].rstrip()
    return (f"{shown}...")

def format_size(size: int) -> str:
    units = ["KB", "MB", "GB", "TB", "PB"]

    current_unit = 0

    while size >= 1000 and current_unit < len(units) - 1:
        size = size / 1000
        current_unit += 1

    return f"{size:.1f} {units[current_unit]}"

def format_languages(languages: dict[str, int], max_languages: int = 5) -> list[str]:
    if not languages:
        return ["No language data returned."]

    total_bytes = sum(languages.values())

    sorted_languages = sorted(
        languages.items(),
        key=lambda item: item[1],
        reverse=True
    )

    shown = sorted_languages[:max_languages]
    remaining = len(sorted_languages) - len(shown)

    formatted = []

    for language, byte_count in shown:
        percent = (byte_count / total_bytes * 100) if total_bytes else 0
        formatted.append(f"{language}: {percent:.1f}%")

    if remaining > 0:
        formatted.append(f"+ {remaining} more...")

    return formatted


@app.command()
def list():
    """See a list of all your repos."""
    from app.services.github import get_user_repos

    repos = get_user_repos()

    for repo in repos:
        typer.echo(f"{repo['full_name']}")
        description = repo.get("description") or "—"
        typer.echo(f"description: {format_description(description)}")
        typer.echo(f"visibility: {repo.get('visibility') or ('private' if repo.get('private') else 'public')}")
        typer.echo(f"language: {repo.get('language') or '—'}")
        typer.echo(f"default branch: {repo.get('default_branch') or '—'}")
        typer.echo(f"stars: {repo.get('stargazers_count', 0)}  forks: {repo.get('forks_count', 0)}  open issues: {repo.get('open_issues_count', 0)}")
        typer.echo(f"  url: {repo['html_url']}")

        topics = repo.get("topics") or []
        if topics:
            typer.echo(f"  topics: {format_topics(topics)}")

        typer.echo("")


@app.command()
def details(
    owner: str = typer.Argument(..., help="Repository owner, e.g. owenpalfreymandev"),
    repo: str = typer.Argument(..., help="Repository name, e.g. atlas"),
):
    """Gain insights into your repo"""
    from app.services.github import get_repo_details, get_languages, get_top_contributors

    details = get_repo_details(owner, repo)
    languages = get_languages(owner, repo)
    contributions = get_top_contributors(owner, repo, limit=5)

    # Repo Details
    typer.echo("Repository")
    typer.echo("-----------")
    typer.echo(f"{details.get('full_name', f'{owner}/{repo}')}") # Name
    description = details.get("description") or "—"
    typer.echo(f"description: {format_description(description)}") # Description
    typer.echo(
        f"visibility: {details.get('visibility') or ('private' if details.get('private') else 'public')}" # Visibility
    )
    typer.echo(f"url: {details.get('html_url') or f'https://github.com/{owner}/{repo}'}") # URL

    # Stats
    typer.echo("")
    typer.echo("Stats")
    typer.echo("-----------")
    typer.echo(f"stars: {details.get('stargazers_count') or 0}") # Stars
    typer.echo(f"forks: {details.get("forks_count")}") # Forks
    typer.echo(f"issues: {details.get('open_issues_count') or 0}") # Issues
    typer.echo(f"size: {format_size(details.get('size'))}") # Size

    typer.echo("")
    typer.echo("Contributions")
    typer.echo("-----------")
    if not contributions:
        typer.echo("No contributor data returned.")
    else:
        for contributor in contributions:
            typer.echo(
                f"{contributor['login']}: {contributor['commits']} commits"
            )

    # Tech
    typer.echo("")
    typer.echo("Languages")
    typer.echo("---------")

    for language in format_languages(languages):
        typer.echo(language)
