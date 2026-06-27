"""Test harness for the Kindle weather generators.

The generators are written for the Kindle's **Python 2** runtime (urllib2, glibc
strftime). This harness lets them be exercised under a normal **Python 3** interpreter
by exec'ing the generator source in a sandbox where the py2-only / device-only calls are
replaced with fakes:

  * ``urllib2.urlopen`` returns a canned Open-Meteo response instead of hitting the network
  * ``urllib.quote`` is stubbed
  * ``open('/sys/.../battery_capacity')`` returns a fake battery reading
  * ``open('.../weather.conf')`` returns a known in-memory config (so tests do not depend
    on whatever weather.conf happens to be on disk)
  * the ``/tmp/weather-latest.svg`` write is captured in memory and returned
  * glibc's ``%-H`` / ``%-I`` strftime flags (unsupported by Windows) are neutralised

It does not modify any project file.
"""
import sys
import os
import io
import json
import types
import codecs
import re
import math
import calendar
from datetime import datetime, timedelta

DEFAULT_CONFIG = {
    "latitude": "48.85",
    "longitude": "2.35",
    "units": "metric",
    "time_format": "24",
    "timezone": "Europe/Paris",
}


def build_fake_response(days=4):
    """A realistic Open-Meteo Meteo-France response. 'now' is 2026-06-20T14:30 local."""
    base = datetime(2026, 6, 20, 0, 0)
    hours, temps, codes, winds = [], [], [], []
    for i in range(days * 24):
        t = base + timedelta(hours=i)
        hours.append(t.strftime("%Y-%m-%dT%H:%M"))
        temps.append(round(15 + 9 * math.sin(i / 24.0 * 2 * math.pi), 1))
        codes.append([0, 1, 2, 3, 61, 80, 95][i % 7])
        winds.append(round(2 + (i % 10) * 0.5, 1))
    return {
        "timezone": "Europe/Paris",
        "current": {"time": "2026-06-20T14:30", "temperature_2m": 24.3,
                    "weather_code": 2, "wind_speed_10m": 3.1, "wind_direction_10m": 210,
                    "surface_pressure": 1013.2},
        "hourly": {"time": hours, "temperature_2m": temps,
                   "weather_code": codes, "wind_speed_10m": winds},
        "daily": {"time": [(base + timedelta(days=d)).strftime("%Y-%m-%d") for d in range(days)],
                  "weather_code": [2, 3, 61, 80][:days],
                  "temperature_2m_max": [26.0, 24.0, 22.0, 23.0][:days],
                  "temperature_2m_min": [15.0, 14.0, 13.0, 14.0][:days],
                  "wind_speed_10m_max": [5.0, 6.0, 7.0, 4.0][:days],
                  "wind_direction_10m_dominant": [200, 220, 180, 90][:days]},
    }


def build_fake_owm_response(days=4):
    """A realistic OpenWeatherMap pair for the /weather + /forecast endpoints.

    The openweathermap generator calls ``urlopen`` twice (current weather, then the
    3-hourly forecast), so this returns a *dispatcher* ``pick(url)`` that the harness
    invokes per request: the ``/data/2.5/weather`` URL gets the current-conditions
    object, ``/data/2.5/forecast`` gets the 3-hour ``list``. 'now' is the same
    2026-06-20 14:30 Europe/Paris instant the Open-Meteo mock uses.
    """
    now_utc = calendar.timegm((2026, 6, 20, 12, 30, 0, 0, 0, 0))  # 14:30 CEST (UTC+2)

    weather = {
        "dt": now_utc,
        "name": "Paris",
        "sys": {"country": "FR"},
        "main": {"temp": 24.3, "temp_max": 26.0, "temp_min": 15.0},
        "weather": [{"id": 802, "description": "scattered clouds", "icon": "02d"}],
        "wind": {"deg": 210, "speed": 3.1},
    }

    # OWM 'icon' codes the generator's icon_def knows how to map.
    cycle = ["01d", "02d", "03d", "04d", "09d", "10d", "11d"]
    desc = {"01d": "clear sky", "02d": "few clouds", "03d": "scattered clouds",
            "04d": "overcast clouds", "09d": "shower rain", "10d": "rain",
            "11d": "thunderstorm"}
    wid = {"01d": 800, "02d": 801, "03d": 802, "04d": 804, "09d": 520, "10d": 500, "11d": 200}

    start = calendar.timegm((2026, 6, 20, 13, 0, 0, 0, 0, 0))  # first slot 15:00 CEST
    slots = []
    for i in range(days * 8):  # OWM returns 3-hour slots -> 8 per day
        ic = cycle[i % len(cycle)]
        temp = round(15 + 9 * math.sin(i / 8.0 * 2 * math.pi), 1)
        slots.append({
            "dt": start + i * 3 * 3600,
            "main": {"temp": temp, "temp_max": round(temp + 2, 1), "temp_min": round(temp - 2, 1)},
            "weather": [{"id": wid[ic], "description": desc[ic], "icon": ic}],
            "wind": {"deg": 200 + (i % 5) * 10, "speed": round(2 + (i % 6) * 0.7, 1)},
        })
    forecast = {"list": slots}

    def pick(url):
        return weather if "data/2.5/weather" in url else forecast

    return pick


class _CaptureIO(io.StringIO):
    def close(self):  # the generator never closes the file; keep getvalue() usable anyway
        pass


def run_generator(bin_dir, generator, template, response, config=None, live=False):
    """Exec a generator under py3 with fakes.

    Returns (svg_text, namespace, request_url) where ``namespace`` is the generator's
    globals after execution (handy for asserting on icon_def / weather_data etc.).

    When ``live=True`` the generator hits the real Open-Meteo API instead of ``response``,
    and reads the real on-disk ``weather.conf`` (your actual coordinates) instead of the
    in-memory test config. The battery file and the ``/tmp`` write are still faked.
    """
    conf = dict(DEFAULT_CONFIG)
    if config:
        conf.update(config)
    conf_text = "".join("%s = %s\n" % (k, v) for k, v in conf.items())
    captured = {}

    class FakeResp:
        def __init__(self, payload):
            self._payload = payload

        def read(self):
            return json.dumps(self._payload)

        def close(self):
            pass

    # Grab the real urlopen now, before we shadow ``urllib``/``urllib2`` in sys.modules below.
    real_urlopen = None
    if live:
        import urllib.request as _ur
        real_urlopen = _ur.urlopen
    orig_mods = {name: sys.modules.get(name) for name in ("urllib", "urllib2")}

    m_urllib2 = types.ModuleType("urllib2")

    def _urlopen(url, *args, **kwargs):   # accept context=... and any other urlopen kwargs
        # ``response`` may be a single object (returned for every call) or a
        # ``pick(url)`` dispatcher for generators that hit multiple endpoints.
        captured["url"] = url
        captured.setdefault("urls", []).append(url)
        if live:
            return real_urlopen(url, context=kwargs.get("context"))
        payload = response(url) if callable(response) else response
        return FakeResp(payload)

    m_urllib2.urlopen = _urlopen
    sys.modules["urllib2"] = m_urllib2
    m_urllib = types.ModuleType("urllib")
    m_urllib.quote = lambda s: s.replace("/", "%2F")
    sys.modules["urllib"] = m_urllib

    import builtins
    real_open = builtins.open

    class FakeBattery:
        def read(self):
            return "88%"

    def fake_open(path, *a, **k):
        sp = str(path)
        if "battery_capacity" in sp:
            return FakeBattery()
        if sp.endswith("weather.conf") and not live:
            return io.StringIO(conf_text)
        return real_open(path, *a, **k)

    real_copen = codecs.open

    def fake_copen(path, *a, **k):
        if str(path).startswith("/tmp/"):
            buf = _CaptureIO()
            captured["svg"] = buf
            return buf
        if path == template:
            return real_copen(os.path.join(bin_dir, template), *a, **k)
        return real_copen(path, *a, **k)

    cwd = os.getcwd()
    builtins.open = fake_open
    codecs.open = fake_copen
    # Put bin/ on the import path so a generator's own imports resolve (the OpenWeatherMap
    # generator does ``import pytz``, which is bundled under bin/).
    path_added = bin_dir not in sys.path
    if path_added:
        sys.path.insert(0, bin_dir)
    try:
        os.chdir(bin_dir)
        src = real_copen(os.path.join(bin_dir, generator), "r", encoding="utf-8").read()
        src = src.replace("%-H", "%H").replace("%-I", "%I")  # Windows strftime has no '-' flag
        ns = {"__name__": "__main__", "__file__": os.path.join(bin_dir, generator)}
        exec(compile(src, generator, "exec"), ns)
    finally:
        os.chdir(cwd)
        builtins.open = real_open
        codecs.open = real_copen
        # Restore urllib/urllib2 so a later real ``import urllib.request`` is not shadowed.
        for name, mod in orig_mods.items():
            if mod is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = mod
        if path_added:
            try:
                sys.path.remove(bin_dir)
            except ValueError:
                pass

    return captured["svg"].getvalue(), ns, captured.get("url")


def template_icon_ids(bin_dir, template):
    text = codecs.open(os.path.join(bin_dir, template), "r", encoding="utf-8").read()
    return set(re.findall(r'id="([a-z0-9-]+)"', text))
