#!/bin/sh
# Resolve which generator script to run, from `provider` and `layout` in weather.conf.
# Echoes a single generator filename. Kept separate from weather-generator.sh so the
# selection logic can be unit-tested without running the whole render pipeline.
#
# Usage: select-generator.sh [path-to-weather.conf]   (defaults to ../weather.conf)

CONF="${1:-../weather.conf}"

read_key() {
    # BusyBox-safe parsing for the Kindle:
    #  - this build's grep does NOT support POSIX classes ([[:space:]] matches nothing), so
    #    match the key plainly at the start of the line (keys must not be indented);
    #  - tr -d ' \t\r' trims the value incl. the CR from CRLF-edited files (BusyBox tr also
    #    mishandles '[:space:]', treating it as a literal character set).
    grep "^$1 *=" "$CONF" 2>/dev/null | tail -n 1 | cut -d '=' -f 2 | tr -d ' \t\r'
}

PROVIDER=$(read_key provider)
LAYOUT=$(read_key layout)

case "$PROVIDER" in
    meteofrance|meteo-france|mf)
        case "$LAYOUT" in
            landscape)
                echo weather-generator-meteofrance-landscape.py ;;
            *)
                echo weather-generator-meteofrance.py ;;
        esac ;;
    *)
        # openweathermap (default) has no landscape layout; layout is ignored
        echo weather-generator-openweathermap.py ;;
esac
