FROM python:3.12-slim as builder

# Install Poetry
RUN pip install poetry

# Add /home/root/.local/bin to the PATH
ENV PATH=/home/root/.local/bin:$PATH

# Copy pyproject.toml and poetry.lock
COPY pyproject.toml poetry.lock ./

# Create a requirements.txt file
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

FROM python:3.12-slim

# Create user so we don't run as root.
RUN useradd --create-home botuser

# Change to the user we created.
USER botuser

# Change directory to where we will run the bot.
WORKDIR /app

# Copy the requirements.txt file from the builder stage
COPY --from=builder ./requirements.txt .

# Copy project files
ADD --chown=botuser:botuser twitch_online_notifier /app/twitch_online_notifier

# Run the bot
ENV PYTHONPATH "${PYTHONPATH}:/app/twitch_online_notifier"
CMD [ "python", "twitch_online_notifier/main.py" ]
