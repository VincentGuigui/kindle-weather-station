"""Tests for weather-generator-meteofrance-landscape.py (800x600 hourly-chart layout).

Run directly (``python tests/test_weather_generator_meteofrance_landscape.py``) or via pytest.
"""
import os
import re
import sys
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN = os.path.join(REPO, "kindle-weather-stand-alone", "extensions", "weather-stand", "bin")
GENERATOR = "weather-generator-meteofrance-landscape.py"
TEMPLATE = "weather-template-landscape.svg"

SVG_NS = "{http://www.w3.org/2000/svg}"
XLINK_NS = "{http://www.w3.org/1999/xlink}"


def _render(days=4):
    return harness.run_generator(BIN, GENERATOR, TEMPLATE, harness.build_fake_response(days))


def test_landscape_renders_cleanly():
    svg, ns, url = _render()

    # 4-day Open-Meteo request, no key
    assert url.startswith("https://api.open-meteo.com/v1/forecast")
    assert "models=meteofrance_seamless" in url  # the actual Meteo-France model, not best_match
    assert "forecast_days=4" in url and "appid" not in url.lower()

    # every placeholder substituted, output is well-formed XML
    leftover = sorted(set(re.findall(r"VAR_[A-Z0-9_]+", svg)))
    assert not leftover, "unresolved placeholders: %s" % leftover
    root = ET.fromstring(svg.encode("utf-8"))
    # Canvas is 600x800 (portrait panel); the 800x600 layout is rotated 90 deg inside it.
    assert root.attrib.get("width") == "600" and root.attrib.get("height") == "800"

    # the icon <defs> were injected from weather-template.svg
    ids = harness.template_icon_ids(BIN, "weather-template.svg")
    assert "fair" in ids and "partlycloudy" in ids
    assert svg.count("<defs>") == 1 and svg.count("</defs>") == 1
    assert 'id="fair"' in svg  # a real icon path made it across


def test_chart_geometry():
    svg, ns, _ = _render()

    n = len(ns["xs"])
    assert n == 12, "expected a 12-hour window, got %d" % n

    # icons aligned to slots: one <use> per slot centred on the slot x (icon_x = x - 50*scale)
    uses = re.findall(r'translate\(([0-9.]+),104\.0\) scale\(0\.40\)"><use xlink:href="#([a-z0-9-]+)"', svg)
    assert len(uses) == n, "expected %d chart icons, found %d" % (n, len(uses))
    for k, (tx, _icon) in enumerate(uses):
        expected = ns["xs"][k] - 50.0 * ns["ICON_SCALE"]
        assert abs(float(tx) - expected) < 0.2, "icon %d misaligned: %s vs %.1f" % (k, tx, expected)

    # exactly one temperature curve, spanning all slots, drawn as a <path> (NOT polyline:
    # the device's old librsvg crashes on poly elements -- undefined symbol g_malloc_n)
    curves = re.findall(r'<path d="M ([^"]+)" fill="none" stroke="#000000" stroke-width="3"', svg)
    assert len(curves) == 1
    assert curves[0].count("L") + 1 == n          # M + (n-1) L commands = n points
    assert "<polyline" not in svg and "<polygon" not in svg

    # a dot and a time label per slot
    assert svg.count('<circle ') == n
    for t in ns["times"]:
        assert (">%s<" % t) in svg, "missing time label %s" % t

    # no min/max reference lines in this layout; the per-point value labels carry the temps,
    # including the window's min and max
    assert "stroke-dasharray" not in svg
    assert (">%d&#176;<" % round(min(ns["temps"]))) in svg
    assert (">%d&#176;<" % round(max(ns["temps"]))) in svg

    # y-axis is inverted (hotter = higher on screen = smaller y) and inside the plot box
    ys = ns["ys"]
    hottest = ns["temps"].index(max(ns["temps"]))
    coldest = ns["temps"].index(min(ns["temps"]))
    assert ys[hottest] < ys[coldest]
    assert all(ns["PLOT_TOP"] <= y <= ns["PLOT_BOTTOM"] for y in ys)


def test_short_window_is_handled():
    # a 1-day mock leaves fewer than 12 hours ahead; the chart must still be valid and full-width
    svg, ns, _ = _render(days=1)
    assert len(ns["xs"]) < 12
    assert abs(ns["xs"][-1] - ns["X1"]) < 0.001  # last point still reaches the right edge
    ET.fromstring(svg.encode("utf-8"))
    assert not re.findall(r"VAR_[A-Z0-9_]+", svg)


if __name__ == "__main__":
    test_landscape_renders_cleanly()
    test_chart_geometry()
    test_short_window_is_handled()
    print("landscape generator: all checks passed")
