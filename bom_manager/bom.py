#!/usr/bin/env python3

# <------------------------------------------- 100 characters -----------------------------------> #

# Coding standards:
#
# * General:
#   * Python 3.6 or greater is used.
#   * The PEP 8 coding standards are generally adhered to.
#   * All code and docmenation lines must be on lines of 100 characters or less.  No exceptions!
#   * Indentation levels are multiples of 4 spaces.
#   * Use `flake8 --max-line-length=100 PROGRAM.py` to check for issues.
# * Class/Function standards:
#   * Classes:
#     * Classes are named in CamelCase as per Python recommendation.
#     * Classes are listed alphabetically with sub-classes are listed alphabetically
#       immediately after their base class definition.
#     * Each Class definition has a comment of the form `# ClassName:` immediately before the
#       class defitinion.
#   * Methods:GG
#     * All methods are in lower case.  If mutliple words, the words are separated by underscores.
#       The words are order as Adjectives, Noun, Adverbs, Verb.  Thus, *xml_file_load* instead of
#       *load_xml_file*.
#     * All methods are listed alphabetically, where an underscore is treated as a space.
#     * All methods check their argument types (i.e. no duck typing!!!)
#     * Inside a method, *self* is almost always replaced with more descriptive variable name.
#     * To aid debugging, many functions have an optional *tracing* argument of the form
#       `tracing=None`.  If this argument is `str`, the tracing information is enabled.
#   * Functions:
#     * The top-level main() function occurs first.
#     * The standards for top-level fuctions are adhered to.
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
#
# Install Notes:
#
#       sudo apt-get install xclip xsel # More here ...
#
# Tasks:
# * Decode Digi-Key parametric search URL's.
# * Start providing ordering operations.
# * Reorder tables/parameters/enumerations/searches.
# * Footprint hooks
# * Better parametric search
#
# # bom_manager
#
# ## Overview:
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
#from bs4 import BeautifulSoup     # HTML/XML data structucure searching
import bs4
import copy                       # Is this used any more?
import csv
from currency_converter import CurrencyConverter         # Currency converter
from functools import partial
import fnmatch                    # File Name Matching
import glob                       # Unix/Linux style command line file name pattern matching
import io                         # I/O stuff
import lxml.etree as etree
import pickle                     # Python data structure pickle/unpickle
import pkg_resources              # Used to find plug-ins.
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import (QApplication, QComboBox, QLineEdit, QMainWindow,
                               QPlainTextEdit, QPushButton,
                               QTableWidget, QTableWidgetItem, QWidget)  # QTreeView
from PySide2.QtCore import (QAbstractItemModel, QFile, QItemSelectionModel,
                            QModelIndex, Qt)
from PySide2.QtGui import (QClipboard,)
import pkgutil
import os
import re                         # Regular expressions
import requests                   # HTML Requests
import sexpdata                   # (LISP) S_EXpresson Data
from sexpdata import Symbol       # (LISP) S-EXpression Symbol
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

def main():
    # table_file_name = "drills_table.xml"
    # assert os.path.isfile(table_file_name)
    # with open(table_file_name) as table_read_file:
    #    table_input_text = table_read_file.read()
    # table_tree = etree.fromstring(table_input_text)
    # table = Table(file_name=table_file_name, table_tree=table_tree)
    # table_write_text = table.to_xml_string()
    # with open(os.path.join(order_root, table_file_name), "w") as table_write_file:
    #    table_write_file.write(table_write_text)

    # Partition the command line *arguments* into *xml_file_names* and *xsd_file_names*:
    # arguments = sys.argv[1:]
    # xml_file_names = list()
    # xsd_file_names = list()
    # for argument in arguments:
    #    if argument.endswith(".xml"):
    #        xml_file_names.append(argument)
    #    elif argument.endswith(".xsd"):
    #        xsd_file_names.append(argument)
    #    else:
    #        assert "File name '{0}' does not have a suffix of '.xml' or '.xsd'"
    #
    # # Verify that we have one '.xsd' file and and one or more '.xml' files:
    # assert len(xsd_file_names) < 2, "Too many '.xsd` files specified"
    # assert len(xsd_file_names) > 0, "No '.xsd' file specified"
    # assert len(xml_file_names) > 0, "No '.xml' file specified"

    tracing = None
    tracing = ""
    next_tracing = None if tracing is None else tracing + " "
    if tracing is not None:
        print(f"{tracing}=>main()")

    Encode.from_file_name
    Encode.test()
    title = "TEST_POINT;M1X1"
    # print(f"title='{title}' => encoded_title='{Encode.to_file_name(title)}'")

    # Set up command line *parser* and parse it into *parsed_arguments* dict:
    parser = argparse.ArgumentParser(description="Bill of Materials (BOM) Manager.")
    parser.add_argument("-n", "--net", action="append", default=[],
                        help="KiCAD .net file. Preceed with 'NUMBER:' to increase count. ")
    parser.add_argument("-s", "--search", default="searches",
                        help="BOM Manager Searches Directory.")
    parser.add_argument("-o", "--order", default=os.path.join(os.getcwd(), "order"),
                        help="Order Information Directory")
    parsed_arguments = vars(parser.parse_args())
    if tracing is not None:
        print(f"{tracing}Arguments Parsed")

    # database = Database()
    order_root = parsed_arguments["order"]
    order = Order(order_root)
    if tracing is not None:
        print(f"{tracing}order_created")

    # Deal with *net_file_names* from *parsed_arguments*:
    net_file_names = parsed_arguments["net"]
    for net_file_name in net_file_names:
        if net_file_name.endswith(".net"):
            # We have a `.net` file name:
            colon_index = net_file_name.find(':')
            # print(f"colon_index={colon_index}")
            count = 1
            if colon_index >= 0:
                count = int(net_file_name[:colon_index])
                net_file_name = net_file_name[colon_index:]
            # print(f"count={count}")
            assert os.path.isfile(net_file_name), f"'{net_file_name}' does not exist."
            paths = os.path.split(net_file_name)
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
            order.project_create(name, revision_letter, net_file_name, count, tracing=tracing)
        else:
            print(f"Ignoring .net '{net_file_name}' does not with '.net` suffix.")
    if tracing is not None:
        print(f"{tracing}nets processed")

    collection_directories = list()    

    tables = list()
    if False:
        # Read in each *table_file_name* in *arguments* and append result to *tables*:
        #for table_file_name in arguments:
        if False:
            # Verify that *table_file_name* exists and has a `.xml` suffix:
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
    # searches_path = arguments[0] if arguments else "searches"
    tracing = None
    tracing = ""
    # print(f"searches_root='{searches_root}'")
    tables_editor = TablesEditor(tables,
                                 collection_directories, searches_root, order, tracing=tracing)

    # Start up the GUI:
    tables_editor.run()

    # When we get here, *tables_editor* has stopped running and we can return.
    if tracing is not None:
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
    assert isinstance(se, list)
    assert isinstance(base_name, str)
    assert isinstance(key_name, str)

    # Do some sanity checking:
    size = len(se)
    assert size > 0
    assert se[0] == Symbol(base_name)

    result = None
    key_symbol = Symbol(key_name)
    for index in range(1, size):
        sub_se = se[index]
        if len(sub_se) > 0 and sub_se[0] == key_symbol:
            result = sub_se
            break
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

    # ActualPart.findchips_scrape():
    def findchips_scrape(self, tracing=None):
        """ Find the *VendorParts* associated with
            *actual_part* scraped from the findchips.com web page.
        """
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        actual_part = self
        if tracing is not None:
            print(f"{tracing}=>ActualPart.findchips('{actual_part.manufacturer_part_name}')")

        # Grab some values from *actual_part* (i.e. *self*):
        manufacturer_name = actual_part.manufacturer_name
        manufacturer_part_name = actual_part.manufacturer_part_name
        original_manufacturer_part_name = manufacturer_part_name

        # Trace every time we send a message to findchips:
        print(f"Find '{manufacturer_name}:{manufacturer_part_name}'")

        # Generate *url_part_name* which is a %XX encoded version of
        # *manufactuerer_part_name*:
        ok = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" + "0123456789" + "-.:;" + \
             "abcdefghijklmnopqrstuvwxyz"
        characters = []
        for character in manufacturer_part_name:
            if ok.find(character) >= 0:
                # Let this *character* through unchanged:
                characters.append(character)
            else:
                # Convert *character* to %XX:
                characters.append(format("%{0:02x}".format(ord(character))))
        url_part_name = "".join(characters)

        # Grab a page of information about *part_name* using *findchips_url*:
        findchips_url = "http://www.findchips.com/search/" + url_part_name
        if tracing is not None:
            print(f"{tracing}findchips_url='findchips_url'")
        findchips_response = requests.get(findchips_url)
        findchips_text = findchips_response.text.encode("ascii", "ignore")

        # Parse the *findchips_text* into *find_chips_tree*:
        findchips_tree = bs4.BeautifulSoup(findchips_text, "html.parser")

        # if trace:
        #    print(findchips_tree.prettify())

        # We use regular expressions to strip out unnecessary characters
        # in numbrers:
        digits_only_re = re.compile("\\D")

        # Result is returned in *vendor_parts*:
        vendor_parts = []

        # Currently, there is a <div class="distributor_results"> tag for
        # each distributor:
        for distributor_tree in findchips_tree.find_all("div", class_="distributor-results"):
            # if trace:
            #        print("**************************************************")
            #        print(distributor_tree.prettify())

            # The vendor name is burried in:
            #   <h3 class="distributor-title"><a ...>vendor name</a></h3>:
            vendor_name = None
            for h3_tree in distributor_tree.find_all(
              "h3", class_="distributor-title"):
                # print("&&&&&&&&&&&&&&&&&&&&&&&")
                # print(h3_tree.prettify())
                for a_tree in h3_tree.find_all("a"):
                    vendor_name = a_tree.get_text().strip()

            # If we can not extact a valid *vendor_name* there is no
            # point in continuing to work on this *distributor_tree*:
            if vendor_name is None:
                continue

            # This code is in the *VendorPart* initialize now:
            # Strip some boring stuff off the end of *vendor_name*:
            # vendor_name = text_filter(vendor_name, str.isprintable)
            # if vendor_name.endswith("Authorized Distributor"):
            #    # Remove "Authorized Distributor" from end
            #    # of *vendor_name*:
            #    if vendor_name.endswith("Authorized Distributor"):
            #        vendor_name = vendor_name[:-22].strip(" ")
            #    if vendor_name.endswith("Member"):
            #        # Remove "Member" from end of *vendor_name*:
            #        vendor_name = vendor_name[:-6].strip(" ")
            #    if vendor_name.endswith("ECIA (NEDA)"):
            #        # Remove "ECIA (NEDA)" from end of *vendor_name*:
            #        vendor_name = vendor_name[:-11].strip(" ")

            # Extract *currency* from *distributor_tree*:
            currency = "USD"
            try:
                currency = distributor_tree["data-currencycode"]
            except ValueError:
                pass

            # All of the remaining information is found in <table>...</table>:
            for table_tree in distributor_tree.find_all("table"):
                # print(table_tree.prettify())

                # There two rows per table.  The first row has the headings
                # and the second row has the data.  The one with the data
                # has a class of "row" -- <row clase="row"...> ... </row>:
                for row_tree in table_tree.find_all("tr", class_="row"):
                    # Now we grab the *vendor_part_name*.  Some vendors
                    # (like Arrow) use the *manufacturer_part_name* as their
                    # *vendor_part_name*.  The data is in:
                    #     <span class="additional-value"> ... </span>:
                    vendor_part_name = manufacturer_part_name
                    for span1_tree in row_tree.find_all(
                      "span", class_="td-desc-distributor"):
                        # print(span1_tree.prettify())
                        for span2_tree in span1_tree.find_all(
                          "span", class_="additional-value"):
                            # Found it; grab it, encode it, and strip it:
                            vendor_part_name = span2_tree.get_text()

                    # The *stock* count is found as:
                    #    <td class="td-stock">stock</td>
                    stock = 0
                    stock_tree = row_tree.find("td", class_="td-stock")
                    if stock_tree is not None:
                        # Strip out commas, space, etc.:
                        stock_text = \
                          digits_only_re.sub("", stock_tree.get_text())
                        # Some sites do not report stock, and leave them
                        # empty.  We just leave *stock* as zero in this case:
                        if len(stock_text) != 0:
                            stock = min(int(stock_text), 1000000)

                    # The *manufacturer_name* is found as:
                    #    <td class="td-mfg"><span>manufacturer_name</span></td>
                    manufacturer_name = ""
                    for mfg_name_tree in row_tree.find_all(
                      "td", class_="td-mfg"):
                        for span_tree in mfg_name_tree.find_all("span"):
                            # Found it; grab it, encode it, and strip it:
                            manufacturer_name = span_tree.get_text().strip()

                    # The *manufacturer_part_name* is found as:
                    #    <td class="td_part"><a ...>mfg_part_name</a></td>
                    manufacturer_part_name = ""
                    for mfg_part_tree in row_tree.find_all(
                      "td", class_="td-part"):
                        for a_tree in mfg_part_tree.find_all("a"):
                            # Found it; grab it, encode it, and strip it:
                            manufacturer_part_name = a_tree.get_text()

                    # The price breaks are encoded in a <ul> tree as follows:
                    #    <td class="td_price">
                    #       <ul>
                    #          <li>
                    #            <span class="label">quantity</span>
                    #            <span class="value">price</span>
                    #          </li>
                    #          ...
                    #       </ul>
                    #    </td>
                    price_breaks = []
                    price_list_tree = row_tree.find("td", class_="td-price")
                    if price_list_tree is not None:
                        for li_tree in price_list_tree.find_all("li"):
                            quantity_tree = li_tree.find("span", class_="label")
                            price_tree = li_tree.find("span", class_="value")
                            if quantity_tree is not None and price_tree is not None:
                                # We extract *quantity*:
                                quantity_text = digits_only_re.sub("", quantity_tree.get_text())
                                quantity = 1
                                if quantity_text != "":
                                    quantity = int(quantity_text)

                                # Extract *price* using only digits and '.':
                                price_text = ""
                                for character in price_tree.get_text():
                                    if character.isdigit() or character == ".":
                                        price_text += character
                                price = float(price_text)

                                # Look up the *exchange_rate* for *currency*:
                                exchange_rates = ActualPart.ACTUAL_PART_EXCHANGE_RATES
                                if currency in exchange_rates:
                                    exchange_rate = exchange_rates[currency]
                                else:
                                    converter = CurrencyConverter()
                                    exchange_rate = converter.convert(1.0, currency, "USD")
                                    exchange_rates[currency] = exchange_rate

                                # Sometimes we get a bogus price of 0.0 and
                                # we just need to ignore the whole record:
                                if price > 0.0:
                                    price_break = PriceBreak(
                                      quantity, price * exchange_rate)
                                    price_breaks.append(price_break)

                    # Now if we have an exact match on the *manufacturer_name*
                    # we can construct the *vendor_part* and append it to
                    # *vendor_parts*:
                    if original_manufacturer_part_name == manufacturer_part_name:
                        now = int(time.time())
                        vendor_part = VendorPart(actual_part, vendor_name, vendor_part_name,
                                                 stock, price_breaks, now)
                        vendor_parts.append(vendor_part)

                        # Print stuff out if *trace* in enabled:
                        if tracing is not None:
                            # Print everything out:
                            print(f"{tracing}vendor_name='{vendor_name}'")
                            print(f"{tracing}vendor_part_name='{vendor_part_name}'")
                            print(f"{tracing}manufacturer_part_name='{manufacturer_part_name}'")
                            print(f"{tracing}manufacturer_name='{manufacturer_name}'")
                            print(f"{tracing}stock={stock}")
                            price_breaks.sort()
                            for price_break in price_breaks:
                                print(f"{tracing}{0}: {1:.6f} ({2})".
                                      format(price_break.quantity, price_break.price, currency))

        # For debugging, let the user now that we are looking for a
        # part and not finding it at all:
        if len(vendor_parts) == 0:
            print("**********Find '{0}:{1}': {2} matches".format(
                  actual_part.manufacturer_name,
                  actual_part.manufacturer_part_name, len(vendor_parts)))

        # Wrap up any requested *tracing* and return the *vendor_parts*:
        if tracing is not None:
            print(f"{tracing}=>ActualPart.findchips('{actual_part.manufacturer_part_name}')=>[...]")
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
    def vendor_parts_restore(self, order, tracing=None):
        # Verify argument types:
        assert isinstance(order, Order)
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}ActualPart.vendor_parts_restore(*)")

        actual_part = self
        result = False
        order_root = order.root
        vendor_searches_root = order.vendor_searches_root
        xml_base_name = actual_part.name + ".xml"
        xml_file_name = os.path.join(vendor_searches_root, xml_base_name)
        

        # Wrap up any requested *tracing*:
        if tracing is not None:
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
    def __init__(self, name, tracing=None):
        # Verify argument types:
        if tracing is not None:
            print(f"{tracing}=>Cad.__init__('{name}')")

        # Wrap up any argument types:
        if tracing is not None:
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
                 comment_set_function, is_active_function, tracing=None, **widgets):
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
        assert isinstance(tracing, str) or tracing is None
        widget_callbacks = ComboEdit.WIDGET_CALLBACKS
        widget_names = list(widget_callbacks)
        for widget_name, widget in widgets.items():
            assert widget_name in widget_names, (
              "Invalid widget name '{0}'".format(widget_name))
            assert isinstance(widget, QWidget), (
              "'{0}' is not a QWidget {1}".format(widget_name, widget))

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{0}=>ComboEdit.__init__(*, {1}, ...)".format(tracing, name))

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
        combo_edit.current_item_set(items[0] if len(items) > 0 else None, tracing=next_tracing)

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
        if tracing is not None:
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
            next_tracing = " " if trace_signals else None
            if trace_signals:
                print("=>ComboEdit.combo_box_changed('{0}', '{1}')".
                      format(combo_edit.name, new_name))

                # Grab *attributes* (and compute *attributes_size*) from *combo_edit* (i.e. *self*):
                items = combo_edit.items
                for index, item in enumerate(items):
                    if item.name == new_name:
                        # We have found the new *current_item*:
                        print("  items[{0}] '{1}'".format(index, item.name))
                        combo_edit.current_item_set(item, tracing=next_tracing)
                        break

            # Update the the GUI:
            tables_editor.update(tracing=next_tracing)

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
            next_tracing = " " if trace_signals else None
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
                combo_edit.comment_set_function(item, actual_text, position, tracing=next_tracing)

            # Force the GUI to be updated:
            tables_editor.update(tracing=next_tracing)

            # Wrap up any signal tracing:
            if trace_signals:
                print(" <=ComboEditor.comment_text_changed():{0}\n".format(cursor.position()))
            tables_editor.in_signal = False

    # ComboEdit.current_item_get():
    def current_item_get(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested tracing:
        combo_edit = self
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{0}=>ComboEdit.current_item_get".format(tracing, combo_edit.name))

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
            combo_edit.current_item_set(new_current_item, tracing=next_tracing)

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print("{0}=>ComboEdit.current_item_get".format(tracing, combo_edit.name))
        return new_current_item

    # ComboEdit.current_item_set():
    def current_item_set(self, current_item, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        combo_edit = self
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{0}=>ComboEdit.current_item_set('{1}', *)".format(tracing, combo_edit.name))

        combo_edit.current_item = current_item
        combo_edit.current_item_set_function(current_item, tracing=next_tracing)

        # Wrap up any requested tracing:
        if tracing is not None:
            print("{0}<=ComboEdit.current_item_set('{1}', *)".format(tracing, combo_edit.name))

    # ComboEdit.delete_button_clicked():
    def delete_button_clicked(self):
        # Perform any requested tracing from *combo_edit* (i.e. *self*):
        combo_edit = self
        tables_editor = combo_edit.tables_editor
        trace_signals = tables_editor.trace_signals
        next_tracing = " " if trace_signals else None
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
                combo_edit.current_item_set(current_item, tracing=next_tracing)
                break

        # Update the GUI:
        tables_editor.update(tracing=next_tracing)

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
        next_tracing = " " if trace_signals else None
        if trace_signals:
            print("=>ComboEdit.first_button_clicked('{0}')".format(combo_edit.name))

        # If possible, select the *first_item*:
        tables_editor.in_signal = True
        items = combo_edit.items
        items_size = len(items)
        if items_size > 0:
            first_item = items[0]
            combo_edit.current_item_set(first_item, tracing=next_tracing)

        # Update the user interface:
        tables_editor.update(tracing=next_tracing)

        # Wrap up any requested tracing:
        if trace_signals:
            print("<=ComboEdit.first_button_clicked('{0})\n".format(combo_edit.name))
        tables_editor.in_signal = False

    # ComboEdit.gui_update():
    def gui_update(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing* of *combo_edit* (i.e. *self*):
        combo_edit = self
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{0}=>ComboEdit.gui_update('{1}')".format(tracing, combo_edit.name))

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
        # if tracing is not None:
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
            # if tracing is not None:
            #    print("{0}[{1}]: '{2}".format(tracing, index,
            #      "--" if item is None else item.name))
            if item is current_item:
                combo_box.setCurrentIndex(index)
                current_item_index = index
                if tracing is not None:
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
              current_item, tracing=next_tracing)

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
        if tracing is not None:
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
        next_tracing = " " if trace_signals else None
        if trace_signals:
            print("=>ComboEdit.last_button_clicked('{0}')".format(combo_edit.name))

        # If possible select the *last_item*:
        tables_editor.in_signal = True
        items = combo_edit.items
        items_size = len(items)
        if items_size > 0:
            last_item = items[-1]
            combo_edit.current_item_set(last_item, tracing=next_tracing)

        # Update the user interface:
        tables_editor.update(tracing=next_tracing)

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
            next_tracing = " " if trace_signals else None
            if trace_signals:
                print("=>ComboEditor.line_edit_changed('{0}')".format(text))

            # Make sure that the *combo_edit* *is_active*:
            is_active = combo_edit.is_active_function()
            if not is_active:
                # We are not active, so do not let the user type anything in:
                line_edit = combo_edit.line_edit
                line_edit.setText("")  # Erase whatever was just typed in!

            # Now just update *combo_edit*:
            combo_edit.gui_update(tracing=next_tracing)

            # Wrap up any requested signal tracing:
            if trace_signals:
                print("<=ComboEditor.line_edit_changed('{0}')\n".format(text))
            tables_editor.in_signal = False

    # ComboEdit.item_append():
    def item_append(self, new_item, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{0}=>ComboEdit.item_append(*)".format(tracing))

        # Append *item* to *items* and make it current for *combo_edit* (i.e. *self*):
        combo_edit = self
        items = combo_edit.items
        items.append(new_item)
        combo_edit.current_item_set(new_item, tracing=next_tracing)

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print("{0}<=ComboEdit.item_append(*)".format(tracing))

    # ComboEdit.new_button_clicked():
    def new_button_clicked(self):
        # Perform any tracing requested by *combo_edit* (i.e. *self*):
        combo_edit = self
        tables_editor = combo_edit.tables_editor
        trace_signals = tables_editor.trace_signals
        next_tracing = " " if trace_signals else None
        if trace_signals:
            print("=>ComboEdit.new_button_clicked('{0}')".format(combo_edit.name))

        # Grab some values from *combo_edit*:
        tables_editor.in_signal = True
        items = combo_edit.items
        line_edit = combo_edit.line_edit
        new_item_function = combo_edit.new_item_function
        print("items.id=0x{0:x}".format(id(items)))

        # Create a *new_item* and append it to *items*:
        new_item_name = line_edit.text()
        # print("new_item_name='{0}'".format(new_item_name))
        new_item = new_item_function(new_item_name, tracing=next_tracing)
        combo_edit.item_append(new_item)

        # Update the GUI:
        tables_editor.update(tracing=next_tracing)

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
        next_tracing = " " if trace_signals else None
        if trace_signals:
            print("=>ComboEdit.next_button_clicked('{0}')".format(combo_edit.name))

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
        combo_edit.current_item_set(current_item, tracing=next_tracing)

        # Update the GUI:
        tables_editor.update(tracing=next_tracing)

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
            next_tracing = " " if trace_signals else None
            if trace_signals:
                print("=>ComboEdit.position_changed('{0}')".format(combo_edit.name))

            # Grab the *actual_text* and *position* from the *comment_text* widget and stuff
            # both into the comment field of *item*:
            item = combo_edit.current_item_get()
            comment_text = combo_edit.comment_text
            cursor = comment_text.textCursor()
            position = cursor.position()
            actual_text = comment_text.toPlainText()
            combo_edit.comment_set_function(item, actual_text, position, tracing=next_tracing)

            # Wrap up any signal tracing:
            if trace_signals:
                # print("position={0}".format(position))
                print("<=ComboEdit.position_changed('{0}')\n".format(combo_edit.name))
            tables_editor.in_signal = False

    # ComboEdit.previous_button_clicked():
    def previous_button_clicked(self):
        # Perform any tracing requested by *combo_edit* (i.e. *self*):
        combo_edit = self
        tables_editor = combo_edit.tables_editor
        trace_signals = tables_editor.trace_signals
        next_tracing = " " if trace_signals else None
        if trace_signals:
            print("=>ComboEdit.previous_button_clicked('{0}')".format(combo_edit.name))

        # ...
        tables_editor.in_signal = True
        items = combo_edit.items
        current_item = combo_edit.current_item_get()
        for index, item in enumerate(items):
            if item == current_item:
                if index > 0:
                    current_item = items[index - 1]
                break
        combo_edit.current_item_set(current_item, tracing=next_tracing)

        # Update the GUI:
        tables_editor.update(tracing=next_tracing)

        # Wrap up any requested tracing:
        if trace_signals:
            print("<=ComboEdit.previous_button_clicked('{0}')\n".format(combo_edit.name))
        tables_editor.in_signal = False

    # ComboEdit.rename_button_clicked():
    def rename_button_clicked(self):
        # Perform any tracing requested by *combo_edit* (i.e. *self*):
        combo_edit = self
        tables_editor = combo_edit.tables_editor
        trace_signals = tables_editor.trace_signals
        next_tracing = " " if trace_signals else None
        if trace_signals:
            print("=>ComboEdit.rename_button_clicked('{0}')".format(combo_edit.name))

        tables_editor.in_signal = True
        combo_edit = self
        line_edit = combo_edit.line_edit
        new_item_name = line_edit.text()

        current_item = combo_edit.current_item_get()
        if current_item is not None:
            current_item.name = new_item_name

        # Update the GUI:
        tables_editor.update(tracing=next_tracing)

        # Wrap up any requested tracing:
        if trace_signals:
            print("=>ComboEdit.rename_button_clicked('{0}')\n".format(combo_edit.name))
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
    def __init__(self, name, tracing=None):
        # Verify argument types:
        if tracing is not None:
            print(f"{tracing}=>Panda.__init__('{name}')")

        # Wrap up any argument types:
        if tracing is not None:
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


# Database:
class Database:
    # Database of *ProjectParts*:

    # Database.__init__():
    def __init__(self):
        """ *Database*: Initialize *self* to be a database of
            *project_part*'s. """

        self.euro_to_dollar_exchange_rate = self.exchange_rate("EUR", "USD")
        self.pound_to_dollar_exchange_rate = self.exchange_rate("GBP", "USD")

        bom_parts_file_name = "bom_parts.pkl"

        # Initialize *vendor_minimums* to contain minimum order amounts for
        # vendors that have a serious mininum:
        vendor_minimums = {}
        vendor_minimums["Verical"] = 100.00
        vendor_minimums["Chip1Stop"] = 100.00

        # Initialize "vendor_priorities" to contain specify preferred
        # vendor priority.  Higher is more preferred.
        vendor_priorities = {}

        # Priorities 0-9 are for vendors with significant minimum
        # order amounts or trans-oceanic shipping costs:
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

        # Initialize the various tables:
        database = self
        database.actual_parts = {}  # Key:(manufacturer_name, manufacturer_part_name)
        database.bom_parts_file_name = bom_parts_file_name
        database.footprints = {}  # Key: "footprint_name"
        database.project_parts = {}   # Key: "part_name;footprint:comment"
        database.vendor_minimums = vendor_minimums
        database.vendor_parts_cache = {}  # Key:(actual_key)
        database.vendor_priorities = vendor_priorities
        database.vendor_priority = 10

        vendor_parts_cache = database.vendor_parts_cache
        # Read in any previously created *vendor_parts*:
        if os.path.isfile(bom_parts_file_name):
            # print("Start reading BOM parts file: '{0}'".
            #  format(bom_parts_file_name))

            # Read in picked *vendor_parts* from *bom_file_name*:
            bom_pickle_file = open(bom_parts_file_name, "rb")
            pickled_vendor_parts_cache = pickle.load(bom_pickle_file)
            bom_pickle_file.close()

            # Flush out old (stale) vendor parts from *pickled_vendor_parts*:
            now = time.time()
            old = now - 2.0 * 24.0 * 60.0 * 60.0
            for actual_key in pickled_vendor_parts_cache.keys():
                vendor_parts = pickled_vendor_parts_cache[actual_key]
                for vendor_part in vendor_parts:
                    assert isinstance(vendor_part, VendorPart)
                    if vendor_part.timestamp < old:
                        del vendor_parts[vendor_part.vendor_key]
                if len(vendor_parts) > 0:
                    vendor_parts_cache[actual_key] = vendor_parts

            with open(os.path.join(order_root, "database.dmp"), "w") as dump_stream:
                database.dump(dump_stream)

        # Now here is where we initialize the database:

        # Batteries and Holders:
        self.choice_part("BAT_HOLDER;2032_THRU", "BU2032-1", "",
                         "HOLDER COIN CELL 2032 PC PIN").actual_part(
          "MPD", "BU2032-1-HD-G")

        # Boxes:
        self.choice_part("JB-3955;102Lx152Wx152H", "102Lx152Wx152H", "",
                         "BOX STEEL GRAY 102Lx152Wx152H").actual_part(
                         "Bud Industries", "JB-3955",
                         [("Digi-Key", "377-1838-ND",
                          "1/12.35 6/10.25000 100/9.25")])

        # Buttons:

        # Change KiCAD Footprint name -- it is totally wrong:
        self.choice_part("BUTTON;6X6MM", "TE_Connectivity_2-1437565-9",
                         "TE_Connectivity_2-1437565-9",
                         "SWITCH TACTILE SPST-NO 0.05A 12V").actual_part(
          "TE", "2-1437565-9").actual_part(
          "C&K", "PTS645SH50SMTR92 LFS").actual_part(
          "C&K", "PTS645SK50SMTR92 LFS").actual_part(
          "TE", "FSM4JSMATR").actual_part(
          "C&K", "PTS645SM43SMTR92 LFS").actual_part(
          "C&K", "PTS645SL50SMTR92 LFS").actual_part(
          "TE", "FSM6JSMATR").actual_part(
          "TE", "1571563-4").actual_part(
          "TE", "FSM2JSMLTR").actual_part(
          "TE", "FSM1LPATR").actual_part(
          "C&K", "RS-014R05B1-SMA10 RT")
        self.alias_part("6MM_4LED_BUTTON;6X6MM",
                        ["BUTTON;6X6MM"], "TE_Connectivity_2-1437565-9",)

        # Capacitors:

        self.choice_part("6pF;1608", "CAPC1608X90N", "",
                         "CAP CER 6PF 50V+ NP0 0603", rotation=90.0).actual_part(
          "TDK", "C1608CH2A060D080AA").actual_part(
          "KEMET Corporation", "CBR06C609BAGAC").actual_part(
          "Yageo", "CC0603DRNPO9BN6R0")
        self.choice_part("18pF;1608", "CAPC1608X90N", "",
                         "CAP CER 18PF 25V+ 10% SMD 0603", rotation=90.0).actual_part(
          "Kamet", "C0603C180J5GACTU", [
           ("Digi-Key", "399-1052-1-ND",
            "1/.10 10/.034 50/.0182 100/.0154 250/.0126")]).actual_part(
          "Samsung", "CL10C180JB8NNNC").actual_part(
          "TDK", "C1608C0G1H180J080AA").actual_part(
          "Samsung", "CL10C180JC8NNNC").actual_part(
          "TDK", "CGA3E2C0G1H180J080AA").actual_part(
          "Kamet", "C0603C180K5GACTU").actual_part(
          "Murata", "GCM1885C1H180JA16D").actual_part(
          "TDK", "C1608CH1H180J080AA").actual_part(
          "AVX", "06035A180JAT2A").actual_part(
          "Yageo", "CC0603JRNPO9BN180")
        self.choice_part(".01uF;1608", "CAPC1608X90N", "",
                         "CAP CER 0.01UF 25V+ 10% SMD 0603", rotation=90.0).actual_part(
          "Yageo", "CC0603KRX7R9BB103").actual_part(
          "KEMET", "C0603C103K5RACTU").actual_part(
          "AVX", "06035C103KAT2A").actual_part(
          "TDK", "CGA3E2X7R1H103K080AA").actual_part(
          "KEMET", "C0603C103J5RACTU").actual_part(
          "Murata", "GCM188R72A103KA37D").actual_part(
          "TDK", "C1608X7R2A103M080AA").actual_part(
          "TDK", "C1608X7R2A103K080AA").actual_part(
          "Samsung", "CL10B103KB8NCNC").actual_part(
          "Samsung", "CL10B103KB8NNNC").actual_part(
          "Samsung", "CL10B103KA8NNNC").actual_part(
          "Samsung", "CL10B103KO8NNNC").actual_part(
          "Samsung", "CL10B103MB8NCNC").actual_part(
          "AV/X", "06035C103KAT4A")
        self.alias_part("10nF;1608",
                        [".01uF;1608"], "CAPC1608X90N", feeder_name="10nF",
                        rotation=90.0, part_height=0.90)
        self.choice_part(".033uF;1608", "CAPC1608X90N", "",
                         "CAP CER 0.01UF 25V+ 10% SMD 0603", rotation=90.0).actual_part(
          "Samsung", "CL10B333KB8NNNC").actual_part(
          "Samsung", "CL10B333KA8NNNC").actual_part(
          "Samsung", "CL10B333KB8SFNC").actual_part(
          "Yageo", "CC0603KRX7R9BB333").actual_part(
          "KEMET", "C0603C333K3RACTU").actual_part(
          "KEMET", "C0603C333K4RACTU").actual_part(
          "KEMET", "C0603C333K5RACTU").actual_part(
          "Samsung", "CL10F333ZB8NNNC").actual_part(
          "Samsung", "CL10B333KO8NNWC").actual_part(
          "Samsung", "CL10B333KA8WPNC").actual_part(
          "KEMET", "C0603C333M5RAC7867").actual_part(
          "Samsung", "CL10B333KB8NFNC").actual_part(
          "Wurth", "885012206068").actual_part(
          "Wurth", "885012206043")
        self.alias_part("33nF;1608", [".033uF;1608"],
                        "CAPC1608X90N", feeder_name="33nF", rotation=90.0, part_height=0.90)
        self.choice_part(".1uF;1608", "CAPC1608X90N", "",
                         "CAP CER 0.1UF 25V+ 10% SMD 0603", rotation=90.0).actual_part(
          "TDK", "C1608X7R1E104K080AA").actual_part(
          "Kemet", "C0603C104K3RACTU").actual_part(
          "Kemet", "C0603C104M5RACTU").actual_part(
          "Samsung", "CL10B104KB8SFNC").actual_part(
          "Kemet", "C0603C104K5RACTU").actual_part(
          "TDK", "C1608X7R1H104K080AA").actual_part(
          "TDK", "C1608X7R1H104M080AA").actual_part(
          "Johanson", "500R14W104KV4T").actual_part(
          "TDK", "CGA3E2X7R1H104K080AA").actual_part(
          "Samsung", "CL10F104ZB8NNNC").actual_part(
          "Samsung", "CL10F104ZA8NNNC").actual_part(
          "Samsung", "CL10B104KA8NNNC").actual_part(
          "Samsung", "CL10B104MA8NNNC").actual_part(
          "Kamet", "C0603C104Z3VACTU").actual_part(
          "TDK", "C1608X7R1E104M080AA")
        self.alias_part("100nF;1608", [".1uF;1608"],
                        "CAPC1608X90N", feeder_name="0.1uF", rotation=90.0, part_height=0.90)
        self.choice_part(".33uF;1608", "CAPC1608X90N", "",
                         "CAP CER .33UF 25V+ 10% SMD 0603",
                         rotation=90.0, part_height=0.90).actual_part(
          "Yageo", "CC0603KRX7R7BB334").actual_part(
          "Samsung", "CL10F334ZA8NNNC").actual_part(
          "Samsung", "CL10F334ZO8NNNC").actual_part(
          "Samsung", "CL10B334KP8NNNC").actual_part(
          "Samsung", "CL10B334KO8NNNC").actual_part(
          "Yageo", "CC0603KRX7R6BB334").actual_part(
          "Wruth", "885012106014").actual_part(
          "Samsung", "CL10B334KO8NFNC").actual_part(
          "AVX", "0603YC334KAT2A").actual_part(
          "KEMET", "C0603C334K8RACTU").actual_part(
          "Wurth", "885012106007").actual_part(
          "TDK", "CGA3E1X7R1C334K080AC").actual_part(
          "Wurth", "885012206023")
        self.alias_part("330nF;1608", [".33uF;1608"], "CAPC1608X90N",
                        feeder_name="330nF", rotation=90.0, part_height=0.90)
        self.choice_part(".47uF;1608", "CAPC1608X90N", "",
                         "CAP CER .47UF 25V+ 10% SMD 0603",
                         rotation=90.0, part_height=0.90).actual_part(
          "KMET", "C0603C473M4RACTU").actual_part(
          "Samsung", "CL10B473KB8NNNC").actual_part(
          "Samsung", "CL10B473KA8NFNC").actual_part(
          "Yageo", "CL10B473KA8NFNC").actual_part(
          "Yageo", "CC0603KRX7R8BB473").actual_part(
          "KMET", "C0603C473K4RACTU").actual_part(
          "KMET", "C0603C473K3RACTU").actual_part(
          "Yageo", "CC0603KRX7R7BB473").actual_part(
          "AVX", "06033C473KAT2A").actual_part(
          "Johanson", "500R14W473KV4T").actual_part(
          "KMET", "C0603C473K5RACTU").actual_part(
          "Samsung", "CL10B473KO8WPNC").actual_part(
          "Samsung", "CL10B473KA8WPNC").actual_part(
          "Samsung", "CL10B473KB8NFNC").actual_part(
          "Samsung", "CL10B473KO8NNNC").actual_part(
          "Yalyo Yuden", "GMK107BJ473KAHT")
        self.alias_part("470nF;1608", [".47uF;1608"],
                        "CAPC1608X90N", feeder_name="470nF", rotation=90.0, part_height=0.90)
        self.choice_part("1uF;1608", "CAPC1608X90N", "",
                         "CAP CER 1UF 25V+ 10% SMD 0603", rotation=90.0).actual_part(
          "Taiyo Yuden", "TMK107BJ105KA-T").actual_part(
          "Samsung", "CL10B105KA8NNNC").actual_part(
          "Taiyo Yuden", "TMK107B7105KA-T").actual_part(
          "Samsung", "CL10A105KA8NNNC").actual_part(
          "Samsung", "CL10A105KA5LNNC").actual_part(
          "Samsung", "CL10B105KA8NFNC").actual_part(
          "Yageo", "CC0603KRX5R8BB105").actual_part(
          "Samsung", "CL10A105KA8NFNC").actual_part(
          "Yageo", "CC0603ZRY5V8BB105")
        self.choice_part("10uF;1608", "CAPC1608X90N", "",
                         "CAP CER 10UF 4V X6S 0603", rotation=90.0).actual_part(
          "Taiyo Yuden", "JMK107BJ106MA-T").actual_part(
          "Taiyo Yuden", "AMK107ABJ106MAHT").actual_part(
          "TDK", "C1608X5R0J106M080AB").actual_part(
          "Samsung", "CL10A106MQ8NNNC").actual_part(
          "Samsung", "CL10A106MR5LQNC").actual_part(
          "Taiyo Yuden", "LMK107BBJ106MALT").actual_part(
          "Taiyo Yuden", "JMK107ABJ106MAHT").actual_part(
          "Yageo", "CC0603MRX5R4BB106").actual_part(
          "AVX", "06036D106MAT2A").actual_part(
          "Taiyo Yuden", "AMK107AC6106MA-T").actual_part(
          "KMET", "C0603C106M7PAC7867").actual_part(
          "Yageo", "CC0603MRX5R5BB106").actual_part(
          "Taiyo Yuden", "JMK107BC6106MA-T").actual_part(
          "Samsung", "CL10X106MO8NRNC").actual_part(
          "Wurth", "885012106006")
        self.choice_part("330uF/63V;D10P5", "CAP_D10P5", "",
                         "CAP ALUM 330UF 20% 63V RADIAL").actual_part(
          "Nichicon", "UVZ1J331MPD").actual_part(
          "Panisonic", "ECA-1JM331B").actual_part(
          "Nichicon", "UVY1J331MPD1TD").actual_part(
          "Nichicon", "UVY1J331MPD").actual_part(
          "Chemi-Con", "EKMG630ELL331MJ20S").actual_part(
          "Rubycon", "63ZLH330MEFC10X23").actual_part(
          "Nichicon", "UVK1J331MPD1TD").actual_part(
          "Nichicon", "UFW1J331MPD").actual_part(
          "Chemi-Con", "EKYB630ELL331MJ25S").actual_part(
          "Chemi-Con", "ELXZ630ELL331MJ30S").actual_part(
          "Panisonic", "ECA-1JHG331").actual_part(
          "Chemi-Con", "EKZN630ELL331MJ25S").actual_part(
          "Chemi-Con", "ESMG630ELL331MJ20S").actual_part(
          "Rubycon", "63PX330MEFC10X20").actual_part(
          "Panisonic", "ECA-1JHG331B").actual_part(
          "Nichicon", "UFW1J331MPD1TD").actual_part(
          "Panisonic", "EEU-FC1J331L").actual_part(
          "Nichicon", "UKW1J331MPD").actual_part(
          "Panisonic", "EEU-FS1J331L").actual_part(
          "RubyCon", "63ZLJ330M10X25").actual_part(
          "Panisonic", "EEU-FS1J331LB").actual_part(
          "Nichicon", "UHW1J331MPD").actual_part(
          "Nichicon", "UHW1J331MPD1TD").actual_part(
          "Wurth", "860010775019").actual_part(
          "Wurth", "860080775020")

        self.choice_part("470uF/35V;D10P5", "CAP_D10P5", "",
                         "CAP ALUM 470UF 20% 35V+ RADIAL").actual_part(
          "Panasonic", "ECA-1VM471").actual_part(
          "Rubycon", "35PK470MEFC10X12.5").actual_part(
          "KEMET", "ESH477M035AH3AA").actual_part(
          "Nichicon", "UVR1V471MPD").actual_part(
          "KEMET", "ESC477M035AH4AA").actual_part(
          "KEMET", "ESK477M035AH2EA").actual_part(
          "Wurth", "860010575013").actual_part(
          "Rubycon", "35PX470MEFC10X12.5").actual_part(
          "Wurth", "860020575014").actual_part(
          "Nichicon", "UVZ1V471MPD").actual_part(
          "KEMET", "ESH477M050AH4AA").actual_part(
          "Nichicon", "UVR1V471MPD1TD").actual_part(
          "TDK", "B41821A7477M000").actual_part(
          "Nichion", "UVY1V471MPD").actual_part(
          "Illinois Capcitor", "477CKE035M").actual_part(
          "Illinois Capcitor", "477CKS035M")
        self.choice_part("1500UF_200V;R35MM", "R35MM", "",
                         "CAP ALUM 1500UF 200V SCREW").actual_part(
          "Unitied Chemi-Con", "E36D201LPN152TA79M",
          [("Digi-Key", "565-3307-ND", "1/12.10 10/11.495 100/9.075")])

        # Connectors:

        # Male Connectors:

        # Create the fractional parts for 1XN male headers:
        self.choice_part("M1X40;M1X40", "Pin_Header_Straight_1x40", "",
                         "CONN HEADER .100in SNGL STR 40POS").actual_part(
          "Sullins", "PREC040SAAN-RC", [
           ("Digi-Key", "S1012EC-40-ND",
            "1/.56 10/.505 100/.4158 500/.32868 1000/.28215")])

        self.fractional_part("M1X1;M1X1", "Pin_Header_Straight_1x01",
                             "M1X40;M1X40", 1, 40, "CONN HEADER .100in SNGL STR 1POS")
        self.fractional_part("M1X2;M1X2", "Pin_Header_Straight_1x02",
                             "M1X40;M1X40", 2, 40, "CONN HEADER .100in SNGL STR 2POS")
        self.fractional_part("M1X3;M1X3", "Pin_Header_Straight_1x03",
                             "M1X40;M1X40", 3, 40, "CONN HEADER .100in SNGL STR 3POS")
        self.fractional_part("M1X4;M1X4", "Pin_Header_Straight_1x04",
                             "M1X40;M1X40", 4, 40, "CONN HEADER .100in SNGL STR 4POS")
        self.fractional_part("M1X5;M1X5", "Pin_Header_Straight_1x05",
                             "M1X40;M1X40", 5, 40, "CONN HEADER .100in SNGL STR 5POS")
        self.fractional_part("M1X6;M1X6", "Pin_Header_Straight_1x06",
                             "M1X40;M1X40", 6, 40, "CONN HEADER .100in SNGL STR 6POS")
        self.fractional_part("M1X7;M1X7", "Pin_Header_Straight_1x07",
                             "M1X40;M1X40", 7, 40, "CONN HEADER .100in SNGL STR 6POS")

        # Test points M1X1:
        self.alias_part("CAN_RXD;M1X1",
                        ["M1X1;M1X1"], "Pin_Header_Straight_1x01")
        self.alias_part("TEST_POINT;M1X1",
                        ["M1X1;M1X1"], "Pin_Header_Straight_1x01")

        # M1X2:
        self.alias_part("CURRENT_SHUNT;M1X2",
                        ["M1X2;M1X2"], "Pin_Header_Straight_1x02")
        self.alias_part("ESTOP_CONN;JSTPH2",
                        ["M1X2;M1X2"], "JSTPH2")
        self.choice_part("JMP1X2;JMP1X2", "-", "",
                         "CONN JUMPER SHORTING").actual_part(
          "Sullins", "SPC02SYAN").actual_part(
          "Sullins", "STC02SYAN").actual_part(
          "Sullins", "QPC02SXGN-RC").actual_part(
          "Sullins", "NPC02SXON-RC").actual_part(
          "Sullins", "SPC02SXCN-RC").actual_part(
          "Amp", "382811-8").actual_part(
          "Sullins", "SPC02SXIN-RC").actual_part(
          "Sullins", "SPC02SVJN-RC").actual_part(
          "Sullins", "SPC02SVGN-RC").actual_part(
          "Harrwin", "M7582-46").actual_part(
          "Amp", "2-382811-1").actual_part(
          "Amp", "2-382811-0").actual_part(
          "Amp", "2-881545-2").actual_part(
          "Amp", "382811-6").actual_part(
          "Harwin", "M7581-05").actual_part(
          "Amphenol", "68786-102LF").actual_part(
          "Harwin", "M7582-05").actual_part(
          "Amp", "1-881545-4").actual_part(
          "Sullins", "SSC02SYAN").actual_part(
          "Samtec", "SNT-100-BK-T")

        # M1X3:
        self.alias_part("CURRENT_SHUNT;M1X3",
                        ["M1X3;M1X3"], "Pin_Header_Straight_1x03")
        self.alias_part("TERMINATE_JUMPER;M1X3",
                        ["M1X3;M1X3"], "Pin_Header_Straight_1x03")
        self.alias_part("SERVO;M1X3",
                        ["M1X3;M1X3"], "Pin_Header_Straight_1x03")
        self.alias_part("SIGNAL_SEL;M1X3",
                        ["M1X3;M1X3", "JMP1X2;JMP1X2"], "Pin_Header_Straight_1x03")
        self.alias_part("PWR_SEL;M1X3",
                        ["M1X3;M1X3", "JMP1X2;JMP1X2"], "Pin_Header_Straight_1x03")

        # M1X4:
        self.alias_part("I2C_CONN;M1X4",
                        ["M1X4;M1X4"], "Pin_Header_Straight_1x04")
        self.alias_part("MTR_ID_CON;M1X4",
                        ["M1X4;M1X4"], "Pin_Header_Straight_1x04")

        # M1X5:
        self.alias_part("MTR_DRV_CON;M1X5",
                        ["M1X5;M1X5"], "Pin_Header_Straight_1x05")

        # M1X6:
        self.alias_part("ENCODER_CONNECTOR;M1X6",
                        ["M1X6;M1X6"], "Pin_Header_Straight_1x06")
        self.alias_part("FTDI_HEADER;M1X6",
                        ["M1X6;M1X6"], "Pin_Header_Straight_1x06")
        self.alias_part("FTDI_HEADER_ALT;M1X6",
                        ["M1X6;M1X6"], "Pin_Header_Straight_1x06")

        # M1X7:
        # self.alias_part("MTR_TRN_CON;M1X7",
        #  ["M1X7;M1X7"], "Pin_Header_Straight_1x07")

        # Create the fractional parts for the 2XN male headers:
        self.choice_part("M2X40;M2X40", "Pin_Header_Straight_2x40",
                         "Pin_Header_Straight_2x40",
                         "CONN HEADER .100in DUAL STR 80POS").actual_part(
          "Sullins", "PREC040DAAN-RC", [
           ("Digi-Key", "S2212EC-40-ND",
            "1/1.28 10/1.14200 100/.9408 500/.74368")]).actual_part(
          "Sullins", "PREC040DFAN-RC").actual_part(
          "Sullins", "PRPC040DAAN-RC").actual_part(
          "Sullins", "PRPC040DABN-RC").actual_part(
          "Sullins", "PRPC040DFAN-RC").actual_part(
          "Sullins", "PRPC040DFBN-RC").actual_part(
          "Wurth", "61308021121").actual_part(
          "TE", "4-103322-2").actual_part(
          "TE", "9-146258-0")

        self.fractional_part("M2X3;M2X3", "Pin_Header_Straight_2x03",
                             "M2X40;M2X40", 6, 80, "CONN HEADER .100in DBL STR 6POS")

        self.fractional_part("AVR_SPI;M2X3", "Pin_Header_Straight_2x03",
                             "M2X40;M2X40", 6, 80, "CONN HEADER .100in DBL STR 6POS")
        self.fractional_part("ISP_HEADER;M2X3", "Pin_Header_Straight_2x03",
                             "M2X40;M2X40", 6, 80, "CONN HEADER .100in DBL STR 6POS")

        # For now, there is no footprint:
        self.fractional_part("M2X35;M2X35", "-",
                             "M2X40;M2X40", 70, 80, "CONN HEADER .100in DBL STR 70POS")

        self.choice_part("M2X5S;M2X5S",
                         "Pin_Header_Straight_2x05_Shrouded", "",
                         "BOX HEADER .100in MALE STR 10POS").actual_part(
          "Assmann", "AWHW-10G-0202-T").actual_part(
          "Sullins", "SBH11-PBPC-D05-ST-BK").actual_part(
          "3M", "30310-6002HB").actual_part(
          "TE Tech", "5103308-1").actual_part(
          "Wurth", "61201021621")
        self.choice_part("F2X5K;F2X5K", "-", "",        # Female 2X5 Keyed
                         "CONN SOCKET IDC 10POS W/KEY").actual_part(
          "On Shore", "101-106").actual_part(
          "CNC Tech", "3030-10-0102-00").actual_part(
          "CNC Tech", "3030-10-0103-00").actual_part(
          "Wruth", "61201023021").actual_part(
          "Assmann", "AWP 10-7240-T").actual_part(
          "Assmann", "AWP 10-7540-T").actual_part(
          "Sullins", "SFH210-PPPC-D05-ID-BK").actual_part(
          "Sullins", "SFH213-PPPC-D05-ID-BK").actual_part(
          "Molex", "0906351101").actual_part(
          "3M", "D89110-0131HK").actual_part(
          "Molex", "0906351103").actual_part(
          "3M", "D89110-0101HK").actual_part(
          "Molex", "0906351102").actual_part(
          "Amphenol", "71600-610LF").actual_part(
          "Omron", "XG4M-1030").actual_part(
          "3M", "89110-0101").actual_part(
          "3M", "89110-0101HA").actual_part(
          "Amp", "1658621-1")
        self.alias_part("BUS_MASTER_HEADER;M2X5S",
                        ["M2X5S;M2X5S"], "Pin_Header_Straight_2x05_Shrouded")
        self.alias_part("MSTR_BUS;M2X5S",
                        ["M2X5S;M2X5S"], "Pin_Header_Straight_2x05_Shrouded")
        self.alias_part("MASTER_BUS;M2X5S",
                        ["M2X5S;M2X5S"], "Pin_Header_Straight_2x05_Shrouded")
        self.alias_part("BUS_MASTER;M2X5S",
                        ["M2X5S;M2X5S", "F2X5K;F2X5K"], "Pin_Header_Straight_2x05_Shrouded")
        self.alias_part("BUS_SLAVE;M2X5S",
                        ["M2X5S;M2X5S", "F2X5K;F2X5K"], "Pin_Header_Straight_2x05_Shrouded")
        self.fractional_part("M2X6;M2X6", "Pin_Header_Straight_2x06",
                             "M2X40;M2X40", 12, 80, "CONN HEADER .100in DBL STR 12POS")

        self.choice_part("M2X7S;M2X7S",
                         "Pin_Header_Straight_2x07_Shrouded", "",
                         "CONN HEADER VERT 14POS 2.54MM").actual_part(
            "On Shore", "302-S141").actual_part(
            "Sullins", "SBH11-PBPC-D07-ST-BK").actual_part(
            "Assmann", "AWHW 14G-0202-T").actual_part(
            "CNC Tech", "3020-14-0100-00").actual_part(
            "Amphenol", "75869-302LF").actual_part(
            "Amphenol", "75869-102LF").actual_part(
            "Wurth", "61201421621").actual_part(
            "Omron", "XG4C-1431").actual_part(
            "Amp", "5103308-2").actual_part(
            "Samtec", "TST-107-01-T-D").actual_part(
            "Amphenol", "10056844-114LF").actual_part(
            "3M", "30314-6002HB").actual_part(
            "Amp", "5102154-2").actual_part(
            "3M", "D3314-6002-AR").actual_part(
            "3M", "D2514-6002-AR").actual_part(
            "Amp", "5103309-2").actual_part(
            "Amp", "103308-2").actual_part(
            "Amp", "1761681-5").actual_part(
            "Molex", "0702461404").actual_part(
            "3M", "N2514-6002-RB").actual_part(
            "Hirose", "HIF3FC-14PA-2.54DSA(71)").actual_part(
            "3M", "N2514-6003-RB").actual_part(
            "Samtec", "TSS-107-01-L-D").actual_part(
            "Samtec", "TST-107-01-L-D").actual_part(
            "Amphenol", "66506-038LF").actual_part(
            "Amp", "2-1761603-5")
        self.alias_part("BUS_MASTER14;M2X7S",
                        ["M2X7S;M2X7S"], "Pin_Header_Straight_2x07_Shrouded")
        self.alias_part("BUS_SLAVE14;M2X7S",
                        ["M2X7S;M2X7S"], "Pin_Header_Straight_2x07_Shrouded")

        # Quick Disconnect Tereminals:
        # .187" Male/Female connectors:
        self.choice_part("FQD187_RED;FQD187_RED", "-", "",
                         "CONN QC RCPT 16-20AWG 0.187").actual_part(
          "Phoenix Contact", "3240537").actual_part(
          "Panduit", "DV18-187B-MY").actual_part(
          "Panduit", "DV18-188B-MY").actual_part(
          "3M", "94800").actual_part(
          "Molex", "0190170007").actual_part(
          "Molex", "0190170008").actual_part(
          "Amp", "2-520182-2").actual_part(
          "Panduit", "DNF18-187-M").actual_part(
          "Amp", "2-520194-2").actual_part(
          "Panduit", "DNF18-187FIB-M").actual_part(
          "Panduit", "DNF18-188FIB-MDNF18-188FIB-M").actual_part(
          "Molex", "01900300110190030011").actual_part(
          "Panduit", "DNF18-188-M").actual_part(
          "Amp", "640917-1").actual_part(
          "Molex", "0190190006").actual_part(
          "Molex", "0190190008").actual_part(
          "Amp", "2-520275-2").actual_part(
          "3M", "94797")
        self.choice_part("FQD187_BLK;FQD187_BLK", "-", "",
                         "CONN QC RCPT 16-20AWG 0.187").actual_part(
          "Amp", "9-520276-2").actual_part(
          "Amp", "9-520193-2").actual_part(
          "Amp", "9-520181-2").actual_part(
          "Amp", "521212-1")
        self.choice_part("TERMINAL;MQD187", "MQD250", "",
                         "CONN QC TAB 0.187 SOLDER").actual_part(
          "Molex", "0197084013").actual_part(
          "Keystone", "1285").actual_part(
          "Amp", "1217332-1").actual_part(
          "Amp", "1217133-1").actual_part(
          "Keystone", "1285-ST").actual_part(
          "Amp", "63823-1").actual_part(
          "Keystone", "1212-ST").actual_part(
          "Keystone", "1212").actual_part(
          "Molex", "0197084001").actual_part(
          "Amp", "1742361-1").actual_part(
          "Keystone", "4900")
        # Note .187" has same PCB lead spacing as .250"
        self.alias_part("TERMINAL_PI;MQD187",
                        ["TERMINAL;MQD187"], "MQD250")
        # Note .187" has same PCB lead spacing as .250"
        self.alias_part("TERMINAL_PO;MQD187",
                        ["TERMINAL;MQD187"], "MQD250")
        self.alias_part("PWR_IN;MQD187B",
                        ["TERMINAL;MQD187", "FQD187_BLK;FQD187_BLK"], "MQD250")
        self.alias_part("PWR_OUT;MQD187B",
                        ["TERMINAL;MQD187", "FQD187_BLK;FQD187_BLK"], "MQD250")

        # .250" Male/Female QD connectors:
        self.choice_part("FQD250_RED;FQD250_RED", "-", "",
                         "CONN QC RCPT 16-20AWG 0.250").actual_part(
          "Phoenix", "3240538").actual_part(
          "3M", "94804").actual_part(
          "Amp", "2-520183-2").actual_part(
          "Amp", "2-520184-2").actual_part(
          "Panduit", "DV18-250B-3K").actual_part(
          "Panduit", "DNF18-250-M").actual_part(
          "Panduit", "DNF18-250FIB-3K").actual_part(
          "Molex", "0192740002").actual_part(
          "Molex", "0192760002").actual_part(
          "Molex", "0190030105").actual_part(
          "Amp", "2-520405-2").actual_part(
          "Molex", "0190170014").actual_part(
          "Panduit", "DPF18-250FIB-M").actual_part(
          "Phoenix", "3240052").actual_part(
          "Amp", "2-520263-2").actual_part(
          "Molex", "0192750002")
        self.choice_part("FQD250_BLK;FQD187_BLK", "-", "",
                         "CONN QC RCPT 16-20AWG 0.250").actual_part(
          "Amp", "521011-2").actual_part(
          "Amp", "9-520183-2").actual_part(
          "Amp", "521011-1")
        self.choice_part("TERMINAL;MQD250", "MQD250", "",
                         "CONN QC TAB 0.250 SOLDER").actual_part(
          "Amp", "1217861-1").actual_part(
          "Amp", "63824-1").actual_part(
          "Amp", "63839-1").actual_part(
          "Molex", "0197054203").actual_part(
          "Amp", "63862-1").actual_part(
          "Molex", "0197054303").actual_part(
          "Amp", "62650-1").actual_part(
          "Amp", "1217126-1").actual_part(
          "Amp", "63066-1").actual_part(
          "Amp", "62409-1").actual_part(
          "Keystone", "1287").actual_part(
          "Keystone", "1287-ST").actual_part(
          "Keystone", "1289-ST").actual_part(
          "Keystone", "1289").actual_part(
          "Keystone", "1292").actual_part(
          "Keystone", "4901").actual_part(
          "Amp", "1217169-1").actual_part(
          "Keystone", "7812")
        self.alias_part("TERMINAL_PI;MQD250",
                        ["TERMINAL;MQD250"], "MQD250")
        self.alias_part("TERMINAL_PO;MQD250",
                        ["TERMINAL;MQD250"], "MQD250")
        self.alias_part("PWR_IN;MQD250R",
                        ["TERMINAL;MQD250", "FQD250_RED;FQD250_RED"], "MQD250")
        self.alias_part("PWR_OUT;MQD250R",
                        ["TERMINAL;MQD250", "FQD250_RED;FQD250_RED"], "MQD250")

        # Non-fractional part Male connectors:

        self.choice_part("ENCODER_CONNECTOR;M1X6_JST", "M1X6_JST", "M1X6_JST",
                         "CONN HEADER ZH SIDE 6POS 1.5MM").actual_part(
                         "JST", "S6B-ZR(LF)(SN)")

        self.choice_part("JSTPH_PIN;JSTPH_PIN", "-", "",
                         "CONN TERM CRIMP PH 24-30AWG").actual_part(
                         "JST", "SPH-002T-P0.5S")

        # 2-pin JST PH
        self.choice_part("JSTPH2;JSTPH2", "JSTPH2", "",
                         "CONN HEADER PH TOP 2POS 2MM").actual_part(
                         "JST", "B2B-PH-K-S(LF)(SN)")
        self.choice_part("FJSTPH2;FJSTPH2", "-", "",
                         "CONN HOUSING PH 2POS 2MM WHITE").actual_part(
                         "JST", "PHR-2")

        # 3-pin JST PH
        self.choice_part("JSTPH3;JSTPH3", "JSTPH3", "",
                         "CONN HEADER PH TOP 3POS 2MM").actual_part(
                         "JST", "B3B-PH-K-S(LF)(SN)")
        self.choice_part("FJSTPH3;FJSTPH3", "-", "",
                         "CONN HOUSING PH 3POS 2MM WHITE").actual_part(
                         "JST", "PHR-3")

        # 4-pin JST PH
        self.choice_part("JSTPH4;JSTPH4", "JSTPH4", "",
                         "CONN HEADER PH TOP 4POS 2MM").actual_part(
                         "JST", "B4B-PH-K-S(LF)(SN)")
        self.choice_part("FJSTPH4;FJSTPH4", "-", "",
                         "CONN HOUSING PH 4POS 2MM WHITE").actual_part(
                         "JST", "PHR-4")
        self.alias_part("MTR_ID_CON;JSTPH4",
                        ["JSTPH4;JSTPH4", "FJSTPH4;FJSTPH4", (4, "JSTPH_PIN;JSTPH_PIN")], "JSTPH4")
        self.alias_part("MTR_ID;JSTPH4",
                        ["JSTPH4;JSTPH4", "FJSTPH4;FJSTPH4", (4, "JSTPH_PIN;JSTPH_PIN")], "JSTPH4")

        # 5-pin JST PH
        self.choice_part("JSTPH5;JSTPH5", "JSTPH5", "",
                         "CONN HEADER PH TOP 5POS 2MM").actual_part(
                         "JST", "B5B-PH-K-S(LF)(SN)")
        self.choice_part("FJSTPH5;FJSTPH5", "-", "",
                         "CONN HOUSING PH 5POS 2MM WHITE").actual_part(
                         "JST", "PHR-5")
        self.alias_part("MTR_DRV_CON;JSTPH5",
                        ["JSTPH5;JSTPH5", "FJSTPH5;FJSTPH5", (5, "JSTPH_PIN;JSTPH_PIN")], "JSTPH5")
        self.alias_part("SLV_DRV_CON;JSTPH5",
                        ["JSTPH5;JSTPH5", "FJSTPH5;FJSTPH5", (5, "JSTPH_PIN;JSTPH_PIN")], "JSTPH5")

        # 6-pin JST PH
        self.choice_part("JSTPH6;JSTPH6", "JSTPH6", "",
                         "CONN HEADER PH TOP 6POS 2MM").actual_part(
                         "JST", "B6B-PH-K-S(LF)(SN)")
        self.choice_part("FJSTPH6;FJSTPH6", "-", "",
                         "CONN HOUSING PH 6POS 2MM WHITE").actual_part(
                         "JST", "PHR-6")

        # 7-pin JST PH
        self.choice_part("JSTPH7;JSTPH7", "JSTPH7", "",
                         "CONN HEADER PH TOP 7POS 2MM").actual_part(
                         "JST", "B7B-PH-K-S(LF)(SN)")
        self.choice_part("FJSTPH7;FJSTPH7", "-", "",
                         "CONN HOUSING PH 7POS 2MM WHITE").actual_part(
                         "JST", "PHR-7")
        self.alias_part("MTR_TRN_CON;JSTPH7",
                        ["JSTPH7;JSTPH7", "FJSTPH7;FJSTPH7", (7, "JSTPH_PIN;JSTPH_PIN")], "JSTPH7")
        self.alias_part("SLV_TRN_CON;JSTPH7",
                        ["JSTPH7;JSTPH7", "FJSTPH7;FJSTPH7", (7, "JSTPH_PIN;JSTPH_PIN")], "JSTPH7")

        # 10-pin JST PH
        # self.choice_part("JSTPH10;JSTPH10", "JSTPH10", "",
        #  "CONN HEADER VERT 10POS 2MM").actual_part(
        #  "JST", "10B-PH-K-S(LF)(SN)")
        self.choice_part("JSTPH10;JSTPH10", "JSTPH10", "",
                         "CONN HEADER VERT 10POS 2MM").actual_part(
                         "JST", "10B-PH-K-S(LF)(SN)",
                         [("Digi-Key", "455-1712-ND",
                           "1/.46 10/.428 100/.3278 500/.28504 1000/.23515")])
        self.choice_part("FJSTPH10;FJSTPH10", "-", "",
                         "CONN HOUSING PH 10POS 2MM WHITE").actual_part(
                         "JST", "PHR-10")
        self.alias_part("LIDAR_CONN;JSTPH10",
                        ["JSTPH10;JSTPH10", "FJSTPH10;FJSTPH10",
                         (10, "JSTPH_PIN;JSTPH_PIN")], "JSTPH10")

        # Female connectors:

        self.choice_part("F1X3;F1X3", "Pin_Header_Straight_1x03", "",
                         "CONN HEADER FEMALE 3POS .1inch").actual_part(
          "Sullins", "PPPC031LFBN-RC").actual_part(
          "Sullins", "PPTC031LFBN-RC").actual_part(
          "3M", "960103-6202-AR").actual_part(
          "Harwin", "M20-7820342").actual_part(
          "TE", "5-535541-1").actual_part(
          "3M", "929850-01-03-RA").actual_part(
          "FCI", "66951-003LF")
        self.alias_part("REGULATOR;F1X3",
                        ["F1X3;F1X3"], "Pin_Header_Straight_1x03")
        self.alias_part("POLOLU_VR;F1X3",
                        ["F1X3;F1X3"], "Pin_Header_Straight_1x03")

        self.choice_part("F1X4;F1X4", "Pin_Header_Straight_1x04", "",
                         "CONN HEADER FEMALE 4POS .1inch").actual_part(
          "Sullins", "PPTC041LFBN-RC").actual_part(
          "Sullins", "PPPC041LFBN-RC").actual_part(
          "Amp", "215299-4").actual_part(
          "Samtec", "SLW-104-01-F-S").actual_part(
          "Samtec", "SS-104-TT-2").actual_part(
          "Samtec", "SSA-104-S-T").actual_part(
          "3M", "929974-01-04-RK").actual_part(
          "Harwin", "M20-7820446").actual_part(
          "Samtec", "SLW-104-01-L-S").actual_part(
          "Harwin", "M20-7820442").actual_part(
          "Samtec", "SSW-104-01-F-S").actual_part(
          "Samtec", "SSQ-104-01-F-S")

        self.choice_part("F1X5;F1X5", "Pin_Header_Straight_1x05", "",
                         "CONN HEADER FEMALE 5POS .1inch").actual_part(
          "Sullins", "PPTC051LFBN-RC").actual_part(
          "Sullins", "PPPC051LFBN-RC").actual_part(
          "Samtec", "SS-105-TT-2").actual_part(
          "Amp", "215299-5").actual_part(
          "Samtec", "SSA-105-S-T").actual_part(
          "Samtec", "SSW-105-01-F-S").actual_part(
          "Harwin", "M20-7820542").actual_part(
          "Amp", "215297-5").actual_part(
          "Samtec", "SSW-105-01-T-S").actual_part(
          "Samtec", "SSW-105-02-T-S")

        self.choice_part("S18V20F6;S18V20Fx", "S18V20Fx", "",
                         "6V STEP-UP/DOWN VOLT REG.").actual_part(
          "Pololu", "S18V20F6",
          [("Pololu", "S18V20F6", "1/14.95 5/13.45 25/12.33 100/11.21")])
        # self.choice_part("V18V20F5;V18V20F5", "-", "",
        #  "5V STEP-UP/DOWN VOLT REG.").actual_part(
        #  "Pololu", "V18V20F5", [
        #    ("Pololu", "V18V20F5", "1/14.95 5/13.45 25/12.33 100/11.21")])
        # self.choice_part("V18V20F6;V18V20F6", "-", "",
        #  "6V STEP-UP/DOWN VOLT REG.").actual_part(
        #  "Pololu", "V18V20F6", [
        #    ("Pololu", "V18V20F6", "1/14.95 5/13.45 25/12.33 100/11.21")])
        # self.alias_part("V18V20Fx;S18V20Fx",
        #  ["F1X5;F1X5", "F1X4;F1X4"], "S18V20Fx")
        # self.alias_part("V18V20F5;S18V20Fx",
        #  ["F1X5;F1X5", "F1X4;F1X4", "V18V20F5;V18V20F5"], "S18V20Fx")
        # self.alias_part("V18V20F6;S18V20Fx",
        #  ["F1X5;F1X5", "F1X4;F1X4", "V18V20F6;V18V20F6"], "S18V20Fx")

        self.choice_part("F1X6;F1X6", "Pin_Header_Straight_1x06", "",
                         "CONN HEADER FEMALE 6POS .1in").actual_part(
          "Sullins", "PPTC061LFBN-RC").actual_part(
          "Sullins", "PPPC061LFBN-RC").actual_part(
          "Molex", "0022022065").actual_part(
          "3M", "929974-01-06-RK").actual_part(
          "Harwin", "M20-7820646").actual_part(
          "Harwin", "M20-7820642")
        self.alias_part("ENCODER_CONNECTOR;F1X6",
                        ["F1X6;F1X6"], "Pin_Header_Straight_1x06")

        # Total kludge here.  We need to make this into the correct 1x6 JST connector:
        self.choice_part("MICRO_GEARMOTOR;M1X6_JST", "MICRO_GEARMOTOR", "",
                         "1x6 JST MALE CONNECTOR").actual_part(
          "JST Manufacturing", "B6B-ZR(LF)(SN)")

        self.choice_part("F2X4;F2X4", "Pin_Header_Straight_2x04", "",
                         "CONN RCPT .100in 8POS DUAL").actual_part(
          "Sullins", "PPTC042LFBN-RC").actual_part(
          "Sullins", "PPPC042LFBN-RC").actual_part(
          "Harwin", "M20-7830446").actual_part(
          "Harwin", "M20-7830442").actual_part(
          "TE", "5-534206-4").actual_part(
          "Samtec", "SSW-104-01-T-D").actual_part(
          "Samtec", "SSQ-104-01-T-D").actual_part(
          "Samtec", "SSQ-104-02-T-D").actual_part(
          "FCI", "68683-304LF").actual_part(
          "Samtec", "SSQ-104-03-T-D")
        self.alias_part("HC_SR04;F2X4",
                        ["F2X4;F2X4"], "Pin_Header_Straight_2x04")

        # For now, no footprint:
        self.choice_part("F2X5;F2X5", "-", "",
                         "CONN RCPT 10POS .100IN DBL PCB 8.51MM HI").actual_part(
          "Sullins", "PPTC052LFBN-RC").actual_part(
          "Sullins", "PPPC052LFBN-RC").actual_part(
          "Hawin", "M20-7830546").actual_part(
          "Amphenol", "87606-305LF").actual_part(
          "Harwin", "M20-7830542").actual_part(
          "Amphenol", "87606-805LF").actual_part(
          "Molex", "0901512110").actual_part(
          "Molex", "0901512210")

        # For now, no footprint:
        self.choice_part("F2X10;F2X10", "-", "",
                         "CONN RCPT 20POS .100IN DBL PCB 8.51MM HI").actual_part(
          "Amphenol", "87606-810LF").actual_part(
          "Sullins", "PPPC102LFBN-RC").actual_part(
          "Sullins", "PPTC102LFBN-RC").actual_part(
          "Amphenol", "87606-310LF").actual_part(
          "Harwin", "M20-7831042").actual_part(
          "Molex", "0901512120").actual_part(
          "Molex", "0901512220")

        self.choice_part("F2X10RA;F2X10", "Pin_Receptale_Angled_2x10", "",
                         "CONN RCPT .100in 20POS DUAL").actual_part(
          "Sullins", "SFH11-PBPC-D10-RA-BK").actual_part(
          "Sullins", "PPTC102LJBN-RC").actual_part(
          "Sullins", "PPPC102LJBN-RC").actual_part(
          "Samtec", "SSQ-110-02-T-D-RA").actual_part(
          "TE", "5535512-2").actual_part(
          "Samtec", "SSW-110-02-G-D-RA").actual_part(
          "Samtec", "SSW-110-02-S-D-RA").actual_part(
          "Hirose", "HIF3H-20DB-2.54DS(71)")

        self.choice_part("F2X20;F2X20", "Pin_Header_Straight_2x20", "",
                         "CONN HEADR FMALE 20POS .1").actual_part(
          "Sullins", "SFH11-PBPC-D20-ST-BK").actual_part(
          "Sullins", "PPTC202LFBN-RC").actual_part(
          "Sullins", "PPPC202LFBN-RC").actual_part(
          "Harwin", "M20-7832046").actual_part(
          "3M", "929975-01-20-RK").actual_part(
          "Samtec", "SSW-120-01-T-D").actual_part(
          "Samtec", "CES-120-01-T-D").actual_part(
          "3M", "929852-01-20-RB").actual_part(
          "Amphenol", "71991-320LF").actual_part(
          "Omron", "XG4H-4031-1")
        self.choice_part("RASPI3;RASPI3", "-", "",
                         "SINGLE PROJECT COMPUTER 1.2GHZ 1GB").actual_part(
          "Raspbeerry Pi", "RASPBERRY PI 3")
        self.alias_part("RASPI3;RASPI", ["F2X20;F2X20", "RASPI3;RASPI3"], "RASPI")

        self.choice_part("F2X20RA;F2X20RA", "Pin_Receptale_Angled_2x20", "",
                         "CONN RCPT .100in 40POS DUAL").actual_part(
          "Sullins", "PPTC202LJBN-RC").actual_part(
          "Sullins", "PPPC202LJBN-RC").actual_part(
          "3M", "960240-7102-AR        ")
        self.alias_part("SBC_CONNECTOR40;F2X20RA",
                        ["F2X20RA;F2X20RA"], "Pin_Receptale_Angled_2x20")

        self.choice_part("2POS_TERM_BLOCK;5MM", "5MM_TERMINAL_BLOCK_2_POS",
                         "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                         "TERM BLOCK PCB 2POS 5.0MM").actual_part(
          "Phoenix Contact", "1935161").actual_part(
          "Phoenix Contact", "1935776").actual_part(
          "TE", "1546216-2").actual_part(
          "TE", "282836-2").actual_part(
          "On Shore", "ED100/2DS")

        # There is a flipped/non-flipped issue here:
        self.choice_part("F2X20RAKF;F2X20RAKF",
                         "Pin_Receptacle_Angle_2x20_Flipped", "",
                         "CONN HEADER FEMALE 40POS 0.100in ANGLED KEYED FLIPPED").actual_part(
          "Sullins", "SFH11-PBPC-D20-RA-BK")
        self.alias_part("SBC_CONNECTOR40;F2X20RAKF", ["F2X20RAKF;F2X20RAKF"],
                        "Pin_Receptacle_Angled_2x20_Flipped")

        self.choice_part("F2X19;F2X19", "Pin_Header_Straight_2x19", "",
                         "CONN HEADER .100in DBL STR 38POS").actual_part(
          "Sullins", "PPPC192LFBN-RC").actual_part(
          "3M", "929975-01-19-RK").actual_part(
          "Samtec", "SSW-119-01-T-D").actual_part(
          "Samtec", "CES-119-01-T-D").actual_part(
          "Samtec", "SSQ-119-01-T-D").actual_part(
          "Samtec", "SLW-119-01-T-D").actual_part(
          "Samtec", "SSQ-119-02-T-D").actual_part(
          "Samtec", "SSQ-119-03-T-D").actual_part(
          "3M", "929852-01-19-RA")
        # Kludge: Use M2X40 instead of F2X35.  This works around a bug in vendor exclude:
        self.choice_part("NUCELO_F303RE;NUCLEO_F303RE", "-", "",
                         "PROJECT NUCLEO FOR STM32F303RE").actual_part(
          "STM", "NUCLEO-F303RE")
        self.alias_part("F303RE;NUCLEO64",
                        ["NUCELO_F303RE;NUCLEO_F303RE", (2, "F2X19;F2X19")], "NUCLEO64")

        self.choice_part("NUCLEO_F767ZI;NUCLEO_F767ZI", "-", "",
                         "PROJECT NUCLEO FOR STM32F767ZI").actual_part(
          "STM", "NUCLEO-F767ZI")
        self.choice_part("F2X35;F2X35", "Pin_Header_Straight_2x35", "",
                         "CONN HEADER .100in DBL STR 70POS").actual_part(
          "3M", "929975-01-35-RK").actual_part(
          "Samtec", "SSW-135-01-T-D").actual_part(
          "Samtec", "SSQ-135-01-T-D").actual_part(
          "Samtec", "SLW-135-01-T-D").actual_part(
          "Samtec", "SSQ-135-02-T-D").actual_part(
          "Samtec", "SSQ-135-03-T-D").actual_part(
          "3M", "929852-01-35-RA").actual_part(
          "Samtec", "SSW-135-01-G-D").actual_part(
          "Samtec", "SSW-135-02-G-D").actual_part(
          "Samtec", "SSW-135-01-S-D")
        # Kludge: 2X35 Female connectors are custom made.  Instead fake it with 3 F2x10's and
        # 1 F2X5 that are at the same height (8.51MM).  Note that we need to buy and solder in
        # *BOTH* the male and female connectors:
        # self.alias_part("F767ZI;NUCLEO144",
        #  ["NUCLEO_F767ZI;NUCLEO_F767ZI",
        #  (6, "F2X10;F2X10"), (2, "F2X5;F2X5"), (2, "M2X35;M2X35")],
        #  "NUCLEO144")
        self.alias_part("F767ZI;NUCLEO144",
                        ["NUCLEO_F767ZI;NUCLEO_F767ZI", (2, "F2X35;F2X35")], "NUCLEO144")
        self.alias_part("MASTER;NUCLEO144",
                        ["NUCLEO_F767ZI;NUCLEO_F767ZI", (2, "F2X35;F2X35")], "NUCLEO144")

        # USB connectors:
        self.choice_part("USB_MICRO_B;S+T", "FCI_10118194_0001LF", "",
                         "CONN USB MICRO B RECPT SMT R/A").actual_part(
          "Amphenol", "10118194-0001LF")

        self.choice_part("USB_B_ALT;ALT", "USB_B", "",
                         "CONN USB TYPE B JACK").actual_part(
          "Pulse Electronics", "E8144-B02022-L")

        # Crystals:

        self.choice_part("16MHZ;HC49S", "XTAL1150X480X430N", "",
                         "CRYSTAL 16.0000MHZ SMD").actual_part(
          "TXC", "9C-16.000MAAE-T").actual_part(
          "TXC", "9C-16.000MAGJ-T")
        # This alias should be removed:
        self.alias_part("16MHZ;HC49",
                        ["16MHZ;HC49S"], "XTAL1150X480X430N")

        self.choice_part("32.7680KHZ;4SOJ_P5.5", "OSCL550P380X800X250-4N", "",
                         "CRYSTAL 32.7680KHZ 12.5PF SMD").actual_part(
          "Abracon", "ABS25-32.768KHZ-T").actual_part(
          "Abracon", "ABS25-32.768KHZ-6-T").actual_part(
          "ECS", "ECS-.327-12.5-17X-TR").actual_part(
          "Epson", "MC-306 32.7680K-A0:ROHS").actual_part(
          "Epson", "MC-306 32.768K-E3:ROHS").actual_part(
          "Pericom", "G43270021").actual_part(
          "Abracon", "ABS25-32.768KHZ-4-T").actual_part(
          "Fox", "FSRLF327").actual_part(
          "Abracon", "ABS25-32.768KHZ-6-1-T").actual_part(
          "Abracon", "ABS25-32.768KHZ-1-T").actual_part(
          "ECS", "ECS-.327-6-17X-TR").actual_part(
          "ECS", "ECS-.327-6-17X-C-TR").actual_part(
          "Citizen", "CM200C32768AZFT").actual_part(
          "Fox", "FSRLF327-6").actual_part(
          "ECS", "ECS-.327-12.5-17X-C-TR").actual_part(
          "Citizen", "CM200C32768DZFT").actual_part(
          "Citizen", "CM200C32768DZCT")

        # Miscellaneous connectors:

        self.choice_part("VAC_FUSE_SW;10C1", "10C1", "",
                         "MODULE PWR ENTRY SCREW-ON").actual_part(
          "Delta Electronics", "10C2", [
           ("Digi-Key", "603-1262-ND",
            "1/8.28 10/7.454 50/5.6318 100/5.3005")])
        # Diodes:

        self.choice_part("4.56V_ZENER;SOD323F", "SOD323F", "",
                         "DIODE ZENER 4.56V 500MW SOD323F").actual_part(
          "Diodes Inc", "DDZ4V7ASF-7",
          [("Digi-Key", "DDZ4V7ASF-7DICT-ND", "1/.16 10/.143 100/.0781 500/.04802 1000/.03275")])

        self.choice_part("18V_ZENER;SOD123", "SOD-123", "",
                         "DIODE ZENER 18V SOT23",
                         rotation=270.0, feeder_name="18V_ZENER", part_height=0.95).actual_part(
          "Micro Commercial", "MMSZ5248B-TP").actual_part(
          "Micro Commercial", "BZT52C18-TP").actual_part(
          "Diodes", "BZT52C18-7-F").actual_part(
          "Micro Commercial", "MMSZ4705-TP").actual_part(
          "On", "MMSZ18T1G").actual_part(
          "On", "MMSZ5248BT1G").actual_part(
          "On", "MMSZ4705T1G").actual_part(
          "Diodes", "MMSZ5248B-7-F").actual_part(
          "Vishay", "BZT52C18-E3-08").actual_part(
          "Diodes", "DDZ18C-7").actual_part(
          "Vishay", "MMSZ5248B-E3-08").actual_part(
          "Diodes", "DDZ9705-7").actual_part(
          "Central", "CMHZ5248B TR")

        self.choice_part("BRIDGE_35A_1000V;GBPC", "GBPC", "",
                         "RECT BRIDGE GPP 1000V 35A GBPC").actual_part(
          "Comchip Tech", "GBPC3510-G",
          [("Digi-Key", "641-1380-ND", "1/2.54 10/2.296 25/2.05 100/1.845 250/1.64")])

        self.choice_part("SMALL_SCHOTTKY;SOT23-3", "SOT95P280X145-3N", "",
                         "DIODE SCHOTTKY 30V 200MA SOT32-3").actual_part(
          "Diodes Inc", "BAT54-7-F").actual_part(
          "Fairchild", "BAT54").actual_part(
          "Fairchild", "BAT54_D87Z").actual_part(
          "On Semi", "BAT54LT1G").actual_part(
          "NXP", "BAT54,215").actual_part(
          "NXP", "BAT54,235").actual_part(
          "Comchip", "BAT54-G").actual_part(
          "NXP", "BAS70,215").actual_part(
          "Micro Commercial", "BAS40-TP")

        self.choice_part("SMALL_SCHOTTKY;DO214AA", "DO214AA", "",
                         "DIODE SCHOTTKY 15V+ 1A+ DO214AA").actual_part(
          "Vishay", "B360B-E3/52T").actual_part(
          "Vishay", "VS-10BQ015-M3/5BT").actual_part(
          "Micro Commercial", "SK14-LTP").actual_part(
          "Micro Commercial", "SK12-LTP").actual_part(
          "Micro Commercial", "SK16-LTP").actual_part(
          "Fairchild", "SS23").actual_part(
          "Micro Commercial", "SK13-LTP").actual_part(
          "Comchip", "CDBB260-G").actual_part(
          "Comchip", "CDBB280-G").actual_part(
          "Vishay", "VSSB410S-E3/52T").actual_part(
          "Vishay", "VSSB310-E3/52T").actual_part(
          "Fairchild", "SS25").actual_part(
          "Fairchild", "SS22").actual_part(
          "Fairchild", "SS26")
        self.alias_part("SCHOTTKY_1A+_15V+;DO214AA",
                        ["SMALL_SCHOTTKY;DO214AA"], "DIOC1608X55N")

        self.choice_part("SCHOTTKY_3A_200V;DO214AA", "DO214AA", "",
                         "DIODE SCHOTTKY 200V 3A DO214AA").actual_part(
          "Fairchild", "S320").actual_part(
          "Micro Commercial", "SK3200B-LTP")

        # Grommets:

        self.choice_part("GROMMET;GR9.5MM", "GR9.5MM", "",
                         "BUSHING SPLIT 0.260\" NYLON BLACK").actual_part(
          "Essentra", "PGSB-0609A",
          [("Digi-Key", "RPC1251-ND", "1/.18 10/.166 25/.1536 100/.1281")])

        # Hardware:
        self.choice_part(".25IN_SCREW;#4-40", "-", "",
                         "MACHINE SCREW PAN PHILLIPS 4-40").actual_part(
          "Keystone", "9900").actual_part(
          "Keystone", "9427").actual_part(
          "Keystone", "9327").actual_part(
          "Keystone", "9527").actual_part(
          "Pomona", "4862").actual_part(
          "Keystone", "2500").actual_part(
          "Serpac", "6004").actual_part(
          "B&F Fastener", "PMSSS 440 0025 PH")

        # Holes:

        self.choice_part("HOLE;2.5MM", "2_5MM_HOLE", "",
                         "2.5MM HOLE").actual_part("Digi-Key", "RM2X8MM 2701")  # Kludge
        self.choice_part("HOLE;3MM_SLOT", "CASTER_SLOT", "",
                         "3MM SLOT HOLE").actual_part("Digi-Key", "RM3X10MM 2701")  # Kludge
        self.alias_part("HOLE;3MM", [".25IN_SCREW;#4-40"], "3MM_HOLE")
        self.choice_part("HOLE;2MM", "2MM_HOLE", "",
                         "2MM HOLE").actual_part("Digi-Key", "PMS 632 0031 SL")  # Kludge
        self.choice_part("SLOT_HOLE;10X20MM", "10X20MM_HOLE", "",
                         "10X20MM HOLE").actual_part("Digi-Key", "PMS 632 0063 SL")  # Kludge

        # Fiducials:
        self.alias_part("FID;FID", ["M1X40;M1X40"], "Fiducial",
                        feeder_name="FID", rotation=0.0, part_height=0.0)

        # Fuses:

        self.choice_part("FUSE_HOLDER;MINI_ATM", "MINI_ATM", "",
                         "FUSE HOLDER BLADE PCB").actual_part(
          "MPD", "BK-6013")
        self.choice_part("7.5A_FUSE_ATM;7.5A_FUSE_ATM", "-", "",
                         "FUSE AUTO 7.5A 32VDC BLADE MINI").actual_part(
          "Littlefuse", "029707.5WXNV").actual_part(
          "Littlefuse", "099707.5WXN").actual_part(
          "Littlefuse", "029707.5L").actual_part(
          "Eaton", "BK/ATM-7-1/2")
        self.alias_part("7.5A_FUSE;MINI_ATM",
                        ["FUSE_HOLDER;MINI_ATM", "7.5A_FUSE_ATM;7.5A_FUSE_ATM"], "MINI_ATM")

        self.choice_part("3A;LF649", "LF649", "",
                         "FUSE BLOCK CART 250V 6.3A PCB").actual_part(
          "Littelfuse", "64900001039",
          [("Digi-Key", "WK0011-ND", "1/.40 10/.378 25/.348 50/.318 100/.264 250/.24 500/.204")])
        # This alias should be removed:
        self.alias_part("3A;LF349", ["3A;LF649"], "LF649")

        # Inductors:

        self.choice_part("SRR1280-221K;12.5MM", "SRR1280", "",
                         "FIXED IND 220UH 1.6A 400 MOHM").actual_part(
          "Bourns", "SRR1280-221K")

        self.choice_part("?uH;I1X10", "Inductor_1x10", "",
                         "INLINE INDUCTER").actual_part(
          "Bourns", "5258-RC",
          [("Digi-Key", "M8275-ND", "1/1.51 10/1.392 25/1.276 50/1.0904 100/.97440")])

        self.choice_part("CIB10P100NC;1608", "INDC1608X95N", "",
                         "FERRITE CHIP 10 OHM 1000MA 0603").actual_part(
          "Samsung", "CIB10P100NC")

        # Integrated Circuits:

        # Note that the SOT89 package pin bindings to Vin/Gnd/Vout vary between parts.
        # We ultimately selected OGI: 1=>vOut 2=>Gnd 3=>vIn
        self.choice_part("3.3V_LDO;SOT89", "SOT-89-3", "",
                         "IC REG LDO 3.3V SOT89", rotation=270.0,
                         feeder_name="3.3V_LDO", part_height=1.60).actual_part(
          # "Microchip", "MCP1700T-3302E/MB").actual_part(   # Gnd/Vin/Vout GIO
          # "Microchip", "MCP1702T-3302E/MB").actual_part(   # Gnd/Vin/Vout GIO
          # "Microchip", "MCP1703AT-3302E/MB").actual_part(  # Gnd/Vin/Vout GIO
          # "On", "MC78FC33HT1G").actual_part(               # Gnd/Vin/Vout GIO
          # "On", "MC78LC33HT1G").actual_part(               # Gnd/Vin/Vout GIO
          # "Diodes", "AP2204RA-3.3TRG1").actual_part(       # Gnd/Vin/Vout GIO

          # "Diodes", "AP2204R-3.3TRG1").actual_part(        # Vin/Gnd/Vout IGO
          # "Richtek", "RT9058-33GX").actual_part(           # Vin/Gnd/Vout IGO
          # "On", "NCP785AH33T1G").actual_part(              # Vin/Gnd/Vout IGO

          "STM", "L78L33ACUTR").actual_part(                 # Vout/Gnd/Vin OGI  -
          "Torex", "XC6201P332PR-G").actual_part(            # Vout/Gnd/Vin OGI  .7V@160mA *
          "STM", "LD2981ABU33TR").actual_part(               # Vout/Gnd/Vin OGI  .375V@100mA
          "Torex", "XC6216D332PR-G").actual_part(            # Vout/Gnd/Vin OGI  1.7V@100mA
          "Microchip", "MCP1804T-3302I/MB").actual_part(     # Vout/Gnd/Vin OGI  1.7V@100mA
          "STM", "L78L33ABUTR").actual_part(                 # Vout/Gnd/Vin OGI  -
          "STM", "LD2981CU33TR")                             # Vout/Gnd/Vin OGI 375@100mA

        self.choice_part("15V_REG;SOT89", "SOT-89-3", "",
                         "IC REG LINEAR 15V 100MA SOT89-3", rotation=270.0).actual_part(
          "STM", "L78L15ACUTR").actual_part(                 # OGI
          "STM", "L78L15ABUTR").actual_part(                 # OGI
          "TI", "UA78L15ACPK")
        self.choice_part("18V_REG;SOT89", "SOT-89-3", "",
                         "IC REG LINEAR 18V 100MA SOT89-3",
                         rotation=270.0, feeder_name="18V_REG", part_height=1.60).actual_part(
          "STM", "L78L18ACUTR")                              # OGI

        self.choice_part("5V_REG;SOT89", "SOT-89-3", "",
                         "IC REG LINEAR 5V 100MA SOT89-3",
                         rotation=90.0, feeder_name="5V_REG/LDO", part_height=1.60).actual_part(
          "ON Semiconductor", "KA78L05AIMTF").actual_part(
          "STM", "L78L05ABUTR").actual_part(
          "STM", "L78L05ACUTR").actual_part(
          "On Semiconductor", "MC78L05ACHX").actual_part(
          "Diodes Incorporated", "ZXTR2005Z-13").actual_part(
          "Diodes Incorporated", "ZXTR2005Z-7").actual_part(
          # "NJR", "NJM78L05UA-TE1").actual_part(
          "Richtek", "RT9058-50GX").actual_part(
          "ON Semiconductor", "NCP785AH50T1G").actual_part(
          "Diodes Incorporated", "AS78L05RTR-E1").actual_part(
          "On Semiconductor", "NCV4275ADS50R4G").actual_part(
          "Diodes Incorporated", "AP7381-50Y-13").actual_part(
          "On Semiconductor", "NCV4276BDS50R4G").actual_part(
          "On Semiconductor", "NCV8675DS50R4G")

        self.choice_part("5V_LDO;SOT89", "SOT-89-3", "",
                         "IC REG LDO 5V SOT89",
                         rotation=90.0, feeder_name="5V_REG/LDO", part_height=1.60).actual_part(
          # "Diodes", "AP2204R-5.0TRG1").actual_part(           # Vin/Gnd/Vout  IGO
          # "Richtek", "RT9064-50GX").actual_part(              # Vin/Gnd/Vout  IGO

          # "IC REG LDO 5V SOT89").actual_part(
          # "Microchip", "MCP1700T-5002E/MB").actual_part(      # Gnd/Vin/Vout  GIO
          # "Diodes", "AP2204RA-5.0TRG1").actual_part(          # Gnd/Vin/Vout  GIO
          # "Microchip", "MCP1702T-5002E/MB").actual_part(      # Gnd/Vin/Vout  GIO
          # "Microchip", "MCP1703AT-5002E/MB").actual_part(     # Gnd/Vin/Vout  GIO
          # "Diodes", "ZXTR2005Z-13").actual_part(              # Gnd/Vin/Vout  GIO
          # "Diodes", "ZXTR2005Z-7").actual_part(               # Gnd/Vin/Vout  GIO
          # "On", "MC78LC50HT1G").actual_part(                  # Gnd/Vin/Vout  GIO

          # "TI", "UA78L05AIPK").actual_part(                   # Vout/Gnd/Vin  OGI  1.7V@40mA
          # "Micro Commercial", "MC78L05F-TP").actual_part(     # Vout/Gnd/Vin  OGI  1.7V@40mA
          # "TI", "UA78L05CPK").actual_part(                    # Vout/Gnd/Vin  OGI  1.7V@40mA
          # "Fairchild", "MC78L05ACHX").actual_part(            # Vout/Gnd/Vin  OGI  -
          # "NJR", "NJM78L05UA-TE1").actual_part(               # Vout/Gnd/Vin  OGI  -
          # "Fairchild", "KA78L05AMTF").actual_part(            # Vout/Gnd/Vin  OGI  -
          # "Fairchild", "KA78L05AIMTF").actual_part(           # Vout/Gnd/Vin  OGI  -
          # "STM", "L78L05ABUTR").actual_part(                  # Vout/Gnd/Vin  OGI  -
          # "STM", "L78L05ACUTR").actual_part(                  # Vout/Gnd/Vin  OGI  -
          # "Torex", "XC6201P502PR-G")                          # Vout/Gnd/Vin  OGI  .6V@200mA *

          "Taiwan Semi", "TS78L05ACY RMG").actual_part(        # OGI
          # "Diodes Inc", "ZXTR2005Z-13").actual_part(          # GIO
          # "Diodes Inc", "ZXTR2005Z-7").actual_part(           # GIO
          "Micro Commercial", "MC78L05F-TP").actual_part(      # OGI
          "NJR", "NJM78L05UA-TE1")                             # OGI

        self.choice_part("3.3V_LDO;SOT223", "SOT-223", "",
                         "IC REG LDO 3.3V SOT223-3").actual_part(
          "Diodes", "AP2114H-3.3TRG1").actual_part(
          "Richtek", "RT9164A-33GG").actual_part(
          "STM", "LD1117S33TR").actual_part(
          "STM", "LD1117S33CTR").actual_part(
          "Exar", "SPX1117M3-L-3-3/TR").actual_part(
          "Diodes", "AP2111H-3.3TRG1").actual_part(
          "Diodes", "AP7361-33E-13").actual_part(
          "On", "NCP1117LPST33T3G").actual_part(
          "Diodes", "AP7361C-33E-13").actual_part(
          "STM", "LD1117AS33TR").actual_part(
          "ON", "MC33375ST-3.3T3G").actual_part(
          "Microchip", "MIC5233-3.3YS-TR").actual_part(
          "Microchip", "MIC5233-3.3YS")

        self.choice_part("AP2210N-3.3T;SOT-23-3", "extra-nominal:SOT95P280X145-3N", "",
                         "3.3V LDO").actual_part(
          "Diodes Inc", "AP2210N-3.3TRG1").actual_part(
          "Microchip", "MCP1700T-3302E/TT").actual_part(
          "Microchip", "MCP1700T-3302E/MB")

        self.choice_part("AS5601;SOIC8", "SOIC127P600X175-8N", "",
                         "ENCODER 12BIT PROGR A/B 8SOIC", rotation=0.0).actual_part(
          "AMS", "AS5601-ASOM")

        self.choice_part("MIC7221;SOT23-5", "SOT23-5", "",
                         "COMPARATOR R-R SOT-23-5").actual_part(
          "Microchip", "MIC7221YM5-TR")

        # self.choice_part("74xHC08;SOIC8", "SOIC127P600X175-14N", "",
        #  "IC GATE AND 4CH 2-INP 14-SOIC").actual_part(
        #  "Fairchild", "MM74HCT08MX").actual_part(
        #  "Fairchild", "74VHCT08AMX").actual_part(
        #  "TI", "SN74HC08DR").actual_part(
        #  "TI", "SN74HCT08DR").actual_part(
        #  "TI", "SN74AHCT08DR").actual_part(
        #  "TI", "SN74AHC08DR").actual_part(
        #  "Fairchild", "MM74HC08MX").actual_part(
        #  "TI", "CD74HC08M96").actual_part(
        #  "TI", "CD74HCT08M96").actual_part(
        #  "Fairchild", "74VHC08MX")

        self.choice_part("74HC08;SOIC8", "SOIC127P600X175-14N", "",
                         "IC GATE AND 4CH 2-INP 14-SOIC",
                         rotation=0.0, feeder_name="74HC08", part_height=1.75).actual_part(
          "Nexperia", "74HC08D,652").actual_part(
          "Nexperia", "74HC08D-Q100,118").actual_part(
          "Toshiba", "74HC08D").actual_part(
          "TI", "SN74HC08D").actual_part(
          "Nexperia", "74HC08D,653").actual_part(
          "On Semi", "MC74HC08ADR2G").actual_part(
          "TI", "SN74HC08DR").actual_part(
          "TI", "SN74HC08DRG4").actual_part(
          "TI", "CD74HC08M96").actual_part(
          "On Semi", "MM74HC08MX").actual_part(
          "On Semi", "MM74HC08M").actual_part(
          "TI", "CD74HC08M").actual_part(
          "TI", "CD74HC08MT").actual_part(
          "TI", "CD74HC08QM96EP")

        self.choice_part("74xHC1G135;TSOP5", "TSOP-5", "",
                         "IC GATE NAND 1CH 2-INP 5TSOP").actual_part(
          "On Semi", "M74VHC1G135DTT1G")

        self.choice_part("74AHC1G04;SOT753", "SOT95P280X145-5N", "",
                         "IC INVERTER 1CH 1-INP 5TSOP").actual_part(
          "Nexperia", "74AHC1G04GV,125").actual_part(
          "Diodes Inc", "74AHC1GU04W5-7").actual_part(
          "TI", "SN74AHC1GU04DBVR").actual_part(
          "Nexperia", "74AHC1GU04GV,125").actual_part(
          "TI", "SN74AHC1G04DBVRG4").actual_part(
          "TI", "SN74AHC1G04DBVR").actual_part(
          "TI", "SN74AHC1G04DBVT").actual_part(
          "TI", "SN74AHC1GU04DBVT")

        self.choice_part("74HC32;SOIC14", "SOIC127P600X175-14N", "",
                         "IC GATE OR 4CH 2-INP 14-SOIC", rotation=0.0).actual_part(
          "Toshiba", "74HC32D(BJ)").actual_part(
          "TI", "SN74HC32D").actual_part(
          "On Semi", "MC74HC32ADG").actual_part(
          "Fairchild", "MM74HC32M").actual_part(
          "On Semi", "MC74HC32ADR2G").actual_part(
          "Fairchild", "MM74HC32MX").actual_part(
          "TI", "SN74HC32DR").actual_part(
          "TI", "SN74HC32DRG4").actual_part(
          "TI", "CD74HC32M").actual_part(
          "TI", "SN74HC32DT")

        self.choice_part("74HC1G04;SOT353", "SOT353", "",
                         "IC INVERTER 1CH 1-INP SOT353        ").actual_part(
          "Nexperia", "74HC1G04GW,125").actual_part(
          "Nexperia", "74HC1GU04GW,125").actual_part(
          "On Semi", "MC74HC1GU04DFT2G").actual_part(
          "On Semi", "MC74HC1GU04DFT1G").actual_part(
          "On Semi", "MC74HC1G04DFT2G").actual_part(
          "On Semi", "MC74HC1G04DFT1G").actual_part(
          "Nexperia", "74HC1G04GW-Q100H")

        self.choice_part("74HC1G14;SOT23-5", "SOT95P280X145-5N", "",
                         "IC INVERTER SGL SCHMITT SOT23-5").actual_part(
          "On Semi", "MC74HC1G14DTT1G", [
           ("Digi-Key", "MC74HC1G14DTT1GOSCT-ND",
            "1/.39 10/.319 100/.1691 500/.11116 1000/.07574")])

        self.choice_part("74HC21;SOIC14", "SOIC127P600X175-14N", "",
                         "IC GATE AND 2CH 4-INP 14SOP", rotation=0.0).actual_part(
           "Toshiba", "74HC21D").actual_part(
           "TI", "SN74HC21D").actual_part(
           "Nexperia", "74HC21D,653").actual_part(
           "Nexperia", "74HC21D,652").actual_part(
           "TI", "SN74HC21DR").actual_part(
           "TI", "CD74HC21M").actual_part(
           "TI", "CD74HC21M96")

        self.choice_part("74HC74;SOIC14",  "SOIC127P600X175-14N", "",
                         "IC FF D-TYPE DUAL 1BIT 14SO", rotation=0.0).actual_part(
           "Nexperia", "74HC74D,652").actual_part(
           "Nexperia", "74HC74D,653").actual_part(
           "TI", "SN74HC74D").actual_part(
           "On Semi", "MC74HC74ADG").actual_part(
           "On Semi", "MC74HC74ADR2G").actual_part(
           "TI", "SN74HC74DR").actual_part(
           "TI", "CD74HC74M96").actual_part(
           "TI", "SN74HC74QDRQ1").actual_part(
           "On Semi", "MM74HC74AMX").actual_part(
           "TI", "SN74HC74QDRG4Q1").actual_part(
           "On Semi", "MM74HC74AM").actual_part(
           "Toshiba", "74HC74D").actual_part(
           "TI", "CD74HC74M").actual_part(
           "TI", "CD74HC74MT")

        self.choice_part("74HC74;TTSOP14", "SOP65P640X120-14N", "",
                         "IC FF D-TYPE DUAL 1BIT 14TSSOP").actual_part(
          "On Semi", "MC74HC74ADTR2G").actual_part(
          "TI", "SN74HC74PW").actual_part(
          "On Semi", "MM74HC74AMTCX").actual_part(
          "Nexperia", "74HC74PW,112").actual_part(
          "TI", "SN74HC74PWR").actual_part(
          "Nexperia", "74HC74PW,118").actual_part(
          "TI", "SN74HC74QPWRQ1").actual_part(
          "TI", "SN74HC74QPWRG4Q1").actual_part(
          "TI", "SN74HC74MPWREP").actual_part(
          "TI", "SN74HC74PWT")

        self.choice_part("74HC123;TTSOP16", "SOP65P640X120-16N", "",
                         "IC DUAL RETRIG MULTIVIB 16-TSSOP").actual_part(
          "Nexperia", "74HC123PW,118").actual_part(
          "Nexperia", "74HC123PW,112").actual_part(
          "On Semi", "MC74HC4538ADTR2G").actual_part(
          "TI", "CD74HC123PW").actual_part(
          "TI", "CD74HC123PWR").actual_part(
          "TI", "CD74HC221PWR").actual_part(
          "TI", "CD74HC4538PWR").actual_part(
          "TI", "CD74HC221PW").actual_part(
          "TI", "CD74HC4538PW").actual_part(
          "TI", "CD74HC221PWT").actual_part(
          "TI", "CD74HC4538PWT")

        self.choice_part("74HC1G175;SOT23-6", "SOT95P280X145-6N", "",
                         "IC D-TYPE POS TRG SNGL SOT23-6").actual_part(
          "TI", "SN74LVC1G175DBVR").actual_part(
          "TI", "SN74LVC1G175DBVT")

        self.choice_part("74HC595;TTSOP16", "SOP65P640X120-16N", "",
                         "IC 8BIT SHIFT REGISTER 16TSSOP").actual_part(
          "Nexperia", "74HC595PW,112").actual_part(
          "Nexperia", "74HC595PW-Q100,118").actual_part(
          "Nexperia", "74HC595PW,118").actual_part(
          "On", "MC74HC595ADTG").actual_part(
          "Fairchild", "MM74HC595MTC").actual_part(
          "Diodes", "74HC595T16-13").actual_part(
          "On", "MC74HC595ADTR2G").actual_part(
          "Fairchild", "MM74HC595MTCX").actual_part(
          "TI", "SN74HC595PWR").actual_part(
          "STM", "M74HC595YTTR").actual_part(
          "TI", "SN74HC595PW")

        self.choice_part("ATMEGA328;QFP32", "QFP80P900X900X120-32N", "",
                         "IC MCU 8BIT 32KB FLASH 32QFP").actual_part(
          "Atmel", "ATMEGA328-AUR",
          [("Digi-Key", "ATMEGA328-AURCT-ND", "1/3.38 10/3.015 25/2.7136 100/2.4723 250/2.23112")])

        self.choice_part("ATMEGA2560_16MHZ;QFP100", "QFP50P1600X1600X120-100N", "",
                         "IC MCU 8BIT 256KB FLASH 100TQFP").actual_part(
          "Atmel", "ATMEGA2560-16AU")

        self.choice_part("L293;DIP16", "DIP-16__300", "",
                         "IC MOTOR DRIVER PAR 16-DIP").actual_part(
          "TI", "L293DNE").actual_part(
          "ST Micro", "L293D").actual_part(
          "TI", "L293NE").actual_part(
          "TI", "L293DNEE4").actual_part(
          "ST Micro", "L293B")

        self.choice_part("L293;SOIC20", "SOIC127P1032X265-20N", "",
                         "IC MOTOR DRIVER PAR 20-SOIC", rotation=0.0).actual_part(
          "ST Micro", "L293DD")

        self.choice_part("LM311;SOIC8", "SOIC127P600X173-8N", "",
                         "IC COMPARATOR SGL 8SOIC").actual_part(
          "TI", "LM311DR", [
           ("Digi-Key", "296-1388-1-ND",
            "1/.47000 10/.361 100/.19 1000/.17")]).actual_part(
          "On Semi", "LM311DR2G").actual_part(
          "TI", "LM311DRG4").actual_part(
          "TI", "LM311MX/NOPB")

        self.choice_part("MC33883;SOIC20", "SOIC127P1032X265-20N", "",
                         "IC H-BRIDGE PRE-DRIVER 20SOIC",
                         rotation=0.0, feeder_name="MC33883", part_height=2.65).actual_part(
          "NXP", "MC33883HEGR2")

        self.choice_part("MCP2562;SOIC8", "SOIC127P600X175-8N", "",
                         "IC TXRX CAN 8SOIC", rotation=0.0,
                         feeder_name="MCP2562", part_height=1.75).actual_part(
          "Microchip", "MCP2562T-E/SN",
          [("Digi-Key", "MCP2562T-E/SNCT-ND", "1/1.08 10/.90 25/.75 100/.68")])
        self.choice_part("MCP7940;SOIC8", "SOIC127P600X175-8N", "",
                         "IC RTC CLK/CALENDAR I2C 8-SOIC", rotation=0.0).actual_part(
          "Microchip", "MCP7940M-I/SN").actual_part(
          "Microchip", "MCP7940N-I/SN").actual_part(
          "Microchip", "MCP7940N-E/SN").actual_part(
          "Microchip", "MCP79400-I/SN").actual_part(
          "Microchip", "MCP79402-I/SN").actual_part(
          "Microchip", "MCP79401-I/SN")
        self.choice_part("CAT24C32;SOIC8", "SOIC127P600X175-8N", "",
                         "IC EEPROM 32KBIT 400KHZ 8SOIC", rotation=0.0).actual_part(
          "ON Semiconductor", "CAT24C32WI-GT3")

        # LED's:

        self.choice_part("GREEN_LED;1608", "DIOC1608X55N", "",
                         "LED 0603 GRN WATER CLEAR", rotation=90.0).actual_part(
          "Wurth", "150060GS75000", [
           ("Digi-Key", "732-4971-1-ND",
            "1/.24 50/.21 100/.192 500/.17400 1000/.162")]).actual_part(
          "Wurth", "150060VS75000").actual_part(
          "Rohm", "SML-310MTT86").actual_part(
          "Rohm", "SML-310FTT86").actual_part(
          "Rohm", "SML-310PTT86").actual_part(
          "Lite-On", "LTST-C190KGKT").actual_part(
          "Lite-On", "LTST-C190GKT").actual_part(
          "Lite-On", "LTST-C191KGKT").actual_part(
          "Lite-On", "LTST-C191GKT").actual_part(
          "Lite-On", "LTST-C193KGKT-5A").actual_part(
          "Lite-On", "LTST-C194KGKT").actual_part(
          "Lite-On", "LTST-C191TGKT").actual_part(
          "Lite-On", "LTST-C190TGKT").actual_part(
          "Lite-On", "LTST-C193TGKT-5A").actual_part(
          "Lite-On", "LTST-C194TGKT")
        self.alias_part("LED;1608",
                        ["GREEN_LED;1608"], "DIOC1608X55N")
        self.alias_part("GRN_LED;1608",
                        ["GREEN_LED;1608"], "DIOC1608X55N",
                        feeder_name="GRN_LED", rotation=90.0, part_height=0.80)

        self.choice_part("GRN_LED;T1", "T1_LED", "",
                         "LED GRN 3MM ROUND").actual_part(
           "Everlight", "MV54643").actual_part(
           "Everlight", "HLMP1540").actual_part(
           "Lite-On", "LTL-4231").actual_part(
           "Lite-On", "LTL-4232N").actual_part(
           "Lite-On", "LTL-4231N-1").actual_part(
           "Lumex", "SSL-LX3044GD").actual_part(
           "Kingbright", "WP710A10PGD").actual_part(
           "Lumex", "SSL-LX3044GT").actual_part(
           "Lumex", "SSL-LX3054GD").actual_part(
           "Broadcom", "HLMP-1503").actual_part(
           "Broadcom", "HLMP-1521").actual_part(
           "Lumex", "SSL-LX3044PGD").actual_part(
           "Kingbright", "WP132XPGD")

        self.choice_part("CREE_3050;CXA3050", "CXA3050", "",
                         "CREE XLAMP CXA3050 23MM WHITE").actual_part(
          "Cree", "CXA3050-0000-000N0HW440F")

        self.choice_part("SI8055;QSOP16", "SOP63P602X173-16N", "",
                         "DGTL ISO 1KV 5CH GEN PURP 16QSOP",
                         rotation=0.0, feeder_name="SI8055", part_height=1.75).actual_part(
          "Silicon Labs", "SI8055AA-B-IU")

        self.choice_part("OPTOISO2;SOIC8", "SOIC127P600X175-8N", "",
                         "OPTOISOLATOR 4KV 2CH TRANS 8SOIC",
                         rotation=0.0, feeder_name="OPTOISO2", part_height=3.20).actual_part(
          "Vishay", "VOD205T").actual_part(
          "Vishay", "VOD206T").actual_part(
          "Vishay", "VOD207T").actual_part(
          "On Semi", "MOCD211M").actual_part(
          "On Semi", "MOCD217M").actual_part(
          "On Semi", "MOCD208M").actual_part(
          "On Semi", "MOCD217R2M").actual_part(
          "On Semi", "MOCD211R2M").actual_part(
          "Vishay", "VOD217T").actual_part(
          "Vishay", "VOD213T").actual_part(
          "On Semi", "MOCD208R2M").actual_part(
          "On Semi", "MOCD213R2M").actual_part(
          "On Semi", "MOCD213M")

        # Slot interrupters:

        self.choice_part("OPB200;OPB200", "OPB200", "",
                         "SENSR OPTO SLOT 5.1MM TRANS THRU").actual_part(
          "TE Electronics/Optek", "OPB200")

        # Potentiometers:

        self.choice_part("10K;9MM", "10X5MM_TRIM_POT", "",
                         "TRIMMER 10K OHM 0.2W PC PIN").actual_part(
          "Bourns", "3319P-1-103", [
           ("Digi-Key", "3319P-103-ND",
            "1/.40 10/.366 25/.33 50/.319 100/.308 250/.286")]).actual_part(
          "Bourns", "3309P-1-103")

        # Power Supplies:

        self.choice_part("9V_444MA_4W;RAC04", "RAC04", "",
                         "AC/DC CONVERTER 9V 4W").actual_part(
          "Recom Power", "RAC04-09SC/W", [
           ("Digi-Key", "945-2211-ND",
            "1/14.35 5/14.146 10/13.94 50/12.71 100/12.30")])

        # Resistors:

        self.choice_part("0;1608", "RESC1608X55N", "",
                         "RES SMD 0.0 OHM JUMPER 1/10W",
                         rotation=90.0, feeder_name="0", part_height=0.45).actual_part(
          "Vishay Dale", "CRCW06030000Z0EA").actual_part(
          "Rohm", "MCR03EZPJ000").actual_part(
          "Panasonic", "ERJ-3GEY0R00V").actual_part(
          "Stackpole", "RMCF0603ZT0R00").actual_part(
          "Bourns", "CR0603-J/-000ELF")
        self.choice_part("10;1608", "RESC1608X55N", "",
                         "RES SMD 10 5% 1/10W 1608",
                         rotation=90.0, feeder_name="10", part_height=0.45).actual_part(
          "Yageo", "RC0603FR-0710RL").actual_part(
          "Yageo", "RC0603JR-0710RL").actual_part(
          "Stackpole", "RMCF0603JT10R0").actual_part(
          "Panasonic", "ERJ-3GEYJ100V").actual_part(
          "Stackpole", "RMCF0603FT10R0").actual_part(
          "Bourns", "CR0603-JW-100ELF").actual_part(
          "Samsung", "RC1608J100CS").actual_part(
          "Yageo", "RC0603JR-0710RP").actual_part(
          "Yageo", "AC0603FR-0710RL").actual_part(
          "Stackpole", "RNCP0603FTD10R0").actual_part(
          "Bourns", "CR0603-FX-10R0GLF").actual_part(
          "Yageo", "RT0603FRE0710RL")
        self.choice_part("0.20_1W;6432", "RESC6432X70N", "",
                         "RES SMD 0.02 OHM 1% 1W 6432").actual_part(
          "TE", "2176057-8", [
            ("Digi-Key", "A109677CT-ND",
             "1/.30 10/.27 100/.241")]).actual_part(
          "TT/Welwyn", "LRMAM2512-R02FT4").actual_part(
          "Bourns", "CRA2512-FZ-R020ELF").actual_part(
          "Yageo", "PE2512FKE070R02L").actual_part(
          "TT/Welwyn", "LRMAP2512-R02FT4").actual_part(
          "Bourns", "CRF2512-FZ-R020ELF").actual_part(
          "Yageo", "RL2512FK-070R02L").actual_part(
          "TT/IRC", "LRC-LRF2512LF-01-R020F").actual_part(
          "Stackpole", "CSRN2512FK20L0")
        self.choice_part("47;1608", "RESC1608X55N", "",
                         "RES SMD 50 5% 1/10W 1608", rotation=90.0).actual_part(
          "Yageo", "RC0603JR-0747RL").actual_part(
          "Stackpole", "RMCF0603JT47R0").actual_part(
          "Yageo", "RC0603FR-0747RL").actual_part(
          "Panasonic", "ERJ-3GEYJ470V").actual_part(
          "Panasonic", "ERJ-3EKF47R0V").actual_part(
          "Samsung", "RC1608F470CS").actual_part(
          "Vishay Dale", "CRCW060347R0JNEA").actual_part(
          "Yageo", "AC0603FR-0747RL").actual_part(
          "Yageo", "AC0603JR-0747RL").actual_part(
          "Bourns", "CR0603-JW-470GLF").actual_part(
          "Bourns", "CR0603-JW-470ELF").actual_part(
          "Vishay Dale", "CRCW060347R0FKEA")
        self.choice_part("120;1608", "RESC1608X55N", "",
                         "RES SMD 120 OHM 5% 1/10W 1608",
                         rotation=90.0, feeder_name="120", part_height=0.45).actual_part(
          "Vishay Dale", "CRCW0603120RFKEA").actual_part(
          "Rohm", "MCR03ERTF1200").actual_part(
          "Samsung", "RC1608J121CS").actual_part(
          "Samsung", "RC1608F121CS").actual_part(
          "Rohm", "KTR03EZPF1200")
        self.choice_part("470;1608", "RESC1608X55N", "",
                         "RES SMD 470 5% 1/10W 1608",
                         rotation=90.0, feeder_name="470", part_height=0.45).actual_part(
          "Vishay Dale", "CRCW0603470RJNEA", [
           ("Digi-Key", "541-470GCT-ND",
            "10/.074 50/.04 200/.02295 1000/.01566")]).actual_part(
          "Samsung", "RC1608J471CS").actual_part(
          "Rohm", "KTR03EZPJ471")
        self.choice_part("1K;1608", "RESC1608X55N", "",
                         "RES SMD 1K 5% 1/10W 0603", rotation=90.0).actual_part(
          "Rohm", "MCR03ERTJ102").actual_part(
          "Yageo", "RC0603JR-071KP").actual_part(
          "Samsung", "RC1608J102CS").actual_part(
          "Rohm", "TRR03EZPJ102").actual_part(
          "Rohm", "KTR03EZPJ102")
        self.choice_part("4K7;1608", "RESC1608X55N", "",
                         "RES SMD 4.7K 5% 1/10W 1608",
                         rotation=90.0, feeder_name="4.7k", part_height=0.45).actual_part(
          "Yageo", "RC0603JR-074K7L").actual_part(
          "Panasonic", "ERJ-3GEYJ472V").actual_part(
          "Rohm", "MCR03EZPJ472").actual_part(
          "Stackpole", "RMCF0603JT4K70").actual_part(
          "Bourns", "CR0603-JW-472ELF").actual_part(
          "Samsung", "RC1608J472CS").actual_part(
          "Yageo", "RC0603JR-074K7P").actual_part(
          "Rohm", "TRR03EZPJ472").actual_part(
          "Bourns", "CR0603-JW-472GLF")
        self.choice_part("10K;1608", "RESC1608X55N", "",
                         "RES SMD 10K OHM 5% 1/10W 1608", rotation=90.0).actual_part(
          "Yageo", "RC0603JR-0710KL").actual_part(
          "Panasonic", "ERJ-3GEYJ103V").actual_part(
          "Rohm", "MCR03ERTJ103").actual_part(
          "Rohm", "MCR03EZPJ103").actual_part(
          "Stackpole", "RMCF0603JT10K0").actual_part(
          "Bourns", "CR0603-JW-103ELF").actual_part(
          "Samsung", "RC1608J103CS").actual_part(
          "Bourns", "CR0603-JW-103GLF").actual_part(
          "Rohm", "TRR03EZPJ103")
        self.choice_part("22K;1608", "RESC1608X55N", "",
                         "RES SMD 22K OHM 5% 1/10W 1608", rotation=90.0).actual_part(
          "Vishay Dale", "CRCW060322K0JNEA").actual_part(
          "Vishay Beyschlag", "MCT06030C2202FP500").actual_part(
          "Vishay Dale", "CRCW060322K0FKEA").actual_part(
          "Yageo", "RC0603JR-0722KL").actual_part(
          "Yageo", "RC0603FR-0722KL").actual_part(
          "Rohm", "MCR03ERTF2202").actual_part(
          "Stackpole", "RMCF0603JT22K0").actual_part(
          "Panasonic", "ERJ-3GEYJ223V").actual_part(
          "Stackpole", "RMCF0603FT22K0").actual_part(
          "Panasonic", "ERJ-3EKF2202V")
        self.choice_part("100K;1608", "RESC1608X55N", "",
                         "RES SMD 100K OHM 5% 1/10W 1608",
                         rotation=90.0, feeder_name="100K", part_height=0.45).actual_part(
          "Vishay Dale", "CRCW0603100KJNEAIF", [
             ("Digi-Key", "541-100KAQCT-ND",
              "1/.45 10/.345 25/.2628 50/.1952 100/.1451")]).actual_part(
          "Yageo", "RC0603JR-07100KL").actual_part(
          "Panasonic", "ERJ-3GEYJ104V").actual_part(
          "Stackpole", "RMCF0603JT100K").actual_part(
          "Bourns", "CR0603-JW-104ELF").actual_part(
          "Samsung", "RC1608J104CS").actual_part(
          "Yageo", "AC0603JR-07100KL").actual_part(
          "Stackpole", "RMCF0603JG100K").actual_part(
          "Bourns", "CR0603-JW-104GLF").actual_part(
          "Yageo", "RC0603JR-10100KL").actual_part(
          "Rohm", "KTR03EZPJ104")

        # Switches
        self.choice_part("DPDT_4A;2X3_8.65X7.92", "GF_426_0020", "",
                         "SWITCH SLIDE DPDT 4A 125V").actual_part(
          "CW Industries", "GF-426-0020")

        # Test Points:
        # (These need to be moved to `prices.py` on a per project basis):

        self.alias_part("0.5V;M1X1",
                        ["M1X1;M1X1"], "Pin_Header_Straight_1x01")
        self.alias_part("170VDC_FUSED;M1X1",
                        ["M1X1;M1X1"], "Pin_Header_Straight_1x01")
        self.alias_part("170VDC_IN;M1X1",
                        ["M1X1;M1X1"], "Pin_Header_Straight_1x01")
        self.alias_part("CAN_RDX;M1X1",
                        ["M1X1;M1X1"], "Pin_Header_Straight_1x01")
        self.alias_part("CLEAR;M1X1",
                        ["M1X1;M1X1"], "Pin_Header_Straight_1x01")
        self.alias_part("CURRENT_SENSE;M1X1",
                        ["M1X1;M1X1"], "Pin_Header_Straight_1x01")
        self.alias_part("CURRENT_SET;M1X1",
                        ["M1X1;M1X1"], "Pin_Header_Straight_1x01")
        self.alias_part("GATE;M1X1",
                        ["M1X1;M1X1"], "Pin_Header_Straight_1x01")
        self.alias_part("GND;M1X1",
                        ["M1X1;M1X1"], "Pin_Header_Straight_1x01")
        self.alias_part("+5V;M1X1",
                        ["M1X1;M1X1"], "Pin_Header_Straight_1x01")
        self.alias_part("INDUCTOR_HIGH;M1X1",
                        ["M1X1;M1X1"], "Pin_Header_Straight_1x01")
        self.alias_part("INDUCTOR_LOW;M1X1",
                        ["M1X1;M1X1"], "Pin_Header_Straight_1x01")
        self.alias_part("MODULATE1;M1X1",
                        ["M1X1;M1X1"], "Pin_Header_Straight_1x01")
        self.alias_part("MODULATE2;M1X1",
                        ["M1X1;M1X1"], "Pin_Header_Straight_1x01")
        self.alias_part("RESET;M1X1",
                        ["M1X1;M1X1"], "Pin_Header_Straight_1x01")
        self.alias_part("RXD0;M1X1",
                        ["M1X1;M1X1"], "Pin_Header_Straight_1x01")
        self.alias_part("STOP;M1X1",
                        ["M1X1;M1X1"], "Pin_Header_Straight_1x01")
        self.alias_part("TRIGGER;M1X1",
                        ["M1X1;M1X1"], "Pin_Header_Straight_1x01")
        self.alias_part("TXD0;M1X1",
                        ["M1X1;M1X1"], "Pin_Header_Straight_1x01")
        self.alias_part("XTAL1;M1X1",
                        ["M1X1;M1X1"], "Pin_Header_Straight_1x01")

        self.alias_part("FTDI;M1X6",
                        ["M1X6;M1X6"], "Pin_Header_Straight_1x06")
        self.alias_part("ISP_CONN;M2X3",
                        ["M2X3;M2X3"], "Pin_Header_Straight_2x03")
        self.alias_part("ID6;M2X6",
                        ["M2X6;M2X6"], "Pin_Header_Straight_2x06")

        # Transistors:

        self.choice_part("BSS138;SOT23", "SOT95P280X145-3N", "",
                         "MOSFET N-CH 50V+ 200MA+ SOT23").actual_part(
          "Fairchild", "BSS138L", [
            ("Digi-Key", "BSS138CT-ND",
             "1/.23 10/.207 25/.1492 100/.1161 250/.07292")]).actual_part(
          "Fairchild", "BSS138").actual_part(
          "NXP", "BSS138P,215").actual_part(
          "ON Semi", "BSS138LT1G").actual_part(
          "On Semi", "BSS138LT3G").actual_part(
          "Fairchild", "BSS138_D87Z").actual_part(
          "Diodes Inc", "BSS138-7-F").actual_part(
          "NXP", "BSS138BK,215").actual_part(
          "NXP", "BSS138AKAR").actual_part(
          "Fairchild", "BSS138K").actual_part(
          "Diodes Inc", "BSS138TA")

        self.choice_part("200V_NFET;DPAK", "DPAK", "",
                         "MOSFET N-CH 200V DPAK", rotation=180.0).actual_part(
          "Fairchild", "FDD7N20TM", [
           ("Digi-Key", "FDD7N20TMCT-ND",
            "1/.62 10/.542 25/.4792 100/.41760 250/.36348")]).actual_part(
          "Fairchild", "FDD6N25TM").actual_part(
          "Fairchild", "FDD3N40TM").actual_part(
          "Vishay Siliconix", "IRFR220TRPBF").actual_part(
          "Vishay Siliconix", "IRFR220TRLPBF").actual_part(
          "On Semi", "NDD03N60ZT4G").actual_part(
          "Fairchild", "FQD4N25TM_WS").actual_part(
          "ST Micro", "STD1NK60T4").actual_part(
          "ST Micro", "STD1NK80ZT4").actual_part(
          "On Semi", "NDD04N60ZT4G")

        self.choice_part("NFET_10A;TO220", "TO-220_FET-GDS_Horizontal_LargePads", "",
                         "MOSFET N-CH >10A TO-220").actual_part(
          "Fairchild", "FQP13N10").actual_part(
          "Fairchild", "FQP13N10L").actual_part(
          "Toshiba", "TK40E06N1,S1X").actual_part(
          "Fairchild", "FQP33N10").actual_part(
          "Toshiba", "TK30E06N1,S1X").actual_part(
          "Fairchild", "FQP17P10").actual_part(
          "Alpha", "AOTF2910L").actual_part(
          "Fairchild", "FQP19N20C").actual_part(
          "Fairchild", "FQP15P12").actual_part(
          "Fairchild", "FQP27P06").actual_part(
          "Fairchild", "FDP55N06").actual_part(
          "Fairchild", "MTP3055VL").actual_part(
          "TI", "CSD18504KCS")

        position_dy = 2.625
        self.choice_part("NFET_10A;DPAK", "DPAK", "",
                         "MOSFET N-CH >10A DPAK", rotation=180.0, feeder_name="NFET_10A",
                         part_height=2.40, pick_dy=6.65 - position_dy).actual_part(
          "Diodes", "DMN6040SK3-13").actual_part(
          "Alpha & Omega", "AOD514").actual_part(
          "Diodes", "DMN3010LK3-13").actual_part(
          "Taiwan", "TSM090N03ECP ROG").actual_part(
          "Diodes", "DMN3016LK3-13").actual_part(
          "Diodes", "DMG4800LK3-13").actual_part(
          "Fairchild", "FDD6630A").actual_part(
          "Diodes", "DMN10H170SK3-13").actual_part(
          "Diodes", "DMN4026SK3-13").actual_part(
          "Diodes", "DMN10H099SK3-13").actual_part(
          "Taiwan", "TSM090N03CP ROG").actual_part(
          "Fairchild", "FDD8880").actual_part(
          "Infineon", "IRLR2705TRPBF").actual_part(
          "Alpha & Omega", "AOD454A").actual_part(
          "Infineon", "IRFR024NTRPBF").actual_part(
          "Infineon", "IRLR8729TRPBF").actual_part(
          "Infineon", "IRFR024NTRLPBF").actual_part(
          "STM", "STD17NF03LT4")

        # Now extract all of the actual parts:
        # print("-------------------------")
        actual_parts = self.actual_parts
        # vendor_parts = self.vendor_parts
        for project_part in self.project_parts.values():
            # print("project_part: {0}".
            #  format(project_part.name))
            if isinstance(project_part, ChoicePart):
                choice_part = project_part
                for actual_part in choice_part.actual_parts:
                    actual_part_key = actual_part.key
                    if actual_part_key in actual_parts:
                        print("'{0}' is a duplicate".format(actual_part_key))
                    else:
                        actual_parts[actual_part_key] = actual_part
                        # print("Insert ActualPart '{0} {1}'".format(
                        # actual_part.manufacturer_name,
                        # actual_part.manufacturer_part_name))

                # print("project_part=", project_part)
                # assert False, "Deal with Fractional and Alias parts"
                pass
        # print("-------------------------")

        # Now we kludge in vendor part pricing:

        # Connectors:
        # self.vendor_part("Phoenix Contact", "1935161",
        #  "Digi-Key", "277-1667-ND",
        #  ".37/1 .352/10 .3366/50 .3274/100 .306/250 .28152/500 .255/1000")

        # Diodes:
        # self.vendor_part("Fairchild", "S320",
        #  "Digi-Key", "S320FSCT-ND",
        #  ".70/1 .614/10 .5424/25 .4726/100 .4114/250 .3502/500 .2805/1000")
        # self.vendor_part("Diodes Inc", "BAT54-7-F",
        #  "Digi-Key", "BAT54-FDICT-ND",
        #  ".15/1 .142/10 .128/25 .0927/100 .0546/250 .0453/500 .0309/1000")

        # Holes:
        # self.vendor_part("McMaster-Carr", "3MM_Hole",
        #  "MMC", "123", "0./1")

        # Integrated Circuits:
        # self.vendor_part("TI", "SN74LVC1G175DBVR",
        #  "Digi-Key", "296-17617-1-ND",
        #  ".40/1 .315/10 .266/25 .2166/100 .1794/250 .1482/500 .1236/750")
        # self.vendor_part("Fairchild", "MM74HCT08MX",
        #  "Digi-Key", "MM74HCT08MXCT-ND",
        #  ".49/1 .412/10 .3612/25 .309/100 .268/250 .227/500 .175/1000")

        # LED's:
        # self.vendor_part("Cree", "CXA3050-0000-000N0HW440F",
        #  "Digi-Key", "CXA3050-0000-000N0HW440F-ND",
        #  "36./1 34.2/10 33.23/50 30.6/100 27.83/200 26.06/500 24/1000")

        # Resistors:
        # self.vendor_part("Vishay Dale", "CRCW060322K0JNEA",
        #  "Digi-Key", "541-22KGCT-ND",
        #  ".074/10 .04/50 .02295/200 .01566/1000")

    # Database.aliase_part():
    def alias_part(self, name, alias_part_names,
                   kicad_footprint="", feeder_name=None, rotation=None, part_height=None):
        """ *Database*: Create *AliasPart* named *name* and containing
            *alias_names* and stuff it into the *Database* object (i.e. *self*).
            Each item in *alias_part_names* can be either a simple string or a tuple.
            A tuple has the form of (count, "name") and means that we need *count*
            instances of "name*".
        """

        # Verify argument types:
        assert isinstance(name, str)
        assert isinstance(alias_part_names, list)
        assert isinstance(feeder_name, str) or feeder_name is None
        assert isinstance(part_height, float) or part_height is None
        assert isinstance(rotation, float) or rotation is None
        for alias_part_name in alias_part_names:
            assert isinstance(alias_part_name, str) or isinstance(alias_part_name, tuple)

        # Expand any *tuple*'s into a sequnce of the same part name:
        expanded_alias_part_names = []
        for alias_part_name_or_tuple in alias_part_names:
            if isinstance(alias_part_name_or_tuple, str):
                # A standard part name string is just appended to the list:
                alias_part_name = alias_part_name_or_tuple
                expanded_alias_part_names.append(alias_part_name)
            elif isinstance(alias_part_name_or_tuple, tuple):
                # A tuple has the form of (count, "part_name") and append to the list *count* times:
                alias_part_tuple = alias_part_name_or_tuple
                count = alias_part_tuple[0]
                assert isinstance(count, int) and count > 0
                alias_part_name = alias_part_tuple[1]
                for index in range(count):
                    expanded_alias_part_names.append(alias_part_name)
        # if len(expanded_alias_part_names) > len(alias_part_names):
        #    print("alias_part_names={0}", alias_part_names)
        #    print("expanded_alias_part_names={0}", expanded_alias_part_names)

        # Lookup each *alias_name* in *expanded_alias_names* and tack it onto *alias_parts*:
        database = self
        project_parts = database.project_parts
        alias_parts = []
        for alias_part_name in expanded_alias_part_names:
            if alias_part_name in project_parts:
                project_part = project_parts[alias_part_name]
                assert isinstance(project_part, ProjectPart)
                alias_parts.append(project_part)
            else:
                print("Part '{0}' not found for for alias '{1}'".
                      format(alias_part_name, name))

        # Create and return the new *alias_part*:
        # assert len(alias_parts) == 1, "alias_parts={0}".format(alias_parts)
        # if isinstance(feeder_name, str):
        #    footprint = database.footprint(feeder_name, rotation)
        alias_part = AliasPart(name,
                               alias_parts, kicad_footprint, feeder_name, part_height)
        return database.insert(alias_part)

    # Database.choice_part():
    def choice_part(self, name, kicad_footprint, location, description,
                    rotation=None, pick_dx=0.0, pick_dy=0.0, feeder_name=None, part_height=None):
        """ *Database*: Add a *ChoicePart* to *self*. """

        # Verify argument types:
        assert isinstance(name, str)
        assert isinstance(kicad_footprint, str)
        assert isinstance(location, str)
        assert isinstance(description, str)
        assert (isinstance(rotation, float) and 0.0 <= rotation <= 360.0) or rotation is None
        assert isinstance(pick_dx, float)
        assert isinstance(pick_dy, float)
        assert isinstance(feeder_name, str) or feeder_name is None
        assert isinstance(part_height, float) or part_height is None

        # Make sure we do not have a duplicate:
        project_parts = self.project_parts
        if name in project_parts:
            print("'{0}' is duplicated".format(name))

        # if kicad_footprint.find(':') < 0:
        #    print("part '{0}' has no associated library in footprint '{1}'".
        #      format(name, kicad_footprint))

        database = self
        # if isinstance(feeder_name, str):
        #    footprint = database.footprint(feeder_name, rotation)
        choice_part = ChoicePart(name, kicad_footprint, location, description,
                                 rotation, pick_dx, pick_dy, feeder_name, part_height)

        return database.insert(choice_part)

    # Database.dump():
    def dump(self, out_stream):
        """ *Database*: Output the *Database* object (i.e. *self*) out to *out_stream*
            in human readable form.
        """

        # Verify argument types:
        assert isinstance(out_stream, io.IOBase)

        vendor_parts_cache = self.vendor_parts_cache
        actual_keys = sorted(vendor_parts_cache.keys())
        for actual_key in actual_keys:
            out_stream.write("{0}:\n".format(actual_key))
            vendor_parts = vendor_parts_cache[actual_key]
            for vendor_part in vendor_parts:
                vendor_part.dump(out_stream, 2)
            out_stream.write("\n")

    # Database.exchange_rate():
    def exchange_rate(self, from_currency, to_currency):
        """ *Database*: Lookup current currency exchange rate:
        """

        # Verify argument types:
        assert isinstance(from_currency, str)
        assert isinstance(to_currency, str)

        converter = currency_converter.CurrencyConverter()
        exchange_rate = converter.convert(1.0, from_currency, to_currency)
        return exchange_rate

    # Database.findchips_scrape():
    def findchips_scrape(self, actual_part):
        """ *Database*: Return a list of *VendorParts* associated with
            *actual_part* scraped from the findchips.com web page.
        """
        # Verify argument types:
        assert isinstance(actual_part, ActualPart)

        # Grab some values from *actual_part*:
        manufacturer_name = actual_part.manufacturer_name
        manufacturer_part_name = actual_part.manufacturer_part_name
        original_manufacturer_part_name = manufacturer_part_name

        # Trace every time we send a message to findchips:
        print("Find '{0}:{1}'".
              format(manufacturer_name, manufacturer_part_name))

        # Set to *trace* to *True* to enable tracing:
        trace = False

        # Generate *url_part_name* which is a %XX encoded version of
        # *manufactuerer_part_name*:
        ok = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" + "0123456789" + "-.:;" + \
             "abcdefghijklmnopqrstuvwxyz"
        url_part_name = ""
        for character in manufacturer_part_name:
            if ok.find(character) >= 0:
                # Let this *character* through unchanged:
                url_part_name += character
            else:
                # Convert *character* to %XX:
                url_part_name += format("%{0:02x}".format(ord(character)))

        # Grab a page of information about *part_name* using *findchips_url*:
        findchips_url = "http://www.findchips.com/search/" + url_part_name
        if trace:
            print("findchips_url='{0}'".format(findchips_url))
        findchips_response = requests.get(findchips_url)
        findchips_text = findchips_response.text.encode("ascii", "ignore")

        # Parse the *findchips_text* into *find_chips_tree*:
        findchips_tree = BeautifulSoup(findchips_text, "html.parser")

        # if trace:
        #    print(findchips_tree.prettify())

        # We use regular expressions to strip out unnecessary characters
        # in numbrers:
        digits_only_re = re.compile("\\D")

        # Result is returned in *vendor_parts*:
        vendor_parts = []

        # Currently, there is a <div class="distributor_results"> tag for
        # each distributor:
        for distributor_tree in findchips_tree.find_all("div", class_="distributor-results"):
            # if trace:
            #        print("**************************************************")
            #        print(distributor_tree.prettify())

            # The vendor name is burried in:
            #   <h3 class="distributor-title"><a ...>vendor name</a></h3>:
            vendor_name = None
            for h3_tree in distributor_tree.find_all(
              "h3", class_="distributor-title"):
                # print("&&&&&&&&&&&&&&&&&&&&&&&")
                # print(h3_tree.prettify())
                for a_tree in h3_tree.find_all("a"):
                    vendor_name = a_tree.get_text()

            # If we can not extact a valid *vendor_name* there is no
            # point in continuing to work on this *distributor_tree*:
            if vendor_name is None:
                continue

            # This code is in the *VendorPart* initialize now:
            # Strip some boring stuff off the end of *vendor_name*:
            # vendor_name = text_filter(vendor_name, str.isprintable)
            # if vendor_name.endswith("Authorized Distributor"):
            #    # Remove "Authorized Distributor" from end
            #    # of *vendor_name*:
            #    if vendor_name.endswith("Authorized Distributor"):
            #        vendor_name = vendor_name[:-22].strip(" ")
            #    if vendor_name.endswith("Member"):
            #        # Remove "Member" from end of *vendor_name*:
            #        vendor_name = vendor_name[:-6].strip(" ")
            #    if vendor_name.endswith("ECIA (NEDA)"):
            #        # Remove "ECIA (NEDA)" from end of *vendor_name*:
            #        vendor_name = vendor_name[:-11].strip(" ")

            # Extract *currency* from *distributor_tree*:
            currency = "USD"
            try:
                currency = distributor_tree["data-currencycode"]
            except ValueError:
                pass

            # All of the remaining information is found in <table>...</table>:
            for table_tree in distributor_tree.find_all("table"):
                # print(table_tree.prettify())

                # There two rows per table.  The first row has the headings
                # and the second row has the data.  The one with the data
                # has a class of "row" -- <row clase="row"...> ... </row>:
                for row_tree in table_tree.find_all("tr", class_="row"):
                    if trace:
                        print("==============================================")
                        # print(row_tree.prettify())

                    # Now we grab the *vendor_part_name*.  Some vendors
                    # (like Arrow) use the *manufacturer_part_name* as their
                    # *vendor_part_name*.  The data is in:
                    #     <span class="additional-value"> ... </span>:
                    vendor_part_name = manufacturer_part_name
                    for span1_tree in row_tree.find_all(
                      "span", class_="td-desc-distributor"):
                        # print(span1_tree.prettify())
                        for span2_tree in span1_tree.find_all(
                          "span", class_="additional-value"):
                            # Found it; grab it, encode it, and strip it:
                            vendor_part_name = span2_tree.get_text()

                    # The *stock* count is found as:
                    #    <td class="td-stock">stock</td>
                    stock = 0
                    stock_tree = row_tree.find("td", class_="td-stock")
                    if stock_tree is not None:
                        # Strip out commas, space, etc.:
                        stock_text = \
                          digits_only_re.sub("", stock_tree.get_text())
                        # Some sites do not report stock, and leave them
                        # empty.  We just leave *stock* as zero in this case:
                        if len(stock_text) != 0:
                            stock = min(int(stock_text), 1000000)

                    # The *manufacturer_name* is found as:
                    #    <td class="td-mfg"><span>manufacturer_name</span></td>
                    manufacturer_name = ""
                    for mfg_name_tree in row_tree.find_all(
                      "td", class_="td-mfg"):
                        for span_tree in mfg_name_tree.find_all("span"):
                            # Found it; grab it, encode it, and strip it:
                            manufacturer_name = span_tree.get_text()

                    # The *manufacturer_part_name* is found as:
                    #    <td class="td_part"><a ...>mfg_part_name</a></td>
                    manufacturer_part_name = ""
                    for mfg_part_tree in row_tree.find_all(
                      "td", class_="td-part"):
                        for a_tree in mfg_part_tree.find_all("a"):
                            # Found it; grab it, encode it, and strip it:
                            manufacturer_part_name = a_tree.get_text()

                    # The price breaks are encoded in a <ul> tree as follows:
                    #    <td class="td_price">
                    #       <ul>
                    #          <li>
                    #            <span class="label">quantity</span>
                    #            <span class="value">price</span>
                    #          </li>
                    #          ...
                    #       </ul>
                    #    </td>
                    price_breaks = []
                    price_list_tree = row_tree.find("td", class_="td-price")
                    if price_list_tree is not None:
                        for li_tree in price_list_tree.find_all("li"):
                            quantity_tree = li_tree.find("span", class_="label")
                            price_tree = li_tree.find("span", class_="value")
                            if quantity_tree is not None and price_tree is not None:
                                # We extract *quantity*:
                                quantity_text = digits_only_re.sub("", quantity_tree.get_text())
                                quantity = 1
                                if quantity_text != "":
                                    quantity = int(quantity_text)

                                # Extract *price* using only digits and '.':
                                price_text = ""
                                for character in price_tree.get_text():
                                    if character.isdigit() or character == ".":
                                        price_text += character
                                price = float(price_text)

                                # This needs to be looked up:
                                exchange_rate = 1.0
                                if currency == "USD":
                                    exchange_rate = 1.0
                                elif currency == "EUR":
                                    exchange_rate = \
                                      self.euro_to_dollar_exchange_rate
                                elif currency == "GBP":
                                    exchange_rate = \
                                      self.pound_to_dollar_exchange_rate
                                # else:
                                #    assert False, \
                                #      "Unrecognized currency '{0}'". \
                                #      format(currency)

                                # Sometimes we get a bogus price of 0.0 and
                                # we just need to ignore the whole record:
                                if price > 0.0:
                                    price_break = PriceBreak(
                                      quantity, price * exchange_rate)
                                    price_breaks.append(price_break)

                    # Now if we have an exact match on the *manufacturer_name*
                    # we can construct the *vendor_part* and append it to
                    # *vendor_parts*:
                    if original_manufacturer_part_name == manufacturer_part_name:
                        now = time.time()
                        vendor_part = VendorPart(actual_part, vendor_name, vendor_part_name,
                                                 stock, price_breaks, now)
                        vendor_parts.append(vendor_part)

                        # Print stuff out if *trace* in enabled:
                        if trace:
                            # Print everything out:
                            print("vendor_name='{0}'".format(vendor_name))
                            print("vendor_part_name='{0}'".
                                  format(vendor_part_name))
                            print("manufacturer_part_name='{0}'".
                                  format(manufacturer_part_name))
                            print("manufacturer_name='{0}'".
                                  format(manufacturer_name))
                            print("stock={0}".format(stock))
                            price_breaks.sort()
                            for price_break in price_breaks:
                                print("{0}: {1:.6f} ({2})".
                                      format(price_break.quantity, price_break.price, currency))

        # For debugging, let the user now that we are looking for a
        # part and not finding it at all:
        if len(vendor_parts) == 0:
            print("**********Find '{0}:{1}': {2} matches".format(
                  actual_part.manufacturer_name,
                  actual_part.manufacturer_part_name, len(vendor_parts)))

        return vendor_parts

    # Database.footprint():
    def footprint(self, feeder_name, rotation):
        """ *Database*: Return a *Footprint* object that matches *name*:

        The arguments are:
        * *feeder_name*: The feeder name to use for `.pos` file.
        * *rotation*: The rotation to apply to the KiCAD footprint to match the feeder
          tape orientation.
        """

        # Verify argument types:
        assert isinstance(feeder_name, str)
        assert ';' not in feeder_name
        assert (isinstance(rotation, float) and 0.0 <= rotation <= 360.0) or rotation is None

        database = self
        footprints = database.footprints
        if feeder_name in footprints:
            footprint = footprints[feeder_name]
            footprint_rotation = footprint.rotation
            if isinstance(rotation, float):
                if isinstance(footprint_rotation, float):
                    if rotation != footprint_rotation:
                        print("Footprint '{0}' mismatched rotations {1} != {2}".format(
                              feeder_name, rotation, footprint_rotation))
                else:
                    print("Not all footprints '{0}' have a feeder rotation of {1}".
                          format(feeder_name, rotation))
            else:
                if isinstance(footprint_rotation, float):
                    print("Not all footprints '{0}' have a feeder rotation of {1}".
                          format(feeder_name, footprint_rotation))
        else:
            footprint = Footprint(feeder_name, rotation)
            footprints[feeder_name] = footprint
            assert feeder_name in footprints
            # print("footprints['{0}'].rotation={1}".format(feeder_name, rotation))
        return footprint

    # Database.fractional_part():
    def fractional_part(self, name, kicad_footprint,
                        whole_part_name, numerator, denominator, description):
        """ *Database*: Insert a new *FractionalPart* named
            *name* and containing *whole_part_name*,
            *numerator*, *denominator*, and *description* in to the
            *Database* object (i.e. *self*.) """

        # Verify argument types:
        assert isinstance(name, str)
        assert isinstance(kicad_footprint, str)
        assert isinstance(whole_part_name, str)
        assert isinstance(numerator, int)
        assert isinstance(denominator, int)
        assert isinstance(description, str)

        project_parts = self.project_parts
        if whole_part_name in project_parts:
            whole_part = project_parts[whole_part_name]

            # Verify argument types:
            fractional_part = FractionalPart(name, kicad_footprint,
                                             whole_part, numerator, denominator, description)
            self.insert(fractional_part)
        else:
            print("Whole part '{0}' not found for fractional part '{1}'!".
                  format(whole_part_name, name))

    # Database.lookup():
    def lookup(self, name):
        """ *Database*: Return the *ProjectPart* associated with
            *name*. """

        assert isinstance(name, str)

        project_part = None
        project_parts = self.project_parts
        if name in project_parts:
            project_part = project_parts[name]
        return project_part

    # Database.insert():
    def insert(self, project_part):
        """ *Database*: Add a *ProjectPart* to *self*. """

        # Verify argument_types:
        assert isinstance(project_part, ProjectPart)

        name = project_part.name
        project_parts = self.project_parts
        if name in project_parts:
            print("{0} is being inserted into database more than once".format(name))
        else:
            project_parts[name] = project_part
        return project_part

    # Database.save():
    def save(self):
        """ *Database*: Save the *vendor_parts* portion of the *Database*
            object (i.e. *self*).
        """

        # print("=>Database.save")

        vendor_parts_cache = self.vendor_parts_cache
        for vendor_parts in vendor_parts_cache.values():
            assert isinstance(vendor_parts, list)
            for vendor_part in vendor_parts:
                assert isinstance(vendor_part, VendorPart)

        bom_pickle_file = open(self.bom_parts_file_name, "wb")
        pickle.dump(self.vendor_parts_cache, bom_pickle_file)
        bom_pickle_file.close()

        # print("<=Database.save")

    # Database.vendor_part():
    def vendor_part(self, manufacturer_name, manufacturer_part_name,
                    vendor_name, vendor_part_name, price_break_text):
        """ *Database*: Add a vendor part to the database. """

        # Verify argument types:
        assert isinstance(manufacturer_name, str)
        assert isinstance(manufacturer_part_name, str)
        assert isinstance(vendor_name, str)
        assert isinstance(vendor_part_name, str)
        assert isinstance(price_break_text, str)

        # Parse *price_break_text* int a list of *PriceBreak*'s:
        price_breaks = []
        breaks_text = price_break_text.split()
        for break_text in breaks_text:
            cost_quantity_pair = break_text.split("/")
            price_break = PriceBreak(int(cost_quantity_pair[1]), float(cost_quantity_pair[0]))
            price_breaks.append(price_break)

        actual_part_key = (manufacturer_name, manufacturer_part_name)
        actual_parts = self.actual_parts
        if actual_part_key in actual_parts:
            actual_part = actual_parts[actual_part_key]
            vendor_part_key = (vendor_name, vendor_part_name)
            vendor_parts = self.vendor_parts
            if vendor_part_key in vendor_parts:
                print("Vendor Part: '{0} {1}' is duplicated in database".
                      format(vendor_name, vendor_part_name))
            else:
                vendor_part = VendorPart(actual_part,
                                         vendor_name, vendor_part_name, 10000, price_breaks)
                vendor_parts[vendor_part_key] = vendor_part
        else:
            print("Actual Part: '{0} {1}' is not in database".format(
                  manufacturer_name, manufacturer_part_name))


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
    def xml_lines_append(self, xml_lines, indent, tracing=None):
        # Verify argument types:
        assert isinstance(xml_lines, list)
        assert isinstance(indent, str)
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        # next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{0}=>Filter.xml_lines_append()".format(tracing))

        # Start appending the `<Filter...>` element to *xml_lines*:
        filter = self
        parameter = filter.parameter
        use = filter.use
        select = filter.select
        parameter_name = parameter.name
        xml_lines.append(f'{indent}<Filter name="{parameter_name}" use="{use}" select="{select}">')
        if tracing is not None:
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

        # Wrap up any requested *Tracing*:
        if tracing is not None:
            print(f"{tracing}<=Filter.xml_lines_append()")


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
    def __init__(self, name, parent, tracing=None):
        # Verify argument types:
        assert isinstance(name, str)
        assert isinstance(parent, Node) or parent is None
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        parent_name = 'None' if parent is None else f"'{parent.name}'"
        if tracing is not None:
            print(f"{tracing}=>Node.__init__('{name}', {parent_name})")

        # Do some additional checking for *node* (i.e. *self*):
        node = self
        is_collection = isinstance(node, Collection)
        is_collections = isinstance(node, Collections)
        is_either = is_collections or is_collection
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

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=Node.__init__('{name}', {parent_name})")

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
    def child_remove(self, child, tracing=None):
        # Verify argument types:
        assert isinstance(child, Node)
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing* for *Node* (i.e. *self*):
        node = self
        if tracing is not None:
            print(f"{tracing}=>Node.child_remove('{node.name}', '{child.name}')")

        children = node._children
        assert child in children
        index = children.index(child)
        assert index >= 0
        node.child_delete(index)

        # Wrap up an requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=Node.child_remove('{node.name}', '{child.name}')")

    # Node.children_get():
    def children_get(self):
        # Return the children of *node* (i.e. *self*):
        node = self
        return node._children

    # Node.clicked():
    def clicked(self, tables_editor, model_index, tracing=None):
        # Verify argument types:
        assert isinstance(tables_editor, TablesEditor)
        assert isinstance(model_index, QModelIndex)
        assert isinstance(tracing, str) or tracing is None

        # Fail with a more useful error message than "no such method":
        node = self
        assert False, "Node.clicked() needs to be overridden for type ('{0}')".format(type(node))

    # Node.csv_read_and_process():
    def csv_read_and_process(self, csv_directory, bind=False, tracing=None):
        # Verify argument types:
        assert isinstance(csv_directory, str)
        assert False, ("Node sub-class '{0}' does not implement csv_read_and_process".
                       format(type(self)))

    # Node.directory_create():
    def directory_create(self, root_path, tracing=None):
        # Verify argument types:
        assert isinstance(root_path, str)
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}=>Node.directory_create('node.name', '{root_path}')")

        node = self
        parent = node.parent
        assert parent is not None
        parent_relative_path = parent.relative_path
        directory_path = os.path.join(root_path, parent_relative_path)
        if not os.path.isdir(directory_path):
            os.makedirs(directory_path)
            if tracing is not None:
                print(f"{tracing}Created directory '{directory_path}'")

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}=>Node.directory_create('node.name', '{root_path}')")

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
    def name_get(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform an requested *tracing*:
        # next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>Node.name_get()")

        # Grab *title* from *node* (i.e. *self*):
        node = self
        name = node.name

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}=>Node.name_get()=>{name}")
        return name

    # Node.remove():
    def remove(self, remove_node, tracing=None):
        # Verify argument types:
        assert isinstance(remove_node, Node)
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing* for *node* (i.e. *self*):
        node = self
        name = node.name
        if tracing is not None:
            print(f"{tracing}=>Node.remove('{name}', '{remove_node.name}')")

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

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=Node.remove('{name}', '{remove_node.name}')")

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
        children = nede._children
        children.sort(key=keyfunction)

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
    def __init__(self, name, parent, tracing=None):
        # Verify argument types:
        assert isinstance(name, str)
        assert isinstance(parent, Node)

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>Directory.__init__('{name}', '{parent.name}')")

        # Perform some additional checking on *parent*:
        assert isinstance(parent, Directory) or isinstance(parent, Collection)

        # Initlialize the *Node* super class for directory (i.e. *self*):
        super().__init__(name, parent, tracing=next_tracing)

        directory = self
        relative_path = directory.relative_path
        if tracing is not None:
            print(f"{tracing}relative_path='{relative_path}'")

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=Directory.__init__('{name}', '{parent.name}')")

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
    def clicked(self, tables_editor, model_index, tracing=None):
        # Verify argument types:
        assert isinstance(tables_editor, TablesEditor)
        assert isinstance(tracing, str) or tracing is None
        assert isinstance(model_index, QModelIndex)

        # Preform any requested *tracing*:
        if tracing is not None:
            print("{0}=>Directory.clicked()".format(tracing))

        tables_editor.current_search = None

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print("{0}<=Directory.clicked()".format(tracing))

    # Directory.directories_get():
    def directories_get(self):
        directory = self
        directories = [directory]
        for node in directory.children_get():
            directories.extend(node.directories_get())
        return directories

    # Directory.name_get():
    def name_get(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing* for *directory* (i.e. *self*):
        directory = self
        name = directory.name
        if tracing is not None:
            print(f"{tracing}=>Directory.name_get('{name}')")
            print(f"{tracing}<=Directory.name_get('{name}')=>'{name}'")

        # Return *name*:
        return name

    # Directory.partial_load():
    def partial_load(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        directory = self
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>Directory.partial_load('{directory.name}')")

        # Compute the *full_path* for the *collection* sub-*directory*:
        relative_path = directory.relative_path
        collection = directory.collection
        collection_root = collection.collection_root
        full_path = os.path.join(collection_root, relative_path)
        if tracing is not None:
            print(f"{tracing}collection_root='{collection_root}'")
            print(f"{tracing}relative_path='{relative_path}'")
            print(f"{tracing}full_path='{full_path}'")
        assert os.path.isdir(full_path), f"Directory '{full_path}' does not exist.!"

        # Visit all of the files and directories in *directory_path*:
        for index, file_or_directory_name in enumerate(sorted(list(os.listdir(full_path)))):
            if tracing is not None:
                print(f"{tracing}File_Name[{index}]:'{file_or_directory_name}'")

            # Skip over any files/directories that start with '.':
            if not file_or_directory_name.startswith('.'):
                # Recursively do a partial load for *full_path*:
                sub_relative_path = os.path.join(relative_path, file_or_directory_name)
                sub_full_path = os.path.join(full_path, file_or_directory_name)
                if tracing is not None:
                    print(f"{tracing}sub_relative_path='{sub_relative_path}'")
                    print(f"{tracing}sub_full_path='{sub_full_path}'")
                if os.path.isdir(sub_full_path):
                    # *full_path* is a directory:
                    name = Encode.from_file_name(file_or_directory_name)
                    sub_directory = Directory(name, directory, tracing=next_tracing)
                    assert directory.has_child(sub_directory)
                    sub_directory.partial_load(tracing=next_tracing)
                elif sub_full_path.endswith(".xml"):
                    # Full path is a *Table* `.xml` file:
                    name = Encode.from_file_name(file_or_directory_name[:-4])
                    url = "bogus URL"
                    table = Table(name, directory, url, tracing=next_tracing)
                    assert directory.has_child(table)
                    sub_relative_path = os.path.join(relative_path, name)
                    table.partial_load(tracing=next_tracing)
                else:
                    assert False, f"'{full_path}' is neither an .xml nor a directory"

        # Wrap up any requested *tracing*:
        if tracing is not None:
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
    def __init__(self, name, parent, collection_root, searches_root, url_load, tracing=None):
        # Verify argument types:
        assert isinstance(name, str)
        assert isinstance(parent, Collections)
        assert isinstance(collection_root, str)
        assert isinstance(searches_root, str)
        assert callable(url_load)
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>Collection.__init__('{name}', '{parent.name}', "
                  f"'{collection_root}', '{searches_root}')")

        # Intialize the *Node* super class of *collection* (i.e. *self*).
        collection = self
        super().__init__(name, parent, tracing=next_tracing)
        if tracing is not None:
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
        collection.url_load = url_load

        # Ensure that *type_letter_get()* returns 'C' for Collection:
        assert collection.type_letter_get() == 'C'

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}=>Collection.__init__('{name}', '{parent.name}', "
                  f"'{collection_root}', '{searches_root}')")

    # Collection.actual_parts_lookup():
    def actual_parts_lookup(self, choice_part, tracing=None):
        # Verify argument types:
        assert isinstance(choice_part, ChoicePart)
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        search_name = choice_part.name
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>Collection.actual_parts_lookup(*, '{search_name})")
        
        # Grab some values from *collection* (i.e. *self*):
        collection = self
        searches_table = collection.searches_table
        searches_root = collection.searches_root

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
            search.file_load(tracing=next_tracing)

            # Grab some values from *search*:
            search.name = search.name
            search_url = search.url
            relative_path = search.relative_path

            # Compute the fill path for ...
            full_path = os.path.join(searches_root, relative_path)


            # Compute the *csv_full_full_file*  and *html_full_file* where search results
            # are stored:
            csv_full_file = os.path.join(searches_root, relative_path + ".csv")
            html_full_file = os.path.join(searches_root, relative_path + ".html")
            if tracing is not None:
                print(f"{tracing}csv_full_file='{csv_full_file}'")
                print(f"{tracing}html_full_file='{html_full_file}'")
                print(f"{tracing}search_url='{search_url}'")

            if not os.path.isfile(html_full_file):
                # Construct the header values that need to be sent with the *url*:
                authority_text = "www.digikey.com"
                accept_text = (
                    "text/html,application/xhtml+xml,application/xml;"
                    "q=0.9,image/webp,image/apng,*/*;"
                    "q=0.8,application/signed-exchange;"
                    "v=b3"
                )
                accept_encoding_text = "gzip, deflate, br"
                cookie_text = (
                    "i10c.bdddb=c2-f0103ZLNqAeI3BH6yYOfG7TZlRtCrMwzKDQfPMtvESnCuVjBtyWjJ1l"
                    "kqXtKsvswxDrjRHdkESNCtx04RiOfGqfIlRUHqt1qPnlkPolfJSiIRsomx0RhMqeKlRtT3"
                    "jxvKEOjKMDfJSvUoxo6uXWaGVZkqoAhloxqQlofPwYkJcS6fhQ6tzOgotZkQMtHDyjnA4lk"
                    "PHeIKNnroxoY8XJKBvefrzwFru4qPnlkPglfJSiIRvjBTuTfbEZkqMupstsvz8qkl7wWr3i"
                    "HtspjsuTFBve9SHoHqjyTKIPfPM3uiiAioxo6uXOfGvdfq4tFloxqPnlkPcxyESnCuVjBt1"
                    "VmBvHmsYoHqjxVKDq3fhvfJSiIRsoBsxOftucfqRoMRjxVKDq3BuEMuNnHoyM9oz3aGv4ul"
                    "RtCrMsvP8tJOPeoESNGw2q6tZSiN2ZkQQxHxjxVOHukKMDjOQlCtXnGt4OfqujoqMtrpt3y"
                    "KDQjVMffM3iHtsolozT7WqeklSRGloXqPDHZHCUfJSiIRvjBTuTfQeKKYMtHlpVtKDQfPM2"
                    "uESnCuVm6tZOfGK1fqRoIOjxvKDrfQvYkvNnuJsojozTaLW"
                )

                # Construct *headers* 
                headers = {
                    "authority": authority_text,
                    "accept": accept_text,
                    "accept-encoding": accept_encoding_text,
                    "cookie": cookie_text
                }

                # Attempt the fetch the contents of *search_url* using *headers*:
                try:
                    response = requests.get(search_url, headers=headers)
                    response.raise_for_status()
                except HTTPError as http_error:
                    assert False, f"HTTP error occurred '{http_error}'"
                except Exception as error:
                    assert False, f"Other exception occurred: '{error}'"
                    
                # Now write *content* out to *html_full_file* so that it is cached:
                content = response.content
                with open(html_full_file, "wb") as html_file:
                    html_file.write(content)
                    if tracing is not None:
                        print(f"{tracing}Wrote out '{html_full_file}'")

            # Now procecess *html_full_file*:
            pairs_text = None
            assert os.path.isfile(html_full_file)
            print(f"html_full_file='{html_full_file}")
            with open(html_full_file) as html_file:
                html_text = html_file.read()
                soup = bs4.BeautifulSoup(html_text, features="lxml")
                assert soup is not None
                #print("type(soup)=", type(soup))
                pairs = []
                pairs_text = None
                print("here 2b")
                for form_tag in soup.find_all("form"):
                    assert isinstance(form_tag, bs4.element.Tag)
                    name = form_tag.get("name")
                    if name == "downloadform":
                        # We found it:
                        print(f"form_tag={form_tag}")
                        for index, input_tag in enumerate(form_tag.children):
                            if isinstance(input_tag, bs4.element.Tag):
                                print(input_tag)
                                assert input_tag.name.lower() == "input"
                                input_name = input_tag.get("name")
                                print(f"input_name='{input_name}'")
                                input_value = input_tag.get("value")
                                print(f"input_value='{input_value}'")
                                input_value = input_value.replace(",", "%2C")
                                input_value = input_value.replace('|', "%7C")
                                input_value = input_value.replace(' ', "+")
                                pair = f"{input_name}={input_value}"
                                print(f"pair='{pair}'")
                                pairs.append(pair)
                        pairs_text = '&'.join(pairs)
                        print(f"pairs_text='{pairs_text}'")
            assert isinstance(pairs_text, str)

            # Construct the *csv_fetch_url*:
            csv_fetch_url = "https://www.digikey.com/product-search/download.csv?" + pairs_text
            if tracing is not None:
                print(f"{tracing}csv_fetch_url='{csv_fetch_url}'")

            # Fetch `.csv` file if it does not exist or it is stale:
            modification_time = (os.path.getmtime(csv_full_file) if os.path.isfile(csv_full_file)
                                 else 0)
            if modification_time + stale_time < now:
                # Construct the text strings fort the *headers*:
                authority_text = "www.digikey.com"
                accept_text = (
                    "text/html,application/xhtml+xml,application/xml;"
                    "q=0.9,image/webp,image/apng,*/*;"
                    "q=0.8,application/signed-exchange;"
                    "v=b3"
                )
                accept_encoding_text = "gzip, deflate, br"
                cookie_text = (
                    "i10c.bdddb="
                    "c2-94990ugmJW7kVZcVNxn4faE4FqDhn8MKnfIFvs7GjpBeKHE8KVv5aK34FQDgF"
                    "PFsXXF9jma8opCeDMnVIOKCaK34GOHjEJSFoCA9oxF4ir7hqL8asJs4nXy9FlJEI"
                    "8MujcFW5Bx9imDEGHDADOsEK9ptrlIgAEuIjcp4olPJUjxXDMDVJwtzfuy9FDXE5"
                    "sHKoXGhrj3FpmCGDMDuQJs4aLb7AqsbFDhdjcF4pJ4EdrmbIMZLbAQfaK34GOHbF"
                    "nHKo1rzjl24jP7lrHDaiYHK2ly9FlJEADMKpXFmomx9imCGDMDqccn4fF4hAqIgF"
                    "JHKRcFFjl24iR7gIfTvaJs4aLb4FqHfADzJnXF9jqd4iR7gIfz8t0TzfKyAnpDgp"
                    "8MKEmA9og3hdrCbLvCdJSn4FJ6EFlIGEHKOjcp8sm14iRBkMT8asNwBmF3jEvJfA"
                    "DwJtgD4oL1Eps7gsLJaKJvfaK34FQDgFfcFocAAMr27pmCGDMD17GivaK34GOGbF"
                    "nHKomypOTx9imDEGHDADOsTpF39ArqeADwFoceWjl24jP7gIHDbDPRzfwy9JlIlA"
                    "DTFocAEP"
                )

                # Construct *headers*:
                headers = {
                    "authority": authority_text,
                    "accept": accept_text,
                    "accept-encoding": accept_encoding_text,
                    "cookie": cookie_text
                }

                # Attempt the fetch the contents of *csv_fetch_url* using *headers*:
                if tracing is not None:
                    print(f"{tracing}A:Fetching '{csv_fetch_url}' for '{search_name}'")
                try:
                    response = requests.get(csv_fetch_url, headers=headers)
                    response.raise_for_status()
                except HTTPError as http_error:
                    assert False, f"HTTP error occurred '{http_error}'"
                except Exception as error:
                    assert False, f"Other exception occurred: '{error}'"
                    
                collection = search.collection
                assert isinstance(collection, Collection)
                collection.url_load(search_url, html_full_file, tracing=next_tracing)

                # Now write *content* out to *html_full_file* so that it is cached:
                content = response.content
                with open(csv_full_file, "wb") as csv_file:
                    csv_file.write(content)
                    if tracing is not None:
                        print(f"{tracing}Wrote out '{csv_full_file}'")

            # Read in the *csv_file_file*:
            assert os.path.isfile(csv_full_file)
            data_rows = []
            column_names = None
            with open(csv_full_file) as csv_file:
                csv_reader = csv.reader(csv_file, delimiter=',', quotechar='"')
                for row_index, row in enumerate(csv_reader):
                    #print(f"[{index}]: {row}")
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
                #print(f"Row[{index}]: '{manufacturer} : '{manufacturer_part_number}'")
            pairs = list(duplicate_removal_table.keys())

            for index, pair in enumerate(pairs):
                manufacturer, part_number = pair
                if tracing is not None:
                    print(f"{tracing}Actual_Part[{index}]: '{manufacturer}' : '{part_number}'")
                actual_part = ActualPart(manufacturer, part_number)
                actual_parts.append(actual_part)

        # Wrap up any requested *tracing* and return *actual_parts*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}<=Collection.actual_parts_lookup(*, '{search_name})"
                  f" => len([...])={len(actual_parts)}")
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
    def partial_load(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform an requested *tracing* for *collection* (i.e. *self*):
        collection = self
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>Collection.partial_load('{collection.name}')")

        # Visit all of the directories and files in *collection_root*:
        collection_root = collection.collection_root
        relative_path = collection.relative_path
        directory_path = os.path.join(collection_root, relative_path)
        if tracing is not None:
            print(f"{tracing}collection_root='{collection_root}'")
            print(f"{tracing}relative_path='{relative_path}'")
            print(f"{tracing}directory_path='{directory_path}'")
        assert os.path.isdir(directory_path)

        for index, base_name in enumerate(list(sorted(os.listdir(directory_path)))):
            if tracing is not None:
                print(f"{tracing}File_Name[{index}]:'{base_name}'")

            # Compute a *full_path* from *collection_root* and *base_name*:
            full_path = os.path.join(directory_path, base_name) 
            if tracing is not None:
                print(f"{tracing}full_path='{full_path}'")
            if not base_name.startswith('.'):
                if base_name.endswith(".xml"):
                    assert False, "Top level tables not implemented yet"
                elif os.path.isdir(full_path):
                    name = Encode.from_file_name(base_name)
                    directory = Directory(name, collection, tracing=next_tracing)
                    assert collection.has_child(directory)
                    directory.partial_load(tracing=next_tracing)
                else:
                    assert False, f"'{base_name}' is neither an .xml file nor a directory"

        # Wrap-up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=Collection.partial_load('{collection.name}')")

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
    def url_load(self, url, output_file_name, tracing=None):
        # Verify argument types:
        assert isinstance(url, str)
        assert isinstance(output_file_name, str)

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>Collection.url_load('{url}', '{output_file_name}')")

        collection = self
        plugin = collection.plugin
        if plugin is None:
            collection_root = collection.collection_root
            if tracing is not None:
                print(f"{tracing}collection_root='{collection_root}'")
            assert collection_root.endswith("ROOT")
            package_directory = os.path.split(collection_root)[0]
            if tracing is not None:
                print(f"{tracing}package_directory='{package_directory}'")
            package_name = os.path.split(package_directory)[1]
            if tracing is not None:
                print(f"{tracing}package_name='{package_name}'")
            plugin_name = f"{package_name}.plugin"
            if tracing is not None:
                print(f"{tracing}plug_name='{plugin_name}'")
            plugin_module = importlib.import_module(plugin_name)
            url_load = getattr(plugin_module, "url_load")
            assert callable(url_load)
            url_load(url, output_file_name, tracing=next_tracing)
            #assert False

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=Collection.url_load('{url}', '{output_file_name}')")

# Collections:
class Collections(Node):

    # Collections.__init__():
    def __init__(self, name, collection_directories, searches_root, tree_model, tracing=None):
        # Verify argument types:
        assert isinstance(name, str)
        assert isinstance(collection_directories, list)
        assert isinstance(searches_root, str)
        assert isinstance(tree_model, TreeModel) or tree_model is None
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>Collections.__init__('{name}', {collection_directories}, "
                  f"'{searches_root}', *)")

        # Intialize the *Node* super class of *collections* (i.e. *self*):
        collections = self
        super().__init__(name, None, tracing=next_tracing)

        # Fill in the *pandas* list with *Panda* objects for doing pricing and availabity checking:
        pandas = list()
        entry_point_key = "bom_manager_panda_get"
        for index, entry_point in enumerate(pkg_resources.iter_entry_points(entry_point_key)):
            entry_point_name = entry_point.name
            if tracing is not None:
                print(f"Entry_Point[{index}]: '{entry_point_name}'")
            assert entry_point_name == "panda_get"
            panda_get = entry_point.load()
            assert callable(panda_get)
            panda = panda_get(tracing=next_tracing)
            assert isinstance(panda, Panda)
            pandas.append(panda)
            #panda.lookup("xxx", tracing=next_tracing)

        # Fill in the *cads* list with *CAD* objects for reading in :
        cads = list()
        entry_point_key = "bom_manager_cad_get"
        for index, entry_point in enumerate(pkg_resources.iter_entry_points(entry_point_key)):
            entry_point_name = entry_point.name
            if tracing is not None:
                print(f"Entry_Point[{index}]: '{entry_point_name}'")
            assert entry_point_name == "cad_get"
            cad_get = entry_point.load()
            assert callable(cad_get)
            cad = cad_get(tracing=next_tracing)
            assert isinstance(cad, Cad)
            cads.append(cad)
            cad.load("xxx", tracing=next_tracing)

        # Stuff some values into *collections*:
        collections.cads = cads
        collections.collection_directories = collection_directories
        collections.pandas = pandas
        collections.searches_root = searches_root
        collections.tree_model = tree_model

        # Do some *tracing*:
        if tracing is not None:
            relative_path = collections.relative_path
            print(f"{tracing}collection_directories={collection_directories}")
            print(f"{tracing}searchs_root='{searches_root}'")
            print(f"{tracing}relative_path='{relative_path}'")

        # Ensure that *type_letter_get()* returns 'R' is for collections Root:
        assert collections.type_letter_get() == 'R'

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=Collections.__init__('{name}', {collection_directories}, "
                  f"'searches_root', *)")

    # Collections.actual_parts_lookup():
    def actual_parts_lookup(self, choice_part, tracing=None):
        # Verify argument types:
        assert isinstance(choice_part, ChoicePart)
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>Collections.actual_parts_lookup('{choice_part.name}')")

        # Visit each *collection* in *collections* (i.e. *self*) and find any
        # *ActualPart*'s that match *search_name*:
        collections = self
        actual_parts = []
        for index, collection in enumerate(collections.children_get()):
            if tracing is not None:
                print(f"{tracing}Collection[{index}]:{collection.name}")
            actual_parts += collection.actual_parts_lookup(choice_part, tracing=next_tracing)

        #FIXME: Cull out duplicate acutal parts (i.e. for the same manufacturer.):
        pass

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=Collections.actual_parts_lookup('{choice_part.name}') => [...]")
        return actual_parts

    # Collections.can_fetch_more():
    def can_fetch_more(self):
        # The children of *collections* (i.e. self*) have already be preloade by
        # *Collections.partial_load*().  There is nothing more to fetch:
        return False

    # Collections.check():
    def check(self, search_name, project_name, reference, tracing=None):
        # Verify argument types:
        assert isinstance(search_name, str)
        assert isinstance(project_name, str)
        assert isinstance(reference, str)
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}=>Collections.check('{search_name}', '{project_name}', '{reference}')")

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
            print(f"{project_name}: {reference} {search_name} not found")

        # Wrap up any reqested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=Collections.check('{search_name}', '{project_name}', '{reference}')")
        
    # Collections.partial_load():
    def partial_load(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing* for *collections* (i.e. *self*):
        collections = self
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>Collections.partial_load('{collections.name})")

        # Extract some values from *collections*:
        collections = self
        collection_directories = collections.collection_directories
        searches_root = collections.searches_root
        tree_model = collections.tree_model
        if tracing is not None:
            print(f"{tracing}collection_directories='{collection_directories}'")
            print(f"{tracing}searches_root='{searches_root}'")

        # Find all of the the *collections*:
        entry_point_key = "bom_manager_collection_url_load"
        for index, entry_point in enumerate(pkg_resources.iter_entry_points(entry_point_key)):
            entry_point_name = entry_point.name
            if tracing is not None:
                print(f"{tracing}Entry_Point[{index}]:'{entry_point_name}'")
            assert entry_point_name == "url_load", f"'{entry_point_name}' is not 'url_load''"
            url_load = entry_point.load()
            url_load_module_name = url_load.__module__
            if tracing is not None:
                print(f"url_load_module_name='{url_load_module_name}'")
            url_load_module = sys.modules[url_load_module_name]
            if tracing is not None:
                print(f"url_load_module={url_load_module}")
            url_load_module_file_name = url_load_module.__file__
            if tracing is not None:
                print(f"url_load_module_file_name='{url_load_module_file_name}'")
            collection_directory, base_name = os.path.split(url_load_module_file_name)
            if tracing is not None:
                print(f"collection_directory='{collection_directory}'")
            assert os.path.isdir(collection_directory)
            collection_root = os.path.join(collection_directory, "ROOT")
            if tracing is not None:
                print(f"collection_root='{collection_root}'")
            assert os.path.isdir(collection_root)

            # Create *collection*:
            name = "Digi-Key"
            collection = Collection(name, collections, collection_root, searches_root, url_load,
                                    tracing=next_tracing)
            assert collections.has_child(collection)

            # Recursively perfrom *partial_load*'s down from *collection*:
            collection.partial_load(tracing=next_tracing)

        # Sweep through *path* finding directories (technically symbolic links):
        for index, collection_directory in enumerate(sorted(collection_directories)):
            # Perform requested *tracing*:
            if tracing is not None:
                print(f"{tracing}Collection[{index}]:'{collection_directory}'")

            # Skip over Unix/Linux *collection_directory*'s that start with a '.':
            if not collection_directory.startswith('.'):
                # Create *collection_root_path* and *searches_root*:
                collection_directory_root = os.path.join(collection_directory, "ROOT")
                collection_directory_root = os.path.abspath(collection_directory_root)
                if tracing is not None:
                    print(f"{tracing}collection_directory_root='{collection_directory_root}'")

                # Now find the directory under `ROOT`:
                sub_directories = list(glob.glob(os.path.join(collection_directory_root, "*")))
                assert len(sub_directories) == 1, f"sub_directories={sub_directories}"
                base_name = os.path.basename(sub_directories[0])
                name = Encode.from_file_name(base_name)
                # collection_root = os.path.join(collection_directory_root, base_name)
                if tracing is not None:
                    print(f"{tracing}base_name='{base_name}'")
                    print(f"{tracing}name='{name}'")
                    # print(f"{tracing}collection_root='{collection_root}'")
                    print(f"{tracing}searches_root='{searches_root}'")

                # Create *collection*:
                #collection = Collection(name, collections, collection_directory_root,
                #                        searches_root, url_load, tracing=next_tracing)
                #assert collections.has_child(collection)

                # Recursively perfrom *partial_load*'s down from *collection*:
                collection.partial_load(tracing=next_tracing)

        # Wrap any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=Collections.partial_load('{collections.name})")

    # Collections.searches_root_get():
    def searches_root_get(self):
        collections = self
        searches_root = collections.searches_root
        return searches_root

    # Collections.searches_find():
    def searches_find(self, search_name, tracing=None):
        # Verify argument types:
        assert isinstance(search_name, str)

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>Collections.searches_find(*, '{search_name}')")

        # Visit each *collection in *collections* (i.e. *self*) to see if it has *search_name*:
        collections = self
        searches = []
        for collection in collections.children_get():
            search = collection.search_find(search_name)
            if search is not None:
                # We have a matching *search*:
                assert search_name == search.name, f"'{search_name}'!='{search.name}'"
                searches.append(search)

        # Perform any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=Collections.searches_find(*, '{search_name}')"
                  f"=>len(searches)={len(searches)}")

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
    def __init__(self, name, parent, search_parent, url, tracing=None):
        # Verify argument types:
        assert isinstance(name, str)
        assert isinstance(parent, Table)
        assert isinstance(search_parent, Search) or search_parent is None
        assert isinstance(url, str)
        assert isinstance(tracing, str) or tracing is None

        # Grab some values from *search* (i.e. *self*):
        search = self

        assert name.find("%3b") < 0

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            search_parent_text = "None" if search_parent is None else f"'{search_parent.name}'"
            print(f"{tracing}=>Search.__init__('{name}', '{parent.name}', "
                  f"{search_parent_text}, '{url}')")

        # Ensure sure that non-template *name is not already in *searches_table*:
        is_template = name.startswith('@')
        collection = parent.collection
        searches_table = collection.searches_table
        # assert (search_parent is None) == (name == "@ALL"), "Search parent problem"
        if not is_template:
            assert name not in searches_table, f"Attempt to duplicate search '{name}'"

        # Initialize the super class for *search* (i.e. *self*):
        search = self
        super().__init__(name, parent, tracing=next_tracing)

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

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=Search.__init__('{name}', '{parent.name}', "
                  f"'{search_parent_text}', '{url}')")

    # Search.can_fetch_more():
    def can_fetch_more(self):
        # Currently, all *Search* objects never have any childre.  Hence, there is nothing fetch:
        return False

    # Search.clicked()
    def clicked(self, tables_editor, model_index, tracing=None):
        # Verify argument types:
        assert isinstance(tables_editor, TablesEditor)
        assert isinstance(model_index, QModelIndex)
        assert isinstance(tracing, str) or tracing is None

        # Preform any requested *tracing*:
        if tracing is not None:
            print("{0}=>Search.clicked()".format(tracing))

        # Fetch the *url* from *search*:
        search = self
        table = search.parent
        assert isinstance(table, Table)
        url = search.url
        assert isinstance(url, str)
        if tracing is not None:
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

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print("{0}<=Search.clicked()".format(tracing))

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
    def file_load(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any required *tracing*:
        search = self
        name = search.name
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>Search.file_load('{name}')")

        # Grab some informtation from parent *table* of *search*:
        table = search.parent
        assert isinstance(table, Table)
        table_name = table.name
        searches = table.children_get()
        searches_size = len(searches)
        # Only load *search* (i.e. *self*) if it is not already *loaded*:
        loaded = search.loaded
        if tracing is not None:
            print(f"{tracing}loaded={loaded} table='{table_name}' searches_size={searches_size}")
        if not loaded:
            # Grab some values from *search*:
            collection = search.collection
            searches_root = collection.searches_root
            relative_path = search.relative_path
            search_full_file_name = os.path.join(searches_root, relative_path + ".xml")
            if tracing is not None:
                print(f"{tracing}search_full_file_name={search_full_file_name}")
            with open(search_full_file_name, "r") as search_file:
                # Read in *search_xml_text* from *search_file*:
                search_xml_text = search_file.read()

                # Parse the XML in *search_xml_text* into *search_tree*:
                search_tree = etree.fromstring(search_xml_text)

                # Now process the contents of *search_tree* and stuff the result:
                search.tree_load(search_tree, tracing=next_tracing)

                # Mark that *table* is no longer sorted since we may updated the
                # *search_parent* and *search_parent_title* fields:
                table = search.parent
                assert isinstance(table, Table)
                table.is_sorted = False

            # Mark *search* as *loaded*:
            search.loaded = True

        # Wrap up any required *tracing*:
        if tracing is not None:
            print(f"{tracing}<=Search.file_load('{name}')")

    # Search.filters_refresh()
    def filters_refresh(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        # next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{0}=>Search.filters_update()".format(tracing))

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

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print("{0}<=Search.filters_refresh()".format(tracing))

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
    def is_deletable(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Grab *search_name* from *search* (i.e. *self*):
        search = self
        search_name = search.name

        # Perform any requested *tracing*:
        # next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>is_deletable('{search_name}')")

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

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=is_deletable('{search_name}')=>{deletable}")
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
    def file_save(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing* for *search* (i.e. *self*):
        search = self
        search_name = search.name
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>Search.file_save('{search_name}')")

        
        # Create the *search_xml_text* from *search*:
        search_xml_lines = list()
        search.xml_lines_append(search_xml_lines, "", tracing=next_tracing)
        search_xml_lines.append("")
        search_xml_text = "\n".join(search_xml_lines)

        # Construct XML *search_file_name*:
        collection = search.collection
        searches_root = collection.searches_root
        relative_path = search.relative_path
        search_file_name = os.path.join(searches_root, relative_path + ".xml")
        if tracing is not None:
            print(f"{tracing}searches_root='{searches_root}'")
            print(f"{tracing}relative_path='{relative_path}'")
            print(f"{tracing}search_file_name='{search_file_name}'")

        # Write *search_xml_text* out to *search_xml_file_name*:
        search.directory_create(searches_root);
        with open(search_file_name, "w") as search_file:
            search_file.write(search_xml_text)

        # Mark *search* as *loaded* since we just wrote out the contents:
        search.loaded = True

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=Search.file_save('{search_name}')")

    # Search.partial_load():
    # def partial_load(self, tracing=None):
    #     # Verify argument types:
    #     assert isinstance(tracing, str) or tracing is None
    #     assert False

    #     # Perform any requested *tracing*:
    #     if tracing is not None:
    #         print(f"{tracing}=>Searches.populate(*)")

    #     # Compute the *glob_pattern* for searching:
    #     searches = self
    #     path = searches.path
    #     slash = os.sep
    #     if tracing is not None:
    #         print(f"{tracing}glob_pattern='{glob_pattern}'")
    #     #for index, file_name in enumerate(glob.glob(glob_pattern, recursive=True)):
    #     #    print(f"Search[{index}]:'{file_name}'")

    #     # Wrap up any requested *tracing*:
    #     if tracing is not None:
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
    def table_set(self, new_table, tracing=None):
        # Verify argument types:
        assert isinstance(new_table, Table) or new_table is None

        # Perform any requested *tracing*:
        # next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{0}=>Search.table_set('{1})".
                  format(tracing, "None" if new_table is None else new_table.name))

        search = self
        search.table = new_table

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print("{0}<=Search.table_set('{1}')".
                  format(tracing, "None" if new_table is None else new_table.name))

    # Search.name_get():
    def name_get(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing* for *search* (i.e. *self*::
        search = self
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>Search.name_get('{search.name}')")

        # Grab some values from *search* (i.e. *self*):
        search_name = search.name
        table = search.parent

        # Make sure that all *searches* associated with *table* are loaded from their
        # associated `.xml` files:
        table.searches_load(tracing=next_tracing)

        # Make sure that *table* is *sort*'ed:
        table = search.parent
        assert isinstance(table, Table)
        table.sort(tracing=next_tracing)

        # Construct the *name*:
        search_parent = search.search_parent
        name = search_name if search_parent is None else f"{search_name} ({search_parent.name})"

        # Wrap any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}=>Search.name_get('{search.name}')=>'{name}'")
        return name

    # Search.tree_load():
    def tree_load(self, search_tree, tracing=None):
        # Verify argument types:
        assert isinstance(search_tree, etree._Element)
        assert isinstance(tracing, str) or tracing is None

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
        table_name = table.name

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
    def xml_lines_append(self, xml_lines, indent, tracing=None):
        # Verify argument types:
        assert isinstance(xml_lines, list)
        assert isinstance(indent, str)
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>Search.xml_lines_append()")

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
        #     filter.xml_lines_append(xml_lines, filter_indent, tracing=next_tracing)
        # xml_lines.append(f'{indent}  </Filters>')

        # Wrap up the `<Search>` element:
        xml_lines.append(f'{indent}</Search>')

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=Search.xml_lines_append()")


# Table:
class Table(Node):

    # Table.__init__():
    def __init__(self, name, parent, url, tracing=None):
        # Verify argument types:
        assert isinstance(name, str)
        assert isinstance(parent, Directory) or isinstance(parent, Collection)
        assert isinstance(url, str)
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            parent_name = parent.name
            print(f"{tracing}=>Table.__init__('{name}', '{parent.name}', 'url'")

        # Initialize the *Node* super-class for *table* (i.e. *self*)
        table = self
        super().__init__(name, parent, tracing=next_tracing)

        # Load additional values into *table*:
        table.comments = list()
        table.is_sorted = False
        table.loaded = False
        table.parameters = list()
        table._relative_path = None
        table.searches_table = dict()
        table.url = None

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=Table.__init__('{name}', '{parent.name}', 'url'")

    # Table.bind_parameters_from_imports():
    def bind_parameters_from_imports(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        # next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{0}=>Tables.bind_parameters_from_imports()".format(tracing))

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

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print("{0}<=Tables.bind_parameters_from_imports()".format(tracing))

    # Table.can_fetch_more():
    def can_fetch_more(self):
        # Conceptually, every table as a default `@ALL` search.  We return *True* if
        # the `@ALL` search has not actually been created yet for *table* (i.e. *self*):
        table = self
        searches = table.children_get()
        can_fetch_more = (len(searches) == 0)
        return can_fetch_more

    # Table.clicked():
    def clicked(self, tables_editor, model_index, tracing=None):
        # Verify argument types:
        assert isinstance(tables_editor, TablesEditor)
        assert isinstance(model_index, QModelIndex)
        assert isinstance(tracing, str) or tracing is None

        # Preform any requested *tracing*:
        if tracing is not None:
            print("{0}=>Table.clicked()".format(tracing))

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
            if tracing is not None:
                print("{0}Before len(tables)={1}".format(tracing, len(tables)))
            tables_editor.tables_combo_edit.item_append(table)
            if tracing is not None:
                print("{0}After len(tables)={1}".format(tracing, len(tables)))

        # Force whatever is visible to be updated:
        tables_editor.update(tracing=tracing)

        # Make *table* the current one:
        tables_editor.current_table = table
        tables_editor.current_parameter = None
        tables_editor.current_enumeration = None
        tables_editor.current_comment = None
        tables_editor.current_search = None

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print("{0}<=Table.clicked()".format(tracing))

    # Table.csv_read_and_process():
    def csv_read_and_process(self, csv_directory, bind=False, tracing=None):
        # Verify argument types:
        assert isinstance(csv_directory, str)
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing* for *table* (i.e. *self*):
        table = self
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>Table.csv_read_process('{table.name}', '{csv_directory}', {bind})")

        # Grab *parameters* from *table* (i.e. *self*):
        parameters = table.parameters
        assert isinstance(parameters, list)

        # Open *csv_file_name* read in both *rows* and *headers*:
        csv_full_name = table.csv_full_name_get()
        assert isinstance(csv_full_name, str)
        if tracing is not None:
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

            # if tracing is not None:
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
            table.bind_parameters_from_imports(tracing=next_tracing)
        table.file_save(tracing=next_tracing)

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=Table.csv_read_process('{table.name}', '{csv_directory}', {bind})")

    # Table.directories_get():
    def directories_get(self):
        return []

    # Table.fetch_more():
    def fetch_more(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        table = self
        name = table.name
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>Table.fetch_more('{name}')")

        # Create *all_search* if it does not already exist (i.e. *searches_size* is 0):
        searches = table.children_get()
        searches_size = len(searches)
        if tracing is not None:
            print(f"{tracing}1:searches_size={searches_size}")
        if searches_size == 0:
            # Note that the call to the *Search*() has the side-effect of appending
            # *all_search* to the children of *table*:
            #base_name = Encode.to_file_name(name)
            all_search = Search("@ALL", table, None, table.url, tracing=next_tracing)
            assert table.has_child(all_search)
            assert len(searches) == 1
            all_search.file_save(tracing=next_tracing)

            # Make sure that *table* is fully loaded so we can grab the *url*:
            table.file_load(tracing=next_tracing)
            searches_size = len(searches)
            if tracing is not None:
                print(f"{tracing}2:searches_size={searches_size}")
            assert searches_size == 1
            url = table.url

            # Fill in the rest of *all_search* from *table*:
            comment = SearchComment(language="EN", lines=list())
            all_search.comments.append(comment)
            all_search.url = url

            # Force *all_search* out to the file system:
            all_search.file_save(tracing=next_tracing)
            if tracing is not None:
                searches_size = len(searches)
                print(f"{tracing}3:searches_size={searches_size}")

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=Table.fetch_more('{name}')")

    # Table.file_load():
    def file_load(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing* for *table* (i.e. *self*):
        table = self
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            table_name = table.name
            print(f"{tracing}=>Table.file_load('{table_name}')")

        # Only load *table* if it is not already *loaded*:
        loaded = table.loaded
        searches = table.children_get()
        searches_size = len(searches)
        if tracing is not None:
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
                table.tree_load(table_tree, tracing=next_tracing)

            # Mark *table* as *loaded*:
            table.loaded = True

        # Wrap up any requested *tracing*:
        if tracing is not None:
            next_tracing = tracing + " "
            print(f"{tracing}<=Table.file_load('{table_name}')")

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
    def name_get(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform an requested *tracing*:
        table = self
        name = table.name
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>Table.name_get('{name}')")

        # Force *table* (i.e. *self*) *load* if it has not already been loaded:
        table.file_load(tracing=next_tracing)

        # Augment *name* with the *searches_size*:
        searches = table.children_get()
        searches_size = len(searches)
        if len(searches) >= 2:
            name += f" ({searches_size})"

        # Wrap up an requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=Table.title_get()=>{name}")
        return name

    # Table.partial_load():
    def partial_load(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        table = self
        # tracing = "res:" if self.name.startswith("resistors-chip") else tracing
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>Table.partial_load('{table.name}')")

        # Grab some values from *table* (i.e. *self*):
        table = self
        name = table.name
        relative_path = table.relative_path
        collection = table.collection

        # Compute *searches_path* which is the directory that contains the *Search* `.xml` files:
        collection_root = collection.collection_root
        searches_root = collection.searches_root
        searches_directory = os.path.join(searches_root, relative_path)
        if tracing is not None:
            print(f"{tracing}collection_root='{collection_root}'")
            print(f"{tracing}searches_root='{searches_root}'")
            print(f"{tracing}relative_path='{relative_path}'")
            print(f"{tracing}searches_directory='{searches_directory}'")

        # Scan through *searches_path* looking for `.xml` files:
        if os.path.isdir(searches_directory):
            # *searches_path* is a directory so we scan it:
            for index, search_file_name in enumerate(sorted(list(os.listdir(searches_directory)))):
                # Preform requested *tracing*:
                if tracing is not None:
                    print(f"{tracing}Search[{index}]:'{search_file_name}'")

                # Skip over any files that do not end with `.xml` suffix:
                if search_file_name.endswith(".xml"):
                    # Extract *name* and *title* from *file_name* (ignoring the `.xml` suffix):
                    file_base = search_file_name[:-4]
                    search_name = Encode.from_file_name(file_base)

                    # Create *search* and then save it out to the file system:
                    search = Search(search_name, table, None, "??", tracing=next_tracing)
                    assert table.has_child(search)
                    search.loaded = False

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=Table.partial_load('{table.name}')")

    # Table.sort():
    def sort(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing* for *table* (i.e. *self*):
        table = self
        name = table.name
        if tracing is not None:
            print(f"{tracing}=>Table.sort('{name}')")

        # Only sort *table* if it is not *is_sorted*:
        is_sorted = table.is_sorted
        if tracing is not None:
            print(f"{tracing}is_sorted={is_sorted}")
        if not is_sorted:
            # Grab *searches* list from *table* (i.e. *self*):
            searches = table.children_get()
            searches_size = len(searches)
            if tracing is not None:
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
                if tracing is not None:
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
            #     if tracing is not None:
            #         search_parent_text = ("None" if search_parent is None
            #                               else f"'{search_parent.name}'")
            #         print(f"{tracing}Search[{index}]:'{search.name}' {search_parent_text}")

            # Now sort *searches*:
            searches.sort(key=Search.key)

            # Mark that *table* *is_sorted*:
            table.is_sorted = True

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=Table.sort('{name}')")

    # Table.save():
    def save(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        table = self
        # next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{0}=>Table.save('{1}')".format(tracing, table.name))

        # Write out *table* (i.e. *self*) to *file_name*:
        output_file_name = table.file_name
        xml_text = table.to_xml_string()
        with open(output_file_name, "w") as output_file:
            output_file.write(xml_text)

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print("{0}=>Table.save('{1}')".format(tracing, table.name))

    # Table.search_directory_get():
    def search_directory_get(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Preform any requested *tracing* for *table* (i.e. *self*):
        table = self
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>Table.search_directory_get('{table.name}')")

        # Compute *search_directory*:
        searches_root = table.searches_root_get()
        relative_path = table.relative_path
        table_name = table.name
        table_base_name = Encode.to_file_name(table_name)
        search_directory  = os.path.join(searches_root, relative_path, table_base_name)
        if tracing is not None:
            print(f"{tracing}searches_root='{searches_root}'")
            print(f"{tracing}relative_path='{relative_path}'")
            #print(f"{tracing}table__directory='{table_directory}'")
            print(f"{tracing}search_directory='{search_directory}'")

        # Make sure *search_directory* exists:
        if not os.path.isdir(search_directory):
            os.makedirs(search_directory)
            if tracing is not None:
                print(f"{tracing}Created directory '{search_directory}'")

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=Table.search_directory_get('{table.name}')=>'{search_directory}'")
        return search_directory

    # Table.searches_load():
    def searches_load(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing* for *table* (i.e. *self*):
        table = self
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>Table.searches_load('{table.name}')")

        # Grab some values from *table* (i.e. *self*):
        table_searches = dict()
        searches_loaded_count = 0
        searches = table.children_get()
        for search in searches:
            # Make sure *search* is *loaded*.  We test *loaded* up here to prevent
            # a lot of unnecessary calls to *file_load*:
            if not search.loaded:
                search.file_load(tracing=next_tracing)
                assert search.loaded
                searches_loaded_count += 1

            # Build up *tables_searches_table_table* with all of the *searches* to used for
            # for the upcoming parent search fix-up step:
            table_searches[search.name] = search

        # Fix up the search parent links:
        if searches_loaded_count >= 1:
            for search in searches:
                search_parent_name = search.search_parent_name
                if tracing is not None:
                    print(f"Search '{search.name}' parent name is '{search_parent_name}'")
                if search_parent_name != "":
                    assert search_parent_name in table_searches, (f"'{search_parent_name} '"
                                                                  f"not in {table_searches.keys()}")
                    search_parent = table_searches[search_parent_name]
                    search.search_parent = search_parent
                    if tracing is not None:
                        print(f"Setting search '{search.name}' "
                              f"search parent to '{search_parent.name}'")
                else:
                    if tracing is not None:
                        print(f"Search '{search.name}' has no search parent.")

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=Table.searches_load('{table.name}')")

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
    def tree_load(self, table_tree, tracing=None):
        # Verify argument types:
        assert isinstance(table_tree, etree._Element)
        assert isinstance(tracing, str) or tracing is None

        # Perform an request *tracing*:
        # next_tracing = None if tacing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>Table.tree_load()")

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

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=Table.file_load()")

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

    def __init__(self, order_root):
        """ *Order*: Initialize *self* for an order. """
        # Verify argument types:
        assert isinstance(order_root, str)

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
        order.excluded_vendor_names = {}  # Dict[String, List[str]]: Excluded vendors
        order.final_choice_parts = []
        order.inventories = []            # List[Inventory]: Existing inventoried parts
        order.order_root = order_root
        order.projects = []               # List[Project]
        order.projects_table = {}         # Dict[Net_File_Name, Project]
        order.selected_vendor_names = None
        order.stale = 2 * 24 * 60 * 60
        order.requests = []               # List[Request]: Additional requested parts
        order.vendor_priorities = vendor_priorities
        order.vendor_priority = 10
        order.vendor_searches_root = vendor_searches_root

    # Order.project_create():
    def project_create(self, name, revision, net_file_name, count,
                       positions_file_name=None, tracing=None):
        """ *Order*: Create a *Project* containing *name*, *revision*,
            *net_file_name* and *count*. """

        # Verify argument types:
        assert isinstance(name, str)
        assert isinstance(revision, str)
        assert isinstance(net_file_name, str)
        assert isinstance(count, int)
        assert isinstance(positions_file_name, str) or positions_file_name is None
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>Order.project_create(*, '{name}', '{revision}', "
                  f"'{net_file_name}', '{count}, '{positions_file_name})")

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
                              tracing=next_tracing)
            projects_table[net_file_name] = project
            projects.append(project)

        # Wrap up any requested *tracing* and return *project*:
        if tracing is not None:
            print(f"{tracing}<=Order.project_create(*, '{name}', '{revision}', "
                  f"'{net_file_name}', '{count}, '{positions_file_name})=>'{project.name}'")
        return project

    # Order.bom_write():
    def bom_write(self, bom_file_name, key_function):
        """ *Order*: Write out the BOM (Bill Of Materials) for the
            *Order* object (i.e. *self*) to *bom_file_name* ("" for stdout)
            using *key_function* to provide the sort key for each
            *ChoicePart*.
        """

        # Verify argument types:
        assert isinstance(bom_file_name, str)
        assert callable(key_function)

        order = self

        # Grab *database* and *vendors*:
        # database = self.database
        excluded_vendor_names = self.excluded_vendor_names

        # Open *bom_file*
        bom_file = sys.stdout
        if bom_file_name != "":
            bom_file = open(bom_file_name, "w")

        # Sort *final_choice_parts* using *key_function*.
        final_choice_parts = order.final_choice_parts
        final_choice_parts.sort(key=key_function)

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
            bom_file.write("  {0}:{1};{2} {3}:{4}\n".format(
                           choice_part.name,
                           choice_part.kicad_footprint, choice_part.description,
                           choice_part.count_get(), choice_part.references_text_get()))

            # Select the vendor_part and associated quantity/cost
            choice_part.select(excluded_vendor_names, True)
            # selected_actual_part = choice_part.selected_actual_part
            selected_vendor_part = choice_part.selected_vendor_part
            selected_order_quantity = choice_part.selected_order_quantity
            selected_total_cost = choice_part.selected_total_cost
            selected_price_break_index = choice_part.selected_price_break_index

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

        # Wrap up the *bom_file*:
        bom_file.write("Total: ${0:.2f}\n".format(total_cost))
        bom_file.close()

    # Order.check():
    def check(self, collections, tracing=None):
        # Verify argument types:
        assert isinstance(collections, Collections)
        
        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>Order.check()")

        # Check each of the *projects* in *order* (i.e. *self*):
        order= self
        projects = order.projects
        for project in projects:
            project.check(collections, tracing=next_tracing)

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=Order.check()")

    # Order.csvs_write():
    def csv_write(self, tracing=None):
        """ *Order*: Write out the *Order* object (i.e. *self) BOM (Bill Of Materials)
            for each vendor as a .csv (Comma Seperated Values).
        """
        # Verify argument types:
        

        # Grab *database* and *vendors*:
        # database = self.database
        excluded_vendor_names = self.excluded_vendor_names

        # Sort *final_choice_parts* using *key_function*.
        order = self
        final_choice_parts = order.final_choice_parts
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
    def exclude_vendors_to_reduce_shipping_costs(self, choice_parts,
                                                 excluded_vendor_names, reduced_vendor_messages):
        """ *Order*: Sweep through *choice_parts* and figure out which vendors
            to add to *excluded_vendor_names* to reduce shipping costs.
        """

        tracing = False
        # tracing = True
        if tracing:
            print("=>exclude_vendors_to_reduce_shipping_costs")

        # Verify argument types:
        assert isinstance(choice_parts, list)
        assert isinstance(excluded_vendor_names, dict)
        assert isinstance(reduced_vendor_messages, list)

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

        if tracing:
            print("<=exclude_vendors_to_reduce_shipping_costs")

    # Order.exclude_vendors_with_high_minimums():
    def exclude_vendors_with_high_minimums(self, choice_parts, excluded_vendor_names,
                                           reduced_vendor_messages, tracing=None):
        """ *Order*: Sweep through *choice* parts and figure out if the
            vendors with large minimum orders can be dropped:
        """

        # Verify argument types:
        assert isinstance(choice_parts, list)
        assert isinstance(excluded_vendor_names, dict)
        assert isinstance(reduced_vendor_messages, list)

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>exclude_vendors_with_high_minimums(...)")
        assert False

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
    def final_choice_parts_compute(self, collections, tracing=None):
        """ *Order*: Return a list of final *ChoicePart* objects to order
            for the the *Order* object (i.e. *self*).  This routine also
            has the side effect of looking up the vendor information for
            each selected *ChoicePart* object.
        """

        # Verify argument types:
        assert isinstance(collections, Collections)
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>Order.final_choice_parts_compute(*)")

        # Grab the some values from *order* (i.e. *self*):
        order = self
        projects = order.projects

        # Construct *project_parts_table* table (Dict[name, List[ProjectPart]]) so that every
        # we have a name to a List[ProjectPart] mapping.
        project_parts_table = {}
        for project_index, project in enumerate(projects):
            if tracing is not None:
                print(f"{tracing}Project[{project_index}]:'{project.name}'")

            # Make sure that each *project_part* in *project* is on a list somewhere
            # in the *project_parts_table*:
            project_parts = project.project_parts
            for project_part_index, project_part in enumerate(project_parts):
                assert isinstance(project_part, ProjectPart), (f"type(project_part)="
                                                               f"{type(project_part)}")
                if tracing is not None:
                    print(f"{tracing}ProjectPart[{project_part_index}]:'{project_part.name}'")
                project_part_name = project_part.name
                if not project_part_name in project_parts_table:
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
            if tracing is not None:
                print(f"{tracing}search_name='{search_name}'")
            assert len(project_parts) >= 1
            searches = collections.searches_find(search_name, tracing=next_tracing)
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
            new_actual_parts = collections.actual_parts_lookup(choice_part, tracing=next_tracing)

            # Get reasonably up-to-date pricing and availability information about
            # each *ActualPart* in actual_parts.  *order* is needed to loccate where
            # the cached information is:
            choice_part.vendor_parts_refresh(new_actual_parts, order, tracing=next_tracing)

        # Wrap up any requested *tracing* and return *final_choice_parts*:
        if tracing is not None:
            print(f"{tracing}<=Order.final_choice_parts_compute(*)"
                  f"=>len([...])={len(final_choice_parts)}")
        order.final_choice_part = final_choice_parts
        return final_choice_parts

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

            for project_part_index, project_part in enumerate(project_parts):
                # Grab some values from *project_part*:
                project_part_name = project_part.name

                searches = collecton.searches_find(project_part_name)
                choice_part = ChoicePart()
                    
                choice_parts = project_part.choice_parts()
                for choice_part_index, choice_part in enumerate(choice_parts):
                    # Do some consistency checking:
                    choice_part_name = choice_part.name
                    assert isinstance(choice_part, ChoicePart), ("Not a choice part "
                                                                 f"'{choice_part_name}'")
                    if tracing is not None:
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
                    choice_part.pose_part_append(pose_part)


        # Save the *database* because we've loaded all of the *vendor_parts*'s:
        #database.save()

        # Sort by *final_choice_parts* by schematic part name:
        final_choice_parts = list(choice_parts_table.values())
        final_choice_parts.sort(
          key=lambda choice_part: choice_part.name)
        order.final_choice_parts = final_choice_parts

        # Sweep through *final_choice_parts* and force the associated
        # *PosePart*'s to be in a reasonable order:
        for choice_part in final_choice_parts:
            # Make sure that we only have *ChoicePart* objects:
            assert isinstance(choice_part, ChoicePart)
            choice_part.pose_parts_sort()

        # Wrap up any requested *tracing* and return *final_choice_parts*:
        if tracing is not None:
            for choice_part_index, choice_part in enumerate(final_choice_parts):
                print(f"{tracing}Final_Choice_Part[{choice_part_index}]:"
                      f"'{choice_part.name}")
            print(f"{tracing}<=Order.final_choice_parts_compute(*) => [...]")
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
    def process(self, collections, tracing=None):
        """ *Order*: Process the *Order* object (i.e. *self*.) """
        # Verify argument types:
        assert isinstance(collections, Collections)
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>Order.process(*)")

        # Use *order instead of *self*:
        order = self

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
        final_choice_parts = order.final_choice_parts_compute(collections, tracing=next_tracing)

        excluded_vendor_names = order.excluded_vendor_names
        selected_vendor_names = order.selected_vendor_names
        if selected_vendor_names is not None:
            all_vendor_names = order.vendor_names_get(final_choice_parts, excluded_vendor_names)
            for vendor_name in all_vendor_names:
                if vendor_name not in selected_vendor_names:
                    excluded_vendor_names[vendor_name] = None
        else:
            # Now we winnow down the total number of vendors to order from
            # to 1) minimize the number of orders that can be messed up
            # (i.e. supply chain simplication) and to save shipping costs.
            # There are two steps -- throw out vendors with excessive minimum
            # order amounts followed by throwing out vendors where the savings
            # do not exceed additional shipping costs.
            #order.exclude_vendors_with_high_minimums(
            #  final_choice_parts, excluded_vendor_names, reduced_vendor_messages)
            pass

        order.exclude_vendors_to_reduce_shipping_costs(
          final_choice_parts, excluded_vendor_names, reduced_vendor_messages)

        # Write out *reduced_vendor_messages* to a report file:
        order_root = order.order_root
        reduced_vendor_messages_file_name = os.path.join(order_root, "vendor_reduction_report.txt")
        with open(reduced_vendor_messages_file_name, "w") as reduced_vendor_messages_file:
            for reduced_vendor_message in reduced_vendor_messages:
                reduced_vendor_messages_file.write(reduced_vendor_message)
            reduced_vendor_messages_file.close()

        # Let the user know how many vendors were eliminated:
        reduced_vendor_messages_size = len(reduced_vendor_messages)
        if reduced_vendor_messages_size >= 1:
            print(f"{reduced_vendor_messages_size} vendors eliminated.  "
                  f"See '{reduced_vendor_messages_file_name}' file for why.")

        # Check for missing footprints:
        # order.footprints_check(final_choice_parts)
        # order.positions_process()

        # Print out the final selected vendor summary:
        order.summary_print(final_choice_parts, excluded_vendor_names)

        # Generate the bom file reports for *self.final_choice_parts*:
        order_root = order.order_root
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

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=Order.process(*)")

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
    def summary_print(self, choice_parts, excluded_vendor_names):
        """ *Order*: Print a summary of the selected vendors.
        """

        # Verify argument types:
        assert isinstance(choice_parts, list)
        assert isinstance(excluded_vendor_names, dict)

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
    def check(self, collections, tracing=None):
        # Verify argument types:
        assert isinstance(collections, Collections)
        assert isinstance(tracing, str) or tracing == None

        # Perform any requested *tracing* for *pose_part* (i.e. *self*):
        pose_part = self    
        reference = pose_part.reference
        project = pose_part.project
        project_name = project.name
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>PosePart.check('{project_name}', '{reference}')")

        # Check the underlying *project_part*:
        project_part = pose_part.project_part
        search_name = project_part.name
        collections.check(search_name, project_name, reference, tracing=next_tracing)

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=PosePart.check('{project_name}', '{reference}')")

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
        assert isinstance(database, Database)

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

    # PriceBreak.compute():
    def compute(self, needed):
        """ *PriceBreak*: """

        assert isinstance(needed, int)

        self.order_quantity = order_quantity = max(needed, self.quantity)
        self.order_price = order_quantity * self.price

    # PriceBreak.__lt__():
    def __lt__(self, price_break2):
        # Verify argument types:
        assert isinstance(price_break2, PriceBreak)

        price_break1 = self
        return price_break1.price < price_break2.price

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
    def __init__(self, name, revision, net_file_name, count, order,
                 positions_file_name=None, tracing=None):
        """ Initialize a new *Project* object (i.e. *self*) containing *name*, *revision*,
            *net_file_name*, *count*, *order*, and optionally *positions_file_name.
        """

        # Verify argument types:
        assert isinstance(name, str)
        assert isinstance(revision, str)
        assert isinstance(net_file_name, str)
        assert isinstance(count, int)
        assert isinstance(order, Order)
        assert isinstance(positions_file_name, str) or positions_file_name is None
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is None:
            print(f"{tracing}=>Project.__init__(*, '{name}', '{revision}', '{net_file_name}', "
                  f"*, '{positions_file_name}'")

        # Load up *project* (i.e. *self*):
        project = self
        project.name = name
        project.revision = revision
        project.net_file_name = net_file_name
        project.count = count
        project.positions_file_name = positions_file_name
        project.order = order
        project.pose_parts_table = {}     # Dict[name, ProjectPart]
        project.project_parts = []           # List[ProjectPart]
        project.project_parts_table = {}     # Dict[name, ProjectPart]
        project.all_pose_parts = []          # List[PosePart] of all project parts
        project.installed_pose_parts = []    # List[PosePart] project parts to be installed
        project.uninstalled_pose_parts = []  # List[PosePart] project parts not to be installed

        # Read in the `.net` file named *net_file_name*:
        project.net_file_read(tracing=next_tracing)

        # Wrap-up any requested *tracing*:
        if tracing is None:
            print(f"{tracing}<=Project.__init__(*, '{name}', '{revision}', '{net_file_name}', "
                  f"*, '{positions_file_name}')")

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

    # Project.project_aprt_append():
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

    # Project.check():
    def check(self, collections, tracing=None):
        # Verify argument types:
        assert isinstance(collections, Collections)

        # Perform an requested *tracing* for *project* (i.e. *self*):
        project = self
        name = project.name
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>Project_check('{name}')")

        # Check *all_pose_parts*:
        all_pose_parts = project.all_pose_parts
        for pose_part in all_pose_parts:
            pose_part.check(collections, tracing=next_tracing)

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=Project_check('{name}')")

    # Project.new_file_read():
    def net_file_read(self, tracing=None):
        """ Read in net file for the *Project* object (i.e. *self*).
        """
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>Project.new_file_read()")

        # Prevent accidental double of *project* (i.e. *self*):
        project = self
        pose_parts = project.all_pose_parts
        assert len(pose_parts) == 0

        # Process *net_file_name* adding footprints as needed:
        errors = 0
        net_file_name = project.net_file_name
        # print("Read '{0}'".format(net_file_name))
        if net_file_name.endswith(".net"):
            with open(net_file_name, "r") as net_stream:
                # Read contents of *net_file_name* in as a string *net_text*:
                net_text = net_stream.read()
                print(f"Read in file '{net_file_name}'")

            # Parse *net_text* into *net_se* (i.e. net S-expression):
            net_se = sexpdata.loads(net_text)
            # print("\nsexpedata.dumps=", sexpdata.dumps(net_se))
            # print("")
            # print("net_se=", net_se)
            # print("")

            # Visit each *component_se* in *net_se*:
            net_file_changed = False
            #database = project.order.database
            components_se = se_find(net_se, "export", "components")

            # Each component has the following form:
            #
            #        (comp
            #          (ref SW123)
            #          (footprint nickname:NAME)              # May not be present
            #          (libsource ....)
            #          (sheetpath ....)
            #          (tstamp xxxxxxxx))
            # print("components=", components_se)
            for component_index, component_se in enumerate(components_se[1:]):
                # print("component_se=", component_se)
                # print("")

                # Grab the *reference* from *component_se*:
                reference_se = se_find(component_se, "comp", "ref")
                reference = reference_se[1].value()
                # print("reference_se=", reference_se)
                # print("")

                # Find *part_name_se* from *component_se*:
                part_name_se = se_find(component_se, "comp", "value")

                # Suprisingly tedious, extract *part_name* as a string:
                if isinstance(part_name_se[1], Symbol):
                    part_name = part_name_se[1].value()
                elif isinstance(part_name_se[1], int):
                    part_name = str(part_name_se[1])
                elif isinstance(part_name_se[1], float):
                    part_name = str(part_name_se[1])
                elif isinstance(part_name_se[1], str):
                    part_name = part_name_se[1]
                else:
                    assert False, "strange part_name: {0}". \
                      format(part_name_se[1])

                # Strip *comment* out of *part_name* if it exists:
                comment = ""
                colon_index = part_name.find(':')
                if colon_index >= 0:
                    comment = part_name[colon_index + 1:]
                    part_name = part_name[0:colon_index]

                # Now see if we have a match for *part_name* in *database*:
                project_part = project.project_part_find(part_name)

                # We have a match; create the *pose_part*:
                pose_part = PosePart(project, project_part, reference, comment)
                project.pose_part_append(pose_part)

                # Ignore footprints for now:
                if False:
                    # Grab *kicad_footprint* from *project_part*:
                    kicad_footprint = project_part.kicad_footprint
                    assert isinstance(kicad_footprint, str)

                    # Grab *footprint_se* from *component_se* (if it exists):
                    footprint_se = se_find(component_se, "comp", "footprint")
                    # print("footprint_se=", footprint_se)
                    # print("Part[{0}]:'{1}' '{2}' changed={3}".format(
                    #    component_index, part_name, kicad_footprint, net_file_changed))

                    # Either add or update the footprint:
                    if footprint_se is None:
                        # No footprint in the .net file; just add one:
                        component_se.append(
                          [Symbol("footprint"), Symbol("common:" + kicad_footprint)])
                        print("Part {0}: Adding binding to footprint '{1}'".
                              format(part_name, kicad_footprint))
                        net_file_changed = True
                    else:
                        # We have a footprint in .net file:
                        previous_footprint = footprint_se[1].value()
                        previous_split = previous_footprint.split(':')
                        current_split = kicad_footprint.split(':')
                        assert len(previous_split) > 0
                        assert len(current_split) > 0
                        if len(current_split) == 2:
                            # *kicad_footprint* has an explicit library,
                            # so we can just use it and ignore
                            # *previous_footprint*:
                            new_footprint = kicad_footprint
                        elif len(current_split) == 1 and len(previous_split) == 2:
                            # *kicad_footprint* does not specify a library,
                            # but the *previous_footprint* does.  We build
                            # *new_foot_print* using the *previous_footprint*
                            # library and the rest from *kicad_footprint*:
                            new_footprint = \
                              previous_split[0] + ":" + kicad_footprint
                            # print("new_footprint='{0}'".format(new_footprint))
                        elif len(current_split) == 1:
                            new_footprint = "common:" + kicad_footprint
                        else:
                            assert False, ("previous_slit={0} current_split={1}".
                                           format(previous_split, current_split))
    
                        # Only do something if it changed:
                        if previous_footprint != new_footprint:
                            # Since they changed, update in place:
                            # if isinstance(project_part, AliasPart):
                            #        print("**AliasPart.footprint={0}".
                            #          format(project_part.kicad_footprint))
                            print("Part '{0}': Footprint changed from '{1}' to '{2}'".
                                  format(part_name, previous_footprint, new_footprint))
                            footprint_se[1] = Symbol(new_footprint)
                            net_file_changed = True

            # Write out updated *net_file_name* if *net_file_changed*:
            if net_file_changed:
                print("Updating '{0}' with new footprints".
                      format(net_file_name))
                net_file = open(net_file_name, "wa")
                # sexpdata.dump(net_se, net_file)
                net_se_string = sexpdata.dumps(net_se)
                # sexpdata.dump(net_se, net_file)

                # Now use some regular expressions to improve formatting to be more like
                # what KiCad outputs:
                net_se_string = re.sub(" \\(design ", "\n  (design ", net_se_string)

                # Sheet part of file:
                net_se_string = re.sub(" \\(sheet ",       "\n    (sheet ",         net_se_string)
                net_se_string = re.sub(" \\(title_block ", "\n      (title_block ", net_se_string)
                net_se_string = re.sub(" \\(title ",       "\n        (title ",     net_se_string)
                net_se_string = re.sub(" \\(company ",     "\n        (company ",   net_se_string)
                net_se_string = re.sub(" \\(rev ",         "\n        (rev ",       net_se_string)
                net_se_string = re.sub(" \\(date ",        "\n        (date ",      net_se_string)
                net_se_string = re.sub(" \\(source ",      "\n        (source ",    net_se_string)
                net_se_string = re.sub(" \\(comment ",     "\n        (comment ",   net_se_string)

                # Components part of file:
                net_se_string = re.sub(" \\(components ", "\n  (components ",    net_se_string)
                net_se_string = re.sub(" \\(comp ",       "\n    (comp ",        net_se_string)
                net_se_string = re.sub(" \\(value ",      "\n      (value ",     net_se_string)
                net_se_string = re.sub(" \\(footprint ",  "\n      (footprint ", net_se_string)
                net_se_string = re.sub(" \\(libsource ",  "\n      (libsource ", net_se_string)
                net_se_string = re.sub(" \\(sheetpath ",  "\n      (sheetpath ", net_se_string)
                net_se_string = re.sub(" \\(path ",       "\n      (path ",      net_se_string)
                net_se_string = re.sub(" \\(tstamp ",     "\n      (tstamp ",    net_se_string)

                # Library parts part of file
                net_se_string = re.sub(" \\(libparts ",    "\n  (libparts ",    net_se_string)
                net_se_string = re.sub(" \\(libpart ",     "\n    (libpart ",   net_se_string)
                net_se_string = re.sub(" \\(description ", "\n      (description ",  net_se_string)
                net_se_string = re.sub(" \\(fields ",      "\n      (fields ",  net_se_string)
                net_se_string = re.sub(" \\(field ",       "\n        (field ", net_se_string)
                net_se_string = re.sub(" \\(pins ",        "\n      (pins ",    net_se_string)
                # net_se_string = re.sub(" \\(pin ",         "\n        (pin ",   net_se_string)

                # Network portion of file:
                net_se_string = re.sub(" \\(nets ", "\n  (nets ", net_se_string)
                net_se_string = re.sub(" \\(net ",  "\n    (net ", net_se_string)
                net_se_string = re.sub(" \\(node ", "\n      (node ", net_se_string)

                # General substitutions:
                # net_se_string = re.sub(" \\;", ";", net_se_string)
                # net_se_string = re.sub(" \\.", ".", net_se_string)

                net_file.write(net_se_string)
                net_file.close()
            # else:
            #        print("File '{0}' not changed".format(net_file_name))

        elif net_file_name.ends_with(".cmp"):
            # Read in {cmp_file_name}:
            cmp_file_name = net_file_name
            cmp_stream = open(cmp_file_name, "r")
            cmp_lines = cmp_stream.readlines()
            cmp_stream.close()

            # Process each {line} in {cmp_lines}:
            database = project.database
            errors = 0
            line_number = 0
            for line in cmp_lines:
                # Keep track of {line} number for error messages:
                line_number = line_number + 1

                # There are three values we care about:
                if line.startswith("BeginCmp"):
                    # Clear out the values:
                    reference = None
                    part_name = None
                    footprint = None
                elif line.startswith("Reference = "):
                    reference = line[12:-2]
                elif line.startswith("ValeurCmp = "):
                    part_name = line[12:-2]
                    # print("part_name:{0}".format(part_name))
                    double_underscore_index = part_name.find("__")
                    if double_underscore_index >= 0:
                        shortened_part_name = \
                          part_name[:double_underscore_index]
                        # print("Shorten part name '{0}' => '{1}'".
                        #  format(part_name, shortened_part_name))
                        part_name = shortened_part_name
                elif line.startswith("IdModule  "):
                    footprint = line[12:-2].split(':')[1]
                    # print("footprint='{0}'".format(footprint))
                elif line.startswith("EndCmp"):
                    part = database.part_lookup(part_name)
                    if part is None:
                        # {part_name} not in {database}; output error message:
                        print("File '{0}', line {1}: Part Name {2} ({3} {4}) not in database".
                              format(cmp_file_name, line_number, part_name, reference, footprint))
                        errors = errors + 1
                    else:
                        footprint_pattern = part.footprint_pattern
                        if fnmatch.fnmatch(footprint, footprint_pattern):
                            # The footprints match:
                            pose_part = \
                              PosePart(project, part, reference, footprint)
                            project.pose_parts_append(pose_part)
                            part.pose_parts.append(pose_part)
                        else:
                            print(("File '{0}',  line {1}: {2}:{3} Footprint" +
                                   "'{4}' does not match database '{5}'").format(
                                   cmp_file_name, line_number,
                                   reference, part_name, footprint,
                                   footprint_pattern))
                            errors = errors + 1
                elif (line == "\n" or line.startswith("TimeStamp") or
                      line.startswith("EndListe") or line.startswith("Cmp-Mod V01")):
                    # Ignore these lines:
                    line = line
                else:
                    # Unrecognized {line}:
                    print("'{0}', line {1}: Unrecognized line '{2}'".
                          format(cmp_file_name, line_number, line))
                    errors = errors + 1
        else:
            print("Net file '{0}' name does not have a recognized suffix".format(net_file_name))

        # Wrap up any requested *tracing* and return *errors*:
        if tracing is not None:
            print(f"{tracing}<=Project.new_file_read()=>[...]")
        return errors

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
            pose_parts.append(pose_part)
        return pose_part

    # Project.find():
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

    # Project.assembly_summary_write():
    def assembly_summary_write(self, final_choice_parts, order):
        """ Write out an assembly summary .csv file for the *Project* object (i.e. *self*)
            using *final_choice_parts*.
        """

        # Verify argument types:
        assert isinstance(final_choice_parts, list)
        assert isinstance(order, Order)

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

    # Project.positions_process():
    def positions_process(self, database):
        """ Reorigin the the contents of the positions table.
        """

        project = self
        positions_file_name = project.positions_file_name
        positions_table = PositionsTable(positions_file_name, database)
        positions_table.reorigin("FD1")
        positions_table.footprints_rotate(database)


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
        #base_name_short_footprint = name.split(';')
        #if len(base_name_short_footprint) == 2:
        #    base_name = base_name_short_footprint[0]
        #    short_footprint = base_name_short_footprint[1]
        #
        #    # Load up *self*:
        #    project_part.name = name
        #    project_part.base_name = base_name
        #    project_part.short_footprint = short_footprint
        #    project_part.kicad_footprint = kicad_footprint
        #    project_part.pose_parts = []
        #else:
        
        # Stuff values into *project_part* (i.e. *self*):
        project_part = self
        project_part.name = name
        project_part.projects = projects
        project_part.pose_parts = []       # List[PosePart]
        project_part.pose_parts_table = {} # Dict[reference, PosePart]

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

        #assert isinstance(kicad_footprint, str)
        #assert isinstance(location, str)
        #assert isinstance(description, str)
        #assert isinstance(rotation, float) or rotation is None
        #assert isinstance(pick_dx, float)
        #assert isinstance(pick_dy, float)
        #assert isinstance(feeder_name, str) or feeder_name is None
        #assert isinstance(part_height, float) or part_height is None

        # Use *choice_part* instead of *self*:
        choice_part = self

        # A *chice_part* (i.e. *self*) can have multiple *Project*'s associated with it.
        # Thus, we need to compute the *union_projects* of all *Project*'s associated
        # with *project parts*:
        projects_table = {}
        for project_part in project_parts:
            projects = project_part.projects
            for project in projects:
                net_file_name = project.net_file_name
                projects_table[net_file_name] = project
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

        #choice_part.description = description
        #choice_part.feeder_name = feeder_name
        #choice_part.location = location
        #choice_part.part_height = part_height
        #choice_part.rotation = rotation
        #choice_part.pick_dx = pick_dx
        #choice_part.pick_dy = pick_dy

    # ChoicePart.__format__():
    def __format__(self, format):
        """ *ChoicePart*: Return the *ChoicePart object (i.e. *self* as a string formatted by
            *format*.
        """

        if format == "s":
            result = "{0};{1}".format(self.base_name, self.short_footprint)
        else:
            result = "{0};{1}".format(self.base_name, self.short_footprint)
        return result

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

        # tracing = False
        # tracing = manufacturer_name == "Pololu"

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
    def select(self, excluded_vendor_names, announce=False):
        """ *ChoicePart*: Select and return the best priced *ActualPart*
            for the *ChoicePart* (i.e. *self*) excluding any vendors
            in the *excluded_vendor_names* dictionary.
        """

        # This lovely piece of code basically brute forces the decision
        # process of figuring out which *vendor_part* to select and the
        # number of parts to order.  We iterate over each *actual_part*,
        # *vendor_part* and *price_break* and compute the *total_cost*
        # and *order_quanity* for that combination.  We store this into
        # a 5-tuple called *quint* and build of the list of *quints*.
        # When we are done, we sort *quints* and select the first one
        # off the head of the list.

        tracing = False
        # tracing = self.name == "S18V20F6;S18V20Fx"
        if tracing:
            print("=>ChoicePart.select()")
            print(" Choice_part:{0}".format(self.name))

        quints = []
        required_quantity = self.count_get()
        actual_parts = self.actual_parts
        for actual_part_index in range(len(actual_parts)):
            actual_part = actual_parts[actual_part_index]
            if tracing:
                print(" Manufacturer: {0} {1}".format(
                      actual_part.manufacturer_name, actual_part.manufacturer_part_name))
            vendor_parts = actual_part.vendor_parts
            for vendor_part_index, vendor_part in enumerate(vendor_parts):
                if tracing:
                    print("  Vendor: {0} {1}".
                          format(vendor_part.vendor_name, vendor_part.vendor_part_name))
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
                    if tracing:
                        print("   price={0:.2f} quant={1} order_quantity={2} total_cost={3:.2f}".
                              format(price, quantity, order_quantity, total_cost))

                    # Assemble the *quint* and append to *quints* if there
                    # enough parts available:
                    is_excluded = vendor_part.vendor_name in excluded_vendor_names
                    if tracing:
                        print("   Quantity Available: {0} Is excluded: {1}".
                              format(vendor_part.quantity_available, is_excluded))
                    if not is_excluded and vendor_part.quantity_available >= order_quantity:
                        assert price_break_index < len(price_breaks)
                        quint = (total_cost, order_quantity,
                                 actual_part_index, vendor_part_index,
                                 price_break_index, len(price_breaks))
                        quints.append(quint)
                        if tracing:
                            print("    quint={0}".format(quint))

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

        if tracing:
            print("<=ChoicePart.select()\n")
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
    def vendor_parts_refresh(self, new_actual_parts, order, tracing=None):
        # Verify argument types:
        assert isinstance(new_actual_parts, list)
        assert isinstance(order, Order)
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested_tracing:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>ChoicePart.vendor_parts_refresh([...], *)")

        # Grab some values from *choice_part* (i.e. *self*):
        choice_part = self
        choice_part_name = choice_part.name

        # Grab some values from *order*:
        vendor_searches_root = order.vendor_searches_root

        # Construct the file path for the `.xml` file associated *choice_part*:
        xml_base_name = Encode.to_file_name(choice_part_name + ".xml")
        xml_full_name = os.path.join(vendor_searches_root, xml_base_name)
        if tracing is not None:
            print(f"{tracing}xml_full_name='{xml_full_name}'")

        # Open *xml_full_name* update *choice_part* from its contents:
        xml_save_required = False
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
                if tracing is not None:
                    print(f"{tracing}Read in '{xml_full_name}'")

                # Sweep through *previous_actual_parts* and enter them into
                # *previous_actual_parts_table*:
                previous_actual_parts = previous_choice_part.actual_parts
                for previous_actual_part in previous_actual_parts:
                    previous_actual_part_key = previous_actual_part.key
                    previous_actual_parts_table[previous_actual_part_key] = previous_actual_part
        else:
             xml_save_required = True       

        # Now sweep through *new_actual_parts* and refresh any missing or out of date vendor parts
        # from the contents of *previous_actual_parts_table*:
        stale = order.stale
        now = int(time.time())
        for new_actual_part in new_actual_parts:
            actual_part_key = new_actual_part.key
            if actual_part_key in previous_actual_parts_table:
                # We have a *previous_actual_part* that matches *new_actual_part*.
                # Now we see if can simply copy *previous_vendor_parts* over or
                # whether we must trigger a vendor parts lookup:
                previous_actual_part = previous_actual_parts_table[actual_part_key]
                previous_vendor_parts = previous_actual_part.vendor_parts

                # Compute the *minimum_time_stamp* across all *previous_vendor_parts*:
                minimum_timestamp = now
                for previous_vendor_part in previous_vendor_parts:
                    minimum_timestamp = min(minimum_timestamp,  previous_vendor_part.timestamp)

                # If the *minimum_time_stamp* is too stale, force a refresh:
                if minimum_timestamp + stale < now:
                    new_actual_part.findchips_scrape(tracing=next_tracing)
                    xml_save_required
                else:
                    new_actual_part.vendor_parts = previous_vendor_parts
            else:
                # There is no matching *previous_actual_part*, so we need to go
                # find any appropriate vendor parts:
                new_actual_part.findchips_scrape(tracing=next_tracing)
                xml_save_required = True

        # Load *new_actual_parts* into *choice_part*:
        choice_part.actual_parts = new_actual_parts

        # Write *choice_part* out to the file named *xml_full_name* if a *scrape_occurred*:
        if xml_save_required:
            if tracing is not None:
                print(f"{tracing}Writing out '{xml_full_name}'")
            xml_lines = []
            xml_lines.append('<?xml version="1.0"?>')
            choice_part.xml_lines_append(xml_lines, "")
            xml_lines.append("")
            xml_text = "\n".join(xml_lines)
            with open(xml_full_name, "w") as xml_write_file:
                xml_write_file.write(xml_text)

        # Wrap up any requested_tracing:
        if tracing is not None:
            print(f"{tracing}<=ChoicePart.vendor_parts_refresh([...], *)")

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
    def __init__(self, tables, collection_directories, searches_root, order, tracing=None):
        # Verify argument types:
        assert isinstance(tables, list)
        assert isinstance(collection_directories, list)
        assert isinstance(searches_root, str)
        assert isinstance(order, Order)
        for table in tables:
            assert isinstance(table, Table)

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>TablesEditor.__init__(...)")

        # Create the *application* first:
        application = QApplication(sys.argv)

        # Obtain the UI file:
        module_file_name = __file__
        if tracing is not None:
            print(f"module_file_name='{module_file_name}'")
        module_directory = os.path.split(module_file_name)[0]
        if tracing is not None:
            print(f"module_directory='{module_directory}'")        
        ui_file_name = os.path.join(module_directory, "bom_manager.ui")
        if tracing is not None:
            print(f"ui_file_name='{ui_file_name}'")        

        # Create *main_window* from thie `.ui` file:
        #ui_qfile = QFile("bom_manager.ui")
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
            print(f"Using '{searches_root}' directory to store searches into.")
        else:
            # Create directory *searches_path*:
            print(f"Attempting to create directory '{searches_root}' to store searches into...")
            try:
                os.mkdir(searches_root)
            except PermissionError:
                print(f"...failed to create `{searches_root}' directory.")
                searches_root = os.path.join(working_directory_path, "searches")
                print(f"Using '{searches_root}' for searches directory "
                      "(which is a really bad idea!!!!)")
        assert os.path.isdir(searches_root)

        # Create *collections_root*:
        #collections_root = os.path.join(working_directory_path, "collections")
        #assert os.path.isdir(collections_root)

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
        tables_editor.original_tables = copy.deepcopy(tables)
        tables_editor.re_table = TablesEditor.re_table_get()
        tables_editor.searches_root = searches_root
        tables_editor.searches = list()
        tables_editor.xsearches = None
        tables_editor.tab_unload = None
        tables_editor.tables = tables
        tables_editor.trace_signals = tracing is not None

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
          tracing=next_tracing)
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
          tracing=next_tracing)
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
          tracing=next_tracing)
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
          tracing=next_tracing)
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
        tree_model = TreeModel(tracing=next_tracing)
        tables_editor.model = tree_model

        # Create the *collections* and stuff into *tables_editor*:
        collections = Collections("Collections", collection_directories, searches_root, tree_model,
                                  tracing=next_tracing)
        tables_editor.collections = collections

        # Now stuff *collections* into *tree_model*:
        tree_model.collections_set(collections)

        # Now that both *collections* and *tree_mode* refer to one another we can safely
        # call *partial_load*():
        collections.partial_load(tracing=next_tracing)

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

        # tables_editor.table_setup(tracing=next_tracing)

        # Read in `searches.xml` if it exists:
        # tables_editor.searches_file_load(os.path.join(order_root, "searches.xml"),
        #                                  tracing=next_tracing)

        # Update the entire user interface:
        tables_editor.update(tracing=next_tracing)

        tables_editor.in_signal = False

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=TablesEditor.__init__(...)\n")

    # TablesEditor.comment_text_set()
    def comment_text_set(self, new_text, tracing=None):
        # Verify argument types:
        assert isinstance(new_text, str)
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested tracing:
        tables_editor = self
        if tracing is not None:
            print("{0}=>TablesEditor.comment_text_set(...)".format(tracing))

        # Carefully set thet text:
        main_window = tables_editor.main_window
        comment_text = main_window.parameters_comment_text
        comment_text.setPlainText(new_text)

        # Wrap up any requested tracing:
        if tracing is not None:
            print("{0}<=TablesEditor.comment_text_set(...)".format(tracing))

    # TablesEditor.collections_delete_changed():
    def collections_delete_clicked(self):
        # Perform any requested signal *tracing* for *tables_editor* (i.e. *self*):
        tables_editor = self
        tracing = "" if tables_editor.trace_signals else None
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>Tables_Editor.collections_delete_clicked()")

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
                if tracing is not None:
                    print(f"{tracing}curent_search_name='{current_search_name}'")

                # Grab the parent *table* from *current_search* and force it to be fixed up:
                table = current_search.parent
                assert isinstance(table, Table)
                table.sort(tracing=next_tracing)

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
                    if tracing is not None:
                        print(f"{tracing}Here 1")
                    tree_model.delete(search_model_index, tracing=next_tracing)
                    collection = current_search.collection
                    searches_table = collection.searches_table
                    if current_search_name in searches_table:
                        del searches_table[current_search_name]

                    # If a *parent_search* as found, set it up as the next selected one:
                    if tracing is not None:
                        print(f"{tracing}Here 2")
                    if search_parent is None:
                        tables_editor.current_model_index = None
                        tables_editor.current_search = None
                    else:
                        if tracing is not None:
                            print(f"Here 3")
                        search_parent_name = search_parent.name
                        if tracing is not None:
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
                    if tracing is not None:
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
        tables_editor.update(tracing=next_tracing)

        # Wrap up any requested signal tracing:
        if tracing is not None:
            print(f"{tracing}<=Tables_Editor.collections_delete_clicked()\n")

    # TablesEditor.collections_line_changed():
    def collections_line_changed(self, text):
        # Verify argument types:
        assert isinstance(text, str)

        # Perform any requested signal tracing:
        tables_editor = self
        tracing = "" if tables_editor.trace_signals else None
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>Tables_Editor.collections_line_changed('{text}')")

        # Update the collections tab:
        tables_editor.update(tracing=next_tracing)

        # Wrap up any requested signal tracing:
        if tracing is not None:
            print(f"{tracing}<=Tables_Editor.collections_line_changed('{text}')\n")

    # TablesEditor.collections_new_clicked():
    def collections_new_clicked(self):
        # Perform any requested *tracing*:
        tables_editor = self
        tracing = "" if tables_editor.trace_signals else None
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>TablesEditor.collections_new_clicked()")

        # Grab some values from *tables_editor* (i.e. *self*):
        current_search = tables_editor.current_search

        # Make sure *current_search* exists (this button click should be disabled if not available):
        assert current_search is not None

        #
        #clip_board = pyperclip.paste()
        #selection = os.popen("xsel").read()
        application = tables_editor.application
        application_clipboard = application.clipboard()
        selection = application_clipboard.text(QClipboard.Selection)
        clipboard = application_clipboard.text(QClipboard.Clipboard)

        url = None
        if selection.startswith("http"):
            url = selection
        elif clipboard.startswith("http"):
            url = clipboard
        if tracing is not None:
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
            new_search = Search(new_search_name, table, current_search, url, tracing=next_tracing)
            assert table.has_child(new_search)

            # if tracing is not None:
            #    print("{0}1:len(searches)={1}".format(tracing, len(searches)))
            table.sort(tracing=next_tracing)
            new_search.file_save(tracing=next_tracing)

            model_index = tables_editor.current_model_index
            if model_index is not None:
                parent_model_index = model_index.parent()
                tree_model = model_index.model()
                tree_model.children_update(parent_model_index, tracing=next_tracing)

            # model = tables_editor.model
            # model.insertNodes(0, [ new_search ], parent_model_index)
            # if tracing is not None:
            #    print("{0}2:len(searches)={1}".format(tracing, len(searches)))

            tables_editor.update(tracing=next_tracing)

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=TablesEditor.collections_new_clicked()\n")

    # TablesEditor.collections_check_clicked():
    def collections_check_clicked(self):
        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self
        tracing = "" if tables_editor.trace_signals else None
        tracing = None
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>TablesEditor.collections_check_clicked()")

        # Delegate checking to *order* object:
        collections = tables_editor.collections
        order = tables_editor.order
        order.check(collections, tracing=next_tracing)

        # Wrap any requested by *tracing*:
        if tracing is not None:
            print(f"{tracing}<=TablesEditor.collections_check_clicked()\n")

    # TablesEditor.collections_process_clicked():
    def collections_process_clicked(self):
        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self
        tracing = "" if tables_editor.trace_signals else None
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>TablesEditor.collections_process_clicked()")

        # Grab some values from *tables_editor*:
        collections = tables_editor.collections
        order = tables_editor.order

        # Now process *order* using *collections*:
        order.process(collections, tracing=next_tracing)

        # Wrap any requested by *tracing*:
        if tracing is not None:
            print(f"{tracing}<=TablesEditor.collections_process_clicked()\n")

    # TablesEditor.collections_tree_clicked():
    def collections_tree_clicked(self, model_index):
        # Verify argument types:
        assert isinstance(model_index, QModelIndex)

        # Perform any requested signal *tracing* for *tables_editor* (i.e. *self*):
        tables_editor = self
        tracing = "" if tables_editor.trace_signals else None
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>TablesEditor.collections_tree_clicked()")

        # Grab the *node* associated with *model_index*:
        tables_editor.current_model_index = model_index
        row = model_index.row()
        column = model_index.column()
        # parent_model_index = model_index.parent()
        model = model_index.model()
        node = model.getNode(model_index)
        assert isinstance(node, Node)
        node.clicked(tables_editor, model_index, tracing=next_tracing)

        if isinstance(node, Search):
            main_window = tables_editor.main_window
            collections_line = main_window.collections_line
            collections_line.setText(node.name)

        tables_editor.update(tracing=next_tracing)

        if tracing is not None:
            print(f"{tracing}row={row} column={column}")

        # Wrap up any requested signal tracing:
        if tracing is not None:
            print(f"{tracing}<=TablesEditor.collections_tree_clicked()\n")

    # TablesEditor.collections_update():
    def collections_update(self, tracing=None):
        # Perform argument testing:
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        # next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>TablesEditor.collections_update()")

        # Grab some widgets from *tables_editor*:
        tables_editor = self
        main_window = tables_editor.main_window
        collections_delete = main_window.collections_delete
        collections_line = main_window.collections_line
        collections_new = main_window.collections_new

        # Grab the *current_search* object:
        current_search = tables_editor.current_search
        if tracing is not None:
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
        if tracing is not None:
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
        if tracing is not None:
            print(f"{tracing}delete_button_enable={delete_button_enable} why='{delete_button_why}'")

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=TablesEditor.collections_update()")

    # TablesEditor.current_enumeration_set()
    def current_enumeration_set(self, enumeration, tracing=None):
        # Verify argument types:
        assert isinstance(enumeration, Enumeration) or enumeration is None, \
          "{0}".format(enumeration)
        assert isinstance(tracing, str) or tracing is None

        # next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{0}=>TablesEditor.current_enumeration_set('{1}')".
                  format(tracing, "None" if enumeration is None else enumeration.name))

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

        if tracing is not None:
            print("{0}<=TablesEditor.current_enumeration_set('{1}')".
                  format(tracing, "None" if enumeration is None else enumeration.name))

    # TablesEditor.current_parameter_set()
    def current_parameter_set(self, parameter, tracing=None):
        # Verify argument types:
        assert isinstance(parameter, Parameter) or parameter is None
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        if tracing is not None:
            name = "None" if parameter is None else parameter.name
            print("{0}=>TablesEditor.current_parameter_set(*, '{1}')".format(tracing, name))

        # Set the *current_parameter* in *tables_editor*:
        tables_editor = self
        tables_editor.current_parameter = parameter

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print("{0}<=TablesEditor.current_parameter_set(*, '{1}')".format(tracing, name))

    # TablesEditor.current_search_set()
    def current_search_set(self, new_current_search, tracing=None):
        # Verify argument types:
        assert isinstance(new_current_search, Search) or new_current_search is None, \
          print(new_current_search)
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        if tracing is not None:
            print("{0}=>TablesEditor.current_search_set('{1}')".format(tracing,
                  "None" if new_current_search is None else new_current_search.name))

        # Make sure *new_current_search* is in *searches*:
        tables_editor = self
        searches = tables_editor.searches
        if new_current_search is not None:
            for search_index, search in enumerate(searches):
                assert isinstance(search, Search)
                if tracing is not None:
                    print("{0}Search[{1}]: '{2}'".format(tracing, search_index, search.name))
                if search is new_current_search:
                    break
            else:
                assert False
        tables_editor.current_search = new_current_search

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print("{0}<=TablesEditor.current_table_set('{1}')".format(
                  tracing, "None" if new_current_search is None else new_current_search.name))

    # TablesEditor.current_table_set()
    def current_table_set(self, new_current_table, tracing=None):
        # Verify argument types:
        assert isinstance(new_current_table, Table) or new_current_table is None
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        if tracing is not None:
            print("{0}=>TablesEditor.current_table_set('{1}')".
                  format(tracing, "None" if new_current_table is None else new_current_table.name))

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

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print("{0}<=TablesEditor.current_table_set('{1}')".
                  format(tracing, "None" if new_current_table is None else new_current_table.name))

    # TablesEditor.current_update()
    def current_update(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self
        # next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{0}=>TablesEditor.current_update()".format(tracing))

        # Make sure *current_table* is valid (or *None*):
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
        if tracing is not None:
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
        if tracing is not None:
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

        if tracing is not None:
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
        if tracing is not None:
            print("{0}current_search='{1}'".
                  format(tracing, "None" if current_search is None else current_search.name))

        # Wrap up any requested tracing:
        if tracing is not None:
            print("{0}<=TablesEditor.current_update()".format(tracing))

    # TablesEditor.data_update()
    def data_update(self, tracing=None):
        # Verify artument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{0}=>TablesEditor.data_update()".format(tracing))

        # Make sure that the *current_table*, *current_parameter*, and *current_enumeration*
        # in *tables_editor* are valid:
        tables_editor.current_update(tracing=next_tracing)

        # Wrap up any requested tracing:
        if tracing is not None:
            print("{0}<=TablesEditor.data_update()".format(tracing))

    # TablesEditor.enumeration_changed()
    def enumeration_changed(self):
        assert False

    # TablesEditor.enumeration_comment_get()
    def enumeration_comment_get(self, enumeration, tracing=None):
        # Verify argument types:
        assert isinstance(enumeration, Enumeration) or enumeration is None
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        # tables_editor = self
        # next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            name = "None" if tracing is None else enumeration.name
            print("{0}=>enumeration_comment_get('{1}')".format(tracing, name))

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

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print("{0}<=table_enumeration_get('{1}')".format(tracing, name))
        return text, position

    # TablesEditor.enumeration_comment_set()
    def enumeration_comment_set(self, enumeration, text, position, tracing=None):
        # Verify argument types:
        assert isinstance(enumeration, Enumeration) or enumeration is None
        assert isinstance(text, str)
        assert isinstance(position, int)
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        # tables_editor = self
        # next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            name = "None" if tracing is None else enumeration.name
            print("{0}=>enumeration_comment_set('{1}')".format(tracing, name))

        # Stuff *text* into *enumeration*:
        if enumeration is not None:
            comments = enumeration.comments
            assert len(comments) >= 1
            comment = comments[0]
            assert isinstance(comment, EnumerationComment)
            comment.lines = text.split('\n')
            comment.position = position

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print("{0}<=enumeration_comment_set('{1}')".format(tracing, name))

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
    def enumerations_update(self, enumeration=None, tracing=None):
        # Verify argument types:
        assert isinstance(enumeration, Enumeration) or enumeration is None
        assert isinstance(tracing, str) or tracing is None

        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{0}=>TablesEditor.enumerations_update()".format(tracing))

        # Make sure that the *current_table*, *current_parameter*, and *current_enumeration*
        # in *tables_editor* are valid:
        tables_editor.current_update(tracing=next_tracing)

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
                if tracing is not None:
                    print("{0}[{1}]'{2}'".format(tracing, index, enumeration.name))
                # print("[{0}]'{1}'".format(index, enumeration_name))
                combo.addItem(enumeration_name, tracing=next_tracing)

        # Update the *enumerations_combo_edit*:
        tables_editor.enumerations_combo_edit.gui_update(tracing=next_tracing)

        # Wrap-up and requested tracing:
        if tracing is not None:
            print("{0}<=TablesEditor.enumerations_update()".format(tracing))

    # TablesEditor.filters_cell_clicked():
    def filters_cell_clicked(self, row, column):
        # Verify argument types:
        assert isinstance(row, int)
        assert isinstance(column, int)

        # Perform any requested signal tracing:
        tables_editor = self
        trace_signals = tables_editor.trace_signals
        next_tracing = " " if trace_signals else None
        if trace_signals:
            print("=>TablesEditor.filters_cell_clicked()")

        # Just update the filters tab:
        tables_editor.filters_update(tracing=next_tracing)

        # Wrap up any requested signal tracing:
        if trace_signals:
            print("<=TablesEditor.filters_cell_clicked()\n")

    # TablesEditor.filters_down_button_clicked():
    def filters_down_button_clicked(self):
        tables_editor = self
        trace_signals = tables_editor.trace_signals
        next_tracing = " " if trace_signals else None
        if trace_signals:
            print("=>TablesEditor.filters_down_button_clicked()")

        # Note: The code here is very similar to the code in
        # *TablesEditor.filters_down_button_clicked*:

        # Grab some values from *tables_editor*:
        tables_editor.current_update(tracing=next_tracing)
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
                    tables_editor.filters_unload(tracing=next_tracing)

                    # Swap *filter_at* with *filter_before*:
                    filter_after = filters[current_row_index + 1]
                    filter_at = filters[current_row_index]
                    filters[current_row_index + 1] = filter_at
                    filters[current_row_index] = filter_after

                    # Force the *filters_table* to be updated:
                    tables_editor.filters_update(tracing=next_tracing)
                    filters_table.setCurrentCell(current_row_index + 1, 0,
                                                 QItemSelectionModel.SelectCurrent)

        # Wrap down any requested signal tracing:
        if trace_signals:
            print("<=TablesEditor.filters_down_button_clicked()\n")

    # TablesEditor.filters_unload()
    def filters_unload(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        # next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{0}=>TablesEditor.filters_unload()".format(tracing))

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

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print("{0}<=TablesEditor.filters_unload()".format(tracing))

    # TablesEditor.filters_up_button_clicked():
    def filters_up_button_clicked(self):
        # Perform any requested signal tracing:
        tables_editor = self
        trace_signals = tables_editor.trace_signals
        next_tracing = " " if trace_signals else None
        if trace_signals:
            print("=>TablesEditor.filters_up_button_clicked()")

        # Note: The code here is very similar to the code in
        # *TablesEditor.filters_down_button_clicked*:

        # Grab some values from *tables_editor*:
        tables_editor.current_update(tracing=next_tracing)
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
                    tables_editor.filters_unload(tracing=next_tracing)

                    # Swap *filter_at* with *filter_before*:
                    filter_before = filters[current_row_index - 1]
                    filter_at = filters[current_row_index]
                    filters[current_row_index - 1] = filter_at
                    filters[current_row_index] = filter_before

                    # Force the *filters_table* to be updated:
                    tables_editor.filters_update(tracing=next_tracing)
                    filters_table.setCurrentCell(current_row_index - 1, 0,
                                                 QItemSelectionModel.SelectCurrent)

            # if trace_signals:
            #    print(" filters_after={0}".format([filter.parameter.name for filter in filters]))

        # Wrap up any requested signal tracing:
        if trace_signals:
            print("<=TablesEditor.filters_up_button_clicked()\n")

    # TablesEditor.filters_update()
    def filters_update(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{0}=>TablesEditor.filters_update()".format(tracing))

        # Empty out *filters_table* widget:
        tables_editor = self
        main_window = tables_editor.main_window
        filters_table = main_window.filters_table
        filters_table.clearContents()
        filters_table.setColumnCount(4)
        filters_table.setHorizontalHeaderLabels(["Parameter", "Type", "Use", "Select"])

        # Only fill in *filters_table* if there is a valid *current_search*:
        tables_editor.current_update(tracing=next_tracing)
        current_search = tables_editor.current_search
        if current_search is None:
            # No *current_search* so there is nothing to show:
            filters_table.setRowCount(0)
        else:
            # Let's update the *filters* and load them into the *filters_table* widget:
            # current_search.filters_update(tables_editor, tracing=next_tracing)
            filters = current_search.filters
            filters_size = len(filters)
            filters_table.setRowCount(filters_size)
            if tracing is not None:
                print("{0}current_search='{1}' filters_size={2}".
                      format(tracing, current_search.name, filters_size))

            # Fill in one *filter* at a time:
            for filter_index, filter in enumerate(filters):
                # Create the header label in the first column:
                parameter = filter.parameter
                # if tracing is not None:
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
                # if tracing is not None:
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

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print("{0}<=TablesEditor.filters_update()".format(tracing))

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
            # next_tracing = " " if trace_signals else None
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
    def find_update(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{0}=>TablesEditor.find_update()".format(tracing))

        tables_editor = self
        main_window = tables_editor.main_window
        find_tabs = main_window.find_tabs
        find_tabs_index = find_tabs.currentIndex()
        if find_tabs_index == 0:
            tables_editor.searches_update(tracing=next_tracing)
        elif find_tabs_index == 1:
            tables_editor.filters_update(tracing=next_tracing)
        elif find_tabs_index == 2:
            tables_editor.results_update(tracing=next_tracing)
        else:
            assert False

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print("{0}<=TablesEditor.find_update()".format(tracing))

    # TablesEditor.import_bind_clicked():
    def import_bind_button_clicked(self):
        # Perform any requested signal tracing:
        tables_editor = self
        trace_signals = tables_editor.trace_signals
        next_tracing = "" if trace_signals else None
        if trace_signals:
            print("=>TablesEditor.import_bind_button_clicked()")

        # Update *current_table* an *parameters* from *tables_editor*:
        tables_editor.current_update(tracing=next_tracing)
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

            tables_editor.update(tracing=next_tracing)

        # Wrap up any requested signal tracing:
        if trace_signals:
            print("<=TablesEditor.import_bind_button_clicked()")

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
            # next_tracing = "" if trace_signals else None
            if trace_signals:
                print("=>TablesEditor.import_csv_file_line_changed('{0}')".format(text))

            # Make sure *current_table* is up-to-date:
            # tables_editor.current_update(tracing=next_tracing)
            # current_table = tables_editor.current_table

            # Read *csv_file_name* out of the *import_csv_file_line* widget and stuff into *table*:
            # if current_table is not None:
            #     main_window = tables_editor.main_window
            #     import_csv_file_line = main_window.import_csv_file_line
            #     xxx = import_csv_file_line.text()
            #     print("xxx='{0}' text='{1}'".format(xxx, text))
            #    current_table.csv_file_name = csv_file_name

            # Force an update:
            # tables_editor.update(tracing=next_tracing)

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
            next_tracing = " " if trace_signals else None
            if trace_signals:
                print("=>TablesEditor.parameter_csv_changed('{0}')".format(new_csv))

            # Stuff *new_csv* into *current_parameter* (if possible):
            tables_editor.current_parameter()
            current_parameter = tables_editor.current_parameter
            if current_parameter is not None:
                current_parameter.csv = new_csv

            tables_editor.update(tracing=next_tracing)
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
    def parameter_comment_get(self, parameter, tracing=None):
        # Verify argument types:
        assert isinstance(parameter, Parameter) or parameter is None
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        text = ""
        # tables_editor = self
        # next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            name = "None" if parameter is None else parameter.name
            print("{0}=>parameter_comment_get('{1}')".format(tracing, name))

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

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print("{0}<=table_parameter_get('{1}')=>(*, {2})".format(tracing, name, position))
        return text, position

    # TablesEditor.parameter_comment_set():
    def parameter_comment_set(self, parameter, text, position, tracing=None):
        # Verify argument types:
        assert isinstance(parameter, Parameter) or parameter is None
        assert isinstance(text, str)
        assert isinstance(position, int)
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        tables_editor = self
        # next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            name = "None" if parameter is None else parameter.name
            print("{0}=>parameter_comment_set('{1}', *, {2})".format(tracing, name, position))

        # Stuff *text* into *parameter*:
        if parameter is not None:
            comments = parameter.comments
            assert len(comments) >= 1
            comment = comments[0]
            assert isinstance(comment, ParameterComment)
            comment.lines = text.split('\n')
            comment.position = position

        if tracing is not None:
            main_window = tables_editor.main_window
            comment_text = main_window.parameters_comment_text
            cursor = comment_text.textCursor()
            actual_position = cursor.position()
            print("{0}position={1}".format(tracing, actual_position))

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print("{0}<=parameter_comment_set('{1}', *, {2}')".format(tracing, name, position))

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
            next_tracing = " " if trace_signals else None
            if trace_signals:
                print("=>TablesEditor.parameter_long_changed('{0}')".format(new_long_heading))

            # Update the correct *parameter_comment* with *new_long_heading*:
            current_parameter = tables_editor.current_parameter
            assert isinstance(current_parameter, Parameter)
            parameter_comments = current_parameter.comments
            assert len(parameter_comments) >= 1
            parameter_comment = parameter_comments[0]
            assert isinstance(parameter_comment, ParameterComment)
            parameter_comment.long_heading = new_long_heading

            # Update the user interface:
            tables_editor.update(tracing=next_tracing)

            # Wrap up
            if trace_signals:
                print("<=TablesEditor.parameter_long_changed('{0}')\n".format(new_long_heading))
            tables_editor.in_signal = False

    # TablesEditor.parameters_edit_update():
    def parameters_edit_update(self, parameter=None, tracing=None):
        # Verify argument types:
        assert isinstance(parameter, Parameter) or parameter is None
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested tracing from *tables_editor* (i.e. *self*):
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{0}=>TablesEditor.parameters_edit_update('{1}')".
                  format(tracing, "None" if parameter is None else parameter.name))

        # Make sure that the *current_table*, *current_parameter*, and *current_enumeration*
        # in *tables_editor* are valid:
        tables_editor = self

        tables_editor.current_update(tracing=next_tracing)
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
        if tracing is not None:
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
            if tracing is not None:
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
            tables_editor.parameters_long_set(comment.long_heading, tracing=next_tracing)
            tables_editor.parameters_short_set(comment.short_heading, tracing=next_tracing)

            previous_csv = csv_line.text()
            if csv != previous_csv:
                csv_line.setText(csv)

            # Deal with comment text edit area:
            tables_editor.current_comment = comment
            lines = comment.lines
            text = '\n'.join(lines)

            tables_editor.comment_text_set(text, tracing=next_tracing)

        # Changing the *parameter* can change the enumeration combo box, so update it as well:
        # tables_editor.enumeration_update()

        # Update the *tables_combo_edit*:
        tables_editor.parameters_combo_edit.gui_update(tracing=next_tracing)

        if tracing is not None:
            print("{0}<=TablesEditor.parameters_edit_update('{1}')".
                  format(tracing, "None" if parameter is None else parameter.name))

    # TablesEditor.parameters_long_set():
    def parameters_long_set(self, new_long_heading, tracing=None):
        # Verify argument types:
        assert isinstance(new_long_heading, str)
        assert isinstance(tracing, str) or tracing is None

        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self
        # next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{0}=>TablesEditor.parameters_long_set('{1}')".format(tracing, new_long_heading))

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

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print("{0}<=TablesEditor.parameters_long_set('{1}')".format(tracing, new_long_heading))

    # TablesEditor.parameter_new():
    def parameter_new(self, name, tracing=None):
        # Verify argument types:
        assert isinstance(name, str)
        assert isinstance(tracing, str) or tracing is None

        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        # tables_editor = self
        if tracing is not None:
            print("{0}=>TablesEditor.parmeter_new('{1}')".format(tracing, name))

        # Create *new_parameter* named *name*:
        comments = [ParameterComment(language="EN", long_heading=name, lines=list())]
        new_parameter = Parameter(name=name, type="boolean", csv="",
                                  csv_index=-1, comments=comments)

        # Wrap up any requested tracing and return *new_parameter*:
        if tracing is not None:
            print("{0}<=TablesEditor.parmeter_new('{1}')".format(tracing, name))
        return new_parameter

    # TablesEditor.parameter_optional_clicked():
    def parameter_optional_clicked(self):
        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self
        trace_level = tables_editor.trace_level
        if trace_level >= 1:
            print("=>TablesEditor.parameter_optional_clicked()")

        current_parameter = tables_editor.current_parameter
        if current_parameter is not None:
            main_window = tables_editor.main_window
            parameter_optional_check = main_window.parameter_optional_check
            optional = parameter_optional_check.isChecked()
            current_parameter.optional = optional

        # Wrap up any requested *tracing*:
        if trace_level >= 1:
            print("=>TablesEditor.parameter_optional_clicked()\n")

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
            next_tracing = " " if trace_signals else None
            if trace_signals:
                print("=>TablesEditor.parameter_short_changed('{0}')".format(new_short_heading))

            # Update *current_parameter* to have *new_short_heading*:
            current_parameter = tables_editor.current_parameter
            assert isinstance(current_parameter, Parameter)
            parameter_comments = current_parameter.comments
            assert len(parameter_comments) >= 1
            parameter_comment = parameter_comments[0]
            assert isinstance(parameter_comment, ParameterComment)
            parameter_comment.short_heading = new_short_heading

            # Update the user interface:
            tables_editor.update(tracing=next_tracing)

            # Wrap up any requested tracing:
            if trace_signals:
                print("<=TablesEditor.parameter_short_changed('{0}')\n".format(new_short_heading))
            tables_editor.in_signal = False

    # TablesEditor.parameters_short_set():
    def parameters_short_set(self, new_short_heading, tracing=None):
        # Verify argument types:
        assert isinstance(new_short_heading, str) or new_short_heading is None
        assert isinstance(tracing, str) or tracing is None

        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self
        if tracing is not None:
            print("{0}=>TablesEditor.parameters_short_set('{1}')".
                  format(tracing, new_short_heading))

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

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print("{0}<=TablesEditor.parameters_short_set('{1}')".
                  format(tracing, new_short_heading))

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
    def parameters_update(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{0}=>TabledsEditor.parameters_update".format(tracing))

            # Make sure *current_table* is up to date:
            tables_editor = self
            tables_editor.current_update()
            current_table = tables_editor.current_table

            # The [import] tab does not do anything if there is no *current_table*:
            if current_table is not None:
                # Do some *tracing* if requested:
                if tracing is not None:
                    print("{0}current_table='{1}'".format(tracing, current_table.name))

                # Grab some widgets from *tables_editor*:
                main_window = tables_editor.main_window
                # import_bind = main_window.import_bind
                # import_csv_file_line = main_window.import_csv_file_line
                # import_read = main_window.import_read
                parameters_table = main_window.parameters_table

                # Update the *import_csv_file_name* widget:
                # csv_file_name = current_table.csv_file_name
                # if tracing is not None:
                #    print("{0}csv_file_name='{1}'".format(tracing, csv_file_name))
                assert False
                current_table.csv_read_and_process(
                  "/home/wayne/public_html/projects/digikey_csvs", tracing=next_tracing)

                # Load up *import_table*:
                headers = current_table.import_headers
                # rows = current_table.import_rows
                column_triples = current_table.import_column_triples
                # if tracing is not None:
                #    print("{0}headers={1} rows={2} column_triples={3}".
                #      format(tracing, headers, rows, column_triples))

                parameters_table.clearContents()
                if headers is not None and column_triples is not None:
                    if tracing is not None:
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

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print("{0}<=TabledsEditor.parameters_update".format(tracing))

    # TablesEditor.quit_button_clicked():
    def quit_button_clicked(self):
        tables_editor = self
        print("TablesEditor.quit_button_clicked() called")
        application = tables_editor.application
        application.quit()

    # TablesEditor.results_update():
    def results_update(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{0}=>TablesEditor.results_update()".format(tracing))

        tables_editor = self
        main_window = tables_editor.main_window
        results_table = main_window.results_table
        results_table.clearContents()

        tables_editor.current_update(tracing=next_tracing)
        current_search = tables_editor.current_search
        if current_search is not None:
            current_search.filters_refresh(tracing=next_tracing)
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
        if tracing is not None:
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
    def run(self):
        # Show the *window* and exit when done:
        tables_editor = self
        main_window = tables_editor.main_window
        application = tables_editor.application
        clipboard = application.clipboard()
        print(f"type(clipboard)='{type(clipboard)}'")
        assert isinstance(clipboard, QClipboard)

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
            table.save(tracing=next_tracing)

        searches = tables_editor.searches
        xml_lines = list()
        xml_lines.append('<?xml version="1.0"?>')
        xml_lines.append('<Searches>')
        for search in searches:
            search.xml_lines_append(xml_lines, "  ")
        xml_lines.append('</Searches>')
        xml_lines.append("")
        xml_text = '\n'.join(xml_lines)
        searches_xml_file_name = os.path.join(order_root, "searches.xml")
        with open(searches_xml_file_name, "w") as searches_xml_file:
            searches_xml_file.write(xml_text)

        # Wrap up any requested signal tracing:
        if trace_signals:
            print("<=TablesEditor.save_button_clicked()\n")

    # TablesEditor.schema_update():
    def schema_update(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{0}=>TablesEditor.schema_update()".format(tracing))

        main_window = tables_editor.main_window
        schema_tabs = main_window.schema_tabs
        schema_tabs_index = schema_tabs.currentIndex()
        if schema_tabs_index == 0:
            tables_editor.tables_update(tracing=next_tracing)
        elif schema_tabs_index == 1:
            tables_editor.parameters_edit_update(tracing=next_tracing)
        elif schema_tabs_index == 2:
            tables_editor.enumerations_update(tracing=next_tracing)
        else:
            assert False
        # tables_editor.combo_edit.update()
        # tables_editor.parameters_update(None)
        # tables_editor.search_update()

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print("{0}=>TablesEditor.schema_update()".format(tracing))

    # TablesEditor.searches_comment_get():
    def searches_comment_get(self, search, tracing=None):
        # Verify argument types:
        assert isinstance(search, Search) or search is None
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        # tables_editor = self
        # next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{0}=>TableEditor.searches_comment_get('{1}')".format(tracing, search.name))

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

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print("{0}<=TablesEditor.searches_comment_get('{1}')".format(tracing, search.name))
        return text, position

    # TablesEditor.searches_comment_set():
    def searches_comment_set(self, search, text, position, tracing=None):
        # Verify argument types:
        assert isinstance(search, Search) or search is None
        assert isinstance(text, str)
        assert isinstance(position, int)
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        # tables_editor = self
        # next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{0}=>TablesEditor.searches_comment_set('{1}')".
                  format(tracing, "None" if search is None else search.name))

        # Stuff *text* and *position* into *search*:
        if search is not None:
            comments = search.comments
            assert len(comments) >= 1
            comment = comments[0]
            assert isinstance(comment, SearchComment)
            comment.lines = text.split('\n')
            comment.position = position

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print("{0}<=TablesEditor.searches_comment_set('{1}')".
                  format(tracing, "None" if search is None else search.name))

    # TablesEditor.searches_file_save():
    def searches_file_save(self, file_name, tracing=None):
        # Verify argument types:
        assert isinstance(file_name, str)
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{0}=>TablesEditor.searches_file_save('{1}')".format(tracing, file_name))

        xml_lines = list()
        xml_lines.append('<?xml version="1.0"?>')
        xml_lines.append('<Searches>')

        # Sweep through each *search* in *searches* and append the results to *xml_lines*:
        tables_editor = self
        searches = tables_editor.searches
        for search in searches:
            search.xml_lines_append(xml_lines, "  ", tracing=next_tracing)

        # Wrap up *xml_lines* and generate *xml_text*:
        xml_lines.append('</Searches>')
        xml_lines.append("")
        xml_text = '\n'.join(xml_lines)

        # Write out *xml_text* to *file_name*:
        with open(file_name, "w") as xml_file:
            xml_file.write(xml_text)

        # Wrqp up any requested *tracing*:
        if tracing is not None:
            print("{0}<=TablesEditor.searches_file_save('{1}')".format(tracing, file_name))

    # TablesEditor.searches_file_load():
    def searches_file_load(self, xml_file_name, tracing=None):
        # Verify argument types:
        assert isinstance(xml_file_name, str)
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{0}=>TablesEditor.searches_file_load('{1})".format(tracing, xml_file_name))

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
                                tables=tables_editor.tables, tracing=next_tracing)
                assert False, "Old code"
                searches.append(search)

            # Set *current_search*
            tables_editor.current_search = searches[0] if len(searches) >= 1 else None

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print("{0}<=TablesEditor.searches_file_load('{1})".format(tracing, xml_file_name))

    # TablesEditor.searches_is_active():
    def searches_is_active(self):
        tables_editor = self
        tables_editor.current_update()
        # We can only edit searches if there is there is an active *current_table8:
        return tables_editor.current_table is not None

    # TablesEditor.searches_new():
    def searches_new(self, name, tracing=None):
        # Verify argument types:
        assert isinstance(name, str)
        assert isinstance(tracing, str) or tracing is None

        # Perform requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{0}=>TablesEditor.searches_new('{1}')".format(tracing, name))

        tables_editor = self
        tables_editor.current_update()
        current_table = tables_editor.current_table

        # Create *serach* with an empty English *serach_comment*:
        search_comment = SearchComment(language="EN", lines=list())
        search_comments = [search_comment]
        search = Search(name=name, comments=search_comments, table=current_table)
        search.filters_refresh(tracing=next_tracing)

        # Wrap up any requested *tracing* and return *search*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{0}<=TablesEditor.searches_new('{1}')".format(tracing, name))
        return search

    # TablesEditor.searches_save_button_clicked():
    def searches_save_button_clicked(self):
        # Peform an requested signal tracing:
        tables_editor = self
        tracing = " " if tables_editor.trace_signals else None
        next_tracing = None if tracing is None else " "
        if tracing is not None:
            print("=>TablesEditor.searches_save_button_clicked()".format(tracing))

        # Write out the searches to *file_name*:
        file_name = os.path.join(order_root, "searches.xml")
        tables_editor.searches_file_save(file_name, tracing=next_tracing)

        if tracing is not None:
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
            tables_editor.current_update(tracing=next_tracing)
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
                current_search.table_set(match_table, tracing=next_tracing)

            # Wrap up any requested *tracing*:
            if trace_signals:
                print("<=TablesEditor.searches_table_changed('{0}')\n".format(new_text))
            tables_editor.in_signal = False

    # TablesEditor.searches_update():
    def searches_update(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{0}=>TablesEditor.searches_update()".format(tracing))

        # Make sure that *current_search* is up to date:
        tables_editor = self
        tables_editor.current_update(tracing=next_tracing)
        current_search = tables_editor.current_search

        # Update *searches_combo_edit*:
        searches_combo_edit = tables_editor.searches_combo_edit
        searches_combo_edit.gui_update(tracing=next_tracing)

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

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print("{0}<=TablesEditor.searches_update()".format(tracing))

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
                tab_unload(tables_editor, tracing=next_tracing)

            # Perform the update:
            tables_editor.update(tracing=next_tracing)

            # Wrap up any requested signal tracing and restore *in_signal*:
            if trace_signals:
                print("<=TablesEditor.tab_changed(*, {0})\n".format(new_index))
            tables_editor.in_signal = False

    # TablesEditor.table_comment_get():
    def table_comment_get(self, table, tracing=None):
        # Verify argument types:
        assert isinstance(table, Table)
        assert isinstance(tracing, str) or tracing is None

        text = ""
        # Perform any requested *tracing*:
        # tables_editor = self
        # next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{0}=>table_comment_get('{1}')".format(tracing, table.name))

        # Extract the comment *text* from *table*:
        if table is not None:
            comments = table.comments
            assert len(comments) >= 1
            comment = comments[0]
            assert isinstance(comment, TableComment)
            text = '\n'.join(comment.lines)
            position = comment.position

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print("{0}<=table_comment_get('{1}')".format(tracing, table.name))
        return text, position

    # TablesEditor.table_comment_set():
    def table_comment_set(self, table, text, position, tracing=None):
        # Verify argument types:
        assert isinstance(table, Table)
        assert isinstance(text, str)
        assert isinstance(position, int)
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        # tables_editor = self
        # next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
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
        if tracing is not None:
            print("{0}<=table_comment_set('{1}')".format(tracing, table.name))

    def table_is_active(self):
        # The table combo box is always active, so we return *True*:
        return True

    # TablesEditor.table_new():
    def table_new(self, name, tracing=None):
        # Verify argument types:
        assert isinstance(name, str)

        # Perform an requested *tracing*:
        # next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{0}=>TablesEditor.table_new('{1}')".format(tracing, name))

        file_name = "{0}.xml".format(name)
        table_comment = TableComment(language="EN", lines=list())
        table = Table(file_name=file_name, name=name, path="", comments=[table_comment],
                      parameters=list(), csv_file_name="", parent=None)

        # Wrap up any requested *tracing* and return table:
        if tracing is not None:
            print("{0}<=TablesEditor.table_new('{1}')".format(tracing, name))
        return table

    # TablesEditor.table_setup():
    def table_setup(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any tracing requested from *tables_editor* (i.e. *self*):
        tables_editor = self
        # next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{0}=>TablesEditor.table_setup(*)".format(tracing))

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

        # Wrap up any requested tracing:
        if tracing is not None:
            print("{0}=>TablesEditor.table_setup(*)".format(tracing))

    # TablesEditor.tables_update():
    def tables_update(self, table=None, tracing=None):
        # Verify argument types:
        assert isinstance(table, Table) or table is None
        assert isinstance(tracing, str) or tracing is None

        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self

        # Perform any requested *trracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{0}=>TablesEditor.tables_update()".format(tracing))

        # Make sure that the *current_table*, *current_parameter*, and *current_enumeration*
        # in *tables_editor* are valid:
        tables_editor.current_update(tracing=next_tracing)

        # Update the *tables_combo_edit*:
        tables_editor.tables_combo_edit.gui_update(tracing=next_tracing)

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print("{0}<=TablesEditor.tables_update()".format(tracing))

    # TablesEditor.update():
    def update(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        tables_editor = self
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>TablesEditor.update()")

        # Only update the visible tabs based on *root_tabs_index*:
        main_window = tables_editor.main_window
        root_tabs = main_window.root_tabs
        root_tabs_index = root_tabs.currentIndex()
        if root_tabs_index == 0:
            tables_editor.collections_update(tracing=next_tracing)
        elif root_tabs_index == 1:
            tables_editor.schema_update(tracing=next_tracing)
        elif root_tabs_index == 2:
            tables_editor.parameters_update(tracing=next_tracing)
        elif root_tabs_index == 3:
            tables_editor.find_update(tracing=next_tracing)
        else:
            assert False, "Illegal tab index: {0}".format(root_tabs_index)

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=TablesEditor.update()")

    # TablesEditor.search_update():
    def xxx_search_update(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{0}=>TablesEditor.search_update(*)".format(tracing))

        # Make sure that the *current_table*, *current_parameter*, and *current_enumeration*
        # in *tables_editor* are valid:
        tables_editor = self
        tables_editor.current_update(tracing=next_tracing)

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
        tables_editor.search_combo_edit.gui_update(tracing=next_tracing)

        if tracing is not None:
            print("{0}<=TablesEditor.search_update(*)".format(tracing))


# TreeModel:
class TreeModel(QAbstractItemModel):

    FLAG_DEFAULT = Qt.ItemIsEnabled | Qt.ItemIsSelectable

    # TreeModel.__init__():
    def __init__(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}=>TreeModel.__init__(*)")

        # Initialize the parent *QAbstraceItemModel*:
        super().__init__()

    
        # Stuff *collections* into *tree_model* (i.e. *self*):
        tree_model = self
        tree_model.headers = {0: "Type", 1: "Name"}
        tree_model.collections = None
        tree_model.tracing = tracing
        #tree_model.tracing = None  # Comment out to enable *TreeModel* *tracing*:

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=TreeModel.__init__(*)")


    # check if the node has data that has not been loaded yet
    # TreeModel.canFetchMore():
    def canFetchMore(self, model_index):
        # Verify argument types:
        assert isinstance(model_index, QModelIndex)

        # Perform any *tracing* requested by *tree_model* (i.e.*self*):
        tree_model = self
        tracing = tree_model.tracing
        if tracing is not None:
            print(f"{tracing}=>TreeModel.canFetchMore()")

        # We delegate the decision of whether we can fetch more stuff to the *node*
        # associated with *model_index*:
        node = tree_model.getNode(model_index)
        can_fetch_more = node.can_fetch_more()

        # Wrap up any requested *tracing*:
        if tracing is not None:
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
        if tracing is not None:
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
                    value = node.name_get(tracing=next_tracing)
        assert isinstance(value, str) or value is None

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=Tree_model.data(*, *, {role}')=>{value}")
        return value

    # TreeModel.delete():
    def delete(self, model_index, tracing=None):
        # Verify argument types:
        assert isinstance(model_index, QModelIndex)
        assert isinstance(tracing, str) or tracing is None

        # Perform any *tracing* requested by *tree_model* (i.e. *self*):
        tree_model = self
        tracing = tracing if tracing is not None else tree_model.tracing
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>TreeModel.delete(*)")

        # Carefully delete the row associated with *model_index*:
        if model_index.isValid():
            row = model_index.row()
            node = tree_model.getNode(model_index)
            assert isinstance(node, Node)
            parent = node.parent
            assert isinstance(parent, Node)
            parent.child_remove(node, tracing=next_tracing)

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=TreeModel.delete(*, *)\n")

    # TreeModel.fetchMore():
    def fetchMore(self, model_index):
        # Verify argument types:
        assert isinstance(model_index, QModelIndex)

        # Perform any *tracing* requested by *tree_model* (i.e. *self*):
        tree_model = self
        tracing = tree_model.tracing
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>TreeModel.fetchMore(*, *)")

        # Delegate fetching to the *node* associated with *model_index*:
        tree_model = self
        node = tree_model.getNode(model_index)
        node.fetch_more(tracing=next_tracing)
        # tree_model.insertNodes(0, node.children_get(), model_index)

        if tracing is not None:
            print(f"{tracing}<=TreeModel.fetchMore(*, *)\n")

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
    def children_update(self, parent_model_index, tracing=None):
        # Verify argument types:
        assert isinstance(parent_model_index, QModelIndex)
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        # next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{0}=>TreeModel.children_update(*,*)".format(tracing))

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

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print("{0}<=TreeModel.children_update(*,*)".format(tracing))

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
if __name__ == "__main__":
    main()
