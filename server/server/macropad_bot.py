import logging
from typing import Tuple
import discord
import aio_pika
import asyncio
import re
from os import path, listdir
from os.path import isfile
from discord.errors import ClientException
from discord.ext import commands
from pyngrok import ngrok
import subprocess
import clips


class MacroPad(commands.Cog):
    def __init__(self, bot, assets_path, ngrok_token, message_broker_url):
        self.bot = bot
        self._on_chat_leave = None
        self._assets_path = assets_path
        self._ngrok_token = ngrok_token
        self._message_broker_url = message_broker_url

    @commands.command()
    async def list(self, ctx):
        """
        Lists all mp3 clips that are playable. In order to be detected they must be
        stored in the ASSETS_PATH folder and have the ".mp3" suffix.
        """
        files = [f'**{f.removesuffix(".mp3")}**' for f in listdir(self._assets_path)
                if isfile(path.join(self._assets_path, f)) and f.endswith('.mp3')]
        await ctx.send('Available sounds are: \n{}'.format("\n".join(files)))

    @commands.command()
    async def play(self, ctx, clip: str):
        """
        Bot command that enables a user to play a target clip using a text message.
        You have to be in a voice chat to run it.
        """
        await self._play_from_source(ctx, clip)

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Logged in as {self.bot.user}.')

    @commands.command()
    async def join(self, ctx):
        """
        Bot command that tells the bot to join a voice channel.
        When that happens this process enstablishes a connection with the message
        broker in order to receive events.
        It also creates an ngrok process exposing the message broker with the chat.
        """
        channel = ctx.author.voice.channel
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)
        await channel.connect()

        async def on_message(message):
            print('receive message')
            async with message.process():
                msg = message.body.decode('utf-8')
                clip = clips.default(msg)
                await self._play_from_source(ctx, clip)

        connection = await aio_pika.connect(self._message_broker_url)
        async with connection:
            channel = await connection.channel()
            await channel.set_qos(prefetch_count=1)
            logs_exchange = await channel.declare_exchange('default',
                                                        aio_pika.ExchangeType.FANOUT)
            queue = await channel.declare_queue(exclusive=True)
            await queue.bind(logs_exchange)

            broker_tag = await queue.consume(on_message)

            async def go():
                await queue.cancel(broker_tag)
            self._on_chat_leave = go
            logging.info(f'Connection with message broker {self._message_broker_url} enstablished.')

            ngrok.set_auth_token(self._ngrok_token)
            tunnel = ngrok.connect(5672, 'tcp')
            hostname, port = self._get_hostname_and_port(tunnel.public_url)
            logging.info(f'Tunnel with ngrok set up. Check out {tunnel.api_url}')
            await ctx.send('\n'.join([f'Message queue address: {tunnel.public_url}',
                                      f'Run `python.exe client {hostname} {port}`']))
            await asyncio.Future()

    @commands.command()
    async def leave(self, ctx):
        """
        It lets the bot leave the chat, closing all pending connections.
        """
        if ctx.voice_client is not None:
            await ctx.voice_client.disconnect()
        ngrok.kill()
        if self._on_chat_leave is not None:
            await self._on_chat_leave()

    async def _play_from_source(self, ctx, name):
        """
        Utility method that allows to play the target audio file.
        """
        file = path.join(self._assets_path, f'{name}.mp3')
        try:
            source = await discord.FFmpegOpusAudio.from_probe(file)
            ctx.voice_client.play(source)
        except subprocess.CalledProcessError:
            logging.warning(f"Requested clip not found: {name}; path: {file}")
            ctx.send(f"Couldn't find clip named {name}.")
        except ClientException:
            logging.warning('Bot was already playing some audio.')

    def _get_hostname_and_port(self, public_url: str) -> Tuple[str, int]:
        matches = re.match('tcp:\\/\\/(([a-z0-9]+\\.)*[a-z0-9]+\\.[a-z0-9]+):(\\d+)', public_url)
        if matches is not None:
            return matches.group(1), matches.group(3)
        raise IndexError(f"Couldn't match ngrok URL against pattern: {public_url}")
