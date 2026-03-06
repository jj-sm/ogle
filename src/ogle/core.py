"""
ogle.core
=========
High-level objects that tie together parsers, catalogue data, and varistar
time-series loading into a single convenient interface.

``OGLE2Field``
    Represents a single OGLE-II survey field.  Wraps a parsed ``.map``
    catalogue and a directory of ``.dat`` photometry files.  Provides
    iteration, lookup-by-ID, and batch loading.

Design goals
------------
* Zero boilerplate: ``OGLE2Field.from_directory("bul_sc1/")`` is enough to
  start working with a whole field.
* varistar-aware: every loader accepts ``as_timeseries=True`` to skip the
  raw DataFrame step entirely.
* Survey-agnostic base: ``BaseField`` will be reused by OGLE3Field, etc.
"""

from __future__ import annotations

from pathlib import Path
from typing import Generator

import polars as pl
import pandas as pd

from ogle.base import OGLEStar
from ogle.shared.utils import (
    find_dat_files,
    parse_ogle2_filename,
)


# ---------------------------------------------------------------------------
# OGLE2Field
# ---------------------------------------------------------------------------

class OGLE2Field:
    """
    Container for all data associated with a single OGLE-II survey field.

    Typical usage
    -------------
    Load from a directory of ``.dat`` files (no map required)::

        field = OGLE2Field.from_directory("path/to/bul_sc1/")
        for ts in field.iter_timeseries():
            lc = LightCurve(ts)
            lc.run_ls()

    Load from a ``.map`` catalogue + photometry directory::

        field = OGLE2Field.from_map("bul_sc1.map", dat_dir="path/to/bul_sc1/")
        ts = field.get_timeseries("bul_sc1.01.123456")

    Attributes
    ----------
    name : str
        Field identifier (e.g. ``'bul_sc1'``).
    dat_dir : Path | None
        Directory containing ``.dat`` photometry files.
    map_path : Path | None
        Path to the ``.map`` catalogue file, if loaded.
    catalogue : pl.DataFrame
        Parsed catalogue table (empty if no map was loaded).
    _dat_files : dict[str, Path]
        Mapping of ``ogle_id → Path`` for all discovered ``.dat`` files.
    """

    def __init__(
        self,
        name: str,
        dat_dir: str | Path | None = None,
        map_path: str | Path | None = None,
    ) -> None:
        self.name      = name
        self.dat_dir   = Path(dat_dir).resolve() if dat_dir else None
        self.map_path  = Path(map_path).resolve() if map_path else None
        self.catalogue: pl.DataFrame = pl.DataFrame()
        self._dat_files: dict[str, Path] = {}
        self._stars: dict[str, OGLEStar] = {}

        if self.dat_dir:
            self._index_dat_files()
        if self.map_path:
            self._load_catalogue()

    # ------------------------------------------------------------------
    # Constructors
    # ------------------------------------------------------------------

    @classmethod
    def from_directory(
        cls,
        dat_dir: str | Path,
        glob: str = "*.dat",
        name: str | None = None,
    ) -> "OGLE2Field":
        """
        Build an ``OGLE2Field`` from a directory of ``.dat`` files.

        No map file is required.  The field name is inferred from the
        first file's stem if *name* is not provided.

        Parameters
        ----------
        dat_dir : str | Path
            Directory containing OGLE-II ``.dat`` photometry files.
        glob : str
            Filename glob pattern (default ``'*.dat'``).
        name : str | None
            Override the inferred field name.

        Returns
        -------
        OGLE2Field
        """
        root = Path(dat_dir).resolve()
        field_name = name or root.name
        obj = cls(name=field_name, dat_dir=root)
        obj._index_dat_files(glob=glob)
        print(
            f"[OGLE2Field] '{field_name}' — "
            f"{len(obj._dat_files)} photometry files indexed."
        )
        return obj

    @classmethod
    def from_map(
        cls,
        map_path: str | Path,
        dat_dir: str | Path | None = None,
        glob: str = "*.dat",
    ) -> "OGLE2Field":
        """
        Build an ``OGLE2Field`` from a ``.map`` catalogue, optionally linking
        a directory of ``.dat`` photometry files.

        Parameters
        ----------
        map_path : str | Path
            Path to the OGLE-II ``.map`` catalogue file.
        dat_dir : str | Path | None
            Directory of ``.dat`` photometry files.  Omit if you only need
            catalogue data without time-series.
        glob : str
            Filename glob (passed to ``from_directory``).

        Returns
        -------
        OGLE2Field
        """
        mp = Path(map_path).resolve()
        field_name = mp.stem  # e.g. 'bul_sc1' from 'bul_sc1.map'
        obj = cls(name=field_name, dat_dir=dat_dir, map_path=mp)
        print(
            f"[OGLE2Field] '{field_name}' — "
            f"{len(obj.catalogue)} catalogue rows, "
            f"{len(obj._dat_files)} photometry files."
        )
        return obj

    # ------------------------------------------------------------------
    # Repr
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return (
            f"OGLE2Field(name='{self.name}', "
            f"n_dat={len(self._dat_files)}, "
            f"n_catalogue={len(self.catalogue)})"
        )

    def __len__(self) -> int:
        return len(self._dat_files)

    # ------------------------------------------------------------------
    # Indexing and catalogue loading
    # ------------------------------------------------------------------

    def _index_dat_files(self, glob: str = "*.dat") -> None:
        """Scan ``self.dat_dir`` and populate ``self._dat_files``."""
        if self.dat_dir is None or not self.dat_dir.is_dir():
            return
        files = find_dat_files(self.dat_dir, glob=glob)
        for fp in files:
            info = parse_ogle2_filename(fp)
            self._dat_files[info["ogle_id"]] = fp

    def _load_catalogue(self) -> None:
        """Parse ``self.map_path`` and populate ``self.catalogue``."""
        if self.map_path is None:
            return
        from ogle.ogle2.parser import parse_ogle2_map
        self.catalogue = parse_ogle2_map(self.map_path, polars=True)  # type: ignore[arg-type]
        # Build OGLEStar records for each row
        from ogle.shared.coords import convert_ra_dec
        cat_deg = convert_ra_dec(self.catalogue)
        for row in cat_deg.iter_rows(named=True):
            db_no = str(row["DB_no"])
            star  = OGLEStar(
                ogle_id  = f"{self.name}.{db_no}",
                field    = self.name,
                star_no  = db_no,
                ra_deg   = row.get("RA_deg"),
                dec_deg  = row.get("DEC_deg"),
                mag_i    = row.get("I"),
                mag_v    = row.get("V"),
                color_vi = row.get("V-I"),
                dat_path = self._dat_files.get(f"{self.name}.{db_no}"),
            )
            self._stars[db_no] = star

    # ------------------------------------------------------------------
    # Single-star access
    # ------------------------------------------------------------------

    def get_dat_path(self, ogle_id: str) -> Path:
        """
        Return the ``Path`` to the ``.dat`` file for *ogle_id*.

        Parameters
        ----------
        ogle_id : str
            Full OGLE-II identifier, e.g. ``'bul_sc1.01.123456'``, OR
            just the filename stem, e.g. ``'bul_sc1.01.123456'``.

        Raises
        ------
        KeyError
            If no matching photometry file is indexed.
        """
        if ogle_id in self._dat_files:
            return self._dat_files[ogle_id]
        # Try matching by stem only
        for key, path in self._dat_files.items():
            if key.endswith(ogle_id) or ogle_id.endswith(key):
                return path
        raise KeyError(
            f"No .dat file indexed for '{ogle_id}' in field '{self.name}'.\n"
            f"Available IDs (first 5): {list(self._dat_files)[:5]}"
        )

    def get_dataframe(
        self,
        ogle_id: str,
        as_polars: bool = True,
    ) -> "pl.DataFrame | pd.DataFrame":
        """
        Load and return the photometry DataFrame for *ogle_id*.

        Parameters
        ----------
        ogle_id : str
            OGLE-II source identifier.
        as_polars : bool
            Return Polars (default) or Pandas.
        """
        from ogle.ogle2.parser import load_dat
        return load_dat(self.get_dat_path(ogle_id), polars=as_polars)

    def get_timeseries(
        self,
        ogle_id: str,
        magnitude: str = "I mag",
        time_scale: str = "HJD",
    ) -> object:
        """
        Load the photometry for *ogle_id* and return a
        ``varistar.TimeSeries`` object.

        Parameters
        ----------
        ogle_id : str
            OGLE-II source identifier.
        magnitude, time_scale : str
            Labels passed to the TimeSeries constructor.

        Returns
        -------
        varistar.TimeSeries

        Example
        -------
        >>> ts = field.get_timeseries("bul_sc1.01.123456")
        >>> lc = LightCurve(ts)
        >>> lc.run_ls()
        """
        from ogle.ogle2.parser import load_dat
        return load_dat(
            self.get_dat_path(ogle_id),
            as_timeseries=True,
            magnitude=magnitude,
            time_scale=time_scale,
        )

    def get_star(self, db_no: str) -> OGLEStar | None:
        """
        Return the ``OGLEStar`` record for a star by its catalogue DB number.

        Requires a map file to have been loaded.  Returns None if the star
        is not in the catalogue.
        """
        return self._stars.get(str(db_no))

    # ------------------------------------------------------------------
    # Iteration
    # ------------------------------------------------------------------

    def iter_dataframes(
        self,
        as_polars: bool = True,
        skip_errors: bool = True,
    ) -> Generator["pl.DataFrame | pd.DataFrame", None, None]:
        """
        Yield photometry DataFrames for every indexed star.

        Parameters
        ----------
        as_polars : bool
            Yield Polars (default) or Pandas DataFrames.
        skip_errors : bool
            If True, log and skip files that fail to parse; otherwise raise.
        """
        from ogle.ogle2.parser import load_dat
        for ogle_id, path in self._dat_files.items():
            try:
                yield load_dat(path, polars=as_polars)
            except Exception as exc:
                if skip_errors:
                    print(f"[OGLE2Field] Skipping '{ogle_id}': {exc}")
                else:
                    raise

    def iter_timeseries(
        self,
        magnitude: str = "I mag",
        time_scale: str = "HJD",
        skip_errors: bool = True,
    ) -> Generator[object, None, None]:
        """
        Yield a ``varistar.TimeSeries`` for every indexed photometry file.

        This is the primary entry point for batch varistar analysis::

            for ts in field.iter_timeseries():
                lc = LightCurve(ts)
                lc.run_ls()
                results.append(lc.to_dict())

        Parameters
        ----------
        skip_errors : bool
            Log and skip files that fail; otherwise raise.
        """
        from ogle.ogle2.parser import load_dat
        for ogle_id, path in self._dat_files.items():
            try:
                yield load_dat(
                    path,
                    as_timeseries=True,
                    magnitude=magnitude,
                    time_scale=time_scale,
                )
            except Exception as exc:
                if skip_errors:
                    print(f"[OGLE2Field] Skipping '{ogle_id}': {exc}")
                else:
                    raise

    # ------------------------------------------------------------------
    # Bulk export
    # ------------------------------------------------------------------

    @property
    def ogle_ids(self) -> list[str]:
        """Sorted list of all indexed OGLE-II source identifiers."""
        return sorted(self._dat_files.keys())

    def summary(self) -> None:
        """Print a human-readable summary of the field."""
        print(
            f"OGLE-II Field: {self.name}\n"
            f"  Photometry files : {len(self._dat_files)}\n"
            f"  Catalogue rows   : {len(self.catalogue)}\n"
            f"  Map file         : {self.map_path or '(not loaded)'}\n"
            f"  Data directory   : {self.dat_dir or '(not set)'}"
        )