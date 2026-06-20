# Tests

Automated checks for the Kindle weather **generators** (the scripts under
`kindle-weather-stand-alone/extensions/weather-stand/bin/`).

## Why these tests look unusual

The generators run on the Kindle's **Python 2** runtime (they use `urllib2`, the glibc
`strftime` `%-H` flag, and read device files such as the battery gauge). Most development
machines only have **Python 3**, and we don't want the tests to hit the live network or
require a Kindle.

So the tests **exec the generator source inside a Python 3 sandbox** where every
py2-only / device-only call is replaced with a fake. No project file is modified, and the
real generator code is what gets executed — only its outside world is faked.

## Requirements

- Python 3 (standard library only — no third-party packages required)
- `pytest` is optional; the tests also run as plain scripts

## Files

| File | Goal |
| --- | --- |
| `harness.py` | Shared sandbox. Builds realistic responses (`build_fake_response` for Open-Meteo / Météo-France, `build_fake_owm_response` for OpenWeatherMap's two-endpoint `/weather` + `/forecast` pair), fakes `urllib2`/`urllib`, the battery file, `weather.conf`, and the `/tmp` write, then runs a generator and returns the produced SVG plus the generator's globals and the request URL it built. Not a test itself. |
| `test_weather_generator_meteofrance.py` | Tests the **portrait** generator (`weather-generator-meteofrance.py` → `weather-template.svg`). Checks the API request shape, that every `VAR_…` placeholder is substituted, that the output is well-formed XML, that every weather icon the WMO map can emit actually exists in the template, that the data is sane (current conditions, hourly strip starting at "now", days beyond the 4-day model window degrading to `N/A`), and that the prefix-sensitive `Wind:` line is not corrupted by the replace loop. |
| `test_weather_generator_meteofrance_landscape.py` | Tests the **landscape** generator (`weather-generator-meteofrance-landscape.py` → `weather-template-landscape.svg`, 800×600). Checks the request shape, placeholder substitution, well-formed 800×600 XML, that the icon definitions were injected from `weather-template.svg`, the hourly-chart geometry (12 icons aligned to slots, a single temperature curve, dots, time labels, min/max dashed lines, inverted y-axis), and short-window handling. |
| `test_generator_selection.py` | Tests `bin/select-generator.sh`: that `provider` + `layout` in `weather.conf` resolve to the correct generator (e.g. `meteofrance` + `landscape` → the landscape generator). Runs the real shell script via `bash`/`sh`; skips if no POSIX shell is available. |
| `render_preview.py` | Not a pass/fail test — a **visual preview**. Generates a generator's SVG from mock data and rasterizes it to PNG, so you can see what the Kindle would display without a device. See below. |

## What the harness fakes

- `urllib2.urlopen` → returns a canned Open-Meteo Météo-France response (no network)
- `urllib.quote` → stubbed
- `open('/sys/.../battery_capacity')` → fake battery reading
- `open('.../weather.conf')` → a known in-memory config, so results don't depend on the
  `weather.conf` that happens to be on disk
- the `/tmp/weather-latest.svg` write → captured in memory and returned
- glibc `%-H` / `%-I` strftime flags → neutralised (Windows `strftime` rejects them)

## Running

From the repository root:

```sh
# run a single test file directly (prints a one-line pass message, non-zero exit on failure)
python tests/test_weather_generator_meteofrance.py

# or discover and run everything with pytest
pytest tests/
```

## Previewing the rendering

The tests above check that a generator produces a correct **SVG**. To also exercise the
`SVG → PNG` rendering step the Kindle performs — the step that shows as a *white screen*
when the on-device rasterizer fails — use `render_preview.py`. It reuses the same mock
data, writes the SVG to `tests/out/`, then rasterizes it to PNG.

```sh
python tests/render_preview.py                              # meteofrance portrait, 4-day mock
python tests/render_preview.py --generator meteofrance-landscape   # landscape hourly chart
python tests/render_preview.py --generator openweathermap
python tests/render_preview.py --days 2                     # simulate a short forecast window
python tests/render_preview.py --open                       # open the result when done
```

The script picks the first SVG rasterizer it finds — **ImageMagick** (`magick`),
`rsvg-convert`, `inkscape`, or Python `cairosvg`. If none is installed it still writes the
`.svg`, which you can open in any browser.

Outputs land in `tests/out/` (git-ignored).

> **Note:** this is a *close proxy*, not a pixel-exact replica of the device. The Kindle
> renders with its own bundled `rsvg-convert` + `pngcrush`; a dev machine typically uses a
> different rasterizer. It reliably catches layout, template, and data bugs — which is most
> of what breaks — but small rendering differences from the real device are possible.
