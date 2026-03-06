"""
ogle.shared.utils
=================
File I/O helpers and OGLE identifier utilities shared across all survey versions.

Key responsibilities
--------------------
* Validate file extensions before passing to parsers (fast fail with clear errors).
* Scan directories for photometry files matching OGLE naming conventions.
* Parse OGLE source identifiers from filenames (field, chip, star number).
* Provide a unified ``read_whitespace`` helper used by all parsers.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import polars as pl


# ---------------------------------------------------------------------------
# Extension validation
# ---------------------------------------------------------------------------

#: File extensions recognised as OGLE-II time-series photometry files.
DAT_EXTENSIONS: frozenset[str] = frozenset({".dat", ".lc"})
#: File extensions recognised as OGLE catalogue / map files.
MAP_EXTENSIONS: frozenset[str] = frozenset({".map"})


def validate_dat(filepath: str | Path) -> Path:
    """
    Return a resolved ``Path`` for a ``.dat`` / ``.lc`` photometry file.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    ValueError
        If the extension is not a recognised photometry extension.
    """
    path = Path(filepath).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Photometry file not found: {path}")
    suffix = path.suffix.lower()
    # Handle compound extension like 'sc1.234567.dat.lc'
    if suffix not in DAT_EXTENSIONS and not str(path).lower().endswith("dat.lc"):
        raise ValueError(
            f"Expected a photometry file ({', '.join(sorted(DAT_EXTENSIONS))}), "
            f"got: '{path.name}'"
        )
    return path


def validate_map(filepath: str | Path) -> Path:
    """
    Return a resolved ``Path`` for a ``.map`` catalogue file.

    Raises
    ------
    FileNotFoundError
        If the file does not exist.
    ValueError
        If the extension is not ``.map``.
    """
    path = Path(filepath).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Map file not found: {path}")
    if path.suffix.lower() not in MAP_EXTENSIONS:
        raise ValueError(
            f"Expected a .map catalogue file, got: '{path.name}'"
        )
    return path


# ---------------------------------------------------------------------------
# Directory scanning
# ---------------------------------------------------------------------------

def find_dat_files(
    directory: str | Path,
    recursive: bool = False,
    glob: str = "*.dat",
    max_files: int | None = None,
) -> list[Path]:
    """
    Return a sorted list of photometry files in *directory*.

    Parameters
    ----------
    directory : str | Path
        Root directory to search.
    recursive : bool
        If True, descend into sub-directories (``rglob`` instead of ``glob``).
    glob : str
        File pattern.  Defaults to ``'*.dat'``.  Use ``'*.lc'`` for OGLE-II
        ``.lc`` variants.
    max_files : int | None
        Cap the result (useful for testing / sampling).

    Returns
    -------
    list[Path]
        Sorted list of matching paths.

    Raises
    ------
    NotADirectoryError
        If *directory* does not exist or is not a directory.
    """
    root = Path(directory)
    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {root}")
    search = root.rglob(glob) if recursive else root.glob(glob)
    files = sorted(search)
    if max_files is not None:
        files = files[:max_files]
    return files


def find_map_files(
    directory: str | Path,
    recursive: bool = False,
) -> list[Path]:
    """Return a sorted list of ``.map`` catalogue files in *directory*."""
    root = Path(directory)
    if not root.is_dir():
        raise NotADirectoryError(f"Not a directory: {root}")
    search = root.rglob("*.map") if recursive else root.glob("*.map")
    return sorted(search)


# ---------------------------------------------------------------------------
# OGLE identifier parsing
# ---------------------------------------------------------------------------

def parse_ogle2_filename(filepath: str | Path) -> dict[str, str]:
    """
    Extract the OGLE-II source identifier components from a ``.dat`` filename.

    OGLE-II photometry filenames follow the convention::

        {field}.{chip}.{star_number}.dat
        e.g.  bul_sc1.01.123456.dat

    Parameters
    ----------
    filepath : str | Path
        Path to (or just the name of) an OGLE-II ``.dat`` file.

    Returns
    -------
    dict with keys:
        ``'stem'``       — full filename without extension.
        ``'field'``      — survey field (e.g. ``'bul_sc1'``).
        ``'chip'``       — CCD chip identifier (e.g. ``'01'``).
        ``'star_no'``    — star sequence number (e.g. ``'123456'``).
        ``'ogle_id'``    — canonical OGLE-II ID string, e.g.
                           ``'bul_sc1.01.123456'``.

    Notes
    -----
    If the filename does not match the three-part convention, ``'field'``,
    ``'chip'``, and ``'star_no'`` will be empty strings and ``'ogle_id'``
    will equal the stem.
    """
    stem = Path(filepath).stem
    # Strip a trailing '.dat' that appears in compound extensions (.dat.lc)
    if stem.endswith(".dat"):
        stem = stem[:-4]

    parts = stem.split(".")
    if len(parts) >= 3:
        field   = ".".join(parts[:-2])
        chip    = parts[-2]
        star_no = parts[-1]
    else:
        field = chip = star_no = ""

    return {
        "stem":    stem,
        "field":   field,
        "chip":    chip,
        "star_no": star_no,
        "ogle_id": stem if not field else f"{field}.{chip}.{star_no}",
    }


# ---------------------------------------------------------------------------
# Unified whitespace reader (used by all parsers)
# ---------------------------------------------------------------------------

def read_whitespace(
    filepath: str | Path,
    col_names: list[str],
    comment: str = "#",
    as_polars: bool = True,
) -> pd.DataFrame | pl.DataFrame:
    """
    Read a whitespace-delimited plain-text file into a DataFrame.

    This is a thin wrapper around pandas ``read_csv`` (which handles
    irregular whitespace correctly) with an optional Polars conversion.
    It is used by all OGLE parsers so the parsing logic lives in one place.

    Parameters
    ----------
    filepath : str | Path
        Path to the data file.
    col_names : list[str]
        Column names to assign (the file is assumed to have no header row).
    comment : str
        Lines beginning with this character are skipped.
    as_polars : bool
        Return a Polars DataFrame (default).  Pass ``False`` for Pandas.

    Returns
    -------
    pd.DataFrame | pl.DataFrame
    """
    path = Path(filepath)
    try:
        pdf = pd.read_csv(
            str(path),
            sep=r"\s+",
            names=col_names,
            comment=comment,
            engine="python",
        )
    except Exception as exc:
        raise RuntimeError(f"Failed to parse {path.name}: {exc}") from exc

    return pl.from_pandas(pdf) if as_polars else pdf