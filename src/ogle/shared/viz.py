"""
ogle.shared.viz
===============
Shared matplotlib visualisation helpers for OGLE catalogue and field data.

All functions accept both Pandas and Polars DataFrames and create
publication-ready plots consistent with the varistar style conventions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import pandas as pd
import polars as pl

if TYPE_CHECKING:
    pass


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _to_pandas(df: pd.DataFrame | pl.DataFrame) -> pd.DataFrame:
    """Normalise to Pandas regardless of input type."""
    return df.to_pandas() if isinstance(df, pl.DataFrame) else df


def _ax_or_figure(
    ax: plt.Axes | None,
    fig_size: tuple[int, int],
) -> tuple[plt.Axes, bool]:
    if ax is None:
        plt.rcParams.update({"font.family": "monospace"})
        _, ax = plt.subplots(figsize=fig_size)
        return ax, True
    return ax, False


def _finalise(ax: plt.Axes, own: bool, save_path: str | None) -> None:
    if not own:
        return
    plt.tight_layout()
    if save_path:
        ax.get_figure().savefig(save_path, bbox_inches="tight", dpi=200)
        plt.close(ax.get_figure())
    else:
        plt.show()


# ---------------------------------------------------------------------------
# Field map  (RA / DEC scatter)
# ---------------------------------------------------------------------------

def plot_field_map(
    df: pd.DataFrame | pl.DataFrame,
    ra_col: str = "RA_deg",
    dec_col: str = "DEC_deg",
    color_col: str | None = "I",
    label_col: str | None = None,
    field_name: str = "",
    fig_size: tuple[int, int] = (8, 6),
    save_path: str | None = None,
    ax: plt.Axes | None = None,
    **scatter_kwargs,
) -> None:
    """
    Scatter plot of stellar positions in a single OGLE field.

    Parameters
    ----------
    df : pd.DataFrame | pl.DataFrame
        Catalogue DataFrame (e.g. output of ``parse_ogle2_map``).
    ra_col, dec_col : str
        Coordinate columns to plot.  Expects decimal degrees.
        If the ``RA_deg`` / ``DEC_deg`` columns are missing, falls back to
        the raw sexagesimal ``RA`` / ``DEC`` columns after conversion.
    color_col : str | None
        Column used to colour-code the points (e.g. ``'I'`` magnitude,
        ``'V-I'`` colour).  Pass ``None`` for a monochrome plot.
    label_col : str | None
        Column whose value is shown as a hover annotation on each point
        (only in interactive backends; silent in non-interactive mode).
    field_name : str
        Used in the plot title.
    ax : plt.Axes | None
        External axis for embedding.
    """
    data = _to_pandas(df)

    # Fallback: convert sexagesimal if decimal columns are missing
    if ra_col not in data.columns or dec_col not in data.columns:
        from ogle.shared.coords import convert_ra_dec
        data = convert_ra_dec(data)  # type: ignore[arg-type]

    ax, own = _ax_or_figure(ax, fig_size)

    # Colour mapping
    c = data[color_col].values if (color_col and color_col in data.columns) else None
    sc = ax.scatter(
        data[ra_col], data[dec_col],
        c=c,
        cmap="viridis_r" if c is not None else None,
        s=scatter_kwargs.pop("s", 4),
        alpha=scatter_kwargs.pop("alpha", 0.7),
        edgecolors="none",
        **scatter_kwargs,
    )
    if c is not None:
        cbar = ax.get_figure().colorbar(sc, ax=ax, pad=0.01)
        cbar.set_label(color_col, fontsize=9)

    ax.set_xlabel("RA (deg)", fontsize=10)
    ax.set_ylabel("DEC (deg)", fontsize=10)
    ax.set_title(
        f"OGLE-II Field: {field_name}" if field_name else "OGLE-II Field Map",
        fontsize=11,
    )
    # Astronomical convention: RA increases to the left
    ax.invert_xaxis()
    ax.tick_params(direction="in", which="both", top=True, right=True, labelsize=8)
    ax.minorticks_on()
    ax.grid(True, alpha=0.2, linestyle="--")

    _finalise(ax, own, save_path)


# ---------------------------------------------------------------------------
# Magnitude / colour distributions
# ---------------------------------------------------------------------------

def plot_cmd(
    df: pd.DataFrame | pl.DataFrame,
    x_col: str = "V-I",
    y_col: str = "I",
    field_name: str = "",
    fig_size: tuple[int, int] = (6, 7),
    save_path: str | None = None,
    ax: plt.Axes | None = None,
    **scatter_kwargs,
) -> None:
    """
    Colour-Magnitude Diagram (CMD) for an OGLE-II field catalogue.

    Parameters
    ----------
    df : pd.DataFrame | pl.DataFrame
        Catalogue DataFrame containing *x_col* (colour) and *y_col* (magnitude).
    x_col : str
        Colour index column (default ``'V-I'``).
    y_col : str
        Magnitude column to plot on the y-axis (default ``'I'``).
    field_name : str
        Field identifier for the plot title.
    """
    data = _to_pandas(df)

    # Drop rows where either column is NaN or sentinel (e.g. 99.99)
    valid = data[(data[x_col] < 90) & (data[y_col] < 90)]

    ax, own = _ax_or_figure(ax, fig_size)

    ax.scatter(
        valid[x_col], valid[y_col],
        s=scatter_kwargs.pop("s", 1),
        alpha=scatter_kwargs.pop("alpha", 0.3),
        color=scatter_kwargs.pop("color", "#2C3E50"),
        edgecolors="none",
        **scatter_kwargs,
    )
    ax.invert_yaxis()
    ax.set_xlabel(x_col, fontsize=10)
    ax.set_ylabel(f"{y_col} mag", fontsize=10)
    ax.set_title(
        f"CMD: {field_name}" if field_name else "CMD",
        fontsize=11,
    )
    ax.tick_params(direction="in", which="both", top=True, right=True, labelsize=8)
    ax.minorticks_on()
    ax.grid(True, alpha=0.15, linestyle="--")

    _finalise(ax, own, save_path)


def plot_mag_histogram(
    df: pd.DataFrame | pl.DataFrame,
    mag_col: str = "I",
    bins: int = 60,
    field_name: str = "",
    fig_size: tuple[int, int] = (7, 4),
    save_path: str | None = None,
    ax: plt.Axes | None = None,
) -> None:
    """
    Histogram of stellar magnitudes in an OGLE-II field catalogue.

    Useful for quickly assessing survey depth and completeness limits.

    Parameters
    ----------
    df : pd.DataFrame | pl.DataFrame
        Catalogue DataFrame.
    mag_col : str
        Magnitude column (default ``'I'``).
    bins : int
        Number of histogram bins.
    """
    data = _to_pandas(df)
    mags = data[mag_col].values
    mags = mags[mags < 90]  # Drop sentinel values

    ax, own = _ax_or_figure(ax, fig_size)

    ax.hist(mags, bins=bins, color="#2980B9", edgecolor="#1A5276", alpha=0.8)
    ax.set_xlabel(f"{mag_col} magnitude", fontsize=10)
    ax.set_ylabel("Number of stars", fontsize=10)
    ax.set_title(
        f"Magnitude distribution: {field_name}" if field_name else "Magnitude distribution",
        fontsize=11,
    )
    ax.tick_params(direction="in", which="both", top=True, right=True, labelsize=8)
    ax.minorticks_on()
    ax.grid(True, alpha=0.2, axis="y", linestyle="--")

    _finalise(ax, own, save_path)