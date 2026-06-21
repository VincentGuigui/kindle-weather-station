#!/bin/sh

cd "$(dirname "$0")"

# Select the generator from weather.conf (provider = openweathermap | meteofrance,
# layout = portrait | landscape). The logic lives in select-generator.sh so it can be tested.
GENERATOR=$(sh select-generator.sh ../weather.conf)

LOG=/mnt/us/weather-debug.log
echo "=== weather-generator diagnostic ===" > $LOG
echo "pwd: $(pwd)" >> $LOG
echo "generator: $GENERATOR" >> $LOG
echo "which python: $(which python 2>&1)" >> $LOG
echo "python version:" >> $LOG
python --version >> $LOG 2>&1
echo "--- pytz import test (only required by openweathermap) ---" >> $LOG
python -c "import pytz; print('pytz OK: ' + pytz.__file__); import pytz; tz=pytz.timezone('Europe/Paris'); print('Europe/Paris OK')" >> $LOG 2>&1
echo "--- running $GENERATOR ---" >> $LOG
python "$GENERATOR" >> $LOG 2>&1
echo "--- generator exit code: $? ---" >> $LOG
echo "--- /tmp/weather-latest.svg present? ---" >> $LOG
ls -la /tmp/weather-latest.svg >> $LOG 2>&1
sync   # IMPORTANT: flush log to disk so a reboot doesn't lose it
# ---- END DIAGNOSTIC ----

# The script should output a svg file in tmp directory, check before conversion
if [ -e /tmp/weather-latest.svg ]; then
    # Keep a copy of the SVG on /mnt/us so it can be inspected over USB
    cp /tmp/weather-latest.svg /mnt/us/weather-latest.svg

    ./rsvg-convert --background-color=white -o /tmp/weather-converted.png /tmp/weather-latest.svg
    RSVG_RC=$?
    ./pngcrush -c 0 /tmp/weather-converted.png /tmp/weather-crushed.png
    PNGCRUSH_RC=$?

    # Diagnostics for the conversion step (runs after the block above) + keep a copy of the PNG
    echo "--- conversion ---" >> $LOG
    echo "rsvg-convert exit: $RSVG_RC" >> $LOG
    echo "pngcrush exit: $PNGCRUSH_RC" >> $LOG
    ls -la /tmp/weather-converted.png /tmp/weather-crushed.png >> $LOG 2>&1
    cp /tmp/weather-crushed.png /mnt/us/weather-latest.png 2>/dev/null
    sync

    rm -f /tmp/weather-latest.svg /tmp/weather-converted.png
    # Exit non-zero if the PNG was not produced, so weather-manager.sh reports the failure
    # instead of silently displaying a missing/blank image.
    if [ -e /tmp/weather-crushed.png ]; then exit 0; else exit 1; fi
else
    exit 1;
fi
