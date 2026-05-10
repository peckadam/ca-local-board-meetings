from __future__ import annotations

import argparse
import logging
from dataclasses import asdict, replace
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from .agendas import agenda_folder, download_agenda
from .agenda_content import extract_agenda_details
from .extraction import extract_meetings, find_candidate_pages
from .fetcher import fetch_url
from .graph import CALENDAR_NAME, GraphClient, GraphConfigError
from .models import BoardSource, Meeting, StoredAgenda
from .registry import load_registry, mark_checked, save_registry
from .reporting import append_progress_log, build_summary, write_reports
from .site_profiles import load_profiles
from .storage import (
    agenda_exists,
    connect,
    future_meetings,
    meetings_for_calendar,
    prune_unseen_future_meetings,
    save_agenda_record,
    set_calendar_event_id,
    upsert_meetings,
    write_run_log,
)
from .web_calendar import write_web_calendar

LOGGER = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "local_board_meetings"
DEFAULT_REGISTRY = DATA_DIR / "source_registry.csv"
DEFAULT_DB = DATA_DIR / "meetings.sqlite3"
DEFAULT_REPORTS = DATA_DIR / "reports"
DEFAULT_AGENDAS = DATA_DIR / "agendas"
DEFAULT_PUBLIC = DATA_DIR / "public"
DEFAULT_PROGRESS = DATA_DIR / "progress_log.md"
DEFAULT_SEED = PROJECT_ROOT / "data" / "cwa-local-board-logos" / "manifest.csv"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level), format="%(levelname)s %(name)s: %(message)s")
    started_at = datetime.now(timezone.utc)
    run_id = started_at.strftime("%Y%m%dT%H%M%SZ")
    mode = "live" if args.live else "dry-run"
    if args.live:
        GraphClient.from_env()
    conn = connect(args.db)
    all_sources = load_registry(args.registry, args.seed_manifest)
    profiles = load_profiles(args.source_profiles)
    sources = all_sources
    if args.boards:
        selected = {item.lower() for item in args.boards}
        sources = [source for source in sources if source.board_id.lower() in selected or source.board_name.lower() in selected]
    if args.limit:
        sources = sources[: args.limit]

    all_meetings: list[Meeting] = []
    failures: list[dict[str, str]] = []
    updated_sources: list[BoardSource] = []

    for source in sources:
        LOGGER.info("Checking %s", source.board_name)
        source_meetings, source_failures, updated_source = check_source(
            source,
            args.lookahead_days,
            args.respect_robots,
            profiles.get(source.board_id),
        )
        all_meetings.extend(source_meetings)
        failures.extend(source_failures)
        updated_sources.append(updated_source)

    updated_by_id = {source.board_id: source for source in updated_sources}
    save_registry(args.registry, [updated_by_id.get(source.board_id, source) for source in all_sources])
    new_meetings, updated_meetings = upsert_meetings(conn, all_meetings, started_at)
    prune_unseen_future_meetings(
        conn,
        [source.board_id for source in sources],
        [meeting.stable_id for meeting in all_meetings],
        started_at,
    )

    agendas_downloaded = 0
    agenda_upload_links: dict[str, str] = {}
    if args.download_agendas or args.live:
        for meeting in all_meetings:
            if should_check_agenda(meeting, started_at.date()):
                agenda = download_agenda(meeting, args.agenda_dir, respect_robots=args.respect_robots)
                if agenda and not agenda_exists(conn, agenda.meeting_id, agenda.source_url, agenda.sha256):
                    agendas_downloaded += 1
                    uploaded_link = ""
                    if args.live:
                        uploaded_link = upload_agenda_live(args, agenda, meeting)
                        agenda = StoredAgenda(**{**asdict(agenda), "onedrive_web_url": uploaded_link})
                    save_agenda_record(conn, agenda)
                    if uploaded_link:
                        agenda_upload_links[meeting.stable_id] = uploaded_link

    events_updated = 0
    if args.live:
        events_updated = sync_calendar_live(conn, args, started_at, agenda_upload_links)
    web_calendar_paths = write_web_calendar(args.public_dir, future_meetings(conn, started_at), started_at)

    summary = build_summary(
        started_at=started_at,
        mode=mode,
        boards_checked=len(sources),
        meetings=all_meetings,
        new_meetings=new_meetings,
        updated_meetings=updated_meetings,
        events_updated=events_updated,
        agendas_downloaded=agendas_downloaded,
        failures=failures,
    )
    write_run_log(conn, run_id, started_at, mode, summary)
    json_report, md_report = write_reports(args.report_dir, run_id, summary, all_meetings)
    append_progress_log(args.progress_log, summary)
    print(f"Run report: {md_report}")
    print(f"Run report JSON: {json_report}")
    print(f"Online calendar HTML: {web_calendar_paths[0]}")
    print(f"Calendar ICS feed: {web_calendar_paths[1]}")
    print(f"Boards checked: {summary['boards_checked']}")
    print(f"Meetings found: {summary['meetings_found']}")
    print(f"Missing agendas within 72 hours: {len(summary['missing_agendas_within_72_hours'])}")
    print(f"Failures requiring human review: {len(summary['failures_requiring_human_review'])}")
    return 0


def check_source(source: BoardSource, lookahead_days: int, respect_robots: bool, profile=None) -> tuple[list[Meeting], list[dict[str, str]], BoardSource]:
    urls = [source.meeting_schedule_url, source.agenda_minutes_url, source.executive_committee_url, source.main_website]
    urls = list(dict.fromkeys([url for url in urls if url]))
    configured_content_urls = {source.meeting_schedule_url, source.agenda_minutes_url, source.executive_committee_url} - {"", source.main_website}
    meetings: list[Meeting] = []
    failures: list[dict[str, str]] = []
    notes = source.notes
    confidence = source.confidence
    candidate_updates: dict[str, str] = {}
    for url in urls:
        try:
            page = fetch_url(url, respect_robots=respect_robots)
            if "pdf" in page.content_type.lower():
                continue
            if url != source.main_website or not configured_content_urls:
                extracted = extract_meetings(
                    source,
                    page.text,
                    page.url,
                    date.today(),
                    lookahead_days,
                    extraction_strategy=profile.extraction_strategy if profile else "generic",
                )
                for meeting in extracted:
                    enriched, enrichment_failure = enrich_meeting_from_agenda(meeting, respect_robots)
                    meetings.append(enriched)
                    if enrichment_failure:
                        failures.append({"board_name": source.board_name, "url": meeting.agenda_url, "error": enrichment_failure})
            if not profile or profile.status == "unaudited":
                candidates = find_candidate_pages(page.text, page.url)
                if candidates["meeting"]:
                    candidate_updates["meeting_schedule_url"] = candidates["meeting"][0]
                if candidates["agenda"]:
                    candidate_updates["agenda_minutes_url"] = candidates["agenda"][0]
                if candidates["executive"]:
                    candidate_updates["executive_committee_url"] = candidates["executive"][0]
        except Exception as exc:
            failures.append({"board_name": source.board_name, "url": url, "error": str(exc)})
    data = asdict(mark_checked(source, notes=notes, confidence=confidence))
    applied_candidate_update = False
    for key, value in candidate_updates.items():
        if not data.get(key) or data.get(key) == source.main_website:
            data[key] = value
            applied_candidate_update = True
    if applied_candidate_update:
        note = "Candidate links found automatically; verify exact endpoints before raising confidence."
        data["notes"] = data["notes"] if note in data["notes"] else f"{data['notes']} {note}"
        data["confidence"] = "medium"
    return _dedupe_meetings(meetings), failures, BoardSource(**data)


def enrich_meeting_from_agenda(meeting: Meeting, respect_robots: bool) -> tuple[Meeting, str]:
    if not meeting.agenda_url or (meeting.location and meeting.virtual_url):
        return meeting, ""
    try:
        page = fetch_url(meeting.agenda_url, timeout=15, retries=1, respect_robots=respect_robots)
    except Exception as exc:
        return meeting, f"Agenda location enrichment failed: {exc}"
    details = extract_agenda_details(page.body, page.content_type, page.url)
    updates = {}
    notes: list[str] = []
    if details.location and not meeting.location:
        updates["location"] = details.location
        notes.append("location")
    if details.virtual_url and not meeting.virtual_url:
        updates["virtual_url"] = details.virtual_url
        notes.append("virtual link")
    if not updates:
        return meeting, ""
    confidence_note = f"{meeting.confidence_notes} Agenda parsed for {' and '.join(notes)}.".strip()
    return replace(meeting, **updates, confidence_notes=confidence_note), ""


def should_check_agenda(meeting: Meeting, today: date) -> bool:
    if not meeting.agenda_url:
        return False
    if meeting.meeting_date >= today:
        return (meeting.meeting_date - today).days <= 10
    return (today - meeting.meeting_date).days <= 14


def upload_agenda_live(args: argparse.Namespace, agenda: StoredAgenda, meeting: Meeting) -> str:
    client = GraphClient.from_env()
    relative_folder = agenda_folder(Path("CWA/Local Board Meetings"), meeting)
    drive_path = str(relative_folder / Path(agenda.local_path).name)
    uploaded = client.upload_file(Path(agenda.local_path), drive_path)
    return uploaded.get("webUrl", "")


def sync_calendar_live(conn, args: argparse.Namespace, started_at: datetime, agenda_upload_links: dict[str, str]) -> int:
    try:
        client = GraphClient.from_env()
    except GraphConfigError:
        raise
    calendar_id = client.ensure_calendar(CALENDAR_NAME)
    count = 0
    for row in meetings_for_calendar(conn, started_at, args.lookahead_days):
        meeting = Meeting(
            board_id=row["board_id"],
            board_name=row["board_name"],
            meeting_type=row["meeting_type"],
            meeting_date=date.fromisoformat(row["meeting_date"]),
            start_time=datetime.strptime(row["start_time"], "%H:%M:%S").time() if row["start_time"] else None,
            timezone=row["timezone"],
            location=row["location"] or "",
            virtual_url=row["virtual_url"] or "",
            source_page_url=row["source_page_url"],
            agenda_url=row["agenda_url"] or "",
            agenda_label=row["agenda_label"] or "",
            confidence_notes=row["confidence_notes"] or "",
        )
        event_id = client.upsert_event(calendar_id, meeting, row["calendar_event_id"] or "", agenda_upload_links.get(meeting.stable_id, ""))
        set_calendar_event_id(conn, meeting.stable_id, event_id)
        count += 1
    return count


def _dedupe_meetings(meetings: list[Meeting]) -> list[Meeting]:
    by_id = {meeting.stable_id: meeting for meeting in meetings}
    return sorted(by_id.values(), key=lambda m: (m.meeting_date, m.board_name, m.meeting_type))


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Monitor California local workforce board meeting schedules and agendas.")
    parser.add_argument("--live", action="store_true", help="Write to Microsoft Graph. Default is dry-run.")
    parser.add_argument("--download-agendas", action="store_true", help="Download found agendas locally during dry-run.")
    parser.add_argument("--limit", type=int, default=0, help="Limit boards checked, useful for smoke tests.")
    parser.add_argument("--boards", nargs="*", default=[], help="Specific board ids or exact board names to check.")
    parser.add_argument("--lookahead-days", type=int, default=180)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--seed-manifest", type=Path, default=DEFAULT_SEED)
    parser.add_argument("--db", type=Path, default=DEFAULT_DB)
    parser.add_argument("--report-dir", type=Path, default=DEFAULT_REPORTS)
    parser.add_argument("--agenda-dir", type=Path, default=DEFAULT_AGENDAS)
    parser.add_argument("--public-dir", type=Path, default=DEFAULT_PUBLIC)
    parser.add_argument("--progress-log", type=Path, default=DEFAULT_PROGRESS)
    parser.add_argument("--source-profiles", type=Path, default=DATA_DIR / "source_profiles.json")
    parser.add_argument("--respect-robots", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    return parser.parse_args(argv)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GraphConfigError as exc:
        print(f"Live mode configuration error: {exc}")
        raise SystemExit(2)
