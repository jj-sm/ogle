"""
ogle.ogle2.parser
=================
Parsers for OGLE-II photometry and catalogue files.

Two file types are supported:

* ``.dat`` / ``.lc``  — Three-column whitespace-delimited time-series:
                         ``HJD  mag_I  sigma``
* ``.map``            — Fourteen-column source catalogue:
                         ``DB_no  RA  DEC  X_tpl  Y_tpl  V  V-I  I
                            Ng_V  Nb_V  sig_V  Ng_I  Nb_I  sig_I``

Public API
----------
``load_dat(filepath, ...)``        → DataFrame or TimeSeries
``parse_ogle2_map(filepath, ...)`` → DataFrame (catalogue)

The original ``parser.py`` function signatures are preserved verbatim as
backward-compatible aliases so existing code keeps working unchanged.
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import polars as pl

from ogle.base import BaseParser
from ogle.shared.utils import validate_dat, validate_map, read_whitespace


# ---------------------------------------------------------------------------
# Column definitions
# ---------------------------------------------------------------------------

#: Default column names for OGLE-II time-series files.
DAT_COLS: list[str] = ["hjd", "mag_i", "m_error"]

#: Column names for OGLE-II ``.map`` catalogue files.
#: DB_no  RA  DEC  X_tpl  Y_tpl  V  V-I  I  Ng_V  Nb_V  sig_V  Ng_I  Nb_I  sig_I
MAP_COLS: list[str] = [
    "DB_no", "RA", "DEC", "X_tpl", "Y_tpl",
    "V", "V-I", "I",
    "Ng_V", "Nb_V", "sig_V",
    "Ng_I", "Nb_I", "sig_I",
]


# ---------------------------------------------------------------------------
# load_dat  — time-series photometry
# ---------------------------------------------------------------------------

def load_dat(
    filepath: str | os.PathLike,
    polars: bool = True,
    col_names: list[str] | None = None,
    as_timeseries: bool = False,
    magnitude: str = "I mag",
    time_scale: str = "HJD",
) -> pd.DataFrame | pl.DataFrame | object:
    """
    Load an OGLE-II ``.dat`` photometry file.

    Parameters
    ----------
    filepath : str | os.PathLike
        Path to the ``.dat`` or ``.lc`` photometry file.
    polars : bool
        Return a Polars DataFrame (default).  Pass ``False`` for Pandas.
        Ignored when *as_timeseries* is True.
    col_names : list[str] | None
        Override the default column names ``['hjd', 'mag_i', 'm_error']``.
    as_timeseries : bool
        If True, return a ``varistar.TimeSeries`` object instead of a raw
        DataFrame.  The TimeSeries is fully populated and ready for period
        analysis — just call ``lc = LightCurve(ts)`` next.
    magnitude : str
        Magnitude label passed to ``TimeSeries`` (only used when
        *as_timeseries* is True).
    time_scale : str
        Time-scale label passed to ``TimeSeries`` (only used when
        *as_timeseries* is True).

    Returns
    -------
    pd.DataFrame | pl.DataFrame | varistar.TimeSeries
        Photometry data in the requested format.

    Raises
    ------
    FileNotFoundError
        If *filepath* does not exist.
    ValueError
        If the file extension is not ``.dat`` or ``.lc``.

    Examples
    --------
    Raw Polars DataFrame::

        from ogle.ogle2.parser import load_dat
        df = load_dat("bul_sc1.01.123456.dat")

    Straight into a varistar TimeSeries::

        ts = load_dat("bul_sc1.01.123456.dat", as_timeseries=True)
        lc = LightCurve(ts)
        lc.run_ls()

    Backward-compatible Pandas call (matches original parser.py signature)::

        df = load_dat("star.dat", polars=False)
    """
    path     = validate_dat(filepath)
    cols     = col_names or DAT_COLS
    df_polar = read_whitespace(path, col_names=cols, as_polars=True)

    # --- varistar integration ---
    if as_timeseries:
        return _to_timeseries(df_polar, cols, path.stem, magnitude, time_scale)

    return df_polar if polars else df_polar.to_pandas()


# ---------------------------------------------------------------------------
# parse_ogle2_map  — catalogue / map file
# ---------------------------------------------------------------------------

def parse_ogle2_map(
    file_path: str | os.PathLike,
    polars: bool = True,
) -> pd.DataFrame | pl.DataFrame:
    """
    Parse an OGLE-II ``.map`` source catalogue file.

    The map file lists one star per line with positions, mean magnitudes, and
    quality statistics for both the V and I bands.

    Parameters
    ----------
    file_path : str | os.PathLike
        Path to the ``.map`` file.
    polars : bool
        Return a Polars DataFrame (default).  Pass ``False`` for Pandas.

    Returns
    -------
    pd.DataFrame | pl.DataFrame
        Columns: ``['DB_no', 'RA', 'DEC', 'X_tpl', 'Y_tpl', 'V', 'V-I', 'I',
        'Ng_V', 'Nb_V', 'sig_V', 'Ng_I', 'Nb_I', 'sig_I']``

    Raises
    ------
    FileNotFoundError
        If *file_path* does not exist.
    ValueError
        If the extension is not ``.map``.

    Examples
    --------
    >>> df = parse_ogle2_map("bul_sc1.map")
    >>> df.shape
    (n_stars, 14)

    Add decimal-degree coordinates::

        from ogle.shared.coords import convert_ra_dec
        df = convert_ra_dec(df)
    """
    path     = validate_map(file_path)
    df_polar = read_whitespace(path, col_names=MAP_COLS, as_polars=True)
    return df_polar if polars else df_polar.to_pandas()


# ---------------------------------------------------------------------------
# OGLE2Parser class  (implements BaseParser interface)
# ---------------------------------------------------------------------------

class OGLE2Parser(BaseParser):
    """
    Concrete parser for OGLE-II file formats.

    Implements the ``BaseParser`` interface so the parser can be passed
    to generic functions that accept any OGLE version's parser.

    Parameters
    ----------
    col_names : list[str] | None
        Override the default time-series column names.

    Examples
    --------
    >>> parser = OGLE2Parser()
    >>> df = parser.load_dat("bul_sc1.01.123456.dat")
    >>> cat = parser.parse_catalogue("bul_sc1.map")
    """

    DEFAULT_COLS = DAT_COLS

    def load_dat(  # type: ignore[override]
        self,
        filepath: str | Path,
        as_polars: bool = True,
        as_timeseries: bool = False,
    ) -> pd.DataFrame | pl.DataFrame | object:
        """Load a single OGLE-II ``.dat`` photometry file."""
        return load_dat(
            filepath,
            polars=as_polars,
            col_names=self.col_names,
            as_timeseries=as_timeseries,
        )

    def parse_catalogue(  # type: ignore[override]
        self,
        filepath: str | Path,
        as_polars: bool = True,
    ) -> pd.DataFrame | pl.DataFrame:
        """Parse an OGLE-II ``.map`` catalogue file."""
        return parse_ogle2_map(filepath, polars=as_polars)


# ---------------------------------------------------------------------------
# varistar integration helper
# ---------------------------------------------------------------------------

def _to_timeseries(
    df: pl.DataFrame,
    col_names: list[str],
    stem: str,
    magnitude: str,
    time_scale: str,
) -> object:
    """
    Wrap a Polars photometry DataFrame in a ``varistar.TimeSeries``.

    Soft-imports varistar so the ogle package stays usable even when
    varistar is not installed (the function raises a clear ImportError
    only when ``as_timeseries=True`` is actually requested).
    """
    try:
        from varistar.timeseries import TimeSeries
    except ImportError as exc:
        raise ImportError(
            "varistar must be installed to use as_timeseries=True. "
            "Install it with: pip install varistar"
        ) from exc

    ts = TimeSeries(
        magnitude=magnitude,
        time_scale=time_scale,
        colnames=col_names,
    )
    ts.load_data_from_df(df, data_id=stem)
    return ts