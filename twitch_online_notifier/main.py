import asyncio
import signal
import sys
from typing import Any, Dict

from discord_webhook import DiscordWebhook
from requests import Response
from twitchAPI.eventsub import EventSub
from twitchAPI.twitch import Twitch

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

    print(f"{broadcaster_user_name} is live!")
    print(f"\tURL: {broadcaster_url}")

    send_message(f"{broadcaster_user_name} is live! \n {broadcaster_url}")


async def on_shutdown(event_sub: EventSub, twitch: Twitch) -> None:
    """Handle shutdown gracefully when running on Linux."""
    print("Shutting down...")
    await event_sub.stop()
    await twitch.close()
    sys.exit(0)


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
        print(f"Listening for events for '{user.login}'...")
        if user.id:
            await event_sub.listen_stream_online(user.id, on_live)  # type: ignore
        else:
            send_message(f"ERROR: User '{user.login}' had no id.")

    # Handle Ctrl+C gracefully on Linux.
    if sys.platform == "linux":
        loop: asyncio.AbstractEventLoop = asyncio.get_running_loop()
        for signame in ("SIGINT", "SIGTERM"):
            loop.add_signal_handler(
                getattr(signal, signame),
                lambda: asyncio.create_task(on_shutdown(event_sub, twitch)),
            )

    print("Listening for events...")


if __name__ == "__main__":
    # Run the main function.
    asyncio.run(main())
