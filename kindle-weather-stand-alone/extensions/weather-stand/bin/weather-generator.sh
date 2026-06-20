#!/bin/sh

cd "$(dirname "$0")"

# Select the weather data source from weather.conf (provider = openweathermap | meteofrance).
# Falls back to openweathermap when the key is missing or unrecognised, so existing setups
# keep working unchanged.
PROVIDER=$(grep -E '^[[:space:]]*provider[[:space:]]*=' ../weather.conf 2>/dev/null | tail -n 1 | cut -d '=' -f 2 | tr -d '[:space:]')
case "$PROVIDER" in
    meteofrance|meteo-france|mf)
        GENERATOR=weather-generator-meteofrance.py ;;
    *)
        GENERATOR=weather-generator-openweathermap.py ;;
esac

LOG=/mnt/us/weather-debug.log
echo "=== weather-generator diagnostic ===" > $LOG
echo "pwd: $(pwd)" >> $LOG
echo "provider: ${PROVIDER:-(default)} -> $GENERATOR" >> $LOG
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
