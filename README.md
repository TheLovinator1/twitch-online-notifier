# twitch-online-notifier

Send a webhook to Discord when a stream goes online

## How it works

Twitch will send a webhook to this server when a stream goes online. This server will then send a webhook to Discord.

## Usage

You need to run this behind a reverse proxy. It needs to be publicly accessible and have a valid SSL certificate. Default port is 8080.

If you go to `EVENTSUB_URL` you should see "pyTwitchAPI eventsub".

### Configuration

The configuration is done via environment variables or a `.env` file.

Go to the [Twitch developer console](https://dev.twitch.tv/console/apps) and create a new application. You need to set the redirect URL to `http://localhost` and the category to `Application Integration`.

| Variable | Description | Example |
|----------|-------------| ------- |
| `TWITCH_APP_ID` | Your Twitch application client ID | `ah3pwocaw0b...8komm9vs6abuzq` |
| `TWITCH_APP_SECRET` | Your Twitch application client secret | `04ml1373bss...d4kapi912e9i6h` |
| `TWITCH_USERNAMES` | Comma-separated list of Twitch usernames to monitor | `warframe,warframeinternational` |
| `EVENTSUB_URL` | The URL to listen for Twitch EventSub webhooks on | `https://eventsub.example.com` |
| `WEBHOOK_URL` | Discord webhook URL | `https://discord.com/api/webhooks/...` |

### Nginx

There is an example for Nginx called `eventsub.subdomain.conf` for all
the swag users out there.

## Help

- Email: tlovinator@gmail.com
- Discord: TheLovinator#9276
- Send an issue: [twitch-online-notifier/issues](https://github.com/TheLovinator1/twitch-online-notifier/issues)
