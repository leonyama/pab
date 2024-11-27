from dotenv import load_dotenv
load_dotenv()

import os

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN') 
OWNER_IDS = os.getenv('OWNER_IDS')
PREFIX = os.getenv('PREFIX')