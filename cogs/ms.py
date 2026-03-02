import discord
from discord.ext import commands
from discord import app_commands
import config
import json

class MessageSender(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def is_admin(self, user_id):
        return str(user_id) in map(str, json.loads(config.OWNER_IDS))

    @commands.command(name="send")
    async def send_message(self, ctx, target_id: int, *, message: str):
        """
        管理者のみ: メッセージをUserまたはChannelに送信
        使用例: !send 123456789 こんにちは
        """
        if not self.is_admin(ctx.author.id):
            await ctx.send("権限不足です。管理者のみこのコマンドを使用できます。")
            return

        try:           
            try:
                user = await self.bot.fetch_user(target_id)
                await user.send(message)
                await ctx.send(f"{user.name} にDMを送信しました")
                return
            except discord.NotFound:
                pass

            channel = self.bot.get_channel(target_id)
            if channel:
                await channel.send(message)
                await ctx.send(f"{channel.mention} にメッセージを送信しました")
                return

            await ctx.send("指定されたUserIDまたはChannelIDが見つかりません")
        except Exception as e:
            await ctx.send(f"エラーが発生しました: {e}")

    @commands.command(name="sendfile")
    async def send_file(self, ctx, target_id: int):
        """
        管理者のみ: ファイルをUserまたはChannelに送信
        使用例: !sendfile 123456789 (ファイルを添付)
        """
        if not self.is_admin(ctx.author.id):
            await ctx.send("権限不足です。管理者のみこのコマンドを使用できます。")
            return

        if not ctx.message.attachments:
            await ctx.send("ファイルが添付されていません")
            return

        try:
            attachment = ctx.message.attachments[0]
            file_data = await attachment.read()

            try:
                user = await self.bot.fetch_user(target_id)
                file_obj = discord.File(
                    fp=__import__('io').BytesIO(file_data),
                    filename=attachment.filename
                )
                await user.send(file=file_obj)
                await ctx.send(f"{user.name} にファイルを送信しました")
                return
            except discord.NotFound:
                pass

            channel = self.bot.get_channel(target_id)
            if channel:
                file_obj = discord.File(
                    fp=__import__('io').BytesIO(file_data),
                    filename=attachment.filename
                )
                await channel.send(file=file_obj)
                await ctx.send(f"{channel.mention} にファイルを送信しました")
                return

            await ctx.send("指定されたUserIDまたはChannelIDが見つかりません")
        except Exception as e:
            await ctx.send(f"エラーが発生しました: {e}")

    @app_commands.command(name="send_message", description="メッセージをUserまたはChannelに送信（管理者のみ）")
    async def send_message_slash(
        self,
        interaction: discord.Interaction,
        target_id: int,
        message: str
    ):

        if not self.is_admin(interaction.user.id):
            await interaction.response.send_message(
                "権限不足です。管理者のみこのコマンドを使用できます。",
                ephemeral=True
            )
            return

        try:
            try:
                user = await self.bot.fetch_user(target_id)
                await user.send(message)
                await interaction.response.send_message(
                    f"{user.name} にDMを送信しました",
                    ephemeral=True
                )
                return
            except discord.NotFound:
                pass

            channel = self.bot.get_channel(target_id)
            if channel:
                await channel.send(message)
                await interaction.response.send_message(
                    f"{channel.mention} にメッセージを送信しました",
                    ephemeral=True
                )
                return

            await interaction.response.send_message(
                "指定されたUserIDまたはChannelIDが見つかりません",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                f"エラーが発生しました: {e}",
                ephemeral=True
            )

    @app_commands.command(name="send_file", description="ファイルをUserまたはChannelに送信（管理者のみ）")
    @app_commands.describe(
        target_id="送信先のUserIDまたはChannelID",
        file="送信するファイル"
    )
    async def send_file_slash(
        self,
        interaction: discord.Interaction,
        target_id: int,
        file: discord.Attachment
    ):
        """Slash command version of send file"""
        if not self.is_admin(interaction.user.id):
            await interaction.response.send_message(
                "権限不足です。管理者のみこのコマンドを使用できます。",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True)

        try:
            file_data = await file.read()

            try:
                user = await self.bot.fetch_user(target_id)
                file_obj = discord.File(
                    fp=__import__('io').BytesIO(file_data),
                    filename=file.filename
                )
                await user.send(file=file_obj)
                await interaction.followup.send(
                    f"{user.name} にファイルを送信しました",
                    ephemeral=True
                )
                return
            except discord.NotFound:
                pass

            channel = self.bot.get_channel(target_id)
            if channel:
                file_obj = discord.File(
                    fp=__import__('io').BytesIO(file_data),
                    filename=file.filename
                )
                await channel.send(file=file_obj)
                await interaction.followup.send(
                    f"{channel.mention} にファイルを送信しました",
                    ephemeral=True
                )
                return

            await interaction.followup.send(
                "指定されたUserIDまたはChannelIDが見つかりません",
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(
                f"エラーが発生しました: {e}",
                ephemeral=True
            )

async def setup(bot):
    await bot.add_cog(MessageSender(bot))
