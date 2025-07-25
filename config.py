import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    BOT_TOKEN = os.getenv('BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
    DATABASE_PATH = 'bot_database.db'
    PHOTOS_DIR = 'saved_photos'
    MUSIC_DIR = 'saved_music'
    TIKTOK_DIR = 'saved_tiktok'
    
    # API Keys (optional)
    SHAZAM_API_KEY = os.getenv('SHAZAM_API_KEY', '')
    
    # Bot settings
    MAX_QUOTES_PER_USER = 100
    MAX_PHOTOS_PER_USER = 50
    MAX_MUSIC_PER_USER = 30