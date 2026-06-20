#!/bin/sh
# Resolve which generator script to run, from `provider` and `layout` in weather.conf.
# Echoes a single generator filename. Kept separate from weather-generator.sh so the
# selection logic can be unit-tested without running the whole render pipeline.
#
# Usage: select-generator.sh [path-to-weather.conf]   (defaults to ../weather.conf)

CONF="${1:-../weather.conf}"

read_key() {
    grep -E "^[[:space:]]*$1[[:space:]]*=" "$CONF" 2>/dev/null | tail -n 1 | cut -d '=' -f 2 | tr -d '[:space:]'
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
