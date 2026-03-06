"""
ogle.cli
========
Command-line interface for the ogle package.

Entry point (configured in ``pyproject.toml``)::

    [project.scripts]
    ogle = "ogle.cli:main"

Available commands
------------------
``ogle info  <file>``      — Print metadata about a .dat or .map file.
``ogle load  <file>``      — Load and print the first N rows.
``ogle field <directory>`` — Summarise an OGLE-II field directory.

Examples
--------
::

    $ ogle info bul_sc1.01.123456.dat
    $ ogle load bul_sc1.01.123456.dat --rows 10
    $ ogle field ./bul_sc1/ --map bul_sc1.map
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Sub-command handlers
# ---------------------------------------------------------------------------

def cmd_info(args: argparse.Namespace) -> None:
    """Print metadata about a photometry or catalogue file."""
    path = Path(args.file)
    if not path.exists():
        print(f"[ogle] Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)

    suffix = path.suffix.lower()

    if suffix == ".map":
        from ogle.ogle2.parser import parse_ogle2_map
        df = parse_ogle2_map(path, polars=True)
        print(f"File    : {path}")
        print("Type    : OGLE-II catalogue (.map)")
        print(f"Stars   : {len(df)}")
        print(f"Columns : {df.columns}")

    elif suffix in (".dat", ".lc") or str(path).lower().endswith("dat.lc"):
        from ogle.ogle2.parser import load_dat
        from ogle.shared.utils import parse_ogle2_filename
        info = parse_ogle2_filename(path)
        df   = load_dat(path, polars=True)
        print(f"File      : {path}")
        print("Type      : OGLE-II photometry (.dat)")
        print(f"OGLE ID   : {info['ogle_id']}")
        print(f"Field     : {info['field']}")
        print(f"Chip      : {info['chip']}")
        print(f"Star No.  : {info['star_no']}")
        print(f"Epochs    : {len(df)}")
        t = df["hjd"].to_numpy()
        import numpy as np
        print(f"HJD range : {t.min():.3f} – {t.max():.3f}  (baseline={np.ptp(t):.1f} d)")
        print(f"Mean mag  : {df['mag_i'].mean():.4f}")
        print(f"Columns   : {df.columns}")

    else:
        print(f"[ogle] Unrecognised file type: {suffix}", file=sys.stderr)
        sys.exit(1)


def cmd_load(args: argparse.Namespace) -> None:
    """Load a .dat file and print the first N rows."""
    path = Path(args.file)
    if not path.exists():
        print(f"[ogle] Error: file not found: {path}", file=sys.stderr)
        sys.exit(1)

    from ogle.ogle2.parser import load_dat
    df = load_dat(path, polars=True)
    n  = min(args.rows, len(df))
    print(df.head(n))
    if len(df) > n:
        print(f"… ({len(df) - n} more rows)")


def cmd_field(args: argparse.Namespace) -> None:
    """Summarise an OGLE-II field directory."""
    from ogle.core import OGLE2Field
    map_path = Path(args.map) if args.map else None
    if map_path:
        field = OGLE2Field.from_map(map_path, dat_dir=args.directory)
    else:
        field = OGLE2Field.from_directory(args.directory)
    field.summary()


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ogle",
        description="OGLE photometry toolkit — command-line interface.",
    )
    sub = parser.add_subparsers(dest="command", help="Sub-command")
    sub.required = True

    # ogle info
    p_info = sub.add_parser("info", help="Print metadata about a .dat or .map file.")
    p_info.add_argument("file", help="Path to the .dat or .map file.")
    p_info.set_defaults(func=cmd_info)

    # ogle load
    p_load = sub.add_parser("load", help="Load and print photometry rows.")
    p_load.add_argument("file", help="Path to the .dat file.")
    p_load.add_argument("--rows", type=int, default=10,
                        help="Number of rows to print (default: 10).")
    p_load.set_defaults(func=cmd_load)

    # ogle field
    p_field = sub.add_parser("field", help="Summarise an OGLE-II field directory.")
    p_field.add_argument("directory", help="Directory of .dat photometry files.")
    p_field.add_argument("--map", default=None,
                         help="Optional path to the .map catalogue file.")
    p_field.set_defaults(func=cmd_field)

    return parser


def main(argv: list[str] | None = None) -> None:
    parser = build_parser()
    args   = parser.parse_args(argv)
    args.func(args)


if __name__ == "__main__":
    main()