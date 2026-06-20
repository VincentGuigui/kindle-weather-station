# Kindle 4 NT → Weather Clock — Build Guide

End-to-end guide for turning a **stock Kindle 4 Non-Touch (D01100, firmware 4.1.4)** into a
standalone weather display using
[x-magic/kindle-weather-stand-alone](https://github.com/x-magic/kindle-weather-stand-alone).


| | |
|---|---|
| Model | Kindle 4 Non-Touch (D01100) |
| Firmware | 4.1.4 (top of supported jailbreak range 4.0.0–4.1.4) |

> ⚠️ **The only real brick risk** in this whole process is jailbreaking *out-of-range*
> firmware. 4.1.4 is in range, so you're safe. If you ever factory-reset and the firmware
> changes, re-check before re-jailbreaking.

---

## 0. Security audit summary (done — safe)

Both the application repo **and** the jailbreak package were read line-by-line before anything
touched the device.

### `kindle-weather-stand-alone` (the app)
- **No malware, no backdoor, no data exfiltration.** Every outbound connection goes to a host
  *you* configure or expect: the weather API you choose, optionally Pushover (low-battery
  alert, opt-in), and PyPI (to fetch the `pytz` dependency, MD5-verified).
- Bundled ARM binaries (`pngcrush`, `rsvg-convert` + libs) are stock open-source image tools.
  The only URL in any of them is pngcrush's homepage string — not a network call.
- Minor notes: scripts use `ssl._create_unverified_context()` (TLS cert check disabled — a
  workaround for the ancient Kindle Python cert store; harmless for public weather data), and
  **Dark Sky is dead** (Apple shut it down in 2023) → we use **OpenWeatherMap**.

### `kindle-k4-jailbreak-1.8.N-r18977` (NiLuJe's jailbreak)
- Downloaded from NiLuJe's official MobileRead thread, **MD5 verified**
  (`8b8dc46c1568655c93244abdce93556a`).
- `install.sh` only: installs a developer key (`/etc/uks/pubdevkey01.pem`) + Kindlet keystore,
  shows a splash, writes `You are Jailbroken.txt`. **No network, no exfiltration.**
- Payload (`data.tar.gz`) contains only the keys + two regenerated config files.

---

## 1. Files already staged on this PC

```
C:\dev_factory\My\Kindle\kindle-weather\
├─ README.md                          ← this file
├─ kindle-weather-stand-alone\        ← the app (cloned, audited)
│  └─ extensions\                     ← this folder gets copied to the Kindle
└─ jailbreak-files\
   ├─ kindle-k4-jailbreak-1.8.N-r18977.tar.xz   ← downloaded, MD5-verified
   └─ K4_JailBreak\                   ← extracted; copy 3 items below to Kindle root
      ├─ data.tar.gz                  ┐
      ├─ ENABLE_DIAGS                 ├─ copy these 3 to the Kindle USB root
      └─ diagnostic_logs\             ┘
```

---

## 2. Jailbreak (manual — requires physical button presses)

> Software/files are staged for you. These steps require pressing buttons on the device, so
> they must be done by hand.

1. Plug the Kindle into the PC; it mounts as a USB drive.
2. Copy these **three items** from `jailbreak-files\K4_JailBreak\` to the **root** of the
   Kindle drive (not inside any folder):
   - `data.tar.gz`
   - `ENABLE_DIAGS`
   - `diagnostic_logs\` (folder)
3. **Safely eject** and unplug.
4. On the Kindle: **Menu → Settings → Menu → Restart**.
5. It boots into **Diagnostics Mode** (text menu). With the 5-way controller:
   - **`D) Exit, Reboot or Disable Diags`**
   - **`R) Reboot System`**
   - **`Q) To continue`**
   - press **left** on the 5-way when told to use *FW Left*.
6. Wait ~20 s — a jailbreak splash shows, then it reboots normally.
7. ✅ **Success** = a new item **"You are Jailbroken"** appears in your library.

To undo later: copy `K4_JailBreak\Update_jailbreak_1.8.N_uninstall.bin` to the Kindle root and
run **Menu → Settings → Menu → Update Your Kindle**.

---

## 3. Install KUAL + MRPI (the launcher + package installer)

Download (legacy/K4 versions):
- **KUAL**: `KUAL-KDK-1.0.azw2`
- **MRPI**: `kual-mrinstaller-1.7.N-r19303.zip`

Steps:
1. Unzip MRPI; copy its `extensions\` and `mrpackages\` folders to the **Kindle root**.
2. Copy `KUAL-KDK-1.0.azw2` into the Kindle's **`documents\`** folder.
3. Eject & unplug.
4. On the Kindle, type **`;log mrpi`** in the search bar and press Enter.
5. Wait — screen may flash white; a **KUAL** book appears when done. (Dismiss any
   "Application Error" popups — normal.)

Source: <https://kindlemodding.org/jailbreaking/post-jailbreak/installing-kual-mrpi/>

---

## 4. Install Kindle Python

- Package: **`kindle-python-0.14.N-k4.zip`** (the **k4** build) from MobileRead thread
  <https://www.mobileread.com/forums/showthread.php?t=88004>.
- Install via MRPI: unzip so its package lands in `mrpackages\` on the Kindle root, then run
  **`;log mrpi`** again from the search bar (or install the provided `.bin` via
  **Update Your Kindle**, per its readme).

---

## 5. Get a free OpenWeatherMap API key

1. Sign up at <https://openweathermap.org/api> (free tier is plenty).
2. Copy your **API key** (`APPID`).
3. Note your location — easiest is city ID or lat/lon. The script uses the still-free
   `/data/2.5/weather` and `/data/2.5/forecast` endpoints.

---

## 6. Configure & deploy the weather stand

1. Edit `kindle-weather-stand-alone\extensions\weather-stand\bin\weather-generator.sh` →
   comment the Dark Sky line, **uncomment the OpenWeatherMap line**:
   ```sh
   #python weather-generator-darksky.py
   python weather-generator-openweathermap.py
   ```
2. Edit `…\weather-stand\weather.conf` (plain key=value file at the extension root — no need
   to touch the Python):
   ```ini
   api_key     = YOUR_OWM_API_KEY
   location    = lat=48.7853&lon=2.4136     # or q=City,CC or id=XXXXXXX
   units       = metric                     # or imperial
   time_format = 24                         # or 12
   timezone    = Europe/Paris               # your tz
   ```
3. *(Optional)* Pushover low-battery alert: put your keys in
   `…\bin\weather-manager.sh` (`PO_TOKEN`, `PO_USER`).
4. *(Optional)* Refresh interval: edit `…\bin\start.sh` — the `echo "+3600"` line is the
   sleep in seconds (3600 = hourly).
5. Copy the whole `extensions\` folder to the **Kindle root** (merges with KUAL's).
6. In KUAL, run **"Kindle Weather Stand Dependencies Checker"** — it verifies Python and
   installs `pytz` if missing (needs Wi-Fi).
7. **Delete the kill-switch:** remove
   `extensions\weather-stand\bin\disable` from the Kindle. The main loop refuses to run while
   that file exists. (Re-add an empty `disable` file + reboot to return the Kindle to normal.)
8. In KUAL, run **"Kindle Weather Stand"**. 🎉

---

## Reverting to a normal Kindle
- Add an empty file named `disable` back into `weather-stand/bin/` and reboot → stops the
  weather loop.
- Run the jailbreak uninstaller `.bin` (§2) to remove the developer key.

## Sources
- App repo: <https://github.com/x-magic/kindle-weather-stand-alone>
- K4NT jailbreak (NiLuJe): <https://www.mobileread.com/forums/showthread.php?t=225030>
- MobileRead K4NT wiki: <https://wiki.mobileread.com/wiki/Kindle4NTHacking>
- KUAL/MRPI: <https://kindlemodding.org/jailbreaking/post-jailbreak/installing-kual-mrpi/>
- Kindle Python: <https://www.mobileread.com/forums/showthread.php?t=88004>
