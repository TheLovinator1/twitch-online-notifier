from __future__ import annotations

import asyncio
import os
import sys
from typing import TYPE_CHECKING

from discord_webhook import DiscordWebhook
from dotenv import find_dotenv, load_dotenv
from loguru import logger
from twitchAPI.eventsub.webhook import EventSubWebhook
from twitchAPI.twitch import Twitch
from twitchAPI.type import (
    EventSubSubscriptionConflict,
    EventSubSubscriptionError,
    EventSubSubscriptionTimeout,
    TwitchAPIException,
    TwitchBackendException,
)

if TYPE_CHECKING:
    from requests import Response
    from twitchAPI.object.eventsub import StreamOnlineEvent

load_dotenv(find_dotenv(), verbose=True)

app_id: str = os.getenv("TWITCH_APP_ID", "")
app_secret: str = os.getenv("TWITCH_APP_SECRET", "")
twitch_usernames: str = os.getenv("TWITCH_USERNAMES", "")
eventsub_url: str = os.getenv("EVENTSUB_URL", "")
webhook_url: str = os.getenv("WEBHOOK_URL", "")
error_webhook_url: str = os.getenv("ERROR_WEBHOOK_URL", "")

if (
    app_id == ""
    or app_secret == ""
    or twitch_usernames == ""
    or eventsub_url == ""
    or webhook_url == ""
):
    logger.error("Missing environment variables. Please check your .env file.")
    sys.exit(1)

usernames = []
if twitch_usernames is not None:
    usernames: list[str] = twitch_usernames.split(",")

logger.info("Starting twitch-online-notifier...")
logger.info("Usernames to listen for:")
for username in usernames:
    logger.info(f"\t- {username}")


def send_message_to_discord(message: str, *, if_error: bool = False) -> None:
    """Send a message to the webhook.

    Args:
        message: The message to send.
        if_error: If the message is an error message.
    """
    webhook_to_use = webhook_url
    if if_error:
        logger.error(message)
        webhook_to_use: str = error_webhook_url

    webhook: DiscordWebhook = DiscordWebhook(
        url=webhook_to_use,
        content=message,
        rate_limit_retry=True,
    )
    response: Response = webhook.execute()

    if not response.ok:
        send_message_to_discord(
            f"Webhook failed when sending last message.\nStatus code: '{response.status_code}'\nMessage: '{message}'",  # noqa: E501
            if_error=True,
        )


async def on_live(data: StreamOnlineEvent) -> None:  # noqa: RUF029
    """Called when a user goes live.

    Args:
        data: The data from the event.
    """
    broadcaster_user_name: str = data.event.broadcaster_user_name
    broadcaster_login: str = data.event.broadcaster_user_login
    broadcaster_url: str = f"https://twitch.tv/{broadcaster_login}"

    logger.info(f"{broadcaster_user_name} is live!")
    logger.info(f"\tURL: {broadcaster_url}")

    send_message_to_discord(f"{broadcaster_user_name} is live!\n{broadcaster_url}")


def send_twitch_error_message(exception: Exception) -> None:
    """Send a message to Discord about a Twitch error.

    Args:
        exception: The exception that was raised.
    """
    msg = "Something went wrong."
    if isinstance(exception, EventSubSubscriptionConflict):
        msg = "You tried to subscribe to a EventSub subscription that already exists."
    elif isinstance(exception, EventSubSubscriptionTimeout):
        msg = "When the waiting for a confirmed EventSub subscription timed out."
    elif isinstance(exception, EventSubSubscriptionError):
        msg = "The subscription request was invalid."
    elif isinstance(exception, TwitchBackendException):
        msg = "I think the Twitch API is down? We tried to subscribe to a user but it failed."  # noqa: E501
    send_message_to_discord("twitch-online-notifier - ERROR: " + msg, if_error=True)


async def main() -> None:
    """The main function."""
    twitch: Twitch = await Twitch(app_id, app_secret)
    eventsub = EventSubWebhook(
        callback_url=eventsub_url,
        port=8080,
        twitch=twitch,
    )
    await eventsub.unsubscribe_all()
    eventsub.start()

    try:
        async for user in twitch.get_users(logins=usernames):
            logger.info(f"Listening for events for '{user.login}'.")
            try:
                await eventsub.listen_stream_online(
                    broadcaster_user_id=user.id,
                    callback=on_live,
                )
            except TwitchAPIException as e:
                send_twitch_error_message(e)
                continue

    except TwitchAPIException as e:
        send_twitch_error_message(e)

    logger.info(f"I am now listening for events on {eventsub_url} :-)")


def start() -> None:
    """Start the main function."""
    asyncio.run(main())


if __name__ == "__main__":
    start()
