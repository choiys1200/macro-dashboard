"""CLI 진입점.

사용법:
  python -m news_brief.main collect|summarize|report|send|all [--date YYYY-MM-DD]
"""

from __future__ import annotations

import argparse
import logging
import sys

from . import collect, report, send, summarize

STEPS = {
    "collect": collect.run,
    "summarize": summarize.run,
    "report": report.run,
    "send": send.run,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="news_brief")
    parser.add_argument("command", choices=[*STEPS, "all"])
    parser.add_argument("--date", default=None, help="대상 날짜 (기본: KST 오늘)")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    commands = list(STEPS) if args.command == "all" else [args.command]
    for cmd in commands:
        print(f"=== {cmd} ===")
        try:
            result = STEPS[cmd](date=args.date)
            print(f"[{cmd}] 완료: {result}")
        except Exception as e:  # noqa: BLE001
            logging.getLogger(cmd).error("%s 단계 실패: %s", cmd, e)
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
