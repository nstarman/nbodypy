# -*- coding: utf-8 -*-

"""nbodypy setup.py."""

#############################################################################
# IMPORTS

import os
import io
import re
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup
from pkg_resources import get_distribution, DistributionNotFound


#############################################################################
# FUNCTIONS


def read(*names, **kwargs):
    """read."""
    with io.open(
        os.path.join(os.path.dirname(__file__), *names),
        encoding=kwargs.get("encoding", "utf8"),
    ) as fp:
        return fp.read()


# /def


def get_dist(pkgname):
    """Get distribution."""
    try:
        return get_distribution(pkgname)
    except DistributionNotFound:
        return None


# /def


def find_version(*file_paths):
    """Find version."""
    version_file = read(*file_paths)
    version_match = re.search(
        r"^__version__ = ['\"]([^'\"]*)['\"]", version_file, re.M
    )
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Unable to find version string.")


# /def


#############################################################################
# RUNNING

README = open('README').read()
HISTORY = open('HISTORY').read().replace('.. :changelog:', '')

VERSION = find_version(os.path.join('nbodypy/', '__init__.py'))


requirements = [
    "numpy>=1.7",
    "scipy>=0.14.0",
    "galpy",
    "numba",
    "limepy",
    "seaborn",
]

classifiers = [
    "Programming Language :: Python :: 3.6",
    "Programming Language :: Python :: 3.7",
]

setup(
    name="nbodypy",
    version=VERSION,
    author="Jeremy Webb",
    author_email="webb@astro.utoronto.ca",
    url="https://github.com/webbjj/nbodypy.git",
    description="Package to Analyze N-body Simulations of Star Clusters",
    long_description=README + "\n\n" + HISTORY,
    long_description_content_type="text/markdown",
    license="BSD",
    # Package info
    packages=["nbodypy"],
    zip_safe=True,
    install_requires=requirements,
    keywords="nbodypy",
)

#############################################################################
# END
