#!/bin/sh
# KUAL action: launch the interactive eips date/time setter.
cd "$(dirname "$0")"
python setclock_ui.py >> /mnt/us/kindle-set-datetime.log 2>&1
