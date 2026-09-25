from __future__ import annotations

import argparse
import logging
from dataclasses import asdict, replace
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from .agendas import agenda_folder, download_agenda
from .agenda_content import extract_agenda_details, extract_text_from_content
from .agenda_notifications import SmtpConfig, process_agenda_notifications, smtp_sender
from .cadence import load_cadence_registry
from .coverage import update_coverage_history, write_coverage_report
from .extraction import agenda_link_date_conflicts, best_agenda_for_date, extract_agenda_links, extract_meetings, find_candidate_pages, parse_time
from .fetcher import fetch_url
from .graph import CALENDAR_NAME, GraphClient, GraphConfigError
from .models import BoardSource, Meeting, StoredAgenda
from .meeting_state import merge_active_meetings
from .registry import load_registry, mark_checked, save_registry
from .reporting import append_progress_log, build_summary, write_reports
from .site_profiles import load_profiles
from .storage import (
    agenda_exists,
    connect,
    meetings_for_calendar,
    save_agenda_record,
    set_calendar_event_id,
    upsert_meetings,
    write_run_log,
)
from .web_calendar import write_web_calendar

LOGGER = logging.getLogger(__name__)
RUN_TIMEZONE = ZoneInfo("America/Los_Angeles")
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data" / "local_board_meetings"
DEFAULT_REGISTRY = DATA_DIR / "source_registry.csv"
DEFAULT_DB = DATA_DIR / "meetings.sqlite3"
DEFAULT_REPORTS = DATA_DIR / "reports"
DEFAULT_AGENDAS = DATA_DIR / "agendas"
DEFAULT_PUBLIC = DATA_DIR / "public"
DEFAULT_PROGRESS = DATA_DIR / "progress_log.md"
DEFAULT_COVERAGE_HISTORY = DATA_DIR / "coverage_history.json"
DEFAULT_COVERAGE_REPORT = DATA_DIR / "coverage_matrix.md"
DEFAULT_NOTIFICATION_STATE = DATA_DIR / "agenda_notifications.json"
DEFAULT_MEETING_STATE = DATA_DIR / "active_meetings.json"
DEFAULT_SEED = PROJECT_ROOT / "data" / "cwa-local-board-logos" / "manifest.csv"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    logging.basicConfig(level=getattr(logging, args.log_level), format="%(levelname)s %(name)s: %(message)s")
    started_at = datetime.now(timezone.utc)
    local_started_at = started_at.astimezone(RUN_TIMEZONE)
    today = local_started_at.date()
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
            today,
            profiles.get(source.board_id),
        )
        source_meetings = _dedupe_meetings(
            source_meetings + confirmed_profile_meetings(source, profiles.get(source.board_id), today, args.lookahead_days)
        )
        source_meetings = [_remove_conflicting_agenda(meeting) for meeting in source_meetings]
        all_meetings.extend(source_meetings)
        failures.extend(source_failures)
        updated_sources.append(updated_source)

    updated_by_id = {source.board_id: source for source in updated_sources}
    save_registry(args.registry, [updated_by_id.get(source.board_id, source) for source in all_sources])
    new_meetings, updated_meetings = upsert_meetings(conn, all_meetings, started_at)
    active_meetings = merge_active_meetings(args.meeting_state, all_meetings, local_started_at, today)
    upsert_meetings(conn, active_meetings, started_at)

    agendas_downloaded = 0
    agenda_upload_links: dict[str, str] = {}
    if args.download_agendas or args.live:
        for meeting in all_meetings:
            if should_check_agenda(meeting, today):
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
        events_updated = sync_calendar_live(conn, args, local_started_at, agenda_upload_links)

    notifications_sent = 0
    if args.notify_agendas or args.bootstrap_agenda_notifications:
        sender = smtp_sender(SmtpConfig.from_env()) if args.notify_agendas else None
        notifications_sent, notification_failures = process_agenda_notifications(
            active_meetings,
            args.notification_state,
            today,
            args.respect_robots,
            sender,
            bootstrap=args.bootstrap_agenda_notifications,
        )
        failures.extend(notification_failures)

    coverage_history = update_coverage_history(
        args.coverage_history,
        conn,
        all_sources,
        active_meetings,
        local_started_at,
        profiles,
    )
    cadence_records = load_cadence_registry()
    coverage_totals = write_coverage_report(
        args.coverage_report,
        coverage_history,
        all_sources,
        profiles,
        active_meetings,
        failures,
        local_started_at,
        cadence_records,
    )
    web_calendar_paths = write_web_calendar(
        args.public_dir,
        active_meetings,
        local_started_at,
        sources=all_sources,
        cadence_records=cadence_records,
        coverage_history=coverage_history,
        failures=failures,
        profiles=profiles,
    )

    summary = build_summary(
        started_at=local_started_at,
        mode=mode,
        boards_checked=len(sources),
        meetings=all_meetings,
        new_meetings=new_meetings,
        updated_meetings=updated_meetings,
        events_updated=events_updated,
        agendas_downloaded=agendas_downloaded,
        agenda_notifications_sent=notifications_sent,
        coverage=coverage_totals,
        failures=failures,
    )
    write_run_log(conn, run_id, local_started_at, mode, summary)
    json_report, md_report = write_reports(args.report_dir, run_id, summary, all_meetings)
    append_progress_log(args.progress_log, summary)
    print(f"Run report: {md_report}")
    print(f"Run report JSON: {json_report}")
    print(f"Online calendar HTML: {web_calendar_paths[0]}")
    print(f"Calendar ICS feed: {web_calendar_paths[1]}")
    print(f"Boards checked: {summary['boards_checked']}")
    print(f"Meetings found: {summary['meetings_found']}")
    print(f"Missing agendas within 72 hours: {len(summary['missing_agendas_within_72_hours'])}")
    print(f"Agenda notifications sent: {summary['agenda_notifications_sent']}")
    print(f"Boards with meeting history: {coverage_totals['boards_with_meetings']} of {coverage_totals['boards']}")
    print(f"Failures requiring human review: {len(summary['failures_requiring_human_review'])}")
    return 0


def check_source(
    source: BoardSource,
    lookahead_days: int,
    respect_robots: bool,
    today: date,
    profile=None,
) -> tuple[list[Meeting], list[dict[str, str]], BoardSource]:
    endpoint_roles: dict[str, set[str]] = {}
    for role, raw_url in (
        ("schedule", source.meeting_schedule_url),
        ("agenda", source.agenda_minutes_url),
        ("executive", source.executive_committee_url),
    ):
        url = _expand_url_template(raw_url, today, lookahead_days)
        if url:
            endpoint_roles.setdefault(url, set()).add(role)
    # An audited profile has explicit authoritative endpoints. Probing its generic
    # homepage adds noise and can turn an irrelevant outage into a board failure.
    if not endpoint_roles or not profile or profile.status == "unaudited":
        main_url = _expand_url_template(source.main_website, today, lookahead_days)
        if main_url:
            endpoint_roles.setdefault(main_url, set()).add("main")
    urls = list(endpoint_roles)
    meetings: list[Meeting] = []
    failures: list[dict[str, str]] = []
    notes = source.notes
    confidence = source.confidence
    candidate_updates: dict[str, str] = {}
    successful_roles: set[str] = set()
    fetch_errors: list[tuple[str, Exception]] = []
    for url in urls:
        try:
            page = fetch_url(url, respect_robots=respect_robots)
            successful_roles.update(endpoint_roles[url])
            is_pdf = "pdf" in page.content_type.lower() or page.url.lower().split("?", 1)[0].endswith(".pdf")
            if is_pdf and not _profile_parses_pdf(profile):
                continue
            if "main" not in endpoint_roles[url] or len(endpoint_roles) == 1:
                page_text = extract_text_from_content(page.body, page.content_type, page.url) if is_pdf else page.text
                extracted = extract_meetings(
                    source,
                    page_text,
                    page.url,
                    today,
                    lookahead_days,
                    extraction_strategy=profile.extraction_strategy if profile else "generic",
                )
                for meeting in extracted:
                    detail_enriched, detail_failure = enrich_meeting_from_detail_page(meeting, page.url, respect_robots)
                    if detail_failure:
                        failures.append({
                            "board_name": source.board_name,
                            "url": meeting.source_page_url,
                            "error": detail_failure,
                            "severity": "warning",
                            "category": "detail_enrichment",
                            "source_role": "detail",
                        })
                    enriched, enrichment_failure = enrich_meeting_from_agenda(detail_enriched, respect_robots)
                    meetings.append(enriched)
                    if enrichment_failure:
                        failures.append({
                            "board_name": source.board_name,
                            "url": detail_enriched.agenda_url,
                            "error": enrichment_failure,
                            "severity": "warning",
                            "category": "agenda_enrichment",
                            "source_role": "agenda",
                        })
            if not profile or profile.status == "unaudited":
                candidates = find_candidate_pages(page.text, page.url)
                if candidates["meeting"]:
                    candidate_updates["meeting_schedule_url"] = candidates["meeting"][0]
                if candidates["agenda"]:
                    candidate_updates["agenda_minutes_url"] = candidates["agenda"][0]
                if candidates["executive"]:
                    candidate_updates["executive_committee_url"] = candidates["executive"][0]
        except Exception as exc:
            fetch_errors.append((url, exc))
    has_authoritative_success = bool(successful_roles & {"schedule", "agenda", "executive"})
    has_verified_fallback = bool(confirmed_profile_meetings(source, profile, today, lookahead_days))
    fetch_severity = "warning" if has_authoritative_success or has_verified_fallback else "error"
    for url, exc in fetch_errors:
        failures.append(
            {
                "board_name": source.board_name,
                "url": url,
                "error": str(exc),
                "severity": fetch_severity,
                "category": "endpoint_fetch",
                "source_role": ",".join(sorted(endpoint_roles[url])),
            }
        )
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
    if not meeting.agenda_url or (meeting.location and meeting.virtual_url and meeting.start_time):
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
    if details.start_time and not meeting.start_time:
        updates["start_time"] = details.start_time
        notes.append("time")
    if not updates:
        return meeting, ""
    confidence_note = f"{meeting.confidence_notes} Agenda parsed for {' and '.join(notes)}.".strip()
    return replace(meeting, **updates, confidence_notes=confidence_note), ""


def enrich_meeting_from_detail_page(meeting: Meeting, originating_url: str, respect_robots: bool) -> tuple[Meeting, str]:
    if not meeting.source_page_url or meeting.source_page_url == originating_url:
        return meeting, ""
    if meeting.agenda_url and meeting.location and meeting.virtual_url and meeting.start_time:
        return meeting, ""
    try:
        page = fetch_url(meeting.source_page_url, timeout=15, retries=1, respect_robots=respect_robots)
    except Exception as exc:
        return meeting, f"Detail page enrichment failed: {exc}"
    if "pdf" in page.content_type.lower():
        return meeting, ""
    detail_text = extract_text_from_content(page.body, page.content_type, page.url)
    agenda = best_agenda_for_date(extract_agenda_links(page.text, page.url), meeting.meeting_date)
    details = extract_agenda_details(page.body, page.content_type, page.url)
    updates = {}
    notes: list[str] = []
    if agenda and not meeting.agenda_url:
        updates["agenda_url"] = agenda.url
        updates["agenda_label"] = agenda.label
        notes.append("agenda")
    if details.location and not meeting.location:
        updates["location"] = details.location
        notes.append("location")
    if details.virtual_url and not meeting.virtual_url:
        updates["virtual_url"] = details.virtual_url
        notes.append("virtual link")
    if not meeting.start_time:
        detail_time = parse_time(detail_text)
        if detail_time:
            updates["start_time"] = detail_time
            notes.append("time")
    if not updates:
        return meeting, ""
    confidence_note = f"{meeting.confidence_notes} Detail page parsed for {' and '.join(notes)}.".strip()
    return replace(meeting, **updates, confidence_notes=confidence_note), ""


def should_check_agenda(meeting: Meeting, today: date) -> bool:
    if not meeting.agenda_url:
        return False
    if meeting.meeting_date >= today:
        return (meeting.meeting_date - today).days <= 10
    return (today - meeting.meeting_date).days <= 14


def confirmed_profile_meetings(source: BoardSource, profile, today: date, lookahead_days: int) -> list[Meeting]:
    if not profile or not profile.confirmed_meetings:
        return []
    max_date = today + timedelta(days=lookahead_days)
    meetings: list[Meeting] = []
    for item in profile.confirmed_meetings:
        meeting_date = date.fromisoformat(item["meeting_date"])
        if meeting_date < today - timedelta(days=14) or meeting_date > max_date:
            continue
        meetings.append(
            Meeting(
                board_id=source.board_id,
                board_name=source.board_name,
                meeting_type=item["meeting_type"],
                meeting_date=meeting_date,
                start_time=time.fromisoformat(item["start_time"]) if item.get("start_time") else None,
                timezone="America/Los_Angeles",
                location=item.get("location", ""),
                virtual_url=item.get("virtual_url", ""),
                source_page_url=item.get("source_url", source.meeting_schedule_url),
                agenda_url=item.get("agenda_url", ""),
                agenda_label=item.get("agenda_label", ""),
                confidence_notes=f"Confirmed official schedule fallback. {item.get('notes', '')}".strip(),
            )
        )
    return meetings


def _remove_conflicting_agenda(meeting: Meeting) -> Meeting:
    if not meeting.agenda_url:
        return meeting
    agenda_text = f"{meeting.agenda_label} {meeting.agenda_url}"
    if not agenda_link_date_conflicts(agenda_text, meeting.meeting_date):
        return meeting
    note = "Rejected agenda because its filename date conflicts with the meeting date."
    return replace(
        meeting,
        agenda_url="",
        agenda_label="",
        confidence_notes=_merge_notes(meeting.confidence_notes, note),
    )


def _profile_parses_pdf(profile) -> bool:
    return bool(profile and profile.extraction_strategy in {"solano_board_calendar", "mother_lode_schedule"})


def _expand_url_template(url: str, today: date, lookahead_days: int) -> str:
    if not url:
        return ""
    return (
        url.replace("{today}", today.isoformat())
        .replace("{lookahead_date}", (today + timedelta(days=lookahead_days)).isoformat())
        .replace("{year}", str(today.year))
    )


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
    by_id: dict[str, Meeting] = {}
    for meeting in meetings:
        existing = by_id.get(meeting.stable_id)
        by_id[meeting.stable_id] = _merge_meeting(existing, meeting) if existing else meeting
    return sorted(by_id.values(), key=lambda m: (m.meeting_date, m.board_name, m.meeting_type))


def _merge_meeting(existing: Meeting, incoming: Meeting) -> Meeting:
    return replace(
        incoming,
        start_time=incoming.start_time or existing.start_time,
        location=incoming.location or existing.location,
        virtual_url=incoming.virtual_url or existing.virtual_url,
        source_page_url=existing.source_page_url or incoming.source_page_url,
        agenda_url=incoming.agenda_url or existing.agenda_url,
        agenda_label=incoming.agenda_label or existing.agenda_label,
        confidence_notes=_merge_notes(existing.confidence_notes, incoming.confidence_notes),
    )


def _merge_notes(first: str, second: str) -> str:
    parts: list[str] = []
    for note in (first, second):
        note = note.strip()
        if note and note not in parts:
            parts.append(note)
    return " ".join(parts)


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
    parser.add_argument("--coverage-history", type=Path, default=DEFAULT_COVERAGE_HISTORY)
    parser.add_argument("--coverage-report", type=Path, default=DEFAULT_COVERAGE_REPORT)
    parser.add_argument("--notification-state", type=Path, default=DEFAULT_NOTIFICATION_STATE)
    parser.add_argument("--meeting-state", type=Path, default=DEFAULT_MEETING_STATE)
    notification_group = parser.add_mutually_exclusive_group()
    notification_group.add_argument("--notify-agendas", action="store_true", help="Email newly available or changed agendas.")
    notification_group.add_argument(
        "--bootstrap-agenda-notifications",
        action="store_true",
        help="Record current agendas without emailing them, preventing an initial notification flood.",
    )
    parser.add_argument("--respect-robots", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    return parser.parse_args(argv)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except GraphConfigError as exc:
        print(f"Live mode configuration error: {exc}")
        raise SystemExit(2)
