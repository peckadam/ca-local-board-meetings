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

### Contra Costa County WDB

- Official source: `https://www.wdbccc.com/meetings-agendas/`
- Current structure: The page has sections for Board of Directors, Executive Committee, Business and Economic Development Committee, and Youth Committee.
- Cadence observed on 2026-05-09: page text states Executive Committee generally meets 2nd Wednesday monthly from 3:00 PM to 5:00 PM; BED Committee generally meets 1st Wednesday every other month from 3:00 PM to 5:00 PM; Youth Council generally meets 4th Monday in Jan/Apr/Aug/Oct from 12:00 PM to 1:30 PM.
- Known traps: Board Member Interest links to Meetings & Agendas but is not a schedule source. Committee cadence text is not the same thing as a published meeting date. Visible dated Legistar links were committee-specific during audit.
- Status: partially audited; full Board of Directors cadence/dates still need official confirmation.

### NOVAworks Workforce Board

- Official source: `https://novaworks.org/about-us/board/`
- Current structure: Board page has an `Upcoming Meetings` section plus board materials and past meetings.
- Cadence observed on 2026-05-09: upcoming meetings include August 26, 2026 and December 2, 2026, Noon to 1:30 PM. April 22, 2026 was already outside the 14-day post-meeting check window.
- Known traps: past agenda links remain on the same page and must be matched by exact date. The page uses `Noon to 1:30 p.m.`, which must parse as a 12:00 PM start.
- Automation rule: generic extraction is acceptable after the Noon parsing fix and date-matched agenda handling.

### Orange County WDB

- Official source: `https://workforce.ocgov.com/oc-workforce-development-board/board-members/meeting-agendas-and-minutes`
- Do not use: policies/procedures pages.
- Current structure: Meeting Agendas and Minutes page has sections for OCWDB Full Board, Executive Committee, Program Services Committee, and Business Services Committee.
- Cadence observed on 2026-05-09: current fetched page showed recent full-board agenda packets, including January 28, 2026 and April 29, 2026. No future full-board meeting was visible in the 180-day window at audit time.
- Known traps: committee agenda packets are present on the same page as full-board packets; agenda links labeled `View Agenda` must be date/section matched.
- Automation rule: use only the official Meeting Agendas and Minutes page; date matching required.

### Santa Cruz County WDB

- Official source: `https://workforcescc.com/board-meetings/`
- Do not use: county SIP Steering Committee or Human Services Commission archive pages as WDB meeting sources.
- Current structure: Workforce Santa Cruz County page is sectioned by `FULL BOARD`, `EXECUTIVE COMMITTEE`, `CAREER SERVICES COMMITTEE`, and `BUSINESS SERVICES / CEDS COMMITTEE`.
- Cadence observed on 2026-05-09: Full Board 2026 dates include March 4 and May 20 at 8:30 AM; Executive Committee 2026 dates include February 4 and April 29 at 8:30 AM.
- Known traps: the page contains many years of archives and several non-board committee sections.
- Automation rule: use the `santa_cruz_wfscc` strategy and only publish Full Board and Executive Committee sections.

### South Bay WIB

- Official source: `https://www.sbwib.org/2026-meeting-agendas`
- Current structure: Annual page grouped by body/committee, including Business/Technology/Economic Development Committee, SBWIB Executive Committee, South Bay Workforce Investment Board, Performance & Evaluation Committee, Youth Development Council Committee, and One-Stop Policy Committee.
- Cadence observed on 2026-05-09: full-board dates visible on the 2026 page were January 15, 2026 and April 16, 2026; Executive Committee dates included January 8, February 12, March 12, and April 9; Youth Development Council had May 5.
- Known traps: dates inherit meaning from the nearest section heading. A Youth Development Council date must not become a full board meeting.
- Automation rule: use the `south_bay_sectioned_agendas` strategy.

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

### Workforce Alliance North Bay

- Official source: `https://www.workforcealliancenorthbay.org/board-meetings/`
- Current structure: Board Meetings page has separate sections for Governing Board, Regional Workforce Development Board, Regional Workforce Development Board Executive Committee, Communications & Outreach Committee, and Issues & Opportunities Committee.
- Cadence observed on 2026-05-09: Regional WDB has June 11, 2026 from 10:00 AM to 12:00 PM; RWDB Executive Committee has May 13, 2026 from 9:00 AM to 10:30 AM.
- Known traps: Governing Board meetings appear before the Regional WDB section and should not be published as local WDB meetings. Canceled rows are interspersed with active rows. Historical agenda links are numerous.
- Automation rule: use the `workforce_alliance_north_bay` strategy and only publish Regional WDB and Regional WDB Executive Committee sections.

## Partially Audited Sources

These sources have official endpoints and known traps documented, but still need either future-date confirmation, a custom parser, or PDF/JavaScript handling before they should be promoted to `high`.

### Imperial County WDB

- Official source: `https://www.ivworkforce.com/about/meetings`
- Current structure: Meeting Calendar lists event-detail pages; known detail page is `https://www.ivworkforce.com/about/meetings/may-27-2026-executive-committee-meeting`.
- Cadence observed on 2026-05-09: May 27, 2026 Executive Committee meeting at 11:00 AM.
- Known traps: the home page and general site summaries can contain workforce-program dates that are not board meetings. Meeting type is clearest from the event-detail page title.
- Automation rule: use `event_detail_title` for event detail URLs and keep the calendar page as the official discovery surface.

### Madera County WDB

- Official source: `https://maderaworkforce.com/wdb`
- Current structure: WDB page contains a Board Meetings area and agenda/minutes links.
- Cadence observed on 2026-05-09: fetched HTML showed a stale June 18, 2025 special meeting agenda but no current 2026 schedule.
- Known traps: homepage announcements and job-fair dates are not board meetings; stale agenda notices can remain visible.
- Automation rule: keep as medium confidence until a current schedule or agenda page is located.

### Mother Lode Workforce Development Board

- Official source: `https://www.mljt.org/agendas-and-minutes`
- Current structure: Wix agendas/minutes page exposes many PDF agenda links; separate schedule PDF candidate is present in the registry.
- Cadence observed on 2026-05-09: no reliable future meeting row was extracted from fetched HTML.
- Known traps: Wix page markup is noisy and PDF labels are not enough to infer current future meetings without schedule context.
- Automation rule: needs PDF schedule extraction or a Wix-aware parser before publishing future meetings.

### Northern Rural Training / NoRTEC

- Official source: `https://www.ncen.org/index.php/meetings/agendas`
- Current structure: agendas archive grouped by year; partner meeting notice PDF candidate is present in the registry.
- Cadence observed on 2026-05-09: no current future meeting row was exposed by generic HTML extraction.
- Known traps: old executive committee PDFs and partner-meeting notices can look relevant but may not be the current local board schedule.
- Automation rule: needs archive/PDF parsing before raising confidence.

### Sacramento SETA

- Official source: `https://www.seta.net/resources/board-operations/`
- Agenda source: `https://www.seta.net/resources/agendas/`
- Current structure: Board Operations separates Governing Board, Community Action Board, Policy Council, Sacramento Works Inc., and committees; Sacramento Works Inc. is the workforce-board body.
- Cadence observed on 2026-05-09: fetched agenda page showed a Sacramento Works section but no current dated meeting rows available to generic extraction.
- Known traps: SETA hosts multiple boards; Governing Board and Head Start/Policy Council meetings are not local workforce board meetings.
- Automation rule: scope to Sacramento Works Inc. only; needs section-specific parsing once dated rows are visible.

### San Luis Obispo County WDB

- Official board source: `https://www.slocounty.ca.gov/departments/social-services/workforce-development-board/board`
- Official executive source: `https://www.slocounty.ca.gov/departments/social-services/workforce-development-board/board/executive-committee`
- Current structure: board/committee pages describe bodies; individual meeting detail pages carry date, time, location, and agenda links.
- Cadence observed on 2026-05-09: Executive Committee meets on the second Wednesday of non-WDB months (January, March, April, June, July, September, October, December) at 8:30 AM; detail page observed for June 10, 2026 at 8:30 AM.
- Known traps: the WDB landing page has training and job-center announcements that can look like meeting dates.
- Automation rule: do not parse the landing page; use event detail pages and infer meeting type from the detail title.

### Santa Clara County work2future

- Official source: `https://www.work2future.org/board/`
- Current structure: Board + Committees page lists event cards for board, executive committee, youth committee, and closed holidays; agendas and packets are on event-detail pages.
- Cadence observed on 2026-05-09: detail pages were visible for April 14, 2026 Board and April 2, 2026 Executive Committee; no future post-May 9 board or executive meeting was confirmed in fetched HTML.
- Known traps: holiday closures and youth committee events share the same calendar surface. Agenda links may be placeholders on some detail pages.
- Automation rule: exclude closed holidays and youth committee events; use event detail title only when the detail page is clearly a board or executive committee meeting.

### SELACO WDB

- Official source: `https://www.selacowdb.com/agendas/`
- Current structure: agendas page is grouped by Board of Directors, Policy Board, and Special Ad-Hoc Committees.
- Cadence observed on 2026-05-09: 2026 visible agenda links included April 21 Policy Board and February 10 Special Ad-Hoc Lease Committee; no future full-board or executive meeting was confirmed.
- Known traps: stale 2024 Executive Committee PDFs remain findable and must not be treated as current meeting endpoints.
- Automation rule: keep as medium confidence until current Board of Directors cadence and executive committee handling are confirmed.

## Remaining Audit Queue

These sources are still `medium` until manually profiled. Each needs the same treatment: official endpoint, cadence, agenda source, committee handling, stale-PDF traps, and extraction strategy.

- Alameda County WDB
- Anaheim WDB
- Foothill WDB
- Fresno Regional WDB
- Humboldt County WDB
- Kern/Inyo/Mono WDB
- Kings County WDB
- Long Beach WIN
- Los Angeles City WDB
- Los Angeles County WDB
- Merced County WDB
- Monterey County WDB
- North Central Counties WDB
- Oakland WDB
- Richmond WDB
- Riverside County WDB
- San Benito County WDB
- San Bernardino County WDB
- San Diego Workforce Partnership
- San Francisco OEWD
- San Joaquin County WorkNet
- Santa Ana WDB
- Santa Barbara County WDB
- Solano County WDB
- Sonoma County WDB
- Ventura County WDB
- Verdugo WDB
- Yolo County WDB
