import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8761733502:AAFtEKI9E50l6vG4CJcnuesGu17fq5zfhfA")

def _get_admins():
    raw_admins = os.getenv("ADMIN_IDS", "8584724112")
    if not raw_admins.strip():
        return []
    return [int(x.strip()) for x in raw_admins.split(",") if x.strip()]

ADMIN_IDS = _get_admins()

def _get_channels():
    raw_channels = os.getenv("CHANNELS", "-1003792683838,-1003997994180")
    if not raw_channels.strip():
        return []
    return [int(x.strip()) for x in raw_channels.split(",") if x.strip()]

CHANNELS = _get_channels()
