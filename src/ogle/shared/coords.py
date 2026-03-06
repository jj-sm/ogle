"""
ogle.shared.coords
==================
Coordinate parsing and conversion utilities shared across all OGLE versions.

OGLE catalogue files store equatorial coordinates as sexagesimal strings::

    RA  → 'HH:MM:SS.ss'
    DEC → '±DD:MM:SS.ss'

All functions handle plain strings, pandas Series, or polars Series and
always return values in decimal degrees (float64).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import polars as pl


# ---------------------------------------------------------------------------
# Scalar converters
# ---------------------------------------------------------------------------

def ra_to_deg(ra_str: str) -> float:
    """
    Convert a right-ascension string ``'HH:MM:SS.ss'`` to decimal degrees.

    Examples
    --------
    >>> ra_to_deg('05:34:31.97')
    83.63320833333333
    """
    try:
        h, m, s = ra_str.strip().split(":")
        return 15.0 * (float(h) + float(m) / 60.0 + float(s) / 3600.0)
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"Cannot parse RA string: {ra_str!r}") from exc


def dec_to_deg(dec_str: str) -> float:
    """
    Convert a declination string ``'±DD:MM:SS.ss'`` to decimal degrees.

    The leading sign is optional; absence of a sign is treated as positive.

    Examples
    --------
    >>> dec_to_deg('-05:23:28.0')
    -5.391111111111111
    """
    s = dec_str.strip()
    sign = -1.0 if s.startswith("-") else 1.0
    s = s.lstrip("+-")
    try:
        d, m, sec = s.split(":")
        return sign * (float(d) + float(m) / 60.0 + float(sec) / 3600.0)
    except (ValueError, AttributeError) as exc:
        raise ValueError(f"Cannot parse DEC string: {dec_str!r}") from exc


# ---------------------------------------------------------------------------
# DataFrame-level converter  (pandas + polars, matches original API)
# ---------------------------------------------------------------------------

def convert_ra_dec(
    df: pd.DataFrame | pl.DataFrame,
    ra_col: str = "RA",
    dec_col: str = "DEC",
    out_ra: str = "RA_deg",
    out_dec: str = "DEC_deg",
    drop_original: bool = False,
) -> pd.DataFrame | pl.DataFrame:
    """
    Append decimal-degree RA / DEC columns to a catalogue DataFrame.

    Accepts both Pandas and Polars DataFrames — type is detected automatically
    and the same type is returned.

    Parameters
    ----------
    df : pd.DataFrame | pl.DataFrame
        Catalogue with sexagesimal coordinate columns.
    ra_col, dec_col : str
        Source column names (default ``'RA'``, ``'DEC'``).
    out_ra, out_dec : str
        Output column names (default ``'RA_deg'``, ``'DEC_deg'``).
    drop_original : bool
        Remove the source string columns after conversion.

    Returns
    -------
    pd.DataFrame | pl.DataFrame
        Same type as *df*, with *out_ra* and *out_dec* appended.
    """
    if isinstance(df, pl.DataFrame):
        df = df.with_columns(
            pl.col(ra_col).map_elements(ra_to_deg,  return_dtype=pl.Float64).alias(out_ra),
            pl.col(dec_col).map_elements(dec_to_deg, return_dtype=pl.Float64).alias(out_dec),
        )
        if drop_original:
            df = df.drop([ra_col, dec_col])
    else:
        df = df.copy()
        df[out_ra]  = df[ra_col].apply(ra_to_deg)
        df[out_dec] = df[dec_col].apply(dec_to_deg)
        if drop_original:
            df = df.drop(columns=[ra_col, dec_col])
    return df


# ---------------------------------------------------------------------------
# Angular separation
# ---------------------------------------------------------------------------

def angular_separation_deg(
    ra1: float, dec1: float,
    ra2: float, dec2: float,
) -> float:
    """
    Great-circle angular separation (decimal degrees in, decimal degrees out).

    Uses the Vincenty formula — numerically stable at all separations.
    """
    r1, d1 = np.radians(ra1), np.radians(dec1)
    r2, d2 = np.radians(ra2), np.radians(dec2)
    dra = r2 - r1
    num = np.sqrt(
        (np.cos(d2) * np.sin(dra)) ** 2
        + (np.cos(d1) * np.sin(d2) - np.sin(d1) * np.cos(d2) * np.cos(dra)) ** 2
    )
    den = np.sin(d1) * np.sin(d2) + np.cos(d1) * np.cos(d2) * np.cos(dra)
    return float(np.degrees(np.arctan2(num, den)))