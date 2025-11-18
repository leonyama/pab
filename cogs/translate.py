import discord
from discord.ext import commands
from discord import app_commands
from googletrans import Translator, LANGUAGES

class TranslateCommands(commands.Cog):
    """翻訳関連のコマンドを提供します。"""
    
    def __init__(self, bot):
        self.bot = bot
        self.translator = Translator()
        # 言語名からコードへの辞書を作成
        self.language_codes = {name: code for code, name in LANGUAGES.items()}

    def get_language_name(self, code):
        """言語コードから言語名を取得します。"""
        return LANGUAGES.get(code, "不明な言語")

    # ---------------------------------------------
    # プレフィックスコマンド (!translate)
    # ---------------------------------------------
    
    @commands.command(name="translate", aliases=['tr'])
    async def translate_command(self, ctx, target_lang, *, text):
        """
        テキストを指定された言語に翻訳します（ソース言語は自動検出）。
        使用法: !translate [ターゲット言語コード] [翻訳したいテキスト]
        例: !translate ja Hello world
        利用可能な言語コードは !tr_langs で確認できます。
        """
        
        target_lang = target_lang.lower()

        if target_lang not in LANGUAGES.keys():
            await ctx.send(f"無効なターゲット言語コード `{target_lang}` です。\n利用可能な言語コードは `!tr_langs` で確認してください。")
            return
            
        await ctx.send("翻訳中...")

        try:
            translation = self.translator.translate(text, dest=target_lang)
            
            source_lang_name = self.get_language_name(translation.src)
            target_lang_name = self.get_language_name(target_lang)

            embed = discord.Embed(
                title="テキスト翻訳 (自動検出)",
                color=discord.Color.green()
            )
            embed.add_field(name=f"元のテキスト ({source_lang_name} から)", value=f"```\n{text}\n```", inline=False)
            embed.add_field(name=f"翻訳結果 ({target_lang_name} へ)", value=f"```\n{translation.text}\n```", inline=False)
            embed.set_footer(text=f"ソース言語を自動検出: {translation.src} | 信頼度: {translation.extra_data['confidence']:.2f}")

            await ctx.send(embed=embed)

        except Exception as e:
            await ctx.send(f"翻訳中にエラーが発生しました: {e}")
            
    @commands.command(name="tr_langs", aliases=['trl'])
    async def list_languages(self, ctx):
        """
        翻訳に利用可能な言語コードの一覧を表示します。
        """
        langs = list(LANGUAGES.items())
        
        half = len(langs) // 2
        col1 = "\n".join([f"`{code}`: {name.title()}" for code, name in langs[:half]])
        col2 = "\n".join([f"`{code}`: {name.title()}" for code, name in langs[half:]])
        
        embed = discord.Embed(
            title="利用可能な翻訳言語コード",
            description="コマンドで使用する際は、言語名の左にある **言語コード** を指定してください。",
            color=discord.Color.blue()
        )
        embed.add_field(name="言語コード (前半)", value=col1, inline=True)
        embed.add_field(name="言語コード (後半)", value=col2, inline=True)
        embed.set_footer(text="Powered by Google Translate")
        
        await ctx.send(embed=embed)

    # ---------------------------------------------
    # スラッシュコマンド (/translate)
    # ---------------------------------------------

    @app_commands.command(name="translate", description="テキストを指定された言語に翻訳します（ソース言語は自動検出）")
    @app_commands.describe(
        target_lang="翻訳先の言語コード (例: ja, en, zh-cn)",
        text="翻訳したいテキスト"
    )
    async def translate_slash(self, interaction: discord.Interaction, target_lang: str, text: str):
        """
        スラッシュコマンド版の翻訳機能
        """
        
        await interaction.response.defer(thinking=True)
        
        target_lang = target_lang.lower()

        if target_lang not in LANGUAGES.keys():
            await interaction.followup.send(f"無効なターゲット言語コード `{target_lang}` です。\n利用可能な言語コードは `/tr_langs` で確認してください。", ephemeral=True)
            return
            
        try:
            translation = self.translator.translate(text, dest=target_lang)
            
            source_lang_name = self.get_language_name(translation.src)
            target_lang_name = self.get_language_name(target_lang)

            embed = discord.Embed(
                title="テキスト翻訳 (自動検出)",
                color=discord.Color.green()
            )
            embed.add_field(name=f"元のテキスト ({source_lang_name} から)", value=f"```\n{text}\n```", inline=False)
            embed.add_field(name=f"翻訳結果 ({target_lang_name} へ)", value=f"```\n{translation.text}\n```", inline=False)
            embed.set_footer(text=f"ソース言語を自動検出: {translation.src} | 信頼度: {translation.extra_data['confidence']:.2f}")

            await interaction.followup.send(embed=embed)

        except Exception as e:
            await interaction.followup.send(f"翻訳中にエラーが発生しました: {e}", ephemeral=True)


    @app_commands.command(name="tr_langs", description="翻訳に利用可能な言語コードの一覧を表示します")
    async def list_languages_slash(self, interaction: discord.Interaction):
        """
        スラッシュコマンド版の言語一覧表示
        """
        langs = list(LANGUAGES.items())
        
        half = len(langs) // 2
        col1 = "\n".join([f"`{code}`: {name.title()}" for code, name in langs[:half]])
        col2 = "\n".join([f"`{code}`: {name.title()}" for code, name in langs[half:]])
        
        embed = discord.Embed(
            title="利用可能な翻訳言語コード",
            description="コマンドで使用する際は、言語名の左にある **言語コード** を指定してください。",
            color=discord.Color.blue()
        )
        embed.add_field(name="言語コード (前半)", value=col1, inline=True)
        embed.add_field(name="言語コード (後半)", value=col2, inline=True)
        embed.set_footer(text="Powered by Google Translate")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(TranslateCommands(bot))