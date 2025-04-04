from typing import List
from datetime import datetime, UTC
import logging

import requests

BASE_URL = "https://api.helloclub.com"

# WNBA Specific
ACTIVITY = "5aadd66e87c6b800048a2908"  # Wellington North Badminton Stadium
COURTS = {
    1: "5aadd66e87c6b800048a290d",
    2: "5aadd66e87c6b800048a290e",
    3: "5aadd66e87c6b800048a290f",
    4: "5aadd66e87c6b800048a2910",
    5: "5aadd66e87c6b800048a2911",
    6: "5aadd66e87c6b800048a2912",
}
MODES = {
    "Stadium Pass": "615fcc5a03fdff65ad87ada7",
}


def format_datetime(dt: datetime) -> str:
    return dt.astimezone(UTC).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def authenticate(username: str, password: str) -> str:
    response = requests.post(
        f"{BASE_URL}/auth/token",
        json={
            "username": username,
            "password": password,
            "clientId": "helloclub-client",
            "grantType": "password",
        },
    )
    if response.status_code == 200:
        json_body = response.json()
        token = json_body["access_token"]
        # TODO: Use these to cache tokens
        # Tokens seem to be valid for 12hrs
        # token_type = json_body["token_type"]
        # expires_in = json_body["expires_in"]
        # scope = json_body["scope"]
        return token
    else:
        raise HelloClubAPIError("Failed to authenticate to Hello Club")


class HelloClubAPIError(Exception):
    pass


class HelloClubClient:
    def __init__(self, token: str):
        self._token = token
        self._logger = logging.getLogger("wnba")

    def find_member(self, name: str) -> str:
        response = requests.get(
            f"{BASE_URL}/member/findByName",
            headers={"Authorization": f"Bearer {self._token}"},
            params={"includeStaff": False, "name": name},
        )
        if response.status_code == 200:
            json_body = response.json()
            members = json_body.get("members")
            if len(members) == 1:
                member_id = members[0]["id"]
                self._logger.info(f"Retrieved user details. ({name=}, {member_id=})")
                return member_id

    def get_member_id(self) -> str:
        response = requests.get(
            f"{BASE_URL}/user/me",
            headers={"Authorization": f"Bearer {self._token}"},
        )
        if response.status_code == 200:
            json_body = response.json()
            id = json_body["id"]
            self._logger.info(f"Retrieved logged in user details. ({id=})")
            return id

    def get_bookings(
        self, from_date: datetime, to_date: datetime, is_removed: bool = False
    ):
        response = requests.get(
            f"{BASE_URL}/booking",
            headers={"Authorization": f"Bearer {self._token}"},
            params={
                "activity": ACTIVITY,
                "fromDate": format_datetime(from_date),
                "toDate": format_datetime(to_date),
                "offset": 0,
                "limit": 100,
                "isRemoved": is_removed,
            },
        )
        if response.status_code == 200:
            self._logger.info(f"Retrieved bookings. ({from_date=}, {to_date=})")
            json_body = response.json()
            return json_body["bookings"]

    def get_events(
        self, from_date: datetime, to_date: datetime, is_removed: bool = False
    ):
        response = requests.get(
            f"{BASE_URL}/event",
            headers={"Authorization": f"Bearer {self._token}"},
            params={
                "activity": ACTIVITY,
                "fromDate": format_datetime(from_date),
                "toDate": format_datetime(to_date),
                "isRemoved": is_removed,
            },
        )
        if response.status_code == 200:
            self._logger.info(f"Retrieved events. ({from_date=}, {to_date=})")
            json_body = response.json()
            return json_body["events"]
        else:
            raise HelloClubAPIError

    def book(
        self,
        members: List[str],
        start_date: datetime,
        end_date: datetime,
        court_numer: int,
        reminder: int = 30,
    ) -> str:
        area = COURTS[court_numer]
        response = requests.post(
            f"{BASE_URL}/booking",
            headers={"Authorization": f"Bearer {self._token}"},
            json={
                "members": members,
                "area": area,
                "activity": ACTIVITY,
                "startDate": format_datetime(start_date),
                "endDate": format_datetime(end_date),
                "mode": MODES["Stadium Pass"],
                "recurrence": None,
                "visitors": [],
                "sendConfirmationEmail": False,
                "forOthers": False,
                "reminderTime": reminder,
            },
        )
        if response.status_code == 201:
            self._logger.info(
                f"Booked court. ({court_numer=}, {members=}, {start_date=}, {end_date=})"
            )
            json_body = response.json()
            booking_id = json_body["id"]
            return booking_id
        else:
            self._logger.error(
                f"Failed to book court. ({response.status_code}, {response.text})"
            )

    def validate_booking(
        self,
        members: List[str],
        start_date: datetime,
        end_date: datetime,
        court_numer: int,
    ) -> str:
        area = COURTS[court_numer]
        response = requests.post(
            f"{BASE_URL}/booking/validate",
            headers={
                "Authorization": f"Bearer {self._token}",
            },
            json={
                "activity": ACTIVITY,
                "area": area,
                "members": members,
                "mode": MODES["Stadium Pass"],
                "startDate": format_datetime(start_date),
                "endDate": format_datetime(end_date),
                "visitors": [],
                "forOthers": False,
                "recurrence": None,
            },
        )
        if response.status_code == 200:
            self._logger.info(
                f"Validated booking request. ({court_numer=}, {members=}, {start_date=}, {end_date=})"
            )
            self._logger.debug(
                f"Validate response. ({response.text=})"
            )
            return response.json()
        else:
            self._logger.error(
                f"Failed to validate booking. ({response.status_code}, {response.text=})"
            )
            raise HelloClubAPIError("Failed to validate booking")
