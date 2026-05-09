# Local Board Source Intelligence

This file is the operating memory for the meeting monitor. The automation should not treat all local board websites as interchangeable: each source needs an explicit understanding of where meeting dates live, where agendas live, what cadence is expected, and which page elements are known false positives.

## Reliability Model

- `high`: manually audited official source; extraction rules are documented and covered by either a profile or a precise registry note.
- `medium`: official source known, but exact meeting/agenda structure still needs manual verification.
- `low`: source likely wrong, stale, JavaScript-only, PDF-only, or mixed with non-board content.

## Audited Sources

### Golden Sierra Workforce Board

- Official meeting source: `https://goldensierra.com/calendar/category/public-meeting/workforce-board`
- Do not use: `https://goldensierra.com/calendar`
- Current structure: The Workforce Board category page contains public meeting events for the full board and executive committee.
- Cadence observed on 2026-05-09: May 21, 2026 has an Executive Committee meeting at 12:00 PM and Workforce Board meeting at 1:00 PM.
- Known traps: the general calendar includes workshops and other non-board events; calendar UI controls can expose dates that are not meetings.
- Automation rule: use the Workforce Board category page only.

### Stanislaus County WDB

- Official meeting source: `https://www.stanworkforce.com/workforce-board/`
- Current structure: The page has a full-board section with `CURRENT AGENDA`, `UPCOMING BOARD MEETING`, and `PREVIOUS AGENDAS & MINUTES`, followed by committee sections.
- Cadence observed on 2026-05-09: full board upcoming meeting is Monday, June 1, 2026, 12:00 PM to 2:00 PM.
- Known traps: the same page includes Workforce Strategy & Innovation Committee, Youth Development Committee, and Business Development Committee dates and agenda archives. Historical committee PDFs include canceled 2024 agendas and must not be matched to current full-board meetings.
- Automation rule: use the Stanislaus-specific extraction strategy. Parse the full-board meeting only from `UPCOMING BOARD MEETING`; use only the full-board current agenda link and reject stale/canceled historical PDFs.

### Tulare County WIB

- Official board source: `https://www.tularewib.org/wibboard`
- Official committee source: `https://www.tularewib.org/pec`
- Do not use: `https://employmentconnection.org/` as the meeting source.
- Current structure: the board page publishes annual meeting dates and year-specific agenda sections whose PDF links may be labeled only by month.
- Cadence observed on 2026-05-09: May 13, 2026 board meeting has a May agenda PDF posted; June 10, 2026 is listed with agenda not yet posted.
- Known traps: Wix PDF URLs do not necessarily contain the word `agenda`; agenda semantics come from the surrounding `2026 Board Agendas` heading.
- Automation rule: allow month-labeled PDF links when they are inside a year-specific agenda section.

## Remaining Audit Queue

These sources are still `medium` until manually profiled. Each needs the same treatment: official endpoint, cadence, agenda source, committee handling, stale-PDF traps, and extraction strategy.

- Alameda County WDB
- Anaheim WDB
- Contra Costa County WDB
- Foothill WDB
- Fresno Regional WDB
- Humboldt County WDB
- Imperial County WDB
- Kern/Inyo/Mono WDB
- Kings County WDB
- Long Beach WIN
- Los Angeles City WDB
- Los Angeles County WDB
- Madera County WDB
- Merced County WDB
- Monterey County WDB
- Mother Lode Workforce Development Board
- NOVAworks Workforce Board
- North Central Counties WDB
- Northern Rural Training / NoRTEC
- Oakland WDB
- Orange County WDB
- Richmond WDB
- Riverside County WDB
- Sacramento SETA
- San Benito County WDB
- San Bernardino County WDB
- San Diego Workforce Partnership
- San Francisco OEWD
- San Joaquin County WorkNet
- San Luis Obispo County WDB
- Santa Ana WDB
- Santa Barbara County WDB
- Santa Clara work2future
- Santa Cruz County WDB
- SELACO WDB
- Solano County WDB
- Sonoma County WDB
- South Bay WIB
- Ventura County WDB
- Verdugo WDB
- Workforce Alliance North Bay
- Yolo County WDB
