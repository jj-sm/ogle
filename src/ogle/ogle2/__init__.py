"""
ogle.ogle2
==========
OGLE-II photometry and catalogue interface.

Quick start — raw DataFrame
---------------------------
>>> from ogle.ogle2 import load_dat, parse_ogle2_map
>>> df  = load_dat("bul_sc1.01.123456.dat")          # Polars DataFrame
>>> cat = parse_ogle2_map("bul_sc1.map")              # Catalogue

Quick start — varistar TimeSeries
----------------------------------
>>> from ogle.ogle2 import load_dat
>>> ts = load_dat("bul_sc1.01.123456.dat", as_timeseries=True)
>>> lc = LightCurve(ts)
>>> lc.run_ls()

Batch loading (via OGLE2Field)
------------------------------
>>> from ogle.ogle2 import OGLE2Field
>>> field = OGLE2Field.from_directory("bul_sc1/")
>>> for ts in field.iter_timeseries():
...     lc = LightCurve(ts)
"""

from ogle.ogle2.parser import (
    load_dat,
    parse_ogle2_map,
    OGLE2Parser,
    DAT_COLS,
    MAP_COLS,
)
from ogle.ogle2.fetcher import OGLE2Fetcher

# OGLE2Field is defined in ogle.core but re-exported here for convenience
from ogle.core import OGLE2Field

__all__ = [
    # Functional API (mirrors original parser.py)
    "load_dat",
    "parse_ogle2_map",
    # Class-based API
    "OGLE2Parser",
    "OGLE2Fetcher",
    "OGLE2Field",
    # Constants
    "DAT_COLS",
    "MAP_COLS",
]