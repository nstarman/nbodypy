# -*- coding: utf-8 -*-

"""Data Management.

Often data is packaged poorly and it can be difficult to understand how
the data should be read.
DON`T PANIC.
This module provides functions to read the contained data.

"""

__all__ = [
    "get_data_path",
    "get_path_orbits",
    "get_data_orbits",
    "get_path_deBoer2019",
    "get_data_deBoer2019",
    "get_path_Harris2010",
    "get_data_Harris2010",
]

#############################################################################
# IMPORTS

# BUILT-IN

import os


# THIRD PARTY

from astropy.table import Table
from astropy.utils.data import get_pkg_data_filename


#############################################################################
# PARAMETERS


#############################################################################
# FUNCTIONS


def get_data_path(*path):
    """Get `nbodypy` data files."""
    return get_pkg_data_filename(os.path.join(path), package="nbodypy")


# /def


# --------------------------------------------------------------------------


def get_path_orbits():
    """Get orbits.dat file."""
    return get_data_path("data", "orbits.dat")


# /def


def get_data_orbits():
    """Get orbits."""
    path = get_path_orbits()

    tbl = Table.read(path)

    return tbl


# /def


# --------------------------------------------------------------------------


def get_path_deBoer2019():
    """Get deBoer2019.dat file."""
    return get_data_path("data", "deBoer2019.dat")


# /def


def get_data_deBoer2019():
    """Get deBoer2019."""
    path = get_path_deBoer2019()

    tbl = Table.read(path)

    return tbl


# /def


# --------------------------------------------------------------------------


def get_path_Harris2010():
    """Get harris2010.dat file."""
    return get_data_path("data", "harris2010.dat")


# /def


def get_data_Harris2010():
    """Get Harris2010."""
    path = get_path_Harris2010()

    tbl = Table.read(path)

    return tbl


# /def


#############################################################################
# END
