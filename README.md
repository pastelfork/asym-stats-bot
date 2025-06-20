# Asymmetry Finance Stats Discord Bot

## Requirements

This project is managed using `uv`

```bash
pip install uv
```

or

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

You will also need:

- Discord bot tokens (1-3 bots depending on which you run)
- Guild ID (aka server ID)
- HTTP RPC URL for Ethereum Mainnet (optional, uses public RPCs by default)

## Setup

```bash
git clone https://github.com/pastelfork/asym-stats-bot
```

```bash
cd asym-stats-bot
```

```bash
cp .env.example .env
```

Paste your environment variables in the .env file (see requirements above).

```bash
uv run main.py
```

The bot should now be running and updating stats in Discord
