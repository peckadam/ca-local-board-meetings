# Local Board Meeting Monitor Progress Log

## 2026-05-09T00:03:57.763240+00:00 (dry-run)

- Boards checked: 45
- Meetings found: 9
- Missing agendas within 72 hours: 0
- Failures requiring human review: 22
- Review: Foothill WDB - https://www.foothillwdb.org/ - DNS resolution failed during validation.
- Review: Fresno Regional WDB - https://www.fresno-ca-wdb.com/ - DNS resolution failed during validation.
- Review: Humboldt County WDB - https://humboldtgov.org/1709/Workforce-Development-Board - HTTP 404; registry URL likely changed.
- Review: Kern/Inyo/Mono WDB - https://www.kern-inyo-mono.org/ - DNS resolution failed during validation.
- Review: Kings County WDB - https://kingsworkforce.org/ - HTTP 403; may need browser/manual verification.
- Review: Long Beach WIN - https://www.longbeach.gov/economicdevelopment/workforce-development/ - redirect loop in urllib fetcher.
- Review: Los Angeles City WDB - https://ewddlacity.com/index.php/wdb - HTTP 404; registry URL likely changed.
- Review: Los Angeles County WDB - https://wdb.lacounty.gov/ - DNS resolution failed during validation.
- Review: Merced County WDB - http://www.workforce-merced.com/ - DNS resolution failed during validation.
- Review: Monterey County WDB - https://www.montereycountywdb.org/ - request timed out.
- Review: North Central Counties (NCCC) - https://ncccwdb.org/ - DNS resolution failed during validation.
- Review: Oakland WDB - https://www.oaklandworkforce.org/ - DNS resolution failed during validation.
- Review: Riverside County WDB - https://www.rivcoworkforce.com/ - certificate hostname mismatch.
- Review: San Benito County WDB - https://sbcworkforce.org/ - DNS resolution failed during validation.
- Review: San Bernardino County WDB - https://wp.sbcounty.gov/workforce/ - HTTP 410; registry URL likely changed.
- Review: San Diego Workforce Partnership - https://workforce.org/ - HTTP 403; may need browser/manual verification.
- Review: San Francisco OEWD - https://oewd.org/ - HTTP 308 redirect not followed by urllib.
- Review: Solano County WDB - https://www.solanowdb.org/ - certificate hostname mismatch.
- Review: Sonoma County WDB - https://sonomawdb.org/ - DNS resolution failed during validation.
- Review: Ventura County WDB - https://vcwdb.org/ - DNS resolution failed during validation.
- Review: Verdugo WDB - https://www.verdugowdb.org/ - DNS resolution failed during validation.
- Review: Yolo County WDB - https://www.yoloworks.org/ - robots.txt disallows fetch.

Live smoke test is blocked until Microsoft Graph credentials are present in the environment.
## 2026-05-09T21:30:00.944530+00:00 (dry-run)

- Boards checked: 5
- Meetings found: 0
- Missing agendas within 72 hours: 0
- Failures requiring human review: 2
- Review: Foothill WDB - https://www.foothillwdb.org/ - <urlopen error [Errno 8] nodename nor servname provided, or not known>
- Review: Fresno Regional WDB - https://www.fresno-ca-wdb.com/ - <urlopen error [Errno 8] nodename nor servname provided, or not known>

## 2026-05-09T22:15:18.117066+00:00 (dry-run)

- Boards checked: 45
- Meetings found: 46
- Missing agendas within 72 hours: 3
- Failures requiring human review: 23
- Review: Foothill WDB - https://www.foothillwdb.org/ - <urlopen error [Errno 8] nodename nor servname provided, or not known>
- Review: Fresno Regional WDB - https://www.fresno-ca-wdb.com/ - <urlopen error [Errno 8] nodename nor servname provided, or not known>
- Review: Humboldt County WDB - https://humboldtgov.org/1709/Workforce-Development-Board - HTTP Error 404: Not Found
- Review: Kern/Inyo/Mono WDB - https://www.kern-inyo-mono.org/ - <urlopen error [Errno 8] nodename nor servname provided, or not known>
- Review: Kings County WDB - https://kingsworkforce.org/ - HTTP Error 403: Forbidden
- Review: Long Beach WIN - https://www.longbeach.gov/economicdevelopment/workforce-development/ - HTTP Error 301: The HTTP server returned a redirect error that would lead to an infinite loop.
The last 30x error message was:
Moved Permanently
- Review: Los Angeles City WDB - https://ewddlacity.com/index.php/wdb - HTTP Error 404: Not Found
- Review: Los Angeles County WDB - https://wdb.lacounty.gov/ - <urlopen error [Errno 8] nodename nor servname provided, or not known>
- Review: Merced County WDB - http://www.workforce-merced.com/ - <urlopen error [Errno 8] nodename nor servname provided, or not known>
- Review: Monterey County WDB - https://www.montereycountywdb.org/ - <urlopen error timed out>
- Review: North Central Counties (NCCC) - https://ncccwdb.org/ - <urlopen error [Errno 8] nodename nor servname provided, or not known>
- Review: Oakland WDB - https://www.oaklandworkforce.org/ - <urlopen error [Errno 8] nodename nor servname provided, or not known>
- Review: Riverside County WDB - https://www.rivcoworkforce.com/ - <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: Hostname mismatch, certificate is not valid for 'www.rivcoworkforce.com'. (_ssl.c:1129)>
- Review: San Benito County WDB - https://sbcworkforce.org/ - <urlopen error [Errno 8] nodename nor servname provided, or not known>
- Review: San Bernardino County WDB - https://wp.sbcounty.gov/workforce/ - HTTP Error 410: Gone
- Review: San Diego Workforce Partnership - https://workforce.org/ - HTTP Error 403: Forbidden
- Review: San Francisco OEWD - https://oewd.org/ - HTTP Error 308: Permanent Redirect
- Review: San Joaquin County WorkNet - https://www.sjcworknet.org/pdfs/STEP Application Packet 1-6-26.pdf - URL can't contain control characters. '/pdfs/STEP Application Packet 1-6-26.pdf' (found at least ' ')
- Review: Solano County WDB - https://www.solanowdb.org/ - <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: Hostname mismatch, certificate is not valid for 'www.solanowdb.org'. (_ssl.c:1129)>
- Review: Sonoma County WDB - https://sonomawdb.org/ - <urlopen error [Errno 8] nodename nor servname provided, or not known>

## 2026-05-09T22:36:09.683588+00:00 (dry-run)

- Boards checked: 1
- Meetings found: 4
- Missing agendas within 72 hours: 0
- Failures requiring human review: 0

## 2026-05-09T22:51:27.135106+00:00 (dry-run)

- Boards checked: 1
- Meetings found: 2
- Missing agendas within 72 hours: 0
- Failures requiring human review: 0

## 2026-05-09T22:59:27.480377+00:00 (dry-run)

- Boards checked: 1
- Meetings found: 5
- Missing agendas within 72 hours: 0
- Failures requiring human review: 0

## 2026-05-09T23:10:49.894266+00:00 (dry-run)

- Boards checked: 1
- Meetings found: 1
- Missing agendas within 72 hours: 0
- Failures requiring human review: 0

## 2026-05-09T23:11:26.590848+00:00 (dry-run)

- Boards checked: 1
- Meetings found: 1
- Missing agendas within 72 hours: 0
- Failures requiring human review: 0

## 2026-05-09T23:24:57.309595+00:00 (dry-run)

- Boards checked: 4
- Meetings found: 3
- Missing agendas within 72 hours: 0
- Failures requiring human review: 0

## 2026-05-10T00:01:55.138902+00:00 (dry-run)

- Boards checked: 3
- Meetings found: 4
- Missing agendas within 72 hours: 0
- Failures requiring human review: 0

## 2026-05-10T00:30:30.008298+00:00 (dry-run)

- Boards checked: 7
- Meetings found: 2
- Missing agendas within 72 hours: 0
- Failures requiring human review: 0

## 2026-05-10T00:31:23.350589+00:00 (dry-run)

- Boards checked: 7
- Meetings found: 2
- Missing agendas within 72 hours: 0
- Failures requiring human review: 0

## 2026-05-10T00:32:48.982803+00:00 (dry-run)

- Boards checked: 7
- Meetings found: 2
- Missing agendas within 72 hours: 0
- Failures requiring human review: 0

## 2026-05-10T01:20:53.617399+00:00 (dry-run)

- Boards checked: 5
- Meetings found: 15
- Missing agendas within 72 hours: 1
- Failures requiring human review: 0

## 2026-05-10T01:53:05.075439+00:00 (dry-run)

- Boards checked: 5
- Meetings found: 1
- Missing agendas within 72 hours: 0
- Failures requiring human review: 0

## 2026-05-10T01:54:39.112005+00:00 (dry-run)

- Boards checked: 5
- Meetings found: 2
- Missing agendas within 72 hours: 0
- Failures requiring human review: 0

## 2026-05-10T02:10:20.176088+00:00 (dry-run)

- Boards checked: 6
- Meetings found: 5
- Missing agendas within 72 hours: 0
- Failures requiring human review: 5
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/full-wdb-board - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/executive-committee - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/about-the-board - HTTP Error 403: Forbidden
- Review: Kings County WDB - https://www.countyofkingsca.gov/departments/board-of-supervisors/boards-commissions/workforce-development-board - HTTP Error 403: Forbidden
- Review: Los Angeles County WDB - https://www.ajcc.lacounty.gov/wdb - HTTP Error 403: Forbidden

## 2026-05-10T02:12:25.257401+00:00 (dry-run)

- Boards checked: 6
- Meetings found: 0
- Missing agendas within 72 hours: 0
- Failures requiring human review: 6
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/full-wdb-board - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/executive-committee - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/about-the-board - HTTP Error 403: Forbidden
- Review: Kings County WDB - https://www.countyofkingsca.gov/departments/board-of-supervisors/boards-commissions/workforce-development-board - HTTP Error 403: Forbidden
- Review: Los Angeles County WDB - https://www.ajcc.lacounty.gov/wdb - HTTP Error 403: Forbidden
- Review: Merced County WDB - https://worknetmerced.com/assets/pdf/WDB-Executive-Mtg-Agenda 1-27-25.pdf - URL can't contain control characters. '/assets/pdf/WDB-Executive-Mtg-Agenda 1-27-25.pdf' (found at least ' ')

## 2026-05-10T02:13:38.924376+00:00 (dry-run)

- Boards checked: 6
- Meetings found: 4
- Missing agendas within 72 hours: 0
- Failures requiring human review: 5
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/full-wdb-board - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/executive-committee - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/about-the-board - HTTP Error 403: Forbidden
- Review: Kings County WDB - https://www.countyofkingsca.gov/departments/board-of-supervisors/boards-commissions/workforce-development-board - HTTP Error 403: Forbidden
- Review: Los Angeles County WDB - https://www.ajcc.lacounty.gov/wdb - HTTP Error 403: Forbidden

## 2026-05-10T02:14:09.068162+00:00 (dry-run)

- Boards checked: 6
- Meetings found: 4
- Missing agendas within 72 hours: 0
- Failures requiring human review: 5
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/full-wdb-board - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/executive-committee - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/about-the-board - HTTP Error 403: Forbidden
- Review: Kings County WDB - https://www.countyofkingsca.gov/departments/board-of-supervisors/boards-commissions/workforce-development-board - HTTP Error 403: Forbidden
- Review: Los Angeles County WDB - https://www.ajcc.lacounty.gov/wdb - HTTP Error 403: Forbidden

## 2026-05-10T02:22:25.403836+00:00 (dry-run)

- Boards checked: 6
- Meetings found: 4
- Missing agendas within 72 hours: 0
- Failures requiring human review: 2
- Review: Riverside County WDB - https://rivcoworkforce.org/workforce-development-board - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/executive-committee - HTTP Error 403: Forbidden

## 2026-05-10T02:33:03.743618+00:00 (dry-run)

- Boards checked: 6
- Meetings found: 11
- Missing agendas within 72 hours: 0
- Failures requiring human review: 1
- Review: San Diego Workforce Partnership - https://workforce.org/boards/workforce-development-board/agendas-minutes/ - HTTP Error 403: Forbidden

## 2026-05-10T02:41:42.564068+00:00 (dry-run)

- Boards checked: 6
- Meetings found: 4
- Missing agendas within 72 hours: 0
- Failures requiring human review: 1
- Review: San Diego Workforce Partnership - https://workforce.org/boards/workforce-development-board/agendas-minutes/ - HTTP Error 403: Forbidden

## 2026-05-10T02:55:47.192152+00:00 (dry-run)

- Boards checked: 5
- Meetings found: 0
- Missing agendas within 72 hours: 0
- Failures requiring human review: 2
- Review: Sonoma County WDB - https://sonomawdb.org/ - <urlopen error [Errno 8] nodename nor servname provided, or not known>
- Review: Yolo County WDB - https://www.yoloworks.org/ - robots.txt disallows fetching https://www.yoloworks.org/

## 2026-05-10T14:37:35.312326+00:00 (dry-run)

- Boards checked: 45
- Meetings found: 30
- Missing agendas within 72 hours: 0
- Failures requiring human review: 10
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/full-wdb-board - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/executive-committee - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/about-the-board - HTTP Error 403: Forbidden
- Review: Kings County WDB - https://www.countyofkingsca.gov/departments/board-of-supervisors/boards-commissions/workforce-development-board - HTTP Error 403: Forbidden
- Review: Los Angeles County WDB - https://www.ajcc.lacounty.gov/wdb - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/workforce-development-board - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/executive-committee - HTTP Error 403: Forbidden
- Review: San Diego Workforce Partnership - https://workforce.org/boards/workforce-development-board/agendas-minutes/ - HTTP Error 403: Forbidden
- Review: Sonoma County WDB - https://sonomawdb.org/ - <urlopen error [Errno 8] nodename nor servname provided, or not known>
- Review: Yolo County WDB - https://www.yoloworks.org/ - robots.txt disallows fetching https://www.yoloworks.org/

## 2026-05-10T14:41:27.340394+00:00 (dry-run)

- Boards checked: 45
- Meetings found: 27
- Missing agendas within 72 hours: 0
- Failures requiring human review: 10
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/full-wdb-board - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/executive-committee - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/about-the-board - HTTP Error 403: Forbidden
- Review: Kings County WDB - https://www.countyofkingsca.gov/departments/board-of-supervisors/boards-commissions/workforce-development-board - HTTP Error 403: Forbidden
- Review: Los Angeles County WDB - https://www.ajcc.lacounty.gov/wdb - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/workforce-development-board - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/executive-committee - HTTP Error 403: Forbidden
- Review: San Diego Workforce Partnership - https://workforce.org/boards/workforce-development-board/agendas-minutes/ - HTTP Error 403: Forbidden
- Review: Sonoma County WDB - https://sonomawdb.org/ - <urlopen error [Errno 8] nodename nor servname provided, or not known>
- Review: Yolo County WDB - https://www.yoloworks.org/ - robots.txt disallows fetching https://www.yoloworks.org/

## 2026-05-10T16:57:21.747899+00:00 (dry-run)

- Boards checked: 45
- Meetings found: 27
- Missing agendas within 72 hours: 0
- Failures requiring human review: 10
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/full-wdb-board - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/executive-committee - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/about-the-board - HTTP Error 403: Forbidden
- Review: Kings County WDB - https://www.countyofkingsca.gov/departments/board-of-supervisors/boards-commissions/workforce-development-board - HTTP Error 403: Forbidden
- Review: Los Angeles County WDB - https://www.ajcc.lacounty.gov/wdb - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/workforce-development-board - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/executive-committee - HTTP Error 403: Forbidden
- Review: San Diego Workforce Partnership - https://workforce.org/boards/workforce-development-board/agendas-minutes/ - HTTP Error 403: Forbidden
- Review: Sonoma County WDB - https://sonomawdb.org/ - <urlopen error [Errno 8] nodename nor servname provided, or not known>
- Review: Yolo County WDB - https://www.yoloworks.org/ - robots.txt disallows fetching https://www.yoloworks.org/

## 2026-05-10T16:59:36.784477+00:00 (dry-run)

- Boards checked: 45
- Meetings found: 27
- Missing agendas within 72 hours: 0
- Failures requiring human review: 10
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/full-wdb-board - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/executive-committee - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/about-the-board - HTTP Error 403: Forbidden
- Review: Kings County WDB - https://www.countyofkingsca.gov/departments/board-of-supervisors/boards-commissions/workforce-development-board - HTTP Error 403: Forbidden
- Review: Los Angeles County WDB - https://www.ajcc.lacounty.gov/wdb - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/workforce-development-board - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/executive-committee - HTTP Error 403: Forbidden
- Review: San Diego Workforce Partnership - https://workforce.org/boards/workforce-development-board/agendas-minutes/ - HTTP Error 403: Forbidden
- Review: Sonoma County WDB - https://sonomawdb.org/ - <urlopen error [Errno 8] nodename nor servname provided, or not known>
- Review: Yolo County WDB - https://www.yoloworks.org/ - robots.txt disallows fetching https://www.yoloworks.org/

## 2026-05-20T14:12:53.785589+00:00 (dry-run)

- Boards checked: 45
- Meetings found: 38
- Missing agendas within 72 hours: 5
- Failures requiring human review: 9
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/full-wdb-board - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/executive-committee - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/about-the-board - HTTP Error 403: Forbidden
- Review: Kings County WDB - https://www.countyofkingsca.gov/departments/board-of-supervisors/boards-commissions/workforce-development-board - HTTP Error 403: Forbidden
- Review: Los Angeles County WDB - https://www.ajcc.lacounty.gov/wdb - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/workforce-development-board - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/executive-committee - HTTP Error 403: Forbidden
- Review: Sonoma County WDB - https://sonomawdb.org/ - <urlopen error [Errno -2] Name or service not known>
- Review: Yolo County WDB - https://www.yoloworks.org/ - robots.txt disallows fetching https://www.yoloworks.org/

## 2026-05-20T14:26:55.636115+00:00 (dry-run)

- Boards checked: 45
- Meetings found: 38
- Missing agendas within 72 hours: 5
- Failures requiring human review: 10
- Review: Foothill WDB - https://fwdbworks.org/events/ - The read operation timed out
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/full-wdb-board - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/executive-committee - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/about-the-board - HTTP Error 403: Forbidden
- Review: Kings County WDB - https://www.countyofkingsca.gov/departments/board-of-supervisors/boards-commissions/workforce-development-board - HTTP Error 403: Forbidden
- Review: Los Angeles County WDB - https://www.ajcc.lacounty.gov/wdb - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/workforce-development-board - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/executive-committee - HTTP Error 403: Forbidden
- Review: Sonoma County WDB - https://sonomawdb.org/ - <urlopen error [Errno 8] nodename nor servname provided, or not known>
- Review: Yolo County WDB - https://www.yoloworks.org/ - robots.txt disallows fetching https://www.yoloworks.org/

## 2026-06-10T22:01:01.957670+00:00 (dry-run)

- Boards checked: 45
- Meetings found: 33
- Missing agendas within 72 hours: 3
- Failures requiring human review: 9
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/full-wdb-board - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/executive-committee - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/about-the-board - HTTP Error 403: Forbidden
- Review: Kings County WDB - https://www.countyofkingsca.gov/departments/board-of-supervisors/boards-commissions/workforce-development-board - HTTP Error 403: Forbidden
- Review: Los Angeles County WDB - https://www.ajcc.lacounty.gov/wdb - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/workforce-development-board - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/executive-committee - HTTP Error 403: Forbidden
- Review: Sonoma County WDB - https://sonomawdb.org/ - <urlopen error [Errno 8] nodename nor servname provided, or not known>
- Review: Yolo County WDB - https://www.yoloworks.org/ - robots.txt disallows fetching https://www.yoloworks.org/

## 2026-06-10T22:11:06.888834+00:00 (dry-run)

- Boards checked: 3
- Meetings found: 11
- Missing agendas within 72 hours: 0
- Failures requiring human review: 0

## 2026-06-10T22:12:22.971977+00:00 (dry-run)

- Boards checked: 45
- Meetings found: 30
- Missing agendas within 72 hours: 0
- Failures requiring human review: 10
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/full-wdb-board - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/executive-committee - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/about-the-board - HTTP Error 403: Forbidden
- Review: Kings County WDB - https://www.countyofkingsca.gov/departments/board-of-supervisors/boards-commissions/workforce-development-board - HTTP Error 403: Forbidden
- Review: Los Angeles County WDB - https://www.ajcc.lacounty.gov/wdb - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/workforce-development-board - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/executive-committee - HTTP Error 403: Forbidden
- Review: SELACO WDB - https://www.selacowdb.com/wp-content/uploads/April-23-2024-Executive-Committee-Meeting.pdf - The read operation timed out
- Review: Sonoma County WDB - https://sonomawdb.org/ - <urlopen error [Errno 8] nodename nor servname provided, or not known>
- Review: Yolo County WDB - https://www.yoloworks.org/ - robots.txt disallows fetching https://www.yoloworks.org/

## 2026-06-10T23:42:22.313001+00:00 (dry-run)

- Boards checked: 45
- Meetings found: 30
- Missing agendas within 72 hours: 0
- Failures requiring human review: 9
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/full-wdb-board - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/executive-committee - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/about-the-board - HTTP Error 403: Forbidden
- Review: Kings County WDB - https://www.countyofkingsca.gov/departments/board-of-supervisors/boards-commissions/workforce-development-board - HTTP Error 403: Forbidden
- Review: Los Angeles County WDB - https://www.ajcc.lacounty.gov/wdb - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/workforce-development-board - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/executive-committee - HTTP Error 403: Forbidden
- Review: Sonoma County WDB - https://sonomawdb.org/ - <urlopen error [Errno 8] nodename nor servname provided, or not known>
- Review: Yolo County WDB - https://www.yoloworks.org/ - robots.txt disallows fetching https://www.yoloworks.org/

## 2026-06-10T23:54:28.237999+00:00 (dry-run)

- Boards checked: 3
- Meetings found: 7
- Missing agendas within 72 hours: 0
- Failures requiring human review: 0

## 2026-06-10T23:55:02.255955+00:00 (dry-run)

- Boards checked: 3
- Meetings found: 7
- Missing agendas within 72 hours: 0
- Failures requiring human review: 0

## 2026-06-10T23:55:21.781883+00:00 (dry-run)

- Boards checked: 45
- Meetings found: 37
- Missing agendas within 72 hours: 0
- Failures requiring human review: 8
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/full-wdb-board - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/executive-committee - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/about-the-board - HTTP Error 403: Forbidden
- Review: Kings County WDB - https://www.countyofkingsca.gov/departments/board-of-supervisors/boards-commissions/workforce-development-board - HTTP Error 403: Forbidden
- Review: Los Angeles County WDB - https://www.ajcc.lacounty.gov/wdb - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/workforce-development-board - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/executive-committee - HTTP Error 403: Forbidden
- Review: Yolo County WDB - https://www.yoloworks.org/ - robots.txt disallows fetching https://www.yoloworks.org/

## 2026-06-11T00:03:49.847320+00:00 (dry-run)

- Boards checked: 45
- Meetings found: 38
- Missing agendas within 72 hours: 0
- Failures requiring human review: 8
- Assessment: `data/local_board_meetings/audits/agenda_process_effectiveness_20260610.md`
- Recovered sources/parsers in this pass: Sonoma Job Link Board Meetings, Solano WDB Board of Directors calendar PDF, Madera current WDB meeting archives, Santa Clara/work2future event-card detail pages.
- Current future/today calendar coverage: 32 events across 14 boards; 8 agenda links, 14 locations, and 3 virtual links attached.
- Remaining source blockers: Kern/Inyo/Mono 403, Kings 403, Los Angeles County 403, Riverside 403, and Yolo robots.txt.

## 2026-06-11T00:02:35.097306+00:00 (dry-run)

- Boards checked: 1
- Meetings found: 1
- Missing agendas within 72 hours: 0
- Failures requiring human review: 0

## 2026-06-11T00:03:29.373163+00:00 (dry-run)

- Boards checked: 1
- Meetings found: 1
- Missing agendas within 72 hours: 0
- Failures requiring human review: 0

## 2026-06-11T00:03:49.847320+00:00 (dry-run)

- Boards checked: 45
- Meetings found: 38
- Missing agendas within 72 hours: 0
- Failures requiring human review: 8
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/full-wdb-board - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/executive-committee - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/about-the-board - HTTP Error 403: Forbidden
- Review: Kings County WDB - https://www.countyofkingsca.gov/departments/board-of-supervisors/boards-commissions/workforce-development-board - HTTP Error 403: Forbidden
- Review: Los Angeles County WDB - https://www.ajcc.lacounty.gov/wdb - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/workforce-development-board - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/executive-committee - HTTP Error 403: Forbidden
- Review: Yolo County WDB - https://www.yoloworks.org/ - robots.txt disallows fetching https://www.yoloworks.org/
## 2026-06-10T17:09:04.052357-07:00 (dry-run)

- Boards checked: 3
- Meetings found: 6
- Missing agendas within 72 hours: 0
- Failures requiring human review: 0

## 2026-06-10T17:09:35.744988-07:00 (dry-run)

- Boards checked: 45
- Meetings found: 38
- Missing agendas within 72 hours: 0
- Failures requiring human review: 8
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/full-wdb-board - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/executive-committee - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/about-the-board - HTTP Error 403: Forbidden
- Review: Kings County WDB - https://www.countyofkingsca.gov/departments/board-of-supervisors/boards-commissions/workforce-development-board - HTTP Error 403: Forbidden
- Review: Los Angeles County WDB - https://www.ajcc.lacounty.gov/wdb - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/workforce-development-board - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/executive-committee - HTTP Error 403: Forbidden
- Review: Yolo County WDB - https://www.yoloworks.org/ - robots.txt disallows fetching https://www.yoloworks.org/

## 2026-06-11T13:25:59.764191-07:00 (dry-run)

- Boards checked: 9
- Meetings found: 16
- Missing agendas within 72 hours: 0
- Failures requiring human review: 6
- Review: Fresno Regional WDB - https://www.google.com/calendar/event?action=TEMPLATE&dates=20260909T160000/20260909T173000&text=FRWDB%20Meeting&details=This+agenda+for+this+meeting+is+not+yet+available.&location=AJCC%20Comprehensive&trp=false&ctz=America/Los_Angeles&sprop=website:https://frwdb.net - Agenda location enrichment failed: robots.txt disallows fetching https://www.google.com/calendar/event?action=TEMPLATE&dates=20260909T160000/20260909T173000&text=FRWDB%20Meeting&details=This+agenda+for+this+meeting+is+not+yet+available.&location=AJCC%20Comprehensive&trp=false&ctz=America/Los_Angeles&sprop=website:https://frwdb.net
- Review: Fresno Regional WDB - https://www.google.com/calendar/event?action=TEMPLATE&dates=20261202T160000/20261202T173000&text=FRWDB%20Meeting&details=This+agenda+for+this+meeting+is+not+yet+available.&location=AJCC%20Comprehensive&trp=false&ctz=America/Los_Angeles&sprop=website:https://frwdb.net - Agenda location enrichment failed: robots.txt disallows fetching https://www.google.com/calendar/event?action=TEMPLATE&dates=20261202T160000/20261202T173000&text=FRWDB%20Meeting&details=This+agenda+for+this+meeting+is+not+yet+available.&location=AJCC%20Comprehensive&trp=false&ctz=America/Los_Angeles&sprop=website:https://frwdb.net
- Review: Fresno Regional WDB - https://www.google.com/calendar/event?action=TEMPLATE&dates=20260715T150000/20260715T170000&text=Executive%20Committee%20Meeting&details=This+agenda+for+this+meeting+is+not+yet+available.&location=AJCC%20Comprehensive&trp=false&ctz=America/Los_Angeles&sprop=website:https://frwdb.net - Agenda location enrichment failed: robots.txt disallows fetching https://www.google.com/calendar/event?action=TEMPLATE&dates=20260715T150000/20260715T170000&text=Executive%20Committee%20Meeting&details=This+agenda+for+this+meeting+is+not+yet+available.&location=AJCC%20Comprehensive&trp=false&ctz=America/Los_Angeles&sprop=website:https://frwdb.net
- Review: Fresno Regional WDB - https://www.google.com/calendar/event?action=TEMPLATE&dates=20261021T150000/20261021T170000&text=Executive%20Committee%20Meeting&details=This+agenda+for+this+meeting+is+not+yet+available.&location=AJCC%20Comprehensive&trp=false&ctz=America/Los_Angeles&sprop=website:https://frwdb.net - Agenda location enrichment failed: robots.txt disallows fetching https://www.google.com/calendar/event?action=TEMPLATE&dates=20261021T150000/20261021T170000&text=Executive%20Committee%20Meeting&details=This+agenda+for+this+meeting+is+not+yet+available.&location=AJCC%20Comprehensive&trp=false&ctz=America/Los_Angeles&sprop=website:https://frwdb.net
- Review: Kings County WDB - https://www.countyofkingsca.gov/departments/board-of-supervisors/boards-commissions/workforce-development-board - HTTP Error 403: Forbidden
- Review: Yolo County WDB - https://www.yoloworks.org/ - robots.txt disallows fetching https://www.yoloworks.org/

## 2026-06-11T13:27:34.179457-07:00 (dry-run)

- Boards checked: 9
- Meetings found: 16
- Missing agendas within 72 hours: 0
- Failures requiring human review: 2
- Review: Kings County WDB - https://www.countyofkingsca.gov/departments/board-of-supervisors/boards-commissions/workforce-development-board - HTTP Error 403: Forbidden
- Review: Yolo County WDB - https://www.yoloworks.org/ - robots.txt disallows fetching https://www.yoloworks.org/

## 2026-06-11T13:30:02.228444-07:00 (dry-run)

- Boards checked: 45
- Meetings found: 51
- Missing agendas within 72 hours: 0
- Failures requiring human review: 8
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/full-wdb-board - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/executive-committee - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/about-the-board - HTTP Error 403: Forbidden
- Review: Kings County WDB - https://www.countyofkingsca.gov/departments/board-of-supervisors/boards-commissions/workforce-development-board - HTTP Error 403: Forbidden
- Review: Los Angeles County WDB - https://www.ajcc.lacounty.gov/wdb - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/workforce-development-board - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/executive-committee - HTTP Error 403: Forbidden
- Review: Yolo County WDB - https://www.yoloworks.org/ - robots.txt disallows fetching https://www.yoloworks.org/

## 2026-09-24T07:02:47.968126-07:00 (dry-run)

- Boards checked: 45
- Meetings found: 39
- Missing agendas within 72 hours: 1
- Agenda notifications sent: 0
- Boards with meeting history: 32 of 45
- Boards with agenda history: 16 of 45
- Failures requiring human review: 10
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/full-wdb-board - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/executive-committee - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/about-the-board - HTTP Error 403: Forbidden
- Review: Kings County WDB - https://www.countyofkingsca.gov/departments/board-of-supervisors/boards-commissions/workforce-development-board - HTTP Error 403: Forbidden
- Review: Long Beach WIN - https://longbeach.primegov.com/api/v2/PublicPortal/ListUpcomingMeetingsByCommitteeId?committeeId=126 - robots.txt disallows fetching https://longbeach.primegov.com/api/v2/PublicPortal/ListUpcomingMeetingsByCommitteeId?committeeId=126
- Review: Los Angeles County WDB - https://www.ajcc.lacounty.gov/wdb - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/workforce-development-board - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/executive-committee - HTTP Error 403: Forbidden
- Review: San Joaquin County WorkNet - https://www.sjcworknet.org/wdb.asp - HTTP Error 404: Not Found
- Review: Yolo County WDB - https://www.yoloworks.org/ - robots.txt disallows fetching https://www.yoloworks.org/

## 2026-09-24T07:10:53.462318-07:00 (dry-run)

- Boards checked: 5
- Meetings found: 18
- Missing agendas within 72 hours: 0
- Agenda notifications sent: 0
- Boards with meeting history: 42 of 45
- Boards with agenda history: 17 of 45
- Failures requiring human review: 0

## 2026-09-24T07:11:33.491726-07:00 (dry-run)

- Boards checked: 45
- Meetings found: 41
- Missing agendas within 72 hours: 0
- Agenda notifications sent: 0
- Boards with meeting history: 42 of 45
- Boards with agenda history: 17 of 45
- Failures requiring human review: 10
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/full-wdb-board - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/executive-committee - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/about-the-board - HTTP Error 403: Forbidden
- Review: Kings County WDB - https://www.countyofkingsca.gov/departments/board-of-supervisors/boards-commissions/workforce-development-board - HTTP Error 403: Forbidden
- Review: Long Beach WIN - https://longbeach.primegov.com/api/v2/PublicPortal/ListUpcomingMeetingsByCommitteeId?committeeId=126 - robots.txt disallows fetching https://longbeach.primegov.com/api/v2/PublicPortal/ListUpcomingMeetingsByCommitteeId?committeeId=126
- Review: Los Angeles County WDB - https://www.ajcc.lacounty.gov/wdb - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/workforce-development-board - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/executive-committee - HTTP Error 403: Forbidden
- Review: San Joaquin County WorkNet - https://www.sjcworknet.org/wdb.asp - HTTP Error 404: Not Found
- Review: Yolo County WDB - https://www.yoloworks.org/ - robots.txt disallows fetching https://www.yoloworks.org/

## 2026-09-24T07:16:47.187448-07:00 (dry-run)

- Boards checked: 1
- Meetings found: 2
- Missing agendas within 72 hours: 0
- Agenda notifications sent: 0
- Boards with meeting history: 42 of 45
- Boards with agenda history: 17 of 45
- Failures requiring human review: 0

## 2026-09-24T07:17:00.031740-07:00 (dry-run)

- Boards checked: 45
- Meetings found: 38
- Missing agendas within 72 hours: 0
- Agenda notifications sent: 0
- Boards with meeting history: 42 of 45
- Boards with agenda history: 17 of 45
- Failures requiring human review: 10
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/full-wdb-board - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/executive-committee - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/about-the-board - HTTP Error 403: Forbidden
- Review: Kings County WDB - https://www.countyofkingsca.gov/departments/board-of-supervisors/boards-commissions/workforce-development-board - HTTP Error 403: Forbidden
- Review: Long Beach WIN - https://longbeach.primegov.com/api/v2/PublicPortal/ListUpcomingMeetingsByCommitteeId?committeeId=126 - robots.txt disallows fetching https://longbeach.primegov.com/api/v2/PublicPortal/ListUpcomingMeetingsByCommitteeId?committeeId=126
- Review: Los Angeles County WDB - https://www.ajcc.lacounty.gov/wdb - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/workforce-development-board - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/executive-committee - HTTP Error 403: Forbidden
- Review: San Joaquin County WorkNet - https://www.sjcworknet.org/wdb.asp - HTTP Error 404: Not Found
- Review: Yolo County WDB - https://www.yoloworks.org/ - robots.txt disallows fetching https://www.yoloworks.org/

## 2026-09-24T07:22:22.102818-07:00 (dry-run)

- Boards checked: 45
- Meetings found: 44
- Missing agendas within 72 hours: 0
- Agenda notifications sent: 0
- Boards with meeting history: 42 of 45
- Boards with agenda history: 17 of 45
- Failures requiring human review: 10
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/full-wdb-board - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/executive-committee - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/about-the-board - HTTP Error 403: Forbidden
- Review: Kings County WDB - https://www.countyofkingsca.gov/departments/board-of-supervisors/boards-commissions/workforce-development-board - HTTP Error 403: Forbidden
- Review: Long Beach WIN - https://longbeach.primegov.com/api/v2/PublicPortal/ListUpcomingMeetingsByCommitteeId?committeeId=126 - robots.txt disallows fetching https://longbeach.primegov.com/api/v2/PublicPortal/ListUpcomingMeetingsByCommitteeId?committeeId=126
- Review: Los Angeles County WDB - https://www.ajcc.lacounty.gov/wdb - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/workforce-development-board - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/executive-committee - HTTP Error 403: Forbidden
- Review: San Joaquin County WorkNet - https://www.sjcworknet.org/wdb.asp - HTTP Error 404: Not Found
- Review: Yolo County WDB - https://www.yoloworks.org/ - robots.txt disallows fetching https://www.yoloworks.org/

## 2026-09-24T07:28:39.337828-07:00 (dry-run)

- Boards checked: 1
- Meetings found: 2
- Missing agendas within 72 hours: 0
- Agenda notifications sent: 0
- Boards with meeting history: 42 of 45
- Boards with agenda history: 17 of 45
- Failures requiring human review: 0

## 2026-09-24T07:28:50.596808-07:00 (dry-run)

- Boards checked: 45
- Meetings found: 44
- Missing agendas within 72 hours: 0
- Agenda notifications sent: 0
- Boards with meeting history: 42 of 45
- Boards with agenda history: 17 of 45
- Failures requiring human review: 11
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/full-wdb-board - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/executive-committee - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/about-the-board - HTTP Error 403: Forbidden
- Review: Kings County WDB - https://www.countyofkingsca.gov/departments/board-of-supervisors/boards-commissions/workforce-development-board - HTTP Error 403: Forbidden
- Review: Long Beach WIN - https://longbeach.primegov.com/api/v2/PublicPortal/ListUpcomingMeetingsByCommitteeId?committeeId=126 - robots.txt disallows fetching https://longbeach.primegov.com/api/v2/PublicPortal/ListUpcomingMeetingsByCommitteeId?committeeId=126
- Review: Los Angeles County WDB - https://www.ajcc.lacounty.gov/wdb - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/workforce-development-board - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/executive-committee - HTTP Error 403: Forbidden
- Review: Santa Barbara County WDB - https://www.countyofsb.org/3033/Board-Agendas - The read operation timed out
- Review: Santa Barbara County WDB - https://www.countyofsb.org/611/Workforce-Development-Board - The read operation timed out
- Review: Yolo County WDB - https://www.yoloworks.org/ - robots.txt disallows fetching https://www.yoloworks.org/

## 2026-09-24T07:32:35.307898-07:00 (dry-run)

- Boards checked: 1
- Meetings found: 1
- Missing agendas within 72 hours: 0
- Agenda notifications sent: 0
- Boards with meeting history: 42 of 45
- Boards with agenda history: 17 of 45
- Failures requiring human review: 0

## 2026-09-24T07:32:49.240000-07:00 (dry-run)

- Boards checked: 45
- Meetings found: 43
- Missing agendas within 72 hours: 0
- Agenda notifications sent: 0
- Boards with meeting history: 42 of 45
- Boards with agenda history: 17 of 45
- Failures requiring human review: 9
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/full-wdb-board - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/executive-committee - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/about-the-board - HTTP Error 403: Forbidden
- Review: Kings County WDB - https://www.countyofkingsca.gov/departments/board-of-supervisors/boards-commissions/workforce-development-board - HTTP Error 403: Forbidden
- Review: Long Beach WIN - https://longbeach.primegov.com/api/v2/PublicPortal/ListUpcomingMeetingsByCommitteeId?committeeId=126 - robots.txt disallows fetching https://longbeach.primegov.com/api/v2/PublicPortal/ListUpcomingMeetingsByCommitteeId?committeeId=126
- Review: Los Angeles County WDB - https://www.ajcc.lacounty.gov/wdb - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/workforce-development-board - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/executive-committee - HTTP Error 403: Forbidden
- Review: Yolo County WDB - https://www.yoloworks.org/ - robots.txt disallows fetching https://www.yoloworks.org/

## 2026-09-24T12:48:48.061110-07:00 (dry-run)

- Boards checked: 45
- Meetings found: 49
- Missing agendas within 72 hours: 0
- Agenda notifications sent: 0
- Boards with meeting history: 43 of 45
- Boards with agenda history: 21 of 45
- Failures requiring human review: 11
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/full-wdb-board - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/executive-committee - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/about-the-board - HTTP Error 403: Forbidden
- Review: Kings County WDB - https://www.countyofkingsca.gov/departments/board-of-supervisors/boards-commissions/workforce-development-board - HTTP Error 403: Forbidden
- Review: Long Beach WIN - https://longbeach.primegov.com/api/v2/PublicPortal/ListUpcomingMeetingsByCommitteeId?committeeId=126 - robots.txt disallows fetching https://longbeach.primegov.com/api/v2/PublicPortal/ListUpcomingMeetingsByCommitteeId?committeeId=126
- Review: Los Angeles County WDB - https://www.ajcc.lacounty.gov/wdb - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/workforce-development-board - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/executive-committee - HTTP Error 403: Forbidden
- Review: Sacramento (SETA) - https://www.seta.net/wp-json/tribe/events/v1/events?search=Sacramento%20Works%2C%20Inc.%20Board&start_date=2026-09-24&end_date=2027-03-23&per_page=50 - The read operation timed out
- Review: Sacramento (SETA) - https://www.seta.net/event/sacramento-works-executive-committee-6/2026-11-12/ - Detail page enrichment failed: The read operation timed out
- Review: Yolo County WDB - https://www.yoloworks.org/ - robots.txt disallows fetching https://www.yoloworks.org/

## 2026-09-24T12:59:45.343211-07:00 (dry-run)

- Boards checked: 1
- Meetings found: 3
- Missing agendas within 72 hours: 0
- Agenda notifications sent: 0
- Boards with meeting history: 43 of 45
- Boards with agenda history: 21 of 45
- Failures requiring human review: 0

## 2026-09-24T19:07:14.827814+00:00 (dry-run)

- Boards checked: 45
- Meetings found: 27
- Missing agendas within 72 hours: 1
- Failures requiring human review: 22
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/full-wdb-board - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/executive-committee - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/about-the-board - HTTP Error 403: Forbidden
- Review: Kings County WDB - https://www.countyofkingsca.gov/departments/board-of-supervisors/boards-commissions/workforce-development-board - HTTP Error 403: Forbidden
- Review: Los Angeles County WDB - https://www.ajcc.lacounty.gov/wdb - HTTP Error 403: Forbidden
- Review: Madera County WDB - https://maderaworkforce.com/wdb - <urlopen error [Errno -2] Name or service not known>
- Review: Madera County WDB - https://maderaworkforce.com/ - <urlopen error [Errno -2] Name or service not known>
- Review: Mother Lode Workforce Development Board - https://www.mljt.org/agendas-and-minutes - HTTP Error 429: Too Many Requests
- Review: Mother Lode Workforce Development Board - https://www.mljt.org/wdb - HTTP Error 429: Too Many Requests
- Review: Riverside County WDB - https://rivcoworkforce.org/workforce-development-board - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/executive-committee - HTTP Error 403: Forbidden
- Review: Sacramento (SETA) - https://www.seta.net/resources/board-operations/ - The read operation timed out
- Review: Sacramento (SETA) - https://www.seta.net/resources/agendas/ - The read operation timed out
- Review: Sacramento (SETA) - https://www.seta.net/ - The read operation timed out
- Review: San Joaquin County WorkNet - https://www.sjcworknet.org/wdb.asp - HTTP Error 404: Not Found
- Review: Sonoma County WDB - https://sonomawdb.org/ - <urlopen error [Errno -2] Name or service not known>
- Review: South Bay WIB - https://www.sbwib.org/2026-meeting-agendas - HTTP Error 429: Too Many Requests
- Review: South Bay WIB - https://www.sbwib.org/ - HTTP Error 429: Too Many Requests
- Review: Tulare County WIB - https://www.tularewib.org/wibboard - HTTP Error 429: Too Many Requests
- Review: Tulare County WIB - https://www.tularewib.org/pec - HTTP Error 429: Too Many Requests

