from pathlib import Path
import json


ATLAS_DIR = Path.home() / ".atlas"
CONFIG_FILE = ATLAS_DIR / "config.json"


def save_token(token: str):
    ATLAS_DIR.mkdir(exist_ok=True)

    data = {
        "github_token": token
    }

    CONFIG_FILE.write_text(
        json.dumps(data, indent=4),
        encoding="utf-8"
    )


def get_token():
    if not CONFIG_FILE.exists():
        return None

    data = json.loads(
        CONFIG_FILE.read_text(encoding="utf-8")
    )

    return data.get("github_token")


def clear_token():
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()