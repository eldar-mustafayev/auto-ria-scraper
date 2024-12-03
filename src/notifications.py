import asyncio
import logging
import re
from collections import defaultdict

from telegram import InputMediaPhoto
from telegram.ext import ExtBot

from src.db.models import Cars
from src.settings import BASE_URL
from src.subscription import SUBSCRIBERS

logger = logging.getLogger(__name__)
lock_dict = defaultdict(asyncio.Lock)


def retry(max_tries: int = 10, ignore=True):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            error = Exception("Max retries exceeded")
            for i in range(max_tries):
                try:
                    return await func(*args, **kwargs)
                except Exception as exc:
                    error = exc
                    exc_msg = str(exc)
                    if "Flood control exceeded" in exc_msg:
                        match = re.search(r"Retry in (\d+) seconds", exc_msg)
                        timeout = int(match.group(1)) if match else 5

                        logger.warning("Flood control exceeded. Retrying in %s seconds...", timeout)
                        await asyncio.sleep(timeout)
                    else:
                        logger.warning(f"Failed to execute {func.__name__}, trying again: {exc}")

            if not ignore:
                raise error

        return wrapper

    return decorator


@retry(10)
async def notify_subscriber(bot: ExtBot, chat_id, message: str, media=None) -> None:
    async with lock_dict[chat_id]:
        if media:
            await bot.send_media_group(chat_id=chat_id, media=media)
        await bot.send_message(chat_id=chat_id, text=message)


async def notify_subscribers(bot: ExtBot, message: str, media=None) -> None:
    for chat_id in SUBSCRIBERS:
        await notify_subscriber(bot, chat_id, message, media)


async def notify_about_new_cars(bot: ExtBot, cars: list[Cars]):
    for car in cars:
        message = (
            f"🚗 New Car Alert! 🚗\n\n"
            f"Brand: {car.brand}\n"
            f"Model: {car.model}\n"
            f"Year: {car.year}\n"
            f"Price: ${car.price}\n"
            f"Location: {car.location}\n"
            f"Link: {BASE_URL}{car.link}\n"
        )

        # Prepare images
        media = [InputMediaPhoto(image.image_url) for image in car.images[:10]]
        await notify_subscribers(bot, message, media)


async def notify_about_sold_car(bot: ExtBot, car: Cars):
    message = (
        f"🚨 Sold Car Alert! 🚨\n\n"
        f"Brand: {car.brand}\n"
        f"Model: {car.model}\n"
        f"Year: {car.year}\n"
        f"Price: ${car.price}\n"
        f"Location: {car.location}\n"
        f"Sold on: {car.update_datetime.strftime('%Y-%m-%d %H:%M:%S')}\n"
    )

    media = [InputMediaPhoto(image.image_url) for image in car.images[:10]]
    await notify_subscribers(bot, message, media)


async def notify_about_price_change(bot: ExtBot, car: Cars, old_price: int):
    message = (
        f"📉 Price Change Alert! 📉\n\n"
        f"Brand: {car.brand}\n"
        f"Model: {car.model}\n"
        f"Year: {car.year}\n"
        f"Old Price: ${old_price}\n"
        f"New Price: ${car.price}\n"
        f"Location: {car.location}\n"
        f"Link: {BASE_URL}{car.link}\n"
    )

    # media = [InputMediaPhoto(image.image_url) for image in car.images[:10]]
    await notify_subscribers(bot, message)
