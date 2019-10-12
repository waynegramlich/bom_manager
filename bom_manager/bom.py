# BOM Manager
#
# BOM Manager is a program for managing one or more Bill of Materials.
#
# ## License
#
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
#
# <------------------------------------------- 100 characters -----------------------------------> #
#
# ## Coding standards:
#
# * General:
#   * Python 3.6 or greater is used.
#   * The PEP 8 coding standards are generally adhered to.
#   * All code and docmenation lines must be on lines of 100 characters or less.  No exceptions.
#     The comment labeled "100 characters" above is 100 characters long for editor width resizing
#     purposes.
#   * Indentation levels are multiples of 4 spaces.
#   * Use `flake8 --max-line-length=100 PROGRAM.py` to check for issues.
# * Class/Function standards:
#   * Classes:
#     * Classes are named in CamelCase as per Python recommendation.
#     * Classes are listed alphabetically with sub-classes are listed alphabetically
#       immediately after their base class definition.
#   * Methods:
#     * All methods are in lower case.  If mutliple words, the words are separated by underscores.
#       The words are order as Adjectives, Noun, Adverbs, Verb.  Thus, *xml_file_load* instead of
#       *load_xml_file*.
#     * All methods are listed alphabetically, where an underscore is treated as a space.
#     * All methods check their argument types (i.e. no duck typing!!!)
#     * Inside a method, *self* is almost always replaced with more descriptive variable name.
#     * To aid debugging, many functions have an optional *tracing* argument of the form
#       `tracing=""`.  If the @trace(LEVEL) decorator preceeds the function/method, the current
#        indentation string is assigned to *tracing*.
#   * Functions:
#     * The top-level main() function occurs first.
#     * Top-level fuctions use the same coding standards as methods (see above.)
#   * Variables:
#     * Variables are lower case with underscores between words.
#     * No single letter variables except for standard mathematical concepts such as X, Y, Z.
#       Use `index` instead of `i`.
# * Comments:
#   * All code comments are written in [Markdown](https://en.wikipedia.org/wiki/Markdown).
#   * Code is organized into blocks are preceeded by comment that explains the code block.
#   * For classes, a comment of the form # CLASS_NAME: is before each class definition as an
#     aid for editor searching.
#   * For methods, a comment of the form `# CLASS_NAME.METHOD_NAME():` is before each method
#     definition as an aid for editor searching.
#   * Print statements that were used for debugging are left commented out rather than deleted.
# * Misc:
#   * The relatively new formatted string style `f"..."` is heavily used.
#   * Generally, single character strings are in single quotes (`'`) and multi characters in double
#     quotes (`"`).  Empty strings are represented as `""`.  Strings with multiple double quotes
#     can be enclosed in single quotes (e.g. `  f'<Tag foo="{foo}" bar="{bar}"/>'  `.)
#
# ## Install Notes:
#
# ## Tasks:
#
# The following tasks are outstanding:
#
# * Decode Digi-Key parametric search URL's.
# * Refactor the code to separate the GUI from the bom engine.
# * Start providing ordering operations.
# * Reorder tables/parameters/enumerations/searches.
# * Footprint hooks
# * Better parametric search
#
# ## Software Overview:
#
# This program is called *bom_manager* (i.e. Bill of Materials Manager.)
# The program fundamentally deals with the task of binding parts in a
# schematic with actual parts that can be ordered from one or more
# vendors (i.e. distributors, sellers, etc.)  It also deals with binding
# the schematic parts with footprints that can be used with the final PCB
# (i.e. Printed Circuit Project.)
#
# In short we have:
#
#    Schematic Part => Manufacturer Part
#
# and
#
#    Manufacturer Part => (Footprint, Vendor Part)
#
# and
#
#    Vendor Part => Pricing
#
# The footprints are passed into the printed circuit design workflow
# and the vendor parts are collected together into one or more orders
# that are sent off to various vendors (i.e. distributors) to be fulfilled.
# The decision of which vendor to order a part from depends upon parts
# availability and pricing.  The availability and pricing information
# is obtained via a process of visiting various web sites and "screen
# scraping" the needed information from the associated web pages.
#
# ## Schematic Parts
#
# KiCad really only deals with schematic parts in the schematic drawing
# program *and* footprints in the PCB layout program.  While in theory
# the binding between a schematic part and PCB footprint is one-to-one
# in practice KiCad keeps the two pretty decoupled.  There is a "program"
# in KiCad called "CvPcb" that is responsible for binding schematic parts
# to PCB footprints.  In general, it is very easy to make mistakes with
# CvPcb and generate incorrect PCB's where the actual parts do not fit
# properly onto the PCB's.  It would be very nice to make this process
# less error prone.
#
# Numerous people have come up with a strategy of explicitly binding
# the schematic part to (footprint, manufacturer part, vendor_part)
# into the schematic part library.  The KiCad fields was explicitly
# added to support these kinds of experiments.  The problem with
# KiCad fields is that they are currently quite brittle.  If you make
# a mistake in the schematic part library (which happens all the time),
# it is necessary to first correct the erroneous fields in the schematic
# part library *and* manually find and update each associated schematic
# part in the schematic.  This strategy is currently extremely error
# prone.
#
# `bom_manager` uses a different strategy.  In KiCad, each schematic
# part in the schematic has a reference name (e.g. R123, U7, etc.)
# and name (e.g. 74HC08, etc.)  The name can be pretty much anything
# that the end user decides provides enough information to identify
# the desired part.  What `bom_manager` does is structure this name
# as follows:
#
#        name;footprint:comment
#
# where:
#
# * *name* specifies the part name,
#
# * *footprint* specifies the footprint to associate with the name, and
#
# * *comment* is an optional comment field that is ignored by `bom_manager`
#
# For example the Atmel ATmega328 comes in several different IC packages --
# DIP28, QFP32, and QFN32.  The `bom_manager` program wants
# to see these symbols show up in the schematic as `ATMEGA328;DIP28`,
# `ATMEGA328;QFP32`, and `ATMEGA328;QFN32`.  There is a textual database
# that maps these `bom_manager` names into the actual manufacturer part
# numbers of `ATmega328P-PU`, `ATmega328P-AU`, and `ATmega328-MU`.
# In addition, this database provides a binding to the correct KiCad
# footprint.  If there is an error in the database, the database can
# be corrected, and the next time `bom_manager` is run, both the
# vendor orders and the footprints will be automatically propagated.
#
# As another example, most people use fairly common resistor values
# in their electrical designs -- 10K, 22K, 33K, 47K, etc.  These are
# considered to be generic parts (sometimes called common parts) and
# designer is happy as long as the resistors have 5% tolerance and
# can dissipate up to 1/8 Watt.  Having said that, there are numerous
# footprints to choose from.  Using inches, the common sizes
# are .008"x.005", .006"x.003", .004"x.002", and .002"x.001".
# These are abbreviated as 0805, 0603, 0402, and 0201.  `bom_manager`
# uses the metric equivalent values of 2013, 1608, 1005, and 0503.
# Thus, a 5% 1/8W 10K resistor in a .006"x.003" package would be
# listed as "10K;1608".  Again, the database is responsible for specifying
# a list of acceptable manufacturer parts that have the same .16mm x.08mm
# footprint.  `bom_manager` is responsible for selecting the specific
# manufacturer part based on availability and price.
#
# Once the designer (i.e. you) have used schematic part names that
# adhere to the `bom_manager` format, the footprint and vendor
# selection is totally automated.
#
# ## Screen Scraping
#
# In the context of `bom_manager` "screen scraping" is the process
# of fetching a web page and obtaining information from the web page
# to be feed into the ordering and footprint process.  In Python,
# screen scraping is typically done using the `BeautifulSoup` library
# which can parse and search HTML.  In general, every distributor
# provides a web interface for searching the parts that they can
# supply.  In addition, there are some electronic part aggregation
# sites (e.g. Octopart, FindChips, SnapEDA, etc.) that serve up
# useful information from their web servers.
#
# In general, the distribution and aggregation outfits are not
# thrilled with screen scrapers.  Here are some reasons why:
#
# * The web vendors are constantly tweaking their HTML.  This causes
#   screen scrapers to break on a regular basis.  They feel no
#   particular obligation to support screen scrapers.
#
# * Distributors do not want it to be easy for their competitors
#   to match prices.
#
# * Aggregators have a business model where they want to sell
#   premium access to their databases.  Screen scraping makes
#   easier for other aggregators to set up shop.
#
# There are a number of ethical issues here.  It costs real money
# to hire people to set up a good distributor web server.
# In general, distributors recoup the web server development
# expense when people purchase the parts from distributor.
# Again, it costs real money to hire people and acquire data feeds
# to set up aggregation web servers.  Charging users for access
# is a reasonable business model for aggregations sites.
#
# The position of the `bom_manager` is that free market economics
# is the way to go.  If the distributors/aggregators provide a
# viable alternative to screen scrapers at a price that is acceptable
# to the designers, the alternatives will be used; if not, screen
# scrapers will continue to be developed and supported by the free
# software community.

# Import some libraries (alphabetical order):

from argparse import ArgumentParser
# from bs4 import BeautifulSoup     # HTML/XML data structucure searching
# import bs4
# import copy                       # Used for the old pickle code...
import csv
# from currency_converter import CurrencyConverter         # Currency converter
# import fnmatch                    # File Name Matching
import glob                         # Unix/Linux style command line file name pattern matching
# import io                           # I/O stuff
import lxml.etree as etree  # type: ignore
# import pickle                     # Python data structure pickle/unpickle
import pkg_resources                # Used to find plug-ins.
# import pkgutil
from bom_manager.tracing import trace, trace_level_get, trace_level_set
import os
import re                           # Regular expressions
# import requests                   # HTML Requests
# import sexpdata                   # (LISP) S_EXpresson Data
# from sexpdata import Symbol       # (LISP) S-EXpression Symbol
# import subprocess
import sys
import time                         # Time package
from typing import Any, Callable, Dict, IO, List, Optional, Tuple, Union
Number = Union[int, float]
PreCompiled = Any
Quad = Tuple[int, float, int, str]
Quint = Tuple[float, int, int, int, int, int]
# *Quint* is misnamed, it currently has 6 fields:
# * Total Cost (float):
# * Order Quantity (int):
# * Actual Part Index (int):
# * Vendor Part Index (int):
# * Price Break Index (int):
# * Price Breaks Size (int):
# import xmlschema

# Data Structure and Algorithm Overview:
#
# There are a plethora of interlocking data structures.  The top level
# concepts are listed below:
#
# *Order*: An order corresponds to parts order.  The parts order may
# be split between multiple *Vendor*'s.
#
# *Vendor*: A vendor corresponds to a distributor such as DigiKey, Mouser,
# Newark, etc.
#
# *Project*: A project corresponds to a single PCB (e.g. a .kicad_pcb file.)
# A single order may order specify multiple PCB's and different quantities
# for each PCB.
#
# *Manufacturer*: A manufacturer is the company that owns the factory that
# creates an electronic part (e.g. MicroChip, Atmel, Texas Instruments, etc.)
# (Note: The *Manufacturer* class has not been defined in this code yet.)
#
# *Database*: The *Database* is responsible for maintaining the bindings
# between various symbols, manufacturer parts, vendor part numbers, etc.
#
# Footprint: A footprint is a description of the footprint to use
# with the part.  There is a concept of a short footprint which
# can be used to disambiguate between different packages of the
# same basic part (e.g. QFP32 vs. DIP28) and a fully specified
# KiCad footprint.
#
# Part: The concept of a part is a bit more fluid.  The manufacturer
# has its parts, the vendor (i.e. distributor) has its parts, and
# the schematic has it parts.
#
# There is a fairly complex set of data structures that link the above
# data structures together.  They are listed below:
#
# *PosePart*: A *PosePart* is essentially one-to-one with a Schematic
# symbol in KiCad.  In particular, it specifies both the annotation
# reference (e.g. SW12, U7, R213, etc.) and a *Schematic_Symbol_Name*
# (e.g. ATMEGA328-PU;QFP32, 74HC08;SOIC14, etc.)
#
# *Schematic_Symbol_Name*: A *Schematic_Symbol_Name" is string that
# has the following structure "Name;Footprint:Comment", where "Name"
# is a logical part name (e.g. ATmega328, 74HC08, 10K, .1uF, etc.),
# "footprint" is a short footprint name (QFP32, SOIC14, 1608, etc.),
# and ":Comment" is a optional comment like ":DNI" (Do Not Install, ...)
# (Note: The *Schematic_Symbol_Name* has not yet been defined as a
# Python class.)
#
# *ProjectPart*: A schematic part is one-to-one with a
# *Schematic_Symbol_Name* (excluding the comment field.)  A *ProjectPart*
# essentially provides a mapping from a *Schematic_Symbol_Name" to a list of
# acceptable manufacturer parts, which in turn provides a mapping to
# acceptable vendor parts.  There are three sub-classes of *ProjectPart* --
# *ChoicePart*, *AliasPart*, and *FractionalPart*.  As the algorithm
# proceeds, all *AliasPart*'s and *FractionalPart*'s are converted into
# associated *ChoicePart*'s.  Thus, *ChoicePart* is the most important
# sub-class of *ProjectPart*.
#
# *ChoicePart*: A *ChoicePart* is sub-classed from *ProjectPart*
# and lists one or more acceptable *ActualPart*'s. (An actual part
# is one-to-one with a manufacturer part -- see below.)  A *ChoicePart*
# also specifies a full KiCad Footprint.
#
# *AliasPart*: An *AliasPart* is also sub-classed from *ProjectPart*
# and specifies one or more *ProjectParts* to substitute.
#
# *FractionalPart*: A *FractionalPart* is also sub-classed from
# *ProjectPart* and corresponds to a 1xN or 2xN break away header.
# It is common special case that specifies a smaller number of pins
# than the full length header.
#
# *ActualPart*: An *ActualPart* should probably have been defined
# as a *Manufacturer_Part*.  An *ActualPart* consists of a *Manufacturer*
# (e.g "Atmel"), and Manufacturer part name (e.g. "ATMEGA328-PU".)
#
# *VendorPart*: A *VendorPart* should have probably been defined
# as a *Distributor_Part*.  A *Vendor* part consists of a *Vendor*
# (e.g. "Mouser") and a *VendorPart_Name* (e.g. "123-ATMEGA328-PU").
#
# Notice that there are 6 different part classes:  *ProjectPart*,
# *ChoicePart*, *AliasPart*, *FractionalPart*, *ActualPart* and
# *VendorPart*.  Having this many different part classes is needed
# to precisely keep track of everything.
#
# There are a few more classes to worry about:
#
# *Order*: An *Order* specifies a list of *Project*'s and a quantity
# for each *Project*.  Also, an order can specify a list of vendors
# to exclude from the order.
#
# *Project*: A *Project* is one-to-one with KiCad PCB.  It is basicaly
# consists of a list of *PosePart*'s.
#
# *PosePart*: A *PosePart* is basically a *Schematic_Symbol_Name*
# along with a project annotation reference (e.g. R123, U7, etc.)
#

# **:
#
#
# There are three sub_classes of *ProjectPart*:
#
# * ChoicePart*: A list of possible *ActualPart*'s to choose from.
#
# * AliasPart*: An alias specifies one or more schematic parts to
#   redirect to.
#
# * FractionalPart*: A fractional part is an alias to another schematic
#   part that specifes a fraction of the part.  A fractional part is
#   usually a 1x40 or 2x40 break-away male header.  They are so common
#   they must be supported.
#
# Now the algorithm iterates through each *ProjectPart* to convert
# each *FractionalPart* and *AliasPart* into *ChoicePart*.
# Errors are flagged.
#
# The *Database* maintains a list of *Vendor*'s and *VendorParts*.
#
# For each *ChoicePart*, the *ActualPart* list is iterated over.
# (Warning: the code has evolved somewhat here...)
# Octopart is queried to find build up a *VendorPart* list.  The
# queries are cached to avoid making excessive queries to Octopart.
# Only *ActualPart*'s that are not in the cache get sent off to
# Octopart to fill the cache.  A log of Octopart quries is kept to
# get an idea of how often the database is queried.  It may be the
# case that there is a flag that disables queries until the user
# explicitly asks for it.
#
# Now that there is a list of *VendorPart*'s for each *ActualPart*,
# the lowest cost *VendorPart* is selected based on the number of
# *ActualPart*'s needed.  The code identifies the cheapest *VendorPart*
# and it may adjust the quantity ordered up to get the benefit of a
# price break.  This is where vendor exclusion occurs.  Errors are
# generated if there are no *VendorPart* left due to exclusion or
# unavailable stock.
#
# Now various reports are generated based on sorting by vendor,
# sorting by cost, etc.  The final BOM's for each project is generated
# as a .csv file.

# main():
@trace(1)
def main(tracing: str = "") -> int:
    # Run the *Encode* class unit tests:
    Encode.test()

    collections_directories: List[str]
    searches_root: str
    order: Order
    collections_directories, searches_root, order = command_line_arguments_process()

    gui: Gui = Gui()

    partial_load: bool = True
    collections: Collections = Collections("Collections", collections_directories,
                                           searches_root, partial_load, gui)

    order.process(collections)

    return 0


@trace(1)
def command_line_arguments_process(tracing: str = "") -> Tuple[List[str], str, "Order"]:
    # Set up command line *parser* and parse it into *parsed_arguments* dict:
    parser: ArgumentParser = ArgumentParser(description="Bill of Materials (BOM) Manager.")
    parser.add_argument("-b", "--bom", action="append", default=[],
                        help="Bom file (.csv, .net). Preceed with 'NUMBER:' to increase count. ")
    parser.add_argument("-s", "--search", default="searches",
                        help="BOM Manager Searches Directory.")
    parser.add_argument("-o", "--order", default=os.path.join(os.getcwd(), "order"),
                        help="Order Information Directory")
    parser.add_argument("-v", "--verbose", action="count",
                        help="Set tracing level (defaults to 0 which is off).")

    # Now parse the command line arguments:
    parsed_arguments: Dict[str, Any] = vars(parser.parse_args())

    trace_level: int = 0 if parsed_arguments["verbose"] is None else parsed_arguments["verbose"]
    trace_level_set(trace_level)

    # Fill in the *pandas* list with *Panda* objects for doing pricing and availabity checking:
    pandas: List[Panda] = list()
    entry_point_key: str = "bom_manager_panda_get"
    index: int
    entry_point: pkg_resources.EntryPoint
    for index, entry_point in enumerate(pkg_resources.iter_entry_points(entry_point_key)):
        entry_point_name: str = entry_point.name
        if tracing:
            print(f"{tracing}Panda_Entry_Point[{index}]: '{entry_point_name}'")
        assert entry_point_name == "panda_get"
        panda_get: Callable = entry_point.load()
        assert callable(panda_get)
        panda: Panda = panda_get()
        pandas.append(panda)

    # Fill in the *cads* list with *CAD* objects for reading in :
    cads: List[Cad] = list()
    entry_point_key = "bom_manager_cad_get"
    for index, entry_point in enumerate(pkg_resources.iter_entry_points(entry_point_key)):
        entry_point_name = entry_point.name
        if tracing:
            print(f"{tracing}Cad_Entry_Point[{index}]: '{entry_point_name}'")
        assert entry_point_name == "cad_get"
        cad_get: Callable = entry_point.load()
        assert callable(cad_get)
        cad: Cad = cad_get()
        cads.append(cad)

    # Now create the *order* object.  It is created here because we need *order*
    # for dealing with *bom_file_names* immediately below:
    order_root: str = parsed_arguments["order"]
    order: Order = Order(order_root, cads, pandas)
    if tracing:
        print(f"{tracing}order_created")

    # Deal with *bom_file_names* from *parsed_arguments*:
    bom_file_names: List[str] = parsed_arguments["bom"]
    bom_file_name: str
    for bom_file_name in bom_file_names:
        if bom_file_name.endswith(".net") or bom_file_name.endswith(".csv"):
            # We have a `.net` file name:
            colon_index: int = bom_file_name.find(':')
            # print(f"colon_index={colon_index}")
            count: int = 1
            if colon_index >= 0:
                count = int(bom_file_name[:colon_index])
                bom_file_name = bom_file_name[colon_index:]
            # print(f"count={count}")
            assert os.path.isfile(bom_file_name), f"'{bom_file_name}' does not exist."
            path: str
            base_name: str
            path, base_name = os.path.split(bom_file_name)
            name: str = base_name[:-4]
            revision_letter: str = 'A'
            if len(path) >= 2:
                revision_letter = path[-1].upper()
            if tracing:
                print(f"path={path}")
                print(f"base_name='{base_name}'")
                print(f"name='{name}'")
                print(f"revision_letter='{revision_letter}'")

            # Create an order project:
            order.project_create(name, revision_letter, bom_file_name, count, tracing=tracing)
        else:
            print(f"Ignoring file '{bom_file_name}' does not with '.net' or '.csv' suffix.")
    if tracing:
        print(f"{tracing}nets processed")

    collection_directories: List[str] = list()

    searches_root: str = os.path.abspath(parsed_arguments["search"])
    return collection_directories, searches_root, order


# # "se" stands for "S Expression":
# def se_find(se, base_name, key_name):
#     """ {}: Find *key_name* in *se* and return its value. """
#
#     # *se* is a list of the form:
#     #
#     #        [base_name, [key1, value1], [key2, value2], ..., [keyN, valueN]]
#     #
#     # This routine searches through the *[keyI, valueI]* pairs
#     # and returnts the *valueI* that corresponds to *key_name*.
#
#     # Check argument types:
#     # assert isinstance(se, list)
#     # assert isinstance(base_name, str)
#     # assert isinstance(key_name, str)
#
#     # Do some sanity checking:
#     # size = len(se)
#     # assert size > 0
#     # assert se[0] == Symbol(base_name)
#
#     result = None
#     # key_symbol = Symbol(key_name)
#     # for index in range(1, size):
#     #     sub_se = se[index]
#     #     if len(sub_se) > 0 and sub_se[0] == key_symbol:
#     #         result = sub_se
#     #         break
#     return result


# def text2safe_attribute(text):
#     # Sweep across *text* one *character* at a time performing any neccesary conversions:
#     new_characters = list()
#     for character in text:
#         new_character = character
#         if character == '&':
#             new_character = "&amp;"
#         elif character == '<':
#             new_character = "&lt;"
#         elif character == '>':
#             new_character = "&gt;"
#         elif character == "'":
#             new_character = "&apos;"
#         elif character == '"':
#             new_character = "&quot;"
#         new_characters.append(new_character)
#     safe_attribute = "".join(new_characters)
#     return safe_attribute


# text_filter():
def text_filter(text: str, function: Callable) -> str:
    return "".join([character for character in text if function(character)])


# ActualPart:
class ActualPart:
    # An *ActualPart* represents a single manufacturer part.
    # A list of vendor parts specifies where the part can be ordered from.

    ACTUAL_PART_EXCHANGE_RATES: Dict[str, float] = dict()

    # ActualPart.__init__():
    def __init__(self, manufacturer_name: str, manufacturer_part_name: str) -> None:
        """ *ActualPart*: Initialize *self* to contain *manufacturer* and
            *manufacturer_part_name*. """
        # Create the *key* for *actual_part* (i.e. *self*):
        # actual_part: ActualPart = self
        key: Tuple[str, str] = (manufacturer_name, manufacturer_part_name)

        # Load up *actual_part* (i.e. *self*):
        # actual_part: Actual_Part = self
        self.manufacturer_name: str = manufacturer_name
        self.manufacturer_part_name: str = manufacturer_part_name
        self.key: Tuple[str, str] = key
        # Fields used by algorithm:
        self.quantity_needed: int = 0
        self.vendor_parts: List[VendorPart] = []
        self.selected_vendor_part: Optional[VendorPart] = None

    # ActualPart.__eq__():
    def __eq__(self, actual_part2: object, tracing: str = "") -> bool:
        equal: bool = False
        if isinstance(actual_part2, ActualPart):
            actual_part1: ActualPart = self
            equal = actual_part1.key == actual_part2.key
            if equal:
                # Extract *vendor_parts* making sure that they are sorted:
                vendor_parts1: List[VendorPart] = actual_part1.sorted_vendor_parts_get()
                vendor_parts2: List[VendorPart] = actual_part2.sorted_vendor_parts_get()
                equal &= len(vendor_parts1) == len(vendor_parts2)
                if equal:
                    index: int
                    vendor_part1: VendorPart
                    for index, vendor_part1 in enumerate(vendor_parts1):
                        vendor_part2: VendorPart = vendor_parts2[index]
                        if vendor_part1 != vendor_part2:
                            equal = False
                            break
        return equal

    # ActualPart.__str__():
    def __str__(self) -> str:
        actual_part: ActualPart = self
        manufacturer_part_name: str = "??"
        if hasattr(actual_part, "manufacturer_part_name"):
            manufacturer_part_name = actual_part.manufacturer_part_name
        return (f"ActualPart('{manufacturer_part_name}')")

    # ActualPart.sorted_vendor_parts_get():
    def sorted_vendor_parts_get(self) -> "List[VendorPart]":
        actual_part: ActualPart = self
        vendor_parts: List[VendorPart] = actual_part.vendor_parts
        sort_function: Callable = lambda vendor_part: vendor_part.vendor_key
        vendor_parts.sort(key=sort_function)
        return vendor_parts

    # ActualPart.vendor_names_load():
    def vendor_names_load(self, vendor_names_table: Dict[str, None],
                          excluded_vendor_names: Dict[str, None]) -> None:
        """ *ActualPart*:*: Add each possible to vendor name for the
            *ActualPart* object (i.e. *self*) to *vendor_names_table*:
        """
        # Add the possible vendor names for *vendor_part* to
        # *vendor_names_table*:
        vendor_part: VendorPart
        for vendor_part in self.vendor_parts:
            vendor_name: str = vendor_part.vendor_name
            if vendor_name not in excluded_vendor_names:
                vendor_names_table[vendor_name] = None

    # ActualPart.vendor_part_append():
    def vendor_part_append(self, vendor_part: "VendorPart") -> None:
        """ *ActualPart: Append *vendor_part* to the vendor parts of *self*. """
        # Append *vendor_part* to the *actual_part* (i.e. *self*):
        actual_part: ActualPart = self
        actual_part.vendor_parts.append(vendor_part)

    # ActualPart.vendor_parts_restore():
    def vendor_parts_restore(self, order: "Order", tracing: str = "") -> bool:
        # FIXME: What does this routine actually do?:
        assert False
        result: bool = False
        return result

    # ActualPart.xml_lines_append():
    def xml_lines_append(self, xml_lines: List[str], indent: str) -> None:
        # Grab some values from *actual_part* (i.e. *self*):
        actual_part: ActualPart = self
        manufacturer_name: str = actual_part.manufacturer_name
        manufacturer_part_name: str = actual_part.manufacturer_part_name
        vendor_parts: List[VendorPart] = actual_part.vendor_parts

        # Output the `<ActualPart ...>` tag first:
        xml_lines.append(f'{indent}<ActualPart '
                         f'manufacturer_name="{Encode.to_attribute(manufacturer_name)}" '
                         f'manufacturer_part_name="{Encode.to_attribute(manufacturer_part_name)}">')

        # Output the nested `<VendorPart ...>` tags:
        next_indent: str = indent + " "
        vendor_part: VendorPart
        for vendor_part in vendor_parts:
            vendor_part.xml_lines_append(xml_lines, next_indent)

        # Close out with the `</ActualPart>` tag:
        xml_lines.append(f"{indent}</ActualPart>")

    # ActualPart.xml_parse():
    @staticmethod
    def xml_parse(actual_part_tree: etree._Element) -> "ActualPart":
        # Grab the attribute information out of *actual_part_tree*:
        assert actual_part_tree.tag == "ActualPart"
        attributes_table: Dict[str, str] = actual_part_tree.attrib
        manufacturer_name: str = attributes_table["manufacturer_name"]
        manufacturer_part_name: str = attributes_table["manufacturer_part_name"]
        vendor_part_trees: List[etree._Element] = list(actual_part_tree)

        # Create *actual_part* with empty *vendor_parts*:
        actual_part: ActualPart = ActualPart(manufacturer_name, manufacturer_part_name)
        vendor_parts: List[VendorPart] = actual_part.vendor_parts

        # Process all of the `<VendorPart ...>` tags:
        for vendor_part_tree in vendor_part_trees:
            vendor_part: VendorPart = VendorPart.xml_parse(vendor_part_tree, actual_part)
            vendor_parts.append(vendor_part)
        return actual_part


# Cad:
class Cad:
    # Cad Stands for Computer Aided Design:

    # Cad.__init__():
    def __init__(self, name: str, tracing: str = "") -> None:
        pass  # This is just a place holder class that is sub-classed against.

    # Cad.file_read():
    def file_read(self, file_name: str, project: "Project") -> bool:
        cad: Cad = self
        class_name: str = cad.__class__.__name__
        assert False, f"{class_name}.file_read() has not been implemented."
        return False


# Comment:
class Comment:

    # Comment.__init__():
    def __init__(self, language: str, lines: List[str]) -> None:
        # Load up *comment* (i.e. *self*):
        # comment: Comment = self
        self.language: str = language
        self.lines: List[str] = lines

    # Comment.__eq__():
    def __eq__(self, comment2: object) -> bool:
        # `mypy` recommends that the *__eq__* method work with any *object*.  So we start
        # with *equal* set to *False* and only set it to *True* on success:
        equal: bool = False
        if isinstance(comment2, Comment):
            comment1: Comment = self
            language_equal: bool = comment1.language == comment2.language
            lines_equal: bool = comment1.lines == comment2.lines
            equal = language_equal and lines_equal
        return equal

    # Comment.__str__():
    def __str__(self) -> str:
        # Return a simple string since there is no need to expose the contents of the comment
        # (i.e. *self*):
        comment: Comment = self
        language: str = "??"
        if hasattr(comment, "language"):
            language = comment.language
        class_name: str = comment.__class__.__name__
        return f"{class_name}('{language}')"

    # Comment.xml_lines_append():
    def xml_lines_append(self, xml_lines: List[str], indent: str) -> None:
        # Grab some values from *comment* (i.e. *self*):
        comment: Comment = self
        class_name: str = comment.__class__.__name__
        language: str = comment.language
        lines: List[str] = comment.lines

        # Output the initial element XML tag (i.e. *class_name*):
        xml_lines.append(f'{indent}<{class_name} language="{language}">')

        # Output the comment *lines*:
        line: str
        for line in lines:
            xml_lines.append(f"{indent}  {line}")

        # Output the closing element XML tag:
        xml_lines.append('f{indent}</{class_name}>")')

    # Comment.xml_parse_helper():
    @staticmethod
    def xml_parse_helper(comment_tree: etree._Element) -> Tuple[Dict[str, str], str, List[str]]:
        # Grab some values from *comment_tree*:
        attributes_table: Dict[str, str] = comment_tree.attrib
        assert "language" in attributes_table
        language: str = attributes_table["language"]

        # Grab the *text* from *comment_tree*, split it into *lines*, clean up each line:
        text: str = comment_tree.text.strip()
        lines: List[str] = text.split('\n')
        for index, line in enumerate(lines):
            lines[index] = line.strip().replace("<", "&lt;").replace(">", "&gt;")

        # Return everything:
        return attributes_table, language, lines


# EnumerationComment:
class EnumerationComment(Comment):

    # EnumerationComment.__init__():
    def __init__(self, language: str, lines: List[str]) -> None:
        # An *EnumerationComment* is just pure sub-class of *Comment*:
        super().__init__(language, lines)

    # EnumerationComment.xml_parse():
    @staticmethod
    def xml_parse(comment_tree: etree._Element) -> "EnumerationComment":
        # Grab some values from *comment_tree*):
        attributes_table: Dict[str, str]
        langauge: str
        lines: List[str]
        attributes_table, language, lines = Comment.xml_parse_helper(comment_tree)

        # Construct and return the final *enumeration_comment*:
        enumeration_comment: EnumerationComment = EnumerationComment(language, lines)
        return enumeration_comment


# ParameterComment:
class ParameterComment(Comment):

    # ParameterComment.__init__():
    def __init__(self, language: str, lines: List[str],
                 long_heading: str, short_heading: str) -> None:

        # Initialize the parent *Comment* class with *language* and *lines*:
        super().__init__(language, lines)

        # Initialize the remaining fields of *parameter_comment*:
        # parameter_comment: ParameterComment = self
        self.long_heading: str = long_heading
        self.short_heading: str = short_heading

    # ParameterComment.__eq__():
    def __eq__(self, parameter_comment2: object) -> bool:
        # `mypy` recommends that the *__eq__* method work with any *object*.  So we start
        # with *equal* set to *False* and only set it to *True* on success:
        equal: bool = False
        if isinstance(parameter_comment2, ParameterComment):
            parameter_comment1: ParameterComment = self
            language_equal: bool = parameter_comment1.language == parameter_comment2.language
            lines_equal: bool = parameter_comment1.lines == parameter_comment2.lines
            long_equal: bool = parameter_comment1.long_heading == parameter_comment2.long_heading
            short_equal: bool = parameter_comment1.short_heading == parameter_comment2.short_heading
            equal = language_equal and lines_equal and long_equal and short_equal
        return equal

    # ParameterComment.xml_lines_append():
    def xml_lines_append(self, xml_lines: List[str], indent: str) -> None:
        # Grab some values from *parameter_comment* (i.e. *self*):
        parameter_comment: ParameterComment = self
        language: str = parameter_comment.language
        lines: List[str] = parameter_comment.lines
        long_heading: str = parameter_comment.long_heading
        short_heading: str = parameter_comment.short_heading

        # Append an XML `<ParameterComment ...>` element to *xml_lines*.
        short_heading_text = f" shortHeading={short_heading}" if short_heading else ""
        xml_line: str = (f'{indent}<ParameterComment'
                         f' language="{language}"'
                         f' longHeading="{long_heading}"'
                         f'{short_heading_text}>')

        # Append *lines* to *xml_lines* indented by *indent* and tack on the closing
        # `</ParameterComment>` XML element:
        xml_lines.append(xml_line)
        line: str
        for line in lines:
            xml_lines.append(f'{indent} {line}')
        xml_lines.append(f'{indent}</ParameterComment>')

    # ParameterComment.xml_parse():
    @staticmethod
    def xml_parse(comment_tree: etree._Element) -> "ParameterComment":
        # Grab some values from *comment_tree*:
        attributes_table: Dict[str, str]
        language: str
        lines: List[str]
        attributes_table, language, lines = Comment.xml_parse_helper(comment_tree)

        # Grab some values from *attributes_table:
        assert "longHeading" in attributes_table
        long_heading: str = attributes_table["longHeading"]
        short_heading: str = (attributes_table["shortHeading"]
                              if "shortHeading" in attributes_table else "")

        # Construct the final *parameter_comment* and return it:
        parameter_comment: ParameterComment = ParameterComment(language, lines,
                                                               long_heading, short_heading)
        return parameter_comment


# SearchComment:
class SearchComment(Comment):
    # SearchComment.__init()
    def __init__(self, language: str, lines: List[str]) -> None:
        # A *SearchComment* is a pure sub-class of the parent *Comment* class:
        super().__init__(language, lines)

    # SearchComment.xml_parse()
    @staticmethod
    def xml_parse(comment_tree: etree._Element) -> "SearchComment":
        # Grab some values out of *comment_tree*:
        attributes_table: Dict[str, str]
        language: str
        lines: List[str]
        attributes_table, language, lines = Comment.xml_parse_helper(comment_tree)

        # Construct and return the final *search_comment*:
        search_comment: SearchComment = SearchComment(language, lines)
        return search_comment


# TableComment:
class TableComment(Comment):

    # TableComment.__init__():
    def __init__(self, language: str, lines: List[str]) -> None:
        # *TableComment* is just a pure sub-class of the parent *Comment* class:
        super().__init__(language, lines)

    # TableComment.xml_parse():
    @staticmethod
    def xml_parse(comment_tree: etree._Element) -> "TableComment":
        # Grab some values out of *comment_tree*:
        attributes_table: Dict[str, str]
        language: str
        lines: List[str]
        attributes_table, language, lines = Comment.xml_parse_helper(comment_tree)

        # Construct and return the final *table_comment*:
        table_comment: TableComment = TableComment(language, lines)
        return table_comment


# Encode:
class Encode:

    # Encode.from_attribute():
    @staticmethod
    def from_attribute(attribute: str) -> str:
        characters: List[str] = list()
        attribute_size: int = len(attribute)
        index: int = 0
        while index < attribute_size:
            # Grab the *character* and compute the *next_index:
            character: str = attribute[index]
            next_index: int = index + 1

            # Determine if we have an HTML entity:
            if character == '&':
                # We do have an HTML entity; find the closing ';':
                # rest = attribute[index:]
                # print(f"rest='{rest}'")
                entity: str = ""
                for entity_index in range(index, attribute_size):
                    entity_character = attribute[entity_index]
                    # print(f"Attribute[{entity_index}]='{entity_character}'")
                    if entity_character == ';':
                        next_index = entity_index + 1
                        entity = attribute[index:next_index]
                        break
                else:
                    assert False, "No closing ';' for entity"
                # print(f"entity='{entity}'")

                # Parse the expected entities:
                assert len(entity) >= 2, f"Empty HTML entity '{entity}'"
                if entity[1] == '#':
                    # Numeric entity of the form `&#d...d;`, try to parse the decimal digits:
                    try:
                        character = chr(int(entity[2:-1]))
                    except ValueError:
                        assert False, f"Entity '{entity}' is broken."
                elif entity == "&amp;":
                    character = '&'
                elif entity == "&lt;":
                    character = '<'
                elif entity == "&gt;":
                    character = '>'
                elif entity == "&apos;":
                    character = "'"
                elif entity == "&quot;":
                    character = '"'
                else:
                    assert False, f"Unrecognized HTML entity '{entity}'"
            else:
                # *character* is not the start of an HTML entity.  Leave it alone:
                pass

            # Tack *character* onto *characters* and advance to *next_index*:
            characters.append(character)
            index = next_index

        # Concatenate *characters* into final *text* and return it:
        text: str = "".join(characters)
        return text

    # Encode.from_file_name():
    @staticmethod
    def from_file_name(file_name: str) -> str:
        # Construct a list of *characters* one at a time to join together into final *text*:
        characters: List[str] = list()
        index: int = 0
        file_name_size: int = len(file_name)
        while index < file_name_size:
            # Dispatch on *character* and compute *next_index*:
            character: str = file_name[index]
            next_index: int = index + 1

            # Dispatch on *character*:
            if character == '_':
                # Underscores are always translated to spaces:
                character = ' '
            elif character == '%':
                # We should have either "%XX" or "%%XXXX, where "X" is a hexadecimal digit.

                # First, ensure that there is a *next_character* following the initial '%':
                if next_index < file_name_size:
                    next_character = file_name[next_index]

                    # Dispatch on *next_character* to figure out whether we have a 2 or 4
                    # digit number:
                    if next_character == '%':
                        # We have "%%XXXX"" to parse:
                        hex_index: int = index + 2
                        next_index = index + 6
                    else:
                        # We have "%XX" to parse into a single *character*:
                        hex_index = index + 1
                        next_index = index + 3

                    # Extract the *hex_text* from *file_name* to parse:
                    assert next_index <= file_name_size, "'%' at end of string is wrong"
                    hex_text: str = file_name[hex_index:next_index]

                    # Now attempt top arse *hex_text* into *character*:
                    try:
                        character = chr(int(hex_text, 16))
                        # print(f"'{hex_text}'=>'{character}'")
                    except ValueError:
                        assert False, f"'{hex_text}' is invalid from '{file_name}'"
                else:
                    # No character after '%":
                    assert False, "'%' at end of string"
            else:
                # Everything else just taken as is:
                pass

            # Tack *character* (which now may be multiple characters) onto *characters*
            # and advance *index* to *next_index*:
            characters.append(character)
            assert next_index > index
            index = next_index

        # Join *characters* back into a single *text* string:
        text: str = "".join(characters)
        return text

    # Encode.to_attribute():
    @staticmethod
    def to_attribute(text: str) -> str:
        assert isinstance(text, str)
        characters: List[str] = list()
        ord_space: int = ord(' ')
        ord_tilde: int = ord('~')
        character: str
        for character in text:
            ord_character: int = ord(character)
            if ord_space <= ord_character <= ord_tilde:
                # *character* is ASCII printable; now convert some of them to HTML entity:
                if character == '&':
                    character = "&amp;"
                elif character == '<':
                    character = "&lt;"
                elif character == '>':
                    character = "&gt;"
                elif character == "'":
                    character = "&apos;"
                elif character == '"':
                    character = "&quot;"
            else:
                # Non-ASII printable, so use decimal version of HTML entity syntax:
                character = f"&#{ord_character};"
            characters.append(character)

        # Convert *characters* to an *attribute* string and return it:
        attribute: str = "".join(characters)
        return attribute

    # Encode.to_csv():
    @staticmethod
    def to_csv(text: str) -> str:
        updated_text: str = text.replace('"', '""')
        return f'"{updated_text}"'

    # Encode.to_file_name():
    @staticmethod
    def to_file_name(text: str) -> str:
        characters: List[str] = list()
        ord_space: int = ord(' ')
        ord_tilde: int = ord('~')
        ord_del: int = ord('\xff')
        character: str
        for character in text:
            # Dispatch on the integer *ord_character*:
            ord_character: int = ord(character)
            if ord_character == ord_space:
                # Convert *character* space (' ') to an underscore ('_'):
                character = '_'
            elif ord_space < ord_character <= ord_tilde:
                # *character* is in normal visible printing ASCII range, but not a space:
                # Since the Unix/Linux shell treats many of the non-alphanumeric ones
                # specially, most of them are convert to '%XX' format.  The ones that are
                # not converted are '+', ',', '.',  and ':'.  Note that '_' must be converted
                # because spaces have been converted to underscores:
                if character in "!\"#$%&'()*/;<=>?[\\]^_`{|}~":
                    character = "%{0:02x}".format(ord_character)
            elif ord_character < ord_space or ord_character == ord_del:
                # *character* is one of the ASCII control characters to convert into '%XX':
                character = "%{0:02x}".format(ord_character)
            else:
                # *character* is a larger unicode character to convert into '%%XXXX':
                character = "%%{0:04x}".format(ord_character)

            # Collect the new *character* (which might be several characters) onto *characters*:
            characters.append(character)

        # Concatenate *characters* into *file_name* and return it:
        file_name: str = "".join(characters)
        return file_name

    # Encode.to_url():
    @staticmethod
    def to_url(text: str) -> str:
        # Convert *text* into the %XX encoding system used by URL's as per RFC 3986:
        character: str
        return "".join([character if character.isalnum() or character in "-.!"
                        else "%0:02x".format(ord(character)) for character in text])

    # Encode.test():
    @staticmethod
    def test() -> None:
        printable_ascii: str = "".join([chr(index) for index in range(ord(' '), ord('~')+1)])
        Encode.test_both(printable_ascii)
        control_ascii: str = "".join([chr(index) for index in range(ord(' ')-1)]) + "\xff"
        Encode.test_both(control_ascii)
        unicode_characters: str = "\u03a9Ω\u03bcμ"
        Encode.test_both(unicode_characters)

    # Encode.test_attribute():
    @staticmethod
    def test_attribute(before_attribute: str) -> None:
        assert isinstance(before_attribute, str)
        # print(f"before_attribute='{before_attribute}'")
        attribute_text: str = Encode.to_attribute(before_attribute)
        # print(f"attribute_text='{attribute_text}'")
        after_attribute: str = Encode.from_attribute(attribute_text)
        # print(f"after_attribute='{after_attribute}'")
        Encode.test_compare(before_attribute, after_attribute)

    # Encode.test_both():
    @staticmethod
    def test_both(text: str) -> None:
        assert isinstance(text, str)
        Encode.test_attribute(text)
        Encode.test_file_name(text)

    # Encode.test_compare():
    @staticmethod
    def test_compare(text1: str, text2: str) -> None:
        if text1 != text2:
            text1_size: int = len(text1)
            text2_size: int = len(text2)
            text_size: int = min(text1_size, text2_size)
            index: int
            character: str
            for index in range(text_size):
                character1: str = text1[index]
                character2: str = text2[index]
                assert character1 == character2, (f"Mismatch at index={index}"
                                                  f" '{character1}' != '{character2}'"
                                                  f" text1='{text1}' text2='{text2}'")
            assert text1_size == text2_size

    # Encode.test_file_name():
    @staticmethod
    def test_file_name(before_text: str) -> None:
        assert isinstance(before_text, str)
        file_name_text: str = Encode.to_file_name(before_text)
        after_text: str = Encode.from_file_name(file_name_text)
        Encode.test_compare(before_text, after_text)


# Enumeration:
class Enumeration:

    # Enumeration.__init__():
    def __init__(self, name: str, comments: List[EnumerationComment]) -> None:
        # Load values into *enumeration* (i.e. *self*):
        # enumeration: Enumeration = self
        self.name: str = name
        self.comments: List[EnumerationComment] = comments

    # Enumeration.__eq__():
    def __eq__(self, enumeration2: object) -> bool:
        equal: bool = False
        if isinstance(enumeration2, Enumeration):
            enumeration1: Enumeration = self
            name_equal: bool = enumeration1.name == enumeration2.name
            comments_equal: bool = enumeration1.comments == enumeration2.comments
            equal = name_equal and comments_equal
        return equal

    # Enumeration.xml_lines_append():
    def xml_lines_append(self, xml_lines: List[str], indent: str) -> None:
        # Append an `<Enumeration>` element to *xml_lines*:
        enumeration: Enumeration = self
        name: str = enumeration.name
        name_attribute: str = Encode.to_attribute(name)
        xml_lines.append(f'{indent}<Enumeration name="{name_attribute}">')
        comment: EnumerationComment
        for comment in enumeration.comments:
            comment.xml_lines_append(xml_lines, indent + "  ")
        xml_lines.append(f'{indent}</Enumeration>')

    # Enumeration.xml_parse():
    @staticmethod
    def xml_parse(enumeration_tree: etree._Element) -> "Enumeration":
        assert enumeration_tree.tag == "Enumeration"
        attributes_table: Dict[str, str] = enumeration_tree.attrib
        assert "name" in attributes_table
        name: str = attributes_table["name"]
        comments_tree: etree._Element = list(enumeration_tree)
        comments: List[EnumerationComment] = list()
        comment_tree: etree._Element
        for comment_tree in comments_tree:
            comment: EnumerationComment = EnumerationComment.xml_parse(comment_tree)
            comments.append(comment)
        assert comments
        enumeration: Enumeration = Enumeration(name, comments)
        return enumeration


# Filter:
class Filter:

    # Filter.__init__():
    def __init__(self, table: "Table", parameter: "Parameter", use: bool, select: str) -> None:
        # Load up *filter* (i.e. *self*):
        # filter: Filter = self
        self.table: Table = table
        self.parameter: Parameter = parameter
        self.select: str = select
        self.use: bool = use

    # Filter.xml_lines_append():
    def xml_lines_append(self, xml_lines: List[str], indent: str, tracing: str = "") -> None:
        # Grab some values from *filter* (i.e. *self*):
        filter: "Filter" = self
        parameter: Parameter = filter.parameter
        use: bool = filter.use
        select: str = filter.select
        parameter_name: str = parameter.name

        # Output the initial `<Filter ...>` XML element:
        xml_lines.append(f'{indent}<Filter '
                         f'name="{parameter_name}" '
                         f'use="{use}" '
                         f'select="{select}">')

        # Append any *enumerations* from *parameter*:
        enumerations: List[Enumeration] = parameter.enumerations
        if enumerations:
            xml_lines.append(f'{indent}  <FilterEnumerations>')
            enumeration: Enumeration
            for enumeration in enumerations:
                enumeration_name: str = enumeration.name
                match: bool = False
                xml_lines.append(f'{indent}    <FilterEnumeration '
                                 f'name="{enumeration_name}" '
                                 f'match="{match}"/>')
            xml_lines.append(f'{indent}  </FilterEnumerations>')

        # Wrap up `<Filter...>` element:
        xml_lines.append(f'{indent}</Filter>')

    # Filter.xml_parse()
    @staticmethod
    def xml_parse(filter_tree: etree._Element, table: "Table") -> "Filter":
        # Grab the attributes from *filter_tree*:
        attributes_table: Dict[str, str] = filter_tree.attrib
        assert "name" in attributes_table
        parameter_name: str = attributes_table["name"]
        assert "match" in attributes_table
        match_text: str = attributes_table["match"].lower()
        assert match_text in ("true", "false")
        use = match_text == "true"

        parameters: List[Parameter] = table.parameters
        parameter: Parameter
        for parameter in parameters:
            if parameter.name == parameter_name:
                break
        else:
            assert False, f"No parameter name '{parameter_name}' not found"

        # Create the resulting *filter* and return it:
        select: str = ""
        assert False, "What is select?"
        filter: Filter = Filter(table, parameter, use, select)
        return filter


# Footprint:
class Footprint:
    """ *Footprint*: Represents a PCB footprint. """

    # Footprint.__init__():
    def __init__(self, name: str, rotation: float) -> None:
        """ *Footprint*: Initialize a new *FootPrint* object.

        The arguments are:
        * *name* (str): The unique footprint name.
        * *rotation* (degrees): The amount to rotate the footprint to match the feeder tape with
          holes on top.
        """

        # Stuff values into *footprint* (i.e. *self*):
        # footprint: Footprint = self
        self.name = name
        self.rotation = rotation


# Inventory:
class Inventory:

    # Inventory.__init__():
    def __init__(self, project_part: "ProjectPart", amount: int) -> None:
        """ *Inventory*: Initialize *self* to contain *scheamtic_part* and
            *amount*. """

        # Load up *inventory* (i.e. *self*):
        # inventory: Inventory = self
        self.project_part: ProjectPart = project_part
        self.amount: int = amount


# The *Node* class and its associated sub-classes *Collections*, *Collection*, *Directory*
# *Table*, *Search* (and eventually *Filter*) are designed to be displayed in the GUI
# (Graphical User Interface) using a *QTreeView* widget.  The graphical display is not
# required, so non-GUI code that uses this *bom_manager* module use the code as well.
# When the GUI is displayed, it uses a *QTreeView* widget in conjunction with the *TreeModel*
# class (which is a sub-class of *QAbstractItemModel*.)
#
# The tree model looks like:
#
#        Collections
#          Collection1
#            Directory1
#              SubDirectory1
#                ...
#                  Sub...SubDirectory1
#                    Table1
#                      Search1
#                      Search2
#                      ..
#                      SearchN
#                    Table2
#                    ...
#                    TableN
#                   ...
#                  Sub...SubDirectoryN
#               ...
#               SubDirectoryN
#            ...
#            DirectoryN
#          ...
#          CollectionN
#
# To summarize:
#
# * There is a top-most *Collections* object that is the root of the tree.
# * There are zero, one or more *Collection* objects under the *Collections* object.
# * There ar zero, one or more *Directory* objects under each *Collections* object.
# * Each *Directory* object can have zero, one or more sub-*Directory* objects and/or
#   zero,one or more *Table* objects.
# * Each *Table* object can have zero, one or more *Search* objects.
#
# {Talk about file system structure here:}

# Gui:
class Gui:
    """ Represents some callback interfaces to the GUI if it exists. """

    # Gui.__init__():
    def __init__(self) -> None:
        # Construct a bunch of regular expressions:
        si_units_re_text: str = Units.si_units_re_text_get()
        float_re_text: str = "-?([0-9]+\\.[0-9]*|\\.[0-9]+)"
        white_space_text: str = "[ \t]*"
        integer_re_text: str = "-?[0-9]+"
        integer_re: PreCompiled = re.compile(integer_re_text + "$")
        float_re: PreCompiled = re.compile(float_re_text + "$")
        url_re: PreCompiled = re.compile("(https?://)|(//).*$")
        empty_re: PreCompiled = re.compile("-?$")
        funits_re: PreCompiled = re.compile(float_re_text +
                                            white_space_text + si_units_re_text + "$")
        iunits_re: PreCompiled = re.compile(integer_re_text + white_space_text +
                                            si_units_re_text + "$")
        range_re: PreCompiled = re.compile("[^~]+~[^~]+$")
        list_re: PreCompiled = re.compile("([^,]+,)+[^,]+$")
        re_table: Dict[str, PreCompiled] = {
          "Empty": empty_re,
          "Float": float_re,
          "FUnits": funits_re,
          "Integer": integer_re,
          "IUnits": iunits_re,
          "List": list_re,
          "Range": range_re,
          "URL": url_re,
        }
        # gui: Gui = self
        self.re_table: Dict[str, PreCompiled] = re_table

    # Gui.__str():
    def __str__(self) -> str:
        return "GUI()"

    # Gui.begin_rows_insert():
    def begin_rows_insert(self, node: "Node",
                          start_row_index: int, end_row_index: int, tracing: str = "") -> None:
        pass  # Do nothing for the non-GUI version of th code

    # Gui.begin_rows_remove():
    def begin_rows_remove(self, node: "Node",
                          start_row_index: int, end_row_index: int, tracing: str = "") -> None:
        pass  # Do nothing for the non-GUI version of th code

    # Gui.collection_clicked():
    def collection_clicked(self, collection: "Collection", tracing: str = "") -> None:
        gui: Gui = self
        class_name: str = gui.__class__.__name__
        assert False, f"{class_name}.collection_clicked() has not been implemented yet"

    # Gui.collection_panel_update():
    @trace(1)
    def collection_panel_update(self, collection: "Collection", tracing: str = "") -> None:
        gui: Gui = self
        class_name: str = gui.__class__.__name__
        assert False, f"{class_name}.collection_panel_update() has not been implmented yet"

    # Gui.collections_clicked():
    def collections_clicked(self, collections: "Collections", tracing: str = "") -> None:
        gui: Gui = self
        class_name: str = gui.__class__.__name__
        assert False, f"{class_name}.collections_clicked() has not been implemented yet"

    # Gui.directory_clicked():
    def directory_clicked(self, directory: "Directory", tracing: str = "") -> None:
        gui: Gui = self
        class_name: str = gui.__class__.__name__
        assert False, f"{class_name}.directory_clicked() has not been implemented yet"

    # Gui.directory_panel_update():
    def directory_panel_update(self, directory: "Directory", tracing: str = "") -> None:
        gui: Gui = self
        class_name: str = gui.__class__.__name__
        assert False, f"{class_name}.directory_panel_update() has not been implemented yet"

    # Gui.end_rows_insert():
    def end_rows_insert(self, tracing: str = "") -> None:
        pass  # Do nothing for the non-GUI version of th code

    # Gui.end_rows_remove():
    def end_rows_remove(self, tracing: str = "") -> None:
        pass  # Do nothing for the non-GUI version of th code

    # Gui.search_clicked():
    def search_clicked(self, search: "Search", tracing: str = "") -> None:
        gui: Gui = self
        class_name: str = gui.__class__.__name__
        assert False, f"{class_name}.search_clicked() has not been implemented yet"

    # Gui.search_panel_update()
    def search_panel_update(self, search: "Search", tracing: str = "") -> None:
        gui: Gui = self
        class_name: str = gui.__class__.__name__
        assert False, f"{class_name}.search_panel_update() has not been implmented yet."

    # Gui.table_clicked():
    def table_clicked(self, table: "Table", tracing: str = "") -> None:
        gui: Gui = self
        class_name: str = gui.__class__.__name__
        assert False, f"{class_name}.table_clicked() has not been implemented yet"

    # Gui.table_panel_update()
    def table_panel_update(self, table: "Table", tracing: str = "") -> None:
        gui: Gui = self
        class_name: str = gui.__class__.__name__
        assert False, f"{class_name}.table_panel_update() has not been implmented yet."


# Node:
class Node:
    """ Represents a single *Node* suitable for use in a *QTreeView* tree. """

    # Node.__init__():
    def __init__(self, name: str, parent: "Optional[Node]",
                 gui: Optional[Gui] = None, tracing: str = "") -> None:
        # Do some additional checking for *node* (i.e. *self*):
        node: Node = self
        # is_collection: bool = isinstance(node, Collection)
        # is_collections: bool = isinstance(node, Collections)
        # is_either = is_collections or is_collection
        # assert (parent is None) == is_collections, f"Node '{name}' has bad parent"

        # Initilize the super class for *node*:
        super().__init__()

        # Determine the *collection* to attache *node*.  Do this very carefully so that
        # `mypy` does not throw a fit:
        collection: Optional[Collection] = None
        if parent is None:
            # A *Node* with no parent is a root node which will not be a *Collection* node,
            # so we mark this *node* as having no *collection*:
            collection = None
        elif isinstance(parent, Collection):
            # If the *parent* is a *Collection*, we can just use the *parent*:
            collection = parent
        elif isinstance(parent, Collections):
            # If the *parent* is a *Collections*, we know this it a child *Collection*, so
            # we just use *node* (i.e. *self*) as the *collection*:
            assert isinstance(node, Collection)
            collection = node
        elif isinstance(parent.collection, Collection):
            # If *parant* has a valid *Collection*, we use it as the *collection*:
            collection = parent.collection
        else:
            # We have not found a valid *Collection* and force *None* into *collection*:
            collection = None

        # Compute *relative_path*:
        relative_path: str = ("" if parent is None
                              else os.path.join(parent.relative_path, Encode.to_file_name(name)))

        # Make sure we have a valid *gui* object:
        if gui is None:
            assert collection is not None
            gui = collection.gui
        assert isinstance(gui, Gui)

        # Load up *node* (i.e. *self*):
        node = self
        self._children: List[Node] = list()       # *Node* sub-classes should use *chldren_get*()
        self.gui: Gui = gui                       # The *gui* object to use for GUI updates
        self.collection: Optional[Collection] = collection  # Parent *Collection* for *node*
        self.name: str = name                     # Human readable name of version of *node*
        self.parent: Optional[Node] = parent      # Parent *Node* (*None* for *Collections*)
        self.relative_path: str = relative_path   # Relative path from root to *node* name wo/suffix

        # To construct a path to the file/directory associated with a *node*:
        # 1. Start with either *node.collection.collection_root* or
        #    *node.collection.searches_root*,
        # 2. Append *relative_path*,
        # 3. If appropriate, append `.xml`.

        # Force *node* to be a child of *parent*:
        if parent is not None:
            parent.child_append(node)

    # Node.can_fetch_more():
    def can_fetch_more(self, tracing: str = "") -> bool:
        node: Node = self
        class_name: str = node.__class__.__name__
        assert False, f"{class_name}.can_fetch_more() needs to be implemented"
        return True

    # Node.child():
    def child(self, index: int) -> "Node":
        node: Node = self
        children: List[Node] = node._children
        assert 0 <= index < len(children)
        child: Node = children[index]
        return child

    # Node.child_append():
    def child_append(self, child: "Node") -> None:
        # FIXME: This should just call *child_insert*() with a position of len(children)!!!

        # Grab some values from *node* (i.e. *self*):
        node: Node = self
        children: List[Node] = node._children
        gui: Gui = node.gui

        # Let *gui* (if it exists) know that we are about to insert *node* at the
        # end of *children* (i.e. at the *insert_row_index*):
        insert_row_index: int = len(children)
        gui.begin_rows_insert(node, insert_row_index, insert_row_index)

        # Now tack *child* onto the end of *child* and update *child*'s parent field:
        children.append(child)
        child.parent = node

        # Let any *gui* know that the row has been appended:
        gui.end_rows_insert()

    # Node.child_count():
    def child_count(self) -> int:
        # Return the number of children associated with *node* (i.e. *self*):
        node: Node = self
        count: int = len(node._children)
        return count

    # Node.child_delete():
    def child_delete(self, index: int) -> None:
        # Grab some values out of *node* (i.e. *self*):
        node = self
        children = node._children
        children_size = len(children)

        # Only delete if *index* is valid*:
        assert 0 <= index < children_size

        # Let *gui* know that the *index*'th row is about to be removed:
        gui = node.gui
        gui.begin_rows_remove(node, index, index)

        # Perform the actual deletion:
        del children[index]

        # Let *gui* know that the row has been deleted:
        gui.end_rows_remove()

    # Node.child_insert():
    def child_insert(self, index: int, child: "Node") -> None:
        # Verify that *index* is valid for inserting into *node* (i.e. *self*):
        node: Node = self
        children = node._children
        children_size = len(children)
        assert 0 <= index <= children_size, f"Bad index={index} size={children_size}"

        # Let *gui* know that we are about to insert *node* at the of *children*
        # (i.e. at *index*):
        gui: Gui = node.gui
        gui.begin_rows_insert(node, index, index)

        # Now stuff *child* into *children* at *index*:
        children.insert(index, child)
        child.parent = node

        # Wrap up *gui* row insert:
        gui.end_rows_insert()

    # Node.child_remove()
    def child_remove(self, child: "Node", tracing="") -> None:
        # Find the *index* of *child* in *node* (i.e. *self*) and delete it:
        node: Node = self
        children: List[Node] = node._children
        index: int = children.index(child)
        assert index >= 0
        node.child_delete(index)

    # Node.children_get():
    def children_get(self) -> "List[Node]":
        # Return the children of *node* (i.e. *self*):
        node: "Node" = self
        children: "List[Node]" = node._children
        return children

    # Node.clicked():
    def clicked(self, gui: Gui, tracing: str = "") -> None:
        # Fail with a more useful error message better than "no such method":
        node: Node = self
        assert False, f"Node.clicked() needs to be overridden for type ('{type(node)}')"

    # Node.csvs_download():
    def csvs_download(self, csvs_directory: str, downloads_count: int, tracing: str = "") -> int:
        node: Node = self
        class_name: str = node.__class__.__name__
        assert False, f"{class_name}.csvs_download() has not been implmented yet!"
        return 0

    # Node.csv_read_and_process():
    def csv_read_and_process(self, csv_directory: str, bind: bool, gui: Gui,
                             tracing: str = "") -> None:
        # Fail with a more useful error message better than "no such method":
        node: Node = self
        assert False, f"Node sub-class '{type(node)}' does not implement csv_read_and_process"

    # Node.directories_get():
    def directories_get(self) -> "List[Directory]":
        node: Node = self
        assert False, f"Node.directories_get() for node of type '{type(node)}'"
        return list()

    # Node.directory_create():
    def directory_create(self, root_path: str, tracing: str = "") -> None:
        node: "Node" = self
        parent: Optional[Node] = node.parent
        if parent is not None:
            parent_relative_path: str = parent.relative_path
            directory_path: str = os.path.join(root_path, parent_relative_path)
            if not os.path.isdir(directory_path):
                os.makedirs(directory_path)
                if tracing:
                    print(f"{tracing}Created directory '{directory_path}'")

    # Node.fetch_more():
    def fetch_more(self, tracing: str = "") -> None:
        node: Node = self
        class_name: str = node.__class__.__name__
        assert False, f"{class_name}.fetch_more() has not been implmented yet."

    # Node.gui_get():
    def gui_get(self) -> Gui:
        # Return *gui* for *node* (i.e. *self*):
        node: "Node" = self
        gui: Gui = node.gui
        return gui

    # Node.has_child():
    def has_child(self, sub_node: "Node") -> bool:
        # Start with *found* set to *False* and only set to *True* if *sub_node* is found
        # in the *children* of *node* (i.e. *self*):
        node: "Node" = self
        found: bool = False
        children: List[Node] = node._children
        child: "Node"
        for child in children:
            if sub_node is child:
                found = True
                break
        return found

    # Node.has_children():
    def has_children(self) -> bool:
        # Return *True* if *node* (i.e. *self*) has one or more children:
        node: "Node" = self
        children: "List[Node]" = node._children
        has_children: bool = len(children) > 0
        return has_children

    # Node.name_get():
    def name_get(self, tracing: str = "") -> str:
        # Grab *title* from *node* (i.e. *self*):
        node: "Node" = self
        name: str = node.name
        return name

    # Node.panel_update():
    @trace(1)
    def panel_update(self, gui: Gui, tracing: str = "") -> None:
        node: Node = self
        class_name: str = node.__class__.__name__
        assert False, f"{class_name}.panel_update() is not implmented yet."

    # Node.remove():
    def remove(self, remove_node: "Node", tracing: str = "") -> None:
        node: "Node" = self
        children: "List[Node]" = node._children
        index: int
        child: Node
        for index, child in enumerate(children):
            if child is remove_node:
                del children[index]
                remove_node.parent = None
                break
        else:
            assert False, f"Node '{remove_node.name}' not in '{node.name}' remove failed"

    # Node.row():
    def row(self) -> int:
        # Return the index of *node* (i.e. *self*) from its parent children list:
        node: Node = self
        parent: Optional[Node] = node.parent
        assert isinstance(parent, Node)
        parent_children: List[Node] = parent._children
        result: int = parent_children.index(node)
        return result

    # Node.sort_helper():
    def sort_helper(self, key_get: "Callable[[Node], Any]", tracing: str = "") -> None:
        # Sort the *children* of *node* (i.e. *self*) using *key_function*:
        node: Node = self
        children: List[Node] = node._children
        children.sort(key=key_get)

    # Node.tables_get():
    def tables_get(self) -> "List[Table]":
        # This routine should never actuall be called:
        node: Node = self
        assert False, f"Node.tables_get() called with a node of type '{type(node)}'"

    # Node.type_letter_get():
    def type_letter_get(self, tracing: str = "") -> str:
        node: Node = self
        class_name: str = node.__class__.__name__
        assert False, f"{class_name}.type_lettet_get() has not been implemented yet."
        return "N"


# Directory:
class Directory(Node):

    # Directory.__init__():
    def __init__(self, name, parent, tracing="") -> None:
        # Perform some additional checking on *parent*:
        assert isinstance(parent, Directory) or isinstance(parent, Collection)

        # Initlialize the *Node* super class for directory (i.e. *self*):
        super().__init__(name, parent)

        # The parent *Node* class initialized *directory* (i.e. *self*) to have a *relative_path*:
        directory: Directory = self
        relative_path: str = directory.relative_path
        if tracing:
            print(f"{tracing}relative_path='{relative_path}'")

    # Directory.append():
    def append(self, node: Node) -> None:
        assert isinstance(node, Directory) or isinstance(node, Table)
        directory: Directory = self
        directory.child_append(node)

    # Directory.can_fetch_more():
    def can_fetch_more(self, tracing: str = "") -> bool:
        # The call to *Directiory.partial_load*, pre-loaded all of the sub-directories and
        # tables for *directory* (i.e. *self*).  That means there is nothing more to fetch.
        return False

    # Directory.clicked():
    def clicked(self, gui: Gui, tracing: str = "") -> None:
        # Send the clicked event back to the *gui* along with *directory* (i.e. *self*):
        directory: Directory = self
        gui.directory_clicked(directory)

    # Directory.directories_get():
    def directories_get(self) -> "List[Directory]":
        directory: Directory = self
        directories: List[Directory] = [directory]
        node: Node
        for node in directory.children_get():
            directories.extend(node.directories_get())
        return directories

    # Directory.name_get():
    def name_get(self, tracing="") -> str:
        directory: Directory = self
        name: str = directory.name
        return name

    # Directory.partial_load():
    def partial_load(self, tracing: str = "") -> None:
        # Compute the *full_path* for the *collection* sub-*directory*:
        directory: Directory = self
        relative_path: str = directory.relative_path
        assert isinstance(directory.collection, Collection)
        collection: Collection = directory.collection
        collection_root: str = collection.collection_root
        full_path: str = os.path.join(collection_root, relative_path)
        if tracing:
            print(f"{tracing}collection_root='{collection_root}'")
            print(f"{tracing}relative_path='{relative_path}'")
            print(f"{tracing}full_path='{full_path}'")
        assert os.path.isdir(full_path), f"Directory '{full_path}' does not exist.!"

        # Visit all of the files and directories in *directory_path*:
        index: int
        file_or_directory_name: str
        for index, file_or_directory_name in enumerate(sorted(list(os.listdir(full_path)))):
            if tracing:
                print(f"{tracing}File_Name[{index}]:'{file_or_directory_name}'")

            # Skip over any files/directories that start with '.':
            if not file_or_directory_name.startswith('.'):
                # Recursively do a partial load for *full_path*:
                sub_relative_path: str = os.path.join(relative_path, file_or_directory_name)
                sub_full_path: str = os.path.join(full_path, file_or_directory_name)
                if tracing:
                    print(f"{tracing}sub_relative_path='{sub_relative_path}'")
                    print(f"{tracing}sub_full_path='{sub_full_path}'")
                if os.path.isdir(sub_full_path):
                    # *full_path* is a directory:
                    name: str = Encode.from_file_name(file_or_directory_name)
                    sub_directory: Directory = Directory(name, directory)
                    assert directory.has_child(sub_directory)
                    sub_directory.partial_load()
                elif sub_full_path.endswith(".xml"):
                    # Full path is a *Table* `.xml` file:
                    name = Encode.from_file_name(file_or_directory_name[:-4])
                    url: str = "bogus URL"
                    table: Table = Table(name, directory, url)
                    assert directory.has_child(table)
                    sub_relative_path = os.path.join(relative_path, name)
                    table.partial_load()
                else:
                    assert False, f"'{full_path}' is neither an .xml nor a directory"

    # Directory.panel_update():
    @trace(1)
    def panel_update(self, gui: Gui, tracing: str = "") -> None:
        directory: Directory = self
        gui.directory_panel_update(directory)

    # Directory.tables_append():
    def tables_get(self) -> "List[Table]":
        directory: Directory = self
        tables: List[Table] = list()
        node: Node
        for node in directory.children_get():
            node_tables: List[Table] = node.tables_get()
            tables.extend(node_tables)
        return tables

    # Directory.type_letter_get():
    def type_letter_get(self, tracing: str = "") -> str:
        return 'D'


# Collection:
class Collection(Node):

    # Collection.__init__():
    @trace(1)
    def __init__(self, name: str, parent: Node,
                 collection_root: str, searches_root: str, gui: Gui, tracing: str = "") -> None:
        # Intialize the *Node* super class of *collection* (i.e. *self*).
        collection: Collection = self
        super().__init__(name, parent, gui=gui)
        if tracing:
            print(f"{tracing}collection.relative_path='{collection.relative_path}'")

        # Do some additional checking on *collections* (i.e. *parent*):
        assert isinstance(parent, Collections)
        collections: Collections = parent
        assert collections.has_child(collection)

        # Stuff some additional values into *collection*:
        self.collection_root: str = collection_root
        self.plugin: Optional[Callable] = None
        self.searches_root: str = searches_root
        self.urls_table: Dict[str, Search] = dict()
        self.searches_table: Dict[str, Search] = dict()
        self.gui: Gui = collections.gui

        # Ensure that *type_letter_get()* returns 'C' for Collection:
        assert collection.type_letter_get() == 'C'

    # Collection.actual_parts_lookup():
    @trace(1)
    def actual_parts_lookup(self, choice_part: "ChoicePart", tracing: str = "") -> List[ActualPart]:
        # Grab some values from *collection* (i.e. *self*) and *choice_part*:
        collection: Collection = self
        searches_table: Dict[str, Search] = collection.searches_table
        searches_root: str = collection.searches_root
        choice_part_name: str = choice_part.name

        # Get some time values:
        stale_time: int = 2 * 24 * 60 * 60  # 2 days in seconds
        now: int = int(time.time())

        # FIXME: This code should be in Search.actual_parts_lookup()!!!

        actual_parts: List[ActualPart] = []
        # Build up *actual_parts* from *collection* (i.e. *self*):
        if choice_part_name in searches_table:
            # We have a *search* that matches *search_name*:
            search = searches_table[choice_part_name]

            # Force *search* to read in all of its information from its associated `.xml` file:
            search.file_load()

            # Grab some values from *search*:
            assert isinstance(search.collection, Collection)
            search_name: str = search.name
            search_url: str = search.url
            relative_path: str = search.relative_path
            if tracing:
                print(f"{tracing}search_name='{search_name}'")
                print(f"{tracing}search_url='{search_url}'")
                print(f"{tracing}relative_path='relative_path'")
            assert search_name == choice_part_name

            # Compute the *csv_file_name* of where the `.csv` file associated with *search_url*
            # is (or will be) stored:
            csv_file_name: str = os.path.join(searches_root, relative_path + ".csv")
            if tracing:
                print(f"{tracing}csv_file_name='{csv_file_name}'")

            # Compute *the
            csv_modification_time: int = (int(os.path.getmtime(csv_file_name))
                                          if os.path.isfile(csv_file_name) else 0)
            if csv_modification_time + stale_time < now:
                assert isinstance(collection, Collection)
                collection.csv_fetch(search_url, csv_file_name)

            # Read in the *csv_file_name*:
            assert os.path.isfile(csv_file_name)
            data_rows: List[List[str]] = []
            column_names: List[str] = []
            csv_file: IO[str]
            with open(csv_file_name) as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=',', quotechar='"')
                row_index: int
                row: List[str]
                for row_index, row in enumerate(csv_reader):
                    # print(f"[{index}]: {row}")
                    if row_index == 0:
                        column_names = row
                    else:
                        data_rows.append(row)

            if tracing:
                print(f"len(data_rows)={len(data_rows)} ; excludes header")
            manufacturer_part_number_index: int = column_names.index("Manufacturer Part Number")
            assert manufacturer_part_number_index >= 0
            manufacturer_index: int = column_names.index("Manufacturer")
            assert manufacturer_index >= 0
            duplicate_removal_table: Dict[Tuple[str, str], Tuple[str, str]] = dict()
            manufacturer: str
            manufacturer_part_number: str
            pair: Tuple[str, str]
            for index, data_row in enumerate(data_rows):
                manufacturer = data_row[manufacturer_index]
                manufacturer_part_number = data_row[manufacturer_part_number_index]
                pair = (manufacturer, manufacturer_part_number)
                duplicate_removal_table[pair] = pair
                # print(f"Row[{index}]: '{manufacturer} : '{manufacturer_part_number}'")
            pairs: List[Tuple[str, str]] = list(duplicate_removal_table.keys())

            for index, pair in enumerate(pairs):
                manufacturer, part_number = pair
                if tracing:
                    print(f"{tracing}Unique_Actual_Part[{index}]: '{manufacturer}': "
                          f"'{part_number}'")
                actual_part: ActualPart = ActualPart(manufacturer, part_number)
                actual_parts.append(actual_part)

        return actual_parts

    # Collection.can_fetch_more():
    def can_fetch_more(self, tracing: str = "") -> bool:
        # All of the directores for *collection* (i.e. *self*) have be previously found
        # using using *Collection.partial_load*().  So, there are no more *Directory*'s
        # to be loaded.
        return False

    # Collection.clicked():
    def clicked(self, gui: Gui, tracing: str = "") -> None:
        collection: Collection = self
        gui.collection_clicked(collection)

    # Collection.directories_get():
    def directories_get(self) -> List[Directory]:
        collection: Collection = self
        directories: List[Directory] = list()
        node: Node
        for node in collection.children_get():
            directories.extend(node.directories_get())
        return directories

    # Collection.partial_load():
    @trace(1)
    def partial_load(self, tracing: str = "") -> None:
        # Visit all of the directories and files in *collection_root*:
        collection: Collection = self
        collection_root: str = collection.collection_root
        relative_path: str = collection.relative_path
        directory_path: str = os.path.join(collection_root, relative_path)
        if tracing:
            print(f"{tracing}collection_root='{collection_root}'")
            print(f"{tracing}relative_path='{relative_path}'")
            print(f"{tracing}directory_path='{directory_path}'")
        assert os.path.isdir(directory_path), f"'{directory_path}' is not a directory"

        index: int
        base_name: str
        for index, base_name in enumerate(list(sorted(os.listdir(directory_path)))):
            if tracing:
                print(f"{tracing}File_Name[{index}]:'{base_name}'")

            # Compute a *full_path* from *collection_root* and *base_name*:
            full_path: str = os.path.join(directory_path, base_name)
            if tracing:
                print(f"{tracing}full_path='{full_path}'")
            if not base_name.startswith('.'):
                if base_name.endswith(".xml"):
                    assert False, "Top level tables not implemented yet"
                elif os.path.isdir(full_path):
                    name: str = Encode.from_file_name(base_name)
                    directory: Directory = Directory(name, collection)
                    assert collection.has_child(directory)
                    directory.partial_load()
                else:
                    assert False, f"'{base_name}' is neither an .xml file nor a directory"

    # Collection.searches_find():
    def searches_find(self, search_name: str, tracing: str = "") -> "Optional[Search]":
        # Grab some values from *collection* (i.e. *self*):
        collection: Collection = self
        searches_table: Dict[str, Search] = collection.searches_table

        # Find a *search* that matches *search_name*:
        search: Optional[Search] = None
        if search_name in searches_table:
            search = searches_table[search_name]
        return search

    # Collection.searches_insert():
    def searches_insert(self, search: "Search", tracing: str = "") -> None:
        search_name: str = search.name
        if search_name[0] != '@':
            collection: Collection = self
            searches_table: Dict[str, Search] = collection.searches_table
            assert search_name not in searches_table, f"Search '{search_name}' already in table"
            searches_table[search_name] = search

    # Collection.searches_remove():
    def searches_remove(self, search: "Search", tracing: str = "") -> None:
        collection: Collection = self
        searches_table: Dict[str, Search] = collection.searches_table
        search_name: str = search.name
        assert search_name[0] != '@', f"Trying to remove template '{search_name}' from table"
        assert search_name in searches_table, "Search '{search_name} not found"
        del searches_table[search_name]

    # Collection.tables_get():
    def tables_get(self) -> "List[Table]":
        collection: Collection = self
        tables: List[Table] = list()
        node: Node
        for node in collection.children_get():
            tables.extend(node.tables_get())
        return tables

    # Collection.type_leter_get()
    def type_letter_get(self, tracing: str = "") -> str:
        # print("Collection.type_letter_get(): name='{0}'".format(self.name))
        return 'C'

    # Collection.url_find():
    def url_find(self, url: str, tracing: str = "") -> "Optional[Search]":
        # Grab some values from *collection* (i.e. *self*):
        collection: Collection = self
        urls_table: Dict[str, Search] = collection.urls_table

        # Find a *search* that matches *search_name*:
        search: Optional[Search] = None
        if url in urls_table:
            search = urls_table[url]
        return search

    # Collection.url_insert():
    def url_insert(self, search: "Search", tracing: str = "") -> None:
        collection: Collection = self
        urls_table: Dict[str, Search] = collection.urls_table
        url: str = search.url
        assert url not in urls_table, f"URL is already in table '{url}'"
        urls_table[url] = search

    # Collection.url_remove():
    def url_remove(self, url: str, tracing: str = "") -> None:
        collection: Collection = self
        urls_table: Dict[str, Search] = collection.urls_table
        assert url in urls_table, f"URL not in table '{url}'"
        del urls_table[url]


# Collections:
class Collections(Node):

    # Collections.__init__():
    @trace(1)
    def __init__(self, name: str, collection_directories: List[str],
                 searches_root: str, partial_load: bool, gui: Gui, tracing: str = "") -> None:
        # Intialize the *Node* super class of *collections* (i.e. *self*):
        collections: Collections = self
        super().__init__(name, None, gui=gui)
        # Stuff some values into *collections*:
        self.collection_directories = collection_directories
        self.searches_root = searches_root
        self.gui = gui

        # Construct the collections list:
        entry_point_key: str = "bom_manager_collection_get"
        index: int
        entry_point: pkg_resources.EntryPoint
        for index, entry_point in enumerate(pkg_resources.iter_entry_points(entry_point_key)):
            entry_point_name: str = entry_point.name
            if tracing:
                print(f"{tracing}Collection_Entry_Point[{index}]: '{entry_point_name}'")
            assert entry_point_name == "collection_get"
            collection_get: Callable[[Collections, str, Gui], Collection] = entry_point.load()
            assert callable(collection_get)
            collection: Collection = collection_get(collections, searches_root, gui)
            assert isinstance(collection, Collection)
            if partial_load:
                collection.partial_load()
            # collections.child_append(collection)

        # Do some *tracing*:
        if tracing:
            relative_path = collections.relative_path
            print(f"{tracing}collection_directories={collection_directories}")
            print(f"{tracing}searchs_root='{searches_root}'")
            print(f"{tracing}relative_path='{relative_path}'")

        # Ensure that *type_letter_get()* returns 'R' is for collections Root:
        assert collections.type_letter_get() == 'R'

    # Collections.__str__():
    def __str__(self) -> str:
        # collections = self
        return f"Collections('Collections')"

    # Collections.actual_parts_lookup():
    @trace(1)
    def actual_parts_lookup(self, choice_part: "ChoicePart", tracing: str = "") -> List[ActualPart]:
        # Visit each *collection* in *collections* (i.e. *self*) and find any
        # *ActualPart*'s that match *search_name*:
        collections: Collections = self
        actual_parts: List[ActualPart] = []
        index: int
        collection: Node
        for index, collection in enumerate(collections.children_get()):
            assert isinstance(collection, Collection)
            if tracing:
                print(f"{tracing}Collection[{index}]:{collection.name}")
            collection_actual_parts: List[ActualPart] = collection.actual_parts_lookup(choice_part)
            actual_parts.extend(collection_actual_parts)

        # FIXME: Cull out duplicate acutal parts (i.e. for the same manufacturer.):
        pass

        return actual_parts

    # Collections.can_fetch_more():
    def can_fetch_more(self, tracing: str = "") -> bool:
        # The children of *collections* (i.e. self*) have already be preloaded by
        # *Collections.partial_load*().  There is nothing more to fetch:
        return False

    # Collections.check():
    def check(self, search_name: str, project_name: str, reference: str,
              tracing: str = "") -> None:
        # Find all *matching_searches* that matach *search_name* from *collections* (i.e. *self*):
        collections: Collections = self
        matching_searches: List[Search] = list()
        collection: Node
        for collection in collections.children_get():
            assert isinstance(collection, Collection)
            searches_table: Dict[str, Search] = collection.searches_table
            if search_name in searches_table:
                matching_search: Search = searches_table[search_name]
                matching_searches.append(matching_search)

        # Output error if nothing is found:
        if not matching_searches:
            print(f"{project_name}: {reference} '{search_name}' not found")

    # Collections.clicked():
    def clicked(self, gui: Gui, tracing: str = "") -> None:
        collections: Collections = self
        gui.collections_clicked(collections)

    # Collections.partial_load():
    def partial_load(self, tracing: str = "") -> None:
        # Extract some values from *collections*:
        collections: Collections = self
        gui: Gui = collections.gui
        collection_directories: List[str] = collections.collection_directories
        searches_root: str = collections.searches_root
        if tracing:
            print(f"{tracing}collection_directories='{collection_directories}'")
            print(f"{tracing}searches_root='{searches_root}'")

        # Find all of the the *collections* by searching through install Python packages
        # for matching plugins:
        entry_point_key: str = "bom_manager_collection_get"
        index: int
        entry_point: pkg_resources.EntryPoint
        for index, entry_point in enumerate(pkg_resources.iter_entry_points(entry_point_key)):
            entry_point_name: str = entry_point.name
            if tracing:
                print(f"{tracing}Entry_Point[{index}]:'{entry_point_name}'")
            assert entry_point_name == "collection_get", (f"'{entry_point_name}' is "
                                                          "not 'collection_get''")
            collection_get: Callable[[Collections, str, Gui], Collection] = entry_point.load()

            # Create *collection*:
            collection: Collection = collection_get(collections, searches_root, gui)
            assert isinstance(collection, Collection)
            assert collections.has_child(collection)

            # Recursively perfrom *partial_load*'s down from *collection*:
            collection.partial_load()

        # Sweep through *path* finding directories (technically symbolic links):
        collection_director: str
        for index, collection_directory in enumerate(sorted(collection_directories)):
            # Perform requested *tracing*:
            if tracing:
                print(f"{tracing}Collection[{index}]:'{collection_directory}'")

            # Skip over Unix/Linux *collection_directory*'s that start with a '.':
            if not collection_directory.startswith('.'):
                # Create *collection_root_path* and *searches_root*:
                collection_directory_root: str = os.path.join(collection_directory, "ROOT")
                collection_directory_root = os.path.abspath(collection_directory_root)
                if tracing:
                    print(f"{tracing}collection_directory_root='{collection_directory_root}'")

                # Now find the directory under `ROOT`:
                sub_directories_glob: str = os.path.join(collection_directory_root, "*")
                sub_directories: List[str] = list(glob.glob(sub_directories_glob))
                assert len(sub_directories) == 1, f"sub_directories={sub_directories}"
                base_name: str = os.path.basename(sub_directories[0])
                name: str = Encode.from_file_name(base_name)
                # collection_root = os.path.join(collection_directory_root, base_name)
                if tracing:
                    print(f"{tracing}base_name='{base_name}'")
                    print(f"{tracing}name='{name}'")
                    # print(f"{tracing}collection_root='{collection_root}'")
                    print(f"{tracing}searches_root='{searches_root}'")

                # Recursively perfrom *partial_load*'s down from *collection*:
                collection.partial_load()

    # Collections.searches_find():
    @trace(1)
    def searches_find(self, search_name: str, tracing: str = "") -> "List[Search]":
        # Visit each *collection in *collections* (i.e. *self*) to see if it has *search_name*:
        collections: Collections = self
        searches: List[Search] = []
        collection: Node
        for collection in collections.children_get():
            assert isinstance(collection, Collection)
            search: Optional[Search] = collection.search_find(search_name)
            if search is not None:
                # We have a matching *search*:
                assert search_name == search.name, f"'{search_name}'!='{search.name}'"
                searches.append(search)
        return searches

    # Collections.type_leter_get():
    def type_letter_get(self, tracing: str = "") -> str:
        # print("Collections.type_letter_get(): name='{0}'".format(self.name))
        return 'R'


# Search:
class Search(Node):

    # FIXME: This tale belongs in *Units*:
    ISO_MULTIPLIER_TABLE: Dict[str, float] = {
      "E": 1.0e18,
      "P": 1.0e15,
      "T": 1.0e12,
      "G": 1.0e9,
      "M": 1.0e6,
      "k": 1.0e3,
      "m": 1.0e-3,
      "μ": 1.0e-6,
      "u": 1.0e-6,
      "n": 1.0e-9,
      "p": 1.0e-12,
      "f": 1.0e-15,
      "a": 1.0e-18,
    }

    # Search.__init__():
    def __init__(self, name: str, parent: "Table", search_parent: "Optional[Search]",
                 url: str, tracing: str = "") -> None:
        # Grab some values from *search* (i.e. *self*):
        search: Search = self
        assert name.find("%3b") < 0

        # Initialize the super class for *search* (i.e. *self*):
        super().__init__(name, parent)

        # The *parent* is known to be a *table* and must contain *search*:
        table: Table = parent
        assert table.has_child(search)

        # Mark that the *table* is no longer sorted, since the *Node.__init__()* just
        # appended *search* to its *children* list:
        table.is_sorted = False

        # Stuff values into *search*:
        self.comments: List[SearchComment] = list()
        self.loaded: bool = False
        self._relative_path: str = ""
        self.filters: List[Filter] = list()
        self.search_parent: Optional[Search] = search_parent
        self.search_parent_title: str = ""
        self.search_parent_name: str = ""  # Used by *Search.tree_load*()
        self.url: str = url

        # Collect global information about the search *name* and *url*:
        collection: Optional[Collection] = parent.collection
        assert isinstance(collection, Collection)
        collection.searches_insert(search)

    # Search.__str__(self):
    def __str__(self) -> str:
        search: Search = self
        name: str = "??"
        if hasattr(search, "name"):
            name = search.name
        return f"Search('{name}')"

    # Search.can_fetch_more():
    def can_fetch_more(self, tracing: str = "") -> bool:
        # Currently, all *Search* objects never have any childre.  Hence, there is nothing fetch:
        return False

    # Search.children_count():
    def children_count(self, tracing: str = "") -> Tuple[int, int]:
        search: Search = self
        table: Optional[Node] = search.parent
        assert isinstance(table, Table)
        children: List[Node] = table.children_get()
        child: Node
        immediate_children: int = 0
        all_children: int = 0
        for child in children:
            assert isinstance(child, Search)
            distance: int = child.distance(search)
            if distance == 1:
                immediate_children += 1
                all_children += 1
            elif distance >= 2:
                all_children += 1
        return (immediate_children, all_children)

    # Search.clicked()
    def clicked(self, gui: Gui, tracing: str = "") -> None:
        # Send the clicked event back to *gui* along with *search* (i.e. *self*):
        search: Search = self
        gui.search_clicked(search)

    # Search.comments_append():
    def comments_append(self, comments: List[SearchComment]) -> None:
        # Tack *comments* onto the the comments list in *search* (i.e. *self*):
        search: Search = self
        search_comments: List[SearchComment] = search.comments
        search_comments.extend(comments)

    # Search.distance():
    def distance(self, target_search: "Search", tracing: str = "") -> int:
        search: Search = self
        distance: int = 0
        while search is not target_search:
            search_parent: Optional[Node] = search.search_parent
            if search_parent is None:
                distance = -1
                break
            assert isinstance(search_parent, Search)
            distance += 1
            search = search_parent
        return distance

    # Search.file_load():
    def file_load(self, tracing: str = "") -> None:
        # Grab some informtation from parent *table* of *search*:
        search: Search = self
        table: Optional[Node] = search.parent
        assert table is not None
        assert isinstance(table, Table)
        table_name: str = table.name
        searches: List[Node] = table.children_get()
        searches_size: int = len(searches)
        # Only load *search* (i.e. *self*) if it is not already *loaded*:
        loaded: bool = search.loaded
        if tracing:
            print(f"{tracing}loaded={loaded} table='{table_name}' searches_size={searches_size}")
        if not loaded:
            # Grab some values from *search*:
            collection: Optional[Collection] = search.collection
            assert isinstance(collection, Collection)
            searches_root: str = collection.searches_root
            relative_path: str = search.relative_path
            search_full_file_name: str = os.path.join(searches_root, relative_path + ".xml")
            if tracing:
                print(f"{tracing}search_full_file_name={search_full_file_name}")
            search_file: IO[str]
            with open(search_full_file_name, "r") as search_file:
                # Read in *search_xml_text* from *search_file*:
                search_xml_text: str = search_file.read()

                # Parse the XML in *search_xml_text* into *search_tree*:
                search_tree: etree._Element = etree.fromstring(search_xml_text)

                # Now process the contents of *search_tree* and stuff the result:
                search.tree_load(search_tree)

                # Mark that *table* is no longer sorted since we may updated the
                # *search_parent* and *search_parent_title* fields:
                table.is_sorted = False

            # Mark *search* as *loaded*:
            search.loaded = True

    # Search.file_delete
    @trace(1)
    def file_delete(self, tracing: str = "") -> None:
        search: Search = self
        collection: Optional[Collection] = search.collection
        assert isinstance(collection, Collection)
        searches_root: str = collection.searches_root
        relative_path: str = search.relative_path
        search_full_file_name: str = os.path.join(searches_root, relative_path + ".xml")
        if tracing:
            print(f"{tracing}search_full_file_name='{search_full_file_name}'")
        if os.path.isfile(search_full_file_name):
            os.remove(search_full_file_name)
            assert not os.path.isfile(search_full_file_name)

    # Search.filters_refresh():
    def filters_refresh(self, tracing: str = "") -> None:
        # Before we do anything we have to make sure that *search* has an associated *table*.
        # Frankly, it is should be impossible not to have an associated table, but we must
        # be careful:
        search: Search = self
        table: Optional[Node] = search.parent
        assert isinstance(table, Table)
        if table is not None:
            # Now we have to make sure that there is a *filter* for each *parameter* in
            # *parameters*.  We want to preserve the order of *filters*, so this is pretty
            # tedious:

            # Step 1: Start by deleting any *filter* from *filters* that does not have a
            # matching *parameter* in parameters.  This algorithme is O(n^2), so it could
            # be improved:
            filters: List[Filter] = search.filters
            parameters: List[Parameter] = table.parameters
            new_filters: List[Filter] = list()
            filter: Filter
            for filter in filters:
                parameter: Parameter
                for parameter in parameters:
                    if filter.parameter is parameter:
                        new_filters.append(filter)
                        break

            # Carefully replace the entire contents of *filters* with the contents of *new_filters*:
            filters[:] = new_filters[:]

            # Step 2: Sweep through *parameters* and create a new *filter* for each *parameter*
            # that does not already have a matching *filter* in *filters*.  Again, O(n^2):
            parameter_index: int
            for pararmeter_index, parameter in enumerate(parameters):
                for filter in filters:
                    if filter.parameter is parameter:
                        break
                else:
                    filter = Filter(table, parameter, use=False, select="")
                    filters.append(filter)

    # Search.is_deletable():
    def is_deletable(self, tracing: str = "") -> bool:
        # Grab *search_name* from *search* (i.e. *self*):
        search: Search = self

        # Search through *sibling_searches* of *table* to ensure that *search* is not
        # a parent of any *sibling_search* object:
        table: Optional[Node] = search.parent
        assert isinstance(table, Table)
        sibling_searches: List[Node] = table.children_get()

        # Make sure that there are now *sibling_search*'s that depend upon *search*:
        deletable: bool = True
        sibling_search: Node
        for sibling_search in sibling_searches:
            if sibling_search.parent is search:
                deletable = False
                break
        return deletable

    # Search.key():
    # def key(self) -> Tuple[int, float, str]:
    @staticmethod
    def key(search: Node) -> Any:
        """ Return a sorting key for the *Search* object (i.e. *self*):

            The sorting key is a three tuple consisting of (*Depth*, *UnitsNumber*, *Text*), where:
            * *Depth*: This is the number of templates between "@ALL" and the search.
            * *UnitsNumber*: This is the number that matches a number followed by ISO units
              (e.g. "1KOhm", ".01uF", etc.)
            * *Text*: This is the remaining text after *UnitsNumber* (if it is present.)
        """
        #

        # In the Tree view, we want searches to order templates (which by convention
        #    start with an '@' character) before the other searches.  In addition, we would
        #    like to order searches based on a number followed by an ISO type (e.g. "4.7KOhm",
        #    ".1pF", etc.) to be sorted in numberical order from smallest to largest (e.g.
        #    ".01pF", ".1pf", "10nF", ".1uF", "10uF", etc.)  Furthermore, the template searches
        #    are organized as a heirachical set of templates and we want the ones closest to
        #    to top

        # Grab *table* and *searches_table* from *search* (i.e. *self*):
        assert isinstance(search, Search)
        table: Optional[Node] = search.parent
        assert isinstance(table, Table)

        # Figure out template *depth*:
        depth: int = 0
        nested_search: Search = search
        while nested_search.search_parent is not None:
            depth += 1
            nested_search = nested_search.search_parent

        # Sweep through the *search_name* looking for a number, optionally followed by an
        # ISO unit mulitplier.:
        number_end_index: int = -1
        search_name: str = search.name
        character_index: int
        character: str
        for character_index, character in enumerate(search_name):
            if character in ".0123456789":
                # We a *character* that "could" be part of a number:
                number_end_index = character_index + 1
            else:
                break

        # Extract *number* from *search_name* if possible:
        number: float = 0.0
        if number_end_index >= 0:
            try:
                number = float(search_name[0:number_end_index])
            except ValueError:
                pass

        # Figure out the ISO *multiplier* and adjust *number* appropriately:
        multiplier: float = 1.0
        if number_end_index >= 0 and number_end_index < len(search_name):
            multiplier_character: str = search_name[number_end_index]
            iso_multiplier_table: Dict[str, float] = Search.ISO_MULTIPLIER_TABLE
            if character in iso_multiplier_table:
                multiplier = iso_multiplier_table[multiplier_character]
        number *= multiplier

        # Return a tuple used for sorting:
        rest: str = search_name if number_end_index < 0 else search_name[number_end_index:]
        key: Tuple[int, float, str] = (depth, number, rest)
        return key

    # Search.panel_update():
    @trace(1)
    def panel_update(self, gui: Gui, tracing: str = "") -> None:
        search: Search = self
        gui.search_panel_update(search)

    # Search.search_parent_set():
    def search_parent_set(self, search_parent: "Search", tracing: str = "") -> None:
        # Stuff *search_parent* into *search* (i.e. *self*):
        search: Search = self
        search.search_parent = search_parent

    # Search.search_parent_title_set():
    def search_parent_title_set(self, search_parent_title: str) -> None:
        # Stuff *search_parent_title* into *search* (i.e. *self*):
        search: Search = self
        search.search_parent_title = search_parent_title

    # Search.name_get():
    def name_get(self, tracing: str = "") -> str:
        # Grab some values from *search* (i.e. *self*):
        search: Search = self
        search_name: str = search.name
        table: Optional[Node] = search.parent
        assert isinstance(table, Table)

        # Make sure that all *searches* associated with *table* are loaded from their
        # associated `.xml` files:
        table.searches_load()

        # Make sure that *table* is *sort*'ed:
        table.sort()

        # Construct the *name*:
        search_parent: Optional[Search] = search.search_parent
        name: str = (search_name if search_parent is None
                     else f"{search_name} ({search_parent.name})")
        return name

    # Search.tree_load():
    def tree_load(self, search_tree: etree._Element, tracing: str = "") -> None:
        # The basic format of the *search_tree* is:
        #
        #        <Search name="..." parent="..." table="..." url="...">
        #          <SerachComments>
        #            <SerachComment language="EN">
        #            </SerachComment language="EN">
        #            ...
        #          </SerachComments>
        #          <Filters>
        #            ...
        #          </Filters>
        #        </Search>

        # Extract the attributes from *attributes_table* of the `<Search ...>` tag:
        attributes_table: Dict[str, str] = search_tree.attrib
        assert "name" in attributes_table
        name: str = Encode.from_attribute(attributes_table["name"])
        search_parent_name: str = (Encode.from_attribute(attributes_table["search_parent"])
                                   if "search_parent" in attributes_table else "")
        assert "url" in attributes_table, "attributes_table={0}".format(attributes_table)
        url: str = attributes_table["url"]

        # Extract the `<SearchComments>...</SearchComments>` XML:
        search_tree_elements: List[etree._Element] = list(search_tree)
        assert search_tree_elements, "No <SearchComments> found."
        comments_tree: etree._Element = search_tree_elements[0]
        assert comments_tree.tag == "SearchComments", (f"<{comments_tree.tag}> found "
                                                       f"instead of <SearchComments>")
        assert not comments_tree.attrib, "<SearchComments> should not have any attributes"
        comments: List[SearchComment] = list()
        comment_tree: etree._Element
        for comment_tree in comments_tree:
            comment: SearchComment = SearchComment.xml_parse(comment_tree)
            comments.append(comment)

        # Load values from *search_tree* into *search* (i.e. *self*):
        search: Search = self
        search.name = name
        search.comments[:] = comments[:]
        # search.filters[:] = filters[:]
        search.search_parent = None  # This is filled in later on
        search.search_parent_name = search_parent_name
        search.url = url

    # Search.type_letter_get():
    def type_letter_get(self, tracing: str = "") -> str:
        return 'S'

    # Search.url_set():
    def url_set(self, url: str) -> None:
        # Stuff *url* into *search* (i.e. *self*):
        search: Search = self
        search.url = url

    # Search.xml_file_save():
    def xml_file_save(self, tracing: str = "") -> None:
        # Compute *xml_file_name* and the *xml_file_directory* starting from *search* (i.e. *self*):
        search: Search = self
        collection: Optional[Collection] = search.collection
        assert isinstance(collection, Collection)
        searches_root: str = collection.searches_root
        relative_path: str = search.relative_path
        xml_file_name: str = os.path.join(searches_root, relative_path + ".xml")
        xml_directory: str = os.path.split(xml_file_name)[0]
        if tracing:
            print(f"{tracing}searches_root='{searches_root}'")
            print(f"{tracing}relative_path='{relative_path}'")
            print(f"{tracing}xml_file_name='{xml_file_name}'")
            print(f"{tracing}xml_directory='{xml_directory}'")

        # Create *xml_text* from *search*:
        xml_lines: List[str] = list()
        xml_lines.append('<?xml version="1.0"?>')
        search.xml_lines_append(xml_lines, "")
        xml_lines.append("")
        xml_text: str = "\n".join(xml_lines)

        # Ensure that *xml_directory* exists:
        if not os.path.isdir(xml_directory):
            os.makedirs(xml_directory)

        # Write *xml_text* out to *xml_file_name*:
        xml_file: IO[str]
        with open(xml_file_name, "w") as xml_file:
            xml_file.write(xml_text)

        # Mark *search* as *loaded* since we just wrote out the contents:
        search.loaded = True

    # Search.xml_lines_append()
    def xml_lines_append(self, xml_lines: List[str], indent: str, tracing: str = "") -> None:
        # Grab some values from *search* (i.e. *self*):
        search: Search = self
        table: Optional[Node] = search.parent
        assert isinstance(table, Table)
        search_parent: Optional[Search] = search.search_parent
        search_name: str = search.name

        # Figure out *search_parent_title* which is empty only for the `@ALL` *Search* object:
        search_parent_text: str = ("" if search_parent is None else
                                   f'search_parent="{Encode.to_attribute(search_parent.name)}" ')

        # Start the `<Search...>` element:
        xml_lines.append(f'{indent}<Search '
                         f'name="{Encode.to_attribute(search_name)}" '
                         f'{search_parent_text}'
                         f'table="{Encode.to_attribute(table.name)}" '
                         f'url="{Encode.to_attribute(search.url)}">')

        # Append the `<SearchComments>` element:
        xml_lines.append(f'{indent}  <SearchComments>')
        search_comments: List[SearchComment] = search.comments
        search_comment_indent = indent + "    "
        for search_comment in search_comments:
            search_comment.xml_lines_append(xml_lines, search_comment_indent)
        xml_lines.append(f'{indent}  </SearchComments>')

        # Wrap up the `<Search>` element:
        xml_lines.append(f'{indent}</Search>')


# Table:
class Table(Node):

    # Table.__init__():
    def __init__(self, name: str, parent: Node, url: str, tracing: str = "") -> None:
        # Initialize the parent class:
        super().__init__(name, parent)

        # Load additional values into *table* (i.e. *self*):
        # table: Table = self
        self.comments: List[TableComment] = list()
        self.import_column_triples: List[List[Tuple[int, str, str]]] = list()
        self.import_headers: List[str] = list()     # Read from .csv file
        self.import_rows: List[str] = list()        # Read from .csv file
        self.is_sorted: bool = False
        self.loaded: bool = False
        self.parameters: List[Parameter] = list()
        self._relative_path: str = ""
        self.searches_table: Dict[str, Search] = dict()
        self.url: str = ""

    # Table.can_fetch_more():
    def can_fetch_more(self, tracing: str = "") -> bool:
        # Conceptually, every table as a default `@ALL` search.  We return *True* if
        # the `@ALL` search has not actually been created yet for *table* (i.e. *self*):
        table: Table = self
        searches: List[Node] = table.children_get()
        can_fetch_more: bool = (len(searches) == 0)
        return can_fetch_more

    # Table.clicked():
    def clicked(self, gui: Gui, tracing: str = "") -> None:
        # Forward clicked event back to *gui* along with *table* (i.e. *self*):
        table: Table = self
        gui.table_clicked(table)

    # Table.column_tables_extract():
    @trace(1)
    def column_tables_extract(self, rows: List[List[str]],
                              tracing: str = "") -> List[Dict[str, int]]:
        # Create and return a *column_tables* which has one dictionary for each column in *rows*.
        # Each *column_table* dictionary that contains an occurance count for each different
        # value in the column.

        # Figure out how many *columns* there are for each row.  Each row is assumed
        # to have the same number of *columns*:
        assert rows, "No data to extract"
        row0: List[str] = rows[0]
        columns: int = len(row0)

        # Create *column_tables* and fill in one *column_table* per *column*:
        column_tables: List[Dict[str, int]] = list()
        for column in range(columns):
            column_table: Dict[str, int] = dict()
            column_tables.append(column_table)

            # Sweep across each *row* in *rows* and fill in *column_table*:
            for row in rows:
                assert len(row) == columns
                value: str = row[column]
                if value in column_table:
                    # We have seen *value* before in this *column*, so increment its count:
                    column_table[value] += 1
                else:
                    # This is the first time we seen *value* in this *column*, so insert it
                    # into *column_table* as the first one:
                    column_table[value] = 1

        # Return *column_tables*:
        return column_tables

    # Table.csv_file_read():
    @trace(1)
    def csv_file_read(self, tracing: str = "") -> Tuple[List[str], List[List[str]]]:
        # Grab some values from *table* (i.e. *self*):
        table: Table = self
        csv_full_name: str = table.csv_full_name_get()

        # Open *csv_full_name* and read in the *headers* and *rows*:
        assert os.path.isfile(csv_full_name), "File '{csv_full_file_name}' does not exist."
        headers: List[str]
        rows: List[List[str]] = list()
        csv_file: IO[str]
        with open(csv_full_name, newline="") as csv_file:
            row_index: int
            row: List[str]
            for row_index, row in enumerate(csv.reader(csv_file, delimiter=',', quotechar='"')):
                if row_index == 0:
                    # The first *row* is actually the *headers*:
                    headers = row
                else:
                    # All others are data *rows*:
                    rows.append(row)

        # Return the resulting *headers* and *rows*:
        return headers, rows

    # Table.csv_full_name_get():
    def csv_full_name_get(self) -> str:
        table: Table = self
        class_name: str = table.__class__.__name__
        assert False, f"{class_name}.csv_full_name_get() needs to be implemented."
        return ""

    # Table.csv_read_and_process():
    @trace(1)
    def csv_read_and_process(self, csv_directory: str, bind: bool, gui: Gui,
                             tracing: str = "") -> None:
        # This delightful piece of code reads in a `.csv` file and attempts to catagorize
        # each column of the table with a "type".  The types are stored in *re_table*
        # (from *gui*) as dictionary of named pre compiled regualar expressions.
        # If there is no good match for the table column contents, it is given a type
        # of "String".  This code is actually pretty involved and convoluted.

        # Read the example `.csv` file associated with *table* (i.e. *self*) into *headers* and
        # *rows*:
        table: Table = self
        headers: List[str]
        rows: List[List[str]]
        headers, rows = table.csv_file_read()

        # Extract *column_tables* which is a list of dictionaries where each dictionary
        # has an occurence count for each unique value in a column:
        column_tables: List[Dict[str, int]] = table.column_tables_extract(rows)

        # Extract *type_tables* which is a list of dictionaries, where each dictionary
        # has an occurence count for each unique type name in the column:
        types_tables: List[Dict[str, int]] = table.type_tables_extract(column_tables, gui)

        # If requested, bind the *types_tables* to *parameters*:
        if bind:
            table.parameters_bind(headers, types_tables)

        # We are done and can write out *table* now:
        table.xml_file_save()

    # Table.directories_get():
    def directories_get(self) -> "List[Directory]":
        # A *table* has no sub-directories, so the empty list is returned:
        return []

    # Table.fetch_more():
    def fetch_more(self, tracing: str = "") -> None:
        # Create *all_search* if it does not already exist (i.e. *searches_size* is 0):
        table: Table = self
        searches: List[Node] = table.children_get()
        searches_size = len(searches)
        if tracing:
            print(f"{tracing}1:searches_size={searches_size}")
        if searches_size == 0:
            # Note that the call to the *Search*() has the side-effect of appending
            # *all_search* to the children of *table*:
            # base_name = Encode.to_file_name(name)
            all_search: Search = Search("@ALL", table, None, table.url)
            assert table.has_child(all_search)
            assert len(searches) == 1
            all_search.xml_file_save()

            # Make sure that *table* is fully loaded so we can grab the *url*:
            table.file_load()
            searches_size = len(searches)
            if tracing:
                print(f"{tracing}2:searches_size={searches_size}")
            assert searches_size == 1
            url: str = table.url

            # Fill in the rest of *all_search* from *table*:
            comment: SearchComment = SearchComment(language="EN", lines=list())
            all_search.comments.append(comment)
            all_search.url = url

            # Force *all_search* out to the file system:
            all_search.xml_file_save()
            if tracing:
                searches_size = len(searches)
                print(f"{tracing}3:searches_size={searches_size}")

    # Table.file_load():
    def file_load(self, tracing: str = "") -> None:
        # Only load *table* (i.e. *self*) if it is not already *loaded*:
        table: Table = self
        loaded: bool = table.loaded
        searches: List[Node] = table.children_get()
        searches_size: int = len(searches)
        if tracing:
            print(f"{tracing}loaded={loaded} searches_size={searches_size}")
        if not table.loaded:
            # Get *table_file_name* for *table*:
            relative_path: str = table.relative_path
            collection: Optional[Collection] = table.collection
            assert isinstance(collection, Collection)
            collection_root: str = collection.collection_root
            table_file_name: str = os.path.join(collection_root, relative_path + ".xml")
            assert os.path.exists(table_file_name), f"'{table_file_name}' does not exist"

            # Read *table_tree* in from *full_file_name*:
            table_file: IO[str]
            with open(table_file_name) as table_file:
                # Read in *table_xml_text* from *table_file*:
                table_xml_text: str = table_file.read()

                # Parse the XML in *table_xml_text* into *table_tree*:
                table_tree: etree._Element = etree.fromstring(table_xml_text)
                # FIXME: Catch XML parsing errors here!!!

                # Now process the contents of *table_tree* and stuff the results into *table*:
                table.tree_load(table_tree)

            # Mark *table* as *loaded*:
            table.loaded = True

    # Table.has_children():
    def has_children(self) -> bool:
        # This is a bit obscure.  A *Table* object conceptually always has an "@ALL" search.
        # *True* is returned even if the *table* (i.e. *self*) does not actually have
        # any children.  When *Table.fetch_more*() is called the "@ALL" search will auto-magically
        # be created under the covers.
        return True

    # Table.header_labels_get():
    def header_labels_get(self) -> List[str]:
        table: Table = self
        parameters: List[Parameter] = table.parameters
        parameters_size: int = len(parameters)
        assert parameters_size >= 1, "Table is empty"
        header_labels: List[str] = list()
        for parameter in parameters:
            parameter_comments: List[ParameterComment] = parameter.comments
            header_label: str = "?"
            if len(parameter_comments) >= 1:
                parameter_comment: ParameterComment = parameter_comments[0]
                short_heading: str = parameter_comment.short_heading
                long_heading: str = parameter_comment.long_heading
                header_label = short_heading if short_heading is not None else long_heading
            header_labels.append(header_label)
        return header_labels

    # Table.name_get():
    def name_get(self, tracing: str = "") -> str:
        # Force *table* (i.e. *self*) *load* if it has not already been loaded:
        table: Table = self
        name: str = table.name
        table.file_load()

        # Augment *name* with the *searches_size*:
        searches: List[Node] = table.children_get()
        searches_size: int = len(searches)
        if len(searches) >= 2:
            name += f" ({searches_size})"
        return name

    # Table.panel_update():
    @trace(1)
    def panel_update(self, gui: Gui, tracing: str = "") -> None:
        table: Table = self
        gui.table_panel_update(table)

    # Table.parameters_bind():
    @trace(1)
    def parameters_bind(self, headers: List[str], type_tables: List[Dict[str, int]],
                        tracing: str = "") -> None:
        # Grab *parameters* from *table* and make sure that there is a 1-to-1 correspondance
        # between *paramters* and *type_tables*:
        table: Table = self
        parameters: List[Parameter] = table.parameters

        # Sweep through *Paramters* finding the *type_name* with the best match:
        index: int
        header: str
        csv: str = ""
        default: str = ""
        optional: bool = False
        for index, header in enumerate(headers):
            # Convert *type_table* into *type_counts*:
            type_table: Dict[str, int] = type_tables[index]
            type_counts: List[Tuple[str, int]] = list(type_table.items())

            # Sort *type_counts* based on count:
            type_counts.sort(key=lambda name_count: (name_count[1], name_count[0]))

            # Grab the *name_count_last* which will have the highest count, and stuff
            # the associated *type_name* into *parameter*:
            name_count_last: Tuple[str, int] = type_counts[-1]
            type_name: str = name_count_last[0]

            parameter: Parameter
            if len(parameters) <= index:
                comments: List[ParameterComment] = [ParameterComment("EN", [], header, "")]
                enumerations: List[Enumeration] = list()
                parameter = Parameter(header, type_name, csv, index, default, optional,
                                      comments, enumerations)
                parameters.append(parameter)
            else:
                parameter.type = type_name

    # Table.partial_load():
    def partial_load(self, tracing: str = "") -> None:
        # Grab some values from *table* (i.e. *self*):
        table: Table = self
        relative_path: str = table.relative_path
        collection: Optional[Collection] = table.collection
        assert isinstance(collection, Collection)

        # Compute *searches_path* which is the directory that contains the *Search* `.xml` files:
        collection_root: str = collection.collection_root
        searches_root: str = collection.searches_root
        searches_directory: str = os.path.join(searches_root, relative_path)
        if tracing:
            print(f"{tracing}collection_root='{collection_root}'")
            print(f"{tracing}searches_root='{searches_root}'")
            print(f"{tracing}relative_path='{relative_path}'")
            print(f"{tracing}searches_directory='{searches_directory}'")

        # Scan through *searches_path* looking for `.xml` files:
        if os.path.isdir(searches_directory):
            # *searches_path* is a directory so we scan it:
            index: int
            search_file_name: str
            for index, search_file_name in enumerate(sorted(list(os.listdir(searches_directory)))):
                # Preform requested *tracing*:
                if tracing:
                    print(f"{tracing}Search[{index}]:'{search_file_name}'")

                # Skip over any files that do not end with `.xml` suffix:
                if search_file_name.endswith(".xml"):
                    # Extract *name* and *title* from *file_name* (ignoring the `.xml` suffix):
                    file_base: str = search_file_name[:-4]
                    search_name: str = Encode.from_file_name(file_base)

                    # Create *search* and then save it out to the file system:
                    search: Search = Search(search_name, table, None, "??")
                    assert table.has_child(search)
                    search.loaded = False

    # Table.sort():
    def sort(self, tracing: str = "") -> None:
        # Only sort *table* (i.e. *self*) if it is not *is_sorted*:
        table: Table = self
        is_sorted: bool = table.is_sorted
        if tracing:
            print(f"{tracing}is_sorted={is_sorted}")
        if not is_sorted:
            # Grab *searches* list from *table* (i.e. *self*):
            searches: List[Node] = table.children_get()
            searches_size: int = len(searches)
            if tracing:
                print(f"{tracing}searches_size={searches_size}")

            # Create a new *searches_table* that contains every *search* keyed by *search_name*:
            searches_table: Dict[str, Search] = dict()
            index: int
            search: Node
            for index, search in enumerate(searches):
                assert isinstance(search, Search)
                search_name: str = search.name
                if search_name in searches_table:
                    assert searches_table[search_name] is search
                else:
                    searches_table[search_name] = search
                # print(f"Search[{index}]:'{search_name}'=>'{search_key}'")
            if len(searches) != len(searches_table):
                # tracing = "TS:" if tracing is None else tracing
                if tracing:
                    searches_titles = [search.name for search in searches]
                    print(f"{tracing}searches_titles={searches_titles}")
                    print(f"{tracing}searches_table={searches_table}")
                assert False, f"{len(searches)} != {len(searches_table)}"

            # Sweep through *searches* and ensure that the *search_parent* field is set:
            # for index, search in enumerate(searches):
            #     search_parent = search.search_parent
            #     if search_parent is not None:
            #         search_parent_name = search_parent.name
            #         if search_parent_name not in searches_table:
            #             keys = list(searches_table.keys())
            #             assert False, f"'{search_parent_name}' not in searches_table {keys}"
            #         search_parent = searches_table[search_parent_title_key]
            #         search.search_parent = search_parent
            #     if tracing:
            #         search_parent_text = ("None" if search_parent is None
            #                               else f"'{search_parent.name}'")
            #         print(f"{tracing}Search[{index}]:'{search.name}' {search_parent_text}")

            # Now sort *searches*:
            searches.sort(key=Search.key)

            # Mark that *table* *is_sorted*:
            table.is_sorted = True

    # Table.search_directory_get():
    # def search_directory_get(self, tracing: str = "") -> str:
    #     # Compute *search_directory*:
    #     table: Table = self
    #     searches_root: str = table.searches_root_get()
    #     relative_path: str = table.relative_path
    #     table_name: str = table.name
    #     table_base_name: str = Encode.to_file_name(table_name)
    #     search_directory: str = os.path.join(searches_root, relative_path, table_base_name)
    #     if tracing:
    #         print(f"{tracing}searches_root='{searches_root}'")
    #         print(f"{tracing}relative_path='{relative_path}'")
    #         # print(f"{tracing}table__directory='{table_directory}'")
    #         print(f"{tracing}search_directory='{search_directory}'")

    #     # Make sure *search_directory* exists:
    #     if not os.path.isdir(search_directory):
    #         os.makedirs(search_directory)
    #         if tracing:
    #             print(f"{tracing}Created directory '{search_directory}'")
    #     return search_directory

    # Table.searches_load():
    def searches_load(self, tracing: str = "") -> None:
        # Grab some values from *table* (i.e. *self*):
        table: Table = self
        table_searches: Dict[str, Search] = dict()
        searches_loaded_count: int = 0
        searches: List[Node] = table.children_get()
        search: Node
        for search in searches:
            # Make sure *search* is *loaded*.  We test *loaded* up here to prevent
            # a lot of unnecessary calls to *file_load*:
            assert isinstance(search, Search)
            if not search.loaded:
                search.file_load()
                assert search.loaded
                searches_loaded_count += 1

            # Build up *tables_searches_table_table* with all of the *searches* to used for
            # for the upcoming parent search fix-up step:
            table_searches[search.name] = search

        # Fix up the search parent links:
        if searches_loaded_count >= 1:
            for search in searches:
                assert isinstance(search, Search)
                search_parent_name: str = search.search_parent_name
                if tracing:
                    print(f"Search '{search.name}' parent name is '{search_parent_name}'")
                if search_parent_name != "":
                    assert search_parent_name in table_searches, (f"'{search_parent_name} '"
                                                                  f"not in {table_searches.keys()}")
                    search_parent: Search = table_searches[search_parent_name]
                    search.search_parent = search_parent
                    if tracing:
                        print(f"Setting search '{search.name}' "
                              f"search parent to '{search_parent.name}'")
                else:
                    if tracing:
                        print(f"Search '{search.name}' has no search parent.")

    # Table.searches_table_set():
    # def searches_table_set(self, searches_table):
    #     # Verify argument types:
    #     assert isinstance(searches_table, dict)
    #
    #     # Stuff *searches_table* into *table* (i.e. *self*):
    #     table = self
    #     table.searches_stable = searches_table

    # Table.tables_get():
    def tables_get(self) -> "List[Table]":
        table: Table = self
        return [table]

    # Table.tree_load():
    def tree_load(self, table_tree: etree._Element, tracing: str = "") -> None:
        # The format of a *Table* `.xml` file is basically:
        #
        #        <Table name="..." url="...">
        #          <TableComments>
        #            ...
        #          </TableComments>
        #          <Parameters>
        #            ...
        #          </Parameters>
        #        </Table>

        # Extract the attributes from *attributes_table*:
        assert table_tree.tag == "Table"
        attributes_table: Dict[str, str] = table_tree.attrib
        assert "name" in attributes_table
        name: str = Encode.from_attribute(attributes_table["name"])
        url: str = Encode.from_attribute(attributes_table["url"])

        # Extract the *comments* from *comments_tree_element*:
        table_tree_elements: List[etree._Element] = list(table_tree)
        comments_tree: etree._Element = table_tree_elements[0]
        assert comments_tree.tag == "TableComments"
        comments: List[TableComment] = list()
        comment_tree: etree._Element
        for comment_tree in comments_tree:
            comment: TableComment = TableComment.xml_parse(comment_tree)
            comments.append(comment)

        # Extract the *parameters* from *parameters_tree_element*:
        parameters: List[Parameter] = list()
        parameters_tree: etree._element = table_tree_elements[1]
        assert parameters_tree.tag == "Parameters"
        parameter_tree: etree._element
        for parameter_tree in parameters_tree:
            parameter: Parameter = Parameter.xml_parse(parameter_tree)
            parameters.append(parameter)

        # Ensure that there are no extra elements:
        assert len(table_tree_elements) == 2

        # Load the extracted information into *table* (i.e. *self*):
        table: Table = self
        table.comments[:] = comments[:]
        table.name = name
        table.parameters[:] = parameters[:]
        table.url = url

    # Table.type_tables_extract():
    @trace(1)
    def type_tables_extract(self, column_tables: List[Dict[str, int]], gui: Gui,
                            tracing: str = "") -> List[Dict[str, int]]:
        # The *re_table* comes from *gui* contains some regular expression for catagorizing
        # values.  The key of *re_table* is the unique *type_name* associated with the regular
        # expression that matches a given type.  The regular expressions are *PreCompiled*
        # to improve efficiency:
        re_table: Dict[str, PreCompiled] = gui.re_table

        # Constuct *type_tables*, which is a list *type_table* that is 1-to-1 with the columns
        # in *column_tables*.  Each *type_table* collects a count of the number of column entries
        # that match a given *type_name*.  If none of the *type_names* match a given *value*,
        # the default *type_name* of "String" is used:
        type_tables: List[Dict[str, int]] = list()
        column_table: Dict[str, int]
        for column_table in column_tables:
            # Create *type_table*, create the "String" *type_name*, and tack it onto *type_tables*:
            type_table: Dict[str, int] = dict()
            type_table["String"] = 0
            type_tables.append(type_table)

            # Sweep through *column_table* characterizing which values match which *type_names*:
            value: str
            count: int
            for value, count in column_table.items():
                type_name: str
                regex: PreCompiled
                match: bool = False
                # Now test *value* against *re* to see if we have a match:
                for type_name, regex in re_table.items():
                    if regex.match(value) is not None:
                        # We have a match, so make sure *type_name* is in *type_table*
                        # update the count appropriately:
                        if type_name in type_table:
                            type_table[type_name] += count
                        else:
                            type_table[type_name] = count
                        match = True

                # If we did not *match*, mark the *value* as a "String" type:
                if not match:
                    type_table["String"] += count
        return type_tables

    # Table.type_letter_get():
    def type_letter_get(self, tracing: str = "") -> str:
        return 'T'

    # Table.xml_file_save():
    def xml_file_save(self, tracing: str = "") -> None:
        # Compute *xml_file_name* and *xml_directory* from *table* (i.e. *self*):
        table: Table = self
        relative_path: str = table.relative_path
        collection: Optional[Collection] = table.collection
        assert isinstance(collection, Collection)
        collection_root: str = collection.collection_root
        xml_file_name: str = os.path.join(collection_root, relative_path + ".xml")
        xml_directory: str = os.path.split(xml_file_name)[0]
        if tracing:
            print("{tracing}relative_path='{relative_path}'")
            print("{tracing}collection_root='{collection_root}'")
            print("{tracing}xml_file_name='{xml_file_name}'")
            print("{tracing}xml_directory='{xml_directory}'")

        # Ensure that *xml_directory* exists:
        os.mkdir(xml_directory)

        # Construct the final *xml_lines*:
        xml_lines: List[str] = list()
        xml_lines.append('<?xml version="1.0"?>')
        table.xml_lines_append(xml_lines, "")
        xml_lines.append("")
        xml_text: str = '\n'.join(xml_lines)

        # Now write *xml_text* out to *xml_file_name*:
        xml_file: IO[str]
        with open(xml_file_name, "w") as xml_file:
            xml_file.write(xml_text)

    # Table.xml_lines_append():
    def xml_lines_append(self, xml_lines: List[str], indent: str, tracing: str = "") -> None:
        # Start appending the `<Table...>` element:
        table: Table = self
        xml_lines.append(f'{indent}<Table '
                         f'name="{Encode.to_attribute(table.name)}" '
                         f'url="{Encode.to_attribute(table.url)}">')

        # Append the `<TableComments>` element:
        xml_lines.append(f'{indent}  <TableComments>')
        table_comments: List[TableComment] = table.comments
        table_comment: TableComment
        next_indent: str = indent + "    "
        for table_comment in table_comments:
            table_comment.xml_lines_append(xml_lines, next_indent)
        xml_lines.append(f'{indent}  </TableComments>')

        # Append the `<Parameters>` element:
        xml_lines.append(f'{indent}  <Parameters>')
        parameters: List[Parameter] = table.parameters
        parameter: Parameter
        for parameter in parameters:
            parameter.xml_lines_append(xml_lines, next_indent)
        xml_lines.append(f'{indent}  </Parameters>')

        # Close out the `<Table>` element:
        xml_lines.append(f'{indent}</Table>')


# Order:
class Order:
    # An Order consists of a list of projects to orders parts for.
    # In addition, the list of vendors to exclude from the ordering
    # process is provided as well.  Vendors are excluded because the
    # shipping costs exceed the part cost savings.  Finally, sometimes
    # you want to order extra stuff, so there is a mechanism for that
    # as well.  Sometimes, you have previous inventory, so that is
    # listed as well.

    # Order.__init__():
    def __init__(self, order_root: str, cads: List[Cad], pandas: "List[Panda]",
                 tracing: str = "") -> None:
        """ *Order*: Initialize *self* for an order. """

        # Ensure that *order_root* exists:
        if not os.path.isdir(order_root):
            try:
                os.makedirs(order_root)
                print(f"Created order directory '{order_root}'.")
            except PermissionError:
                cwd = os.getcwd()
                print(f"Unable to create order directory '{order_root}', using '{cwd}' instead!")
                order_root = cwd
        order_root = os.path.abspath(order_root)
        assert os.path.isdir(order_root), f"'{order_root} is not a directory!'"

        # Create *vendor_searches_root*:
        vendor_searches_root: str = os.path.join(order_root, "vendor_searches")
        if not os.path.isdir(vendor_searches_root):
            os.mkdir(vendor_searches_root)
        assert os.path.isdir(vendor_searches_root)

        # Priorities 0-9 are for vendors with significant minimum
        # order amounts or trans-oceanic shipping costs:
        vendor_priorities: Dict[str, int] = {}
        vendor_priorities["Verical"] = 0
        vendor_priorities["Chip1Stop"] = 1
        vendor_priorities["Farnell element14"] = 2
        vendor_priorities["element14 Asia-Pacific"] = 2
        vendor_priorities["Heilind Electronics - Asia"] = 2

        # Priorities 100-999 are auto assigned for vendors that are
        # not explicitly prioritiezed below.

        # Priorities 1000+ are for explicitly preferred vendors:
        # vendor_priorities["Arrow"] = 1000
        # vendor_priorities["Avnet Express"] = 1001
        # vendor_priorities["Newark"] = 1002
        vendor_priorities["Mouser"] = 1003
        vendor_priorities["Digi-Key"] = 1004

        vendor_minimums: Dict[str, float] = {}

        # Stuff values into *order* (i.e. *self*):
        # order: Order = self
        self.cads: List[Cad] = cads
        self.excluded_vendor_names: Dict[str, None] = {}  # Excluded vendors
        self.final_choice_parts: List[ChoicePart] = []
        self.inventories: List[Inventory] = []      # List[Inventory]: Existing inventoried parts
        self.order_root: str = order_root
        self.pandas: List[Panda] = pandas
        self.projects: List[Project] = []                 # List[Project]
        self.projects_table: Dict[str, Project] = {}      # Dict[Net_File_Name, Project]
        self.selected_vendor_names: List[str] = []
        self.stale: int = 2 * 7 * 24 * 60 * 60  # 2 weeks
        # self.requests: List[Request] = []           # List[Request]: Additional requested parts
        self.vendor_minimums: Dict[str, float] = vendor_minimums
        self.vendor_priorities: Dict[str, int] = vendor_priorities
        self.vendor_priority: int = 10
        self.vendor_searches_root: str = vendor_searches_root

    # Order.__str__():
    def __str__(self) -> str:
        result = "Order()"
        return result

    # Order.project_create():
    def project_create(self, name: str, revision: str, net_file_name: str, count: int,
                       positions_file_name: str = "", tracing: str = "") -> "Project":
        """ *Order*: Create a *Project* containing *name*, *revision*,
            *net_file_name* and *count*. """

        # Grab some values from *order* (i.e. *self*):
        order: Order = self
        projects: List[Project] = order.projects
        projects_table: Dict[str, Project] = order.projects_table

        # Ignore duplicate *net_file_names*:
        if net_file_name in projects_table:
            print(f"Duplicate .net file '{net_file_name}' specified.")
        else:
            # Create the new *project* and stuff into the appropriate data structures:
            project: Project = Project(name, revision, net_file_name, count,
                                       order, positions_file_name)
            projects_table[net_file_name] = project
            projects.append(project)

        return project

    # Order.bom_write():
    @trace(1)
    def bom_write(self, bom_file_name: str, key_function: "Callable[[ChoicePart], Any]",
                  tracing: str = "") -> None:
        """ *Order*: Write out the BOM (Bill Of Materials) for the
            *Order* object (i.e. *self*) to *bom_file_name* ("" for stdout)
            using *key_function* to provide the sort key for each
            *ChoicePart*.
        """
        # Grab some values from *order* (i.e. *self*):
        order: Order = self
        excluded_vendor_names: Dict[str, None] = order.excluded_vendor_names
        final_choice_parts: List[ChoicePart] = order.final_choice_parts
        if tracing:
            print(f"{tracing}len(final_choice_parts)={len(final_choice_parts)}")

        # Sort *final_choice_parts* using *key_function*.
        final_choice_parts.sort(key=key_function)

        # Open *bom_file*
        bom_file: IO[str]
        with (sys.stdout if bom_file_name == "" else open(bom_file_name, "w")) as bom_file:
            # Now generate a BOM summary:
            total_cost: float = 0.0
            choice_part: ChoicePart
            for choice_part in final_choice_parts:
                # Sort the *pose_parts* by *project* followed by reference:
                pose_parts: List[PosePart] = choice_part.pose_parts
                pose_parts.sort(key=lambda pose_part:
                                (pose_part.project.name, pose_part.reference.upper(),
                                 int(text_filter(pose_part.reference, str.isdigit))))

                # Write the first line out to *bom_file*:
                part_name: str = choice_part.name
                part_footprint: str = choice_part.footprint
                part_description: str = choice_part.description
                part_count: int = choice_part.count_get()
                part_references_text: str = choice_part.references_text_get()
                bom_file.write(f"  {part_name}:{part_footprint};{part_description}"
                               f" {part_count}:{part_references_text}\n")

                # Select the vendor_part and associated quantity/cost
                choice_part.select(excluded_vendor_names, True)
                # selected_actual_part = choice_part.selected_actual_part
                selected_vendor_part: Optional[VendorPart] = choice_part.selected_vendor_part
                assert isinstance(selected_vendor_part, VendorPart)
                selected_order_quantity: int = choice_part.selected_order_quantity
                selected_total_cost: float = choice_part.selected_total_cost
                selected_price_break_index: int = choice_part.selected_price_break_index

                # It should be impossible not to have a *VendorPart*:
                if isinstance(selected_vendor_part, VendorPart):
                    # Grab the *vendor_name*:
                    assert isinstance(selected_vendor_part, VendorPart)
                    # vendor_name = selected_vendor_part.vendor_name

                    # Show the *price breaks* on each side of the
                    # *selected_price_breaks_index*:
                    price_breaks: List[PriceBreak] = selected_vendor_part.price_breaks
                    # print("len(price_breaks)={0} selected_price_break_index={1}".
                    #  format(len(price_breaks), selected_price_break_index))
                    selected_price_break: PriceBreak = price_breaks[selected_price_break_index]
                    minimum_index: int = max(selected_price_break_index - 1, 0)
                    maximum_index: int = min(selected_price_break_index + 2, len(price_breaks))
                    price_breaks = price_breaks[minimum_index: maximum_index]

                    # Compute the *price_breaks_text*:
                    price_breaks_text: str = ""
                    price_break: PriceBreak
                    for price_break in price_breaks[minimum_index: maximum_index]:
                        price_breaks_text += "{0}/${1:.3f} ".format(
                          price_break.quantity, price_break.price)

                    # Print out the line:
                    selected_actual_key: Tuple[str, str] = selected_vendor_part.actual_part_key
                    selected_manufacturer_name: str = selected_actual_key[0]
                    selected_manufacturer_part_name: str = selected_actual_key[1]
                    vendor_name: str = selected_vendor_part.vendor_name
                    vendor_part_name: str = selected_vendor_part.vendor_part_name
                    bom_file.write(f"    {vendor_name}:"
                                   f"{vendor_part_name} "
                                   f"[{selected_manufacturer_name}: "
                                   f"{selected_manufacturer_part_name}] "
                                   f"{price_breaks_text}\n")

                    # Print out the result:
                    bom_file.write("        {0}@({1}/${2:.3f})={3:.2f}\n".format(
                      selected_order_quantity,
                      selected_price_break.quantity, selected_price_break.price,
                      selected_total_cost))

                    total_cost += selected_total_cost
                else:
                    # It should be impossible to get here:
                    print(f"{tracing}type(selected_vendor_part)={type(selected_vendor_part)}")

            # Wrap up the *bom_file*:
            bom_file.write(f"{tracing}Total: ${0:.2f}\n".format(total_cost))

    # Order.check():
    @trace(1)
    def check(self, collections: Collections, tracing: str = "") -> None:
        # Check each of the *projects* in *order* (i.e. *self*):
        order: Order = self
        projects: List[Project] = order.projects
        project: Project
        for project in projects:
            project.check(collections)

    # Order.csvs_write():
    @trace(1)
    def csv_write(self, tracing: str = "") -> None:
        """ *Order*: Write out the *Order* object (i.e. *self) BOM (Bill Of Materials)
            for each vendor as a .csv (Comma Seperated Values).
        """
        # Grab some values from *order* (i.e. *self*):
        order: Order = self
        excluded_vendor_names: Dict[str, None] = order.excluded_vendor_names
        final_choice_parts: List[ChoicePart] = order.final_choice_parts

        # Sort *final_choice_parts*:
        final_choice_parts.sort(key=lambda choice_part:
                                (choice_part.selected_vendor_name,
                                 choice_part.selected_total_cost,
                                 choice_part.name))

        vendor_boms: Dict[str, List[str]] = {}
        choice_part: ChoicePart
        for choice_part in final_choice_parts:
            # Sort the *pose_parts* by *project* followed by reference:
            pose_parts: List[PosePart] = choice_part.pose_parts
            pose_parts.sort(key=lambda pose_part:
                            (pose_part.project.name, pose_part.reference.upper(),
                             int(text_filter(pose_part.reference, str.isdigit))))

            # Select the vendor_part and associated quantity/cost
            choice_part.select(excluded_vendor_names, True)
            selected_actual_part: Optional[ActualPart] = choice_part.selected_actual_part
            selected_vendor_part: Optional[VendorPart] = choice_part.selected_vendor_part
            selected_order_quantity: int = choice_part.selected_order_quantity

            if selected_vendor_part is not None and selected_actual_part is not None:
                # Grab the *vendor_name* and *vendor_part_name*:
                vendor_name: str = selected_vendor_part.vendor_name
                # vendor_part_name = selected_vendor_part.vendor_name

                # Make sure we have a *vendor_bom* line list:
                if vendor_name not in vendor_boms:
                    vendor_boms[vendor_name] = []
                lines: List[str] = vendor_boms[vendor_name]

                # Create *line* and append it to *vendor_bom*:
                line: str = (f'"{selected_order_quantity}",'
                             f'"{selected_vendor_part.vendor_part_name},"'
                             f'"{selected_actual_part.manufacturer_name},"'
                             f'"{selected_actual_part.manufacturer_part_name},"'
                             f'"{choice_part.name}"')
                lines.append(line)

        # Wrap up the *bom_file*:
        order_root: str = order.order_root
        for vendor_name in vendor_boms.keys():
            # Create the *vendor_text*:
            vendor_lines: List[str] = vendor_boms[vendor_name]
            vendor_text: str = '\n'.join(vendor_lines) + '\n'

            # Write *vendor_text* out to *vendor_full_file*:
            vendor_base_name: str = Encode.to_file_name(vendor_name) + ".csv"
            vendor_full_name: str = os.path.join(order_root, vendor_base_name)
            vendor_file: IO[str]
            with open(vendor_full_name, "w") as vendor_file:
                # Write out each line in *lines*:
                print(f"Writing '{vendor_full_name}'")
                vendor_file.write(vendor_text)

    # Order.exclude_vendors_to_reduce_shipping_costs():
    def exclude_vendors_to_reduce_shipping_costs(self, choice_parts: "List[ChoicePart]",
                                                 excluded_vendor_names: Dict[str, None],
                                                 reduced_vendor_messages: List[str],
                                                 tracing: str = "") -> None:
        """ *Order*: Sweep through *choice_parts* and figure out which vendors
            to add to *excluded_vendor_names* to reduce shipping costs.
        """
        # First figure out the total *missing_parts*.  We will stop if
        # excluding a vendor increases above the *missing_parts* number:
        order: Order = self
        quad: Quad = order.quad_compute(choice_parts, excluded_vendor_names, "")
        missing_parts: int = quad[0]

        # Sweep through and figure out what vendors to order from:
        done: bool = False
        while not done:
            # Get the base cost for the current *excluded_vendor_names*:
            base_quad: Quad = \
              order.quad_compute(choice_parts, excluded_vendor_names, "")
            # print(">>>>base_quad={0}".format(base_quad))

            # If the *base_missing_parts* increases, we need to stop because
            # excluding additional vendors will cause the order to become
            # incomplete:
            base_missing_parts: int = base_quad[0]
            if base_missing_parts > missing_parts:
                break

            # Grab *base_cost*:
            base_cost: float = base_quad[1]

            # Figure out what vendors are still available for *choice_parts*:
            base_vendor_names: List[str] = order.vendor_names_get(choice_parts,
                                                                  excluded_vendor_names)
            # print("base: {0} {1}".format(base_cost, base_vendor_names))

            # For small designs, sometimes the algorithm will attempt to
            # throw everything out.  The test below makes sure we always
            # have one last remaining vendor:
            if len(base_vendor_names) <= 1:
                break

            # Iterate through *vendor_names*, excluding one *vendor_name*
            # at a time:
            trial_quads: List[Quad] = []
            for vendor_name in base_vendor_names:
                # Create *trial_excluded_vendor_names* which is a copy
                # of *excluded_vendor_names* plus *vendor_name*:
                trial_excluded_vendor_names: Dict[str, None] = dict(excluded_vendor_names)
                trial_excluded_vendor_names[vendor_name] = None

                # Get the base cost for *trial_excluded_vendor_names*
                # and tack it onto *trial_quads*:
                trial_quad: Quad = order.quad_compute(choice_parts, trial_excluded_vendor_names,
                                                      vendor_name)
                trial_quads.append(trial_quad)

                # For debugging only:
                # trial_cost = trial_quad[0]
                # trial_vendor_name = trial_quad[1]
                # print("    {0:.2f} with {1} excluded".
                #  format(trial_cost, trial_vendor_name))

            # Sort the *trial_quads* to bring the most interesting one to the front:
            trial_quads.sort(key=lambda quad: (quad[0], quad[1]))
            # For debugging:
            # for trial_quad in trial_quads:
            #        print("   {0}".format(trial_quad))

            # Quickly ignore all vendors that have zero cost savings:
            while len(trial_quads) >= 2:
                # We want to ensure that *trial_quads* always has at least 2
                # entries for so that the next step after this loop will be
                # guaranteed to have at least one entry in *trial_quads*:
                lowest_quad = trial_quads[0]
                lowest_cost = lowest_quad[1]
                lowest_vendor_name = lowest_quad[3]
                savings = lowest_cost - base_cost
                if savings == 0.0:
                    # This vendor offers no savings; get rid of the vendor:
                    # print("trail_quads[0]={0}".format(trial_quads))
                    reduced_vendor_messages.append("Excluding '{0}': saves nothing\n".format(
                                                   lowest_vendor_name, savings))
                    excluded_vendor_names[lowest_vendor_name] = None
                    del trial_quads[0]
                else:
                    # We are done skipping over zero *savings*:
                    break
            assert len(trial_quads) >= 1

            # Grab some values from *lowest_quad*:
            lowest_quad = trial_quads[0]
            lowest_cost = lowest_quad[1]
            lowest_vendor_name = lowest_quad[3]
            # lowest_vendor_name = text_filter(lowest_vendor_name, str.isprintable)
            savings = lowest_cost - base_cost
            print("      Price is ${0:.2f} when '{1}' is excluded".
                  format(lowest_cost, lowest_vendor_name))

            # We use $15.00 as an approximate minimum shipping cost.
            # If the savings is less that the shipping cost, we exclude
            # the vendor:
            if savings < 15.0 and len(trial_quads) >= 2 and lowest_vendor_name != "Digi-Key":
                # The shipping costs are too high and there at least one
                # vendor left; exclude this vendor:
                message: str = ("Excluding '{0}': only saves {1:.2f}".
                                format(lowest_vendor_name, savings))
                reduced_vendor_messages.append(message + '\n')
                if tracing:
                    print(message)
                excluded_vendor_names[lowest_vendor_name] = None
            else:
                # We are done when *lowest_quad* is worth shipping:
                # print("lowest_cost={0:.2f}".format(lowest_cost))
                done = True

    # Order.exclude_vendors_with_high_minimums():
    def exclude_vendors_with_high_minimums(self, choice_parts: "List[ChoicePart]",
                                           excluded_vendor_names: Dict[str, None],
                                           reduced_vendor_messages: List[str],
                                           tracing: str = "") -> None:
        """ *Order*: Sweep through *choice* parts and figure out if the
            vendors with large minimum orders can be dropped:
        """
        # Grab table of *vendor_minimums* from *order*:
        order: Order = self
        vendor_minimums: Dict[str, float] = order.vendor_minimums

        # Now visit each vendor a decide if we should dump them because
        # they cost too much:
        vendor_name: str
        for vendor_name in vendor_minimums.keys():
            # Grab the *vendor_minimum_cost*:
            vendor_minimum_cost: float = vendor_minimums[vendor_name]

            # Compute *vendor_total_cost* by visiting each *choice_part*
            # to figure out if it has be selected to from *vendor_name*:
            vendor_total_cost = 0.0
            for choice_part in choice_parts:
                choice_part.select(excluded_vendor_names)
                if choice_part.selected_vendor_name == vendor_name:
                    vendor_total_cost += choice_part.selected_total_cost

            # If the amount of order parts does not exceed the minimum,
            # exclude *vendor_name*:
            if vendor_total_cost < vendor_minimum_cost:
                excluded_vendor_names[vendor_name] = None
                reduced_vendor_messages.append(
                    f"{tracing}Excluding '{vendor_name}': needed order {vendor_total_cost}"
                    f" < minimum order {vendor_minimum_cost}\n")

    # Order.final_choice_parts_compute():
    @trace(1)
    def final_choice_parts_compute(self, collections: Collections,
                                   tracing: str = "") -> "List[ChoicePart]":
        """ *Order*: Return a list of final *ChoicePart* objects to order
            for the the *Order* object (i.e. *self*).  This routine also
            has the side effect of looking up the vendor information for
            each selected *ChoicePart* object.
        """
        # Grab the some values from *order* (i.e. *self*):
        order: Order = self
        projects: List[Project] = order.projects
        excluded_vendor_names: Dict[str, None] = order.excluded_vendor_names

        # Construct *project_parts_table* table (Dict[name, List[ProjectPart]]) so that every
        # we have a name to a List[ProjectPart] mapping.
        project_parts_table: Dict[str, List[ProjectPart]] = {}
        project_index: int
        project: Project
        for project_index, project in enumerate(projects):
            if tracing:
                print(f"{tracing}Project[{project_index}]:'{project.name}'")

            # Make sure that each *project_part* in *project* is on a list somewhere
            # in the *project_parts_table*:
            project_parts: List[ProjectPart] = project.project_parts
            project_part_index: int
            project_part: ProjectPart
            for project_part_index, project_part in enumerate(project_parts):
                assert isinstance(project_part, ProjectPart), (f"type(project_part)="
                                                               f"{type(project_part)}")
                if tracing:
                    print(f"{tracing}ProjectPart[{project_part_index}]:'{project_part.name}'")
                project_part_name: str = project_part.name
                if project_part_name not in project_parts_table:
                    project_parts_table[project_part_name] = [project_part]
                else:
                    project_parts_table[project_part_name].append(project_part)

        # Now construct the *final_choice_parts* list, where each *choice_part* on
        # the list consisists of a list of *project_parts* and *searches* where
        # all their names match *search_name*:
        final_choice_parts: List[ChoicePart] = []
        pairs: List[Tuple[str, List[ProjectPart]]] = list(project_parts_table.items())
        pairs.sort(key=lambda pair: pair[0])
        search_name: str
        for search_name, project_parts in pairs:
            if tracing:
                print(f"{tracing}search_name='{search_name}'")
            assert len(project_parts) >= 1
            searches: List[Search] = collections.searches_find(search_name)
            if searches:
                assert len(project_parts) >= 1, "Empty project_parts?"
                search: Search
                for search in searches:
                    assert search.name == search_name
                for project_part in project_parts:
                    assert project_part.name == search_name, (f"'{search_name}'!="
                                                              f"'{project_part.name}'")
                choice_part: ChoicePart = ChoicePart(search_name, project_parts, searches)
                final_choice_parts.append(choice_part)
            else:
                print(f"{tracing}Could not find a search that matches part '{search_name}'")

        # Now load the associated *actual_parts* into each *choice_part* from *final_choice_parts*:
        for choice_part in final_choice_parts:
            # Refresh the vendor part cache for each *actual_part*:
            new_actual_parts: List[ActualPart] = collections.actual_parts_lookup(choice_part)

            # Get reasonably up-to-date pricing and availability information about
            # each *ActualPart* in actual_parts.  *order* is needed to loccate where
            # the cached information is:
            choice_part_name: str = choice_part.name
            choice_part.vendor_parts_refresh(new_actual_parts, order, choice_part_name)

        # Stuff *final_choice_parts* back into *order*:
        final_choice_parts.sort(key=lambda final_choice_part: final_choice_part.name)
        order.final_choice_parts = final_choice_parts

        final_choice_part: ChoicePart
        for final_choice_part in final_choice_parts:
            final_choice_part.select(excluded_vendor_names, True)

        if False:
            # Old code:

            # Grab some values from *project*:
            pose_parts = project.all_pose_parts
            project_parts = project.project_parts
            project_parts_table = project.project_parts_table

            # Sort *pose_parts* by letters first followed by integers:
            pose_parts.sort(key=lambda pose_part: (
                             text_filter(pose_part.reference, str.isalpha).upper(),
                             int(text_filter(pose_part.reference, str.isdigit))))

            choice_parts_table = None
            assert False
            for project_part_index, project_part in enumerate(project_parts):
                # Grab some values from *project_part*:
                project_part_name = project_part.name

                collection = None
                assert False
                searches = collection.searches_find(project_part_name)
                choice_part = ChoicePart()
                choice_parts = project_part.choice_parts()
                for choice_part_index, choice_part in enumerate(choice_parts):
                    # Do some consistency checking:
                    choice_part_name = choice_part.name
                    assert isinstance(choice_part, ChoicePart), ("Not a choice part "
                                                                 f"'{choice_part_name}'")
                    if tracing:
                        print(f"{tracing}  ChoicePart[{choice_part_index}]:'{choice_part_name}'")

                    # Make sure *choice_part* is in *choice_parts_table*
                    # exactly once:
                    if choice_part_name not in choice_parts_table:
                        choice_parts_table[choice_part_name] = choice_part
                    #        print(("Order.final_choice_parts_compute():" +
                    #          " Insert {0:s} into table under key {1} (size={2})").format(
                    #          choice_part, choice_part_name, len(choice_parts_table)))
                    # else:
                    #    print("Order.final_choice_parts_compute(): Key {0} in table".format(
                    #          choice_part_name))

                    # Remember *pose_part* in *choice_part*:
                    # choice_part.pose_part_append(pose_part)

        # Sort by *final_choice_parts* by name and stuff backinto *order*:
        # final_choice_parts = list(choice_parts_table.values())
        # final_choice_parts.sort(key=lambda choice_part: choice_part.name)
        # order.final_choice_parts = final_choice_parts

        # Sweep through *final_choice_parts* and force the associated
        # *PosePart*'s to be in a reasonable order:
        for choice_part in final_choice_parts:
            # Make sure that we only have *ChoicePart* objects:
            assert isinstance(choice_part, ChoicePart)
            choice_part.pose_parts_sort()

        return final_choice_parts

    # Order.footprints_check():
    def footprints_check(self, final_choice_parts: "List[ChoicePart]", tracing: str = "") -> None:
        """ *Order*: Verify that footprints exist. """

        assert False, "Old Code"

        # Visit each *project_part* in all of the *projects*:
        kicad_footprints = {}
        for project in self.projects:
            for pose_part in project.all_pose_parts:
                assert isinstance(pose_part, PosePart)
                project_part = pose_part.project_part
                assert isinstance(project_part, ProjectPart)

                project_part.footprints_check(kicad_footprints)

                # Sweep through aliases:
                # while isinstance(project_part, AliasPart):
                #    alias_part = project_part
                #    project_parts = alias_part.project_parts
                #    # Conceptually, alias parts can reference one or more parts.
                #    # For now, assume it is 1-to-1:
                #    assert len(project_parts) == 1, \
                #      "Multiple Schematic Parts for {0}".format(alias_part.base_name)
                #    project_part = project_parts[0]
                # assert isinstance(project_part, ProjectPart)
                # assert not isinstance(project_part, AliasPart)

                # Dispatch on type of *project_part*.  This really should be done with
                # with a method:
                # if isinstance(project_part, FractionalPart):
                #    fractional_part = project_part
                #    # print("{0} is fractional {1}".
                #    #  format(fractional_part.base_name, fractional_part.kicad_footprint))
                #    kicad_footprints[fractional_part.kicad_footprint] = \
                #      project_part.name
                # elif isinstance(project_part, ChoicePart):
                #    choice_part = project_part
                #    # print("{0} is choice".format(choice_part.base_name))
                #    kicad_footprint = choice_part.kicad_footprint
                #    kicad_footprints[kicad_footprint] = project_part.name
                # else:
                #    print("{0} is ??".format(project_part.base_name))
                #    assert False

        # Now verify that each footprint exists:
        sorted_kicad_footprints = sorted(kicad_footprints.keys())
        for footprint_name in sorted_kicad_footprints:
            footprint_path = "pretty/{0}.kicad_mod".format(footprint_name)
            if not os.path.isfile(footprint_path):
                print("Footprint '{0}' does not exist for '{1}'".
                      format(footprint_path, kicad_footprints[footprint_name]))

    # Order.positions_process():
    def positions_process(self) -> None:
        """ *Order*: Process any Pick and Place `.csv` or `.pos` file.
        """

        order: Order = self
        projects = order.projects
        project: Project
        for project in projects:
            project.positions_process()

    # Order.process():
    @trace(1)
    def process(self, collections: Collections, tracing: str = "") -> None:
        """ *Order*: Process the *Order* object (i.e. *self*.) """
        # Grab some values from *order* (i.e. *self*):
        order: Order = self
        excluded_vendor_names: Dict[str, None] = order.excluded_vendor_names

        # print("=>Order.process()")

        # Collect the messages from each vendor reduction operation into *reduced_vendor_messages*:
        reduced_vendor_messages: List[str] = []

        # We need to contruct a list of *ChoicePart* objects.  This
        # will land in *final_choice_parts* below.   Only *ChoicePart*
        # objects can actually be ordered because they list one or
        # more *ActualPart* objects to choose from.  Both *AliasPart*
        # objects and *FractionalPart* objects eventually get
        # converted to *ChoicePart* objects.  Once we have
        # *final_choice_parts* it can be sorted various different ways
        # (by vendor, by cost, by part_name, etc.)
        final_choice_parts: List[ChoicePart] = order.final_choice_parts_compute(collections)
        if tracing:
            print(f"{tracing}A:len(final_choice_parts)={len(final_choice_parts)}")

        # excluded_vendor_names = order.excluded_vendor_names
        # selected_vendor_names = order.selected_vendor_names
        # if selected_vendor_names is not None:
        #     all_vendor_names = order.vendor_names_get(final_choice_parts, excluded_vendor_names)
        #     for vendor_name in all_vendor_names:
        #        if vendor_name not in selected_vendor_names:
        #                excluded_vendor_names[vendor_name] = None
        # else:
        #     # Now we winnow down the total number of vendors to order from
        #     # to 1) minimize the number of orders that can be messed up
        #     # (i.e. supply chain simplication) and to save shipping costs.
        #     # There are two steps -- throw out vendors with excessive minimum
        #     # order amounts followed by throwing out vendors where the savings
        #     # do not exceed additional shipping costs.
        #     #order.exclude_vendors_with_high_minimums(
        #     #  final_choice_parts, excluded_vendor_names, reduced_vendor_messages)
        #     pass
        if tracing:
            print(f"{tracing}B:len(final_choice_parts)={len(final_choice_parts)}")

        # order.exclude_vendors_with_high_minimums(final_choice_parts, excluded_vendor_names,
        #                                          reduced_vendor_messages)
        order.exclude_vendors_to_reduce_shipping_costs(final_choice_parts, excluded_vendor_names,
                                                       reduced_vendor_messages)
        if tracing:
            print(f"{tracing}C:len(final_choice_parts)={len(final_choice_parts)}")

        # Write out *reduced_vendor_messages* to a report file:
        order_root: str = order.order_root
        reduced_vendor_messages_file_name = os.path.join(order_root, "vendor_reduction_report.txt")
        reduced_vendor_messages_file: IO[str]
        with open(reduced_vendor_messages_file_name, "w") as reduced_vendor_messages_file:
            reduced_vendor_message: str
            for reduced_vendor_message in reduced_vendor_messages:
                reduced_vendor_messages_file.write(reduced_vendor_message)
        if tracing:
            print(f"{tracing}D:len(final_choice_parts)={len(final_choice_parts)}")

        # Let the user know how many vendors were eliminated:
        reduced_vendor_messages_size: int = len(reduced_vendor_messages)
        if reduced_vendor_messages_size >= 1:
            print(f"{tracing}{reduced_vendor_messages_size} vendors eliminated.  "
                  f"See '{reduced_vendor_messages_file_name}' file for why.")
        if tracing:
            print(f"{tracing}E:len(final_choice_parts)={len(final_choice_parts)}")

        # Check for missing footprints:
        # order.footprints_check(final_choice_parts)
        # order.positions_process()

        if tracing:
            print(f"{tracing}F:len(final_choice_parts)={len(final_choice_parts)}")
        # Print out the final selected vendor summary:
        order.summary_print(final_choice_parts, excluded_vendor_names)

        # Generate the bom file reports for *self.final_choice_parts*:
        order.final_choice_parts = final_choice_parts
        order.bom_write(os.path.join(order_root, "bom_by_price.txt"), lambda choice_part:
                        (choice_part.selected_total_cost,
                         choice_part.selected_vendor_name,
                         choice_part.name))
        order.bom_write(os.path.join(order_root, "bom_by_vendor.txt"), lambda choice_part:
                        (choice_part.selected_vendor_name,
                         choice_part.selected_total_cost,
                         choice_part.name))
        order.bom_write(os.path.join(order_root, "bom_by_name.txt"), lambda choice_part:
                        (choice_part.name,
                         choice_part.selected_vendor_name,
                         choice_part.selected_total_cost))
        order.csv_write()

        # Write a part summary file for each project:
        project: Project
        for project in order.projects:
            project.assembly_summary_write(final_choice_parts, order)

        # Now generate a BOM summary:
        if False:
            total_cost = 0.0
            for choice_part in final_choice_parts:
                # Open *csv_file* for summary spread sheet:
                csv_file = open(os.path.join(order_root, "order.csv"), "w")
                # Output a one line header
                csv_file.write("Quantity,Vendor Part Name,Reference\n")

                # Select the vendor_part and associated quantity/cost
                choice_part.select(excluded_vendor_names, False)
                # selected_actual_part = choice_part.selected_actual_part
                selected_vendor_part = choice_part.selected_vendor_part
                selected_order_quantity = choice_part.selected_order_quantity
                selected_total_cost = choice_part.selected_total_cost
                selected_price_break_index = choice_part.selected_price_break_index

            # Per vendor order lists need some more thought:
            if isinstance(selected_vendor_part, VendorPart):
                vendor_name = selected_vendor_part.vendor_name
                assert False
                vendor_files = None
                if vendor_name not in vendor_files:
                    # csv_vendor_name = vendor_name.replace(' ', '_').replace('&', '+')
                    csv_file = open("{0}.csv".format(vendor_name), "wa")
                    vendor_files[vendor_name] = csv_file
                else:
                    csv_file = vendor_files[vendor_name]

                # Print out the *price breaks* on each side of the
                # *selected_price_breaks_index*:
                price_breaks = selected_vendor_part.price_breaks
                # print("len(price_breaks)={0} selected_price_break_index={1}".
                #  format(len(price_breaks), selected_price_break_index))
                # selected_price_break = price_breaks[selected_price_break_index]
                minimum_index = max(selected_price_break_index - 1, 0)
                maximum_index = min(selected_price_break_index + 2, len(price_breaks))
                price_breaks = price_breaks[minimum_index: maximum_index]

                # Compute the *price_breaks_text*:
                price_breaks_text = ""
                for price_break in price_breaks[minimum_index: maximum_index]:
                    price_breaks_text += "{0}/${1:.3f} ".format(
                      price_break.quantity, price_break.price)

                # Print out the line:
                # print("    {0}:{1} {2}".format(
                #  selected_vendor_part.vendor_name,
                #  selected_vendor_part.vendor_part_name, price_breaks_text))

                # Print out the result:
                # print("        {0}@({1}/${2:.3f})={3:.2f}".format(
                #  selected_order_quantity,
                #  selected_price_break.quantity, selected_price_break.price,
                #  selected_total_cost))

                total_cost += selected_total_cost

                # Write out another line in the *csv_file*:
                csv_file.write("{0},{1},{2}\n".format(
                  selected_order_quantity,
                  selected_vendor_part.vendor_part_name,
                  choice_part.name))

            # Close all the vendor files:
            for csv_file in vendor_files.values():
                csv_file.close()

    # Order.quad_compute():
    def quad_compute(self, choice_parts: "List[ChoicePart]",
                     excluded_vendor_names: Dict[str, None],
                     excluded_vendor_name: str, trace: str = "") -> Quad:
        """ *Order*: Return quad tuple of the form:
               (*missing_parts*, *total_cost*,
                *vendor_priority*, *excluded_vendor_name*) where:
            * *missing_parts* is number of parts that can not be fullfilled.
            * *total_cost* is the sum the parts costs for all *ChoicePart*
              objects in *choice_parts* that do not use any vendors in
              *excluded_vendor_names*.
            * *vendor_priority* is a sort order for *excluded_vendor_name*.
            * *excluded_vendor_name* is the current vendor that is excluded.
            The returned key is structured to sort so that most interesting
            vendor to exclude sorts to the first item.
        """
        order: Order = self
        missing_parts: int = 0
        total_cost: float = 0.0
        choice_part: ChoicePart
        for choice_part in choice_parts:
            # Perform the vendor selection excluding all vendors in
            # *excluded_vendor_names*:
            missing_parts += choice_part.select(excluded_vendor_names, False)

            # Grab some values out of *choice_part*:
            # selected_vendor_name = choice_part.selected_vendor_name
            selected_total_cost = choice_part.selected_total_cost

            # Keep a running total of everything:
            total_cost += selected_total_cost

        # Figure out *vendor_priority* for *excluded_vendor_name*:
        vendor_priorities: Dict[str, int] = order.vendor_priorities
        if excluded_vendor_name in vendor_priorities:
            # Priority already assigned to *excluded_vendor_name*:
            vendor_priority = vendor_priorities[excluded_vendor_name]
        else:
            # Assigned a new priority for *excluded_vendor_name*:
            vendor_priority = order.vendor_priority
            vendor_priorities[excluded_vendor_name] = vendor_priority
            order.vendor_priority += 1

        # Return the final *quad*:
        quad: Quad = (missing_parts, total_cost, vendor_priority, excluded_vendor_name)
        return quad

    # Order.summary_print():
    @trace(1)
    def summary_print(self, choice_parts: "List[ChoicePart]",
                      excluded_vendor_names: Dict[str, None], tracing: str = "") -> None:
        """ *Order*: Print a summary of the selected vendors.
        """
        # Let the user know what we winnowed the vendor list down to:
        final_vendor_names: List[str] = self.vendor_names_get(choice_parts, excluded_vendor_names)

        # Print the final *total_cost*:
        total_cost: float = 0.0
        choice_part: ChoicePart
        for choice_part in choice_parts:
            choice_part.select(excluded_vendor_names, False)
            total_cost += choice_part.selected_total_cost
        print("Total Cost: ${0:.2f}".format(total_cost))

        # Print out the sub-totals for each vendor:
        print("Final selected vendors:")
        venodr_name: str
        for vendor_name in final_vendor_names:
            vendor_cost: float = 0.0
            for choice_part in choice_parts:
                if choice_part.selected_vendor_name == vendor_name:
                    vendor_cost += choice_part.selected_total_cost
            print("    {0}: ${1:.2f}".format(vendor_name, vendor_cost))

    # Order.vendor_exclude():
    def vendor_exclude(self, vendor_name: str) -> None:
        """ *Order*: Exclude *vendor_name* from the *Order* object (i.e. *self*)
        """
        # Mark *vendor_name* from being selectable:
        self.excluded_vendor_names[vendor_name] = None

    # Order.vendor_names_get():
    def vendor_names_get(self, choice_parts: "List[ChoicePart]",
                         excluded_vendor_names: Dict[str, None]) -> List[str]:
        """ *Order*: Return all possible vendor names for *choice_parts*:
        """
        # Load up *vendor_names_table*:
        vendor_names_table: Dict[str, None] = {}
        choice_part: ChoicePart
        for choice_part in choice_parts:
            choice_part.vendor_names_load(vendor_names_table, excluded_vendor_names)

        # Return the sorted list of vendor names:
        return list(sorted(vendor_names_table.keys()))

    # Order.vendors_select():
    def vendors_select(self, selected_vendor_names: List[str]) -> None:
        """ *Order*: Force the selected vendors for the *order* object (i.e. *self*)
            to *selected_vendors.
        """

        # Stuff *selected_vendor_names* into *order* (i.e. *self*):
        order: Order = self
        order.selected_vendor_names = selected_vendor_names


# Panda:
class Panda:
    # Panda stands for Pricing AND Availability:

    # Panda.__init__():
    def __init__(self, name: str, tracing: str = "") -> None:
        # Stuff values into *panda* (i.e. *self*):
        # panda = self
        self.name = name

    # Panda.__str__():
    def __str__(self) -> str:
        panda: Panda = self
        name: str = "??"
        if hasattr(panda, "name"):
            name = panda.name
        return f"Panda({name})"

    # Panda.vendor_parts_lookup():
    def vendor_parts_lookup(self, actual_part, part_name, tracing: str = "") -> "List[VendorPart]":
        panda: Panda = self
        class_name: str = panda.__class__.__name__
        assert False, f"{class_name}.vendor_parts_lookup() has not been implemented"
        return list()


# Parameter():
class Parameter:

    # Parameter.__init__():
    def __init__(self, name: str, type: str, csv: str, csv_index: int, default: str, optional: bool,
                 comments: List[ParameterComment], enumerations: List[Enumeration]) -> None:
        # Load values into *parameter* (i.e. *self*):
        # parameter: Parameter = self
        self.comments: List[ParameterComment] = comments
        self.csv: str = csv
        self.csv_index: int = csv_index
        self.default: str = default
        self.enumerations: List[Enumeration] = enumerations
        self.name: str = name
        self.optional: bool = optional
        self.type: str = type
        self.use: bool = False

    # Parameter.__equ__():
    def __eq__(self, parameter2: object) -> bool:
        # print("=>Parameter.__eq__()")

        # Compare each field of *parameter1* (i.e. *self*) with the corresponding field
        # of *parameter2*:
        equal: bool = False
        if isinstance(parameter2, Parameter):
            parameter1: Parameter = self
            name_equal: bool = (parameter1.name == parameter2.name)
            default_equal: bool = (parameter1.default == parameter2.default)
            type_equal: bool = (parameter1.type == parameter2.type)
            optional_equal: bool = (parameter1.optional == parameter2.optional)
            comments_equal: bool = (parameter1.comments == parameter2.comments)
            enumerations_equal: bool = (parameter1.enumerations == parameter2.enumerations)
            equal = (name_equal and default_equal and type_equal and
                     optional_equal and comments_equal and enumerations_equal)

        # Debugging code:
        # print("name_equal={0}".format(name_equal))
        # print("default_equal={0}".format(default_equal))
        # print("type_equal={0}".format(type_equal))
        # print("optional_equal={0}".format(optional_equal))
        # print("comments_equal={0}".format(comments_equal))
        # print("enumerations_equal={0}".format(enumerations_equal))
        # print("<=Parameter.__eq__()=>{0}".format(all_equal))

        return equal

    # Parameter.xml_lines_append():
    def xml_lines_append(self, xml_lines: List[str], indent: str) -> None:
        # Grab some values from *parameter* (i.e. *self*):
        parameter: Parameter = self
        csv: str = parameter.csv
        csv_index: int = parameter.csv_index
        default: str = parameter.default
        name: str = parameter.name
        optional: bool = parameter.optional
        type: str = parameter.type

        # Start with the `<Parameter ...> XML element:
        optional_text: str = ' optional="true"' if optional else ''
        default_text: str = ' default="{default}"' if default else ''
        xml_line: str = (f'{indent}<Parameter'
                         f' name="{name}"'
                         f' type="{type}"'
                         f' csv="{csv}"'
                         f' csv_index="{csv_index}"'
                         f'{default_text}'
                         f'{optional_text}'
                         '>')
        xml_lines.append(xml_line)

        # Append all of the comments*:
        comments: List[ParameterComment] = parameter.comments
        comment: ParameterComment
        comment_indent = indent + "    "
        for comment in comments:
            xml_lines.append(f'{indent}  <ParameterComments>')
            comment.xml_lines_append(xml_lines, comment_indent)
            xml_lines.append(f'{indent}  </ParameterComments>')

        # Append all of the *enumerations*:
        enumerations: List[Enumeration] = parameter.enumerations
        if enumerations:
            xml_lines.append(f'{indent}  <Enumerations>')
            enumeration_indent = indent + "    "
            enumeration: Enumeration
            for enumeration in enumerations:
                enumeration.xml_lines_append(xml_lines, enumeration_indent)
            xml_lines.append(f'{indent}  </Enumerations>')

        # Close out with the `</Parameter>` XML element:
        xml_lines.append(f'{indent}</Parameter>')

    # Parameter.xml_parse():
    @staticmethod
    def xml_parse(parameter_tree: etree._Element) -> "Parameter":
        assert parameter_tree.tag == "Parameter"
        attributes_table: Dict[str, str] = parameter_tree.attrib
        assert "name" in attributes_table
        name: str = attributes_table["name"]
        assert "type" in attributes_table
        type: str = attributes_table["type"].lower()
        optional: bool = False
        if "optional" in attributes_table:
            optional_text: str = attributes_table["optional"].lower()
            assert optional_text in ("true", "false")
            optional = (optional_text == "true")
        csv: str = attributes_table["csv"] if "csv" in attributes_table else ""
        csv_index: int = (int(attributes_table["csv_index"])
                          if "csv_index" in attributes_table else -1)
        default: str = attributes_table["default"] if "default" in attributes_table else ""
        parameter_tree_elements: List[etree._Element] = list(parameter_tree)
        assert parameter_tree_elements
        comments_tree: etree._Element = parameter_tree_elements[0]
        assert comments_tree.tag == "ParameterComments"
        assert not comments_tree.attrib
        comments: List[ParameterComment] = list()
        comment_tree: etree._Element
        for comment_tree in comments_tree:
            comment: ParameterComment = ParameterComment.xml_parse(comment_tree)
            comments.append(comment)

        enumerations: List[Enumeration] = list()
        if type == "enumeration":
            assert len(parameter_tree_elements) == 2
            enumerations_tree: etree._Element = parameter_tree_elements[1]
            assert len(enumerations_tree.attrib) == 0
            assert enumerations_tree.tag == "Enumerations"
            assert len(enumerations_tree) >= 1
            for enumeration_tree in enumerations_tree:
                enumeration: Enumeration = Enumeration.xml_parse(enumeration_tree)
                enumerations.append(enumeration)
        else:
            assert len(parameter_tree_elements) == 1

        # Finally, create *parameter* and return it:
        parameter: Parameter = Parameter(name, type, csv, csv_index,
                                         default, optional, comments, enumerations)
        return parameter


# PosePart:
class PosePart:
    # A PosePart basically specifies the binding of a ProjectPart
    # and its associated schemtatic reference.  Reference strings must
    # be unique for a given project.

    # PosePart.__init__():
    def __init__(self, project: "Project", project_part: "ProjectPart", reference: str,
                 comment: str, tracing: str = "") -> None:
        """ Initialize *PosePart* object (i.e. *self*) to contain *project*,
            *project_part*, *reference*, and *comment*.
        """
        # Load up *pose_part* (i.e. *self*):
        # pose_part: PosePart = self
        self.project: Project = project
        self.project_part: ProjectPart = project_part
        self.reference: str = reference
        self.comment: str = comment
        self.install: bool = (comment != "DNI")

    # PosePart.__str__():
    def __str__(self) -> str:
        reference: str = "??"
        pose_part: PosePart = self
        if hasattr(pose_part, "reference"):
            reference = pose_part.reference
        return f"PosePart('{reference}')"

    # PosePart.check():
    def check(self, collections: Collections, tracing: str = "") -> None:
        # Grab some values from *pose_part* (i.e. *self*):
        pose_part: PosePart = self
        reference: str = pose_part.reference
        project: Project = pose_part.project
        project_name: str = project.name

        # Check the underlying *project_part*:
        project_part: ProjectPart = pose_part.project_part
        search_name: str = project_part.name
        collections.check(search_name, project_name, reference)


# PositionRow:
class PositionRow:
    """ PositionRow: Represents one row of data for a *PositionsTable*: """

    # PositionRow.__init__():
    def __init__(self, reference: str, value: str, package: str, x: float, y: float,
                 rotation: float, feeder_name: str, pick_dx: float, pick_dy: float,
                 side: str, part_height: float, tracing: str = "") -> None:
        """ *PositionRow*: ...
        """

        # Load up *position_row* (i.e. *self*):
        # position_row: PositionRow = self
        self.package: str = package
        self.part_height: float = part_height
        self.feeder_name: str = feeder_name
        self.rotation: float = rotation
        self.reference: str = reference
        self.side: str = side
        self.value: str = value
        self.x: float = x - pick_dx
        self.y: float = y - pick_dy
        self.pick_dx: float = pick_dx
        self.pick_dy: float = pick_dx

    # PositionRow:__str__():
    def __str__(self) -> str:
        reference = "??"
        position_row: PositionRow = self
        if hasattr(position_row, "reference"):
            reference = position_row.reference
        return f"PositionRow('{reference}')"

    # PositionsRow.as_strings():
    def as_strings(self, mapping: List[int], feeders: Dict[str, None],
                   tracing: str = "") -> List[str]:
        """ *PositionsRow*: Return a list of formatted strings.

        The arguments are:
        * *mapping*: The order to map the strings in.
        """

        positions_row: PositionRow = self
        value: str = positions_row.value
        if value not in feeders:
            print(f"There is no feeder for '{value}'")
        row_strings = [""] * 7
        row_strings[mapping[0]] = positions_row.reference
        row_strings[mapping[1]] = positions_row.value
        row_strings[mapping[2]] = positions_row.package
        row_strings[mapping[3]] = "{0:.4f}".format(positions_row.x)
        row_strings[mapping[4]] = "{0:.4f}".format(positions_row.y)
        row_strings[mapping[5]] = "{0:.4f}".format(positions_row.rotation)
        row_strings[mapping[6]] = positions_row.side
        return row_strings

    # PositionsRow.part_rotate():
    def part_rotate(self, rotation_adjust: float, tracing: str = "") -> None:
        """ *PostitionRow*: """
        position_row: PositionRow = self
        rotation: float = position_row.rotation
        rotation -= rotation_adjust
        while rotation < 0.0:
            rotation += 360.0
        while rotation > 360.0:
            rotation -= 360.0
        position_row.rotation = rotation

    # PositionsRow.translate():
    def translate(self, dx: float, dy: float) -> None:
        """
        """

        position_row: PositionRow = self
        position_row.x += dx
        position_row.y += dy


# PositionsTable:
class PositionsTable:
    def __init__(self, positions_file_name: str, tracing: str = "") -> None:
        # positions_table: PositionsTable = self
        self.positions_file_name: str = positions_file_name

#    """ PositionsTable: Represents a part positining table for a Pick and Place machine. """
#
#    # PositionsTable.__init__():
#    def __init__(self, file_name: str, database):
#        """ *PositionsTable*: Initialize the *PositionsTable* object read in from *file_name*:
#
#        The arguments are:
#        * *file_name*: The file name to read positions table from.  *file_name* must
#          have one of the following suffixes:
#          * `.csv`: A comma separated value format.
#          * `.pos`: A text file with the columns separated by one or more spaces.
#            Usually the columns are aligned virtically when viewe using a fixed
#            pitch font.
#        """
#
#        # Verify argument types:
#        assert isinstance(file_name, str) and (
#          file_name.endswith(".csv") or file_name.endswith(".pos"))
#
#        #
#        positions_table = self
#        comments = list()
#        heading_indices = dict()
#        rows = list()
#        row_table = dict()
#        mapping = list()
#        trailers = list()
#        headings_line = None
#        headings = list()
#        headings_size = 0
#        part_heights = dict()
#
#        # Process `.pos` and `.csv` *file_name*'s differently:
#        if file_name.endswith(".pos"):
#            # `.pos` suffix:
#
#            # Read in *file_name* and break it into a *lines* list with no carriage returns:
#            with open(file_name, "r") as positions_file:
#                content = positions_file.read().replace('\r', "")
#                lines = content.split('\n')
#
#                # Start parsing the file *lines*:
#                for line_number, line in enumerate(lines):
#                    # Dispatch on the beginning of the *line*:
#                    if line.startswith("##"):
#                        # Lines starting with "##" or "###" are just *comments*:
#                        if headings_size <= 0:
#                            comments.append(line)
#                        else:
#                            trailers.append(line)
#                        # print("comment='{0}'".format(line))
#                    elif line.startswith("# "):
#                        # Lines that start with "# " are the column headings:
#                        assert headings_size <= 0
#                        headings_line = line
#                        headings = line[2:].split()
#                        headings_size = len(headings)
#                        assert headings_size > 0
#                        for heading_index, heading in enumerate(headings):
#                            heading_indices[heading] = heading_index
#                            # print("key='{0}' index={1}".format(key, heading_index))
#
#                        # Create the *mapping* used for formatting the output table:
#                        heading_keys = ("Ref", "Val", "Package", "PosX", "PosY", "Rot", "Side")
#                        for heading in heading_keys:
#                            heading_index = heading_indices[heading]
#                            mapping.append(heading_index)
#                        # print("mapping={0}".format(mapping))
#                    else:
#                        # Assume that everything else is a row of data:
#                        columns = line.split()
#                        columns_size = len(columns)
#                        if columns_size == headings_size:
#                            # print("row={0}".format(row))
#                            reference = columns[heading_indices["Ref"]]
#                            value = columns[heading_indices["Val"]]
#                            value = value.replace('\\', "")
#                            part = database.lookup(value)
#                            if isinstance(part, ChoicePart):
#                                choice_part = part
#                                feeder_name = choice_part.feeder_name
#                                part_height = choice_part.part_height
#                                pick_dx = choice_part.pick_dx
#                                pick_dy = choice_part.pick_dy
#                                if isinstance(feeder_name, str) and isinstance(part_height, float):
#                                    # print("'{0}'=>'{1}''".format(value, feeder_name))
#                                    value = feeder_name
#                                    part_heights[value] = part_height
#                                # print("part_heights['{0}'] = {1}".format(value, part_height))
#                            elif isinstance(part, AliasPart):
#                                alias_part = part
#                                feeder_name = alias_part.feeder_name
#                                part_height = alias_part.part_height
#                                pick_dx = alias_part.pick_dx
#                                pick_dy = alias_part.pick_dy
#                                if isinstance(feeder_name, str) and isinstance(part_height, float):
#                                    # print("'{0}'=>'{1}''".format(value, feeder_name))
#                                    value = feeder_name
#                                    part_heights[value] = part_height
#                                # print("part_heights['{0}'] = {1}".format(value, part_height))
#                            package = columns[heading_indices["Package"]]
#                            x = float(columns[heading_indices["PosX"]])
#                            y = float(columns[heading_indices["PosY"]])
#                            rotation = float(columns[heading_indices["Rot"]])
#                            side = columns[heading_indices["Side"]]
#                            if isinstance(part_height, float):
#                                row = PositionRow(reference, value, package, x, y, rotation,
#                                                  feeder_name, pick_dx, pick_dy, side, part_height)
#                                rows.append(row)
#                                row_table[reference] = row
#                            else:
#                                print("Part '{0}' does not have a part_height".format(value))
#                        elif columns_size != 0:
#                            assert False, "Row/Header mismatch {0} {0}".format(row)  # , headers)
#        elif file_name.endswith(".csv"):
#            assert ".csv reader not implemented yet."
#        else:
#            assert "Bad file suffix for file: '{0}'".format(file_name)
#
#        feeders = {
#         "1uF":        "E1",
#         "2N7002":     "E2",
#         "27K":        "E4",
#         "0":          "E5",
#         "33":         "E7",
#         "4.7uF_?":    "E11",
#         "1.0M":       "E14",
#         "49.9K":      "E16",
#         "200K":       "E19",
#         "BAT54":      "E21",
#         "0.1uF":      "W4",
#         "49.9":       "W6",
#         "20k":        "W7",
#         "330":        "W10",
#         "10K":        "W11",
#         "100":        "W15",
#         "100K":       "W16",
#         "5.1K":       "W17",
#         "GRN_LED":    "W14",
#         "470":        "W20",
#         "10uF":       "W21",
#         "120":        "W22",
#         "4.7k":       "W23",
#         "220":        "W24",
#
#         "33nF":       "E100",
#         "470nF":      "E101",
#         "10nF":       "E102",
#         "NFET_10A":   "E103",
#         "330nF":      "E104",
#         "18V_ZENER":  "E105",
#         "SI8055":     "E106",
#         "MC33883":    "E107",
#         "MCP2562":    "E108",
#         "18V_REG":    "E109",
#         "74HC08":     "E110",
#         "OPTOISO2":   "E111",
#         "5V_REG/LDO": "E112",
#         "3.3V_LDO":   "E113",
#         "FID":        "E114",
#         "10":         "E115",
#        }
#
#        # Write out `feeders.txt`:
#        footprints = database.footprints
#        quintuples = list()
#        for key in feeders.keys():
#            feeder_name = feeders[key]
#            part_height = "{0:.2f}".format(part_heights[key]) if key in part_heights else "----"
#            rotation = int(footprints[key].rotation) if key in footprints else "----"
#            quintuple = (feeder_name[0], int(feeder_name[1:]), key, part_height, rotation)
#            quintuples.append(quintuple)
#        quintuples.sort()
#        order_root = None
#        feeders_file_name = os.path.join(order_root, "feeders.txt")
#        with open(feeders_file_name, "w") as feeders_file:
#            feeders_file.write("Feeder\tHeight\tRotate\tValue\n")
#            feeders_file.write(('=' * 50) + '\n')
#            for quintuple in quintuples:
#                side = quintuple[0]
#                number = quintuple[1]
#                value = quintuple[2]
#                rotation = quintuple[2]
#                part_height = quintuple[3]
#                rotation = quintuple[4]
#                feeders_file.write(f"{side}{number}:\t{part_height}\t{rotation}\t{value}\n")
#
#        # Fill in the value of *positions_table* (i.e. *self*):
#        positions_table.comments = comments
#        positions_table.headings_line = headings_line
#        positions_table.headings = headings
#        positions_table.headings_indices = heading_indices
#        positions_table.feeders = feeders
#        positions_table.file_name = file_name
#        positions_table.mapping = mapping
#        positions_table.rows = rows
#        positions_table.row_table = row_table
#        positions_table.trailers = trailers
#
#    # PositionsTable.footprints_rotate():
#    def footprints_rotate(self, database):
#        """ *Positions_Table: ..."""
#
#        order_root = None
#        positions_table = self
#        file_name = positions_table.file_name
#        footprints = database.footprints
#        rows = positions_table.rows
#        for row_index, row in enumerate(rows):
#            feeder_name = row.feeder_name
#            debugging = False
#            # debugging = package == "DPAK"
#            # print("Row[{0}]: '{1}'".format(row_index, package))
#            if feeder_name in footprints:
#                # We have a match:
#                footprint = footprints[feeder_name]
#                rotation = footprint.rotation
#                if debugging:
#                    print("rotation={0}".format(rotation))
#                if isinstance(rotation, float):
#                    row.part_rotate(rotation)
#                else:
#                    print("Footprint '{0}' does not have a feeder rotation.".format(feeder_name))
#            else:
#                # No match:
#                print("Could not find footprint '{0}' from file '{1}'".
#                      format(feeder_name, file_name))
#        positions_table.write(os.path.join(order_root, file_name))
#
#    # PositionsTable.reorigin():
#    def reorigin(self, reference):
#        """
#        """
#
#        positions = self
#        row_table = positions.row_table
#        if reference in row_table:
#            row = row_table[reference]
#            dx = -row.x
#            dy = -row.y
#            positions.translate(dx, dy)
#
#    # PositionsTable.translate():
#    def translate(self, dx, dy):
#        """
#        """
#
#        positions = self
#        rows = positions.rows
#        for row in rows:
#            row.translate(dx, dy)
#
#    # PositionsTable.write():
#    def write(self, file_name):
#        """ *PositionsTable*: Write out the *PostionsTable* object to *file_name*.
#
#        The arguments are:
#        * *file_name*: specifies the file to write out to.  It must of a suffix of:
#          * `.csv`: Writes the file out in Comma Separated Values format.
#          * `.pos`: Writes the file out as a text file with data separated by spaces.
#        """
#
#        # Verify argument types:
#        assert isinstance(file_name, str)
#        assert len(file_name) >= 4 and file_name[-4:] in (".csv", ".pos")
#
#        # Unpack the *positions_table* (i.e. *self*):
#        positions_table = self
#        comments = positions_table.comments
#        headings_line = positions_table.headings_line
#        headings = positions_table.headings
#        rows = positions_table.rows
#        mapping = positions_table.mapping
#        trailers = positions_table.trailers
#        feeders = positions_table.feeders
#
#        # In order exactly match KiCAD output, the output formatting is adjusted based
#        # on the column heading. *spaces_table* specifies the extra spaces to add to the column.
#        # *aligns_table* specifies whether the data is left justified (i.e. "") or right
#        # justified (i.e. ">"):
#        extras_table = {"Ref": 5, "Val": 0, "Package": 1,
#                        "PosX": 0, "PosY": 0, "Rot": 0, "Side": 0}
#        aligns_table = {"Ref": "", "Val": "", "Package": "",
#                        "PosX": ">", "PosY": ">", "Rot": ">", "Side": ""}
#
#        # Build up the final output as a list of *final_lines*:
#        final_lines = list()
#
#        # Just copy the *comments* and *headings_line* into *final_lines*:
#        final_lines.extend(comments)
#        final_lines.append(headings_line)
#
#        # Dispatch on *file_name* suffix:
#        if file_name.endswith(".pos"):
#            # We have a `.pos` file:
#
#            # Populate *string_rows* with strings containing the data:
#            string_rows = list()
#            for row in rows:
#                string_row = row.as_strings(mapping, feeders)
#                string_rows.append(string_row)
#
#            # Figure out the maximum *sizes* for each column:
#            sizes = [0] * len(headings)
#            for string_row in string_rows:
#                for column_index, column in enumerate(string_row):
#                    sizes[column_index] = max(sizes[column_index], len(column))
#
#            # Convert *aligns_table* into a properly ordered list of *aligns*:
#            aligns = list()
#            for header_index, header in enumerate(headings):
#                sizes[header_index] += extras_table[header]
#                aligns.append(aligns_table[header])
#
#            # Create a *format_string* for outputing each row:
#            format_columns = list()
#            for size_index, size in enumerate(sizes):
#                format_columns.append("{{{0}:{1}{2}}}"
#                  .format(size_index, aligns[size_index], size))
#                # format_columns.append("{" + str(size_index) +
#                #  ":" + aligns[size_index] + str(size) + "}")
#            format_string = "  ".join(format_columns)
#            # print("format_string='{0}'".format(format_string))
#
#            # Now format each *string_row* and append the result to *final_lines*:
#            for string_row in string_rows:
#                final_line = format_string.format(*string_row)
#                final_lines.append(final_line)
#
#            # Tack *trailers* and an empty line onto *final_lines*:
#            final_lines.extend(trailers)
#            final_lines.append("")
#        elif file_name.endswith(".csv"):
#            # File is a `.csv` file:
#            assert False, ".csv file support not implemented yet."
#        else:
#            assert False, ("File name ('{0}') does not have a suffixe of .csv or .pos".
#                           format(file_name))
#
#        # Write *final_lines* to *file_name*:
#        with open(file_name, "w") as output_file:
#            output_file.write("\r\n".join(final_lines))

    # PositionTable.__str__():
    def __str__(self) -> str:
        return "PositionsTable()"


# PriceBreak:
class PriceBreak:
    # A price break is where a the pricing changes:

    # PriceBreak.__init__():
    def __init__(self, quantity: int, price: float) -> None:
        """ *PriceBreak*: Initialize *self* to contain *quantity*
            and *price*.  """
        # Load up *price_break* (i.e. *self*):
        # price_break: PriceBreak = self
        self.quantity: int = quantity
        self.price: float = price
        self.order_quantity: int = 0
        self.order_price: float = 0.00

    # PriceBreak.__eq__():
    def __eq__(self, price_break2: object) -> bool:
        equal: bool = False
        if isinstance(price_break2, PriceBreak):
            price_break1: PriceBreak = self
            equal = (price_break1.quantity == price_break2.quantity and
                     price_break1.price == price_break2.price)
        return equal

    # PriceBreak.__format__():
    def __format__(self, format: str) -> str:
        """ *PriceBreak*: Return the *PriceBreak* object as a human redable string.
        """

        # Grab some values from *price_break* (i.e. *self*):
        price_break: PriceBreak = self
        quantity = price_break.quantity
        price = price_break.price
        result = "{0}/{1}".format(quantity, price)
        # print("Result='{0}'".format(result))
        return result

    # PriceBreak.__lt__():
    def __lt__(self, price_break2: "PriceBreak") -> bool:
        price_break1: PriceBreak = self
        return price_break1.price < price_break2.price

    # PriceBreak.__str__():
    def __str__(self) -> str:
        return "PriceBreak()"

    # PriceBreak.compute():
    def compute(self, needed: int) -> None:
        """ *PriceBreak*: """
        price_break: PriceBreak = self
        price_break.order_quantity = order_quantity = max(needed, price_break.quantity)
        price_break.order_price = order_quantity * price_break.price

    # PriceBreak.xml_lines_append():
    def xml_lines_append(self, xml_lines: List[str], indent: str, tracing: str = "") -> None:
        # Grab some values from *price_break* (i.e. *self*):
        price_break: PriceBreak = self
        quantity: int = price_break.quantity
        price: float = price_break.price

        # Output `<PriceBreak ...>` tag:
        xml_lines.append('{0}<PriceBreak quantity="{1}" price="{2:.6f}"/>'.
                         format(indent, quantity, price))

    # PriceBreak.xml_parse():
    @staticmethod
    def xml_parse(price_break_tree: etree._Element, tracing: str = "") -> "PriceBreak":
        # Grab some the attribute values from *price_break_tree*:
        attributes_table: Dict[str, str] = price_break_tree.attrib
        quantity: int = int(attributes_table["quantity"])
        price: float = float(attributes_table["price"])

        # Create and return the new *PriceBreak* object:
        price_break: PriceBreak = PriceBreak(quantity, price)
        return price_break


# Project:
class Project:
    # Project.__init__():
    def __init__(self, name: str, revision: str, cad_file_name: str, count: int, order: Order,
                 positions_file_name: str = "", tracing: str = "") -> None:
        """ Initialize a new *Project* object (i.e. *self*) containing *name*, *revision*,
            *net_file_name*, *count*, *order*, and optionally *positions_file_name.
        """

        # Load up *project* (i.e. *self*):
        project: Project = self
        self.name: str = name                                  # Project name
        self.revision: str = revision                          # Revision designator
        self.cad_file_name: str = cad_file_name                # Cad/bom file name
        self.count: int = count                                # Number of this project to order
        self.positions_file_name: str = positions_file_name    # Positions Pick and Place file name
        self.order: Order = order                              # Parent *Order*
        self.pose_parts_table: Dict[str, PosePart] = {}        # PosePart name to *PosePart* table
        self.project_parts: List[ProjectPart] = []             # List of *ProjectPart*'s
        self.project_parts_table: Dict[str, ProjectPart] = {}  # ProjectPart name to *ProjectPart*
        self.all_pose_parts: List[PosePart] = []               # All *ProjectPart*'s
        self.installed_pose_parts: List[PosePart] = []         # *ProjectPart*'s to be installed
        self.uninstalled_pose_parts: List[PosePart] = []       # *ProjectParts*'s not installed

        # Read all of the *cads* associated with *order*:
        cads: List[Cad] = order.cads
        success: bool = False
        cad: Cad
        for cad in cads:
            success = cad.file_read(cad_file_name, project)
            if success:
                break
        assert success, f"Could not successfully read and process file '{cad_file_name}'!"

    # Project.__format__():
    def __format__(self, format) -> str:
        # Grab some values from *project* (i.e. *self*):
        project: Project = self
        name: str = project.name
        revision: str = project.revision
        # Return *result*:
        result: str = f"{name}.{revision}"
        return result

    # Project.__str__():
    def __str__(self) -> str:
        name: str = "??"
        project: Project = self
        if hasattr(project, "name"):
            name = project.name
        return f"Project('{name}')"

    # Project.assembly_summary_write():
    @trace(1)
    def assembly_summary_write(self, final_choice_parts: "List[ChoicePart]",
                               order: Order, tracing: str = "") -> None:
        """ Write out an assembly summary .csv file for the *Project* object (i.e. *self*)
            using *final_choice_parts*.
        """
        # Open *project_file* (i.e. *self*):
        project: Project = self
        order_root: str = order.order_root
        project_file_name: str = os.path.join(order_root, f"{project.name}.csv")
        project_file: IO[str]
        with open(project_file_name, "w") as project_file:
            # Write out the column headings:
            project_file.write(
              '"Quan.","Reference","Schematic Name","Description","Fractional",' +
              '"Manufacturer","Manufacture PN","Vendor","Vendor PN"\n\n')

            # Output the installed parts:
            has_fractional_parts1: bool = project.assembly_summary_write_helper(True,
                                                                                final_choice_parts,
                                                                                project_file)

            # Output the uninstalled parts:
            project_file.write("\nDo Not Install\n")

            # Output the installed parts:
            has_fractional_parts2: bool = project.assembly_summary_write_helper(False,
                                                                                final_choice_parts,
                                                                                project_file)

            # Explain what a fractional part is:
            if has_fractional_parts1 or has_fractional_parts2:
                project_file.write(
                  '"","\nFractional parts are snipped off of 1xN or 2xN break-way headers"\n')

        # Write out a progress message:
        print(f"Wrote out assembly file '{project_file_name}'")

    # Project.assembly_summary_write_helper():
    def assembly_summary_write_helper(self, install: bool, final_choice_parts: "List[ChoicePart]",
                                      csv_file: IO[str], tracing: str = "") -> bool:
        """ Write out an assembly summary .csv file for *Project* object (i.e. *self*)
            out to *project_file*.  *install* is set *True* to list the installable parts from
            *final_choice_parts* and *False* for an uninstallable parts listing.
            This routine returns *True* if there are any fractional parts output to *csv_file*.
        """
        # Each *final_choice_part* that is part of the project (i.e. *self*) will wind up
        # in a list in *pose_parts_table*.  The key is the *project_part_key*:
        project: Project = self
        pose_parts_table: Dict[str, List[Tuple[PosePart, ChoicePart]]] = {}
        final_choice_part: ChoicePart
        for final_choice_part in final_choice_parts:
            # Now figure out if final choice part is part of *pose_parts*:
            pose_parts: List[PosePart] = final_choice_part.pose_parts
            pose_part: PosePart
            for pose_part in pose_parts:
                # We only care care about *final_choice_part* if is used on *project* and
                # it matches the *install* selector:
                if pose_part.project is project and pose_part.install == install:
                    # We are on the project; create *schemati_part_key*:
                    project_part: ProjectPart = pose_part.project_part
                    project_part_key: str = (f"{project_part.base_name};"
                                             f"{project_part.short_footprint}")

                    # Create/append a list to *pose_parts_table*, keyed on *project_part_key*:
                    if project_part_key not in pose_parts_table:
                        pose_parts_table[project_part_key] = []
                    key: str = project_part_key
                    pairs_list: List[Tuple[PosePart, ChoicePart]] = pose_parts_table[key]

                    # Append a pair of *pose_part* and *final_choice_part* onto *pairs_list*:
                    project_final_pair = (pose_part, final_choice_part)
                    pairs_list.append(project_final_pair)

        # Now organize everything around the *reference_list*:
        reference_pose_parts: Dict[str, Tuple[PosePart, ChoicePart]] = {}
        for pairs_list in pose_parts_table.values():
            # We want to sort base on *reference_value* which is converted into *reference_text*:
            reference_list: List[str] = \
              [project_final_pair[0].reference.upper() for project_final_pair in pairs_list]
            reference_text: str = ", ".join(reference_list)
            # print("reference_text='{0}'".format(reference_text))
            pair: Tuple[PosePart, ChoicePart] = pairs_list[0]
            reference_pose_parts[reference_text] = pair

        # Sort the *reference_parts_keys*:
        reference_pose_parts_keys: List[str] = list(reference_pose_parts.keys())
        reference_pose_parts_keys.sort()

        # Now dig down until we have all the information we need for output the next
        # `.csv` file line:
        has_fractional_parts: bool = False
        for reference_pose_parts_key in reference_pose_parts_keys:
            # Extract the *pose_part* and *final_choice_part*:
            key = reference_pose_parts_key
            project_final_pair = reference_pose_parts[key]
            pose_part = project_final_pair[0]
            final_choice_part = project_final_pair[1]

            # Now get the corresponding *project_part*:
            project_part = pose_part.project_part
            project_part_key = f"{project_part.base_name};{project_part.short_footprint}"

            # Now get the *actual_part*:
            actual_part: Optional[ActualPart] = final_choice_part.selected_actual_part
            if isinstance(actual_part, ActualPart):

                # Now get the VendorPart:
                manufacturer_name: str = actual_part.manufacturer_name
                manufacturer_part_name: str = actual_part.manufacturer_part_name
                vendor_part: Optional[VendorPart] = final_choice_part.selected_vendor_part
                assert isinstance(vendor_part, VendorPart)

                # Output the line for the .csv file:
                vendor_name: str = vendor_part.vendor_name
                vendor_part_name: str = vendor_part.vendor_part_name
                quantity: int = final_choice_part.count_get()
                fractional: str = "No"
                if len(final_choice_part.fractional_parts) > 0:
                    fractional = "Yes"
                    has_fractional_parts = True
                csv_file.write(f'{Encode.to_csv(str(quantity))},'
                               f'{Encode.to_csv(reference_pose_parts_key)},'
                               f'{Encode.to_csv(project_part_key)},'
                               f'{Encode.to_csv(final_choice_part.description)},'
                               f'{Encode.to_csv(fractional)},'
                               f'{Encode.to_csv(manufacturer_name)},'
                               f'{Encode.to_csv(manufacturer_part_name)},'
                               f'{Encode.to_csv(vendor_name)},'
                               f'{Encode.to_csv(vendor_part_name)}\n')
            else:
                print(f"Problems with actual_part '{actual_part}'")

        return has_fractional_parts

    # Project.check():
    def check(self, collections: Collections, tracing: str = "") -> None:
        # Grab some values from *project* (i.e. *self*):
        project: Project = self
        all_pose_parts: List[PosePart] = project.all_pose_parts

        # Check *all_pose_parts*:
        pose_part: PosePart
        for pose_part in all_pose_parts:
            pose_part.check(collections)

    # Project.project_part_append():
    def pose_part_append(self, pose_part: PosePart) -> None:
        """ Append *pose_part* onto the *Project* object (i.e. *self*).
        """
        # Tack *pose_part* onto the appropriate lists inside of *project* (i.e. *self*):
        project: Project = self
        project.all_pose_parts.append(pose_part)
        if pose_part.install:
            project.installed_pose_parts.append(pose_part)
        else:
            project.uninstalled_pose_parts.append(pose_part)

    # Project.pose_part_find():
    def pose_part_find(self, name: str, reference: str) -> PosePart:
        # Grab some values from *project_part* (i.e. *self*):
        project: Project = self
        all_pose_parts: List[PosePart] = project.all_pose_parts
        pose_parts_table: Dict[str, PosePart] = project.pose_parts_table

        # Find the *project_part* named *name* associated with *project*:
        project_part: ProjectPart = project.project_part_find(name)

        # Make sure that *reference* is not a duplicated:
        pose_part: PosePart
        if reference in pose_parts_table:
            pose_part = pose_parts_table[reference]
            print(f"Project {project} has a duplicate '{reference}'?")
        else:
            pose_part = PosePart(project, project_part, reference, "")
            pose_parts_table[reference] = pose_part
            all_pose_parts.append(pose_part)
        return pose_part

    # Project.positions_process():
    def positions_process(self) -> None:
        """ Reorigin the the contents of the positions table.
        """
        pass
        # project: Project = self
        # positions_file_name: str = project.positions_file_name
        # positions_table: PositionsTable = PositionsTable(positions_file_name)
        # positions_table.reorigin("FD1")
        # positions_table.footprints_rotate()

    # Project.project_part_find():
    def project_part_find(self, project_part_name: str) -> "ProjectPart":
        # Grab some values from *project* (i.e. *self*):
        project: Project = self
        project_parts: List[ProjectPart] = project.project_parts
        project_parts_table: Dict[str, ProjectPart] = project.project_parts_table

        # Determine if we have a pre-existing *project_part* named *name*:
        project_part: ProjectPart
        if project_part_name in project_parts_table:
            # Reuse the pre-existing *project_part* named *name*:
            project_part = project_parts_table[project_part_name]
        else:
            # Create a new *project_part* named *name* and stuff into the *project* data structures:
            project_part = ProjectPart(project_part_name, [project])
            project_parts.append(project_part)
            project_parts_table[project_part_name] = project_part
        return project_part


# ProjectPart:
class ProjectPart:
    # A *ProjectPart* represents part with a footprint.  The schematic
    # part name must adhere to the format of "name;footprint:comment", where
    # ":comment" is optional.  The footprint name can be short (e.g. 1608,
    # QFP100, SOIC20, SOT3), since it only has to disambiguate the various
    # footprints associated with "name".  A *ProjectPart* is always
    # sub-classed by one of *ChoicePart*, *AliasPart*, or *FractionalPart*.

    # ProjectPart.__init__():
    def __init__(self, name: str, projects: List[Project], tracing: str = "") -> None:
        """ *ProjectPart*: Initialize *self* to contain
            *name*, and *kicad_footprint*. """

        # Extract *base_name*, *short_footprint* and *comment* from *name* where
        # *name* is formatted as '*base_name*;*short_footprint_name*:*comment*':
        short_footprint: str = ""
        comment: str = ""
        base_name: str = ""
        pieces: List[str] = [name]
        if ':' in pieces[0]:
            pieces = pieces[0].split(':')
            pieces_size: int = len(pieces)
            assert pieces_size <= 2, f"Too many colons (':') in '{name}'"
            comment = pieces[1] if len(pieces) == 2 else ""
        if ';' in pieces[0]:
            pieces = pieces[0].split(';')
            pieces_size = len(pieces)
            assert pieces_size <= 2, f"Too many semi-colons (';') in '{name}'"
            short_footprint = pieces[1] if pieces_size == 2 else ""
        base_name = pieces[0]

        # Stuff values into *project_part* (i.e. *self*):
        # project_part = self
        self.name: str = name
        self.base_name: str = base_name
        self.comment: str = comment
        self.pose_parts: List[PosePart] = []
        self.pose_parts_table: Dict[str, PosePart] = {}
        self.projects: List[Project] = projects
        self.short_footprint: str = short_footprint

    # ProjectPart.__format__():
    def __format__(self, format: str) -> str:
        """ *ProjectPart*: Format the *ProjectPart* object (i.e. *self*) using *format***. """
        # Grab some values from *project_part* (i.e. *self*):
        project_part: ProjectPart = self
        name: str = project_part.name

        # Return *result*' based on *format*:
        result: str
        if format == "s":
            projects: List[Project] = project_part.projects
            project_names: List[str] = [project.name for project in projects]
            project_names_text: str = ":".join(project_names)
            result = f"{project_names_text}:{name}"
        else:
            result = f"{name}"
        return result

    # ProjectPart.__str__():
    def __str__(self) -> str:
        name: str = "??"
        project_part: ProjectPart = self
        if hasattr(project_part, "name"):
            name = project_part.name
        return f"ProjectPart('{name}')"

    # ProjectPart.footprints_check():
    def footprints_check(self, footprints: Dict[str, str]) -> None:
        """ *ProjectPart*: Verify that all the footprints exist for the *ProjectPart* object
            (i.e. *self*.)
        """

        assert False, "No footprints_check method for this Schematic Part"


# AliasPart():
class AliasPart(ProjectPart):
    # An *AliasPart* specifies one or more *ProjectParts* to use.

    # AliasPart.__init__():
    def __init__(self, name: str, project_parts: List[ProjectPart], footprint: str = "",
                 feeder_name="", part_height=0.0, pick_dx=0.0, pick_dy=0.0,
                 tracing: str = "") -> None:
        """ *AliasPart*: Initialize *self* to contain *name*,
            *kicad_footprint*, and *project_parts*. """

        projects_table: Dict[str, Project] = {}
        project_part: ProjectPart
        for project_part in project_parts:
            projects: List[Project] = project_part.projects
            project: Project
            for project in projects:
                project_name_revision: str = f"{project.name}.{project.revision}"
                if project_name_revision not in projects_table:
                    projects_table[project_name_revision] = project
        union_projects: List[Project] = list(projects_table.values())

        # Load up *alias_part* (i.e *self*):
        super().__init__(name, union_projects)
        # alias_part: AliasPart = self
        self.project_parts: List[ProjectPart] = project_parts
        self.feeder_name: str = feeder_name
        self.footprint: str = footprint
        self.part_height: float = part_height
        self.pick_dx: float = pick_dx
        self.pick_dy: float = pick_dy

    # AliasPart.__str__():
    def __str__(self) -> str:
        name: str = "??"
        alias_part: AliasPart = self
        if hasattr(alias_part, "name"):
            name = alias_part.name
        return f"AliasPart('{name}')"

    # AliasPart.choice_parts():
    def choice_parts(self) -> "List[ChoicePart]":
        """ *AliasPart*: Return a list of *ChoicePart*'s corresponding to *self*
        """
        # choice_parts: List[ChoicePart] = []
        # project_part: ProjectPart
        # project_parts: List[ProjectPart]
        # for project_part in project_parts:
        #     choice_parts.extend(project_part.choice_parts)
        # return choice_parts
        assert False, "Fix this code"
        return list()

    # AliasPart.footprints_check():
    def footprints_check(self, footprints: Dict[str, str]) -> None:
        """ *AliasPart*: Verify that all the footprints exist for the *AliasPart* object
            (i.e. *self*.)
        """

        # Grab *project_parts* from *alias_part* (i.e. *self*):
        alias_part: AliasPart = self
        project_parts: List[ProjectPart] = alias_part.project_parts
        project_part: ProjectPart
        for project_part in project_parts:
            project_part.footprints_check(footprints)


# ChoicePart:
class ChoicePart(ProjectPart):
    # A *ChoicePart* specifies a list of *ActualPart*'s to choose from.

    # ChoicePart.__init__():
    def __init__(self, name: str, project_parts: List[ProjectPart], searches: List[Search],
                 tracing: str = "") -> None:
        """ *ChoicePart*: Initiailize *self* to contain *name*
            *kicad_footprint* and *actual_parts*. """

        # A *chice_part* (i.e. *self*) can have multiple *Project*'s associated with it.
        # Thus, we need to compute the *union_projects* of all *Project*'s associated
        # with *project parts*:
        projects_table: Dict[str, Project] = {}
        for project_part in project_parts:
            projects: List[Project] = project_part.projects
            project: Project
            for project in projects:
                cad_file_name: str = project.cad_file_name
                projects_table[cad_file_name] = project
        union_projects: List[Project] = list(projects_table.values())

        # Load up *choice_part* (i.e. *self*):
        super().__init__(name, union_projects)
        self.actual_parts: List[ActualPart] = []
        self.searches: List[Search] = searches
        # Fields used by algorithm:
        self.description: str = "DESCRIPTION"
        self.footprint: str = "FOOTPRINT"
        self.fractional_parts: List[FractionalPart] = []
        self.selected_total_cost: float = 0.00
        self.selected_order_quantity: int = -1
        self.selected_actual_part: Optional[ActualPart] = None
        self.selected_vendor_part: Optional[VendorPart] = None
        self.selected_vendor_name: str = ""
        self.selected_price_break_index: int = -1
        self.selected_price_break: Optional[PriceBreak] = None

        # assert isinstance(kicad_footprint, str)
        # assert isinstance(location, str)
        # assert isinstance(description, str)
        # assert isinstance(rotation, float) or rotation is None
        # assert isinstance(pick_dx, float)
        # assert isinstance(pick_dy, float)
        # assert isinstance(feeder_name, str) or feeder_name is None
        # assert isinstance(part_height, float) or part_height is None

        # choice_part.feeder_name = feeder_name
        # choice_part.location = location
        # choice_part.part_height = part_height
        # choice_part.rotation = rotation
        # choice_part.pick_dx = pick_dx
        # choice_part.pick_dy = pick_dy

    # ChoicePart.__format__():
    def __format__(self, format) -> str:
        """ *ChoicePart*: Return the *ChoicePart object (i.e. *self* as a string formatted by
            *format*.
        """

        choice_part: ChoicePart = self
        return choice_part.__str__()

    # ChoicePart.__str__():
    def __str__(self) -> str:
        choice_part: ChoicePart = self
        name: str = "??"
        if hasattr(choice_part, "name"):
            name = choice_part.name
        return f"ChoicePart('{name}')"

    # # ChoicePart.actual_part():
    # def actual_part(self, manufacturer_name, manufacturer_part_name, vendor_triples=[]):
    #     """ *ChoicePart*: Create an *ActualPart* that contains *manufacturer_name* and
    #         *manufacturer_part_name* and append it to the *ChoicePart* object (i.e. *self*.)
    #         For parts whose prices are not available via screen scraping, it is possible to
    #         specify vendor/pricing information as a list of vendor triples.  The vendor triples
    #         are a *tuple* of(*vendor_name*, *vendor_part_name*, *price_pairs_text*),
    #         where *vendor_name* is a distributor (i.e. "Newark", or "Pololu"), *vendor_part_name*
    #         is a the vendors order number of the part, and *price_pairs_text* is a string of
    #         the form "quant1/price1 quant2/price2 ... quantN/priceN".  *quantI* is an quantity
    #         as an integer and *priceI* is a price in dollars.
    #     """

    #     # Verify argument types:
    #     assert isinstance(manufacturer_name, str)
    #     assert isinstance(manufacturer_part_name, str)
    #     assert isinstance(vendor_triples, list)
    #     for vendor_triple in vendor_triples:
    #         assert len(vendor_triple) == 3
    #         assert isinstance(vendor_triple[0], str)
    #         assert isinstance(vendor_triple[1], str)
    #         assert isinstance(vendor_triple[2], str)

    #     actual_part = ActualPart(manufacturer_name, manufacturer_part_name)
    #     self.actual_parts.append(actual_part)

    #     if True:
    #         for vendor_triple in vendor_triples:
    #             vendor_name = vendor_triple[0]
    #             vendor_part_name = vendor_triple[1]
    #             price_pairs_text = vendor_triple[2]

    #             price_breaks = []
    #             for price_pair_text in price_pairs_text.split():
    #                 # Make sure we only have a price and a pair*:
    #                 price_pair = price_pair_text.split('/')
    #                 assert len(price_pair) == 2

    #                 # Extract the *quantity* from *price_pair*:
    #                 quantity = 1
    #                 try:
    #                     quantity = int(price_pair[0])
    #                 except ValueError:
    #                     assert False, \
    #                       "Quantity '{0}' is not an integer". \
    #                       format(price_pair[0])

    #                 # Extract the *price* from *price_pair*:
    #                 price = 100.00
    #                 try:
    #                     price = float(price_pair[1])
    #                 except ValueError:
    #                     assert False, \
    #                       "Price '{0}' is not a float".format(price_pair[1])

    #                 # Construct the *price_break* and append to *price_breaks*:
    #                 price_break = PriceBreak(quantity, price)
    #                 price_breaks.append(price_break)

    #             # Create the *vendor_part* and append it to *actual_part*:
    #             assert len(price_breaks) > 0
    #             vendor_part = VendorPart(actual_part,
    #                                      vendor_name, vendor_part_name, 1000000, price_breaks)
    #             actual_part.vendor_part_append(vendor_part)
    #             # if tracing:
    #             #    print("vendor_part_append called")

    #             # print("ChoicePart.actual_part(): Explicit vendor_part specified={0}".
    #             #  format(vendor_part))

    #     return self

    # ChoicePart.pose_part_append():
    def pose_part_append(self, pose_part: PosePart) -> None:
        """ *ChoicePart*: Store *pose_part* into the *ChoicePart* object
            (i.e. *self*.)
        """
        choice_part: ChoicePart = self
        choice_part.pose_parts.append(pose_part)

    # ChoicePart.pose_parts_sort():
    def pose_parts_sort(self) -> None:
        """ *ChoicePart*: Sort the *pose_parts* of the *ChoicePart* object
            (i.e. *self*.)
        """

        # Sort the *pose_parts* using a key of
        # (project_name, reference, reference_number).  A reference of
        # "SW123" gets conferted to (..., "SW123", 123):
        choice_part: ChoicePart = self
        pose_parts: List[PosePart] = choice_part.pose_parts
        pose_parts.sort(key=lambda pose_part:
                        (pose_part.project.name,
                         text_filter(pose_part.reference, str.isalpha).upper(),
                         int(text_filter(pose_part.reference, str.isdigit))))

        # print("  {0}:{1};{2} {3}:{4}".\
        #  format(choice_part.name,
        # choice_part.kicad_footprint, choice_part.description,
        #  choice_part.count_get(), choice_part.references_text_get()))

    # ChoicePart.count_get():
    def count_get(self) -> int:
        """ *ChoicePart*: Return the number of needed instances of *self*. """
        choice_part: ChoicePart = self
        count: int = 0
        fractional_part: FractionalPart
        fractional_parts: List[FractionalPart] = choice_part.fractional_parts
        pose_parts: List[PosePart] = choice_part.pose_parts
        pose_part: PosePart
        if len(fractional_parts) == 0:
            for pose_part in pose_parts:
                count += pose_part.project.count
        else:
            # for fractional_part in fractional_parts:
            #        print("{0}".format(fractional_part.name))

            # This code is not quite right:
            first_fractional_part: FractionalPart = fractional_parts[0]
            denominator: int = first_fractional_part.denominator
            for fractional_part in fractional_parts[1:]:
                assert denominator == fractional_part.denominator, \
                  "'{0}' has a denominator of {1} and '{2}' has one of {3}". \
                  format(first_fractional_part.name,
                         first_fractional_part.denominator,
                         fractional_part.name,
                         fractional_part.denominator)

            # Compute the *count*:
            numerator: int = 0
            for pose_part in pose_parts:
                project_part: ProjectPart = pose_part.project_part
                # print("'{0}'".format(project_part.name))
                if isinstance(project_part, AliasPart):
                    alias_part = project_part
                    for project_part in alias_part.project_parts:
                        if isinstance(project_part, FractionalPart):
                            fractional_part = project_part
                elif isinstance(project_part, FractionalPart):
                    fractional_part = project_part
                else:
                    assert False, "Missing code"

                fractional_numerator: int = fractional_part.numerator
                for index in range(pose_part.project.count):
                    if numerator + fractional_numerator > denominator:
                        count += 1
                        numerator = 0
                    numerator += fractional_numerator
            if numerator > 0:
                numerator = 0
                count += 1
        return count

    # ChoicePart.choice_parts():
    def choice_parts(self) -> "List[ChoicePart]":
        """ *ChoicePart*: Return a list of *ChoicePart* corresponding
            to *self* """
        choice_part: ChoicePart = self
        return [choice_part]

    # ChoicePart.footprints_check():
    def footprints_check(self, footprints: Dict[str, str]) -> None:
        """ *ChoicePart*: Verify that all the footprints exist for the *ChoicePart* object
            (i.e. *self*.)
        """

        # Use *choice_part* instead of *self*:
        choice_part: ChoicePart = self
        footprint: str = choice_part.footprint
        if footprint != "-":
            footprints[footprint] = choice_part.name
            # rotation = choice_part.rotation

    # ChoicePart.references_text_get():
    def references_text_get(self) -> str:
        """ *ChoicePart*: Return a string of references for *self*. """

        choice_part: ChoicePart = self
        references_text: str = ""
        previous_project: Optional[Project] = None
        is_first: bool = True
        pose_part: PosePart
        for pose_part in choice_part.pose_parts:
            project: Project = pose_part.project
            if project != previous_project:
                if not is_first:
                    references_text += "]"
                references_text += f"[{project.name}"
            previous_project = project
            is_first = False

            # Now tack the reference to the end:
            references_text += f" {pose_part.reference}"
        references_text += "]"
        return references_text

    # ChoicePart.select():
    @trace(2)
    def select(self, excluded_vendor_names: Dict[str, None], announce: bool = False,
               tracing: str = "") -> int:
        """ *ChoicePart*: Select and return the best priced *ActualPart*
            for the *ChoicePart* (i.e. *self*) excluding any vendors
            in the *excluded_vendor_names* dictionary.
        """
        trace_level: int = trace_level_get()

        # This lovely piece of code basically brute forces the decision
        # process of figuring out which *vendor_part* to select and the
        # number of parts to order.  We iterate over each *actual_part*,
        # *vendor_part* and *price_break* and compute the *total_cost*
        # and *order_quanity* for that combination.  We store this into
        # a 5-tuple called *quint* and build of the list of *quints*.
        # When we are done, we sort *quints* and select the first one
        # off the head of the list.

        # Grab some values from *choice_part* (i.e. *self*):
        choice_part: "ChoicePart" = self
        required_quantity: int = choice_part.count_get()
        actual_parts: List[ActualPart] = choice_part.actual_parts
        quints: List[Quint] = []

        actual_part_index: int
        actual_part: ActualPart
        for actual_part_index, actual_part in enumerate(actual_parts):
            if tracing and trace_level >= 1:
                manufacturer_name: str = actual_part.manufacturer_name
                manufacturer_part_name: str = actual_part.manufacturer_part_name
                print(f"{tracing} Manufacturer: '{manufacturer_name}' '{manufacturer_part_name}'")
            vendor_parts: List[VendorPart] = actual_part.vendor_parts
            vendor_part_index: int
            vendor_part: VendorPart
            for vendor_part_index, vendor_part in enumerate(vendor_parts):
                # if tracing and trace_level >= 2
                #     print(f"Vendor: {vendor_part.vendor_name}: "
                #           f"'{vendor_part.vendor_part_name}':"
                #           f":{vendor_part.quantity_available}")
                if tracing and trace_level >= 2:
                    vendor_name: str = vendor_part.vendor_name
                    vendor_part_name: str = vendor_part.vendor_part_name
                    quantity_available: int = vendor_part.quantity_available
                    print(f"{tracing}  Vendor: {quantity_available} x "
                          f"'{vendor_name}': '{vendor_part_name}'")
                price_breaks: List[PriceBreak] = vendor_part.price_breaks
                price_break_index: int
                price_break: PriceBreak
                for price_break_index, price_break in enumerate(price_breaks):
                    # if tracing:
                    #        print("  B")

                    # We not have an *actual_part*, *vendor_part* and
                    # *price_break* triple.  Compute *order_quantity*
                    # and *total_cost*:
                    price: float = price_break.price
                    quantity: int = price_break.quantity
                    order_quantity: int = max(required_quantity, quantity)
                    total_cost: float = order_quantity * price
                    # if tracing:
                    #     print("   price={0:.2f} quant={1} order_quantity={2} total_cost={3:.2f}".
                    #           format(price, quantity, order_quantity, total_cost))

                    # Assemble the *quint* and append to *quints* if there
                    # enough parts available:
                    is_excluded: bool = vendor_part.vendor_name in excluded_vendor_names
                    # if trace_level:
                    #    print(f"quantity_available={vendor_part.quantity_available}, "
                    #          f"is_excluded={is_excluded}")
                    if tracing and trace_level >= 3:
                        quantity_available = vendor_part.quantity_available
                        print(f"{tracing}   Quantity Available:{quantity_available} "
                              f"Is Excluded:{is_excluded}")
                    if not is_excluded and vendor_part.quantity_available >= order_quantity:
                        assert price_break_index < len(price_breaks)
                        quint: Quint = (total_cost, order_quantity,
                                        actual_part_index, vendor_part_index,
                                        price_break_index, len(price_breaks))
                        quints.append(quint)
                        if tracing:
                            print(f"{tracing}    quint={quint}")

        if len(quints) == 0:
            choice_part_name = self.name
            if announce:
                print(f"{tracing}No vendor parts found for Part '{choice_part_name}'")
        else:
            # Now sort in ascending order:
            quints.sort()
            quint = quints[0]

            # Extract values from *quint*:
            selected_total_cost = quint[0]
            selected_order_quantity = quint[1]
            selected_actual_part = actual_parts[quint[2]]
            selected_vendor_part = selected_actual_part.vendor_parts[quint[3]]
            selected_vendor_name = selected_vendor_part.vendor_name
            selected_price_break_index = quint[4]

            # Now stuff extracted values from *quint* into *self*:
            self.selected_total_cost = selected_total_cost
            self.selected_order_quantity = selected_order_quantity
            self.selected_actual_part = selected_actual_part
            self.selected_vendor_part = selected_vendor_part
            self.selected_vendor_name = selected_vendor_name
            self.selected_price_break_index = selected_price_break_index
            assert selected_price_break_index < len(selected_vendor_part.price_breaks)

            # print("selected_vendor_name='{0}'".format(selected_vendor_name))

        # actual_parts = self.actual_parts
        # for actual_part in actual_parts:
        #    print("       {0}:{1}".format(actual_part.manufacturer_name,
        #      actual_part.manufacturer_part_name))

        # actual_parts = self.actual_parts
        # selected_actual_part = actual_parts[0]
        # assert isinstance(selected_actual_part, ActualPart)
        # self.selected_actual_part = selected_actual_part

        # vendor_parts = selected_actual_part.vendor_parts
        # if len(vendor_parts) == 0:
        #    key = selected_actual_part.key
        #    print("No vendor part for Actual Part '{0} {1}'". \
        #      format(key[0], key[1]))
        # else:
        #    selected_actual_part.selected_vendor_part = vendor_parts[0]

        # assert isinstance(selected_actual_part, ActualPart)

        missing_part: int = 0
        if len(quints) == 0:
            missing_part = 1

        return missing_part

    # ChoicePart.vendor_names_load():
    def vendor_names_load(self, vendor_names_table: Dict[str, None],
                          excluded_vendor_names: Dict[str, None], tracing: str = "") -> None:
        """ *ChoicePart*: Add each possible vendor name possible for the
            *ChoicePart* object (i.e. *self*) to *vendor_names_table*
            provided it is not in *excluded_vendor_names*:
        """
        # Visit each *actual_part* and add the vendor names to
        # *vendor_names_table*:
        choice_part: ChoicePart = self
        actual_parts: List[ActualPart] = choice_part.actual_parts
        actual_part: ActualPart
        for actual_part in actual_parts:
            actual_part.vendor_names_load(vendor_names_table, excluded_vendor_names)

    # ChoicePart.vendor_parts_refresh():
    @trace(1)
    def vendor_parts_refresh(self, proposed_actual_parts: List[ActualPart],
                             order: Order, part_name: str, tracing: str = "") -> None:
        # Grab some values from *choice_part* (i.e. *self*) and *order*:
        choice_part: ChoicePart = self
        choice_part_name: str = choice_part.name
        pandas: List[Panda] = order.pandas
        stale: int = order.stale
        vendor_searches_root: str = order.vendor_searches_root
        trace_level: int = trace_level_get()

        # Construct the file path for the `.xml` file associated *choice_part*:
        xml_base_name: str = Encode.to_file_name(choice_part_name + ".xml")
        xml_full_name: str = os.path.join(vendor_searches_root, xml_base_name)
        if tracing:
            print(f"{tracing}choice_part_name='{choice_part_name}'")
            print(f"{tracing}vendor_searches_root='{vendor_searches_root}'")
            print(f"{tracing}xml_base_name='{xml_base_name}'")
            print(f"{tracing}xml_full_name='{xml_full_name}'")

        # Open *xml_full_name*, read it in, and fill in *previous_actual_parts_table* with
        # the resulting *previous_actual_part* from the `.xml` file.  Mark *xml_save_required*
        # as *True* if *xml_full_file_name* does not exist:
        xml_save_required: bool = False
        previous_actual_parts: List[ActualPart] = list()
        previous_actual_parts_table: Dict[Tuple[str, str], ActualPart] = dict()
        if os.path.isfile(xml_full_name):
            # Read in and parse the *xml_full_name* file:
            xml_read_file: IO[str]
            with open(xml_full_name) as xml_read_file:
                choice_part_xml_text: str = xml_read_file.read()
                choice_part_tree: etree._Element = etree.fromstring(choice_part_xml_text)

                # Note that *previous_choice_part* is kind of busted since it
                # its internal *project_parts* and *searches* lists are empty.
                # This is OK, since we only need the *previous_actual_parts* list
                # which is popluated with valid *ActualPart*'s:
                previous_choice_part: ChoicePart = ChoicePart.xml_parse(choice_part_tree)
                if tracing:
                    print(f"{tracing}Read in '{xml_full_name}'")

                # Sweep through *previous_actual_parts* and enter them into
                # *previous_actual_parts_table*:
                previous_actual_parts = previous_choice_part.actual_parts
                for previous_actual_part in previous_actual_parts:
                    previous_actual_parts_table[previous_actual_part.key] = previous_actual_part
        else:
            # *xml_full_name* does not exist, so we must write out a new one later one:
            xml_save_required = True

        # For debugging show both the sorted *proposed_actual_parts* and *previous_actual_parts*
        # side-by-side:
        if tracing and trace_level >= 2:
            # First sort *proposed_actual_parts* and *previous_actual_parts*:
            proposed_actual_parts.sort(key=lambda proposed_actual_part: proposed_actual_part.key)
            previous_actual_parts.sort(key=lambda previous_actual_part: previous_actual_part.key)

            # Compute the *maximum_actual_parts_size*:
            proposed_actual_parts_size: int = len(proposed_actual_parts)
            previous_actual_parts_size: int = len(previous_actual_parts)
            maximum_actual_parts_size: int = max(proposed_actual_parts_size,
                                                 previous_actual_parts_size)
            print(f"{tracing}proposed_actual_parts_size={proposed_actual_parts_size}")
            print(f"{tracing}previous_actual_parts_size={previous_actual_parts_size}")
            print(f"{tracing}maximum_actual_parts_size={maximum_actual_parts_size}")

            # Now sweep across both *proposed_actual_parts* and *previous_actual_parts*
            # printing out the key values side by side:
            print(f"{tracing}Actual_Parts[xx]: (proposed)  (previous)")
            for index in range(maximum_actual_parts_size):
                proposed_text: str = ("--------" if index >= proposed_actual_parts_size
                                      else str(proposed_actual_parts[index].key))
                previous_text: str = ("--------" if index >= previous_actual_parts_size
                                      else str(previous_actual_parts[index].key))
                print(f"{tracing}Actual_Parts[{index}]:'{previous_text}'\t{proposed_text}")

        # We need to figure out when actual parts from the `.xml` are old (i.e. *stale*)
        # and refresh them.
        now: int = int(time.time())
        if tracing:
            print(f"{tracing}now={now} stale={stale} now-stale={now-stale}")

        # Now sweep through *proposed_actual_parts* and refresh any that are either missing or out
        # of date and construct the *final_actual_parts*:
        final_actual_parts: List[ActualPart] = list()
        proposed_actual_part: ActualPart
        for index, proposed_actual_part in enumerate(proposed_actual_parts):
            # Grab the *proposed_actual_part_key*:
            proposed_actual_part_key: Tuple[str, str] = proposed_actual_part.key
            if tracing:
                print(f"{tracing}Proposed_Actual_Part[{index}]:'{proposed_actual_part.key}'")

            # Start by assuming that *lookup_is_required* and set to *False* if we can avoid
            # the lookup:
            lookup_is_required: bool = True
            if proposed_actual_part_key in previous_actual_parts_table:
                if tracing and trace_level >= 2:
                    print(f"{tracing}'{proposed_actual_part_key} is in previous_actual_parts_table")

                # We have a *previous_actual_part* that matches *proposed_actual_part*.
                # Now we see if can simply copy *previous_vendor_parts* over or
                # whether we must trigger a vendor parts lookup:
                key: Tuple[str, str] = proposed_actual_part_key
                previous_actual_part = previous_actual_parts_table[key]
                previous_vendor_parts: List[VendorPart] = previous_actual_part.vendor_parts
                if tracing and trace_level >= 2:
                    print(f"{tracing}previous_actual_part.name="
                          f"'{previous_actual_part.manufacturer_part_name}'")
                    print(f"{tracing}len(previous_vendor_parts)={len(previous_vendor_parts)}")

                # Compute the *minimum_time_stamp* across all *previous_vendor_parts*:
                minimum_timestamp: int = now
                for previous_vendor_part in previous_vendor_parts:
                    minimum_timestamp = min(minimum_timestamp, previous_vendor_part.timestamp)
                if tracing and trace_level >= 2:
                    print(f"{tracing}minimum_timestamp={minimum_timestamp}")

                # If the *minimum_time_stamp* is too stale, force a refresh:
                if minimum_timestamp + stale > now:
                    if tracing and trace_level >= 2:
                        print(f"{tracing}Not stale")
                    proposed_actual_part.vendor_parts = previous_vendor_parts
                    lookup_is_required = False
            else:
                if tracing and trace_level >= 2:
                    print(f"{tracing}'{proposed_actual_part_key} is not"
                          f" in previous_actual_parts_table")
            if tracing:
                print(f"{tracing}lookup_is_required={lookup_is_required}")

            # If *lookup_is_required*, visit each *Panda* object in *pandas* and look up
            # *VendorPart*'s.  Assemble them all in the *new_vendor_parts* list:
            if lookup_is_required:
                new_vendor_parts: List[VendorPart] = list()
                panda: Panda
                for panda in pandas:
                    actual_part: ActualPart = proposed_actual_part
                    panda_vendor_parts: List[VendorPart] = panda.vendor_parts_lookup(actual_part,
                                                                                     part_name)
                    if tracing:
                        print(f"{tracing}len(panda_vendor_parts)={len(panda_vendor_parts)}")
                    new_vendor_parts.extend(panda_vendor_parts)
                    if tracing:
                        panda_vendor_parts_size: int = len(panda_vendor_parts)
                        new_vendor_parts_size: int = len(new_vendor_parts)
                        print(f"{tracing}panda_vendor_parts_size={panda_vendor_parts_size}")
                        print(f"{tracing}new_vendor_parts_size={new_vendor_parts_size}")
                if len(new_vendor_parts) >= 0:
                    final_actual_parts.append(proposed_actual_part)
                xml_save_required = True
            else:
                final_actual_parts.append(proposed_actual_part)

        # Figure out if we need to write out *final_actual_parts* by figuring out
        # whether or not they match *previous_actual_parts*:
        TableType = Dict[Tuple[str, str], ActualPart]
        previous_actual_parts_table = {previous_actual_part.key: previous_actual_part
                                       for previous_actual_part in previous_actual_parts}
        final_actual_parts_table: TableType = {final_actual_part.key: final_actual_part
                                               for final_actual_part in final_actual_parts}
        xml_save_required &= len(previous_actual_parts_table) != len(final_actual_parts_table)
        if not xml_save_required:
            for final_actual_part_key, final_actual_part in final_actual_parts_table.items():
                if final_actual_part_key not in previous_actual_parts_table:
                    xml_save_required = True
                    break
                previous_actual_part = previous_actual_parts_table[final_actual_part_key]
                if previous_actual_part != final_actual_part:
                    xml_save_required = True
                    break

        # Do a little more *tracing*:
        if tracing:
            final_actual_parts_size = len(final_actual_parts)
            previous_actual_parts_size = len(previous_actual_parts)
            proposed_actual_parts_size = len(proposed_actual_parts)
            print(f"{tracing}final_actual_parts_size={final_actual_parts_size}")
            print(f"{tracing}previous_actual_parts_size={previous_actual_parts_size}")
            print(f"{tracing}proposed_actual_parts_size={proposed_actual_parts_size}")

        # Update *choice_part* with the new *final_actual_parts*:
        choice_part.actual_parts = final_actual_parts

        # Save *choice_part* out to *xml_file* if *xml_save_required* hase been set:
        if xml_save_required:
            if tracing:
                print(f"{tracing}Writing out '{xml_full_name}'")
            xml_lines = []
            xml_lines.append('<?xml version="1.0"?>')
            choice_part.xml_lines_append(xml_lines, "")
            xml_lines.append("")
            xml_text = "\n".join(xml_lines)
            with open(xml_full_name, "w") as xml_write_file:
                xml_write_file.write(xml_text)

    # ChoicePart.xml_lines_append():
    def xml_lines_append(self, xml_lines: List[str], indent: str, tracing: str = "") -> None:
        # Grab some values from *choice_part* (i.e. *self*):
        choice_part: ChoicePart = self
        actual_parts: List[ActualPart] = choice_part.actual_parts
        name: str = choice_part.name

        # Output the `<ChoicePart ... >` tag:
        xml_lines.append(f'{indent}<ChoicePart name="{Encode.to_attribute(name)}">')

        # Output the `<ActualPart ... >` tags:
        next_indent: str = indent + " "
        actual_part: ActualPart
        for actual_part in actual_parts:
            actual_part.xml_lines_append(xml_lines, next_indent)

        # Output the closing `</ChoicePart>` tag:
        xml_lines.append(f'{indent}</ChoicePart>')

    # ChoicePart.xml_parse():
    @staticmethod
    def xml_parse(choice_part_tree: etree._Element) -> "ChoicePart":
        # Create *choice_part* (most of the values are no longer used...):
        assert choice_part_tree.tag == "ChoicePart"
        attributes_table: Dict[str, str] = choice_part_tree.attrib
        name: str = attributes_table["name"]
        choice_part: ChoicePart = ChoicePart(name, [], [])

        # Read in the *actual_parts* from *choice_part_tree* and return the resulting *choice_part*:
        actual_parts: List[ActualPart] = choice_part.actual_parts
        actual_part_tree: etree._Element
        for actual_part_tree in list(choice_part_tree):
            actual_part: ActualPart = ActualPart.xml_parse(actual_part_tree)
            actual_parts.append(actual_part)
        return choice_part


# FractionalPart:
class FractionalPart(ProjectPart):
    # A *FractionalPart* specifies a part that is constructed by
    # using a portion of another *ProjectPart*.

    # FractionalPart.__init__():
    def __init__(self, name: str, projects: List[Project], footprint: str, choice_part: ChoicePart,
                 numerator: int, denominator: int, description: str, tracing: str = "") -> None:
        """ *FractionalPart*: Initialize *self* to contain
            *name*, *kicad_footprint*, *choie_part*,
            *numerator*, *denomoniator*, and *description*. """
        # Load up *self*:
        super().__init__(name, projects)
        # fractional_part: FractionPart = self
        self.choice_part: ChoicePart = choice_part
        self.footprint: str = footprint
        self.numerator: int = numerator
        self.denominator: int = denominator
        self.description: str = description

    # FractionalPart.__str__()
    def __str__(self) -> str:
        name: str = "??"
        fractional_part: FractionalPart = self
        if hasattr(fractional_part, "name"):
            name = fractional_part.name
        return f"FractionalPart('{name}')"

    # FractionalPart.choice_parts():
    def choice_parts(self) -> List[ChoicePart]:
        """ *FractionalPart*: Return the *ChoicePart* objects associated
            with *self*.
        """

        choice_part = self.choice_part
        choice_part.fractional_parts.append(self)
        return [choice_part]

    # FractionalPart.footprints_check():
    def footprints_check(self, footprints: Dict[str, str]) -> None:
        """ *FractionalPart*: Verify that all the footprints exist for the *FractionalPart* object
            (i.e. *self*.)
        """

        # Use *fractional_part* instead of *self*:
        fractional_part: FractionalPart = self

        # Record *kicad_footprint* into *kicad_footprints*:
        footprint: str = fractional_part.footprint
        if footprint != "-":
            footprints[footprint] = fractional_part.name


# Units:
class Units:
    # Units.__init():
    def __init__(self) -> None:
        pass

    # Units.__str__():
    def __str__(self) -> str:
        return "Units()"

    # Units.si_units_re_text_get():
    @staticmethod
    def si_units_re_text_get() -> str:
        base_units: List[str] = ["s(ecs?)?", "seconds?", "m(eters?)?", "g(rams?)?", "[Aa](mps?)?",
                                 "[Kk](elvin)?", "mol(es?)?", "cd", "candelas?"]
        derived_units: List[str] = ["rad", "sr", "[Hh]z", "[Hh]ertz", "[Nn](ewtons?)?",
                                    "Pa(scals?)?", "J(oules?)?", "W(atts?)?", "°C", "V(olts?)?",
                                    "F(arads?)?", "Ω", "O(hms?)?", "S", "Wb", "T(eslas?)?", "H",
                                    "degC", "lm", "lx", "Bq", "Gy", "Sv", "kat"]
        all_units: List[str] = base_units + derived_units
        all_units_re_text: str = "(" + "|".join(all_units) + ")"
        prefixes: List[Tuple[str, float]] = [
          ("Y", 1e24),
          ("Z", 1e21),
          ("E", 1e18),
          ("P", 1e15),
          ("T", 1e12),
          ("G", 1e9),
          ("M", 1e6),
          ("k", 1e3),
          ("h", 1e2),
          ("da", 1e1),
          ("c", 1e-2),
          ("u", 1e-6),
          ("n", 1e-9),
          ("p", 1e-12),
          ("f", 1e-15),
          ("a", 1e-18),
          ("z", 1e-21),
          ("y", 1e-24)
        ]
        single_letter_prefixes: List[str] = [prefix[0] for prefix in prefixes
                                             if len(prefix[0]) == 1]
        single_letter_re_text: str = "[" + "".join(single_letter_prefixes) + "]"
        multi_letter_prefixes: List[str] = [prefix[0] for prefix in prefixes if len(prefix[0]) >= 2]
        letter_prefixes: List[str] = [single_letter_re_text] + multi_letter_prefixes
        prefix_re_text: str = "(" + "|".join(letter_prefixes) + ")"
        # print("prefix_re_text='{0}'".format(prefix_re_text))
        si_units_re_text: str = prefix_re_text + "?" + all_units_re_text
        # print("si_units_re_text='{0}'".format(si_units_re_text))
        return si_units_re_text


# VendorPart:
class VendorPart:
    # A vendor part represents a part that can be ordered from a vendor.

    # VendorPart.__init__():
    def __init__(self, actual_part: ActualPart, vendor_name: str, vendor_part_name: str,
                 quantity_available: int, price_breaks: List[PriceBreak],
                 timestamp: int = 0, tracing: str = "") -> None:
        """ *VendorPart*: Initialize *self* to contain *actual_part"""

        # Clean up *vendor_name*:
        # original_vendor_name = vendor_name
        vendor_name = vendor_name.replace('\n', "")
        if vendor_name.endswith(" •"):
            vendor_name = vendor_name[:-2]
        if vendor_name.endswith(" ECIA (NEDA) Member"):
            vendor_name = vendor_name[:-19]
        if vendor_name.endswith(" CEDA member"):
            vendor_name = vendor_name[:-12]
        vendor_name = vendor_name.strip(" \t")
        # print("vendor_name='{0}'\t\toriginal_vendor_name='{1}'".format(
        #  vendor_name, original_vendor_name))

        # Sort *price_breakes* and convert to a tuple:
        price_breaks.sort(key=lambda price_break: (price_break.quantity, price_break.price))

        # Load up *self*:
        # vendor_part: VendorPart = self
        self.actual_part_key: Tuple[str, str] = actual_part.key
        self.quantity_available: int = quantity_available
        self.price_breaks: List[PriceBreak] = price_breaks
        self.timestamp: int = timestamp
        self.vendor_key: Tuple[str, str] = (vendor_name, vendor_part_name)
        self.vendor_name: str = vendor_name
        self.vendor_part_name: str = vendor_part_name

        # Append *self* to the vendor parts of *actual_part*:
        actual_part.vendor_part_append(self)

    # VendorPart.__eq__():
    def __eq__(self, vendor_part2: object) -> bool:
        equal: bool = False
        if isinstance(vendor_part2, VendorPart):
            # Compare *vendor_part1* to *vendor_part2*:
            vendor_part1: VendorPart = self
            actual_part_key_equal: bool = (vendor_part1.actual_part_key ==
                                           vendor_part2.actual_part_key)
            quantity_available_equal: bool = (vendor_part1.quantity_available ==
                                              vendor_part2.quantity_available)
            timestamp_equal: bool = vendor_part1.timestamp == vendor_part2.timestamp
            vendor_key_equal: bool = vendor_part1.vendor_key == vendor_part2.vendor_key

            # Compute whether *price_breaks1* is equal to *price_breaks2*:
            price_breaks_equal: bool = vendor_part1.price_breaks == vendor_part2.price_breaks

            equal = (actual_part_key_equal and quantity_available_equal and
                     timestamp_equal and vendor_key_equal and price_breaks_equal)
        return equal

    # VendorPart.__format__():
    def __format__(self, format: str) -> str:
        """ *VendorPart*: Print out the information of the *VendorPart* (i.e. *self*):
        """
        vendor_part = self
        vendor_name = vendor_part.vendor_name
        vendor_part_name = vendor_part.vendor_part_name
        # price_breaks = vendor_part.price_breaks
        return "'{0}':'{1}'".format(vendor_name, vendor_part_name)

    # VendorPart.__str__():
    def __str__(self):
        vendor_part: VendorPart = self
        return f"VendorPart('{vendor_part.vendor_name}':'{vendor_part.vendor_part_name}')"

    # VendorPart.price_breaks_text_get():
    def price_breaks_text_get(self) -> str:
        """ *VendorPart*: Return the prices breaks for the *VendorPart*
            object (i.e. *self*) as a text string:
        """

        price_breaks_texts: List[str] = list()
        for price_break in self.price_breaks:
            price_breaks_texts.append("{0}/${1:.3f}".
                                      format(price_break.quantity, price_break.price))
        price_breaks_text: str = " ".join(price_breaks_texts)
        return price_breaks_text

    # VendorPart.xml_lines_append():
    def xml_lines_append(self, xml_lines: List[str], indent: str, tracing: str = "") -> None:
        # Grab some values from *vendor_part* (i.e. *self*):
        vendor_part: VendorPart = self
        quantity_available: int = vendor_part.quantity_available
        price_breaks: List[PriceBreak] = vendor_part.price_breaks
        vendor_name: str = vendor_part.vendor_name
        vendor_part_name: str = vendor_part.vendor_part_name
        timestamp: int = vendor_part.timestamp

        # Output the `<VendorPart ...>` tag first:
        xml_lines.append(f'{indent}<VendorPart '
                         f'quantity_available="{quantity_available}\" '
                         f'timestamp="{timestamp}" '
                         f'vendor_name="{Encode.to_attribute(vendor_name)}\" '
                         f'vendor_part_name="{Encode.to_attribute(vendor_part_name)}">')

        # Output the nested `<PriceBreak ...>` tags:
        next_indent: str = indent + " "
        price_break: PriceBreak
        for price_break in price_breaks:
            price_break.xml_lines_append(xml_lines, next_indent)

        # Close out with the `</VendorPart>` tag:
        xml_lines.append(f"{indent}</VendorPart>")

    # VendorPart.xml_parse():
    @staticmethod
    @trace(2)
    def xml_parse(vendor_part_tree: etree._Element, actual_part: ActualPart,
                  tracing: str = "") -> "VendorPart":
        # Pull out the attribute values:
        attributes_table: Dict[str, str] = vendor_part_tree.attrib
        timestamp: int = int(float(attributes_table["timestamp"]))
        vendor_name: str = attributes_table["vendor_name"]
        vendor_part_name: str = attributes_table["vendor_part_name"]
        quantity_available: int = int(attributes_table["quantity_available"])

        price_breaks: List[PriceBreak] = []
        price_break_trees: List[etree._Element] = list(vendor_part_tree)
        price_break_tree: etree._Element
        for price_break_tree in price_break_trees:
            price_break: PriceBreak = PriceBreak.xml_parse(price_break_tree)
            price_breaks.append(price_break)

        vendor_part: VendorPart = VendorPart(actual_part, vendor_name, vendor_part_name,
                                             quantity_available, price_breaks, timestamp)
        return vendor_part


if __name__ == "__main__":
    main()

#
# Notes on using tab widgets:
# * Tabs are actually named in the parent tab widget (1 level up.)
# * To add a tab, hover the mouse over an existing tab, right click mouse, and select
#   Insert page.


# PySide2 TableView Video: https://www.youtube.com/watch?v=4PkPezdpO90
# Associatied repo: https://github.com/vfxpipeline/filebrowser

# [Python Virtual Environments](https://realpython.com/python-virtual-environments-a-primer/)
#
# * Use [Virtual Environment Wrapper](https://virtualenvwrapper.readthedocs.io/en/latest/)
#   to make life easier.
#
# * Add to `~/.bashrc`:
#
#        # Setup for Python virtual enviroments:
#        export WORKON_HOME=$HOME/.virtualenvs             # Standard place to store virtual env.'s
#        export VIRTUALENVWRAPPER_PYTHON=/usr/bin/python3  # Make sure you point to correct Python
#        export VIRTUALENVWRAPPER_WORKON_CD=1              # Forces `workon` to cd to project dir.
#        source /usr/local/bin/virtualenvwrapper.sh        # Actually `which virtualenvwrapper.sh`
#
# * Run the following commands in your shell:
#
#        sudo -H pip3 install virtualenv                   # Should already be installed
#        sudo -H pip3 install virtualenvwrapper            # This makes life easier.
#        source ~/.bashrc
#
# * The following shell commands now exist:
#   * mkvirtualenv -a *project_directory* *env_name*: Create new virtual environment named
#     *env_name* with *project_directory* as the home directory to go to when initially
#     activated.  (Requires `export VIRTUALENVWRAPPER_WORKON_CD=1` to be set in `~/.bashrc`.
#   * workon: List all available virtual environments.
#   * workon *env_name*: Switch over to virtual environment *env_name*.
#   * lssitepackages: List the packages installed in the current virtual environment.
#   * Read the documentation for more commands.
#
# * There is a section about "Using Different Versions of Python" that looks interesting.
#
# Python Packaging Tutorial (2.x):
#     https://python-packaging.readthedocs.io/en/latest/
# [Python Packaging](https://packaging.python.org/tutorials/packaging-projects/)
#   *
# Another URL (talks about PyPlace accounts -- dated 2009, Python 2.6):
#     https://pythonhosted.org/an_example_pypi_project/setuptools.html
# [Configuring `~/.pypirc`](https://truveris.github.io/articles/configuring-pypirc/)
# [Python Plugins](https://packaging.python.org/guides/creating-and-discovering-plugins/)
# [Python Plugins Tutorial](https://amir.rachum.com/blog/2017/07/28/python-entry-points/)
