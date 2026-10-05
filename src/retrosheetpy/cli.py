"""Command-line entry point."""

import argparse
import sys

from retrosheetpy import season
from retrosheetpy._meta import __version__
from retrosheetpy.errors import RetrosheetError


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="retrosheetpy", description=__doc__)
    p.add_argument("-V", "--version", action="store_true", help="print the version and exit")
    p.add_argument(
        "--cache-dir", help="cache folder (default: $RETROSHEETPY_HOME or ~/.retrosheetpy)"
    )
    sub = p.add_subparsers(dest="command")
    g = sub.add_parser("get", help="download and unpack a season into the cache")
    g.add_argument("year", type=int)
    g.add_argument("--force", action="store_true", help="download again even if cached")
    sub.add_parser("list", help="show the seasons that are cached")
    c = sub.add_parser("cache", help="manage the cache")
    c.add_argument("action", choices=["path", "verify", "clear"])
    return p


def _notice(text: str) -> None:
    print(text, file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    if args.version:
        print(f"retrosheetpy {__version__}")
        return 0
    try:
        if args.command == "get":
            s = season.get(args.year, cache=args.cache_dir, force=args.force, notice=_notice)
            print(f"{s.year}: {len(s.event_files)} event files, {len(s.roster_files)} rosters")
            print(s.folder)
        elif args.command == "list":
            for year in season.cached_seasons(args.cache_dir):
                print(year)
        elif args.command == "cache":
            if args.action == "path":
                print(season.cache_dir(args.cache_dir))
            elif args.action == "clear":
                print(f"removed {season.clear(args.cache_dir)}")
            else:
                problems = season.verify(args.cache_dir)
                for line in problems:
                    print(line, file=sys.stderr)
                return 1 if problems else 0
        else:
            parser.print_usage(sys.stderr)
            return 2
    except (RetrosheetError, ValueError, OSError) as exc:
        print(f"retrosheetpy: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
