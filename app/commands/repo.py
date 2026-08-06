import typer

app = typer.Typer()


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
    remaining = len(description) - len(shown)
    return (f"{shown}...")


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
    from app.services.github import get_repo_details, get_languages

    details = get_repo_details(owner, repo)
    languages = get_languages(owner, repo)

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
    typer.echo(f"stars: {details.get('starsgazers_count') or 0}") # Stars
    typer.echo(f"forks: {details.get("forks_count")}") # Forks
    typer.echo(f"issues: {details.get('open_issues_count') or 0}") # Issues
    typer.echo(f"size: {details.get("size")}") # Size

    # TODO: Contributions

    # Tech
    typer.echo("")
    typer.echo("Languages")
    typer.echo("---------")
    total_bytes = sum(languages.values()) if languages else 0
    if not languages:
        typer.echo("No language data returned.")
        return

    # Convert the byte count into a percentage figure
    for language, byte_count in sorted(languages.items(), key=lambda item: item[1], reverse=True):
        percent = (byte_count / total_bytes * 100) if total_bytes else 0
        typer.echo(f"{language}: {percent:.1f}% ({byte_count} bytes)")

    topics = details.get("topics") or []
    if topics:
        typer.echo(f"topics: {format_topics(topics)}")
