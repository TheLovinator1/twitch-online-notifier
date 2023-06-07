import os

from twitch_online_notifier.settings import Settings, get_settings


def test_get_settings() -> None:
    """Test the get_settings function."""
    settings: Settings = get_settings()

    app_id: str | None = os.getenv("TWITCH_APP_ID")
    app_secret: str | None = os.getenv("TWITCH_APP_SECRET")
    twitch_usernames: str | None = os.getenv("TWITCH_USERNAMES")

    if twitch_usernames is None:
        msg = "TWITCH_USERNAMES must be set."
        raise ValueError(msg)

    usernames: list[str] = twitch_usernames.split(",")
    eventsub_url: str | None = os.getenv("EVENTSUB_URL")
    webhook_url: str | None = os.getenv("WEBHOOK_URL")

    assert settings.app_id == app_id
    assert settings.app_secret == app_secret
    assert settings.usernames == usernames
    assert settings.eventsub_url == eventsub_url
    assert settings.webhook_url == webhook_url
