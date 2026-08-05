import typer

from app.commands import auth, me, repo

app = typer.Typer()

app.command(name="login")(auth.login)
app.command(name="logout")(auth.logout)
app.command(name="me")(me.me)
app.command(name="list")(repo.list)