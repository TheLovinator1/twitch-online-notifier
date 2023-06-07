import asyncio
import random
import sys
from typing import TYPE_CHECKING, Any

from discord_webhook import DiscordWebhook
from loguru import logger
from twitchAPI.eventsub import EventSub
from twitchAPI.twitch import Twitch
from twitchAPI.types import EventSubSubscriptionTimeout

from twitch_online_notifier.settings import Settings, get_settings

if TYPE_CHECKING:
    from requests import Response

# Get the settings from the .env file.
settings: Settings = get_settings()


def send_message(message: str, if_error: bool = False) -> None:
    """Send a message to the webhook.

    Args:
        message (str): The message to send.
        if_error (bool, optional): If the message is an error message. Defaults to False. If True, the message will be
            logged as an error.
    """
    if if_error:
        logger.error(message)

    webhook: DiscordWebhook = DiscordWebhook(url=settings.webhook_url, content=message)
    response: Response = webhook.execute()

    if not response.ok:
        send_message(
            f"Webhook failed when sending last message.\nStatus code: '{response.status_code}'\nMessage: '{message}'",
            if_error=True,
        )


def mexican_msg() -> str:
    catch_phrases: list[str] = [
        "¡Ándale, ándale, arriba, arriba!",
        "¡Órale, güey!",
        "¡Que padre!",
        "¡Ay, caramba!",
        "¡Viva México!",
        "¡No hay bronca!",
        "¡Chido, compadre!",
        "¡A huevo!",
        "¡Qué chula es mi tierra!",
        "¡Ajúa!",
    ]
    emojis: list[str] = ["🌮", "🇲🇽", "🎊", "🎈", "💃", "🎸", "🌵", "🌶️", "🌯", "🔥"]
    return (
        f"{random.choice(emojis)} ¡WarframeInternational está en vivo!"  # noqa: S311
        f" {random.choice(catch_phrases)}\nhttps://twitch.tv/warframeinternational"  # noqa: S311
    )


async def on_live(data: dict[str, Any]) -> None:
    """Called when a user goes live.

    Args:
        data (dict[str, Any]): The data from the event.
    """
    broadcaster_user_name: str = data["event"]["broadcaster_user_name"] or "Unknown"
    broadcaster_login: str = data["event"]["broadcaster_user_login"] or "Unknown"
    broadcaster_url: str = f"https://twitch.tv/{broadcaster_login}"

    # Report error if any of the values are Unknown.
    if "Unknown" in (broadcaster_user_name, broadcaster_login, broadcaster_url):
        send_message(
            (
                "twitch-online-notifier - ERROR: Unknown value in 'on_live' function.\n"
                f"broadcaster_user_name: '{broadcaster_user_name}'\n"
                f"broadcaster_login: '{broadcaster_login}'\n"
                f"broadcaster_url: '{broadcaster_url}'"
            ),
            if_error=True,
        )

    logger.info(f"{broadcaster_user_name} is live!")
    logger.info(f"\tURL: {broadcaster_url}")

    if broadcaster_user_name == "warframeinternational":
        send_message(mexican_msg())
    else:
        send_message(f"{broadcaster_user_name} is live!\n{broadcaster_url}")


async def main() -> None:
    """The main function."""
    # The Twitch API client.
    twitch: Twitch = await Twitch(settings.app_id, settings.app_secret)

    # Start the EventSub server on port 8080.
    event_sub: EventSub = EventSub(settings.eventsub_url, settings.app_id, 8080, twitch)

    # Unsubscribe from all subscriptions so we don't get duplicate events.
    await event_sub.unsubscribe_all()

    # Start the EventSub server. If you go to http://localhost:8080/ in your browser, you should see a message saying "pyTwitchAPI eventsub". # noqa: E501
    event_sub.start()

    # Add a listener for the stream.online event for each user.
    async for user in twitch.get_users(logins=settings.usernames):
        logger.info(f"Listening for events for '{user.login}'.")
        if user.id:
            try:
                await event_sub.listen_stream_online(user.id, on_live)
            except EventSubSubscriptionTimeout:
                send_message(
                    (
                        f"twitch-online-notifier - ERROR: EventSub timed out for user '{user.login}'.\nYou should"
                        " double check that the EventSub URL is correct, and that it is reachable from the internet.\n"
                        "Is your container on the same network as your reverse proxy?"
                    ),
                    if_error=True,
                )
                sys.exit(1)
        else:
            send_message(f"twitch-online-notifier - ERROR: User '{user.login}' had no id.", if_error=True)

    logger.info(f"I am now listening for events on {settings.eventsub_url} :-)")


def start() -> None:
    """Start the main function."""
    asyncio.run(main())


if __name__ == "__main__":
    # Run the main function.
    start()
