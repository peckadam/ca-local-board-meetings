from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROFILE_PATH = PROJECT_ROOT / "data" / "local_board_meetings" / "source_profiles.json"


@dataclass(frozen=True)
class SourceProfile:
    board_id: str
    status: str = "unaudited"
    cadence: str = ""
    extraction_strategy: str = "generic"
    agenda_rules: dict[str, Any] | None = None
    known_traps: list[str] | None = None
    verification_notes: str = ""
    confirmed_meetings: list[dict[str, str]] | None = None
    verified_meeting_dates: list[str] | None = None
    verified_agenda_dates: list[str] | None = None


MECHANISM_LABELS = {
    "tribe_events_api": "Official events API plus event detail pages",
    "ventura_google_calendar_ics": "Official public ICS feed plus packet archive",
    "contra_costa_legistar": "Official Legistar calendar and agenda rows",
    "la_city_novus": "Official NovusAgenda meeting portal",
    "san_joaquin_worknet": "Official agenda JSON API",
    "santa_barbara_hcms": "Official county agenda widget API",
    "mother_lode_schedule": "Official annual schedule PDF plus agenda archive",
    "solano_board_calendar": "Official annual schedule PDF plus board archive",
    "kings_jto_packets": "Official JTO packet list",
    "no_publish": "Official source tracked; connector still requires verification",
    "generic": "Official HTML or PDF page with date-matched agenda parsing",
}


def load_profiles(path: Path = DEFAULT_PROFILE_PATH) -> dict[str, SourceProfile]:
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {item["board_id"]: SourceProfile(**item) for item in raw.get("profiles", [])}


def mechanism_label(profile: SourceProfile | None) -> str:
    if not profile:
        return "Generic official-page discovery"
    label = MECHANISM_LABELS.get(
        profile.extraction_strategy,
        "Official board-specific page parser",
    )
    if profile.confirmed_meetings:
        label += " plus verified schedule fallback"
    return label
