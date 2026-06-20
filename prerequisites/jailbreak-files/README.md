# Kindle 4 NT Jailbreak

NiLuJe's jailbreak for the **Kindle 4 Non-Touch (D01100)**, firmware **4.0.0–4.1.4**.
Downloaded and **MD5-verified** (`8b8dc46c1568655c93244abdce93556a`).

## Contents
- `kindle-k4-jailbreak-1.8.N-r18977.tar.xz` — original archive
- `K4_JailBreak/` — extracted; the 3 items below go on the Kindle

## Quick steps
> These steps require pressing buttons on the device, so they must be done by hand.

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

## ⚠️ Warning
- **Jailbreaking can brick your device and voids your warranty.** Use only on firmware **4.0.0–4.1.4** (check at Settings → bottom of screen). Wrong firmware/model = high brick risk.
- Do this **only on a Kindle you own**. You proceed entirely **at your own risk** — no warranty, express or implied.
- The jailbreak only *allows* unsigned software; badly-coded add-ons you install afterward can still damage the device.

## Online source
NiLuJe's official thread (downloads, support, latest version):
<https://www.mobileread.com/forums/showthread.php?t=225030>

Wiki: <https://wiki.mobileread.com/wiki/Kindle4NTHacking>