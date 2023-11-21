# twitch-online-notifier

Send a webhook to Discord when a Twitch stream goes live.

<p align="center">
    <img alt="Warframe is live!" src="https://github.com/TheLovinator1/twitch-online-notifier/blob/master/.github/example.png?raw=true" loading="lazy" width="50%" height="50%" />
</p>

## How it works

Twitch will send a webhook to this program when a stream goes live. This program will then send a webhook to Discord.

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

```nginx
## Version 2023/11/21
server {
    listen 443 ssl;

    server_name eventsub.example.com; # Change this to your domain

    include /config/nginx/ssl.conf;

    client_max_body_size 0;

    location / {
        include /config/nginx/proxy.conf;
        include /config/nginx/resolver.conf;
        set $upstream_app twitch-online-notifier; # Name of the docker container
        set $upstream_port 8080;
        set $upstream_proto http;
        proxy_pass $upstream_proto://$upstream_app:$upstream_port;
    }
}
```
