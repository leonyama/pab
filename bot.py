import discord
from discord.ext import commands
import config
import os

TOKEN = config.DISCORD_TOKEN
prefix = config.PREFIX

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=prefix, intents=intents)

async def load_cogs():
    cog_path = os.path.join(os.path.dirname(__file__), 'cogs')
    for filename in os.listdir(cog_path):
        if filename.endswith('.py'):
            cog_name = filename[:-3]
            try:
                await bot.load_extension(f'cogs.{cog_name}')
                print(f"Loaded cog: {cog_name}")
            except Exception as e:
                print(f"Failed to load cog {cog_name}: {e}")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    await bot.change_presence(activity=discord.Game(f"prefix : {prefix}"))
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} commands")
    except Exception as e:
        print(f"Failed to sync commands: {e}")
    await load_cogs()

@bot.event
async def on_message(message):
    if message.author.bot:
        return  
    if message.content.startswith(bot.command_prefix):
        await bot.process_commands(message)

bot.run(TOKEN)