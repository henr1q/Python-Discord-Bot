import os
import discord
import asyncio
from discord.ext import commands
from youtube import YTDLSource
import random
import time
import aiohttp
from weather import get_coord, get_clima

# TODO: FIX DOCSTRINGS

TOKEN = os.environ.get('DISCORD_TOKEN')
CAT_TOKEN = os.environ.get('CAT_TOKEN')

client = discord.Client()
activity = discord.Activity(type=discord.ActivityType.listening, name="Vibin")
bot = commands.Bot(command_prefix="!", activity=activity, help_command=None)
prefix = '!'

def g_embed(color, message, title=None):
    """ Function to help generate embeds """

    colors = {'red': 0x5c1313, 'green': 0x3AFF33, 'blue': 0x0e0e52, 'yellow': 0x99a140}

    if not title:
        embed = discord.Embed(description=message, color=colors[color])
        return embed
    else:
        embed = discord.Embed(title=title, description=message, color=colors[color])
        return embed

class Media(commands.Cog):
    """ Media related commands """

    def __init__(self, bot):
        self.bot = bot
        self.guilds = {}
        self.queue = []


    def play_next(self, ctx, player):
        """ Function to play next songs and run queue as loop """

        server = ctx.guild.id

        if len(self.guilds[server]):
            self.guilds[server].pop(0)

            try:
                song = self.guilds[server][0]
                ctx.voice_client.play(song, after=lambda e: self.play_next(ctx, player))
                embed = discord.Embed(title=f"Now Playing", description=f'{song.title}', color=0x3AFF33)
                asyncio.run_coroutine_threadsafe(ctx.send(embed=embed), self.bot.loop)
            except:
                embed = g_embed('blue', message="No more songs in queue.")
                asyncio.run_coroutine_threadsafe(ctx.send(embed=embed), self.bot.loop)
                if ctx.voice_client:
                    asyncio.run_coroutine_threadsafe(ctx.voice_client.disconnect(), self.bot.loop)


    @commands.command(name='play', aliases=['PLAY', 'Play'])
    async def play(self, ctx, *, url):
        """ Play songs and add to queue. Usage: play <URL or Search query>"""
        player = None
        server = ctx.guild.id

        try:
            player = await YTDLSource.from_url(url, loop=self.bot.loop, stream=True)
        except:
            embed = g_embed('red', "Couldn't queue the song")
            await ctx.send(embed=embed)

        if server not in self.guilds:
            self.guilds[server] = []

        if player:
            self.guilds[server].append(player)
            if not ctx.voice_client.is_playing():
                ctx.voice_client.play(player, after=lambda x: self.play_next(ctx, player))
                embed = g_embed('green', player.title, title='Now playing')
                await ctx.send(embed=embed)
            else:
                embed = g_embed('blue', f'Queued: {player.title}',)
                await ctx.send(embed=embed)


    # TODO: fix this for guilds
    @commands.command(name='playlist')
    async def playlist(self, ctx, *, url):
        """ Same as play, but for playlists. Usage: playlist <playlist URL> """

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

        server = ctx.guild.id
        if len(self.guilds[server]):
            self.guilds[server].clear()


        await ctx.voice_client.disconnect()


    @commands.command(name='clear')
    async def clear(self, ctx):
        """ Clear the current queue """
        server = ctx.guild.id
        leng = len(self.guilds[server])
        if leng:
            self.guilds[server].clear()
            embed = g_embed('red', f'{leng} Songs removed from queue')
        else:
            embed = g_embed('red', f'{leng} No songs in queue')

        await ctx.send(embed=embed)


    @commands.command(name='now', aliases=['Now', 'current'])
    async def current(self, ctx):
        """ Show the current song playing"""

        server = ctx.guild.id

        if len(self.guilds[server]):
            embed = discord.Embed(title=f"Now Playing", description=f'{self.guilds[server][0].title}', color=0x3AFF33)
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
        """ Skip current song """
        server = ctx.guild.id

        if len(self.guilds[server]):
            ctx.voice_client.pause()
            # TODO: embed this
            await ctx.send(f'{self.guilds[server][0].title} skipped')
            self.play_next(ctx, self.guilds[server][0])
        else:
            await ctx.send('Not playing any song')


    @commands.command(name='queue')
    async def show_queue(self, ctx):
        """ Show the current queue """

        server = ctx.guild.id

        if len(self.guilds[server]) > 1:
            title_queue = {index: item.title for index, item in enumerate(self.guilds[server])}
            embed = discord.Embed(title=f"Music Queue", color=0xFF5733)
            embed.set_thumbnail(url='https://i.imgur.com/A9O7sye.jpeg')
            title_queue.pop(0)

            for k, v in title_queue.items():
                embed.add_field(name=f'Position {k}', value=v, inline=False)

            await ctx.send(embed=embed)

        else:
            # TODO: EMBED THIS
            await ctx.send('Not songs in queue')


    @play.before_invoke
    @playlist.before_invoke
    async def ensure_voice(self, ctx):
        """ Ensure that the bot is connected to a voice channel before tries playing a song """
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")


class Utility(commands.Cog):
    """ Utility related commands """

    def __init__(self, bot):
        self.bot = bot


    @commands.command(name='join', aliases=['Join', 'JOIN'])
    async def join(self, ctx, *, channel: discord.VoiceChannel = None):
        """Join the channel provided, if none join author channel . Usage: Join <optional:voice channel name>"""

        if ctx.voice_client is not None and channel is not None:
            return await ctx.voice_client.move_to(channel)
        else:
            await ctx.author.voice.channel.connect()


    @commands.command(name='ping')
    async def ping(self, ctx):
        embed = g_embed('yellow', f"Pong! {round(self.bot.latency * 1000)}ms")
        await ctx.send(embed=embed)


    @commands.command(name='erase')
    async def erase(self, ctx):
        """" Delete the last 100 messages on the channel that it is used """
        deleted = await ctx.channel.purge(limit=100)
        await ctx.send(f'Deleted {len(deleted)} message(s)')


class Clima(commands.Cog):
    """ Clima related commands """

    def __init__(self, bot):
        self.bot = bot


    @commands.command(name='clima')
    async def on_message(self, ctx):
        """ Return the current weather. usage: !clima <city name> """

        msg = ctx.message.content
        city = msg[7:]

        if not city:
            embed = g_embed('red', 'City not provided')
            await ctx.send(embed=embed)
        else:
            coord = await get_coord(city)
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
                embed = g_embed('red', 'Invalid city name')
                await ctx.send(embed=embed)


class Fun(commands.Cog):
    """ Fun related commands """

    def __init__(self, bot):
        self.bot = bot


    @commands.command(name='cat')
    async def cat(self, ctx):
        """ Generate random cat imgs/gifs. """

        url = 'https://api.thecatapi.com/v1/images/search'

        async with aiohttp.ClientSession() as session:
            response = await session.get(url, headers={"x-api-key": CAT_TOKEN}, ssl=False)
            data = await response.json()
            img = data[0]['url']

        await ctx.send(img)


    @commands.command(name='dog')
    async def dog(self, ctx):
        """ Generate random dogs imgs/gifs """

        url = 'https://dog.ceo/api/breeds/image/random'

        async with aiohttp.ClientSession() as session:
            response = await session.get(url, ssl=False)
            data = await response.json()
            img = data['message']

        await ctx.send(img)


class Help(commands.Cog):
    """ Help related commands """

    def __init__(self, bot):
        self.bot = bot


    @commands.command(name='help', aliases=['Help', 'HELP'])
    async def show_help(self, ctx, *args):
        """ Show all commands. Usage: help <optional:command name> """

        prefix = '!'

        embed = discord.Embed(title='Your guide', color=0x32a875, description=f'To see the usage of a command, use: {prefix}help <command name>')
        cogs_names = [cog for cog in self.bot.cogs]
        cogs = [bot.get_cog(cog) for cog in cogs_names]
        dict_from_list = dict(zip(cogs, cogs_names))

        cog_commands = {dict_from_list[cog]:[f'{prefix}{c.name}' for c in cog.get_commands()] for cog in cogs}

        for module, coms in cog_commands.items():
            embed.add_field(name=f'`{module}`', value=f'{",  ".join(coms)}', inline=False)


        if len(args) == 1:
            embed = discord.Embed(title=f'{prefix}{args[0]}', description=f'{self.bot.get_command(args[0]).help}', color=0x0388fc)


        await ctx.send(embed=embed)




@bot.event
async def on_ready():
    print(f'{bot.user} is ON!')


bot.add_cog(Media(bot))
bot.add_cog(Utility(bot))
bot.add_cog(Clima(bot))
bot.add_cog(Fun(bot))
bot.add_cog(Help(bot))
bot.run(TOKEN)





