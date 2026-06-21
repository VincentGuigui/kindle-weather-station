# Set Date & Time — KUAL extension

Manually set the Kindle's clock with the **buttons only** — no network, no typing. Built for
the case where the clock has drifted/reset and, because of that, Wi-Fi/HTTPS won't work (so
NTP isn't an option). The device's BusyBox has no `ntpd`/`awk`, so the date math is done in
Python (already installed for the weather app); a thin shell wrapper applies it.

## How it works
- **Set Date and Time** launches a full-screen `eips` editor showing `YYYY-MM-DD  HH:MM`
  with a `^` cursor under one digit.
- Controls (5-way d-pad):
  - **left / right** move the cursor between digits;
  - **up / down** increase / decrease the value at that digit's place (year by 1000/100/10/1,
    month/day/hour/minute by 10/1), wrapping/clamping to valid ranges (day clamped to the
    month, leap years included; changing minutes never rolls the hour);
  - **select** (or **back/home**) finishes; it also auto-exits after 90 s of no input.
- Every change is applied **immediately** in UTC (`date -u`) and saved to the RTC
  (`hwclock -u -w`).
- The d-pad is read by grabbing `/dev/input` (`EVIOCGRAB`) so the framework doesn't also act
  on the keys; the grab releases automatically on exit (even on error, when the fds close).

## Timezone
The tool reads and sets the clock with `date -u`, so you are always editing **UTC**
(independent of any device timezone), and it persists to the RTC with `hwclock -u -w`. So
enter your local time minus your UTC offset — e.g. Paris is UTC+2 in summer / UTC+1 in
winter, so local 16:45 (summer) = **14:45** in this menu. This doesn't affect the weather
display: the weather scripts show local time from the Open-Meteo response (your
`timezone = Europe/Paris` setting), not the device clock — the device clock only needs to be
roughly correct so HTTPS/Wi-Fi work.

## Install
1. Copy the whole `kindle-set-datetime` folder into the Kindle's `extensions` folder, i.e.
   `/mnt/us/extensions/kindle-set-datetime/` (drag it onto `E:\extensions\` over USB).
   - To see `E:\` you must be in USB-storage mode; if usbnet is active, disable it first.
2. Eject, reboot if needed, open **KUAL** → **Set Date & Time**.

## Use
1. **KUAL → Set Date and Time.** The current clock appears with a cursor under a digit.
2. **left/right** to pick a digit, **up/down** to change it. Use the high digits (year tens,
   minute tens) for big jumps and the low digits to fine-tune.
3. Press **select** when it's right (changes are already saved); it also auto-exits after 90 s
   idle.

Logs go to `/mnt/us/kindle-set-datetime.log` (`E:\kindle-set-datetime.log`). If the d-pad does
nothing, that log records each `unhandled keycode: N` it sees — send me those numbers and I'll
map them (the arrow codes assumed are the standard 103/108/105/106).

## Files
- `config.xml` — KUAL extension descriptor.
- `menu.json` — single launcher item (`Set Date and Time`).
- `bin/run.sh` — KUAL action; launches the Python UI.
- `bin/setclock_ui.py` — the eips/d-pad editor: draws the field, reads & grabs the d-pad,
  applies each change with `date -u` + `hwclock -u -w`.
