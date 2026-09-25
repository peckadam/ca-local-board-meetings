from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

from .models import BoardSource, Meeting
from .source_health import failure_health_by_board, failure_roles_by_board


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CADENCE_PATH = PROJECT_ROOT / "data" / "local_board_meetings" / "cadence_registry.json"


@dataclass(frozen=True)
class CadenceRecord:
    board_id: str
    category: str
    confidence: str
    summary: str


@dataclass(frozen=True)
class CadenceCoverageRow:
    board_id: str
    board_name: str
    local_area: str
    category: str
    confidence: str
    summary: str
    next_meeting: str
    latest_known_meeting: str
    coverage_signal: str
    coverage_level: str
    source_url: str


def load_cadence_registry(path: Path = DEFAULT_CADENCE_PATH) -> dict[str, CadenceRecord]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {item["board_id"]: CadenceRecord(**item) for item in raw.get("boards", [])}


def cadence_counts(records: dict[str, CadenceRecord]) -> dict[str, int]:
    counts = Counter(record.category for record in records.values())
    return dict(counts)


def build_cadence_coverage_rows(
    sources: list[BoardSource],
    records: dict[str, CadenceRecord],
    meetings: list[Meeting],
    coverage_history: dict,
    failures: list[dict[str, str]],
) -> list[CadenceCoverageRow]:
    meetings_by_board: dict[str, list[Meeting]] = {}
    for meeting in meetings:
        meetings_by_board.setdefault(meeting.board_id, []).append(meeting)
    source_health = failure_health_by_board(failures)
    source_roles = failure_roles_by_board(failures)
    history_by_board = coverage_history.get("boards", {})
    rows: list[CadenceCoverageRow] = []

    for source in sorted(sources, key=lambda item: item.board_name):
        record = records.get(
            source.board_id,
            CadenceRecord(source.board_id, "Not established", "unknown", "Cadence record is missing."),
        )
        future = sorted(meetings_by_board.get(source.board_id, []), key=lambda item: item.meeting_date)
        dates = history_by_board.get(source.board_id, {}).get("meeting_dates", [])
        next_meeting = future[0].meeting_date.isoformat() if future else ""
        latest_known = dates[-1] if dates else ""

        signals: list[str] = []
        health = source_health.get(source.board_name)
        if health:
            role_text = "/".join(sorted(source_roles.get(source.board_name, set()))) or "source"
            signals.append(
                f"Source access blocked ({role_text})"
                if health == "blocked"
                else f"Source partly degraded ({role_text})"
            )
        if not dates:
            signals.append("No meeting date ever found")
        if future:
            signals.append("Future meeting listed")
        elif record.category == "Not established":
            signals.append("No future date; cadence unknown")
        else:
            signals.append("No future meeting despite known cadence")
        signal = "; ".join(signals)
        level = "review" if health or not dates or not future else "ok"

        rows.append(
            CadenceCoverageRow(
                board_id=source.board_id,
                board_name=source.board_name,
                local_area=source.local_area,
                category=record.category,
                confidence=record.confidence,
                summary=record.summary,
                next_meeting=next_meeting,
                latest_known_meeting=latest_known,
                coverage_signal=signal,
                coverage_level=level,
                source_url=source.meeting_schedule_url or source.main_website,
            )
        )
    return rows
