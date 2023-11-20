import unittest
from typing import Self
from unittest.mock import MagicMock, patch

import requests

from twitch_online_notifier.healthcheck import healthcheck


class TestHealthcheck(unittest.TestCase):
    """Test the healthcheck function.

    Args:
        unittest: The unittest class.
    """

    @patch("requests.get")
    @patch("sys.exit")
    def test_healthcheck_success(
        self: Self,
        mock_sys_exit: MagicMock,
        mock_requests_get: MagicMock,
    ) -> None:
        """Fake a successful response from the website."""
        mock_response = MagicMock()
        mock_response.ok = True
        mock_requests_get.return_value = mock_response

        # Run the healthcheck function.
        healthcheck()

        # Check that sys.exit was called with 0. (Success)
        mock_sys_exit.assert_called_with(0)

    @patch("requests.get")
    @patch("sys.exit")
    def test_healthcheck_failure(
        self: Self,
        mock_sys_exit: MagicMock,
        mock_requests_get: MagicMock,
    ) -> None:
        """Fake a failed response from the website."""
        mock_requests_get.side_effect = requests.exceptions.RequestException(
            "Connection error",
        )

        # Run the healthcheck function.
        healthcheck()

        # Check that sys.exit was called with 1. (Failure)
        mock_sys_exit.assert_called_with(1)
