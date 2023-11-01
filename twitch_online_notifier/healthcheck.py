import sys

import requests
from loguru import logger


def healthcheck() -> None:
    """Check if the website is up.

    sys.exit(0): success - the container is healthy and ready for use.
    sys.exit(1): unhealthy - the container is not working correctly.
    """
    try:
        response: requests.Response = requests.get(
            url="http://localhost:8080",
            timeout=5,
        )
        if response.ok:
            logger.info("Healthcheck passed.")
            sys.exit(0)
    except requests.exceptions.RequestException as e:
        logger.critical(f"Healthcheck failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    healthcheck()
