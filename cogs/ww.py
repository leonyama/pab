import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import random

ROLES = ["人狼", "市民", "占い師"]

class WerewolfGame:
    def __init__(self):
        self.players = []  
        self.roles = {}
        self.alive = set()
        self.started = False
        self.night_actions = {}

    def add_player(self, member, vc_channel):
        if self.started:
            return False, "既にゲームが開始されています。"
        if any(p[0].id == member.id for p in self.players):
            return False, "既に参加済みです。"
        self.players.append((member, vc_channel))
        return True, None

    def assign_roles(self):
        n_players = len(self.players)
        n_werewolves = max(1, n_players // 4)
        n_seer = 1 if n_players >= 4 else 0
        roles_list = ["人狼"] * n_werewolves + ["占い師"] * n_seer + ["市民"] * (n_players - n_werewolves - n_seer)
        random.shuffle(roles_list)
        self.roles = {player[0].id: role for player, role in zip(self.players, roles_list)}
        self.alive = set(player[0].id for player in self.players)

    def get_alive_players(self):
        return [p for p in self.players if p[0].id in self.alive]

    def kill(self, user_id):
        if user_id in self.alive:
            self.alive.remove(user_id)

    def reset_night(self):
        self.night_actions = {}

    def get_player_obj(self, user_id):
        for p, vc in self.players:
            if p.id == user_id:
                return p
        return None

class WerewolfCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games = {}

    def get_game(self, guild_id):
        if guild_id not in self.games:
            self.games[guild_id] = WerewolfGame()
        return self.games[guild_id]


    @commands.command(name="ww_create")
    async def create(self, ctx):
        """人狼ゲーム部屋を作成します"""
        game = self.get_game(ctx.guild.id)
        if game.started:
            await ctx.send("すでにゲームが開始されています。")
        else:
            self.games[ctx.guild.id] = WerewolfGame()
            await ctx.send("人狼ゲーム部屋が作成されました！VC参加の上 `!ww_join`")

    @commands.command(name="ww_join")
    async def join(self, ctx):
        """人狼ゲームに参加します (VC必須)"""
        if not ctx.author.voice or not ctx.author.voice.channel:
            await ctx.send("VCに接続してください！VC未参加だと参加できません。")
            return
        game = self.get_game(ctx.guild.id)
        success, msg = game.add_player(ctx.author, ctx.author.voice.channel)
        if success:
            await ctx.send(f"{ctx.author.mention} が参加しました。現在の人数: {len(game.players)}")
        else:
            await ctx.send(msg)

    @commands.command(name="ww_start")
    async def start(self, ctx):
        """人狼ゲームを開始します (VC必須)"""
        await self.start_game(ctx.guild, ctx.author, ctx.channel)

    @commands.command(name="ww_status")
    async def status(self, ctx):
        """生存中のプレイヤー一覧（役職は表示しません）"""
        await self.show_status(ctx.guild, ctx.channel)

    @commands.command(name="ww_night")
    async def night(self, ctx):
        """夜のターン（人狼・占い師はDMで行動）"""
        await self.night_turn(ctx.guild, ctx.channel)

    @commands.command(name="ww_vote")
    async def vote(self, ctx):
        """昼の投票タイム（生存者から投票で1人を追放）"""
        await self.vote_turn(ctx.guild, ctx.channel)

    @commands.command(name="ww_end")
    async def end(self, ctx):
        """人狼ゲームを終了します"""
        await self.end_game(ctx.guild, ctx.channel)

    ### スラッシュコマンド

    @app_commands.command(name="ww_create", description="人狼ゲーム部屋を作成します")
    async def slash_create(self, interaction: discord.Interaction):
        game = self.get_game(interaction.guild.id)
        if game.started:
            await interaction.response.send_message("すでにゲームが開始されています。", ephemeral=True)
        else:
            self.games[interaction.guild.id] = WerewolfGame()
            await interaction.response.send_message("人狼ゲーム部屋が作成されました！VC参加の上 `/ww_join`", ephemeral=True)

    @app_commands.command(name="ww_join", description="人狼ゲームに参加します (VC必須)")
    async def slash_join(self, interaction: discord.Interaction):
        member = interaction.user
        if not member.voice or not member.voice.channel:
            await interaction.response.send_message("VCに接続してください！VC未参加だと参加できません。", ephemeral=True)
            return
        game = self.get_game(interaction.guild.id)
        success, msg = game.add_player(member, member.voice.channel)
        if success:
            await interaction.response.send_message(f"{member.mention} が参加しました。現在の人数: {len(game.players)}")
        else:
            await interaction.response.send_message(msg, ephemeral=True)

    @app_commands.command(name="ww_start", description="人狼ゲームを開始します (VC必須)")
    async def slash_start(self, interaction: discord.Interaction):
        await self.start_game(interaction.guild, interaction.user, interaction.channel)

    @app_commands.command(name="ww_status", description="生存中のプレイヤー一覧（役職は表示しません）")
    async def slash_status(self, interaction: discord.Interaction):
        await self.show_status(interaction.guild, interaction.channel)

    @app_commands.command(name="ww_night", description="夜のターン（人狼・占い師はDMで行動）")
    async def slash_night(self, interaction: discord.Interaction):
        await self.night_turn(interaction.guild, interaction.channel)

    @app_commands.command(name="ww_vote", description="昼の投票タイム（生存者から投票で1人を追放）")
    async def slash_vote(self, interaction: discord.Interaction):
        await self.vote_turn(interaction.guild, interaction.channel)

    @app_commands.command(name="ww_end", description="人狼ゲームを終了します")
    async def slash_end(self, interaction: discord.Interaction):
        await self.end_game(interaction.guild, interaction.channel)


    async def start_game(self, guild, author, channel):
        game = self.get_game(guild.id)
        if game.started:
            await channel.send("すでにゲームが開始されています。")
            return
        if len(game.players) < 4:
            await channel.send("4人以上で開始できます。")
            return
        not_in_vc = [p[0].mention for p in game.players if not p[0].voice or not p[0].voice.channel]
        if not_in_vc:
            await channel.send(f"VC未参加のプレイヤーがいます: {'、'.join(not_in_vc)}\n全員VCに入ってください。")
            return

        game.assign_roles()
        game.started = True

        for player, _ in game.players:
            role = game.roles[player.id]
            try:
                await player.send(f"あなたの役職: {role}")
            except Exception:
                pass
        await channel.send("ゲームを開始します。DMに役職が送信されました。\n夜のターン開始はコマンドで。")

    async def show_status(self, guild, channel):
        game = self.get_game(guild.id)
        alive_list = [self.bot.get_user(pid).mention for pid in game.alive]
        await channel.send(f"生存者: {'、'.join(alive_list)}")

    async def night_turn(self, guild, channel):
        game = self.get_game(guild.id)
        if not game.started:
            await channel.send("まだゲームは開始されていません。")
            return
        game.reset_night()
        wolves = [p for p in game.get_alive_players() if game.roles[p[0].id] == "人狼"]
        seers = [p for p in game.get_alive_players() if game.roles[p[0].id] == "占い師"]
        citizens = [p for p in game.get_alive_players() if game.roles[p[0].id] == "市民"]

        citizen_ids = [p[0].id for p in citizens]
        msg_tasks = []
        # 人狼へのDM
        for wolf, _ in wolves:
            try:
                msg = f"夜です。殺したい市民の番号を選んでください: {', '.join(str(i+1) + '.' + self.bot.get_user(cid).name for i, cid in enumerate(citizen_ids))}\nDMで番号のみ送ってください。"
                msg_tasks.append(wolf.send(msg))
            except Exception:
                pass
        # 占い師へのDM
        alive_ids = [p[0].id for p in game.get_alive_players() if game.roles[p[0].id] != "占い師"]
        for seer, _ in seers:
            try:
                msg = f"夜です。占いたい相手の番号を選んでください: {', '.join(str(i+1) + '.' + self.bot.get_user(cid).name for i, cid in enumerate(alive_ids))}\nDMで番号のみ送ってください。"
                msg_tasks.append(seer.send(msg))
            except Exception:
                pass

        if msg_tasks:
            await asyncio.gather(*msg_tasks)

        await channel.send("夜のターンです。人狼・占い師はDMで行動を選んでください。")
        await asyncio.sleep(15)

        victim_id = None
        result_msg = ""
        if wolves and citizens:
            victim_id = random.choice(citizen_ids)
            game.kill(victim_id)
            result_msg += f"夜が明けました。{self.bot.get_user(victim_id).mention} が人狼に殺されました。\n"
        # 占い師の結果
        if seers and alive_ids:
            divined_id = random.choice(alive_ids)
            for seer, _ in seers:
                role_result = game.roles[divined_id]
                try:
                    await seer.send(f"あなたが占った {self.bot.get_user(divined_id).name} の役職は: {role_result}")
                except Exception:
                    pass
            result_msg += f"占い師は誰かを占いました。"

        if not victim_id and not seers:
            result_msg += "今夜は何も起こりませんでした。"
        await channel.send(result_msg.strip())

    async def vote_turn(self, guild, channel):
        game = self.get_game(guild.id)
        if not game.started:
            await channel.send("まだゲームは開始されていません。")
            return
        alive_players = game.get_alive_players()
        vote_msg = "昼の投票タイム。追放したい人の番号を送ってください:\n"
        vote_msg += "\n".join([f"{i+1}. {p[0].name}" for i, p in enumerate(alive_players)])
        await channel.send(vote_msg + "\n60秒後にランダム追放します")
        await asyncio.sleep(60)

        if alive_players:
            target = random.choice(alive_players)[0]
            game.kill(target.id)
            await channel.send(f"投票の結果、{target.mention} が追放されました。")

        alive_wolves = [p for p in game.get_alive_players() if game.roles[p[0].id] == "人狼"]
        alive_citizens = [p for p in game.get_alive_players() if game.roles[p[0].id] in ["市民", "占い師"]]

        if not alive_wolves:
            await channel.send("市民陣営の勝利！人狼は全滅しました。")
            game.started = False
        elif len(alive_wolves) >= len(alive_citizens):
            await channel.send("人狼陣営の勝利！人狼が市民と同数以上になりました。")
            game.started = False

    async def end_game(self, guild, channel):
        if guild.id in self.games:
            del self.games[guild.id]
        await channel.send("人狼ゲームを終了しました。")

async def setup(bot):
    await bot.add_cog(WerewolfCog(bot))