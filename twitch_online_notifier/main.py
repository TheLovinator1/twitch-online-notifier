from __future__ import annotations

import asyncio
import os
from typing import TYPE_CHECKING

from discord_webhook import AsyncDiscordWebhook
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
    from twitchAPI.object.eventsub import StreamOnlineEvent

load_dotenv(dotenv_path=find_dotenv(), verbose=True)

app_id: str | None = os.environ["TWITCH_APP_ID"]
app_secret: str | None = os.environ["TWITCH_APP_SECRET"]
twitch_usernames: str | None = os.environ["TWITCH_USERNAMES"]
eventsub_url: str | None = os.environ["EVENTSUB_URL"]
webhook_url: str | None = os.environ["WEBHOOK_URL"]

usernames = []
if twitch_usernames is not None:
    usernames: list[str] = twitch_usernames.split(",")


async def send_message_to_discord(message: str, *, if_error: bool = False) -> None:
    """Send a message to the webhook.

    Args:
        message: The message to send.
        if_error: If the message is an error message.
    """
    if if_error:
        logger.error(message)

    webhook: AsyncDiscordWebhook = AsyncDiscordWebhook(
        url=webhook_url,
        content=message,
        rate_limit_retry=True,
    )
    await webhook.execute()


async def on_live(data: StreamOnlineEvent) -> None:
    """Called when a user goes live.

    Args:
        data: The data from the event.
    """
    broadcaster_user_name: str = data.event.broadcaster_user_name
    broadcaster_login: str = data.event.broadcaster_user_login
    broadcaster_url: str = f"https://twitch.tv/{broadcaster_login}"

    logger.info(f"{broadcaster_user_name} is live!")
    logger.info(f"\tURL: {broadcaster_url}")

    await send_message_to_discord(
        f"{broadcaster_user_name} is live!\n{broadcaster_url}",
    )


async def send_twitch_error_message(exception: Exception) -> None:
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
    await send_message_to_discord(
        "twitch-online-notifier - ERROR: " + msg,
        if_error=True,
    )


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
                await send_twitch_error_message(e)
                continue

    except TwitchAPIException as e:
        await send_twitch_error_message(e)

    logger.info(f"I am now listening for events on {eventsub_url} :-)")


def start() -> None:
    """Start the main function."""
    asyncio.run(main())


if __name__ == "__main__":
    start()
