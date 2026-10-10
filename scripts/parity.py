"""Compare retrosheetpy's output with the real Chadwick C tools, season by season.

    uv run python scripts/parity.py 1914 1968 2010 --c-bin ~/.local/bin

For each season it downloads (once, cached) and runs all six tools both ways in the season folder,
plus a few option variants (chosen fields, a date range, one home team, one game), and reports
whether the output is byte-for-byte equal, the line count and the time. Exit status 1 if anything
differs. Needs the real Chadwick tools; not part of the unit tests (``tests/test_parity_c.py`` is
the small version that CI runs).
"""

import argparse
import hashlib
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import retrosheetpy as rs
from retrosheetpy import runner
from retrosheetpy.options import Options, Opts
from retrosheetpy.tools import TOOLS, Tool


def _digest(path: Path) -> tuple[str, int]:
    h, lines = hashlib.sha256(), 0
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
            lines += chunk.count(b"\n")
    return h.hexdigest(), lines


def _c_command(c_bin: Path, tool: Tool, year: int, o: Options, files: list[str]) -> list[str]:
    cmd = [str(c_bin / tool.command), "-Q", "-y", str(year)]
    for flag, value in (("-i", o.game), ("-s", o.start), ("-e", o.end)):
        if value:
            cmd += [flag, value]
    if tool.rows:
        chose = o.fields is not None or o.extended is not None
        none = "" if chose else None
        f = (
            o.fields
            if o.fields is not None
            else (none if none is not None else f"0-{tool.max_field}")
        )
        cmd += ["-n", "-f", f]
        if tool.max_ext_field is not None:
            x = (
                o.extended
                if o.extended is not None
                else (none if none is not None else f"0-{tool.max_ext_field}")
            )
            cmd += ["-x", x]
    return cmd + files


def _variants(season: rs.Season) -> list[tuple[str, Opts]]:
    """A few option combinations that every season can answer."""
    team = season.teams[0]
    return [
        ("events", {"fields": "0-9", "extended": "0-3"}),
        ("events", {"home": team, "start": "0601", "end": "0630"}),
        ("games", {"extended": "0-96"}),
        ("games", {"start": "0701", "end": "0731"}),
        ("daily", {"fields": "0-5"}),
        ("boxscores", {"home": team}),
    ]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("years", nargs="+", type=int)
    ap.add_argument("--c-bin", type=Path, required=True, help="folder holding cwevent, cwgame, ...")
    ap.add_argument(
        "--kind", default="regular", help="regular, postseason, allstar, negro, negro_box, box"
    )
    ap.add_argument("--cache-dir")
    ap.add_argument("--jobs", type=int, help="workers for retrosheetpy (default: automatic)")
    args = ap.parse_args()
    bad = 0
    with tempfile.TemporaryDirectory() as tmp:
        mine, theirs = Path(tmp) / "mine", Path(tmp) / "c"
        for year in args.years:
            s = rs.season(year, kind=args.kind, cache=args.cache_dir)
            cases: list[tuple[str, Opts]] = [(name, {}) for name in TOOLS]
            if args.kind == "regular":  # the option variants pick files by home team
                cases += _variants(s)
            for name, raw in cases:
                tool = TOOLS[name]
                opts = Options.build(tool, {**raw, **({"jobs": args.jobs} if args.jobs else {})})
                label = name + (" " + ",".join(f"{k}={v}" for k, v in raw.items()) if raw else "")
                t0 = time.perf_counter()
                note = ""
                try:
                    with mine.open("wb") as out:
                        runner.run(tool, s, out, opts)
                except Exception as exc:
                    note = f"retrosheetpy FAILED: {exc}"
                t1 = time.perf_counter()
                with theirs.open("wb") as out:
                    c = subprocess.run(  # noqa: S603
                        _c_command(args.c_bin, tool, year, opts, runner.files_for(s, opts)),
                        cwd=s.folder,
                        stdout=out,
                        stderr=subprocess.DEVNULL,
                        check=False,
                    )
                t2 = time.perf_counter()
                if note or c.returncode != 0:
                    verdict, bad = note or f"C tool exited {c.returncode}", bad + 1
                else:
                    (hm, nm), (hc, _) = _digest(mine), _digest(theirs)
                    verdict = f"IDENTICAL {nm:>9} lines" if hm == hc else "DIFFERENT"
                    bad += hm != hc
                timing = f"retrosheetpy {t1 - t0:5.1f}s, C {t2 - t1:5.1f}s"
                print(f"{year} {label:<42} {verdict}  ({timing})", flush=True)
        if len(args.years) > 1:
            bad += _check_combined(args, tmp)
    return 1 if bad else 0


def _check_combined(args: argparse.Namespace, tmp: str) -> int:
    """Several seasons in one Table must equal the C outputs joined, with the header once."""
    bad = 0
    for name in ("games", "events"):
        tool = TOOLS[name]
        table = getattr(rs, name)(args.years, kind=args.kind, cache=args.cache_dir)
        joined = bytearray()
        for i, year in enumerate(args.years):
            s = rs.season(year, kind=args.kind, cache=args.cache_dir)
            o = Options()
            out = subprocess.run(  # noqa: S603
                _c_command(Path(args.c_bin), tool, year, o, runner.files_for(s, o)),
                cwd=s.folder, capture_output=True, check=True,
            ).stdout  # fmt: skip
            joined += out if i == 0 else out.split(b"\n", 1)[1]
        mine = Path(tmp) / "combined.csv"
        table.to_csv(mine, encoding="latin-1")
        # to_csv re-quotes only where needed, so compare parsed rows rather than bytes
        import csv
        import io

        want = list(csv.reader(io.StringIO(bytes(joined).decode("latin-1"), newline="")))
        with mine.open(newline="", encoding="latin-1") as f:
            got = list(csv.reader(f))
        ok = got == want
        bad += not ok
        print(
            f"{args.years[0]}-{args.years[-1]} combined {name:<9} "
            f"{'IDENTICAL' if ok else 'DIFFERENT'} {len(got):>9} rows",
            flush=True,
        )
    return bad


if __name__ == "__main__":
    sys.exit(main())
