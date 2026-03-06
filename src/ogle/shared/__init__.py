"""
ogle.shared
===========
Utilities shared across all OGLE survey versions.
"""

from ogle.shared.coords import (
    ra_to_deg,
    dec_to_deg,
    convert_ra_dec,
    angular_separation_deg,
)
from ogle.shared.utils import (
    validate_dat,
    validate_map,
    find_dat_files,
    find_map_files,
    parse_ogle2_filename,
    read_whitespace,
)

__all__ = [
    # coords
    "ra_to_deg",
    "dec_to_deg",
    "convert_ra_dec",
    "angular_separation_deg",
    # utils
    "validate_dat",
    "validate_map",
    "find_dat_files",
    "find_map_files",
    "parse_ogle2_filename",
    "read_whitespace",
]