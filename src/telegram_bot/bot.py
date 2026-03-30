"""
Telegram bot entry point for HedgeFundAI insights.

Commands:
  /start   — welcome message
  /help    — list commands
  /stats   — recommendation statistics
  /latest  — immediately post unposted recommendations to the channel
  /summary — immediately post portfolio long/short summary to the channel
"""
import logging
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from . import db_reader, formatter, scheduler as sched_module

load_dotenv()

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

WELCOME_TEXT = (
    "👋 <b>HedgeFundAI Bot</b>\n"
    "\n"
    "Я публикую инсайты от ИИ хедж-фонда в канал.\n"
    "\n"
    "Доступные команды:\n"
    "/stats   — статистика рекомендаций\n"
    "/latest  — отправить новые рекомендации в канал прямо сейчас\n"
    "/summary — отправить сводку по портфелю прямо сейчас\n"
    "/help    — это сообщение"
)


async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_TEXT, parse_mode="HTML")


async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(WELCOME_TEXT, parse_mode="HTML")


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    stats = db_reader.get_stats()
    text = formatter.format_stats(stats)
    await update.message.reply_text(text, parse_mode="HTML")


async def cmd_latest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    channel_id = os.environ["TELEGRAM_CHANNEL_ID"]
    recs = db_reader.get_unposted_recommendations()

    if not recs:
        await update.message.reply_text("✅ Нет новых рекомендаций для отправки.")
        return

    await update.message.reply_text(f"📤 Отправляю {len(recs)} рекомендаций в канал...")

    ok = 0
    for rec in recs:
        text = formatter.format_recommendation(rec)
        try:
            await context.bot.send_message(
                chat_id=channel_id,
                text=text,
                parse_mode="HTML",
            )
            db_reader.mark_as_posted(rec["id"])
            ok += 1
        except Exception as e:
            logger.error(f"Failed to send {rec['ticker']}: {e}")
            await update.message.reply_text(f"⚠️ Ошибка при отправке {rec['ticker']}: {e}")

    await update.message.reply_text(f"✅ Отправлено {ok} из {len(recs)}.")


async def cmd_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    channel_id = os.environ["TELEGRAM_CHANNEL_ID"]
    data = db_reader.get_latest_scoring_summary()

    if not data:
        await update.message.reply_text("⚠️ Нет данных о портфеле в базе.")
        return

    text = formatter.format_portfolio_summary(data)
    await context.bot.send_message(
        chat_id=channel_id,
        text=text,
        parse_mode="HTML",
    )
    await update.message.reply_text("✅ Сводка отправлена в канал.")


async def post_startup(application: Application):
    """Runs after the bot starts: apply DB migration and start scheduler."""
    db_reader.migrate()
    logger.info("DB migration applied (posted_to_telegram column).")

    channel_id = os.environ.get("TELEGRAM_CHANNEL_ID", "")
    if not channel_id:
        logger.warning("TELEGRAM_CHANNEL_ID not set — scheduler will not start.")
        return

    scheduler = sched_module.build_scheduler(application.bot, channel_id)
    scheduler.start()
    logger.info("Scheduler started (09:00 digest, 18:00 summary, Moscow time).")


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is not set in environment / .env")

    app = (
        Application.builder()
        .token(token)
        .post_init(post_startup)
        .build()
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("stats", cmd_stats))
    app.add_handler(CommandHandler("latest", cmd_latest))
    app.add_handler(CommandHandler("summary", cmd_summary))

    logger.info("Bot is running. Press Ctrl+C to stop.")
    app.run_polling(drop_pending_updates=True)
