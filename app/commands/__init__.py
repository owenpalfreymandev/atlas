"""CLI command modules."""
from app.commands.auth import login, logout
from app.commands.general import hello

__all__ = ["login", "logout", "hello"]
