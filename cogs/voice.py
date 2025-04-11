import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import yt_dlp
import re
# import spotipy
# from spotipy.oauth2 import SpotifyClientCredentials
import os
import config

YOUTUBE_URL_PATTERN = r'(?:https?://)?(?:www\.)?(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]+)'
# SPOTIFY_URL_PATTERN = r'(?:https?://)?(?:open\.spotify\.com/)(?:track/)([a-zA-Z0-9]+)'

class MusicPlayer:
    def __init__(self, bot):
        self.bot = bot
        self.voice_clients = {}
        self.queues = {}
        self.now_playing = {}

        '''
        try:
            self.spotify_client_id = os.getenv('SPOTIFY_CLIENT_ID')
            self.spotify_client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
            if self.spotify_client_id and self.spotify_client_secret:
                self.spotify = spotipy.Spotify(
                    client_credentials_manager=SpotifyClientCredentials(
                        client_id=self.spotify_client_id,
                        client_secret=self.spotify_client_secret
                    )
                )
            else:
                self.spotify = None
        except Exception as e:
            print(f"Spotify API初期化エラー: {e}")
            self.spotify = None
        '''
        self.spotify = None

        self.ydl_opts = {
            'format': 'bestaudio/best',
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        }

    def get_queue(self, guild_id):
        if guild_id not in self.queues:
            self.queues[guild_id] = []
        return self.queues[guild_id]

    async def play_next(self, guild_id):
        queue = self.get_queue(guild_id)
        if not queue or guild_id not in self.voice_clients:
            self.now_playing[guild_id] = None
            return

        next_song = queue.pop(0)
        self.now_playing[guild_id] = next_song
        
        voice_client = self.voice_clients[guild_id]
        if voice_client.is_playing():
            voice_client.stop()

        source = discord.FFmpegPCMAudio(next_song['url'], options='-vn')
        voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(
            self.play_next(guild_id), self.bot.loop).result())

        if 'text_channel' in next_song:
            await next_song['text_channel'].send(f"再生中: {next_song['title']}")

    async def add_to_queue(self, ctx, url, is_search=False):
        guild_id = ctx.guild.id
        queue = self.get_queue(guild_id)
        
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                if is_search:
                    info = ydl.extract_info(f"ytsearch:{url}", download=False)['entries'][0]
                else:
                    info = ydl.extract_info(url, download=False)
                
                song_info = {
                    'url': info['url'],
                    'title': info['title'],
                    'duration': info['duration'],
                    'text_channel': ctx.channel
                }
                
                queue.append(song_info)
                await ctx.send(f"キューに追加: {song_info['title']}")

                if guild_id in self.voice_clients and not self.voice_clients[guild_id].is_playing():
                    await self.play_next(guild_id)
                
                return True
        except Exception as e:
            await ctx.send(f"曲の追加に失敗しました: {e}")
            return False

    '''
    async def process_spotify(self, ctx, url):
        if not self.spotify:
            await ctx.send("Spotify APIが設定されていません。")
            return False
            
        try:
            match = re.search(SPOTIFY_URL_PATTERN, url)
            if match:
                track_id = match.group(1)
                track = self.spotify.track(track_id)
                
                artist = track['artists'][0]['name']
                song_name = track['name']
                search_query = f"{artist} - {song_name}"
                
                await ctx.send(f"Spotifyトラック `{search_query}` をYouTubeで検索中...")
                return await self.add_to_queue(ctx, search_query, is_search=True)
            else:
                await ctx.send("有効なSpotify URLではありません。")
                return False
        except Exception as e:
            await ctx.send(f"Spotifyトラックの処理に失敗しました: {e}")
            return False
    '''


class VoiceCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.music_player = MusicPlayer(bot)
        
    @commands.command(name="join")
    async def join(self, ctx):
        """ボイスチャンネルに参加します"""
        if not ctx.author.voice:
            await ctx.send("ボイスチャンネルに接続してください")
            return
        
        channel = ctx.author.voice.channel

        if ctx.guild.id in self.music_player.voice_clients:
            await self.music_player.voice_clients[ctx.guild.id].move_to(channel)
            await ctx.send(f"{channel.name}に移動しました")
            return

        try:
            voice_client = await channel.connect()
            self.music_player.voice_clients[ctx.guild.id] = voice_client
            await ctx.send(f"{channel.name}に接続しました")
        except Exception as e:
            await ctx.send(f"エラーが発生しました: {e}")

    @commands.command(name="leave")
    async def leave(self, ctx):
        """ボイスチャンネルから退出します"""
        if ctx.guild.id not in self.music_player.voice_clients:
            await ctx.send("ボイスチャンネルに接続していません")
            return
        
        await self.music_player.voice_clients[ctx.guild.id].disconnect()
        del self.music_player.voice_clients[ctx.guild.id]
        if ctx.guild.id in self.music_player.queues:
            self.music_player.queues[ctx.guild.id] = []
        if ctx.guild.id in self.music_player.now_playing:
            self.music_player.now_playing[ctx.guild.id] = None
        await ctx.send("ボイスチャンネルから退出しました")

    @commands.command(name="music")
    async def music(self, ctx, *, query):
        """音楽を再生します (YouTube URLまたは検索語句)"""
        if not ctx.author.voice:
            await ctx.send("ボイスチャンネルに接続してください")
            return

        if ctx.guild.id not in self.music_player.voice_clients:
            await self.join(ctx)

        youtube_match = re.search(YOUTUBE_URL_PATTERN, query)
        # spotify_match = re.search(SPOTIFY_URL_PATTERN, query)
        
        '''
        if spotify_match:
            # SpotifyのURLの場合
            await self.music_player.process_spotify(ctx, query)
        elif youtube_match:
            # YouTubeのURLの場合
            await self.music_player.add_to_queue(ctx, query)
        else:
            # 検索語句として扱う
            await ctx.send(f"「{query}」をYouTubeで検索中...")
            await self.music_player.add_to_queue(ctx, query, is_search=True)
        '''
        
        if youtube_match:
            await self.music_player.add_to_queue(ctx, query)
        else:
            await ctx.send(f"「{query}」をYouTubeで検索中...")
            await self.music_player.add_to_queue(ctx, query, is_search=True)

    @commands.command(name="skip")
    async def skip(self, ctx):
        """現在再生中の曲をスキップします"""
        if ctx.guild.id not in self.music_player.voice_clients:
            await ctx.send("ボイスチャンネルに接続していません")
            return
            
        voice_client = self.music_player.voice_clients[ctx.guild.id]
        if voice_client.is_playing():
            voice_client.stop()
            await ctx.send("曲をスキップしました")
        else:
            await ctx.send("現在再生中の曲はありません")

    @commands.command(name="queue")
    async def queue(self, ctx):
        """現在のキューを表示します"""
        guild_id = ctx.guild.id
        if guild_id not in self.music_player.queues or not self.music_player.queues[guild_id]:
            await ctx.send("キューに曲はありません")
            return
            
        queue = self.music_player.queues[guild_id]
        now_playing = self.music_player.now_playing.get(guild_id)
        
        embed = discord.Embed(title="音楽キュー", color=discord.Color.blue())
        
        if now_playing:
            embed.add_field(name="再生中", value=f"**{now_playing['title']}**", inline=False)
            
        if queue:
            queue_text = ""
            for i, song in enumerate(queue[:10], 1):
                queue_text += f"{i}. {song['title']}\n"
                
            if len(queue) > 10:
                queue_text += f"...他 {len(queue) - 10} 曲"
                
            embed.add_field(name="次の曲", value=queue_text or "なし", inline=False)
            
        await ctx.send(embed=embed)

    @commands.command(name="pause")
    async def pause(self, ctx):
        """音楽を一時停止します"""
        if ctx.guild.id not in self.music_player.voice_clients:
            await ctx.send("ボイスチャンネルに接続していません")
            return
            
        voice_client = self.music_player.voice_clients[ctx.guild.id]
        if voice_client.is_playing():
            voice_client.pause()
            await ctx.send("一時停止しました")
        else:
            await ctx.send("現在再生中の曲はありません")

    @commands.command(name="resume")
    async def resume(self, ctx):
        """一時停止した音楽を再開します"""
        if ctx.guild.id not in self.music_player.voice_clients:
            await ctx.send("ボイスチャンネルに接続していません")
            return
            
        voice_client = self.music_player.voice_clients[ctx.guild.id]
        if voice_client.is_paused():
            voice_client.resume()
            await ctx.send("再生を再開しました")
        else:
            await ctx.send("一時停止している曲はありません")

    @app_commands.command(name="join", description="ボイスチャンネルに参加します")
    async def join_slash(self, interaction: discord.Interaction):
        if not interaction.user.voice:
            await interaction.response.send_message("ボイスチャンネルに接続してください", ephemeral=True)
            return
        
        channel = interaction.user.voice.channel
        
        if interaction.guild.id in self.music_player.voice_clients:
            await self.music_player.voice_clients[interaction.guild.id].move_to(channel)
            await interaction.response.send_message(f"{channel.name}に移動しました", ephemeral=True)
            return

        try:
            await interaction.response.defer(ephemeral=True)
            voice_client = await channel.connect()
            self.music_player.voice_clients[interaction.guild.id] = voice_client
            await interaction.followup.send(f"{channel.name}に接続しました", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"エラーが発生しました: {e}", ephemeral=True)

    @app_commands.command(name="leave", description="ボイスチャンネルから退出します")
    async def leave_slash(self, interaction: discord.Interaction):
        if interaction.guild.id not in self.music_player.voice_clients:
            await interaction.response.send_message("ボイスチャンネルに接続していません", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        await self.music_player.voice_clients[interaction.guild.id].disconnect()
        del self.music_player.voice_clients[interaction.guild.id]
        if interaction.guild.id in self.music_player.queues:
            self.music_player.queues[interaction.guild.id] = []
        if interaction.guild.id in self.music_player.now_playing:
            self.music_player.now_playing[interaction.guild.id] = None
        await interaction.followup.send("ボイスチャンネルから退出しました", ephemeral=True)

    @app_commands.command(name="music", description="音楽を再生します")
    async def music_slash(self, interaction: discord.Interaction, query: str):
        if not interaction.user.voice:
            await interaction.response.send_message("ボイスチャンネルに接続してください", ephemeral=True)
            return
            
        await interaction.response.defer()

        if interaction.guild.id not in self.music_player.voice_clients:
            channel = interaction.user.voice.channel
            voice_client = await channel.connect()
            self.music_player.voice_clients[interaction.guild.id] = voice_client
            await interaction.followup.send(f"{channel.name}に接続しました")
            
        youtube_match = re.search(YOUTUBE_URL_PATTERN, query)
        # spotify_match = re.search(SPOTIFY_URL_PATTERN, query)
        
        ctx = await self.bot.get_context(interaction.message) if interaction.message else None
        if ctx is None:
            class FakeContext:
                def __init__(self, interaction):
                    self.guild = interaction.guild
                    self.channel = interaction.channel
                    self.author = interaction.user
                    self.send = interaction.followup.send
                    
            ctx = FakeContext(interaction)
        
        '''    
        if spotify_match:
            await self.music_player.process_spotify(ctx, query)
        elif youtube_match:
            await self.music_player.add_to_queue(ctx, query)
        else:
            await interaction.followup.send(f"「{query}」をYouTubeで検索中...")
            await self.music_player.add_to_queue(ctx, query, is_search=True)
        '''
        
        if youtube_match:
            await self.music_player.add_to_queue(ctx, query)
        else:
            await interaction.followup.send(f"「{query}」をYouTubeで検索中...")
            await self.music_player.add_to_queue(ctx, query, is_search=True)

    @app_commands.command(name="skip", description="現在再生中の曲をスキップします")
    async def skip_slash(self, interaction: discord.Interaction):
        if interaction.guild.id not in self.music_player.voice_clients:
            await interaction.response.send_message("ボイスチャンネルに接続していません", ephemeral=True)
            return
            
        voice_client = self.music_player.voice_clients[interaction.guild.id]
        if voice_client.is_playing():
            voice_client.stop()
            await interaction.response.send_message("曲をスキップしました")
        else:
            await interaction.response.send_message("現在再生中の曲はありません", ephemeral=True)

    @app_commands.command(name="queue", description="現在のキューを表示します")
    async def queue_slash(self, interaction: discord.Interaction):
        guild_id = interaction.guild.id
        if guild_id not in self.music_player.queues or not self.music_player.queues[guild_id]:
            await interaction.response.send_message("キューに曲はありません", ephemeral=True)
            return
            
        queue = self.music_player.queues[guild_id]
        now_playing = self.music_player.now_playing.get(guild_id)
        
        embed = discord.Embed(title="音楽キュー", color=discord.Color.blue())
        
        if now_playing:
            embed.add_field(name="再生中", value=f"**{now_playing['title']}**", inline=False)
            
        if queue:
            queue_text = ""
            for i, song in enumerate(queue[:10], 1):
                queue_text += f"{i}. {song['title']}\n"
                
            if len(queue) > 10:
                queue_text += f"...他 {len(queue) - 10} 曲"
                
            embed.add_field(name="次の曲", value=queue_text or "なし", inline=False)
            
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="pause", description="音楽を一時停止します")
    async def pause_slash(self, interaction: discord.Interaction):
        if interaction.guild.id not in self.music_player.voice_clients:
            await interaction.response.send_message("ボイスチャンネルに接続していません", ephemeral=True)
            return
            
        voice_client = self.music_player.voice_clients[interaction.guild.id]
        if voice_client.is_playing():
            voice_client.pause()
            await interaction.response.send_message("一時停止しました")
        else:
            await interaction.response.send_message("現在再生中の曲はありません", ephemeral=True)

    @app_commands.command(name="resume", description="一時停止した音楽を再開します")
    async def resume_slash(self, interaction: discord.Interaction):
        if interaction.guild.id not in self.music_player.voice_clients:
            await interaction.response.send_message("ボイスチャンネルに接続していません", ephemeral=True)
            return
            
        voice_client = self.music_player.voice_clients[interaction.guild.id]
        if voice_client.is_paused():
            voice_client.resume()
            await interaction.response.send_message("再生を再開しました")
        else:
            await interaction.response.send_message("一時停止している曲はありません", ephemeral=True)

async def setup(bot):
    await bot.add_cog(VoiceCommands(bot))