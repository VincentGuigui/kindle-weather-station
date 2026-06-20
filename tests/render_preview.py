"""Render a generator's SVG to an image on a dev machine, using mock weather data.

This is the *rendering* counterpart to the generation tests: it exercises the same
``SVG -> PNG`` step the Kindle performs (the step that shows as a white screen when the
rasterizer fails), but on this computer with faked weather so no Kindle / network is needed.

It reuses ``harness.run_generator`` (the same mock used by the tests) to produce the SVG,
writes it to ``tests/out/``, then rasterizes it to PNG with whatever rasterizer is
available (ImageMagick ``magick``, ``rsvg-convert``, ``inkscape``, or Python ``cairosvg``).
If none is present it still writes the ``.svg`` (open it in any browser to preview).

Usage:
    python tests/render_preview.py                 # meteofrance generator, 4-day mock
    python tests/render_preview.py --days 2        # simulate the 2-day model window
    python tests/render_preview.py --open          # open the rendered PNG/SVG afterwards
"""
import argparse
import os
import shutil
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import harness

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN = os.path.join(REPO, "kindle-weather-stand-alone", "extensions", "weather-stand", "bin")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")

GENERATORS = {
    # name -> (generator script, template, mock-response builder)
    "meteofrance": ("weather-generator-meteofrance.py", "weather-template.svg",
                    harness.build_fake_response),
    "openweathermap": ("weather-generator-openweathermap.py", "weather-template.svg",
                       harness.build_fake_owm_response),
}


def rasterize(svg_path, png_path):
    """Render svg_path to png_path with the first rasterizer available. Returns the tool name or None."""
    magick = shutil.which("magick")
    if magick:
        # -density 150 oversamples the 600x800 art so text/icons stay crisp, then -resize back.
        subprocess.run([magick, "-background", "white", "-density", "150",
                        svg_path, "-resize", "600x800", png_path], check=True)
        return "ImageMagick"
    rsvg = shutil.which("rsvg-convert")
    if rsvg:
        with open(png_path, "wb") as f:
            subprocess.run([rsvg, "--background-color=white", svg_path], stdout=f, check=True)
        return "rsvg-convert"
    inkscape = shutil.which("inkscape")
    if inkscape:
        subprocess.run([inkscape, svg_path, "--export-type=png",
                        "--export-filename=" + png_path], check=True)
        return "inkscape"
    try:
        import cairosvg
        cairosvg.svg2png(url=svg_path, write_to=png_path, background_color="white")
        return "cairosvg"
    except ImportError:
        return None


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--generator", choices=sorted(GENERATORS), default="meteofrance")
    ap.add_argument("--days", type=int, default=4, help="forecast days in the mock response")
    ap.add_argument("--open", action="store_true", help="open the result when done")
    args = ap.parse_args()

    generator, template, build_response = GENERATORS[args.generator]
    resp = build_response(days=args.days)
    svg, _ns, _url = harness.run_generator(BIN, generator, template, resp)

    os.makedirs(OUT, exist_ok=True)
    svg_path = os.path.join(OUT, "weather-%s.svg" % args.generator)
    png_path = os.path.join(OUT, "weather-%s.png" % args.generator)
    with open(svg_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print("SVG written: %s (%d bytes)" % (svg_path, len(svg.encode("utf-8"))))

    tool = rasterize(svg_path, png_path)
    if tool:
        print("PNG written: %s  (rasterizer: %s)" % (png_path, tool))
        result = png_path
    else:
        print("No SVG rasterizer found (magick / rsvg-convert / inkscape / cairosvg).")
        print("Open the SVG in a browser to preview: %s" % svg_path)
        result = svg_path

    if args.open:
        if sys.platform.startswith("win"):
            os.startfile(result)  # noqa: S606 - dev convenience
        elif sys.platform == "darwin":
            subprocess.run(["open", result])
        else:
            subprocess.run(["xdg-open", result])


if __name__ == "__main__":
    main()
