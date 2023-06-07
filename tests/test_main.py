import pytest

from twitch_online_notifier.main import mexican_msg, on_live, send_message


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


def test_mexican_msg() -> None:
    """Test the mexican_msg function."""
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

    msg = mexican_msg()
    # Check that the message contains the channel name.
    assert "¡WarframeInternational está en vivo!" in msg

    # Check that the message contains the URL.
    assert "https://twitch.tv/warframeinternational" in msg

    # Check that the message contains one of the catch phrases.
    assert any(phrase in msg for phrase in catch_phrases)

    # Check that the message contains one of the emojis.
    assert any(emoji in msg for emoji in emojis)
