import operator
import datetime
import zoneinfo
import argparse
import os
import copy

import tabulate

from client.wnba import HelloClubClient, authenticate

WNBA_ACITIVTY_ID = "5aadd66e87c6b800048a2908"
PACIFIC_AUCKLAND = zoneinfo.ZoneInfo("Pacific/Auckland")


def print_timetable(from_date: datetime.datetime, bookings, events):
    timetable_start = from_date.replace(hour=0)
    timetable_end = from_date.replace(hour=23, minute=30)
    slots = int((timetable_end - timetable_start) / datetime.timedelta(minutes=30))
    time_slots = [
        timetable_start + datetime.timedelta(minutes=30 * i) for i in range(slots)
    ]
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
        name = booking["name"]
        court = booking["court"]
        start_time = booking["start_date"]
        end_time = booking["end_date"]
        slots = int((end_time - start_time) / datetime.timedelta(minutes=30))
        for i in range(slots):
            new_start_time = start_time + datetime.timedelta(minutes=30 * i)
            slot_index = time_slots.index(new_start_time)
            timetable[court][slot_index] = name

    for event in events:
        name = event["name"]
        court = event["court"]
        start_time = event["start_date"]
        end_time = event["end_date"]
        slots = int((end_time - start_time) / datetime.timedelta(minutes=30))
        for i in range(slots):
            new_start_time = start_time + datetime.timedelta(minutes=30 * i)
            slot_index = time_slots.index(new_start_time)
            timetable[court][slot_index] = name

    print(tabulate.tabulate(timetable, headers="keys", tablefmt="grid"))


def print_removed_bookings(from_date: datetime, to_date):
    access_token = authenticate(
        os.environ["HELLO_CLUB_USERNAME"], os.environ["HELLO_CLUB_PASSWORD"]
    )
    client = HelloClubClient(access_token)
    bookings = client.get_bookings(from_date, to_date, is_removed=True)

    bookings = [
        {
            "name": booking["owner"]["name"],
            "email_sent": datetime.datetime.fromisoformat(
                booking["emailConfirmationSent"]
            ).astimezone(PACIFIC_AUCKLAND),
            "start_date": datetime.datetime.fromisoformat(
                booking["startDate"]
            ).astimezone(PACIFIC_AUCKLAND),
            "end_date": datetime.datetime.fromisoformat(booking["endDate"]).astimezone(
                PACIFIC_AUCKLAND
            ),
            "removed_on": datetime.datetime.fromisoformat(
                booking["removedOn"]
            ).astimezone(PACIFIC_AUCKLAND)
            if "removedOn" in booking
            else None,
            "removed_by": (booking.get("removedBy", {}) or {}).get("name"),
            "court": booking["area"]["name"],
        }
        for booking in bookings
        if booking
    ]

    for booking in sorted(bookings, key=operator.itemgetter("email_sent")):
        email_sent = booking["email_sent"].strftime("%Y-%m-%d %H:%M:%S")
        name = booking["name"]
        court = booking["court"]
        start = booking["start_date"].strftime("%H:%M")
        end = booking["end_date"].strftime("%H:%M")
        removed_on = (
            booking["removed_on"].strftime("%Y-%m-%d %H:%M:%S")
            if "removed_on" in booking and booking.get("removed_on")
            else None
        )
        removed_by = booking.get("removed_by")
        print(
            f"{email_sent} {name[:20]: <20} {court}: {start}-{end} (REMOVED {removed_on + ' ' + removed_by if removed_by else ''})"
        )


def print_bookings(from_date: datetime, to_date: datetime):
    access_token = authenticate(
        os.environ["HELLO_CLUB_USERNAME"], os.environ["HELLO_CLUB_PASSWORD"]
    )
    client = HelloClubClient(access_token)
    bookings = client.get_bookings(from_date, to_date)
    events = client.get_events(from_date, to_date)

    bookings = [
        {
            "name": booking["owner"]["name"],
            "court": booking["area"]["name"],
            "start_date": datetime.datetime.fromisoformat(
                booking["startDate"]
            ).astimezone(PACIFIC_AUCKLAND),
            "end_date": datetime.datetime.fromisoformat(booking["endDate"]).astimezone(
                PACIFIC_AUCKLAND
            ),
        }
        for booking in bookings
        if booking
    ]

    events = [
        {
            "name": event["name"],
            "court": area["name"],
            "start_date": datetime.datetime.fromisoformat(
                event["startDate"]
            ).astimezone(PACIFIC_AUCKLAND),
            "end_date": datetime.datetime.fromisoformat(event["endDate"]).astimezone(
                PACIFIC_AUCKLAND
            ),
        }
        for event in events
        for area in event["areas"]
    ]

    print_timetable(from_date, bookings, events)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="bookings")
    parser.add_argument("--from-date", required=False)
    parser.add_argument("--removed", required=False, default=False, action="store_true")

    args = parser.parse_args()

    from_date = (
        datetime.datetime.fromisoformat(args.from_date).replace(tzinfo=PACIFIC_AUCKLAND)
        if args.from_date
        else datetime.datetime.today()
        .replace(hour=0, minute=0, second=0, microsecond=0)
        .astimezone(PACIFIC_AUCKLAND)
    )
    to_date = (
        from_date + datetime.timedelta(days=1) - datetime.timedelta(milliseconds=1)
    ).astimezone(PACIFIC_AUCKLAND)
    print(from_date, to_date, "\n")

    if args.removed:
        print_removed_bookings(from_date, to_date)
    else:
        print_bookings(from_date, to_date)
