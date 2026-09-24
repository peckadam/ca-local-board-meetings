from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime
from pathlib import Path

from .models import BoardSource, Meeting
from .site_profiles import SourceProfile


PROJECT_ROOT = Path(__file__).resolve().parents[2]
LEGACY_NOTICE_AUDIT = PROJECT_ROOT / "data" / "local_board_meetings" / "audits" / "meeting_notice_coverage_20260611.md"


def update_coverage_history(
    path: Path,
    conn: sqlite3.Connection,
    sources: list[BoardSource],
    meetings: list[Meeting],
    checked_at: datetime,
    profiles: dict[str, SourceProfile] | None = None,
) -> dict:
    payload = _load_history(path)
    boards = payload.setdefault("boards", {})
    for source in sources:
        boards.setdefault(
            source.board_id,
            {
                "board_name": source.board_name,
                "local_area": source.local_area,
                "meeting_dates": [],
                "agenda_dates": [],
                "last_meeting_seen_at": "",
            },
        )
    _merge_legacy_notice_audit(boards, sources)
    _merge_profile_evidence(boards, profiles or {})
    rows = conn.execute(
        "SELECT board_id, board_name, meeting_date, agenda_url FROM meetings ORDER BY meeting_date"
    ).fetchall()
    current_ids = {meeting.stable_id for meeting in meetings}
    for row in rows:
        record = boards.setdefault(
            row["board_id"],
            {
                "board_name": row["board_name"],
                "local_area": "",
                "meeting_dates": [],
                "agenda_dates": [],
                "last_meeting_seen_at": "",
            },
        )
        record["meeting_dates"] = sorted(set(record.get("meeting_dates", [])) | {row["meeting_date"]})
        if row["agenda_url"]:
            record["agenda_dates"] = sorted(set(record.get("agenda_dates", [])) | {row["meeting_date"]})
        meeting_id_prefix = f"{row['board_id']}:"
        if any(item.startswith(meeting_id_prefix) for item in current_ids):
            record["last_meeting_seen_at"] = checked_at.isoformat()
    payload["updated_at"] = checked_at.isoformat()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def write_coverage_report(
    path: Path,
    history: dict,
    sources: list[BoardSource],
    profiles: dict[str, SourceProfile],
    current_meetings: list[Meeting],
    failures: list[dict[str, str]],
    checked_at: datetime,
) -> dict[str, int]:
    current_by_board: dict[str, list[Meeting]] = {}
    for meeting in current_meetings:
        current_by_board.setdefault(meeting.board_id, []).append(meeting)
    failed_boards = {failure.get("board_name", "") for failure in failures}
    rows = []
    for source in sorted(sources, key=lambda item: item.board_name):
        record = history.get("boards", {}).get(source.board_id, {})
        dates = record.get("meeting_dates", [])
        agenda_dates = record.get("agenda_dates", [])
        profile = profiles.get(source.board_id)
        cadence = _cadence_status(profile)
        current = current_by_board.get(source.board_id, [])
        rows.append(
            {
                "board": source.board_name,
                "area": source.local_area,
                "meeting_history": "yes" if dates else "NO",
                "latest_date": dates[-1] if dates else "",
                "agenda_history": "yes" if agenda_dates else "NO",
                "current_meetings": len(current),
                "current_agendas": sum(bool(meeting.agenda_url) for meeting in current),
                "cadence": cadence,
                "fetch": "review" if source.board_name in failed_boards else "ok",
            }
        )
    totals = {
        "boards": len(rows),
        "boards_with_meetings": sum(row["meeting_history"] == "yes" for row in rows),
        "boards_with_agendas": sum(row["agenda_history"] == "yes" for row in rows),
        "cadence_understood": sum(row["cadence"] == "documented" for row in rows),
        "cadence_partial": sum(row["cadence"] == "partial" for row in rows),
        "fetch_review": sum(row["fetch"] == "review" for row in rows),
    }
    missing_meetings = [row["board"] for row in rows if row["meeting_history"] == "NO"]
    missing_agendas = [row["board"] for row in rows if row["agenda_history"] == "NO"]
    partial_cadence = [row["board"] for row in rows if row["cadence"] != "documented"]
    fetch_review = [row["board"] for row in rows if row["fetch"] == "review"]
    lines = [
        "# Local Board Coverage Matrix",
        "",
        f"- Updated: {checked_at.isoformat()}",
        f"- Boards with at least one confirmed meeting date: {totals['boards_with_meetings']} of {totals['boards']}",
        f"- Boards with at least one agenda matched to a meeting: {totals['boards_with_agendas']} of {totals['boards']}",
        f"- Cadence documented with audited source context: {totals['cadence_understood']} of {totals['boards']}",
        f"- Cadence still partial: {totals['cadence_partial']} of {totals['boards']}",
        f"- Boards with a fetch failure in this run: {totals['fetch_review']}",
        "",
        "`NO` and `review` cells are the active manual-research queue. Cadence is never used to publish an unconfirmed meeting.",
        "",
        "## Active Research Queue",
        "",
        f"- No confirmed meeting notice/date: {_join_names(missing_meetings)}",
        f"- No agenda ever matched to a meeting: {_join_names(missing_agendas)}",
        f"- Cadence/source context still partial: {_join_names(partial_cadence)}",
        f"- Fetch failure this run: {_join_names(fetch_review)}",
        "",
        "| Board / local area | Meeting date ever found | Latest date | Agenda ever matched | Current meetings / agendas | Cadence | Fetch |",
        "|---|---:|---|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['board']} / {row['area']} | {row['meeting_history']} | {row['latest_date']} | "
            f"{row['agenda_history']} | {row['current_meetings']} / {row['current_agendas']} | "
            f"{row['cadence']} | {row['fetch']} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return totals


def _join_names(names: list[str]) -> str:
    return ", ".join(names) if names else "none"


def _load_history(path: Path) -> dict:
    if not path.exists():
        return {"version": 1, "updated_at": "", "boards": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def _merge_legacy_notice_audit(boards: dict, sources: list[BoardSource]) -> None:
    if not LEGACY_NOTICE_AUDIT.exists():
        return
    lines = LEGACY_NOTICE_AUDIT.read_text(encoding="utf-8").splitlines()
    for source in sources:
        matching = next((line for line in lines if line.startswith("|") and f"| {source.board_name} |" in line), "")
        if not matching or "NO DATES FOUND" in matching:
            continue
        dates = re.findall(r"20\d{2}-\d{2}-\d{2}", matching)
        record = boards[source.board_id]
        record["meeting_dates"] = sorted(set(record.get("meeting_dates", [])) | set(dates))


def _merge_profile_evidence(boards: dict, profiles: dict[str, SourceProfile]) -> None:
    """Merge dates manually verified against official sources into the audit ledger.

    These dates document source coverage only. They never create calendar events; live
    events must still come from a parsed source or an explicit confirmed_meetings row.
    """
    for board_id, profile in profiles.items():
        record = boards.get(board_id)
        if not record:
            continue
        meeting_dates = set(record.get("meeting_dates", []))
        agenda_dates = set(record.get("agenda_dates", []))
        meeting_dates.update(profile.verified_meeting_dates or [])
        agenda_dates.update(profile.verified_agenda_dates or [])
        meeting_dates.update(agenda_dates)
        record["meeting_dates"] = sorted(meeting_dates)
        record["agenda_dates"] = sorted(agenda_dates)


def _cadence_status(profile: SourceProfile | None) -> str:
    if not profile or not profile.cadence.strip():
        return "MISSING"
    return "documented" if profile.status == "audited" else "partial"
