"""Tests for select-generator.sh: provider + layout -> generator script.

This is what makes the landscape layout reachable on the device. It runs the real shell
script through a POSIX shell (bash/sh). If no shell is available (e.g. a bare Windows box
without Git Bash) the test skips rather than fails.

Run directly (``python tests/test_generator_selection.py``) or via pytest.
"""
import os
import shutil
import subprocess
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN = os.path.join(REPO, "kindle-weather-stand-alone", "extensions", "weather-stand", "bin")
SCRIPT = os.path.join(BIN, "select-generator.sh")

CASES = [
    ("provider = meteofrance\nlayout = landscape\n", "weather-generator-meteofrance-landscape.py"),
    ("provider = meteofrance\nlayout = portrait\n", "weather-generator-meteofrance.py"),
    ("provider = meteofrance\n", "weather-generator-meteofrance.py"),                 # layout omitted
    ("provider = mf\nlayout = landscape\n", "weather-generator-meteofrance-landscape.py"),  # alias
    ("provider = openweathermap\n", "weather-generator-openweathermap.py"),
    ("provider = openweathermap\nlayout = landscape\n", "weather-generator-openweathermap.py"),  # layout ignored
    ("units = metric\n", "weather-generator-openweathermap.py"),                      # provider missing -> default
    ("# provider = meteofrance\n", "weather-generator-openweathermap.py"),            # commented out -> default
    ("  PROVIDER not a key\nprovider=meteofrance\nlayout=landscape\n",
     "weather-generator-meteofrance-landscape.py"),                                   # whitespace / no spaces
]


def _shell():
    return shutil.which("bash") or shutil.which("sh")


def test_generator_selection():
    shell = _shell()
    if not shell:
        print("SKIP: no POSIX shell (bash/sh) found")
        return

    for conf_text, expected in CASES:
        fd, conf_path = tempfile.mkstemp(suffix=".conf")
        try:
            with os.fdopen(fd, "w") as handle:
                handle.write(conf_text)
            out = subprocess.check_output([shell, SCRIPT, conf_path], cwd=BIN).decode().strip()
            assert out == expected, "conf=%r -> %r (expected %r)" % (conf_text, out, expected)
        finally:
            os.remove(conf_path)

    print("generator selection: all %d cases passed" % len(CASES))


if __name__ == "__main__":
    test_generator_selection()
