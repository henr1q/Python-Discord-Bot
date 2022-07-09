import youtube_dl
import asyncio
import discord

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
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': ['-vn', '-sn', '-dn', '-ignore_unknown']
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
    async def from_url(cls, url, *, loop=None, stream=False, mode_playlist=None):
        loop = loop or asyncio.get_event_loop()
        playlist_output = []
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))


        if 'entries' in data:
            playlist = data['entries']
            data = data['entries'][0]
            if mode_playlist:
                for i, item in enumerate(playlist):
                    url = playlist[i]['url']
                    playlist_output.append(cls(discord.FFmpegPCMAudio(url, **ffmpeg_options), data=playlist[i]))

                return playlist_output



        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)
