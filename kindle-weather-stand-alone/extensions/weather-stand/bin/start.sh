#!/bin/sh

cd "$(dirname "$0")"

# Refresh interval in seconds (3600 = hourly). Used both for the deep-sleep RTC alarm and
# the light-sleep fallback below.
REFRESH=3600

# buttons = disabled (default) stops the UI framework and deep-sleeps between updates for
# maximum battery life -- the Kindle buttons and USB stay dead until you reboot. buttons =
# enabled keeps the framework running and uses a light sleep instead, so the buttons remain
# usable (at the cost of battery life).
# tr -d ' \t\r' (not '[:space:]'): BusyBox tr treats '[:space:]' as a literal character set.
BUTTONS=$(grep -E '^[[:space:]]*buttons[[:space:]]*=' ../weather.conf 2>/dev/null | tail -n 1 | cut -d '=' -f 2 | tr -d ' \t\r')

# Shutdown as many services as possible
if [ "$BUTTONS" != "enabled" ]; then
    /etc/init.d/framework stop
fi
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
    
    # Disable WiFi, then wait for the next refresh
    /usr/bin/lipc-set-prop com.lab126.cmd wirelessEnable 0
    sleep 15
    if [ "$BUTTONS" != "enabled" ]; then
        # Deep sleep: arm the RTC wake alarm (seconds) then suspend until it fires.
        # Buttons cannot wake the device in this mode.
        echo "" > /sys/class/rtc/rtc1/wakealarm
        echo "+$REFRESH" > /sys/class/rtc/rtc1/wakealarm
        echo mem > /sys/power/state
    else
        # Keep the device awake so the buttons stay responsive; just wait the interval.
        sleep "$REFRESH"
    fi
done
