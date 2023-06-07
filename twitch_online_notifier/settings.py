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
    twitch_usernames: str | None = os.getenv("TWITCH_USERNAMES")
    eventsub_url: str | None = os.getenv("EVENTSUB_URL")
    webhook_url: str | None = os.getenv("WEBHOOK_URL")
    usernames = []

    if twitch_usernames is not None:
        usernames: list[str] = twitch_usernames.split(",")

    if not usernames:
        msg = "TWITCH_USERNAMES must be set. See README.md for more information."
        raise ValueError(msg)

    if eventsub_url is None:
        msg = "EVENTSUB_URL must be set. See README.md for more information."
        raise ValueError(msg)

    if webhook_url is None:
        msg = "WEBHOOK_URL must be set. See README.md for more information."
        raise ValueError(msg)

    if app_id is None:
        msg = "TWITCH_APP_ID must be set. See README.md for more information."
        raise ValueError(msg)

    if app_secret is None:
        msg = "TWITCH_APP_SECRET must be set. See README.md for more information."
        raise ValueError(msg)

    return Settings(
        app_id=app_id,
        app_secret=app_secret,
        usernames=usernames,
        eventsub_url=eventsub_url,
        webhook_url=webhook_url,
    )
