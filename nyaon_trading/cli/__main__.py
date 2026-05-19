from __future__ import annotations

import sys
import os

from nyaon_trading.cli import main

if __name__ == "__main__":
    # When invoked via shebang (e.g., #!/usr/bin/env -S uv run python -m nyaon_trading.cli),
    # the script path gets inserted as argv[1]. Strip it if detected.
    argv = sys.argv[1:]
    if argv and (argv[0].startswith("./") or argv[0].startswith("/") or argv[0].endswith("/nyaon")):
        argv = argv[1:]
    raise SystemExit(main(argv))
