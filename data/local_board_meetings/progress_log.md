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

## 2026-05-20T18:01:43.418100+00:00 (dry-run)

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

## 2026-05-21T17:34:30.908660+00:00 (dry-run)

- Boards checked: 45
- Meetings found: 37
- Missing agendas within 72 hours: 3
- Failures requiring human review: 10
- Review: Foothill WDB - https://fwdbworks.org/events/ - The read operation timed out
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/full-wdb-board - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/executive-committee - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/about-the-board - HTTP Error 403: Forbidden
- Review: Kings County WDB - https://www.countyofkingsca.gov/departments/board-of-supervisors/boards-commissions/workforce-development-board - HTTP Error 403: Forbidden
- Review: Los Angeles County WDB - https://www.ajcc.lacounty.gov/wdb - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/workforce-development-board - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/executive-committee - HTTP Error 403: Forbidden
- Review: Sonoma County WDB - https://sonomawdb.org/ - <urlopen error [Errno -2] Name or service not known>
- Review: Yolo County WDB - https://www.yoloworks.org/ - robots.txt disallows fetching https://www.yoloworks.org/

## 2026-05-22T17:17:58.837664+00:00 (dry-run)

- Boards checked: 45
- Meetings found: 38
- Missing agendas within 72 hours: 2
- Failures requiring human review: 10
- Review: Foothill WDB - https://fwdbworks.org/events/ - HTTP Error 404: Not Found
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/full-wdb-board - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/executive-committee - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/about-the-board - HTTP Error 403: Forbidden
- Review: Kings County WDB - https://www.countyofkingsca.gov/departments/board-of-supervisors/boards-commissions/workforce-development-board - HTTP Error 403: Forbidden
- Review: Los Angeles County WDB - https://www.ajcc.lacounty.gov/wdb - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/workforce-development-board - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/executive-committee - HTTP Error 403: Forbidden
- Review: Sonoma County WDB - https://sonomawdb.org/ - <urlopen error [Errno -2] Name or service not known>
- Review: Yolo County WDB - https://www.yoloworks.org/ - robots.txt disallows fetching https://www.yoloworks.org/

## 2026-05-23T16:12:08.276211+00:00 (dry-run)

- Boards checked: 45
- Meetings found: 40
- Missing agendas within 72 hours: 2
- Failures requiring human review: 10
- Review: Foothill WDB - https://fwdbworks.org/events/ - HTTP Error 404: Not Found
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/full-wdb-board - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/executive-committee - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/about-the-board - HTTP Error 403: Forbidden
- Review: Kings County WDB - https://www.countyofkingsca.gov/departments/board-of-supervisors/boards-commissions/workforce-development-board - HTTP Error 403: Forbidden
- Review: Los Angeles County WDB - https://www.ajcc.lacounty.gov/wdb - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/workforce-development-board - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/executive-committee - HTTP Error 403: Forbidden
- Review: Sonoma County WDB - https://sonomawdb.org/ - <urlopen error [Errno -2] Name or service not known>
- Review: Yolo County WDB - https://www.yoloworks.org/ - robots.txt disallows fetching https://www.yoloworks.org/

## 2026-05-24T16:14:26.289904+00:00 (dry-run)

- Boards checked: 45
- Meetings found: 41
- Missing agendas within 72 hours: 2
- Failures requiring human review: 10
- Review: Foothill WDB - https://fwdbworks.org/events/ - HTTP Error 404: Not Found
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/full-wdb-board - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/executive-committee - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/about-the-board - HTTP Error 403: Forbidden
- Review: Kings County WDB - https://www.countyofkingsca.gov/departments/board-of-supervisors/boards-commissions/workforce-development-board - HTTP Error 403: Forbidden
- Review: Los Angeles County WDB - https://www.ajcc.lacounty.gov/wdb - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/workforce-development-board - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/executive-committee - HTTP Error 403: Forbidden
- Review: Sonoma County WDB - https://sonomawdb.org/ - <urlopen error [Errno -2] Name or service not known>
- Review: Yolo County WDB - https://www.yoloworks.org/ - robots.txt disallows fetching https://www.yoloworks.org/

## 2026-05-25T17:16:30.194109+00:00 (dry-run)

- Boards checked: 45
- Meetings found: 40
- Missing agendas within 72 hours: 4
- Failures requiring human review: 10
- Review: Foothill WDB - https://fwdbworks.org/events/ - HTTP Error 404: Not Found
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/full-wdb-board - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/executive-committee - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/about-the-board - HTTP Error 403: Forbidden
- Review: Kings County WDB - https://www.countyofkingsca.gov/departments/board-of-supervisors/boards-commissions/workforce-development-board - HTTP Error 403: Forbidden
- Review: Los Angeles County WDB - https://www.ajcc.lacounty.gov/wdb - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/workforce-development-board - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/executive-committee - HTTP Error 403: Forbidden
- Review: Sonoma County WDB - https://sonomawdb.org/ - <urlopen error [Errno -2] Name or service not known>
- Review: Yolo County WDB - https://www.yoloworks.org/ - robots.txt disallows fetching https://www.yoloworks.org/

## 2026-05-26T18:06:50.371519+00:00 (dry-run)

- Boards checked: 45
- Meetings found: 39
- Missing agendas within 72 hours: 3
- Failures requiring human review: 10
- Review: Foothill WDB - https://fwdbworks.org/events/ - HTTP Error 404: Not Found
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/full-wdb-board - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/executive-committee - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/about-the-board - HTTP Error 403: Forbidden
- Review: Kings County WDB - https://www.countyofkingsca.gov/departments/board-of-supervisors/boards-commissions/workforce-development-board - HTTP Error 403: Forbidden
- Review: Los Angeles County WDB - https://www.ajcc.lacounty.gov/wdb - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/workforce-development-board - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/executive-committee - HTTP Error 403: Forbidden
- Review: Sonoma County WDB - https://sonomawdb.org/ - <urlopen error [Errno -2] Name or service not known>
- Review: Yolo County WDB - https://www.yoloworks.org/ - robots.txt disallows fetching https://www.yoloworks.org/

## 2026-05-27T18:07:24.815527+00:00 (dry-run)

- Boards checked: 45
- Meetings found: 39
- Missing agendas within 72 hours: 3
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

## 2026-05-28T18:20:07.664766+00:00 (dry-run)

- Boards checked: 45
- Meetings found: 37
- Missing agendas within 72 hours: 3
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

## 2026-05-29T18:16:06.391494+00:00 (dry-run)

- Boards checked: 45
- Meetings found: 32
- Missing agendas within 72 hours: 1
- Failures requiring human review: 10
- Review: Golden Sierra Workforce Board - https://goldensierra.com/calendar/category/public-meeting/workforce-board - HTTP Error 500: Internal Server Error
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/full-wdb-board - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/executive-committee - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/about-the-board - HTTP Error 403: Forbidden
- Review: Kings County WDB - https://www.countyofkingsca.gov/departments/board-of-supervisors/boards-commissions/workforce-development-board - HTTP Error 403: Forbidden
- Review: Los Angeles County WDB - https://www.ajcc.lacounty.gov/wdb - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/workforce-development-board - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/executive-committee - HTTP Error 403: Forbidden
- Review: Sonoma County WDB - https://sonomawdb.org/ - <urlopen error [Errno -2] Name or service not known>
- Review: Yolo County WDB - https://www.yoloworks.org/ - robots.txt disallows fetching https://www.yoloworks.org/

## 2026-05-30T16:15:06.397192+00:00 (dry-run)

- Boards checked: 45
- Meetings found: 34
- Missing agendas within 72 hours: 1
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

## 2026-05-31T16:35:37.432902+00:00 (dry-run)

- Boards checked: 45
- Meetings found: 34
- Missing agendas within 72 hours: 1
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

## 2026-06-01T19:58:18.093548+00:00 (dry-run)

- Boards checked: 45
- Meetings found: 32
- Missing agendas within 72 hours: 2
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

## 2026-06-02T18:53:53.472827+00:00 (dry-run)

- Boards checked: 45
- Meetings found: 23
- Missing agendas within 72 hours: 1
- Failures requiring human review: 11
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/full-wdb-board - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/executive-committee - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/about-the-board - HTTP Error 403: Forbidden
- Review: Kings County WDB - https://www.countyofkingsca.gov/departments/board-of-supervisors/boards-commissions/workforce-development-board - HTTP Error 403: Forbidden
- Review: Los Angeles County WDB - https://www.ajcc.lacounty.gov/wdb - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/workforce-development-board - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/executive-committee - HTTP Error 403: Forbidden
- Review: San Benito County WDB - https://sbcjobs.org/meeting-packets/ - <urlopen error timed out>
- Review: San Benito County WDB - https://sbcjobs.org/about/ - <urlopen error timed out>
- Review: Sonoma County WDB - https://sonomawdb.org/ - <urlopen error [Errno -2] Name or service not known>
- Review: Yolo County WDB - https://www.yoloworks.org/ - robots.txt disallows fetching https://www.yoloworks.org/

## 2026-06-03T18:57:57.949528+00:00 (dry-run)

- Boards checked: 45
- Meetings found: 32
- Missing agendas within 72 hours: 1
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

## 2026-06-04T17:50:23.727118+00:00 (dry-run)

- Boards checked: 45
- Meetings found: 29
- Missing agendas within 72 hours: 1
- Failures requiring human review: 12
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/full-wdb-board - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/executive-committee - HTTP Error 403: Forbidden
- Review: Kern/Inyo/Mono WDB - https://www.employerstrainingresource.com/wdb/about-the-board - HTTP Error 403: Forbidden
- Review: Kings County WDB - https://www.countyofkingsca.gov/departments/board-of-supervisors/boards-commissions/workforce-development-board - HTTP Error 403: Forbidden
- Review: Los Angeles County WDB - https://www.ajcc.lacounty.gov/wdb - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/workforce-development-board - HTTP Error 403: Forbidden
- Review: Riverside County WDB - https://rivcoworkforce.org/executive-committee - HTTP Error 403: Forbidden
- Review: Sonoma County WDB - https://sonomawdb.org/ - <urlopen error [Errno -2] Name or service not known>
- Review: Ventura County WDB - https://workforce.venturacounty.gov/about-us/wdb-committees/ - HTTP Error 403: Forbidden
- Review: Ventura County WDB - https://workforce.venturacounty.gov/resources/meeting-packets/ - HTTP Error 403: Forbidden
- Review: Ventura County WDB - https://workforce.venturacounty.gov/ - HTTP Error 403: Forbidden
- Review: Yolo County WDB - https://www.yoloworks.org/ - robots.txt disallows fetching https://www.yoloworks.org/

## 2026-06-05T17:23:58.673215+00:00 (dry-run)

- Boards checked: 45
- Meetings found: 20
- Missing agendas within 72 hours: 0
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

## 2026-06-06T16:18:16.524113+00:00 (dry-run)

- Boards checked: 45
- Meetings found: 30
- Missing agendas within 72 hours: 1
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

## 2026-06-07T16:43:26.017493+00:00 (dry-run)

- Boards checked: 45
- Meetings found: 29
- Missing agendas within 72 hours: 0
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

## 2026-06-08T18:07:55.735503+00:00 (dry-run)

- Boards checked: 45
- Meetings found: 21
- Missing agendas within 72 hours: 1
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

## 2026-06-09T17:29:07.395671+00:00 (dry-run)

- Boards checked: 45
- Meetings found: 31
- Missing agendas within 72 hours: 3
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

