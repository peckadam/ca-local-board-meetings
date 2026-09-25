# California Local Board Meeting Monitor

This automation checks California local workforce development board and executive committee pages once per day, discovers future meetings, revisits near-term meetings for agendas, writes run reports, and publishes an online calendar plus an `.ics` subscription feed.

Microsoft Graph OneDrive/Outlook support still exists in the codebase, but the recommended implementation is now credential-free publishing through static web artifacts.

## What It Creates

- Source registry: `data/local_board_meetings/source_registry.csv`
- SQLite database: `data/local_board_meetings/meetings.sqlite3`
- Reports: `data/local_board_meetings/reports/*.md` and `*.json`
- Progress log: `data/local_board_meetings/progress_log.md`
- Statewide coverage matrix: `data/local_board_meetings/coverage_matrix.md`
- Historical coverage state: `data/local_board_meetings/coverage_history.json`
- Structured full-board cadence registry: `data/local_board_meetings/cadence_registry.json`
- Persisted future-meeting state: `data/local_board_meetings/active_meetings.json`
- Agenda email deduplication state: `data/local_board_meetings/agenda_notifications.json`
- Local agenda cache: `data/local_board_meetings/agendas/`
- Generated online calendar page: `data/local_board_meetings/public/index.html`
- Generated calendar subscription feed: `data/local_board_meetings/public/calendar.ics`
- Published GitHub Pages files: `docs/index.html` and `docs/calendar.ics`

## Run

Dry-run checks pages, updates the local database, writes reports, and builds the static calendar:

```bash
python -m etl.local_board_meetings.runner
```

Dry-run with local agenda downloads:

```bash
python -m etl.local_board_meetings.runner --download-agendas
```

Fast smoke run:

```bash
python -m etl.local_board_meetings.runner --limit 5
```

Make targets are also available:

```bash
make local-board-meetings-dry-run
make test
```

## Publish Online

This repo publishes through the same GitHub Actions workflow that performs the daily refresh:

1. Open **Settings → Pages**.
2. Set **Build and deployment → Source** to **GitHub Actions**.
3. Leave that setting in place. The refresh workflow packages the `docs/` folder and deploys it after each successful run.

The published page will use:

- Page: `https://OWNER.github.io/REPO/`
- Subscribe URL: `https://OWNER.github.io/REPO/calendar.ics`

The published `calendar.ics` URL can be subscribed to from Apple Calendar, Google Calendar, Outlook, or most calendaring tools.

## Daily Scheduling

The preferred production scheduler is GitHub Actions:

- Workflow: `.github/workflows/refresh-local-board-meetings.yml`
- Schedule: daily at `15:17 UTC`, which is morning Pacific time.
- Manual run: GitHub repository -> Actions -> Refresh Local Board Meetings -> Run workflow.

The workflow checks official source pages, regenerates `docs/index.html` and `docs/calendar.ics`, commits/pushes changed state, uploads the `docs/` folder as a Pages artifact, and deploys the live site. It has the required `contents: write`, `pages: write`, and `id-token: write` permissions.

## Agenda Email Notifications

When SMTP secrets are configured, the daily workflow emails `apeck@calworkforce.org` whenever an agenda is first found or its file content changes. Each message includes the board, meeting date/type, location and virtual link when known, direct agenda/source links, and an automated narrative synopsis that distinguishes proposed decisions, informational reports, closed-session topics, and public comment. The synopsis uses prospective language and does not imply that an agendized action was approved. A committed content-hash ledger prevents duplicate messages across stateless GitHub Actions runs.

Add these repository secrets under **Settings -> Secrets and variables -> Actions**:

- `AGENDA_SMTP_HOST`
- `AGENDA_SMTP_PORT` (normally `587` for STARTTLS or `465` for SSL)
- `AGENDA_SMTP_USERNAME`
- `AGENDA_SMTP_PASSWORD`
- `AGENDA_SMTP_FROM`
- `AGENDA_SMTP_USE_SSL` (`true` only for implicit SSL, normally port 465)

The recipient is fixed in the workflow as `apeck@calworkforce.org`. Before enabling delivery for the first time, record already-known agendas without sending an initial batch:

```bash
python -m etl.local_board_meetings.runner --bootstrap-agenda-notifications
```

To test configured delivery manually:

```bash
python -m etl.local_board_meetings.runner --notify-agendas --limit 3
```

For cron on a local machine, the refresh script remains available as a fallback:

```cron
17 8 * * * "/Users/adampeck/Documents/New project/etl/local_board_meetings/refresh_and_publish.sh" >> "/Users/adampeck/Documents/New project/data/local_board_meetings/cron.log" 2>&1
```

## Operating Notes

- The registry starts from the existing official CWA local-board website manifest and adds Mother Lode.
- Exact meeting/agenda endpoints are refined as official pages reveal schedule, agenda, minutes, or executive committee links.
- Source-specific structure, cadence, and false-positive traps are documented in `docs/local-board-source-intelligence.md` and encoded in `data/local_board_meetings/source_profiles.json` when a generic extractor is not reliable enough.
- The fetcher uses a descriptive user agent, retry/backoff, and robots.txt checks by default. A narrowly recognized public Google Calendar ICS subscription URL embedded by an official board page is treated as an explicit machine feed; this is not a general robots.txt bypass.
- Meetings within 10 days are eligible for agenda downloads when an agenda URL has been found.
- Missing agendas within 72 hours are expected sometimes, especially for special meetings, but are always listed in the run report.
- Past meetings are retained in SQLite. The web calendar publishes future meetings only.
- Confirmed future meetings remain in the persisted state when a source temporarily fails or stops showing an already-announced date; they age out after the meeting date instead of disappearing from the calendar.
- The online page includes a **Cadence & coverage** tab. It compares the documented full-board cadence with future calendar entries and historical evidence for every local area.

## Meeting-Coverage Review

Each daily run evaluates all 45 areas against four independent checks:

- **Future coverage:** whether at least one future board or executive meeting is currently listed.
- **Historical coverage:** whether any official meeting date has ever been confirmed.
- **Cadence expectation:** whether the primary full board is monthly, quarterly, every other month, follows another published schedule, or remains unestablished.
- **Source health:** whether every required official endpoint is usable, one secondary endpoint is degraded, or the primary meeting source is blocked.

An area enters the review queue when its primary source is blocked, a secondary endpoint is degraded, no meeting date has ever been found, or no future meeting is currently listed. A review row is therefore not automatically a source failure. Cadence is used only to identify likely gaps; it never generates a calendar event without an official date.

Source health has three states:

- **OK:** the authoritative schedule and agenda mechanisms completed without a relevant fetch error.
- **Degraded:** a secondary schedule, agenda, executive, or detail endpoint failed, but another authoritative endpoint or a manually verified official schedule still supplies meeting data.
- **Blocked:** no authoritative endpoint succeeded and there is no verified official schedule fallback for the run.

### Connector Hierarchy

Each board profile records the narrowest official mechanism that fits its publishing system. The runner prefers, in order:

1. An official API, public ICS feed, Legistar, NovusAgenda, or other structured agenda system.
2. A board-specific event/category page and its event-detail records.
3. An official annual schedule PDF paired with a board-specific agenda archive.
4. A board-specific HTML schedule or packet list with section and date matching.
5. Manually verified official meeting fallbacks when the same government source blocks unattended requests.

Generic homepages are not probed for audited sources unless they are the documented authoritative endpoint. Agenda files are attached only by exact date and meeting type; cadence never projects an event.

### Audit Snapshot (September 25, 2026)

- 44 of 45 local boards have at least one confirmed meeting date in the historical coverage ledger.
- 24 of 45 have at least one agenda matched to a board or executive committee meeting.
- 32 of 45 have an audited source and documented cadence; 13 remain partial.
- Primary full-board cadence: 1 monthly, 12 quarterly, 8 every other month, 9 other published patterns, and 15 not yet established.
- 19 of 45 currently have at least one future meeting listed, representing 49 future board or executive meetings.
- 30 areas require some coverage review, usually because no future notice is currently published; only 2 are source-blocked and 4 are degraded.
- Yolo County is the only board without a confirmed usable meeting notice. Its current source constraints are documented in `docs/local-board-source-intelligence.md`.

## Optional Microsoft Graph Mode

If you later want OneDrive uploads or Outlook calendar writes, the `--live` flag still uses Microsoft Graph. See `.env.example` and `etl/local_board_meetings/auth_device_code.py`.

Delegated Graph permissions:

- `offline_access`
- `User.Read`
- `Files.ReadWrite`
- `Calendars.ReadWrite`

## Troubleshooting

- If a board reports failures, open `data/local_board_meetings/progress_log.md` and verify the official schedule or agenda page manually.
- If meetings are not found, the source may use embedded calendars, JavaScript rendering, or PDF-only schedule packets. Add the exact official page URL to `source_registry.csv`.
- Review `data/local_board_meetings/coverage_matrix.md` after every run. `NO`, `partial`, and `review` cells are the explicit research queue; a successful fetch alone does not count as meeting or agenda coverage.
- If the GitHub Pages deployment succeeds but the calendar app does not update immediately, wait for the calendar client’s refresh interval or remove/re-add the subscription.
