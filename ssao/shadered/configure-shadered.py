import re
import shutil
import struct
import sys
from pathlib import Path

width, height = map(int, sys.argv[1:])
directory = Path(shutil.which("SHADERed.exe")).parent / "data"

settings_path = directory / "settings.ini"
with settings_path.open(encoding="utf-8", newline="") as file:
    settings = file.read()
with settings_path.open("w", encoding="utf-8", newline="") as file:
    file.write(re.sub(r"^vsync=.*$", "vsync=0", settings, flags=re.MULTILINE))

# width, height, x, y, fullscreen, maximized, performance mode
(directory / "preload.dat").write_bytes(
    struct.pack("<hhhh???xx", width, height, 0, 0, False, False, False)
)
