"""Run the terminal clock application loop.

This module wires together clock state, weather data, particle effects, and
full-screen terminal rendering for the interactive dashboard.
"""

import sys

from typing import Any, Dict
from datetime import datetime
from clock import Clock, time
from rain import ParticleEngine
from blessed import Terminal
from widgets_templates import get_widget, get_widget_dimensions
import json
from weather_math import (
    weather_handler,
    Transition,
    TRANSITION_OFFSET,
    DAYLIGHT_COLOR,
    NIGHT_COLOR,
)

TRANSITIONS: tuple = ()


# ---------------- APPLICATION RENDER LOOP ----------------


class App(Terminal):

    BACKGROUND_COLOR: tuple = DAYLIGHT_COLOR

    def __init__(self, clock_instance: Clock, weather_handle: weather_handler):
        super().__init__()
        print(f"Terminal type: {self.kind}")
        print(f"Number of colors supported: {self.number_of_colors}")

        is_truecolor = self.number_of_colors >= 1 << 24
        if not is_truecolor:
            raise RuntimeError(
                "Your terminal does not support color feature required. Please try a different terminal or emulator."
            )

        # Character buffer used to compose each frame before styling.
        self.canvas = [[" " for _ in range(self.width)] for _ in range(self.height)]

        # Set the clock position
        WIDGET_WIDTH, WIDGET_HEIGHT = get_widget_dimensions()
        clock_instance.x = (self.width // 2) - (WIDGET_WIDTH // 2)
        clock_instance.y = (self.height // 2) - (WIDGET_HEIGHT // 2)
        self.clock_instance = clock_instance

        # -------- Particles ------------
        self.PE: ParticleEngine = ParticleEngine(self.width, self.height)
        self._last_weather_code: int = -1

        self.weather: weather_handler = weather_handle
        self._last_date = datetime.fromtimestamp(clock_instance.current_time()).date()
        self._apply_weather_particles()

    # ---------------- WEATHER-DRIVEN VISUAL STATE ----------------

    def _check_weather_condition(self):
        current_time = self.clock_instance.current_time()
        color = None
        # Iterate from latest transition to earliest and select first match.
        for transition in reversed(TRANSITIONS):
            if current_time >= transition.start_time:
                color = transition.apply(current_time)
                break
        App.BACKGROUND_COLOR = color if color is not None else NIGHT_COLOR

    def _midnight_check(self):
        today = datetime.fromtimestamp(self.clock_instance.current_time()).date()
        if today == self._last_date:
            return
        self._last_date = today
        self.weather.refresh()
        global TRANSITIONS
        sunrise, sunset = self.weather.get_transition_data()
        # Rebuild sunrise/sunset transition sequence for the new day.
        TRANSITIONS = (
            Transition(
                NIGHT_COLOR,
                sunrise - TRANSITION_OFFSET,
                TRANSITION_OFFSET * 2,
                DAYLIGHT_COLOR,
            ),
            Transition(DAYLIGHT_COLOR, sunrise + TRANSITION_OFFSET),
            Transition(
                DAYLIGHT_COLOR,
                sunset - TRANSITION_OFFSET,
                TRANSITION_OFFSET * 2,
                NIGHT_COLOR,
            ),
            Transition(NIGHT_COLOR, sunset + TRANSITION_OFFSET),
        )

    # WMO weather-code groups mapped to particle presets.
    _RAIN_LIGHT = {51, 53, 61, 63, 80, 81}
    _RAIN_HEAVY = {55, 65, 82, 95, 96, 99}
    _SNOW = {71, 73, 75, 77, 85, 86}

    def _apply_weather_particles(self):
        code = self.weather.get_current_weather_code()
        if code == self._last_weather_code:
            return
        self._last_weather_code = code
        if code in self._RAIN_LIGHT:
            self.PE.configure("|", 2.0, 15)
        elif code in self._RAIN_HEAVY:
            self.PE.configure("|", 5.0, 40)
        elif code in self._SNOW:
            self.PE.configure("*", 0.2, 20)
        else:
            self.PE.configure(" ", 0.0, 0)

    def on_resize(self):
        self.canvas = [
            [self.on_color_rgb(*self.BACKGROUND_COLOR)(" ") for _ in range(self.width)]
            for _ in range(self.height)
        ]

    # ---------------- MAIN INPUT/UPDATE/RENDER LOOP ----------------

    def run_loop(self):
        with self.cbreak(), self.hidden_cursor():
            print(self.clear)

            while True:
                # --- INPUT ---
                key = self.inkey(timeout=0.3)
                if key == "4":
                    break
                elif key == "1":
                    self.clock_instance.add_hour()
                elif key == "2":
                    self.clock_instance.add_minute()
                elif key == "3":
                    self.clock_instance.add_second()

                self._check_weather_condition()
                self._midnight_check()
                self.clock_instance.update_clock()

                # Update dimensions in case of resize
                w, h = self.width, self.height
                if len(self.canvas) != h or len(self.canvas[0]) != w:
                    self.canvas = [[" " for _ in range(w)] for _ in range(h)]

                # --- RESET BUFFER ---
                for row in self.canvas:
                    for x in range(w):
                        row[x] = " "

                # --- UPDATE & DRAW ---
                self.PE.update_particles(self.canvas)

                # --- Render Particles  ---
                styled_rows = []
                for row in self.canvas:
                    styled_row = self.on_color_rgb(*self.BACKGROUND_COLOR)("".join(row))
                    styled_rows.append(styled_row)

                frame_output = "\n".join(styled_rows)

                # term.home moves cursor to 0,0; term.clear_eos handles resizing cleanup
                sys.stdout.write(self.home + frame_output + self.clear_eos)

                time12, time24 = self.clock_instance.get_time_strings(
                    bool(self.weather.is_day())
                )

                self.weather.set_closest_timeframe(self.clock_instance.current_time())
                self._apply_weather_particles()
                widget_text = get_widget(
                    weather_data=self.weather.get_weather_dict(),
                    time12=time12,
                    time24=time24,
                )

                # ------------- Render Widget -----------------

                for y_offset, line in enumerate(widget_text):
                    # Move cursor to widget coordinates and print one line.
                    with self.location(
                        self.clock_instance.x, self.clock_instance.y + y_offset
                    ):
                        sys.stdout.write(
                            self.on_color_rgb(*self.BACKGROUND_COLOR)(
                                self.color_hex(self.clock_instance.font_color)(line)
                            )
                        )
                sys.stdout.write(self.home)
                sys.stdout.flush()

        print(self.normal + self.clear)

    # ---------------- PROGRAM ENTRYPOINT ----------------


if __name__ == "__main__":
    try:

        user_input = input("Enter a location:")
        weather_instance = weather_handler(user_input)

        sunrise, sunset = weather_instance.get_transition_data()
        TRANSITIONS = (
            Transition(
                NIGHT_COLOR,
                sunrise - TRANSITION_OFFSET,
                TRANSITION_OFFSET * 2,
                DAYLIGHT_COLOR,
            ),  # sunrise ranged
            Transition(DAYLIGHT_COLOR, sunrise + TRANSITION_OFFSET),  # daytime static
            Transition(
                DAYLIGHT_COLOR,
                sunset - TRANSITION_OFFSET,
                TRANSITION_OFFSET * 2,
                NIGHT_COLOR,
            ),  # sunset ranged
            Transition(NIGHT_COLOR, sunset + TRANSITION_OFFSET),  # nighttime static
        )

        my_clock = Clock(weather_instance.tz_data)

        app = App(my_clock, weather_instance)
        app.run_loop()
    except KeyboardInterrupt:
        pass
    finally:
        print("Program has ended")
