"""Command-line entry point."""

import sys

from retrosheetpy import __version__


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args and args[0] in ("-V", "--version"):
        print(f"retrosheetpy {__version__}")
        return 0
    print("retrosheetpy: under construction. Try --version.", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
