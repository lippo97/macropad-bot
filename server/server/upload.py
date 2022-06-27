import os
import ffmpeg
from os import path
from discord.ext import commands
from discord.ext.commands.bot import Bot

class Upload(commands.Cog):
    def __init__(self, bot: Bot, assets_path: str):
        self.bot = bot
        self._assets_path = assets_path
        self._success_gif = 'https://images-wixmp-ed30a86b8c4ca887773594c2.wixmp.com/f/feb4a7b1-cb6a-45d1-a930-8abbc46e14f2/d5e6xfh-27193a15-234b-4a61-80fd-2f67d5d8d2d1.gif?token=eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1cm46YXBwOjdlMGQxODg5ODIyNjQzNzNhNWYwZDQxNWVhMGQyNmUwIiwiaXNzIjoidXJuOmFwcDo3ZTBkMTg4OTgyMjY0MzczYTVmMGQ0MTVlYTBkMjZlMCIsIm9iaiI6W1t7InBhdGgiOiJcL2ZcL2ZlYjRhN2IxLWNiNmEtNDVkMS1hOTMwLThhYmJjNDZlMTRmMlwvZDVlNnhmaC0yNzE5M2ExNS0yMzRiLTRhNjEtODBmZC0yZjY3ZDVkOGQyZDEuZ2lmIn1dXSwiYXVkIjpbInVybjpzZXJ2aWNlOmZpbGUuZG93bmxvYWQiXX0.t_W8moL4mgLNNI9l4Z_0mmlHKc6fucUbxW2IBEHpvBk'
        self._loading_gif = 'https://media.giphy.com/media/zIwexiqyBDeI8UP2PO/giphy.gif'
        self._sad_gif = 'https://pa1.narvii.com/5802/9464297bcf8a7ceedacd6fd424d80b799af19d69_00.gif'

    @commands.command()
    async def add(self, ctx, name: str):
        '''Aggiungi una nuova clip audio.'''
        if len(ctx.message.attachments) != 1:
            return await ctx.reply('Devi caricare una clip audio.')
        if not self._check_name(name):
            return await ctx.reply('Il nome deve contenere solo lettere minuscole, numeri e underscore.')

        filepath = self._make_path(name)
        if os.path.exists(filepath):
            return await ctx.reply(f'Esiste già una clip nominata **{name}**.')
        attachment = ctx.message.attachments[0]
        if attachment.size > 5 * (10**6):
            return await ctx.reply('La dimensione massima della clip è di 5MB.')
        if attachment.content_type == 'audio/mpeg':
            await attachment.save(self._make_path(name))
            await ctx.reply(self._success_gif)
            await ctx.reply(f'Clip **{name}** salvata con successo.')
        elif attachment.content_type == 'audio/x-wav':
            message = await ctx.reply(self._loading_gif)
            bytes = (await attachment.to_file()).fp
            ffmpeg_process = (
                ffmpeg
                .input('pipe:', f='wav')
                .output(self._make_path(name))
                .run_async(pipe_stdin=True)
            )
            ffmpeg_process.stdin.write(bytes.read())
            ffmpeg_process.stdin.close()
            ffmpeg_process.wait()
            await message.edit(content=self._success_gif)
            await ctx.reply(f'Clip **{name}** salvata con successo.')

    @commands.command()
    async def remove(self, ctx, name: str):
        '''Rimuovi una clip audio esistente.'''
        filepath = self._make_path(name)
        if name is not None and name != "" and os.path.exists(filepath):
            os.remove(filepath)
            return await ctx.send('Clip eliminata con successo.')
        await ctx.send(f'Clip **{name}** non trovata.')

    @commands.command()
    async def rename(self, ctx, source: str, dest: str):
        source_path = self._make_path(source)
        dest_path = self._make_path(dest)
        if not os.path.exists(source_path):
            return await ctx.send(f'Clip **{source}** non trovata.')
        if os.path.exists(dest_path):
            return await ctx.send(f'Esiste già una clip nominata **{dest}**.')

        os.rename(source_path, dest_path)
        await ctx.send('Clip rinominata con successo.')

    def _make_path(self, name):
        return os.path.join(self._assets_path, f'{name}.mp3')

    def _check_name(self, name: str) -> bool:
        import re
        pattern = '^[a-z0-9]+(_[a-z0-9]+)*(/[a-z0-9]+(_[a-z0-9]+)*)*$'
        return re.match(pattern, name) != None
