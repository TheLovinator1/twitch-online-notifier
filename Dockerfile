FROM python:3.11-alpine3.17

# Install Poetry
RUN pip install poetry

# Copy only requirements to cache them in docker layer
WORKDIR /code
COPY poetry.lock pyproject.toml /code/

# Install dependencies
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi --only main

# Copy project files
COPY twitch_online_notifier /code/twitch_online_notifier

# Run the bot
CMD [ "poetry", "run", "bot" ]
