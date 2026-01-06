import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv('BOT_TOKEN')
TIMEZONE = 'Asia/Kolkata'  # Change to your timezone
DAILY_REPORT_TIME = '08:00'  # 8:00 AM
