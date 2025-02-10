from __future__ import annotations

import asyncio
import logging
import os
import sys
from typing import TYPE_CHECKING

import sentry_sdk
from discord_webhook import DiscordWebhook
from dotenv import load_dotenv
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


logging.basicConfig(
    level=logging.DEBUG,
    stream=sys.stdout,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger: logging.Logger = logging.getLogger(__name__)

sentry_sdk.init(
    dsn="https://d86618c233104cf6f82cffc93db087cf@o4505228040339456.ingest.us.sentry.io/4508792266358784",
    send_default_pii=True,
    traces_sample_rate=1.0,
    _experiments={"continuous_profiling_auto_start": True},
)

load_dotenv(verbose=True)

app_id: str = os.getenv("TWITCH_APP_ID", "")
app_secret: str = os.getenv("TWITCH_APP_SECRET", "")
twitch_usernames: str = os.getenv("TWITCH_USERNAMES", "")
eventsub_url: str = os.getenv("EVENTSUB_URL", "")
webhook_url: str = os.getenv("WEBHOOK_URL", "")
error_webhook_url: str = os.getenv("ERROR_WEBHOOK_URL", "")

if not app_id or not app_secret or not twitch_usernames or not eventsub_url or not webhook_url:
    logger.error("Missing environment variables. Please check your .env file.")
    sys.exit(1)

usernames: list[str] = twitch_usernames.split(",")

logger.info("Starting twitch-online-notifier...")
logger.info("Usernames to listen for:")
for username in usernames:
    logger.info("\t- %s", username)


def send_message_to_discord(message: str, *, if_error: bool = False) -> None:
    """Send a message to the webhook.

    Args:
        message: The message to send.
        if_error: If the message is an error message.
    """
    webhook_to_use: str = webhook_url
    if if_error:
        logger.error(message)
        webhook_to_use = error_webhook_url or webhook_url

    webhook: DiscordWebhook = DiscordWebhook(url=webhook_to_use, content=message, rate_limit_retry=True)
    response: Response = webhook.execute()

    if not response.ok:
        logger.error(
            "Webhook failed when sending last message.\nStatus code: '%s'\nMessage: '%s'",
            response.status_code,
            message,
        )
        send_message_to_discord(
            f"Webhook failed when sending last message.\nStatus code: '{response.status_code}'\nMessage: '{message}'",
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

    logger.info("%s is live!", broadcaster_user_name)
    logger.info("\t%s", broadcaster_url)

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
        msg = "I think the Twitch API is down? We tried to subscribe to a user but it failed."
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
            logger.info("Listening for events for '%s' (%s)", user.display_name, user.id)
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

    logger.info("I am now listening for events on %s", eventsub_url)


def start() -> None:
    """Start the main function."""
    asyncio.run(main())


if __name__ == "__main__":
    start()
