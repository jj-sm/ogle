"""
ogle
====
Python toolkit for working with OGLE (Optical Gravitational Lensing
Experiment) photometric survey data.

Currently implemented
---------------------
* **OGLE-II** — ``.dat`` time-series loading, ``.map`` catalogue parsing,
  field-level batch loading, varistar integration.

Planned
-------
* OGLE-I, OGLE-III, OGLE-IV parsers.
* Remote fetchers for all survey versions.

Quick start
-----------
Load a single photometry file as a raw DataFrame::

    from ogle.ogle2 import load_dat
    df = load_dat("bul_sc1.01.123456.dat")          # Polars DataFrame

Load directly into a varistar TimeSeries::

    from ogle.ogle2 import load_dat
    from varistar import LightCurve
    ts = load_dat("bul_sc1.01.123456.dat", as_timeseries=True)
    lc = LightCurve(ts)
    lc.run_ls()

Work with a whole field::

    from ogle.ogle2 import OGLE2Field
    field = OGLE2Field.from_map("bul_sc1.map", dat_dir="bul_sc1/")
    for ts in field.iter_timeseries():
        ...

Parse an OGLE-II source catalogue::

    from ogle.ogle2 import parse_ogle2_map
    from ogle.shared import convert_ra_dec
    cat = parse_ogle2_map("bul_sc1.map")
    cat = convert_ra_dec(cat)
"""

from ogle.ogle2.parser import load_dat, parse_ogle2_map, OGLE2Parser
from ogle.ogle2.fetcher import OGLE2Fetcher
from ogle.core import OGLE2Field
from ogle.base import OGLEStar, OGLEField, BaseParser, BaseFetcher

__version__ = "0.1.0"

__all__ = [
    # Functional API (top-level shortcuts to the most common operations)
    "load_dat",
    "parse_ogle2_map",
    # Class-based API
    "OGLE2Parser",
    "OGLE2Fetcher",
    "OGLE2Field",
    # Data containers
    "OGLEStar",
    "OGLEField",
    # Abstract bases (for extension authors)
    "BaseParser",
    "BaseFetcher",
]