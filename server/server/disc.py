import os
import logging
import discord
import asyncio
import aio_pika
from os import path, listdir
from os.path import isfile
from discord.errors import ClientException
from discord.ext import commands
import subprocess
import clips

ASSETS_PATH = 'assets'
LOGLEVEL = os.environ.get('LOGLEVEL', 'WARNING').upper()
DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
MESSAGE_BROKER = os.environ.get('MESSAGE_BROKER', 'localhost')
if DISCORD_TOKEN is None:
    raise RuntimeError('DISCORD_TOKEN should be defined.')

logging.basicConfig(level=LOGLEVEL)

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='>', intents=intents)
on_leave = None

async def play_from_source(ctx, name):
    file = path.join(ASSETS_PATH, f'{name}.mp3')
    try:
        source = await discord.FFmpegOpusAudio.from_probe(file)
        ctx.voice_client.play(source)
    except subprocess.CalledProcessError:
        logging.warning(f"Requested clip not found: {name}; path: {file}")
        ctx.send(f"Couldn't find clip named {name}.")
    except ClientException:
        logging.warning('Bot was already playing some audio.')

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}.')

@bot.command()
async def join(ctx):
    channel = ctx.author.voice.channel
    if ctx.voice_client is not None:
        return await ctx.voice_client.move_to(channel)
    await channel.connect()

    async def on_message(message):
        async with message.process():
            msg = message.body.decode('utf-8')
            clip = clips.default(msg)
            await play_from_source(ctx, clip)

    connection = await aio_pika.connect(MESSAGE_BROKER)
    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=1)
        logs_exchange = await channel.declare_exchange('default',
                                                       aio_pika.ExchangeType.FANOUT)
        queue = await channel.declare_queue(exclusive=True)
        await queue.bind(logs_exchange)

        broker_tag = await queue.consume(on_message)
        global on_leave
        async def go():
            await queue.cancel(broker_tag)
        on_leave = go
        logging.info(f'Connection with message broker {MESSAGE_BROKER} enstablished.')
        await asyncio.Future()

@bot.command()
async def list(ctx):
    files = [f'**{f.removesuffix(".mp3")}**' for f in listdir(ASSETS_PATH)
             if isfile(path.join(ASSETS_PATH, f)) and f.endswith('.mp3')]
    await ctx.send('Available sounds are: \n{}'.format("\n".join(files)))

@bot.command()
async def play(ctx, clip: str):
    await play_from_source(ctx, clip)

@bot.command()
async def leave(ctx):
    if ctx.voice_client is not None:
        await ctx.voice_client.disconnect()
    if on_leave is not None:
        await on_leave()

bot.run(DISCORD_TOKEN)
