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

usernames: list[str] = [username.strip() for username in twitch_usernames.split(",") if username.strip()]

logger.info("Starting twitch-online-notifier...")
logger.info("Usernames to listen for:")
for username in usernames:
    logger.info("\t- %s", username)


def send_message_to_discord(message: str) -> None:
    """Send a message to the webhook.

    Args:
        message: The message to send.
    """
    sentry_sdk.add_breadcrumb(message=message)
    webhook = DiscordWebhook(url=webhook_url, content=message, rate_limit_retry=True)

    sentry_sdk.add_breadcrumb(message="Sending message to Discord...")
    webhook.execute()

    sentry_sdk.add_breadcrumb(message="Message sent to Discord")


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


def send_err_msg(exception: Exception, msg: str, extra_info: dict[str, str]) -> None:
    """Send a message to Discord about a Twitch error.

    Args:
        exception: The exception that was raised.
        msg: A message describing the error.
        extra_info: Additional information to include in the message.
    """
    sentry_sdk.capture_exception(exception)
    if msg:
        logger.error(msg)
        sentry_sdk.capture_message(msg)

    for key, value in extra_info.items():
        sentry_sdk.set_tag(key, value)

    sentry_sdk.set_tag("type", "twitch_error")
    sentry_sdk.set_tag("app_id", app_id)
    sentry_sdk.set_tag("app_secret", app_secret)
    sentry_sdk.set_tag("eventsub_url", eventsub_url)
    sentry_sdk.set_tag("webhook_url", webhook_url)
    sentry_sdk.set_tag("error_webhook_url", error_webhook_url)
    sentry_sdk.set_tag("msg", msg)

    webhook = DiscordWebhook(
        url=error_webhook_url or webhook_url,
        content=f"twitch-online-notifier - ERROR: {msg}",
        rate_limit_retry=True,
    )
    webhook.execute()


async def main() -> None:
    """The main function."""
    twitch: Twitch = await Twitch(app_id, app_secret)
    eventsub = EventSubWebhook(callback_url=eventsub_url, port=8080, twitch=twitch)
    await eventsub.unsubscribe_all()
    logger.info("Waiting for cancellations to propagate...")
    await asyncio.sleep(5)  # Wait 5 seconds before subscribing again

    eventsub.start()

    async for user in twitch.get_users(logins=usernames):
        logger.info("Listening for events for '%s' (%s)", user.display_name, user.id)
        sentry_sdk.add_breadcrumb(message=f"Listening for events for '{user.display_name}' ({user.id})")

        sentry_sdk.set_user({
            "id": user.id,
            "username": user.display_name,
            "type": user.type,
            "broadcaster_type": user.broadcaster_type,
            "description": user.description,
            "profile_image_url": user.profile_image_url,
            "offline_image_url": user.offline_image_url,
            "view_count": user.view_count,
            "email": user.email,
            "created_at": user.created_at,
        })

        try:
            await eventsub.listen_stream_online(broadcaster_user_id=user.id, callback=on_live)
        except EventSubSubscriptionConflict as e:
            send_err_msg(
                exception=e,
                msg=f"User '{user.display_name}' is already being listened for.",
                extra_info={"name": user.display_name},
            )
        except EventSubSubscriptionTimeout as e:
            send_err_msg(
                exception=e,
                msg=f"Timeout occurred while subscribing to user '{user.display_name}'.",
                extra_info={"name": user.display_name},
            )
        except EventSubSubscriptionError as e:
            send_err_msg(
                exception=e,
                msg=f"The subscription request was invalid for '{user.display_name}'.",
                extra_info={"name": user.display_name},
            )
        except TwitchBackendException as e:
            send_err_msg(
                exception=e,
                msg=f"Twitch backend error occurred for user '{user.display_name}'.",
                extra_info={"name": user.display_name},
            )
        except TwitchAPIException as e:
            send_err_msg(
                exception=e,
                msg=f"Twitch API error occurred for user '{user.display_name}'.",
                extra_info={"name": user.display_name},
            )

    logger.info("I am now listening for events on %s", eventsub_url)
    sentry_sdk.add_breadcrumb(message=f"I am now listening for events on {eventsub_url}")


def start() -> None:
    """Start the main function."""
    asyncio.run(main())


if __name__ == "__main__":
    start()
