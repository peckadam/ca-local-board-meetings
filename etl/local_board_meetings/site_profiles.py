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


def load_profiles(path: Path = DEFAULT_PROFILE_PATH) -> dict[str, SourceProfile]:
    if not path.exists():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    return {item["board_id"]: SourceProfile(**item) for item in raw.get("profiles", [])}
