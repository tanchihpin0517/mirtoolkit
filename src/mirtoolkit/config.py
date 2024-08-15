import sys

import platformdirs

_appname = "mirtoolkit"
_appauthor = "mirtoolkit"

# CACHE_DIR = Path.home().joinpath(".mirtoolkit")
CACHE_DIR = platformdirs.user_cache_path(_appname, _appauthor)
SYS_PATH_DIR = CACHE_DIR.joinpath("sys_path")

if not CACHE_DIR.exists():
    CACHE_DIR.mkdir()
if not SYS_PATH_DIR.exists():
    SYS_PATH_DIR.mkdir()
if str(SYS_PATH_DIR) not in sys.path:
    sys.path.append(str(SYS_PATH_DIR))
