from __future__ import annotations

import html
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .cadence import CadenceCoverageRow, CadenceRecord, build_cadence_coverage_rows, cadence_counts
from .models import BoardSource, Meeting
from .site_profiles import SourceProfile, mechanism_label

CALENDAR_TITLE = "California Local Workforce Board Meetings"
CALENDAR_FEED_NAME = "Local Board Meetings"
PUBLIC_CALENDAR_URL = "https://peckadam.github.io/ca-local-board-meetings/calendar.ics"
WEBCAL_URL = "webcal://peckadam.github.io/ca-local-board-meetings/calendar.ics"


def write_web_calendar(
    output_dir: Path,
    meetings: list[Meeting],
    generated_at: datetime,
    *,
    sources: list[BoardSource] | None = None,
    cadence_records: dict[str, CadenceRecord] | None = None,
    coverage_history: dict | None = None,
    failures: list[dict[str, str]] | None = None,
    profiles: dict[str, SourceProfile] | None = None,
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    future = sorted(
        [meeting for meeting in meetings if meeting.meeting_date >= generated_at.date()],
        key=lambda m: (m.meeting_date, m.start_time or datetime.min.time(), m.board_name, m.meeting_type),
    )
    ics_path = output_dir / "calendar.ics"
    html_path = output_dir / "index.html"
    ics_path.write_text(render_ics(future, generated_at), encoding="utf-8")
    html_path.write_text(
        render_html(
            future,
            generated_at,
            sources=sources or [],
            cadence_records=cadence_records or {},
            coverage_history=coverage_history or {},
            failures=failures or [],
            profiles=profiles or {},
        ),
        encoding="utf-8",
    )
    return html_path, ics_path


def render_ics(meetings: list[Meeting], generated_at: datetime) -> str:
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//CWA//Local Board Meeting Monitor//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"NAME:{_ics_text(CALENDAR_FEED_NAME)}",
        f"X-WR-CALNAME:{_ics_text(CALENDAR_FEED_NAME)}",
        "X-WR-CALDESC:California local workforce board meeting feed",
        "X-WR-TIMEZONE:America/Los_Angeles",
        "REFRESH-INTERVAL;VALUE=DURATION:PT12H",
        "X-PUBLISHED-TTL:PT12H",
    ]
    stamp = _utc_stamp(generated_at)
    for meeting in meetings:
        if meeting.start_time:
            start = datetime.combine(meeting.meeting_date, meeting.start_time)
            end = start + timedelta(hours=1)
            timing = [
                f"DTSTART;TZID=America/Los_Angeles:{start.strftime('%Y%m%dT%H%M%S')}",
                f"DTEND;TZID=America/Los_Angeles:{end.strftime('%Y%m%dT%H%M%S')}",
            ]
        else:
            timing = [
                f"DTSTART;VALUE=DATE:{meeting.meeting_date.strftime('%Y%m%d')}",
                f"DTEND;VALUE=DATE:{(meeting.meeting_date + timedelta(days=1)).strftime('%Y%m%d')}",
            ]
        description = "\n".join(
            [
                f"Source page: {meeting.source_page_url}",
                f"Agenda URL: {meeting.agenda_url or 'Not found yet'}",
                f"Location: {meeting.location or 'Not published'}",
                f"Virtual link: {meeting.virtual_url or 'Not published'}",
                f"Confidence notes: {meeting.confidence_notes}",
            ]
        )
        lines.extend(
            [
                "BEGIN:VEVENT",
                f"UID:{_ics_text(meeting.stable_id)}@cwa-local-board-meetings",
                f"DTSTAMP:{stamp}",
                *timing,
                f"SUMMARY:{_ics_text(f'{meeting.board_name} - {meeting.meeting_type}')}",
                f"LOCATION:{_ics_text(meeting.location or meeting.virtual_url)}",
                f"DESCRIPTION:{_ics_text(description)}",
                f"URL:{meeting.agenda_url or meeting.source_page_url}",
                "END:VEVENT",
            ]
        )
    lines.append("END:VCALENDAR")
    return "\r\n".join(_fold_ics(line) for line in lines) + "\r\n"


def render_html(
    meetings: list[Meeting],
    generated_at: datetime,
    *,
    sources: list[BoardSource] | None = None,
    cadence_records: dict[str, CadenceRecord] | None = None,
    coverage_history: dict | None = None,
    failures: list[dict[str, str]] | None = None,
    profiles: dict[str, SourceProfile] | None = None,
) -> str:
    rows = "\n".join(_meeting_row(meeting) for meeting in meetings)
    if not rows:
        rows = '<tr><td colspan="5">No future meetings discovered yet.</td></tr>'
    cadence_records = cadence_records or {}
    cadence_rows = build_cadence_coverage_rows(
        sources or [],
        cadence_records,
        meetings,
        coverage_history or {},
        failures or [],
    )
    profiles = profiles or {}
    cadence_table_rows = "\n".join(_cadence_row(row, profiles.get(row.board_id)) for row in cadence_rows)
    if not cadence_table_rows:
        cadence_table_rows = '<tr><td colspan="8">Cadence coverage data is not available.</td></tr>'
    counts = cadence_counts(cadence_records)
    review_count = sum(row.coverage_level == "review" for row in cadence_rows)
    metrics = "\n".join(
        _cadence_metric(label, counts.get(label, 0))
        for label in ("Monthly", "Quarterly", "Every other month", "Other published cadence", "Not established")
    )
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(CALENDAR_TITLE)}</title>
  <style>
    :root {{
      color-scheme: light;
      --ink: #1c2430;
      --muted: #5d6a7a;
      --line: #d8dee7;
      --band: #f5f7fa;
      --accent: #0b6f85;
      --warn: #9a5b00;
    }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color: var(--ink);
      background: white;
    }}
    header {{
      border-bottom: 1px solid var(--line);
      padding: 24px clamp(16px, 4vw, 48px);
    }}
    h1 {{
      margin: 0 0 8px;
      font-size: clamp(24px, 3vw, 34px);
      font-weight: 700;
      letter-spacing: 0;
    }}
    .meta {{
      color: var(--muted);
      font-size: 14px;
    }}
    main {{
      padding: 24px clamp(16px, 4vw, 48px) 48px;
    }}
    .actions {{
      display: flex;
      gap: 12px;
      flex-wrap: wrap;
      margin-bottom: 20px;
    }}
    .actions a {{
      color: white;
      background: var(--accent);
      text-decoration: none;
      padding: 10px 14px;
      border-radius: 6px;
      font-weight: 600;
      font-size: 14px;
    }}
    .tabs {{
      display: flex;
      gap: 24px;
      border-bottom: 1px solid var(--line);
      margin-bottom: 20px;
    }}
    .tab {{
      appearance: none;
      border: 0;
      border-bottom: 3px solid transparent;
      background: transparent;
      color: var(--muted);
      cursor: pointer;
      font: inherit;
      font-weight: 700;
      padding: 10px 2px 9px;
    }}
    .tab[aria-selected="true"] {{
      border-bottom-color: var(--accent);
      color: var(--ink);
    }}
    [role="tabpanel"][hidden] {{
      display: none;
    }}
    .section-heading {{
      margin: 0 0 6px;
      font-size: 20px;
      letter-spacing: 0;
    }}
    .section-note {{
      color: var(--muted);
      line-height: 1.5;
      margin: 0 0 18px;
      max-width: 980px;
    }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(5, minmax(120px, 1fr));
      border: 1px solid var(--line);
      margin-bottom: 18px;
    }}
    .metric {{
      border-right: 1px solid var(--line);
      padding: 14px;
    }}
    .metric:last-child {{
      border-right: 0;
    }}
    .metric strong {{
      display: block;
      font-size: 24px;
      margin-bottom: 3px;
    }}
    .metric span {{
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
    }}
    .review-summary {{
      border-left: 4px solid var(--warn);
      margin: 0 0 18px;
      padding: 8px 12px;
    }}
    .status {{
      font-weight: 700;
    }}
    .status-review {{
      color: var(--warn);
    }}
    .status-ok {{
      color: #23733b;
    }}
    .status-unknown {{
      color: var(--muted);
    }}
    .cadence-summary {{
      color: var(--muted);
      display: block;
      line-height: 1.4;
      margin-top: 4px;
      max-width: 460px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      padding: 12px 10px;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      background: var(--band);
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
    }}
    a {{
      color: var(--accent);
    }}
    .missing {{
      color: var(--warn);
      font-weight: 600;
    }}
    @media (max-width: 720px) {{
      .stats {{
        grid-template-columns: 1fr 1fr;
      }}
      .metric {{
        border-bottom: 1px solid var(--line);
      }}
      table, thead, tbody, tr, th, td {{
        display: block;
      }}
      thead {{
        display: none;
      }}
      tr {{
        border-bottom: 1px solid var(--line);
        padding: 10px 0;
      }}
      td {{
        border: 0;
        padding: 5px 0;
      }}
      td::before {{
        content: attr(data-label) ": ";
        color: var(--muted);
        font-weight: 700;
      }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>{html.escape(CALENDAR_TITLE)}</h1>
    <div class="meta">Generated {html.escape(generated_at.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M UTC'))}</div>
  </header>
  <main>
    <div class="actions">
      <a href="{html.escape(WEBCAL_URL)}">Subscribe feed</a>
      <a href="{html.escape(PUBLIC_CALENDAR_URL)}">Download ICS file</a>
    </div>
    <div class="tabs" role="tablist" aria-label="Calendar views">
      <button class="tab" id="meetings-tab" role="tab" aria-selected="true" aria-controls="meetings-panel">Meetings</button>
      <button class="tab" id="cadence-tab" role="tab" aria-selected="false" aria-controls="cadence-panel">Cadence &amp; coverage</button>
    </div>
    <section id="meetings-panel" role="tabpanel" aria-labelledby="meetings-tab">
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Board</th>
            <th>Meeting Type</th>
            <th>Agenda</th>
            <th>Source</th>
          </tr>
        </thead>
        <tbody>
          {rows}
        </tbody>
      </table>
    </section>
    <section id="cadence-panel" role="tabpanel" aria-labelledby="cadence-tab" hidden>
      <h2 class="section-heading">Local area meeting cadence</h2>
      <p class="section-note">Cadence categories describe the primary full board. Executive committee patterns are included in the notes. Published dates always control; cadence is an audit expectation and never creates an unconfirmed calendar event.</p>
      <div class="stats">
        {metrics}
      </div>
      <p class="review-summary"><strong>{review_count} areas need review.</strong> These areas have blocked or degraded source access, no meeting date ever found, or no future meeting currently listed.</p>
      <table>
        <thead>
          <tr>
            <th>Local area</th>
            <th>Board</th>
            <th>Primary cadence</th>
            <th>Cadence evidence</th>
            <th>Meeting / agenda mechanism</th>
            <th>Next / latest known</th>
            <th>Coverage signal</th>
            <th>Source</th>
          </tr>
        </thead>
        <tbody>
          {cadence_table_rows}
        </tbody>
      </table>
    </section>
  </main>
  <script>
    const tabs = Array.from(document.querySelectorAll('[role="tab"]'));
    for (const tab of tabs) {{
      tab.addEventListener('click', () => {{
        for (const item of tabs) {{
          const selected = item === tab;
          item.setAttribute('aria-selected', String(selected));
          document.getElementById(item.getAttribute('aria-controls')).hidden = !selected;
        }}
      }});
    }}
  </script>
</body>
</html>
"""


def _meeting_row(meeting: Meeting) -> str:
    agenda = (
        f'<a href="{html.escape(meeting.agenda_url)}">Agenda</a>'
        if meeting.agenda_url
        else '<span class="missing">Missing</span>'
    )
    return f"""<tr>
  <td data-label="Date">{html.escape(meeting.meeting_date.isoformat())}</td>
  <td data-label="Board">{html.escape(meeting.board_name)}</td>
  <td data-label="Meeting Type">{html.escape(meeting.meeting_type)}</td>
  <td data-label="Agenda">{agenda}</td>
  <td data-label="Source"><a href="{html.escape(meeting.source_page_url)}">Source</a></td>
</tr>"""


def _cadence_metric(label: str, count: int) -> str:
    return f'<div class="metric"><strong>{count}</strong><span>{html.escape(label)}</span></div>'


def _cadence_row(row: CadenceCoverageRow, profile: SourceProfile | None = None) -> str:
    confidence = "confirmed" if row.confidence == "confirmed" else row.confidence
    evidence = (
        f"{html.escape(row.summary)}"
        f'<span class="cadence-summary">Classification: {html.escape(confidence)}</span>'
    )
    meeting_dates = (
        f"Next: {html.escape(row.next_meeting)}"
        if row.next_meeting
        else f"Latest: {html.escape(row.latest_known_meeting)}" if row.latest_known_meeting else "None found"
    )
    return f"""<tr>
  <td data-label="Local area">{html.escape(row.local_area)}</td>
  <td data-label="Board">{html.escape(row.board_name)}</td>
  <td data-label="Primary cadence">{html.escape(row.category)}</td>
  <td data-label="Cadence evidence">{evidence}</td>
  <td data-label="Meeting / agenda mechanism">{html.escape(mechanism_label(profile))}</td>
  <td data-label="Next / latest known">{meeting_dates}</td>
  <td data-label="Coverage signal"><span class="status status-{html.escape(row.coverage_level)}">{html.escape(row.coverage_signal)}</span></td>
  <td data-label="Source"><a href="{html.escape(row.source_url)}">Source</a></td>
</tr>"""


def _utc_stamp(value: datetime) -> str:
    return value.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _ics_text(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace(",", "\\,")
        .replace(";", "\\;")
        .replace("\r", "")
    )


def _fold_ics(line: str) -> str:
    if len(line) <= 75:
        return line
    chunks = [line[:75]]
    line = line[75:]
    while line:
        chunks.append(" " + line[:74])
        line = line[74:]
    return "\r\n".join(chunks)
