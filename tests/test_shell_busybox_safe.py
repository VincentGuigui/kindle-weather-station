"""Guard against BusyBox-incompatible idioms in the on-device shell scripts.

The Kindle's BusyBox build does NOT support POSIX character classes in grep (a pattern like
[[:space:]] silently matches nothing). On a dev machine GNU grep supports them, so config
parsing passes in tests but fails on the device -- which is exactly the bug that shipped.

This test fails if any *code* line (comments stripped) in the bin/*.sh scripts uses a POSIX
class such as [[:space:]]. Run directly or via pytest.
"""
import glob
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN = os.path.join(REPO, "kindle-weather-stand-alone", "extensions", "weather-stand", "bin")


def test_no_posix_class_in_shell_code():
    scripts = sorted(glob.glob(os.path.join(BIN, "*.sh")))
    assert scripts, "no shell scripts found under %s" % BIN
    offenders = []
    for path in scripts:
        with open(path, encoding="utf-8") as handle:
            for lineno, line in enumerate(handle, 1):
                code = line.split("#", 1)[0]  # ignore comments
                if "[[:" in code:
                    offenders.append("%s:%d: %s" % (os.path.basename(path), lineno, line.strip()))
    assert not offenders, (
        "POSIX character class in shell code (BusyBox/Kindle does not support it):\n  "
        + "\n  ".join(offenders))
    print("shell scripts: no POSIX classes in code (%d files checked)" % len(scripts))


if __name__ == "__main__":
    test_no_posix_class_in_shell_code()
