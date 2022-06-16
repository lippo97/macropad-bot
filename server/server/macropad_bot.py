import logging
from typing import Tuple
import discord
import aio_pika
import asyncio
import re
from os import name, path, listdir
from os.path import isfile
from discord import VoiceState, VoiceClient
from discord.ext.commands.bot import Bot, Context
from discord.errors import ClientException
from discord.ext import commands
from pyngrok import ngrok
import subprocess


class MacroPad(commands.Cog):
    def __init__(self, bot: Bot, assets_path: str, ngrok_token: str, message_broker: Tuple[str, int]):
        self.bot = bot
        self._on_chat_leave = None
        self._connection_message = None
        self._assets_path = assets_path
        self._ngrok_token = ngrok_token
        self._message_broker_hostname, self._message_broker_port = message_broker
        self._message_broker_url = f'amqp://{self._message_broker_hostname}:{self._message_broker_port}'

    @commands.command()
    async def list(self, ctx):
        """
        Lists all the playable audio clips.
        """
        files = [f'**{f.removesuffix(".mp3")}**' for f in listdir(self._assets_path)
                if isfile(path.join(self._assets_path, f)) and f.endswith('.mp3')]
        await ctx.send("L'elenco dei suoni disponibili è il seguente: \n{}".format("\n".join(files)))

    @commands.command()
    async def play(self, ctx, clip: str):
        """
        Plays the selected audio clip.
        """
        await self._play_from_source(ctx, clip)

    @commands.Cog.listener()
    async def on_ready(self):
        print(f'Logged in as {self.bot.user}.')
        await self._set_idle_activity()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        channel_ids = [ x.channel.id for x in self.bot.voice_clients ]
        if before.channel is not None and before.channel.id in channel_ids:
            before_channel_id = before.channel.id
            after_channel_id = after.channel.id if after.channel is not None else None
            if before_channel_id != after_channel_id:
                voice_client = next(filter(lambda x: x.channel.id == before_channel_id, self.bot.voice_clients))
                if len(voice_client.channel.members) == 1 and voice_client.channel.members[0].id == self.bot.user.id:
                    logging.info('No one left in channel, leaving.')
                    await self._handle_leave(voice_client)

    @commands.command()
    async def client(self, ctx: Context):
        """
        Restituisce l'ultima versione del macropad-client.
        """
        await ctx.reply(file=discord.File(path.join(self._assets_path, "macropad-client.zip")))

    @commands.command()
    async def join(self, ctx):
        """
        Chiedi al bot di partecipare alla tua chat vocale.
        """
        # When that happens this process enstablishes a connection with the message
        # broker in order to receive events.
        # It also creates an ngrok process exposing the message broker with the chat.
        if ctx.author.voice is None:
            return await ctx.reply("Devi essere in un canale vocale.")
        channel = ctx.author.voice.channel
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)
        await channel.connect()

        async def on_message(message):
            async with message.process():
                msg = message.body.decode('utf-8')
                await self._parse_message(ctx, msg)

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
            tunnel = ngrok.connect(f'{self._message_broker_hostname}:{self._message_broker_port}', 'tcp')
            hostname, port = self._get_hostname_and_port(tunnel.public_url)
            logging.info(f'Tunnel with ngrok set up. Check out {tunnel.api_url}')
            self._connection_message = await ctx.send(f'Per connetterti apri una PowerShell e lancia il seguente comando `.\\macropad-client.exe {hostname} {port}`')
            await self.bot.change_presence(status=discord.Status.online)
            await asyncio.Future()

    @commands.command()
    async def leave(self, ctx):
        """
        Chiedi al bot di uscire dalla chat vocale.
        """
        await self._handle_leave(ctx.voice_client)

    async def _handle_leave(self, voice_client: VoiceClient):
        if voice_client is not None:
            await voice_client.disconnect()
        ngrok.kill()
        if self._on_chat_leave is not None:
            await self._on_chat_leave()
        if self._connection_message is not None:
            await self._connection_message.edit(content=f'~~{self._connection_message.content}~~')
            self._connection_message = None
        await self._set_idle_activity()

    async def _set_idle_activity(self):
        activity = discord.Activity(type=discord.ActivityType.watching, name="Brizz94")
        await self.bot.change_presence(status=discord.Status.idle, activity=activity)

    async def _parse_message(self, ctx, msg: str) -> None:
        match msg.split('/'):
            case ['play', clip]:
                await self._play_from_source(ctx, clip)
            case _:
                logging.warning(f"Received command {msg}, but couldn't match it against any pattern.")

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
            ctx.reply(f"Non ho trovato nessuna clip chiamata {name}.")
        except ClientException:
            logging.warning('Bot was already playing some audio.')

    def _get_hostname_and_port(self, public_url: str) -> Tuple[str, int]:
        matches = re.match('tcp:\\/\\/(([a-z0-9]+\\.)*[a-z0-9]+\\.[a-z0-9]+):(\\d+)', public_url)
        if matches is not None:
            return matches.group(1), matches.group(3)
        raise IndexError(f"Couldn't match ngrok URL against pattern: {public_url}")
