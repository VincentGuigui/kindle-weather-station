# Kindle Python — files & quick steps

NiLuJe's **Python** for a **jailbroken Kindle 4 Non-Touch**. The weather stand needs
**Python 2** (its scripts use `urllib2`). Downloaded and **MD5-verified**
(`749fe028c87463b1abf326c98e702b81`).

## Contents
- `kindle-python-0.14.N-r18833.tar.xz` — original archive (covers K2/DX/3/**4**)
- `Python/` — extracted; the K4 installers you need:
  - `Update_python_0.14.N_k4_install.bin` — **Python 2** (use this one)
  - `Update_python3_0.14.N_k4_install.bin` — Python 3 (optional, not needed here)
  - `Update_python_0.14.N_uninstall.bin` — uninstaller

## Quick steps
1. Jailbreak first (`../jailbreak-files`).
2. Copy **`Update_python_0.14.N_k4_install.bin`** to the Kindle's USB **root** (only one
   `.bin` on root at a time).
3. Eject & unplug → **Menu → Settings → Menu → Update Your Kindle**. Takes a few minutes;
   it may pause a while on "restarting" — that's normal.
4. Verify: in KUAL run the weather stand's **Dependencies Checker**, or via SSH `python --version`.

> Note: this project bundles its own `pytz` next to the weather script, so the checker's
> pytz download step isn't required.

**Undo:** copy `Update_python_0.14.N_uninstall.bin` to root → **Update Your Kindle**.

## ⚠️ Warning
Only for a **jailbroken Kindle you own**; proceed **at your own risk** (no warranty).

## Online source
Kindle Python (NiLuJe): <https://www.mobileread.com/forums/showthread.php?t=88004>
Snapshots/downloads: <https://www.mobileread.com/forums/showthread.php?t=225030>
