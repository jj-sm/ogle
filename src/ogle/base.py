"""
ogle.base
=========
Abstract base classes that define the interface every OGLE sub-package must
implement.

Having a shared contract means:
* New survey versions (OGLE-V, etc.) slot in with no changes to user code.
* ``mypy`` / type checkers can validate call sites against the interface.
* Common logic (caching, logging, DataFrame normalisation) lives here once.

Concrete implementations live in ``ogle.ogle2``, ``ogle.ogle3``, etc.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import polars as pl


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass
class OGLEStar:
    """
    Minimal metadata record for a single OGLE source.

    Populated by ``BaseParser.parse_catalogue()`` and used as keys when
    loading time-series data on demand.

    Attributes
    ----------
    ogle_id : str
        Canonical source identifier, e.g. ``'bul_sc1.01.123456'``.
    field : str
        Survey field code, e.g. ``'bul_sc1'``.
    chip : str
        CCD chip identifier, e.g. ``'01'``.
    star_no : str
        Star sequence number within the chip, e.g. ``'123456'``.
    ra_deg : float | None
        Right ascension in decimal degrees.
    dec_deg : float | None
        Declination in decimal degrees.
    mag_i : float | None
        Mean I-band magnitude from the catalogue.
    mag_v : float | None
        Mean V-band magnitude from the catalogue (if available).
    color_vi : float | None
        V − I colour index from the catalogue (if available).
    dat_path : Path | None
        Resolved path to the photometry ``.dat`` file for this star.
    """
    ogle_id:  str
    field:    str              = ""
    chip:     str              = ""
    star_no:  str              = ""
    ra_deg:   float | None     = None
    dec_deg:  float | None     = None
    mag_i:    float | None     = None
    mag_v:    float | None     = None
    color_vi: float | None     = None
    dat_path: Path | None      = None

    def __repr__(self) -> str:
        ra  = f"{self.ra_deg:.4f}"  if self.ra_deg  is not None else "—"
        dec = f"{self.dec_deg:.4f}" if self.dec_deg is not None else "—"
        return (
            f"OGLEStar(id='{self.ogle_id}', "
            f"RA={ra}, DEC={dec}, I={self.mag_i})"
        )


@dataclass
class OGLEField:
    """
    Metadata record for an OGLE survey field.

    Attributes
    ----------
    name : str
        Field identifier, e.g. ``'bul_sc1'``.
    survey : str
        Survey version, e.g. ``'OGLE-II'``.
    ra_center : float | None
        Approximate field centre RA (decimal degrees).
    dec_center : float | None
        Approximate field centre DEC (decimal degrees).
    n_stars : int
        Number of sources in the catalogue.
    catalogue : pl.DataFrame
        Full parsed catalogue table.
    stars : list[OGLEStar]
        Per-star metadata records derived from the catalogue.
    """
    name:       str
    survey:     str                 = "OGLE-II"
    ra_center:  float | None        = None
    dec_center: float | None        = None
    n_stars:    int                 = 0
    catalogue:  pl.DataFrame        = field(default_factory=pl.DataFrame)
    stars:      list[OGLEStar]      = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            f"OGLEField(name='{self.name}', "
            f"survey='{self.survey}', "
            f"n_stars={self.n_stars})"
        )

    def __len__(self) -> int:
        return self.n_stars


# ---------------------------------------------------------------------------
# Abstract base classes
# ---------------------------------------------------------------------------

class BaseParser(abc.ABC):
    """
    Abstract interface for OGLE photometry parsers.

    Subclasses implement the survey-specific file format knowledge while the
    rest of the package interacts exclusively with this interface.

    Parameters
    ----------
    col_names : list[str] | None
        Override the default three-column names ``[time_col, mag_col, err_col]``.
    """

    #: Default column names for the time-series DataFrame.
    DEFAULT_COLS: list[str] = ["hjd", "mag_i", "m_error"]

    def __init__(self, col_names: list[str] | None = None) -> None:
        self.col_names = col_names or list(self.DEFAULT_COLS)

    @abc.abstractmethod
    def load_dat(
        self,
        filepath: str | Path,
        as_polars: bool = True,
    ) -> pd.DataFrame | pl.DataFrame:
        """
        Load a single photometry file into a DataFrame.

        Parameters
        ----------
        filepath : str | Path
            Path to the ``.dat`` (or ``.lc``) file.
        as_polars : bool
            Return Polars (True) or Pandas (False).

        Returns
        -------
        pd.DataFrame | pl.DataFrame
            Three-column photometry table.
        """

    @abc.abstractmethod
    def parse_catalogue(
        self,
        filepath: str | Path,
        as_polars: bool = True,
    ) -> pd.DataFrame | pl.DataFrame:
        """
        Parse a survey catalogue / map file.

        Parameters
        ----------
        filepath : str | Path
            Path to the catalogue file (``.map``, ``.cat``, etc.).
        as_polars : bool
            Return Polars (True) or Pandas (False).

        Returns
        -------
        pd.DataFrame | pl.DataFrame
            Catalogue table with at minimum RA, DEC, and magnitude columns.
        """


class BaseFetcher(abc.ABC):
    """
    Abstract interface for OGLE remote data fetchers.

    Fetchers handle downloading photometry and catalogue data from the OGLE
    public archive.  Authentication, caching, and retry logic are implemented
    here or in concrete subclasses.

    Parameters
    ----------
    cache_dir : str | Path | None
        Directory for caching downloaded files.  Defaults to
        ``~/.cache/ogle/{survey}/``.
    timeout : float
        HTTP request timeout in seconds.
    """

    SURVEY: str = "ogle"  # Overridden by subclasses, e.g. 'ogle2'

    def __init__(
        self,
        cache_dir: str | Path | None = None,
        timeout: float = 30.0,
    ) -> None:
        if cache_dir is None:
            cache_dir = Path.home() / ".cache" / "ogle" / self.SURVEY
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.timeout = timeout

    @abc.abstractmethod
    def fetch_dat(
        self,
        star_id: str,
        field: str,
        save: bool = True,
    ) -> Path:
        """
        Download the photometry file for *star_id* in *field*.

        Parameters
        ----------
        star_id : str
            Source identifier (survey-specific format).
        field : str
            Survey field code.
        save : bool
            Persist the downloaded file to ``self.cache_dir``.

        Returns
        -------
        Path
            Local path to the downloaded file.
        """

    def is_cached(self, filename: str) -> bool:
        """Return True if *filename* already exists in the local cache."""
        return (self.cache_dir / filename).exists()

    def cache_path(self, filename: str) -> Path:
        """Return the full path to *filename* in the local cache."""
        return self.cache_dir / filename