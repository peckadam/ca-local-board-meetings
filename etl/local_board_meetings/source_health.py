from __future__ import annotations

from collections import defaultdict
from typing import Iterable


def is_blocking_failure(failure: dict) -> bool:
    return failure.get("severity", "error") == "error"


def failure_health_by_board(failures: Iterable[dict]) -> dict[str, str]:
    health: dict[str, str] = {}
    for failure in failures:
        board_name = failure.get("board_name", "")
        if not board_name:
            continue
        status = "blocked" if is_blocking_failure(failure) else "degraded"
        if health.get(board_name) != "blocked":
            health[board_name] = status
    return health


def failure_roles_by_board(failures: Iterable[dict]) -> dict[str, set[str]]:
    roles: dict[str, set[str]] = defaultdict(set)
    for failure in failures:
        board_name = failure.get("board_name", "")
        if not board_name:
            continue
        for role in str(failure.get("source_role", "")).split(","):
            if role:
                roles[board_name].add(role)
    return dict(roles)
