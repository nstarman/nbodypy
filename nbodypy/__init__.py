# -*- coding: utf-8 -*-
# see LICENSE.rst

# ----------------------------------------------------------------------------
#
# TITLE   : nbodypy
# AUTHOR  : Jeremy Webb
# PROJECT : nbodypy
#
# ----------------------------------------------------------------------------

"""nbodypy.

# The structure of the code is as follows:
# Read in data from a star cluster simulation (various routines are already written in load_cluster.py, and a custom read in function is easily built
# Use data from simulation to define a StarCluster class (cluster.py)
# -- Basic class consists of only id's, masses, positions and velocities of stars
# -- Class can be defined with or without some initial information (orbit, stellar evolution, unit information, binaries) if available
# -- If the necessary conversions are given, StarCluster can easily have the units and reference frame shifted
# -- Key parameters, like total mass, half-mass radius, etc are automatically calculated when class is defined or updated
# Once a StarCluster has been defined, various operations and functions are in place to manipulate the data and/or calculation key properties (operations.py, functions.py, profiles.py)
# A plotting package is also setup (plots.py) to make standard figures (position, density profile)

"""

__author__ = "Jeremy Webb"
# __copyright__ = "Copyright 2018, "
# __credits__ = [""]
# __license__ = ""
# __maintainer__ = ""
# __email__ = ""
# __status__ = "Production"


##############################################################################
# IMPORTS

# Packages may add whatever they like to this file, but
# should keep this content at the top.
# ----------------------------------------------------------------------------
from ._astropy_init import *  # noqa

# ----------------------------------------------------------------------------

from .main import *
from .observations import *
from .utils import *
from .custom import *
from .extern import *

# modules
from . import custom, extern


__all__ = []
__all__ += observations.__all__
__all__ += custom.__all__
__all__ += utils.__all__
__all__ += extern.__all__


##############################################################################
# END
