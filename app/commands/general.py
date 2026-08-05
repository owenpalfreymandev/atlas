"""General/miscellaneous commands."""
import typer


def hello(name: str):
    """Say hello to someone."""
    typer.echo(f"Hello, {name}")
