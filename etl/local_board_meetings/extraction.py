from __future__ import annotations

import calendar
import json
import re
import urllib.parse
from html import unescape
from datetime import date, datetime, time, timedelta
from typing import Iterable, List, Optional
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup

from .fetcher import USER_AGENT, absolute_url, fetch_url
from .models import AgendaLink, BoardSource, Meeting

MONTH_NAMES = "|".join(calendar.month_name[1:] + calendar.month_abbr[1:])
DATE_PATTERNS = [
    re.compile(rf"\b({MONTH_NAMES})\.?\s+(\d{{1,2}})(?:st|nd|rd|th)?(?:,\s*|\s+)(20\d{{2}})\b", re.I),
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
EXCLUDED_AGENDA_LINK_TERMS = (
    "google.com/calendar",
    "outlook.office.com",
    "outlook.live.com",
    "webcal:",
    "ical=1",
    "calendar/action/compose",
    "calendar/event?action=template",
)


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
    if not 1 <= hour <= 12 or not 0 <= minute <= 59:
        return None
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
        if any(term in candidate for term in EXCLUDED_AGENDA_LINK_TERMS):
            continue
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
    if extraction_strategy == "no_publish":
        return []
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
    if extraction_strategy == "tulare_wib_board_only":
        if "/pec" in page_url.lower():
            return []
        return extract_tulare_wib_board_meetings(source, html, page_url, today, lookahead_days)
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
    if extraction_strategy == "madera_board_archives":
        return extract_madera_board_archives(source, html, page_url, today, lookahead_days)
    if extraction_strategy == "la_county_wdb_calendar":
        return extract_la_county_wdb_calendar(source, html, page_url, today, lookahead_days)
    if extraction_strategy == "nccc_wdb_schedule":
        return extract_nccc_wdb_schedule(source, html, page_url, today, lookahead_days)
    if extraction_strategy == "riverside_wdb_schedule":
        return extract_riverside_wdb_schedule(source, html, page_url, today, lookahead_days)
    if extraction_strategy == "san_diego_wdb":
        return extract_san_diego_wdb_meetings(source, html, page_url, today, lookahead_days)
    if extraction_strategy == "san_joaquin_worknet":
        return extract_san_joaquin_worknet_meetings(source, html, page_url, today, lookahead_days)
    if extraction_strategy == "sonoma_joblink_board_meetings":
        return extract_sonoma_joblink_board_meetings(source, html, page_url, today, lookahead_days)
    if extraction_strategy == "solano_board_calendar":
        return extract_solano_board_calendar(source, html, page_url, today, lookahead_days)
    if extraction_strategy == "work2future_board_events":
        return extract_work2future_board_events(source, html, page_url, today, lookahead_days)
    if extraction_strategy == "tribe_events_api":
        return extract_tribe_events_api_meetings(source, html, page_url, today, lookahead_days)
    if extraction_strategy == "la_city_novus":
        return extract_la_city_novus_meetings(source, html, page_url, today, lookahead_days)
    if extraction_strategy == "mother_lode_schedule":
        return extract_mother_lode_meetings(source, html, page_url, today, lookahead_days)
    if extraction_strategy == "santa_ana_wdb_events":
        return extract_santa_ana_wdb_events(source, html, page_url, today, lookahead_days)
    if extraction_strategy == "santa_barbara_hcms":
        return extract_santa_barbara_hcms_agendas(source, html, page_url, today, lookahead_days)
    if extraction_strategy == "orange_ocwdb":
        return extract_orange_ocwdb_meetings(source, html, page_url, today, lookahead_days)
    if extraction_strategy == "slo_county_meetings":
        return extract_slo_county_meetings(source, html, page_url, today, lookahead_days)
    if extraction_strategy == "golden_sierra_events":
        return extract_golden_sierra_events(source, html, page_url, today, lookahead_days)
    if extraction_strategy == "ventura_google_calendar_ics":
        return extract_ventura_google_calendar_ics(source, html, page_url, today, lookahead_days)
    if extraction_strategy == "anaheim_civicengage":
        return extract_anaheim_civicengage(source, html, page_url, today, lookahead_days)
    if extraction_strategy == "richmond_wdb":
        return extract_richmond_wdb(source, html, page_url, today, lookahead_days)
    if extraction_strategy == "contra_costa_legistar":
        return extract_contra_costa_legistar(source, html, page_url, today, lookahead_days)
    if extraction_strategy == "kings_jto_packets":
        return extract_kings_jto_packets(source, html, page_url, today, lookahead_days)
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


def extract_kings_jto_packets(
    source: BoardSource,
    html: str,
    page_url: str,
    today: date,
    lookahead_days: int,
) -> list[Meeting]:
    soup = BeautifulSoup(html, "html.parser")
    heading = next(
        (
            node
            for node in soup.find_all(["h1", "h2", "h3", "h4"])
            if "workforce development board meetings" in node.get_text(" ", strip=True).lower()
        ),
        None,
    )
    if not heading:
        return []
    meetings: dict[str, Meeting] = {}
    max_date = today + timedelta(days=lookahead_days)
    for node in heading.find_all_next():
        if node is not heading and node.name in {"h1", "h2", "h3", "h4"}:
            break
        if node.name != "a" or not node.get("href"):
            continue
        label = node.get_text(" ", strip=True)
        if "packet" not in label.lower():
            continue
        meeting_date = parse_date(label, today, lookahead_days)
        if not meeting_date or meeting_date < today - timedelta(days=14) or meeting_date > max_date:
            continue
        agenda_url = absolute_url(page_url, node["href"].strip())
        meeting = Meeting(
            board_id=source.board_id,
            board_name=source.board_name,
            meeting_type="Board Meeting",
            meeting_date=meeting_date,
            start_time=None,
            timezone="America/Los_Angeles",
            location="",
            virtual_url="",
            source_page_url=page_url,
            agenda_url=agenda_url,
            agenda_label=label,
            confidence_notes="Profiled Kings County extraction: only packet links under the official JTO Workforce Development Board Meetings heading are published.",
        )
        meetings[meeting.stable_id] = meeting
    return sorted(meetings.values(), key=lambda meeting: meeting.meeting_date)


def extract_tulare_wib_board_meetings(
    source: BoardSource,
    html: str,
    page_url: str,
    today: date,
    lookahead_days: int,
) -> List[Meeting]:
    """Extract every date from Tulare's two-column annual board schedule."""
    soup = BeautifulSoup(html, "html.parser")
    page_text = " ".join(soup.stripped_strings)
    schedule_text = _between_markers(page_text, "Board Meeting Schedule", "Board Agendas")
    if not schedule_text:
        return []

    agenda_links = extract_agenda_links(html, page_url)
    matches = list(DATE_PATTERNS[0].finditer(schedule_text))
    max_date = today + timedelta(days=lookahead_days)
    default_location_match = re.search(
        r"(309\s+W\.\s+Main\s+St\.\s+Suite\s+130,\s*Visalia,\s*CA)",
        schedule_text,
        re.I,
    )
    october_location_match = re.search(
        r"(303\s+E\.\s+Acequia\s+Ave\.,\s*Visalia,\s*CA)",
        schedule_text,
        re.I,
    )
    default_location = default_location_match.group(1) if default_location_match else ""
    october_location = (
        f"Visalia Convention Center, {october_location_match.group(1)}"
        if october_location_match
        else default_location
    )
    start_time = parse_time(schedule_text)
    meetings: dict[str, Meeting] = {}

    for index, match in enumerate(matches):
        meeting_date = date(int(match.group(3)), _month_number(match.group(1)), int(match.group(2)))
        if meeting_date < today - timedelta(days=14) or meeting_date > max_date:
            continue
        next_start = matches[index + 1].start() if index + 1 < len(matches) else len(schedule_text)
        date_context = schedule_text[match.end() : next_start]
        if re.search(r"\bcancel(?:ed|led)\b", date_context, re.I):
            continue

        agenda = best_agenda_for_date(agenda_links, meeting_date)
        meeting = Meeting(
            board_id=source.board_id,
            board_name=source.board_name,
            meeting_type="Board Meeting",
            meeting_date=meeting_date,
            start_time=start_time,
            timezone="America/Los_Angeles",
            location=october_location if meeting_date.month == 10 else default_location,
            virtual_url="",
            source_page_url=page_url,
            agenda_url=agenda.url if agenda else "",
            agenda_label=agenda.label if agenda else "",
            confidence_notes=(
                "Profiled Tulare extraction: date read from the official annual WIB schedule; "
                "the two-column layout is parsed one date at a time and canceled meetings are excluded."
            ),
        )
        meetings[meeting.stable_id] = meeting
    return sorted(meetings.values(), key=lambda meeting: meeting.meeting_date)


def extract_ventura_google_calendar_ics(
    source: BoardSource,
    ics_text: str,
    page_url: str,
    today: date,
    lookahead_days: int,
) -> list[Meeting]:
    """Read Ventura's official embedded Google Calendar feed.

    The public page wraps the real schedule in an iframe. Its ICS feed is the stable,
    machine-readable source and also carries locations and packet URLs.
    """
    meetings: dict[str, Meeting] = {}
    max_date = today + timedelta(days=lookahead_days)
    for event in _parse_ics_events(ics_text):
        summary = _ics_value(event, "SUMMARY")
        lowered = summary.lower()
        if "cancel" in lowered:
            continue
        if "executive" in lowered and "committee" in lowered:
            meeting_type = "Executive Committee"
        elif "board" in lowered and "meeting" in lowered:
            meeting_type = "Board Meeting"
        else:
            continue
        start = _ics_start(event)
        if not start:
            continue
        meeting_date, start_time = start
        if meeting_date < today - timedelta(days=14) or meeting_date > max_date:
            continue
        description = _ics_clean_text(_ics_value(event, "DESCRIPTION"))
        agenda_url = _ics_agenda_url(_ics_value(event, "DESCRIPTION"))
        location = _ics_clean_text(_ics_value(event, "LOCATION"))
        virtual_url = infer_virtual_url(description) if any(term in description.lower() for term in ("zoom", "teams")) else ""
        meeting = Meeting(
            board_id=source.board_id,
            board_name=source.board_name,
            meeting_type=meeting_type,
            meeting_date=meeting_date,
            start_time=start_time,
            timezone="America/Los_Angeles",
            location=location,
            virtual_url=virtual_url,
            source_page_url=source.agenda_minutes_url or source.main_website or page_url,
            agenda_url=agenda_url,
            agenda_label="Meeting Packet" if agenda_url else "",
            confidence_notes=(
                "Profiled Ventura extraction: uses the official public Google Calendar ICS embedded on the WDB meeting page; "
                "only full-board and executive committee events are published and canceled events are excluded."
            ),
        )
        meetings[meeting.stable_id] = meeting
    return sorted(meetings.values(), key=lambda m: (m.meeting_date, m.meeting_type))


def extract_anaheim_civicengage(
    source: BoardSource,
    html: str,
    page_url: str,
    today: date,
    lookahead_days: int,
) -> list[Meeting]:
    soup = BeautifulSoup(html, "html.parser")
    meetings: dict[str, Meeting] = {}
    max_date = today + timedelta(days=lookahead_days)
    for row in soup.select("tr.catAgendaRow"):
        context = row.get_text(" ", strip=True)
        if "cancel" in context.lower():
            continue
        meeting_date = parse_date(context, today, lookahead_days)
        if not meeting_date or meeting_date < today - timedelta(days=14) or meeting_date > max_date:
            continue
        agenda_url = ""
        for anchor in row.find_all("a", href=True):
            href = anchor["href"].strip()
            if "/AgendaCenter/ViewFile/Agenda/" in href and "html=true" not in href.lower():
                agenda_url = absolute_url(page_url, href)
                break
        meeting = Meeting(
            board_id=source.board_id,
            board_name=source.board_name,
            meeting_type="Board Meeting",
            meeting_date=meeting_date,
            start_time=time(9, 0),
            timezone="America/Los_Angeles",
            location="Anaheim West Tower, Gordon Hoyt Conference Room",
            virtual_url="",
            source_page_url=page_url,
            agenda_url=agenda_url,
            agenda_label="Agenda" if agenda_url else "",
            confidence_notes=(
                "Profiled Anaheim extraction: reads only Workforce Development Board AgendaCenter rows, "
                "skips canceled meetings, and binds an agenda from the same dated row."
            ),
        )
        meetings[meeting.stable_id] = meeting
    return sorted(meetings.values(), key=lambda m: m.meeting_date)


def extract_richmond_wdb(
    source: BoardSource,
    html: str,
    page_url: str,
    today: date,
    lookahead_days: int,
) -> list[Meeting]:
    soup = BeautifulSoup(html, "html.parser")
    meetings: dict[str, Meeting] = {}
    max_date = today + timedelta(days=lookahead_days)
    agenda_heading = next(
        (heading for heading in soup.find_all(["h2", "h3", "h4"]) if "agenda & minutes" in heading.get_text(" ", strip=True).lower()),
        None,
    )
    if agenda_heading:
        node = agenda_heading.find_next_sibling()
        while node and node.name not in {"h2", "h3", "h4"}:
            context = node.get_text(" ", strip=True)
            is_reschedule_notice = node.find("s") is not None or "-->" in context or "rescheduled" in context.lower()
            if "cancel" not in context.lower() and not is_reschedule_notice:
                meeting_date = parse_date(context, today, lookahead_days)
                if meeting_date and today - timedelta(days=14) <= meeting_date <= max_date:
                    anchor = node.find("a", href=True)
                    agenda_url = absolute_url(page_url, anchor["href"].strip()) if anchor else ""
                    meeting = Meeting(
                        board_id=source.board_id,
                        board_name=source.board_name,
                        meeting_type="Board Meeting",
                        meeting_date=meeting_date,
                        start_time=time(11, 30),
                        timezone="America/Los_Angeles",
                        location="RichmondWORKS, 330 25th Street, Richmond, CA",
                        virtual_url="",
                        source_page_url=page_url,
                        agenda_url=agenda_url,
                        agenda_label="Agenda and minutes" if agenda_url else "",
                        confidence_notes=(
                            "Profiled Richmond extraction: reads only the WDB Agenda & Minutes section; canceled dates are excluded. "
                            "Exact future dates also come from the linked official annual schedule fallback."
                        ),
                    )
                    meetings[meeting.stable_id] = meeting
            node = node.find_next_sibling()
    return sorted(meetings.values(), key=lambda m: m.meeting_date)


def extract_contra_costa_legistar(
    source: BoardSource,
    html: str,
    page_url: str,
    today: date,
    lookahead_days: int,
) -> list[Meeting]:
    soup = BeautifulSoup(html, "html.parser")
    meetings: dict[str, Meeting] = {}
    max_date = today + timedelta(days=lookahead_days)
    for row in soup.find_all("tr"):
        cells = row.find_all("td", recursive=False)
        if len(cells) < 6 or cells[0].get_text(" ", strip=True) != "Workforce Development Board":
            continue
        context = cells[4].get_text(" ", strip=True)
        lowered = context.lower()
        if "full board/executive committee" not in lowered or "cancel" in lowered:
            continue
        meeting_date = parse_date(cells[1].get_text(" ", strip=True), today, lookahead_days)
        if not meeting_date or meeting_date < today - timedelta(days=14) or meeting_date > max_date:
            continue
        agenda_url = ""
        for anchor in row.find_all("a", href=True):
            href = anchor["href"].strip()
            if "M=A&" in href or "M=A&amp;" in href:
                agenda_url = absolute_url(page_url, href)
                break
        virtual_url = next(
            (
                anchor["href"].strip()
                for anchor in cells[4].find_all("a", href=True)
                if any(term in anchor["href"].lower() for term in ("zoom.", "teams.", "meet.google"))
            ),
            "",
        )
        location = re.sub(r"\s*Full Board/Executive Committee\s*$", "", context, flags=re.I)
        location = re.split(r"\b(?:Meeting ID|Zoom):", location, maxsplit=1, flags=re.I)[0].strip()
        meeting = Meeting(
            board_id=source.board_id,
            board_name=source.board_name,
            meeting_type="Board / Executive Committee",
            meeting_date=meeting_date,
            start_time=parse_time(cells[3].get_text(" ", strip=True)),
            timezone="America/Los_Angeles",
            location=location,
            virtual_url=virtual_url or infer_virtual_url(context),
            source_page_url=page_url,
            agenda_url=agenda_url,
            agenda_label="Agenda" if agenda_url else "",
            confidence_notes=(
                "Profiled Contra Costa extraction: uses the county Legistar calendar and publishes only rows whose "
                "meeting subtype is Full Board/Executive Committee; Youth and BED committee rows are excluded."
            ),
        )
        meetings[meeting.stable_id] = meeting
    return sorted(meetings.values(), key=lambda m: m.meeting_date)


def _parse_ics_events(ics_text: str) -> list[dict[str, list[tuple[str, str]]]]:
    unfolded: list[str] = []
    for raw_line in ics_text.replace("\r\n", "\n").split("\n"):
        if raw_line.startswith((" ", "\t")) and unfolded:
            unfolded[-1] += raw_line[1:]
        else:
            unfolded.append(raw_line)
    events: list[dict[str, list[tuple[str, str]]]] = []
    current: dict[str, list[tuple[str, str]]] | None = None
    for line in unfolded:
        if line == "BEGIN:VEVENT":
            current = {}
            continue
        if line == "END:VEVENT":
            if current is not None:
                events.append(current)
            current = None
            continue
        if current is None or ":" not in line:
            continue
        raw_key, value = line.split(":", 1)
        name = raw_key.split(";", 1)[0].upper()
        current.setdefault(name, []).append((raw_key, value))
    return events


def _ics_value(event: dict[str, list[tuple[str, str]]], name: str) -> str:
    values = event.get(name, [])
    return values[0][1] if values else ""


def _ics_start(event: dict[str, list[tuple[str, str]]]) -> tuple[date, time | None] | None:
    values = event.get("DTSTART", [])
    if not values:
        return None
    raw_key, value = values[0]
    try:
        if "VALUE=DATE" in raw_key or len(value) == 8:
            return datetime.strptime(value[:8], "%Y%m%d").date(), None
        if value.endswith("Z"):
            dt = datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(tzinfo=ZoneInfo("UTC"))
            local = dt.astimezone(ZoneInfo("America/Los_Angeles"))
        else:
            tz_match = re.search(r"TZID=([^;:]+)", raw_key)
            zone = ZoneInfo(tz_match.group(1)) if tz_match else ZoneInfo("America/Los_Angeles")
            local = datetime.strptime(value, "%Y%m%dT%H%M%S").replace(tzinfo=zone)
        return local.date(), local.time().replace(tzinfo=None, microsecond=0)
    except (ValueError, KeyError):
        return None


def _ics_clean_text(value: str) -> str:
    value = re.sub(r"<[^>]+>", " ", unescape(value))
    value = value.replace("\\n", " ").replace("\\,", ",").replace("\\;", ";").replace("\\\\", "\\")
    return " ".join(value.split())


def _ics_agenda_url(description: str) -> str:
    for candidate in re.findall(r"https?://[^\s<>\"]+", unescape(description)):
        url = candidate.rstrip("'\"),.;")
        lowered = url.lower()
        if ("packet" in lowered or "agenda" in lowered) and ".pdf" in lowered:
            return url.replace("\\,", ",")
    return ""


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
    date_links = _date_labeled_links_by_date(html, page_url, today, lookahead_days)
    section_types = {
        "BUSINESS, TECHNOLOGY & ECONOMIC DEVELOPMENT COMMITTEE": "",
        "SBWIB EXECUTIVE COMMITTEE": "Executive Committee",
        "SOUTH BAY WORKFORCE INVESTMENT BOARD": "Board Meeting",
        "PERFORMANCE & EVALUATION COMMITTEE": "",
        "YOUTH DEVELOPMENT COUNCIL COMMITTEE": "",
        "ONE-STOP POLICY COMMITTEE": "",
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
        linked_agenda = date_links.get(meeting_date)
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
            agenda_url=linked_agenda.url if linked_agenda else "",
            agenda_label=linked_agenda.label if linked_agenda else "",
            confidence_notes="Profiled South Bay extraction: dates are assigned to the section heading that precedes them on the annual meeting agendas page; date-labeled links are treated as agenda PDFs.",
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
    if "primegov.com/api/" in page_url.lower():
        return _extract_long_beach_primegov_meetings(source, html, page_url, today, lookahead_days)
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


def extract_madera_board_archives(
    source: BoardSource,
    html: str,
    page_url: str,
    today: date,
    lookahead_days: int,
) -> list[Meeting]:
    soup = BeautifulSoup(html, "html.parser")
    lines = [line.strip() for line in soup.get_text("\n", strip=True).splitlines() if line.strip()]
    agenda_links = extract_agenda_links(html, page_url)
    meeting_type = "Executive Committee" if "executive-committee" in page_url.lower() else "Board Meeting"
    location = _madera_location(lines)
    meetings: dict[str, Meeting] = {}
    max_date = today + timedelta(days=lookahead_days)
    in_archive = meeting_type == "Executive Committee"
    for index, line in enumerate(lines):
        if line == "Meetings & Agendas":
            in_archive = True
            continue
        if not in_archive:
            continue
        meeting_date = parse_date(line, today, lookahead_days)
        if not meeting_date or meeting_date < today - timedelta(days=14) or meeting_date > max_date:
            continue
        nearby = " ".join(lines[index : index + 4])
        if any(term in nearby.lower() for term in ("cancel", "no quorum")):
            continue
        linked_agenda = best_agenda_for_date(agenda_links, meeting_date)
        meeting = Meeting(
            board_id=source.board_id,
            board_name=source.board_name,
            meeting_type=meeting_type,
            meeting_date=meeting_date,
            start_time=parse_time(nearby),
            timezone="America/Los_Angeles",
            location=location,
            virtual_url="",
            source_page_url=page_url,
            agenda_url=linked_agenda.url if linked_agenda else "",
            agenda_label=linked_agenda.label if linked_agenda else "",
            confidence_notes="Profiled Madera extraction: official board/executive archive rows are parsed by date, canceled/no-quorum rows are excluded, and agenda packets are date-matched.",
        )
        meetings[meeting.stable_id] = meeting
    return sorted(meetings.values(), key=lambda m: (m.meeting_date, m.meeting_type))


def extract_nccc_wdb_schedule(
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
    in_2026 = False
    for index, line in enumerate(lines):
        lowered = line.lower()
        if "2026 workforce development board meetings" in lowered:
            in_2026 = True
            continue
        if in_2026 and "2025 workforce development board meetings" in lowered:
            break
        if not in_2026:
            continue
        meeting_date = parse_date(line, today, lookahead_days)
        if not meeting_date or meeting_date < today - timedelta(days=14) or meeting_date > max_date:
            continue
        nearby = " ".join(lines[index : index + 4])
        if "cancel" in nearby.lower():
            continue
        linked_agenda = best_agenda_for_date(agenda_links, meeting_date)
        meeting = Meeting(
            board_id=source.board_id,
            board_name=source.board_name,
            meeting_type="Board Meeting",
            meeting_date=meeting_date,
            start_time=parse_time(nearby),
            timezone="America/Los_Angeles",
            location="",
            virtual_url="",
            source_page_url=page_url,
            agenda_url=linked_agenda.url if linked_agenda else "",
            agenda_label=linked_agenda.label if linked_agenda else "",
            confidence_notes="Profiled NCCC extraction: only dates under the 2026 Workforce Development Board Meetings heading are published.",
        )
        meetings[meeting.stable_id] = meeting
    return sorted(meetings.values(), key=lambda m: (m.meeting_date, m.meeting_type))


def extract_riverside_wdb_schedule(
    source: BoardSource,
    html: str,
    page_url: str,
    today: date,
    lookahead_days: int,
) -> list[Meeting]:
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text("\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    agenda_links = extract_agenda_links(html, page_url)
    meeting_type = "Executive Committee" if "executive" in page_url.lower() or "executive committee" in text.lower()[:500] else "Board Meeting"
    meetings: dict[str, Meeting] = {}
    max_date = today + timedelta(days=lookahead_days)
    in_schedule = False
    for index, line in enumerate(lines):
        lowered = line.lower()
        if "2026" in lowered and "meeting schedule" in lowered:
            in_schedule = True
            continue
        if in_schedule and ("agendas" in lowered or "for more information" in lowered):
            break
        if not in_schedule:
            continue
        meeting_date = parse_date(line, today, lookahead_days)
        if not meeting_date or meeting_date < today - timedelta(days=14) or meeting_date > max_date:
            continue
        nearby = " ".join(lines[index : index + 5])
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
            location=_first_address(lines[index + 1 : index + 6]),
            virtual_url="",
            source_page_url=page_url,
            agenda_url=linked_agenda.url if linked_agenda else "",
            agenda_label=linked_agenda.label if linked_agenda else "",
            confidence_notes="Profiled Riverside extraction: dates are scoped to the 2026 full board or executive committee meeting schedule tables and canceled rows are excluded.",
        )
        meetings[meeting.stable_id] = meeting
    return sorted(meetings.values(), key=lambda m: (m.meeting_date, m.meeting_type))


def extract_san_diego_wdb_meetings(
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
    in_upcoming = False
    current_type = ""
    for index, line in enumerate(lines):
        lowered = line.lower()
        if lowered == "upcoming meetings":
            in_upcoming = True
            continue
        if in_upcoming and lowered == "past meetings":
            break
        if not in_upcoming:
            continue
        if lowered in {"executive committee", "board meeting"}:
            current_type = "Executive Committee" if "executive" in lowered else "Board Meeting"
            continue
        meeting_date = parse_date(line, today, lookahead_days)
        if not current_type or not meeting_date or meeting_date < today - timedelta(days=14) or meeting_date > max_date:
            continue
        nearby = " ".join(lines[index : index + 3])
        linked_agenda = best_agenda_for_meeting(agenda_links, meeting_date, current_type)
        meeting = Meeting(
            board_id=source.board_id,
            board_name=source.board_name,
            meeting_type=current_type,
            meeting_date=meeting_date,
            start_time=parse_time(nearby),
            timezone="America/Los_Angeles",
            location="",
            virtual_url="",
            source_page_url=page_url,
            agenda_url=linked_agenda.url if linked_agenda else "",
            agenda_label=linked_agenda.label if linked_agenda else "",
            confidence_notes="Profiled San Diego extraction: only the Upcoming Meetings section for the WDB Board and Executive Committee is published; audit/policy board rows are excluded and date-matched agenda links are attached.",
        )
        meetings[meeting.stable_id] = meeting
        current_type = ""
    return sorted(meetings.values(), key=lambda m: (m.meeting_date, m.meeting_type))


def extract_orange_ocwdb_meetings(
    source: BoardSource,
    html: str,
    page_url: str,
    today: date,
    lookahead_days: int,
) -> list[Meeting]:
    soup = BeautifulSoup(html, "html.parser")
    max_date = today + timedelta(days=lookahead_days)
    meetings: list[Meeting] = []
    for heading in soup.find_all(["h2", "h3"]):
        title = heading.get_text(" ", strip=True).lower()
        if "full board" in title:
            meeting_type = "Board Meeting"
        elif "executive committee" in title:
            meeting_type = "Executive Committee"
        else:
            continue
        table = heading.find_next("table")
        if not table:
            continue
        for row in table.find_all("tr"):
            cells = row.find_all(["td", "th"])
            if not cells:
                continue
            row_text = " ".join(cell.get_text(" ", strip=True) for cell in cells)
            if "cancel" in row_text.lower():
                continue
            meeting_date = parse_date(cells[0].get_text(" ", strip=True), today, lookahead_days)
            if not meeting_date or meeting_date < today - timedelta(days=14) or meeting_date > max_date:
                continue
            agenda_anchor = next(
                (
                    anchor
                    for anchor in row.find_all("a", href=True)
                    if "agenda" in f"{anchor.get_text(' ', strip=True)} {anchor['href']}".lower()
                    and "summary" not in f"{anchor.get_text(' ', strip=True)} {anchor['href']}".lower()
                ),
                None,
            )
            agenda_url = absolute_url(page_url, agenda_anchor["href"]) if agenda_anchor else ""
            meetings.append(
                Meeting(
                    board_id=source.board_id,
                    board_name=source.board_name,
                    meeting_type=meeting_type,
                    meeting_date=meeting_date,
                    start_time=None,
                    timezone="America/Los_Angeles",
                    location="",
                    virtual_url="",
                    source_page_url=page_url,
                    agenda_url=agenda_url,
                    agenda_label=agenda_anchor.get_text(" ", strip=True) if agenda_anchor else "",
                    confidence_notes="Profiled Orange County extraction: only Full Board and Executive Committee tables are published; canceled and standing-committee rows are excluded.",
                )
            )
    return sorted(meetings, key=lambda meeting: (meeting.meeting_date, meeting.meeting_type))


def extract_slo_county_meetings(
    source: BoardSource,
    html: str,
    page_url: str,
    today: date,
    lookahead_days: int,
) -> list[Meeting]:
    soup = BeautifulSoup(html, "html.parser")
    max_date = today + timedelta(days=lookahead_days)
    meetings: list[Meeting] = []
    for row in soup.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 4:
            continue
        row_text = " ".join(cell.get_text(" ", strip=True) for cell in cells)
        lowered = row_text.lower()
        if "cancel" in lowered or "meeting" not in lowered:
            continue
        if "executive committee" in lowered:
            meeting_type = "Executive Committee"
        elif "workforce development board meeting" in lowered:
            meeting_type = "Board Meeting"
        else:
            continue
        meeting_date = parse_date(cells[0].get_text(" ", strip=True), today, lookahead_days)
        if not meeting_date or meeting_date < today - timedelta(days=14) or meeting_date > max_date:
            continue
        anchor = row.find("a", href=True)
        source_url = absolute_url(page_url, anchor["href"]) if anchor else page_url
        location = cells[-1].get_text(" ", strip=True)
        meetings.append(
            Meeting(
                board_id=source.board_id,
                board_name=source.board_name,
                meeting_type=meeting_type,
                meeting_date=meeting_date,
                start_time=parse_time(cells[0].get_text(" ", strip=True)),
                timezone="America/Los_Angeles",
                location=location,
                virtual_url="",
                source_page_url=source_url,
                agenda_url="",
                agenda_label="",
                confidence_notes="Profiled San Luis Obispo County meeting table; canceled rows and non-WDB events are excluded, and detail pages are followed for agenda documents.",
            )
        )
    return sorted(meetings, key=lambda meeting: (meeting.meeting_date, meeting.meeting_type))


def extract_golden_sierra_events(
    source: BoardSource,
    html: str,
    page_url: str,
    today: date,
    lookahead_days: int,
) -> list[Meeting]:
    soup = BeautifulSoup(html, "html.parser")
    max_date = today + timedelta(days=lookahead_days)
    meetings: dict[str, Meeting] = {}
    articles = soup.select("article.tribe-events-calendar-month-mobile-events__mobile-event")
    for article in articles:
        anchor = article.find("a", href=True)
        title = anchor.get_text(" ", strip=True) if anchor else ""
        lowered = title.lower()
        if lowered == "executive committee meeting":
            meeting_type = "Executive Committee"
        elif lowered == "workforce development board meeting":
            meeting_type = "Board Meeting"
        else:
            continue
        time_node = article.find("time", attrs={"datetime": True})
        meeting_date = parse_date(time_node.get("datetime", "") if time_node else "", today, lookahead_days)
        if not meeting_date or meeting_date < today - timedelta(days=14) or meeting_date > max_date:
            continue
        meeting = Meeting(
            board_id=source.board_id,
            board_name=source.board_name,
            meeting_type=meeting_type,
            meeting_date=meeting_date,
            start_time=parse_time(time_node.get_text(" ", strip=True) if time_node else ""),
            timezone="America/Los_Angeles",
            location="",
            virtual_url="",
            source_page_url=absolute_url(page_url, anchor["href"]),
            agenda_url="",
            agenda_label="",
            confidence_notes="Profiled Golden Sierra Workforce Board calendar category; exact board/executive event cards are followed for agenda and location details.",
        )
        meetings[meeting.stable_id] = meeting
    return sorted(meetings.values(), key=lambda meeting: (meeting.meeting_date, meeting.meeting_type))


def extract_san_joaquin_worknet_meetings(
    source: BoardSource,
    html: str,
    page_url: str,
    today: date,
    lookahead_days: int,
) -> list[Meeting]:
    try:
        payload = json.loads(html)
    except json.JSONDecodeError:
        payload = None
    if isinstance(payload, dict) and isinstance(payload.get("items"), list):
        meetings: list[Meeting] = []
        max_date = today + timedelta(days=lookahead_days)
        for item in payload["items"]:
            if item.get("cancelledAt") or item.get("deletedAt"):
                continue
            try:
                meeting_date = date.fromisoformat(item["date"][:10])
            except (KeyError, TypeError, ValueError):
                continue
            if meeting_date < today - timedelta(days=14) or meeting_date > max_date:
                continue
            start_time = None
            if item.get("startTime"):
                try:
                    start_time = datetime.fromisoformat(item["startTime"].replace("Z", "+00:00")).astimezone(
                        ZoneInfo("America/Los_Angeles")
                    ).time().replace(tzinfo=None)
                except ValueError:
                    pass
            location = ", ".join(
                value.strip()
                for value in (item.get("address", ""), item.get("building", ""), item.get("city", ""), item.get("stateCode", ""))
                if value and value.strip()
            )
            attachment = absolute_url(page_url, item["attachmentLink"]) if item.get("attachmentLink") else ""
            meetings.append(
                Meeting(
                    board_id=source.board_id,
                    board_name=source.board_name,
                    meeting_type="Board Meeting",
                    meeting_date=meeting_date,
                    start_time=start_time,
                    timezone="America/Los_Angeles",
                    location=location,
                    virtual_url=item.get("urlLink") or "",
                    source_page_url=source.meeting_schedule_url,
                    agenda_url=attachment,
                    agenda_label=item.get("attachmentFileName") or "Agenda",
                    confidence_notes="Profiled San Joaquin official agenda API; canceled/deleted records are excluded and agenda attachment, time, and location come from the same record.",
                )
            )
        return sorted(meetings, key=lambda meeting: (meeting.meeting_date, meeting.meeting_type))

    soup = BeautifulSoup(html, "html.parser")
    lines = [line.strip() for line in soup.get_text("\n", strip=True).splitlines() if line.strip()]
    agenda_links = extract_agenda_links(html, page_url)
    meetings: dict[str, Meeting] = {}
    max_date = today + timedelta(days=lookahead_days)
    in_schedule = False
    for index, line in enumerate(lines):
        lowered = line.lower()
        if "workforce development board meeting schedule" in lowered:
            in_schedule = True
            continue
        if in_schedule and "workforce development board links" in lowered:
            break
        if not in_schedule:
            continue
        meeting_date = parse_date(line, today, lookahead_days)
        if not meeting_date or meeting_date < today - timedelta(days=14) or meeting_date > max_date:
            continue
        nearby = " ".join(lines[index : index + 3])
        if "cancel" in nearby.lower():
            continue
        linked_agenda = best_agenda_for_date(agenda_links, meeting_date)
        meeting = Meeting(
            board_id=source.board_id,
            board_name=source.board_name,
            meeting_type="Board Meeting",
            meeting_date=meeting_date,
            start_time=parse_time(nearby),
            timezone="America/Los_Angeles",
            location="",
            virtual_url="",
            source_page_url=page_url,
            agenda_url=linked_agenda.url if linked_agenda else "",
            agenda_label=linked_agenda.label if linked_agenda else "",
            confidence_notes="Profiled San Joaquin extraction: only dates from the official Workforce Development Board Meeting Schedule are published; canceled rows are excluded.",
        )
        meetings[meeting.stable_id] = meeting
    return sorted(meetings.values(), key=lambda m: (m.meeting_date, m.meeting_type))


def extract_sonoma_joblink_board_meetings(
    source: BoardSource,
    html: str,
    page_url: str,
    today: date,
    lookahead_days: int,
) -> list[Meeting]:
    soup = BeautifulSoup(html, "html.parser")
    lines = [line.strip() for line in soup.get_text("\n", strip=True).splitlines() if line.strip()]
    agenda_links = [
        link
        for link in extract_agenda_links(html, page_url)
        if not any(term in f"{link.label} {link.url}".lower() for term in ("labor", "youth", "membership", "ad hoc"))
    ]
    meetings: dict[str, Meeting] = {}
    max_date = today + timedelta(days=lookahead_days)
    for index, line in enumerate(lines):
        lowered = line.lower()
        if "labor" in lowered or "youth" in lowered or "membership" in lowered or "ad hoc" in lowered:
            continue
        if "wib executive committee" in lowered:
            meeting_type = "Executive Committee"
        elif "workforce investment board meeting" in lowered:
            meeting_type = "Board Meeting"
        else:
            continue
        nearby = " ".join(lines[index : index + 8])
        meeting_date = parse_date(nearby, today, lookahead_days)
        if not meeting_date or meeting_date < today - timedelta(days=14) or meeting_date > max_date:
            continue
        linked_agenda = best_agenda_for_date(agenda_links, meeting_date)
        meeting = Meeting(
            board_id=source.board_id,
            board_name=source.board_name,
            meeting_type=meeting_type,
            meeting_date=meeting_date,
            start_time=parse_time(nearby),
            timezone="America/Los_Angeles",
            location=_sonoma_event_location(lines[index + 4 : index + 8]),
            virtual_url=infer_virtual_url(nearby),
            source_page_url=page_url,
            agenda_url=linked_agenda.url if linked_agenda else "",
            agenda_label=linked_agenda.label if linked_agenda else "",
            confidence_notes="Profiled Sonoma extraction: only Job Link Sonoma WIB Executive Committee and Workforce Investment Board event rows are published; labor, youth, membership, and ad hoc committee rows are excluded.",
        )
        meetings[meeting.stable_id] = meeting
    return sorted(meetings.values(), key=lambda m: (m.meeting_date, m.meeting_type))


def extract_solano_board_calendar(
    source: BoardSource,
    html: str,
    page_url: str,
    today: date,
    lookahead_days: int,
) -> list[Meeting]:
    lines = [line.strip() for line in html.splitlines() if line.strip()]
    if "<" in html[:500].lower():
        soup = BeautifulSoup(html, "html.parser")
        lines = [line.strip() for line in soup.get_text("\n", strip=True).splitlines() if line.strip()]
    agenda_links = extract_agenda_links(html, page_url)
    meetings: dict[str, Meeting] = {}
    max_date = today + timedelta(days=lookahead_days)
    location = _solano_location(lines)
    start_time = parse_time(" ".join(lines[:8])) or time(8, 30)

    if "2026 Meeting Dates" in html or "BOARD OF DIRECTORS" in html[:200]:
        for line in lines:
            meeting_date = parse_date(line, today, lookahead_days)
            if not meeting_date or meeting_date < today - timedelta(days=14) or meeting_date > max_date:
                continue
            meeting = _solano_meeting(source, page_url, meeting_date, start_time, location, agenda_links)
            meetings[meeting.stable_id] = meeting
        return sorted(meetings.values(), key=lambda m: (m.meeting_date, m.meeting_type))

    in_board = False
    section_year: int | None = None
    for index, line in enumerate(lines):
        if line == "Board of Directors Meetings":
            in_board = True
            continue
        if in_board and line == "Planning & Oversight Committee Meeting":
            break
        if not in_board:
            continue
        if re.fullmatch(r"20\d{2}", line):
            section_year = int(line)
            continue
        if section_year is None:
            continue
        meeting_date = _month_day_in_year(line, section_year)
        if not meeting_date or meeting_date < today - timedelta(days=14) or meeting_date > max_date:
            continue
        nearby = " ".join(lines[index : index + 3])
        if "cancel" in nearby.lower():
            continue
        meeting = _solano_meeting(source, page_url, meeting_date, start_time, location, agenda_links)
        meetings[meeting.stable_id] = meeting
    return sorted(meetings.values(), key=lambda m: (m.meeting_date, m.meeting_type))


def extract_work2future_board_events(
    source: BoardSource,
    html: str,
    page_url: str,
    today: date,
    lookahead_days: int,
) -> list[Meeting]:
    if "/calendar/" in page_url:
        return extract_event_detail_title_meeting(source, html, page_url, today, lookahead_days)
    soup = BeautifulSoup(html, "html.parser")
    lines = [line.strip() for line in soup.get_text("\n", strip=True).splitlines() if line.strip()]
    detail_urls: dict[str, str] = {}
    for anchor in soup.find_all("a", href=True):
        label = anchor.get_text(" ", strip=True)
        lowered = label.lower()
        if "executive committee meeting" in lowered or "work2future board meeting" in lowered:
            detail_urls[label] = absolute_url(page_url, anchor["href"].strip())
    meetings: dict[str, Meeting] = {}
    max_date = today + timedelta(days=lookahead_days)
    for index, line in enumerate(lines):
        lowered = line.lower()
        if "cancel" in lowered:
            continue
        if "executive committee meeting" in lowered:
            meeting_type = "Executive Committee"
        elif "work2future board meeting" in lowered:
            meeting_type = "Board Meeting"
        else:
            continue
        meeting_date = _work2future_event_date(lines, index)
        if not meeting_date or meeting_date < today - timedelta(days=14) or meeting_date > max_date:
            continue
        location = lines[index + 1] if index + 1 < len(lines) and "|" in lines[index + 1] else ""
        meeting = Meeting(
            board_id=source.board_id,
            board_name=source.board_name,
            meeting_type=meeting_type,
            meeting_date=meeting_date,
            start_time=None,
            timezone="America/Los_Angeles",
            location=location.replace(" | ", ", "),
            virtual_url="",
            source_page_url=detail_urls.get(line, page_url),
            agenda_url="",
            agenda_label="",
            confidence_notes="Profiled work2future extraction: board and executive event cards are published, canceled rows and youth/holiday cards are excluded, and detail pages provide agenda/location/virtual links.",
        )
        meetings[meeting.stable_id] = meeting
    return sorted(meetings.values(), key=lambda m: (m.meeting_date, m.meeting_type))


def extract_tribe_events_api_meetings(
    source: BoardSource,
    html: str,
    page_url: str,
    today: date,
    lookahead_days: int,
) -> list[Meeting]:
    try:
        payload = json.loads(html)
    except json.JSONDecodeError:
        return []
    events = payload.get("events") if isinstance(payload, dict) else []
    if not isinstance(events, list):
        return []
    meetings: dict[str, Meeting] = {}
    max_date = today + timedelta(days=lookahead_days)
    for event in events:
        if not isinstance(event, dict):
            continue
        title = _html_to_text(str(event.get("title") or ""))
        meeting_type = _tribe_event_meeting_type(source.board_id, title, event)
        if not meeting_type:
            continue
        start_dt = _parse_local_datetime(str(event.get("start_date") or ""))
        if not start_dt:
            continue
        meeting_date = start_dt.date()
        if meeting_date < today - timedelta(days=14) or meeting_date > max_date:
            continue
        event_url = str(event.get("url") or page_url)
        description = str(event.get("description") or "")
        agenda = best_agenda_for_date(extract_agenda_links(description, event_url), meeting_date)
        meeting = Meeting(
            board_id=source.board_id,
            board_name=source.board_name,
            meeting_type=meeting_type,
            meeting_date=meeting_date,
            start_time=start_dt.time().replace(microsecond=0),
            timezone=str(event.get("timezone") or "America/Los_Angeles"),
            location=_tribe_event_location(event),
            virtual_url=infer_virtual_url(description) or infer_virtual_url(str(event.get("website") or "")),
            source_page_url=event_url,
            agenda_url=agenda.url if agenda else "",
            agenda_label=agenda.label if agenda else "",
            confidence_notes="Profiled Tribe Events API extraction: REST event rows are filtered to full board and executive committee titles/categories, with workshops and other committees excluded.",
        )
        meetings[meeting.stable_id] = meeting
    return sorted(meetings.values(), key=lambda m: (m.meeting_date, m.meeting_type))


def extract_la_city_novus_meetings(
    source: BoardSource,
    html: str,
    page_url: str,
    today: date,
    lookahead_days: int,
) -> list[Meeting]:
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", id="SearchAgendasMeetings_radGridMeetings_ctl00")
    if not table:
        return []
    meetings: dict[str, Meeting] = {}
    max_date = today + timedelta(days=lookahead_days)
    for row in table.find_all("tr")[1:]:
        cells = row.find_all("td")
        if len(cells) < 3:
            continue
        meeting_date = parse_date(cells[0].get_text(" ", strip=True), today, lookahead_days)
        raw_type = cells[1].get_text(" ", strip=True)
        meeting_type = _la_city_meeting_type(raw_type)
        if not meeting_date or not meeting_type or meeting_date < today - timedelta(days=14) or meeting_date > max_date:
            continue
        agenda_url = ""
        for anchor in row.find_all("a", href=True):
            href = anchor["href"].strip()
            if "DisplayAgendaPDF" in href:
                agenda_url = absolute_url(page_url, href)
                break
        detail_url = _novus_detail_url(row, page_url) or page_url
        meeting = Meeting(
            board_id=source.board_id,
            board_name=source.board_name,
            meeting_type=meeting_type,
            meeting_date=meeting_date,
            start_time=None,
            timezone="America/Los_Angeles",
            location=cells[2].get_text(" ", strip=True).replace("...", "").strip(),
            virtual_url="",
            source_page_url=detail_url,
            agenda_url=agenda_url,
            agenda_label="Agenda PDF" if agenda_url else "",
            confidence_notes="Profiled LA City Novus extraction: only WDB quarterly/full WDB and executive committee rows from the official NovusAgenda iframe are published; Youth Council and other committees are excluded.",
        )
        meetings[meeting.stable_id] = meeting
    return sorted(meetings.values(), key=lambda m: (m.meeting_date, m.meeting_type))


def extract_mother_lode_meetings(
    source: BoardSource,
    html: str,
    page_url: str,
    today: date,
    lookahead_days: int,
) -> list[Meeting]:
    if "<" not in html[:500].lower() and "WDB Meetings" in html:
        return _extract_mother_lode_schedule_pdf(source, html, page_url, today, lookahead_days)
    return _extract_mother_lode_archive_agendas(source, html, page_url, today, lookahead_days)


def extract_santa_ana_wdb_events(
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
        href = anchor["href"].strip()
        if label.strip().lower() != "workforce development board" or "/event/workforce-development-board" not in href:
            continue
        container = anchor.find_parent("li") or anchor.parent
        context = container.get_text(" ", strip=True) if container else label
        meeting_date = parse_date(context, today, lookahead_days)
        if not meeting_date or meeting_date < today - timedelta(days=14) or meeting_date > max_date:
            continue
        meeting = Meeting(
            board_id=source.board_id,
            board_name=source.board_name,
            meeting_type="Board Meeting",
            meeting_date=meeting_date,
            start_time=parse_time(context),
            timezone="America/Los_Angeles",
            location="",
            virtual_url="",
            source_page_url=absolute_url(page_url, href),
            agenda_url="",
            agenda_label="",
            confidence_notes="Profiled Santa Ana extraction: Public Meetings category pages are filtered to Workforce Development Board event links only; unrelated city public meetings and WORK Center events are excluded.",
        )
        meetings[meeting.stable_id] = meeting
    return sorted(meetings.values(), key=lambda m: (m.meeting_date, m.meeting_type))


def extract_santa_barbara_hcms_agendas(
    source: BoardSource,
    html: str,
    page_url: str,
    today: date,
    lookahead_days: int,
) -> list[Meeting]:
    config = _hcms_config(html)
    if not config:
        return []
    base_url, app_name, token = config
    tags = _santa_barbara_hcms_tags(html, page_url, today, lookahead_days)
    meetings: dict[str, Meeting] = {}
    max_date = today + timedelta(days=lookahead_days)
    for tag in tags:
        tag_filter = urllib.parse.quote(f"tags/any(t:t eq '{tag}')", safe="()/ ")
        api_url = (
            f"https://{base_url}/api/content/{app_name}/agendasandminutes"
            f"?%24top=50&%24filter={tag_filter}"
        ).replace(" ", "%20")
        try:
            page = fetch_url(api_url, timeout=15, retries=1, extra_headers={"Authorization": token, "Accept": "application/json"})
            payload = json.loads(page.text)
        except Exception:
            continue
        for item in payload.get("items", []):
            if not isinstance(item, dict):
                continue
            data = item.get("data") if isinstance(item.get("data"), dict) else {}
            meeting_date = _hcms_meeting_date(data)
            if not meeting_date or meeting_date < today - timedelta(days=14) or meeting_date > max_date:
                continue
            meeting_type = "Executive Committee" if "executive" in tag.lower() or "executive" in _hcms_text(data.get("boardname")).lower() else "Board Meeting"
            agenda_ids = _hcms_list(data.get("agenda"))
            agenda_url = f"https://{base_url}/api/assets/{app_name}/{agenda_ids[0]}" if agenda_ids else ""
            meeting = Meeting(
                board_id=source.board_id,
                board_name=source.board_name,
                meeting_type=meeting_type,
                meeting_date=meeting_date,
                start_time=None,
                timezone="America/Los_Angeles",
                location="",
                virtual_url="",
                source_page_url=page_url,
                agenda_url=agenda_url,
                agenda_label="Agenda PDF" if agenda_url else "",
                confidence_notes="Profiled Santa Barbara CivicPlus extraction: WDB agenda widgets are read through the public HCMS API by year tag; agenda PDF assets are linked directly when present.",
            )
            meetings[meeting.stable_id] = meeting
    return sorted(meetings.values(), key=lambda m: (m.meeting_date, m.meeting_type))


def _html_to_text(value: str) -> str:
    return BeautifulSoup(value, "html.parser").get_text(" ", strip=True)


def _parse_local_datetime(value: str) -> datetime | None:
    if not value:
        return None
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(value[:19], fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def _tribe_event_meeting_type(board_id: str, title: str, event: dict) -> str:
    lowered = title.lower()
    category_slugs = {str(category.get("slug") or "").lower() for category in event.get("categories") or [] if isinstance(category, dict)}
    if board_id == "fresno-regional-wdb":
        if "executive committee meeting" == lowered or "executive_committee" in category_slugs:
            return "Executive Committee"
        if lowered == "frwdb meeting" or "workforce_development_board" in category_slugs:
            return "Board Meeting"
        return ""
    if board_id == "sacramento-seta":
        if lowered == "sacramento works executive committee":
            return "Executive Committee"
        if lowered == "sacramento works, inc. board":
            return "Board Meeting"
        return ""
    return infer_meeting_type(title) if "meeting" in lowered else ""


def _tribe_event_location(event: dict) -> str:
    venue = event.get("venue")
    if not isinstance(venue, dict):
        return ""
    parts = [
        str(venue.get("venue") or "").strip(),
        str(venue.get("address") or "").strip(),
        str(venue.get("city") or "").strip(),
        str(venue.get("stateprovince") or venue.get("state") or "").strip(),
        str(venue.get("zip") or "").strip(),
    ]
    if parts[2] and parts[3]:
        city_state_zip = " ".join(part for part in [f"{parts[2]}, {parts[3]}", parts[4]] if part)
        parts = parts[:2] + [city_state_zip]
    return ", ".join(dict.fromkeys(part for part in parts if part and part.lower() != "tbd"))


def _la_city_meeting_type(raw_type: str) -> str:
    lowered = raw_type.lower()
    if "youth" in lowered or "business services" in lowered or "oversight" in lowered or "orientation" in lowered:
        return ""
    if "executive committee" in lowered:
        return "Executive Committee"
    if "wdb quarterly" in lowered or "wdb meeting" in lowered or "full wdb" in lowered:
        return "Board Meeting"
    return ""


def _novus_detail_url(row, page_url: str) -> str:
    html = str(row)
    match = re.search(r"MeetingView\.aspx\?MeetingID=\d+[^'\"&<]*(?:&amp;[^'\"<]+)?", html)
    if not match:
        return ""
    return absolute_url(page_url, match.group(0).replace("&amp;", "&"))


def _extract_mother_lode_schedule_pdf(
    source: BoardSource,
    text: str,
    page_url: str,
    today: date,
    lookahead_days: int,
) -> list[Meeting]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    meetings: dict[str, Meeting] = {}
    max_date = today + timedelta(days=lookahead_days)
    location = _mother_lode_location(lines)
    in_wdb = False
    for index, line in enumerate(lines):
        if line == "WDB Meetings":
            in_wdb = True
            continue
        if in_wdb and (line.startswith("Lunch provided") or line == "CSEDD Meetings"):
            break
        if not in_wdb:
            continue
        meeting_date = parse_date(line, today, lookahead_days)
        if not meeting_date or meeting_date < today - timedelta(days=14) or meeting_date > max_date:
            continue
        nearby = " ".join(lines[index : index + 2])
        meeting = Meeting(
            board_id=source.board_id,
            board_name=source.board_name,
            meeting_type="Board Meeting",
            meeting_date=meeting_date,
            start_time=parse_time(nearby),
            timezone="America/Los_Angeles",
            location=location,
            virtual_url="",
            source_page_url=page_url,
            agenda_url="",
            agenda_label="",
            confidence_notes="Profiled Mother Lode extraction: future WDB dates come only from the current Board Meeting Schedule PDF's WDB Meetings section; BOD and CSEDD meetings are excluded.",
        )
        meetings[meeting.stable_id] = meeting
    return sorted(meetings.values(), key=lambda m: (m.meeting_date, m.meeting_type))


def _extract_mother_lode_archive_agendas(
    source: BoardSource,
    html: str,
    page_url: str,
    today: date,
    lookahead_days: int,
) -> list[Meeting]:
    meetings: dict[str, Meeting] = {}
    max_date = today + timedelta(days=lookahead_days)
    for meeting_date, agenda in _mother_lode_archive_links(html, page_url, today, lookahead_days).items():
        if meeting_date < today - timedelta(days=14) or meeting_date > max_date:
            continue
        meeting = Meeting(
            board_id=source.board_id,
            board_name=source.board_name,
            meeting_type="Board Meeting",
            meeting_date=meeting_date,
            start_time=None,
            timezone="America/Los_Angeles",
            location="",
            virtual_url="",
            source_page_url=page_url,
            agenda_url=agenda.url,
            agenda_label=agenda.label,
            confidence_notes="Profiled Mother Lode extraction: agenda archive rows are accepted only when the row is Mother Lode Workforce Development Board, not canceled, and the linked document is labeled AGENDA.",
        )
        meetings[meeting.stable_id] = meeting
    return sorted(meetings.values(), key=lambda m: (m.meeting_date, m.meeting_type))


def _mother_lode_archive_links(html: str, page_url: str, today: date, lookahead_days: int) -> dict[date, AgendaLink]:
    soup = BeautifulSoup(html, "html.parser")
    links: dict[date, AgendaLink] = {}
    for anchor in soup.find_all("a", href=True):
        if anchor.get_text(" ", strip=True).upper() != "AGENDA":
            continue
        parent = anchor.parent
        context = ""
        while parent:
            context = parent.get_text(" ", strip=True)
            if "Mother Lode Workforce Development Board" in context or len(context) > 500:
                break
            parent = parent.parent
        lowered = context.lower()
        if "mother lode workforce development board" not in lowered or "cancel" in lowered:
            continue
        meeting_date = parse_date(context, today, lookahead_days)
        if not meeting_date:
            continue
        links[meeting_date] = AgendaLink(absolute_url(page_url, anchor["href"].strip()), context, page_url)
    return links


def _mother_lode_location(lines: list[str]) -> str:
    parts: list[str] = []
    for line in lines:
        if line.startswith("Primary Location") or line.startswith("Teleconference"):
            parts.append(line.replace("Primary Location In-Person:", "In-person:").strip())
    return "; ".join(parts)


def _hcms_config(html: str) -> tuple[str, str, str] | None:
    match = re.search(
        r"hcmsReadOnlyConfiguration:\{baseUrl:\"([^\"]+)\",appName:\"([^\"]+)\".*?userToken:\"([^\"]+)\"",
        html,
        re.S,
    )
    if not match:
        return None
    return match.group(1), match.group(2), match.group(3)


def _santa_barbara_hcms_tags(html: str, page_url: str, today: date, lookahead_days: int) -> list[str]:
    years = {today.year, (today + timedelta(days=lookahead_days)).year}
    tags = set(re.findall(r"ds-wdb-[a-z0-9-]+(?:20\d{2})", html))
    if "Board-Agendas" in page_url:
        tags.update(f"ds-wdb-board-agendas-{year}" for year in years)
    if "Executive-Committee-Agendas" in page_url:
        tags.update(f"ds-wdb-executive-agendas-{year}" for year in years)
    return sorted(tags)


def _hcms_meeting_date(data: dict) -> date | None:
    value = _hcms_text(data.get("meetingdate"))
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return parse_date(value)


def _hcms_text(value) -> str:
    if isinstance(value, dict):
        if "en" in value:
            return str(value.get("en") or "")
        if "iv" in value:
            return str(value.get("iv") or "")
    return str(value or "")


def _hcms_list(value) -> list[str]:
    if isinstance(value, dict):
        raw = value.get("iv") or value.get("en") or []
        if isinstance(raw, list):
            return [str(item) for item in raw if item]
    return []


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
    decoded = unescape(text)
    for match in re.finditer(r"https?://[^\s<>\"']+", decoded, re.IGNORECASE):
        url = match.group(0).rstrip(").,;:]}>")
        lowered = url.lower()
        if any(
            token in lowered
            for token in (
                "zoom.us/",
                "teams.microsoft.com/",
                "meet.google.com/",
                "webex.com/",
                "meet.goto.com/",
                "gotomeet.me/",
            )
        ):
            return url
    return ""


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


def _madera_location(lines: list[str]) -> str:
    for index, line in enumerate(lines):
        if "2037 W. Cleveland Avenue" in line:
            prefix = "Workforce Assistance Center Executive Conference Room"
            city_parts = []
            for candidate in lines[index + 1 : index + 3]:
                if re.fullmatch(r"\d{5}", candidate) or "Madera" in candidate:
                    city_parts.append(candidate)
            suffix = ", ".join(city_parts) if city_parts else "Madera, CA 93637"
            return f"{prefix}, {line}, {suffix}"
    return ""


def _sonoma_event_location(lines: list[str]) -> str:
    parts: list[str] = []
    for line in lines:
        if parse_date(line) or parse_time(line) or line == "-":
            continue
        if len(line) > 100 or line.lower().startswith("we will"):
            continue
        if line == "Job Link Office" or "Capricorn" in line:
            parts.append(line)
    return ", ".join(dict.fromkeys(parts))


def _solano_location(lines: list[str]) -> str:
    for index, line in enumerate(lines):
        if "500 Chadbourne Road" in line:
            prefix = lines[index - 1] if index > 0 and "Workforce Development Board" in lines[index - 1] else "Workforce Development Board of Solano County"
            city = lines[index + 1] if index + 1 < len(lines) and "Fairfield" in lines[index + 1] else "Fairfield, CA 94534"
            return f"{prefix}, {line}, {city}"
    return "Workforce Development Board of Solano County, 500 Chadbourne Road, Suite A, Fairfield, CA 94534"


def _month_day_in_year(text: str, year: int) -> date | None:
    match = re.search(rf"\b({MONTH_NAMES})\.?\s+(\d{{1,2}})(?:st|nd|rd|th)?\b", text, re.I)
    if not match:
        return None
    try:
        return date(year, _month_number(match.group(1)), int(match.group(2)))
    except ValueError:
        return None


def _work2future_event_date(lines: list[str], title_index: int) -> date | None:
    year = None
    for candidate in reversed(lines[max(0, title_index - 12) : title_index]):
        match = re.fullmatch(rf"({MONTH_NAMES})\s+(20\d{{2}})", candidate, re.I)
        if match:
            year = int(match.group(2))
            break
    if year is None:
        return None
    day = None
    month = None
    for candidate in reversed(lines[max(0, title_index - 5) : title_index]):
        if day is None and re.fullmatch(r"\d{1,2}", candidate):
            day = int(candidate)
            continue
        if month is None and _month_number_or_none(candidate) is not None:
            month = _month_number(candidate)
    if day is None or month is None:
        return None
    try:
        return date(year, month, day)
    except ValueError:
        return None


def _solano_meeting(
    source: BoardSource,
    page_url: str,
    meeting_date: date,
    start_time: time,
    location: str,
    agenda_links: list[AgendaLink],
) -> Meeting:
    linked_agenda = best_agenda_for_date(agenda_links, meeting_date)
    return Meeting(
        board_id=source.board_id,
        board_name=source.board_name,
        meeting_type="Board Meeting",
        meeting_date=meeting_date,
        start_time=start_time,
        timezone="America/Los_Angeles",
        location=location,
        virtual_url="",
        source_page_url=page_url,
        agenda_url=linked_agenda.url if linked_agenda else "",
        agenda_label=linked_agenda.label if linked_agenda else "",
        confidence_notes="Profiled Solano extraction: future board dates come from the official 2026 Board of Directors meeting calendar PDF; agenda packets are date-matched from the Board of Directors page when posted.",
    )


def _rescheduled_date(text: str) -> date | None:
    original_year = re.search(r"\b(20\d{2})\b", text)
    if not original_year or "rescheduled to" not in text.lower():
        return None
    match = re.search(rf"rescheduled to\s+(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday),?\s+({MONTH_NAMES})\.?\s+(\d{{1,2}})(?:st|nd|rd|th)?", text, re.I)
    if not match:
        return None
    return date(int(original_year.group(1)), _month_number(match.group(1)), int(match.group(2)))


def _extract_long_beach_primegov_meetings(
    source: BoardSource,
    text: str,
    page_url: str,
    today: date,
    lookahead_days: int,
) -> list[Meeting]:
    try:
        rows = json.loads(text)
    except json.JSONDecodeError:
        return []
    if not isinstance(rows, list):
        return []
    meetings: dict[str, Meeting] = {}
    max_date = today + timedelta(days=lookahead_days)
    for row in rows:
        if not isinstance(row, dict):
            continue
        title = str(row.get("title") or "")
        if "workforce innovation network" not in title.lower():
            continue
        date_time = str(row.get("dateTime") or "")
        try:
            parsed_datetime = datetime.fromisoformat(date_time)
        except ValueError:
            continue
        meeting_date = parsed_datetime.date()
        if meeting_date < today - timedelta(days=14) or meeting_date > max_date:
            continue
        agenda = _primegov_agenda_link(row, page_url)
        meeting = Meeting(
            board_id=source.board_id,
            board_name=source.board_name,
            meeting_type="Board Meeting",
            meeting_date=meeting_date,
            start_time=parsed_datetime.time().replace(microsecond=0),
            timezone="America/Los_Angeles",
            location="",
            virtual_url=str(row.get("zoomMeetingLink") or ""),
            source_page_url=source.meeting_schedule_url,
            agenda_url=agenda.url if agenda else "",
            agenda_label=agenda.label if agenda else "",
            confidence_notes="Profiled Long Beach extraction: agenda link comes from the official OneMeeting/PrimeGov public API for the LBWIN committee.",
        )
        meetings[meeting.stable_id] = meeting
    return sorted(meetings.values(), key=lambda m: (m.meeting_date, m.meeting_type))


def _primegov_agenda_link(row: dict, page_url: str) -> AgendaLink | None:
    for document in row.get("documentList") or []:
        if not isinstance(document, dict):
            continue
        name = str(document.get("templateName") or "")
        if name.lower() != "agenda":
            continue
        link = document.get("link")
        if link:
            return AgendaLink(absolute_url(page_url, str(link)), name, page_url)
        template_id = document.get("templateId")
        output_type = document.get("compileOutputType") or 1
        if template_id:
            return AgendaLink(
                absolute_url(page_url, f"/Public/CompiledDocument?meetingTemplateId={template_id}&compileOutputType={output_type}"),
                name,
                page_url,
            )
    return None


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
        label = link.label.lower()
        if str(meeting_date.year) in label and meeting_date.strftime("%B").lower() in label:
            return link
        if str(meeting_date.year) in label and meeting_date.strftime("%b").lower() in label:
            return link
    return None


def best_agenda_for_meeting(
    links: Iterable[AgendaLink],
    meeting_date: date,
    meeting_type: str,
) -> Optional[AgendaLink]:
    """Choose a date-matched agenda that also belongs to the requested body."""
    candidates = [link for link in links if best_agenda_for_date([link], meeting_date)]
    if not candidates:
        return None
    wanted = meeting_type.lower()
    excluded_terms = ("audit", "deia", "youth", "policy", "finance", "business services", "program services")

    def score(link: AgendaLink) -> int:
        value = f"{link.label} {link.url}".lower()
        points = 0
        if "executive" in wanted:
            points += 12 if any(term in value for term in ("executive", "exec", "ex-cmte")) else -6
        else:
            points += 8 if any(term in value for term in ("wdb", "workforce development board", "board meeting")) else 0
            points -= 8 if any(term in value for term in ("executive", "exec", "ex-cmte")) else 0
        points -= 20 * sum(term in value for term in excluded_terms)
        points += 2 if "agenda" in value else 0
        return points

    winner = max(candidates, key=score)
    return winner if score(winner) >= 0 else None


def _date_labeled_links_by_date(
    html: str,
    page_url: str,
    today: date,
    lookahead_days: int,
) -> dict[date, AgendaLink]:
    soup = BeautifulSoup(html, "html.parser")
    links: dict[date, AgendaLink] = {}
    for anchor in soup.find_all("a", href=True):
        label = anchor.get_text(" ", strip=True)
        linked_date = parse_date(label, today, lookahead_days)
        if not linked_date:
            continue
        href = anchor["href"].strip()
        if not href or href.startswith(("mailto:", "tel:", "#")):
            continue
        links[linked_date] = AgendaLink(absolute_url(page_url, href), label, page_url)
    return links


def _agenda_context_label(anchor, label: str) -> str:
    normalized_label = label.strip()
    if _month_number_or_none(normalized_label) is None:
        return ""
    nearby_text = []
    parent = anchor.parent
    if parent:
        nearby_text.append(parent.get_text(" ", strip=True))
    previous_heading = anchor.find_previous(["h1", "h2", "h3", "h4", "h5", "h6"])
    if previous_heading:
        nearby_text.append(previous_heading.get_text(" ", strip=True))
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
            row_location = ""
            for row in soup.find_all("tr"):
                cells = row.find_all("td")
                if not cells or parse_date(cells[0].get_text(" ", strip=True), today, lookahead_days) != meeting_date:
                    continue
                heading = row.find_previous(["h1", "h2", "h3", "h4", "h5"])
                heading_text = heading.get_text(" ", strip=True).lower() if heading else ""
                if meeting_type == "Executive Committee" and "executive" not in heading_text:
                    continue
                if meeting_type == "Board Meeting" and "executive" in heading_text:
                    continue
                agenda_anchor = next(
                    (anchor for anchor in row.find_all("a", href=True) if "agenda" in anchor.get_text(" ", strip=True).lower()),
                    None,
                )
                if agenda_anchor:
                    agenda_text = f"{agenda_anchor.get_text(' ', strip=True)} {agenda_anchor['href']}"
                    if agenda_link_date_conflicts(agenda_text, meeting_date):
                        agenda_anchor = None
                if agenda_anchor:
                    linked_agenda = AgendaLink(
                        absolute_url(page_url, agenda_anchor["href"]),
                        agenda_anchor.get_text(" ", strip=True),
                        page_url,
                    )
                if len(cells) > 1:
                    row_location = cells[1].get_text(" ", strip=True)
                break
            meeting = Meeting(
                board_id=source.board_id,
                board_name=source.board_name,
                meeting_type=meeting_type,
                meeting_date=meeting_date,
                start_time=parse_time(nearby),
                timezone="America/Los_Angeles",
                location=row_location,
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


def agenda_link_date_conflicts(value: str, meeting_date: date) -> bool:
    linked_date = _date_from_numeric_filename(value, meeting_date)
    return bool(linked_date and linked_date != meeting_date)


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
