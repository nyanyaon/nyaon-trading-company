from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        print("usage: nyaon <command> [args]", file=sys.stderr)
        return 2
    cmd, rest = argv[0], argv[1:]
    if cmd == "signals":
        from nyaon_trading.cli.signals import run
        return run(rest)
    if cmd == "klines":
        from nyaon_trading.cli.klines import run
        return run(rest)
    if cmd == "account":
        from nyaon_trading.cli.account import run
        return run(rest)
    if cmd == "snapshot":
        from nyaon_trading.cli.snapshot import run
        return run(rest)
    if cmd == "place-order":
        from nyaon_trading.cli.place_order import run
        return run(rest)
    if cmd == "cancel":
        from nyaon_trading.cli.cancel import run
        return run(rest)
    if cmd == "mode":
        from nyaon_trading.cli.mode import run
        return run(rest)
    if cmd in ("halt", "resume"):
        from nyaon_trading.cli.halt import run
        return run([cmd, *rest])
    print(f"unknown command: {cmd}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
