# Interactive date/time setter for the "Set Date & Time" KUAL extension.
#
# Full-screen eips UI:  shows  YYYY-MM-DD  HH:MM  with a "^" cursor under one digit.
#   LEFT / RIGHT  move the cursor between digits
#   UP   / DOWN   increase / decrease the value at that digit's place (year by 1000/100/10/1,
#                 the rest by 10/1), wrapping/clamping to valid ranges
#   SELECT / BACK / HOME  finish (it also auto-exits after IDLE_TIMEOUT s of no input)
#
# Every change is applied immediately in UTC (`date -u`) and saved to the RTC (`hwclock -u -w`).
# Standard-library Python only (works on the device's 2.7); no network. The d-pad is read by
# grabbing /dev/input (EVIOCGRAB) so the framework doesn't also act on the keys; closing the
# fds releases the grab even if this crashes.
import calendar
import os
import select
import struct
import subprocess
import time

try:
    import fcntl   # Linux only; used to grab the input device. Absent on dev (Windows) -> ok.
except ImportError:
    fcntl = None

LOG = "/mnt/us/kindle-set-datetime.log"
EVENT_SIZE = struct.calcsize("=llHHi")   # input_event on a 32-bit kernel = 16 bytes
EVIOCGRAB = 0x40044590                   # _IOW('E', 0x90, int)
IDLE_TIMEOUT = 90.0                      # safety: never trap the UI -> auto-exit when idle

KEY_LEFT, KEY_RIGHT, KEY_UP, KEY_DOWN = 105, 106, 103, 108
EXIT_KEYS = (28, 158, 102)               # ENTER, BACK, HOME

COL, ROW = 14, 16                        # eips character-grid position of the field

# Editable digit positions: (index in "YYYY-MM-DD  HH:MM", field, step applied on UP).
POSITIONS = [
    (0, "Y", 1000), (1, "Y", 100), (2, "Y", 10), (3, "Y", 1),
    (5, "Mo", 10), (6, "Mo", 1),
    (8, "D", 10), (9, "D", 1),
    (12, "H", 10), (13, "H", 1),
    (15, "Mi", 10), (16, "Mi", 1),
]


def log(msg):
    try:
        handle = open(LOG, "a")
        handle.write(msg + "\n")
        handle.close()
    except Exception:
        pass


def run(cmd):
    out = subprocess.Popen(cmd, stdout=subprocess.PIPE).communicate()[0]
    if isinstance(out, bytes):
        out = out.decode("ascii", "ignore")
    return out.strip()


def eips(col, row, text):
    os.system('/usr/sbin/eips %d %d "%s" >/dev/null 2>&1' % (col, row, text))


def eips_clear():
    os.system("/usr/sbin/eips -c >/dev/null 2>&1")
    os.system("/usr/sbin/eips -c >/dev/null 2>&1")


def step(state, field, delta):
    # Pure: apply delta to one field of (y, mo, d, h, mi), wrap/clamp, keep the day valid.
    y, mo, d, h, mi = state
    if field == "Y":
        y = max(1970, min(2099, y + delta))
    elif field == "Mo":
        mo = (mo - 1 + delta) % 12 + 1
    elif field == "D":
        dim = calendar.monthrange(y, mo)[1]
        d = (d - 1 + delta) % dim + 1
    elif field == "H":
        h = (h + delta) % 24
    elif field == "Mi":
        mi = (mi + delta) % 60
    d = min(d, calendar.monthrange(y, mo)[1])
    return (y, mo, d, h, mi)


def read_clock():
    parts = run(["date", "-u", "+%Y %m %d %H %M"]).split()
    y, mo, d, h, mi = [int(x) for x in parts]
    return step((y, mo, d, h, mi), "", 0)  # clamp via no-op


def apply_clock(state):
    y, mo, d, h, mi = state
    os.system("date -u %02d%02d%02d%02d%04d.00 >/dev/null 2>&1" % (mo, d, h, mi, y))
    os.system("hwclock -u -w >/dev/null 2>&1")


def fmt(state):
    return "%04d-%02d-%02d  %02d:%02d" % state


def draw(state, cursor):
    text = fmt(state)
    idx = POSITIONS[cursor][0]
    eips(COL, ROW - 2, "Set date and time (UTC):")
    eips(COL, ROW, text)
    # Cursor row: clear it, then place a dash under the selected digit by absolute column
    # (positioning by column, not by leading spaces, so eips can't mis-handle/hide it).
    eips(COL, ROW + 1, " " * len(text))
    eips(COL + idx, ROW + 1, "-")
    eips(COL, ROW + 3, "left/right move   up/down change")
    eips(COL, ROW + 4, "select = done")


def open_inputs():
    fds = []
    try:
        names = sorted(os.listdir("/dev/input"))
    except OSError:
        names = []
    for name in names:
        if not name.startswith("event"):
            continue
        try:
            fd = os.open("/dev/input/" + name, os.O_RDONLY)
        except OSError:
            continue
        try:
            fcntl.ioctl(fd, EVIOCGRAB, 1)   # take exclusive control of the keys
        except Exception:
            pass
        fds.append(fd)
    return fds


def main():
    state = read_clock()
    cursor = 0
    eips_clear()
    draw(state, cursor)

    fds = open_inputs()
    if not fds:
        eips(COL, ROW + 6, "No input device; exiting.")
        return

    last = time.time()
    try:
        while True:
            ready, _, _ = select.select(fds, [], [], 5.0)
            if not ready:
                if time.time() - last > IDLE_TIMEOUT:
                    break
                continue
            for fd in ready:
                data = os.read(fd, EVENT_SIZE)
                if len(data) < EVENT_SIZE:
                    continue
                _sec, _usec, etype, code, value = struct.unpack("=llHHi", data)
                if etype != 1 or value == 0:   # EV_KEY, press or autorepeat only
                    continue
                last = time.time()
                _idx, field, stepamt = POSITIONS[cursor]
                if code == KEY_LEFT:
                    cursor = (cursor - 1) % len(POSITIONS)
                elif code == KEY_RIGHT:
                    cursor = (cursor + 1) % len(POSITIONS)
                elif code == KEY_UP:
                    state = step(state, field, stepamt)
                    apply_clock(state)
                elif code == KEY_DOWN:
                    state = step(state, field, -stepamt)
                    apply_clock(state)
                elif code in EXIT_KEYS:
                    raise KeyboardInterrupt
                else:
                    log("unhandled keycode: %d" % code)
                    continue
                draw(state, cursor)
    except KeyboardInterrupt:
        pass
    finally:
        for fd in fds:
            try:
                fcntl.ioctl(fd, EVIOCGRAB, 0)
            except Exception:
                pass
            try:
                os.close(fd)
            except Exception:
                pass
        apply_clock(state)
        eips_clear()
        eips(COL, ROW, "Clock set: " + fmt(state) + " UTC")


if __name__ == "__main__":
    main()
