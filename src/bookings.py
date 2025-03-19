from datetime import datetime, timedelta
import zoneinfo
import argparse
import os
import copy
import dataclasses

import tabulate

from client.wnba import HelloClubClient, authenticate

WNBA_ACITIVTY_ID = "5aadd66e87c6b800048a2908"
PACIFIC_AUCKLAND = zoneinfo.ZoneInfo("Pacific/Auckland")


@dataclasses.dataclass
class Booking:
    owner_name: str
    confirmation_email_sent: datetime | None
    start_time: datetime
    end_time: datetime
    court: str
    removed_on: datetime | None
    removed_by: str | None

    def __lt__(self, other: "Booking"):
        if self.confirmation_email_sent and other.confirmation_email_sent:
            return self.confirmation_email_sent < other.confirmation_email_sent
        return self.confirmation_email_sent is not None

    @classmethod
    def from_dict(cls, booking: dict):
        return cls(
            owner_name=booking["owner"]["name"],
            confirmation_email_sent=parse_datetime(booking["emailConfirmationSent"]),
            start_time=parse_datetime(booking["startDate"]),
            end_time=parse_datetime(booking["endDate"]),
            court=booking["area"]["name"],
            removed_on=parse_datetime(booking["removedOn"])
            if booking.get("removedOn")
            else None,
            removed_by=booking.get("removedBy", {}).get("name")
            if booking.get("removedOn")
            else None,
        )


def parse_datetime(dt: str):
    return datetime.fromisoformat(dt).astimezone(PACIFIC_AUCKLAND)


def print_timetable(client: HelloClubClient, from_date: datetime, to_date: datetime):
    bookings = client.get_bookings(from_date, to_date)
    events = client.get_events(from_date, to_date)

    bookings = [Booking.from_dict(booking) for booking in bookings if booking]
    events = [
        Booking(
            owner_name=event["name"],
            confirmation_email_sent=None,
            start_time=parse_datetime(event["startDate"]),
            end_time=parse_datetime(event["endDate"]),
            court=area["name"],
            removed_on=None,
            removed_by=None,
        )
        for event in events
        for area in event["areas"]
    ]

    timetable_start = from_date.replace(hour=0)
    timetable_end = from_date + timedelta(days=1)
    slots = int((timetable_end - timetable_start) / timedelta(minutes=30))
    time_slots = [timetable_start + timedelta(minutes=30 * i) for i in range(slots)]
    slots_list = ["x" for _ in range(slots)]

    timetable = {
        "Time": [time_slot.strftime("%H:%M") for time_slot in time_slots],
        "Court 1": copy.copy(slots_list),
        "Court 2": copy.copy(slots_list),
        "Court 3": copy.copy(slots_list),
        "Court 4": copy.copy(slots_list),
        "Court 5": copy.copy(slots_list),
        "Court 6": copy.copy(slots_list),
    }

    for booking in bookings:
        slots = int((booking.end_time - booking.start_time) / timedelta(minutes=30))
        for i in range(slots):
            new_start_time = booking.start_time + timedelta(minutes=30 * i)
            slot_index = time_slots.index(new_start_time)
            timetable[booking.court][slot_index] = booking.owner_name

    for event in events:
        slots = int((event.end_time - event.start_time) / timedelta(minutes=30))
        for i in range(slots):
            new_start_time = event.start_time + timedelta(minutes=30 * i)
            slot_index = time_slots.index(new_start_time)
            timetable[event.court][slot_index] = event.owner_name

    print(tabulate.tabulate(timetable, headers="keys", tablefmt="grid"))


def print_bookings(client: HelloClubClient, from_date: datetime, to_date: datetime):
    bookings = client.get_bookings(from_date, to_date)
    removed_bookings = client.get_bookings(from_date, to_date, is_removed=True)

    bookings = [Booking.from_dict(booking) for booking in bookings if booking]
    removed_bookings = [
        Booking.from_dict(booking) for booking in removed_bookings if booking
    ]

    for booking in sorted(bookings + removed_bookings):
        email_confirmation = (
            booking.confirmation_email_sent.strftime("%Y-%m-%d %H:%M:%S")
            if booking.confirmation_email_sent
            else ""
        )
        start_time = booking.start_time.strftime("%H:%M:%S")
        end_time = booking.end_time.strftime("%H:%M:%S")
        if booking.removed_on:
            removed_on = booking.removed_on.strftime("%Y-%m-%d %H:%M:%S")
            removed_by = booking.removed_by if booking.removed_by else "UNKNOWN"
            removed_message = f"(REMOVED {removed_on + ' ' + removed_by})"
        else:
            removed_message = ""
        print(
            f"{email_confirmation} {booking.owner_name[:20]: <20} {booking.court}: {start_time}-{end_time} {removed_message}"
        )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="bookings")
    parser.add_argument("--from-date", required=False)
    parser.add_argument("--removed", required=False, default=False, action="store_true")
    parser.add_argument(
        "--timetable", required=False, default=False, action="store_true"
    )

    args = parser.parse_args()

    access_token = authenticate(
        os.environ["HELLO_CLUB_USERNAME"], os.environ["HELLO_CLUB_PASSWORD"]
    )
    client = HelloClubClient(access_token)

    from_date = (
        datetime.fromisoformat(args.from_date).replace(tzinfo=PACIFIC_AUCKLAND)
        if args.from_date
        else datetime.today()
        .replace(hour=0, minute=0, second=0, microsecond=0)
        .astimezone(PACIFIC_AUCKLAND)
    )
    to_date = (from_date + timedelta(days=1) - timedelta(milliseconds=1)).astimezone(
        PACIFIC_AUCKLAND
    )

    print(from_date, to_date, "\n")
    if args.timetable:
        print_timetable(client, from_date, to_date)
    else:
        print_bookings(client, from_date, to_date)
