import typer

from app.commands import hello

app = typer.Typer()

app.command(name="hello")(hello.hello)
app.command(name="goodbye")(hello.goodbye)
