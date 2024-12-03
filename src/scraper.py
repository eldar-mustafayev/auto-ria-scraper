import asyncio
import logging
from datetime import datetime

import requests
from aiohttp import ClientSession
from lxml.html import HtmlElement, fromstring

from src.db.crud import get_cars_by_ids
from src.db.models import ImageSourceEnum
from src.db.models.car_images import CarImages
from src.db.models.cars import Cars, OriginCountryEnum
from src.db.session import LocalAsyncSession
from src.notifications import notify_about_new_cars, notify_about_price_change, notify_about_sold_car
from src.settings import BASE_URL, settings
from src.utils import get_datetime_attr, get_int_attr, get_text, try_get_text

logger = logging.getLogger(__name__)

page_processing_sema = asyncio.Semaphore(settings.MAX_PARALLEL_PIPELINE_WORKERS)
image_retrival_sema = asyncio.Semaphore(settings.MAX_PARALLEL_PIPELINE_WORKERS)

PARSED_CAR_IDS = set()


def get_cars_page(pagenum=0) -> str:
    logger.info(f"Fetching cars page {pagenum}")
    params = {
        "categories.main.id": 1,
        "brand.id[0]": 79,
        "model.id[0]": 2104,
        "country.import.usa.not": -1,
        "price.currency": 1,
        "sort[0].order": "dates.created.desc",
        "abroad.not": 0,
        "custom.not": 1,
        "page": pagenum,
        "size": 100,
    }

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    }

    response = requests.get(BASE_URL + "/search/", params=params, headers=headers)
    response.raise_for_status()

    return response.text


def extract_cars_data(parser: HtmlElement) -> dict[int, Cars]:
    logger.info("Extracting cars data from page")
    car_element_list = parser.cssselect(".ticket-item")

    cars = {}
    for car_element in car_element_list:
        basic_info_element = car_element.cssselect("div")[0]
        content_element = car_element.cssselect(".content")[0]

        car = Cars(
            origin_country=OriginCountryEnum.US.value,
            had_accident=True,
            id=int(basic_info_element.attrib["data-id"]),
            link=basic_info_element.attrib["data-link-to-view"].strip(),
            brand=basic_info_element.attrib["data-mark-name"].strip(),
            model=basic_info_element.attrib["data-model-name"].strip(),
            year=int(basic_info_element.attrib["data-year"]),
            generation=basic_info_element.attrib["data-generation-name"].strip(),
            engine=basic_info_element.attrib["data-modification-name"].strip(),
            price=get_int_attr(content_element, ".price-ticket", "data-main-price"),
            fueltype=get_text(content_element, "li:has(.icon-fuel)"),
            millage=get_text(content_element, "li:has(.icon-mileage)"),
            location=get_text(content_element, "li:has(.icon-location)").removesuffix(" ( от )"),
            gearbox=get_text(content_element, "li:has(.icon-akp)"),
            ua_number=try_get_text(content_element, ".state-num"),
            vin=try_get_text(content_element, ".label-vin span, .vin-code"),
            description=get_text(content_element, ".descriptions-ticket > span"),
        )

        if car_element.cssselect(".sold-out"):
            sale_datetime = get_datetime_attr(car_element, ".footer_ticket > span", "data-sold-date")
            car.is_sold = True
            car.creation_datetime = sale_datetime
            car.update_datetime = sale_datetime
        else:
            car.is_sold = False
            car.creation_datetime = get_datetime_attr(car_element, ".footer_ticket > span", "data-add-date")
            car.update_datetime = get_datetime_attr(car_element, ".footer_ticket > span", "data-update-date")

        cars[car.id] = car

    logger.info(f"Extracted {len(cars)} cars")
    return cars


async def set_car_images(session: ClientSession, car: Cars):
    async with image_retrival_sema:
        logger.info(f"Fetching images for car {car.id}")
        async with session.get(car.link) as response:
            html = await response.text()

        parser = fromstring(html)
        image_elements = parser.cssselect(".photo-620x465 source")
        car.images = [
            CarImages(
                image_url=element.attrib["srcset"],
                source=ImageSourceEnum.AUTO_RIA.value,
                car_id=car.id,
            )
            for element in image_elements
        ]
        logger.info(f"Fetched {len(car.images)} images for car {car.id}")


async def set_all_car_images(cars: list[Cars]):
    async with ClientSession(BASE_URL) as session:
        coros = [set_car_images(session, car) for car in cars]
        await asyncio.gather(*coros)


async def send_update_cars_data(bot, cars_dict: dict[int, Cars]):
    async with LocalAsyncSession.begin() as session:
        car_records = await get_cars_by_ids(session, cars_dict.keys())

        for car_record in car_records:
            car = cars_dict.pop(car_record.id)

            if car.price != car_record.price:
                await notify_about_price_change(bot, car, car_record.price)
                car_record.price = car.price
                logger.info(f"Price changed for car {car.id}")

            if car.is_sold > car_record.is_sold:
                await notify_about_sold_car(bot, car)
                car_record.is_sold = True
                logger.info(f"Car {car.id} is sold")


async def send_store_cars_data(bot, cars_dict: dict[int, Cars]):
    cars = list(cars_dict.values())
    if not cars:
        return

    await set_all_car_images(cars)
    await notify_about_new_cars(bot, cars)
    logger.info(f"Storing {len(cars)} new cars")

    async with LocalAsyncSession.begin() as session:
        session.add_all(cars)


async def consumer(bot, parser: HtmlElement):
    global PARSED_CAR_IDS
    async with page_processing_sema:
        cars_dict = extract_cars_data(parser)
        PARSED_CAR_IDS.update(cars_dict.keys())

        await send_update_cars_data(bot, cars_dict)
        await send_store_cars_data(bot, cars_dict)


def get_latest_run_time() -> datetime:
    try:
        with open("latest_run_time.txt") as file:
            return datetime.fromtimestamp(float(file.read()))
    except FileNotFoundError:
        return datetime.min


def producer() -> list[HtmlElement]:
    oldest_listing_datetime = datetime.now()
    latest_run_time = get_latest_run_time()

    pagenum = 0
    parsers = []
    while oldest_listing_datetime > latest_run_time:
        html = get_cars_page(pagenum)
        parser = fromstring(html)

        try:
            oldest_listing_datetime = get_datetime_attr(
                parser, ".footer_ticket > span[data-update-date]", "data-update-date", last=True
            )
        except IndexError:
            break

        parsers.append(parser)
        pagenum += 1

    logger.info(f"Fetched {len(parsers)} pages")
    return parsers


async def run(bot):
    parsers = producer()
    coros = [consumer(bot, parser) for parser in parsers]
    await asyncio.gather(*coros)

    with open("latest_run_time.txt", "w") as file:
        file.write(str(datetime.now().timestamp()))

    async with LocalAsyncSession.begin() as session:
        cars = await get_cars_by_ids(session, PARSED_CAR_IDS, inverse=True)
        for car in cars:
            await notify_about_sold_car(bot, car)
            logger.info(f"Car {car.id} is sold")
