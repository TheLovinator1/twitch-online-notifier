import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv(verbose=True)


@dataclass
class Settings:
    app_id: str
    app_secret: str
    usernames: list[str]
    eventsub_url: str
    webhook_url: str


def get_settings() -> Settings:
    """Get the settings from the .env file.

    Raises:
        ValueError: If the settings are not set.

    Returns:
        tuple[str, str]: The app id and app secret.
    """

    app_id: str | None = os.getenv("TWITCH_APP_ID")
    app_secret: str | None = os.getenv("TWITCH_APP_SECRET")
    usernames: str | None = os.getenv("TWITCH_USERNAMES")
    eventsub_url: str | None = os.getenv("EVENTSUB_URL")
    webhook_url: str | None = os.getenv("WEBHOOK_URL")
    username_list = []

    if usernames is not None:
        username_list: list[str] = usernames.split(",")

    if not username_list:
        raise ValueError("TWITCH_USERNAMES must be set. See README.md for more information.")

    if eventsub_url is None:
        raise ValueError("EVENTSUB_URL must be set. See README.md for more information.")

    if webhook_url is None:
        raise ValueError("WEBHOOK_URL must be set. See README.md for more information.")

    if app_id is None:
        raise ValueError("TWITCH_APP_ID must be set. See README.md for more information.")

    if app_secret is None:
        raise ValueError("TWITCH_APP_SECRET must be set. See README.md for more information.")

    return Settings(
        app_id=app_id,
        app_secret=app_secret,
        usernames=username_list,
        eventsub_url=eventsub_url,
        webhook_url=webhook_url,
    )
