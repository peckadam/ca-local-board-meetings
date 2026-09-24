from __future__ import annotations

import hashlib
import html
import json
import os
import re
import smtplib
import ssl
from dataclasses import dataclass
from datetime import date, datetime, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Callable

from .agenda_content import extract_text_from_content
from .fetcher import fetch_url
from .models import Meeting


@dataclass(frozen=True)
class SmtpConfig:
    host: str
    port: int
    username: str
    password: str
    sender: str
    recipient: str
    use_ssl: bool = False

    @classmethod
    def from_env(cls) -> "SmtpConfig":
        host = os.environ.get("AGENDA_SMTP_HOST", "").strip()
        username = os.environ.get("AGENDA_SMTP_USERNAME", "").strip()
        password = os.environ.get("AGENDA_SMTP_PASSWORD", "")
        sender = os.environ.get("AGENDA_SMTP_FROM", username).strip()
        recipient = os.environ.get("AGENDA_NOTIFICATION_TO", "apeck@calworkforce.org").strip()
        missing = [
            name
            for name, value in {
                "AGENDA_SMTP_HOST": host,
                "AGENDA_SMTP_USERNAME": username,
                "AGENDA_SMTP_PASSWORD": password,
                "AGENDA_SMTP_FROM": sender,
                "AGENDA_NOTIFICATION_TO": recipient,
            }.items()
            if not value
        ]
        if missing:
            raise ValueError(f"Missing agenda email configuration: {', '.join(missing)}")
        use_ssl = os.environ.get("AGENDA_SMTP_USE_SSL", "").lower() in {"1", "true", "yes"}
        return cls(host, int(os.environ.get("AGENDA_SMTP_PORT", "465" if use_ssl else "587")), username, password, sender, recipient, use_ssl)


def process_agenda_notifications(
    meetings: list[Meeting],
    state_path: Path,
    today: date,
    respect_robots: bool,
    send: Callable[[EmailMessage], None] | None,
    bootstrap: bool = False,
) -> tuple[int, list[dict[str, str]]]:
    state = _load_state(state_path)
    records = state.setdefault("notifications", {})
    sent = 0
    failures: list[dict[str, str]] = []
    for meeting in sorted(meetings, key=lambda item: (item.meeting_date, item.board_name, item.meeting_type)):
        if not meeting.agenda_url or meeting.meeting_date < today:
            continue
        try:
            page = fetch_url(
                meeting.agenda_url,
                timeout=20,
                retries=1,
                respect_robots=respect_robots,
                max_bytes=100 * 1024 * 1024,
            )
            digest = hashlib.sha256(page.body).hexdigest()
            previous = records.get(meeting.stable_id, {})
            if previous.get("sha256") == digest:
                continue
            agenda_text = extract_text_from_content(page.body, page.content_type, page.url)
            summary = summarize_agenda(agenda_text)
            if not bootstrap:
                if send is None:
                    raise ValueError("Agenda email delivery was requested without an email sender")
                send(build_agenda_email(meeting, summary, bool(previous)))
                sent += 1
            records[meeting.stable_id] = {
                "board_name": meeting.board_name,
                "meeting_date": meeting.meeting_date.isoformat(),
                "meeting_type": meeting.meeting_type,
                "agenda_url": meeting.agenda_url,
                "sha256": digest,
                "recorded_at": datetime.now(timezone.utc).isoformat(),
                "delivery": "bootstrapped" if bootstrap else "sent",
            }
            _save_state(state_path, state)
        except Exception as exc:
            failures.append({"board_name": meeting.board_name, "url": meeting.agenda_url, "error": f"Agenda notification failed: {exc}"})
    return sent, failures


def smtp_sender(config: SmtpConfig) -> Callable[[EmailMessage], None]:
    def send(message: EmailMessage) -> None:
        message["From"] = config.sender
        message["To"] = config.recipient
        if config.use_ssl:
            with smtplib.SMTP_SSL(config.host, config.port, timeout=30, context=ssl.create_default_context()) as client:
                client.login(config.username, config.password)
                client.send_message(message)
        else:
            with smtplib.SMTP(config.host, config.port, timeout=30) as client:
                client.ehlo()
                client.starttls(context=ssl.create_default_context())
                client.ehlo()
                client.login(config.username, config.password)
                client.send_message(message)

    return send


def summarize_agenda(text: str, max_items: int = 8) -> list[str]:
    lines = [re.sub(r"\s+", " ", line).strip(" \t-•") for line in text.splitlines()]
    lines = [line for line in lines if 5 <= len(line) <= 220]
    noise = re.compile(r"^(page \d+|agenda$|meeting agenda$|public comment$|call to order$)", re.I)
    item_pattern = re.compile(r"^(?:\d+[\.)]|[IVX]+[\.)]|[A-Z][\.)]|item\s+\d+|action\s+item|information\s+item)", re.I)
    selected: list[str] = []
    for line in lines:
        if noise.search(line) or "http" in line.lower():
            continue
        if item_pattern.search(line) or (line.isupper() and 12 <= len(line) <= 120):
            normalized = line.title() if line.isupper() else line
            if normalized not in selected:
                selected.append(normalized)
        if len(selected) >= max_items:
            break
    if not selected:
        selected = [line for line in lines if not noise.search(line)][:max_items]
    return selected or ["The agenda was posted, but its text could not be summarized automatically."]


def build_agenda_email(meeting: Meeting, summary: list[str], updated: bool = False) -> EmailMessage:
    status = "updated" if updated else "available"
    subject = f"Agenda {status}: {meeting.board_name} - {meeting.meeting_type} - {meeting.meeting_date.isoformat()}"
    details = [
        f"Board: {meeting.board_name}",
        f"Meeting: {meeting.meeting_type}",
        f"Date: {meeting.meeting_date.isoformat()}",
    ]
    if meeting.start_time:
        details.append(f"Time: {meeting.start_time.strftime('%-I:%M %p')} Pacific")
    if meeting.location:
        details.append(f"Location: {meeting.location}")
    if meeting.virtual_url:
        details.append(f"Virtual meeting: {meeting.virtual_url}")
    details.extend([f"Agenda: {meeting.agenda_url}", f"Source: {meeting.source_page_url}"])
    plain = "\n".join(details) + "\n\nAgenda summary:\n" + "\n".join(f"- {item}" for item in summary)
    body = "".join(f"<p><strong>{html.escape(line.split(':', 1)[0])}:</strong>{html.escape(line.split(':', 1)[1])}</p>" for line in details)
    bullets = "".join(f"<li>{html.escape(item)}</li>" for item in summary)
    body += f'<p><a href="{html.escape(meeting.agenda_url, quote=True)}">Open the agenda</a></p><h2>Agenda summary</h2><ul>{bullets}</ul>'
    message = EmailMessage()
    message["Subject"] = subject
    message.set_content(plain)
    message.add_alternative(f"<html><body>{body}</body></html>", subtype="html")
    return message


def _load_state(path: Path) -> dict:
    if not path.exists():
        return {"version": 1, "notifications": {}}
    return json.loads(path.read_text(encoding="utf-8"))


def _save_state(path: Path, state: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n", encoding="utf-8")
