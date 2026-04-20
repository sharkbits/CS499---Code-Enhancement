"""Manage timezone-aware clock state for the terminal dashboard.

Provides incremental time controls, real-time ticking, and 12/24-hour string
formatting used by the widget renderer.
"""

from dataclasses import dataclass, field, InitVar
from typing import ClassVar
from datetime import datetime
from zoneinfo import ZoneInfo
import time

HOUR = 3600
MINUTE = 60


# ---------------- CLOCK STATE AND FORMATTERS ----------------


@dataclass
class Clock:
    timezone: InitVar[str]
    x: int = 0
    y: int = 0
    _hours: int = field(default=0, init=False, repr=True)
    _minutes: int = field(default=0, init=False, repr=True)
    _seconds: int = field(default=0, init=False, repr=True)
    _AM_or_PM: str = field(default="", init=False, repr=True)
    _unixtime: float = field(default=0.0, init=False, repr=True)
    font_color: ClassVar[str] = "#ffffff"

    def add_hour(self):
        self._unixtime += HOUR

    def add_minute(self):
        self._unixtime += MINUTE

    def add_second(self):
        self._unixtime += 1

    # checks if a second has passed
    def update_clock(self):
        time_now = time.time()
        # Compare integer seconds so one tick is applied at most once each second.
        if int(time_now) > self._internal_clock:
            self.add_second()
            self._internal_clock = int(time_now)

    def __post_init__(self, timezone: str):
        self._unixtime = datetime.now(ZoneInfo(timezone)).timestamp()
        self._internal_clock = int(time.time())
        self._unix_to_datetime()

    def _unix_to_datetime(self):
        datetime_object = datetime.fromtimestamp(self._unixtime)

        self._hours = datetime_object.hour
        self._minutes = datetime_object.minute
        self._seconds = datetime_object.second

    def _format12hr(self):
        # Convert 0 and 12 both to 12 for standard 12-hour output.
        hours_AM_PM = self._hours % 12 if self._hours % 12 != 0 else 12

        if self._hours > 11:
            self._AM_or_PM = "PM"
        else:
            self._AM_or_PM = "AM"
        return f"{hours_AM_PM}:{self._minutes}:{self._seconds} {self._AM_or_PM}"

    def _format24hr(self):
        return f"{self._hours}:{self._minutes}:{self._seconds}"

    def current_time(self) -> float:
        return self._unixtime

    def get_time_strings(self, is_day: bool):
        self._unix_to_datetime()
        # ClassVar color is shared by all Clock instances.
        if is_day:
            Clock.font_color = "#000000"
        else:
            Clock.font_color = "#ffffff"
        return self._format12hr(), self._format24hr()

    def __ge__(self, other):
        return self._unixtime >= other
