import os
import logging
import discord
from discord.ext import commands

from macropad_bot import MacroPad

ASSETS_PATH = os.environ.get('ASSETS_PATH')
LOGLEVEL = os.environ.get('LOGLEVEL', 'WARNING').upper()
DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
NGROK_TOKEN = os.environ.get('NGROK_TOKEN', '')
MESSAGE_BROKER_HOSTNAME = os.environ.get('MESSAGE_BROKER_HOSTNAME', 'localhost')
MESSAGE_BROKER_PORT = int(os.environ.get('MESSAGE_BROKER_PORT', '5672'))
if ASSETS_PATH is None:
    raise RuntimeError('ASSETS_PATH should be defined.')
if DISCORD_TOKEN is None:
    raise RuntimeError('DISCORD_TOKEN should be defined.')

logging.basicConfig(level=LOGLEVEL)

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='>', intents=intents)
bot.add_cog(MacroPad(bot,
                     assets_path=ASSETS_PATH,
                     ngrok_token=NGROK_TOKEN,
                     message_broker=(MESSAGE_BROKER_HOSTNAME, MESSAGE_BROKER_PORT)
                     ))
bot.run(DISCORD_TOKEN)
