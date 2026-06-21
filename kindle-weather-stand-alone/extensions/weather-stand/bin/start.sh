#!/bin/sh

cd "$(dirname "$0")"

# Mode is chosen from the KUAL menu (passed as $1), not from weather.conf:
#   normal (default) - production: stop the UI framework and deep-sleep between updates for
#                      maximum battery life. The device is locked, so you reboot to exit.
#   debug            - leave the UI/framework running and do a single update, so you can
#                      inspect the result and /mnt/us/weather-debug.log with the device still
#                      usable. Press Back to leave.
MODE="${1:-normal}"
REFRESH=3600   # seconds between updates in normal mode (3600 = hourly)

if [ "$MODE" = "debug" ]; then
    /usr/sbin/eips -c
    /usr/sbin/eips 3 20 'Kindle Weather Stand - DEBUG (single update)'
    /usr/sbin/eips 15 24 'Press Back to exit.'
    /usr/bin/lipc-set-prop com.lab126.cmd wirelessEnable 1
    sleep 20
    # weather-manager.sh renders and displays the PNG itself (eips -g) on success, or an
    # error message on failure -- so we leave that on screen and just exit.
    ./weather-manager.sh
    exit 0
fi

# ----- normal (production) -----
# Shutdown as many services as possible
/etc/init.d/framework stop
/etc/init.d/powerd stop
/etc/init.d/phd stop
/etc/init.d/volumd stop
/etc/init.d/lipc-daemon stop
/etc/init.d/tmd stop
/etc/init.d/webreaderd stop
/etc/init.d/browserd stop
killall lipc-wait-event
/etc/init.d/pmond stop
/etc/init.d/cron stop
sleep 5

# Clean up display, show initialisation message
/usr/sbin/eips -c
/usr/sbin/eips -c
/usr/sbin/eips 11 18 'Kindle Weather Stand Project'
/usr/sbin/eips 19 21 'Initialising...'

while true
do
    # Enable WiFi
    /usr/bin/lipc-set-prop com.lab126.cmd wirelessEnable 1
    sleep 30

    # Update weather
    ./weather-manager.sh

    # Disable WiFi, arm the RTC wake alarm, then deep-sleep until it fires
    /usr/bin/lipc-set-prop com.lab126.cmd wirelessEnable 0
    sleep 15
    echo "" > /sys/class/rtc/rtc1/wakealarm
    echo "+$REFRESH" > /sys/class/rtc/rtc1/wakealarm
    echo mem > /sys/power/state
done
