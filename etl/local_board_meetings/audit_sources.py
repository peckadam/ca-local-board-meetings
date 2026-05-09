from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from datetime import date, datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup

from .extraction import extract_agenda_links, extract_meetings, find_candidate_pages
from .fetcher import fetch_url
from .registry import load_registry
from .runner import DATA_DIR, DEFAULT_REGISTRY, DEFAULT_SEED
from .site_profiles import load_profiles


DEFAULT_AUDIT_DIR = DATA_DIR / "audits"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    started_at = datetime.now(timezone.utc)
    sources = load_registry(args.registry, args.seed_manifest)
    profiles = load_profiles(args.source_profiles)
    if args.boards:
        selected = {item.lower() for item in args.boards}
        sources = [source for source in sources if source.board_id.lower() in selected or source.board_name.lower() in selected]
    if args.limit:
        sources = sources[: args.limit]
    results = []
    for source in sources:
        profile = profiles.get(source.board_id)
        urls = list(dict.fromkeys([u for u in [source.meeting_schedule_url, source.agenda_minutes_url, source.executive_committee_url] if u]))
        board_result = {
            "board_id": source.board_id,
            "board_name": source.board_name,
            "status": profile.status if profile else "unaudited",
            "registry": asdict(source),
            "pages": [],
            "red_flags": [],
        }
        for url in urls:
            try:
                page = fetch_url(url, respect_robots=args.respect_robots)
                if "pdf" in page.content_type.lower():
                    board_result["pages"].append({"url": url, "content_type": page.content_type, "note": "PDF source; manual schedule extraction required"})
                    continue
                strategy = profile.extraction_strategy if profile else "generic"
                meetings = extract_meetings(source, page.text, page.url, args.today, args.lookahead_days, extraction_strategy=strategy)
                agendas = extract_agenda_links(page.text, page.url)
                candidates = find_candidate_pages(page.text, page.url)
                page_result = {
                    "url": page.url,
                    "content_type": page.content_type,
                    "title": _title(page.text),
                    "headings": _headings(page.text),
                    "meetings": [_meeting_summary(meeting) for meeting in meetings],
                    "agenda_links": [_agenda_summary(agenda) for agenda in agendas[:25]],
                    "candidate_pages": {key: values[:10] for key, values in candidates.items()},
                }
                if len(meetings) > 6:
                    board_result["red_flags"].append(f"{url} produced {len(meetings)} meetings; verify that general calendars or archives are not being parsed.")
                if any("cancel" in item["url"].lower() for item in page_result["agenda_links"]):
                    board_result["red_flags"].append(f"{url} contains canceled agenda links.")
                if meetings and not any(item["url"] for item in page_result["agenda_links"]):
                    board_result["red_flags"].append(f"{url} produced meetings but no agenda links.")
                board_result["pages"].append(page_result)
            except Exception as exc:
                board_result["red_flags"].append(f"{url}: {exc}")
                board_result["pages"].append({"url": url, "error": str(exc)})
        results.append(board_result)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    stamp = started_at.strftime("%Y%m%dT%H%M%SZ")
    json_path = args.output_dir / f"{stamp}.json"
    md_path = args.output_dir / f"{stamp}.md"
    payload = {"started_at": started_at.isoformat(), "boards": results}
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    md_path.write_text(render_markdown(payload), encoding="utf-8")
    print(f"Audit JSON: {json_path}")
    print(f"Audit markdown: {md_path}")
    print(f"Boards audited: {len(results)}")
    return 0


def render_markdown(payload: dict) -> str:
    lines = ["# Local Board Source Audit", "", f"- Started: {payload['started_at']}", ""]
    for board in payload["boards"]:
        lines.extend([f"## {board['board_name']}", "", f"- Board ID: `{board['board_id']}`", f"- Status: {board['status']}"])
        if board["red_flags"]:
            lines.append("- Red flags:")
            lines.extend(f"  - {flag}" for flag in board["red_flags"])
        for page in board["pages"]:
            lines.extend(["", f"### {page.get('url', 'unknown URL')}"])
            if "error" in page:
                lines.append(f"- Error: {page['error']}")
                continue
            lines.append(f"- Title: {page.get('title', '')}")
            if page.get("headings"):
                lines.append(f"- Headings: {'; '.join(page['headings'][:12])}")
            if page.get("meetings"):
                lines.append("- Meetings:")
                for meeting in page["meetings"]:
                    agenda = meeting["agenda_url"] or "missing"
                    lines.append(f"  - {meeting['date']} {meeting['time'] or ''} {meeting['type']} | agenda: {agenda}")
            else:
                lines.append("- Meetings: none extracted")
            if page.get("agenda_links"):
                lines.append("- Agenda candidates:")
                for agenda in page["agenda_links"][:8]:
                    lines.append(f"  - {agenda['label']}: {agenda['url']}")
        lines.append("")
    return "\n".join(lines)


def _title(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    title = soup.find("title")
    return title.get_text(" ", strip=True) if title else ""


def _headings(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    return [node.get_text(" ", strip=True) for node in soup.find_all(["h1", "h2", "h3", "h4"]) if node.get_text(" ", strip=True)][:20]


def _meeting_summary(meeting) -> dict[str, str]:
    return {
        "date": meeting.meeting_date.isoformat(),
        "time": meeting.start_time.isoformat() if meeting.start_time else "",
        "type": meeting.meeting_type,
        "source_page_url": meeting.source_page_url,
        "agenda_url": meeting.agenda_url,
    }


def _agenda_summary(agenda) -> dict[str, str]:
    return {"label": agenda.label, "url": agenda.url, "source_page_url": agenda.source_page_url}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Audit local board meeting sources and extraction quality.")
    parser.add_argument("--boards", nargs="*", default=[])
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--lookahead-days", type=int, default=180)
    parser.add_argument("--today", type=date.fromisoformat, default=date.today())
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY)
    parser.add_argument("--seed-manifest", type=Path, default=DEFAULT_SEED)
    parser.add_argument("--source-profiles", type=Path, default=DATA_DIR / "source_profiles.json")
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_AUDIT_DIR)
    parser.add_argument("--respect-robots", action=argparse.BooleanOptionalAction, default=True)
    return parser.parse_args(argv)


if __name__ == "__main__":
    raise SystemExit(main())
