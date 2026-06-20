# KUAL (Kindle Unified Application Launcher + MRPI (package installer)

Launcher (**KUAL**) and package installer (**MRPI**) for a **jailbroken Kindle 4 Non-Touch**.
Downloaded from NiLuJe's mirror. Install the jailbreak **first** (see [../jailbreak-files/README.md](../jailbreak-files/README.md)`).

## Contents
- `KUAL-v2.7.37-gfcb45b5-20250419.tar.xz` — KUAL (contains `KUAL-KDK-1.0.azw2`, the K4 booklet)
- `kual-mrinstaller-1.7.N-r19303.tar.xz` — MRPI / MRInstaller
- extracted folders alongside the archives

## Quick steps
1. Copy **`KUAL-KDK-1.0.azw2`** into the Kindle's **`documents/`** folder.
2. Copy the MRInstaller **`extensions/MRInstaller/`** folder to the Kindle's **`extensions/`**, and create an empty **`mrpackages/`** folder at the Kindle root.
3. Eject & unplug. Open the **"KUAL-KDK-1.0"** item from Home to launch the menu.
   - MRPI can also be run from the search bar with `;log mrpi`.

## ⚠️ "Not signed by an authorized developer" on Kindle 4
The KDK launcher needs a developer certificate. The **2014 MKK is not enough** on modern K4
units — if not done already, install the **2025 keystore** fix (see [../mkk-files/README.md](../mkk-files/README.md), then re-open KUAL

## ⚠️ Warning
- Only for a **jailbroken Kindle you own**; proceed **at your own risk** (no warranty).
- Install update `.bin` files **one at a time** — multiple on the root at once can make the
  updater skip one.

## Online source
KUAL / MRPI (NiLuJe's official thread): <https://www.mobileread.com/forums/showthread.php?t=225030>

Guide: <https://kindlemodding.org/jailbreaking/post-jailbreak/installing-kual-mrpi/>
