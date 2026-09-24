from __future__ import annotations

import logging
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from dataclasses import dataclass
from functools import lru_cache

LOGGER = logging.getLogger(__name__)
USER_AGENT = "Mozilla/5.0 (compatible; CWA-local-board-meeting-monitor/0.1; +https://calworkforce.org)"
ROBOTS_TIMEOUT_SECONDS = 5
ROBOTS_MAX_BYTES = 256 * 1024
DEFAULT_MAX_BYTES = 25 * 1024 * 1024


@dataclass(frozen=True)
class FetchedPage:
    url: str
    status: int
    content_type: str
    body: bytes

    @property
    def text(self) -> str:
        return self.body.decode("utf-8", errors="replace")


@lru_cache(maxsize=256)
def _robots_for(base_url: str) -> urllib.robotparser.RobotFileParser:
    parsed = urllib.parse.urlparse(base_url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
    rp = urllib.robotparser.RobotFileParser()
    rp.set_url(robots_url)
    try:
        req = urllib.request.Request(robots_url, headers={"User-Agent": USER_AGENT, "Accept": "text/plain,*/*;q=0.8"})
        with urllib.request.urlopen(req, timeout=ROBOTS_TIMEOUT_SECONDS) as resp:
            body = resp.read(ROBOTS_MAX_BYTES)
        rp.parse(body.decode("utf-8", errors="replace").splitlines())
    except Exception as exc:  # robots.txt fetch failures should not halt official public pages.
        LOGGER.debug("Could not read robots.txt %s: %s", robots_url, exc)
    return rp


def can_fetch(url: str) -> bool:
    rp = _robots_for(url)
    if rp.mtime() == 0:
        return True
    return rp.can_fetch(USER_AGENT, url)


def fetch_url(
    url: str,
    timeout: int = 8,
    retries: int = 1,
    respect_robots: bool = True,
    extra_headers: dict[str, str] | None = None,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> FetchedPage:
    # Public ICS feeds are explicit machine-consumption endpoints, not crawlable
    # web pages. Google Calendar's site-wide robots rule covers its UI but would
    # otherwise make a published subscription feed unusable by calendar clients.
    if respect_robots and not _is_public_calendar_feed(url) and not can_fetch(url):
        raise PermissionError(f"robots.txt disallows fetching {url}")
    headers = {"User-Agent": USER_AGENT, "Accept": "text/calendar,text/html,application/pdf,*/*;q=0.8"}
    if extra_headers:
        headers.update(extra_headers)
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                content_length = int(resp.headers.get("content-length", "0") or 0)
                if content_length > max_bytes:
                    raise ValueError(f"Response exceeds {max_bytes} byte safety limit: {url}")
                body = resp.read(max_bytes + 1)
                if len(body) > max_bytes:
                    raise ValueError(f"Response exceeds {max_bytes} byte safety limit: {url}")
                return FetchedPage(
                    url=resp.geturl(),
                    status=resp.status,
                    content_type=resp.headers.get("content-type", ""),
                    body=body,
                )
        except (urllib.error.URLError, TimeoutError, PermissionError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(2**attempt)
    assert last_error is not None
    if _should_try_curl(last_error):
        return _fetch_with_curl(url, timeout, extra_headers or {}, max_bytes)
    raise last_error


def absolute_url(base_url: str, href: str) -> str:
    return urllib.parse.urljoin(base_url, href)


def _is_public_calendar_feed(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    return (
        parsed.scheme == "https"
        and parsed.hostname in {"calendar.google.com", "www.google.com"}
        and "/calendar/ical/" in parsed.path
        and parsed.path.endswith("/public/basic.ics")
    )


def _should_try_curl(exc: Exception) -> bool:
    if isinstance(exc, PermissionError):
        return False
    if isinstance(exc, urllib.error.HTTPError):
        return False
    return isinstance(exc, (urllib.error.URLError, TimeoutError))


def _fetch_with_curl(
    url: str,
    timeout: int,
    extra_headers: dict[str, str] | None = None,
    max_bytes: int = DEFAULT_MAX_BYTES,
) -> FetchedPage:
    cmd = [
        "curl",
        "-L",
        "--fail",
        "--silent",
        "--show-error",
        "--max-time",
        str(timeout),
        "--max-filesize",
        str(max_bytes),
        "-A",
        USER_AGENT,
        "-H",
        "Accept: text/html,application/pdf,*/*;q=0.8",
    ]
    for name, value in (extra_headers or {}).items():
        cmd.extend(["-H", f"{name}: {value}"])
    cmd.append(url)
    result = subprocess.run(cmd, capture_output=True, check=True)
    return FetchedPage(url=url, status=200, content_type=_guess_content_type(url, result.stdout), body=result.stdout)


def _guess_content_type(url: str, body: bytes) -> str:
    if url.lower().split("?", 1)[0].endswith(".pdf") or body.startswith(b"%PDF"):
        return "application/pdf"
    return "text/html"
