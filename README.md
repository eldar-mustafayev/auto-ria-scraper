# Auto RIA Scraping

This project is designed to scrape car data from the Auto RIA website, store it in a SQLite database, and notify subscribers about new cars, price changes, and sold cars via a Telegram bot.


## Installation

1. Clone the repository:
    ```sh
    git clone <repository-url>
    cd <repository-directory>
    ```

2. Install dependencies using Poetry:
    ```sh
    poetry install
    ```

3. Create a `.env` file with the following content:
    ```env
    ASYNC_SQLITE_URL='sqlite+aiosqlite:///database.sqlite'
    ```

## Usage

1. Initialize the database:
    ```sh
    poetry run python src/db/create.py
    ```

2. Run the scraper and bot:
    ```sh
    poetry run python src/bot.py
    ```

## Project Components

### Scraper

The scraper fetches car data from the Auto RIA website and stores it in the database. It is implemented in [`src/scraper.py`](src/scraper.py).

### Database

The database models and CRUD operations are defined in the `src/db` directory. The main components are:
- Models: [`src/db/models/cars.py`](src/db/models/cars.py)
- CRUD operations: [`src/db/crud.py`](src/db/crud.py)
- Database session: [`src/db/session.py`](src/db/session.py)

### Notifications

The notification system sends updates to subscribers via a Telegram bot. It is implemented in [`src/notifications.py`](src/notifications.py).

### Bot

The Telegram bot handles user subscriptions and sends notifications. It is implemented in [`src/bot.py`](src/bot.py).

### Settings

The project settings are defined in [`src/settings.py`](src/settings.py).

### Utilities

Utility functions are defined in [`src/utils.py`](src/utils.py).

### Subscription Management

Subscriber management is handled in [`src/subscription.py`](src/subscription.py).
