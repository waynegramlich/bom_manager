# # BOM Manager
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

import argparse
# from bs4 import BeautifulSoup     # HTML/XML data structucure searching
# import bs4
# import copy                       # Used for the old pickle code...
import csv
# from currency_converter import CurrencyConverter         # Currency converter
from functools import partial
# import fnmatch                    # File Name Matching
import glob                       # Unix/Linux style command line file name pattern matching
import io                         # I/O stuff
import lxml.etree as etree
# import pickle                     # Python data structure pickle/unpickle
import pkg_resources              # Used to find plug-ins.
# import pkgutil
from bom_manager.tracing import trace, trace_level_get, trace_level_set
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import (QApplication, QComboBox, QLineEdit, QMainWindow,
                               QPlainTextEdit, QPushButton,
                               QTableWidget, QTableWidgetItem, QWidget)  # QTreeView
from PySide2.QtCore import (QAbstractItemModel, QCoreApplication, QFile, QItemSelectionModel,
                            QModelIndex, Qt)
from PySide2.QtGui import (QClipboard,)
import os
import re                         # Regular expressions
# import requests                   # HTML Requests
# import sexpdata                   # (LISP) S_EXpresson Data
# from sexpdata import Symbol       # (LISP) S-EXpression Symbol
# import subprocess
import sys
import time                       # Time package
import webbrowser
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
def main(tracing=""):
    # Verify argument types:
    assert isinstance(tracing, str)

    # Run the *Encode* class unit tests:
    Encode.test()

    # Set up command line *parser* and parse it into *parsed_arguments* dict:
    parser = argparse.ArgumentParser(description="Bill of Materials (BOM) Manager.")
    parser.add_argument("-b", "--bom", action="append", default=[],
                        help="Bom file (.csv, .net). Preceed with 'NUMBER:' to increase count. ")
    parser.add_argument("-s", "--search", default="searches",
                        help="BOM Manager Searches Directory.")
    parser.add_argument("-o", "--order", default=os.path.join(os.getcwd(), "order"),
                        help="Order Information Directory")
    parser.add_argument("-v", "--verbose", action="count",
                        help="Set tracing level (defaults to 0 which is off).")

    # Now parse the command line arguments:
    parsed_arguments = vars(parser.parse_args())

    trace_level_set(parsed_arguments["verbose"])

    # Fill in the *pandas* list with *Panda* objects for doing pricing and availabity checking:
    pandas = list()
    entry_point_key = "bom_manager_panda_get"
    for index, entry_point in enumerate(pkg_resources.iter_entry_points(entry_point_key)):
        entry_point_name = entry_point.name
        if tracing:
            print(f"{tracing}Panda_Entry_Point[{index}]: '{entry_point_name}'")
        assert entry_point_name == "panda_get"
        panda_get = entry_point.load()
        assert callable(panda_get)
        panda = panda_get()
        assert isinstance(panda, Panda)
        pandas.append(panda)

    # Fill in the *cads* list with *CAD* objects for reading in :
    cads = list()
    entry_point_key = "bom_manager_cad_get"
    for index, entry_point in enumerate(pkg_resources.iter_entry_points(entry_point_key)):
        entry_point_name = entry_point.name
        if tracing:
            print(f"{tracing}Cad_Entry_Point[{index}]: '{entry_point_name}'")
        assert entry_point_name == "cad_get"
        cad_get = entry_point.load()
        assert callable(cad_get)
        cad = cad_get()
        assert isinstance(cad, Cad)
        cads.append(cad)

    # Now create the *order* object.  It is created here because we need *order*
    # for dealing with *bom_file_names* immediately below:
    order_root = parsed_arguments["order"]
    order = Order(order_root, cads, pandas)
    if tracing:
        print(f"{tracing}order_created")

    # Deal with *bom_file_names* from *parsed_arguments*:
    bom_file_names = parsed_arguments["bom"]
    for bom_file_name in bom_file_names:
        if bom_file_name.endswith(".net") or bom_file_name.endswith(".csv"):
            # We have a `.net` file name:
            colon_index = bom_file_name.find(':')
            # print(f"colon_index={colon_index}")
            count = 1
            if colon_index >= 0:
                count = int(bom_file_name[:colon_index])
                bom_file_name = bom_file_name[colon_index:]
            # print(f"count={count}")
            assert os.path.isfile(bom_file_name), f"'{bom_file_name}' does not exist."
            paths = os.path.split(bom_file_name)
            # print(f"paths={paths}")
            base_name = paths[-1]
            # print(f"base_name='{base_name}'")
            name = base_name[:-4]
            # print(f"name='{name}'")
            revision_letter = 'A'
            if len(paths) >= 2:
                revision_letter = paths[-2][-1].upper()
            # print(f"revision_letter='{revision_letter}'")

            # Create an order project:
            order.project_create(name, revision_letter, bom_file_name, count, tracing=tracing)
        else:
            print(f"Ignoring file '{bom_file_name}' does not with '.net' or '.csv' suffix.")
    if tracing:
        print(f"{tracing}nets processed")

    collection_directories = list()

    tables = list()
    if False:
        # Read in each *table_file_name* in *arguments* and append result to *tables*:
        # for table_file_name in arguments:
        if False:
            # Verify that *table_file_name* exists and has a `.xml` suffix:
            table_file_name = None
            assert os.path.isfile(table_file_name), "'{0}' does not exist".format(table_file_name)
            assert table_file_name.endswith(".xml"), (
              "'{0}' does not have a .xml suffix".format(table_file_name))

            # Read in *table_file_name* as a *table* and append to *tables* list:
            with open(table_file_name) as table_read_file:
                table_input_text = table_read_file.read()
            table_tree = etree.fromstring(table_input_text)
            table = Table(file_name=table_file_name, table_tree=table_tree, csv_file_name="")
            tables.append(table)

            # For debugging only, write *table* out to the `/tmp` directory:
            debug = False
            debug = True
            if debug:
                table_write_text = table.to_xml_string()
                with open(os.path.join(order_root, table_file_name), "w") as table_write_file:
                    table_write_file.write(table_write_text)

    searches_root = os.path.abspath(parsed_arguments["search"])

    # Now create the *tables_editor* graphical user interface (GUI) and run it:
    if tracing:
        print(f"{tracing}searches_root='{searches_root}'")
    tables_editor = TablesEditor(tables, collection_directories, searches_root, order)

    # Start up the GUI:
    tables_editor.run()

    # When we get here, *tables_editor* has stopped running and we can return.
    if tracing:
        print(f"{tracing}<=main()")

    return 0


# "se" stands for "S Expression":
def se_find(se, base_name, key_name):
    """ {}: Find *key_name* in *se* and return its value. """

    # *se* is a list of the form:
    #
    #        [base_name, [key1, value1], [key2, value2], ..., [keyN, valueN]]
    #
    # This routine searches through the *[keyI, valueI]* pairs
    # and returnts the *valueI* that corresponds to *key_name*.

    # Check argument types:
    # assert isinstance(se, list)
    # assert isinstance(base_name, str)
    # assert isinstance(key_name, str)

    # Do some sanity checking:
    # size = len(se)
    # assert size > 0
    # assert se[0] == Symbol(base_name)

    result = None
    # key_symbol = Symbol(key_name)
    # for index in range(1, size):
    #     sub_se = se[index]
    #     if len(sub_se) > 0 and sub_se[0] == key_symbol:
    #         result = sub_se
    #         break
    return result


def text2safe_attribute(text):
    # Verify argument types:
    assert isinstance(text, str)

    # Sweep across *text* one *character* at a time performing any neccesary conversions:
    new_characters = list()
    for character in text:
        new_character = character
        if character == '&':
            new_character = "&amp;"
        elif character == '<':
            new_character = "&lt;"
        elif character == '>':
            new_character = "&gt;"
        elif character == "'":
            new_character = "&apos;"
        elif character == '"':
            new_character = "&quot;"
        new_characters.append(new_character)
    safe_attribute = "".join(new_characters)
    return safe_attribute


def text_filter(text, function):
    # Verify argument types:
    assert isinstance(text, str)
    assert callable(function)

    return "".join([character for character in text if function(character)])


# ActualPart:
class ActualPart:
    # An *ActualPart* represents a single manufacturer part.
    # A list of vendor parts specifies where the part can be ordered from.

    ACTUAL_PART_EXCHANGE_RATES = dict()

    # ActualPart.__init__():
    def __init__(self, manufacturer_name, manufacturer_part_name):
        """ *ActualPart*: Initialize *self* to contain *manufacturer* and
            *manufacturer_part_name*. """

        # Verify argument_types:
        assert isinstance(manufacturer_name, str)
        assert isinstance(manufacturer_part_name, str)

        # Create the *key* for *actual_part* (i.e. *self*):
        actual_part = self
        key = (manufacturer_name, manufacturer_part_name)

        # Load up *self*:
        actual_part.manufacturer_name = manufacturer_name
        actual_part.manufacturer_part_name = manufacturer_part_name

        actual_part.key = key
        # Fields used by algorithm:
        actual_part.quantity_needed = 0
        actual_part.vendor_parts = []
        actual_part.selected_vendor_part = None

    # ActualPart.__eq__():
    def __eq__(self, actual_part2, tracing=""):
        # Verify argument types:
        assert isinstance(actual_part2, ActualPart)

        actual_part1 = self
        equal = actual_part1.key == actual_part2.key
        if equal:
            # Extract *vendor_parts* making sure that they are sorted:
            vendor_parts1 = actual_part1.sorted_vendor_parts_get()
            vendor_parts2 = actual_part2.sorted_vendor_parts_get()
            equal &= len(vendor_parts1) == len(vendor_parts2)
            if equal:
                for index, vendor_part1 in enumerate(vendor_parts1):
                    vendor_part2 = vendor_parts2[index]
                    if vendor_part1 != vendor_part2:
                        equal = False
                        break

        # Wrap up requested any *tracing* and return *equal*:
        if tracing:
            print(f"{tracing}<=ActualPart.__eq__({actual_part1.key}, {actual_part2.key})=>{equal}")
        return equal

    # ActualPart.sorted_vendor_parts_get():
    def sorted_vendor_parts_get(self):
        actual_part = self
        vendor_parts = actual_part.vendor_parts
        vendor_parts.sort(key=lambda vendor_part: vendor_part.vendor_key)
        return vendor_parts

    # ActualPart.vendor_names_restore():
    def vendor_names_load(self, vendor_names_table, excluded_vendor_names):
        """ *ActualPart*:*: Add each possible to vendor name for the
            *ActualPart* object (i.e. *self*) to *vendor_names_table*:
        """

        # Verify argument types:
        assert isinstance(vendor_names_table, dict)
        assert isinstance(excluded_vendor_names, dict)

        # Add the possible vendor names for *vendor_part* to
        # *vendor_names_table*:
        for vendor_part in self.vendor_parts:
            vendor_name = vendor_part.vendor_name
            if vendor_name not in excluded_vendor_names:
                vendor_names_table[vendor_name] = None

    # ActualPart.vendor_part_append():
    def vendor_part_append(self, vendor_part):
        """ *ActualPart: Append *vendor_part* to the vendor parts of *self*. """

        actual_part = self
        tracing = False
        tracing = (actual_part.manufacturer_name == "Pololu" and
                   actual_part.manufacturer_part_name == "S18V20F6)")
        if tracing:
            print("appending part")
            assert False
        assert isinstance(vendor_part, VendorPart)
        actual_part.vendor_parts.append(vendor_part)

    # ActualPart.vendor_parts_restore():
    def vendor_parts_restore(self, order, tracing=""):
        # Verify argument types:
        assert isinstance(order, Order)
        assert isinstance(tracing, str)

        # actual_part = self
        result = False
        # order_root = order.root
        # vendor_searches_root = order.vendor_searches_root
        # xml_base_name = actual_part.name + ".xml"
        # xml_file_name = os.path.join(vendor_searches_root, xml_base_name)

        # Wrap up any requested *tracing*:
        if tracing:
            print(f"{tracing}ActualPart.vendor_parts_restore(*)=>{result}")
        return result

    # ActualPart.xml_lines_append():
    def xml_lines_append(self, xml_lines, indent):
        # Verify argument types:
        assert isinstance(xml_lines, list)
        assert isinstance(indent, str)

        # Grab some values from *actual_part* (i.e. *self*):
        actual_part = self
        manufacturer_name = actual_part.manufacturer_name
        manufacturer_part_name = actual_part.manufacturer_part_name
        vendor_parts = actual_part.vendor_parts

        # Output the `<ActualPart ...>` tag first:
        xml_lines.append(f'{indent}<ActualPart '
                         f'manufacturer_name="{Encode.to_attribute(manufacturer_name)}" '
                         f'manufacturer_part_name="{Encode.to_attribute(manufacturer_part_name)}">')

        # Output the nested `<VendorPart ...>` tags:
        next_indent = indent + " "
        for vendor_part in vendor_parts:
            vendor_part.xml_lines_append(xml_lines, next_indent)

        # Close out with the `</ActualPart>` tag:
        xml_lines.append(f"{indent}</ActualPart>")

    # ActualPart.xml_parse():
    @staticmethod
    def xml_parse(actual_part_tree):
        # Verify argument types:
        assert isinstance(actual_part_tree, etree._Element)

        # Grab the attribute information out of *actual_part_tree*:
        assert actual_part_tree.tag == "ActualPart"
        attributes_table = actual_part_tree.attrib
        manufacturer_name = attributes_table["manufacturer_name"]
        manufacturer_part_name = attributes_table["manufacturer_part_name"]
        vendor_part_trees = list(actual_part_tree)

        # Create *actual_part* with empty *vendor_parts*:
        actual_part = ActualPart(manufacturer_name, manufacturer_part_name)
        vendor_parts = actual_part.vendor_parts

        # Process all of the `<VendorPart ...>` tags:
        for vendor_part_tree in vendor_part_trees:
            vendor_part = VendorPart.xml_parse(vendor_part_tree, actual_part)
            vendor_parts.append(vendor_part)
        return actual_part


# Cad:
class Cad:
    # Cad Stands for Computer Aided Design:

    # Cad.__init__():
    def __init__(self, name, tracing=""):
        # Verify argument types:
        if tracing:
            print(f"{tracing}=>Cad.__init__('{name}')")

        # Wrap up any argument types:
        if tracing:
            print(f"{tracing}<=Cad.__init__('{name}')")


# ComboEdit:
class ComboEdit:
    """ A *ComboEdit* object repesents the GUI controls for manuipulating a combo box widget.
    """

    # *WIDGET_CALLBACKS* is defined at the end of this class after all of the callback routines
    # are defined.
    WIDGET_CALLBACKS = dict()

    # ComboEdit.__init__():
    def __init__(self, name, tables_editor, items,
                 new_item_function, current_item_set_function, comment_get_function,
                 comment_set_function, is_active_function, tracing="", **widgets):
        """ Initialize the *ComboEdit* object (i.e. *self*.)

        The arguments are:
        * *name*: A name for the *ComboEdit* object (i.e. *self*) for debugging.
        * *tables_editor*: The root *TablesEditor* object.
        * *items*: A list of item objects to manage.
        * *new_item_function*: A function that is called to create a new item.
        * *is_active_function*: A function that returns *True* if combo box should be active.
        * *current_item_set_function*: A function that is called each time the current item is set.
        * *comment_get_function*: A function that is called to get the comment text.
        * *comment_set_function*: A function that is called to set the comment new comment text.
        * *tracing* (optional): The amount to indent when tracing otherwise *None* for no tracing:
        * *widgets*: A dictionary of widget names to widgets.  The following widget names
          are required:
          * "combo_box":    The *QComboBox* widget to be edited.
          * "comment_text": The *QComboPlainText* widget for comments.
          * "delete_button: The *QPushButton* widget that deletes the current entry.
          * "first_button": The *QPushButton* widget that moves to the first entry.
          * "last_button":  The *QPushButton* widget that moves to the last entry.
          * "line_edit":    The *QLineEdit* widget that supports new entry names and entry renames.
          * "next_button":  The *QPushButton* widget that moves to the next entry.
          * "new_button":   The *QPushButton* widget that create a new entry.
          * "previous_button": The *QPushButton* widget that moves tot the pervious entry.
          * "rename_button": The *QPushButton* widget that   rename_button_clicked,
        """

        # Verify argument types:
        assert isinstance(name, str)
        assert isinstance(items, list)
        assert callable(new_item_function)
        assert callable(current_item_set_function)
        assert callable(comment_get_function)
        assert callable(comment_set_function)
        assert callable(is_active_function)
        assert isinstance(tracing, str)
        widget_callbacks = ComboEdit.WIDGET_CALLBACKS
        widget_names = list(widget_callbacks)
        for widget_name, widget in widgets.items():
            assert widget_name in widget_names, (
              "Invalid widget name '{0}'".format(widget_name))
            assert isinstance(widget, QWidget), (
              "'{0}' is not a QWidget {1}".format(widget_name, widget))

        # Load some values into *combo_edit* (i.e. *self*):
        combo_edit = self
        combo_edit.comment_get_function = comment_get_function
        combo_edit.comment_set_function = comment_set_function
        combo_edit.comment_position = 0
        combo_edit.current_item_set_function = current_item_set_function
        combo_edit.is_active_function = is_active_function
        combo_edit.items = items
        combo_edit.name = name
        combo_edit.new_item_function = new_item_function
        combo_edit.tables_editor = tables_editor

        # Set the current item after *current_item_set_function* has been set.
        combo_edit.current_item_set(items[0] if len(items) > 0 else None)

        # Stuff each *widget* into *combo_edit* and connect the *widget* to the associated
        # callback routine from *widget_callbacks*:
        for widget_name, widget in widgets.items():
            # Store *widget* into *combo_edit* with an attribute name of *widget_name*:
            setattr(combo_edit, widget_name, widget)

            # Lookup the *callback* routine from *widget_callbacks*:
            callback = widget_callbacks[widget_name]

            # Using *widget* widget type, perform appropraite signal connection to *widget*:
            if isinstance(widget, QComboBox):
                # *widget* is a *QcomboBox* and generate a callback each time it changes:
                assert widget_name == "combo_box"
                widget.currentTextChanged.connect(partial(callback, combo_edit))
            elif isinstance(widget, QLineEdit):
                # *widget* is a *QLineEdit* and generate a callback for each character changed:
                assert widget_name == "line_edit"
                widget.textEdited.connect(partial(callback, combo_edit))
            elif isinstance(widget, QPushButton):
                # *widget* is a *QPushButton* and generat a callback for each click:
                widget.clicked.connect(partial(callback, combo_edit))
            elif isinstance(widget, QPlainTextEdit):
                # *widget* is a *QPushButton* and generate a callback for each click:
                widget.textChanged.connect(partial(callback, combo_edit))
                widget.cursorPositionChanged.connect(
                                                    partial(ComboEdit.position_changed, combo_edit))
            else:
                assert False, "'{0}' is not a valid widget".format(widget_name)

        # Wrap-up any requested *tracing*:
        if tracing:
            print("{0}<=ComboEdit.__init__(*, {1}, ...)".format(tracing, name))

    # ComboEdit.combo_box_changed():
    def combo_box_changed(self, new_name):
        """ Callback method invoked when the *QComboBox* widget changes:

        The arguments are:
        * *new_name*: The *str* that specifies the new *QComboBox* widget value selected.
        """

        # Verify argument types:
        assert isinstance(new_name, str)

        # Only do something if we are not already *in_signal*:
        combo_edit = self
        tables_editor = combo_edit.tables_editor
        if not tables_editor.in_signal:
            tables_editor.in_signal = True

            # Perform any requested signal tracing:
            trace_signals = tables_editor.trace_signals
            if trace_signals:
                print("=>ComboEdit.combo_box_changed('{0}', '{1}')".
                      format(combo_edit.name, new_name))

                # Grab *attributes* (and compute *attributes_size*) from *combo_edit* (i.e. *self*):
                items = combo_edit.items
                for index, item in enumerate(items):
                    if item.name == new_name:
                        # We have found the new *current_item*:
                        print("  items[{0}] '{1}'".format(index, item.name))
                        combo_edit.current_item_set(item)
                        break

            # Update the the GUI:
            tables_editor.update()

            # Wrap up any signal tracing:
            if trace_signals:
                print("<=ComboEdit.combo_box_changed('{0}', '{1}')\n".
                      format(combo_edit.name, new_name))
            tables_editor.in_signal = False

    # ComboEdit.comment_text_changed():
    def comment_text_changed(self):
        # Do nothing if we are in a signal:
        combo_edit = self
        tables_editor = combo_edit.tables_editor
        in_signal = tables_editor.in_signal
        if not in_signal:
            tables_editor.in_signal = True

            # Perform any requested signal tracing:
            trace_signals = tables_editor.trace_signals
            if trace_signals:
                print("=>ComboEdit.comment_text_changed()")

            # Extract *actual_text* from the *comment_plain_text* widget:
            comment_text = combo_edit.comment_text
            actual_text = comment_text.toPlainText()
            cursor = comment_text.textCursor()
            position = cursor.position()

            # Store *actual_text* into *current_comment* associated with *current_parameter*:
            item = combo_edit.current_item_get()
            if item is not None:
                combo_edit.comment_set_function(item, actual_text, position)

            # Force the GUI to be updated:
            tables_editor.update()

            # Wrap up any signal tracing:
            if trace_signals:
                print(" <=ComboEditor.comment_text_changed():{0}\n".format(cursor.position()))
            tables_editor.in_signal = False

    # ComboEdit.current_item_get():
    def current_item_get(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Perform any requested tracing:
        combo_edit = self
        current_item = combo_edit.current_item
        items = combo_edit.items

        # In general, we just want to return *current_item*. However, things can get
        # messed up by accident.  So we want to be darn sure that *current_item* is
        # either *None* or a valid item from *items*.

        # Step 1: Search for *current_item* in *tems:
        new_current_item = None
        for item in items:
            if item is current_item:
                # Found it:
                new_current_item = current_item

        # Just in case we did not find it, we attempt to grab the first item in *items* instead:
        if new_current_item is None and len(items) >= 1:
            new_current_item = items[0]

        # If the *current_item* has changed, we let the parent know:
        if new_current_item is not current_item:
            combo_edit.current_item_set(new_current_item)

        # Wrap up any requested *tracing*:
        if tracing:
            print("{0}=>ComboEdit.current_item_get".format(tracing, combo_edit.name))
        return new_current_item

    # ComboEdit.current_item_set():
    def current_item_set(self, current_item, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Perform any requested *tracing*:
        combo_edit = self
        combo_edit.current_item = current_item
        combo_edit.current_item_set_function(current_item)

    # ComboEdit.delete_button_clicked():
    def delete_button_clicked(self):
        # Perform any requested tracing from *combo_edit* (i.e. *self*):
        combo_edit = self
        tables_editor = combo_edit.tables_editor
        trace_signals = tables_editor.trace_signals
        if trace_signals:
            print("=>ComboEdit.delete_button_clicked('{0}')".format(combo_edit.name))

        # Find the matching *item* in *items* and delete it:
        tables_editor.in_signal = True
        items = combo_edit.items
        items_size = len(items)
        current_item = combo_edit.current_item_get()
        for index, item in enumerate(items):
            if item == current_item:
                # Delete the *current_item* from *items*:
                del items[index]
                items_size = len(items)

                # Update *current_item* in *combo_edit*:
                if 0 <= index < items_size:
                    current_item = items[index]
                elif 0 <= index - 1 < items_size:
                    current_item = items[index - 1]
                else:
                    current_item = None
                combo_edit.current_item_set(current_item)
                break

        # Update the GUI:
        tables_editor.update()

        # Wrap up any requested tracing;
        if trace_signals:
            print("<=ComboEdit.delete_button_clicked('{0}')\n".format(combo_edit.name))
        tables_editor.in_signal = False

    # ComboEdit.first_button_clicked():
    def first_button_clicked(self):
        # Perform any tracing requested by *combo_edit* (i.e. *self*):
        combo_edit = self
        tables_editor = combo_edit.tables_editor
        trace_signals = tables_editor.trace_signals
        if trace_signals:
            print("=>ComboEdit.first_button_clicked('{0}')".format(combo_edit.name))

        # If possible, select the *first_item*:
        tables_editor.in_signal = True
        items = combo_edit.items
        items_size = len(items)
        if items_size > 0:
            first_item = items[0]
            combo_edit.current_item_set(first_item)

        # Update the user interface:
        tables_editor.update()

        # Wrap up any requested tracing:
        if trace_signals:
            print("<=ComboEdit.first_button_clicked('{0})\n".format(combo_edit.name))
        tables_editor.in_signal = False

    # ComboEdit.gui_update():
    def gui_update(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Perform any requested *tracing* of *combo_edit* (i.e. *self*):
        combo_edit = self

        # Grab the widgets from *combo_edit* (i.e. *self*):
        combo_box = combo_edit.combo_box
        delete_button = combo_edit.delete_button
        first_button = combo_edit.first_button
        last_button = combo_edit.last_button
        line_edit = combo_edit.line_edit
        new_button = combo_edit.new_button
        next_button = combo_edit.next_button
        previous_button = combo_edit.previous_button
        rename_button = combo_edit.rename_button

        # If *current_item* *is_a_valid_item* we can enable most of the item widgets:
        current_item = combo_edit.current_item_get()
        items = combo_edit.items
        items_size = len(items)
        is_a_valid_item = current_item is not None
        combo_box.setEnabled(is_a_valid_item)
        # if tracing:
        #    print("{0}current_item='{1}'".
        #      format(tracing, "None" if current_item is None else current_item.name))

        # Changing the *combo_box* generates a bunch of spurious callbacks to
        # *ComboEdit.combo_box_changed()* callbacks.  The *combo_box_being_updated* attribute
        # is set to *True* in *combo_edit* so that these spurious callbacks can be ignored.
        combo_edit.combo_box_being_updated = True
        # print("combo_edit.combo_box_being_updated={0}".
        #  format(combo_edit.combo_box_being_updated))

        # Empty out *combo_box* and then refill it from *items*:
        combo_box.clear()
        current_item_index = -1
        for index, item in enumerate(items):
            combo_box.addItem(item.name)
            # if tracing:
            #    print("{0}[{1}]: '{2}".format(tracing, index,
            #      "--" if item is None else item.name))
            if item is current_item:
                combo_box.setCurrentIndex(index)
                current_item_index = index
                if tracing:
                    print("{0}match".format(tracing))
                break
        assert not is_a_valid_item or current_item_index >= 0
        # print("current_item_index={0}".format(current_item_index))
        # print("items_size={0}".format(items_size))

        # Read the comment *current_text* out:
        if current_item is None:
            current_text = ""
            position = 0
        else:
            current_text, position = combo_edit.comment_get_function(
              current_item)

        # Make sure that *current_text* is being displayed by the *comment_text* widget:
        comment_text = combo_edit.comment_text
        previous_text = comment_text.toPlainText()
        if previous_text != current_text:
            comment_text.setPlainText(current_text)

        # Set the cursor to be at *position* in the *comment_text* widget.  *cursor* is a
        # copy of the cursor from *comment_text*.  *position* is loaded into *cursor* which
        # is then loaded back into *comment_text* to actually move the cursor position:
        cursor = comment_text.textCursor()
        cursor.setPosition(position)
        comment_text.setTextCursor(cursor)

        # Figure out if *_new_button_is_visible*:
        line_edit_text = line_edit.text()
        # print("line_edit_text='{0}'".format(line_edit_text))
        no_name_conflict = line_edit_text != ""
        for index, item in enumerate(items):
            item_name = item.name
            # print("[{0}] attribute_name='{1}'".format(index, item_name))
            if item_name == line_edit_text:
                no_name_conflict = False
                # print("new is not allowed")
        # print("no_name_conflict={0}".format(no_name_conflict))

        # If *current_attribute* *is_a_valid_attribute* we can enable most of the attribute
        # widgets.  The first, next, previous, and last buttons depend upon the
        # *current_attribute_index*:
        combo_box.setEnabled(is_a_valid_item)
        delete_button.setEnabled(is_a_valid_item)
        first_button.setEnabled(is_a_valid_item and current_item_index > 0)
        last_button.setEnabled(is_a_valid_item and current_item_index + 1 < items_size)
        new_button.setEnabled(no_name_conflict)
        next_button.setEnabled(is_a_valid_item and current_item_index + 1 < items_size)
        previous_button.setEnabled(is_a_valid_item and current_item_index > 0)
        next_button.setEnabled(is_a_valid_item and current_item_index + 1 < items_size)
        rename_button.setEnabled(no_name_conflict)

        # Wrap up any requeted *tracing*:
        if tracing:
            print("{0}<=ComboEdit.gui_update('{1}')".format(tracing, combo_edit.name))

    # ComboEdit.items_replace():
    def items_replace(self, new_items):
        # Verify argument types:
        assert isinstance(new_items, list)

        # Stuff *new_items* into *combo_item*:
        combo_item = self
        combo_item.items = new_items

    # ComboEdit.items_set():
    def items_set(self, new_items, update_function, new_item_function, current_item_set_function):
        # Verify argument types:
        assert isinstance(new_items, list)
        assert callable(update_function)
        assert callable(new_item_function)
        assert callable(current_item_set_function)

        # Load values into *items*:
        combo_edit = self
        combo_edit.current_item_set_function = current_item_set_function
        combo_edit.items = new_items
        combo_edit.new_item_function = new_item_function
        combo_edit.update_function = update_function

        # Set the *current_item* last to be sure that the call back occurs:
        combo_edit.current_item_set(new_items[0] if len(new_items) > 0 else None, "items_set")

    # ComboEdit.last_button_clicked():
    def last_button_clicked(self):
        # Perform any tracing requested by *combo_edit* (i.e. *self*):
        combo_edit = self
        tables_editor = combo_edit.tables_editor
        trace_signals = tables_editor.trace_signals
        if trace_signals:
            print("=>ComboEdit.last_button_clicked('{0}')".format(combo_edit.name))

        # If possible select the *last_item*:
        tables_editor.in_signal = True
        items = combo_edit.items
        items_size = len(items)
        if items_size > 0:
            last_item = items[-1]
            combo_edit.current_item_set(last_item)

        # Update the user interface:
        tables_editor.update()

        # Wrap up any requested tracing:
        if trace_signals:
            print("<=ComboEdit.last_button_clicked('{0}')\n".format(combo_edit.name))
        tables_editor.in_signal = False

    # ComboEdit.line_edit_changed():
    def line_edit_changed(self, text):
        # Verify argument types:
        assert isinstance(text, str)

        # Make sure that we are not already in a signal before doing anything:
        combo_edit = self
        tables_editor = combo_edit.tables_editor
        if not tables_editor.in_signal:
            tables_editor.in_signal = True

            # Perform any requested siginal tracing:
            trace_signals = tables_editor.trace_signals

            # Make sure that the *combo_edit* *is_active*:
            is_active = combo_edit.is_active_function()
            if not is_active:
                # We are not active, so do not let the user type anything in:
                line_edit = combo_edit.line_edit
                line_edit.setText("")  # Erase whatever was just typed in!

            # Now just update *combo_edit*:
            combo_edit.gui_update()

            # Wrap up any requested signal tracing:
            if trace_signals:
                print("<=ComboEditor.line_edit_changed('{0}')\n".format(text))
            tables_editor.in_signal = False

    # ComboEdit.item_append():
    def item_append(self, new_item, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Perform any requested *tracing*:

        # Append *item* to *items* and make it current for *combo_edit* (i.e. *self*):
        combo_edit = self
        items = combo_edit.items
        items.append(new_item)
        combo_edit.current_item_set(new_item)

    # ComboEdit.new_button_clicked():
    def new_button_clicked(self):
        # Perform any tracing requested by *combo_edit* (i.e. *self*):
        combo_edit = self
        tables_editor = combo_edit.tables_editor
        trace_signals = tables_editor.trace_signals

        # Grab some values from *combo_edit*:
        tables_editor.in_signal = True
        items = combo_edit.items
        line_edit = combo_edit.line_edit
        new_item_function = combo_edit.new_item_function
        print("items.id=0x{0:x}".format(id(items)))

        # Create a *new_item* and append it to *items*:
        new_item_name = line_edit.text()
        # print("new_item_name='{0}'".format(new_item_name))
        new_item = new_item_function(new_item_name)
        combo_edit.item_append(new_item)

        # Update the GUI:
        tables_editor.update()

        # Wrap up any requested signal tracing:
        if trace_signals:
            print("<=ComboEdit.new_button_clicked('{0}')\n".format(combo_edit.name))
        tables_editor.in_signal = False

    # ComboEdit.next_button_clicked():
    def next_button_clicked(self):
        # Perform any tracing requested by *combo_edit* (i.e. *self*):
        combo_edit = self
        tables_editor = combo_edit.tables_editor
        trace_signals = tables_editor.trace_signals

        # ...
        tables_editor.in_signal = True
        items = combo_edit.items
        items_size = len(items)
        current_item = combo_edit.current_item_get()
        for index, item in enumerate(items):
            if item == current_item:
                if index + 1 < items_size:
                    current_item = items[index + 1]
                break
        combo_edit.current_item_set(current_item)

        # Update the GUI:
        tables_editor.update()

        # Wrap up any requested tracing:
        if trace_signals:
            print("<=ComboEdit.next_button_clicked('{0}')\n".format(combo_edit.name))
        tables_editor.in_signal = False

    # ComboEdit.position_changed():
    def position_changed(self):
        # Do nothing if we already in a signal:
        combo_edit = self
        tables_editor = combo_edit.tables_editor
        if not tables_editor.in_signal:
            tables_editor.in_signal = True

            # Perform any requested signal tracing:
            trace_signals = tables_editor.trace_signals

            # Grab the *actual_text* and *position* from the *comment_text* widget and stuff
            # both into the comment field of *item*:
            item = combo_edit.current_item_get()
            comment_text = combo_edit.comment_text
            cursor = comment_text.textCursor()
            position = cursor.position()
            actual_text = comment_text.toPlainText()
            combo_edit.comment_set_function(item, actual_text, position)

            # Wrap up any signal tracing:
            tables_editor.in_signal = False

    # ComboEdit.previous_button_clicked():
    def previous_button_clicked(self):
        # Perform any tracing requested by *combo_edit* (i.e. *self*):
        combo_edit = self
        tables_editor = combo_edit.tables_editor
        trace_signals = tables_editor.trace_signals

        # ...
        tables_editor.in_signal = True
        items = combo_edit.items
        current_item = combo_edit.current_item_get()
        for index, item in enumerate(items):
            if item == current_item:
                if index > 0:
                    current_item = items[index - 1]
                break
        combo_edit.current_item_set(current_item)

        # Update the GUI:
        tables_editor.update()

        tables_editor.in_signal = False

    # ComboEdit.rename_button_clicked():
    def rename_button_clicked(self):
        # Perform any tracing requested by *combo_edit* (i.e. *self*):
        combo_edit = self
        tables_editor = combo_edit.tables_editor
        trace_signals = tables_editor.trace_signals

        tables_editor.in_signal = True
        combo_edit = self
        line_edit = combo_edit.line_edit
        new_item_name = line_edit.text()

        current_item = combo_edit.current_item_get()
        if current_item is not None:
            current_item.name = new_item_name

        # Update the GUI:
        tables_editor.update()

        tables_editor.in_signal = False

    # ComboEdit.WIDGET_CALLBACKS:
    # *WIDGET_CALLBACKS* is defined here **after** the actual callback routines are defined:
    WIDGET_CALLBACKS = {
      "combo_box":       combo_box_changed,
      "comment_text":    comment_text_changed,
      "delete_button":   delete_button_clicked,
      "first_button":    first_button_clicked,
      "last_button":     last_button_clicked,
      "line_edit":       line_edit_changed,
      "next_button":     next_button_clicked,
      "new_button":      new_button_clicked,
      "previous_button": previous_button_clicked,
      "rename_button":   rename_button_clicked,
    }


# Comment:
class Comment:

    # Comment.__init__():
    def __init__(self, tag_name, **arguments_table):
        # Verify argument types:
        assert isinstance(tag_name, str) and tag_name in \
         ("EnumerationComment", "ParameterComment", "TableComment", "SearchComment")
        is_comment_tree = "comment_tree" in arguments_table
        if is_comment_tree:
            assert len(arguments_table) == 1
            assert isinstance(arguments_table["comment_tree"], etree._Element)
        else:
            assert len(arguments_table) >= 2
            assert "language" in arguments_table and isinstance(arguments_table["language"], str)
            assert "lines" in arguments_table
            lines = arguments_table["lines"]
            for line in lines:
                assert isinstance(line, str)

        if is_comment_tree:
            comment_tree = arguments_table["comment_tree"]
            assert comment_tree.tag == tag_name, (
              "tag_name='{0}' tree_tag='{1}'".format(tag_name, comment_tree.tag))
            attributes_table = comment_tree.attrib
            assert "language" in attributes_table
            language = attributes_table["language"]
            text = comment_tree.text.strip()
            lines = text.split('\n')
            for index, line in enumerate(lines):
                lines[index] = line.strip().replace("<", "&lt;").replace(">", "&gt;")
        else:
            language = arguments_table["language"]
            lines = arguments_table["lines"]

        # Load up *table_comment* (i.e. *self*):
        comment = self
        comment.position = 0
        comment.language = language
        comment.lines = lines
        # print("Comment(): comment.lines=", tag_name, lines)

    # Comment.__eq__():
    def __eq__(self, comment2):
        # Verify argument types:
        assert isinstance(comment2, Comment)

        # Compare each field in *comment1* (i.e. *self*) with the corresponding field in *comment2*:
        comment1 = self
        language_equal = (comment1.language == comment2.language)
        lines_equal = (comment1.lines == comment2.lines)
        all_equal = (language_equal and lines_equal)
        # print("language_equal={0}".format(language_equal))
        # print("lines_equal={0}".format(lines_equal))
        return all_equal


# EnumerationComment:
class EnumerationComment(Comment):

    # EnumerationComment.__init__():
    def __init__(self, **arguments_table):
        # print("=>EnumerationComment.__init__()")
        enumeration_comment = self
        super().__init__("EnumerationComment", **arguments_table)
        assert isinstance(enumeration_comment.language, str)
        assert isinstance(enumeration_comment.lines, list)

    # EnumerationComment.__equ__():
    def __equ__(self, enumeration_comment2):
        assert isinstance(enumeration_comment2, EnumerationComment)
        return super.__eq__(enumeration_comment2)

    # EnumerationComment.xml_lines_append():
    def xml_lines_append(self, xml_lines, indent):
        # Verify argument types:
        assert isinstance(xml_lines, list)
        assert isinstance(indent, str)

        # Append and `<EnumerationComment>` an element to *xml_lines*:
        enumeration_comment = self
        language = enumeration_comment.language
        xml_lines.append(enumeration_comment.language,
                         f'{indent}<EnumerationComment language="{language}">')
        for line in enumeration_comment.lines:
            xml_lines.append('{0}  {1}'.format(indent, line))
        xml_lines.append('{0}</EnumerationComment>'.format(indent))


# Panda:
class Panda:
    # Panda stands for Pricing AND Availability:

    # Panda.__init__():
    def __init__(self, name, tracing=""):
        # Verify argument types:
        if tracing:
            print(f"{tracing}=>Panda.__init__('{name}')")

        # Wrap up any argument types:
        if tracing:
            print(f"{tracing}<=Panda.__init__('{name}')")


# ParameterComment:
class ParameterComment(Comment):

    # ParameterComment.__init__():
    def __init__(self, **arguments_table):
        # Verify argument types:
        is_comment_tree = "comment_tree" in arguments_table
        if is_comment_tree:
            assert isinstance(arguments_table["comment_tree"], etree._Element)
        else:
            assert "language" in arguments_table and isinstance(arguments_table["language"], str)
            assert ("long_heading" in arguments_table
                    and isinstance(arguments_table["long_heading"], str))
            assert "lines" in arguments_table
            lines = arguments_table["lines"]
            for line in lines:
                assert isinstance(line, str)
            arguments_count = 3
            has_short_heading = "short_heading" in arguments_table
            if has_short_heading:
                arguments_count += 1
                assert isinstance(arguments_table["short_heading"], str)
            assert len(arguments_table) == arguments_count

        if is_comment_tree:
            comment_tree = arguments_table["comment_tree"]
            attributes_table = comment_tree.attrib
            attributes_count = 2
            long_heading = attributes_table["longHeading"]
            if "shortHeading" in attributes_table:
                attributes_count += 1
                short_heading = attributes_table["shortHeading"]
            else:
                short_heading = None
            assert len(attributes_table) == attributes_count
        else:
            long_heading = arguments_table["long_heading"]
            lines = arguments_table["lines"]
            short_heading = arguments_table["short_heading"] if has_short_heading else None

        # Initailize the parent of *parameter_comment* (i.e. *self*).  The parent initializer
        # will fill in the *language* and *lines* fields:
        parameter_comment = self
        super().__init__("ParameterComment", **arguments_table)
        assert isinstance(parameter_comment.language, str)
        assert isinstance(parameter_comment.lines, list)

        # Initialize the remaining two fields that are specific to a *parameter_comment*:
        parameter_comment.long_heading = long_heading
        parameter_comment.short_heading = short_heading

    # ParameterComment.__equ__():
    def __eq__(self, parameter_comment2):
        # Verify argument types:
        assert isinstance(parameter_comment2, ParameterComment)

        parameter_comment1 = self
        language_equal = parameter_comment1.language == parameter_comment2.language
        lines_equal = parameter_comment1.lines == parameter_comment2.lines
        long_equal = parameter_comment1.long_heading == parameter_comment2.long_heading
        short_equal = parameter_comment1.short_heading == parameter_comment2.short_heading
        all_equal = language_equal and lines_equal and long_equal and short_equal
        return all_equal

    # ParameterComment.xml_lines_append():
    def xml_lines_append(self, xml_lines):
        parameter_comment = self
        xml_line = '        <ParameterComment language="{0}" longHeading="{1}"'.format(
          parameter_comment.language, parameter_comment.long_heading)
        short_heading = parameter_comment.short_heading
        if short_heading is not None:
            xml_line += ' shortHeading="{0}"'.format(short_heading)
        xml_line += '>'
        xml_lines.append(xml_line)
        for line in parameter_comment.lines:
            xml_lines.append('          {0}'.format(line))
        xml_lines.append('        </ParameterComment>')


# SearchComment:
class SearchComment(Comment):
    # SearchComment.__init()
    def __init__(self, **arguments_table):
        # Verify argument types:
        is_comment_tree = "comment_tree" in arguments_table
        if is_comment_tree:
            assert len(arguments_table) == 1
            assert isinstance(arguments_table["comment_tree"], etree._Element)
        else:
            assert len(arguments_table) == 2
            assert "language" in arguments_table and isinstance(arguments_table["language"], str)
            assert "lines" in arguments_table
            lines = arguments_table["lines"]
            assert isinstance(lines, list)
            for line in lines:
                assert isinstance(line, str)

        # There are no extra attributes above a *Comment* object, so we can just use the
        # intializer for the *Coment* class:
        super().__init__("SearchComment", **arguments_table)

    # SearchComment.xml_lines_append():
    def xml_lines_append(self, xml_lines, indent):
        # Verify argument types:
        assert isinstance(xml_lines, list)
        assert isinstance(indent, str)

        # Append the <SearchComment> element:
        search_comment = self
        lines = search_comment.lines
        xml_lines.append('{0}<SearchComment language="{1}">'.
                         format(indent, search_comment.language))
        for line in lines:
            xml_lines.append("{0}  {1}".format(indent, line))
        xml_lines.append('{0}</SearchComment>'.format(indent))


# TableComment:
class TableComment(Comment):

    # TableComment.__init__():
    def __init__(self, **arguments_table):
        # Verify argument types:
        is_comment_tree = "comment_tree" in arguments_table
        if is_comment_tree:
            assert len(arguments_table) == 1
            assert isinstance(arguments_table["comment_tree"], etree._Element)
        else:
            assert len(arguments_table) == 2
            assert "language" in arguments_table and isinstance(arguments_table["language"], str)
            assert "lines" in arguments_table
            lines = arguments_table["lines"]
            assert isinstance(lines, list)
            for line in lines:
                assert isinstance(line, str)

        # There are no extra attributes above a *Comment* object, so we can just use the
        # intializer for the *Coment* class:
        super().__init__("TableComment", **arguments_table)

    # TableComment.__equ__():
    def __equ__(self, table_comment2):
        # Verify argument types:
        assert isinstance(table_comment2, TableComment)
        return super().__eq__(table_comment2)

    # TableComment.xml_lines_append():
    def xml_lines_append(self, xml_lines, indent):
        # Verify argument types:
        assert isinstance(xml_lines, list)
        assert isinstance(indent, str)

        # Append the <TableComment...> element:
        table_comment = self
        xml_lines.append('{0}<TableComment language="{1}">'.format(indent, table_comment.language))
        for line in table_comment.lines:
            xml_lines.append('{0}  {1}'.format(indent, line))
        xml_lines.append('{0}</TableComment>'.format(indent))


# Encode:
class Encode:

    # Encode.from_attribute():
    @staticmethod
    def from_attribute(attribute):
        characters = list()
        attribute_size = len(attribute)
        index = 0
        while index < attribute_size:
            # Grab the *character* and compute the *next_index:
            character = attribute[index]
            next_index = index + 1

            # Determine if we have an HTML entity:
            if character == '&':
                # We do have an HTML entity; find the closing ';':
                # rest = attribute[index:]
                # print(f"rest='{rest}'")
                entity = ""
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
        text = "".join(characters)
        return text

    # Encode.from_file_name():
    @staticmethod
    def from_file_name(file_name):
        # Verify argument types:
        assert isinstance(file_name, str)

        # Construct a list of *characters* one at a time to join together into final *text*:
        characters = list()
        index = 0
        file_name_size = len(file_name)
        while index < file_name_size:
            # Dispatch on *character* and compute *next_index*:
            character = file_name[index]
            next_index = index + 1

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
                        hex_index = index + 2
                        next_index = index + 6
                    else:
                        # We have "%XX" to parse into a single *character*:
                        hex_index = index + 1
                        next_index = index + 3

                    # Extract the *hex_text* from *file_name* to parse:
                    assert next_index <= file_name_size, "'%' at end of string is wrong"
                    hex_text = file_name[hex_index:next_index]

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
        text = "".join(characters)
        return text

    # Encode.to_attribute():
    @staticmethod
    def to_attribute(text):
        assert isinstance(text, str)
        characters = list()
        ord_space = ord(' ')
        ord_tilde = ord('~')
        for character in text:
            ord_character = ord(character)
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
        attribute = "".join(characters)
        return attribute

    # Encode.to_file_name():
    @staticmethod
    def to_file_name(text):
        characters = list()
        ord_space = ord(' ')
        ord_tilde = ord('~')
        ord_del = ord('\xff')
        for character in text:
            # Dispatch on the integer *ord_character*:
            ord_character = ord(character)
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
        file_name = "".join(characters)
        return file_name

    # Encode.to_url():
    @staticmethod
    def to_url(text):
        # Convert *text* into the %XX encoding system used by URL's as per RFC 3986:
        return "".join([character if character.isalnum() or character in "-.!"
                        else "%0:02x".format(ord(character)) for character in text])

    # Encode.test():
    @staticmethod
    def test():
        printable_ascii = "".join([chr(index) for index in range(ord(' '), ord('~')+1)])
        Encode.test_both(printable_ascii)
        control_ascii = "".join([chr(index) for index in range(ord(' ')-1)]) + "\xff"
        Encode.test_both(control_ascii)
        unicode_characters = "\u03a9Ω\u03bcμ"
        Encode.test_both(unicode_characters)

    # Encode.test_attribute():
    @staticmethod
    def test_attribute(before_attribute):
        assert isinstance(before_attribute, str)
        # print(f"before_attribute='{before_attribute}'")
        attribute_text = Encode.to_attribute(before_attribute)
        # print(f"attribute_text='{attribute_text}'")
        after_attribute = Encode.from_attribute(attribute_text)
        # print(f"after_attribute='{after_attribute}'")
        Encode.test_compare(before_attribute, after_attribute)

    # Encode.test_both():
    @staticmethod
    def test_both(text):
        assert isinstance(text, str)
        Encode.test_attribute(text)
        Encode.test_file_name(text)

    # Encode.test_compare():
    @staticmethod
    def test_compare(text1, text2):
        # Verify argument types:
        assert isinstance(text1, str)
        assert isinstance(text2, str)

        if text1 != text2:
            text1_size = len(text1)
            text2_size = len(text2)
            text_size = min(text1_size, text2_size)
            for index, character in enumerate(range(text_size)):
                character1 = text1[index]
                character2 = text2[index]
                assert character1 == character2, (f"Mismatch at index={index}"
                                                  f" '{character1}' != '{character2}'"
                                                  f" text1='{text1}' text2='{text2}'")
            assert text1_size == text2_size

    # Encode.test_file_name():
    @staticmethod
    def test_file_name(before_text):
        assert isinstance(before_text, str)
        file_name_text = Encode.to_file_name(before_text)
        after_text = Encode.from_file_name(file_name_text)
        Encode.test_compare(before_text, after_text)


# Enumeration:
class Enumeration:

    # Enumeration.__init__():
    def __init__(self, **arguments_table):
        is_enumeration_tree = "enumeration_tree" in arguments_table
        if is_enumeration_tree:
            assert isinstance(arguments_table["enumeration_tree"], etree._Element)
        else:
            assert len(arguments_table) == 2
            assert "name" in arguments_table
            assert "comments" in arguments_table
            comments = arguments_table["comments"]
            for comment in comments:
                assert isinstance(comment, EnumerationComment)

        if is_enumeration_tree:
            enumeration_tree = arguments_table["enumeration_tree"]
            assert enumeration_tree.tag == "Enumeration"
            attributes_table = enumeration_tree.attrib
            assert len(attributes_table) == 1
            assert "name" in attributes_table
            name = attributes_table["name"]
            comments_tree = list(enumeration_tree)
            comments = list()
            for comment_tree in comments_tree:
                comment = EnumerationComment(comment_tree=comment_tree)
                comments.append(comment)
            assert len(comments) >= 1
        else:
            name = arguments_table["name"]
            comments = arguments_table["comments"]

        # Load value into *enumeration* (i.e. *self*):
        enumeration = self
        enumeration.name = name
        enumeration.comments = comments

    # Enumeration.__eq__():
    def __eq__(self, enumeration2):
        # Verify argument types:
        assert isinstance(enumeration2, Enumeration)

        enumeration1 = self
        name_equal = (enumeration1.name == enumeration2.name)
        comments_equal = (enumeration1.comments == enumeration2.comments)
        return name_equal and comments_equal

    # Enumeration.xml_lines_append():
    def xml_lines_append(self, xml_lines, indent):
        # Verify argument types:
        assert isinstance(xml_lines, list)
        assert isinstance(indent, str)

        # Append an `<Enumeration>` element to *xml_lines*:
        enumeration = self
        name = enumeration.name
        name_attribute = Encode.to_attribute(name)
        xml_lines.append(f'{indent}<Enumeration name="{name_attribute}">')
        for comment in enumeration.comments:
            comment.xml_lines_append(xml_lines, indent + "  ")
        xml_lines.append(f'{indent}</Enumeration>')


# Filter:
class Filter:

    # Filter.__init__():
    def __init__(self, **arguments_table):
        # Verify argument types:
        is_filter_tree = "tree" in arguments_table
        arguments_table_size = len(arguments_table)
        if is_filter_tree:
            assert arguments_table_size == 2
            assert "table" in arguments_table
        else:
            assert arguments_table_size == 4
            assert "parameter" in arguments_table
            assert "table" in arguments_table
            assert "use" in arguments_table
            assert "select" in arguments_table

        # Dispatch on *is_filter_tree*:
        if is_filter_tree:
            # Grab *tree* and *table* out of *arguments_table*:
            tree = arguments_table["tree"]
            assert isinstance(tree, etree._Element)
            table = arguments_table["table"]
            assert isinstance(table, Table)

            # Grab the *parameter_name* and *use* from *filter_tree*:
            attributes_table = tree.attrib
            assert len(attributes_table) == 3

            # Extrace *use* from *attributes_table*:
            assert "use" in attributes_table
            use_text = attributes_table["use"].lower()
            if use_text == "true":
                use = True
            elif use_text == "false":
                use = False
            else:
                assert False

            # Extract the *match* from *attributes_table*:
            assert "select" in attributes_table
            select = attributes_table["select"]

            # Extract *parameter* from *attributes_table* and *table*:
            assert "name" in attributes_table
            parameter_name = attributes_table["name"]
            parameters = table.parameters
            match_parameter = None
            for parameter in parameters:
                if parameter.name == parameter_name:
                    match_parameter = parameter
                    break
            else:
                assert False
            parameter = match_parameter
        else:
            # Just grab *table*, *parameter*, *use*, and *select* directly from *arguments_table*:
            table = arguments_table["table"]
            assert isinstance(table, Table)
            parameter = arguments_table["parameter"]
            assert isinstance(parameter, Parameter)
            use = arguments_table["use"]
            assert isinstance(use, bool)
            select = arguments_table["select"]
            assert isinstance(select, str)

            # Make sure that *parameter* is in *parameters*:
            parameter_name = parameter.name
            parameters = table.parameters
            for parameter in parameters:
                if parameter.name == parameter_name:
                    break
            else:
                assert False

        # Load up *filter* (i.e. *self*):
        filter = self
        filter.parameter = parameter
        filter.reg_ex = None
        filter.select = select
        filter.select_item = None
        filter.use = use
        filter.use_item = None

    # Filter.xml_lines_append():
    def xml_lines_append(self, xml_lines, indent, tracing=""):
        # Verify argument types:
        assert isinstance(xml_lines, list)
        assert isinstance(indent, str)
        assert isinstance(tracing, str)

        # Perform any requested *tracing*:

        # Start appending the `<Filter...>` element to *xml_lines*:
        filter = self
        parameter = filter.parameter
        use = filter.use
        select = filter.select
        parameter_name = parameter.name
        xml_lines.append(f'{indent}<Filter name="{parameter_name}" use="{use}" select="{select}">')
        if tracing:
            print("{0}Name='{1}' Use='{2}' Select='{3}'".
                  format(tracing, parameter.name, filter.use, select))

        # Append any *enumerations*:
        enumerations = parameter.enumerations
        if len(enumerations) >= 1:
            xml_lines.append('{0}  <FilterEnumerations>'.format(indent))
            for enumeration in enumerations:
                enumeration_name = enumeration.name
                match = False
                xml_lines.append(f'{indent}    <FilterEnumeration'
                                 f' name="{enumeration_name}" match="{match}"/>')
            xml_lines.append(f'{indent}  </FilterEnumerations>')

        # Wrap up `<Filter...>` element:
        xml_lines.append(f'{indent}</Filter>')


# Footprint:
class Footprint:
    """ *Footprint*: Represents a PCB footprint. """

    # Footprint.__init__():
    def __init__(self, name, rotation):
        """ *Footprint*: Initialize a new *FootPrint* object.

        The arguments are:
        * *name* (str): The unique footprint name.
        * *rotation* (degrees): The amount to rotate the footprint to match the feeder tape with
          holes on top.
        """

        # Verify argument types:
        assert isinstance(name, str)
        assert isinstance(rotation, float) and 0.0 <= rotation <= 360.0 or rotation is None

        # Stuff values into *footprint* (i.e. *self*):
        footprint = self
        footprint.name = name
        footprint.rotation = rotation


# Inventory:
class Inventory:

    # Inventory.__init__():
    def __init__(self, project_part, amount):
        """ *Inventory*: Initialize *self* to contain *scheamtic_part* and
            *amount*. """

        # Verify argument types:
        assert isinstance(project_part, ProjectPart)
        assert isinstance(amount, int)

        # Load up *self*:
        self.project_part = project_part
        self.amount = amount


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

# Node:
class Node:
    """ Represents a single *Node* suitable for use in a *QTreeView* tree. """

    # Node.__init__():
    def __init__(self, name, parent, tracing=""):
        # Verify argument types:
        assert isinstance(name, str)
        assert isinstance(parent, Node) or parent is None
        assert isinstance(tracing, str)

        # Do some additional checking for *node* (i.e. *self*):
        node = self
        is_collection = isinstance(node, Collection)
        is_collections = isinstance(node, Collections)
        # is_either = is_collections or is_collection
        assert (parent is None) == is_collections, f"Node '{name}' has bad parent"

        # Initilize the super class for *node*:
        super().__init__()

        # Compute *relative_path* using *partent*:
        collection = None if is_collections else (node if is_collection else parent.collection)
        relative_path = ("" if parent is None
                         else os.path.join(parent.relative_path, Encode.to_file_name(name)))

        # Load up *node* (i.e. *self*):
        node = self
        node._children = list()              # List of children *Node*'s
        node.collection = collection         # Parent *Collection* for *node* (if it makes sense)
        node.name = name                     # Human readable name of version of *Node*
        node.parent = parent                 # Parent *Node* (*None* for *Collections*)
        node.relative_path = relative_path   # Relative path from root to *node* name without suffix

        # To construct a path to the file/directory associated with a *node*:
        # 1. Start with either *node.collection.collection_root* or
        #    *node.collection.searches_root*,
        # 2. Append *relative_path*,
        # 3. If appropriate, append `.xml`.

        # Force *node* to be a child of *parent*:
        if parent is not None:
            parent.child_append(node)

    # Node.child():
    def child(self, row):
        # Verify argument types:
        assert isinstance(row, int)

        node = self
        children = node._children
        result = children[row] if 0 <= row < len(children) else None
        return result

    # Node.child_append():
    def child_append(self, child):
        # Verify argument types:
        assert isinstance(child, Node)

        # FIXME: This should just call *child_insert*() with a position of 0!!!

        # Grab *children* from *node* (i.e. *self*):
        node = self
        children = node._children

        # Let *tree_model* (if it exists) know that we are about to insert *node* at the
        # end of *children* (i.e. at the *insert_row_index*):
        tree_model = node.tree_model_get()
        if tree_model is not None:
            model_index = tree_model.createIndex(0, 0, node)
            insert_row_index = len(children)
            tree_model.beginInsertRows(model_index, insert_row_index, insert_row_index)

        # Now tack *child* onto the end of *child* and update *child*'s parent field:
        children.append(child)
        child.parent = node

        # Wrap up *tree_model* row insert (if there is a *tree_model*):
        if tree_model is not None:
            tree_model.endInsertRows()

    # Node.child_count():
    def child_count(self):
        # Return the number of children associated with *node* (i.e. *self*):
        node = self
        count = len(node._children)
        return count

    # Node.child_delete():
    def child_delete(self, position):
        # Verify argument types:
        assert isinstance(position, int)

        # Grab some values out of *node* (i.e. *self*):
        node = self
        children = node._children
        children_size = len(children)

        # Only delete if *position* is valid*:
        deleted = False
        if 0 <= position < children_size:
            # Let *tree_model* know that the delete is about to happend:
            tree_model = node.tree_model_get()
            if tree_model is not None:
                model_index = tree_model.createIndex(0, 0, node)
                tree_model.beginRemoveRows(model_index, position, position)

            # Perform the actual deletion:
            del children[position]
            deleted = True

            # Wrap up the *tree_model* deletion:
            if tree_model is not None:
                tree_model.endRemoveRows()

        # Return whether or not we succussfully *deleted* the child:
        return deleted

    # Node.child_insert():
    def child_insert(self, position, child):
        # Verify argument types:
        assert isinstance(position, int)
        assert isinstance(child, Node)

        # Verify that *position* is valid for inserting into *node* (i.e. *self*):
        node = self
        children = node._children
        children_size = len(children)
        assert 0 <= position <= children_size, f"Bad position={position} size={children_size}"

        # Let *tree_model* (if it exists) know that we are about to insert *node* at the
        # end of *children* (i.e. at *position*):
        tree_model = node.tree_model_get()
        if tree_model is not None:
            model_index = tree_model.createIndex(0, 0, node)
            tree_model.beginInsertRows(model_index, position, position)

        # Now stuff *child* into *children* at *position*:
        children.insert(position, child)
        child.parent = node

        # Wrap up *tree_model* row insert (if there is a *tree_model*):
        if tree_model is not None:
            tree_model.endInsertRows()

        return True

    # Node.child_remove()
    def child_remove(self, child, tracing=""):
        # Verify argument types:
        assert isinstance(child, Node)
        assert isinstance(tracing, str)

        children = node._children
        assert child in children
        index = children.index(child)
        assert index >= 0
        node.child_delete(index)

    # Node.children_get():
    def children_get(self):
        # Return the children of *node* (i.e. *self*):
        node = self
        return node._children

    # Node.clicked():
    def clicked(self, tables_editor, model_index, tracing=""):
        # Verify argument types:
        assert isinstance(tables_editor, TablesEditor)
        assert isinstance(model_index, QModelIndex)
        assert isinstance(tracing, str)

        # Fail with a more useful error message than "no such method":
        node = self
        assert False, "Node.clicked() needs to be overridden for type ('{0}')".format(type(node))

    # Node.csv_read_and_process():
    def csv_read_and_process(self, csv_directory, bind=False, tracing=""):
        # Verify argument types:
        assert isinstance(csv_directory, str)
        assert False, ("Node sub-class '{0}' does not implement csv_read_and_process".
                       format(type(self)))

    # Node.directory_create():
    def directory_create(self, root_path, tracing=""):
        # Verify argument types:
        assert isinstance(root_path, str)
        assert isinstance(tracing, str)

        node = self
        parent = node.parent
        assert parent is not None
        parent_relative_path = parent.relative_path
        directory_path = os.path.join(root_path, parent_relative_path)
        if not os.path.isdir(directory_path):
            os.makedirs(directory_path)
            if tracing:
                print(f"{tracing}Created directory '{directory_path}'")

    # Node.full_file_name_get():
    def xxx_full_file_name_get(self):
        assert False, "Node.full_file_name_get() needs to be overridden"

    # Node.has_child():
    def has_child(self, sub_node):
        # Verify argument types:
        assert isinstance(sub_node, Node)

        node = self
        found = False
        for child in node._children:
            if sub_node is child:
                found = True
                break
        return found

    # Node.has_children():
    def has_children(self):
        # Return *True* if *node* (i.e. *self*) has one or more children:
        node = self
        children = node._children
        has_children = len(children) > 0
        return has_children

    # Node.name_get():
    def name_get(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Grab *title* from *node* (i.e. *self*):
        node = self
        name = node.name
        return name

    # Node.remove():
    def remove(self, remove_node, tracing=""):
        # Verify argument types:
        assert isinstance(remove_node, Node)
        assert isinstance(tracing, str)

        node = self
        children = node._children
        for child_index, child_node in enumerate(children):
            if child_node is remove_node:
                del children[child_index]
                remove_node.parent = None
                break
        else:
            assert False, ("Node '{0}' not in '{1}' remove failed".
                           format(remove_node.name, node.name))

    # Node.searches_root_get():
    def searches_root_get(self):
        # Ensure that we have a *parent* Node:
        node = self
        parent = node.parent
        assert isinstance(parent, Node)

        # Recursively go up the tree until we get a *searches_root*:
        searches_root = parent.searches_root_get()

        return searches_root

    # Node.sort():
    def sort(self, key_function):
        # Verify argument types:
        assert isinstance(key_function, callable)

        # Sort the *children* of *node* (i.e. *self*) using *key_function*:
        node = self
        children = node._children
        children.sort(key=key_function)

    # Node.tree_model_get():
    def tree_model_get(self):
        # Return *tree_model* (or *None*) for *node* (i.e. *self*):
        node = self
        collection = node.collection
        tree_model = None if collection is None else collection.tree_model
        return tree_model

    # Node.row():
    def row(self):
        # Return the index of *node* (i.e. *self*) from its parent children list:
        node = self
        parent = node.parent
        result = 0 if parent is None else parent._children.index(node)
        return result


# Directory:
class Directory(Node):

    # Directory.__init__():
    def __init__(self, name, parent, tracing=""):
        # Verify argument types:
        assert isinstance(name, str)
        assert isinstance(parent, Node)
        assert isinstance(tracing, str)

        # Perform some additional checking on *parent*:
        assert isinstance(parent, Directory) or isinstance(parent, Collection)

        # Initlialize the *Node* super class for directory (i.e. *self*):
        super().__init__(name, parent)

        directory = self
        relative_path = directory.relative_path
        if tracing:
            print(f"{tracing}relative_path='{relative_path}'")

    # Directory.append():
    def append(self, node):
        assert isinstance(node, Directory) or isinstance(node, Table)
        directory = self
        directory.child_append(node)

    # Directory.can_fetch_more():
    def can_fetch_more(self):
        # The call to *Directiory.partial_load*, pre-loaded all of the sub-directories and
        # tables for *directory* (i.e. *self*).  That means there is nothing more to fetch.
        return False

    # Directory.clicked():
    def clicked(self, tables_editor, model_index, tracing=""):
        # Verify argument types:
        assert isinstance(tables_editor, TablesEditor)
        assert isinstance(model_index, QModelIndex)
        assert isinstance(tracing, str)

        tables_editor.current_search = None

    # Directory.directories_get():
    def directories_get(self):
        directory = self
        directories = [directory]
        for node in directory.children_get():
            directories.extend(node.directories_get())
        return directories

    # Directory.name_get():
    def name_get(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        directory = self
        name = directory.name
        return name

    # Directory.partial_load():
    def partial_load(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Compute the *full_path* for the *collection* sub-*directory*:
        directory = self
        relative_path = directory.relative_path
        collection = directory.collection
        collection_root = collection.collection_root
        full_path = os.path.join(collection_root, relative_path)
        if tracing:
            print(f"{tracing}collection_root='{collection_root}'")
            print(f"{tracing}relative_path='{relative_path}'")
            print(f"{tracing}full_path='{full_path}'")
        assert os.path.isdir(full_path), f"Directory '{full_path}' does not exist.!"

        # Visit all of the files and directories in *directory_path*:
        for index, file_or_directory_name in enumerate(sorted(list(os.listdir(full_path)))):
            if tracing:
                print(f"{tracing}File_Name[{index}]:'{file_or_directory_name}'")

            # Skip over any files/directories that start with '.':
            if not file_or_directory_name.startswith('.'):
                # Recursively do a partial load for *full_path*:
                sub_relative_path = os.path.join(relative_path, file_or_directory_name)
                sub_full_path = os.path.join(full_path, file_or_directory_name)
                if tracing:
                    print(f"{tracing}sub_relative_path='{sub_relative_path}'")
                    print(f"{tracing}sub_full_path='{sub_full_path}'")
                if os.path.isdir(sub_full_path):
                    # *full_path* is a directory:
                    name = Encode.from_file_name(file_or_directory_name)
                    sub_directory = Directory(name, directory)
                    assert directory.has_child(sub_directory)
                    sub_directory.partial_load()
                elif sub_full_path.endswith(".xml"):
                    # Full path is a *Table* `.xml` file:
                    name = Encode.from_file_name(file_or_directory_name[:-4])
                    url = "bogus URL"
                    table = Table(name, directory, url)
                    assert directory.has_child(table)
                    sub_relative_path = os.path.join(relative_path, name)
                    table.partial_load()
                else:
                    assert False, f"'{full_path}' is neither an .xml nor a directory"

        # Wrap up any requested *tracing*:
        if tracing:
            print(f"{tracing}<=Directory.partial_load('{directory.name}')")

    # Directory.tables_append():
    def tables_get(self):
        directory = self
        tables = list()
        for node in directory.children_get():
            tables.extend(node.tables_get())
        return tables

    # Directory.type_letter_get():
    def type_letter_get(self):
        assert not isinstance(self, Collection)
        # print("Directory.type_letter_get():name='{}'".format(self.name))
        return 'D'


# Collection:
class Collection(Node):

    # Collection.__init__():
    @trace(1)
    def __init__(self, name, parent, collection_root, searches_root, tracing=""):
        # Verify argument types:
        assert isinstance(name, str)
        assert isinstance(parent, Collections)
        assert isinstance(collection_root, str)
        assert isinstance(searches_root, str)
        assert isinstance(tracing, str)

        # Intialize the *Node* super class of *collection* (i.e. *self*).
        collection = self
        super().__init__(name, parent)
        if tracing:
            print(f"{tracing}collection.relative_path='{collection.relative_path}'")

        # Do some additional checktin on *collections* (i.e. *parent*):
        collections = parent
        assert isinstance(collections, Collections)
        assert collections.has_child(collection)

        # Stuff some additional values into *collection*:
        collection.collection_root = collection_root
        collection.plugin = None
        collection.searches_root = searches_root
        collection.searches_table = dict()
        collection.tree_model = collections.tree_model

        # Ensure that *type_letter_get()* returns 'C' for Collection:
        assert collection.type_letter_get() == 'C'

    # Collection.actual_parts_lookup():
    @trace(1)
    def actual_parts_lookup(self, choice_part, tracing=""):
        # Verify argument types:
        assert isinstance(choice_part, ChoicePart)
        assert isinstance(tracing, str)

        # Grab some values from *collection* (i.e. *self*) and *choice_part*:
        collection = self
        searches_table = collection.searches_table
        searches_root = collection.searches_root
        search_name = choice_part.name

        # Get some time values:
        stale_time = 2 * 24 * 60 * 60  # 2 days in seconds
        now = time.time()

        # FIXME: This code should be in Search.actual_parts_lookup()!!!

        actual_parts = []
        # Build up *actual_parts* from *collection* (i.e. *self*):
        if search_name in searches_table:
            # We have a *search* that matches *search_name*:
            search = searches_table[search_name]

            # Force *search* to read in all of its information from its associated `.xml` file:
            search.file_load()

            # Grab some values from *search*:
            collection = search.collection
            search_name = search.name
            search_url = search.url
            relative_path = search.relative_path
            if tracing:
                print(f"{tracing}search_name='{search_name}'")
                print(f"{tracing}search_url='{search_url}'")
                print(f"{tracing}relative_path='relative_path'")

            # Compute the *csv_file_name* of where the `.csv` file associated with *search_url*
            # is (or will be) stored:
            csv_file_name = os.path.join(searches_root, relative_path + ".csv")
            if tracing:
                print(f"{tracing}csv_file_name='{csv_file_name}'")

            # Compute *the
            csv_modification_time = (os.path.getmtime(csv_file_name)
                                     if os.path.isfile(csv_file_name)
                                     else 0)
            now = time.time()
            stale_time = 2 * 24 * 60 * 60  # 2 days in seconds
            if csv_modification_time + stale_time < now:
                assert isinstance(collection, Collection)
                collection.csv_fetch(search_url, csv_file_name)

            # Read in the *csv_file_name*:
            assert os.path.isfile(csv_file_name)
            data_rows = []
            column_names = None
            with open(csv_file_name) as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=',', quotechar='"')
                for row_index, row in enumerate(csv_reader):
                    # print(f"[{index}]: {row}")
                    if row_index == 0:
                        column_names = row
                    else:
                        data_rows.append(row)

            # print("column_names=", column_names)
            manufacturer_part_number_index = column_names.index("Manufacturer Part Number")
            assert manufacturer_part_number_index >= 0
            manufacturer_index = column_names.index("Manufacturer")
            assert manufacturer_index >= 0
            duplicate_removal_table = dict()
            for index, data_row in enumerate(data_rows):
                manufacturer = data_row[manufacturer_index]
                manufacturer_part_number = data_row[manufacturer_part_number_index]
                pair = (manufacturer, manufacturer_part_number)
                duplicate_removal_table[pair] = pair
                # print(f"Row[{index}]: '{manufacturer} : '{manufacturer_part_number}'")
            pairs = list(duplicate_removal_table.keys())

            for index, pair in enumerate(pairs):
                manufacturer, part_number = pair
                if tracing:
                    print(f"{tracing}Actual_Part[{index}]: '{manufacturer}' : '{part_number}'")
                actual_part = ActualPart(manufacturer, part_number)
                actual_parts.append(actual_part)

        return actual_parts

    # Collection.can_fetch_more():
    def can_fetch_more(self):
        # All of the directores for *collection* (i.e. *self*) have be previously found
        # using using *Collection.partial_load*().  So, there are no more *Directory*'s
        # to be loaded.
        return False

    # Collection.directories_get():
    def directories_get(self):
        collection = self
        directories = list()
        for node in collection.children_get():
            directories.extend(node.directories_get())
        return directories

    # Collection.partial_load():
    def partial_load(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Visit all of the directories and files in *collection_root*:
        collection = self
        collection_root = collection.collection_root
        relative_path = collection.relative_path
        directory_path = os.path.join(collection_root, relative_path)
        if tracing:
            print(f"{tracing}collection_root='{collection_root}'")
            print(f"{tracing}relative_path='{relative_path}'")
            print(f"{tracing}directory_path='{directory_path}'")
        assert os.path.isdir(directory_path)

        for index, base_name in enumerate(list(sorted(os.listdir(directory_path)))):
            if tracing:
                print(f"{tracing}File_Name[{index}]:'{base_name}'")

            # Compute a *full_path* from *collection_root* and *base_name*:
            full_path = os.path.join(directory_path, base_name)
            if tracing:
                print(f"{tracing}full_path='{full_path}'")
            if not base_name.startswith('.'):
                if base_name.endswith(".xml"):
                    assert False, "Top level tables not implemented yet"
                elif os.path.isdir(full_path):
                    name = Encode.from_file_name(base_name)
                    directory = Directory(name, collection)
                    assert collection.has_child(directory)
                    directory.partial_load()
                else:
                    assert False, f"'{base_name}' is neither an .xml file nor a directory"

    # Collection.search_find():
    def search_find(self, search_name):
        # Verify argument types:
        assert isinstance(search_name, str)

        # Grab some values from *collection* (i.e. *self*):
        collection = self
        searches_table = collection.searches_table

        # Find a *search* that matches *search_name*:
        search = None
        if search_name in searches_table:
            search = searches_table[search_name]
        return search

    # Collection.tables_get():
    def tables_get(self):
        collection = self
        tables = list()
        for node in collection.children_get():
            tables.extend(node.tables_get())
        return tables

    # Collection.type_leter_get()
    def type_letter_get(self):
        # print("Collection.type_letter_get(): name='{0}'".format(self.name))
        return 'C'

    # Collection.url_load():
    def url_load(self, url, output_file_name, tracing=""):
        # Verify argument types:
        assert isinstance(url, str)
        assert isinstance(output_file_name, str)

        assert False, "Old plugin code"
        collection = self
        plugin = collection.plugin
        if plugin is None:
            collection_root = collection.collection_root
            if tracing:
                print(f"{tracing}collection_root='{collection_root}'")
            assert collection_root.endswith("ROOT")
            package_directory = os.path.split(collection_root)[0]
            if tracing:
                print(f"{tracing}package_directory='{package_directory}'")
            package_name = os.path.split(package_directory)[1]
            if tracing:
                print(f"{tracing}package_name='{package_name}'")
            plugin_name = f"{package_name}.plugin"
            if tracing:
                print(f"{tracing}plug_name='{plugin_name}'")
            # plugin_module = importlib.import_module(plugin_name)
            # url_load = getattr(plugin_module, "url_load")
            # assert callable(url_load)
            # url_load(url, output_file_name)
            # assert False


# Collections:
class Collections(Node):

    # Collections.__init__():
    def __init__(self, name, collection_directories, searches_root, tree_model, tracing=""):
        # Verify argument types:
        assert isinstance(name, str)
        assert isinstance(collection_directories, list)
        assert isinstance(searches_root, str)
        assert isinstance(tree_model, TreeModel) or tree_model is None
        assert isinstance(tracing, str)


        # Intialize the *Node* super class of *collections* (i.e. *self*):
        collections = self
        super().__init__(name, None)

        # Stuff some values into *collections*:
        collections.collection_directories = collection_directories
        collections.searches_root = searches_root
        collections.tree_model = tree_model

        # Do some *tracing*:
        if tracing:
            relative_path = collections.relative_path
            print(f"{tracing}collection_directories={collection_directories}")
            print(f"{tracing}searchs_root='{searches_root}'")
            print(f"{tracing}relative_path='{relative_path}'")

        # Ensure that *type_letter_get()* returns 'R' is for collections Root:
        assert collections.type_letter_get() == 'R'

    # Collections.__str__():
    def __str__(self):
        collections = self
        return f"Collections('{collections.name}')"

    # Collections.actual_parts_lookup():
    @trace(1)
    def actual_parts_lookup(self, choice_part, tracing=""):
        # Verify argument types:
        assert isinstance(choice_part, ChoicePart)
        assert isinstance(tracing, str)

        # Visit each *collection* in *collections* (i.e. *self*) and find any
        # *ActualPart*'s that match *search_name*:
        collections = self
        actual_parts = []
        for index, collection in enumerate(collections.children_get()):
            if tracing:
                print(f"{tracing}Collection[{index}]:{collection.name}")
            actual_parts += collection.actual_parts_lookup(choice_part)

        # FIXME: Cull out duplicate acutal parts (i.e. for the same manufacturer.):
        pass

        return actual_parts

    # Collections.can_fetch_more():
    def can_fetch_more(self):
        # The children of *collections* (i.e. self*) have already be preloade by
        # *Collections.partial_load*().  There is nothing more to fetch:
        return False

    # Collections.check():
    def check(self, search_name, project_name, reference, tracing=""):
        # Verify argument types:
        assert isinstance(search_name, str)
        assert isinstance(project_name, str)
        assert isinstance(reference, str)
        assert isinstance(tracing, str)

        # Find all *matching_searches* that matach *search_name* from *collections* (i.e. *self*):
        collections = self
        matching_searches = list()
        for collection in collections.children_get():
            searches_table = collection.searches_table
            if search_name in searches_table:
                matching_search = searches_table[search_name]
                matching_searches.append(matching_search)

        # Output error if nothing is found:
        if not matching_searches:
            print(f"{project_name}: {reference} '{search_name}' not found")

    # Collections.partial_load():
    def partial_load(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Extract some values from *collections*:
        collections = self
        collection_directories = collections.collection_directories
        searches_root = collections.searches_root
        # tree_model = collections.tree_model
        if tracing:
            print(f"{tracing}collection_directories='{collection_directories}'")
            print(f"{tracing}searches_root='{searches_root}'")

        # Find all of the the *collections* by searching through install Python packages
        # for matching plugins:
        entry_point_key = "bom_manager_collection_get"
        for index, entry_point in enumerate(pkg_resources.iter_entry_points(entry_point_key)):
            entry_point_name = entry_point.name
            if tracing:
                print(f"{tracing}Entry_Point[{index}]:'{entry_point_name}'")
            assert entry_point_name == "collection_get", (f"'{entry_point_name}' is "
                                                          "not 'collection_get''")
            collection_get = entry_point.load()

            # Create *collection*:
            name = "Digi-Key"
            collection = collection_get(collections, searches_root)
            # collection = Collection(name, collections, collection_root, searches_root, url_load,
            #                         )
            assert isinstance(collection, Collection)
            assert collections.has_child(collection)

            # Recursively perfrom *partial_load*'s down from *collection*:
            collection.partial_load()

        # Sweep through *path* finding directories (technically symbolic links):
        for index, collection_directory in enumerate(sorted(collection_directories)):
            # Perform requested *tracing*:
            if tracing:
                print(f"{tracing}Collection[{index}]:'{collection_directory}'")

            # Skip over Unix/Linux *collection_directory*'s that start with a '.':
            if not collection_directory.startswith('.'):
                # Create *collection_root_path* and *searches_root*:
                collection_directory_root = os.path.join(collection_directory, "ROOT")
                collection_directory_root = os.path.abspath(collection_directory_root)
                if tracing:
                    print(f"{tracing}collection_directory_root='{collection_directory_root}'")

                # Now find the directory under `ROOT`:
                sub_directories = list(glob.glob(os.path.join(collection_directory_root, "*")))
                assert len(sub_directories) == 1, f"sub_directories={sub_directories}"
                base_name = os.path.basename(sub_directories[0])
                name = Encode.from_file_name(base_name)
                # collection_root = os.path.join(collection_directory_root, base_name)
                if tracing:
                    print(f"{tracing}base_name='{base_name}'")
                    print(f"{tracing}name='{name}'")
                    # print(f"{tracing}collection_root='{collection_root}'")
                    print(f"{tracing}searches_root='{searches_root}'")

                # Create *collection*:
                # collection = Collection(name, collections, collection_directory_root,
                #                        searches_root, url_load)
                # assert collections.has_child(collection)

                # Recursively perfrom *partial_load*'s down from *collection*:
                collection.partial_load()

    # Collections.searches_root_get():
    def searches_root_get(self):
        collections = self
        searches_root = collections.searches_root
        return searches_root

    # Collections.searches_find():
    @trace(1)
    def searches_find(self, search_name, tracing=""):
        # Verify argument types:
        assert isinstance(search_name, str)

        # Visit each *collection in *collections* (i.e. *self*) to see if it has *search_name*:
        collections = self
        searches = []
        for collection in collections.children_get():
            search = collection.search_find(search_name)
            if search is not None:
                # We have a matching *search*:
                assert search_name == search.name, f"'{search_name}'!='{search.name}'"
                searches.append(search)
        return searches

    # Collections.type_leter_get():
    def type_letter_get(self):
        # print("Collections.type_letter_get(): name='{0}'".format(self.name))
        return 'R'


# Search:
class Search(Node):

    # FIXME: This tale belongs in *Units*:
    ISO_MULTIPLIER_TABLE = {
      "M": 1.0e6,
      "K": 1.0e3,
      "m": 1.0e-3,
      "u": 1.0e-6,
      "n": 1.0e-9,
      "p": 1.0e-12,
    }

    # Search.__init__():
    def __init__(self, name, parent, search_parent, url, tracing=""):
        # Verify argument types:
        assert isinstance(name, str)
        assert isinstance(parent, Table)
        assert isinstance(search_parent, Search) or search_parent is None
        assert isinstance(url, str)
        assert isinstance(tracing, str)

        # Grab some values from *search* (i.e. *self*):
        search = self

        assert name.find("%3b") < 0

        # Ensure sure that non-template *name is not already in *searches_table*:
        is_template = name.startswith('@')
        collection = parent.collection
        searches_table = collection.searches_table
        # assert (search_parent is None) == (name == "@ALL"), "Search parent problem"
        if not is_template:
            assert name not in searches_table, f"Attempt to duplicate search '{name}'"

        # Initialize the super class for *search* (i.e. *self*):
        search = self
        super().__init__(name, parent)

        # The *parent* is known to be a *table* and must contain *search*:
        table = parent
        assert table.has_child(search)

        # Mark that the *table* is no longer sorted, since the *Node.__init__()* just
        # appended *search* to its *children* list:
        table.is_sorted = False

        # Stuff values into *search*:
        search.comments = list()
        search.loaded = False
        search._relative_path = None
        search.search_parent = search_parent
        search.search_parent_name = None  # Used by *Search.tree_load*()
        search.url = url

        # Stuff *search* into *searches_table* if is not *is_template*:
        if not is_template:
            searches_table[name] = search

    # Search.can_fetch_more():
    def can_fetch_more(self):
        # Currently, all *Search* objects never have any childre.  Hence, there is nothing fetch:
        return False

    # Search.clicked()
    def clicked(self, tables_editor, model_index, tracing=""):
        # Verify argument types:
        assert isinstance(tables_editor, TablesEditor)
        assert isinstance(model_index, QModelIndex)
        assert isinstance(tracing, str)

        # Fetch the *url* from *search*:
        search = self
        table = search.parent
        assert isinstance(table, Table)
        url = search.url
        assert isinstance(url, str)
        if tracing:
            print(f"{tracing}url='{url}' table.name='{table.name}'")

        # Force the *url* to open in the web browser:
        webbrowser.open(url, new=0, autoraise=True)

        # Remember that *search* and *model_index* are current:
        tables_editor.current_search = search
        tables_editor.current_model_index = model_index

        # Get the *selection_model* associated with *collections_tree*:
        main_window = tables_editor.main_window
        collections_tree = main_window.collections_tree
        collections_line = main_window.collections_line
        selection_model = collections_tree.selectionModel()

        # Now tediously force the GUI to high-light *model_index*:
        flags = (QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)
        selection_model.setCurrentIndex(model_index, flags)
        flags = (QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)
        selection_model.setCurrentIndex(model_index, flags)

        # Force *search_title* into the *collections_line* widget:
        search_name = search.name
        collections_line.setText(search_name)

    # Search.comments_append():
    def comments_append(self, comments):
        # Verify argument types:
        assert isinstance(comments, list)
        for comment in comments:
            assert isinstance(comment, SearchComment)

        # Tack *comments* onto the the comments list in *search* (i.e. *self*):
        search = self
        search.comments.extend(comments)

    # Search.file_load():
    def file_load(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Grab some informtation from parent *table* of *search*:
        search = self
        table = search.parent
        assert isinstance(table, Table)
        table_name = table.name
        searches = table.children_get()
        searches_size = len(searches)
        # Only load *search* (i.e. *self*) if it is not already *loaded*:
        loaded = search.loaded
        if tracing:
            print(f"{tracing}loaded={loaded} table='{table_name}' searches_size={searches_size}")
        if not loaded:
            # Grab some values from *search*:
            collection = search.collection
            searches_root = collection.searches_root
            relative_path = search.relative_path
            search_full_file_name = os.path.join(searches_root, relative_path + ".xml")
            if tracing:
                print(f"{tracing}search_full_file_name={search_full_file_name}")
            with open(search_full_file_name, "r") as search_file:
                # Read in *search_xml_text* from *search_file*:
                search_xml_text = search_file.read()

                # Parse the XML in *search_xml_text* into *search_tree*:
                search_tree = etree.fromstring(search_xml_text)

                # Now process the contents of *search_tree* and stuff the result:
                search.tree_load(search_tree)

                # Mark that *table* is no longer sorted since we may updated the
                # *search_parent* and *search_parent_title* fields:
                table = search.parent
                assert isinstance(table, Table)
                table.is_sorted = False

            # Mark *search* as *loaded*:
            search.loaded = True

    # Search.filters_refresh()
    def filters_refresh(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Before we do anything we have to make sure that *search* has an associated *table*.
        # Frankly, it is should be impossible not to have an associated table, but we must
        # be careful:
        search = self
        table = search.table
        assert isinstance(table, Table) or table is None
        if table is not None:
            # Now we have to make sure that there is a *filter* for each *parameter* in
            # *parameters*.  We want to preserve the order of *filters*, so this is pretty
            # tedious:

            # Step 1: Start by deleting any *filter* from *filters* that does not have a
            # matching *parameter* in parameters.  This algorithme is O(n^2), so it could
            # be improved:
            filters = search.filters
            parameters = table.parameters
            new_filters = list()
            for filter in filters:
                for parameter in parameters:
                    if filter.parameter is parameter:
                        new_filters.append(filter)
                        break

            # Carefully replace the entire contents of *filters* with the contents of *new_filters*:
            filters[:] = new_filters[:]

            # Step 2: Sweep through *parameters* and create a new *filter* for each *parameter*
            # that does not already have a matching *filter* in *filters*.  Again, O(n^2):
            for pararmeter_index, parameter in enumerate(parameters):
                for filter in filters:
                    if filter.parameter is parameter:
                        break
                else:
                    filter = Filter(parameter=parameter, table=table, use=False, select="")
                    filters.append(filter)

    # Search.full_file_name_get():
    def xxx_full_file_name_get(self):
        # Grab some values from *search* (i.e. *self*):
        search = self
        collection = search.collection
        name = search.name
        relative_path = search.relative_path

        # Compute *full_file_name*:
        searches_root = collection.searches_root
        xml_name = Encode.to_file_name(name) + ".xml"
        # print(f"searches_root='{searches_root}' "
        #       f"relative_path='{relative_path}; "
        #       f"xml_name='{xml_name}'")
        full_file_name = os.path.join(searches_root, relative_path, xml_name)
        return full_file_name

    # Search.is_deletable():
    def is_deletable(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Grab *search_name* from *search* (i.e. *self*):
        search = self
        search_name = search.name

        # Search through *sibling_searches* of *table* to ensure that *search* is not
        # a parent of any *sibling_search* object:
        table = search.parent
        assert isinstance(table, Table)
        sibling_searches = table.children_get()

        # Make sure that there are now *sibling_search*'s that depend upon *search*:
        deletable = True
        for index, sibling_search in enumerate(sibling_searches):
            if sibling_search.search_parent is search:
                deletable = False
                break
        return deletable

    # Search.key():
    def key(self):
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
        search = self
        table = search.parent
        assert isinstance(table, Table)
        searches_table = table.searches_table
        assert isinstance(searches_table, dict)

        # Figure out template *depth*:
        depth = 0
        nested_search = search
        while nested_search.search_parent is not None:
            depth += 1
            nested_search = nested_search.search_parent

        # Sweep through the *search_name* looking for a number, optionally followed by an
        # ISO unit mulitplier.:
        number_end_index = -1
        search_name = search.name
        for character_index, character in enumerate(search_name):
            if character in ".0123456789":
                # We a *character* that "could" be part of a number:
                number_end_index = character_index + 1
            else:
                break

        # Extract *number* from *search_name* if possible:
        number = 0.0
        if number_end_index >= 0:
            try:
                number = float(search_name[0:number_end_index])
            except ValueError:
                pass

        # Figure out the ISO *multiplier* and adjust *number* appropriately:
        multiplier = 1.0
        if number_end_index >= 0 and number_end_index < len(search_name):

            multiplier_character = search_name[number_end_index]
            iso_multiplier_table = Search.ISO_MULTIPLIER_TABLE
            if character in iso_multiplier_table:
                multiplier = iso_multiplier_table[multiplier_character]
        number *= multiplier

        # Return a tuple used for sorting:
        rest = search_name if number_end_index < 0 else search_name[number_end_index:]
        return (depth, number, rest)

    # Search.file_save():
    def file_save(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Create the *search_xml_text* from *search*:
        search = self
        search_xml_lines = list()
        search.xml_lines_append(search_xml_lines, "")
        search_xml_lines.append("")
        search_xml_text = "\n".join(search_xml_lines)

        # Construct XML *search_file_name*:
        collection = search.collection
        searches_root = collection.searches_root
        relative_path = search.relative_path
        search_file_name = os.path.join(searches_root, relative_path + ".xml")
        if tracing:
            print(f"{tracing}searches_root='{searches_root}'")
            print(f"{tracing}relative_path='{relative_path}'")
            print(f"{tracing}search_file_name='{search_file_name}'")

        # Write *search_xml_text* out to *search_xml_file_name*:
        search.directory_create(searches_root)
        with open(search_file_name, "w") as search_file:
            search_file.write(search_xml_text)

        # Mark *search* as *loaded* since we just wrote out the contents:
        search.loaded = True

    # Search.partial_load():
    # def partial_load(self, tracing=""):
    #     # Verify argument types:
    #     assert isinstance(tracing, str)
    #     assert False

    #     # Perform any requested *tracing*:
    #     if tracing:
    #         print(f"{tracing}=>Searches.populate(*)")

    #     # Compute the *glob_pattern* for searching:
    #     searches = self
    #     path = searches.path
    #     slash = os.sep
    #     if tracing:
    #         print(f"{tracing}glob_pattern='{glob_pattern}'")
    #     #for index, file_name in enumerate(glob.glob(glob_pattern, recursive=True)):
    #     #    print(f"Search[{index}]:'{file_name}'")

    #     # Wrap up any requested *tracing*:
    #     if tracing:
    #         print(f"{tracing}<=Searches.populate(*)")

    # Search.search_parent_set():
    def search_parent_set(self, search_parent):
        # Verify argument types:
        assert isinstance(search_parent, Search) or search_parent is None

        # Stuff *search_parent* into *search* (i.e. *self*):
        search = self
        print("Search.search_parent_set('{0}', {1})".format(search.name,
              "None" if search_parent is None else "'{0}'".format(search_parent.name)))
        search.search_parent = search_parent

    # Search.search_parent_title_set():
    def search_parent_title_set(self, search_parent_title):
        # Verify argument types:
        assert isinstance(search_parent_title, str)

        # Stuff *search_parent_title* into *search* (i.e. *self*):
        search = self
        search.search_parent_title = search_parent_title

    # Search.table_set():
    def table_set(self, new_table, tracing=""):
        # Verify argument types:
        assert isinstance(new_table, Table) or new_table is None

        search = self
        search.table = new_table

    # Search.name_get():
    def name_get(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Grab some values from *search* (i.e. *self*):
        search = self
        search_name = search.name
        table = search.parent

        # Make sure that all *searches* associated with *table* are loaded from their
        # associated `.xml` files:
        table.searches_load()

        # Make sure that *table* is *sort*'ed:
        table = search.parent
        assert isinstance(table, Table)
        table.sort()

        # Construct the *name*:
        search_parent = search.search_parent
        name = search_name if search_parent is None else f"{search_name} ({search_parent.name})"
        return name

    # Search.tree_load():
    def tree_load(self, search_tree, tracing=""):
        # Verify argument types:
        assert isinstance(search_tree, etree._Element)
        assert isinstance(tracing, str)

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

        # Grab some values from *search* (i.e. *self*):
        search = self
        table = search.parent
        assert isinstance(table, Table)
        # table_name = table.name

        # Extract the attributes from *attributes_table* of the `<Search ...>` tag:
        attributes_table = search_tree.attrib
        assert "name" in attributes_table
        name = Encode.from_attribute(attributes_table["name"])
        search_parent_name = (Encode.from_attribute(attributes_table["search_parent"])
                              if "search_parent" in attributes_table else "")
        assert "url" in attributes_table, "attributes_table={0}".format(attributes_table)
        url = attributes_table["url"]

        # Extract the *comments* and *filters* from *search_tree*:
        comments = list()
        # filters = list()
        # sub_trees = list(search_tree)
        # assert len(sub_trees) == 2
        # for sub_tree in sub_trees:
        #     sub_tree_tag = sub_tree.tag
        #     if sub_tree_tag == "SearchComments":
        #         # We have `<SearchComments ...>`:
        #         search_comment_trees = list(sub_tree)
        #         for search_comment_tree in search_comment_trees:
        #             # We should have `<SearchComment ...>... `:
        #             assert search_comment_tree.tag == "SearchComment"
        #             comment = SearchComment(comment_tree=search_comment_tree)
        #             comments.append(comment)
        #     elif sub_tree_tag == "Filters":
        #         # We have `<Filters ...>...`:
        #         filter_trees = list(sub_tree)
        #         for filter_tree in filter_trees:
        #             # We should have `<Filter ...>... `:
        #             assert filter_tree.tag == "Filter"
        #             filter = Filter(tree=filter_tree, table=table)
        #             filters.append(filter)
        #     else:
        #         assert False, f"Unexpected tag <{sub_tree_tag}...> under <Search> tag"

        # Stuff new values into *search* (i.e. *self*):
        search = self
        search.name = name
        search.comments[:] = comments[:]
        # search.filters[:] = filters[:]
        search.search = None
        search.search_parent_name = search_parent_name
        search.url = url

    # Search.type_letter_get():
    def type_letter_get(self):
        return 'S'

    # Search.url_set():
    def url_set(self, url):
        # Verify argument types:
        assert isinstance(url, str)

        # Stuff *url* into *search* (i.e. *self*):
        search = self
        search.url = url

    # Search.xml_lines_append()
    def xml_lines_append(self, xml_lines, indent, tracing=""):
        # Verify argument types:
        assert isinstance(xml_lines, list)
        assert isinstance(indent, str)
        assert isinstance(tracing, str)

        # Grab some values from *search* (i.e. *self*):
        search = self
        table = search.parent
        assert isinstance(table, Table)
        search_parent = search.search_parent
        search_name = search.name

        # Figure out *search_parent_title* which is empty only for the `@ALL` *Search* object:
        search_parent_text = ("" if search_parent is None
                              else f'search_parent="{Encode.to_attribute(search_parent.name)}" ')

        # Start the `<Search...>` element:
        xml_lines.append(f'{indent}<Search '
                         f'name="{Encode.to_attribute(search_name)}" '
                         f'{search_parent_text}'
                         f'table="{Encode.to_attribute(table.name)}" '
                         f'url="{Encode.to_attribute(search.url)}">')

        # Append the `<SearchComments>` element:
        xml_lines.append(f'{indent}  <SearchComments>')
        search_comments = search.comments
        search_comment_indent = indent + "    "
        for search_comment in search_comments:
            search_comment.xml_lines_append(xml_lines, search_comment_indent)
        xml_lines.append(f'{indent}  </SearchComments>')

        # Append the `<Filters>` element:
        # filters = search.filters
        # xml_lines.append(f'{indent}  <Filters>')
        # filter_indent = indent + "    "
        # for filter in filters:
        #     filter.xml_lines_append(xml_lines, filter_indent)
        # xml_lines.append(f'{indent}  </Filters>')

        # Wrap up the `<Search>` element:
        xml_lines.append(f'{indent}</Search>')


# Table:
class Table(Node):

    # Table.__init__():
    def __init__(self, name, parent, url, tracing=""):
        # Verify argument types:
        assert isinstance(name, str)
        assert isinstance(parent, Directory) or isinstance(parent, Collection)
        assert isinstance(url, str)
        assert isinstance(tracing, str)

        # Initialize the *Node* super-class for *table* (i.e. *self*)
        table = self
        super().__init__(name, parent)

        # Load additional values into *table*:
        table.comments = list()
        table.is_sorted = False
        table.loaded = False
        table.parameters = list()
        table._relative_path = None
        table.searches_table = dict()
        table.url = None

    # Table.bind_parameters_from_imports():
    def bind_parameters_from_imports(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Update *current_table* an *parameters* from *tables_editor*:
        table = self
        parameters = table.parameters
        headers = table.import_headers
        column_triples = table.import_column_triples
        for column_index, triples in enumerate(column_triples):
            header = headers[column_index]
            # Replace '&' with '+' so that we don't choke the evenutaly .xml file with
            # an  XML entity (i.e. 'Rock & Roll' = > 'Rock + Roll'.  Entities are always
            # "&name;".
            header = header.replace('&', '+')
            header = header.replace('<', '[')
            header = header.replace('>', ']')

            if len(triples) >= 1:
                # We only care about the first *triple* in *triples*:
                triple = triples[0]
                count, name, value = triple

                # See if an existing *parameter* matches *name* (not likely):
                for parameter_index, parameter in enumerate(parameters):
                    if parameter.csv == name:
                        # This *parameter* already exists, so we done:
                        break
                else:
                    # This is no preexisting *parameter* so we have to create one:

                    # Create *scrunched_name* from *header*:
                    scrunched_characters = list()
                    in_word = False
                    for character in header:
                        if character.isalnum():
                            if not in_word:
                                character = character.upper()
                            scrunched_characters.append(character)
                            in_word = True
                        else:
                            in_word = False
                    scrunched_name = "".join(scrunched_characters)

                    # Create *parameter* and append to *parameters*:
                    comments = [ParameterComment(language="EN",
                                long_heading=scrunched_name, lines=list())]
                    parameter = Parameter(name=scrunched_name, type=name, csv=header,
                                          csv_index=column_index, comments=comments)
                    parameters.append(parameter)

    # Table.can_fetch_more():
    def can_fetch_more(self):
        # Conceptually, every table as a default `@ALL` search.  We return *True* if
        # the `@ALL` search has not actually been created yet for *table* (i.e. *self*):
        table = self
        searches = table.children_get()
        can_fetch_more = (len(searches) == 0)
        return can_fetch_more

    # Table.clicked():
    def clicked(self, tables_editor, model_index, tracing=""):
        # Verify argument types:
        assert isinstance(tables_editor, TablesEditor)
        assert isinstance(model_index, QModelIndex)
        assert isinstance(tracing, str)

        tables_editor.current_search = None

        # Sweep through *tables* to see if *table* (i.e. *self*) is in it:
        tables = tables_editor.tables
        table = self
        for sub_table in tables:
            if table is sub_table:
                # We found a match, so we are done searching:
                break
        else:
            # Nope, *table* is not in *tables*, so let's stuff it in:
            if tracing:
                print("{0}Before len(tables)={1}".format(tracing, len(tables)))
            tables_editor.tables_combo_edit.item_append(table)
            if tracing:
                print("{0}After len(tables)={1}".format(tracing, len(tables)))

        # Force whatever is visible to be updated:
        tables_editor.update(tracing=tracing)

        # Make *table* the current one:
        tables_editor.current_table = table
        tables_editor.current_parameter = None
        tables_editor.current_enumeration = None
        tables_editor.current_comment = None
        tables_editor.current_search = None

    # Table.csv_read_and_process():
    def csv_read_and_process(self, csv_directory, bind=False, tracing=""):
        # Verify argument types:
        assert isinstance(csv_directory, str)
        assert isinstance(tracing, str)

        # Grab *parameters* from *table* (i.e. *self*):
        table = self
        parameters = table.parameters
        assert isinstance(parameters, list)

        # Open *csv_file_name* read in both *rows* and *headers*:
        csv_full_name = table.csv_full_name_get()
        assert isinstance(csv_full_name, str)
        if tracing:
            print(f"{tracing}csv_full_name='{csv_full_name}'")

        rows = None
        headers = None
        if not os.path.isfile(csv_full_name):
            print(f"{tracing}csv_directory='{csv_directory}' csv_full_name='{csv_full_name}'")
        with open(csv_full_name, newline="") as csv_file:
            # Read in *csv_file* using *csv_reader*:
            csv_reader = csv.reader(csv_file, delimiter=',', quotechar='"')
            rows = list()
            for row_index, row in enumerate(csv_reader):
                if row_index == 0:
                    headers = row
                else:
                    rows.append(row)

        # Create *column_tables* which is used to process the following *row*'s:
        column_tables = [dict() for header in headers]
        for row in rows:
            # Build up a count of each of the different data values in for a given column
            # in *column_table*:
            for column_index, value in enumerate(row):
                column_table = column_tables[column_index]
                if value in column_table:
                    # We have seen *value* before, so increment its count:
                    column_table[value] += 1
                else:
                    # This is the first time we seen *value*, so insert it into
                    # *column_table* as the first one:
                    column_table[value] = 1

        # Now *column_tables* has a list of tables (i.e. *dict*'s) where it entry
        # has a count of the number of times that value occured in the column.

        # Now sweep through *column_tables* and build *column_triples*:
        re_table = TablesEditor.re_table_get()
        column_triples = list()
        for column_index, column_table in enumerate(column_tables):
            # FIXME: Does *column_list* really need to be sorted???!!!!
            # Create *column_list* from *column_table* such that the most common value in the
            # columns comes first and the least commone one comes last:
            column_list = sorted(list(column_table.items()),
                                 key=lambda pair: (pair[1], pair[0]), reverse=True)

            # Build up *matches* which is the regular expressions that match best:
            regex_table = dict()
            regex_table["String"] = list()
            total_count = 0
            for value, count in column_list:
                # print("Column[{0}]:'{1}': {2} ".format(column_index, value, count))
                total_count += count
                match_count = 0
                for regex_name, regex in re_table.items():
                    if not regex.match(value) is None:
                        if regex_name in regex_table:
                            regex_table[regex_name].append((value, count))
                        else:
                            regex_table[regex_name] = [(value, count)]

                        match_count += 1
                if match_count == 0:
                    regex_table["String"].append((value, count))
            # assert total_count == len(rows), \
            #  "total_count={0} len_rows={1}".format(total_count, len(rows))

            # if tracing:
            #    print("{0}Column[{1}]: regex_table={2}".
            #      format(tracing, column_index, regex_table))

            # Now construct the *triples* list such containing of tuples that have
            # three values -- *total_count*, *regex_name*, and *value* where,
            # * *total_count*: is the number column values that the regular expression matched,
            # * *regex_name*: is the name of the regular expression, and
            # * *value*: is an example value that matches the regular expression.
            triples = list()
            for regex_name, pair_list in regex_table.items():
                total_count = 0
                value = ""
                for pair in pair_list:
                    value, count = pair
                    total_count += count
                triple = (total_count, regex_name, value)
                triples.append(triple)

            # Sort *triples* such that the regular expression that maches the most entries comes
            # first the least matches are at the end.  Tack *triples* onto *column_triples* list:
            triples.sort(reverse=True)
            column_triples.append(triples)

        # Save some values into *tables_editor* for the update routine:
        table.import_column_triples = column_triples
        table.import_headers = headers
        table.import_rows = rows
        assert isinstance(column_triples, list)
        assert isinstance(headers, list)
        assert isinstance(rows, list)

        if bind:
            table.bind_parameters_from_imports()
        table.file_save()

    # Table.directories_get():
    def directories_get(self):
        return []

    # Table.fetch_more():
    def fetch_more(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Create *all_search* if it does not already exist (i.e. *searches_size* is 0):
        table = self
        name = table.name
        searches = table.children_get()
        searches_size = len(searches)
        if tracing:
            print(f"{tracing}1:searches_size={searches_size}")
        if searches_size == 0:
            # Note that the call to the *Search*() has the side-effect of appending
            # *all_search* to the children of *table*:
            # base_name = Encode.to_file_name(name)
            all_search = Search("@ALL", table, None, table.url)
            assert table.has_child(all_search)
            assert len(searches) == 1
            all_search.file_save()

            # Make sure that *table* is fully loaded so we can grab the *url*:
            table.file_load()
            searches_size = len(searches)
            if tracing:
                print(f"{tracing}2:searches_size={searches_size}")
            assert searches_size == 1
            url = table.url

            # Fill in the rest of *all_search* from *table*:
            comment = SearchComment(language="EN", lines=list())
            all_search.comments.append(comment)
            all_search.url = url

            # Force *all_search* out to the file system:
            all_search.file_save()
            if tracing:
                searches_size = len(searches)
                print(f"{tracing}3:searches_size={searches_size}")

    # Table.file_load():
    def file_load(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Only load *table* (i.e. *self*) if it is not already *loaded*:
        table = self
        loaded = table.loaded
        searches = table.children_get()
        searches_size = len(searches)
        if tracing:
            print(f"{tracing}loaded={loaded} searches_size={searches_size}")
        if not table.loaded:
            # Get *table_file_name* for *table*:
            relative_path = table.relative_path
            collection = table.collection
            collection_root = collection.collection_root
            table_file_name = os.path.join(collection_root, relative_path + ".xml")
            assert os.path.exists(table_file_name), f"'{table_file_name}' does not exist"

            # Read *table_tree* in from *full_file_name*:
            with open(table_file_name) as table_file:
                # Read in *table_xml_text* from *table_file*:
                table_xml_text = table_file.read()

                # Parse the XML in *table_xml_text* into *table_tree*:
                table_tree = etree.fromstring(table_xml_text)
                # FIXME: Catch XML parsing errors here!!!

                # Now process the contents of *table_tree* and stuff the results into *table*:
                table.tree_load(table_tree)

            # Mark *table* as *loaded*:
            table.loaded = True

    # Table.full_file_name_get():
    def xxx_full_file_name_get(self):
        # Grab some values out of *table*:
        table = self
        collection = table.collection
        name = table.name
        relative_path = table.relative_path

        # Compute *file_file_name*:
        collection_root = collection.collection_root
        file_base = Encode.to_file_name(name) + ".xml"
        full_file_name = os.path.join(collection_root, relative_path, file_base)
        return full_file_name

    # Table.has_children():
    def has_children(self):
        # This is a bit obscure.  A *Table* object conceptually always has an "@ALL" search.
        # *True* is returned even if the *table* (i.e. *self*) does not actually have
        # any children.  When *Table.fetch_more*() is called the "@ALL" search will auto-magically
        # be created under the covers.
        return True

    # Table.header_labels_get():
    def header_labels_get(self):
        table = self
        parameters = table.parameters
        parameters_size = len(parameters)
        assert parameters_size >= 1
        header_labels = list()
        for parameter in parameters:
            parameter_comments = parameter.comments
            header_label = "?"
            if len(parameter_comments) >= 1:
                parameter_comment = parameter_comments[0]
                short_heading = parameter_comment.short_heading
                long_heading = parameter_comment.long_heading
                header_label = short_heading if short_heading is not None else long_heading
            header_labels.append(header_label)
        return header_labels

    # Table.name_get():
    def name_get(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Force *table* (i.e. *self*) *load* if it has not already been loaded:
        table = self
        name = table.name
        table.file_load()

        # Augment *name* with the *searches_size*:
        searches = table.children_get()
        searches_size = len(searches)
        if len(searches) >= 2:
            name += f" ({searches_size})"
        return name

    # Table.partial_load():
    def partial_load(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Grab some values from *table* (i.e. *self*):
        table = self
        # name = table.name
        relative_path = table.relative_path
        collection = table.collection

        # Compute *searches_path* which is the directory that contains the *Search* `.xml` files:
        collection_root = collection.collection_root
        searches_root = collection.searches_root
        searches_directory = os.path.join(searches_root, relative_path)
        if tracing:
            print(f"{tracing}collection_root='{collection_root}'")
            print(f"{tracing}searches_root='{searches_root}'")
            print(f"{tracing}relative_path='{relative_path}'")
            print(f"{tracing}searches_directory='{searches_directory}'")

        # Scan through *searches_path* looking for `.xml` files:
        if os.path.isdir(searches_directory):
            # *searches_path* is a directory so we scan it:
            for index, search_file_name in enumerate(sorted(list(os.listdir(searches_directory)))):
                # Preform requested *tracing*:
                if tracing:
                    print(f"{tracing}Search[{index}]:'{search_file_name}'")

                # Skip over any files that do not end with `.xml` suffix:
                if search_file_name.endswith(".xml"):
                    # Extract *name* and *title* from *file_name* (ignoring the `.xml` suffix):
                    file_base = search_file_name[:-4]
                    search_name = Encode.from_file_name(file_base)

                    # Create *search* and then save it out to the file system:
                    search = Search(search_name, table, None, "??")
                    assert table.has_child(search)
                    search.loaded = False

    # Table.sort():
    def sort(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Only sort *table* (i.e. *self*) if it is not *is_sorted*:
        table = self
        name = table.name
        is_sorted = table.is_sorted
        if tracing:
            print(f"{tracing}is_sorted={is_sorted}")
        if not is_sorted:
            # Grab *searches* list from *table* (i.e. *self*):
            searches = table.children_get()
            searches_size = len(searches)
            if tracing:
                print(f"{tracing}searches_size={searches_size}")

            # Create a new *searches_table* that contains every *search* keyed by *search_name*:
            searches_table = dict()
            for index, search in enumerate(searches):
                search_name = search.name
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

    # Table.save():
    def save(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Write out *table* (i.e. *self*) to *file_name*:
        table = self
        output_file_name = table.file_name
        xml_text = table.to_xml_string()
        with open(output_file_name, "w") as output_file:
            output_file.write(xml_text)

    # Table.search_directory_get():
    def search_directory_get(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Compute *search_directory*:
        table = self
        searches_root = table.searches_root_get()
        relative_path = table.relative_path
        table_name = table.name
        table_base_name = Encode.to_file_name(table_name)
        search_directory = os.path.join(searches_root, relative_path, table_base_name)
        if tracing:
            print(f"{tracing}searches_root='{searches_root}'")
            print(f"{tracing}relative_path='{relative_path}'")
            # print(f"{tracing}table__directory='{table_directory}'")
            print(f"{tracing}search_directory='{search_directory}'")

        # Make sure *search_directory* exists:
        if not os.path.isdir(search_directory):
            os.makedirs(search_directory)
            if tracing:
                print(f"{tracing}Created directory '{search_directory}'")

        return search_directory

    # Table.searches_load():
    def searches_load(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Grab some values from *table* (i.e. *self*):
        table = self
        table_searches = dict()
        searches_loaded_count = 0
        searches = table.children_get()
        for search in searches:
            # Make sure *search* is *loaded*.  We test *loaded* up here to prevent
            # a lot of unnecessary calls to *file_load*:
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
                search_parent_name = search.search_parent_name
                if tracing:
                    print(f"Search '{search.name}' parent name is '{search_parent_name}'")
                if search_parent_name != "":
                    assert search_parent_name in table_searches, (f"'{search_parent_name} '"
                                                                  f"not in {table_searches.keys()}")
                    search_parent = table_searches[search_parent_name]
                    search.search_parent = search_parent
                    if tracing:
                        print(f"Setting search '{search.name}' "
                              f"search parent to '{search_parent.name}'")
                else:
                    if tracing:
                        print(f"Search '{search.name}' has no search parent.")

    # Table.searches_table_set():
    def searches_table_set(self, searches_table):
        # Verify argument types:
        assert isinstance(searches_table, dict)

        # Stuff *searches_table* into *table* (i.e. *self*):
        table = self
        table.searches_stable = searches_table

    # Table.tables_get():
    def tables_get(self):
        table = self
        return [table]

    # Table.tree_load():
    def tree_load(self, table_tree, tracing=""):
        # Verify argument types:
        assert isinstance(table_tree, etree._Element)
        assert isinstance(tracing, str)

        # Verify that we have a "<Table ...> ... </Table>" at the top level of *table_tree*:
        assert table_tree.tag == "Table"

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
        attributes_table = table_tree.attrib
        assert "name" in attributes_table
        name = Encode.from_attribute(attributes_table["name"])
        url = Encode.from_attribute(attributes_table["url"])

        # Extract the *comments* from *comments_tree_element*:
        table_tree_elements = list(table_tree)
        comments_tree = table_tree_elements[0]
        assert comments_tree.tag == "TableComments"
        comments = list()
        for comment_tree in comments_tree:
            comment = TableComment(comment_tree=comment_tree)
            comments.append(comment)

        # Extract the *parameters* from *parameters_tree_element*:
        parameters = list()
        parameters_tree = table_tree_elements[1]
        assert parameters_tree.tag == "Parameters"
        for parameter_tree in parameters_tree:
            parameter = Parameter(parameter_tree=parameter_tree)
            parameters.append(parameter)

        # Ensure that there are no extra elements:
        assert len(table_tree_elements) == 2

        # Load the extracted information into *table* (i.e. *self*):
        table = self
        table.comments[:] = comments[:]
        table.name = name
        table.parameters[:] = parameters[:]
        table.url = url

    # Table.to_xml_string():
    def to_xml_string(self):
        table = self
        xml_lines = list()
        xml_lines.append('<?xml version="1.0"?>')
        table.xml_lines_append(xml_lines, "")
        xml_lines.append("")
        text = '\n'.join(xml_lines)
        return text

    # Table.type_letter_get():
    def type_letter_get(self):
        return 'T'

    # Table.xml_lines_append():
    def xml_lines_append(self, xml_lines, indent):
        # Verify argument types:
        assert isinstance(xml_lines, list)
        assert isinstance(indent, str)

        # Start appending the `<Table...>` element:
        table = self
        xml_lines.append(f'{indent}<Table '
                         f'name="{Encode.to_attribute(table.name)}" '
                         f'url="{Encode.to_attribute(table.url)}">')

        # Append the `<TableComments>` element:
        xml_lines.append(f'{indent}  <TableComments>')
        for comment in table.comments:
            comment.xml_lines_append(xml_lines, indent + "    ")
        xml_lines.append(f'{indent}  </TableComments>')

        # Append the `<Parameters>` element:
        xml_lines.append(f'{indent}  <Parameters>')
        for parameter in table.parameters:
            parameter.xml_lines_append(xml_lines, "    ")
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
    def __init__(self, order_root, cads, pandas):
        """ *Order*: Initialize *self* for an order. """
        # Verify argument types:
        assert isinstance(order_root, str)
        assert isinstance(cads, list)
        assert isinstance(pandas, list)
        for cad in cads:
            assert isinstance(cad, Cad)
        for panda in pandas:
            assert isinstance(panda, Panda)

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
        vendor_searches_root = os.path.join(order_root, "vendor_searches")
        if not os.path.isdir(vendor_searches_root):
            os.mkdir(vendor_searches_root)
        assert os.path.isdir(vendor_searches_root)

        # Priorities 0-9 are for vendors with significant minimum
        # order amounts or trans-oceanic shipping costs:
        vendor_priorities = {}
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

        # Stuff values into *order* (i.e. *self*):
        order = self
        order.cads = cads
        order.excluded_vendor_names = {}    # Dict[String, List[str]]: Excluded vendors
        order.final_choice_parts = []
        order.inventories = []              # List[Inventory]: Existing inventoried parts
        order.order_root = order_root
        order.pandas = pandas
        order.projects = []                 # List[Project]
        order.projects_table = {}           # Dict[Net_File_Name, Project]
        order.selected_vendor_names = None
        order.stale = 2 * 7 * 24 * 60 * 60  # 2 weeks
        order.requests = []                 # List[Request]: Additional requested parts
        order.vendor_priorities = vendor_priorities
        order.vendor_priority = 10
        order.vendor_searches_root = vendor_searches_root

    # Order.__str__():
    def __str__(self):
        # Grab some values from *order* (i.e. *self*):
        order = self
        order_root = order.order_root
        vendor_searches_root = order.vendor_searches_root
        
        # Construct the *result* string and return it:
        result = f"Order(order_root='{order_root}', vendor_searches_root='{vendor_searches_root}'))"
        return result

    # Order.project_create():
    def project_create(self, name, revision, net_file_name, count,
                       positions_file_name=None, tracing=""):
        """ *Order*: Create a *Project* containing *name*, *revision*,
            *net_file_name* and *count*. """

        # Verify argument types:
        assert isinstance(name, str)
        assert isinstance(revision, str)
        assert isinstance(net_file_name, str)
        assert isinstance(count, int)
        assert isinstance(positions_file_name, str) or positions_file_name is None
        assert isinstance(tracing, str)

        # Grab some values from *order* (i.e. *self*):
        order = self
        projects = order.projects
        projects_table = order.projects_table

        # Ignore duplicate *net_file_names*:
        if net_file_name in projects_table:
            print(f"Duplicate .net file '{net_file_name}' specified.")
        else:
            # Create the new *project* and stuff into the appropriate data structures:
            project = Project(name, revision, net_file_name, count, order, positions_file_name,
                              )
            projects_table[net_file_name] = project
            projects.append(project)

        return project

    # Order.bom_write():
    @trace(1)
    def bom_write(self, bom_file_name, key_function, tracing=""):
        """ *Order*: Write out the BOM (Bill Of Materials) for the
            *Order* object (i.e. *self*) to *bom_file_name* ("" for stdout)
            using *key_function* to provide the sort key for each
            *ChoicePart*.
        """

        # Verify argument types:
        assert isinstance(bom_file_name, str)
        assert callable(key_function)

        # Grab some values from *order* (i.e. *self*):
        order = self
        excluded_vendor_names = order.excluded_vendor_names
        final_choice_parts = order.final_choice_parts
        if tracing:
            print(f"{tracing}len(final_choice_parts)={len(final_choice_parts)}")

        # Sort *final_choice_parts* using *key_function*.
        final_choice_parts.sort(key=key_function)

        # Open *bom_file*
        with (sys.stdout if bom_file_name == "" else open(bom_file_name, "w")) as bom_file:
            # Now generate a BOM summary:
            total_cost = 0.0
            for choice_part in final_choice_parts:
                # Make sure that nonething nasty got into *final_choice_parts*:
                assert isinstance(choice_part, ChoicePart)

                # Sort the *pose_parts* by *project* followed by reference:
                pose_parts = choice_part.pose_parts
                pose_parts.sort(key=lambda pose_part:
                                (pose_part.project.name, pose_part.reference.upper(),
                                 int(text_filter(pose_part.reference, str.isdigit))))

                # Write the first line out to *bom_file*:
                part_name = choice_part.name
                part_footprint = "FOOTPRINT"  # choice_part.kicad_footprint,
                part_description = "DESCRIPTION"  # choice_part.description
                part_count = choice_part.count_get()
                part_references_text = choice_part.references_text_get()
                bom_file.write(f"  {part_name}:{part_footprint};{part_description}"
                               f" {part_count}:{part_references_text}\n")

                # Select the vendor_part and associated quantity/cost
                choice_part.select(excluded_vendor_names, True)
                # selected_actual_part = choice_part.selected_actual_part
                selected_vendor_part = choice_part.selected_vendor_part
                selected_order_quantity = choice_part.selected_order_quantity
                selected_total_cost = choice_part.selected_total_cost
                selected_price_break_index = choice_part.selected_price_break_index

                # It should be impossible not to have a *VendorPart*:
                if isinstance(selected_vendor_part, VendorPart):
                    # Grab the *vendor_name*:
                    assert isinstance(selected_vendor_part, VendorPart)
                    # vendor_name = selected_vendor_part.vendor_name

                    # Show the *price breaks* on each side of the
                    # *selected_price_breaks_index*:
                    price_breaks = selected_vendor_part.price_breaks
                    # print("len(price_breaks)={0} selected_price_break_index={1}".
                    #  format(len(price_breaks), selected_price_break_index))
                    selected_price_break = price_breaks[selected_price_break_index]
                    minimum_index = max(selected_price_break_index - 1, 0)
                    maximum_index = min(selected_price_break_index + 2, len(price_breaks))
                    price_breaks = price_breaks[minimum_index: maximum_index]

                    # Compute the *price_breaks_text*:
                    price_breaks_text = ""
                    for price_break in price_breaks[minimum_index: maximum_index]:
                        price_breaks_text += "{0}/${1:.3f} ".format(
                          price_break.quantity, price_break.price)

                    # Print out the line:
                    selected_actual_key = selected_vendor_part.actual_part_key
                    selected_manufacturer_name = selected_actual_key[0]
                    selected_manufacturer_part_name = selected_actual_key[1]
                    bom_file.write("    {0}:{1} [{2}: {3}] {4}\n".format(
                                   selected_vendor_part.vendor_name,
                                   selected_vendor_part.vendor_part_name,
                                   selected_manufacturer_name,
                                   selected_manufacturer_part_name,
                                   price_breaks_text))

                    # Print out the result:
                    bom_file.write("        {0}@({1}/${2:.3f})={3:.2f}\n".format(
                      selected_order_quantity,
                      selected_price_break.quantity, selected_price_break.price,
                      selected_total_cost))

                    total_cost += selected_total_cost
                else:
                    # It should be impossible to get here:
                    print(f"type(selected_vendor_part)={type(selected_vendor_part)}")

            # Wrap up the *bom_file*:
            bom_file.write("Total: ${0:.2f}\n".format(total_cost))

    # Order.check():
    @trace(1)
    def check(self, collections, tracing=""):
        # Verify argument types:
        assert isinstance(collections, Collections)

        # Check each of the *projects* in *order* (i.e. *self*):
        order = self
        projects = order.projects
        for project in projects:
            project.check(collections)

    # Order.csvs_write():
    @trace(1)
    def csv_write(self, tracing=""):
        """ *Order*: Write out the *Order* object (i.e. *self) BOM (Bill Of Materials)
            for each vendor as a .csv (Comma Seperated Values).
        """
        # Verify argument types:

        # Grab some values from *order* (i.e. *self*):
        order = self
        excluded_vendor_names = order.excluded_vendor_names
        final_choice_parts = order.final_choice_parts

        # Sort *final_choice_parts*:
        final_choice_parts.sort(key=lambda choice_part:
                                (choice_part.selected_vendor_name,
                                 choice_part.selected_total_cost,
                                 choice_part.name))

        vendor_boms = {}
        for choice_part in final_choice_parts:
            assert isinstance(choice_part, ChoicePart)

            # Sort the *pose_parts* by *project* followed by reference:
            pose_parts = choice_part.pose_parts
            pose_parts.sort(key=lambda pose_part:
                            (pose_part.project.name, pose_part.reference.upper(),
                             int(text_filter(pose_part.reference, str.isdigit))))

            # Select the vendor_part and associated quantity/cost
            choice_part.select(excluded_vendor_names, True)
            selected_actual_part = choice_part.selected_actual_part
            selected_vendor_part = choice_part.selected_vendor_part
            selected_order_quantity = choice_part.selected_order_quantity

            if isinstance(selected_vendor_part, VendorPart):
                # Grab the *vendor_name* and *vendor_part_name*:
                assert isinstance(selected_vendor_part, VendorPart)
                vendor_name = selected_vendor_part.vendor_name
                # vendor_part_name = selected_vendor_part.vendor_name

                # Make sure we have a *vendor_bom* line list:
                if vendor_name not in vendor_boms:
                    vendor_boms[vendor_name] = []
                lines = vendor_boms[vendor_name]

                # Create *line* and append it to *vendor_bom*:
                line = ('"{0}","{1}","{2}","{3}","{4}"'.format(
                        selected_order_quantity,
                        selected_vendor_part.vendor_part_name,
                        selected_actual_part.manufacturer_name,
                        selected_actual_part.manufacturer_part_name,
                        choice_part.name))
                lines.append(line)

        # Wrap up the *bom_file*:
        order_root = order.order_root
        for vendor_name in vendor_boms.keys():
            # Create the *vendor_text*:
            vendor_lines = vendor_boms[vendor_name]
            vendor_text = '\n'.join(vendor_lines) + '\n'

            # Write *vendor_text* out to *vendor_full_file*:
            vendor_base_name = Encode.to_file_name(vendor_name) + ".csv"
            vendor_full_name = os.path.join(order_root, vendor_base_name)
            with open(vendor_full_name, "w") as vendor_file:
                # Write out each line in *lines*:
                print(f"Writing '{vendor_full_name}'")
                vendor_file.write(vendor_text)

    # Order.exclude_vendors_to_reduce_shipping_costs():
    def exclude_vendors_to_reduce_shipping_costs(self, choice_parts, excluded_vendor_names,
                                                 reduced_vendor_messages, tracing=""):
        """ *Order*: Sweep through *choice_parts* and figure out which vendors
            to add to *excluded_vendor_names* to reduce shipping costs.
        """
        # Verify argument types:
        assert isinstance(choice_parts, list)
        assert isinstance(excluded_vendor_names, dict)
        assert isinstance(reduced_vendor_messages, list)
        assert isinstance(tracing, str)

        # First figure out the total *missing_parts*.  We will stop if
        # excluding a vendor increases above the *missing_parts* number:
        quad = self.quad_compute(choice_parts, excluded_vendor_names, "")
        missing_parts = quad[0]

        # Sweep through and figure out what vendors to order from:
        done = False
        while not done:
            # Get the base cost for the current *excluded_vendor_names*:
            base_quad = \
              self.quad_compute(choice_parts, excluded_vendor_names, "")
            # print(">>>>base_quad={0}".format(base_quad))

            # If the *base_missing_parts* increases, we need to stop because
            # excluding additional vendors will cause the order to become
            # incomplete:
            base_missing_parts = base_quad[0]
            assert isinstance(base_missing_parts, int)
            if base_missing_parts > missing_parts:
                break

            # Grab *base_cost*:
            base_cost = base_quad[1]
            assert isinstance(base_cost, float)

            # Figure out what vendors are still available for *choice_parts*:
            base_vendor_names = self.vendor_names_get(choice_parts, excluded_vendor_names)
            assert isinstance(base_vendor_names, tuple)
            # print("base: {0} {1}".format(base_cost, base_vendor_names))

            # For small designs, sometimes the algorithm will attempt to
            # throw everything out.  The test below makes sure we always
            # have one last remaining vendor:
            if len(base_vendor_names) <= 1:
                break

            # Iterate through *vendor_names*, excluding one *vendor_name*
            # at a time:
            trial_quads = []
            for vendor_name in base_vendor_names:
                # Create *trial_excluded_vendor_names* which is a copy
                # of *excluded_vendor_names* plus *vendor_name*:
                trial_excluded_vendor_names = dict(excluded_vendor_names)
                trial_excluded_vendor_names[vendor_name] = None

                # Get the base cost for *trial_excluded_vendor_names*
                # and tack it onto *trial_quads*:
                trial_quad = self.quad_compute(choice_parts, trial_excluded_vendor_names,
                                               vendor_name)
                trial_quads.append(trial_quad)

                # For debugging only:
                # trial_cost = trial_quad[0]
                # trial_vendor_name = trial_quad[1]
                # print("    {0:.2f} with {1} excluded".
                #  format(trial_cost, trial_vendor_name))

            # Sort the *trial_quads* to bring the most interesting one to the
            # front:
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
                message = "Excluding '{0}': only saves {1:.2f}".format(lowest_vendor_name, savings)
                reduced_vendor_messages.append(message + '\n')
                if tracing:
                    print(message)
                excluded_vendor_names[lowest_vendor_name] = None
            else:
                # We are done when *lowest_quad* is worth shipping:
                # print("lowest_cost={0:.2f}".format(lowest_cost))
                done = True

    # Order.exclude_vendors_with_high_minimums():
    def exclude_vendors_with_high_minimums(self, choice_parts, excluded_vendor_names,
                                           reduced_vendor_messages, tracing=""):
        """ *Order*: Sweep through *choice* parts and figure out if the
            vendors with large minimum orders can be dropped:
        """

        # Verify argument types:
        assert isinstance(choice_parts, list)
        assert isinstance(excluded_vendor_names, dict)
        assert isinstance(reduced_vendor_messages, list)

        # Grab the talb eof *vendor_minimums*:
        database = self.database
        vendor_minimums = database.vendor_minimums

        # Now visit each vendor a decide if we should dump them because
        # they cost too much:
        for vendor_name in vendor_minimums.keys():
            # Grab the *vendor_minimum_cost*:
            vendor_minimum_cost = vendor_minimums[vendor_name]

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
                  "Excluding '{0}': needed order {1} < minimum order {2}\n".
                  format(vendor_name, vendor_total_cost, vendor_minimum_cost))

    # Order.final_choice_parts_compute():
    @trace(1)
    def final_choice_parts_compute(self, collections, tracing=""):
        """ *Order*: Return a list of final *ChoicePart* objects to order
            for the the *Order* object (i.e. *self*).  This routine also
            has the side effect of looking up the vendor information for
            each selected *ChoicePart* object.
        """

        # Verify argument types:
        assert isinstance(collections, Collections)
        assert isinstance(tracing, str)

        # Grab the some values from *order* (i.e. *self*):
        order = self
        # pandas = order.pandas
        projects = order.projects
        excluded_vendor_names = order.excluded_vendor_names

        # Construct *project_parts_table* table (Dict[name, List[ProjectPart]]) so that every
        # we have a name to a List[ProjectPart] mapping.
        project_parts_table = {}
        for project_index, project in enumerate(projects):
            if tracing:
                print(f"{tracing}Project[{project_index}]:'{project.name}'")

            # Make sure that each *project_part* in *project* is on a list somewhere
            # in the *project_parts_table*:
            project_parts = project.project_parts
            for project_part_index, project_part in enumerate(project_parts):
                assert isinstance(project_part, ProjectPart), (f"type(project_part)="
                                                               f"{type(project_part)}")
                if tracing:
                    print(f"{tracing}ProjectPart[{project_part_index}]:'{project_part.name}'")
                project_part_name = project_part.name
                if project_part_name not in project_parts_table:
                    project_parts_table[project_part_name] = [project_part]
                else:
                    project_parts_table[project_part_name].append(project_part)

        # Now construct the *final_choice_parts* list, where each *choice_part* on
        # the list consisists of a list of *project_parts* and *searches* where
        # all their names match *search_name*:
        final_choice_parts = []
        pairs = list(project_parts_table.items())
        pairs.sort(key=lambda pair: pair[0])
        for search_name, project_parts in pairs:
            if tracing:
                print(f"{tracing}search_name='{search_name}'")
            assert len(project_parts) >= 1
            searches = collections.searches_find(search_name)
            if searches:
                assert len(project_parts) >= 1, "Empty project_parts?"
                for search in searches:
                    assert search.name == search_name
                for project_part in project_parts:
                    assert project_part.name == search_name, (f"'{search_name}'!="
                                                              f"'{project_part.name}'")
                choice_part = ChoicePart(search_name, project_parts, searches)
                final_choice_parts.append(choice_part)
            else:
                print(f"Could not find a search that matches part '{search_name}'")

        # Now load the associated *actual_parts* into each *choice_part* from *final_choice_parts*:
        for choice_part in final_choice_parts:
            # Refresh the vendor part cache for each *actual_part*:
            new_actual_parts = collections.actual_parts_lookup(choice_part)

            # Get reasonably up-to-date pricing and availability information about
            # each *ActualPart* in actual_parts.  *order* is needed to loccate where
            # the cached information is:
            choice_part_name = choice_part.name
            choice_part.vendor_parts_refresh(new_actual_parts, order, choice_part_name,
                                             )

        # Stuff *final_choice_parts* back into *order*:
        final_choice_parts.sort(key=lambda final_choice_part: final_choice_part.name)
        order.final_choice_part = final_choice_parts

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
    def footprints_check(self, final_choice_parts):
        """ *Order*: Verify that footprints exist. """

        # Verify argument types:
        assert isinstance(final_choice_parts, list)

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
    def positions_process(self):
        """ *Order*: Process any Pick and Place `.csv` or `.pos` file.
        """

        order = self
        database = order.database
        projects = order.projects
        for project in projects:
            project.positions_process(database)

    # Order.process():
    @trace(1)
    def process(self, collections, tracing=""):
        """ *Order*: Process the *Order* object (i.e. *self*.) """
        # Verify argument types:
        assert isinstance(collections, Collections)
        assert isinstance(tracing, str)

        # Grab some values from *order* (i.e. *self*):
        order = self
        excluded_vendor_names = order.excluded_vendor_names

        # print("=>Order.process()")

        # Collect the messages from each vendor reduction operation into *reduced_vendor_messages*:
        reduced_vendor_messages = []

        # We need to contruct a list of *ChoicePart* objects.  This
        # will land in *final_choice_parts* below.   Only *ChoicePart*
        # objects can actually be ordered because they list one or
        # more *ActualPart* objects to choose from.  Both *AliasPart*
        # objects and *FractionalPart* objects eventually get
        # converted to *ChoicePart* objects.  Once we have
        # *final_choice_parts* it can be sorted various different ways
        # (by vendor, by cost, by part_name, etc.)
        final_choice_parts = order.final_choice_parts_compute(collections)
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
                                                       reduced_vendor_messages,
                                                       )

        if tracing:
            print(f"{tracing}C:len(final_choice_parts)={len(final_choice_parts)}")

        # Write out *reduced_vendor_messages* to a report file:
        order_root = order.order_root
        reduced_vendor_messages_file_name = os.path.join(order_root, "vendor_reduction_report.txt")
        with open(reduced_vendor_messages_file_name, "w") as reduced_vendor_messages_file:
            for reduced_vendor_message in reduced_vendor_messages:
                reduced_vendor_messages_file.write(reduced_vendor_message)
            reduced_vendor_messages_file.close()

        if tracing:
            print(f"{tracing}D:len(final_choice_parts)={len(final_choice_parts)}")

        # Let the user know how many vendors were eliminated:
        reduced_vendor_messages_size = len(reduced_vendor_messages)
        if reduced_vendor_messages_size >= 1:
            print(f"{reduced_vendor_messages_size} vendors eliminated.  "
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
        order_root = order.order_root
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
    def quad_compute(self, choice_parts, excluded_vendor_names,
                     excluded_vendor_name, trace=False):
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

        # Verify argument types:
        assert isinstance(choice_parts, list)
        assert isinstance(excluded_vendor_names, dict)
        assert isinstance(excluded_vendor_name, str)
        assert isinstance(trace, bool)

        # *trace* is set to *True* to debug stuff:
        if trace:
            print("=>quad_compute({0}, {1}, '{2}')".format(
              [choice_part.name for choice_part in choice_parts],
              excluded_vendor_names.keys(), excluded_vendor_name))

        order = self
        missing_parts = 0
        total_cost = 0.0
        for choice_part in choice_parts:
            # Make sure *choice_part* is actually a *ChoicePart*:
            assert isinstance(choice_part, ChoicePart)

            # Perform the vendor selection excluding all vendors in
            # *excluded_vendor_names*:
            missing_parts += choice_part.select(excluded_vendor_names, False)

            # Grab some values out of *choice_part*:
            # selected_vendor_name = choice_part.selected_vendor_name
            selected_total_cost = choice_part.selected_total_cost

            # Keep a running total of everything:
            total_cost += selected_total_cost

        # Figure out *vendor_priority* for *excluded_vendor_name*:
        vendor_priorities = order.vendor_priorities
        if excluded_vendor_name in vendor_priorities:
            # Priority already assigned to *excluded_vendor_name*:
            vendor_priority = vendor_priorities[excluded_vendor_name]
        else:
            # Assigned a new priority for *excluded_vendor_name*:
            vendor_priority = order.vendor_priority
            vendor_priorities[excluded_vendor_name] = vendor_priority
            order.vendor_priority += 1

        # Return the final *quad*:
        quad = (missing_parts, total_cost, vendor_priority, excluded_vendor_name)

        # *trace* for debugging:
        if trace:
            print("<=quad_compute({0}, {1}, '{2}')=>{3}".format(
              [choice_part.name for choice_part in choice_parts],
              excluded_vendor_names.keys(), excluded_vendor_name, quad))

        return quad

    # Order.xxxrequest():
    def xxxrequest(self, name, amount):
        """ *Order*: Request *amount* parts named *name*. """

        assert isinstance(name, str)
        assert isinstance(amount, int)
        # inventory = Inventory(name, str)

        assert False
        final_vendor_names = None
        # final_vendor_names = \
        #  self.vendor_names_get(final_choice_parts, excluded_vendor_names)
        print("Final selected vendors:")
        for vendor_name in final_vendor_names:
            print("    {0}".format(vendor_name))

        # Print the fianl *total_cost*:
        total_cost = 0.0
        final_choice_parts = None
        excluded_vendor_names = None
        for choice_part in final_choice_parts:
            choice_part.select(excluded_vendor_names, False)
            total_cost += choice_part.selected_total_cost
        print("Total Cost: {0}".format(total_cost))

    # Order.summary_print():
    @trace(1)
    def summary_print(self, choice_parts, excluded_vendor_names, tracing=""):
        """ *Order*: Print a summary of the selected vendors.
        """

        # Verify argument types:
        assert isinstance(choice_parts, list)
        assert isinstance(excluded_vendor_names, dict)
        assert isinstance(tracing, str)

        # Let the user know what we winnowed the vendor list down to:
        final_vendor_names = self.vendor_names_get(choice_parts, excluded_vendor_names)

        # Print the final *total_cost*:
        total_cost = 0.0
        for choice_part in choice_parts:
            choice_part.select(excluded_vendor_names, False)
            total_cost += choice_part.selected_total_cost
        print("Total Cost: ${0:.2f}".format(total_cost))

        # Print out the sub-totals for each vendor:
        print("Final selected vendors:")
        for vendor_name in final_vendor_names:
            vendor_cost = 0.0
            for choice_part in choice_parts:
                if choice_part.selected_vendor_name == vendor_name:
                    vendor_cost += choice_part.selected_total_cost
            print("    {0}: ${1:.2f}".format(vendor_name, vendor_cost))

    # Order.vendor_exclude():
    def vendor_exclude(self, vendor_name):
        """ *Order*: Exclude *vendor_name* from the *Order* object (i.e. *self*)
        """

        # Verify argument typees:
        assert isinstance(vendor_name, str)

        # Mark *vendor_name* from being selectable:
        self.excluded_vendor_names[vendor_name] = None

    # Order.vendor_names_get():
    def vendor_names_get(self, choice_parts, excluded_vendor_names):
        """ *Order*: Return all possible vendor names for *choice_parts*:
        """

        # Verify argument types:
        assert isinstance(choice_parts, list)
        assert isinstance(excluded_vendor_names, dict)

        # Load up *vendor_names_table*:
        vendor_names_table = {}
        for choice_part in choice_parts:
            choice_part.vendor_names_load(
              vendor_names_table, excluded_vendor_names)

        # Return the sorted list of vendor names:
        return tuple(sorted(vendor_names_table.keys()))

    # Order.vendors_select():
    def vendors_select(self, selected_vendor_names):
        """ *Order*: Force the selected vendors for the *order* object (i.e. *self*)
            to *selected_vendors.
        """

        # Use *order* instead of *self*:
        order = self

        # Verify argument types:
        assert isinstance(selected_vendor_names, list) or isinstance(selected_vendor_names, tuple)

        # Stuff *selected_vendors* into *order*:
        order.selected_vendor_names = selected_vendor_names


# Parameter():
class Parameter:

    # Parameter.__init__():
    def __init__(self, **arguments_table):
        is_parameter_tree = "parameter_tree" in arguments_table
        if is_parameter_tree:
            assert len(arguments_table) == 1
            assert isinstance(arguments_table["parameter_tree"], etree._Element)
        else:
            assert "name" in arguments_table
            assert "type" in arguments_table
            assert "csv" in arguments_table
            assert "csv_index" in arguments_table
            assert "comments" in arguments_table
            arguments_count = 5
            if "default" in arguments_table:
                arguments_count += 1
                assert isinstance(arguments_table["default"], str)
            if "optional" in arguments_table:
                assert isinstance(arguments_table["optional"], bool)
                arguments_count += 1
            if "enumerations" in arguments_table:
                arguments_count += 1
                enumerations = arguments_table["enumerations"]
                for enumeration in enumerations:
                    assert isinstance(enumeration, Enumeration)
            assert len(arguments_table) == arguments_count, arguments_table

        if is_parameter_tree:
            parameter_tree = arguments_table["parameter_tree"]
            assert parameter_tree.tag == "Parameter"
            attributes_table = parameter_tree.attrib
            assert "name" in attributes_table
            name = attributes_table["name"]
            assert "type" in attributes_table
            type = attributes_table["type"].lower()
            if "optional" in attributes_table:
                optional_text = attributes_table["optional"].lower()
                assert optional_text in ("true", "false")
                optional = (optional_text == "true")
            else:
                optional = False
            csv = attributes_table["csv"] if "csv" in attributes_table else ""
            csv_index = (
              int(attributes_table["csv_index"]) if "csv_index" in attributes_table else -1)
            default = attributes_table["default"] if "default" in attributes_table else None
            parameter_tree_elements = list(parameter_tree)
            assert len(parameter_tree_elements) >= 1
            comments_tree = parameter_tree_elements[0]
            assert comments_tree.tag == "ParameterComments"
            assert len(comments_tree.attrib) == 0
            comments = list()
            for comment_tree in comments_tree:
                comment = ParameterComment(comment_tree=comment_tree)
                comments.append(comment)

            enumerations = list()
            if type == "enumeration":
                assert len(parameter_tree_elements) == 2
                enumerations_tree = parameter_tree_elements[1]
                assert len(enumerations_tree.attrib) == 0
                assert enumerations_tree.tag == "Enumerations"
                assert len(enumerations_tree) >= 1
                for enumeration_tree in enumerations_tree:
                    enumeration = Enumeration(enumeration_tree=enumeration_tree)
                    enumerations.append(enumeration)
            else:
                assert len(parameter_tree_elements) == 1
        else:
            name = arguments_table["name"]
            type = arguments_table["type"]
            csv = arguments_table["csv"]
            csv_index = arguments_table["csv_index"]
            default = arguments_table["defualt"] if "default" in arguments_table else None
            optional = arguments_table["optional"] if "optional" in arguments_table else False
            comments = arguments_table["comments"] if "comments" in arguments_table else list()
            enumerations = (
              arguments_table["enumerations"] if "enumerations" in arguments_table else list())

        # Load values into *parameter* (i.e. *self*):
        super().__init__()
        parameter = self
        parameter.comments = comments
        parameter.csv = csv
        parameter.csv_index = csv_index
        parameter.default = default
        parameter.enumerations = enumerations
        parameter.name = name
        parameter.optional = optional
        parameter.type = type
        parameter.use = False
        # print("Parameter('{0}'): optional={1}".format(name, optional))
        # print("Parameter(name='{0}', type='{1}', csv='{1}')".format(name, type, parameter.csv))

    # Parameter.__equ__():
    def __eq__(self, parameter2):
        # print("=>Parameter.__eq__()")

        # Verify argument types:
        assert isinstance(parameter2, Parameter)

        # Compare each field of *parameter1* (i.e. *self*) with the corresponding field
        # of *parameter2*:
        parameter1 = self
        name_equal = (parameter1.name == parameter2.name)
        default_equal = (parameter1.default == parameter2.default)
        type_equal = (parameter1.type == parameter2.type)
        optional_equal = (parameter1.optional == parameter2.optional)
        comments_equal = (parameter1.comments == parameter2.comments)
        enumerations_equal = (parameter1.enumerations == parameter2.enumerations)
        all_equal = (
          name_equal and default_equal and type_equal and
          optional_equal and comments_equal and enumerations_equal)

        # Debugging code:
        # print("name_equal={0}".format(name_equal))
        # print("default_equal={0}".format(default_equal))
        # print("type_equal={0}".format(type_equal))
        # print("optional_equal={0}".format(optional_equal))
        # print("comments_equal={0}".format(comments_equal))
        # print("enumerations_equal={0}".format(enumerations_equal))
        # print("<=Parameter.__eq__()=>{0}".format(all_equal))

        return all_equal

    # Parameter.xml_lines_append():
    def xml_lines_append(self, xml_lines, indent):
        assert isinstance(xml_lines, list)
        assert isinstance(indent, str)

        # Grab some values from *parameter* (i.e. *self*):
        parameter = self
        default = parameter.default
        optional = parameter.optional

        # Start the *parameter* XML add in *optional* and *default* if needed:
        xml_line = '{0}<Parameter name="{1}" type="{2}" csv="{3}" csv_index="{4}"'.format(
          indent, parameter.name, parameter.type, parameter.csv, parameter.csv_index)
        if optional:
            xml_line += ' optional="true"'
        if default is not None:
            xml_line += ' default="{0}"'.format(default)
        xml_line += '>'
        xml_lines.append(xml_line)

        # Append all of the comments*:
        comments = parameter.comments
        for comment in comments:
            xml_lines.append('{0}  <ParameterComments>'.format(indent))
            comment.xml_lines_append(xml_lines)
            xml_lines.append('{0}  </ParameterComments>'.format(indent))

        # Append all of the *enumerations*:
        enumerations = parameter.enumerations
        if len(enumerations) >= 1:
            xml_lines.append('{0}  <Enumerations>'.format(indent))
            for enumeration in enumerations:
                enumeration.xml_lines_append(xml_lines, indent + "    ")
            xml_lines.append('{0}  </Enumerations>'.format(indent))

        # Close out the *parameter*:
        xml_lines.append('{0}</Parameter>'.format(indent))


# PosePart:
class PosePart:
    # A PosePart basically specifies the binding of a ProjectPart
    # and its associated schemtatic reference.  Reference strings must
    # be unique for a given project.

    # PosePart.__init__():
    def __init__(self, project, project_part, reference, comment):
        """ Initialize *PosePart* object (i.e. *self*) to contain *project*,
            *project_part*, *reference*, and *comment*.
        """

        # Verify argument types:
        assert isinstance(project, Project)
        assert isinstance(project_part, ProjectPart)
        assert isinstance(reference, str)
        assert isinstance(comment, str)

        # Load up *pose_part* (i.e. *self*):
        pose_part = self
        pose_part.project = project
        pose_part.project_part = project_part
        pose_part.reference = reference
        pose_part.comment = comment
        pose_part.install = (comment != "DNI")

    # PosePart.check():
    def check(self, collections, tracing=""):
        # Verify argument types:
        assert isinstance(collections, Collections)
        assert isinstance(tracing, str)

        # Grab some values from *pose_part* (i.e. *self*):
        pose_part = self
        reference = pose_part.reference
        project = pose_part.project
        project_name = project.name

        # Check the underlying *project_part*:
        project_part = pose_part.project_part
        search_name = project_part.name
        collections.check(search_name, project_name, reference)


# PositionRow:
class PositionRow:
    """ PositionRow: Represents one row of data for a *PositionsTable*: """

    # PositionRow.__init__():
    def __init__(self, reference, value, package, x, y,
                 rotation, feeder_name, pick_dx, pick_dy, side, part_height):
        """ *PositionRow*: ...
        """

        # Verify argument types:
        assert isinstance(reference, str)
        assert isinstance(value, str)
        assert isinstance(package, str)
        assert isinstance(x, float)
        assert isinstance(y, float)
        assert isinstance(rotation, float) and 0.0 <= rotation <= 360.0
        assert isinstance(feeder_name, str)
        assert isinstance(pick_dx, float)
        assert isinstance(pick_dy, float)
        assert isinstance(side, str)
        assert isinstance(part_height, float)

        # if package.startswith("DPAK"):
        #    print("Rotation={0}".format(rotation))

        # Load up *position_row* (i.e. *self*):
        position_row = self
        position_row.package = package
        position_row.part_height = part_height
        position_row.feeder_name = feeder_name
        position_row.rotation = rotation
        position_row.reference = reference
        position_row.side = side
        position_row.value = value
        position_row.x = x - pick_dx
        position_row.y = y - pick_dy
        position_row.pick_dx = pick_dx
        position_row.pick_dy = pick_dx

    # PositionsRow.as_strings():
    def as_strings(self, mapping, feeders):
        """ *PositionsRow*: Return a list of formatted strings.

        The arguments are:
        * *mapping*: The order to map the strings in.
        """

        # Verify argument types:
        assert isinstance(mapping, list) and len(mapping) == 7, "mapping={0}".format(mapping)
        assert isinstance(feeders, dict)

        positions_row = self
        value = positions_row.value
        if value not in feeders:
            print("There is no feeder for '{0}'".format(value))
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
    def part_rotate(self, rotation_adjust):
        """ *PostitionRow*: """

        assert isinstance(rotation_adjust, float)

        row = self
        rotation = row.rotation
        rotation -= rotation_adjust
        while rotation < 0.0:
            rotation += 360.0
        while rotation > 360.0:
            rotation -= 360.0
        row.rotation = rotation

    # PositionsRow.translate():
    def translate(self, dx, dy):
        """
        """

        row = self
        row.x += dx
        row.y += dy


# PositionsTable:
class PositionsTable:
    """ PositionsTable: Represents a part positining table for a Pick and Place machine. """

    # PositionsTable.__init__():
    def __init__(self, file_name, database):
        """ *PositionsTable*: Initialize the *PositionsTable* object read in from *file_name*:

        The arguments are:
        * *file_name*: The file name to read positions table from.  *file_name* must
          have one of the following suffixes:
          * `.csv`: A comma separated value format.
          * `.pos`: A text file with the columns separated by one or more spaces.
            Usually the columns are aligned virtically when viewe using a fixed
            pitch font.
        """

        # Verify argument types:
        assert isinstance(file_name, str) and (
          file_name.endswith(".csv") or file_name.endswith(".pos"))

        #
        positions_table = self
        comments = list()
        heading_indices = dict()
        rows = list()
        row_table = dict()
        mapping = list()
        trailers = list()
        headings_line = None
        headings = list()
        headings_size = 0
        part_heights = dict()

        # Process `.pos` and `.csv` *file_name*'s differently:
        if file_name.endswith(".pos"):
            # `.pos` suffix:

            # Read in *file_name* and break it into a *lines* list with no carriage returns:
            with open(file_name, "r") as positions_file:
                content = positions_file.read().replace('\r', "")
                lines = content.split('\n')

                # Start parsing the file *lines*:
                for line_number, line in enumerate(lines):
                    # Dispatch on the beginning of the *line*:
                    if line.startswith("##"):
                        # Lines starting with "##" or "###" are just *comments*:
                        if headings_size <= 0:
                            comments.append(line)
                        else:
                            trailers.append(line)
                        # print("comment='{0}'".format(line))
                    elif line.startswith("# "):
                        # Lines that start with "# " are the column headings:
                        assert headings_size <= 0
                        headings_line = line
                        headings = line[2:].split()
                        headings_size = len(headings)
                        assert headings_size > 0
                        for heading_index, heading in enumerate(headings):
                            heading_indices[heading] = heading_index
                            # print("key='{0}' index={1}".format(key, heading_index))

                        # Create the *mapping* used for formatting the output table:
                        heading_keys = ("Ref", "Val", "Package", "PosX", "PosY", "Rot", "Side")
                        for heading in heading_keys:
                            heading_index = heading_indices[heading]
                            mapping.append(heading_index)
                        # print("mapping={0}".format(mapping))
                    else:
                        # Assume that everything else is a row of data:
                        columns = line.split()
                        columns_size = len(columns)
                        if columns_size == headings_size:
                            # print("row={0}".format(row))
                            reference = columns[heading_indices["Ref"]]
                            value = columns[heading_indices["Val"]]
                            value = value.replace('\\', "")
                            part = database.lookup(value)
                            if isinstance(part, ChoicePart):
                                choice_part = part
                                feeder_name = choice_part.feeder_name
                                part_height = choice_part.part_height
                                pick_dx = choice_part.pick_dx
                                pick_dy = choice_part.pick_dy
                                if isinstance(feeder_name, str) and isinstance(part_height, float):
                                    # print("'{0}'=>'{1}''".format(value, feeder_name))
                                    value = feeder_name
                                    part_heights[value] = part_height
                                # print("part_heights['{0}'] = {1}".format(value, part_height))
                            elif isinstance(part, AliasPart):
                                alias_part = part
                                feeder_name = alias_part.feeder_name
                                part_height = alias_part.part_height
                                pick_dx = alias_part.pick_dx
                                pick_dy = alias_part.pick_dy
                                if isinstance(feeder_name, str) and isinstance(part_height, float):
                                    # print("'{0}'=>'{1}''".format(value, feeder_name))
                                    value = feeder_name
                                    part_heights[value] = part_height
                                # print("part_heights['{0}'] = {1}".format(value, part_height))
                            package = columns[heading_indices["Package"]]
                            x = float(columns[heading_indices["PosX"]])
                            y = float(columns[heading_indices["PosY"]])
                            rotation = float(columns[heading_indices["Rot"]])
                            side = columns[heading_indices["Side"]]
                            if isinstance(part_height, float):
                                row = PositionRow(reference, value, package, x, y, rotation,
                                                  feeder_name, pick_dx, pick_dy, side, part_height)
                                rows.append(row)
                                row_table[reference] = row
                            else:
                                print("Part '{0}' does not have a part_height".format(value))
                        elif columns_size != 0:
                            assert False, "Row/Header mismatch {0} {0}".format(row)  # , headers)
        elif file_name.endswith(".csv"):
            assert ".csv reader not implemented yet."
        else:
            assert "Bad file suffix for file: '{0}'".format(file_name)

        feeders = {
         "1uF":        "E1",
         "2N7002":     "E2",
         "27K":        "E4",
         "0":          "E5",
         "33":         "E7",
         "4.7uF_?":    "E11",
         "1.0M":       "E14",
         "49.9K":      "E16",
         "200K":       "E19",
         "BAT54":      "E21",
         "0.1uF":      "W4",
         "49.9":       "W6",
         "20k":        "W7",
         "330":        "W10",
         "10K":        "W11",
         "100":        "W15",
         "100K":       "W16",
         "5.1K":       "W17",
         "GRN_LED":    "W14",
         "470":        "W20",
         "10uF":       "W21",
         "120":        "W22",
         "4.7k":       "W23",
         "220":        "W24",

         "33nF":       "E100",
         "470nF":      "E101",
         "10nF":       "E102",
         "NFET_10A":   "E103",
         "330nF":      "E104",
         "18V_ZENER":  "E105",
         "SI8055":     "E106",
         "MC33883":    "E107",
         "MCP2562":    "E108",
         "18V_REG":    "E109",
         "74HC08":     "E110",
         "OPTOISO2":   "E111",
         "5V_REG/LDO": "E112",
         "3.3V_LDO":   "E113",
         "FID":        "E114",
         "10":         "E115",
        }

        # Write out `feeders.txt`:
        footprints = database.footprints
        quintuples = list()
        for key in feeders.keys():
            feeder_name = feeders[key]
            part_height = "{0:.2f}".format(part_heights[key]) if key in part_heights else "----"
            rotation = int(footprints[key].rotation) if key in footprints else "----"
            quintuple = (feeder_name[0], int(feeder_name[1:]), key, part_height, rotation)
            quintuples.append(quintuple)
        quintuples.sort()
        order_root = None
        feeders_file_name = os.path.join(order_root, "feeders.txt")
        with open(feeders_file_name, "w") as feeders_file:
            feeders_file.write("Feeder\tHeight\tRotate\tValue\n")
            feeders_file.write(('=' * 50) + '\n')
            for quintuple in quintuples:
                side = quintuple[0]
                number = quintuple[1]
                value = quintuple[2]
                rotation = quintuple[2]
                part_height = quintuple[3]
                rotation = quintuple[4]
                feeders_file.write(f"{side}{number}:\t{part_height}\t{rotation}\t{value}\n")

        # Fill in the value of *positions_table* (i.e. *self*):
        positions_table.comments = comments
        positions_table.headings_line = headings_line
        positions_table.headings = headings
        positions_table.headings_indices = heading_indices
        positions_table.feeders = feeders
        positions_table.file_name = file_name
        positions_table.mapping = mapping
        positions_table.rows = rows
        positions_table.row_table = row_table
        positions_table.trailers = trailers

    # PositionsTable.footprints_rotate():
    def footprints_rotate(self, database):
        """ *Positions_Table: ..."""

        order_root = None
        positions_table = self
        file_name = positions_table.file_name
        footprints = database.footprints
        rows = positions_table.rows
        for row_index, row in enumerate(rows):
            feeder_name = row.feeder_name
            debugging = False
            # debugging = package == "DPAK"
            # print("Row[{0}]: '{1}'".format(row_index, package))
            if feeder_name in footprints:
                # We have a match:
                footprint = footprints[feeder_name]
                rotation = footprint.rotation
                if debugging:
                    print("rotation={0}".format(rotation))
                if isinstance(rotation, float):
                    row.part_rotate(rotation)
                else:
                    print("Footprint '{0}' does not have a feeder rotation.".format(feeder_name))
            else:
                # No match:
                print("Could not find footprint '{0}' from file '{1}'".
                      format(feeder_name, file_name))
        positions_table.write(os.path.join(order_root, file_name))

    # PositionsTable.reorigin():
    def reorigin(self, reference):
        """
        """

        positions = self
        row_table = positions.row_table
        if reference in row_table:
            row = row_table[reference]
            dx = -row.x
            dy = -row.y
            positions.translate(dx, dy)

    # PositionsTable.translate():
    def translate(self, dx, dy):
        """
        """

        positions = self
        rows = positions.rows
        for row in rows:
            row.translate(dx, dy)

    # PositionsTable.write():
    def write(self, file_name):
        """ *PositionsTable*: Write out the *PostionsTable* object to *file_name*.

        The arguments are:
        * *file_name*: specifies the file to write out to.  It must of a suffix of:
          * `.csv`: Writes the file out in Comma Separated Values format.
          * `.pos`: Writes the file out as a text file with data separated by spaces.
        """

        # Verify argument types:
        assert isinstance(file_name, str)
        assert len(file_name) >= 4 and file_name[-4:] in (".csv", ".pos")

        # Unpack the *positions_table* (i.e. *self*):
        positions_table = self
        comments = positions_table.comments
        headings_line = positions_table.headings_line
        headings = positions_table.headings
        rows = positions_table.rows
        mapping = positions_table.mapping
        trailers = positions_table.trailers
        feeders = positions_table.feeders

        # In order exactly match KiCAD output, the output formatting is adjusted based
        # on the column heading. *spaces_table* specifies the extra spaces to add to the column.
        # *aligns_table* specifies whether the data is left justified (i.e. "") or right
        # justified (i.e. ">"):
        extras_table = {"Ref": 5, "Val": 0, "Package": 1, "PosX": 0, "PosY": 0, "Rot": 0, "Side": 0}
        aligns_table = {"Ref": "", "Val": "", "Package": "",
                        "PosX": ">", "PosY": ">", "Rot": ">", "Side": ""}

        # Build up the final output as a list of *final_lines*:
        final_lines = list()

        # Just copy the *comments* and *headings_line* into *final_lines*:
        final_lines.extend(comments)
        final_lines.append(headings_line)

        # Dispatch on *file_name* suffix:
        if file_name.endswith(".pos"):
            # We have a `.pos` file:

            # Populate *string_rows* with strings containing the data:
            string_rows = list()
            for row in rows:
                string_row = row.as_strings(mapping, feeders)
                string_rows.append(string_row)

            # Figure out the maximum *sizes* for each column:
            sizes = [0] * len(headings)
            for string_row in string_rows:
                for column_index, column in enumerate(string_row):
                    sizes[column_index] = max(sizes[column_index], len(column))

            # Convert *aligns_table* into a properly ordered list of *aligns*:
            aligns = list()
            for header_index, header in enumerate(headings):
                sizes[header_index] += extras_table[header]
                aligns.append(aligns_table[header])

            # Create a *format_string* for outputing each row:
            format_columns = list()
            for size_index, size in enumerate(sizes):
                format_columns.append("{{{0}:{1}{2}}}".format(size_index, aligns[size_index], size))
                # format_columns.append("{" + str(size_index) +
                #  ":" + aligns[size_index] + str(size) + "}")
            format_string = "  ".join(format_columns)
            # print("format_string='{0}'".format(format_string))

            # Now format each *string_row* and append the result to *final_lines*:
            for string_row in string_rows:
                final_line = format_string.format(*string_row)
                final_lines.append(final_line)

            # Tack *trailers* and an empty line onto *final_lines*:
            final_lines.extend(trailers)
            final_lines.append("")
        elif file_name.endswith(".csv"):
            # File is a `.csv` file:
            assert False, ".csv file support not implemented yet."
        else:
            assert False, ("File name ('{0}') does not have a suffixe of .csv or .pos".
                           format(file_name))

        # Write *final_lines* to *file_name*:
        with open(file_name, "w") as output_file:
            output_file.write("\r\n".join(final_lines))


# PriceBreak:
class PriceBreak:
    # A price break is where a the pricing changes:

    # PriceBreak.__init__():
    def __init__(self, quantity, price):
        """ *PriceBreak*: Initialize *self* to contain *quantity*
            and *price*.  """

        # Verify argument types:
        assert isinstance(quantity, int)
        assert isinstance(price, float)

        # Load up *self*;
        self.quantity = quantity
        self.price = price
        self.order_quantity = 0
        self.order_price = 0.00

    # PriceBreak.__format__():
    def __format__(self, format):
        """ *PriceBreak*: Return the *PriceBreak* object as a human redable string.
        """

        # Grab some values from *price_break* (i.e. *self*):
        price_break = self
        quantity = price_break.quantity
        price = price_break.price
        result = "{0}/{1}".format(quantity, price)
        # print("Result='{0}'".format(result))
        return result

    # PriceBreak.__eq__():
    def __eq__(self, price_break2):
        # Verify argument types:
        assert isinstance(price_break2, PriceBreak)

        price_break1 = self
        price_breaks_equal = (price_break1.quantity == price_break2.quantity and
                              price_break1.price == price_break2.price)
        return price_breaks_equal

    # PriceBreak.__lt__():
    def __lt__(self, price_break2):
        # Verify argument types:
        assert isinstance(price_break2, PriceBreak)

        price_break1 = self
        return price_break1.price < price_break2.price

    # PriceBreak.compute():
    def compute(self, needed):
        """ *PriceBreak*: """

        assert isinstance(needed, int)

        self.order_quantity = order_quantity = max(needed, self.quantity)
        self.order_price = order_quantity * self.price

    # PriceBreak.xml_lines_append():
    def xml_lines_append(self, xml_lines, indent):
        # Verify argument types:
        assert isinstance(xml_lines, list)
        assert isinstance(indent, str)

        # Grab some values from *price_break* (i.e. *self*):
        price_break = self
        quantity = price_break.quantity
        price = price_break.price

        # Output `<PriceBreak ...>` tag:
        xml_lines.append('{0}<PriceBreak quantity="{1}" price="{2:.6f}"/>'.
                         format(indent, quantity, price))

    # PriceBreak.xml_parse():
    @staticmethod
    def xml_parse(price_break_tree):
        # Verify argument types:
        assert isinstance(price_break_tree, etree._Element)
        assert price_break_tree.tag == "PriceBreak"

        # Grab some the attribute values from *price_break_tree*:
        attributes_table = price_break_tree.attrib
        quantity = int(attributes_table["quantity"])
        price = float(attributes_table["price"])

        # Create and return the new *PriceBreak* object:
        price_break = PriceBreak(quantity, price)
        return price_break


# Project:
class Project:

    # Project.__init__():
    def __init__(self, name, revision, cad_file_name, count, order,
                 positions_file_name=None, tracing=""):
        """ Initialize a new *Project* object (i.e. *self*) containing *name*, *revision*,
            *net_file_name*, *count*, *order*, and optionally *positions_file_name.
        """

        # Verify argument types:
        assert isinstance(name, str)
        assert isinstance(revision, str)
        assert isinstance(cad_file_name, str)
        assert isinstance(count, int)
        assert isinstance(order, Order)
        assert isinstance(positions_file_name, str) or positions_file_name is None
        assert isinstance(tracing, str)

        # Load up *project* (i.e. *self*):
        project = self
        project.name = name
        project.revision = revision
        project.cad_file_name = cad_file_name
        project.count = count
        project.positions_file_name = positions_file_name
        project.order = order
        project.pose_parts_table = {}        # Dict[name, ProjectPart]
        project.project_parts = []           # List[ProjectPart]
        project.project_parts_table = {}     # Dict[name, ProjectPart]
        project.all_pose_parts = []          # List[PosePart] of all project parts
        project.installed_pose_parts = []    # List[PosePart] project parts to be installed
        project.uninstalled_pose_parts = []  # List[PosePart] project parts not to be installed

        # Read in the *cad_file_name*:
        success = False
        cads = order.cads
        for cad in cads:
            assert isinstance(cad, Cad)
            success = cad.file_read(cad_file_name, project)
            if success:
                break
        assert success, f"Could not successfully read and process file '{cad_file_name}'!"

    # Project.__format__():
    def __format__(self, format):
        # Verify arugment_types:
        assert isinstance(format, str)

        # Grab some values from *project* (i.e. *self*):
        project = self
        name = project.name
        revision = project.revision
        # Return *result*:
        result = f"{name}.{revision}"
        return result

    # Project.assembly_summary_write():
    @trace(1)
    def assembly_summary_write(self, final_choice_parts, order, tracing=""):
        """ Write out an assembly summary .csv file for the *Project* object (i.e. *self*)
            using *final_choice_parts*.
        """

        # Verify argument types:
        assert isinstance(final_choice_parts, list)
        assert isinstance(order, Order)
        assert isinstance(tracing, str)

        # Open *project_file* (i.e. *self*):
        project = self
        order_root = order.order_root
        project_file_name = os.path.join(order_root, f"{project.name}.csv")
        with open(project_file_name, "w") as project_file:
            # Write out the column headings:
            project_file.write(
              '"Quan.","Reference","Schematic Name","Description","Fractional",' +
              '"Manufacturer","Manufacture PN","Vendor","Vendor PN"\n\n')

            # Output the installed parts:
            has_fractional_parts1 = project.assembly_summary_write_helper(True, final_choice_parts,
                                                                          project_file)

            # Output the uninstalled parts:
            project_file.write("\nDo Not Install\n")

            # Output the installed parts:
            has_fractional_parts2 = project.assembly_summary_write_helper(False, final_choice_parts,
                                                                          project_file)

            # Explain what a fractional part is:
            if has_fractional_parts1 or has_fractional_parts2:
                project_file.write(
                  '"","\nFractional parts are snipped off of 1xN or 2xN break-way headers"\n')

            # Close *project_file* and print out a summary announcement:

        # Write out a progress message:
        print("Wrote out assembly file '{0}'".format(project_file_name))

    # Project.assembly_summary_write_helper():
    def assembly_summary_write_helper(self, install, final_choice_parts, project_file):
        """ Write out an assembly summary .csv file for *Project* object (i.e. *self*)
            out to *project_file*.  *install* is set *True* to list the installable parts from
            *final_choice_parts* and *False* for an uninstallable parts listing.
            This routine returns *True* if there are any fractional parts output to *project_file*.
        """

        # Verify argument types:
        assert isinstance(install, bool)
        assert isinstance(final_choice_parts, list)
        assert isinstance(project_file, io.IOBase)

        # Each *final_choice_part* that is part of the project (i.e. *self*) will wind up
        # in a list in *pose_parts_table*.  The key is the *project_part_key*:
        project = self
        pose_parts_table = {}
        for final_choice_part in final_choice_parts:
            # Now figure out if final choice part is part of *pose_parts*:
            pose_parts = final_choice_part.pose_parts
            for pose_part in pose_parts:
                # We only care care about *final_choice_part* if is used on *project* and
                # it matches the *install* selector:
                if pose_part.project is project and pose_part.install == install:
                    # We are on the project; create *schemati_part_key*:
                    project_part = pose_part.project_part
                    project_part_key = "{0};{1}".format(
                      project_part.base_name, project_part.short_footprint)

                    # Create/append a list to *pose_parts_table*, keyed on *project_part_key*:
                    if project_part_key not in pose_parts_table:
                        pose_parts_table[project_part_key] = []
                    pairs_list = pose_parts_table[project_part_key]

                    # Append a pair of *pose_part* and *final_choice_part* onto *pairs_list*:
                    project_final_pair = (pose_part, final_choice_part)
                    pairs_list.append(project_final_pair)

        # Now organize everything around the *reference_list*:
        reference_pose_parts = {}
        for pairs_list in pose_parts_table.values():
            # We want to sort base on *reference_value* which is converted into *reference_text*:
            reference_list = \
              [project_final_pair[0].reference.upper() for project_final_pair in pairs_list]
            reference_text = ", ".join(reference_list)
            # print("reference_text='{0}'".format(reference_text))
            pose_part = pairs_list[0]
            reference_pose_parts[reference_text] = pose_part

        # Sort the *reference_parts_keys*:
        reference_pose_parts_keys = list(reference_pose_parts.keys())
        reference_pose_parts_keys.sort()

        # Now dig down until we have all the information we need for output the next
        # `.csv` file line:
        has_fractional_parts = False
        for reference_pose_parts_key in reference_pose_parts_keys:
            # Extract the *pose_part* and *final_choice_part*:
            project_final_pair = reference_pose_parts[reference_pose_parts_key]
            pose_part = project_final_pair[0]
            final_choice_part = project_final_pair[1]
            assert isinstance(final_choice_part, ChoicePart)

            # Now get the corresponding *project_part*:
            project_part = pose_part.project_part
            project_part_key = "{0};{1}".format(
              project_part.base_name, project_part.short_footprint)
            assert isinstance(project_part, ProjectPart)

            # Now get the *actual_part*:
            actual_part = final_choice_part.selected_actual_part
            if isinstance(actual_part, ActualPart):

                # Now get the VendorPart:
                manufacturer_name = actual_part.manufacturer_name
                manufacturer_part_name = actual_part.manufacturer_part_name
                vendor_part = final_choice_part.selected_vendor_part
                assert isinstance(vendor_part, VendorPart)

                # Output the line for the .csv file:
                vendor_name = vendor_part.vendor_name
                vendor_part_name = vendor_part.vendor_part_name
                quantity = final_choice_part.count_get()
                fractional = "No"
                if len(final_choice_part.fractional_parts) > 0:
                    fractional = "Yes"
                    has_fractional_parts = True
                project_file.write('"{0} x","{1}","{2}","{3}","{4}","{5}","{6}","{7}","{8}"\n'.
                                   format(quantity, reference_pose_parts_key,
                                          project_part_key, final_choice_part.description,
                                          fractional, manufacturer_name, manufacturer_part_name,
                                          vendor_name, vendor_part_name))
            else:
                print("Problems with actual_part", actual_part)

        return has_fractional_parts

    # Project.check():
    def check(self, collections, tracing=""):
        # Verify argument types:
        assert isinstance(collections, Collections)

        # Grab some values from *project* (i.e. *self*):
        project = self
        name = project.name
        all_pose_parts = project.all_pose_parts

        # Check *all_pose_parts*:
        for pose_part in all_pose_parts:
            pose_part.check(collections)

    # Project.project_part_append():
    def pose_part_append(self, pose_part):
        """ Append *pose_part* onto the *Project* object (i.e. *self*).
        """

        # Verify argument types:
        assert isinstance(pose_part, PosePart)

        # Tack *pose_part* onto the appropriate lists inside of *project*:
        project = self
        project.all_pose_parts.append(pose_part)
        if pose_part.install:
            project.installed_pose_parts.append(pose_part)
        else:
            project.uninstalled_pose_parts.append(pose_part)

    # Project.pose_part_find():
    def pose_part_find(self, name, reference):
        # Verify argument types:
        assert isinstance(name, str)
        assert isinstance(reference, str)

        # Grab some values from *project_part* (i.e. *self*):
        project = self
        all_pose_parts = project.all_pose_parts
        pose_parts_table = project.pose_parts_table

        # Find the *project_part* named *name* associated with *project*:
        project_part = project.project_part_find(name)

        # Make sure that *reference* is not a duplicated:
        if reference in pose_parts_table:
            pose_part = pose_parts_table[reference]
            print(f"Project {project} has a duplicate '{reference}'?")
        else:
            pose_part = PosePart(project_part, reference, "")
            pose_parts_table[reference] = pose_part
            all_pose_parts.append(pose_part)
        return pose_part

    # Project.positions_process():
    def positions_process(self, database):
        """ Reorigin the the contents of the positions table.
        """

        project = self
        positions_file_name = project.positions_file_name
        positions_table = PositionsTable(positions_file_name, database)
        positions_table.reorigin("FD1")
        positions_table.footprints_rotate(database)

    # Project.project_part_find():
    def project_part_find(self, project_part_name):
        # Verify argument types:
        assert isinstance(project_part_name, str)

        # Grab some values from *project*:
        project = self
        project_parts = project.project_parts
        project_parts_table = project.project_parts_table

        # Determine if we have a pre-existing *project_part* named *name*:
        if project_part_name in project_parts_table:
            # Reuse the pre-existing *project_part* named *name*:
            project_part = project_parts_table[project_part_name]
        else:
            # Create a new *project_part* named *name* and stuff into the *project* data structures:
            project_part = ProjectPart(project_part_name, [project])
            project_parts.append(project_part)
            project_parts_table[project_part_name] = project_part
        assert isinstance(project_part, ProjectPart)
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
    def __init__(self, name, projects):
        """ *ProjectPart*: Initialize *self* to contain
            *name*, and *kicad_footprint*. """

        # Verify argument types:
        assert isinstance(name, str)
        assert isinstance(projects, list)
        for project in projects:
            assert isinstance(project, Project)

        # Split *name" into *base_name* and *short_footprint*:
        # base_name_short_footprint = name.split(';')
        # if len(base_name_short_footprint) == 2:
        #     base_name = base_name_short_footprint[0]
        #     short_footprint = base_name_short_footprint[1]
        #
        #     # Load up *self*:
        #     project_part.name = name
        #     project_part.base_name = base_name
        #     project_part.short_footprint = short_footprint
        #     project_part.kicad_footprint = kicad_footprint
        #     project_part.pose_parts = []
        # else:

        # Stuff values into *project_part* (i.e. *self*):
        project_part = self
        project_part.name = name
        project_part.projects = projects
        project_part.pose_parts = []        # List[PosePart]
        project_part.pose_parts_table = {}  # Dict[reference, PosePart]

    # ProjectPart.__format__():
    def __format__(self, format):
        """ *ProjectPart*: Format the *ProjectPart* object (i.e. *self*) using *format***. """
        # Verify aregument types:
        assert isinstance(format, str)

        # Grab some values from *project_part* (i.e. *self*):
        project_part = self
        name = project_part.name
        project = project_part.project

        # Return *result*' based on *format*:
        result = f"{name}" if format == "s" else f"{project}:{name}"
        return result

    # ProjectPart.footprints_check():
    def footprints_check(self, kicad_footprints):
        """ *ProjectPart*: Verify that all the footprints exist for the *ProjectPart* object
            (i.e. *self*.)
        """

        assert False, "No footprints_check method for this Schematic Part"


# AliasPart():
class AliasPart(ProjectPart):
    # An *AliasPart* specifies one or more *ProjectParts* to use.

    # AliasPart.__init__():
    def __init__(self, name, project_parts, kicad_footprint,
                 feeder_name=None, part_height=None, pick_dx=0.0, pick_dy=0.0):
        """ *AliasPart*: Initialize *self* to contain *name*,
            *kicad_footprint*, and *project_parts*. """

        # Verify argument types:
        assert isinstance(name, str)
        assert isinstance(project_parts, list)
        assert isinstance(feeder_name, str) or feeder_name is None
        assert isinstance(part_height, float) or part_height is None
        assert isinstance(pick_dx, float)
        assert isinstance(pick_dy, float)
        for project_part in project_parts:
            assert isinstance(project_part, ProjectPart)

        # assert len(project_parts) == 1, "project_parts={0}".format(project_parts)

        # Load up *alias_part* (i.e *self*):
        alias_part = self
        super().__init__(name, kicad_footprint)
        alias_part.project_parts = project_parts
        alias_part.feeder_name = feeder_name
        alias_part.part_height = part_height
        alias_part.pick_dx = pick_dx
        alias_part.pick_dy = pick_dy

    # AliasPart.choice_parts():
    def choice_parts(self):
        """ *AliasPart*: Return a list of *ChoicePart*'s corresponding to *self*
        """

        assert isinstance(self, AliasPart)
        choice_parts = []
        for project_part in self.project_parts:
            choice_parts += project_part.choice_parts()

        # assert False, \
        #  "No choice parts for '{0}'".format(self.name)
        return choice_parts

    # AliasPart.footprints_check():
    def footprints_check(self, kicad_footprints):
        """ *AliasPart*: Verify that all the footprints exist for the *AliasPart* object
            (i.e. *self*.)
        """

        # Use *alias_part* instead of *self*:
        alias_part = self

        # Verify argument types:
        assert isinstance(kicad_footprints, dict)

        # Visit all of the listed schematic parts:
        project_parts = alias_part.project_parts
        for project_part in project_parts:
            project_part.footprints_check(kicad_footprints)


# ChoicePart:
class ChoicePart(ProjectPart):
    # A *ChoicePart* specifies a list of *ActualPart*'s to choose from.

    # ChoicePart.__init__():
    def __init__(self, name, project_parts, searches):
        """ *ChoicePart*: Initiailize *self* to contain *name*
            *kicad_footprint* and *actual_parts*. """

        # Verify argument types:
        assert isinstance(name, str)  # I.e. search name
        assert isinstance(project_parts, list)
        assert isinstance(searches, list)
        for project_part in project_parts:
            assert project_part.name == name
        for search in searches:
            assert search.name == name

        # assert isinstance(kicad_footprint, str)
        # assert isinstance(location, str)
        # assert isinstance(description, str)
        # assert isinstance(rotation, float) or rotation is None
        # assert isinstance(pick_dx, float)
        # assert isinstance(pick_dy, float)
        # assert isinstance(feeder_name, str) or feeder_name is None
        # assert isinstance(part_height, float) or part_height is None

        # Use *choice_part* instead of *self*:
        choice_part = self

        # A *chice_part* (i.e. *self*) can have multiple *Project*'s associated with it.
        # Thus, we need to compute the *union_projects* of all *Project*'s associated
        # with *project parts*:
        projects_table = {}
        for project_part in project_parts:
            projects = project_part.projects
            for project in projects:
                cad_file_name = project.cad_file_name
                projects_table[cad_file_name] = project
        union_projects = list(projects_table.values())

        # Load up *choice_part* (i.e. *self*):
        super().__init__(name, union_projects)
        choice_part.actual_parts = []
        choice_part.searches = searches

        # Fields used by algorithm:
        choice_part.fractional_parts = []
        choice_part.selected_total_cost = -0.01
        choice_part.selected_order_quantity = -1
        choice_part.selected_actual_part = None
        choice_part.selected_vendor_part = None
        choice_part.selected_vendor_name = ""
        choice_part.selected_price_break_index = -1
        choice_part.selected_price_break = None

        # choice_part.description = description
        # choice_part.feeder_name = feeder_name
        # choice_part.location = location
        # choice_part.part_height = part_height
        # choice_part.rotation = rotation
        # choice_part.pick_dx = pick_dx
        # choice_part.pick_dy = pick_dy

    # ChoicePart.__format__():
    def __format__(self, format):
        """ *ChoicePart*: Return the *ChoicePart object (i.e. *self* as a string formatted by
            *format*.
        """

        choice_part = self
        return choice_part.__str__()

    # ChoicePart.__str__():
    def __str__(self):
        choice_part = self
        return f"ChoicePart('{choice_part.name}')"

    # ChoicePart.actual_part():
    def actual_part(self, manufacturer_name, manufacturer_part_name, vendor_triples=[]):
        """ *ChoicePart*: Create an *ActualPart* that contains *manufacturer_name* and
            *manufacturer_part_name* and append it to the *ChoicePart* object (i.e. *self*.)
            For parts whose prices are not available via screen scraping, it is possible to specify
            vendor/pricing information as a list of vendor triples.  The vendor triples are a
            *tuple* of consisting of (*vendor_name*, *vendor_part_name*, *price_pairs_text*),
            where *vendor_name* is a distributor (i.e. "Newark", or "Pololu"), *vendor_part_name*
            is a the vendors order number of the part, and *price_pairs_text* is a string of
            the form "quant1/price1 quant2/price2 ... quantN/priceN".  *quantI* is an quantity
            as an integer and *priceI* is a price in dollars.
        """

        # Verify argument types:
        assert isinstance(manufacturer_name, str)
        assert isinstance(manufacturer_part_name, str)
        assert isinstance(vendor_triples, list)
        for vendor_triple in vendor_triples:
            assert len(vendor_triple) == 3
            assert isinstance(vendor_triple[0], str)
            assert isinstance(vendor_triple[1], str)
            assert isinstance(vendor_triple[2], str)

        actual_part = ActualPart(manufacturer_name, manufacturer_part_name)
        self.actual_parts.append(actual_part)

        if True:
            for vendor_triple in vendor_triples:
                vendor_name = vendor_triple[0]
                vendor_part_name = vendor_triple[1]
                price_pairs_text = vendor_triple[2]

                price_breaks = []
                for price_pair_text in price_pairs_text.split():
                    # Make sure we only have a price and a pair*:
                    price_pair = price_pair_text.split('/')
                    assert len(price_pair) == 2

                    # Extract the *quantity* from *price_pair*:
                    quantity = 1
                    try:
                        quantity = int(price_pair[0])
                    except ValueError:
                        assert False, \
                          "Quantity '{0}' is not an integer". \
                          format(price_pair[0])

                    # Extract the *price* from *price_pair*:
                    price = 100.00
                    try:
                        price = float(price_pair[1])
                    except ValueError:
                        assert False, \
                          "Price '{0}' is not a float".format(price_pair[1])

                    # Construct the *price_break* and append to *price_breaks*:
                    price_break = PriceBreak(quantity, price)
                    price_breaks.append(price_break)

                # Create the *vendor_part* and append it to *actual_part*:
                assert len(price_breaks) > 0
                vendor_part = VendorPart(actual_part,
                                         vendor_name, vendor_part_name, 1000000, price_breaks)
                actual_part.vendor_part_append(vendor_part)
                # if tracing:
                #    print("vendor_part_append called")

                # print("ChoicePart.actual_part(): Explicit vendor_part specified={0}".
                #  format(vendor_part))

        return self

    # ChoicePart.pose_part_append():
    def pose_part_append(self, pose_part):
        """ *ChoicePart*: Store *pose_part* into the *ChoicePart* object
            (i.e. *self*.)
        """

        # Verify argument types:
        assert isinstance(pose_part, PosePart)

        # Append *pose_part* to *pose_parts*:
        self.pose_parts.append(pose_part)

    # ChoicePart.pose_parts_sort():
    def pose_parts_sort(self):
        """ *ChoicePart*: Sort the *pose_parts* of the *ChoicePart* object
            (i.e. *self*.)
        """

        # Sort the *pose_parts* using a key of
        # (project_name, reference, reference_number).  A reference of
        # "SW123" gets conferted to (..., "SW123", 123):
        pose_parts = self.pose_parts
        pose_parts.sort(key=lambda pose_part:
                        (pose_part.project.name,
                         text_filter(pose_part.reference, str.isalpha).upper(),
                         int(text_filter(pose_part.reference, str.isdigit))))

        # print("  {0}:{1};{2} {3}:{4}".\
        #  format(choice_part.name,
        # choice_part.kicad_footprint, choice_part.description,
        #  choice_part.count_get(), choice_part.references_text_get()))

    # ChoicePart.count_get():
    def count_get(self):
        """ *ChoicePart*: Return the number of needed instances of *self*. """

        count = 0

        fractional_parts = self.fractional_parts
        if len(fractional_parts) == 0:
            for pose_part in self.pose_parts:
                count += pose_part.project.count
        else:
            # for fractional_part in fractional_parts:
            #        print("{0}".format(fractional_part.name))

            # This code is not quite right:
            first_fractional_part = fractional_parts[0]
            denominator = first_fractional_part.denominator
            for fractional_part in fractional_parts[1:]:
                assert denominator == fractional_part.denominator, \
                  "'{0}' has a denominator of {1} and '{2}' has one of {3}". \
                  format(first_fractional_part.name,
                         first_fractional_part.denominator,
                         fractional_part.name,
                         fractional_part.denominator)

            # Compute the *count*:
            numerator = 0
            for pose_part in self.pose_parts:
                project_part = pose_part.project_part
                # print("'{0}'".format(project_part.name))
                if isinstance(project_part, AliasPart):
                    alias_parts = project_part
                    for project_part in alias_parts.project_parts:
                        if isinstance(project_part, FractionalPart):
                            fractional_part = project_part
                elif isinstance(project_part, FractionalPart):
                    fractional_part = project_part
                else:
                    assert False, "Missing code"

                fractional_numerator = fractional_part.numerator
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
    def choice_parts(self):
        """ *ChoicePart*: Return a list of *ChoicePart* corresponding
            to *self* """

        assert isinstance(self, ChoicePart)
        return [self]

    # ChoicePart.footprints_check():
    def footprints_check(self, kicad_footprints):
        """ *ChoicePart*: Verify that all the footprints exist for the *ChoicePart* object
            (i.e. *self*.)
        """

        # Use *choice_part* instead of *self*:
        choice_part = self

        # Verify argument types:
        assert isinstance(kicad_footprints, dict)

        kicad_footprint = choice_part.kicad_footprint
        if kicad_footprint != "-":
            kicad_footprints[kicad_footprint] = choice_part.name
            # rotation = choice_part.rotation

    # ChoicePart.references_text_get():
    def references_text_get(self):
        """ *ChoicePart*: Return a string of references for *self*. """

        references_text = ""
        previous_project = None
        is_first = True
        for pose_part in self.pose_parts:
            project = pose_part.project
            if project != previous_project:
                if not is_first:
                    references_text += "]"
                references_text += "[{0}:".format(project.name)
            previous_project = project
            is_first = False

            # Now tack the reference to the end:
            references_text += " {0}".format(pose_part.reference)
        references_text += "]"
        return references_text

    # ChoicePart.select():
    def select(self, excluded_vendor_names, announce=False, tracing=""):
        """ *ChoicePart*: Select and return the best priced *ActualPart*
            for the *ChoicePart* (i.e. *self*) excluding any vendors
            in the *excluded_vendor_names* dictionary.
        """
        # Verify argument types:
        assert isinstance(excluded_vendor_names, dict)
        assert isinstance(announce, bool)
        assert isinstance(tracing, str)

        global trace_level

        # This lovely piece of code basically brute forces the decision
        # process of figuring out which *vendor_part* to select and the
        # number of parts to order.  We iterate over each *actual_part*,
        # *vendor_part* and *price_break* and compute the *total_cost*
        # and *order_quanity* for that combination.  We store this into
        # a 5-tuple called *quint* and build of the list of *quints*.
        # When we are done, we sort *quints* and select the first one
        # off the head of the list.

        # Grab some values from *choice_part* (i.e. *self*):
        choice_part = self
        required_quantity = choice_part.count_get()
        actual_parts = choice_part.actual_parts
        actual_parts_size = len(actual_parts)
        quints = []

        for actual_part_index, actual_part in enumerate(actual_parts):
            if tracing and trace_level >= 1: 
                manufacturer_name = actual_part.manufacturer_name
                manufacturer_part_name = actual_part.manufacturer_part_name
                print(f"{tracing} Manufacturer: '{manufacturer_name}' '{manufacturer_part_name}'")
            vendor_parts = actual_part.vendor_parts
            for vendor_part_index, vendor_part in enumerate(vendor_parts):
                # if trace_level:
                #     print(f"Vendor: {vendor_part.vendor_name}: "
                #           f"'{vendor_part.vendor_part_name}':"
                #           f":{vendor_part.quantity_available}")
                if tracing and trace_level >= 2:
                    vendor_name = vendor_part.vendor_name
                    vendor_part_name = vendor_part.vendor_part_name
                    print(f"{tracing}  Vendor: '{vendor_name}': '{vendor_part_name}'")
                price_breaks = vendor_part.price_breaks
                for price_break_index, price_break in enumerate(price_breaks):
                    # if tracing:
                    #        print("  B")

                    # We not have an *actual_part*, *vendor_part* and
                    # *price_break* triple.  Compute *order_quantity*
                    # and *total_cost*:
                    price = price_break.price
                    quantity = price_break.quantity
                    order_quantity = max(required_quantity, quantity)
                    total_cost = order_quantity * price
                    # if tracing:
                    #     print("   price={0:.2f} quant={1} order_quantity={2} total_cost={3:.2f}".
                    #           format(price, quantity, order_quantity, total_cost))

                    # Assemble the *quint* and append to *quints* if there
                    # enough parts available:
                    is_excluded = vendor_part.vendor_name in excluded_vendor_names
                    #if trace_level:
                    #    print(f"quantity_available={vendor_part.quantity_available}, "
                    #          f"is_excluded={is_excluded}")
                    if tracing and trace_level >= 3:
                        quantity_available = vendor_part.quantity_available
                        print(f"{tracing}   Quantity Available:{quantity_available} "
                              f"Is Excluded:{is_excluded}")
                    if not is_excluded and vendor_part.quantity_available >= order_quantity:
                        assert price_break_index < len(price_breaks)
                        quint = (total_cost, order_quantity,
                                 actual_part_index, vendor_part_index,
                                 price_break_index, len(price_breaks))
                        quints.append(quint)
                        if tracing:
                            print(f"{tracing}    quint={quint}")

        if len(quints) == 0:
            choice_part_name = self.name
            if announce:
                print("No vendor parts found for Part '{0}'".format(choice_part_name))
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

        missing_part = 0
        if len(quints) == 0:
            missing_part = 1

        return missing_part

    # ChoicePart.vendor_names_load():
    def vendor_names_load(self, vendor_names_table, excluded_vendor_names):
        """ *ChoicePart*: Add each possible vendor name possible for the
            *ChoicePart* object (i.e. *self*) to *vendor_names_table*
            provided it is not in *excluded_vendor_names*:
        """

        # Verify argument types:
        assert isinstance(vendor_names_table, dict)
        assert isinstance(excluded_vendor_names, dict)

        # Visit each *actual_part* and add the vendor names to
        # *vendor_names_table*:
        for actual_part in self.actual_parts:
            actual_part.vendor_names_load(
              vendor_names_table, excluded_vendor_names)

    # ChoicePart.vendor_parts_refresh():
    @trace(1)
    def vendor_parts_refresh(self, proposed_actual_parts, order, part_name, tracing=""):
        # Verify argument types:
        assert isinstance(proposed_actual_parts, list)
        assert isinstance(order, Order)
        assert isinstance(part_name, str)
        assert isinstance(tracing, str)

        # Grab some values from *choice_part* (i.e. *self*) and *order*:
        choice_part = self
        choice_part_name = choice_part.name
        pandas = order.pandas
        stale = order.stale
        vendor_searches_root = order.vendor_searches_root

        # Construct the file path for the `.xml` file associated *choice_part*:
        xml_base_name = Encode.to_file_name(choice_part_name + ".xml")
        xml_full_name = os.path.join(vendor_searches_root, xml_base_name)
        if tracing:
            print(f"{tracing}choice_part_name='{choice_part_name}'")
            print(f"{tracing}vendor_searches_root='{vendor_searches_root}'")
            print(f"{tracing}xml_base_name='{xml_base_name}'")
            print(f"{tracing}xml_full_name='{xml_full_name}'")

        # Open *xml_full_name*, read it in, and fill in *previous_actual_parts_table* with
        # the resulting *previous_actual_part* from the `.xml` file.  Mark *xml_save_required*
        # as *True* if *xml_full_file_name* does not exist:
        xml_save_required = False
        previous_actual_parts = list()
        previous_actual_parts_table = dict()
        if os.path.isfile(xml_full_name):
            # Read in and parse the *xml_full_name* file:
            with open(xml_full_name) as xml_read_file:
                choice_part_xml_text = xml_read_file.read()
                choice_part_tree = etree.fromstring(choice_part_xml_text)

                # Note that *previous_choice_part* is kind of busted since it
                # its internal *project_parts* and *searches* lists are empty.
                # This is OK, since we only need the *previous_actual_parts* list
                # which is popluated with valid *ActualPart*'s:
                previous_choice_part = ChoicePart.xml_parse(choice_part_tree)
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
        if tracing:
            # First sort *proposed_actual_parts* and *previous_actual_parts*:
            proposed_actual_parts.sort(key=lambda proposed_actual_part: proposed_actual_part.key)
            previous_actual_parts.sort(key=lambda previous_actual_part: previous_actual_part.key)

            # Compute the *maximum_actual_parts_size*:
            proposed_actual_parts_size = len(proposed_actual_parts)
            previous_actual_parts_size = len(previous_actual_parts)
            maximum_actual_parts_size = max(proposed_actual_parts_size, previous_actual_parts_size)
            print(f"{tracing}proposed_actual_parts_size={proposed_actual_parts_size}")
            print(f"{tracing}previous_actual_parts_size={previous_actual_parts_size}")
            print(f"{tracing}maximum_actual_parts_size={maximum_actual_parts_size}")

            # Now sweep across both *proposed_actual_parts* and *previous_actual_parts*
            # printing out the key values side by side:
            for index in range(maximum_actual_parts_size):
                proposed_text = ("--------" if index >= proposed_actual_parts_size
                                 else proposed_actual_parts[index].key)
                previous_text = ("--------" if index >= previous_actual_parts_size
                                 else previous_actual_parts[index].key)
                print(f"{tracing}Actual_Parts[{index}]:'{previous_text}'\t{proposed_text}")

        # We need to figure out when actual parts from the `.xml` are old (i.e. *stale*)
        # and refresh them.
        now = int(time.time())
        if tracing:
            print(f"{tracing}now={now} stale={stale} now-stale={now-stale}")

        # Now sweep through *proposed_actual_parts* and refresh any that are either missing or out
        # of date and construct the *final_actual_parts*:
        final_actual_parts = list()
        for index, proposed_actual_part in enumerate(proposed_actual_parts):
            # Grab the *proposed_actual_part_key*:
            proposed_actual_part_key = proposed_actual_part.key
            if tracing:
                print(f"{tracing}Proposed_Actual_Part[{index}]:'{proposed_actual_part.key}'")

            # Start by assuming that *lookup_required* and set to *False* if we can avoid
            # the lookup:
            lookup_required = True
            if proposed_actual_part_key in previous_actual_parts_table:
                if tracing:
                    print(f"{tracing}'{proposed_actual_part_key} is in previous_actual_parts_table")

                # We have a *previous_actual_part* that matches *proposed_actual_part*.
                # Now we see if can simply copy *previous_vendor_parts* over or
                # whether we must trigger a vendor parts lookup:
                previous_actual_part = previous_actual_parts_table[proposed_actual_part_key]
                previous_vendor_parts = previous_actual_part.vendor_parts
                if tracing:
                    print(f"{tracing}previous_actual_part.name="
                          f"'{previous_actual_part.manufacturer_part_name}'")
                    print(f"{tracing}len(previous_vendor_parts)={len(previous_vendor_parts)}")

                # Compute the *minimum_time_stamp* across all *previous_vendor_parts*:
                minimum_timestamp = now
                for previous_vendor_part in previous_vendor_parts:
                    minimum_timestamp = min(minimum_timestamp, previous_vendor_part.timestamp)
                if tracing:
                    print(f"{tracing}minimum_timestamp={minimum_timestamp}")

                # If the *minimum_time_stamp* is too stale, force a refresh:
                if minimum_timestamp + stale > now:
                    if tracing:
                        print(f"{tracing}Not stale")
                    proposed_actual_part.vendor_parts = previous_vendor_parts
                    lookup_required = False
            else:
                if tracing:
                    print(f"{tracing}'{proposed_actual_part_key} is not"
                          f" in previous_actual_parts_table")
            if tracing:
                print(f"{tracing}lookup_required={lookup_required}")

            # If *lookup_required*, visit each *Panda* object in *pandas* and look up
            # *VendorPart*'s.  Assemble them all in the *new_vendor_parts* list:
            if lookup_required:
                new_vendor_parts = list()
                for panda in pandas:
                    panda_vendor_parts = panda.vendor_parts_lookup(proposed_actual_part,
                                                                   part_name)
                    if trace_level:
                        trace("len(panda_vendor_parts)={len(panda_vendor_parts)}")
                    new_vendor_parts.extend(panda_vendor_parts)
                    if tracing:
                        panda_vendor_parts_size = len(panda_vendor_parts)
                        new_vendor_parts_size = len(new_vendor_parts)
                        print(f"{tracing}panda_vendor_parts_size={panda_vendor_parts_size}")
                        print(f"{tracing}new_vendor_parts_size={new_vendor_parts_size}")
                if len(new_vendor_parts) >= 0:
                    final_actual_parts.append(proposed_actual_part)
                xml_save_required = True
            else:
                final_actual_parts.append(proposed_actual_part)

        # Figure out if we need to write out *final_actual_parts* by figuring out
        # whether or not they match *previous_actual_parts*:
        previous_actual_parts_table = {previous_actual_part.key: previous_actual_part
                                       for previous_actual_part in previous_actual_parts}
        final_actual_parts_table = {final_actual_part.key: final_actual_part
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
    def xml_lines_append(self, xml_lines, indent):
        # Verify argument types:
        assert isinstance(xml_lines, list)
        assert isinstance(indent, str)

        # Grab some values from *choice_part* (i.e. *self*):
        choice_part = self
        actual_parts = choice_part.actual_parts
        name = choice_part.name

        # Output the `<ChoicePart ... >` tag:
        xml_lines.append(f'{indent}<ChoicePart name="{Encode.to_attribute(name)}">')

        # Output the `<ActualPart ... >` tags:
        next_indent = indent + " "
        for actual_part in actual_parts:
            actual_part.xml_lines_append(xml_lines, next_indent)

        # Output the closing `</ChoicePart>` tag:
        xml_lines.append(f'{indent}</ChoicePart>')

    # ChoicePart.xml_parse():
    @staticmethod
    def xml_parse(choice_part_tree):
        # Verify argument types:
        assert isinstance(choice_part_tree, etree._Element)

        # Create *choice_part* (most of the values are no longer used...):
        assert choice_part_tree.tag == "ChoicePart"
        attributes_table = choice_part_tree.attrib
        name = attributes_table["name"]
        choice_part = ChoicePart(name, [], [])

        # Read in the *actual_parts* from *choice_part_tree* and return the resulting *choice_part*:
        actual_parts = choice_part.actual_parts
        for actual_part_tree in list(choice_part_tree):
            actual_part = ActualPart.xml_parse(actual_part_tree)
            actual_parts.append(actual_part)
        return choice_part


# FractionalPart:
class FractionalPart(ProjectPart):
    # A *FractionalPart* specifies a part that is constructed by
    # using a portion of another *ProjectPart*.

    # FractionalPart.__init__():
    def __init__(self, name, kicad_footprint,
                 choice_part, numerator, denominator, description):
        """ *FractionalPart*: Initialize *self* to contain
            *name*, *kicad_footprint*, *choie_part*,
            *numerator*, *denomoniator*, and *description*. """

        # Verify argument types:
        assert isinstance(name, str)
        assert isinstance(kicad_footprint, str)
        assert isinstance(choice_part, ChoicePart)

        # Load up *self*:
        super().__init__(name, kicad_footprint)
        self.choice_part = choice_part
        self.numerator = numerator
        self.denominator = denominator
        self.description = description

    # FractionalPart.choice_parts():
    def choice_parts(self):
        """ *FractionalPart*: Return the *ChoicePart* objects associated
            with *self*.
        """

        choice_part = self.choice_part
        choice_part.fractional_parts.append(self)
        return [choice_part]

    # FractionalPart.footprints_check():
    def footprints_check(self, kicad_footprints):
        """ *FractionalPart*: Verify that all the footprints exist for the *FractionalPart* object
            (i.e. *self*.)
        """

        # Use *fractional_part* instead of *self*:
        fractional_part = self

        # Verify argument types:
        assert isinstance(kicad_footprints, dict)

        # Record *kicad_footprint* into *kicad_footprints*:
        kicad_footprint = fractional_part.kicad_footprint
        if kicad_footprint != "-":
            kicad_footprints[kicad_footprint] = fractional_part.name


# TablesEditor:
class TablesEditor(QMainWindow):

    # TablesEditor.__init__()
    @trace(1)
    def __init__(self, tables, collection_directories, searches_root, order, tracing=""):
        # Verify argument types:
        assert isinstance(tables, list)
        assert isinstance(collection_directories, list)
        assert isinstance(searches_root, str)
        assert isinstance(order, Order)
        for table in tables:
            assert isinstance(table, Table)

        # Create the *application* first.  The set attribute makes a bogus warning message
        # printout go away:
        QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
        application = QApplication(sys.argv)

        # Construct *ui_file_name*:
        module_file_name = __file__
        module_directory = os.path.split(module_file_name)[0]
        ui_file_name = os.path.join(module_directory, "bom_manager.ui")
        if tracing:
            print(f"{tracing}module_file_name='{module_file_name}'")
            print(f"{tracing}module_directory='{module_directory}'")
            print(f"{tracing}ui_file_name='{ui_file_name}'")

        # Create *main_window* from thie `.ui` file:
        # ui_qfile = QFile("bom_manager.ui")
        ui_qfile = QFile(ui_file_name)
        ui_qfile.open(QFile.ReadOnly)
        loader = QUiLoader()
        main_window = loader.load(ui_qfile)

        # ui_qfile = QFile(os.path.join(order_root, "test.ui"))
        # ui_qfile.open(QFile.ReadOnly)
        # loader.registerCustomWidget(CheckableComboBox)
        # search_window = loader.load(ui_qfile)

        # for table in tables:
        #    break
        #    for parameter in table.parameters:
        #        if parameter.type == "enumeration":
        #            name = parameter.name
        #            checkable_combo_box = getattr(search_window, name + "_combo_box")
        #            enumerations = parameter.enumerations
        #            for enumeration in enumerations:
        #                checkable_combo_box.addItem(enumeration.name)
        #                #checkable_combo_box.setCheckable(True)

        # For debugging:
        # for table in tables:
        #    break
        #    parameters = table.parameters
        #    for index, parameter in enumerate(parameters):
        #        name = parameter.name
        #        radio_button = getattr(search_window, name + "_radio_button")
        #        print("[{0}]: Radio Button '{1}' {2}".format(index, name, radio_button))
        #        check_box = getattr(search_window, name + "_check_box")
        #        print("[{0}]: Check Box '{1}' {2}".format(index, name, check_box))
        #        if parameter.type == "enumeration":
        #            line_edit = getattr(search_window, name + "_combo_box")
        #        else:
        #            line_edit = getattr(search_window, name + "_line_edit")
        #        print("[{0}]: Line Edit '{1}' {2}".format(index, name, line_edit))

        # Grab the file widgets from *main_window*:

        # file_line_edit = main_window.file_line_edit
        # file_new_button = main_window.file_new_button
        # file_open_button = main_window.file_open_button

        # Connect file widgets to their callback routines:
        # file_line_edit.textEdited.connect(
        #  partial(TablesEditor.file_line_edit_changed, tables_editor))
        # file_new_button.clicked.connect(
        #  partial(TablesEditor.file_new_button_clicked, tables_editor))
        # file_open_button.clicked.connect(
        #  partial(TablesEditor.file_open_button_clicked, tables_editor))

        # Get *working_directory_path*:
        working_directory_path = os.getcwd()
        assert isinstance(working_directory_path, str)
        assert os.path.isdir(working_directory_path)

        # Figure out *searches_root* and make sure it exists:
        if os.path.isdir(searches_root):
            # *searches_path* already exists:
            if tracing:
                print(f"{tracing}Using '{searches_root}' directory to store searches into.")
        else:
            # Create directory *searches_path*:
            if tracing:
                print(f"{tracing}Creating directory '{searches_root}' to store searches into...")
            try:
                os.mkdir(searches_root)
            except PermissionError:
                print(f"...failed to create `{searches_root}' directory.")
                searches_root = os.path.join(working_directory_path, "searches")
                print(f"Using '{searches_root}' for searches directory "
                      "(which is a really bad idea!!!!)")
        assert os.path.isdir(searches_root)

        # Create *collections_root*:
        # collections_root = os.path.join(working_directory_path, "collections")
        # assert os.path.isdir(collections_root)

        # Load all values into *tables_editor* before creating *combo_edit*.
        # The *ComboEdit* initializer needs to access *tables_editor.main_window*:
        current_table = tables[0] if len(tables) >= 1 else None
        tables_editor = self
        tables_editor.application = application
        tables_editor.collection_directories = collection_directories
        tables_editor.collections = None  # Filled in below
        tables_editor.current_comment = None
        tables_editor.current_enumeration = None
        tables_editor.current_model_index = None
        tables_editor.current_parameter = None
        tables_editor.current_search = None
        tables_editor.current_table = current_table
        tables_editor.current_tables = tables
        tables_editor.in_signal = True
        tables_editor.languages = ["English", "Spanish", "Chinese"]
        tables_editor.main_window = main_window
        tables_editor.order = order
        # tables_editor.original_tables = copy.deepcopy(tables)
        tables_editor.re_table = TablesEditor.re_table_get()
        tables_editor.searches_root = searches_root
        tables_editor.searches = list()
        tables_editor.xsearches = None
        tables_editor.tab_unload = None
        tables_editor.tables = tables
        # tables_editor.tracing_level = tracing_level
        # tables_editor.trace_signals = tracing_level >= 1

        # Set up *tables* first, followed by *parameters*, followed by *enumerations*:

        # Set up *tables_combo_edit* and stuff into *tables_editor*:
        new_item_function = partial(TablesEditor.table_new, tables_editor)
        current_item_set_function = partial(TablesEditor.current_table_set, tables_editor)
        comment_get_function = partial(TablesEditor.table_comment_get, tables_editor)
        comment_set_function = partial(TablesEditor.table_comment_set, tables_editor)
        is_active_function = partial(TablesEditor.table_is_active, tables_editor)
        tables_combo_edit = ComboEdit(
          "tables",
          tables_editor,
          tables,
          new_item_function,
          current_item_set_function,
          comment_get_function,
          comment_set_function,
          is_active_function,
          combo_box=main_window.tables_combo,
          comment_text=main_window.tables_comment_text,
          delete_button=main_window.tables_delete,
          first_button=main_window.tables_first,
          last_button=main_window.tables_last,
          line_edit=main_window.tables_line,
          next_button=main_window.tables_next,
          new_button=main_window.tables_new,
          previous_button=main_window.tables_previous,
          rename_button=main_window.tables_rename,
          )
        tables_editor.tables_combo_edit = tables_combo_edit

        # Set up *parameters_combo_edit* and stuff into *tables_editor*:
        parameters = list() if current_table is None else current_table.parameters
        new_item_function = partial(TablesEditor.parameter_new, tables_editor)
        current_item_set_function = partial(TablesEditor.current_parameter_set, tables_editor)
        comment_get_function = partial(TablesEditor.parameter_comment_get, tables_editor)
        comment_set_function = partial(TablesEditor.parameter_comment_set, tables_editor)
        is_active_function = partial(TablesEditor.parameter_is_active, tables_editor)
        parameters_combo_edit = ComboEdit(
          "parameters",
          tables_editor,
          parameters,
          new_item_function,
          current_item_set_function,
          comment_get_function,
          comment_set_function,
          is_active_function,
          combo_box=main_window.parameters_combo,
          comment_text=main_window.parameters_comment_text,
          delete_button=main_window.parameters_delete,
          first_button=main_window.parameters_first,
          last_button=main_window.parameters_last,
          line_edit=main_window.parameters_line,
          next_button=main_window.parameters_next,
          new_button=main_window.parameters_new,
          previous_button=main_window.parameters_previous,
          rename_button=main_window.parameters_rename,
          )
        tables_editor.parameters_combo_edit = parameters_combo_edit

        # Set up *enumerations_combo_edit* and stuff into *tables_editor*:
        enumerations = (
          list() if parameters is None or len(parameters) == 0 else parameters[0].enumerations)
        new_item_function = partial(TablesEditor.enumeration_new, tables_editor)
        current_item_set_function = partial(TablesEditor.current_enumeration_set, tables_editor)
        comment_get_function = partial(TablesEditor.enumeration_comment_get, tables_editor)
        comment_set_function = partial(TablesEditor.enumeration_comment_set, tables_editor)
        is_active_function = partial(TablesEditor.enumeration_is_active, tables_editor)
        enumerations_combo_edit = ComboEdit(
          "enumerations",
          tables_editor,
          enumerations,
          new_item_function,
          current_item_set_function,
          comment_get_function,
          comment_set_function,
          is_active_function,
          combo_box=main_window.enumerations_combo,
          comment_text=main_window.enumerations_comment_text,
          delete_button=main_window.enumerations_delete,
          first_button=main_window.enumerations_first,
          last_button=main_window.enumerations_last,
          line_edit=main_window.enumerations_line,
          next_button=main_window.enumerations_next,
          new_button=main_window.enumerations_new,
          previous_button=main_window.enumerations_previous,
          rename_button=main_window.enumerations_rename,
          )
        tables_editor.enumerations_combo_edit = enumerations_combo_edit

        # Now build the *searches_combo_edit* and stuff into *tables_editor*:
        searches = tables_editor.searches
        new_item_function = partial(TablesEditor.searches_new, tables_editor)
        current_item_set_function = partial(TablesEditor.current_search_set, tables_editor)
        comment_get_function = partial(TablesEditor.searches_comment_get, tables_editor)
        comment_set_function = partial(TablesEditor.searches_comment_set, tables_editor)
        is_active_function = partial(TablesEditor.searches_is_active, tables_editor)
        searches_combo_edit = ComboEdit(
          "searches",
          tables_editor,
          searches,
          new_item_function,
          current_item_set_function,
          comment_get_function,
          comment_set_function,
          is_active_function,
          combo_box=main_window.searches_combo,
          comment_text=main_window.searches_comment_text,
          delete_button=main_window.searches_delete,
          first_button=main_window.searches_first,
          last_button=main_window.searches_last,
          line_edit=main_window.searches_line,
          next_button=main_window.searches_next,
          new_button=main_window.searches_new,
          previous_button=main_window.searches_previous,
          rename_button=main_window.searches_rename,
          )
        tables_editor.searches = searches
        tables_editor.searches_combo_edit = searches_combo_edit

        # Perform some global signal connections to *main_window* (abbreviated as *mw*):
        mw = main_window
        mw.common_save_button.clicked.connect(tables_editor.save_button_clicked)
        mw.common_quit_button.clicked.connect(tables_editor.quit_button_clicked)
        mw.find_tabs.currentChanged.connect(tables_editor.tab_changed)
        mw.filters_down.clicked.connect(tables_editor.filters_down_button_clicked)
        mw.filters_up.clicked.connect(tables_editor.filters_up_button_clicked)
        mw.collections_check.clicked.connect(tables_editor.collections_check_clicked)
        mw.collections_process.clicked.connect(tables_editor.collections_process_clicked)
        mw.parameters_csv_line.textChanged.connect(tables_editor.parameter_csv_changed)
        mw.parameters_default_line.textChanged.connect(tables_editor.parameter_default_changed)
        mw.parameters_long_line.textChanged.connect(tables_editor.parameter_long_changed)
        mw.parameters_optional_check.clicked.connect(tables_editor.parameter_optional_clicked)
        mw.parameters_short_line.textChanged.connect(tables_editor.parameter_short_changed)
        mw.parameters_type_combo.currentTextChanged.connect(tables_editor.parameters_type_changed)
        mw.schema_tabs.currentChanged.connect(tables_editor.tab_changed)
        mw.searches_save.clicked.connect(tables_editor.searches_save_button_clicked)
        mw.searches_table_combo.currentTextChanged.connect(tables_editor.searches_table_changed)
        mw.root_tabs.currentChanged.connect(tables_editor.tab_changed)

        mw.collections_new.clicked.connect(tables_editor.collections_new_clicked)
        mw.collections_new.setEnabled(False)
        mw.collections_line.textChanged.connect(tables_editor.collections_line_changed)
        mw.collections_tree.clicked.connect(tables_editor.collections_tree_clicked)
        mw.collections_delete.clicked.connect(tables_editor.collections_delete_clicked)
        mw.collections_delete.setEnabled(False)

        # file_names = glob.glob("../digikey_tables/**", recursive=True)
        # file_names.sort()
        # print("file_names=", file_names)

        # Create the *tree_model* needed for *collections* and stuff into *tables_editor*:
        tree_model = TreeModel()
        tables_editor.model = tree_model

        # Create the *collections* and stuff into *tables_editor*:
        collections = Collections("Collections", collection_directories, searches_root, tree_model,
                                  )
        tables_editor.collections = collections

        # Now stuff *collections* into *tree_model*:
        tree_model.collections_set(collections)

        # Now that both *collections* and *tree_mode* refer to one another we can safely
        # call *partial_load*():
        collections.partial_load()

        # Now bind *tree_model* to the *collections_tree* widget:
        collections_tree = mw.collections_tree
        collections_tree.setModel(tree_model)
        collections_tree.setSortingEnabled(True)

        # FIXME: Used *tables_editor.current_update()* instead!!!
        current_table = None
        current_parameter = None
        current_enumeration = None
        if len(tables) >= 1:
            table = tables[0]
            parameters = table.parameters
            if len(parameters) >= 1:
                parameter = parameters[0]
                current_parameter = parameter
                enumerations = parameter.enumerations
                if len(enumerations) >= 1:
                    enumeration = enumerations[0]
                    current_enumeration = enumeration
            table.current_table = current_table
            table.current_parameter = current_parameter
            table.current_enumeration = current_enumeration

        # tables_editor.table_setup()

        # Read in `searches.xml` if it exists:
        # tables_editor.searches_file_load(os.path.join(order_root, "searches.xml"),
        #                                  )

        # Update the entire user interface:
        tables_editor.update()

        tables_editor.in_signal = False

    # TablesEditor.__str__():
    def __str__(self):
        return "TablesEditor"

    # TablesEditor.comment_text_set()
    def comment_text_set(self, new_text, tracing=""):
        # Verify argument types:
        assert isinstance(new_text, str)
        assert isinstance(tracing, str)

        # Carefully set thet text:
        tables_editor = self
        main_window = tables_editor.main_window
        comment_text = main_window.parameters_comment_text
        comment_text.setPlainText(new_text)

    # TablesEditor.collections_delete_changed():
    @trace(1)
    def collections_delete_clicked(self, tracing=""):
        assert isinstance(tracing, str)
        # Perform any requested signal *tracing* for *tables_editor* (i.e. *self*):
        tables_editor = self

        # Grab the *current_model_index* from *tables_editor* and process it if it exists:
        current_model_index = tables_editor.current_model_index
        if current_model_index is None:
            # It should be impossible to get here, since the [Delete] button should be disabled
            # if there is no *current_model_index*:
            print("No node selected.")
        else:
            # Grab current *tree_model* and *node* associated with *current_model_index*:
            tree_model = current_model_index.model()
            assert isinstance(tree_model, TreeModel)
            node = tree_model.getNode(current_model_index)
            assert isinstance(node, Node)

            # Make sure *node* is a *Search* *Node*:
            if isinstance(node, Search):
                # Rename *node* and *current_model_index* to *current_search* and
                # *search_model_index* to be more descriptive variable names:
                current_search = node
                search_model_index = current_model_index
                current_search_name = current_search.name
                if tracing:
                    print(f"{tracing}curent_search_name='{current_search_name}'")

                # Grab the parent *table* from *current_search* and force it to be fixed up:
                table = current_search.parent
                assert isinstance(table, Table)
                table.sort()

                # Only attempt to delete *current_search* if it is in *searches* of *table*:
                searches = table.children_get()
                if current_search in searches:
                    # Sweep through *searches* to get the *search_index* needed to obtain
                    # *search_parent_model_index* needed to move the selection later on:
                    search_parent = current_search.search_parent
                    find_index = -1
                    for search_index, search in enumerate(searches):
                        search_name = search.name
                        print(f"{tracing}Sub_Search[{search_index}]: '{search_name}'")
                        if search is search_parent:
                            find_index = search_index
                            break
                    assert find_index >= 0
                    parent_search_model_index = search_model_index.siblingAtRow(find_index)

                    # Delete the *search* associated with *search_model_index* from *tree_model*:
                    if tracing:
                        print(f"{tracing}Here 1")
                    tree_model.delete(search_model_index)
                    collection = current_search.collection
                    searches_table = collection.searches_table
                    if current_search_name in searches_table:
                        del searches_table[current_search_name]

                    # If a *parent_search* as found, set it up as the next selected one:
                    if tracing:
                        print(f"{tracing}Here 2")
                    if search_parent is None:
                        tables_editor.current_model_index = None
                        tables_editor.current_search = None
                    else:
                        if tracing:
                            print(f"Here 3")
                        search_parent_name = search_parent.name
                        if tracing:
                            print(f"{tracing}Parent is '{search_parent_name}'")
                        main_window = tables_editor.main_window
                        collections_tree = main_window.collections_tree
                        selection_model = collections_tree.selectionModel()
                        collections_line = main_window.collections_line
                        collections_line.setText(search_parent_name)
                        flags = (QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)
                        selection_model.setCurrentIndex(parent_search_model_index, flags)
                        tables_editor.current_model_index = parent_search_model_index
                        tables_editor.current_search = search_parent

                    # Remove the associated files `.xml` and `.csv` files (if they exist):
                    if tracing:
                        print(f"Here 4")
                    collection = current_search.collection
                    searches_root = collection.searches_root
                    relative_path = current_search.relative_path
                    csv_file_name = os.path.join(searches_root, relative_path + ".csv")
                    xml_file_name = os.path.join(searches_root, relative_path + ".xml")

                    # Remove the offending files:
                    if os.path.isfile(xml_file_name):
                        os.remove(xml_file_name)
                    if os.path.isfile(csv_file_name):
                        os.remove(csv_file_name)

                    # Force the *table* to be resorted:
                    table.sort()
            else:
                print("Non-search node '{0}' selected???".format(node.name))

        # Update the collections tab:
        tables_editor.update()

    # TablesEditor.collections_line_changed():
    @trace(1)
    def collections_line_changed(self, text, tracing=""):
        # Verify argument types:
        assert isinstance(text, str)
        assert isinstance(tracing, str)

        # Make sure that *tables_editor* (i.e. *self*) is updated:
        tables_editor = self
        tables_editor.update()

    # TablesEditor.collections_new_clicked():
    @trace(1)
    def collections_new_clicked(self, tracing=""):
        # Perform any requested *tracing*:
        tables_editor = self
        # Grab some values from *tables_editor* (i.e. *self*):
        current_search = tables_editor.current_search

        # Make sure *current_search* exists (this button click should be disabled if not available):
        assert current_search is not None

        # clip_board = pyperclip.paste()
        # selection = os.popen("xsel").read()
        application = tables_editor.application
        application_clipboard = application.clipboard()
        selection = application_clipboard.text(QClipboard.Selection)
        clipboard = application_clipboard.text(QClipboard.Clipboard)

        url = None
        if selection.startswith("http"):
            url = selection
        elif clipboard.startswith("http"):
            url = clipboard
        if tracing:
            print(f"{tracing}clipbboard='{clipboard}'")
            print(f"{tracing}selection='{selection}'")
            print(f"{tracing}url='{url}'")

        # Process *url* (if it is valid):
        if url is None:
            print("URL: No valid URL found!")
        else:
            # Grab some stuff from *tables_editor*:
            main_window = tables_editor.main_window
            collections_line = main_window.collections_line
            new_search_name = collections_line.text().strip()

            # Grab some values from *current_search*:
            table = current_search.parent
            assert isinstance(table, Table)

            # Construct *new_search_name*:
            new_search = Search(new_search_name, table, current_search, url)
            assert table.has_child(new_search)

            # if tracing:
            #    print("{0}1:len(searches)={1}".format(tracing, len(searches)))
            table.sort()
            new_search.file_save()

            model_index = tables_editor.current_model_index
            if model_index is not None:
                parent_model_index = model_index.parent()
                tree_model = model_index.model()
                tree_model.children_update(parent_model_index)

            # model = tables_editor.model
            # model.insertNodes(0, [ new_search ], parent_model_index)
            # if tracing:
            #    print("{0}2:len(searches)={1}".format(tracing, len(searches)))

            tables_editor.update()

    # TablesEditor.collections_check_clicked():
    @trace(1)
    def collections_check_clicked(self, tracing=""):
        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self

        # Delegate checking to *order* object:
        collections = tables_editor.collections
        order = tables_editor.order
        order.check(collections)

    # TablesEditor.collections_process_clicked():
    @trace(1)
    def collections_process_clicked(self, tracing=""):
        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self

        # Grab some values from *tables_editor*:
        collections = tables_editor.collections
        order = tables_editor.order

        # Now process *order* using *collections*:
        order.process(collections)

    # TablesEditor.collections_tree_clicked():
    @trace(1)
    def collections_tree_clicked(self, model_index, tracing=""):
        # Verify argument types:
        assert isinstance(model_index, QModelIndex)
        assert isinstance(tracing, str)

        # Stuff *model_index* into *tables_editor* (i.e. *self*):
        tables_editor = self
        tables_editor.current_model_index = model_index

        # If *tracing*, show the *row* and *column*:
        if tracing:
            row = model_index.row()
            column = model_index.column()
            print(f"{tracing}row={row} column={column}")

        # Now grab the associated *node* from *model_index*:
        model = model_index.model()
        node = model.getNode(model_index)
        assert isinstance(node, Node)

        # Let the *node* know it has been clicked:
        node.clicked(tables_editor, model_index)

        # *Search* *node*'s get some additional treatment:
        if isinstance(node, Search):
            main_window = tables_editor.main_window
            collections_line = main_window.collections_line
            collections_line.setText(node.name)

        # Lastly, tell *tables_editor* to update the GUI:
        tables_editor.update()

    # TablesEditor.collections_update():
    @trace(1)
    def collections_update(self, tracing=""):
        # Perform argument testing:
        assert isinstance(tracing, str)

        # Grab some widgets from *tables_editor*:
        tables_editor = self
        main_window = tables_editor.main_window
        collections_delete = main_window.collections_delete
        collections_line = main_window.collections_line
        collections_new = main_window.collections_new

        # Grab the *current_search* object:
        current_search = tables_editor.current_search
        if tracing:
            current_search_name = "None" if current_search is None else f"'{current_search.name}'"
            print(f"{tracing}current_search={current_search_name}")

        # Grab the *search_tile* from the *collections_line* widget*:
        search_title = collections_line.text()

        # We can only create a search if:
        # * the search *search_title* not empty,
        # * the search *search_title* is not named "@ALL",
        # * there is a preexisting *current_search* to depend upon
        # * the *search_title* is not a duplicate:
        new_button_enable = False
        new_button_why = "Default off"
        if search_title == "":
            # Empty search names are not acceptable:
            new_button_enable = False
            new_button_why = "Empty Search name"
        elif search_title == "@ALL":
            # '@ALL' is not allowed:
            new_button_enable = False
            new_button_why = "@ALL is reserved"
        elif current_search is None:
            # We really need to have a *current_search* selected to add as a dependency:
            new_button_enable = False
            new_button_why = "No search seleted"
        else:
            # Search *table* for a match of *search_title*:
            table = current_search.parent
            assert isinstance(table, Table)
            collection = table.collection
            assert isinstance(collection, Collection)
            searches_table = collection.searches_table
            if search_title in searches_table:
                # We already have a *search* named *search_title*:
                new_button_enable = False
                new_button_why = "Search already exists"
            else:
                # Nothing matched, so this must be a new and unique search name:
                new_button_enable = True
                new_button_why = "Unique Name"

        # Enable/disable the *collections_new* button widget:
        collections_new.setEnabled(new_button_enable)
        if tracing:
            print(f"{tracing}new_button_enable={new_button_enable} why='{new_button_why}'")

        # We can only delete a search that exists and has no other sub searches that depend on it:
        delete_button_enable = False
        delete_button_why = "Default Off"
        if current_search is None:
            delete_button_enable = False
            delete_button_why = "Default Off"
        elif current_search.name == "@ALL":
            delete_button_enable = False
            delete_button_why = "Can not delete @All"
        elif current_search.is_deletable():
            delete_button_enable = True
            delete_button_why = "No sub-search dependencies"
        else:
            delete_button_enable = False
            delete_button_why = "Sub-search_dependencies"

        # Enable/disable *delete_button_enable* button widget:
        collections_delete.setEnabled(delete_button_enable)
        if tracing:
            print(f"{tracing}delete_button_enable={delete_button_enable} why='{delete_button_why}'")

    # TablesEditor.current_enumeration_set()
    def current_enumeration_set(self, enumeration, tracing=""):
        # Verify argument types:
        assert isinstance(enumeration, Enumeration) or enumeration is None, \
          "{0}".format(enumeration)
        assert isinstance(tracing, str)

        # Only do something if we are not in a signal:
        tables_editor = self
        if not tables_editor.in_signal:
            tables_editor.in_signal = True

            # Perform any tracing requested signal tracing:
            trace_signals = tables_editor.trace_signals
            if trace_signals:
                print("=>TablesEditor.current_enumeration_set('{0}')".
                      format("None" if enumeration is None else enumeration.name))

            # Finally, set the *current_enumeration*:
            tables_editor.current_enumeration = enumeration

            # Wrap up any requested tracing:
            if trace_signals:
                print("<=TablesEditor.current_enumeration_set('{0}')\n".
                      format("None" if enumeration is None else enumeration.name))
            tables_editor.in_signal = False

    # TablesEditor.current_parameter_set()
    def current_parameter_set(self, parameter, tracing=""):
        # Verify argument types:
        assert isinstance(parameter, Parameter) or parameter is None
        assert isinstance(tracing, str)

        # Perform any requested *tracing*:
        if tracing:
            name = "None" if parameter is None else parameter.name
            print("{0}=>TablesEditor.current_parameter_set(*, '{1}')".format(tracing, name))

        # Set the *current_parameter* in *tables_editor*:
        tables_editor = self
        tables_editor.current_parameter = parameter

    # TablesEditor.current_search_set()
    def current_search_set(self, new_current_search, tracing=""):
        # Verify argument types:
        assert isinstance(new_current_search, Search) or new_current_search is None, \
          print(new_current_search)
        assert isinstance(tracing, str)

        # Make sure *new_current_search* is in *searches*:
        tables_editor = self
        searches = tables_editor.searches
        if new_current_search is not None:
            for search_index, search in enumerate(searches):
                assert isinstance(search, Search)
                if tracing:
                    print("{0}Search[{1}]: '{2}'".format(tracing, search_index, search.name))
                if search is new_current_search:
                    break
            else:
                assert False
        tables_editor.current_search = new_current_search

    # TablesEditor.current_table_set()
    def current_table_set(self, new_current_table, tracing=""):
        # Verify argument types:
        assert isinstance(new_current_table, Table) or new_current_table is None
        assert isinstance(tracing, str)

        # Stuff *new_current_table* into *tables_editor*:
        tables_editor = self
        if new_current_table is not None:
            tables = tables_editor.tables
            for table in tables:
                if table is new_current_table:
                    break
            else:
                assert False, "table '{0}' not in tables list".format(new_current_table.name)
        tables_editor.current_table = new_current_table


    # TablesEditor.current_update()
    def current_update(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Make sure *current_table* is valid (or *None*):
        tables_editor = self
        tables = tables_editor.tables
        tables_size = len(tables)
        current_table = None
        if tables_size >= 1:
            # Figure out if *current_table* is in *tables):
            current_table = tables_editor.current_table
            if current_table is not None:
                for table_index, table in enumerate(tables):
                    # print("Table[{0}]: '{1}'".format(table_index, table.name))
                    assert isinstance(table, Table)
                    if table is current_table:
                        break
                else:
                    # *current_table* points to a *Table* object that is not in *tables* and
                    # is invalid:
                    current_table = None
        if current_table is None and tables_size >= 1:
            current_table = tables[0]
        tables_editor.current_table = current_table
        if tracing:
            print("{0}current_table='{1}'".
                  format(tracing, "None" if current_table is None else current_table.name))

        # Make sure *current_parameter* is valid (or *None*):
        current_parameter = None
        if current_table is None:
            parameters = list()
        else:
            parameters = current_table.parameters
            parameters_size = len(parameters)
            if parameters_size >= 1:
                current_parameter = tables_editor.current_parameter
                if current_parameter is not None:
                    for parameter in parameters:
                        assert isinstance(parameter, Parameter)
                        if parameter is current_parameter:
                            break
                    else:
                        # *current_parameter* is invalid:
                        current_parameter = None
            if current_parameter is None and parameters_size >= 1:
                current_parameter = parameters[0]
        tables_editor.current_parameter = current_parameter
        if tracing:
            print("{0}current_parameter='{1}'".
                  format(tracing, "None" if current_parameter is None else current_parameter.name))

        # Update *parameters* in *parameters_combo_edit*:
        parameters_combo_edit = tables_editor.parameters_combo_edit
        parameters_combo_edit.items_replace(parameters)

        # Make sure *current_enumeration* is valid (or *None*):
        current_enumeration = None
        if current_parameter is None:
            enumerations = list()
        else:
            enumerations = current_parameter.enumerations
            enumerations_size = len(enumerations)
            if enumerations_size >= 1:
                current_enumeration = tables_editor.current_enumeration
                if current_enumeration is not None:
                    for enumeration in enumerations:
                        assert isinstance(enumeration, Enumeration)
                        if enumeration is current_enumeration:
                            break
                    else:
                        # *current_enumeration* is invalid:
                        current_enumeration = None
                if current_enumeration is None and enumerations_size >= 1:
                    current_enumeration = enumerations[0]
        tables_editor.current_enumeration = current_enumeration

        # Make sure that *current_search* is valid (or *None*):
        # tables_editor.current_search = current_search

        if tracing:
            print("{0}current_enumeration'{1}'".format(
              tracing, "None" if current_enumeration is None else current_enumeration.name))

        # Update *enumerations* into *enumerations_combo_edit*:
        enumerations_combo_edit = tables_editor.enumerations_combo_edit
        enumerations_combo_edit.items_replace(enumerations)

        # Make sure that *current_search* is valid (or *None*):
        searches = tables_editor.searches
        current_search = tables_editor.current_search
        if current_search is None:
            if len(searches) >= 1:
                current_search = searches[0]
        else:
            for search_index, search in enumerate(searches):
                if search is current_search:
                    break
            else:
                # *current_search* is not in *searches* and must be invalid:
                current_search = None
        tables_editor.current_search = current_search
        if tracing:
            print("{0}current_search='{1}'".
                  format(tracing, "None" if current_search is None else current_search.name))

    # TablesEditor.data_update()
    def data_update(self, tracing=""):
        # Verify artument types:
        assert isinstance(tracing, str)

        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self

        # Make sure that the *current_table*, *current_parameter*, and *current_enumeration*
        # in *tables_editor* are valid:
        tables_editor.current_update()

    # TablesEditor.enumeration_changed()
    def enumeration_changed(self):
        assert False

    # TablesEditor.enumeration_comment_get()
    def enumeration_comment_get(self, enumeration, tracing=""):
        # Verify argument types:
        assert isinstance(enumeration, Enumeration) or enumeration is None
        assert isinstance(tracing, str)

        # Perform any requested *tracing*:
        # tables_editor = self

        # Extract the comment *text* associated with *enumeration*:
        position = 0
        text = ""
        if enumeration is not None:
            comments = enumeration.comments
            assert len(comments) >= 1
            comment = comments[0]
            assert isinstance(comment, EnumerationComment)
            text = '\n'.join(comment.lines)
            position = comment.position

        return text, position

    # TablesEditor.enumeration_comment_set()
    def enumeration_comment_set(self, enumeration, text, position, tracing=""):
        # Verify argument types:
        assert isinstance(enumeration, Enumeration) or enumeration is None
        assert isinstance(text, str)
        assert isinstance(position, int)
        assert isinstance(tracing, str)

        # Perform any requested *tracing*:
        # tables_editor = self

        # Stuff *text* into *enumeration*:
        if enumeration is not None:
            comments = enumeration.comments
            assert len(comments) >= 1
            comment = comments[0]
            assert isinstance(comment, EnumerationComment)
            comment.lines = text.split('\n')
            comment.position = position

    # TablesEditor.enumeration_is_active():
    def enumeration_is_active(self):
        tables_editor = self
        tables_editor.current_update()
        current_parameter = tables_editor.current_parameter
        return current_parameter is not None and current_parameter.type == "enumeration"

    # TablesEditor.enumeration_new()
    def enumeration_new(self, name):
        # Verify argument types:
        assert isinstance(name, str)

        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self
        trace_level = tables_editor.trace_level
        if trace_level >= 1:
            print("=>TablesEditor.enumeration_new('{0}')".format(name))

        # Create *new_parameter* named *name*:
        comments = [EnumerationComment(language="EN", lines=list())]
        new_enumeration = Enumeration(name=name, comments=comments)

        # Wrap up any requested tracing and return *new_parameter*:
        if trace_level >= 1:
            print("<=TablesEditor.enumeration_new('{0}')=>'{1}'".format(new_enumeration.name))
        return new_enumeration

    # TablesEditor.enumerations_update()
    def enumerations_update(self, enumeration=None, tracing=""):
        # Verify argument types:
        assert isinstance(enumeration, Enumeration) or enumeration is None
        assert isinstance(tracing, str)

        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self

        # Make sure that the *current_table*, *current_parameter*, and *current_enumeration*
        # in *tables_editor* are valid:
        tables_editor.current_update()

        # Grab some widgets from *main_window*:
        main_window = tables_editor.main_window
        table_name = main_window.enumerations_table_name
        parameter_name = main_window.enumerations_parameter_name
        combo = main_window.enumerations_combo

        # Upbdate the *table_name* and *parameter_name* widgets:
        current_table = tables_editor.current_table
        table_name.setText("" if current_table is None else current_table.name)
        current_parameter = tables_editor.current_parameter
        parameter_name.setText("" if current_parameter is None else current_parameter.name)

        # Empty out *enumeration_combo* widgit:
        main_window = tables_editor.main_window
        while combo.count() > 0:
            combo.removeItem(0)

        # Grab *enumerations* from *current_parameter* (if possible):
        if current_parameter is not None and current_parameter.type.lower() == "enumeration":
            enumerations = current_parameter.enumerations

            # Now fill in *enumerations_combo_box* from *enumerations*:
            for index, enumeration in enumerate(enumerations):
                enumeration_name = enumeration.name
                if tracing:
                    print("{0}[{1}]'{2}'".format(tracing, index, enumeration.name))
                # print("[{0}]'{1}'".format(index, enumeration_name))
                combo.addItem(enumeration_name)

        # Update the *enumerations_combo_edit*:
        tables_editor.enumerations_combo_edit.gui_update()

    # TablesEditor.filters_cell_clicked():
    def filters_cell_clicked(self, row, column):
        # Verify argument types:
        assert isinstance(row, int)
        assert isinstance(column, int)

        # Perform any requested signal tracing:
        tables_editor = self

        # Just update the filters tab:
        tables_editor.filters_update()

    # TablesEditor.filters_down_button_clicked():
    def filters_down_button_clicked(self):
        tables_editor = self
        trace_signals = tables_editor.trace_signals

        # Note: The code here is very similar to the code in
        # *TablesEditor.filters_down_button_clicked*:

        # Grab some values from *tables_editor*:
        tables_editor.current_update()
        main_window = tables_editor.main_window
        filters_table = main_window.filters_table
        current_search = tables_editor.current_search

        # If there is no *current_search* there is nothing to be done:
        if current_search is not None:
            # We have a valid *current_search*, so grab *filters* and *current_row*:
            filters = current_search.filters
            current_row_index = filters_table.currentRow()

            # Dispactch on *current_row*:
            last_row_index = max(0, filters_table.rowCount() - 1)
            if current_row_index < 0:
                # No *current_row* is selected, so select the last row:
                filters_table.setCurrentCell(last_row_index, 0, QItemSelectionModel.SelectCurrent)
            else:
                # We can only move a filter up if it is not the last one:
                if current_row_index < last_row_index:
                    # Save all the stuff we care about from *filters_table* back into *filters*:
                    tables_editor.filters_unload()

                    # Swap *filter_at* with *filter_before*:
                    filter_after = filters[current_row_index + 1]
                    filter_at = filters[current_row_index]
                    filters[current_row_index + 1] = filter_at
                    filters[current_row_index] = filter_after

                    # Force the *filters_table* to be updated:
                    tables_editor.filters_update()
                    filters_table.setCurrentCell(current_row_index + 1, 0,
                                                 QItemSelectionModel.SelectCurrent)

    # TablesEditor.filters_unload()
    def filters_unload(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        tables_editor = self
        tables_editor.current_update()
        current_search = tables_editor.current_search
        if current_search is not None:
            filters = current_search.filters
            for filter in filters:
                use_item = filter.use_item
                use = False
                if use_item is not None:
                    check_state = use_item.checkState()
                    if check_state == Qt.CheckState.Checked:
                        use = True
                filter.use = use

                select = ""
                select_item = filter.select_item
                if select_item is not None:
                    select = select_item.text()
                filter.select = select

    # TablesEditor.filters_up_button_clicked():
    def filters_up_button_clicked(self):
        # Perform any requested signal tracing:
        tables_editor = self
        trace_signals = tables_editor.trace_signals

        # Note: The code here is very similar to the code in
        # *TablesEditor.filters_down_button_clicked*:

        # Grab some values from *tables_editor*:
        tables_editor.current_update()
        main_window = tables_editor.main_window
        filters_table = main_window.filters_table
        current_search = tables_editor.current_search

        # If there is no *current_search* there is nothing to be done:
        if current_search is not None:
            # We have a valid *current_search*, so grab *filters* and *current_row*:
            filters = current_search.filters
            current_row_index = filters_table.currentRow()
            # if trace_signals:
            #    print(" filters_before={0}".format([filter.parameter.name for filter in filters]))

            # Dispactch on *current_row_index*:
            if current_row_index < 0:
                # No *current_row_index* is selected, so select the first row:
                filters_table.setCurrentCell(0, 0, QItemSelectionModel.SelectCurrent)
            else:
                # We can only move a filter up if it is not the first one:
                if current_row_index >= 1:
                    # Save all the stuff we care about from *filters_table* back into *filters*:
                    tables_editor.filters_unload()

                    # Swap *filter_at* with *filter_before*:
                    filter_before = filters[current_row_index - 1]
                    filter_at = filters[current_row_index]
                    filters[current_row_index - 1] = filter_at
                    filters[current_row_index] = filter_before

                    # Force the *filters_table* to be updated:
                    tables_editor.filters_update()
                    filters_table.setCurrentCell(current_row_index - 1, 0,
                                                 QItemSelectionModel.SelectCurrent)

            # if trace_signals:
            #    print(" filters_after={0}".format([filter.parameter.name for filter in filters]))

    # TablesEditor.filters_update()
    def filters_update(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Empty out *filters_table* widget:
        tables_editor = self
        main_window = tables_editor.main_window
        filters_table = main_window.filters_table
        filters_table.clearContents()
        filters_table.setColumnCount(4)
        filters_table.setHorizontalHeaderLabels(["Parameter", "Type", "Use", "Select"])

        # Only fill in *filters_table* if there is a valid *current_search*:
        tables_editor.current_update()
        current_search = tables_editor.current_search
        if current_search is None:
            # No *current_search* so there is nothing to show:
            filters_table.setRowCount(0)
        else:
            # Let's update the *filters* and load them into the *filters_table* widget:
            # current_search.filters_update(tables_editor)
            filters = current_search.filters
            filters_size = len(filters)
            filters_table.setRowCount(filters_size)
            if tracing:
                print("{0}current_search='{1}' filters_size={2}".
                      format(tracing, current_search.name, filters_size))

            # Fill in one *filter* at a time:
            for filter_index, filter in enumerate(filters):
                # Create the header label in the first column:
                parameter = filter.parameter
                # if tracing:
                #    print("{0}[{1}]: '{2}'".format(tracing, filter_index, parameter_name))
                parameter_comments = parameter.comments
                assert len(parameter_comments) >= 1
                parameter_comment = parameter_comments[0]
                assert isinstance(parameter_comment, ParameterComment)

                # Figure out what *heading* to use:
                parameter_name = parameter.name
                short_heading = parameter_comment.short_heading
                long_heading = parameter_comment.long_heading
                heading = short_heading
                if heading is None:
                    heading = long_heading
                if heading is None:
                    heading = parameter_name
                # if tracing:
                #    print("{0}[{1}]: sh='{2}' lh='{3}' pn='{4}".format(
                #      tracing, filter_index, short_heading, long_heading, parameter_name))

                # Stuff the *heading* into the first column:
                header_item = QTableWidgetItem(heading)
                filter.header_item = header_item
                filters_table.setItem(filter_index, 0, filter.header_item)

                # Stuff the *type* into the second column:
                type = parameter.type
                type_item = QTableWidgetItem(type)
                filters_table.setItem(filter_index, 1, type_item)

                use = filter.use
                use_item = QTableWidgetItem("")
                filter.use_item = use_item
                use_item.setData(Qt.UserRole, filter)
                # print(type(use_item))
                # print(use_item.__class__.__bases__)
                flags = use_item.flags()
                use_item.setFlags(flags | Qt.ItemIsUserCheckable)
                check_state = Qt.CheckState.Checked if use else Qt.CheckState.Unchecked
                use_item.setCheckState(check_state)
                filters_table.setItem(filter_index, 2, use_item)

                select_item = QTableWidgetItem(filter.select)
                filter.select_item = select_item
                select_item.setData(Qt.UserRole, filter)
                filters_table.setItem(filter_index, 3, select_item)

            # if current_row_index >= 0 and current_row_index < filters_size:
            #    #filters_table.setCurrentCell(current_row_index, 0)
            #    filters_down.setEnabled(True)
            #    filters_up.setEnabled(True)
            # else:
            #    #filters_table.setCurrentCell(-1, -1)
            #    filters_down.setEnabled(False)
            #    filters_up.setEnabled(False)

        # Remember to unload the filters before changing from the [Filters] tab:
        tables_editor.tab_unload = TablesEditor.filters_unload

    # TablesEditor.filter_use_clicked()
    def filter_use_clicked(self, use_item, filter, row, column):
        # Verify argument types:
        assert isinstance(use_item, QTableWidgetItem)
        assert isinstance(filter, Filter)
        assert isinstance(row, int)
        assert isinstance(column, int)

        # FIXME: This routine probably no longer used!!!

        # Do nothing if we are already in a signal:
        tables_editor = self
        if not tables_editor.in_signal:
            tables_editor.in_signal = True

            # Perform an requested signal tracing:
            trace_signals = tables_editor.trace_signals
            if trace_signals:
                print("=>TablesEditor.filter_use_clicked(*, '{0}', {1}, {2})".
                      format(filter.parameter.name, row, column))

            check_state = use_item.checkState()
            print("check-state=", check_state)
            if check_state == Qt.CheckState.Checked:
                result = "checked"
                filter.use = True
            elif check_state == Qt.CheckState.Unchecked:
                result = "unchecked"
                filter.use = False
            elif check_state == Qt.CheckState.PartiallyChecked:
                result = "partially checked"
            else:
                result = "unknown"
            print("filter.name='{0}' filter.use={1}".format(filter.parameter.name, filter.use))

            # Wrap up any signal tracing:
            if trace_signals:
                print("parameter check state={0}".format(result))
                print("<=TablesEditor.filter_use_clicked(*, '{0}', {1}, {2})\n".
                      format(filter.parameter.name, row, column))
            tables_editor.in_signal = False

    # TablesEditor.find_update():
    def find_update(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        tables_editor = self
        main_window = tables_editor.main_window
        find_tabs = main_window.find_tabs
        find_tabs_index = find_tabs.currentIndex()
        if find_tabs_index == 0:
            tables_editor.searches_update()
        elif find_tabs_index == 1:
            tables_editor.filters_update()
        elif find_tabs_index == 2:
            tables_editor.results_update()
        else:
            assert False

    # TablesEditor.import_bind_clicked():
    def import_bind_button_clicked(self):
        # Perform any requested signal tracing:
        tables_editor = self
        trace_signals = tables_editor.trace_signals

        # Update *current_table* an *parameters* from *tables_editor*:
        tables_editor.current_update()
        current_table = tables_editor.current_table
        if current_table is not None:
            parameters = current_table.parameters
            headers = tables_editor.import_headers
            column_triples = tables_editor.import_column_triples
            for column_index, triples in enumerate(column_triples):
                header = headers[column_index]
                if len(triples) >= 1:
                    triple = triples[0]
                    count, name, value = triple
                    for parameter_index, parameter in enumerate(parameters):
                        if parameter.csv == name:
                            break
                    else:
                        scrunched_name = \
                          "".join([character for character in header if character.isalnum()])
                        comments = [ParameterComment(language="EN",
                                    long_heading=scrunched_name, lines=list())]
                        parameter = Parameter(name=scrunched_name, type=name, csv=header,
                                              csv_index=column_index, comments=comments)
                        parameters.append(parameter)

            tables_editor.update()

    # TablesEditor.import_file_line_changed():
    def import_csv_file_line_changed(self, text):
        # Verify argument types:
        assert isinstance(text, str)

        tables_editor = self
        in_signal = tables_editor.in_signal
        if not in_signal:
            tables_editor.in_signal = True

            # Perform any requested signal tracing:
            trace_signals = tables_editor.trace_signals
            if trace_signals:
                print("=>TablesEditor.import_csv_file_line_changed('{0}')".format(text))

            # Make sure *current_table* is up-to-date:
            # tables_editor.current_update()
            # current_table = tables_editor.current_table

            # Read *csv_file_name* out of the *import_csv_file_line* widget and stuff into *table*:
            # if current_table is not None:
            #     main_window = tables_editor.main_window
            #     import_csv_file_line = main_window.import_csv_file_line
            #     xxx = import_csv_file_line.text()
            #     print("xxx='{0}' text='{1}'".format(xxx, text))
            #    current_table.csv_file_name = csv_file_name

            # Force an update:
            # tables_editor.update()

            # Wrap up any requested signal tracing:
            if trace_signals:
                print("<=TablesEditor.import_csv_file_line_changed('{0}')\n".format(text))
            tables_editor.in_signal = False

    # TablesEditor.parameter_default_changed():
    def parameter_csv_changed(self, new_csv):
        # Verify argument types:
        assert isinstance(new_csv, str)

        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self
        in_signal = tables_editor.in_signal
        if not in_signal:
            tables_editor.in_signal = True

            # Perform any requested *tracing*:
            trace_signals = tables_editor.trace_signals

            # Stuff *new_csv* into *current_parameter* (if possible):
            tables_editor.current_parameter()
            current_parameter = tables_editor.current_parameter
            if current_parameter is not None:
                current_parameter.csv = new_csv

            tables_editor.update()
            # Wrap up any requested signal tracing:
            if trace_signals:
                print("=>TablesEditor.parameter_csv_changed('{0}')\n".format(new_csv))
                tables_editor.in_signal = False

    # TablesEditor.parameter_default_changed():
    def parameter_default_changed(self, new_default):
        # Verify argument types:
        assert isinstance(new_default, str)

        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self
        trace_level = tables_editor.trace_level
        trace_level = 1
        if trace_level >= 1:
            print("=>TablesEditor.parameter_default_changed('{0}')".format(new_default))

        # Stuff *new_default* into *current_parameter* (if possible):
        current_parameter = tables_editor.current_parameter
        if current_parameter is not None:
            current_parameter.default = new_default

        # Wrap up any requested tracing:
        if trace_level >= 1:
            print("<=TablesEditor.parameter_default_changed('{0}')\n".format(new_default))

    # TablesEditor.parameter_comment_get():
    def parameter_comment_get(self, parameter, tracing=""):
        # Verify argument types:
        assert isinstance(parameter, Parameter) or parameter is None
        assert isinstance(tracing, str)

        # Perform any requested *tracing*:
        text = ""

        # Grab the comment *text* from *parameter*:
        position = 0
        text = ""
        if parameter is not None:
            comments = parameter.comments
            assert len(comments) >= 1
            comment = comments[0]
            assert isinstance(comment, ParameterComment)
            text = '\n'.join(comment.lines)
            position = comment.position

        # Return *text* and *position*:
        return text, position

    # TablesEditor.parameter_comment_set():
    def parameter_comment_set(self, parameter, text, position, tracing=""):
        # Verify argument types:
        assert isinstance(parameter, Parameter) or parameter is None
        assert isinstance(text, str)
        assert isinstance(position, int)
        assert isinstance(tracing, str)

        # Perform any requested *tracing*:
        tables_editor = self

        # Stuff *text* into *parameter*:
        if parameter is not None:
            comments = parameter.comments
            assert len(comments) >= 1
            comment = comments[0]
            assert isinstance(comment, ParameterComment)
            comment.lines = text.split('\n')
            comment.position = position

        if tracing:
            main_window = tables_editor.main_window
            comment_text = main_window.parameters_comment_text
            cursor = comment_text.textCursor()
            actual_position = cursor.position()
            print("{0}position={1}".format(tracing, actual_position))

    # TablesEditor.parameter_is_active():
    def parameter_is_active(self):
        tables_editor = self
        tables_editor.current_update()
        # We can only create/edit parameters when there is an active *current_table*:
        return tables_editor.current_table is not None

    # TablesEditor.parameter_long_changed():
    def parameter_long_changed(self, new_long_heading):
        # Verify argument types:
        assert isinstance(new_long_heading, str)

        # Only do something if we are not already in a signal:
        tables_editor = self
        in_signal = tables_editor.in_signal
        if not in_signal:
            tables_editor.in_signal = True
            trace_signals = tables_editor.trace_signals

            # Update the correct *parameter_comment* with *new_long_heading*:
            current_parameter = tables_editor.current_parameter
            assert isinstance(current_parameter, Parameter)
            parameter_comments = current_parameter.comments
            assert len(parameter_comments) >= 1
            parameter_comment = parameter_comments[0]
            assert isinstance(parameter_comment, ParameterComment)
            parameter_comment.long_heading = new_long_heading

            # Update the user interface:
            tables_editor.update()


    # TablesEditor.parameters_edit_update():
    def parameters_edit_update(self, parameter=None, tracing=""):
        # Verify argument types:
        assert isinstance(parameter, Parameter) or parameter is None
        assert isinstance(tracing, str)

        # Make sure that the *current_table*, *current_parameter*, and *current_enumeration*
        # in *tables_editor* are valid:
        tables_editor = self

        tables_editor.current_update()
        current_table = tables_editor.current_table
        current_parameter = tables_editor.current_parameter
        parameter = current_parameter

        # Initialize all fields to an "empty" value:
        csv = ""
        is_valid_parameter = False
        default = ""
        optional = False
        type = ""

        # If we have a valid *parameter*, copy the field values out:
        if parameter is not None:
            # Grab some values from *parameter*:
            csv = parameter.csv
            is_valid_parameter = True
            default = parameter.default
            optional = parameter.optional
            type = parameter.type
            # print("type='{0}' optional={1}".format(type, optional))
        if tracing:
            print("{0}Parameter.name='{1}' csv='{2}'".
                  format(tracing, "None" if parameter is None else parameter.name, csv))

        # Grab some widgets from *main_window*:
        main_window = tables_editor.main_window
        csv_line = main_window.parameters_csv_line
        default_line = main_window.parameters_default_line
        optional_check = main_window.parameters_optional_check
        table_name = main_window.parameters_table_name
        type_combo = main_window.parameters_type_combo

        # The top-level update routine should have already called *TablesEditor*.*current_update*
        # to enusure that *current_table* is up-to-date:
        current_table = tables_editor.current_table
        table_name.setText("" if current_table is None else current_table.name)

        # Set the *csv_line* widget:
        previous_csv = csv_line.text()
        if previous_csv != csv:
            csv_line.setText(csv)
            if tracing:
                print("{0}Set csv to '{1}'".format(tracing, csv))

        # Stuff the values in to the *type_combo* widget:
        type_combo_size = type_combo.count()
        assert type_combo_size >= 1
        type_lower = type.lower()
        match_index = 0
        for type_index in range(type_combo_size):
            type_text = type_combo.itemText(type_index)
            if type_text.lower() == type_lower:
                match_index = type_index
                break
        type_combo.setCurrentIndex(match_index)

        default_line.setText(default)
        optional_check.setChecked(optional)

        # Enable/disable the parameter widgets:
        type_combo.setEnabled(is_valid_parameter)
        default_line.setEnabled(is_valid_parameter)
        optional_check.setEnabled(is_valid_parameter)

        # Update the *comments* (if they exist):
        if parameter is not None:
            comments = parameter.comments
            # Kludge for now, select the first comment
            assert len(comments) >= 1
            comment = comments[0]
            assert isinstance(comment, ParameterComment)

            # Update the headings:
            tables_editor.parameters_long_set(comment.long_heading)
            tables_editor.parameters_short_set(comment.short_heading)

            previous_csv = csv_line.text()
            if csv != previous_csv:
                csv_line.setText(csv)

            # Deal with comment text edit area:
            tables_editor.current_comment = comment
            lines = comment.lines
            text = '\n'.join(lines)

            tables_editor.comment_text_set(text)

        # Changing the *parameter* can change the enumeration combo box, so update it as well:
        # tables_editor.enumeration_update()

        # Update the *tables_combo_edit*:
        tables_editor.parameters_combo_edit.gui_update()

    # TablesEditor.parameters_long_set():
    def parameters_long_set(self, new_long_heading, tracing=""):
        # Verify argument types:
        assert isinstance(new_long_heading, str)
        assert isinstance(tracing, str)

        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self

        # Stuff *new_long_heading* into *current_parameter*:
        current_parameter = tables_editor.current_parameter
        if current_parameter is None:
            new_long_heading = ""
        else:
            assert isinstance(current_parameter, Parameter)
            current_parameter.long_heading = new_long_heading

        # Now update the user interface to shove *new_long_heading* into the *parameter_long_line*
        # widget:
        main_window = tables_editor.main_window
        long_line = main_window.parameters_long_line
        previous_long_heading = long_line.text()
        if previous_long_heading != new_long_heading:
            long_line.setText(new_long_heading)

    # TablesEditor.parameter_new():
    def parameter_new(self, name, tracing=""):
        # Verify argument types:
        assert isinstance(name, str)
        assert isinstance(tracing, str)

        # Create *new_parameter* named *name*:
        comments = [ParameterComment(language="EN", long_heading=name, lines=list())]
        new_parameter = Parameter(name=name, type="boolean", csv="",
                                  csv_index=-1, comments=comments)
        return new_parameter

    # TablesEditor.parameter_optional_clicked():
    def parameter_optional_clicked(self):
        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self

        current_parameter = tables_editor.current_parameter
        if current_parameter is not None:
            main_window = tables_editor.main_window
            parameter_optional_check = main_window.parameter_optional_check
            optional = parameter_optional_check.isChecked()
            current_parameter.optional = optional

    # TablesEditor.parameter_short_changed():
    def parameter_short_changed(self, new_short_heading):
        # Verify argument types:
        assert isinstance(new_short_heading, str)

        # Do not do anything when we are already in a signal:
        tables_editor = self
        if not tables_editor.in_signal:
            tables_editor.in_signal = True

            # Perform any requested tracing from *tables_editor* (i.e. *self*):
            trace_signals = tables_editor.trace_signals

            # Update *current_parameter* to have *new_short_heading*:
            current_parameter = tables_editor.current_parameter
            assert isinstance(current_parameter, Parameter)
            parameter_comments = current_parameter.comments
            assert len(parameter_comments) >= 1
            parameter_comment = parameter_comments[0]
            assert isinstance(parameter_comment, ParameterComment)
            parameter_comment.short_heading = new_short_heading

            # Update the user interface:
            tables_editor.update()

            tables_editor.in_signal = False

    # TablesEditor.parameters_short_set():
    def parameters_short_set(self, new_short_heading, tracing=""):
        # Verify argument types:
        assert isinstance(new_short_heading, str) or new_short_heading is None
        assert isinstance(tracing, str)

        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self

        # Stuff *new_short_heading* into *current_parameter*:
        current_parameter = tables_editor.current_parameter
        if new_short_heading is None or current_parameter is None:
            new_short_heading = ""
        else:
            current_parameter.short_heading = new_short_heading

        # Now update the user interface to show *new_short_heading* into the *parameter_short_line*
        # widget:
        main_window = tables_editor.main_window
        short_line = main_window.parameters_short_line
        previous_short_heading = short_line.text()
        if previous_short_heading != new_short_heading:
            short_line.setText(new_short_heading)

    # TablesEditor.parameters_type_changed():
    def parameters_type_changed(self):
        # Perform any requested *signal_tracing* from *tables_editor* (i.e. *self*):
        tables_editor = self
        if tables_editor.in_signal == 0:
            tables_editor.in_signal = True
            current_parameter = tables_editor.current_parameter
            trace_signals = tables_editor.trace_signals
            if trace_signals:
                print("=>TablesEditor.parameters_type_changed('{0}')".
                      format(None if current_parameter is None else current_parameter.name))

            # Load *type* into *current_parameter*:
            if current_parameter is not None:
                main_window = tables_editor.main_window
                parameters_type_combo = main_window.parameters_type_combo
                type = parameters_type_combo.currentText().lower()
                current_parameter.type = type

            # Wrap-up any requested *signal_tracing*:
            if trace_signals:
                print("<=TablesEditor.parameters_type_changed('{0}')\n".
                      format(None if current_parameter is None else current_parameter.name))
            tables_editor.in_signal = False

    # TablesEditor.parameters_update():
    def parameters_update(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Perform any requested *tracing*:
        if tracing:
            print("{0}=>TabledsEditor.parameters_update".format(tracing))

            # Make sure *current_table* is up to date:
            tables_editor = self
            tables_editor.current_update()
            current_table = tables_editor.current_table

            # The [import] tab does not do anything if there is no *current_table*:
            if current_table is not None:
                # Do some *tracing* if requested:
                if tracing:
                    print("{0}current_table='{1}'".format(tracing, current_table.name))

                # Grab some widgets from *tables_editor*:
                main_window = tables_editor.main_window
                # import_bind = main_window.import_bind
                # import_csv_file_line = main_window.import_csv_file_line
                # import_read = main_window.import_read
                parameters_table = main_window.parameters_table

                # Update the *import_csv_file_name* widget:
                # csv_file_name = current_table.csv_file_name
                # if tracing:
                #    print("{0}csv_file_name='{1}'".format(tracing, csv_file_name))
                assert False
                current_table.csv_read_and_process(
                  "/home/wayne/public_html/projects/digikey_csvs")

                # Load up *import_table*:
                headers = current_table.import_headers
                # rows = current_table.import_rows
                column_triples = current_table.import_column_triples
                # if tracing:
                #    print("{0}headers={1} rows={2} column_triples={3}".
                #      format(tracing, headers, rows, column_triples))

                parameters_table.clearContents()
                if headers is not None and column_triples is not None:
                    if tracing:
                        print("{0}Have column_triples".format(tracing))
                    parameters_table.setRowCount(len(headers))
                    parameters_table.setColumnCount(6)
                    # Fill in the left size row headers for *parameters_table*:
                    parameters_table.setVerticalHeaderLabels(headers)

                    assert len(column_triples) == len(headers)
                    for column_index, triples in enumerate(column_triples):
                        for triple_index, triple in enumerate(triples):
                            assert len(triple) == 3
                            count, name, value = triple

                            if count >= 1:
                                item = QTableWidgetItem("{0} x {1} '{2}'".
                                                        format(count, name, value))
                                parameters_table.setItem(column_index, triple_index, item)

                            # print("Column[{0}]: '{1}':{2} => {3}".
                            #  format(column_index, value, count, matches))

                            # print("Column[{0}]: {1}".format(column_index, column_table))
                            # print("Column[{0}]: {1}".format(column_index, column_list))

                            # assert column_index < len(parameters)
                            # parameter = parameters[column_index]
                            # type = "String"
                            # if len(matches) >= 1:
                            #    match = matches[0]
                            #    if match == "Integer":
                            #        type = "Integer"
                            #    elif match == "Float":
                            #        type = "Float"
                            # parameter.type = type

            # Enable/Disable *import_read* button widget depending upon whether *csv_file_name*
            # exists:
            # import_read.setEnabled(
            #  csv_file_name is not None and os.path.isfile(csv_file_name))
            # import_bind.setEnabled(current_table.import_headers is not None)

    # TablesEditor.quit_button_clicked():
    def quit_button_clicked(self):
        tables_editor = self
        print("TablesEditor.quit_button_clicked() called")
        application = tables_editor.application
        application.quit()

    # TablesEditor.results_update():
    def results_update(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        tables_editor = self
        main_window = tables_editor.main_window
        results_table = main_window.results_table
        results_table.clearContents()

        tables_editor.current_update()
        current_search = tables_editor.current_search
        if current_search is not None:
            current_search.filters_refresh()
            filters = current_search.filters

            # Compile *reg_ex* for each *filter* in *filters* that is marked for *use*:
            for filter_index, filter in enumerate(filters):
                reg_ex = None
                if filter.use:
                    reg_ex = re.compile(filter.select + "$")
                filter.reg_ex = reg_ex

            with open("download.csv", newline="") as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=',', quotechar='"')
                rows = list(csv_reader)
                table_row_index = 0
                for row_index, row in enumerate(rows):
                    if row_index == 0:
                        results_table.setColumnCount(len(row))
                        results_table.setRowCount(len(rows))
                        headers = [filter.parameter.name for filter in filters]
                        results_table.setHorizontalHeaderLabels(headers)
                    else:
                        match = True
                        for filter_index, filter in enumerate(filters):
                            value = row[filter_index]
                            if filter.use and filter.reg_ex.match(value) is None:
                                match = False
                                break
                        if match:
                            for filter_index, filter in enumerate(filters):
                                parameter = filter.parameter
                                datum = row[parameter.csv_index]
                                assert isinstance(datum, str), "datum='{0}'".format(datum)
                                if tracing is not None and row_index == 1:
                                    print("{0}[{1},{2}='{3}']:'{4}'".format(
                                      tracing, row_index, filter_index, parameter.name, datum))
                                if filter_index == 0:
                                    results_table.setRowCount(table_row_index + 1)

                                datum_item = QTableWidgetItem(datum)
                                results_table.setItem(table_row_index, filter_index, datum_item)
                            table_row_index += 1
            results_table.resizeRowsToContents()

        # Wrap up any requested *tracing*:
        if tracing:
            print("{0}<=TablesEditor.results_update()".format(tracing))

    # TablesEditor.re_table_get():
    @staticmethod
    def re_table_get():
        # Create some regular expressions and stuff the into *re_table*:
        si_units_re_text = Units.si_units_re_text_get()
        float_re_text = "-?([0-9]+\\.[0-9]*|\\.[0-9]+)"
        white_space_text = "[ \t]*"
        integer_re_text = "-?[0-9]+"
        integer_re = re.compile(integer_re_text + "$")
        float_re = re.compile(float_re_text + "$")
        url_re = re.compile("(https?://)|(//).*$")
        empty_re = re.compile("-?$")
        funits_re = re.compile(float_re_text + white_space_text + si_units_re_text + "$")
        iunits_re = re.compile(integer_re_text + white_space_text + si_units_re_text + "$")
        range_re = re.compile("[^~]+~[^~]+$")
        list_re = re.compile("([^,]+,)+[^,]+$")
        re_table = {
          "Empty": empty_re,
          "Float": float_re,
          "FUnits": funits_re,
          "Integer": integer_re,
          "IUnits": iunits_re,
          "List": list_re,
          "Range": range_re,
          "URL": url_re,
        }
        return re_table

    # TablesEditor.run():
    @trace(1)
    def run(self, tracing=""):
        # Show the *window* and exit when done:
        tables_editor = self
        main_window = tables_editor.main_window
        application = tables_editor.application
        # clipboard = application.clipboard()
        # print(f"type(clipboard)='{type(clipboard)}'")
        # assert isinstance(clipboard, QClipboard)

        main_window.show()

        sys.exit(application.exec_())

    # TablesEditor.save_button_clicked():
    def save_button_clicked(self):
        # Perform any requested signal tracing:
        tables_editor = self
        trace_signals = tables_editor.trace_signals
        next_tracing = " " if trace_signals else None
        if trace_signals:
            print("=>TablesEditor.save_button_clicked()")
        current_tables = tables_editor.current_tables

        # Save each *table* in *current_tables*:
        for table in current_tables:
            table.save()

        searches = tables_editor.searches
        xml_lines = list()
        xml_lines.append('<?xml version="1.0"?>')
        xml_lines.append('<Searches>')
        for search in searches:
            search.xml_lines_append(xml_lines, "  ")
        xml_lines.append('</Searches>')
        xml_lines.append("")
        # xml_text = '\n'.join(xml_lines)
        # searches_xml_file_name = os.path.join(order_root, "searches.xml")
        # with open(searches_xml_file_name, "w") as searches_xml_file:
        #     searches_xml_file.write(xml_text)
        assert False

    # TablesEditor.schema_update():
    def schema_update(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Grab some values from *tables_editor* (i.e. *self*):
        tables_editor = self
        main_window = tables_editor.main_window
        schema_tabs = main_window.schema_tabs
        schema_tabs_index = schema_tabs.currentIndex()
        if schema_tabs_index == 0:
            tables_editor.tables_update()
        elif schema_tabs_index == 1:
            tables_editor.parameters_edit_update()
        elif schema_tabs_index == 2:
            tables_editor.enumerations_update()
        else:
            assert False
        # tables_editor.combo_edit.update()
        # tables_editor.parameters_update(None)
        # tables_editor.search_update()

    # TablesEditor.searches_comment_get():
    def searches_comment_get(self, search, tracing=""):
        # Verify argument types:
        assert isinstance(search, Search) or search is None
        assert isinstance(tracing, str)

        # Perform any requested *tracing*:
        # tables_editor = self

        # Extract the comment *text* from *search*:
        if search is None:
            text = ""
            position = 0
        else:
            comments = search.comments
            assert len(comments) >= 1
            comment = comments[0]
            assert isinstance(comment, SearchComment)
            text = '\n'.join(comment.lines)
            position = comment.position

        return text, position

    # TablesEditor.searches_comment_set():
    def searches_comment_set(self, search, text, position, tracing=""):
        # Verify argument types:
        assert isinstance(search, Search) or search is None
        assert isinstance(text, str)
        assert isinstance(position, int)
        assert isinstance(tracing, str)

        # Perform any requested *tracing*:
        # tables_editor = self

        # Stuff *text* and *position* into *search*:
        if search is not None:
            comments = search.comments
            assert len(comments) >= 1
            comment = comments[0]
            assert isinstance(comment, SearchComment)
            comment.lines = text.split('\n')
            comment.position = position

    # TablesEditor.searches_file_save():
    def searches_file_save(self, file_name, tracing=""):
        # Verify argument types:
        assert isinstance(file_name, str)
        assert isinstance(tracing, str)

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing:
            print("{0}=>TablesEditor.searches_file_save('{1}')".format(tracing, file_name))

        xml_lines = list()
        xml_lines.append('<?xml version="1.0"?>')
        xml_lines.append('<Searches>')

        # Sweep through each *search* in *searches* and append the results to *xml_lines*:
        tables_editor = self
        searches = tables_editor.searches
        for search in searches:
            search.xml_lines_append(xml_lines, "  ")

        # Wrap up *xml_lines* and generate *xml_text*:
        xml_lines.append('</Searches>')
        xml_lines.append("")
        xml_text = '\n'.join(xml_lines)

        # Write out *xml_text* to *file_name*:
        with open(file_name, "w") as xml_file:
            xml_file.write(xml_text)

        # Wrqp up any requested *tracing*:
        if tracing:
            print("{0}<=TablesEditor.searches_file_save('{1}')".format(tracing, file_name))

    # TablesEditor.searches_file_load():
    def searches_file_load(self, xml_file_name, tracing=""):
        # Verify argument types:
        assert isinstance(xml_file_name, str)
        assert isinstance(tracing, str)

        # Read in *xml_file_name* (if it exists):
        if os.path.isfile(xml_file_name):
            with open(xml_file_name) as xml_file:
                xml_text = xml_file.read()

            # Parse *xml_text* into *searches_tree*:
            searches_tree = etree.fromstring(xml_text)
            assert isinstance(searches_tree, etree._Element)
            assert searches_tree.tag == "Searches"

            # Dig dow the next layer of *searches_tree*
            search_trees = list(searches_tree)

            # Grab *searches* from *tables_editor* (i.e. *self*) and empty it out:
            tables_editor = self
            searches = tables_editor.searches
            assert isinstance(searches, list)
            del searches[:]

            # Parse each *search_tree* in *search_trees*:
            for search_tree in search_trees:
                assert isinstance(search_tree, etree._Element)
                search = Search(search_tree=search_tree,
                                tables=tables_editor.tables)
                assert False, "Old code"
                searches.append(search)

            # Set *current_search*
            tables_editor.current_search = searches[0] if len(searches) >= 1 else None

    # TablesEditor.searches_is_active():
    def searches_is_active(self):
        tables_editor = self
        tables_editor.current_update()
        # We can only edit searches if there is there is an active *current_table8:
        return tables_editor.current_table is not None

    # TablesEditor.searches_new():
    def searches_new(self, name, tracing=""):
        # Verify argument types:
        assert isinstance(name, str)
        assert isinstance(tracing, str)

        tables_editor = self
        tables_editor.current_update()
        current_table = tables_editor.current_table

        # Create *serach* with an empty English *serach_comment*:
        search_comment = SearchComment(language="EN", lines=list())
        search_comments = [search_comment]
        search = Search(name=name, comments=search_comments, table=current_table)
        search.filters_refresh()

        return search

    # TablesEditor.searches_save_button_clicked():
    def searches_save_button_clicked(self):
        # Peform an requested signal tracing:
        tables_editor = self
        tracing = " " if tables_editor.trace_signals else None
        # next_tracing = None if tracing is None else " "
        if tracing:
            print("=>TablesEditor.searches_save_button_clicked()".format(tracing))

        # Write out the searches to *file_name*:
        # file_name = os.path.join(order_root, "searches.xml")
        # tables_editor.searches_file_save(file_name)
        assert False

        if tracing:
            print("<=TablesEditor.searches_save_button_clicked()\n".format(tracing))

    # TablesEditor.searches_table_changed():
    def searches_table_changed(self, new_text):
        # Verify argument types:
        assert isinstance(new_text, str)

        # Do nothing if we are already in a signal:
        tables_editor = self
        if not tables_editor.in_signal:
            tables_editor.in_signal = True
            # Perform any requested *tracing*:
            trace_signals = tables_editor.trace_signals
            next_tracing = " " if trace_signals else None
            if trace_signals:
                print("=>TablesEditor.searches_table_changed('{0}')".format(new_text))

            # Make sure *current_search* is up to date:
            tables_editor = self
            tables_editor.current_update()
            current_search = tables_editor.current_search

            # Find the *table* that matches *new_text* and stuff it into *current_search*:
            if current_search is not None:
                match_table = None
                tables = tables_editor.tables
                for table_index, table in enumerate(tables):
                    assert isinstance(table, Table)
                    if table.name == new_text:
                        match_table = table
                        break
                current_search.table_set(match_table)

            # Wrap up any requested *tracing*:
            if trace_signals:
                print("<=TablesEditor.searches_table_changed('{0}')\n".format(new_text))
            tables_editor.in_signal = False

    # TablesEditor.searches_update():
    def searches_update(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Make sure that *current_search* is up to date:
        tables_editor = self
        tables_editor.current_update()
        current_search = tables_editor.current_search

        # Update *searches_combo_edit*:
        searches_combo_edit = tables_editor.searches_combo_edit
        searches_combo_edit.gui_update()

        # Next: Update the table options:
        search_table = None if current_search is None else current_search.table
        tables = tables_editor.tables
        main_window = tables_editor.main_window
        searches_table_combo = main_window.searches_table_combo
        searches_table_combo.clear()
        if len(tables) >= 1:
            match_index = -1
            for table_index, table in enumerate(tables):
                assert isinstance(table, Table)
                searches_table_combo.addItem(table.name)
                if table is search_table:
                    match_index = table_index
            if match_index >= 0:
                searches_table_combo.setCurrentIndex(match_index)

    # TablesEditor.tab_changed():
    def tab_changed(self, new_index):
        # Verify argument types:
        assert isinstance(new_index, int)

        # Note: *new_index* is only used for debugging.

        # Only deal with this siginal if we are not already *in_signal*:
        tables_editor = self
        if not tables_editor.in_signal:
            # Disable  *nested_signals*:
            tables_editor.in_signal = True

            # Perform any requested signal tracing:
            trace_signals = tables_editor.trace_signals
            next_tracing = " " if trace_signals else None
            if trace_signals:
                print("=>TablesEditor.tab_changed(*, {0})".format(new_index))

            # Deal with clean-up of previous tab (if requested):
            tab_unload = tables_editor.tab_unload
            if callable(tab_unload):
                tab_unload(tables_editor)

            # Perform the update:
            tables_editor.update()

            # Wrap up any requested signal tracing and restore *in_signal*:
            if trace_signals:
                print("<=TablesEditor.tab_changed(*, {0})\n".format(new_index))
            tables_editor.in_signal = False

    # TablesEditor.table_comment_get():
    def table_comment_get(self, table, tracing=""):
        # Verify argument types:
        assert isinstance(table, Table)
        assert isinstance(tracing, str)

        text = ""
        # Perform any requested *tracing*:
        # tables_editor = self

        # Extract the comment *text* from *table*:
        if table is not None:
            comments = table.comments
            assert len(comments) >= 1
            comment = comments[0]
            assert isinstance(comment, TableComment)
            text = '\n'.join(comment.lines)
            position = comment.position
        return text, position

    # TablesEditor.table_comment_set():
    def table_comment_set(self, table, text, position, tracing=""):
        # Verify argument types:
        assert isinstance(table, Table)
        assert isinstance(text, str)
        assert isinstance(position, int)
        assert isinstance(tracing, str)

        # Perform any requested *tracing*:
        # tables_editor = self
        # next_tracing = None if tracing is None else tracing + " "
        if tracing:
            print("{0}=>table_comment_set('{1}')".format(tracing, table.name))

        # Stuff *text* into *table*:
        if table is not None:
            comments = table.comments
            assert len(comments) >= 1
            comment = comments[0]
            assert isinstance(comment, TableComment)
            comment.lines = text.split('\n')
            comment.position = position

        # Wrap up any requested *tracing*:
        if tracing:
            print("{0}<=table_comment_set('{1}')".format(tracing, table.name))

    def table_is_active(self):
        # The table combo box is always active, so we return *True*:
        return True

    # TablesEditor.table_new():
    def table_new(self, name, tracing=""):
        # Verify argument types:
        assert isinstance(name, str)

        # Perform an requested *tracing*:

        file_name = "{0}.xml".format(name)
        table_comment = TableComment(language="EN", lines=list())
        table = Table(file_name=file_name, name=name, path="", comments=[table_comment],
                      parameters=list(), csv_file_name="", parent=None)

        return table

    # TablesEditor.table_setup():
    def table_setup(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Perform any tracing requested from *tables_editor* (i.e. *self*):
        tables_editor = self

        # Grab the *table* widget and *current_table* from *tables_editor* (i.e. *self*):
        tables_editor = self
        main_window = tables_editor.main_window
        data_table = main_window.data_table
        assert isinstance(data_table, QTableWidget)
        current_table = tables_editor.current_table

        # Dispatch on *current_table* depending upon whether it exists or not:
        if current_table is None:
            # *current_table* is empty, so we initialize the *table* widget to be empty:
            data_table.setHorizontalHeaderLabels([])
            data_table.setColumnCount(0)
            data_table.setRowCount(0)
        else:
            # *current_table* is valid, so we extract the *header_labels* and attach them to the
            # *table* widget:
            assert isinstance(current_table, Table)
            header_labels = current_table.header_labels_get()
            data_table.setHorizontalHeaderLabels(header_labels)
            data_table.setColumnCount(len(header_labels))
            data_table.setRowCount(1)

    # TablesEditor.tables_update():
    def tables_update(self, table=None, tracing=""):
        # Verify argument types:
        assert isinstance(table, Table) or table is None
        assert isinstance(tracing, str)

        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self

        # Make sure that the *current_table*, *current_parameter*, and *current_enumeration*
        # in *tables_editor* are valid:
        tables_editor.current_update()

        # Update the *tables_combo_edit*:
        tables_editor.tables_combo_edit.gui_update()

    # TablesEditor.update():
    @trace(1)
    def update(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Perform any requested *tracing*:
        tables_editor = self

        # Only update the visible tabs based on *root_tabs_index*:
        main_window = tables_editor.main_window
        root_tabs = main_window.root_tabs
        root_tabs_index = root_tabs.currentIndex()
        if root_tabs_index == 0:
            tables_editor.collections_update()
        elif root_tabs_index == 1:
            tables_editor.schema_update()
        elif root_tabs_index == 2:
            tables_editor.parameters_update()
        elif root_tabs_index == 3:
            tables_editor.find_update()
        else:
            assert False, "Illegal tab index: {0}".format(root_tabs_index)

    # TablesEditor.search_update():
    def xxx_search_update(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Make sure that the *current_table*, *current_parameter*, and *current_enumeration*
        # in *tables_editor* are valid:
        tables_editor = self
        tables_editor.current_update()

        # Grab the *current_table* *Table* object from *tables_editor* (i.e. *self*.)
        # Grab the *seach_table* widget from *tables_editor* as well:
        current_table = tables_editor.current_table
        main_window = tables_editor.main_window
        search_table = main_window.search_table
        assert isinstance(search_table, QTableWidget)

        # Step 1: Empty out *search_table*:
        search_table.clearContents()
        search_table.setHorizontalHeaderLabels(["Parameter", "Use", "Criteria"])

        # Dispatch on whether *current_table* exists or not:
        if current_table is None:
            # We have no *current_table*, so show an empty search table:
            # search_table.setHorizontalHeaderLabels([])
            # search_table.setColumnCount(0)
            # data_table.setRowCount(0)
            pass
        else:
            # *current_table* is active, so fill in *search_table*:
            assert isinstance(current_table, Table)
            header_labels = current_table.header_labels_get()
            # print("Header_labels={0}".format(header_labels))
            search_table.setColumnCount(3)
            search_table.setRowCount(len(header_labels))

            # Now convert eacch *parameter* in *parameters into a row in *search_table*:
            parameters = current_table.parameters
            assert len(parameters) == len(header_labels)
            for parameter_index, parameter in enumerate(parameters):
                # Create the header label in the first column:
                header_item = QTableWidgetItem(header_labels[parameter_index])
                header_item.setData(Qt.UserRole, parameter)
                search_table.setItem(parameter_index, 0, header_item)

                # Create the use [] check box in the second column:
                use_item = QTableWidgetItem("")
                assert isinstance(use_item, QTableWidgetItem)
                # print(type(use_item))
                # print(use_item.__class__.__bases__)
                flags = use_item.flags()
                use_item.setFlags(flags | Qt.ItemIsUserCheckable)
                check_state = Qt.Unchecked
                if parameter.use:
                    check_state = Qt.Checked
                use_item.setCheckState(check_state)
                # use_item.itemChanged.connect(
                #  partial(TablesEditor.search_use_clicked, tables_editor, use_item, parameter))
                parameter.use = False
                search_table.setItem(parameter_index, 1, use_item)
                search_table.cellClicked.connect(
                  partial(TablesEditor.search_use_clicked, tables_editor, use_item, parameter))

                # if parameter.type == "enumeration":
                #    #combo_box = QComboBox()
                #    #combo_box = QTableWidgetItem("")
                #    combo_box = QComboBox()
                #    assert isinstance(combo_box, QWidget)
                #    model = QStandardItemModel(1, 1)
                #    enumerations = parameter.enumerations
                #    for enumeration_index, enumeration in enumerate(enumerations):
                #        assert isinstance(enumeration, Enumeration)
                #        #comments = enumeration.comments
                #        #comments_size = len(comments)
                #        #assert comments_size >= 1
                #        #comment = comments[0]
                #        #combo_box.addItem(enumeration.name, userData=enumeration)
                #        item = QStandardItem(enumeration.name)
                #        combo_box.setItem(enumeration_index, 0, item)
                #    search_table.setCellWidget(parameter_index, 2, combo_box)
                # else:
                criteria_item = QTableWidgetItem("")
                criteria_item.setData(Qt.UserRole, parameter)
                search_table.setItem(parameter_index, 2, criteria_item)

        # Update the *search_combo_edit*:
        tables_editor.search_combo_edit.gui_update()


# TreeModel:
class TreeModel(QAbstractItemModel):

    FLAG_DEFAULT = Qt.ItemIsEnabled | Qt.ItemIsSelectable

    # TreeModel.__init__():
    def __init__(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Initialize the parent *QAbstraceItemModel*:
        super().__init__()

        # Stuff values into *tree_model* (i.e. *self*):
        tree_model = self
        tree_model.headers = {0: "Type", 1: "Name"}
        tree_model.collections = None
        tree_model.tracing = tracing

    # check if the node has data that has not been loaded yet
    # TreeModel.canFetchMore():
    def canFetchMore(self, model_index):
        # Verify argument types:
        assert isinstance(model_index, QModelIndex)

        # Perform any *tracing* requested by *tree_model* (i.e.*self*):
        tree_model = self
        tracing = tree_model.tracing
        if tracing:
            print(f"{tracing}=>TreeModel.canFetchMore()")

        # We delegate the decision of whether we can fetch more stuff to the *node*
        # associated with *model_index*:
        node = tree_model.getNode(model_index)
        can_fetch_more = node.can_fetch_more()

        # Wrap up any requested *tracing*:
        if tracing:
            print(f"{tracing}<=TreeModel.canFetchMore()=>{can_fetch_more}")
        return can_fetch_more

    # TreeModel.collections_set():
    def collections_set(self, collections):
        # Verify argument types:
        assert isinstance(collections, Collections)

        # Stuff *collections* into *tree_model* (i.e. *self*):
        tree_model = self
        tree_model.collections = collections

    # TreeModel.columnCount():
    def columnCount(self, model_index):
        # Verify argument types:
        assert isinstance(model_index, QModelIndex)
        return 2

    # TreeModel.data():
    def data(self, model_index, role):
        # Verify argument types:
        assert isinstance(model_index, QModelIndex)
        assert isinstance(role, int)

        # Perform any *tracing* requested by *tree_model* (i.e. *self*):
        tree_model = self
        tracing = tree_model.tracing
        tracing = None   # Disable *tracing* for now:
        next_tracing = None if tracing is None else tracing + " "
        if tracing:
            print(f"{tracing}=>Tree_model.data(*, *, {role}')")

        value = None
        if model_index.isValid():
            # row = model_index.row()
            column = model_index.column()
            node = model_index.internalPointer()
            if role == Qt.DisplayRole:
                if column == 0:
                    value = node.type_letter_get()
                elif column == 1:
                    value = node.name_get()
        assert isinstance(value, str) or value is None

        # Wrap up any requested *tracing*:
        if tracing:
            print(f"{tracing}<=Tree_model.data(*, *, {role}')=>{value}")
        return value

    # TreeModel.delete():
    def delete(self, model_index, tracing=""):
        # Verify argument types:
        assert isinstance(model_index, QModelIndex)
        assert isinstance(tracing, str)

        # Perform any *tracing* requested by *tree_model* (i.e. *self*):
        tree_model = self

        # Carefully delete the row associated with *model_index*:
        if model_index.isValid():
            # row = model_index.row()
            node = tree_model.getNode(model_index)
            assert isinstance(node, Node)
            parent = node.parent
            assert isinstance(parent, Node)
            parent.child_remove(node)

    # TreeModel.fetchMore():
    def fetchMore(self, model_index):
        # Verify argument types:
        assert isinstance(model_index, QModelIndex)

        # Perform any *tracing* requested by *tree_model* (i.e. *self*):
        tree_model = self

        # Delegate fetching to the *node* associated with *model_index*:
        tree_model = self
        node = tree_model.getNode(model_index)
        node.fetch_more()
        # tree_model.insertNodes(0, node.children_get(), model_index)

    # TreeModel.getNode():
    def getNode(self, model_index):
        # Verify argument types:
        assert isinstance(model_index, QModelIndex)

        tree_model = self
        node = (model_index.internalPointer() if model_index.isValid()
                else tree_model.collections)
        assert isinstance(node, Node), f"node.type={type(node)}"
        return node

    # TreeModel.hasChildren():
    def hasChildren(self, model_index):
        # Verify argument types:
        assert isinstance(model_index, QModelIndex)

        # Grab the *node* associated with *model_index* in *tree_mode* (i.e. *self*):
        tree_model = self
        node = tree_model.getNode(model_index)
        assert isinstance(node, Node)

        # Delegate to *has_children*() method of *node*:
        has_children = node.has_children()
        return has_children

    # TreeModel.headerData():
    def headerData(self, section, orientation, role):
        assert isinstance(section, int)
        assert isinstance(orientation, Qt.Orientation)
        assert isinstance(role, int)

        tree_model = self
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return tree_model.headers[section]
        return None

    # TreeModel.flags():
    def flags(self, model_index):
        # Verify argument types:
        assert isinstance(model_index, QModelIndex)

        return TreeModel.FLAG_DEFAULT

    # TreeModel.index():
    def index(self, row, column, parent_model_index):
        # Verify argument types:
        assert isinstance(row, int)
        assert isinstance(column, int)
        assert isinstance(parent_model_index, QModelIndex)

        tree_model = self
        node = tree_model.getNode(parent_model_index)
        # FIXME: child method should be sibling method!!!
        child = node.child(row)
        index = QModelIndex() if child is None else tree_model.createIndex(row, column, child)
        assert isinstance(parent_model_index, QModelIndex)
        return index

    # TreeModel.children_update():
    def children_update(self, parent_model_index, tracing=""):
        # Verify argument types:
        assert isinstance(parent_model_index, QModelIndex)
        assert isinstance(tracing, str)

        # Grab the *parent_node* using *parent_model_index* and *tree_model* (i.e. *self*):
        tree_model = self
        parent_node = tree_model.getNode(parent_model_index)
        children = parent_node.children_get()
        children_size = len(children)

        # For now delete everything and reinsert it:
        if children_size >= 1:
            tree_model.beginRemoveRows(parent_model_index, 0, children_size - 1)
            tree_model.endRemoveRows()
        tree_model.beginInsertRows(parent_model_index, 0, children_size - 1)
        tree_model.endInsertRows()

    # TreeModel.insertNodes():
    def insertNodes(self, position, nodes, parent_model_index=QModelIndex()):
        # Verify argument types:
        assert isinstance(position, int)
        assert isinstance(nodes, list)
        assert isinstance(parent_model_index, QModelIndex)
        for node in nodes:
            assert isinstance(node, Node)

        tree_model = self
        node = tree_model.getNode(parent_model_index)

        tree_model.beginInsertRows(parent_model_index, position, position + len(nodes) - 1)

        for child in reversed(nodes):
            node.child_insert(position, child)

        tree_model.endInsertRows()

        return True

    # TreeModel.parent():
    def parent(self, model_index):
        # Verify argument types:
        assert isinstance(model_index, QModelIndex)

        tree_model = self
        node = tree_model.getNode(model_index)

        parent = node.parent
        parent_model_index = (QModelIndex() if parent is tree_model.collections else
                              tree_model.createIndex(parent.row(), 0, parent))
        assert isinstance(model_index, QModelIndex)
        return parent_model_index

    # Return 0 if there is data to fetch (handled implicitly by check length of child list)
    # TreeModel.rowCount():
    def rowCount(self, parent):
        # Verify argument types:
        assert isinstance(parent, QModelIndex)
        tree_model = self
        node = tree_model.getNode(parent)
        count = node.child_count()
        return count


# Units:
class Units:
    # Units.__init():
    def __init__(self):
        pass

    # Units.si_units_re_text_get():
    @staticmethod
    def si_units_re_text_get():
        base_units = (
          "s(ecs?)?", "seconds?", "m(eters?)?", "g(rams?)?", "[Aa](mps?)?", "[Kk](elvin)?",
          "mol(es?)?", "cd", "candelas?")
        derived_units = ("rad", "sr", "[Hh]z", "[Hh]ertz", "[Nn](ewtons?)?", "Pa(scals?)?",
                         "J(oules?)?", "W(atts?)?", "°C", "V(olts?)?", "F(arads?)?", "Ω",
                         "O(hms?)?", "S", "Wb", "T(eslas?)?", "H", "degC", "lm", "lx", "Bq",
                         "Gy", "Sv", "kat")
        all_units = base_units + derived_units
        all_units_re_text = "(" + "|".join(all_units) + ")"
        prefixes = (
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
        )
        single_letter_prefixes = [prefix[0] for prefix in prefixes if len(prefix[0]) == 1]
        single_letter_re_text = "[" + "".join(single_letter_prefixes) + "]"
        multi_letter_prefixes = [prefix[0] for prefix in prefixes if len(prefix[0]) >= 2]
        letter_prefixes = [single_letter_re_text] + multi_letter_prefixes
        prefix_re_text = "(" + "|".join(letter_prefixes) + ")"
        # print("prefix_re_text='{0}'".format(prefix_re_text))
        si_units_re_text = prefix_re_text + "?" + all_units_re_text
        # print("si_units_re_text='{0}'".format(si_units_re_text))
        return si_units_re_text


# VendorPart:
class VendorPart:
    # A vendor part represents a part that can be ordered from a vendor.

    # VendorPart.__init__():
    def __init__(self, actual_part, vendor_name, vendor_part_name,
                 quantity_available, price_breaks, timestamp=0):
        """ *VendorPart*: Initialize *self* to contain *actual_part"""

        # print("vendor_part_name=", vendor_part_name)

        # Check argument types:
        assert isinstance(actual_part, ActualPart)
        assert isinstance(vendor_name, str)
        assert isinstance(vendor_part_name, str)
        assert isinstance(quantity_available, int), ("quantity_available={0}".format(
                                                     quantity_available))
        assert isinstance(price_breaks, list)
        assert isinstance(timestamp, int)
        for price_break in price_breaks:
            assert isinstance(price_break, PriceBreak)

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
        price_breaks = tuple(price_breaks)

        # Load up *self*:
        self.actual_part_key = actual_part.key
        self.quantity_available = quantity_available
        self.price_breaks = price_breaks
        self.timestamp = timestamp
        self.vendor_key = (vendor_name, vendor_part_name)
        self.vendor_name = vendor_name
        self.vendor_part_name = vendor_part_name

        # Append *self* to the vendor parts of *actual_part*:
        actual_part.vendor_part_append(self)

    # VendorPart.__eq__():
    def __eq__(self, vendor_part2):
        # Verify argument types:
        assert isinstance(vendor_part2, VendorPart)

        # Compare *vendor_part1* to *vendor_part2*:
        vendor_part1 = self
        actual_part_key_equal = vendor_part1.actual_part_key == vendor_part2.actual_part_key
        quantity_available_equal = (vendor_part1.quantity_available ==
                                    vendor_part2.quantity_available)
        timestamp_equal = vendor_part1.timestamp == vendor_part2.timestamp
        vendor_key_equal = vendor_part1.vendor_key == vendor_part2.vendor_key

        # Compute whether *price_breaks1* is equal to *price_breaks2*:
        price_breaks1 = vendor_part1.price_breaks
        price_breaks2 = vendor_part2.price_breaks
        price_breaks1_size = len(price_breaks1)
        price_breaks2_size = len(price_breaks2)
        price_breaks_equal = price_breaks1_size == price_breaks2_size
        if price_breaks_equal:
            for index in range(price_breaks1_size):
                price_break1 = price_breaks1[index]
                price_break2 = price_breaks2[index]
                price_breaks_equal = price_breaks_equal and (price_break1 == price_break2)

        # Compute *vendor_parts_equal* which is only *True* if all the other fields are equal:
        vendor_parts_equal = (actual_part_key_equal and quantity_available_equal and
                              timestamp_equal and vendor_key_equal and price_breaks_equal)
        return vendor_parts_equal

    # VendorPart.__format__():
    def __format__(self, format):
        """ *VendorPart*: Print out the information of the *VendorPart* (i.e. *self*):
        """

        vendor_part = self
        vendor_name = vendor_part.vendor_name
        vendor_part_name = vendor_part.vendor_part_name
        # price_breaks = vendor_part.price_breaks
        return "'{0}':'{1}'".format(vendor_name, vendor_part_name)

    # VendorPart.dump():
    def dump(self, out_stream, indent):
        """ *VendorPart*: Dump the *VendorPart* (i.e. *self*) out to
            *out_stream* in human readable form indented by *indent* spaces.
        """

        # Verify argument types:
        assert isinstance(out_stream, io.IOBase)
        assert isinstance(indent, int)

        # Dump out *self*:
        out_stream.write("{0}ActualPart_Key:{1}\n".
                         format(" " * indent, self.actual_part_key))
        out_stream.write("{0}Vendor_Key:{1}\n".
                         format(" " * indent, self.vendor_key))
        out_stream.write("{0}Vendor_Name:{1}\n".
                         format(" " * indent, self.vendor_name))
        out_stream.write("{0}VendorPart_Name:{1}\n".
                         format(" " * indent, self.vendor_part_name))
        out_stream.write("{0}Quantity_Available:{1}\n".
                         format(" " * indent, self.quantity_available))
        out_stream.write("{0}PriceBreaks: (skip)\n".
                         format(" " * indent))

    # VendorPart.price_breaks_text_get():
    def price_breaks_text_get(self):
        """ *VendorPart*: Return the prices breaks for the *VendorPart*
            object (i.e. *self*) as a text string:
        """

        price_breaks_text = ""
        for price_break in self.price_breaks:
            price_breaks_text += "{0}/${1:.3f} ".format(
              price_break.quantity, price_break.price)
        return price_breaks_text

    # VendorPart.xml_lines_append():
    def xml_lines_append(self, xml_lines, indent):
        # Verify argument types:
        assert isinstance(xml_lines, list)
        assert isinstance(indent, str)

        # Grab some values from *vendor_part* (i.e. *self*):
        vendor_part = self
        quantity_available = vendor_part.quantity_available
        price_breaks = vendor_part.price_breaks
        vendor_name = vendor_part.vendor_name
        vendor_part_name = vendor_part.vendor_part_name
        timestamp = vendor_part.timestamp

        # Output the `<VendorPart ...>` tag first:
        xml_lines.append(f'{indent}<VendorPart '
                         f'quantity_available="{quantity_available}\" '
                         f'timestamp="{timestamp}" '
                         f'vendor_name="{Encode.to_attribute(vendor_name)}\" '
                         f'vendor_part_name="{Encode.to_attribute(vendor_part_name)}">')

        # Output the nested `<PriceBreak ...>` tags:
        next_indent = indent + " "
        for price_break in price_breaks:
            price_break.xml_lines_append(xml_lines, next_indent)

        # Close out with the `</VendorPart>` tag:
        xml_lines.append(f"{indent}</VendorPart>")

    # VendorPart.xml_parse():
    @staticmethod
    def xml_parse(vendor_part_tree, actual_part):
        # Verify argument types:
        assert isinstance(vendor_part_tree, etree._Element)
        assert isinstance(actual_part, ActualPart)
        assert vendor_part_tree.tag == "VendorPart"

        # Pull out the attribute values:
        attributes_table = vendor_part_tree.attrib
        timestamp = int(float(attributes_table["timestamp"]))
        vendor_name = attributes_table["vendor_name"]
        vendor_part_name = attributes_table["vendor_part_name"]

        price_breaks = []
        price_break_trees = list(vendor_part_tree)
        for price_break_tree in price_break_trees:
            price_break = PriceBreak.xml_parse(price_break_tree)
            price_breaks.append(price_break)

        quantity_available = 0  # Old inventory stuff...
        vendor_part = VendorPart(actual_part, vendor_name, vendor_part_name,
                                 quantity_available, price_breaks, timestamp)
        return vendor_part

# class XXXAttribute:
#    def __init__(self, name, type, default, optional, documentations, enumerates):
#        # Verify argument types:
#        assert isinstance(name, str) and len(name) > 0
#        assert isinstance(type, str)
#        assert isinstance(default, str) or default == None
#        assert isinstance(optional, bool)
#        assert isinstance(documentations, list)
#        for documentation in documentations:
#            assert isinstance(documentation, Documentation)
#        assert isinstance(enumerates, list)
#        for enumerate in enumerates:
#            assert isinstance(enumerate, Enumerate)
#
#        # Stuff arguments into *attribute* (i.e. *self*):
#        attribute = self
#        attribute.name = name
#        attribute.type = type
#        attribute.default = default
#        attribute.enumerates = enumerates
#        attribute.optional = optional
#        attribute.documentations = documentations
#
#    def __eq__(self, attribute2):
#        # Verify argument types:
#        assert isinstance(attribute2, Attribute)
#        attribute1 = self
#
#        is_equal = (
#          attribute1.name == attribute2.name and
#          attribute1.type == attribute2.type and
#          attribute1.default == attribute2.default and
#          attribute1.optional == attribute2.optional)
#
#        documentations1 = attribute1.documentations
#        documentations2 = attribute1.documentations
#        if len(documentations1) == len(documentations2):
#            for index in range(len(documentations1)):
#                documentation1 = documentations1[index]
#                documentation2 = documentations2[index]
#                if documentation1 != documentation2:
#                    is_result = False
#                    break
#        else:
#            is_equal = False
#        return is_equal
#
#    def copy(self):
#        attribute = self
#
#        new_documentations = list()
#        for documentation in attribute.documentations:
#            new_documentations.append(documentation.copy())
#        new_attribute = Attribute(attribute.name,
#          attribute.type, attribute.default, attribute.optional, new_documentations, list())
#        return new_attribute
#
# class XXXDocumentation:
#    def __init__(self, language, xml_lines):
#        # Verify argument types:
#        assert isinstance(language, str)
#        assert isinstance(xml_lines, list)
#        for line in xml_lines:
#           assert isinstance(line, str)
#
#        # Load arguments into *documentation* (i.e. *self*):
#        documentation = self
#        documentation.language = language
#        documentation.xml_lines = xml_lines
#
#    def __equ__(self, documentation2):
#        # Verify argument types:
#        assert isinstance(documentation2, Documenation)
#
#        documentation1 = self
#        is_equal = documentation1.langauge == documentation2.language
#
#        # Determine wheter *xml_lines1* is equal to *xml_lines2*:
#        xml_lines1 = documentation1.xml_lines
#        xml_lines2 = documentation2.xml_lines
#        if len(xml_lines1) == len(line2):
#            for index, line1 in enumerate(xml_lines1):
#                line2 = xml_lines2[index]
#                if line1 != line2:
#                    is_equal = False
#                    break
#        else:
#            is_equal = False
#        return is_equal
#
#    def copy(self):
#        documentation = self
#        new_documentation = Documentation(documentation.language, list(documentation.xml_lines))
#        return new_documentation
#
# class XEnumeration:
#    """ An *Enumeration* object represents a single enumeration possibility for an attribute.
#    """
#
#    # Class: Enumeration
#    def __init__(self, **arguments_table):
#        """
#        """
#        # Verify argument types:
#        assert isinstance(name, str, documents)
#        assert isinstace(documentations, list)
#        for documentation in documentations:
#            assert isinstance(documentation, Documentation)
#
#        # Stuff *name* value into *enumeration* (i.e. *self*):
#        enumeration.name = name
#        enumeration.documents = documents
#
# class XXXSchema:
#    def __init__(self, schema_text=None):
#        # Veritfy argument types:
#        assert isinstance(schema_text, str) or schema_text == None
#
#        # Create an empty *schema*:
#        target_name_space = ""
#        attributes = list()
#        if isinstance(schema_text, str):
#            # Convert *schema_text* from XML format into *schema_root* (an *etree._element*):
#            schema_root = etree.fromstring(schema_text)
#            assert isinstance(schema_root, etree._Element)
#
#            xml_name_space = "{http://www.w3.org/XML/1998/namespace}"
#
#            assert schema_root.tag.endswith("}schema")
#            attributes_table = schema_root.attrib
#            assert "targetNamespace" in attributes_table
#            target_name_space = attributes_table["targetNamespace"]
#            xsd_elements = list(schema_root)
#
#            assert len(xsd_elements) == 1
#            table_element = xsd_elements[0]
#            assert isinstance(table_element, etree._Element)
#            table_element_name = table_element.tag
#            assert table_element_name.endswith("}element")
#
#            table_complex_types = list(table_element)
#            assert len(table_complex_types) == 1
#            table_complex_type = table_complex_types[0]
#            assert isinstance(table_complex_type, etree._Element)
#            assert table_complex_type.tag.endswith("}complexType")
#
#            sequences = list(table_complex_type)
#            assert len(sequences) == 1
#            sequence = sequences[0]
#            assert isinstance(sequence, etree._Element)
#            assert sequence.tag.endswith("}sequence"), sequence.tag
#
#            item_elements = list(sequence)
#            assert len(item_elements) == 1
#            item_element = item_elements[0]
#            assert isinstance(item_element, etree._Element)
#            assert item_element.tag.endswith("}element")
#
#            item_complex_types = list(item_element)
#            assert len(item_complex_types) == 1
#            item_complex_type = item_complex_types[0]
#            assert isinstance(item_complex_type, etree._Element)
#            assert item_complex_type.tag.endswith("}complexType")
#
#            item_attributes = list(item_complex_type)
#            assert len(item_attributes) >= 1
#            for attribute_child in item_attributes:
#                # Extract the attributes of `<attribute ...>`:
#                assert attribute_child.tag.endswith("}attribute")
#                attributes_table = attribute_child.attrib
#                assert "name" in attributes_table
#                name = attributes_table["name"]
#                #assert "type" in attributes_table  # Not present for an enumeration
#                type = attributes_table["type"]
#                assert type in ("xs:boolean",
#                  "xs:enumeration", "xs:float", "xs:integer", "xs:string")
#                optional = True
#                if "use" in attributes_table:
#                    use = attributes_table["use"]
#                    assert use == "required"
#                    optional = False
#                default = None
#                if "default" in attributes_table:
#                    default = attributes_table["default"]
#                # print("default={0}".format(default))
#
#                annotation_children = list(attribute_child)
#                assert len(annotation_children) == 1
#                annotation_child = annotation_children[0]
#                assert isinstance(annotation_child, etree._Element)
#
#                # Iterate over *documentation_children* and build of a list of *Docuemtation*
#                # objects in *documentations*:
#                documentations = list()
#                documentations_children = list(annotation_child)
#                for documentation_child in documentations_children:
#                    # Verify that that *documentation_child* has exactly on attribute named `lang`:
#                    assert isinstance(documentation_child, etree._Element)
#                    attributes_table = documentation_child.attrib
#                    assert len(attributes_table) == 1
#                    # print("attributes_table=", attributes_table)
#                    key = xml_name_space + "lang"
#                    assert key in attributes_table
#
#                    # Extract the *language* attribute value:
#                    language = attributes_table[key]
#
#                    # Grab the *text* from *documentation_children*:
#                    text = documentation_child.text.strip()
#                    xml_lines = [line.strip().replace("<", "&lt;") for line in text.split('\n')]
#
#                    # Create the *documentation* and append to *documentations*:
#                    documentation = Documentation(language, xml_lines)
#                    documentations.append(documentation)
#
#                # Create *attribute* and append to *attributes*:
#                enumerates = list()
#                attribute = Attribute(name, type, default, optional, documentations, enumerates)
#                attributes.append(attribute)
#
#        # Construct the final *schema* (i.e. *self*):
#        schema = self
#        schema.target_name_space = target_name_space
#        schema.attributes = attributes
#
#    def __eq__(self, schema2):
#        assert isinstance(schema2, Schema)
#        schema1 = self
#        attributes1 = schema1.attributes
#        attributes2 = schema2.attributes
#        is_equal = len(attributes1) == len(attributes2)
#        if is_equal:
#            for index, attribute1 in enumerate(attributes1):
#                attribute2 = attributes2[index]
#                if attribute1 != attribute2:
#                    is_equal = False
#                    break
#        return is_equal
#
#    def copy(self):
#        schema = self
#        new_schema = Schema()
#        new_schema.target_name_space = schema.target_name_space
#        new_schema_attributes = new_schema.attributes
#        assert len(new_schema_attributes) == 0
#        for attribute in schema.attributes:
#            new_schema_attributes.append(attribute.copy())
#        return new_schema
#
#    def to_string(self):
#        schema = self
#        attributes = schema.attributes
#        target_name_space = schema.target_name_space
#
#        xml_lines = list()
#        xml_lines.append('<?xml version="1.0"?>')
#        xml_lines.append('<xs:schema')
#        xml_lines.append(' targetNamespace="{0}"'.format(target_name_space))
#        xml_lines.append(' xmlns:xs="{0}"'.format("http://www.w3.org/2001/XMLSchema"))
#        xml_lines.append(' xmlns="{0}">'.
#          format("file://home/wayne/public_html/projects/manufactory_project"))
#        xml_lines.append('  <xs:element name="{0}">'.format("drillBits"))
#        xml_lines.append('    <xs:complexType>')
#        xml_lines.append('      <xs:sequence>')
#        xml_lines.append('        <xs:element name="{0}">'.format("drillBit"))
#        xml_lines.append('          <xs:complexType>')
#
#        for attribute in attributes:
#            # Unpack the values from *attribute*:
#            name = attribute.name
#            type = attribute.type
#            default = attribute.default
#            optional = attribute.optional
#            documentations = attribute.documentations
#
#            xml_lines.append('            <xs:attribute')
#            xml_lines.append('             name="{0}"'.format(name))
#            if isinstance(default, str):
#                xml_lines.append('             default="{0}"'.format(default))
#            if not optional:
#                xml_lines.append('             use="required"')
#            xml_lines.append('             type="{0}">'.format(type))
#            xml_lines.append('              <xs:annotation>')
#            for document in documentations:
#                language = document.language
#                documentation_xml_lines = document.xml_lines
#                xml_lines.append('                <xs:documentation xml:lang="{0}">'.
#                  format(language))
#                for documentation_line in documentation_xml_lines:
#                    xml_lines.append('                  {0}'.format(documentation_line))
#                xml_lines.append('                </xs:documentation>')
#            xml_lines.append('              </xs:annotation>')
#            xml_lines.append('            </xs:attribute>')
#        xml_lines.append('          </xs:complexType>')
#        xml_lines.append('        </xs:element>')
#        xml_lines.append('      </xs:sequence>')
#        xml_lines.append('    </xs:complexType>')
#        xml_lines.append('  </xs:element>')
#        xml_lines.append('</xs:schema>')
#
#        xml_lines.append("")
#        text = '\n'.join(xml_lines)
#        return text
#
# class CheckableComboBox(QComboBox):
#    # once there is a checkState set, it is rendered
#    # here we assume default Unchecked
#    def addItem(self, item):
#        super(CheckableComboBox, self).addItem(item)
#        item = self.model().item(self.count()-1,0)
#        item.setFlags(QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
#        item.setCheckState(QtCore.Qt.Unchecked)
#
#    def itemChecked(self, index):
#        item = self.model().item(i,0)
#        return item.checkState() == QtCore.Qt.Checked

    # Old Stuff....

    # Read the contents of the file named *xsd_file_name* into *xsd_file_text*:
    # xsd_file_name = xsd_file_names[0]
    # with open(xsd_file_name) as xsd_file:
    #     xsd_file_text = xsd_file.read()
    #
    # Parse *xsd_file_text* into *xsd_schema*:
    # xsd_schema = xmlschema.XMLSchema(xsd_file_text)

    # Iterate across all of the *xml_file_names* and verify that they are valid:
    # for xml_file_name in xml_file_names:
    #     with open(xml_file_name) as xml_file:
    #         xml_file_text = xml_file.read()
    #     xsd_schema.validate(xml_file_text)

    # Parse the *xsd_file_text* into *xsd_root*:
    # xsd_root = etree.fromstring(xsd_file_text)
    # show(xsd_root, "")

    # schema = Schema(xsd_root)
    # assert schema == schema

    # For debugging:
    # schema_text = schema.to_string()
    # with open(os.path.join(order_root, "drills.xsd"), "w") as schema_file:
    #     schema_file.write(schema_text)

    # Now run the *tables_editor* graphical user interface (GUI):
    # tables_editor = TablesEditor(xsd_root, schema)
    # tables_editor.run()

# https://stackoverflow.com/questions/5226091/checkboxes-in-a-combobox-using-pyqt?rq=1
# https://stackoverflow.com/questions/24961383/how-to-see-the-value-of-pyside-qtcore-qt-itemflag
# /usr/local/lib/python3.6/dist-packages/PySide2/examples/widgets/itemviews/stardelegate
# https://stackoverflow.com/questions/8422760/combobox-of-checkboxes


# Qt Designer application Notes:
# * Use grid layouts for everything.  This easier said than done since the designer
#   user interface is kind of clunky:
#   1. Just drop one or more widgets into the area.
#   2. Using the tree view, select the widgets using left mouse button and [Control] key.
#   3. Using right mouse button, get a drop-down, and set the grid layout.
#   4. You are not done until all the widgets with layouts are grids with no red circle
#      that indicate that now layout is active.
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
# [Python Tracing Decorator](https://cscheid.net/2017/12/11/minimal-tracing-decorator-python-3.html)
if __name__ == "__main__":
    main()
