import requests
from bs4 import BeautifulSoup


HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}

MAX_CHARS = 8000  # cap per URL to avoid token overload


def scrape_url(url: str) -> str:
    """Fetch and extract clean text from a URL using requests + BeautifulSoup."""
    if not url:
        return ""
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")

        # Remove noise
        for tag in soup(["script", "style", "nav", "footer", "header",
                          "aside", "form", "iframe", "noscript"]):
            tag.decompose()

        text = soup.get_text(separator="\n", strip=True)
        lines = [line.strip() for line in text.splitlines() if len(line.strip()) > 40]
        clean = "\n".join(lines)
        return clean[:MAX_CHARS]

    except Exception as e:
        return f"[Scrape error for {url}: {str(e)}]"


def scrape_multiple(urls: list[str]) -> str:
    """Scrape a list of URLs and concatenate results."""
    results = []
    for url in urls:
        if url:
            content = scrape_url(url)
            results.append(f"--- Source: {url} ---\n{content}")
    return "\n\n".join(results)
