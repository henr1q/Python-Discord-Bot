import os
import discord
import asyncio
from discord.ext import commands
from youtube import YTDLSource
import random
from weather import get_coord, get_clima


TOKEN = os.environ.get('DISCORD_TOKEN')

client = discord.Client()
activity = discord.Activity(type=discord.ActivityType.listening, name="Vibin")
bot = commands.Bot(command_prefix="!", activity=activity, status=discord.Status.idle)


def g_embed(color, message, title=None):
    colors = {'red': 0x5c1313, 'green': 0x3AFF33, 'blue': 0x0e0e52, 'yellow': 0x99a140}

    if not title:
        embed = discord.Embed(description=message, color=colors[color])
        return embed
    else:
        embed = discord.Embed(title=title, description=message, color=colors[color])
        return embed

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
                embed = discord.Embed(title=f"Now Playing", description=f'{song.title}', color=0x3AFF33)
                asyncio.run_coroutine_threadsafe(ctx.send(embed=embed), self.bot.loop)
            except:
                asyncio.run_coroutine_threadsafe(ctx.send("No more songs in queue."), self.bot.loop)
                asyncio.run_coroutine_threadsafe(ctx.voice_client.disconnect(), self.bot.loop)


    @commands.command(name='play')
    async def play(self, ctx, *, url):
        """" Play songs and add to queue """
        player = None

        try:
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
        except:
            embed = g_embed('red', "Couldn't queue the song")
            await ctx.send(embed=embed)

        if player:
            self.queue.append(player)
            if not ctx.voice_client.is_playing():
                ctx.voice_client.play(player, after=lambda x: self.play_next(ctx, player))
                embed = g_embed('green', player.title, title='Now playing')
                await ctx.send(embed=embed)
            else:
                embed = g_embed('blue', f'Queued: {player.title}',)
                await ctx.send(embed=embed)


    @commands.command(name='playlist')
    async def playlist(self, ctx, *, url):
        """ Same as play, but for playlists """

        try:
            self.queue.extend(await YTDLSource.from_url(url, loop=self.bot.loop, stream=True, mode_playlist=True))
        except:
            embed = g_embed('red', "Couldn't queue this playlist")
            await ctx.send(embed=embed)

        if self.queue:
            if not ctx.voice_client.is_playing():
                ctx.voice_client.play(self.queue[0], after=lambda x: self.play_next(ctx, self.queue[0]))
                embed = g_embed('blue', f'Queued {len(self.queue)} Songs')
                await ctx.send(embed=embed)
                await ctx.send(embed=g_embed('blue', self.queue[0].title, title=f'Now playing'))
            else:
                # FIX THIS
                await ctx.send(f'IDK')


    @commands.command()
    async def stop(self, ctx):
        """ Stops and disconnects the bot from voice """

        await ctx.voice_client.disconnect()


    @commands.command(name='clear')
    async def clear(self, ctx):
        """ Clear the current queue """
        leng = len(self.queue)
        self.queue.clear()
        embed = g_embed('red', f'{leng} Songs removed from queue')

        await ctx.send(embed=embed)


    @commands.command(name='current')
    async def current(self, ctx):
        """Show the current song playing"""

        if self.queue:
            embed = discord.Embed(title=f"Now Playing", description=f'{self.queue[0].title}', color=0x3AFF33)
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"Bot isn't playing any song")


    @commands.command()
    async def pause(self, ctx):
        """ Pause the current song """
        if ctx.voice_client.is_playing():
            ctx.voice_client.pause()
        else:
            await ctx.send(f'Bot is not playing')

        await ctx.send(f'Paused')


    @commands.command()
    async def resume(self, ctx):
        """ Stops and disconnects the bot from voice """
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
            embed.set_thumbnail(url='https://i.imgur.com/A9O7sye.jpeg')
            title_queue.pop(0)

            for k, v in title_queue.items():
                embed.add_field(name=f'Position {k}', value=v, inline=False)

            await ctx.send(embed=embed)

        else:
            await ctx.send('Not songs in queue')


    @play.before_invoke
    @playlist.before_invoke
    async def ensure_voice(self, ctx):
        """" Ensure that the bot is connected to a voice channel before tries playing a song """
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
        embed = g_embed('yellow', f"Pong! {round(bot.latency * 1000)}ms")
        await ctx.send(embed=embed)


    @commands.command(name='erase')
    async def erase(self, ctx):
        """" Delete the last 100 messages on the channel that it is used """
        deleted = await ctx.channel.purge(limit=100)
        await ctx.send(f'Deleted {len(deleted)} message(s)')


class Clima(commands.Cog):

    def __init__(self, bot):
        self.bot = bot


    @commands.command(name='clima')
    async def on_message(self, ctx):
        msg = ctx.message.content

        city = msg[7:]

        if not city:
            embed = g_embed('red', 'City not provided')
            await ctx.send(embed=embed)
        else:
            coord = get_coord(city)

            if coord:
                lat = coord['lat']
                lon = coord['lon']
                name = coord['name']
                state = coord['state']
                clima = get_clima(lat, lon)
                graus = clima['temp']
                humidity = clima['humidity']
                desc = clima['desc']

                embed = discord.Embed(title=f'Weather in {name}, {state}', color=0x3254a8)
                embed.add_field(name='Description', value=desc.capitalize(), inline=False)
                embed.add_field(name='Temperature (C)', value=f'{graus} °C', inline=False)
                embed.add_field(name='Humidity', value=f'{humidity}%', inline=False)
                embed.set_thumbnail(url='https://images-na.ssl-images-amazon.com/images/I/51ljr9z1+RL.png')
                await ctx.send(embed=embed)

            else:
                embed = g_embed('red', 'A error occurred')
                await ctx.send(embed=embed)



@bot.event
async def on_ready():
    print(f'{bot.user} is ON!')


bot.add_cog(Media(bot))
bot.add_cog(Utility(bot))
bot.add_cog(Clima(bot))
bot.run(TOKEN)





