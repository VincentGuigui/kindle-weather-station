#!/bin/sh
# Enable/disable Wi-Fi via lipc, then rewrite this extension's menu.json so the header shows
# the current state. Pure shell (no Python). KUAL re-reads the menu because it is "dynamic".
#   ./bin/wifi.sh on    -> wirelessEnable 1
#   ./bin/wifi.sh off   -> wirelessEnable 0
#   ./bin/wifi.sh status-> just refresh the displayed state
cd "$(dirname "$0")"
LOG=/mnt/us/kindle-wifi.log

case "$1" in
    on)  /usr/bin/lipc-set-prop com.lab126.cmd wirelessEnable 1 ;;
    off) /usr/bin/lipc-set-prop com.lab126.cmd wirelessEnable 0 ;;
esac

# Current radio state (1/0) and, if available, the connection state.
EN=$(/usr/bin/lipc-get-prop com.lab126.cmd wirelessEnable 2>/dev/null)
CM=$(/usr/bin/lipc-get-prop com.lab126.wifid cmState 2>/dev/null)
case "$EN" in
    1) STATE="ON" ;;
    0) STATE="OFF" ;;
    *) STATE="?" ;;
esac
HEADER="Wi-Fi is: $STATE"
if [ -n "$CM" ]; then HEADER="$HEADER  [$CM]"; fi

[ -d /mnt/us ] && echo "$(date) action=$1 wirelessEnable=$EN cmState=$CM" >> "$LOG" 2>/dev/null

# Regenerate the menu with the current state in the header line.
cat > ../menu.json <<EOF
{
    "items": [
        {
            "name": "$HEADER  (select to refresh)",
            "priority": 0,
            "action": "./bin/wifi.sh",
            "params": "status",
            "exitmenu": false,
            "refresh": true,
            "status": false
        },
        {
            "name": "Turn Wi-Fi ON",
            "priority": 1,
            "action": "./bin/wifi.sh",
            "params": "on",
            "exitmenu": false,
            "refresh": true,
            "status": false
        },
        {
            "name": "Turn Wi-Fi OFF",
            "priority": 2,
            "action": "./bin/wifi.sh",
            "params": "off",
            "exitmenu": false,
            "refresh": true,
            "status": false
        }
    ]
}
EOF
