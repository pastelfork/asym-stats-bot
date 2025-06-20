import asyncio
import os

import hikari
from dotenv import load_dotenv
from rich import print
from rich.traceback import install

from .utils import format_large_number, fetch_protocol_tvl

install()
load_dotenv()

USDAF_TVL_BOT_TOKEN = os.getenv("USDAF_TVL_BOT_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")


async def send_update(bot: hikari.GatewayBot):
    try:
        # Fetch TVL using generalized function
        tvl = fetch_protocol_tvl("asymmetry-usdaf")
        formatted_tvl = format_large_number(tvl)
        
        # Update nickname to show TVL
        await bot.rest.edit_my_member(GUILD_ID, nickname=formatted_tvl)
        
    except Exception as e:
        print(f"Error fetching data: {e}")
    
    await asyncio.sleep(60)


async def run():
    bot = hikari.GatewayBot(token=USDAF_TVL_BOT_TOKEN)

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
                name="USDaf TVL",
                type=hikari.ActivityType.WATCHING,
            ),
        )
        await bot.join()
    finally:
        await bot.close()
