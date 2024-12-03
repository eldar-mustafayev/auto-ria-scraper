from datetime import datetime

from lxml.html import HtmlElement


def get_text(element: HtmlElement, selector: str) -> str:
    try:
        return element.cssselect(selector)[0].text_content().strip()
    except AttributeError:
        return ""


def get_int_attr(element: HtmlElement, selector: str, attr: str) -> int:
    return int(element.cssselect(selector)[0].attrib[attr])


def get_attr(element: HtmlElement, selector: str, attr: str, last=False) -> str:
    try:
        return element.cssselect(selector)[0 - last].attrib[attr].strip()
    except AttributeError:
        return ""


def get_datetime_attr(element: HtmlElement, selector: str, attr: str, last=False) -> datetime:
    return datetime.fromisoformat(get_attr(element, selector, attr, last))


def try_get_text(element: HtmlElement, selector: str):
    try:
        return element.cssselect(selector)[0].text.strip()
    except IndexError:
        return None


def try_get_attr(element: HtmlElement, selector: str, attr: str):
    try:
        return get_attr(element, selector, attr)
    except IndexError:
        return None
