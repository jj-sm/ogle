# ogle 🔭
![PyPI - Version](https://img.shields.io/pypi/v/ogle?style=flat-square)
![PyPI - License](https://img.shields.io/pypi/l/ogle?style=flat-square)
[![Python Versions](https://img.shields.io/pypi/pyversions/ogle.svg?style=flat-square)](https://pypi.org/project/ogle/)

**ogle** is a Python package designed to simplify the management, retrieval, and interaction with **Optical Gravitational Lensing Experiment (OGLE)** survey data. It provides a clean, type-annotated interface for astronomers and researchers to load photometry, parse source catalogues, and pipe data directly into analysis workflows — including native integration with the [varistar](https://github.com/jj-sm/varistar) variable-star toolkit.

---

## Features

* **Data Loading** — Parse OGLE-II `.dat` photometry and `.map` source catalogues with a single function call, returning either Polars or Pandas DataFrames.
* **varistar Integration** — Load any `.dat` file directly as a `varistar.TimeSeries`, ready for Lomb-Scargle, PDM, and Fourier analysis.
* **Field-Level Batch Processing** — `OGLE2Field` indexes an entire directory of photometry files and lets you iterate over them as DataFrames or TimeSeries objects with one loop.
* **Coordinate Utilities** — Convert OGLE sexagesimal RA/DEC strings to decimal degrees, compute angular separations, and cross-match catalogues.
* **Catalogue Visualisation** — Field maps, Colour-Magnitude Diagrams, and magnitude histograms directly from `.map` files.
* **Extensible Architecture** — Abstract base classes (`BaseParser`, `BaseFetcher`) ensure OGLE-I/III/IV implementations slot in without touching existing code.
* **Command-Line Interface** — Inspect files, print photometry, and summarise fields from the terminal with `ogle info`, `ogle load`, and `ogle field`.
* **Modern Workflow** — Full type annotations, `py.typed` marker, compatible with `uv`, `pip`, and `mypy`.

---

## Quick Start

### Load a single photometry file

```python
from ogle.ogle2 import load_dat

# Polars DataFrame (default)
df = load_dat("bul_sc1.01.123456.dat")

# Pandas DataFrame
df = load_dat("bul_sc1.01.123456.dat", polars=False)
```

### Load directly into a varistar TimeSeries

```python
from ogle.ogle2 import load_dat
from varistar import LightCurve

ts = load_dat("bul_sc1.01.123456.dat", as_timeseries=True)
lc = LightCurve(ts)
lc.run_ls()
lc.plot_best()
```

### Parse an OGLE-II source catalogue

```python
from ogle.ogle2 import parse_ogle2_map
from ogle.shared import convert_ra_dec

cat = parse_ogle2_map("bul_sc1.map")           # 14-column Polars DataFrame
cat = convert_ra_dec(cat)                       # Appends RA_deg, DEC_deg columns
```

### Work with a whole field

```python
from ogle.ogle2 import OGLE2Field
from varistar import LightCurve

# From a directory of .dat files only
field = OGLE2Field.from_directory("path/to/bul_sc1/")

# From a .map catalogue + photometry directory
field = OGLE2Field.from_map("bul_sc1.map", dat_dir="path/to/bul_sc1/")

field.summary()
# OGLE-II Field: bul_sc1
#   Photometry files : 3421
#   Catalogue rows   : 3421
#   Map file         : /data/bul_sc1.map

# Iterate as TimeSeries — direct varistar pipeline
results = []
for ts in field.iter_timeseries():
    lc = LightCurve(ts)
    lc.run_ls()
    results.append(lc.to_dict())

# Load a single star by its OGLE ID
ts = field.get_timeseries("bul_sc1.01.123456")
```

### Visualise a field catalogue

```python
from ogle.ogle2 import parse_ogle2_map
from ogle.shared.coords import convert_ra_dec
from ogle.shared.viz import plot_field_map, plot_cmd, plot_mag_histogram

cat = convert_ra_dec(parse_ogle2_map("bul_sc1.map"))

plot_field_map(cat, field_name="bul_sc1")
plot_cmd(cat, x_col="V-I", y_col="I")
plot_mag_histogram(cat, mag_col="I")
```

### Command-line interface

```bash
# Inspect a photometry file
ogle info bul_sc1.01.123456.dat

# Print the first 10 rows
ogle load bul_sc1.01.123456.dat --rows 10

# Summarise a whole field directory
ogle field ./bul_sc1/ --map bul_sc1.map
```

---

## Package Structure

```
src/ogle/
├── __init__.py          # Top-level shortcuts: load_dat, parse_ogle2_map, OGLE2Field
├── base.py              # Abstract base classes: BaseParser, BaseFetcher
│                        # Data containers: OGLEStar, OGLEField
├── core.py              # OGLE2Field — field-level batch loading and iteration
├── cli.py               # Argparse CLI: ogle info / load / field
├── shared/
│   ├── coords.py        # ra_to_deg, dec_to_deg, convert_ra_dec, angular_separation_deg
│   ├── utils.py         # File validation, directory scanning, OGLE ID parsing
│   └── viz.py           # Field maps, CMD plots, magnitude histograms (matplotlib)
└── ogle2/
    ├── parser.py        # load_dat(), parse_ogle2_map(), OGLE2Parser class
    └── fetcher.py       # OGLE2Fetcher (remote download — planned)
```

---

## Roadmap & Feature Status

> **Legend:**
> - ✅ **Completed** — Stable and available in the current version.
> - 🏗️ **In Progress** — Actively being developed.
> - 📅 **Planned** — On the radar for a future release.

### OGLE-I

| Feature | Status | Priority |
|:--------|:------:|:--------:|
| `BaseParser` / `BaseFetcher` interface defined | ✅ Completed | — |
| `.dat` parser implementation | 📅 Planned | Low |
| Remote fetcher | 📅 Planned | Low |


### OGLE-II

| Feature | Status | Priority |
|:--------|:------:|:--------:|
| `.dat` photometry loading (Polars + Pandas) | ✅ Completed | High |
| `.map` source catalogue parsing | ✅ Completed | High |
| `OGLE2Field` — field-level batch loading | ✅ Completed | High |
| `varistar.TimeSeries` integration (`as_timeseries=True`) | ✅ Completed | High |
| Coordinate conversion (RA/DEC → decimal degrees) | ✅ Completed | High |
| Field map, CMD, magnitude histogram plots | ✅ Completed | Medium |
| Angular separation & cross-matching utilities | ✅ Completed | Medium |
| `OGLE2Parser` class (implements `BaseParser`) | ✅ Completed | Medium |
| CLI — `ogle info / load / field` | ✅ Completed | Medium |
| Remote `.dat` fetching (`OGLE2Fetcher`) | 🏗️ In Progress | High |
| Remote `.map` catalogue fetching | 🏗️ In Progress | High |
| `astropy.Table` / `astropy.TimeSeries` export | 🏗️ In Progress | Medium |
| Interactive Plotly light-curve viewer | 📅 Planned | Medium |
| Cross-matching with Gaia DR3 | 📅 Planned | Low |
| Automated variability / event classification | 📅 Planned | Medium |


### OGLE-III

| Feature | Status | Priority |
|:--------|:------:|:--------:|
| `BaseParser` / `BaseFetcher` interface defined | ✅ Completed | — |
| `.dat` parser implementation | 📅 Planned | Medium |
| Extended header metadata parsing | 📅 Planned | Medium |
| Remote fetcher | 📅 Planned | Medium |

### OGLE-IV

| Feature | Status | Priority |
|:--------|:------:|:--------:|
| `BaseParser` / `BaseFetcher` interface defined | ✅ Completed | — |
| `.dat` parser implementation | 📅 Planned | High |
| Real-time transient portal integration | 📅 Planned | High |
| Early Warning System (EWS) API support | 📅 Planned | High |

---

## Installation

Install the stable version from [PyPI](https://pypi.org/project/ogle/):

```bash
pip install ogle
```

Or, if you prefer using [uv](https://github.com/astral-sh/uv):

```bash
uv add ogle
```

### Optional dependencies

For varistar integration (strongly recommended for variable star analysis):

```bash
pip install ogle varistar
```

For interactive Plotly plots:

```bash
pip install ogle[viz]
```

---

## Documentation and Usage

Full documentation is available at [docs.jjsm.science/ogle](https://docs.jjsm.science/ogle).

---

## Development

This project is built using the latest Python standards. If you are contributing:

1. **Clone the repo**:
    ```bash
    git clone https://github.com/jj-sm/ogle.git
    cd ogle
    ```

2. **Sync the environment (using uv)**:
    ```bash
    uv sync
    ```

3. **Run the test suite**:
    ```bash
    uv run pytest
    ```

The package follows a layered architecture:

- **`ogle.shared`** — Survey-agnostic utilities (coordinates, file I/O, plotting). No knowledge of any specific OGLE version.
- **`ogle.base`** — Abstract interfaces. New survey versions implement `BaseParser` and `BaseFetcher` and inherit all shared logic automatically.
- **`ogle.ogle2`** — OGLE-II concrete implementation. The reference for future `ogle3`, `ogle4` implementations.
- **`ogle.core`** — High-level objects (`OGLE2Field`) that orchestrate parsers, catalogue data, and varistar loading.

---

## License

This project is licensed under the **GNU General Public License v3 (GPLv3)**. This ensures the software remains free and open for the scientific community. See the [LICENSE](LICENSE) file for details.

---

## Contributing

Contributions make the scientific community stronger!

1. Check out the [Contributing Guidelines](CONTRIBUTING.md).
2. Adhere to the [Code of Conduct](CODE_OF_CONDUCT.md).
3. Open a [Feature Request](https://github.com/jj-sm/ogle/issues) for new ideas.

---

## Citation

If you use **ogle** in your research or publications, please cite it using the metadata provided in the `CITATION.cff` file, or click the **"Cite this repository"** button in the GitHub sidebar.

---

*Maintained by [Juan José Sánchez Medina](mailto:pip@jjsm.science), BSc. Astronomy Student (Pontificia Universidad Católica de Chile)*