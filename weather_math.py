"""Fetch and transform weather data for the terminal clock app.

This module geocodes a user location, requests forecast data from Open-Meteo,
and computes colors used for sunrise/sunset background transitions.
"""

import colorsys
from dataclasses import dataclass, field, InitVar
from typing import Any, Callable, ClassVar, Dict, List, Tuple, cast
import requests
import json
from requests import Session
import geopy.exc
from geopy.geocoders import Nominatim
from geopy.location import Location
from widgets_templates import PARTLY_CLOUDY, MOSTLY_CLOUDY

# WEATHER PARAMETER FOR API CALL
API_PARAMETERS = {
    "latitude": "43.6135",
    "longitude": "-116.2035",
    "daily": "sunrise,sunset",
    "hourly": "temperature_2m,precipitation,weather_code,cloud_cover,wind_direction_10m,wind_speed_10m",
    "current": "is_day",
    "timezone": "auto",
    "forecast_days": "1",
    "timeformat": "unixtime",
    "wind_speed_unit": "mph",
    "temperature_unit": "fahrenheit",
    "precipitation_unit": "inch",
}

geolocator = Nominatim(user_agent="clockApp")

TRANSITION_OFFSET = 1800 // 2


# ---------------- WEATHER DATA LOADING AND TRANSFORMS ------------------------


@dataclass
class weather_handler:
    _location_query: InitVar[str]

    def _request_handler(self) -> Dict[str, Any]:
        try:
            with Session() as s:
                response = s.get(
                    "https://api.open-meteo.com/v1/forecast",
                    params=API_PARAMETERS,
                    timeout=10,
                )
                response.raise_for_status()
                return response.json()
        except requests.exceptions.Timeout:
            raise RuntimeError("Weather API request timed out.")
        except requests.exceptions.ConnectionError:
            raise RuntimeError(
                "Unable to connect to weather API. Check your internet connection."
            )
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(f"Weather API returned HTTP {e.response.status_code}.")
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Weather API request failed: {e}")

    def __post_init__(self, _location_query: str):
        # ----- Geocoding --------
        self.location: str = _location_query
        try:
            result = geolocator.geocode(_location_query, exactly_one=True)
            loc = cast(Location | None, result)

            if loc is not None:
                # Re-point API coordinates to the resolved place.
                API_PARAMETERS["latitude"] = loc.latitude
                API_PARAMETERS["longitude"] = loc.longitude
                self.location = loc.address
            else:
                # Keep default coordinates when lookup fails.
                print("[WARN]: Could not resolve location, using default coordinates.")
        except geopy.exc.GeocoderTimedOut:
            print("[WARN]: Geocoder timed out, using default coordinates.")
        except geopy.exc.GeocoderServiceError as e:
            print(f"[WARN]: Geocoder service error ({e}), using default coordinates.")

        self._load_weather_data()

    def _load_weather_data(self) -> None:
        try:
            weather_data: Dict[str, Any] = self._request_handler()

            self.tz_data: str = weather_data["timezone"]

            hourly_events: Dict[str, list] = weather_data["hourly"]
            daily_events: Dict[str, list] = weather_data["daily"]

            self.timeframes: list[float] = [
                float(time) for time in hourly_events["time"]
            ]
            self.precip: list[float] = hourly_events["precipitation"]
            self.weather_code: list[int] = hourly_events["weather_code"]
            self.temps: list[float] = hourly_events["temperature_2m"]
            self.cloud_cover: list[int] = hourly_events["cloud_cover"]
            self.wind_direction: list[int] = hourly_events["wind_direction_10m"]
            self.wind_speed: list[float] = hourly_events["wind_speed_10m"]

            # Stored as Unix timestamps to compare directly with clock time.
            self._transition_data = (
                float(daily_events["sunrise"][0]),
                float(daily_events["sunset"][0]),
            )
            self.current_timeframe: int = 0

        except RuntimeError:
            raise
        except KeyError as e:
            raise RuntimeError(f"Unexpected API response structure, missing key: {e}")

    def refresh(self) -> None:
        self._load_weather_data()

    def get_transition_data(self):
        if not hasattr(self, "_transition_data"):
            raise RuntimeError(
                "Transition data unavailable — weather initialization failed."
            )
        return self._transition_data

    def is_day(self):
        sunrise_time, sunset_time = self._transition_data
        return sunrise_time < self.timeframes[self.current_timeframe] < sunset_time

    def degrees_to_compass(self, degrees: float) -> str:
        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        # Split 360 degrees into 8 sectors and map to the closest heading.
        index = round(degrees / (360 / len(directions))) % len(directions)
        return directions[index]

    def get_cloud_status(self) -> str | None:
        percent = self.cloud_cover[self.current_timeframe]
        # 0-31 clear, 32-69 partly cloudy, 70-94 mostly cloudy.
        if percent <= 31:
            return None
        if percent <= 69:
            return PARTLY_CLOUDY
        if percent <= 94:
            return MOSTLY_CLOUDY
        return None

    def get_weather_dict(self) -> dict:
        idx = self.current_timeframe
        return {
            "loc": self.location,
            "temp": self.temps[idx],
            "wind_dir": self.degrees_to_compass(self.wind_direction[idx]),
            "wind_speed": self.wind_speed[idx],
            "precip": self.precip[idx],
            "cloud_art": self.get_cloud_status() or "",
        }

    def get_current_weather_code(self) -> int:
        return self.weather_code[self.current_timeframe]

    def set_closest_timeframe(self, current_time: float) -> None:
        self.current_timeframe = 0
        for idx, timeframe in enumerate(self.timeframes):
            if timeframe >= current_time:
                # Use the most recent completed hourly bucket.
                self.current_timeframe = idx - 1


# ---------------- BACKGROUND SUNSET/SUNRISE TRANSITIONS ------------------------

DAYLIGHT_COLOR = (66, 135, 245)
NIGHT_COLOR = (5, 5, 20)

SUNRISE_START = ()


class Transition:
    def __init__(
        self,
        start_color: tuple,
        start_time: float,
        duration: float | None = None,
        end_color: tuple | None = None,
    ):
        self.start_color = start_color
        self.end_color = end_color
        self.start_time = start_time
        self.duration = duration

    def apply(self, current_time: float) -> tuple | None:
        if self.end_color is None:
            return self.static_transition(current_time)
        return self.ranged_transition(current_time)

    def ranged_transition(self, current_time: float) -> tuple:
        assert (
            self.end_color is not None and self.duration is not None
        ), "end_color and duration required for a ranged transition"
        progress = (current_time - self.start_time) / self.duration
        # Clamp progression to avoid color channel overshoot.
        progress = max(0.0, min(1.0, progress))

        r = int(
            self.start_color[0] + (self.end_color[0] - self.start_color[0]) * progress
        )
        g = int(
            self.start_color[1] + (self.end_color[1] - self.start_color[1]) * progress
        )
        b = int(
            self.start_color[2] + (self.end_color[2] - self.start_color[2]) * progress
        )

        return (r, g, b)

    def static_transition(self, current_time: float) -> tuple | None:
        return self.start_color if current_time > self.start_time else self.end_color
