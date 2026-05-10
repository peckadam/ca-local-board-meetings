from __future__ import annotations

import unittest
from datetime import date, datetime, time, timezone

from etl.local_board_meetings.extraction import extract_agenda_links, extract_meetings, parse_date, parse_time
from etl.local_board_meetings.graph import meeting_to_event_payload
from etl.local_board_meetings.models import BoardSource, Meeting
from etl.local_board_meetings.storage import agenda_hash, connect, future_meetings, prune_unseen_future_meetings, upsert_meetings
from etl.local_board_meetings.web_calendar import render_ics


class LocalBoardMeetingTests(unittest.TestCase):
    def test_parse_common_date_formats(self) -> None:
        self.assertEqual(parse_date("Board Meeting: May 14, 2026 at 9:00 AM"), date(2026, 5, 14))
        self.assertEqual(parse_date("Executive Committee 2026-06-02"), date(2026, 6, 2))
        self.assertEqual(parse_date("Agenda for 7/8/2026"), date(2026, 7, 8))
        self.assertEqual(parse_date("Wednesday, May 13 Agenda", date(2026, 5, 9)), date(2026, 5, 13))

    def test_parse_time(self) -> None:
        self.assertEqual(parse_time("10:30 a.m."), time(10, 30))
        self.assertEqual(parse_time("1 PM"), time(13, 0))
        self.assertEqual(parse_time("Noon to 1:30 p.m."), time(12, 0))
        self.assertEqual(parse_time("9:00 – 10:30AM"), time(9, 0))

    def test_agenda_link_detection(self) -> None:
        html = """
        <a href="/files/2026-05-14-agenda.pdf">May 14, 2026 Board Agenda</a>
        <a href="/contact">Contact</a>
        <a href="packet.pdf">Board Packet</a>
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
        <p>April 9, 2026</p>
        <p>SOUTH BAY WORKFORCE INVESTMENT BOARD</p>
        <p>April 16, 2026</p>
        <p>YOUTH DEVELOPMENT COUNCIL COMMITTEE</p>
        <p>May 5, 2026</p>
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
        self.assertEqual([m.meeting_type for m in meetings], ["Executive Committee", "Board Meeting", "Committee"])

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
        <p>May 20, 2026 (8:30 a.m)</p>
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
        self.assertIn("UID:sample-wdb:board-meeting:2026-05-14@cwa-local-board-meetings", ics)
        self.assertIn("SUMMARY:Sample WDB - Board Meeting", ics)


if __name__ == "__main__":
    unittest.main()
