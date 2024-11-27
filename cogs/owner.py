import discord
from discord.ext import commands
from discord import app_commands
import config
import os
import sys

class OwnerCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_owner(self, user_id):
        return user_id in config.OWNER_IDS

    @commands.command(name="kick")
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        if not self.is_owner(ctx.author.id):
            await ctx.send("権限不足です")
            return
        try:
            await member.kick(reason=reason)
            await ctx.send(f"{member.name}をkickしました")
        except Exception as e:
            await ctx.send(f"Kickに失敗しました: {e}")

    @commands.command(name="ban")
    async def ban(self, ctx, member: discord.Member, *, reason=None):
        if not self.is_owner(ctx.author.id):
            await ctx.send("権限不足です")
            return
        try:
            await member.ban(reason=reason)
            await ctx.send(f"{member.name}をbanしました")
        except Exception as e:
            await ctx.send(f"Banに失敗しました: {e}")

    @commands.command(name="restart")
    async def restart(self, ctx):
        if not self.is_owner(ctx.author.id):
            await ctx.send("権限不足です")
            return
        await ctx.send("Botを再起動しています...")
        await self.bot.close()
        os.execv(sys.executable, ['python'] + sys.argv)

    @app_commands.command(name="kick", description="メンバーをキックします")
    async def kick_slash(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        if not self.is_owner(interaction.user.id):
            await interaction.response.send_message("権限不足です", ephemeral=True)
            return
        try:
            await member.kick(reason=reason)
            await interaction.response.send_message(f"{member.name}をkickしました", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Kickに失敗しました: {e}", ephemeral=True)

    @app_commands.command(name="ban", description="メンバーをBANします")
    async def ban_slash(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        if not self.is_owner(interaction.user.id):
            await interaction.response.send_message("権限不足です", ephemeral=True)
            return
        try:
            await member.ban(reason=reason)
            await interaction.response.send_message(f"{member.name}をbanしました", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Banに失敗しました: {e}", ephemeral=True)

    @app_commands.command(name="restart", description="Botを再起動します")
    async def restart_slash(self, interaction: discord.Interaction):
        if not self.is_owner(interaction.user.id):
            await interaction.response.send_message("権限不足です", ephemeral=True)
            return
        await interaction.response.send_message("Botを再起動しています...", ephemeral=True)
        await self.bot.close()
        os.execv(sys.executable, ['python'] + sys.argv)

async def setup(bot):
    await bot.add_cog(OwnerCommands(bot))
    await bot.tree.sync()