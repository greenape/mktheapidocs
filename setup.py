#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Setup configuration for `mktheapidocs`.

"""
import versioneer

try:
    from setuptools import setup, find_packages

except ImportError:
    from distutils.core import setup

__status__ = "Development"
__author__ = "Jonathan Gray"
__maintainer__ = "Jonathan Gray"
__email__ = "jonathan.gray@flowminder.org"
__copyright__ = "Copyright 2018, Jonathan Gray"
__license__ = "Copyright © Jonathan Gray"


setup(
    name="mktheapidocs",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    entry_points={
        "console_scripts": ["mktheapidocs = mktheapidocs.mkapi:cli"],
        'mkdocs.plugins': [
        'mktheapidocs = mktheapidocs.plugin:Plugin',
    ]
    },
    description="Generate markdown API documentation from Numpydoc docstrings.",
    author=__author__,
    author_email=__email__,
    url="https://github.com/greenape/mktheapidocs",
    license=__license__,
    keywords="mkdocs documentation markdown",
    packages=["mktheapidocs"],
    include_package_data=True,
    install_requires=["numpydoc", "black", "click"],
    extras_require={"plugin": ["mkdocs"]},
    platforms=["MacOS X", "Linux"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: MIT",
        "Programming Language :: Python :: 3.6",
        "Natural Language :: English",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        "Operating System :: POSIX :: Linux",
    ],
)
