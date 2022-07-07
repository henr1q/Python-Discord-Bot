# bot.py
import functools
import os
import discord
import random
import youtube_dl
import asyncio
from discord import channel
from discord.ext import commands
from discord import FFmpegPCMAudio
from youtube_dl import YoutubeDL

TOKEN = os.environ.get('DISCORD_TOKEN')

client = discord.Client()
bot = commands.Bot(command_prefix='!')


youtube_dl.utils.bug_reports_message = lambda: ''


ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes
}


ffmpeg_options = {
    'options': '-vn',
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):

    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')


    def __getitem__(self, item: str):
        """Allows us to access attributes similar to a dict.
        This is only useful when you are NOT downloading.
        """
        return self.__getattribute__(item)


    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)


class Media(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.queue = []


    def play_next(self, ctx, player):
        if len(self.queue) >= 1:
            self.queue.pop(0)

            try:
                song = self.queue[0]
                ctx.voice_client.play(song, after=lambda e: self.play_next(ctx, player))
            except:
                asyncio.run_coroutine_threadsafe(ctx.send("No more songs in queue."), self.bot.loop)
                asyncio.run_coroutine_threadsafe(ctx.voice_client.disconnect(), self.bot.loop)


    @commands.command(name='play')
    async def play(self, ctx, *, url):
        player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
        self.queue.append(player)
        if not ctx.voice_client.is_playing():
            ctx.voice_client.play(player, after=lambda x: self.play_next(ctx, player))
            await ctx.send(f'Now playing: {player.title}')
        else:
            await ctx.send(f'Queued: {player.title} ')


    @commands.command()
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""

        await ctx.voice_client.disconnect()


    @commands.command()
    async def pause(self, ctx):
        """Stops and disconnects the bot from voice"""
        if ctx.voice_client.is_playing():
            ctx.voice_client.pause()
        else:
            await ctx.send(f'Bot is not playing')

        await ctx.send(f'Paused')


    @commands.command()
    async def resume(self, ctx):
        """Stops and disconnects the bot from voice"""
        if ctx.voice_client.is_paused():
            ctx.voice_client.resume()
        else:
            await ctx.send(f'Bot is not paused')

        await ctx.send(f'Resumed')


    @commands.command(name='skip')
    async def skip(self, ctx):
        """" Skip current song """

        if self.queue:
            ctx.voice_client.pause()
            self.play_next(ctx, self.queue[0])
            await ctx.send(f'{self.queue[0].title} skipped')
        else:
            await ctx.send('Not playing any song')


    @commands.command(name='show')
    async def show_queue(self, ctx):
        """" Show the current queue """

        if self.queue:
            title_queue = {index + 1: item.title for index, item in enumerate(self.queue)}
            embed = discord.Embed(title="Song Queue", color=0xFF5733)

            for k, v in title_queue.items():
                embed.add_field(name=f'Position {k}', value=v, inline=False)

            await ctx.send(embed=embed)

        else:
            await ctx.send('Not songs in queue')


    @play.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")


class Utility(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @commands.command(name='join')
    async def join(self, ctx, *, channel: discord.VoiceChannel = None):
        """Join the channel provided, if none join author channel"""

        if ctx.voice_client is not None and channel is not None:
            return await ctx.voice_client.move_to(channel)
        else:
            await ctx.author.voice.channel.connect()


    @commands.command(name='99')
    async def on_message(self, ctx):

        brooklyn_99_quotes = [
            'I\'m the human form of the 💯 emoji.',
            'Bingpot!',
            'Cool. Cool cool cool cool cool cool cool, '
            'no doubt no doubt no doubt no doubt.'
        ]

        response = random.choice(brooklyn_99_quotes)
        await ctx.send(response)


    @commands.command(name='ping')
    async def ping(self, ctx):
        await ctx.send(f"Pong! {round(bot.latency * 1000)}ms")


    @commands.command(name='clear')
    async def clear(self, ctx):
        deleted = await ctx.channel.purge(limit=100)
        await ctx.send(f'Deleted {len(deleted)} message(s)')


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')


bot.add_cog(Media(bot))
bot.add_cog(Utility(bot))
bot.run(TOKEN)





