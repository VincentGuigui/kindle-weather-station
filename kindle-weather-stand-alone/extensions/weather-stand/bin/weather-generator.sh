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
    ./rsvg-convert --background-color=white -o /tmp/weather-converted.png /tmp/weather-latest.svg
    rm -f /tmp/weather-latest.svg
    ./pngcrush -c 0 /tmp/weather-converted.png /tmp/weather-crushed.png
    rm -f /tmp/weather-converted.png
    exit 0;
else
    exit 1;
fi
