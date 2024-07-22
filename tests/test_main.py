import datetime

import pytest
from twitchAPI.object.eventsub import StreamOnlineData, StreamOnlineEvent

from twitch_online_notifier.main import (
    on_live,
    send_message_to_discord,
    send_twitch_error_message,
)


def test_send_message() -> None:
    """Test the send_message function."""
    send_message_to_discord("Test message from twitch_online_notifier")


@pytest.mark.asyncio
async def test_on_live() -> None:
    """Test the on_live function."""
    data = StreamOnlineEvent()
    data.event = StreamOnlineData()
    data.event.broadcaster_user_name = "broadcaster_user_name"
    data.event.broadcaster_user_login = "broadcaster_user_login"
    data.event.started_at = datetime.datetime.now(tz=datetime.UTC)

    await on_live(data)


def test_send_twitch_error_message() -> None:
    """Test the send_twitch_error_message function."""
    send_twitch_error_message(Exception())
