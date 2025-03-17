import logging
import os
import calendar
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from client.wnba import authenticate, HelloClubClient, HelloClubAPIError
from config import get_booking_config

LOGLEVEL = os.getenv("LOGLEVEL", "INFO")
USERNAME = os.getenv("HELLO_CLUB_USERNAME")
PASSWORD = os.getenv("HELLO_CLUB_PASSWORD")
CONFIG_PATH = os.getenv("CONFIG_PATH", "examples/basic.yaml")

logging.basicConfig(level=LOGLEVEL)
logger = logging.getLogger("main")

DAY_OF_WEEK_INDEX = {day_name: idx for idx, day_name in enumerate(calendar.day_name)}


def get_future_bookings(booking_config, lookahead_days: int = 14):
    future_bookings = []
    today = datetime.now()
    for day_index in range(lookahead_days):
        for booking in booking_config:
            day_of_week = DAY_OF_WEEK_INDEX[booking["weekday"]]
            eval_day = today + timedelta(days=lookahead_days - day_index)
            if day_of_week == eval_day.weekday():
                start_time = datetime.strptime(booking["start_time"], "%H:%M")
                end_time = datetime.strptime(booking["end_time"], "%H:%M")
                future_booking = {
                    "start_time": eval_day.replace(
                        hour=start_time.hour,
                        minute=start_time.minute,
                        second=0,
                        microsecond=0,
                        tzinfo=ZoneInfo("Pacific/Auckland"),
                    ),
                    "end_time": eval_day.replace(
                        hour=end_time.hour,
                        minute=end_time.minute,
                        second=0,
                        microsecond=0,
                        tzinfo=ZoneInfo("Pacific/Auckland"),
                    ),
                    "court_number": booking["court"],
                    "members": booking["members"],
                    "mode": booking["mode"],
                }
                future_bookings.append(future_booking)

    return future_bookings


def main():
    booking_config = get_booking_config(CONFIG_PATH)
    future_bookings = get_future_bookings(booking_config)

    token = authenticate(USERNAME, PASSWORD)
    client = HelloClubClient(token)

    for booking in future_bookings:
        start_time = booking["start_time"]
        end_time = booking["end_time"]
        court_number = booking["court_number"]
        members = [client.find_member(member) for member in booking["members"]]
        try:
            client.validate_booking(members, start_time, end_time, court_number)
            # client.book(members, start_time, end_time, court_number)
        except HelloClubAPIError:
            pass
            # TODO: Attempt to book adjacent courts


if __name__ == "__main__":
    main()
