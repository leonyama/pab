import discord
from discord.ext import commands
from discord import app_commands
import config

class HelpCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self._original_help_command = bot.help_command
        bot.help_command = None 
        
    def cog_unload(self):
        """Cogがアンロードされる時に元のヘルプコマンドを復元"""
        self.bot.help_command = self._original_help_command

    @commands.command(name="help")
    async def help_command(self, ctx, command_name=None):
        """コマンドの一覧とその説明を表示します"""
        prefix = config.PREFIX
        
        if command_name:

            command = self.bot.get_command(command_name)
            if command:
                embed = discord.Embed(
                    title=f"コマンド: {prefix}{command.name}",
                    description=command.help or "説明がありません",
                    color=discord.Color.blue()
                )

                usage = f"{prefix}{command.name}"
                if command.signature:
                    usage += f" {command.signature}"
                embed.add_field(name="使用法", value=f"`{usage}`", inline=False)

                await ctx.send(embed=embed)
            else:
                await ctx.send(f"コマンド `{command_name}` は見つかりませんでした。")
            return

        embed = discord.Embed(
            title="ボットコマンド一覧",
            description=f"プレフィックス: `{prefix}`\n"
                      f"詳細は `{prefix}help [コマンド名]` で確認できます。",
            color=discord.Color.blue()
        )

        cogs = {}
        for command in self.bot.commands:
            if command.hidden:
                continue
                
            cog_name = command.cog.qualified_name if command.cog else "その他"
            if cog_name not in cogs:
                cogs[cog_name] = []
            cogs[cog_name].append(command)

        for cog_name, commands_list in cogs.items():
            commands_text = "\n".join([
                f"`{prefix}{cmd.name}` - {cmd.help.split('\n')[0] if cmd.help else 'No description'}"
                for cmd in commands_list
            ])
            embed.add_field(name=cog_name, value=commands_text, inline=False)
        
        await ctx.send(embed=embed)

    @app_commands.command(name="help", description="コマンドの一覧とその説明を表示します")
    async def help_slash(self, interaction: discord.Interaction, command_name: str = None):
        """スラッシュコマンドのヘルプを表示します"""
        prefix = config.PREFIX
        
        if command_name:
            command = self.bot.get_command(command_name)
            if command:
                embed = discord.Embed(
                    title=f"コマンド: {prefix}{command.name}",
                    description=command.help or "説明がありません",
                    color=discord.Color.blue()
                )

                usage = f"{prefix}{command.name}"
                if command.signature:
                    usage += f" {command.signature}"
                embed.add_field(name="使用法", value=f"`{usage}`", inline=False)

                if command.aliases:
                    aliases = ", ".join([f"{prefix}{alias}" for alias in command.aliases])
                    embed.add_field(name="別名", value=aliases, inline=False)
                
                await interaction.response.send_message(embed=embed)
            else:
                # スラッシュコマンドを探す
                # discord.pyのAPIでは制限あり？
                commands_dict = {}
                for cmd in self.bot.tree.get_commands():
                    commands_dict[cmd.name] = cmd
                
                if command_name in commands_dict:
                    cmd = commands_dict[command_name]
                    embed = discord.Embed(
                        title=f"スラッシュコマンド: /{cmd.name}",
                        description=cmd.description or "説明がありません",
                        color=discord.Color.blue()
                    )
                    await interaction.response.send_message(embed=embed)
                else:
                    await interaction.response.send_message(f"コマンド `{command_name}` は見つかりませんでした。", ephemeral=True)
            return
        
        # 全コマンドのヘルプを表示
        embed = discord.Embed(
            title="ボットコマンド一覧",
            description=f"プレフィックス: `{prefix}`\n"
                      f"詳細は `{prefix}help [コマンド名]` または `/help [コマンド名]` で確認できます。",
            color=discord.Color.blue()
        )

        cogs = {}
        for command in self.bot.commands:
            if command.hidden:
                continue
                
            cog_name = command.cog.qualified_name if command.cog else "その他"
            if cog_name not in cogs:
                cogs[cog_name] = []
            cogs[cog_name].append(command)

        for cog_name, commands_list in cogs.items():
            commands_text = "\n".join([
                f"`{prefix}{cmd.name}` - {cmd.help.split('\n')[0] if cmd.help else '説明なし'}"
                for cmd in commands_list
            ])
            embed.add_field(name=cog_name, value=commands_text, inline=False)
        
        # スラッシュコマンド一覧
        slash_commands = []
        for cmd in self.bot.tree.get_commands():
            slash_commands.append(f"`/{cmd.name}` - {cmd.description}")
        
        if slash_commands:
            embed.add_field(
                name="スラッシュコマンド",
                value="\n".join(slash_commands),
                inline=False
            )
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(HelpCommands(bot))