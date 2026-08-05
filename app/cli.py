import typer

from app.commands import hello
from app.commands import auth

app = typer.Typer()

app.command(name="hello")(hello.hello)
app.command(name="goodbye")(hello.goodbye)
app.command(name="login")(auth.login)
app.command(name="logout")(auth.logout)