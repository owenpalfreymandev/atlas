import typer

from app.commands import hello, me, auth

app = typer.Typer()

app.command(name="hello")(hello.hello)
app.command(name="goodbye")(hello.goodbye)
app.command(name="login")(auth.login)
app.command(name="logout")(auth.logout)
app.command(name="me")(me.me)