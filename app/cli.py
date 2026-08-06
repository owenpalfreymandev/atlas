import typer

from app.commands import auth, me, repo

app = typer.Typer()

# Commands that can be ran in the CLI
app.command(name="login")(auth.login)
app.command(name="logout")(auth.logout)
app.command(name="me")(me.me)
app.command(name="list")(repo.list)
app.command(name="details")(repo.details)