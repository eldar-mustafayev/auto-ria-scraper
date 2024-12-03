import asyncio
import logging

from telegram import Update
from telegram.ext import AIORateLimiter, ApplicationBuilder, CommandHandler, ContextTypes

from src.scraper import run as run_scraper
from src.settings import settings
from src.subscription import SUBSCRIBERS, upload_subscribers

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id # type: ignore
    if chat_id not in SUBSCRIBERS:
        SUBSCRIBERS.add(chat_id)
        await update.message.reply_text("You are now subscribed to car updates!") # type: ignore
        logger.info(f"New subscriber added: {chat_id}")
    else:
        await update.message.reply_text("You are already subscribed!") # type: ignore


# Command: Stop
async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id # type: ignore
    if chat_id in SUBSCRIBERS:
        SUBSCRIBERS.remove(chat_id)
        await update.message.reply_text("You have been unsubscribed from car updates.") # type: ignore
        logger.info(f"Subscriber removed: {chat_id}")
    else:
        await update.message.reply_text("You are not subscribed.") # type: ignore


async def start_scraper_task(context: ContextTypes.DEFAULT_TYPE):
    while True:
        try:
            logger.info("Running the scraper...")
            await run_scraper(context.bot)
        except Exception as e:
            logger.error(f"Error in scraper: {e}")

        await asyncio.sleep(600)


if __name__ == "__main__":
    application = ApplicationBuilder().rate_limiter(AIORateLimiter()).token(settings.BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stop", stop))

    application.job_queue.run_repeating(start_scraper_task, interval=600, first=5) # type: ignore

    try:
        logger.info("Starting the bot...")
        application.run_polling()
    finally:
        upload_subscribers()
        logger.info("Shutting down the bot...")
