# Wi-Fi On / Off — KUAL extension

Turn the Kindle's Wi-Fi radio on or off from KUAL, using `lipc` — **pure shell, no Python**.
Handy because the weather loop deliberately disables Wi-Fi, and a usable Wi-Fi toggle is the
quickest way to get the radio back for SSH/updates without rebooting.

## How it works
- KUAL shows three items, navigated with the 5-way:
  - `Wi-Fi is: <state>  (select to refresh)` — a live status line
  - `Turn Wi-Fi ON`
  - `Turn Wi-Fi OFF`
- Selecting ON/OFF runs `/usr/bin/lipc-set-prop com.lab126.cmd wirelessEnable 1` (or `0`).
- It then reads the current state back (`lipc-get-prop com.lab126.cmd wirelessEnable`, plus
  `com.lab126.wifid cmState` for the connection state) and **rewrites `menu.json`** so the
  status line reflects reality. The menu is `dynamic`, so KUAL re-reads it on each press.
- No Python and no input parsing — KUAL handles the d-pad/selection.

## Install
1. Copy the `kindle-wifi-toggle` folder into the Kindle's `extensions` folder:
   `/mnt/us/extensions/kindle-wifi-toggle/` (drag onto `E:\extensions\` over USB; you must be
   in USB-storage mode, so disable usbnet first if it's active).
2. Eject, reboot if needed, open **KUAL → Wi-Fi On / Off**.

## Use
Open it, select **Turn Wi-Fi ON** (or OFF). The top line updates to e.g.
`Wi-Fi is: ON  [CONNECTED]`. Select the status line any time to refresh it.

A log is written to `/mnt/us/kindle-wifi.log` (`E:\kindle-wifi.log`).

## Files
- `config.xml` — KUAL extension descriptor.
- `menu.json` — the three-item menu (rewritten by `wifi.sh` to show the current state).
- `bin/wifi.sh` — sets `wirelessEnable` via `lipc`, reads the state back, regenerates `menu.json`.

## Note
If `lipc-set-prop`/`lipc-get-prop` do nothing, the `com.lab126.cmd`/`wifid` services aren't
running (e.g. the weather loop stopped the framework). Wi-Fi control needs those services up.
