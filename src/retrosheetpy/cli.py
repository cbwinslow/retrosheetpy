"""Command-line entry point. Parses arguments and calls the API; no logic of its own."""

import argparse
import io
import sys
from pathlib import Path

import retrosheetpy as rs
from retrosheetpy._meta import __version__
from retrosheetpy.api import Years
from retrosheetpy.errors import RetrosheetError
from retrosheetpy.options import Opts
from retrosheetpy.tools import TOOLS

TABLE_FORMATS = ("csv", "jsonl", "json", "sqlite")
BOX_FORMATS = ("text", "xml", "sportsml")
_EXT = {"csv": "csv", "jsonl": "jsonl", "json": "json", "sqlite": "sqlite", "text": "txt",
        "xml": "xml", "sportsml": "xml"}  # fmt: skip


def parse_years(tokens: list[str]) -> list[int]:
    """``2010``, ``2000-2010`` and ``2001,2005`` (any mix) -> a list of seasons, in order."""
    years: list[int] = []
    for token in tokens:
        for part in token.split(","):
            lo, dash, hi = part.partition("-")
            try:
                a, b = int(lo), int(hi) if dash else int(lo)
            except ValueError:
                raise ValueError(
                    f"cannot read {part!r} as a year or a range like 2000-2010"
                ) from None
            if b < a:
                raise ValueError(f"{part!r} is backwards")
            years += range(a, b + 1)
    return years


def _label(years: list[int]) -> str:
    return str(years[0]) if len(years) == 1 else f"{years[0]}-{years[-1]}"


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="retrosheetpy",
        description="Download Retrosheet seasons and turn them into tables.",
    )
    p.add_argument("-V", "--version", action="store_true", help="print the version and exit")
    p.add_argument(
        "--cache-dir", help="cache folder (default: $RETROSHEETPY_HOME or ~/.retrosheetpy)"
    )
    sub = p.add_subparsers(dest="command")

    g = sub.add_parser("get", help="download and unpack seasons into the cache")
    g.add_argument("years", nargs="+", metavar="YEARS", help="2010, 2000-2010, 2001,2005")
    g.add_argument("--force", action="store_true", help="download again even if cached")

    for name, t in TOOLS.items():
        q = sub.add_parser(name, help=f"{t.command} over seasons (downloads them if needed)")
        q.add_argument("years", nargs="+", metavar="YEARS", help="2010, 2000-2010, 2001,2005")
        q.add_argument("--home", help="only these home teams' files, e.g. NYA or NYA,BOS")
        q.add_argument("--game", help="only this game id, e.g. ANA201004050")
        q.add_argument("--start", help="earliest date, mmdd")
        q.add_argument("--end", help="latest date, mmdd")
        q.add_argument("-j", "--jobs", type=int, help="worker processes (default: automatic)")
        if t.rows:
            q.add_argument("--fields", help="field numbers to print, e.g. 0-5,9 (see: fields)")
            if t.max_ext_field is not None:
                q.add_argument("--extended", help="extended field numbers, e.g. 0-10")
            q.add_argument("--format", choices=TABLE_FORMATS, default="csv")
            q.add_argument("--table", help="SQLite table name (default: the table's name)")
            q.add_argument("--if-exists", choices=["fail", "replace", "append"], default="fail")
        else:
            q.add_argument("--format", choices=BOX_FORMATS, default="text")
        q.add_argument("--out", help="file or folder to write (default: print to stdout)")

    f = sub.add_parser("fields", help="list a table's numbered fields (Chadwick's -d)")
    f.add_argument("table", choices=[n for n, t in TOOLS.items() if t.rows])

    sub.add_parser("list", help="show the seasons that are cached")
    c = sub.add_parser("cache", help="manage the cache")
    c.add_argument("action", choices=["path", "verify", "clear"])
    return p


def _opts(args: argparse.Namespace) -> Opts:
    opts: Opts = {}
    if args.home:
        opts["home"] = [t for t in args.home.split(",") if t]
    for key in ("game", "start", "end", "fields", "extended", "jobs"):
        value = getattr(args, key, None)
        if value is not None:
            opts[key] = value
    return opts


def _destination(args: argparse.Namespace, years: list[int]) -> Path | None:
    """The file to write, or None for stdout. A folder (or a name ending in /) gets a default."""
    if not args.out:
        return None
    out = Path(args.out)
    if out.is_dir() or args.out.endswith(("/", "\\")):
        return out / f"{_label(years)}-{args.command}.{_EXT[args.format]}"
    return out


def _run_query(args: argparse.Namespace) -> int:
    years = parse_years(args.years)
    spec: Years = years
    obj = getattr(rs, args.command)(spec, cache=args.cache_dir, **_opts(args))
    dest = _destination(args, years)
    fmt = args.format
    if fmt == "sqlite":
        if dest is None:
            raise ValueError("--format sqlite needs --out FILE")
        n = obj.to_sqlite(dest, args.table, if_exists=args.if_exists)
        print(f"{n} rows -> {dest}")
        return 0
    if dest is not None:
        obj.write(dest, fmt)
        print(dest)
        return 0
    out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", newline="", write_through=True)
    try:
        if args.command == "boxscores":
            out.write(getattr(obj, fmt)())
        else:
            {"csv": obj.to_csv, "jsonl": obj.to_jsonl, "json": obj.to_json}[fmt](out)
    finally:
        out.detach()
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(sys.argv[1:] if argv is None else argv)
    if args.version:
        print(f"retrosheetpy {__version__}")
        return 0
    try:
        if args.command == "get":
            for y in parse_years(args.years):
                s = rs.season(y, cache=args.cache_dir, force=args.force)
                print(f"{y}: {len(s.event_files)} event files ({', '.join(s.teams)}) -> {s.folder}")
        elif args.command in TOOLS:
            return _run_query(args)
        elif args.command == "fields":
            for fld in rs.fields(args.table):
                kind = "x" if fld.extended else "f"
                print(f"{kind}{fld.number:>3}  {fld.description}")
        elif args.command == "list":
            for y in rs.cached_seasons(args.cache_dir):
                print(y)
        elif args.command == "cache":
            if args.action == "path":
                print(rs.cache_dir(args.cache_dir))
            elif args.action == "clear":
                print(f"removed {rs.clear_cache(args.cache_dir)}")
            else:
                problems = rs.verify_cache(args.cache_dir)
                for line in problems:
                    print(line, file=sys.stderr)
                return 1 if problems else 0
        else:
            parser.print_usage(sys.stderr)
            return 2
    except BrokenPipeError:
        return 0  # the reader (e.g. `| head`) closed the pipe; that is not an error
    except (RetrosheetError, ValueError, OSError, TypeError) as exc:
        print(f"retrosheetpy: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
