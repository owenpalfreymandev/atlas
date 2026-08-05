import typer

app = typer.Typer()


@app.command()
def list():
    """See a list of all your repos."""
    from app.services.github import get_user_repos

    repos = get_user_repos()

    for repo in repos:
        typer.echo(f"{repo['full_name']}")
        typer.echo(f"  description: {repo.get('description') or '—'}")
        typer.echo(f"  visibility: {repo.get('visibility') or ('private' if repo.get('private') else 'public')}")
        typer.echo(f"  language: {repo.get('language') or '—'}")
        typer.echo(f"  default branch: {repo.get('default_branch') or '—'}")
        typer.echo(f"  stars: {repo.get('stargazers_count', 0)}  forks: {repo.get('forks_count', 0)}  open issues: {repo.get('open_issues_count', 0)}")
        typer.echo(f"  url: {repo['html_url']}")

        topics = repo.get("topics") or []
        if topics:
            typer.echo(f"  topics: {', '.join(topics)}")

        typer.echo("")

