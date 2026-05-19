from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

_HALT = Path("state/halt.flag")


def run(argv: list[str]) -> int:
    cmd = argv[0]
    rest = argv[1:]
    if cmd == "halt":
        p = argparse.ArgumentParser(prog="nyaon halt")
        p.add_argument("--reason", required=True)
        a = p.parse_args(rest)
        _HALT.parent.mkdir(parents=True, exist_ok=True)
        _HALT.write_text(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {a.reason}\n")
        print(f"halted: {a.reason}")
        return 0
    if cmd == "resume":
        if _HALT.exists():
            _HALT.unlink()
            print("resumed")
        else:
            print("not halted", file=sys.stderr)
        return 0
    print(f"unknown subcommand: {cmd}", file=sys.stderr)
    return 2
