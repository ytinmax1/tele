import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "8761733502:AAFtEKI9E50l6vG4CJcnuesGu17fq5zfhfA")
YOUR_USER_ID = int(os.getenv("YOUR_USER_ID", "8584724112"))

def _get_channels():
    raw_channels = os.getenv("CHANNELS", "-1003792683838,-1003997994180")
    if not raw_channels.strip():
        return []
    return [int(x.strip()) for x in raw_channels.split(",") if x.strip()]

CHANNELS = _get_channels()

