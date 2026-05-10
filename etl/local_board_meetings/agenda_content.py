from __future__ import annotations

import re
from dataclasses import dataclass
from io import BytesIO
from typing import Iterable

from bs4 import BeautifulSoup


@dataclass(frozen=True)
class AgendaDetails:
    location: str = ""
    virtual_url: str = ""


_URL_RE = re.compile(r"https?://[^\s<>)\"']+", re.IGNORECASE)
_ADDRESS_RE = re.compile(
    r"\b\d{2,6}\s+[A-Za-z0-9.' -]+"
    r"\b(?:Street|St\.?|Avenue|Ave\.?|Road|Rd\.?|Drive|Dr\.?|Boulevard|Blvd\.?|"
    r"Way|Lane|Ln\.?|Court|Ct\.?|Circle|Cir\.?|Parkway|Pkwy\.?|Highway|Hwy\.?|"
    r"Plaza|Place|Pl\.?)\b",
    re.IGNORECASE,
)
_LOCATION_MARKER_RE = re.compile(
    r"\b(?:location|meeting location|in[- ]person|attend in person|address|place|where)\b",
    re.IGNORECASE,
)
_NOISE_RE = re.compile(
    r"\b(?:agenda|packet|minutes|page\s+\d+|public comment|http|www\.|@|password|passcode|meeting id)\b",
    re.IGNORECASE,
)


def extract_agenda_details(content: bytes, content_type: str = "", source_url: str = "") -> AgendaDetails:
    text = _extract_text(content, content_type, source_url)
    return extract_details_from_text(text)


def extract_details_from_text(text: str) -> AgendaDetails:
    lines = _clean_lines(text)
    return AgendaDetails(location=_find_location(lines), virtual_url=_find_virtual_url("\n".join(lines)))


def _extract_text(content: bytes, content_type: str, source_url: str) -> str:
    lowered = f"{content_type} {source_url}".lower()
    if ".pdf" in lowered or "application/pdf" in lowered:
        return _extract_pdf_text(content)
    soup = BeautifulSoup(content, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    text = soup.get_text("\n", strip=True)
    if text:
        return text
    return content.decode("utf-8", errors="replace")


def _extract_pdf_text(content: bytes) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        return ""
    try:
        reader = PdfReader(BytesIO(content))
    except Exception:
        return ""
    page_text: list[str] = []
    for page in reader.pages[:5]:
        try:
            page_text.append(page.extract_text() or "")
        except Exception:
            continue
    return "\n".join(page_text)


def _clean_lines(text: str) -> list[str]:
    normalized = text.replace("\xa0", " ")
    lines = []
    for raw in normalized.splitlines():
        line = re.sub(r"\s+", " ", raw).strip(" \t\r:-")
        if line:
            lines.append(line)
    return lines


def _find_virtual_url(text: str) -> str:
    urls = [_strip_url(url) for url in _URL_RE.findall(text)]
    preferred = [url for url in urls if any(token in url.lower() for token in ("zoom.us", "teams.microsoft.com", "meet.google.com"))]
    return (preferred or [""])[0]


def _strip_url(url: str) -> str:
    return url.rstrip(".,;:]}")


def _find_location(lines: list[str]) -> str:
    for index, line in enumerate(lines):
        if _LOCATION_MARKER_RE.search(line):
            candidate = _location_after_marker(line)
            if _is_location_candidate(candidate):
                return candidate
            block = _join_location_block(lines[index + 1 : index + 5])
            if block:
                return block
    for index, line in enumerate(lines):
        if _ADDRESS_RE.search(line):
            previous = lines[index - 1] if index > 0 else ""
            if _is_location_candidate(previous) and not _ADDRESS_RE.search(previous):
                return _compact_location([previous, line])
            return line
    return ""


def _location_after_marker(line: str) -> str:
    match = re.search(r"(?:location|meeting location|address|place|where)\s*[:\-]\s*(.+)", line, re.IGNORECASE)
    return match.group(1).strip() if match else ""


def _join_location_block(lines: Iterable[str]) -> str:
    parts: list[str] = []
    for line in lines:
        if _is_block_boundary(line):
            break
        if _is_location_candidate(line) or _ADDRESS_RE.search(line):
            parts.append(line)
        if _ADDRESS_RE.search(line):
            break
    return _compact_location(parts)


def _is_block_boundary(line: str) -> bool:
    return bool(re.search(r"\b(?:zoom|teams|virtual|agenda item|call to order|public comment)\b", line, re.IGNORECASE))


def _is_location_candidate(line: str) -> bool:
    if not line or len(line) < 5 or len(line) > 180:
        return False
    if _NOISE_RE.search(line):
        return False
    return bool(_ADDRESS_RE.search(line) or re.search(r"\b(?:room|suite|board room|conference|hall|center|office|chambers)\b", line, re.IGNORECASE))


def _compact_location(parts: Iterable[str]) -> str:
    cleaned: list[str] = []
    for part in parts:
        if part and part not in cleaned:
            cleaned.append(part)
    return ", ".join(cleaned)
