import asyncio
import os

import hikari
from dotenv import load_dotenv
from rich import print
from rich.traceback import install

from .utils import format_large_number, fetch_token_price, calculate_market_cap

install()
load_dotenv()

ASF_PRICE_BOT_TOKEN = os.getenv("ASF_PRICE_BOT_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")


async def send_update(bot: hikari.GatewayBot):
    try:
        # Fetch price
        price = fetch_token_price("ASF")
        price_formatted = f"${price:.2f}"
        
        # Update nickname to show price
        await bot.rest.edit_my_member(GUILD_ID, nickname=price_formatted)
        
        # Try to calculate market cap
        try:
            market_cap = calculate_market_cap("ASF")
            mcap_formatted = format_large_number(market_cap)
            
            # Update activity to show market cap
            await bot.update_presence(
                activity=hikari.Activity(
                    name=f"{mcap_formatted} Market Cap",
                    type=hikari.ActivityType.WATCHING,
                ),
            )
        except Exception as e:
            # If market cap fails, just show price in activity
            print(f"Warning: Could not calculate market cap: {e}")
            await bot.update_presence(
                activity=hikari.Activity(
                    name=f"ASF Price: {price_formatted}",
                    type=hikari.ActivityType.WATCHING,
                ),
            )
        
    except Exception as e:
        print(f"Error fetching data: {e}")
    
    await asyncio.sleep(60)


async def run():
    bot = hikari.GatewayBot(token=ASF_PRICE_BOT_TOKEN)

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
        await bot.start()
        await bot.join()
    finally:
        await bot.close()
