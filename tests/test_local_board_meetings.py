from __future__ import annotations

import unittest
from datetime import date, datetime, time, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from etl.local_board_meetings.agenda_notifications import narrate_agenda, process_agenda_notifications, summarize_agenda
from etl.local_board_meetings.agenda_content import extract_details_from_text
from etl.local_board_meetings.extraction import extract_agenda_links, extract_meetings, infer_virtual_url, parse_date, parse_time
from etl.local_board_meetings.fetcher import _is_public_calendar_feed
from etl.local_board_meetings.graph import meeting_to_event_payload
from etl.local_board_meetings.models import BoardSource, Meeting
from etl.local_board_meetings.meeting_state import merge_active_meetings
from etl.local_board_meetings.runner import _dedupe_meetings, _remove_conflicting_agenda, confirmed_profile_meetings
from etl.local_board_meetings.storage import agenda_hash, connect, future_meetings, prune_unseen_future_meetings, upsert_meetings
from etl.local_board_meetings.web_calendar import render_html, render_ics


class LocalBoardMeetingTests(unittest.TestCase):
    def test_public_calendar_feed_exception_is_narrow(self) -> None:
        self.assertTrue(
            _is_public_calendar_feed(
                "https://calendar.google.com/calendar/ical/example%40gmail.com/public/basic.ics"
            )
        )
        self.assertFalse(_is_public_calendar_feed("https://calendar.google.com/calendar/embed?src=example"))
        self.assertFalse(_is_public_calendar_feed("https://example.gov/public/basic.ics"))

    def test_virtual_link_detection_ignores_agenda_urls(self) -> None:
        text = (
            '<a href="https://example.gov/packet.pdf">Agenda</a> '
            '<a href="https://us06web.zoom.us/j/123456">Join Zoom</a>'
        )
        self.assertEqual(infer_virtual_url(text), "https://us06web.zoom.us/j/123456")
        self.assertEqual(infer_virtual_url('Agenda: https://example.gov/packet.pdf">9'), "")

    def test_parse_common_date_formats(self) -> None:
        self.assertEqual(parse_date("Board Meeting: May 14, 2026 at 9:00 AM"), date(2026, 5, 14))
        self.assertEqual(parse_date("Executive Committee 2026-06-02"), date(2026, 6, 2))
        self.assertEqual(parse_date("Agenda for 7/8/2026"), date(2026, 7, 8))
        self.assertEqual(parse_date("Wednesday, May 13 Agenda", date(2026, 5, 9)), date(2026, 5, 13))
        self.assertEqual(parse_date("February 10,2021", date(2026, 9, 24)), date(2021, 2, 10))

    def test_parse_time(self) -> None:
        self.assertEqual(parse_time("10:30 a.m."), time(10, 30))
        self.assertEqual(parse_time("1 PM"), time(13, 0))
        self.assertEqual(parse_time("Noon to 1:30 p.m."), time(12, 0))
        self.assertEqual(parse_time("9:00 – 10:30AM"), time(9, 0))
        self.assertIsNone(parse_time("September 25th for Native American Day"))

    def test_agenda_details_finds_location_after_time(self) -> None:
        text = """
        Santa Barbara County Workforce Development Board
        BOARD MEETING
        Friday, March 20, 2026
        9:30 AM
        SANTA MARIA INN
        801 SOUTH BROADWAY
        SANTA MARIA, CA 93454
        """
        details = extract_details_from_text(text)
        self.assertEqual(details.start_time, time(9, 30))
        self.assertEqual(details.location, "SANTA MARIA INN, 801 SOUTH BROADWAY, SANTA MARIA, CA 93454")

    def test_agenda_link_detection(self) -> None:
        html = """
        <a href="/files/2026-05-14-agenda.pdf">May 14, 2026 Board Agenda</a>
        <a href="/contact">Contact</a>
        <a href="packet.pdf">Board Packet</a>
        <a href="https://www.google.com/calendar/event?action=TEMPLATE&details=This+agenda+is+not+yet+available">Google Calendar</a>
        <a href="?ical=1">Add to iCalendar</a>
        """
        links = extract_agenda_links(html, "https://example.gov/wdb")
        self.assertEqual(len(links), 2)
        self.assertEqual(links[0].url, "https://example.gov/files/2026-05-14-agenda.pdf")

    def test_month_named_pdf_in_agenda_section(self) -> None:
        html = """
        <h5>2026 Board Agendas</h5>
        <p><a href="/files/may.pdf">May</a></p>
        <p><a href="/files/june.pdf">June</a></p>
        """
        source = BoardSource(
            board_id="sample-wdb",
            board_name="Sample WDB",
            local_area="Sample County",
            main_website="https://example.gov",
            meeting_schedule_url="https://example.gov",
            agenda_minutes_url="https://example.gov",
            executive_committee_url="",
            notes="test",
            last_checked_at="",
            confidence="high",
        )
        meetings = extract_meetings(source, html + "<p>May 13, 2026</p>", "https://example.gov/meetings", date(2026, 5, 9), 180)
        self.assertEqual(meetings[0].agenda_url, "https://example.gov/files/may.pdf")

    def test_duplicate_meeting_stable_id(self) -> None:
        source = BoardSource(
            board_id="sample-wdb",
            board_name="Sample WDB",
            local_area="Sample County",
            main_website="https://example.gov",
            meeting_schedule_url="https://example.gov",
            agenda_minutes_url="https://example.gov",
            executive_committee_url="",
            notes="test",
            last_checked_at="",
            confidence="high",
        )
        html = """
        <ul>
          <li>Board Meeting May 14, 2026 9:00 AM <a href="2026-05-14-agenda.pdf">Agenda</a></li>
          <li>Board Meeting May 14, 2026 9:00 AM</li>
        </ul>
        """
        meetings = extract_meetings(source, html, "https://example.gov/meetings", date(2026, 5, 1), 180)
        self.assertEqual(len(meetings), 1)
        self.assertEqual(meetings[0].stable_id, "sample-wdb:board-meeting:2026-05-14")

    def test_calendar_select_date_controls_are_ignored(self) -> None:
        source = BoardSource(
            board_id="sample-wdb",
            board_name="Sample WDB",
            local_area="Sample County",
            main_website="https://example.gov",
            meeting_schedule_url="https://example.gov",
            agenda_minutes_url="https://example.gov",
            executive_committee_url="",
            notes="test",
            last_checked_at="",
            confidence="high",
        )
        html = """
        <div>This Month 5/9/2026 May 2026 Select date.</div>
        <article>May 21 @ 1:00 pm Workforce Board Meeting</article>
        """
        meetings = extract_meetings(source, html, "https://example.gov/calendar", date(2026, 5, 9), 180)
        self.assertEqual([meeting.meeting_date for meeting in meetings], [date(2026, 5, 21)])

    def test_stanislaus_profile_ignores_committee_and_stale_agendas(self) -> None:
        source = BoardSource(
            board_id="stanislaus-county-wdb",
            board_name="Stanislaus County WDB",
            local_area="Stanislaus County",
            main_website="https://www.stanworkforce.com/",
            meeting_schedule_url="https://www.stanworkforce.com/workforce-board/",
            agenda_minutes_url="https://www.stanworkforce.com/workforce-board/",
            executive_committee_url="",
            notes="test",
            last_checked_at="",
            confidence="high",
        )
        html = """
        <a href="/media/vshjwvol/wdb-agenda-pkt_3-2-26-rev.pdf">Download the latest agenda</a>
        <h2>UPCOMING BOARD MEETING</h2>
        <p>Date: Monday, June 1, 2026</p>
        <p>Time: 12:00 PM - 2:00 PM</p>
        <h2>PREVIOUS AGENDAS & MINUTES</h2>
        <a href="/media/vjvjdk2a/ydc-agenda-06-10-24_cancelled.pdf">June 10, 2024</a>
        <h2>COMMITTEES</h2>
        <h3>Youth Development Committee</h3>
        <p>Date: Tuesday, October 13, 2026</p>
        <a href="/media/vjvjdk2a/ydc-agenda-06-10-24_cancelled.pdf">Current Agenda</a>
        """
        meetings = extract_meetings(
            source,
            html,
            "https://www.stanworkforce.com/workforce-board/",
            date(2026, 5, 9),
            180,
            extraction_strategy="stanislaus_workforce_board",
        )
        self.assertEqual(len(meetings), 1)
        self.assertEqual(meetings[0].meeting_date, date(2026, 6, 1))
        self.assertEqual(meetings[0].meeting_type, "Board Meeting")
        self.assertEqual(meetings[0].agenda_url, "")

    def test_south_bay_sectioned_agendas_assign_meeting_type(self) -> None:
        source = BoardSource(
            board_id="south-bay-wib",
            board_name="South Bay WIB",
            local_area="South Bay",
            main_website="https://www.sbwib.org/",
            meeting_schedule_url="https://www.sbwib.org/2026-meeting-agendas",
            agenda_minutes_url="https://www.sbwib.org/2026-meeting-agendas",
            executive_committee_url="",
            notes="test",
            last_checked_at="",
            confidence="high",
        )
        html = """
        <h1>2026 Meeting Agendas</h1>
        <p>SBWIB EXECUTIVE COMMITTEE</p>
        <p><a href="/exec-2026-04-09.pdf">April 9, 2026</a></p>
        <p>SOUTH BAY WORKFORCE INVESTMENT BOARD</p>
        <p><a href="/board-2026-04-16.pdf">April 16, 2026</a></p>
        <p>YOUTH DEVELOPMENT COUNCIL COMMITTEE</p>
        <p><a href="/youth-2026-05-05.pdf">May 5, 2026</a></p>
        <p>South Bay Workforce Investment Board</p>
        """
        meetings = extract_meetings(
            source,
            html,
            "https://www.sbwib.org/2026-meeting-agendas",
            date(2026, 4, 1),
            180,
            extraction_strategy="south_bay_sectioned_agendas",
        )
        self.assertEqual([m.meeting_type for m in meetings], ["Executive Committee", "Board Meeting"])
        self.assertEqual([m.agenda_url for m in meetings], [
            "https://www.sbwib.org/exec-2026-04-09.pdf",
            "https://www.sbwib.org/board-2026-04-16.pdf",
        ])

    def test_tulare_profile_excludes_program_evaluation_committee(self) -> None:
        source = BoardSource(
            board_id="tulare-county-wib",
            board_name="Tulare County WIB",
            local_area="Tulare County",
            main_website="https://www.tularewib.org/",
            meeting_schedule_url="https://www.tularewib.org/wibboard",
            agenda_minutes_url="https://www.tularewib.org/wibboard",
            executive_committee_url="https://www.tularewib.org/pec",
            notes="test",
            last_checked_at="",
            confidence="high",
        )
        html = "<p>May 4, 2026</p><p>Program & Evaluation Committee</p>"
        meetings = extract_meetings(
            source,
            html,
            "https://www.tularewib.org/pec",
            date(2026, 5, 1),
            180,
            extraction_strategy="tulare_wib_board_only",
        )
        self.assertEqual(meetings, [])

    def test_tulare_profile_extracts_second_date_in_two_column_schedule(self) -> None:
        source = BoardSource(
            board_id="tulare-county-wib",
            board_name="Tulare County WIB",
            local_area="Tulare County",
            main_website="https://www.tularewib.org/",
            meeting_schedule_url="https://www.tularewib.org/wibboard",
            agenda_minutes_url="https://www.tularewib.org/wibboard",
            executive_committee_url="https://www.tularewib.org/pec",
            notes="test",
            last_checked_at="",
            confidence="high",
        )
        html = """
        <h2>Board Meeting Schedule</h2>
        <p>WIB meetings are held the second Wednesday of the month at 7:30 a.m.
        located at 309 W. Main St. Suite 130, Visalia, CA unless otherwise noted.</p>
        <h3>2026</h3>
        <p>January 14, 2026 &nbsp; July 8, 2026 (Canceled)</p>
        <p>April 8, 2026 &nbsp; October 7, 2026 **</p>
        <p>May 13, 2026 &nbsp; November 18, 2026 *</p>
        <p>June 10, 2026 &nbsp; December 9, 2026 *</p>
        <p>October meeting moved to the first Wednesday and will be held at the
        Visalia Convention Center located at 303 E. Acequia Ave., Visalia, CA.</p>
        <h3>2026 Board Agendas</h3>
        <p><a href="/_files/21ddec71.pdf">September</a> October November December</p>
        <h3>2026 Board Minutes</h3>
        <p><a href="/december-minutes.pdf">December</a></p>
        """
        meetings = extract_meetings(
            source,
            html,
            source.meeting_schedule_url,
            date(2026, 9, 24),
            180,
            extraction_strategy="tulare_wib_board_only",
        )
        self.assertEqual(
            [meeting.meeting_date for meeting in meetings],
            [date(2026, 10, 7), date(2026, 11, 18), date(2026, 12, 9)],
        )
        self.assertEqual(meetings[0].start_time, time(7, 30))
        self.assertEqual(
            meetings[0].location,
            "Visalia Convention Center, 303 E. Acequia Ave., Visalia, CA",
        )
        self.assertEqual(meetings[1].location, "309 W. Main St. Suite 130, Visalia, CA")
        self.assertEqual(meetings[2].agenda_url, "")

    def test_workforce_alliance_profile_scopes_board_sections(self) -> None:
        source = BoardSource(
            board_id="workforce-alliance-north-bay",
            board_name="Workforce Alliance North Bay",
            local_area="North Bay",
            main_website="https://www.workforcealliancenorthbay.org/",
            meeting_schedule_url="https://www.workforcealliancenorthbay.org/board-meetings/",
            agenda_minutes_url="https://www.workforcealliancenorthbay.org/board-meetings/",
            executive_committee_url="",
            notes="test",
            last_checked_at="",
            confidence="high",
        )
        html = """
        <h2>Governing Board</h2>
        <p>June 20, 2026</p><p>3:00 - 5:00 PM</p>
        <h2>Regional Workforce Development Board</h2>
        <p>June 11, 2026</p><p>10:00 AM - 12:00 PM</p>
        <h2>Regional Workforce Development Board Executive Committee</h2>
        <p>May 13, 2026</p><p>9:00 – 10:30AM</p>
        <p>April 8, 2026</p><p>cancelled</p>
        <h2>Communications & Outreach Committee</h2>
        <p>March 26, 2026</p>
        """
        meetings = extract_meetings(
            source,
            html,
            "https://www.workforcealliancenorthbay.org/board-meetings/",
            date(2026, 5, 9),
            180,
            extraction_strategy="workforce_alliance_north_bay",
        )
        self.assertEqual([(m.meeting_date, m.meeting_type, m.start_time) for m in meetings], [
            (date(2026, 5, 13), "Executive Committee", time(9, 0)),
            (date(2026, 6, 11), "Board Meeting", time(10, 0)),
        ])

    def test_workforce_alliance_rejects_stale_row_agenda(self) -> None:
        source = BoardSource(
            board_id="workforce-alliance-north-bay",
            board_name="Workforce Alliance North Bay",
            local_area="North Bay",
            main_website="https://www.workforcealliancenorthbay.org/",
            meeting_schedule_url="https://www.workforcealliancenorthbay.org/board-meetings/",
            agenda_minutes_url="https://www.workforcealliancenorthbay.org/board-meetings/",
            executive_committee_url="",
            notes="test",
            last_checked_at="",
            confidence="high",
        )
        html = """
        <h2>Regional Workforce Development Board Executive Committee</h2>
        <table><tr>
          <td>February 10, 2027</td>
          <td><a href="/uploads/Executive-Committee-Agenda-2.10.21.pdf">Agenda</a></td>
        </tr></table>
        <h2>Communications &amp; Outreach Committee</h2>
        """
        meetings = extract_meetings(
            source,
            html,
            "https://www.workforcealliancenorthbay.org/board-meetings/",
            date(2026, 9, 24),
            180,
            extraction_strategy="workforce_alliance_north_bay",
        )
        self.assertEqual(len(meetings), 1)
        self.assertEqual(meetings[0].meeting_date, date(2027, 2, 10))
        self.assertEqual(meetings[0].agenda_url, "")

    def test_santa_cruz_profile_scopes_full_board_and_executive(self) -> None:
        source = BoardSource(
            board_id="santa-cruz-county-wdb",
            board_name="Santa Cruz County WDB",
            local_area="Santa Cruz County",
            main_website="https://workforcescc.com/",
            meeting_schedule_url="https://workforcescc.com/board-meetings/",
            agenda_minutes_url="https://workforcescc.com/board-meetings/",
            executive_committee_url="",
            notes="test",
            last_checked_at="",
            confidence="high",
        )
        html = """
        <h2>FULL BOARD</h2>
        <p>March 04, 2026 (8:30 am)</p>
        <table><tr><td>May 20, 2026 (8:30 a.m)</td><td>500 Westridge Drive</td><td><a href="/uploads/final-packet.pdf">Agenda</a></td></tr></table>
        <h2>EXECUTIVE COMMITTEE</h2>
        <p>April 29, 2026 (8:30 a.m)</p>
        <h2>CAREER SERVICES COMMITTEE</h2>
        <p>July 29, 2026 (3:00 p.m.)</p>
        """
        meetings = extract_meetings(
            source,
            html,
            "https://workforcescc.com/board-meetings/",
            date(2026, 5, 9),
            180,
            extraction_strategy="santa_cruz_wfscc",
        )
        self.assertEqual([(m.meeting_date, m.meeting_type) for m in meetings], [
            (date(2026, 4, 29), "Executive Committee"),
            (date(2026, 5, 20), "Board Meeting"),
        ])
        self.assertEqual(meetings[1].agenda_url, "https://workforcescc.com/uploads/final-packet.pdf")
        self.assertEqual(meetings[1].location, "500 Westridge Drive")

    def test_event_detail_title_sets_meeting_type(self) -> None:
        source = BoardSource(
            board_id="imperial-county-wdb",
            board_name="Imperial County WDB",
            local_area="Imperial County",
            main_website="https://example.gov",
            meeting_schedule_url="https://example.gov/event",
            agenda_minutes_url="https://example.gov/event",
            executive_committee_url="https://example.gov/event",
            notes="test",
            last_checked_at="",
            confidence="high",
        )
        html = """
        <title>Executive Committee Meeting | Example</title>
        <h1>Meeting Calendar</h1>
        <h1>Executive Committee Meeting</h1>
        <p>Date: May 27, 2026 11:00 AM</p>
        <a href="/agenda-05-27-2026.pdf">Agenda</a>
        """
        meetings = extract_meetings(
            source,
            html,
            "https://example.gov/event",
            date(2026, 5, 9),
            180,
            extraction_strategy="event_detail_title",
        )
        self.assertEqual(len(meetings), 1)
        self.assertEqual(meetings[0].meeting_type, "Executive Committee")
        self.assertEqual(meetings[0].start_time, time(11, 0))

    def test_alameda_profile_scopes_board_and_executive_links(self) -> None:
        source = BoardSource(
            board_id="alameda-county-wdb",
            board_name="Alameda County WDB",
            local_area="Alameda County",
            main_website="https://acwdb.org/",
            meeting_schedule_url="https://acwdb.org/boards/",
            agenda_minutes_url="https://acwdb.org/boards/",
            executive_committee_url="",
            notes="test",
            last_checked_at="",
            confidence="high",
        )
        html = """
        <p>5/14/26 - <a href="/board-packet.pdf">9:00 - Noon - Quarterly Board Meeting</a></p>
        <p><a href="/joint.pdf">4/15/26 - Joint Committee Meeting</a></p>
        <p><a href="/exec.pdf">4/22/26 - Executive Committee Meeting</a></p>
        <p><a href="/youth.pdf">6/8/26 - Youth Committee</a></p>
        """
        meetings = extract_meetings(
            source,
            html,
            "https://acwdb.org/boards/",
            date(2026, 5, 9),
            180,
            extraction_strategy="alameda_acwdb",
        )
        self.assertEqual([(m.meeting_date, m.meeting_type, m.start_time) for m in meetings], [
            (date(2026, 5, 14), "Board Meeting", time(9, 0)),
        ])

    def test_humboldt_profile_scopes_agenda_center_categories(self) -> None:
        source = BoardSource(
            board_id="humboldt-county-wdb",
            board_name="Humboldt County WDB",
            local_area="Humboldt County",
            main_website="https://humboldtgov.org/3803/Humboldt-County-Workforce-Development-Bo",
            meeting_schedule_url="https://humboldtgov.org/agendacenter",
            agenda_minutes_url="https://humboldtgov.org/agendacenter",
            executive_committee_url="",
            notes="test",
            last_checked_at="",
            confidence="high",
        )
        html = """
        <h2>Behavioral Health Board - Executive Committee</h2>
        <p>May 6, 2026</p>
        <h2>Workforce Development Board</h2>
        <p>June 26, 2026</p><p>Humboldt County Workforce Development Board Meeting</p>
        <h2>Workforce Development Board Executive Committee</h2>
        <p>May 29, 2026</p><p>Humboldt County Workforce Development Board Executive Committee</p>
        <h2>Youth Council of the Workforce Investment Board</h2>
        <p>June 10, 2026</p>
        """
        meetings = extract_meetings(
            source,
            html,
            "https://humboldtgov.org/agendacenter",
            date(2026, 5, 9),
            180,
            extraction_strategy="humboldt_civicengage",
        )
        self.assertEqual([(m.meeting_date, m.meeting_type) for m in meetings], [
            (date(2026, 5, 29), "Executive Committee"),
            (date(2026, 6, 26), "Board Meeting"),
        ])

    def test_foothill_profile_uses_event_titles_only(self) -> None:
        source = BoardSource(
            board_id="foothill-wdb",
            board_name="Foothill WDB",
            local_area="Foothill",
            main_website="https://fwdbworks.org/wp/",
            meeting_schedule_url="https://fwdbworks.org/events/",
            agenda_minutes_url="https://fwdbworks.org/events/",
            executive_committee_url="",
            notes="test",
            last_checked_at="",
            confidence="medium",
        )
        html = """
        <div><time>May 14, 2026 9:00 AM</time><a href="/event/fwdb-meeting/">FWDB Meeting</a></div>
        <div><time>May 21, 2026 10:00 AM</time><a href="/event/orientation/">FWDB Orientation</a></div>
        <div><time>May 28, 2026 1:00 PM</time><a href="/event/exec/">FWDB Executive Committee Meeting</a></div>
        <div><span>May 29, 2026</span><a href="/event/other/">Community Workshop</a></div>
        """
        meetings = extract_meetings(
            source,
            html,
            "https://fwdbworks.org/events/",
            date(2026, 5, 9),
            180,
            extraction_strategy="foothill_events",
        )
        self.assertEqual([(m.meeting_date, m.meeting_type, m.start_time) for m in meetings], [
            (date(2026, 5, 14), "Board Meeting", time(9, 0)),
            (date(2026, 5, 28), "Executive Committee", time(13, 0)),
        ])

    def test_tribe_events_api_filters_fresno_titles(self) -> None:
        source = BoardSource(
            board_id="fresno-regional-wdb",
            board_name="Fresno Regional WDB",
            local_area="Fresno",
            main_website="https://frwdb.net/",
            meeting_schedule_url="https://frwdb.net/wp-json/tribe/events/v1/events",
            agenda_minutes_url="",
            executive_committee_url="",
            notes="test",
            last_checked_at="",
            confidence="high",
        )
        html = """
        {"events": [
          {"title": "FRWDB Meeting", "start_date": "2026-09-09 16:00:00", "timezone": "America/Los_Angeles", "url": "https://frwdb.net/event/frwdb-meeting-29/", "description": "", "categories": [{"slug": "workforce_development_board"}], "venue": {"venue": "AJCC Comprehensive"}},
          {"title": "Executive Committee Meeting", "start_date": "2026-07-15 15:00:00", "timezone": "America/Los_Angeles", "url": "https://frwdb.net/event/executive-committee-meeting-34/", "description": "", "categories": [{"slug": "executive_committee"}], "venue": {"venue": "AJCC Comprehensive"}},
          {"title": "FAWIC Board of Directors Meeting", "start_date": "2026-07-15 08:00:00", "timezone": "America/Los_Angeles", "url": "https://frwdb.net/event/fawic/", "description": "", "categories": [{"slug": "fawic_board"}]}
        ]}
        """
        meetings = extract_meetings(source, html, source.meeting_schedule_url, date(2026, 6, 11), 180, extraction_strategy="tribe_events_api")
        self.assertEqual([(m.meeting_date, m.meeting_type, m.start_time) for m in meetings], [
            (date(2026, 7, 15), "Executive Committee", time(15, 0)),
            (date(2026, 9, 9), "Board Meeting", time(16, 0)),
        ])

    def test_tribe_events_api_does_not_treat_agenda_as_virtual_link(self) -> None:
        source = BoardSource(
            board_id="fresno-regional-wdb",
            board_name="Fresno Regional WDB",
            local_area="Fresno",
            main_website="https://frwdb.net/",
            meeting_schedule_url="https://frwdb.net/wp-json/tribe/events/v1/events",
            agenda_minutes_url="",
            executive_committee_url="",
            notes="test",
            last_checked_at="",
            confidence="high",
        )
        payload = """
        {"events": [{
          "title": "FRWDB Meeting",
          "start_date": "2026-09-24 16:00:00",
          "timezone": "America/Los_Angeles",
          "url": "https://frwdb.net/event/special-frwdb-meeting-2/",
          "website": "https://frwdb.net/wp-content/uploads/2026/09/9-24-26-FRWDB-Packet.pdf",
          "description": "Agenda https://frwdb.net/wp-content/uploads/2026/09/9-24-26-FRWDB-Packet.pdf",
          "categories": [{"slug": "workforce_development_board"}],
          "venue": {"venue": "AJCC Comprehensive"}
        }]}
        """
        meetings = extract_meetings(
            source,
            payload,
            source.meeting_schedule_url,
            date(2026, 9, 24),
            180,
            extraction_strategy="tribe_events_api",
        )
        self.assertEqual(len(meetings), 1)
        self.assertEqual(meetings[0].virtual_url, "")

    def test_la_city_novus_filters_wdb_rows(self) -> None:
        source = BoardSource(
            board_id="los-angeles-city-wdb",
            board_name="Los Angeles City WDB",
            local_area="Los Angeles",
            main_website="https://www.wiblacity.org/",
            meeting_schedule_url="https://wiblacity.novusagenda.com/agendapublic/meetingsgeneral.aspx",
            agenda_minutes_url="",
            executive_committee_url="",
            notes="test",
            last_checked_at="",
            confidence="high",
        )
        html = """
        <table id="SearchAgendasMeetings_radGridMeetings_ctl00">
          <tr><th>Meeting Date</th><th>Meeting Type</th><th>Meeting Location</th></tr>
          <tr><td>07/21/26</td><td>WDB QUARTERLY MEETING</td><td>The Plaza At Cabrillo Marina, 2965 Via C...</td><td><a onclick="window.open('MeetingView.aspx?MeetingID=399&amp;MinutesMeetingID=-1&amp;doctype=Agenda')"></a></td></tr>
          <tr><td>07/14/26</td><td>YOUTH COUNCIL MEETING</td><td>LATTC</td></tr>
        </table>
        """
        meetings = extract_meetings(source, html, source.meeting_schedule_url, date(2026, 6, 11), 180, extraction_strategy="la_city_novus")
        self.assertEqual(len(meetings), 1)
        self.assertEqual(meetings[0].meeting_date, date(2026, 7, 21))
        self.assertEqual(meetings[0].source_page_url, "https://wiblacity.novusagenda.com/agendapublic/MeetingView.aspx?MeetingID=399&MinutesMeetingID=-1&doctype=Agenda")

    def test_mother_lode_schedule_scopes_wdb_section(self) -> None:
        source = BoardSource(
            board_id="mother-lode-workforce-development-board",
            board_name="Mother Lode Workforce Development Board",
            local_area="Mother Lode",
            main_website="https://www.mljt.org/wdb",
            meeting_schedule_url="https://www.mljt.org/schedule.pdf",
            agenda_minutes_url="https://www.mljt.org/agendas-and-minutes",
            executive_committee_url="",
            notes="test",
            last_checked_at="",
            confidence="high",
        )
        text = """
        BOD Meetings
        Monday, July 20, 2026
        10:00 am - 12:00 pm
        WDB Meetings
        Thursday, August 20, 2026
        12:00 - 2:00 pm
        Thursday, November 19, 2026
        12:00 - 2:00 pm
        Lunch provided for WDB Meetings
        Primary Location In-Person: 197 Mono Way, Suite B, Sonora, CA 95370
        CSEDD Meetings
        Thursday, August 20, 2026
        """
        meetings = extract_meetings(source, text, source.meeting_schedule_url, date(2026, 6, 11), 180, extraction_strategy="mother_lode_schedule")
        self.assertEqual([(m.meeting_date, m.meeting_type, m.start_time) for m in meetings], [
            (date(2026, 8, 20), "Board Meeting", time(12, 0)),
            (date(2026, 11, 19), "Board Meeting", time(12, 0)),
        ])

    def test_santa_ana_public_meetings_filters_wdb_links(self) -> None:
        source = BoardSource(
            board_id="santa-ana-wdb",
            board_name="Santa Ana WDB",
            local_area="Santa Ana",
            main_website="https://www.santa-ana.org/workforce-development-board/",
            meeting_schedule_url="https://www.santa-ana.org/events/categories/public-meetings/",
            agenda_minutes_url="",
            executive_committee_url="",
            notes="test",
            last_checked_at="",
            confidence="high",
        )
        html = """
        <ul>
          <li><a href="/event/planning/">Planning Commission Meeting</a> - 07/13/2026 - 5:30 pm - 10:00 pm</li>
          <li><a href="/event/workforce-development-board-7-16-26/">Workforce Development Board</a> - 07/16/2026 - 8:00 am - 9:30 am</li>
        </ul>
        """
        meetings = extract_meetings(source, html, source.meeting_schedule_url, date(2026, 6, 11), 180, extraction_strategy="santa_ana_wdb_events")
        self.assertEqual([(m.meeting_date, m.start_time, m.source_page_url) for m in meetings], [
            (date(2026, 7, 16), time(8, 0), "https://www.santa-ana.org/event/workforce-development-board-7-16-26/")
        ])

    def test_santa_barbara_hcms_uses_tagged_agenda_items(self) -> None:
        source = BoardSource(
            board_id="santa-barbara-county-wdb",
            board_name="Santa Barbara County WDB",
            local_area="Santa Barbara",
            main_website="https://www.countyofsb.org/611/Workforce-Development-Board",
            meeting_schedule_url="https://www.countyofsb.org/3034/Executive-Committee-Agendas",
            agenda_minutes_url="",
            executive_committee_url="",
            notes="test",
            last_checked_at="",
            confidence="high",
        )
        html = 'hcmsReadOnlyConfiguration:{baseUrl:"content.civicplus.com",appName:"ca-santabarbaracounty",userToken:"Bearer test"} ds-wdb-executive-agendas-2026'
        response = SimpleNamespace(
            text='{"items":[{"data":{"boardname":{"en":"Executive Committee"},"meetingdate":{"iv":"2026-05-20T07:00:00Z"},"agenda":{"iv":["asset-id"]}}}]}'
        )
        with patch("etl.local_board_meetings.extraction.fetch_url", return_value=response):
            meetings = extract_meetings(source, html, source.meeting_schedule_url, date(2026, 5, 15), 180, extraction_strategy="santa_barbara_hcms")
        self.assertEqual(len(meetings), 1)
        self.assertEqual(meetings[0].meeting_type, "Executive Committee")
        self.assertEqual(meetings[0].agenda_url, "https://content.civicplus.com/api/assets/ca-santabarbaracounty/asset-id")

    def test_long_beach_profile_reads_scheduled_meetings_block(self) -> None:
        source = BoardSource(
            board_id="long-beach-win",
            board_name="Long Beach WIN",
            local_area="Long Beach",
            main_website="https://www.longbeach.gov/edo/talent-workforce/workforce-development-board/",
            meeting_schedule_url="https://www.longbeach.gov/edo/talent-workforce/workforce-development-board/",
            agenda_minutes_url="",
            executive_committee_url="",
            notes="test",
            last_checked_at="",
            confidence="high",
        )
        html = """
        <p>Board member served from 2018-2023 and chair since 2024.</p>
        <h3>2026 Scheduled Meetings:</h3>
        <p>Thursday, June 4</p>
        <p>9 - 11 a.m.</p>
        <p>Long Beach Workforce Innovation Network</p>
        <p>Adult Career Services Center</p>
        <p>4811 Airport Plaza Dr. Ste 120</p>
        <p>Thursday, August 6</p>
        <p>9 - 11 a.m.</p>
        <p>Adult Career Services Center</p>
        <h3>Useful Links</h3>
        """
        meetings = extract_meetings(
            source,
            html,
            source.meeting_schedule_url,
            date(2026, 5, 9),
            180,
            extraction_strategy="long_beach_lbwin_schedule",
        )
        self.assertEqual([(m.meeting_date, m.meeting_type, m.start_time) for m in meetings], [
            (date(2026, 6, 4), "Board Meeting", time(9, 0)),
            (date(2026, 8, 6), "Board Meeting", time(9, 0)),
        ])

    def test_long_beach_profile_reads_primegov_agenda_api(self) -> None:
        source = BoardSource(
            board_id="long-beach-win",
            board_name="Long Beach WIN",
            local_area="Long Beach",
            main_website="https://www.longbeach.gov/edo/talent-workforce/workforce-development-board/",
            meeting_schedule_url="https://www.longbeach.gov/edo/talent-workforce/workforce-development-board/",
            agenda_minutes_url="https://longbeach.primegov.com/api/v2/PublicPortal/ListUpcomingMeetingsByCommitteeId?committeeId=126",
            executive_committee_url="",
            notes="test",
            last_checked_at="",
            confidence="high",
        )
        html = """
        [{
          "id": 6782,
          "dateTime": "2026-06-11T09:00:00",
          "title": "Long Beach Workforce Innovation Network - Special Meeting",
          "documentList": [
            {"compileOutputType": 3, "templateId": 36045, "templateName": "HTML Agenda"},
            {"compileOutputType": 1, "templateId": 36045, "templateName": "Agenda"}
          ]
        }]
        """
        meetings = extract_meetings(
            source,
            html,
            source.agenda_minutes_url,
            date(2026, 6, 10),
            180,
            extraction_strategy="long_beach_lbwin_schedule",
        )
        self.assertEqual(len(meetings), 1)
        self.assertEqual(meetings[0].meeting_date, date(2026, 6, 11))
        self.assertEqual(meetings[0].agenda_url, "https://longbeach.primegov.com/Public/CompiledDocument?meetingTemplateId=36045&compileOutputType=1")

    def test_deduped_meeting_keeps_schedule_location_and_agenda(self) -> None:
        schedule = Meeting(
            board_id="long-beach-win",
            board_name="Long Beach WIN",
            meeting_type="Board Meeting",
            meeting_date=date(2026, 6, 11),
            start_time=time(9, 0),
            timezone="America/Los_Angeles",
            location="Port of Long Beach",
            virtual_url="",
            source_page_url="https://www.longbeach.gov/edo/talent-workforce/workforce-development-board/",
            agenda_url="",
            agenda_label="",
            confidence_notes="schedule source",
        )
        agenda = Meeting(
            board_id="long-beach-win",
            board_name="Long Beach WIN",
            meeting_type="Board Meeting",
            meeting_date=date(2026, 6, 11),
            start_time=time(9, 0),
            timezone="America/Los_Angeles",
            location="",
            virtual_url="",
            source_page_url="https://www.longbeach.gov/edo/talent-workforce/workforce-development-board/",
            agenda_url="https://longbeach.primegov.com/Public/CompiledDocument?meetingTemplateId=36045&compileOutputType=1",
            agenda_label="Agenda",
            confidence_notes="agenda source",
        )
        merged = _dedupe_meetings([schedule, agenda])
        self.assertEqual(len(merged), 1)
        self.assertEqual(merged[0].location, "Port of Long Beach")
        self.assertEqual(merged[0].agenda_url, agenda.agenda_url)

    def test_merced_profile_scopes_wdb_and_executive_rows(self) -> None:
        source = BoardSource(
            board_id="merced-county-wdb",
            board_name="Merced County WDB",
            local_area="Merced County",
            main_website="https://worknetmerced.com/workforce-development",
            meeting_schedule_url="https://worknetmerced.com/workforce-development",
            agenda_minutes_url="https://worknetmerced.com/workforce-development",
            executive_committee_url="",
            notes="test",
            last_checked_at="",
            confidence="high",
        )
        html = """
        <p>Monday, May 11, 2026 (Rescheduled to Monday, June 8th)</p>
        <p>Executive Committee Meeting</p>
        <p>7:30am-8:30am</p>
        <a href="/may-agenda.pdf">View Agenda</a>
        <p>Thursday, June 26, 2026</p>
        <p>WDB Meeting</p>
        <p>12:00-1:30pm</p>
        <p>203 State Highway 59 Suite B</p>
        <a href="/june-agenda.pdf">View Agenda</a>
        <p>Monday, June 16, 2026</p>
        <p>Executive Committee Meeting</p>
        <p>9:00 am - 10:00 am</p>
        <p>1900 Airdrome Entry, Atwater, CA 95301</p>
        <p>Dates</p><p>September 25</p>
        <p>Workforce Development Board (WDB) ROSTER</p>
        <p>June 7</p><p>Workforce Development Board Meeting</p>
        """
        meetings = extract_meetings(
            source,
            html,
            source.meeting_schedule_url,
            date(2026, 5, 9),
            180,
            extraction_strategy="merced_worknet",
        )
        self.assertEqual([(m.meeting_date, m.meeting_type, m.start_time) for m in meetings], [
            (date(2026, 6, 8), "Executive Committee", time(7, 30)),
            (date(2026, 6, 16), "Executive Committee", time(9, 0)),
            (date(2026, 6, 26), "Board Meeting", time(12, 0)),
        ])

    def test_madera_profile_skips_canceled_rows(self) -> None:
        source = BoardSource(
            board_id="madera-county-wdb",
            board_name="Madera County WDB",
            local_area="Madera County",
            main_website="https://www.maderaworkforce.org/wdb/",
            meeting_schedule_url="https://www.maderaworkforce.org/wdb/workforce-board-meetings/",
            agenda_minutes_url="https://www.maderaworkforce.org/wdb/workforce-board-meetings/",
            executive_committee_url="https://www.maderaworkforce.org/wdb/executive-committee-meetings/",
            notes="test",
            last_checked_at="",
            confidence="high",
        )
        html = """
        <p>Workforce Assistance Center</p>
        <p>Executive Conference Room</p>
        <p>2037 W. Cleveland Avenue</p>
        <p>Madera, CA</p>
        <p>93637</p>
        <h2>Meetings & Agendas</h2>
        <p>June 18, 2026 - CANCELLED</p>
        <p>August 20, 2026</p>
        <a href="/WDB-Agenda-Packet-2026.8.20.pdf">Agenda Packet</a>
        """
        meetings = extract_meetings(
            source,
            html,
            source.meeting_schedule_url,
            date(2026, 6, 10),
            220,
            extraction_strategy="madera_board_archives",
        )
        self.assertEqual([(m.meeting_date, m.meeting_type) for m in meetings], [(date(2026, 8, 20), "Board Meeting")])
        self.assertEqual(meetings[0].agenda_url, "https://www.maderaworkforce.org/WDB-Agenda-Packet-2026.8.20.pdf")

    def test_sonoma_profile_scopes_event_rows_and_agendas(self) -> None:
        source = BoardSource(
            board_id="sonoma-county-wdb",
            board_name="Sonoma County WDB",
            local_area="Sonoma County",
            main_website="https://joblinksonoma.org/board-meetings/",
            meeting_schedule_url="https://joblinksonoma.org/board-meetings/",
            agenda_minutes_url="https://joblinksonoma.org/board-meetings/",
            executive_committee_url="",
            notes="test",
            last_checked_at="",
            confidence="high",
        )
        html = """
        <a href="https://cdn.example/06-10-2026-WIBE-Agenda-Packet.pdf">06-10-2026 WIBE Agenda Packet</a>
        <a href="https://cdn.example/07-23-2026-WIB-LaborAgenda.pdf">07-23-2026 WIB Labor Agenda</a>
        <p>June WIB Executive Committee</p>
        <p>June 10 @ 4:00 pm</p><p>-</p><p>5:00 pm</p>
        <p>Job Link Office</p><p>2227 Capricorn Way, Santa Rosa, CA</p>
        <p>July Workforce Investment Board Meeting</p>
        <p>July 8 @ 3:00 pm</p><p>-</p><p>5:00 pm</p>
        <p>Job Link Office</p><p>2227 Capricorn Way, Santa Rosa, CA</p>
        <p>July WIB Labor Committee</p>
        <p>July 23 @ 2:00 pm</p>
        """
        meetings = extract_meetings(
            source,
            html,
            source.meeting_schedule_url,
            date(2026, 6, 10),
            220,
            extraction_strategy="sonoma_joblink_board_meetings",
        )
        self.assertEqual([(m.meeting_date, m.meeting_type, m.start_time) for m in meetings], [
            (date(2026, 6, 10), "Executive Committee", time(16, 0)),
            (date(2026, 7, 8), "Board Meeting", time(15, 0)),
        ])
        self.assertEqual(meetings[0].agenda_url, "https://cdn.example/06-10-2026-WIBE-Agenda-Packet.pdf")

    def test_solano_profile_reads_calendar_pdf_text(self) -> None:
        source = BoardSource(
            board_id="solano-county-wdb",
            board_name="Solano County WDB",
            local_area="Solano County",
            main_website="https://solanoemployment.org/board-of-directors/",
            meeting_schedule_url="https://solanoemployment.org/wp-content/uploads/2022/03/Board-of-Directors-2026-Meeting-Calendar.pdf",
            agenda_minutes_url="https://solanoemployment.org/board-of-directors/",
            executive_committee_url="",
            notes="test",
            last_checked_at="",
            confidence="high",
        )
        text = """
        BOARD OF DIRECTORS
        2026 Meeting Dates
        All meetings are held from 8:30 a.m. to 10:30 a.m.
        July 17, 2026
        September 18, 2026
        Meetings are scheduled to take place at:
        Workforce Development Board of Solano County
        500 Chadbourne Road, Suite A
        Fairfield, CA 94534
        """
        meetings = extract_meetings(
            source,
            text,
            source.meeting_schedule_url,
            date(2026, 6, 10),
            220,
            extraction_strategy="solano_board_calendar",
        )
        self.assertEqual([(m.meeting_date, m.start_time) for m in meetings], [
            (date(2026, 7, 17), time(8, 30)),
            (date(2026, 9, 18), time(8, 30)),
        ])
        self.assertIn("500 Chadbourne Road", meetings[0].location)

    def test_work2future_profile_reads_event_cards(self) -> None:
        source = BoardSource(
            board_id="santa-clara-county-work2future",
            board_name="Santa Clara County (work2future)",
            local_area="Santa Clara County",
            main_website="https://www.work2future.org/",
            meeting_schedule_url="https://www.work2future.org/board/",
            agenda_minutes_url="https://www.work2future.org/board/",
            executive_committee_url="",
            notes="test",
            last_checked_at="",
            confidence="high",
        )
        html = """
        <p>June 2026</p><p>10</p><p>June</p><p>Wednesday</p>
        <a href="/calendar/executive-cmte-meeting/?occurrence=2026-06-10">Executive Committee Meeting</a>
        <p>San Jose Career Center | 1608 Las Plumas Ave, San Jose, CA</p>
        <p>May 2026</p><p>14</p><p>May</p><p>Thursday</p>
        <a href="/calendar/youth/">Youth Committee Meeting</a>
        <p>April 2026</p><p>14</p><p>April</p><p>Tuesday</p>
        <a href="/calendar/board/">work2future Board Meeting (CANCELLED)</a>
        """
        meetings = extract_meetings(
            source,
            html,
            source.meeting_schedule_url,
            date(2026, 6, 10),
            220,
            extraction_strategy="work2future_board_events",
        )
        self.assertEqual([(m.meeting_date, m.meeting_type) for m in meetings], [(date(2026, 6, 10), "Executive Committee")])
        self.assertEqual(
            meetings[0].source_page_url,
            "https://www.work2future.org/calendar/executive-cmte-meeting/?occurrence=2026-06-10",
        )

    def test_san_diego_profile_attaches_upcoming_agenda(self) -> None:
        source = BoardSource(
            board_id="san-diego-workforce-partnership",
            board_name="San Diego Workforce Partnership",
            local_area="San Diego County",
            main_website="https://workforce.org/",
            meeting_schedule_url="https://workforce.org/boards/workforce-development-board/agendas-minutes/",
            agenda_minutes_url="https://workforce.org/boards/workforce-development-board/agendas-minutes/",
            executive_committee_url="",
            notes="test",
            last_checked_at="",
            confidence="medium",
        )
        html = """
        <h2>Upcoming Meetings</h2>
        <h3>2026</h3>
        <p>Board Meeting</p>
        <p>June 11, 2026</p>
        <p>12-2 p.m.</p>
        <p><a href="/wp-content/uploads/2026/06/2026-06-11-WDB-Agenda-1.pdf">Download Agenda</a></p>
        <p>Audit Committee</p>
        <p>June 29, 2026</p>
        <h2>Past Meetings</h2>
        """
        meetings = extract_meetings(
            source,
            html,
            source.meeting_schedule_url,
            date(2026, 6, 10),
            180,
            extraction_strategy="san_diego_wdb",
        )
        self.assertEqual(len(meetings), 1)
        self.assertEqual(meetings[0].agenda_url, "https://workforce.org/wp-content/uploads/2026/06/2026-06-11-WDB-Agenda-1.pdf")

    def test_san_diego_profile_matches_agenda_to_meeting_body(self) -> None:
        source = BoardSource(
            board_id="san-diego-workforce-partnership",
            board_name="San Diego Workforce Partnership",
            local_area="San Diego County",
            main_website="https://workforce.org/",
            meeting_schedule_url="https://workforce.org/meetings/",
            agenda_minutes_url="https://workforce.org/meetings/",
            executive_committee_url="",
            notes="test",
            last_checked_at="",
            confidence="high",
        )
        html = """
        <h2>Upcoming Meetings</h2><p>Executive Committee</p><p>September 28, 2026</p><p>11 a.m.</p>
        <a href="/2026-09-28-Audit-Committee-Agenda.pdf">Download Agenda</a>
        <a href="/2026-09-28-Exec-Cmte-Agenda.pdf">Download Agenda</a>
        <h2>Past Meetings</h2>
        """
        meetings = extract_meetings(source, html, source.meeting_schedule_url, date(2026, 9, 24), 180, "san_diego_wdb")
        self.assertEqual(len(meetings), 1)
        self.assertTrue(meetings[0].agenda_url.endswith("2026-09-28-Exec-Cmte-Agenda.pdf"))

    def test_orange_profile_excludes_other_committees_and_cancellations(self) -> None:
        source = BoardSource(
            board_id="orange-county-wdb",
            board_name="Orange County WDB",
            local_area="Orange County",
            main_website="https://workforce.oc.gov/",
            meeting_schedule_url="https://workforce.oc.gov/meetings",
            agenda_minutes_url="https://workforce.oc.gov/meetings",
            executive_committee_url="",
            notes="test",
            last_checked_at="",
            confidence="high",
        )
        html = """
        <h3>OCWDB Full Board</h3><table><tr><td>October 28, 2026</td><td><a href="/board-agenda.pdf">View Agenda</a></td></tr></table>
        <h3>Executive Committee</h3><table><tr><td>September 23, 2026</td><td><a href="/cancel.pdf">Notice of Cancellation</a></td></tr></table>
        <h3>Business Services Committee</h3><table><tr><td>October 14, 2026</td><td><a href="/business-agenda.pdf">View Agenda</a></td></tr></table>
        """
        meetings = extract_meetings(source, html, source.meeting_schedule_url, date(2026, 9, 24), 180, "orange_ocwdb")
        self.assertEqual([(item.meeting_date, item.meeting_type) for item in meetings], [(date(2026, 10, 28), "Board Meeting")])
        self.assertEqual(meetings[0].agenda_url, "https://workforce.oc.gov/board-agenda.pdf")

    def test_slo_meeting_table_excludes_cancellations(self) -> None:
        source = BoardSource(
            board_id="san-luis-obispo-county-wdb",
            board_name="San Luis Obispo County WDB",
            local_area="San Luis Obispo County",
            main_website="https://www.slocounty.ca.gov/",
            meeting_schedule_url="https://www.slocounty.ca.gov/wdb/meetings",
            agenda_minutes_url="https://www.slocounty.ca.gov/wdb/meetings",
            executive_committee_url="https://www.slocounty.ca.gov/wdb/meetings",
            notes="test",
            last_checked_at="",
            confidence="high",
        )
        html = """
        <table><tbody>
          <tr><td>10/14/2026 8:30:00 AM</td><td><a href="/meetings/executive-10-14">Executive Committee Meeting 10/14/2026</a></td><td>Executive Committee Meeting</td><td>10/14/2026 8:30 AM</td><td>3433 S Higuera St</td></tr>
          <tr><td>11/5/2026 8:30:00 AM</td><td><a href="/meetings/board-11-05">Workforce Development Board Meeting 11/05/2026</a></td><td>Board Meeting</td><td>11/5/2026 8:30 AM</td><td>1050 Southwood Dr</td></tr>
          <tr><td>12/9/2026 8:30:00 AM</td><td>Executive Committee Meeting 12/09/2026-Cancelled</td><td>Cancelled</td><td>8:30 AM</td><td>3433 S Higuera St</td></tr>
        </tbody></table>
        """
        meetings = extract_meetings(source, html, source.meeting_schedule_url, date(2026, 9, 24), 180, "slo_county_meetings")
        self.assertEqual([(item.meeting_date, item.meeting_type) for item in meetings], [(date(2026, 10, 14), "Executive Committee"), (date(2026, 11, 5), "Board Meeting")])
        self.assertEqual(meetings[0].location, "3433 S Higuera St")

    def test_golden_sierra_uses_exact_board_event_detail_links(self) -> None:
        source = BoardSource(
            board_id="golden-sierra-workforce-board",
            board_name="Golden Sierra Workforce Board",
            local_area="Placer region",
            main_website="https://goldensierra.com/",
            meeting_schedule_url="https://goldensierra.com/calendar/category/public-meeting/workforce-board",
            agenda_minutes_url="",
            executive_committee_url="",
            notes="test",
            last_checked_at="",
            confidence="high",
        )
        html = """
        <article class="tribe-events-calendar-month-mobile-events__mobile-event">
          <time datetime="2026-10-15">October 15 @ 12:00 pm - 1:00 pm</time>
          <a href="/event/executive-committee-meeting-13">Executive Committee Meeting</a>
        </article>
        <article class="tribe-events-calendar-month-mobile-events__mobile-event">
          <time datetime="2026-10-15">October 15 @ 1:00 pm - 3:00 pm</time>
          <a href="/event/workforce-development-board-meeting-3">Workforce Development Board Meeting</a>
        </article>
        <article class="tribe-events-calendar-month-mobile-events__mobile-event">
          <time datetime="2026-10-16">October 16 @ 9:00 am</time><a href="/workshop">Job Workshop</a>
        </article>
        """
        meetings = extract_meetings(source, html, source.meeting_schedule_url, date(2026, 9, 24), 180, "golden_sierra_events")
        self.assertEqual(len(meetings), 2)
        executive = next(item for item in meetings if item.meeting_type == "Executive Committee")
        self.assertEqual(executive.source_page_url, "https://goldensierra.com/event/executive-committee-meeting-13")
        self.assertEqual(meetings[0].meeting_type, "Board Meeting")

    def test_agenda_notification_is_deduplicated_by_content_hash(self) -> None:
        meeting = Meeting(
            board_id="test-board",
            board_name="Test Board",
            meeting_type="Board Meeting",
            meeting_date=date(2026, 10, 1),
            start_time=time(9),
            timezone="America/Los_Angeles",
            location="123 Main St",
            virtual_url="",
            source_page_url="https://example.gov/meetings",
            agenda_url="https://example.gov/agenda.txt",
            agenda_label="Agenda",
            confidence_notes="test",
        )
        sent = []
        page = SimpleNamespace(body=b"1. Approval of Minutes\n2. Director Report", content_type="text/plain", url=meeting.agenda_url)
        with TemporaryDirectory() as directory, patch("etl.local_board_meetings.agenda_notifications.fetch_url", return_value=page):
            state = Path(directory) / "notifications.json"
            first, failures = process_agenda_notifications([meeting], state, date(2026, 9, 24), True, sent.append)
            second, second_failures = process_agenda_notifications([meeting], state, date(2026, 9, 24), True, sent.append)
        self.assertEqual((first, second), (1, 0))
        self.assertEqual(failures + second_failures, [])
        self.assertEqual(len(sent), 1)
        self.assertIn("Agenda available:", sent[0]["Subject"])
        self.assertIn(meeting.agenda_url, sent[0].get_body(preferencelist=("plain",)).get_content())
        self.assertIn("approval of minutes", sent[0].get_body(preferencelist=("plain",)).get_content())
        self.assertIn("scheduled to consider", sent[0].get_body(preferencelist=("plain",)).get_content())
        self.assertIn("not actions ultimately taken", sent[0].get_body(preferencelist=("plain",)).get_content())

    def test_conflicting_dated_agenda_is_removed_before_publication(self) -> None:
        meeting = Meeting(
            board_id="test-board",
            board_name="Test Board",
            meeting_type="Executive Committee",
            meeting_date=date(2027, 2, 10),
            start_time=None,
            timezone="America/Los_Angeles",
            location="",
            virtual_url="",
            source_page_url="https://example.gov/meetings",
            agenda_url="https://example.gov/agenda-2.10.21.pdf",
            agenda_label="Agenda",
            confidence_notes="test",
        )
        cleaned = _remove_conflicting_agenda(meeting)
        self.assertEqual(cleaned.agenda_url, "")
        self.assertIn("filename date conflicts", cleaned.confidence_notes)

    def test_agenda_summary_prefers_numbered_items(self) -> None:
        summary = summarize_agenda("Header\n1. Approval of Minutes\n2. Workforce Plan Update\nFooter")
        self.assertEqual(summary[:2], ["1. Approval of Minutes", "2. Workforce Plan Update"])

    def test_agenda_narrative_distinguishes_decisions_reports_and_closed_session(self) -> None:
        narrative = narrate_agenda(
            [
                "Non-Agenda Public Comment",
                "Closed Session",
                "Item 1: Conference with Legal Counsel - Anticipated Litigation",
                "Action Items",
                "Item 2: Approval of August 31, 2026, Minutes",
                "Information Items",
                "Item 3: October Workforce Development Board Agenda",
                "Item 4: Executive Committee Chair Report",
            ],
            "Executive Committee",
        )
        self.assertIn("scheduled to consider approval of August 31, 2026, minutes", narrative)
        self.assertIn("receive or discuss October Workforce Development Board agenda", narrative)
        self.assertIn("closed session is listed concerning anticipated litigation", narrative)
        self.assertIn("opportunity for public comment", narrative)
        self.assertIn("not actions ultimately taken", narrative)

    def test_la_county_profile_excludes_finance_and_news_items(self) -> None:
        source = BoardSource(
            board_id="los-angeles-county-wdb",
            board_name="Los Angeles County WDB",
            local_area="Los Angeles County",
            main_website="https://www.ajcc.lacounty.gov/wdb",
            meeting_schedule_url="https://www.ajcc.lacounty.gov/wdb",
            agenda_minutes_url="https://www.ajcc.lacounty.gov/wdb",
            executive_committee_url="",
            notes="test",
            last_checked_at="",
            confidence="medium",
        )
        html = """
        <p>Jun 02 All Day Los Angeles County Workforce Development Board Finance Committee</p>
        <p>March 20, Los Angeles County Workforce Development Board recordings of the Regular Quarterly meeting</p>
        <p>July 16, 2026 10:00 AM Los Angeles County Workforce Development Board Regular Quarterly Meeting</p>
        """
        meetings = extract_meetings(
            source,
            html,
            source.meeting_schedule_url,
            date(2026, 5, 9),
            180,
            extraction_strategy="la_county_wdb_calendar",
        )
        self.assertEqual([(m.meeting_date, m.meeting_type) for m in meetings], [
            (date(2026, 7, 16), "Board Meeting"),
        ])

    def test_nccc_profile_scopes_2026_wdb_section(self) -> None:
        source = BoardSource(
            board_id="north-central-counties-nccc",
            board_name="North Central Counties (NCCC)",
            local_area="North Central Counties",
            main_website="https://www.northcentralcounties.com/",
            meeting_schedule_url="https://www.northcentralcounties.com/nccc-workforce-development-board",
            agenda_minutes_url="https://www.northcentralcounties.com/nccc-workforce-development-board",
            executive_committee_url="",
            notes="test",
            last_checked_at="",
            confidence="high",
        )
        html = """
        <h2>2026 Workforce Development Board Meetings</h2>
        <p>February 19, 2026</p><a href="/feb-agenda.pdf">Special Meeting Agenda</a>
        <p>May 21, 2026</p>
        <p>August 20, 2026</p>
        <h2>2025 Workforce Development Board Meetings</h2>
        <p>November 6, 2025</p>
        """
        meetings = extract_meetings(
            source,
            html,
            source.meeting_schedule_url,
            date(2026, 5, 9),
            180,
            extraction_strategy="nccc_wdb_schedule",
        )
        self.assertEqual([(m.meeting_date, m.meeting_type) for m in meetings], [
            (date(2026, 5, 21), "Board Meeting"),
            (date(2026, 8, 20), "Board Meeting"),
        ])

    def test_riverside_profile_scopes_schedule_and_skips_canceled(self) -> None:
        source = BoardSource(
            board_id="riverside-county-wdb",
            board_name="Riverside County WDB",
            local_area="Riverside County",
            main_website="https://rivcoworkforce.org/workforce-development-board",
            meeting_schedule_url="https://rivcoworkforce.org/executive-committee",
            agenda_minutes_url="https://rivcoworkforce.org/executive-committee",
            executive_committee_url="https://rivcoworkforce.org/executive-committee",
            notes="test",
            last_checked_at="",
            confidence="high",
        )
        html = """
        <h1>RCWDB Executive Committee</h1>
        <h3>2026 Executive Committee Meeting Schedule</h3>
        <p>April 15, 2026 Canceled</p><p>10:30 am - 11:00 am</p>
        <p>June 17, 2026</p><p>11:00 am to 11:30 am</p><p>1325 Spruce Street, Riverside, CA 92507</p>
        <h3>Agendas/Notes</h3>
        <p>June 17, 2026 Agenda</p><a href="/june.pdf">WDB EC Meeting Agenda PACKET.pdf</a>
        """
        meetings = extract_meetings(
            source,
            html,
            source.executive_committee_url,
            date(2026, 5, 9),
            180,
            extraction_strategy="riverside_wdb_schedule",
        )
        self.assertEqual([(m.meeting_date, m.meeting_type, m.start_time) for m in meetings], [
            (date(2026, 6, 17), "Executive Committee", time(11, 0)),
        ])

    def test_prunes_unseen_future_meetings_for_checked_board(self) -> None:
        conn = connect(__import__("pathlib").Path(":memory:"))
        seen_at = datetime(2026, 5, 9, tzinfo=timezone.utc)
        old = Meeting(
            board_id="sample-wdb",
            board_name="Sample WDB",
            meeting_type="Board Meeting",
            meeting_date=date(2026, 5, 13),
            start_time=None,
            timezone="America/Los_Angeles",
            location="",
            virtual_url="",
            source_page_url="https://example.gov/general-calendar",
            agenda_url="",
            agenda_label="",
            confidence_notes="old false positive",
        )
        current = Meeting(
            board_id="sample-wdb",
            board_name="Sample WDB",
            meeting_type="Board Meeting",
            meeting_date=date(2026, 5, 21),
            start_time=None,
            timezone="America/Los_Angeles",
            location="",
            virtual_url="",
            source_page_url="https://example.gov/workforce-board",
            agenda_url="",
            agenda_label="",
            confidence_notes="current",
        )
        upsert_meetings(conn, [old, current], seen_at)
        deleted = prune_unseen_future_meetings(conn, ["sample-wdb"], [current.stable_id], seen_at)
        self.assertEqual(deleted, 1)
        self.assertEqual([meeting.stable_id for meeting in future_meetings(conn, seen_at)], [current.stable_id])

    def test_agenda_hash_is_stable(self) -> None:
        self.assertEqual(agenda_hash(b"agenda"), agenda_hash(b"agenda"))
        self.assertNotEqual(agenda_hash(b"agenda"), agenda_hash(b"changed agenda"))

    def test_active_meeting_state_retains_unseen_future_meeting(self) -> None:
        observed = Meeting(
            board_id="sample-wdb",
            board_name="Sample WDB",
            meeting_type="Board Meeting",
            meeting_date=date(2026, 11, 5),
            start_time=time(9),
            timezone="America/Los_Angeles",
            location="Board Room",
            virtual_url="",
            source_page_url="https://example.gov/meetings",
            agenda_url="",
            agenda_label="",
            confidence_notes="official schedule",
        )
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "active.json"
            merge_active_meetings(path, [observed], datetime(2026, 9, 24, tzinfo=timezone.utc), date(2026, 9, 24))
            retained = merge_active_meetings(path, [], datetime(2026, 9, 25, tzinfo=timezone.utc), date(2026, 9, 25))
            self.assertEqual(retained, [observed])

    def test_active_meeting_state_updates_agenda_and_drops_past(self) -> None:
        meeting = Meeting(
            board_id="sample-wdb",
            board_name="Sample WDB",
            meeting_type="Board Meeting",
            meeting_date=date(2026, 9, 24),
            start_time=None,
            timezone="America/Los_Angeles",
            location="",
            virtual_url="",
            source_page_url="https://example.gov/meetings",
            agenda_url="",
            agenda_label="",
            confidence_notes="official schedule",
        )
        updated = Meeting(**{**meeting.__dict__, "agenda_url": "https://example.gov/agenda.pdf"})
        with TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "active.json"
            merge_active_meetings(path, [meeting], datetime(2026, 9, 23, tzinfo=timezone.utc), date(2026, 9, 23))
            current = merge_active_meetings(path, [updated], datetime(2026, 9, 24, tzinfo=timezone.utc), date(2026, 9, 24))
            self.assertEqual(current[0].agenda_url, "https://example.gov/agenda.pdf")
            self.assertEqual(merge_active_meetings(path, [], datetime(2026, 9, 25, tzinfo=timezone.utc), date(2026, 9, 25)), [])

    def test_confirmed_profile_meeting_survives_blocked_source(self) -> None:
        source = BoardSource(
            board_id="sample-wdb",
            board_name="Sample WDB",
            local_area="Sample County",
            main_website="https://example.gov",
            meeting_schedule_url="https://example.gov/meetings",
            agenda_minutes_url="",
            executive_committee_url="",
            notes="test",
            last_checked_at="",
            confidence="high",
        )
        profile = SimpleNamespace(
            confirmed_meetings=[
                {
                    "meeting_date": "2026-12-09",
                    "meeting_type": "Board Meeting",
                    "start_time": "09:00",
                    "source_url": "https://example.gov/meetings",
                }
            ]
        )
        meetings = confirmed_profile_meetings(source, profile, date(2026, 9, 24), 180)
        self.assertEqual(len(meetings), 1)
        self.assertEqual(meetings[0].start_time, time(9))

    def test_ventura_google_calendar_ics_filters_and_maps_events(self) -> None:
        source = BoardSource(
            board_id="ventura-county-wdb",
            board_name="Ventura County WDB",
            local_area="Ventura County",
            main_website="https://workforce.venturacounty.gov/",
            meeting_schedule_url="https://calendar.google.com/calendar/ical/example/public/basic.ics",
            agenda_minutes_url="https://workforce.venturacounty.gov/resources/meeting-packets/",
            executive_committee_url="",
            notes="test",
            last_checked_at="",
            confidence="high",
        )
        ics = """BEGIN:VCALENDAR
BEGIN:VEVENT
DTSTART:20261008T160000Z
SUMMARY:WDBVC Full Board Meeting and Strategic Planning
LOCATION:5100 Adolfo Rd\\, Camarillo\\, CA
DESCRIPTION:<a href=\"https://vcportal.ventura.org/wdb/current-meeting-packets/2026-10-08-wdb-meeting-packet.pdf\">Meeting Packet</a>
END:VEVENT
BEGIN:VEVENT
DTSTART:20261008T150000Z
SUMMARY:CANCELED: WDBVC Executive Committee
END:VEVENT
BEGIN:VEVENT
DTSTART:20261009T160000Z
SUMMARY:Performance and Evaluation Committee
END:VEVENT
END:VCALENDAR"""
        meetings = extract_meetings(
            source,
            ics,
            source.meeting_schedule_url,
            date(2026, 9, 24),
            180,
            extraction_strategy="ventura_google_calendar_ics",
        )
        self.assertEqual(len(meetings), 1)
        self.assertEqual(meetings[0].meeting_date, date(2026, 10, 8))
        self.assertEqual(meetings[0].start_time, time(9))
        self.assertEqual(meetings[0].location, "5100 Adolfo Rd, Camarillo, CA")
        self.assertTrue(meetings[0].agenda_url.endswith("2026-10-08-wdb-meeting-packet.pdf"))

    def test_anaheim_civicengage_uses_same_row_agenda_and_skips_canceled(self) -> None:
        source = BoardSource(
            board_id="anaheim-wdb",
            board_name="Anaheim WDB",
            local_area="City of Anaheim",
            main_website="https://www.anaheim.net/",
            meeting_schedule_url="https://www.anaheim.net/AgendaCenter/Workforce-Development-Board-24",
            agenda_minutes_url="https://www.anaheim.net/AgendaCenter/Workforce-Development-Board-24",
            executive_committee_url="",
            notes="test",
            last_checked_at="",
            confidence="high",
        )
        html = """
        <table><tr class="catAgendaRow"><td>Jun 17, 2026 Anaheim Workforce Development Board Meeting
        <a href="/AgendaCenter/ViewFile/Agenda/_06172026-1753">Agenda</a></td></tr>
        <tr class="catAgendaRow"><td>Apr 15, 2026 Meeting-Canceled
        <a href="/AgendaCenter/ViewFile/Agenda/_04152026-1726">Agenda</a></td></tr></table>
        """
        meetings = extract_meetings(
            source,
            html,
            source.meeting_schedule_url,
            date(2026, 6, 10),
            180,
            extraction_strategy="anaheim_civicengage",
        )
        self.assertEqual(len(meetings), 1)
        self.assertEqual(meetings[0].meeting_date, date(2026, 6, 17))
        self.assertEqual(meetings[0].start_time, time(9))
        self.assertIn("_06172026-1753", meetings[0].agenda_url)

    def test_richmond_profile_scopes_agenda_section(self) -> None:
        source = BoardSource(
            board_id="richmond-wdb",
            board_name="Richmond WDB",
            local_area="City of Richmond",
            main_website="https://www.richmondca.gov/671/Richmond-WDB",
            meeting_schedule_url="https://www.richmondca.gov/671/Richmond-WDB",
            agenda_minutes_url="https://www.richmondca.gov/671/Richmond-WDB",
            executive_committee_url="",
            notes="test",
            last_checked_at="",
            confidence="high",
        )
        html = """
        <p>Unrelated plan date November 1, 2026</p>
        <h3>Agenda &amp; Minutes</h3>
        <p><a href="/DocumentCenter/View/79527">May 14, 2026</a></p>
        <p>July 9, 2026 - CANCELLED</p>
        <h3>Purpose</h3>
        """
        meetings = extract_meetings(
            source,
            html,
            source.meeting_schedule_url,
            date(2026, 5, 9),
            180,
            extraction_strategy="richmond_wdb",
        )
        self.assertEqual(len(meetings), 1)
        self.assertEqual(meetings[0].meeting_date, date(2026, 5, 14))
        self.assertEqual(meetings[0].agenda_url, "https://www.richmondca.gov/DocumentCenter/View/79527")

    def test_contra_costa_legistar_uses_subtype_not_generic_body_name(self) -> None:
        source = BoardSource(
            board_id="contra-costa-county-wdb",
            board_name="Contra Costa County WDB",
            local_area="Contra Costa County",
            main_website="https://www.wdbccc.com/",
            meeting_schedule_url="https://contra-costa.legistar.com/Calendar.aspx",
            agenda_minutes_url="https://contra-costa.legistar.com/Calendar.aspx",
            executive_committee_url="",
            notes="test",
            last_checked_at="",
            confidence="high",
        )
        html = """
        <table>
          <tr><td>Workforce Development Board</td><td>9/16/2026</td><td></td><td>12:00 PM</td>
            <td>4071 Port Chicago Highway Zoom: <a href="https://zoom.example/board">join</a><em>Full Board/Executive Committee</em></td>
            <td><a href="View.ashx?M=A&amp;ID=1&amp;GUID=abc">Agenda</a></td></tr>
          <tr><td>Workforce Development Board</td><td>10/21/2026</td><td></td><td>12:00 PM</td>
            <td>4071 Port Chicago Highway<em>Youth Committee</em></td><td></td></tr>
        </table>
        """
        meetings = extract_meetings(
            source,
            html,
            source.meeting_schedule_url,
            date(2026, 9, 10),
            180,
            extraction_strategy="contra_costa_legistar",
        )
        self.assertEqual(len(meetings), 1)
        self.assertEqual(meetings[0].meeting_type, "Board / Executive Committee")
        self.assertEqual(meetings[0].start_time, time(12))
        self.assertEqual(meetings[0].virtual_url, "https://zoom.example/board")
        self.assertIn("M=A", meetings[0].agenda_url)

    def test_san_joaquin_agenda_api_maps_same_record_details(self) -> None:
        source = BoardSource(
            board_id="san-joaquin-county-worknet",
            board_name="San Joaquin County WorkNet",
            local_area="San Joaquin County",
            main_website="https://sjcworknet.org/boards/wdb",
            meeting_schedule_url="https://sjcworknet.org/boards/wdb",
            agenda_minutes_url="https://sjcworknet.org/api/agendas",
            executive_committee_url="",
            notes="test",
            last_checked_at="",
            confidence="high",
        )
        payload = """{"items":[
          {"date":"2026-10-28T00:00:00.000Z","startTime":"2026-10-28T16:00:00.000Z",
           "address":"6221 West Lane","building":"Suite 105","city":"Stockton","stateCode":"CA",
           "urlLink":null,"attachmentLink":"/api/agendas/123/attachment/wdb-agenda.pdf",
           "attachmentFileName":"wdb-agenda.pdf","cancelledAt":null,"deletedAt":null}
        ]}"""
        meetings = extract_meetings(
            source,
            payload,
            "https://sjcworknet.org/api/agendas",
            date(2026, 9, 24),
            180,
            extraction_strategy="san_joaquin_worknet",
        )
        self.assertEqual(len(meetings), 1)
        self.assertEqual(meetings[0].start_time, time(9))
        self.assertEqual(meetings[0].location, "6221 West Lane, Suite 105, Stockton, CA")
        self.assertEqual(meetings[0].agenda_url, "https://sjcworknet.org/api/agendas/123/attachment/wdb-agenda.pdf")

    def test_calendar_event_mapping(self) -> None:
        meeting = Meeting(
            board_id="sample-wdb",
            board_name="Sample WDB",
            meeting_type="Executive Committee",
            meeting_date=date(2026, 5, 14),
            start_time=time(13, 30),
            timezone="America/Los_Angeles",
            location="Virtual",
            virtual_url="https://example.gov/zoom",
            source_page_url="https://example.gov/meetings",
            agenda_url="https://example.gov/agenda.pdf",
            agenda_label="Agenda",
            confidence_notes="high confidence",
        )
        payload = meeting_to_event_payload(meeting, "https://onedrive.live.com/agenda")
        self.assertEqual(payload["subject"], "Sample WDB - Executive Committee")
        self.assertEqual(payload["start"]["dateTime"], "2026-05-14T13:30:00")
        self.assertEqual(payload["start"]["timeZone"], "America/Los_Angeles")
        self.assertIn("sample-wdb:executive-committee:2026-05-14", payload["body"]["content"])

    def test_ics_feed_contains_stable_event(self) -> None:
        meeting = Meeting(
            board_id="sample-wdb",
            board_name="Sample WDB",
            meeting_type="Board Meeting",
            meeting_date=date(2026, 5, 14),
            start_time=time(9, 0),
            timezone="America/Los_Angeles",
            location="Room 1",
            virtual_url="",
            source_page_url="https://example.gov/meetings",
            agenda_url="https://example.gov/agenda.pdf",
            agenda_label="Agenda",
            confidence_notes="test",
        )
        ics = render_ics([meeting], __import__("datetime").datetime(2026, 5, 1, tzinfo=__import__("datetime").timezone.utc))
        self.assertIn("BEGIN:VCALENDAR", ics)
        self.assertIn("NAME:Local Board Meetings", ics)
        self.assertIn("X-WR-CALNAME:Local Board Meetings", ics)
        self.assertIn("UID:sample-wdb:board-meeting:2026-05-14@cwa-local-board-meetings", ics)
        self.assertIn("SUMMARY:Sample WDB - Board Meeting", ics)

    def test_ics_uses_all_day_placeholder_when_time_is_unknown(self) -> None:
        meeting = Meeting(
            board_id="sample-wdb",
            board_name="Sample WDB",
            meeting_type="Board Meeting",
            meeting_date=date(2026, 12, 16),
            start_time=None,
            timezone="America/Los_Angeles",
            location="",
            virtual_url="",
            source_page_url="https://example.gov/meetings",
            agenda_url="",
            agenda_label="",
            confidence_notes="date confirmed; time not published",
        )
        ics = render_ics([meeting], datetime(2026, 9, 24, tzinfo=timezone.utc))
        self.assertIn("DTSTART;VALUE=DATE:20261216", ics)
        self.assertIn("DTEND;VALUE=DATE:20261217", ics)
        self.assertNotIn("T090000", ics)

    def test_html_exposes_subscription_and_download_links(self) -> None:
        meeting = Meeting(
            board_id="sample-wdb",
            board_name="Sample WDB",
            meeting_type="Board Meeting",
            meeting_date=date(2026, 5, 14),
            start_time=time(9, 0),
            timezone="America/Los_Angeles",
            location="Room 1",
            virtual_url="",
            source_page_url="https://example.gov/meetings",
            agenda_url="https://example.gov/agenda.pdf",
            agenda_label="Agenda",
            confidence_notes="test",
        )
        html = render_html([meeting], datetime(2026, 5, 1, tzinfo=timezone.utc))
        self.assertIn("webcal://peckadam.github.io/ca-local-board-meetings/calendar.ics", html)
        self.assertIn("https://peckadam.github.io/ca-local-board-meetings/calendar.ics", html)

    def test_agenda_text_extracts_location_and_virtual_link(self) -> None:
        details = extract_details_from_text(
            """
            Workforce Development Board
            ATTEND IN PERSON
            San Jose Job Center
            1608 Las Plumas Ave, San Jose, CA 95133
            ATTEND VIA ZOOM
            https://sanjoseca.zoom.us/j/123456789?pwd=test
            """
        )
        self.assertIn("1608 Las Plumas Ave", details.location)
        self.assertEqual(details.virtual_url, "https://sanjoseca.zoom.us/j/123456789?pwd=test")

    def test_agenda_location_ignores_where_in_narrative_text(self) -> None:
        details = extract_details_from_text(
            """
            Focus: attracting skilled out-of-market talent to fill jobs where demand eclipses local capacity.
            B. Multicultural Center of Marin Career Fair (Information)
            REGIONAL WORKFORCE DEVELOPMENT BOARD AGENDA
            Primary Meeting Locations:
            Saw Shop Public House - 3825 Main St, Kelseyville, CA
            Marin CareerPoint - Rm 213, Building 27, 1800 Ignacio Blvd, Novato, CA
            """
        )
        self.assertIn("3825 Main St", details.location)
        self.assertNotIn("Multicultural Center", details.location)


if __name__ == "__main__":
    unittest.main()
