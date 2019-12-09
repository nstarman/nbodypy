# -*- coding: utf-8 -*-

"""**DOCSTRING**."""

__author__ = "Jeremy Webb"

#############################################################################
# IMPORTS

import os


#############################################################################
# PARAMETERS

_ROOT = os.path.abspath(os.path.dirname(__file__))


#############################################################################
# FUNCTIONS


def get_data(path):
    """Get `nbodypy` data files."""
    return os.path.join(_ROOT, "data", path)


# /def


# --------------------------------------------------------------------------


def get_data_orbits():
    """Get orbits.dat file."""
    return get_data("orbits.dat")


# /def


# --------------------------------------------------------------------------


def get_data_deBoer2019():
    """Get deBoer2019.dat file."""
    return get_data("deBoer2019.dat")


# /def


# --------------------------------------------------------------------------


def get_data_Harris2010():
    """Get harris2010.dat file."""
    return get_data("harris2010.dat")


# /def


#############################################################################
# END
