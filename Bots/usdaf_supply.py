import asyncio
import os

import hikari
from dotenv import load_dotenv
from rich import print
from rich.traceback import install

from .utils import format_large_number, fetch_token_supply

install()
load_dotenv()

USDAF_PRICE_BOT_TOKEN = os.getenv("USDAF_PRICE_BOT_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")


async def send_update(bot: hikari.GatewayBot):
    try:
        # Fetch supply using generalized function
        supply = fetch_token_supply("USDAF")
        supply_formatted = format_large_number(supply)
        
        # Update nickname to show supply
        await bot.rest.edit_my_member(GUILD_ID, nickname=supply_formatted)
        
    except Exception as e:
        print(f"Error fetching data: {e}")
    
    await asyncio.sleep(60)


async def run():
    bot = hikari.GatewayBot(token=USDAF_PRICE_BOT_TOKEN)

    @bot.listen()
    async def on_ready(event: hikari.ShardReadyEvent):
        while True:
            try:
                await send_update(bot)
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in send_update: {e}")
                await asyncio.sleep(60)

    try:
        await bot.start(
            activity=hikari.Activity(
                name="USDaf Supply",
                type=hikari.ActivityType.WATCHING,
            ),
        )
        await bot.join()
    finally:
        await bot.close()
