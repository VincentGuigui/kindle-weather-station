"""Tests for weather-generator-meteofrance.py (portrait layout, weather-template.svg).

Run directly (``python tests/test_weather_generator_meteofrance.py``) or via pytest.
"""
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN = os.path.join(REPO, "kindle-weather-stand-alone", "extensions", "weather-stand", "bin")
GENERATOR = "weather-generator-meteofrance.py"
TEMPLATE = "weather-template.svg"


def test_portrait_generator():
    resp = harness.build_fake_response(days=4)
    svg, ns, url = harness.run_generator(BIN, GENERATOR, TEMPLATE, resp)

    # 1. request is the keyless, 4-day Open-Meteo call with the configured timezone
    assert url.startswith("https://api.open-meteo.com/v1/forecast"), url
    assert "latitude=48.85" in url and "longitude=2.35" in url
    assert "forecast_days=4" in url
    assert "timezone=Europe%2FParis" in url
    assert "current=temperature_2m,weather_code,wind_speed_10m,wind_direction_10m" in url
    assert "daily=weather_code,temperature_2m_max,temperature_2m_min" in url

    # 2. every placeholder was substituted
    leftover = sorted(set(re.findall(r"VAR_[A-Z0-9_]+", svg)))
    assert not leftover, "unresolved placeholders: %s" % leftover

    # 3. output is well-formed XML
    ET.fromstring(svg.encode("utf-8"))

    # 4. every icon the WMO map can emit is actually defined in the template
    ids = harness.template_icon_ids(BIN, TEMPLATE)
    missing = sorted(set(ns["icon_def"].values()) - ids)
    assert not missing, "icons referenced but missing from template: %s" % missing

    # 5. data sanity
    data = ns["weather_data"]
    assert data["VAR_NOW_ICON"] == "partlycloudy"   # WMO code 2
    assert data["VAR_NOW_TEMP"] == 24               # 24.3 rounded
    assert data["VAR_LOCATION"] == "Paris"          # derived from the timezone name
    assert data["VAR_HOURLY_1_TIME"] == "14:00"     # strip begins at the current hour
    assert data["VAR_DAILY_TOM_DAY"] == "Sunday"    # 2026-06-21
    assert data["VAR_DAILY_3_DAY"] == "N/A"         # beyond the 4-day model window

    # 6. the prefix-sensitive wind line must not be corrupted by the replace loop
    #    (VAR_DAILY_TOM_WIND is a prefix of VAR_DAILY_TOM_WIND_BEARING)
    assert "_BEARING" not in svg
    wind_line = [l for l in svg.splitlines() if "Wind:" in l][0]
    assert re.search(r"Wind:\s*220.*at .*up to", wind_line), wind_line

    print("portrait generator: all checks passed")


if __name__ == "__main__":
    test_portrait_generator()
