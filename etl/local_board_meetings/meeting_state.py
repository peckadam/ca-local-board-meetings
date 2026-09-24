from __future__ import annotations

import json
from dataclasses import asdict
from datetime import date, datetime, time
from pathlib import Path

from .models import Meeting


def merge_active_meetings(
    path: Path,
    observed: list[Meeting],
    checked_at: datetime,
    today: date,
) -> list[Meeting]:
    """Persist confirmed future meetings across stateless daily runs."""
    state = _load_state(path)
    records = state.setdefault("meetings", {})
    for meeting in observed:
        records[meeting.stable_id] = {
            "meeting": _serialize(meeting),
            "last_seen_at": checked_at.isoformat(),
        }

    active: dict[str, dict] = {}
    for stable_id, record in records.items():
        try:
            meeting = _deserialize(record["meeting"])
        except (KeyError, TypeError, ValueError):
            continue
        if meeting.meeting_date >= today:
            active[stable_id] = record

    state["meetings"] = dict(sorted(active.items()))
    state["updated_at"] = checked_at.isoformat()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return sorted(
        (_deserialize(record["meeting"]) for record in active.values()),
        key=lambda meeting: (meeting.meeting_date, meeting.board_name, meeting.meeting_type),
    )


def _load_state(path: Path) -> dict:
    if not path.exists():
        return {"version": 1, "updated_at": "", "meetings": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def _serialize(meeting: Meeting) -> dict:
    payload = asdict(meeting)
    payload["meeting_date"] = meeting.meeting_date.isoformat()
    payload["start_time"] = meeting.start_time.isoformat() if meeting.start_time else ""
    return payload


def _deserialize(payload: dict) -> Meeting:
    values = dict(payload)
    values["meeting_date"] = date.fromisoformat(values["meeting_date"])
    values["start_time"] = time.fromisoformat(values["start_time"]) if values.get("start_time") else None
    return Meeting(**values)
