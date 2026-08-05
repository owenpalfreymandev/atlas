import typer

app = typer.Typer()

@app.command()
def me():
    """Get information about me!"""
    from app.services.github import get_authenticated_user

    user = get_authenticated_user()

    username = user.get("login") or "N/A"
    name = user.get("name") or "N/A"
    email = user.get("email") or "N/A"
    bio = user.get("bio") or "N/A"
    location = user.get("location") or "N/A"
    company = user.get("company") or "N/A"

    public_repos = user.get("public_repos", "N/A")
    total_private_repos = user.get("total_private_repos")
    if total_private_repos is None:
        total_private_repos = "N/A"

    followers = user.get("followers", "N/A")
    following = user.get("following", "N/A")

    typer.echo(f"Username: {username}")
    typer.echo(f"Name: {name}")
    typer.echo(f"Email: {email}")
    typer.echo(f"Bio: {bio}")
    typer.echo(f"Location: {location}")
    typer.echo(f"Company: {company}")
    typer.echo(f"Public repos: {public_repos}")
    typer.echo(f"Private repos: {total_private_repos}")
    typer.echo(f"Followers: {followers}")
    typer.echo(f"Following: {following}")
