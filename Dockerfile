FROM python:3.13-slim
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
RUN useradd --create-home botuser
USER botuser
WORKDIR /app
COPY --chown=botuser:botuser twitch_online_notifier /app/twitch_online_notifier
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --no-install-project

CMD [ "uv", "run", "twitch_online_notifier/main.py" ]
