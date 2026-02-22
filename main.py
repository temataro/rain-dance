import json
import re
import xml.etree.ElementTree as ET

import requests

from time import sleep
from pathlib import Path
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from datetime import date, datetime, timedelta

SITEMAP_NAMESPACE = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
OUTPUT_ROOT = Path("data/gulfnews/articles")
ANSI_RESET = "\033[0m"
ANSI_BOLD = "\033[1m"
ANSI_INFO = "\033[38;5;39m"
ANSI_FETCH = "\033[38;5;214m"
ANSI_WARN = "\033[38;5;196m"
ANSI_DONE = "\033[38;5;82m"
ANSI_DIM = "\033[38;5;244m"
TITLE_KEYWORDS = (
    " rain ",
    " rainfall ",
    " precipitation ",
    " downpour ",
    " drizzle ",
    " weather ",
    " shower ",
    " storm ",
    " thunderstorm ",
    " hail ",
    " flood ",
)


class SitemapEntry:
    def __init__(self, url, lastmod):
        self.url = url
        self.lastmod = lastmod


def fetch_text(url, *, timeout_s=30):
    response = requests.get(
        url,
        timeout=timeout_s,
        headers={"User-Agent": "news-fetcher"},
    )
    response.raise_for_status()

    return response.text


def parse_date(value):
    if isinstance(value, date):
        return value

    return date.fromisoformat(value)


def parse_lastmod(value):
    """
    Get the last modified date of an entry.
    """

    if not value:
        return None
    normalized = value.strip().replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized).date()
    except ValueError:
        return None


def parse_sitemap(xml_text):
    root = ET.fromstring(xml_text)
    entries = []
    for url_node in root.findall("sm:url", SITEMAP_NAMESPACE):
        loc_node = url_node.find("sm:loc", SITEMAP_NAMESPACE)
        if loc_node is None or not loc_node.text:
            continue
        lastmod_node = url_node.find("sm:lastmod", SITEMAP_NAMESPACE)
        lastmod = parse_lastmod(lastmod_node.text if lastmod_node is not None else None)
        entries.append(SitemapEntry(url=loc_node.text.strip(), lastmod=lastmod))
    return entries


def title_matches_keywords(title, keywords=TITLE_KEYWORDS):
    for keyword in keywords:
        if keyword in title:
            return True
    return False


def extract_title(soup):
    meta_title = soup.find("meta", attrs={"property": "og:title"})
    if meta_title and meta_title.get("content"):
        content = meta_title.get("content")
        if isinstance(content, list):
            content = " ".join(content)
        if isinstance(content, str):
            return content.strip()
    if soup.title and soup.title.string:
        return soup.title.string.strip()
    h1 = soup.find("h1")
    if h1:
        title_text = h1.get_text(strip=True)
        if title_text:
            return title_text
    return None


def extract_article_text(soup):
    for script in soup.find_all("script", attrs={"type": "application/ld+json"}):
        if not script.string:
            continue
        try:
            data = json.loads(script.string)
        except json.JSONDecodeError:
            continue
        candidates = data if isinstance(data, list) else [data]
        for item in candidates:
            if not isinstance(item, dict):
                continue
            article_body = item.get("articleBody")
            if isinstance(article_body, str) and article_body.strip():
                return normalize_text(article_body)

    article = soup.find("article")
    if article:
        text = "\n\n".join(
            part.get_text(" ", strip=True)
            for part in article.find_all("p")
            if part.get_text(strip=True)
        )
        if text:
            return normalize_text(text)

    main = soup.find("main")
    if main:
        text = "\n\n".join(
            part.get_text(" ", strip=True)
            for part in main.find_all("p")
            if part.get_text(strip=True)
        )
        if text:
            return normalize_text(text)

    paragraphs = soup.find_all("p")
    text = "\n\n".join(
        part.get_text(" ", strip=True)
        for part in paragraphs
        if part.get_text(strip=True)
    )
    return normalize_text(text) if text else None


def normalize_text(value):
    cleaned = re.sub(r"\s+", " ", value).strip()
    return cleaned


def output_path_for_sitemap(sitemap_date, output_root=OUTPUT_ROOT):
    month_dir = output_root / sitemap_date[:-3]
    filename = f"sitemap-{sitemap_date}.jsonl"
    return month_dir / filename


def extract_sitemap_urls_to_jsonl(
    start_date,
    end_date,
    output_root=OUTPUT_ROOT,
    request_delay_s=0.5,
    force=False,
):
    output_path = None
    header = (
        f"{ANSI_INFO}╔══════════════════════════════════════════════╗{ANSI_RESET}\n"
        f"{ANSI_INFO}║{ANSI_RESET} {ANSI_BOLD}Gulf News Extraction Console{ANSI_RESET}           {ANSI_INFO}║{ANSI_RESET}\n"
        f"{ANSI_INFO}╚══════════════════════════════════════════════╝{ANSI_RESET}"
    )
    print(header, flush=True)

    # We'll generate a sitemap url based on the format of the website:
    #    "https://gulfnews.com/sitemap/sitemap-daily-2026-02-21.xml"
    prefix = "https://gulfnews.com/sitemap/sitemap-daily"

    current_date = parse_date(start_date)
    end = parse_date(end_date)

    while current_date < end:
        sitemap_url = f"{prefix}-{current_date.isoformat()}.xml"
        sitemap_date = current_date.isoformat()
        output_path = output_path_for_sitemap(sitemap_date, output_root=output_root)
        # This prevents us from re-bothering the server for data we've already
        # collected, unless the force option is passed.
        if output_path.exists() and not force:
            return output_path

        xml_text = fetch_text(sitemap_url)
        entries = parse_sitemap(xml_text)
        total = len(entries)
        counter = 0
        print(
            f"{ANSI_INFO}[INFO]{ANSI_RESET} "
            f"Date: {ANSI_BOLD}{sitemap_date}{ANSI_RESET} | "
            f"Entries: {ANSI_BOLD}{total}{ANSI_RESET}",
            flush=True,
        )

        # Make a different JSONL for each month of entries that've been filtered
        # through.
        output_path.parent.mkdir(parents=True, exist_ok=True)

        matches = 0
        with output_path.open("w", encoding="utf-8") as handle:
            for entry in entries:
                counter += 1
                progress = f"{counter}/{total}" if total else "0/0"
                print(
                    f"\r{ANSI_FETCH}[FETCH]{ANSI_RESET} "
                    f"{ANSI_BOLD}{progress}{ANSI_RESET} "
                    f"{ANSI_DIM}{current_date}{ANSI_RESET}",
                    end="",
                    flush=True,
                )
                html_text = fetch_text(entry.url)
                soup = BeautifulSoup(html_text, "html.parser")
                title = extract_title(soup)
                if title == "":
                    print(f"\n{ANSI_WARN}[WARN]{ANSI_RESET} Empty title", flush=True)
                matched = title_matches_keywords(title)
                if matched:
                    matches += 1
                    article_text = extract_article_text(soup)
                else:
                    article_text = None
                handle.write(
                    json.dumps(
                        {
                            "url": entry.url,
                            "lastmod": (
                                entry.lastmod.isoformat() if entry.lastmod else None
                            ),
                            "title": title,
                            "title_matches_keywords": matched,
                            "text": article_text,
                        }
                    )
                    + "\n"
                )
                if request_delay_s:
                    sleep(request_delay_s)
            print(
                f"\r{ANSI_DONE}[DONE]{ANSI_RESET} Day complete with #{matches=}",
                flush=True,
            )

        current_date += timedelta(days=1)

    return output_path


def main():
    extract_sitemap_urls_to_jsonl(
        start_date="2020-01-01",
        end_date="2026-01-01",
    )


if __name__ == "__main__":
    main()
