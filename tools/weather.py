"""Weather tool — current conditions via the free Open-Meteo API.

No API key required. Two HTTP calls per invocation:
  1. Geocoding API to resolve `location` (a free-text place name) to lat/lon.
  2. Forecast API for the current weather at that point.

Open-Meteo returns weather as a numeric WMO code, which we map to a short
human-readable condition string here. `httpx` honours `HTTPS_PROXY` via
its default `trust_env=True`, so the corporate proxy is picked up
automatically when running locally.
"""

from __future__ import annotations

import json
import sys

import httpx
from langchain_core.tools import tool


_GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"
_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
_TIMEOUT_S = 10.0


# ============================================================
# WMO weather-code → short human-readable condition
# https://open-meteo.com/en/docs#weather_variable_documentation
# ============================================================
_WEATHER_CODE_MAP: dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def _condition_from_code(code: int) -> str:
    return _WEATHER_CODE_MAP.get(code, "Unknown")


# ============================================================
# Tool
# ============================================================
@tool
def get_weather(location: str, unit: str = "celsius") -> str:
    """Get the current weather for a city or place using Open-Meteo.

    Use this whenever the user asks about current weather, temperature,
    or sky conditions for a specific location. Do NOT use this tool for
    historical weather, multi-day forecasts, or climate questions — only
    "right now" conditions.

    Args:
        location: City or place name, preferably in English (e.g. "Tokyo",
            "Berlin", "Shanghai", "New York"). The geocoder also accepts
            many local-language spellings, but English is most reliable.
        unit: "celsius" (default) or "fahrenheit".

    Returns:
        A JSON string of the form
            `{"location": "<name>, <country>", "temperature": <n>,
              "unit": "celsius|fahrenheit", "condition": "<text>",
              "wind_speed_kmh": <n>}`
        or `{"error": "<message>"}` on failure.
    """
    temp_unit = "fahrenheit" if unit.lower().startswith("f") else "celsius"

    try:
        # Step 1 — geocode the place name to coordinates.
        geo_resp = httpx.get(
            _GEOCODING_URL,
            params={"name": location, "count": 1, "language": "en", "format": "json"},
            timeout=_TIMEOUT_S,
        )
        geo_resp.raise_for_status()
        geo_data = geo_resp.json()
        results = geo_data.get("results") or []
        if not results:
            return json.dumps({"error": f"Location '{location}' not found"})

        place = results[0]
        lat = place["latitude"]
        lon = place["longitude"]
        place_name = place["name"]
        country = place.get("country", "")

        # Step 2 — fetch current weather for those coordinates.
        weather_resp = httpx.get(
            _FORECAST_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "current_weather": "true",
                "temperature_unit": temp_unit,
            },
            timeout=_TIMEOUT_S,
        )
        weather_resp.raise_for_status()
        current = weather_resp.json().get("current_weather") or {}
        if not current:
            return json.dumps({"error": "Open-Meteo returned no current_weather block"})

        return json.dumps(
            {
                "location": f"{place_name}, {country}".strip(", "),
                "temperature": round(float(current["temperature"]), 1),
                "unit": temp_unit,
                "condition": _condition_from_code(int(current["weathercode"])),
                "wind_speed_kmh": round(float(current["windspeed"]), 1),
            }
        )
    except httpx.HTTPError as e:
        err_msg = f"Weather API HTTP error for '{location}': {type(e).__name__}: {e}"
        print(f"[tools.weather] {err_msg}", file=sys.stderr, flush=True)
        return json.dumps({"error": err_msg})
    except Exception as e:  # noqa: BLE001 — surface any failure to the agent
        err_msg = f"Weather lookup failed for '{location}': {type(e).__name__}: {e}"
        print(f"[tools.weather] {err_msg}", file=sys.stderr, flush=True)
        return json.dumps({"error": err_msg})
