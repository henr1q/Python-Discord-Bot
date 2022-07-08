import os
import discord
import random
import asyncio
from discord.ext import commands
from youtube import YTDLSource
import random


TOKEN = os.environ.get('DISCORD_TOKEN')

client = discord.Client()
bot = commands.Bot(command_prefix='!')

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
        player = None

        try:
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
        except:
            await ctx.send("Couldn't queue the song")

        if player:
            self.queue.append(player)
            if not ctx.voice_client.is_playing():
                ctx.voice_client.play(player, after=lambda x: self.play_next(ctx, player))
                await ctx.send(f'Now playing: {player.title}')
            else:
                await ctx.send(f'Queued: {player.title} ')


    @commands.command(name='playlist')
    async def playlist(self, ctx, *, url):

        try:
            self.queue = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True, mode_playlist=True)
        except:
            await ctx.send("Couldn't queue this playlist")

        if self.queue:
            if not ctx.voice_client.is_playing():
                ctx.voice_client.play(self.queue[0], after=lambda x: self.play_next(ctx, self.queue[0]))
                await ctx.send(f'Queued {len(self.queue)} Songs')
                await ctx.send(f'Now playing: {self.queue[0].title}')
            else:
                await ctx.send(f'Queued: {self.queue[0].title} ')


    @commands.command()
    async def stop(self, ctx):
        """Stops and disconnects the bot from voice"""

        await ctx.voice_client.disconnect()


    @commands.command(name='clear')
    async def clear(self, ctx):
        """Clear the current queue"""
        leng = len(self.queue)
        self.queue.clear()

        await ctx.send(f'{leng} Songs removed from queue')


    @commands.command(name='current')
    async def current(self, ctx):
        """Show the current song playing"""

        await ctx.send(f'Current song is: {self.queue[0].title}')


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


    @commands.command(name='skip', aliases=['SKIP', 'Skip'])
    async def skip(self, ctx):
        """" Skip current song """

        if self.queue:
            ctx.voice_client.pause()
            await ctx.send(f'{self.queue[0].title} skipped')
            self.play_next(ctx, self.queue[0])
        else:
            await ctx.send('Not playing any song')


    @commands.command(name='queue')
    async def show_queue(self, ctx):
        """" Show the current queue """

        if self.queue:
            title_queue = {index: item.title for index, item in enumerate(self.queue)}
            embed = discord.Embed(title=f"Music Queue", color=0xFF5733)
            title_queue.pop(1)

            for k, v in title_queue.items():
                embed.add_field(name=f'Position {k}', value=v, inline=False)

            await ctx.send(embed=embed)

        else:
            await ctx.send('Not songs in queue')


    @play.before_invoke
    @playlist.before_invoke
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


    @commands.command(name='join', aliases=['Join', 'JOIN'])
    async def join(self, ctx, *, channel: discord.VoiceChannel = None):
        """Join the channel provided, if none join author channel"""

        if ctx.voice_client is not None and channel is not None:
            return await ctx.voice_client.move_to(channel)
        else:
            await ctx.author.voice.channel.connect()


    @commands.command(name='rad')
    async def on_message(self, ctx):

        name = str(ctx.message.author)
        response = random.randint(1, 100)
        await ctx.send(f'{name} tem {response}% de chance de pegar radiante')


    @commands.command(name='ping')
    async def ping(self, ctx):
        await ctx.send(f"Pong! {round(bot.latency * 1000)}ms")


    @commands.command(name='erase')
    async def erase(self, ctx):
        deleted = await ctx.channel.purge(limit=100)
        await ctx.send(f'Deleted {len(deleted)} message(s)')


@bot.event
async def on_ready():
    activity_type = discord.ActivityType.listening
    await bot.change_presence(activity=discord.Activity(type=activity_type, name="Vibin"))
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')


bot.add_cog(Media(bot))
bot.add_cog(Utility(bot))
bot.run(TOKEN)





