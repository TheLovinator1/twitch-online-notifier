import pytest

from twitch_online_notifier.main import on_live, send_message


def test_send_message() -> None:
    """Test the send_message function."""
    send_message("Test message from twitch_online_notifier")


@pytest.mark.asyncio()
async def test_on_live() -> None:
    """Test the on_live function."""
    await on_live(
        {
            "event": {
                "broadcaster_user_name": "TestUser",
                "broadcaster_user_login": "testuser",
            },
        },
    )
