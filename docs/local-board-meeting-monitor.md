# California Local Board Meeting Monitor

This automation checks California local workforce development board and executive committee pages once per day, discovers future meetings, revisits near-term meetings for agendas, writes run reports, and publishes an online calendar plus an `.ics` subscription feed.

Microsoft Graph OneDrive/Outlook support still exists in the codebase, but the recommended implementation is now credential-free publishing through static web artifacts.

## What It Creates

- Source registry: `data/local_board_meetings/source_registry.csv`
- SQLite database: `data/local_board_meetings/meetings.sqlite3`
- Reports: `data/local_board_meetings/reports/*.md` and `*.json`
- Progress log: `data/local_board_meetings/progress_log.md`
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

This repo publishes through GitHub Pages branch publishing, which avoids GitHub Actions permissions:

1. Open **Settings → Pages**.
2. Set **Build and deployment → Source** to **Deploy from a branch**.
3. Select branch **main**.
4. Select folder **/docs**.
5. Save.

The published page will use:

- Page: `https://OWNER.github.io/REPO/`
- Subscribe URL: `https://OWNER.github.io/REPO/calendar.ics`

The published `calendar.ics` URL can be subscribed to from Apple Calendar, Google Calendar, Outlook, or most calendaring tools.

## Daily Scheduling

The preferred production scheduler is GitHub Actions:

- Workflow: `.github/workflows/refresh-local-board-meetings.yml`
- Schedule: daily at `15:17 UTC`, which is morning Pacific time.
- Manual run: GitHub repository -> Actions -> Refresh Local Board Meetings -> Run workflow.

The workflow checks official source pages, regenerates `docs/index.html` and `docs/calendar.ics`, and commits/pushes changes only when the published calendar content changes.

For cron on a local machine, the refresh script remains available as a fallback:

```cron
17 8 * * * "/Users/adampeck/Documents/New project/etl/local_board_meetings/refresh_and_publish.sh" >> "/Users/adampeck/Documents/New project/data/local_board_meetings/cron.log" 2>&1
```

## Operating Notes

- The registry starts from the existing official CWA local-board website manifest and adds Mother Lode.
- Exact meeting/agenda endpoints are refined as official pages reveal schedule, agenda, minutes, or executive committee links.
- Source-specific structure, cadence, and false-positive traps are documented in `docs/local-board-source-intelligence.md` and encoded in `data/local_board_meetings/source_profiles.json` when a generic extractor is not reliable enough.
- The fetcher uses a descriptive user agent, retry/backoff, and robots.txt checks by default.
- Meetings within 10 days are eligible for agenda downloads when an agenda URL has been found.
- Missing agendas within 72 hours are expected sometimes, especially for special meetings, but are always listed in the run report.
- Past meetings are retained in SQLite. The web calendar publishes future meetings only.

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
- If the GitHub Pages deployment succeeds but the calendar app does not update immediately, wait for the calendar client’s refresh interval or remove/re-add the subscription.
