import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time
import requests
from bs4 import BeautifulSoup
from urllib import robotparser
from urllib.parse import urljoin
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session
from models import get_engine, Book
from datetime import datetime

db_engine = get_engine()
SessionLocal = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)


BASE_URL = "http://books.toscrape.com/"


class RespectfulSession:
    """
    Session wrapper that respects robots.txt and enforces simple throttling.
    """

    def __init__(self, base_url, delay=1.0, user_agent="MyScraperBot/1.0"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": user_agent})
        self.delay = delay
        self._last_request = None
        # robots parser
        self.rp = robotparser.RobotFileParser()
        self.rp.set_url(urljoin(self.base_url, "robots.txt"))
        try:
            self.rp.read()
        except Exception:
            # if robots.txt cannot be read assume allowed, but you may want to fail
            pass

    def get(self, path):
        url = urljoin(self.base_url, path)
        if not self.rp.can_fetch(self.session.headers["User-Agent"], url):
            raise PermissionError(f"Fetching disallowed by robots.txt: {url}")
        # simple throttling
        now = time.time()
        if self._last_request is not None:
            elapsed = now - self._last_request
            if elapsed < self.delay:
                time.sleep(self.delay - elapsed)
        resp = self.session.get(url, timeout=15)
        resp.raise_for_status()
        self._last_request = time.time()
        return resp


def parse_book_page(soup):
    title = soup.select_one(".product_main h1").get_text(strip=True)

    raw_price = soup.select_one(".price_color").get_text(strip=True)

    # Fix encoding issues (Â£)
    try:
        raw_price = raw_price.encode("latin1").decode("utf-8")
    except Exception:
        pass  # fallback

    price = float(
        raw_price.replace("£", "")
        .replace("Â£", "")
        .replace("â‚¤", "")  # rare mis-decoding
        .strip()
    )

    availability = soup.select_one(".availability").get_text(strip=True)
    return title, price, availability


def scrape_one_book(relative_url, session: RespectfulSession, db_engine):
    resp = session.get(relative_url)
    soup = BeautifulSoup(resp.text, "html.parser")
    title, price, availability = parse_book_page(soup)
    full_url = urljoin(session.base_url, relative_url)
    # store in DB
    from sqlalchemy.orm import sessionmaker


SessionLocal = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)


def save_book(db_engine, title, price, availability, full_url):
    SessionLocal = sessionmaker(bind=db_engine, autoflush=False, autocommit=False)
    session = SessionLocal()
    try:
        book = Book(
            title=title,
            price=price,
            availability=availability,
            url=full_url,
            scraped_at=datetime.utcnow(),
        )
        session.add(book)
        session.commit()
    except Exception as e:
        print("DB insert error:", e)
        session.rollback()
    finally:
        session.close()
    return {
        "title": title,
        "price": price,
        "availability": availability,
        "url": full_url,
    }


def scrape_catalog(page_limit=2, delay=1.0, db_path="sqlite:///scraper_data.db"):
    engine = get_engine(db_path)
    session = RespectfulSession(BASE_URL, delay=delay)
    results = []
    # Example: walk the first `page_limit` pages of the catalog
    for page in range(1, page_limit + 1):
        path = f"catalogue/page-{page}.html" if page > 1 else ""
        # root page is BASE_URL
        path = path or ""
        try:
            resp = session.get(path)
        except PermissionError as e:
            print("Robots.txt blocked:", e)
            break
        soup = BeautifulSoup(resp.text, "html.parser")
        # find book links
        for article in soup.select("article.product_pod"):
            a = article.select_one("h3 a")
            rel = a.get("href")
            # some links are like '../../../travel_2/...' — normalize using urljoin
            # The fuller link for book page typically lives under 'catalogue/...'
            # Many links are relative; requests + urljoin inside scrape_one_book handles it.
            # Clean the relative url: replace '../../..' etc by removing '../' segments.
            # Simplest approach here is to join with current page URL:
            book_rel = rel
            # On this site relative links often need 'catalogue/' insertion for pages > root:
            if "catalogue/" not in book_rel:
                book_rel = "catalogue/" + book_rel
            try:
                item = scrape_one_book(book_rel, session, engine)
                results.append(item)
                print("Scraped:", item["title"])
            except Exception as ex:
                print("Failed to scrape item:", ex)
    return results


if __name__ == "__main__":
    # simple run
    scraped = scrape_catalog(page_limit=1, delay=1.5)
    print(f"Scraped {len(scraped)} books.")
