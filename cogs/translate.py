import discord
from discord.ext import commands
from discord import app_commands
from deep_translator import GoogleTranslator

LANGUAGES = GoogleTranslator.get_supported_languages()  # ['afrikaans', 'albanian', ... ,'japanese', 'english']

class TranslateCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="translate", aliases=['tr'])
    async def translate_command(self, ctx, target_lang, *, text):
        target_lang = target_lang.lower()
        # サポート言語名のみで判定
        if target_lang not in LANGUAGES:
            await ctx.send(f"無効なターゲット言語名 `{target_lang}` です。\n利用可能な言語名は `!tr_langs` で確認してください。")
            return
        await ctx.send("翻訳中...")
        try:
            translated = GoogleTranslator(source="auto", target=target_lang).translate(text)
            embed = discord.Embed(
                title="テキスト翻訳 (自動検出)",
                color=discord.Color.green()
            )
            embed.add_field(name=f"元のテキスト (自動判定)", value=f"```\n{text}\n```", inline=False)
            embed.add_field(name=f"翻訳結果 ({target_lang} へ)", value=f"```\n{translated}\n```", inline=False)
            embed.set_footer(text="Powered by Google Translate")
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"翻訳中にエラーが発生しました: {e}")

    @commands.command(name="tr_langs", aliases=['trl'])
    async def list_languages(self, ctx):
        # リストを2列に分割
        half = len(LANGUAGES) // 2
        col1 = "\n".join([f"`{lang}`" for lang in LANGUAGES[:half]])
        col2 = "\n".join([f"`{lang}`" for lang in LANGUAGES[half:]])
        embed = discord.Embed(
            title="利用可能な翻訳言語名",
            description="コマンドで使用する際は、リスト内の **言語名** を指定してください（例: japanese, english, chinese (simplified) など）。",
            color=discord.Color.blue()
        )
        embed.add_field(name="言語名 (前半)", value=col1, inline=True)
        embed.add_field(name="言語名 (後半)", value=col2, inline=True)
        embed.set_footer(text="Powered by Google Translate")
        await ctx.send(embed=embed)

    @app_commands.command(name="translate", description="テキストを指定された言語に翻訳します（ソース言語は自動検出）")
    @app_commands.describe(
        target_lang="翻訳先の言語名 (例: japanese, english, chinese (simplified)など)",
        text="翻訳したいテキスト"
    )
    async def translate_slash(self, interaction: discord.Interaction, target_lang: str, text: str):
        await interaction.response.defer(thinking=True)
        target_lang = target_lang.lower()
        if target_lang not in LANGUAGES:
            await interaction.followup.send(f"無効なターゲット言語名 `{target_lang}` です。\n利用可能な言語名は `/tr_langs` で確認してください。", ephemeral=True)
            return
        try:
            translated = GoogleTranslator(source="auto", target=target_lang).translate(text)
            embed = discord.Embed(
                title="テキスト翻訳 (自動検出)",
                color=discord.Color.green()
            )
            embed.add_field(name=f"元のテキスト (自動判定)", value=f"```\n{text}\n```", inline=False)
            embed.add_field(name=f"翻訳結果 ({target_lang} へ)", value=f"```\n{translated}\n```", inline=False)
            embed.set_footer(text="Powered by Google Translate")
            await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"翻訳中にエラーが発生しました: {e}", ephemeral=True)

    @app_commands.command(name="tr_langs", description="翻訳に利用可能な言語名リストを表示します")
    async def list_languages_slash(self, interaction: discord.Interaction):
        half = len(LANGUAGES) // 2
        col1 = "\n".join([f"`{lang}`" for lang in LANGUAGES[:half]])
        col2 = "\n".join([f"`{lang}`" for lang in LANGUAGES[half:]])
        embed = discord.Embed(
            title="利用可能な翻訳言語名",
            description="コマンドで使用する際は、リスト内の **言語名** を指定してください（例: japanese, english, chinese (simplified) など）。",
            color=discord.Color.blue()
        )
        embed.add_field(name="言語名 (前半)", value=col1, inline=True)
        embed.add_field(name="言語名 (後半)", value=col2, inline=True)
        embed.set_footer(text="Powered by Google Translate")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(TranslateCommands(bot))