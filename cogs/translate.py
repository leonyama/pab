import discord
from discord.ext import commands
from discord import app_commands
from deep_translator import GoogleTranslator

translator = GoogleTranslator()
LANGUAGE_NAME2CODE = translator.get_supported_languages(as_dict=True)
LANGUAGE_CODES = set(LANGUAGE_NAME2CODE.values())
LANGUAGES = list(LANGUAGE_NAME2CODE.keys())

def normalize_lang(target_lang):
    lower = target_lang.strip().lower()
    if lower in LANGUAGE_CODES:
        return lower
    if lower in LANGUAGE_NAME2CODE:
        return LANGUAGE_NAME2CODE[lower]
    return None

def split_text(text, max_length=2000):
    import re
    sentences = re.split(r'(?<=[。.!?])|\n', text)
    chunks = []
    current = ""
    for sent in sentences:
        if len(current) + len(sent) > max_length and current:
            chunks.append(current)
            current = sent
        else:
            current += sent
    if current:
        chunks.append(current)
    return chunks

async def safe_translate(text, target_lang_code, source_lang="auto"):
    results = []
    for chunk in split_text(text):
        try:
            translated = GoogleTranslator(source=source_lang, target=target_lang_code).translate(chunk)
        except Exception as e:
            translated = f"[ERROR] {str(e)} : {chunk}"
        results.append(translated)
    return ''.join(results)


class TranslateCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="translate", aliases=['tr'])
    async def translate_command(self, ctx, target_lang, *, text):
        target_lang_code = normalize_lang(target_lang)
        if not target_lang_code:
            await ctx.send(
                f"無効なターゲット言語 `{target_lang}` です。\n"
                "利用可能な言語名は `!tr_langs` で確認してください。\n"
                "またはコードが不明な場合は `!tr_langs` をご覧ください。"
            )
            return

        status_msg = await ctx.send("翻訳中...")
        try:
            translated = await safe_translate(text, target_lang_code)
            if translated.strip() == text.strip():
                await status_msg.edit(content=f"翻訳に失敗した可能性があります。（原文: {text[:40]} ...）")
            else:
                embed = discord.Embed(
                    title="Translate",
                    color=discord.Color.green()
                )
                embed.add_field(name=f"To {target_lang}", value=f"```\n{translated}\n```", inline=False)
                await status_msg.edit(content=None, embed=embed)
        except Exception as e:
            await status_msg.edit(content=f"翻訳中にエラーが発生しました: {e}")

    @commands.command(name="tr_langs", aliases=['trl'])
    async def list_languages(self, ctx):
        half = len(LANGUAGE_NAME2CODE) // 2
        items = list(LANGUAGE_NAME2CODE.items())
        col1 = "\n".join([f"`{name}` : `{code}`" for name, code in items[:half]])
        col2 = "\n".join([f"`{name}` : `{code}`" for name, code in items[half:]])
        embed = discord.Embed(
            title="利用可能な翻訳言語名・コード一覧",
            description="コマンドで使う際は **言語名かコード** のどちらかを入力してください。（例: japanese / ja, english / en など）",
            color=discord.Color.blue()
        )
        embed.add_field(name="言語", value=col1, inline=True)
        embed.add_field(name="言語", value=col2, inline=True)
        await ctx.send(embed=embed)

    @app_commands.command(name="translate", description="テキストを指定された言語に翻訳します")
    @app_commands.describe(
        target_lang="翻訳先の言語名またはコード (例: japanese, ja, english, en, chinese (simplified) など)",
        text="翻訳したいテキスト"
    )
    async def translate_slash(self, interaction: discord.Interaction, target_lang: str, text: str):
        await interaction.response.defer(thinking=True)
        target_lang_code = normalize_lang(target_lang)
        if not target_lang_code:
            await interaction.followup.send(
                f"無効なターゲット言語 `{target_lang}` です。\n"
                "利用可能な言語名およびコードは `/tr_langs` で確認してください。\n"
                "またはコードが不明な場合は `/tr_langs` をどうぞ。",
                ephemeral=True
            )
            return

        try:
            translated = await safe_translate(text, target_lang_code)
            if translated.strip() == text.strip():
                await interaction.followup.send(
                    f"翻訳に失敗した可能性があります。（原文: {text[:40]} ...）",
                    ephemeral=True
                )
            else:
                embed = discord.Embed(
                    title="Translate",
                    color=discord.Color.green()
                )
                embed.add_field(name=f"To {target_lang}", value=f"```\n{translated}\n```", inline=False)
                await interaction.followup.send(embed=embed)
        except Exception as e:
            await interaction.followup.send(f"翻訳中にエラーが発生しました: {e}", ephemeral=True)

    @app_commands.command(name="tr_langs", description="翻訳に利用可能な言語名およびコード一覧を表示します")
    async def list_languages_slash(self, interaction: discord.Interaction):
        half = len(LANGUAGE_NAME2CODE) // 2
        items = list(LANGUAGE_NAME2CODE.items())
        col1 = "\n".join([f"`{name}` : `{code}`" for name, code in items[:half]])
        col2 = "\n".join([f"`{name}` : `{code}`" for name, code in items[half:]])
        embed = discord.Embed(
            title="利用可能な翻訳言語名・コード一覧",
            description="コマンドで使う際は **言語名かコード** のどちらかを入力してください。（例: japanese / ja, english / en など）",
            color=discord.Color.blue()
        )
        embed.add_field(name="言語", value=col1, inline=True)
        embed.add_field(name="言語", value=col2, inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot):
    await bot.add_cog(TranslateCommands(bot))