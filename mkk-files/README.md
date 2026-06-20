# MKK / Developer Certificates — files & quick steps

Developer-certificate packages that let a **jailbroken Kindle 4** run unsigned kindlets such as
**KUAL**. Without the right cert you get *"not signed by an authorized developer."*

## Contents
- `kindle-mkk-20141129-r18833.tar.xz` — **2014 MKK** (MD5 `8af8c2a4cbdf6a9f4a45a63bb4c4dd02`).
  Often **not enough** on modern K4 units.
- `DevCerts-20250419-KeyStore.zip` — **2025 keystore fix** (the one that actually works).
  Contains `Update_mkk-20250419-k4-ALL_keystore-install.bin`.

## Quick steps (the fix that worked)
1. Jailbreak first, install KUAL (`../kual-files`).
2. If KUAL says **"not signed by an authorized developer"**, copy
   **`Update_mkk-20250419-k4-ALL_keystore-install.bin`** to the Kindle **root**.
3. **Menu → Settings → Menu → Update Your Kindle** → wait for "Update successful" + reboot.
4. Re-open the **KUAL-KDK-1.0** item — the menu should now launch.

> Install update `.bin` files **one at a time** (only one on the root at once).

## ⚠️ Warning
Only for a **jailbroken Kindle you own**; proceed **at your own risk** (no warranty).

## Online source
2025 keystore fix (NiLuJe, forum attachment — free MobileRead account needed):
<https://www.mobileread.com/forums/showpost.php?p=4506164&postcount=1295>

MKK thread: <https://www.mobileread.com/forums/showthread.php?t=233932>
Snapshots/downloads: <https://www.mobileread.com/forums/showthread.php?t=225030>
