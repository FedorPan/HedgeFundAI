"""
APScheduler jobs for the Telegram bot.

Schedule (Moscow time / Europe/Moscow):
  - 09:00  — Morning digest: post all unposted recommendations to the channel
  - 18:00  — Evening summary: post portfolio long/short overview
"""
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

logger = logging.getLogger(__name__)

MOSCOW_TZ = pytz.timezone("Europe/Moscow")


async def _post_morning_digest(bot, channel_id: str):
    """Post every unposted recommendation to the channel."""
    from . import db_reader, formatter

    recs = db_reader.get_unposted_recommendations()
    if not recs:
        logger.info("Morning digest: no new recommendations to post.")
        return

    logger.info(f"Morning digest: posting {len(recs)} recommendations.")
    for rec in recs:
        text = formatter.format_recommendation(rec)
        try:
            await bot.send_message(
                chat_id=channel_id,
                text=text,
                parse_mode="HTML",
            )
            db_reader.mark_as_posted(rec["id"])
        except Exception as e:
            logger.error(f"Failed to send recommendation {rec['id']} ({rec['ticker']}): {e}")


async def _post_evening_summary(bot, channel_id: str):
    """Post portfolio long/short summary to the channel."""
    from . import db_reader, formatter

    data = db_reader.get_latest_scoring_summary()
    if not data:
        logger.info("Evening summary: no scoring data available.")
        return

    text = formatter.format_portfolio_summary(data)
    try:
        await bot.send_message(
            chat_id=channel_id,
            text=text,
            parse_mode="HTML",
        )
        logger.info("Evening summary posted.")
    except Exception as e:
        logger.error(f"Failed to post evening summary: {e}")


def build_scheduler(bot, channel_id: str) -> AsyncIOScheduler:
    """
    Create and return a configured AsyncIOScheduler.
    Call scheduler.start() after the bot is running.
    """
    scheduler = AsyncIOScheduler(timezone=MOSCOW_TZ)

    scheduler.add_job(
        _post_morning_digest,
        trigger=CronTrigger(hour=9, minute=0, timezone=MOSCOW_TZ),
        args=[bot, channel_id],
        id="morning_digest",
        name="Morning recommendations digest",
        replace_existing=True,
    )

    scheduler.add_job(
        _post_evening_summary,
        trigger=CronTrigger(hour=18, minute=0, timezone=MOSCOW_TZ),
        args=[bot, channel_id],
        id="evening_summary",
        name="Evening portfolio summary",
        replace_existing=True,
    )

    return scheduler
