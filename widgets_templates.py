"""Build terminal widget text for clock, weather, and menu panels.

Includes ANSI-styled cloud art and helper utilities for formatting fixed-width
sections that render cleanly inside the full-screen dashboard.
"""

import re
from string import Template

# ANSI escape sequences encode colored cloud background blocks.
PARTLY_CLOUDY = "  \x1b[48;5;255m          \x1b[0m                  \x1b[48;5;255m        \x1b[0m                  \x1b[48;5;255m          \x1b[0m  \n \x1b[48;5;231m  \x1b[0m\x1b[48;5;255m            \x1b[0m              \x1b[48;5;255m          \x1b[0m              \x1b[48;5;255m            \x1b[0m \n    \x1b[48;5;255m        \x1b[0m                  \x1b[48;5;255m            \x1b[0m                 \x1b[48;5;255m        \x1b[0m    "

MOSTLY_CLOUDY = "         \x1b[48;5;255m          \x1b[0m\x1b[48;5;255m              \x1b[0m          \n    \x1b[48;5;255m    \x1b[0m\x1b[48;5;231m                \x1b[0m\x1b[48;5;255m    \x1b[0m\x1b[48;5;255m    \x1b[0m\x1b[48;5;231m                    \x1b[0m\x1b[48;5;255m    \x1b[0m   \n \x1b[48;5;255m  \x1b[0m\x1b[48;5;231m                      \x1b[0m\x1b[48;5;255m  \x1b[0m\x1b[48;5;255m  \x1b[0m\x1b[48;5;231m                            \x1b[0m\x1b[48;5;255m  \x1b[0m \n \x1b[48;5;252m  \x1b[0m\x1b[48;5;255m                      \x1b[0m\x1b[48;5;252m  \x1b[0m\x1b[48;5;252m  \x1b[0m\x1b[48;5;255m                            \x1b[0m\x1b[48;5;252m  \x1b[0m \n \x1b[48;5;248m   \x1b[0m\x1b[48;5;252m                    \x1b[0m\x1b[48;5;248m   \x1b[0m\x1b[48;5;248m    \x1b[0m\x1b[48;5;252m                        \x1b[0m\x1b[48;5;248m    \x1b[0m \n  \x1b[48;5;244m                        \x1b[0m\x1b[48;5;240m                                \x1b[0m "

CLOCK_TEMPLATE = Template(
    """
 ___________________________________
|   12hr time     |   24hr time     |
|-----------------|-----------------|
| $hour_12 | $hour_24 |
|-----------------|-----------------|"""
)

_W_INNER = 35  # inner width between the | pipes

MENU = """
***********************************
* 1. Add an hour                  *
* 2. Add an minute                *
* 3. Add an Second                *
* 4. Exit program                 *
***********************************
"""

# ---------------- RENDERING UTILITIES ----------------

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def set_clock_data(time12: str, time24: str) -> str:
    return CLOCK_TEMPLATE.safe_substitute(
        hour_12=time12.center(15),
        hour_24=time24.center(15),
    )


def set_weather_data(data: dict) -> str:
    loc = f"Location: {data.get('loc', '')}"
    temp_wind = f"Temp: {data.get('temp', '')} F  Wind: {data.get('wind_dir', '')} @ {data.get('wind_speed', '')} mph"
    precip = f"Precip: {data.get('precip', '')} in"

    border = " " + "=" * _W_INNER + " "

    def row(text: str) -> str:
        if len(text) > _W_INNER:
            # Truncate oversized content to keep the frame width stable.
            text = text[: _W_INNER - 1] + "…"
        return "|" + text.center(_W_INNER) + "|"

    return (
        "\n"
        + border
        + "\n"
        + row(loc)
        + "\n"
        + row(temp_wind)
        + "\n"
        + row(precip)
        + "\n"
        + border
        + "\n"
    )


def get_widget(weather_data: dict, time12: str, time24: str) -> list[str]:
    cloud_art = weather_data.get("cloud_art", "")
    # Cloud art, when present, is rendered above the clock/weather box.
    prefix = cloud_art + "\n" if cloud_art else ""
    widget_text = (
        prefix + set_clock_data(time12, time24) + set_weather_data(weather_data) + MENU
    )
    return widget_text.splitlines(keepends=True)


def get_widget_dimensions() -> tuple[int, int]:
    dummy = get_widget({}, "", "")
    lines = "".join(dummy).splitlines()
    # Strip ANSI color codes so width reflects visible characters only.
    width = max(len(_ANSI_RE.sub("", line)) for line in lines)
    height = len(lines)
    return width, height
