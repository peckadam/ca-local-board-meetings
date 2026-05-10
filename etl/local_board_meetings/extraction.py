from __future__ import annotations

import calendar
import re
from datetime import date, datetime, time, timedelta
from typing import Iterable, List, Optional

from bs4 import BeautifulSoup

from .fetcher import absolute_url
from .models import AgendaLink, BoardSource, Meeting

MONTH_NAMES = "|".join(calendar.month_name[1:] + calendar.month_abbr[1:])
DATE_PATTERNS = [
    re.compile(rf"\b({MONTH_NAMES})\.?\s+(\d{{1,2}})(?:st|nd|rd|th)?(?:,)?\s+(20\d{{2}})\b", re.I),
    re.compile(r"\b(20\d{2})[-/](\d{1,2})[-/](\d{1,2})\b"),
    re.compile(r"\b(\d{1,2})/(\d{1,2})/(20\d{2})\b"),
    re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{2})\b"),
    re.compile(rf"\b({MONTH_NAMES})\.?\s+(\d{{1,2}})(?:st|nd|rd|th)?\b", re.I),
]
TIME_RE = re.compile(r"\b(\d{1,2})(?::(\d{2}))?\s*([ap]\.?m\.?)\b", re.I)
AGENDA_TERMS = ("agenda", "packet", "board packet")
MEETING_TERMS = ("meeting", "board", "committee", "agenda", "minutes", "calendar")
EXEC_TERMS = ("executive", "exec committee")
EXCLUDED_LINK_HOST_TERMS = ("facebook.com", "linkedin.com", "twitter.com", "x.com", "forms.office.com", "survey")


def parse_date(text: str, reference_date: date | None = None, lookahead_days: int = 180) -> Optional[date]:
    text = " ".join(text.split())
    match = DATE_PATTERNS[0].search(text)
    if match:
        month = _month_number(match.group(1))
        return date(int(match.group(3)), month, int(match.group(2)))
    match = DATE_PATTERNS[1].search(text)
    if match:
        return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    match = DATE_PATTERNS[2].search(text)
    if match:
        return date(int(match.group(3)), int(match.group(1)), int(match.group(2)))
    match = DATE_PATTERNS[3].search(text)
    if match:
        return date(2000 + int(match.group(3)), int(match.group(1)), int(match.group(2)))
    match = DATE_PATTERNS[4].search(text)
    if match and reference_date:
        month = _month_number(match.group(1))
        day = int(match.group(2))
        candidate = date(reference_date.year, month, day)
        if candidate < reference_date - timedelta(days=14):
            candidate = date(reference_date.year + 1, month, day)
        if candidate <= reference_date + timedelta(days=lookahead_days):
            return candidate
    return None


def parse_time(text: str) -> Optional[time]:
    noon_match = re.search(r"\bnoon\b", text, re.I)
    meridian_match = TIME_RE.search(text)
    noon_range_match = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*[–-]\s*noon\b", text, re.I)
    if noon_range_match:
        return time(int(noon_range_match.group(1)), int(noon_range_match.group(2) or "0"))
    if noon_match and (not meridian_match or noon_match.start() < meridian_match.start()):
        return time(12, 0)
    range_match = re.search(r"\b(\d{1,2})(?::(\d{2}))?\s*[–-]\s*\d{1,2}(?::\d{2})?\s*([ap])\.?m\.?", text, re.I)
    if range_match:
        hour = int(range_match.group(1))
        minute = int(range_match.group(2) or "0")
        meridian = range_match.group(3).lower()
        if meridian == "p" and hour != 12:
            hour += 12
        if meridian == "a" and hour == 12:
            hour = 0
        return time(hour, minute)
    match = TIME_RE.search(text)
    if not match:
        return None
    hour = int(match.group(1))
    minute = int(match.group(2) or "0")
    meridian = match.group(3).lower()[0]
    if meridian == "p" and hour != 12:
        hour += 12
    if meridian == "a" and hour == 12:
        hour = 0
    return time(hour, minute)


def _month_number(value: str) -> int:
    normalized = value.strip(".").lower()
    for idx, name in enumerate(calendar.month_name):
        if name and name.lower() == normalized:
            return idx
    for idx, name in enumerate(calendar.month_abbr):
        if name and name.lower() == normalized:
            return idx
    raise ValueError(f"Unknown month {value}")


def extract_agenda_links(html: str, page_url: str) -> List[AgendaLink]:
    soup = BeautifulSoup(html, "html.parser")
    links: list[AgendaLink] = []
    for anchor in soup.find_all("a", href=True):
        href = anchor["href"].strip()
        label = anchor.get_text(" ", strip=True)
        candidate = f"{label} {href}".lower()
        context_label = _agenda_context_label(anchor, label)
        if any(term in candidate for term in AGENDA_TERMS) and (
            ".pdf" in candidate or "agenda" in candidate or "packet" in candidate
        ):
            links.append(AgendaLink(absolute_url(page_url, href), label or href, page_url))
        elif ".pdf" in href.lower() and context_label:
            links.append(AgendaLink(absolute_url(page_url, href), context_label, page_url))
    return _dedupe_agendas(links)


def find_candidate_pages(html: str, page_url: str) -> dict[str, list[str]]:
    soup = BeautifulSoup(html, "html.parser")
    candidates = {"meeting": [], "agenda": [], "executive": []}
    for anchor in soup.find_all("a", href=True):
        label = anchor.get_text(" ", strip=True)
        href = anchor["href"].strip()
        if href.startswith(("mailto:", "tel:", "#")):
            continue
        combined = f"{label} {href}".lower()
        url = absolute_url(page_url, href)
        if any(term in url.lower() for term in EXCLUDED_LINK_HOST_TERMS):
            continue
        if any(term in combined for term in MEETING_TERMS):
            candidates["meeting"].append(url)
        if any(term in combined for term in AGENDA_TERMS) or "minutes" in combined:
            candidates["agenda"].append(url)
        if any(term in combined for term in EXEC_TERMS):
            candidates["executive"].append(url)
    return {key: sorted(set(value)) for key, value in candidates.items()}


def extract_meetings(
    source: BoardSource,
    html: str,
    page_url: str,
    today: date,
    lookahead_days: int,
    extraction_strategy: str = "generic",
) -> List[Meeting]:
    if extraction_strategy == "stanislaus_workforce_board":
        return extract_stanislaus_workforce_board_meetings(source, html, page_url, today, lookahead_days)
    if extraction_strategy == "south_bay_sectioned_agendas":
        return extract_south_bay_sectioned_meetings(source, html, page_url, today, lookahead_days)
    if extraction_strategy == "workforce_alliance_north_bay":
        return extract_workforce_alliance_north_bay_meetings(source, html, page_url, today, lookahead_days)
    if extraction_strategy == "santa_cruz_wfscc":
        return extract_santa_cruz_wfscc_meetings(source, html, page_url, today, lookahead_days)
    if extraction_strategy == "event_detail_title":
        return extract_event_detail_title_meeting(source, html, page_url, today, lookahead_days)
    if extraction_strategy == "alameda_acwdb":
        return extract_alameda_acwdb_meetings(source, html, page_url, today, lookahead_days)
    if extraction_strategy == "humboldt_civicengage":
        return extract_humboldt_civicengage_meetings(source, html, page_url, today, lookahead_days)
    if extraction_strategy == "foothill_events":
        return extract_foothill_events(source, html, page_url, today, lookahead_days)
    if extraction_strategy == "long_beach_lbwin_schedule":
        return extract_long_beach_lbwin_schedule(source, html, page_url, today, lookahead_days)
    if extraction_strategy == "merced_worknet":
        return extract_merced_worknet_meetings(source, html, page_url, today, lookahead_days)
    if extraction_strategy == "la_county_wdb_calendar":
        return extract_la_county_wdb_calendar(source, html, page_url, today, lookahead_days)
    soup = BeautifulSoup(html, "html.parser")
    agenda_links = extract_agenda_links(html, page_url)
    text_blocks = _candidate_text_blocks(soup)
    meetings: dict[str, Meeting] = {}
    max_date = today + timedelta(days=lookahead_days)
    for block in text_blocks:
        meeting_date = parse_date(block, today, lookahead_days)
        if not meeting_date or meeting_date < today - timedelta(days=14) or meeting_date > max_date:
            continue
        meeting_type = infer_meeting_type(block)
        linked_agenda = best_agenda_for_date(agenda_links, meeting_date)
        meeting = Meeting(
            board_id=source.board_id,
            board_name=source.board_name,
            meeting_type=meeting_type,
            meeting_date=meeting_date,
            start_time=parse_time(block),
            timezone="America/Los_Angeles",
            location=infer_location(block),
            virtual_url=infer_virtual_url(block),
            source_page_url=page_url,
            agenda_url=linked_agenda.url if linked_agenda else "",
            agenda_label=linked_agenda.label if linked_agenda else "",
            confidence_notes="Extracted from official source page text; verify manually if the source page uses embedded calendars or PDFs.",
        )
        meetings[meeting.stable_id] = meeting
    return sorted(meetings.values(), key=lambda m: (m.meeting_date, m.board_name, m.meeting_type))


def extract_stanislaus_workforce_board_meetings(
    source: BoardSource,
    html: str,
    page_url: str,
    today: date,
    lookahead_days: int,
) -> List[Meeting]:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)
    board_section = _between_markers(text, "UPCOMING BOARD MEETING", "PREVIOUS AGENDAS & MINUTES")
    if not board_section:
        return []
    meeting_date = parse_date(board_section, today, lookahead_days)
    if not meeting_date or meeting_date < today - timedelta(days=14) or meeting_date > today + timedelta(days=lookahead_days):
        return []
    agenda = _stanislaus_current_board_agenda(soup, page_url, meeting_date)
    meeting = Meeting(
        board_id=source.board_id,
        board_name=source.board_name,
        meeting_type="Board Meeting",
        meeting_date=meeting_date,
        start_time=parse_time(board_section),
        timezone="America/Los_Angeles",
        location=infer_location(board_section),
        virtual_url=infer_virtual_url(board_section),
        source_page_url=page_url,
        agenda_url=agenda.url if agenda else "",
        agenda_label=agenda.label if agenda else "",
        confidence_notes=(
            "Profiled Stanislaus extraction: uses only the Upcoming Board Meeting section and the full-board "
            "current agenda link; committee sections and historical/cancelled PDFs are excluded."
        ),
    )
    return [meeting]


def extract_south_bay_sectioned_meetings(
    source: BoardSource,
    html: str,
    page_url: str,
    today: date,
    lookahead_days: int,
) -> List[Meeting]:
    soup = BeautifulSoup(html, "html.parser")
    lines = [line.strip() for line in soup.get_text("\n", strip=True).splitlines() if line.strip()]
    section_types = {
        "BUSINESS, TECHNOLOGY & ECONOMIC DEVELOPMENT COMMITTEE": "Committee",
        "SBWIB EXECUTIVE COMMITTEE": "Executive Committee",
        "SOUTH BAY WORKFORCE INVESTMENT BOARD": "Board Meeting",
        "PERFORMANCE & EVALUATION COMMITTEE": "Committee",
        "YOUTH DEVELOPMENT COUNCIL COMMITTEE": "Committee",
        "ONE-STOP POLICY COMMITTEE": "Committee",
    }
    current_type = ""
    meetings: dict[str, Meeting] = {}
    max_date = today + timedelta(days=lookahead_days)
    in_agenda_area = False
    for line in lines:
        if line == "2026 Meeting Agendas":
            in_agenda_area = True
            continue
        if not in_agenda_area:
            continue
        if line.startswith("South Bay Workforce Investment Board"):
            break
        if line in section_types:
            current_type = section_types[line]
            continue
        meeting_date = parse_date(line, today, lookahead_days)
        if not current_type or not meeting_date:
            continue
        if meeting_date < today - timedelta(days=14) or meeting_date > max_date:
            continue
        meeting = Meeting(
            board_id=source.board_id,
            board_name=source.board_name,
            meeting_type=current_type,
            meeting_date=meeting_date,
            start_time=None,
            timezone="America/Los_Angeles",
            location="",
            virtual_url="",
            source_page_url=page_url,
            agenda_url="",
            agenda_label="",
            confidence_notes="Profiled South Bay extraction: dates are assigned to the section heading that precedes them on the annual meeting agendas page.",
        )
        meetings[meeting.stable_id] = meeting
    return sorted(meetings.values(), key=lambda m: (m.meeting_date, m.meeting_type))


def extract_workforce_alliance_north_bay_meetings(
    source: BoardSource,
    html: str,
    page_url: str,
    today: date,
    lookahead_days: int,
) -> List[Meeting]:
    sections = [
        ("Regional Workforce Development Board", "Regional Workforce Development Board Executive Committee", "Board Meeting"),
        ("Regional Workforce Development Board Executive Committee", "Communications & Outreach Committee", "Executive Committee"),
    ]
    return _extract_sectioned_line_table_meetings(source, html, page_url, today, lookahead_days, sections)


def extract_santa_cruz_wfscc_meetings(
    source: BoardSource,
    html: str,
    page_url: str,
    today: date,
    lookahead_days: int,
) -> List[Meeting]:
    sections = [
        ("FULL BOARD", "EXECUTIVE COMMITTEE", "Board Meeting"),
        ("EXECUTIVE COMMITTEE", "CAREER SERVICES COMMITTEE", "Executive Committee"),
    ]
    return _extract_sectioned_line_table_meetings(source, html, page_url, today, lookahead_days, sections)


def extract_event_detail_title_meeting(
    source: BoardSource,
    html: str,
    page_url: str,
    today: date,
    lookahead_days: int,
) -> list[Meeting]:
    soup = BeautifulSoup(html, "html.parser")
    title_text = _page_title_or_heading(soup)
    body_text = soup.get_text("\n", strip=True)
    meeting_date = parse_date(body_text, today, lookahead_days)
    if not meeting_date or meeting_date < today - timedelta(days=14) or meeting_date > today + timedelta(days=lookahead_days):
        return []
    if _looks_like_nonmeeting_event(title_text):
        return []
    meeting_type = infer_meeting_type(title_text)
    agenda = best_agenda_for_date(extract_agenda_links(html, page_url), meeting_date)
    meeting = Meeting(
        board_id=source.board_id,
        board_name=source.board_name,
        meeting_type=meeting_type,
        meeting_date=meeting_date,
        start_time=parse_time(body_text),
        timezone="America/Los_Angeles",
        location=infer_location(body_text),
        virtual_url=infer_virtual_url(body_text),
        source_page_url=page_url,
        agenda_url=agenda.url if agenda else "",
        agenda_label=agenda.label if agenda else "",
        confidence_notes="Profiled event-detail extraction: meeting type is inferred from the event title rather than surrounding page text.",
    )
    return [meeting]


def extract_alameda_acwdb_meetings(
    source: BoardSource,
    html: str,
    page_url: str,
    today: date,
    lookahead_days: int,
) -> list[Meeting]:
    soup = BeautifulSoup(html, "html.parser")
    meetings: dict[str, Meeting] = {}
    max_date = today + timedelta(days=lookahead_days)
    for anchor in soup.find_all("a", href=True):
        label = anchor.get_text(" ", strip=True)
        lowered = label.lower()
        if "quarterly board meeting" not in lowered and "executive committee" not in lowered:
            continue
        if "joint" in lowered or "organizational" in lowered or "systems" in lowered or "youth" in lowered:
            continue
        if "cancel" in lowered:
            continue
        context = anchor.parent.get_text(" ", strip=True) if anchor.parent else label
        meeting_date = parse_date(context, today, lookahead_days)
        if not meeting_date or meeting_date < today - timedelta(days=14) or meeting_date > max_date:
            continue
        meeting_type = "Executive Committee" if "executive" in lowered else "Board Meeting"
        agenda = AgendaLink(absolute_url(page_url, anchor["href"].strip()), context, page_url)
        meeting = Meeting(
            board_id=source.board_id,
            board_name=source.board_name,
            meeting_type=meeting_type,
            meeting_date=meeting_date,
            start_time=parse_time(label),
            timezone="America/Los_Angeles",
            location=_nearby_location(anchor),
            virtual_url=infer_virtual_url(anchor.parent.get_text(" ", strip=True) if anchor.parent else label),
            source_page_url=page_url,
            agenda_url=agenda.url,
            agenda_label=agenda.label,
            confidence_notes="Profiled Alameda extraction: only Quarterly Board Meeting and Executive Committee links on the official Board and Committees page are published.",
        )
        meetings[meeting.stable_id] = meeting
    return sorted(meetings.values(), key=lambda m: (m.meeting_date, m.meeting_type))


def extract_humboldt_civicengage_meetings(
    source: BoardSource,
    html: str,
    page_url: str,
    today: date,
    lookahead_days: int,
) -> list[Meeting]:
    sections = [
        ("Workforce Development Board", "Workforce Development Board Executive Committee", "Board Meeting"),
        ("Workforce Development Board Executive Committee", "Youth Council of the Workforce Investment Board", "Executive Committee"),
    ]
    return _extract_sectioned_line_table_meetings(source, html, page_url, today, lookahead_days, sections)


def extract_foothill_events(
    source: BoardSource,
    html: str,
    page_url: str,
    today: date,
    lookahead_days: int,
) -> list[Meeting]:
    soup = BeautifulSoup(html, "html.parser")
    meetings: dict[str, Meeting] = {}
    max_date = today + timedelta(days=lookahead_days)
    for anchor in soup.find_all("a", href=True):
        title = anchor.get_text(" ", strip=True)
        lowered = title.lower()
        if "fwdb" not in lowered or "meeting" not in lowered:
            continue
        if any(term in lowered for term in ("orientation", "workshop", "training")):
            continue
        container = anchor.find_parent(["article", "li", "div"])
        context = container.get_text(" ", strip=True) if container else title
        meeting_date = parse_date(context, today, lookahead_days)
        if not meeting_date or meeting_date < today - timedelta(days=14) or meeting_date > max_date:
            continue
        if "executive" in lowered:
            meeting_type = "Executive Committee"
        elif "special" in lowered:
            meeting_type = "Special Board Meeting"
        else:
            meeting_type = "Board Meeting"
        meeting = Meeting(
            board_id=source.board_id,
            board_name=source.board_name,
            meeting_type=meeting_type,
            meeting_date=meeting_date,
            start_time=parse_time(context),
            timezone="America/Los_Angeles",
            location=infer_location(context),
            virtual_url=infer_virtual_url(context),
            source_page_url=absolute_url(page_url, anchor["href"].strip()),
            agenda_url="",
            agenda_label="",
            confidence_notes="Profiled Foothill extraction: only FWDB meeting event titles from the official events calendar are published; calendar day cells and orientation/workshop events are excluded.",
        )
        meetings[meeting.stable_id] = meeting
    return sorted(meetings.values(), key=lambda m: (m.meeting_date, m.meeting_type))


def extract_long_beach_lbwin_schedule(
    source: BoardSource,
    html: str,
    page_url: str,
    today: date,
    lookahead_days: int,
) -> list[Meeting]:
    soup = BeautifulSoup(html, "html.parser")
    lines = [line.strip() for line in soup.get_text("\n", strip=True).splitlines() if line.strip()]
    schedule_year = _year_after_marker(lines, "Scheduled Meetings") or today.year
    meetings: dict[str, Meeting] = {}
    max_date = today + timedelta(days=lookahead_days)
    in_schedule = False
    for index, line in enumerate(lines):
        if "scheduled meetings" in line.lower():
            in_schedule = True
            continue
        if in_schedule and ("useful links" in line.lower() or "contact economic" in line.lower()):
            break
        if not in_schedule:
            continue
        meeting_date = _weekday_month_day_date(line, schedule_year)
        if not meeting_date or meeting_date < today - timedelta(days=14) or meeting_date > max_date:
            continue
        nearby = " ".join(lines[index : index + 5])
        meeting = Meeting(
            board_id=source.board_id,
            board_name=source.board_name,
            meeting_type="Board Meeting",
            meeting_date=meeting_date,
            start_time=parse_time(nearby),
            timezone="America/Los_Angeles",
            location=_long_beach_location(lines[index + 2 : index + 6]),
            virtual_url="",
            source_page_url=page_url,
            agenda_url="",
            agenda_label="",
            confidence_notes="Profiled Long Beach extraction: dates come only from the LBWIN scheduled meetings block, not board member biography text.",
        )
        meetings[meeting.stable_id] = meeting
    return sorted(meetings.values(), key=lambda m: (m.meeting_date, m.meeting_type))


def extract_merced_worknet_meetings(
    source: BoardSource,
    html: str,
    page_url: str,
    today: date,
    lookahead_days: int,
) -> list[Meeting]:
    soup = BeautifulSoup(html, "html.parser")
    lines = [line.strip() for line in soup.get_text("\n", strip=True).splitlines() if line.strip()]
    agenda_links = extract_agenda_links(html, page_url)
    meetings: dict[str, Meeting] = {}
    max_date = today + timedelta(days=lookahead_days)
    for index, line in enumerate(lines):
        original_date = parse_date(line, today, lookahead_days) if re.search(r"\b20\d{2}\b", line) else None
        meeting_date = _rescheduled_date(line) or original_date
        if not meeting_date or meeting_date < today - timedelta(days=14) or meeting_date > max_date:
            continue
        label_text = " ".join(lines[index + 1 : index + 3])
        lowered_label = label_text.lower()
        nearby = " ".join(lines[index : index + 5])
        if "executive" in lowered_label:
            meeting_type = "Executive Committee"
        elif "wdb meeting" in lowered_label or "workforce development board" in lowered_label:
            meeting_type = "Board Meeting"
        else:
            continue
        if any(term in lowered_label for term in ("roster", "for more information", "board members")):
            continue
        linked_agenda = best_agenda_for_date(agenda_links, meeting_date)
        if not linked_agenda and original_date and original_date != meeting_date:
            linked_agenda = best_agenda_for_date(agenda_links, original_date)
        meeting = Meeting(
            board_id=source.board_id,
            board_name=source.board_name,
            meeting_type=meeting_type,
            meeting_date=meeting_date,
            start_time=parse_time(nearby),
            timezone="America/Los_Angeles",
            location=_first_address(lines[index + 2 : index + 7]),
            virtual_url=infer_virtual_url(nearby),
            source_page_url=page_url,
            agenda_url=linked_agenda.url if linked_agenda else "",
            agenda_label=linked_agenda.label if linked_agenda else "",
            confidence_notes="Profiled Merced extraction: only rows labeled WDB meeting or Executive Committee Meeting are published; roster and cadence text are ignored unless date-labeled as a meeting row.",
        )
        meetings[meeting.stable_id] = meeting
    return sorted(meetings.values(), key=lambda m: (m.meeting_date, m.meeting_type))


def extract_la_county_wdb_calendar(
    source: BoardSource,
    html: str,
    page_url: str,
    today: date,
    lookahead_days: int,
) -> list[Meeting]:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)
    meetings: dict[str, Meeting] = {}
    max_date = today + timedelta(days=lookahead_days)
    for line in [line.strip() for line in text.splitlines() if line.strip()]:
        lowered = line.lower()
        if "los angeles county workforce development board" not in lowered:
            continue
        if any(term in lowered for term in ("finance", "orientation", "news", "recording", "youth")):
            continue
        meeting_date = parse_date(line, today, lookahead_days)
        if not meeting_date or meeting_date < today - timedelta(days=14) or meeting_date > max_date:
            continue
        meeting_type = "Executive Committee" if "executive" in lowered else "Board Meeting"
        meeting = Meeting(
            board_id=source.board_id,
            board_name=source.board_name,
            meeting_type=meeting_type,
            meeting_date=meeting_date,
            start_time=parse_time(line),
            timezone="America/Los_Angeles",
            location="",
            virtual_url="",
            source_page_url=page_url,
            agenda_url="",
            agenda_label="",
            confidence_notes="Profiled LA County extraction: only full Workforce Development Board or Executive Committee calendar entries are published; Finance, orientation, and news items are excluded.",
        )
        meetings[meeting.stable_id] = meeting
    return sorted(meetings.values(), key=lambda m: (m.meeting_date, m.meeting_type))


def infer_meeting_type(text: str) -> str:
    lowered = text.lower()
    if "executive" in lowered:
        return "Executive Committee"
    if "committee" in lowered:
        return "Committee"
    if "special" in lowered:
        return "Special Board Meeting"
    return "Board Meeting"


def infer_location(text: str) -> str:
    lowered = text.lower()
    if "zoom" in lowered or "teams" in lowered or "virtual" in lowered:
        return "Virtual"
    if "hybrid" in lowered:
        return "Hybrid"
    return ""


def infer_virtual_url(text: str) -> str:
    match = re.search(r"https?://\S+", text)
    return match.group(0).rstrip(").,") if match else ""


def _nearby_location(anchor) -> str:
    text = anchor.parent.get_text("\n", strip=True) if anchor.parent else ""
    for line in text.splitlines():
        if line.lower().startswith("location:"):
            return line.split(":", 1)[1].strip()
    return ""


def _year_after_marker(lines: list[str], marker: str) -> int | None:
    marker_lower = marker.lower()
    for line in lines:
        if marker_lower not in line.lower():
            continue
        match = re.search(r"\b(20\d{2})\b", line)
        if match:
            return int(match.group(1))
    return None


def _weekday_month_day_date(text: str, year: int) -> date | None:
    match = re.search(rf"\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+({MONTH_NAMES})\.?\s+(\d{{1,2}})\b", text, re.I)
    if not match:
        return None
    return date(year, _month_number(match.group(1)), int(match.group(2)))


def _long_beach_location(lines: list[str]) -> str:
    useful = [line for line in lines if not parse_time(line) and not _weekday_month_day_date(line, 2000)]
    return ", ".join(useful[:3])


def _first_address(lines: list[str]) -> str:
    for line in lines:
        if re.search(r"\b\d{2,6}\s+\w+", line):
            return line
    return ""


def _rescheduled_date(text: str) -> date | None:
    original_year = re.search(r"\b(20\d{2})\b", text)
    if not original_year or "rescheduled to" not in text.lower():
        return None
    match = re.search(rf"rescheduled to\s+(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+({MONTH_NAMES})\.?\s+(\d{{1,2}})(?:st|nd|rd|th)?", text, re.I)
    if not match:
        return None
    return date(int(original_year.group(1)), _month_number(match.group(1)), int(match.group(2)))


def best_agenda_for_date(links: Iterable[AgendaLink], meeting_date: date) -> Optional[AgendaLink]:
    tokens = {
        meeting_date.isoformat(),
        meeting_date.strftime("%m/%d/%Y"),
        meeting_date.strftime("%m-%d-%Y"),
        meeting_date.strftime("%Y%m%d"),
        meeting_date.strftime("%B %-d") if hasattr(meeting_date, "strftime") else "",
        meeting_date.strftime("%B %d"),
        meeting_date.strftime("%b %-d") if hasattr(meeting_date, "strftime") else "",
        meeting_date.strftime("%b %d"),
        meeting_date.strftime("%m/%d"),
        meeting_date.strftime("%m-%d"),
        meeting_date.strftime("%B %-d, %Y") if hasattr(meeting_date, "strftime") else "",
        meeting_date.strftime("%B %d, %Y"),
        f"{meeting_date.year} {meeting_date.strftime('%B')}",
        f"{meeting_date.year} {meeting_date.strftime('%b')}",
    }
    for link in links:
        haystack = f"{link.label} {link.url}".lower()
        linked_date = _date_from_numeric_filename(haystack, meeting_date)
        if linked_date == meeting_date:
            return link
        if linked_date and linked_date != meeting_date:
            continue
        if any(token and token.lower() in haystack for token in tokens):
            return link
        if str(meeting_date.year) in haystack and meeting_date.strftime("%B").lower() in haystack:
            return link
        if str(meeting_date.year) in haystack and meeting_date.strftime("%b").lower() in haystack:
            return link
    return None


def _agenda_context_label(anchor, label: str) -> str:
    normalized_label = label.strip()
    if _month_number_or_none(normalized_label) is None:
        return ""
    nearby_text = []
    parent = anchor.parent
    if parent:
        nearby_text.append(parent.get_text(" ", strip=True))
    for previous in anchor.find_all_previous(["h1", "h2", "h3", "h4", "h5", "strong"], limit=4):
        nearby_text.append(previous.get_text(" ", strip=True))
    context = " ".join(nearby_text)
    if "agenda" not in context.lower():
        return ""
    year_match = re.search(r"\b(20\d{2})\b", context)
    if year_match:
        return f"{year_match.group(1)} Board Agendas - {normalized_label}"
    return f"Agenda - {normalized_label}"


def _between_markers(text: str, start: str, end: str) -> str:
    start_index = text.find(start)
    if start_index == -1:
        return ""
    end_index = text.find(end, start_index + len(start))
    if end_index == -1:
        return text[start_index:]
    return text[start_index:end_index]


def _extract_sectioned_line_table_meetings(
    source: BoardSource,
    html: str,
    page_url: str,
    today: date,
    lookahead_days: int,
    sections: list[tuple[str, str, str]],
) -> list[Meeting]:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)
    all_lines = [line.strip() for line in text.splitlines() if line.strip()]
    agenda_links = extract_agenda_links(html, page_url)
    meetings: dict[str, Meeting] = {}
    max_date = today + timedelta(days=lookahead_days)
    for start_marker, end_marker, meeting_type in sections:
        lines = _lines_between_markers(all_lines, start_marker, end_marker)
        if not lines:
            continue
        for index, line in enumerate(lines):
            meeting_date = parse_date(line, today, lookahead_days)
            if not meeting_date or meeting_date < today - timedelta(days=14) or meeting_date > max_date:
                continue
            nearby = " ".join(lines[index : index + 2])
            if "cancel" in nearby.lower():
                continue
            linked_agenda = best_agenda_for_date(agenda_links, meeting_date)
            meeting = Meeting(
                board_id=source.board_id,
                board_name=source.board_name,
                meeting_type=meeting_type,
                meeting_date=meeting_date,
                start_time=parse_time(nearby),
                timezone="America/Los_Angeles",
                location="",
                virtual_url=infer_virtual_url(nearby),
                source_page_url=page_url,
                agenda_url=linked_agenda.url if linked_agenda else "",
                agenda_label=linked_agenda.label if linked_agenda else "",
                confidence_notes="Profiled sectioned extraction: dates are scoped to the official board or executive committee section and canceled rows are excluded.",
            )
            meetings[meeting.stable_id] = meeting
    return sorted(meetings.values(), key=lambda m: (m.meeting_date, m.meeting_type))


def _page_title_or_heading(soup: BeautifulSoup) -> str:
    candidates: list[str] = []
    for selector in ["h1", "h2", "h3", "title"]:
        for node in soup.find_all(selector):
            text = node.get_text(" ", strip=True)
            if text:
                candidates.append(text)
    ranked = sorted(((_meeting_title_score(text), text) for text in candidates), reverse=True)
    if ranked and ranked[0][0] > 0:
        return ranked[0][1]
    if candidates:
        return candidates[0]
    return ""


def _meeting_title_score(text: str) -> int:
    lowered = text.lower()
    score = 0
    if "executive" in lowered:
        score += 6
    if "committee meeting" in lowered:
        score += 5
    elif "committee" in lowered:
        score += 3
    if "board meeting" in lowered:
        score += 5
    elif "board" in lowered:
        score += 2
    if "meeting" in lowered:
        score += 2
    if "calendar" in lowered:
        score -= 3
    return score


def _looks_like_nonmeeting_event(text: str) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in ("closed", "holiday", "job fair", "workshop", "training"))


def _lines_between_markers(lines: list[str], start: str, end: str) -> list[str]:
    start_index = next((idx for idx, line in enumerate(lines) if line == start), -1)
    if start_index == -1:
        return []
    end_index = next((idx for idx in range(start_index + 1, len(lines)) if lines[idx] == end), len(lines))
    return lines[start_index:end_index]


def _stanislaus_current_board_agenda(soup: BeautifulSoup, page_url: str, meeting_date: date) -> AgendaLink | None:
    for anchor in soup.find_all("a", href=True):
        label = anchor.get_text(" ", strip=True)
        if "latest agenda" not in label.lower():
            continue
        href = anchor["href"].strip()
        if "cancel" in href.lower():
            continue
        linked_date = _date_from_numeric_filename(href, meeting_date)
        if linked_date and abs((linked_date - meeting_date).days) > 14:
            return None
        return AgendaLink(absolute_url(page_url, href), label, page_url)
    return None


def _date_from_numeric_filename(value: str, reference_date: date) -> date | None:
    year_first_matches = re.findall(r"(?<!\d)(20\d{2})[-_.](\d{1,2})[-_.](\d{1,2})(?!\d)", value)
    if year_first_matches:
        year, month, day = year_first_matches[-1]
        try:
            return date(int(year), int(month), int(day))
        except ValueError:
            return None
    matches = re.findall(r"(?<!\d)(\d{1,2})[-_.](\d{1,2})[-_.](\d{2,4})(?!\d)", value)
    if not matches:
        return None
    month, day, year = matches[-1]
    full_year = int(year)
    if full_year < 100:
        full_year += 2000
    try:
        return date(full_year, int(month), int(day))
    except ValueError:
        return None


def _month_number_or_none(value: str) -> int | None:
    try:
        return _month_number(value)
    except ValueError:
        return None


def _candidate_text_blocks(soup: BeautifulSoup) -> list[str]:
    blocks: list[str] = []
    selectors = ["li", "tr", "p", "article", "div"]
    for selector in selectors:
        for node in soup.select(selector):
            text = node.get_text(" ", strip=True)
            if len(text) < 8 or len(text) > 800:
                continue
            lowered = text.lower()
            if "select date" in lowered or re.fullmatch(r"(?:\d+ events?,?\s*)+\d+", lowered):
                continue
            if any(pattern.search(text) for pattern in DATE_PATTERNS):
                blocks.append(text)
    return blocks


def _dedupe_agendas(links: Iterable[AgendaLink]) -> list[AgendaLink]:
    seen: set[str] = set()
    output: list[AgendaLink] = []
    for link in links:
        if link.url in seen:
            continue
        seen.add(link.url)
        output.append(link)
    return output
