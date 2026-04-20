# CS 499 Clock Application Enhancement

## Project Structure

- **`original src/`** — Original C++ implementation from CS 210: Programming Languages
- **Root directory** — Enhanced Python implementation with weather API integration

## Files

- `main.py` — Application entry point and render loop
- `clock.py` — Clock dataclass with Unix timestamp-based time handling
- `rain.py` — Particle engine for animated weather effects
- `weather_math.py` — Weather API integration and color transition system
- `widgets_templates.py` — Terminal UI widget rendering
- `requirements.txt` — Python dependencies

## Running the Enhanced Version

```bash
pip install -r requirements.txt
python main.py
```

Enter a location when prompted (e.g., "Boise, Idaho").
