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
- Cadence observed: paired Executive Committee and Workforce Board events commonly appear on the same date, with the Executive Committee immediately before the board. Confirmed examples include May 21 and September 17, 2026.
- Known traps: the general calendar includes workshops and other non-board events; calendar UI controls can expose dates that are not meetings.
- Automation rule: use the Workforce Board category page only, publish exact event titles, and follow each event-detail link for agenda and venue data.

### Contra Costa County WDB

- Official schedule/agenda source: `https://contra-costa.legistar.com/Calendar.aspx`
- Supporting board page: `https://www.wdbccc.com/meetings-agendas/`
- Current structure: Legistar names every WDB-related row `Workforce Development Board`; the subtype at the end of the location cell identifies `Full Board/Executive Committee`, Youth, or BED.
- Cadence verified on 2026-09-24: actual 2026 postings use combined Full Board/Executive Committee meetings and do not follow the older proposed separate cadence. September 16 was a combined noon meeting with a published agenda.
- Known traps: the October 2025 draft calendar was superseded by actual postings. The October 21, 2026 generic WDB row is Youth Committee and must not be published as full board/executive.
- Automation rule: use `contra_costa_legistar`; require the exact `Full Board/Executive Committee` subtype and bind agenda/location/Zoom from that row.

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
- Known traps: dates inherit meaning from the nearest section heading. Youth Development Council, One-Stop Policy, Performance & Evaluation, and Business/Technology/Economic Development dates must not become public calendar events.
- Automation rule: use the `south_bay_sectioned_agendas` strategy and publish only `SBWIB EXECUTIVE COMMITTEE` and `SOUTH BAY WORKFORCE INVESTMENT BOARD`.

### Stanislaus County WDB

- Official meeting source: `https://www.stanworkforce.com/workforce-board/`
- Current structure: The page has a full-board section with `CURRENT AGENDA`, `UPCOMING BOARD MEETING`, and `PREVIOUS AGENDAS & MINUTES`, followed by committee sections.
- Cadence observed on 2026-05-09: full board upcoming meeting is Monday, June 1, 2026, 12:00 PM to 2:00 PM.
- Known traps: the same page includes Workforce Strategy & Innovation Committee, Youth Development Committee, and Business Development Committee dates and agenda archives. Historical committee PDFs include canceled 2024 agendas and must not be matched to current full-board meetings.
- Automation rule: use the Stanislaus-specific extraction strategy. Parse the full-board meeting only from `UPCOMING BOARD MEETING`; use only the full-board current agenda link and reject stale/canceled historical PDFs.

### Tulare County WIB

- Official board source: `https://www.tularewib.org/wibboard`
- Official committee context source: `https://www.tularewib.org/pec`
- Do not use: `https://employmentconnection.org/` as the meeting source.
- Current structure: the board page publishes annual meeting dates and year-specific agenda sections whose PDF links may be labeled only by month.
- Cadence observed on 2026-05-09: May 13, 2026 board meeting has a May agenda PDF posted; June 10, 2026 is listed with agenda not yet posted.
- Known traps: Wix PDF URLs do not necessarily contain the word `agenda`; agenda semantics come from the surrounding `2026 Board Agendas` heading. Program & Evaluation Committee meetings on `/pec` are not full-board or executive-committee meetings.
- Automation rule: use `tulare_wib_board_only`; allow month-labeled PDF links on the board page and exclude `/pec` from the public board/executive calendar.

### Workforce Alliance North Bay

- Official source: `https://www.workforcealliancenorthbay.org/board-meetings/`
- Current structure: Board Meetings page has separate sections for Governing Board, Regional Workforce Development Board, Regional Workforce Development Board Executive Committee, Communications & Outreach Committee, and Issues & Opportunities Committee.
- Cadence observed on 2026-05-09: Regional WDB has June 11, 2026 from 10:00 AM to 12:00 PM; RWDB Executive Committee has May 13, 2026 from 9:00 AM to 10:30 AM.
- Known traps: Governing Board meetings appear before the Regional WDB section and should not be published as local WDB meetings. Canceled rows are interspersed with active rows. Historical agenda links are numerous.
- Automation rule: use the `workforce_alliance_north_bay` strategy and only publish Regional WDB and Regional WDB Executive Committee sections.

### Alameda County WDB

- Official source: `https://acwdb.org/boards/`
- Current structure: Board and Committees page publishes meeting links for the board and several committees.
- Cadence observed on 2026-05-10: Quarterly Board meetings observed March 12 and May 14, 2026 from 9:00 AM to Noon; Executive Committee meetings observed February 25 and April 22, 2026.
- Known traps: Youth Committee, Systems and Strategies Committee, Organizational Effectiveness Committee, and Joint Committee entries share the page and should not be published as board/executive meetings.
- Automation rule: use the `alameda_acwdb` strategy and only publish Quarterly Board Meeting and Executive Committee links.

### Humboldt County WDB

- Official board source: `https://humboldtgov.org/3803/Humboldt-County-Workforce-Development-Bo`
- Official agenda source: `https://humboldtgov.org/agendacenter`
- Current structure: CivicEngage Agenda Center contains separate sections for Workforce Development Board and Workforce Development Board Executive Committee.
- Cadence observed on 2026-05-10: county page states quarterly board meetings; 2026 agenda entries observed include February 27 Board and January 30/April 24 Executive Committee.
- Known traps: Agenda Center includes many unrelated county boards before the WDB sections. The old `/1709/Workforce-Development-Board` URL returns 404. Youth Council is a separate category.
- Automation rule: use the `humboldt_civicengage` strategy and publish only Workforce Development Board and Workforce Development Board Executive Committee sections.

## Additional Source Profiles

This section includes both fully audited and still-partial sources. The generated `coverage_matrix.md` is authoritative for current status.

### Anaheim WDB

- Official board source: `https://www.anaheim.net/176/Boards-Commissions`
- Official agenda source: `https://www.anaheim.net/AgendaCenter/Workforce-Development-Board-24`
- Current structure: Boards and Commissions page lists the WDB cadence; AgendaCenter category 24 lists agenda/minute items.
- Cadence verified on 2026-09-24: WDB meets 3rd Wednesday every other month at 9:00 AM at Anaheim West Tower, Gordon Hoyt Conference Room. AgendaCenter has February 18, canceled April 15, and June 17, 2026 rows; February and June have agendas.
- Known traps: City Council agenda pages and Visit Anaheim subcontractor pages are false sources.
- Automation rule: use `anaheim_civicengage`; parse only category 24 rows, skip canceled rows, bind agendas from the same row, and never project cadence.

### Foothill WDB

- Official source: `https://fwdbworks.org/events/`
- Current structure: WordPress Events Calendar month view lists FWDB meetings and non-board events; board page points users to the Meetings and Events calendar.
- Cadence observed on 2026-05-10: April 30, 2026 Special Board Meeting and FWDB Executive Committee Meeting were visible; no future post-May 9 board/executive meeting appeared in the fetched May view.
- Known traps: old `foothillwdb.org` domain no longer resolves. The month grid exposes day numbers and orientation/workshop events that must not become meetings.
- Automation rule: use `foothill_events`; parse only event titles containing FWDB meeting language and exclude orientation/workshop/training titles.

### Fresno Regional WDB

- Official source: `https://frwdb.net/board-of-directors/`
- Current structure: Board & Committees page describes the board, Executive Committee, Adult Council, Youth Council, and Skills Development Council.
- Cadence observed on 2026-05-10: no current meeting schedule or agenda links were visible in fetched HTML.
- Known traps: old `fresno-ca-wdb.com` domain no longer resolves. Governance page content should not be treated as a schedule.
- Automation rule: keep as medium confidence until the agenda/schedule endpoint is found.

### Kern/Inyo/Mono WDB

- Official board source: `https://www.employerstrainingresource.com/wdb/full-wdb-board`
- Official executive source: `https://www.employerstrainingresource.com/wdb/executive-committee`
- Current structure: Employers Training Resource hosts archive pages for Full WDB Board and Executive Committee agendas; county BCC page describes the board and says it meets at least four times per year.
- Cadence observed on 2026-05-10: historical 2025 full-board dates included February 19, May 28, September 24, and December 17; executive dates included February 6, May 15, September 11, and December 2. No current 2026 future date row was visible in fetched HTML.
- Known traps: old `kern-inyo-mono.org` domain no longer resolves. Americas Job Center overview is descriptive, not a schedule. The ETR pages returned 403 to the automation during validation.
- Automation rule: keep as medium confidence and human-review blocked until the fetcher can reliably access the official archive pages or another official schedule source is found.

### Kings County WDB

- Official source: `https://www.countyofkingsca.gov/departments/board-of-supervisors/boards-commissions/workforce-development-board`
- Current structure: county Boards & Commissions page identifies the WDB and links meetings/contact/calendar/website controls, but fetched HTML did not expose WDB dates or agenda files.
- Cadence observed on 2026-05-10: no current meeting cadence was confirmed.
- Known traps: `kingsworkforce.org` returned 403; Board of Supervisors agenda pages are not WDB meeting sources.
- Automation rule: keep as medium confidence until a fetchable official agenda/schedule endpoint is found.

### Los Angeles City WDB

- Official source: `https://www.wiblacity.org/index.php/calendar`
- Current structure: Meeting Calendar & Agendas page embeds a NovusAgenda iframe and says agendas/minutes/reports from the past six months are available there; older documents are split between searchable and archive pages.
- Cadence observed on 2026-05-10: fetched HTML did not expose meeting rows without iframe/NovusAgenda handling.
- Known traps: old `ewddlacity.com/index.php/wdb` URL returns 404. Landing pages and newsletter/program dates should not be parsed as board meetings.
- Automation rule: needs iframe/NovusAgenda support before raising confidence.

### Los Angeles County WDB

- Official source: `https://www.ajcc.lacounty.gov/wdb`
- Current structure: AJCC WDB page has visible calendar and news items; calendar can include committee-specific entries.
- Cadence observed on 2026-05-10: visible item found for June 2, 2026 Finance Committee; news item referenced a March 20, 2026 Regular Quarterly meeting recording. No future full board or executive committee row was confirmed.
- Known traps: old `wdb.lacounty.gov` domain does not resolve. Finance Committee, orientation, and recording/news rows must not be published as full board/executive meetings. The AJCC page returned 403 to the automation during validation.
- Automation rule: use `la_county_wdb_calendar` and publish only full WDB or Executive Committee entries.

### Merced County WDB

- Official source: `https://worknetmerced.com/workforce-development`
- Current structure: Worknet Merced page lists WDB and Executive Committee rows with dates, times, locations, and agenda links; a side card lists general cadence/dates.
- Cadence observed on 2026-05-10: May 11, 2026 Executive Committee was marked rescheduled to June 8 with agenda link; side card says full board meets last Thursday of each quarter and Executive Committee meets odd-numbered months on Mondays.
- Known traps: old `workforce-merced.com` domain does not resolve. Historical no-year rows such as `June 7` must not be projected into the current year.
- Automation rule: use `merced_worknet`; require explicit-year meeting rows, except for same-row rescheduled dates.

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

- Official schedule source: `https://www.slocounty.ca.gov/departments/social-services/workforce-development-board/meetings`
- Current structure: a stable Upcoming/Archived Meetings table provides exact board and executive dates, detail links, times, locations, cancellations, and agenda documents.
- Cadence confirmed on 2026-09-24: full WDB meets quarterly on the first Thursday of February, May, August, and November at 8:30 AM. Executive Committee meets on the second Wednesday of non-WDB months at 8:30 AM.
- Known traps: the descriptive Board page contains a dated Native American Day closure notice that generic extraction incorrectly treated as a committee meeting.
- Automation rule: use only the stable Meetings table, reject canceled rows, and follow each detail page for agenda documents.

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

### Long Beach WIN

- Official source: `https://www.longbeach.gov/edo/talent-workforce/workforce-development-board/`
- Current structure: LBWIN Board page has a `2026 Scheduled Meetings` block.
- Cadence observed on 2026-05-10: April 2, June 4, August 6, October 1, and December 3 from 9:00 to 11:00 AM at LBWIN Adult Career Services Center.
- Known traps: old `economicdevelopment/workforce-development` URL redirects badly for urllib. Board member biographies include date-like text.
- Automation rule: use `long_beach_lbwin_schedule`; parse only the scheduled meetings block.

### Monterey County WDB

- Official source: `https://montereycountyworks.com/events/mcwdb-meeting-jun-25-2026/`
- Current structure: Monterey County Works publishes individual event-detail pages with date, time, location/category, and packet links when available.
- Cadence observed on 2026-05-10: June 25, 2026 Board Meeting from 9:00 AM to 11:00 AM at Monterey County Works Center.
- Known traps: old `montereycountywdb.org` timed out. Monterey County Works includes non-board events, so event detail title/category should be checked before publishing.
- Automation rule: use `event_detail_title` for known detail pages; needs event listing pagination to discover more meetings automatically.

### North Central Counties WDB

- Official source: `https://www.northcentralcounties.com/nccc-workforce-development-board`
- Current structure: NCCC WDB page has a dedicated `2026 Workforce Development Board Meetings` section.
- Cadence observed on 2026-05-10: February 19, May 21, August 20, and November 5, 2026; additional meetings may be scheduled as necessary.
- Known traps: old `ncccwdb.org` does not resolve. NCCC Governing Board meetings are separate from WDB meetings.
- Automation rule: use `nccc_wdb_schedule`; parse only the 2026 WDB section.

### Oakland WDB

- Official source: `https://www.oaklandca.gov/Government/Boards-Commissions/Workforce-Development-Board`
- Current structure: city page lists WDB agenda/minutes documents and states the regular-meeting cadence.
- Cadence observed on 2026-05-10: regular meetings are 1st Thursday of February, May, August, and November from 8:30 AM to 11:00 AM. Document list had 2026 rows for February 26 and March 20 but no confirmed future post-May 9 agenda row.
- Known traps: old `oaklandworkforce.org` does not resolve. Executive Committee and full-board rows are mixed in the documents list.
- Automation rule: keep as medium confidence; do not infer future meetings from cadence until publication policy is confirmed.

### Richmond WDB

- Official source: `https://www.richmondca.gov/671/Richmond-WDB`
- Current structure: the WDB-specific page links an annual schedule and date-labeled agenda/minutes documents; live cancellation/reschedule text overrides the annual PDF.
- Cadence verified on 2026-09-24: 11:30 AM on the second Thursday every other month at RichmondWORKS, 330 25th Street. July 9 was canceled, September 10 moved to September 17, and November 12 remains scheduled.
- Known traps: City Council agenda documents page is not a WDB source. Richmond has multiple WDB-related pages.
- Automation rule: use `richmond_wdb`; parse only the `Agenda & Minutes` section and merge exact dates from the official schedule fallback.

### Riverside County WDB

- Official full-board source: `https://rivcoworkforce.org/workforce-development-board`
- Official executive source: `https://rivcoworkforce.org/executive-committee`
- Current structure: full board and executive committee pages have separate 2026 schedule tables and agenda archives.
- Cadence observed on 2026-05-10: full-board dates listed February 25, canceled April 15, August 12, and December 9; executive dates listed February 25, May 7, June 17, August 12, October 7, and December 9.
- Known traps: old `www.rivcoworkforce.com` has a certificate mismatch. Riverside County Works and regional committees are separate. Current official pages returned HTTP 403 to the automation during validation.
- Automation rule: `riverside_wdb_schedule` is implemented, but the source remains medium until the daily runner can fetch the official pages.

### San Benito County WDB

- Official board source: `https://sbcjobs.org/about/`
- Official agenda source: `https://sbcjobs.org/meeting-packets/`
- Current structure: WDB board page describes the board; agenda/minutes page uses iframes for 2025-2023 and visible older 2021 links.
- Cadence observed on 2026-05-10: no current 2026 meeting schedule confirmed.
- Known traps: old `sbcworkforce.org` does not resolve. iframe content needs embedded-source parsing.
- Automation rule: keep as medium confidence until current schedule or iframe agenda content is parsed.

### San Bernardino County WDB

- Official source: `https://workforce.sbcounty.gov/about/board-agenda/`
- Current structure: Board Agenda page shows current agenda information and links PDF agendas.
- Cadence observed on 2026-05-10: February 18, 2026 Finance Committee at 8:30 AM and General Board Meeting at 9:30 AM were visible; no future post-May 9 row was visible.
- Known traps: old `wp.sbcounty.gov/workforce` URL returns 410 Gone. Finance Committee appears on the same page as General Board Meeting.
- Automation rule: `no_publish` until a future full-board/executive source is visible.

### San Diego Workforce Partnership

- Official source: `https://workforce.org/boards/workforce-development-board/agendas-minutes/`
- Current structure: WDB Agendas & Minutes page has an `Upcoming Meetings` section for 2026 with alternating Executive Committee and Board Meeting rows.
- Cadence observed on 2026-05-10: future rows after May 9 include May 14 Board; June 1 Executive; June 11 Board; August 31 Executive; September 10 Board; September 28 Executive; October 8 Board; November 2 Executive; November 12 Board; November 30 Executive; December 10 Board.
- Known traps: San Diego Consortium Policy Board and Audit Committee are separate bodies. A same-date Audit Committee PDF must never be attached to an Executive Committee meeting.
- Automation rule: `san_diego_wdb` parses only the Upcoming Meetings WDB/Executive rows and type-matches agenda files as well as matching their dates.

### San Francisco OEWD / WISF

- Official source: `https://www.sf.gov/departments--workforce-investment-san-francisco-wisf-board`
- Current structure: SF.gov WISF page has a calendar widget and detail pages for meetings.
- Cadence observed on 2026-05-10: page says board and executive committee meetings occur quarterly; visible calendar items were 2025 meetings.
- Known traps: old `oewd.org` redirects with 308. Generic parsing produced false future rows from SF.gov calendar fragments.
- Automation rule: `no_publish` until current 2026 WISF meeting detail pages are confirmed.

### San Joaquin County WorkNet

- Official source: `https://sjcworknet.org/boards/wdb`
- Current structure: the replacement Next.js WDB page uses a board-specific `/api/agendas` endpoint. Each record carries the meeting date/time/location, cancellation status, and agenda attachment.
- Cadence observed on 2026-05-10: February 25, canceled March 25, May 27, July 22, August 26, October 28, and combined November/December meeting on December 16, 2026.
- Known traps: WorkNet homepage and STEP application packet are not WDB meeting sources.
- Automation rule: use `san_joaquin_worknet`; query board ID `cmp323sd50001ict5fpgb619o`, skip canceled/deleted records, and merge API details into the confirmed schedule fallbacks.

### Santa Ana WDB

- Official source: `https://www.santa-ana.org/events/category/public-meetings/`
- Current structure: official Public Meetings event pages publish WDB dates, times, locations, and agenda links when posted.
- 2026 schedule verified on 2026-06-11: July 16, September 17, and November 19 from 8:00 to 9:30 AM at the WORK Center.
- Known traps: Travel Santa Ana and Santa Ana Regional Water Quality Control Board are unrelated false positives.
- Automation rule: publish only exact Workforce Development Board event titles from the official Public Meetings category.

### Santa Barbara County WDB

- Official board source: `https://www.countyofsb.org/611/Workforce-Development-Board`
- Official agenda archive: `https://www.countyofsb.org/3033/Board-Agendas`
- Current structure: county WDB pages use CivicPlus HCMS agenda widgets for Board and Executive Committee records and PDF assets.
- 2026 records verified on 2026-06-11: Full Board March 20; Executive Committee January 21 and May 20. Future rows appear when the HCMS record is published.
- Known traps: old `/wdb` shortcut returns Page Not Found. BSCC Santa Barbara board agenda is unrelated.
- Automation rule: query the public HCMS tags for Full Board and Executive Committee; attach only the PDF belonging to the same record.

### Solano County WDB

- Official source: `https://www.wdbsolano.com/board-of-directors/`
- Current structure: the active WDB Solano page publishes agenda packets and a separate annual Meeting Calendar PDF.
- 2026 schedule verified on 2026-06-10: January 23, March 20, May 15, July 17, September 18, and November 20 from 8:30 to 10:30 AM at 500 Chadbourne Road, Suite A, Fairfield.
- Known traps: old Solano county and `solanowdb.org` pages can outrank the active WDB Solano source in search results.
- Automation rule: parse the annual calendar PDF for dates and match packet PDFs by exact date.

### Sonoma County WDB

- Official source: `https://joblinksonoma.org/board-meetings/`
- Current structure: Job Link Sonoma publishes Workforce Investment Board and Executive Committee event rows plus agenda packets.
- Cadence observed on 2026-06-10: future rows include separate board and executive dates/times at Job Link Office, 2227 Capricorn Way, Santa Rosa.
- Known traps: the old `sonomawdb.org` domain is dead, and other Job Link committees share the page.
- Automation rule: publish only Workforce Investment Board and WIB Executive Committee rows and match agenda packets by date.

### Ventura County WDB

- Official source: `https://workforce.venturacounty.gov/`
- Agenda/packet source: `https://workforce.venturacounty.gov/resources/meeting-packets/`
- Machine-readable schedule: `https://calendar.google.com/calendar/ical/venturacountywdb%40gmail.com/public/basic.ics`
- Current structure: the official meeting page embeds a public Google Calendar. Its published ICS feed carries exact dates, times, locations, cancellations, descriptions, and packet URLs.
- Dates verified on 2026-09-24: Oct. 8 and Dec. 3, 2026 full board; Jan. 14 and Mar. 18, 2027 executive; Feb. 18, 2027 full board. The Oct. 8, 2026 executive meeting is canceled and excluded.
- Known traps: old `vcwdb.org` does not resolve. Legacy `workforceventuracounty.org` pages exist; prefer `workforce.venturacounty.gov`.
- Automation rule: use `ventura_google_calendar_ics`; publish only full-board and executive titles, skip cancellations, and extract packet/location/virtual data from each event. The narrowly recognized public ICS subscription endpoint is treated as an explicit machine feed, not a crawlable UI page.

### Verdugo WDB

- Official source: `https://verdugoworks.com/board/`
- Current structure: Verdugo Works board page has Board Meeting Packets.
- Cadence observed on 2026-05-10: visible packet dates include February 14, 2025; April 9, 2025; May 21/June 25, 2025; and March 11, 2026. No future post-May 9 2026 meeting confirmed.
- Known traps: old `verdugowdb.org` does not resolve. Sparse packet dates should not be projected forward.
- Automation rule: `no_publish` until future schedule is confirmed.

### Yolo County WDB

- Official source: `https://www.yoloworks.org/`
- Current structure: Yoloworks and the user-supplied VOS document endpoint are blocked by robots.txt for the automation.
- Cadence confirmed from an official Yolo County release on 2026-09-24: in-person meetings are bimonthly on the second Wednesday from 8:30 to 10:30 AM at HHSA, 25 North Cottonwood Street, Woodland.
- Known traps: robots.txt disallows fetching the current source.
- Automation rule: `no_publish` until a robots-compliant alternate source is found.

## Remaining Audit Queue

All source-registry boards have a first-pass profile, but coverage is not complete. The daily `coverage_matrix.md` is authoritative for the active queue.

- No confirmed usable meeting notice: Kings County and Yolo County.
- Automation-blocked official sources: Kern/Inyo/Mono, Kings, Los Angeles County, Riverside, and Yolo.
- Yolo cadence is independently confirmed by an official 2026 county release as in-person, bimonthly, second Wednesday, 8:30-10:30 AM, but cadence must not be converted into calendar events without a specific notice.
- Kings has old evidence of first-Thursday/every-other-month meetings, but no current 2026 notice or schedule has been located.
- Ventura is resolved through the public ICS feed embedded in its official meeting page.

## Persistence And Agenda Matching Rules

- Confirmed future meetings are stored in `active_meetings.json`, committed by the daily workflow, and retained through temporary fetch failures or page-listing changes until the meeting date passes.
- A missing row is not treated as a cancellation. Removal requires explicit official cancellation evidence or a reviewed correction.
- Official dates already verified on pages that are now blocked or missing can be recorded as structured `confirmed_meetings` fallbacks in the source profile, with the original source URL and verification note.
- Agenda links with an explicit date that conflicts with the meeting date are rejected even when they appear in the same HTML row. Generic filenames are accepted only from the exact meeting row/detail record.
- Agenda emails are content-hash deduplicated. A first appearance sends an `Agenda available` email; a changed file sends an `Agenda updated` email.
