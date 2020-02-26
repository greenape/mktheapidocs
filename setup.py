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
__email__ = "jonathan.gray@nanosheep.net"
__copyright__ = "Copyright 2018, Jonathan Gray"
__license__ = """
MIT License

Copyright (c) 2018 Jonathan Gray

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


setup(
    name="mktheapidocs",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    entry_points={
        "console_scripts": ["mktheapidocs = mktheapidocs.mkapi:cli"],
        "mkdocs.plugins": ["mktheapidocs = mktheapidocs.plugin:Plugin"],
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
    extras_require={"plugin": ["mkdocs >= 1.1"]},
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
