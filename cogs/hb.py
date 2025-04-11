import discord
from discord.ext import commands
import random

class HitAndBlow(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.games = {}

    def generate_code(self):
        return random.sample(range(10), 4)

    def judge(self, player_input, computer_code):
        hit = 0
        blow = 0
        checked_indices_b = set()

        for i in range(4):
            if player_input[i] == computer_code[i]:
                hit += 1
                checked_indices_b.add(i)

        for i in range(4):
            if player_input[i] != computer_code[i] and player_input[i] in computer_code:
                for j in range(4):
                    if j not in checked_indices_b and computer_code[j] == player_input[i]:
                        blow += 1
                        checked_indices_b.add(j)
                        break

        return hit, blow

    @commands.command(name="hb")
    async def start_game(self, ctx):
        """Hit & Blowを開始します"""
        if ctx.author.id in self.games:
            await ctx.send(f"{ctx.author.mention} すでにゲームが進行中です。`!end_hb`で終了できます。")
            return

        code = self.generate_code()
        self.games[ctx.author.id] = {"code": code, "attempts": 0}
        await ctx.reply(f"Hit and Blowを開始します！4桁の数字を予想して入力してください。")
        #print(f"（デバッグ用：{ctx.author.name}の生成された数字は {code} です）") 

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.author.id not in self.games:
            return

        game_data = self.games[message.author.id]
        code = game_data["code"]

        if not message.content.isdigit():
            await message.channel.send(f"数字以外を入力しないでください。")
            return
        if len(message.content) != 4:
            await message.channel.send(f"4桁の数字を入力してください。")
            return

        player_input = [int(x) for x in message.content]
        game_data["attempts"] += 1

        hit, blow = self.judge(player_input, code)

        await message.channel.send(f"ヒット: {hit}, ブロー: {blow}")

        if hit == 4:
            await message.channel.send(f"正解です！おめでとうございます！！（試行回数: {game_data['attempts']}）")
            del self.games[message.author.id]

    @commands.command(name="end_hb")
    async def end_game(self, ctx):
        """Hit & Blowを終了します"""
        if ctx.author.id in self.games:
            correct_code = ''.join(map(str, self.games[ctx.author.id]["code"]))
            del self.games[ctx.author.id]
            await ctx.send(f"ゲーム終了！正解の数字は {correct_code} でした。")
        else:
            await ctx.send(f"{ctx.author.mention} 進行中のゲームはありません。")

async def setup(bot):
    await bot.add_cog(HitAndBlow(bot))