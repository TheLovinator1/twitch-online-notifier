import asyncio
import logging
import sys
from typing import Any, Dict

from discord_webhook import DiscordWebhook
from requests import Response
from twitchAPI.eventsub import EventSub
from twitchAPI.twitch import Twitch
from twitchAPI.types import EventSubSubscriptionTimeout

from twitch_online_notifier.settings import Settings, get_settings

# Get the settings from the .env file.
settings: Settings = get_settings()


def send_message(message: str) -> None:
    """Send a message to the webhook.

    Args:
        message (str): The message to send.
    """
    webhook: DiscordWebhook = DiscordWebhook(url=settings.webhook_url, content=message)
    response: Response = webhook.execute()

    if response.status_code != 200:
        send_message(
            "Webhook failed when sending last message.\n"
            f"Status code: '{response.status_code}'\n"
            f"Message: '{message}' "
        )


async def on_live(data: Dict[str, Any]) -> None:
    broadcaster_user_name: str = data["event"]["broadcaster_user_name"] or "Unknown"
    broadcaster_login: str = data["event"]["broadcaster_user_login"] or "Unknown"
    broadcaster_url: str = f"https://twitch.tv/{broadcaster_login}" or "Unknown"

    # Report error if any of the values are Unknown.
    if "Unknown" in (broadcaster_user_name, broadcaster_login, broadcaster_url):
        send_message(
            "twitch-online-notifier - ERROR: Unknown value in 'on_live' function.\n"
            f"broadcaster_user_name: '{broadcaster_user_name}'\n"
            f"broadcaster_login: '{broadcaster_login}'\n"
            f"broadcaster_url: '{broadcaster_url}'"
        )

    logging.info("%s is live!", broadcaster_user_name)
    logging.info("\tURL: %s", broadcaster_url)

    send_message(f"{broadcaster_user_name} is live!\n{broadcaster_url}")


async def main() -> None:
    # The Twitch API client.
    twitch: Twitch = await Twitch(settings.app_id, settings.app_secret)

    # Start the EventSub server on port 8080.
    event_sub: EventSub = EventSub(settings.eventsub_url, settings.app_id, 8080, twitch)

    # Unsubscribe from all subscriptions so we don't get duplicate events.
    await event_sub.unsubscribe_all()

    # Start the EventSub server. If you go to http://localhost:8080/ in your browser, you should see a message saying "pyTwitchAPI eventsub".
    event_sub.start()

    # Add a listener for the stream.online event for each user.
    async for user in twitch.get_users(logins=settings.usernames):
        logging.info("Listening for events for '%s'...", user.login)
        if user.id:
            try:
                await event_sub.listen_stream_online(user.id, on_live)  # type: ignore
            except EventSubSubscriptionTimeout:
                logging.error("EventSub timed out for user '%s'.", user.login)
                send_message(
                    f"twitch-online-notifier - ERROR: EventSub timed out for user '{user.login}'."
                    f" Are you sure {settings.eventsub_url} is accessible from the internet?"
                    " Is it on the same network as your reverse proxy?"
                )
                sys.exit(1)
        else:
            logging.error("User '%s' had no id.", user.login)
            send_message(f"twitch-online-notifier - ERROR: User '{user.login}' had no id.")

    logging.info("I am now listening for events on %s :-)", settings.eventsub_url)


def start() -> None:
    logging.basicConfig(level=logging.getLevelName("INFO"))
    asyncio.run(main())


if __name__ == "__main__":
    # Run the main function.
    start()
