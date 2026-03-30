"""
Entry point for the HedgeFundAI Telegram bot.

Usage:
    python run_telegram_bot.py

Required environment variables (set in .env):
    TELEGRAM_BOT_TOKEN   — bot token from @BotFather
    TELEGRAM_CHANNEL_ID  — channel username (@mychannel) or numeric ID (-100xxxxxxx)
"""
import sys
from pathlib import Path

# Make sure src/ is on the path when running from project root
sys.path.insert(0, str(Path(__file__).parent))

from src.telegram_bot.bot import main

if __name__ == "__main__":
    main()
