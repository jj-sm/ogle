"""
ogle.ogle2.fetcher
==================
Remote data fetcher for the OGLE-II public archive.

.. note::
   **Not yet implemented.**  This module documents the planned interface
   and the remote archive structure so the implementation can be dropped
   in without any changes to user code.

OGLE-II archive
---------------
The OGLE-II photometry archive is hosted at the Warsaw University Astronomical
Observatory.  The base URL structure is::

    https://www.astrouw.edu.pl/ogle/ogle2/phot/
        {survey_area}/          e.g. bul/, lmc/, smc/
            {field}/            e.g. bul_sc1/, lmc_sc1/
                {chip}/         e.g. 01/ … 10/
                    {star}.dat  e.g. 123456.dat

Map catalogue files are served alongside the photometry::

    https://www.astrouw.edu.pl/ogle/ogle2/maps/{field}.map

Planned API
-----------
>>> fetcher = OGLE2Fetcher(cache_dir="~/.cache/ogle/ogle2")
>>> path = fetcher.fetch_dat("123456", field="bul_sc1", chip="01")
>>> ts   = fetcher.fetch_timeseries("123456", field="bul_sc1", chip="01")
>>> cat  = fetcher.fetch_map("bul_sc1")
"""

from __future__ import annotations

from pathlib import Path

from ogle.base import BaseFetcher


class OGLE2Fetcher(BaseFetcher):
    """
    Fetcher for OGLE-II photometry and catalogue data.

    Parameters
    ----------
    cache_dir : str | Path | None
        Local cache directory.  Defaults to ``~/.cache/ogle/ogle2/``.
    timeout : float
        HTTP request timeout in seconds.
    base_url : str
        Root URL of the OGLE-II archive.
    """

    SURVEY   = "ogle2"
    BASE_URL = "https://www.astrouw.edu.pl/ogle/ogle2"

    def __init__(
        self,
        cache_dir: str | Path | None = None,
        timeout: float = 30.0,
        base_url: str = BASE_URL,
    ) -> None:
        super().__init__(cache_dir=cache_dir, timeout=timeout)
        self.base_url = base_url.rstrip("/")

    # ------------------------------------------------------------------
    # Not yet implemented — raise NotImplementedError with roadmap info
    # ------------------------------------------------------------------

    def fetch_dat(
        self,
        star_id: str,
        field: str,
        chip: str = "01",
        survey_area: str = "bul",
        save: bool = True,
    ) -> Path:
        """
        Download the ``.dat`` photometry file for a single OGLE-II star.

        Parameters
        ----------
        star_id : str
            Six-digit star sequence number (e.g. ``'123456'``).
        field : str
            Field identifier (e.g. ``'bul_sc1'``).
        chip : str
            CCD chip number (e.g. ``'01'``).
        survey_area : str
            Top-level archive area: ``'bul'`` (Bulge), ``'lmc'``, or ``'smc'``.
        save : bool
            Persist the downloaded file in ``self.cache_dir``.

        Returns
        -------
        Path
            Local path to the downloaded ``.dat`` file.

        Planned URL
        -----------
        ``{BASE_URL}/phot/{survey_area}/{field}/{chip}/{star_id}.dat``
        """
        raise NotImplementedError(
            "OGLE2Fetcher.fetch_dat() is not yet implemented.\n"
            "To load local .dat files, use ogle.ogle2.parser.load_dat() directly."
        )

    def fetch_timeseries(
        self,
        star_id: str,
        field: str,
        chip: str = "01",
        survey_area: str = "bul",
        as_timeseries: bool = True,
    ) -> object:
        """
        Download an OGLE-II photometry file and return it as a
        ``varistar.TimeSeries`` (when *as_timeseries* is True).

        This is a convenience wrapper: ``fetch_dat`` + ``load_dat(as_timeseries=True)``.
        """
        raise NotImplementedError(
            "OGLE2Fetcher.fetch_timeseries() is not yet implemented."
        )

    def fetch_map(
        self,
        field: str,
        survey_area: str = "bul",
        save: bool = True,
    ) -> Path:
        """
        Download the ``.map`` source catalogue for an OGLE-II field.

        Planned URL
        -----------
        ``{BASE_URL}/maps/{survey_area}/{field}.map``
        """
        raise NotImplementedError(
            "OGLE2Fetcher.fetch_map() is not yet implemented.\n"
            "To load local .map files, use ogle.ogle2.parser.parse_ogle2_map() directly."
        )

    def list_fields(self, survey_area: str = "bul") -> list[str]:
        """
        Return the list of available OGLE-II fields for a survey area.

        Planned implementation: scrape the archive index page.
        """
        raise NotImplementedError("OGLE2Fetcher.list_fields() is not yet implemented.")