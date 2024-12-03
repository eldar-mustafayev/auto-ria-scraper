SUBSCRIBERS_FILE = "subscribers.txt"


def load_subscribers():
    try:
        with open(SUBSCRIBERS_FILE) as file:
            return set(map(int, file.readlines()))
    except FileNotFoundError:
        return set()


def upload_subscribers():
    with open(SUBSCRIBERS_FILE, "w") as file:
        for subscriber in SUBSCRIBERS:
            file.write(f"{subscriber}\n")


SUBSCRIBERS = load_subscribers()
