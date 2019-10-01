# MIT License
#
# Copyright (c) 2019 Wayne C. Gramlich
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import os
import setuptools  # type: ignore
from typing import TextIO


def long_description_read() -> str:
    readme_file: TextIO
    with open("README.md") as readme_file:
        long_description: str = readme_file.read()
    return long_description


environment: os._Environ[str] = os.environ
assert "BOM_VERSION" in environment, "BOM_VERSION environment variable is not set"
version: str = environment["BOM_VERSION"]
is_test: bool = version.startswith("0.0.")

# Arguments to *setup*() are in alphabetical order:
setuptools.setup(
    author="Wayne Gramlich",
    author_email="Wayne@Gramlich.Net",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    description="Bill Of Materials Manager",
    entry_points={
        "console_scripts": [
            "bom_manager=bom_manager:main",
            "bom_gui=bom_manager:gui_main",
        ],
    },
    include_package_data=True,
    install_requires=([] if is_test else [
        "bom_digikey_plugin",
        "bom_findchips_plugin",
        "bom_kicad_plugin",
        "bs4",
        "lxml",
        "pkg_resources",
        "pyside2",
        # "setuptools", # Needed to get pkg_resources
        ]),
    license="MIT",
    long_description=long_description_read(),
    long_description_content_type="text/markdown",
    name=("bom_manager_waynegramlich" if is_test else "bom_manager"),
    packages=[
        "bom_manager",
    ],
    python_requires=">=3.6",
    url="https://github.com/waynegramlich/bom_manager",
    version=version,
)
