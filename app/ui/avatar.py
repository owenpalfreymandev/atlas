import requests

from io import BytesIO
from PIL import Image
from rich_pixels import Pixels


def get_profile_picture(user: dict):
    """Return user profile picture as a small Rich renderable."""

    avatar_url = user.get("avatar_url")

    if not avatar_url:
        return ""

    response = requests.get(avatar_url, timeout=10)
    response.raise_for_status()

    image = Image.open(BytesIO(response.content))

    # Resize avatar for terminal display
    image.thumbnail((28, 28))

    return Pixels.from_image(image)