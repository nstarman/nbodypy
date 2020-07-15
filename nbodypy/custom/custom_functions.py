# -*- coding: utf-8 -*-

"""custom functions."""

__author__ = "Jeremy Webb"

#############################################################################
# IMPORTS

import numpy as np


#############################################################################
# CODE


def def_dc(m, x, v=None, r_min=0.0045):
    """Calculate Central Density.

    Calculates the center of density. Translated to Python from phiGRAPE.

    Parameters
    ----------
    m, x, v : array_like
        Particle parameters. v is optional.
    r_min : scalar
        For star clusters, should be 0.1 pc in N-body units.

    Returns
    -------
    xdc, vdc : ndarrays

    """
    calc_vdc = v is not None
    x_ = x.copy()
    xdc = np.zeros(3)
    vdc = np.zeros(3)
    v_ = v.copy() if calc_vdc else None
    r_lim = np.sqrt(np.max(np.sum(x ** 2, axis=1)))
    num_iter = 0

    while (r_lim > r_min) and (num_iter < 100):
        ncm, mcm, xcm, vcm = cenmas_lim(m, x_, v_, r_lim)
        if (mcm > 0) and (ncm > 100):
            x_ -= xcm
            xdc += xcm
            if calc_vdc:
                v_ -= vcm
                vdc += vcm
        else:
            break
        r_lim *= 0.8
        num_iter += 1

    if calc_vdc:
        return xdc, vdc
    else:
        return xdc


# /def


def cenmas_lim(m, x, v, r_lim):
    """Center of Mass Limit."""
    r2 = np.sum(x ** 2, axis=1)
    cond = r2 < r_lim ** 2
    ncm = np.sum(cond)
    mcm = np.sum(m[cond])
    if mcm == 0:
        return ncm, 0.0, np.zeros(3), np.zeros(3)
    xcm = np.sum(m[cond, None] * x[cond, :], axis=0) / mcm

    if v is not None:
        vcm = np.sum(m[cond, None] * v[cond, :], axis=0) / mcm
    else:
        vcm = None

    return ncm, mcm, xcm, vcm


# /def


#############################################################################
# END
