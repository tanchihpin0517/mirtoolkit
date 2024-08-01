from pathlib import Path
import sys


PROJ_DIR = Path.home().joinpath(".mirtoolkit")
SYS_PATH_DIR = PROJ_DIR.joinpath("sys_path")

if not PROJ_DIR.exists():
    PROJ_DIR.mkdir()
if not SYS_PATH_DIR.exists():
    SYS_PATH_DIR.mkdir()
if str(SYS_PATH_DIR) not in sys.path:
    sys.path.append(str(SYS_PATH_DIR))
