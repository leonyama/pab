import discord
from discord.ext import commands
import yt_dlp as youtube_dl

class Voice(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.queue = []
        self.is_playing = False
        self.current_song = None

    async def join_vc(self, ctx):
        if not ctx.author.voice:
            await ctx.send("先にボイスチャンネルに接続してください。", ephemeral=True)
            return None
        channel = ctx.author.voice.channel
        return await channel.connect()

    async def play_next(self, ctx, vc):
        if not self.queue:
            self.is_playing = False
            return

        self.current_song = self.queue.pop(0)
        ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'extractaudio': True,
            'audioquality': 1,
            'outtmpl': 'downloads/%(id)s.%(ext)s',
        }

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(self.current_song, download=False)
                url2 = info['formats'][0]['url']
                vc.play(discord.FFmpegPCMAudio(url2, before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5"), after=lambda e: self.bot.loop.create_task(self.play_next(ctx, vc)))
                await ctx.send(f"再生中: {info['title']}", ephemeral=True)
                self.is_playing = True
            except Exception as e:
                await ctx.send(f"再生中にエラーが発生しました: {str(e)}", ephemeral=True)

    @commands.command(name="play")
    async def play(self, ctx, url: str):
        if not ctx.voice_client:
            vc = await self.join_vc(ctx)
            if vc is None:
                return
        else:
            vc = ctx.voice_client

        if self.is_playing:
            self.queue.append(url)
            await ctx.send(f"曲がキューに追加されました: {url}", ephemeral=True)
        else:
            self.queue.append(url)
            await self.play_next(ctx, vc)

    @commands.command(name="leave")
    async def leave(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("ボイスチャンネルから退出しました。", ephemeral=True)
        else:
            await ctx.send("ボイスチャンネルに参加していません。", ephemeral=True)

    @commands.command(name="stop")
    async def stop(self, ctx):
        if ctx.voice_client and self.is_playing:
            ctx.voice_client.stop()
            self.is_playing = False
            await ctx.send("再生中の音楽を停止しました。", ephemeral=True)
        else:
            await ctx.send("現在再生中の音楽はありません。", ephemeral=True)

    @commands.command(name="skip")
    async def skip(self, ctx):
        if ctx.voice_client and self.is_playing:
            ctx.voice_client.stop()
            await self.play_next(ctx, ctx.voice_client)
        else:
            await ctx.send("再生中の音楽がありません。", ephemeral=True)

    @commands.command(name="list")
    async def list_queue(self, ctx):
        if not self.queue:
            await ctx.send("キューに音楽はありません。", ephemeral=True)
        else:
            queue_list = "\n".join(self.queue)
            await ctx.send(f"現在のキュー:\n{queue_list}", ephemeral=True)

        if not self.queue:
            await ctx.send("再生する曲がありません。", ephemeral=True)

async def setup(bot):
    await bot.add_cog(Voice(bot))