#!/usr/bin/env python

# # bom_manager
#
# ## Overview:
#
#
# This program is called *bom_manager* (i.e. Bill of Materials Manager.)
# The program fundamentally deals with the task of binding parts in a
# schematic with actual parts that can be ordered from one or more
# vendors (i.e. distributors, sellers, etc.)  It also deals with binding
# the schematic parts with footprints that can be used with the final PCB
# (i.e. Printed Circuit Board.)
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
# For example the Atmel ATmega328 comes in 4 different IC packages --
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

# Import some libraries:
from bs4 import BeautifulSoup	# HTML/XML data structucure searching
import fnmatch			# File Name Matching
import json			# Another pickling format
import math			# Math
import os.path			# File names/paths
import pickle			# Python data structure pickle/unpickle
import re			# Regular expressions
import requests			# HTML Requests
import sexpdata			# (LISP) S_EXpresson Data
from sexpdata import Symbol	# (LISP) S-EXpression Symbol
import sys			# Miscellanesous SYStem stuff
import time			# Time package

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
# *Board*: A board corresponds to a single PCB (e.g. a .kicad_pcb file.)
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
# *Board_Part*: A *Board_Part* is essentially one-to-one with a Schematic
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
# *Schematic_Part*: A schematic part is one-to-one with a
# *Schematic_Symbol_Name* (excluding the comment field.)  A *Schematic_Part*
# essentially provides a mapping from a *Schematic_Symbol_Name" to a list of
# acceptable manufacturer parts, which in turn provides a mapping to
# acceptable vendor parts.  There are three sub-classes of *Schematic_Part* --
# *Choice_Part*, *Alias_Part*, and *Fractional_Part*.  As the algorithm
# proceeds, all *Alias_Part*'s and *Fractional_Part*'s are converted into
# associated *Choice_Part*'s.  Thus, *Choice_Part* is the most important
# sub-class of *Schematic_Part*.
#
# *Choice_Part*: A *Choice_Part* is sub-classed from *Schematic_Part*
# and lists one or more acceptable *Actual_Part*'s. (An actual part
# is one-to-one with a manufacturer part -- see below.)  A *Choice_Part*
# also specifies a full KiCad Footprint.
#
# *Alias_Part*: An *Alias_Part* is also sub-classed from *Schematic_Part*
# and specifies one or more *Schematic_Parts* to substitute.
#
# *Fractional_Part*: A *Fractional_Part* is also sub-classed from
# *Schematic_Part* and corresponds to a 1xN or 2xN break away header.
# It is common special case that specifies a smaller number of pins
# than the full length header.
#
# *Actual_Part*: An *Actual_Part* should probably have been defined
# as a *Manufacturer_Part*.  An *Actual_Part* consists of a *Manufacturer*
# (e.g "Atmel"), and Manufacturer part name (e.g. "ATMEGA328-PU".)
#
# *Vendor_Part*: A *Vendor_Part* should have probably been defined
# as a *Distributor_Part*.  A *Vendor* part consists of a *Vendor*
# (e.g. "Mouser") and a *Vendor_Part_Name* (e.g. "123-ATMEGA328-PU").
#
# Notice that there are 6 different part classes:  *Schematic_Part*,
# *Choice_Part*, *Alias_Part*, *Fractional_Part*, *Actual_Part* and
# *Vendor_Part*.  Having this many different part classes is needed
# to precisely keep track of everything.
#
# There are a few more classes to worry about:
#
# *Order*: An *Order* specifies a list of *Board*'s and a quantity
# for each *Board*.  Also, an order can specify a list of vendors
# to exclude from the order.
#
# *Board*: A *Board* is one-to-one with KiCad PCB.  It is basicaly
# consists of a list of *Board_Part*'s.
#
# *Board_Part*: A *Board_Part* is basically a *Schematic_Symbol_Name*
# along with a board annotation reference (e.g. R123, U7, etc.)
#

# **:
#
#
# There are three sub_classes of *Schematic_Part*:
#
# * Choice_Part*: A list of possible *Actual_Part*'s to choose from.
#
# * Alias_Part*: An alias specifies one or more schematic parts to
#   redirect to.
#
# * Fractional_Part*: A fractional part is an alias to another schematic
#   part that specifes a fraction of the part.  A fractional part is
#   usually a 1x40 or 2x40 break-away male header.  They are so common
#   they must be supported.
#
# Now the algorithm iterates through each *Schematic_Part* to convert
# each *Fractional_Part* and *Alias_Part* into *Choice_Part*.
# Errors are flagged.
#
# The *Database* maintains a list of *Vendor*'s and *Vendor_Parts*.
#
# For each *Choice_Part*, the *Actual_Part* list is iterated over.
# (Warning: the code has evolved somewhat here...)
# Octopart is queried to find build up a *Vendor_Part* list.  The
# queries are cached to avoid making excessive queries to Octopart.
# Only *Actual_Part*'s that are not in the cache get sent off to
# Octopart to fill the cache.  A log of Octopart quries is kept to
# get an idea of how often the database is queried.  It may be the
# case that there is a flag that disables queries until the user
# explicitly asks for it.
#
# Now that there is a list of *Vendor_Part*'s for each *Actual_Part*,
# the lowest cost *Vendor_Part* is selected based on the number of
# *Actual_Part*'s needed.  The code identifies the cheapest *Vendor_Part*
# and it may adjust the quantity ordered up to get the benefit of a
# price break.  This is where vendor exclusion occurs.  Errors are
# generated if there are no *Vendor_Part* left due to exclusion or
# unavailable stock.
#
# Now various reports are generated based on sorting by vendor,
# sorting by cost, etc.  The final BOM's for each board is generated
# as a .csv file.


class Database:
    # Database of *Schematic_Parts*:

    def __init__(self):
	""" *Database*: Initialize *self* to be a database of
	    *Schematic_part*'s. """

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

	# Priorities 100-999 are auto assigned for vendors that are
	# not explicitly prioritiezed below.
	
	# Prioritins 1000+ are for explicitly preferred vendors:
	vendor_priorities["Arrow"] = 1000
	vendor_priorities["Avnet Express"] = 1001
	vendor_priorities["Newark"] = 1002
	vendor_priorities["Mouser"] = 1003
	vendor_priorities["Digi-Key"] = 1004

	# Initialize the various tables:
	self.actual_parts = {} # Key:(manufacturer_name, manufacturer_part_name)
	self.bom_parts_file_name = bom_parts_file_name
	self.schematic_parts = {}   # Key: "part_name;footprint:comment"
	self.vendor_minimums = vendor_minimums
	self.vendor_parts_cache = {} # Key:(actual_key)
	self.vendor_priorities = vendor_priorities
	self.vendor_priority = 10

	vendor_parts_cache = self.vendor_parts_cache
	# Read in any previously created *vendor_parts*:
	if os.path.isfile(bom_parts_file_name):
	    #print("Start reading BOM parts file: '{0}'".
	    #  format(bom_parts_file_name))

	    # Read in picked *vendor_parts* from *bom_file_name*:
	    bom_pickle_file = open(bom_parts_file_name, "r")
	    pickled_vendor_parts_cache = pickle.load(bom_pickle_file)
	    bom_pickle_file.close()

	    # Flush out old (stale) vendor parts from *pickled_vendor_parts*:
	    now = time.time()
	    old = now - 2.0 * 24.0 * 60.0 * 60.0
	    for actual_key in pickled_vendor_parts_cache.keys():
		vendor_parts = pickled_vendor_parts_cache[actual_key]
		for vendor_part in vendor_parts:
		    assert isinstance(vendor_part, Vendor_Part)
		    if vendor_part.timestamp < old:
			del vendor_parts[vendor_part.vendor_key]
		if len(vendor_parts) > 0:
		    vendor_parts_cache[actual_key] = vendor_parts

	    with open("/tmp/database.dmp", "w") as dump_stream:
		self.dump(dump_stream)

	# Now here is where we initialize the database:

	# Batteries and Holders:
	self.choice_part("BAT_HOLDER;2032_THRU", "BU2032-1", "",
	  "HOLDER COIN CELL 2032 PC PIN").actual_part(
	  "MPD", "BU2032-1-HD-G").actual_part(
	  "MPD", "BU2032-1").actual_part(
	  "MPD", "BU2032-1-G")

	# Boxes:
	self.choice_part("JB-3955;102Lx152Wx152H", "102Lx152Wx152H", "",
	  "BOX STEEL GRAY 102Lx152Wx152H").actual_part(
	  "Bud Industries", "JB-3955", [
	  ("Digi-Key", "377-1838-ND",
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

	self.choice_part("6pF;1608", "IPC7351:CAPC1608X90N", "",
	  "CAP CER 6PF 50V+ NP0 0603").actual_part(
	  "TDK", "C1608CH2A060D080AA").actual_part(
	  "KEMET Corporation", "CBR06C609BAGAC").actual_part(
	  "Yageo", "CC0603DRNPO9BN6R0")
	self.choice_part("18pF;1608", "IPC7351:CAPC1608X90N", "",
	  "CAP CER 18PF 25V+ 10% SMD 0603").actual_part(
	  "Kamet", "C0603C180J5GACTU", [
	   ("Digi-Key", "399-1052-1-ND",
	    "1/.10 10/.034 50/.0182 100/.0154 250/.0126")]).actual_part(
	  "Samsung", "CL10C180JB8NNNC").actual_part(
	  "TDK", "C1608C0G1H180J080AA").actual_part(
	  "Murata", "GRM1885C1H180JA01D").actual_part(
	  "Samsung", "CL10C180JC8NNNC").actual_part(
	  "Murata", "GRM1885C2A180JA01D").actual_part(
	  "TDK", "CGA3E2C0G1H180J080AA").actual_part(
	  "Kamet", "C0603C180K5GACTU").actual_part(
	  "Murata", "GCM1885C1H180JA16D").actual_part(
	  "TDK", "C1608CH1H180J080AA").actual_part(
	  "AVX", "06035A180JAT2A").actual_part(
	  "Yageo", "CC0603JRNPO9BN180")
	self.choice_part(".1uF;1608", "IPC7351:CAPC1608X90N", "",
	  "CAP CER 0.1UF 25V+ 10% SMD 0603").actual_part(
	  "Murata", "GRM188R71E104KA01D", [
	  ("Digi-Key", "490-1524-1-ND",
	   "1/.10 10/.019 50/.0104 100/.0088 250/.0072")]).actual_part(
	  "TDK", "C1608X7R1E104K080AA").actual_part(
	  "Kemet", "C0603C104K3RACTU").actual_part(
	  "Kemet", "C0603C104M5RACTU").actual_part(
	  "Samsung", "CL10B104KB8SFNC").actual_part(
	  "Murata", "GRM188R71H104KA93D").actual_part(
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
	self.choice_part("1uF;1608", "IPC7351:CAPC1608X90N", "",
	  "CAP CER 1UF 25V+ 10% SMD 0603").actual_part(
	  "Murata", "GRM188R61E105KA12D").actual_part(
	  "Taiyo Yuden", "TMK107BJ105KA-T").actual_part(
	  "Samsung", "CL10B105KA8NNNC").actual_part(
	  "Taiyo Yuden", "TMK107B7105KA-T").actual_part(
	  "Samsung", "CL10A105KA8NNNC").actual_part(
	  "Samsung", "CL10A105KA5LNNC").actual_part(
	  "Samsung", "CL10B105KA8NFNC").actual_part(
	  "Murata", "GRM188F51E105ZA12D").actual_part(
	  "Yageo", "CC0603KRX5R8BB105").actual_part(
	  "Murata", "GRM188R61E105MA12D").actual_part(
	  "Samsung", "CL10A105KA8NFNC").actual_part(
	  "Yageo", "CC0603ZRY5V8BB105")
	self.choice_part("470uF;D10P5", "CAP_D10P5", "",
	  "CAP ALUM 470UF 20% 16V+ RADIAL").actual_part(
	  "Kemet", "ESK477M025AH1EA").actual_part(
	  "Nichicon", "UVR1V471MPD1TD").actual_part(
	  "Panasonic", "ECA-1EM471B").actual_part(
	  "Nichicon", "UPS1C471MPD1TD").actual_part(
	  "Nichicon", "UPW1C471MPD1TD").actual_part(
	  "Nichicon", "UPM1C471MPD6TD").actual_part(
	  "Nichicon", "UPW1E471MPD1TD").actual_part(
	  "Nichicon", "UVZ1E471MPD1TD").actual_part(
	  "Kemet", "ESK477M035AH2EA").actual_part(
	  "Nichicon", "UVK1E471MPD1TD")

	self.choice_part("1500UF_200V;R35MM", "R35MM", "",
	  "CAP ALUM 1500UF 200V SCREW").actual_part(
	  "Unitied Chemi-Con", "E36D201LPN152TA79M", [
	  ("Digi-Key", "565-3307-ND",
	   "1/12.10 10/11.495 100/9.075")])

	# Connectors:

	## Male Connectors:

	### Create the fractional parts for 1XN male headers:
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

	# Test points M1X1:
	self.alias_part("CAN_RXD;M1X1",
	  ["M1X1;M1X1"], "Pin_Header_Straight_1x01")
	self.alias_part("TEST_POINT;M1X1",
	  ["M1X1;M1X1"], "Pin_Header_Straight_1x01")

	# M1X2:
	self.alias_part("CURRENT_SHUNT;M1X2",
	  ["M1X2;M1X2"], "Pin_Header_Straight_1x02")

	# M1X3:
	self.alias_part("CURRENT_SHUNT;M1X3",
	  ["M1X3;M1X3"], "Pin_Header_Straight_1x03")
	self.alias_part("TERMINATE_JUMPER;M1X3",
	  ["M1X3;M1X3"], "Pin_Header_Straight_1x03")
	self.alias_part("SERVO;M1X3",
	  ["M1X3;M1X3"], "Pin_Header_Straight_1x03")

	# M1X4:
	self.alias_part("I2C_CONN;M1X4",
	  ["M1X4;M1X4"], "Pin_Header_Straight_1x04")

	# M1X6:
	self.alias_part("ENCODER_CONNECTOR;M1X6",
	  ["M1X6;M1X6"], "Pin_Header_Straight_1x06")
	self.alias_part("FTDI_HEADER;M1X6",
	  ["M1X6;M1X6"], "Pin_Header_Straight_1x06")
	self.alias_part("FTDI_HEADER_ALT;M1X6",
	  ["M1X6;M1X6"], "Pin_Header_Straight_1x06")

	### Create the fractional parts for the 2XN male headers:
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

	self.choice_part("M2X5S;M2X5S",
	  "Pin_header_Straight_2x05_Shrouded", "",
	  "BOX HEADER .100in MALE STR 10POS").actual_part(
	  "Assmann", "AWHW-10G-0202-T").actual_part(
	  "Sullins", "SBH11-PBPC-D05-ST-BK").actual_part(
	  "3M", "30310-6002HB").actual_part(
	  "TE Tech", "5103308-1").actual_part(
	  "Wurth", "61201021621")
	self.alias_part("BUS_MASTER_HEADER;M2X5S",
	  ["M2X5S;M2X5S"], "Pin_Header_Straight_2x05_Shrouded")

	self.fractional_part("M2X6;M2X6", "Pin_Header_Straight_2x06",
	  "M2X40;M2X40", 12, 80, "CONN HEADER .100in DBL STR 12POS")

        # Non-fractional part Male connectors:

        self.choice_part("ENCODER_CONNECTOR;M1X6_JST", "M1X6_JST", "M1X6_JST",
	  "CONN HEADER ZH SIDE 6POS 1.5MM").actual_part(
	  "JST", "S6B-ZR(LF)(SN)")

	## Female connectors:

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

	self.choice_part("F2X10RA;F2X10RA", "Pin_Receptale_Angled_2x10", "",
	  "CONN RCPT .100in 20POS DUAL").actual_part(
	  "Sullins", "SFH11-PBPC-D10-RA-BK").actual_part(
	  "Sullins", "PPTC102LJBN-RC").actual_part(
	  "Sullins", "PPPC102LJBN-RC").actual_part(
	  "Samtec", "SSQ-110-02-T-D-RA").actual_part(
	  "TE", "5535512-2").actual_part(
	  "Samtec", "SSW-110-02-G-D-RA").actual_part(
	  "Samtec", "SSW-110-02-S-D-RA").actual_part(
	  "Hirose", "HIF3H-20DB-2.54DS(71)")

	self.choice_part("F2X20RA;F2X20RA", "Pin_Receptale_Angled_2x20", "",
	  "CONN RCPT .100in 40POS DUAL").actual_part(
	  "Sullins", "PPTC202LJBN-RC").actual_part(
	  "Sullins", "SFH11-PBPC-D20-RA-BK").actual_part(
	  "Sullins", "PPPC202LJBN-RC").actual_part(
	  "3M", "960240-7102-AR	")
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

	# USB connectors:
        self.choice_part("USB_MICRO_B;S+T", "FCI_10118194_0001LF", "",
	  "CONN USB MICRO B RECPT SMT R/A").actual_part(
	  "Amphenol", "10118194-0001LF")

	self.choice_part("USB_B_ALT;ALT", "USB_B", "",
	  "CONN USB TYPE B JACK").actual_part(
	  "Pulse Electronics", "E8144-B02022-L")

	# Crystals:

	self.choice_part("16MHZ;HC49S", "IPC7351:XTAL1150X480X430N", "",
	  "CRYSTAL 16.0000MHZ SMD").actual_part(
	  "TXC", "9C-16.000MAAE-T").actual_part(
	  "TXC", "9C-16.000MAGJ-T")
	# This alias should be removed:
	self.alias_part("16MHZ;HC49",
	  ["16MHZ;HC49S"], "IPC7351:XTAL1150X480X430N")

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
	  "Cardinal", "CPFBZ-A2C4-32.768KD6").actual_part(
	  "Cardinal", "CPFBZ-A2C5-32.768KD12.5").actual_part(
	  "Cardinal", "CPFBZ-A2C5-32.768KD6").actual_part(
	  "ECS", "ECS-.327-6-17X-TR").actual_part(
	  "ECS", "ECS-.327-6-17X-C-TR").actual_part(
	  "Citizen", "CM200C32768AZFT").actual_part(
	  "Fox", "FSRLF327-6").actual_part(
	  "ECS", "ECS-.327-12.5-17X-C-TR").actual_part(
	  "Citizen", "CM200C32768DZFT").actual_part(
	  "Citizen", "CM200C32768DZYT").actual_part(
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
	  "Diodes Inc", "DDZ4V7ASF-7", [
	  ("Digi-Key", "DDZ4V7ASF-7DICT-ND",
	   "1/.16 10/.143 100/.0781 500/.04802 1000/.03275")])

	self.choice_part("BRIDGE_35A_1000V;GBPC", "GBPC", "",
	  "RECT BRIDGE GPP 1000V 35A GBPC").actual_part(
	  "Comchip Tech", "GBPC3510-G", [
	  ("Digi-Key", "641-1380-ND",
	   "1/2.54 10/2.296 25/2.05 100/1.845 250/1.64")])

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
	  "Micro Commercial", "SK18-LTP").actual_part(
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
	  "Essentra", "PGSB-0609A", [
	  ("Digi-Key", "RPC1251-ND",
	   "1/.18 10/.166 25/.1536 100/.1281")])

	# Holes:

	self.choice_part("HOLE;2.5MM", "2_5MM_HOLE", "",
	  "2.5MM HOLE").actual_part(
	  "Digi-Key", "RM2X8MM 2701") # Kludge
	self.choice_part("HOLE;3MM_SLOT", "CASTER_SLOT", "",
          "3MM SLOT HOLE").actual_part(
	  "Digi-Key", "RM3X10MM 2701") # Kludge
	self.choice_part("HOLE;3MM", "3MM_HOLE", "",
	  "3MM HOLE").actual_part(
	  "Digi-Key", "PMS 440 0063 SL")	# Kludge
	self.choice_part("HOLE;2MM", "2MM_HOLE", "",
	  "2MM HOLE").actual_part(
	  "Digi-Key", "PMS 632 0031 SL") # Kludge
	self.choice_part("SLOT_HOLE;10X20MM", "10X20MM_HOLE", "",
	  "10X20MM HOLE").actual_part( # Kludge
	  "Digi-Key", "PMS 632 0063 SL")

	# Fuses:

	self.choice_part("3A;LF649", "LF649", "",
	  "FUSE BLOCK CART 250V 6.3A PCB").actual_part(
	  "Littelfuse", "64900001039", [
	  ("Digi-Key", "WK0011-ND",
	    "1/.40 10/.378 25/.348 50/.318 100/.264 250/.24 500/.204")])
	# This alias should be removed:
	self.alias_part("3A;LF349", ["3A;LF649"], "LF649")

	# Inductors:

	self.choice_part("SRR1280-221K;12.5MM", "SRR1280", "",
	  "FIXED IND 220UH 1.6A 400 MOHM").actual_part(
	  "Bourns", "SRR1280-221K")

	self.choice_part("?uH;I1X10", "Inductor_1x10", "",
	  "INLINE INDUCTER").actual_part(
	  "Bourns", "5258-RC", [
	  ("Digi-Key", "M8275-ND",
	   "1/1.51 10/1.392 25/1.276 50/1.0904 100/.97440")])

	self.choice_part("CIB10P100NC;1608", "IPC7351:INDC1608X95N", "",
	  "FERRITE CHIP 10 OHM 1000MA 0603").actual_part(
	  "Samsung", "CIB10P100NC")

	# Integrated Circuits:

	self.choice_part("5V_LDO;SOT223", "SOT223", "",
	  "IC REG LDO 5V SOT223-3").actual_part(
	  "Diodes Inc", "AP1117E50G-13", [
	   ("Digi-Key", "AP1117E50GDICT-ND",
	    "1/.47 10/.377 100/.2571 500/.19242 1000/.14412")]).actual_part(
	  "Diodes Inc", "ZLDO1117G50TA").actual_part(
	  "Microchip", "MCP1824ST-5002E/DB").actual_part(
	  "Microchip", "MCP1825S-5002E/DB").actual_part(
	  "Microchip", "TC1262-5.0VDB").actual_part(
	  "Microchip", "MCP1703-5002E/DB").actual_part(
	  "Microchip", "MCP1703T-5002E/DB")

	self.choice_part("AP2210N-3.3T;SOT-23-3", "extra-nominal:SOT95P280X145-3N", "",
	  "3.3V LDO").actual_part(
	  "Diodes Inc", "AP2210N-3.3TRG1").actual_part(
          "Microchip", "MCP1700T-3302E/TT").actual_part(
          "Microchip", "MCP1700T-3302E/MB")


	self.choice_part("74xHC08;SOIC8", "SOIC127P600X175-14N", "",
	  "IC GATE AND 4CH 2-INP 14-SOIC").actual_part(
	  "Fairchild", "MM74HCT08MX").actual_part(
	  "Fairchild", "74VHCT08AMX").actual_part(
	  "TI", "SN74HC08DR").actual_part(
	  "TI", "SN74HCT08DR").actual_part(
	  "TI", "SN74AHCT08DR").actual_part(
	  "TI", "SN74AHC08DR").actual_part(
	  "Fairchild", "MM74HC08MX").actual_part(
	  "TI", "CD74HC08M96").actual_part(
	  "TI", "CD74HCT08M96").actual_part(
	  "Fairchild", "74VHC08MX")

	self.choice_part("74HC32;SOIC14", "SOIC127P600X175-14N", "",
	  "IC GATE OR 4CH 2-INP 14-SOIC").actual_part(
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

	self.choice_part("74HC1G14;SOT23-5", "SOT95P280X145-5N", "",
	  "IC INVERTER SGL SCHMITT SOT23-5").actual_part(
	  "On Semi", "MC74HC1G14DTT1G", [
	   ("Digi-Key", "MC74HC1G14DTT1GOSCT-ND",
	    "1/.39 10/.319 100/.1691 500/.11116 1000/.07574")])

	self.choice_part("74HC1G175;SOT23-6", "SOT95P280X145-6N", "",
	  "IC D-TYPE POS TRG SNGL SOT23-6").actual_part(
	  "TI", "SN74LVC1G175DBVR").actual_part(
	  "TI", "SN74LVC1G175DBVT")

	self.choice_part("ATMEGA328;QFP32", "QFP80P900X900X120-32N", "",
	  "IC MCU 8BIT 32KB FLASH 32QFP").actual_part(
	  "Atmel", "ATMEGA328-AUR", [
	  ("Digi-Key", "ATMEGA328-AURCT-ND",
	   "1/3.38 10/3.015 25/2.7136 100/2.4723 250/2.23112")])

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
	  "IC MOTOR DRIVER PAR 20-SOIC").actual_part(
	  "ST Micro", "L293DD")

	self.choice_part("LM311;SOIC8", "SOIC127P600X173-8N", "",
	  "IC COMPARATOR SGL 8SOIC").actual_part(
	  "TI", "LM311DR",[
	   ("Digi-Key", "296-1388-1-ND",
	    "1/.47000 10/.361 100/.19 1000/.17")]).actual_part(
	  "On Semi", "LM311DR2G").actual_part(
	  "TI", "LM311DRG4").actual_part(
	  "TI", "LM311MX/NOPB")

	self.choice_part("MCP2562;SOIC8", "SOIC127P600X175-8N", "",
	  "IC TXRX CAN 8SOIC").actual_part(
	  "Microchip", "MCP2562T-E/SN", [
	  ("Digi-Key", "MCP2562T-E/SNCT-ND",
	   "1/1.08 10/.90 25/.75 100/.68")])
	self.choice_part("MCP7940;SOIC8", "SOIC127P600X175-8N", "",
	  "IC RTC CLK/CALENDAR I2C 8-SOIC").actual_part(
	  "Microchip", "MCP7940M-I/SN").actual_part(
	  "Microchip", "MCP7940N-I/SN").actual_part(
	  "Microchip", "MCP7940N-E/SN").actual_part(
	  "Microchip", "MCP79400-I/SN").actual_part(
	  "Microchip", "MCP79402-I/SN").actual_part(
	  "Microchip", "MCP79401-I/SN")
	self.choice_part("CAT24C32;SOIC8", "IPC7351:SOIC127P600X175-8N", "",
	  "IC EEPROM 32KBIT 400KHZ 8SOIC").actual_part(
	  "ON Semiconductor", "CAT24C32WI-GT3")
	
	# LED's:
	
	self.choice_part("GREEN_LED;1608", "DIOC1608X55N", "",
	  "LED 0603 GRN WATER CLEAR").actual_part(
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

	self.choice_part("CREE_3050;CXA3050", "CXA3050", "",
	  "CREE XLAMP CXA3050 23MM WHITE").actual_part(
	  "Cree", "CXA3050-0000-000N0HW440F")

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

	self.choice_part("0;1608", "IPC7351:RESC1608X55N", "",
	  "RES SMD 0.0 OHM JUMPER 1/10W").actual_part(
	  "Vishay Dale", "CRCW06030000Z0EA").actual_part(
	  "Rohm", "MCR03EZPJ000").actual_part(
	  "Panasonic", "ERJ-3GEY0R00V").actual_part(
	  "Stackpole", "RMCF0603ZT0R00").actual_part(
	  "Bourns", "CR0603-J/-000ELF")
	self.choice_part("0.20_1W;6432", "IPC7351:RESC6432X70N", "",
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
	
	self.choice_part("120;1608", "IPC7351:RESC1608X55N", "",
	  "RES SMD 120 OHM 5% 1/10W 1608").actual_part(
	  "Vishay Dale", "CRCW0603120RJNEA", [
	   ("Digi-Key", "541-120GCT-ND",
	    "10/.074 50/.04 200/.02295 1000/.01566")]).actual_part(
	  "Vishay Dale", "CRCW0603120RFKEA").actual_part(
	  "Rohm", "MCR03ERTJ121").actual_part(
	  "Rohm", "MCR03ERTF1200").actual_part(
	  "Samsung", "RC1608J121CS").actual_part(
	  "Samsung", "RC1608F121CS").actual_part(
	  "Rohm", "KTR03EZPF1200")
	self.choice_part("470;1608", "IPC7351:RESC1608X55N", "",
	  "RES SMD 470 5% 1/10W 1608").actual_part(
	  "Vishay Dale", "CRCW0603470RJNEA", [
	   ("Digi-Key", "541-470GCT-ND",
	    "10/.074 50/.04 200/.02295 1000/.01566")]).actual_part(
	  "Rohm", "MCR03ERTJ471").actual_part(
	  "Samsung", "RC1608J471CS").actual_part(
	  "Rohm", "KTR03EZPJ471")
	self.choice_part("1K;1608", "IPC7351:RESC1608X55N", "",
	  "RES SMD 1K 5% 1/10W 0603").actual_part(
	  "Vishay Dale", "CRCW06031K00JNEA").actual_part(
	  "Rohm", "MCR03ERTJ102").actual_part(
	  "Yageo", "RC0603JR-071KP").actual_part(
	  "Samsung", "RC1608J102CS").actual_part(
	  "Rohm", "TRR03EZPJ102").actual_part(
	  "Vishay Dale", "RCG06031K00JNEA").actual_part(
	  "Rohm", "KTR03EZPJ102")
	self.choice_part("4K7;1608", "IPC7351:RESC1608X55N", "",
	  "RES SMD 4.7K 5% 1/10W 1608").actual_part(
	  "Vishay Dale", "CRCW06034K70JNEA").actual_part(
	  "Yageo", "RC0603JR-074K7L").actual_part(
	  "Panasonic", "ERJ-3GEYJ472V").actual_part(
	  "Rohm", "MCR03EZPJ472").actual_part(
	  "Rohm", "MCR03ERTJ472").actual_part(
	  "Stackpole", "RMCF0603JT4K70").actual_part(
	  "Bourns", "CR0603-JW-472ELF").actual_part(
	  "Samsung", "RC1608J472CS").actual_part(
	  "Yageo", "RC0603JR-074K7P").actual_part(
	  "Rohm", "TRR03EZPJ472").actual_part(
	  "Vishay Dale", "RCG06034K70JNEA").actual_part(
	  "Bourns", "CR0603-JW-472GLF")
	self.choice_part("10K;1608", "IPC7351:RESC1608X55N", "",
	  "RES SMD 10K OHM 5% 1/10W 1608").actual_part(
	  "Yageo", "RC0603JR-0710KL").actual_part(
	  "Panasonic", "ERJ-3GEYJ103V").actual_part(
	  "Rohm", "MCR03ERTJ103").actual_part(
	  "Rohm", "MCR03EZPJ103").actual_part(
	  "Stackpole", "RMCF0603JT10K0").actual_part(
	  "Bourns", "CR0603-JW-103ELF").actual_part(
	  "Samsung", "RC1608J103CS").actual_part(
	  "Bourns", "CR0603-JW-103GLF").actual_part(
	  "Rohm", "TRR03EZPJ103")
	self.choice_part("22K;1608", "IPC7351:RESC1608X55N", "",
	  "RES SMD 22K OHM 5% 1/10W 1608").actual_part(
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
	self.choice_part("100K;1608", "IPC7351:RESC1608X55N", "",
	  "RES SMD 100K OHM 5% 1/10W 1608").actual_part(
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
	  "Rohm", "MCR03ERTJ104").actual_part(
	  "Rohm", "KTR03EZPJ104")

	# Switches

	# Test Points:
	# (These need to be moved to `prices.py` on a per board basis):

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
	self.alias_part("BUS_SLAVE;M2X5S",
	  ["M2X5S;M2X5S"], "Pin_Header_Straight_2x05")

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
	  "MOSFET N-CH 200V DPAK").actual_part(
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

	# Now extract all of the actual parts:
	#print("-------------------------")
	actual_parts = self.actual_parts
	#vendor_parts = self.vendor_parts
	for schematic_part in self.schematic_parts.values():
	    #print("schematic_part: {0}".
	    #  format(schematic_part.schematic_part_name))
	    if isinstance(schematic_part, Choice_Part):
		choice_part = schematic_part
		for actual_part in choice_part.actual_parts:
		    actual_part_key = actual_part.key
		    if actual_part_key in actual_parts:
			print("'{0}' is a duplicate".format(actual_part_key))
		    else:
			actual_parts[actual_part_key] = actual_part
			#print("Insert Actual_Part '{0} {1}'".format(
			# actual_part.manufacturer_name,
			# actual_part.manufacturer_part_name))

		#print("schematic_part=", schematic_part)
		#assert False, "Deal with Fractional and Alias parts"
		pass
	#print("-------------------------")

	# Now we kludge in vendor part pricing:

	# Connectors:
	#self.vendor_part("Phoenix Contact", "1935161",
	#  "Digi-Key", "277-1667-ND",
	#  ".37/1 .352/10 .3366/50 .3274/100 .306/250 .28152/500 .255/1000")

	# Diodes:
	#self.vendor_part("Fairchild", "S320",
	#  "Digi-Key", "S320FSCT-ND",
	#  ".70/1 .614/10 .5424/25 .4726/100 .4114/250 .3502/500 .2805/1000")
	#self.vendor_part("Diodes Inc", "BAT54-7-F",
	#  "Digi-Key", "BAT54-FDICT-ND",
	#  ".15/1 .142/10 .128/25 .0927/100 .0546/250 .0453/500 .0309/1000")
	  
	# Holes:
	#self.vendor_part("McMaster-Carr", "3MM_Hole",
	#  "MMC", "123", "0./1")

	# Integrated Circuits:
	#self.vendor_part("TI", "SN74LVC1G175DBVR",
	#  "Digi-Key", "296-17617-1-ND",
	#  ".40/1 .315/10 .266/25 .2166/100 .1794/250 .1482/500 .1236/750")
	#self.vendor_part("Fairchild", "MM74HCT08MX",
	#  "Digi-Key", "MM74HCT08MXCT-ND",
	#  ".49/1 .412/10 .3612/25 .309/100 .268/250 .227/500 .175/1000")

	# LED's:
	#self.vendor_part("Cree", "CXA3050-0000-000N0HW440F",
	#  "Digi-Key", "CXA3050-0000-000N0HW440F-ND",
	#  "36./1 34.2/10 33.23/50 30.6/100 27.83/200 26.06/500 24/1000")

	# Resistors:
	#self.vendor_part("Vishay Dale", "CRCW060322K0JNEA",
	#  "Digi-Key", "541-22KGCT-ND",
	#  ".074/10 .04/50 .02295/200 .01566/1000")

    def alias_part(self,
      schematic_part_name, alias_part_names, kicad_footprint=""):
	""" *Database*: Create *Alias_Part* named *schematic_part_name* and
`	    containing *alias_names* and stuff it into *self*. """

	# Verify argument types:
	assert isinstance(schematic_part_name, str)
	assert isinstance(alias_part_names, list)
	for alias_part_name in alias_part_names:
	    assert isinstance(alias_part_name, str)

	# Lookup each *alias_name* in *alias_names* and tack it
	# onto *alias_parts*:
	schematic_parts = self.schematic_parts
	alias_parts = []
	for alias_part_name in alias_part_names:
	    if alias_part_name in schematic_parts:
		schematic_part = schematic_parts[alias_part_name]
		assert isinstance(schematic_part, Schematic_Part)
		alias_parts.append(schematic_part)
	    else:
		print("Part '{0}' not found for for alias '{1}'".
		  format(alias_part_name, schematic_part_name))

	# Create and return the new *alias_part*:
	alias_part = Alias_Part(schematic_part_name, \
	  alias_parts, kicad_footprint)
	return self.insert(alias_part)

    def choice_part(self,
      schematic_part_name, kicad_footprint, location, description):
	""" *Database*: Add a *Choice_Part* to *self*. """

	# Make sure we do not have a duplicate:
	schematic_parts = self.schematic_parts
	if schematic_part_name in schematic_parts:
	    print("'{0}' is duplicated".format(schematic_part_name))

	#if kicad_footprint.find(':') < 0:
	#    print("part '{0}' has no associated library in footprint '{1}'".
	#      format(schematic_part_name, kicad_footprint))

	choice_part = Choice_Part(schematic_part_name,
	  kicad_footprint, location, description)

	return self.insert(choice_part)

    def dump(self, out_stream):
	""" *Database*: Output the *Database* object (i.e. *self*) out to *out_stream*
	    in human readable form.
	"""

	# Verify argument types:
	assert isinstance(out_stream, file);

	vendor_parts_cache = self.vendor_parts_cache
	actual_keys = sorted(vendor_parts_cache.keys())
	for actual_key in actual_keys:
	    out_stream.write("{0}:\n".format(actual_key))
	    vendor_parts = vendor_parts_cache[actual_key]
	    for vendor_part in vendor_parts:
		vendor_part.dump(out_stream, 2);
	    out_stream.write("\n")

    def exchange_rate(self, from_currency, to_currency):
	""" *Database*: Lookup current currency exchange rate:
	"""

	# Verify argument types:
	assert isinstance(from_currency, str)
	assert isinstance(to_currency, str)

	# The documenation for this API can be found at:
	#    https://currency-api.appspot.com/

	# First construct the *exchange_url*:
	exchange_url = \
	  "https://currency-api.appspot.com/api/{0}/{1}.json".format(
	    from_currency, to_currency)
	#print("exchange_url='{0}'".format(exchange_url))

	# Now fetch the infromation from the server:
	exchange_response = requests.get(exchange_url)
	exchange_text = \
	  exchange_response.text.encode("ascii", "ignore").strip(" \n")
	#print("exchange_text='{0}'".format(exchange_text))

	# Now extract the exchange rate and return it:
	exchange_information = json.loads(exchange_text)
	#print("exchange_information=", exchange_information)
	return exchange_information["rate"]

    def findchips_scrape(self, actual_part):
	""" *Database*: Return a list of *Vendor_Parts* associated with
	    *actual_part* scraped from the findchips.com web page.
	"""

	# Verify argument types:
	assert isinstance(actual_part, Actual_Part)


	# Grab some values from *actual_part*:
	manufacturer_name =      actual_part.manufacturer_name
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
	  
	#if trace:
	#    print(findchips_tree.prettify())

	# We use regular expressions to strip out unnecessary characters
	# in numbrers:
	digits_only_re = re.compile("\D")

	# Result is returned in *vendor_parts*:
	vendor_parts = []

	# Currently, there is a <div class="distributor_results"> tag for
	# each distributor:
	for distributor_tree in findchips_tree.find_all("div",
	  class_="distributor-results"):
	    #if trace:
	    #	print("**************************************************")
	    #	print(distributor_tree.prettify())

	    # The vendor name is burried in:
	    #   <h3 class="distributor-title"><a ...>vendor name</a></h3>:
	    vendor_name = None
	    for h3_tree in distributor_tree.find_all(
	      "h3", class_="distributor-title"):
		#print("&&&&&&&&&&&&&&&&&&&&&&&")
		#print(h3_tree.prettify())
		for a_tree in h3_tree.find_all("a"):
		    vendor_name = a_tree.get_text(). \
		      encode("ascii", "ignore").strip(" \n")

		    # Strip some boring stuff off the end of *vendor_name*:
		    if vendor_name.endswith("Authorized Distributor"):
			# Remove "Authorized Distributor" from end
			# of *vendor_name*:
			vendor_name = vendor_name[:-22].strip(" ")
		    if vendor_name.endswith("Member"):
			# Remove "Member" from end of *vendor_name*:
			vendor_name = vendor_name[:-6].strip(" ")
		    if vendor_name.endswith("ECIA (NEDA)"):
			# Remove "ECIA (NEDA)" from end of *vendor_name*:
			vendor_name = vendor_name[:-11].strip(" ")

	    # If we can not extact a valid *vendor_name* there is no
	    # point in continuing to work on this *distributor_tree*:
	    if vendor_name == None:
		continue

	    # Extract *currency* from *distributor_tree*:
	    currency = "USD"
	    try:
		currency = distributor_tree["data-currencycode"]
	    except:
		pass

	    # All of the remaining information is found in <table>...</table>:
	    for table_tree in distributor_tree.find_all("table"):
		#print(table_tree.prettify())

		# There two rows per table.  The first row has the headings
		# and the second row has the data.  The one with the data
		# has a class of "row" -- <row clase="row"...> ... </row>:
		for row_tree in table_tree.find_all("tr", class_="row"):
		    if trace:
			print("==============================================")
			#print(row_tree.prettify())
	
		    # Now we grab the *vendor_part_name*.  Some vendors
		    # (like Arrow) use the *manufacturer_part_name* as their
		    # *vendor_part_name*.  The data is in:
		    #     <span class="additional-value"> ... </span>:
		    vendor_part_name = manufacturer_part_name
		    for span1_tree in row_tree.find_all(
		      "span", class_="td-desc-distributor"):
			#print(span1_tree.prettify())
			for span2_tree in span1_tree.find_all(
			  "span", class_="additional-value"):
			    # Found it; grab it, encode it, and strip it:
			    vendor_part_name = span2_tree.get_text(). \
			      encode("ascii", "ignore").strip(" \n")

		    # The *stock* count is found as:
		    #    <td class="td-stock">stock</td>
		    stock = 0
		    stock_tree = row_tree.find("td", class_="td-stock")
		    if stock_tree != None:
			# Strip out commas, space, etc.:
			stock_text = \
			  digits_only_re.sub("", stock_tree.get_text())
			# Some sites do not report stock, and leave them
			# empty.  We just leave *stock* as zero in this case:
 			if len(stock_text) != 0:
			    stock = int(stock_text)

		    # The *manufacturer_name* is found as:
		    #    <td class="td-mfg"><span>manufacturer_name</span></td>
		    manufacturer_name = ""
		    for mfg_name_tree in row_tree.find_all(
		      "td", class_="td-mfg"):
			for span_tree in mfg_name_tree.find_all("span"):
			    # Found it; grab it, encode it, and strip it:
			    manufacturer_name = span_tree.get_text(). \
			      encode("ascii", "ignore").strip(" \n")

		    # The *manufacturer_part_name* is found as:
		    #    <td class="td_part"><a ...>mfg_part_name</a></td>
		    manufacturer_part_name = ""
		    for mfg_part_tree in row_tree.find_all(
		      "td", class_="td-part"):
			for a_tree in mfg_part_tree.find_all("a"):
			    # Found it; grab it, encode it, and strip it:
			    manufacturer_part_name = a_tree.get_text(). \
			      encode("ascii", "ignore").strip(" \n")

		    # The price breaks are encode in a <ul> tree as follows:
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
		    if price_list_tree != None:
			for li_tree in price_list_tree.find_all("li"):
			    quantity_tree = li_tree.find("span", class_="label")
			    price_tree = li_tree.find("span", class_="value")
			    if quantity_tree != None and price_tree != None:
				# We extract *quantity*:
			        quantity_text = digits_only_re.sub("",
				  quantity_tree.get_text())
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
				rate = 1.0
				if currency == "USD":
				    exchange_rate = 1.0
				elif currency == "EUR":
				    exchange_rate = \
				      self.euro_to_dollar_exchange_rate
				elif currency == "GBP":
				    exchange_rate = \
				      self.pound_to_dollar_exchange_rate
				else:
				    assert False, \
				      "Unrecognized currency '{0}'". \
				      format(currency)

				# Sometimes we get a bogus price of 0.0 and
				# we just need to ignore the whole record:
				if price > 0.0:
				    price_break = Price_Break(
				      quantity, price * exchange_rate)
				    price_breaks.append(price_break)

		    # Now if we have an exact match on the *manufacturer_name*
		    # we can construct the *vendor_part* and append it to
		    # *vendor_parts*:
		    if original_manufacturer_part_name == \
		      manufacturer_part_name:
			now = time.time()
			vendor_part = Vendor_Part(actual_part,
			  vendor_name, vendor_part_name,
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
				  format(price_break.quantity,
				  price_break.price, currency))

	# For debugging, let the user now that we are looking for a
	# part and not finding it at all:
	if len(vendor_parts) == 0:
       	    print("**********Find '{0}:{1}': {2} matches".
	      format(actual_part.manufacturer_name,
	      actual_part.manufacturer_part_name, len(vendor_parts)))

	return vendor_parts

    def fractional_part(self, schematic_part_name, kicad_footprint,
      whole_part_name, numerator, denominator, description):
	""" *Database*: Insert a new *Fractional_Part* named
	    *schematic_part_name* and containing *whole_part_name*,
	    *numerator*, *denominator*, and *description* in to the
	    *Database* object (i.e. *self*.) """

	# Verify argument types:
	assert isinstance(schematic_part_name, str)
	assert isinstance(kicad_footprint, str)
	assert isinstance(whole_part_name, str)
	assert isinstance(numerator, int)
	assert isinstance(denominator, int)
	assert isinstance(description, str)

	schematic_parts = self.schematic_parts
	if whole_part_name in schematic_parts:
	    whole_part = schematic_parts[whole_part_name]

	    # Verify argument types:
	    fractional_part = Fractional_Part(schematic_part_name,
	      kicad_footprint, whole_part, numerator, denominator, description)
	    self.insert(fractional_part)
	else:
	    print("Whole part '{0}' not found for fractional part '{1}'!".
	      format(whole_part_name, schematic_part_name))

    def lookup(self, schematic_part_name):
	""" *Database*: Return the *Schematic_Part* associated with
	    *schematic_part_name*. """

	assert isinstance(schematic_part_name, str)

	schematic_part = None
	schematic_parts = self.schematic_parts
	if schematic_part_name in schematic_parts:
	    schematic_part = schematic_parts[schematic_part_name]
	return schematic_part

    def insert(self, schematic_part):
	""" *Database*: Add a *Schematic_Part* to *self*. """

	# Verify argument_types:
	assert isinstance(schematic_part, Schematic_Part)

	schematic_part_name = schematic_part.schematic_part_name
	schematic_parts = self.schematic_parts
	if schematic_part_name in schematic_parts:
	    print("{0} is being inserted into database more than once".
	     format(schematic_part_name))
	else:
	    schematic_parts[schematic_part_name] = schematic_part
	return schematic_part

    def save(self):
	""" *Database*: Save the *vendor_parts* portion of the *Database*
	    object (i.e. *self*).
	"""

	#print("=>Database.save")

	vendor_parts_cache = self.vendor_parts_cache
	for vendor_parts in vendor_parts_cache.values():
	    assert isinstance(vendor_parts, list)
	    for vendor_part in vendor_parts:
		assert isinstance(vendor_part, Vendor_Part)

	bom_pickle_file = open(self.bom_parts_file_name, "w")
	pickle.dump(self.vendor_parts_cache, bom_pickle_file)
	bom_pickle_file.close()

	#print("<=Database.save")

    def vendor_part(self, manufacturer_name, manufacturer_part_name,
      vendor_name, vendor_part_name, price_break_text):
	""" *Database*: Add a vendor part to the database. """

	# Verify argument types:
	assert isinstance(manufacturer_name, str)
	assert isinstance(manufacturer_part_name, str)
	assert isinstance(vendor_name, str)
	assert isinstance(vendor_part_name, str)
	assert isinstance(price_break_text, str)

	# Parse *price_break_text* int a list of *Price_Break*'s:
	price_breaks = []
	breaks_text = price_break_text.split()
	for break_text in breaks_text:
	    cost_quantity_pair = break_text.split("/")
	    price_break = Price_Break(int(cost_quantity_pair[1]),
	      float(cost_quantity_pair[0]))
	    price_breaks.append(price_break)

	actual_part_key = (manufacturer_name, manufacturer_part_name)
	actual_parts = self.actual_parts
	if actual_part_key in actual_parts:
	    actual_part = actual_parts[actual_part_key]
	    vendor_part_key = (vendor_name, vendor_part_name)
	    vendor_parts = self.vendor_parts
	    if vendor_part_key in vendor_parts:
		print("Vendor Part: '{0} {1}' is duplicated in database". \
		  format(vendor_name, vendor_part_name))
	    else:
		vendor_part = Vendor_Part(actual_part,
		 vendor_name, vendor_part_name, 10000, price_breaks)
		vendor_parts[vendor_part_key] = vendor_part
	else:
		print("Actual Part: '{0} {1}' is not in database". \
		  format(manufacturer_name, manufacturer_part_name))

class Order:
    # An Order consists of a list of boards to orders parts for.
    # In addition, the list of vendors to exclude from the ordering
    # process is provided as well.  Vendors are excluded because the
    # shipping costs exceed the part cost savings.  Finally, sometimes
    # you want to order extra stuff, so there is a mechanism for that
    # as well.  Sometimes, you have previous inventory, so that is
    # listed as well.

    def __init__(self, database):
	""" *Order*: Initialize *self* for an order. """

	assert isinstance(database, Database)

	self.boards = []	  # List[Board]: Boards	
	self.excluded_vendor_names = {} # Dict[String]: Excluded vendors
	self.requests = []	  # List[Request]: Additional requested parts
	self.inventories = []	  # List[Inventory]: Existing inventoried parts
	self.database = database

    def board(self, name, revision, net_file_name, count):
	""" *Order*: Create a *Board* containing *name*, *revision*,
	    *net_file_name* and *count*. """

	# Verify argument types:
	assert isinstance(name, str)
	assert isinstance(revision, str)
	assert isinstance(net_file_name, str)
	assert isinstance(count, int)

	# Create the *Board*:
	board = Board(name, revision, net_file_name, count, self)
	self.boards.append(board)
	return board

    def bom_write(self, bom_file_name, key_function):
	""" *Order*: Write out the BOM (Bill Of Materials) for the
	    *Order* object (i.e. *self*) to *bom_file_name* ("" for stdout)
	    using *key_function* to provide the sort key for each
	    *Choice_Part*.
	"""

	# Verify argument types:
	assert isinstance(bom_file_name, str)

	# Grab *database* and *vendors*:
	database = self.database
	excluded_vendor_names = self.excluded_vendor_names

	# Open *bom_file*
	bom_file = sys.stdout
	if bom_file_name != "":
	    bom_file = open(bom_file_name, "wa")

	# Sort *final_choice_parts* using *key_function*.
	final_choice_parts = self.final_choice_parts
	final_choice_parts.sort(key= key_function)

	# Now generate a BOM summary:
	total_cost = 0.0
	for choice_part in final_choice_parts:
	    # Make sure that nonething nasty got into *final_choice_parts*:
	    assert isinstance(choice_part, Choice_Part)

	    # Sort the *board_parts* by *board* followed by reference:
	    board_parts = choice_part.board_parts
	    board_parts.sort(key = lambda board_part:
	      (board_part.board.name, board_part.reference.upper(),
	       int(filter(str.isdigit, board_part.reference))))

	    # Write the first line out to *bom_file*:
	    bom_file.write("  {0}:{1};{2} {3}:{4}\n".\
	      format(choice_part.schematic_part_name,
	      choice_part.kicad_footprint, choice_part.description,
	      choice_part.count_get(), choice_part.references_text_get()))

	    # Select the vendor_part and associated quantity/cost
	    choice_part.select(excluded_vendor_names, True)
	    selected_actual_part = choice_part.selected_actual_part
	    selected_vendor_part = choice_part.selected_vendor_part
	    selected_order_quantity = choice_part.selected_order_quantity
	    selected_total_cost = choice_part.selected_total_cost
	    selected_price_break_index = choice_part.selected_price_break_index

	    if isinstance(selected_vendor_part, Vendor_Part):
		# Grab the *vendor_name*:
		assert isinstance(selected_vendor_part, Vendor_Part)
		vendor_name = selected_vendor_part.vendor_name

		# Show the *price breaks* on each side of the
		# *selected_price_breaks_index*:
		price_breaks = selected_vendor_part.price_breaks
		#print("len(price_breaks)={0} selected_price_break_index={1}".
		#  format(len(price_breaks), selected_price_break_index))
		selected_price_break = price_breaks[selected_price_break_index]
		minimum_index = max(selected_price_break_index - 1, 0)
	        maximum_index = \
		  min(selected_price_break_index + 2, len(price_breaks))
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
		bom_file.write("    {0}:{1} [{2}: {3}] {4}\n".
		  format(selected_vendor_part.vendor_name,
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

    def csv_write(self):
	""" *Order*: Write out the *Order* object (i.e. *self) BOM (Bill Of Materials)
	    for each vendor as a .csv (Comma Seperated Values).
	"""

	# Grab *database* and *vendors*:
	database = self.database
	excluded_vendor_names = self.excluded_vendor_names

	# Sort *final_choice_parts* using *key_function*.
	final_choice_parts = self.final_choice_parts
	final_choice_parts.sort(key = lambda choice_part:
	  (choice_part.selected_vendor_name,
	  choice_part.selected_total_cost,
	  choice_part.schematic_part_name) )

	vendor_boms = {}
	for choice_part in final_choice_parts:
	    assert isinstance(choice_part, Choice_Part)

	    # Sort the *board_parts* by *board* followed by reference:
	    board_parts = choice_part.board_parts
	    board_parts.sort(key = lambda board_part:
	      (board_part.board.name, board_part.reference.upper(),
	       int(filter(str.isdigit, board_part.reference))))

	    # Select the vendor_part and associated quantity/cost
	    choice_part.select(excluded_vendor_names, True)
	    selected_actual_part = choice_part.selected_actual_part
	    selected_vendor_part = choice_part.selected_vendor_part
	    selected_order_quantity = choice_part.selected_order_quantity

	    if isinstance(selected_vendor_part, Vendor_Part):
		# Grab the *vendor_name* and *vendor_part_name*:
		assert isinstance(selected_vendor_part, Vendor_Part)
		vendor_name = selected_vendor_part.vendor_name
		vendor_part_name = selected_vendor_part.vendor_name

		# Make sure we have a *vendor_bom* line list:
		if not vendor_name in vendor_boms:
		    vendor_boms[vendor_name] = []
		lines = vendor_boms[vendor_name]

		# Create *line* and append it to *vendor_bom*:
		line = "{0},{1},{2},{3},{4}".format(
		  selected_order_quantity,
		  selected_vendor_part.vendor_part_name,
		  selected_actual_part.manufacturer_name,
		  selected_actual_part.manufacturer_part_name,
		  choice_part.schematic_part_name)
		lines.append(line)

	# Wrap up the *bom_file*:
	for vendor_name in vendor_boms.keys():
	    # Open *csv_file*:
	    csv_file_name = "/tmp/{0}.csv".format(vendor_name)
	    print("Opening '{0}' for writing".format(csv_file_name))
            csv_file = open(csv_file_name, "w")
	    
	    # Write out each line in *lines*:
	    lines = vendor_boms[vendor_name]
	    for line in lines:
		csv_file.write(line)
		csv_file.write("\n")
	
	    # Close *csv_file*:
	    csv_file.close()

    def exclude_vendors_to_reduce_shipping_costs(self,
      choice_parts, excluded_vendor_names, reduced_vendor_messages):
	""" *Order*: Sweep through *choice_parts* and figure out which vendors
	    to add to *excluded_vendor_names* to reduce shipping costs.
	"""

	# Verify argument types:
	assert isinstance(choice_parts, list)
	assert isinstance(excluded_vendor_names, dict)
	assert isinstance(reduced_vendor_messages, list)

	# First figure out the total *missing_parts*.  We will stop if
	# excluding a vendor increases above the *missing_parts* number:
	quad = \
	  self.quad_compute(choice_parts, excluded_vendor_names, "")
	missing_parts = quad[0]

	# Sweep through and figure out what vendors to order from:
	done = False
	while not done:
	    # Get the base cost for the current *excluded_vendor_names*:
	    base_quad = \
	      self.quad_compute(choice_parts, excluded_vendor_names, "")
	    #print("base_quad={0}".format(base_quad))

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
	    base_vendor_names = \
	      self.vendor_names_get(choice_parts, excluded_vendor_names)
	    assert isinstance(base_vendor_names, tuple)
	    #print("base: {0} {1}".format(base_cost, base_vendor_names))

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
		trial_quad = self.quad_compute(choice_parts,
		  trial_excluded_vendor_names, vendor_name)
		trial_quads.append(trial_quad)

		# For debugging only:
		#trial_cost = trial_quad[0]
		#trial_vendor_name = trial_quad[1]
		#print("    {0:.2f} with {1} excluded".
		#  format(trial_cost, trial_vendor_name))

	    # Sort the *trial_quads* to bring the most interesting one to the
	    # front:
	    trial_quads.sort()
	    # For debugging:
	    #for trial_quad in trial_quads:
	    #	print("   {0}".format(trial_quad))

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
		    reduced_vendor_messages.append("Excluding '{0}': saves nothing\n".
		      format(lowest_vendor_name, savings))
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
	    savings = lowest_cost - base_cost
	    #print("      Lowest {0} with {1} exlcuded".
	    #  format(lowest_cost, lowest_vendor_name))

	    # We use $5.00 as an approximate minimum shipping cost.
	    # If the savings is less that the shipping cost, we exclude
	    # the vendor:
	    if savings < 5.0 and len(trial_quads) >= 2 and lowest_vendor_name != "Digi-Key":
		# The shipping costs are too high and there at lease one
		# vendor left; exclude this vendor:
		reduced_vendor_messages.append("Excluding '{0}': only saves {1:.2f}\n".
		  format(lowest_vendor_name, savings))
		excluded_vendor_names[lowest_vendor_name] = None
	    else:
		# We are done when *lowest_quad* is worth shipping:
		#print("lowest_cost={0:.2f}".format(lowest_cost))
		done = True

    def exclude_vendors_with_high_minimums(self,
      choice_parts, excluded_vendor_names, reduced_vendor_messages):
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

    def final_choice_parts_compute(self):
	""" *Order*: Return a list of final *Choice_Part* objects to order
	    for the the *Order* object (i.e. *self*).  This routine also
	    has the side effect of looking up the vendor information for
	    each selected *Choice_Part* object.
	"""

	# Grab the *boards* and *database*:
	boards = self.boards
	database = self.database

	# Sort *boards* by name (not really needed, but why not?):
	boards.sort(key = lambda board:board.name)

	# Visit each *board* in *boards* to locate the associated
	# *Choice_Part* objects.  We want to eliminate duplicate
	# *Choice_Part* objects, so we use *choice_parts_table* to
	# eliminate duplicates.
	choice_parts_table = {}
	for board in boards:
	    #print("Order.final_choice_parts_compute(): board:{0}".format(board.name))
	
	    # Sort *board_parts* by reference.  A reference is a sequence
	    # letters followed by an integer (e.g. SW1, U12, D123...)
	    # Sort alphabetically followed by numerically.  The lambda
	    # expression converts "SW123" into ("SW", 123).  
	    board_parts = board.all_board_parts
	    board_parts.sort(key = lambda board_part:
	      (    filter(str.isalpha, board_part.reference).upper(),
	       int(filter(str.isdigit, board_part.reference)) ))

	    # Visit each *board_part* in *board_parts*:
	    for board_part in board_parts:
		schematic_part = board_part.schematic_part
		schematic_part_name = schematic_part.schematic_part_name
		#print("Order.final_choice_parts_compute():  {0}: {1}".
		#  format(board_part.reference, schematic_part_name))

		# Only *choice_parts* can be ordered from a vendor:
		# Visit each *choice_part* in *choice_parts* and
		# load it into *choice_parts_table*:
		choice_parts = schematic_part.choice_parts()
		for choice_part in choice_parts:
		    # Do some consistency checking:
		    assert isinstance(choice_part, Choice_Part), \
		      "Not a choice part '{0}'".format(choice_part_name)

		    # Make sure *choice_part* is in *choice_parts_table*
		    # exactly once:
		    choice_part_name = choice_part.schematic_part_name
		    if not choice_part_name in choice_parts_table:
			choice_parts_table[choice_part_name] = choice_part
		    #	print(("Order.final_choice_parts_compute():" +
		    #	  " Insert {0:s} into table under key {1} (size={2})").format(
		    #	  choice_part, choice_part_name, len(choice_parts_table)))
		    #else:
                    #    print("Order.final_choice_parts_compute(): Key {0} in table".format(
		    #	  choice_part_name))

		    # Remember *board_part* in *choice_part*:
		    choice_part.board_part_append(board_part)

		    # Refresh the vendor part cache for each *actual_part*:
                    vendor_parts_cache = database.vendor_parts_cache
		    actual_parts = choice_part.actual_parts
		    for actual_part in actual_parts:
			# Check for errors:
			assert isinstance(actual_part, Actual_Part)

			# Get *vendor_parts* from the cache or from
			# a screen scrape:
			actual_key = actual_part.key
			if actual_key in vendor_parts_cache:
			    # Reuse cached *vendor_parts*:
			    vendor_parts = vendor_parts_cache[actual_key]
			else:
			    # Grab the *vendor* parts via a screen scrape:
			    vendor_parts = \
			      database.findchips_scrape(actual_part)
			    vendor_parts_cache[actual_key] = vendor_parts
			    database.save()

			for vendor_part in vendor_parts:
			    actual_part.vendor_part_append(vendor_part)

	# Save the *database* because we've loaded all of the *vendor_parts*'s:
	database.save()

	# Sort by *final_choice_parts* by schematic part name:
	final_choice_parts = list(choice_parts_table.values())
	final_choice_parts.sort(
	  key = lambda choice_part: choice_part.schematic_part_name)
	self.final_choice_parts = final_choice_parts

	# Sweep through *final_choice_parts* and force the associated
	# *Board_Part*'s to be in a reasonable order:
	for choice_part in final_choice_parts:
	    # Make sure that we only have *Choice_Part* objects:
	    assert isinstance(choice_part, Choice_Part)
	    choice_part.board_parts_sort()

	#for choice_part in final_choice_parts:
	#    print("End_Order.final_choice_parts_compute(): board:{0}".format(choice_part))

	return final_choice_parts

    def process(self):
	""" *Order*: Process the order. """

	#print("=>Order.process()")

	# Collect the messages from each vendor reduction operation into *reduced_vendor_messages*:
	reduced_vendor_messages = []

	# We need to contruct a list of *Choice_Part* objects.  This
        # will land in *final_choice_parts* below.   Only *Choice_Part*
	# objects can actually be ordered because they list one or
	# more *Actual_Part* objects to choose from.  Both *Alias_Part*
	# objects and *Fractional_Part* objects eventually get
	# converted to *Choice_Part* objects.  Once we have
	# *final_choice_parts* it can be sorted various different ways
	# (by vendor, by cost, by part_name, etc.)
	final_choice_parts = self.final_choice_parts_compute()

	# Now we winnow down the total number of vendors to order from
	# to 1) minimize the number of orders that can be messed up
	# (i.e. supply chain simplication) and to save shipping costs.
	# There are two steps -- throw out vendors with excessive minimum
	# order amounts followed by throwing out vendors where the savings
	# do not exceed additional shipping costs.
	excluded_vendor_names = self.excluded_vendor_names
	self.exclude_vendors_with_high_minimums(
	  final_choice_parts, excluded_vendor_names, reduced_vendor_messages)
	self.exclude_vendors_to_reduce_shipping_costs(
	  final_choice_parts, excluded_vendor_names, reduced_vendor_messages)

	# Write out *reduced_vendor_messages* to a report file:
	reduced_vendor_messages_file_name = "/tmp/vendor_reduction_report.txt"
	reduced_vendor_messages_file = open(reduced_vendor_messages_file_name, "w")
	for reduced_vendor_message in reduced_vendor_messages:
            reduced_vendor_messages_file.write(reduced_vendor_message)
	reduced_vendor_messages_file.close()
	print("{0} vendors eliminated.  See '{1}' file for why".
	  format(len(reduced_vendor_messages), reduced_vendor_messages_file_name))

	# Print out the final selected vendor summary:
	self.summary_print(final_choice_parts, excluded_vendor_names)

	# Generate the bom file reports for *self.final_choice_parts*:
	self.bom_write("bom_by_price.txt", lambda choice_part:
	  (choice_part.selected_total_cost,
	  choice_part.selected_vendor_name,
	  choice_part.schematic_part_name) )
	self.bom_write("bom_by_vendor.txt", lambda choice_part:
	  (choice_part.selected_vendor_name,
	  choice_part.selected_total_cost,
	  choice_part.schematic_part_name) )
	self.bom_write("bom_by_name.txt", lambda choice_part:
	  (choice_part.schematic_part_name,
	  choice_part.selected_vendor_name,
	  choice_part.selected_total_cost) )
	self.csv_write()

	
	# Write a part summary file for each board:
	for board in self.boards:
	    board.assembly_summary_write(final_choice_parts)

	# Now generate a BOM summary:
	if False:
	    total_cost = 0.0
	    for choice_part in final_choice_parts:
		# Open *csv_file* for summary spread sheet:
		csv_file = open("/tmp/order.csv", "wa")
		# Output a one line header
		csv_file.write("Quantity,Vendor Part Name,Reference\n")

		# Select the vendor_part and associated quantity/cost
		choice_part.select(excluded_vendor_names, False)
		selected_actual_part = choice_part.selected_actual_part
		selected_vendor_part = choice_part.selected_vendor_part
		selected_order_quantity = choice_part.selected_order_quantity
		selected_total_cost = choice_part.selected_total_cost
		selected_price_break_index = \
		  choice_part.selected_price_break_index

	    # Per vendor order lists need some more thought:
	    if isinstance(selected_vendor_part, Vendor_Part):
		vendor_name = selected_vendor_part.vendor_name
		if not vendor_name in vendor_files:
		    csv_file = open("{0}.csv".format(vendor_name), "wa")
		    vendor_files[vendor_name] = csv_file
		else:
		    csv_file = vendor_files[vendor_name]

		# Print out the *price breaks* on each side of the
		# *selected_price_breaks_index*:
		price_breaks = selected_vendor_part.price_breaks
		#print("len(price_breaks)={0} selected_price_break_index={1}".
		#  format(len(price_breaks), selected_price_break_index))
		selected_price_break = price_breaks[selected_price_break_index]
		minimum_index = max(selected_price_break_index - 1, 0)
	        maximum_index = \
		  min(selected_price_break_index + 2, len(price_breaks))
		price_breaks = price_breaks[minimum_index: maximum_index]
		
		# Compute the *price_breaks_text*:
		price_breaks_text = ""
		for price_break in price_breaks[minimum_index: maximum_index]:
		    price_breaks_text += "{0}/${1:.3f} ".format(
		      price_break.quantity, price_break.price)

		# Print out the line:
		#print("    {0}:{1} {2}".format(
		#  selected_vendor_part.vendor_name,
		#  selected_vendor_part.vendor_part_name, price_breaks_text))

		# Print out the result:
		#print("        {0}@({1}/${2:.3f})={3:.2f}".format(
		#  selected_order_quantity,
		#  selected_price_break.quantity, selected_price_break.price,
		#  selected_total_cost))

		total_cost += selected_total_cost

		# Write out another line in the *csv_file*:
		csv_file.write("{0},{1},{2}\n".format(
		  selected_order_quantity,
		  selected_vendor_part.vendor_part_name,
		  choice_part.schematic_part_name))

	    # Close all the vendor files:
	    for csv_file in vendor_files.values():
	        csv_file.close()

	#print("<=Order.process()")


    def quad_compute(self,
      choice_parts, excluded_vendor_names, excluded_vendor_name, trace=False):
	""" *Order*: Return quad tuple of the form:
	       (*missing_parts*, *total_cost*,
		*vendor_priority*, *excluded_vendor_name*) where:
	    * *missing_parts* is number of parts that can not be fullfilled.
	    * *total_cost* is the sum the parts costs for all *Choice_Part*
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
	      [choice_part.schematic_part_name for choice_part in choice_parts],
	      excluded_vendor_names.keys(), excluded_vendor_name))

	# Verify argument types:
	assert isinstance(choice_parts, list)
	assert isinstance(excluded_vendor_names, dict)
	assert isinstance(excluded_vendor_name, str)
	assert isinstance(trace, bool)

	missing_parts = 0
	total_cost = 0.0
	for choice_part in choice_parts:
	    # Make sure *choice_part* is actually a *Choice_Part*:
	    assert isinstance(choice_part, Choice_Part)

	    # Perform the vendor selection excluding all vendors in
	    # *excluded_vendor_names*:
	    missing_parts += choice_part.select(excluded_vendor_names, False)

	    # Grab some values out of *choice_part*:
	    selected_vendor_name = choice_part.selected_vendor_name
	    selected_total_cost = choice_part.selected_total_cost
		
	    # Keep a running total of everything:
	    total_cost += selected_total_cost

	# Figure out *vendor_priority* for *excluded_vendor_name*:
	database = self.database
	vendor_priorities = database.vendor_priorities
	if excluded_vendor_name in vendor_priorities:
	    # Priority already assigned to *excluded_vendor_name*:
	    vendor_priority = vendor_priorities[excluded_vendor_name]
	else:
	    # Assigned a new priority for *excluded_vendor_name*:
	    vendor_priority = database.vendor_priority
	    vendor_priorities[excluded_vendor_name] = vendor_priority
	    database.vendor_priority = vendor_priority + 1

	# Return the final *quad*:
	quad = \
	  (missing_parts, total_cost, vendor_priority, excluded_vendor_name)

	# *trace* for debugging:
	if trace:
	    print("<=quad_compute({0}, {1}, '{2}')=>{3}".format(
	      [choice_part.schematic_part_name for choice_part in choice_parts],
	      excluded_vendor_names.keys(), excluded_vendor_name, quad))

	return quad

    def request(self, name, amount):
	""" *Order*: Request *amount* parts named *name*. """

	assert isinstance(name, str)
	assert isinstance(amount, int)
	inventory = Inventory(name, str)

	final_vendor_names = \
	  self.vendor_names_get(final_choice_parts, excluded_vendor_names)
	print("Final selected vendors:")
	for vendor_name in final_vendor_names:
	    print("    {0}".format(vendor_name))

	# Print the fianl *total_cost*:
	total_cost = 0.0
	for choice_part in final_choice_parts:
	    choice_part.select(excluded_vendor_names, False)
	    total_cost += choice_part.selected_total_cost
	print("Total Cost: {0}".format(total_cost))

    def summary_print(self, choice_parts, excluded_vendor_names):
	""" *Order*: Print a summary of the selected vendors.
	"""

	# Verify argument types:
	assert isinstance(choice_parts, list)
	assert isinstance(excluded_vendor_names, dict)

	# Let the user know what we winnowed the vendor list down to:
	final_vendor_names = \
	  self.vendor_names_get(choice_parts, excluded_vendor_names)
	print("Final selected vendors:")
	for vendor_name in final_vendor_names:
	    print("    {0}".format(vendor_name))

	# Print the final *total_cost*:
	total_cost = 0.0
	for choice_part in choice_parts:
	    choice_part.select(excluded_vendor_names, False)
	    total_cost += choice_part.selected_total_cost
	print("Total Cost: {0}".format(total_cost))

    def vendor_exclude(self, vendor_name):
	""" *Order*: Exclude *vendor_name* from the *Order* object (i.e. *self*)
	"""

	# Verify argument typees:
	assert isinstance(vendor_name, str)

	# Mark *vendor_name* from being selectable:
	self.excluded_vendor_names[vendor_name] = None

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

class Request:
    def __init__(self, schematic_part, amount):
	""" *Request*: Create *Request* containing *schematic_part*
	    and *amount*. """
	assert isinstance(schematic_part, Schematic_Part)
	assert isinstance(amount, int)
	self.schematic_part = schematic_part
	self.amount = amount
    
class Inventory:
    def __init__(self, schematic_part, amount):
	""" *Inventory*: Initialize *self* to contain *scheamtic_part* and
	    *amount*. """

	# Verify argument types:
	assert isinstance(schematic_part, Schematic_Part)
	assert isinstance(amount, int)

	# Load up *self*:
	self.schematic_part = schematic_part
	self.amount = amount

class Board:
    def __init__(self, name, revision, net_file_name, count, order):
	""" *Board*: Create a new board containing *name*, *revision*,
	    *net_file_name*, *count*. """

	# Verify argument types:
	assert isinstance(name, str)
	assert isinstance(revision, str)
	assert isinstance(net_file_name, str)
	assert isinstance(count, int)
	assert isinstance(order, Order)

	# Load up *self*:
	self.name = name
	self.revision = revision
	self.net_file_name = net_file_name
	self.count = count
	self.order = order
	self.all_board_parts = []	    # List[Board_Part] of all board parts
	self.installed_board_parts = []	    # List[Board_Part] board parts to be installed
	self.uninstalled_board_parts = []   # List[Board_Part] board parts not to be installed

	self.net_file_read()

    def board_part_append(self, board_part):
        """ *Board*: Append *board_part* onto the *Board* object (i.e. *self*). """

	# Verify argument types:
        assert isinstance(board_part, Board_Part)

	self.all_board_parts.append(board_part)
	if board_part.install:
            self.installed_board_parts.append(board_part)
	else:
            self.uninstalled_board_parts.append(board_part)

    def net_file_read(self):
	""" *Board*: Read in net file for {self}. """

	# Prevent accidental double read:
	board_parts = self.all_board_parts
	assert len(board_parts) == 0

	errors = 0

	# Read the contents *net_file_name* into *net_text*:
	net_file_name = self.net_file_name
	if net_file_name.endswith(".net"):
	    # Read contents of *net_file_name* in as a string *net_text*:
	    net_stream = open(net_file_name, "ra")
	    net_text = net_stream.read()
	    net_stream.close()

	    # Parse *net_text* into *net_se* (i.e. net S-expression):
	    net_se = sexpdata.loads(net_text)
	    #print("\nsexpedata.dumps=", sexpdata.dumps(net_se))
	    #print("")
	    #print("net_se=", net_se)
	    #print("")

	    # Visit each *component_se* in *net_se*:
	    net_file_changed = False
	    database = self.order.database
	    components_se = se_find(net_se, "export", "components")
	    #print("components=", components_se)
	    for component_se in components_se[1:]:
		#print("component_se=", component_se)
		#print("")

		# Grab the *reference* from *component_se*:
		reference_se = se_find(component_se, "comp", "ref")
		reference = reference_se[1].value()
		#print("reference_se=", reference_se)
		#print("")
	
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

		#print(reference, part_name, footprint)

		# Strip *comment* out of *part_name* if it exists:
		comment = ""
		colon_index = part_name.find(':')
		if colon_index >= 0:
		    comment = part_name[colon_index + 1:]
                    part_name = part_name[0:colon_index]

		# Now see if we have a match for *part_name* in *database*:
		schematic_part = database.lookup(part_name)
		if schematic_part == None:
		    # {part_name} is not in {database}; output error message:
		    print(("File '{0}: Part Name '{2}' {3}" +
		      " not in database").format(net_file_name, 0,
		      part_name, reference))
		    errors += 1
		else:
		    # We have a match; create the *board_part*:
                    board_part = Board_Part(self, schematic_part, reference, comment)
		    self.board_part_append(board_part)

                    # Grab *kicad_footprint* from *schematic_part*:
		    kicad_footprint = schematic_part.kicad_footprint

		    # Grab *footprint_se* from *component_se* (if it exists):
		    footprint_se = se_find(component_se, "comp", "footprint")
		    #print("footprint_se=", footprint_se)
		    #print("")

		    # Either add or update the footprint:
		    if footprint_se == None:
			# No footprint in the .net file; just add one:
			component_se.append(
			  [Symbol("footprint"), Symbol(kicad_footprint)])
			print("Part {0}: Adding binding to footprint '{1}'".
			  format(kicad_footprint))
			net_file_changed = True
		    else:
			# We have a footprint in .net file:
			previous_footprint = footprint_se[1].value()
			previous_split = previous_footprint.split(':')
			kicad_split = kicad_footprint.split(':')
			assert len(previous_split) > 0
			assert len(kicad_split) > 0
			new_footprint = previous_footprint
			if len(kicad_split) == 2:
			    # *kicad_footprint* has an explicit library,
			    # so we can just use it and ignore
			    # *previous_footprint*:
			    new_footprint = kicad_footprint
			elif len(kicad_split) == 1 and \
			  len(previous_split) == 2:
			    # *kicad_footprint* does not specify a library,
			    # but the *previous_footprint* does.  We build
			    # *new_foot_print* using the *previous_footprint*
			    # library and the rest from *kicad_footprint*:
			    new_footprint = \
			      previous_split[0] + ":" + kicad_footprint

			# Only do something if it changed:
			if previous_footprint != new_footprint:
			    # Since they changed, update in place:
			    #if isinstance(schematic_part, Alias_Part):
			    #	print("**Alias_Part.footprint={0}".
			    #	  format(schematic_part.kicad_footprint))
			    print(("Part '{0}': " + 
			      "Footprint changed from '{1}' to '{2}'").
			      format(part_name,
			      previous_footprint, new_footprint))
			    footprint_se[1] = Symbol(new_footprint)
			    net_file_changed = True

	    # Write out updated *net_file_name* if *net_file_changed*:
	    if net_file_changed:
		print("Updating '{0}' with new footprints".
		  format(net_file_name))
		net_file = open(net_file_name, "wa")
		#sexpdata.dump(net_se, net_file)
		net_se_string = sexpdata.dumps(net_se)
		#sexpdata.dump(net_se, net_file)

		# Now use some regular expressions to improve formatting to be more like
                # what KiCad outputs:
		net_se_string = re.sub(" \(design ", "\n  (design ", net_se_string)

		# Sheet part of file:
		net_se_string = re.sub(" \(sheet ",       "\n    (sheet ",         net_se_string)
		net_se_string = re.sub(" \(title_block ", "\n      (title_block ", net_se_string)
		net_se_string = re.sub(" \(title ",       "\n        (title ",     net_se_string)
		net_se_string = re.sub(" \(company ",     "\n        (company ",   net_se_string)
		net_se_string = re.sub(" \(rev ",         "\n        (rev ",       net_se_string)
		net_se_string = re.sub(" \(date ",        "\n        (date ",      net_se_string)
		net_se_string = re.sub(" \(source ",      "\n        (source ",    net_se_string)
		net_se_string = re.sub(" \(comment ",     "\n        (comment ",   net_se_string)

                # Components part of file:
		net_se_string = re.sub(" \(components ", "\n  (components ",    net_se_string)
		net_se_string = re.sub(" \(comp ",       "\n    (comp ",        net_se_string)
		net_se_string = re.sub(" \(value ",      "\n      (value ",     net_se_string)
		net_se_string = re.sub(" \(footprint ",  "\n      (footprint ", net_se_string)
		net_se_string = re.sub(" \(libsource ",  "\n      (libsource ", net_se_string)
		net_se_string = re.sub(" \(sheetpath ",  "\n      (sheetpath ", net_se_string)
		net_se_string = re.sub(" \(path ",       "\n      (path ",      net_se_string)
		net_se_string = re.sub(" \(tstamp ",     "\n      (tstamp ",    net_se_string)

                # Library parts part of file
		net_se_string = re.sub(" \(libparts ",    "\n  (libparts ",    net_se_string)
		net_se_string = re.sub(" \(libpart ",     "\n    (libpart ",   net_se_string)
		net_se_string = re.sub(" \(description ", "\n      (description ",  net_se_string)
		net_se_string = re.sub(" \(fields ",      "\n      (fields ",  net_se_string)
		net_se_string = re.sub(" \(field ",       "\n        (field ", net_se_string)
		net_se_string = re.sub(" \(pins ",        "\n      (pins ",    net_se_string)
		#net_se_string = re.sub(" \(pin ",         "\n        (pin ",   net_se_string)

		# Network portion of file:
		net_se_string = re.sub(" \(nets ", "\n  (nets ", net_se_string)
		net_se_string = re.sub(" \(net ",  "\n    (net ", net_se_string)
		net_se_string = re.sub(" \(node ", "\n      (node ", net_se_string)

		# General substitutions:
		#net_se_string = re.sub(" \\;", ";", net_se_string)
		#net_se_string = re.sub(" \\.", ".", net_se_string)

		net_file.write(net_se_string)
		net_file.close()

        elif file_name.ends_with(".cmp"):
	    # Read in {cmp_file_name}:
	    cmp_file_name = net_file_name
	    cmp_stream = open(cmp_file_name, "r")
	    cmp_lines = cmp_stream.readlines()
	    cmp_stream.close()

	    # Process each {line} in {cmp_lines}:
	    database = self.database
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
		    #print("part_name:{0}".format(part_name))
		    double_underscore_index = part_name.find("__")
		    if double_underscore_index >= 0:
			shortened_part_name = \
			  part_name[:double_underscore_index]
			#print("Shorten part name '{0}' => '{1}'".
			#  format(part_name, shortened_part_name))
			part_name = shortened_part_name
		elif line.startswith("IdModule  "):
		    footprint = line[12:-2].split(':')[1]
		    #print("footprint='{0}'".format(footprint))
		elif line.startswith("EndCmp"):
		    part = database.part_lookup(part_name)
		    if part == None:
			# {part_name} not in {database}; output error message:
			print(("File '{0}', line {1}: Part Name {2} ({3} {4})" +
			  " not in database").format(cmp_file_name, line_number,
			  part_name, reference, footprint))
			errors = errors + 1
		    else:
			footprint_pattern = part.footprint_pattern
			if fnmatch.fnmatch(footprint, footprint_pattern):
			    # The footprints match:
			    board_part = \
			      Board_Part(self, part, reference, footprint)
			    self.board_parts_append(board_part)
			    part.board_parts.append(board_part)
			else:
			    print ("File '{0}',  line {1}: {2}:{3} Footprint" +
			      "'{4}' does not match database '{5}'"). \
			      format(cmp_file_name, line_number,
			      reference, part_name, footprint,
			      footprint_pattern)
			    errors = errors + 1
		elif line == "\n" or line.startswith("TimeStamp") or \
		  line.startswith("EndListe") or line.startswith("Cmp-Mod V01"):
		    # Ignore these lines:
		    line = line
		else:
		    # Unrecognized {line}:
		    print "'{0}', line {1}: Unrecognized line '{2}'". \
		      format(cmp_file_name, line_number, line)
		    errors = errors + 1
        else:
	    print("Net file '{0}' name does not have a recognized suffix".
	      format(net_file_name))

	return errors

    def assembly_summary_write(self, final_choice_parts):
        """ *Board*: Write out an assembly summary .csv file for the *Board* object (i.e. *self*)
	    using *final_choice_parts*.
	"""

	# Verify argument types:
        assert isinstance(final_choice_parts, list)

	# Open *board_file*:
	board_file_name = "/tmp/{0}.csv".format(self.name)
	board_file = open(board_file_name, "w")

	# Write out the column headings:
	board_file.write(
	  '"Quan.","Reference","Schematic Name","Description","Fractional",' + \
          '"Manufacturer","Manufacture PN","Vendor","Vendor PN"\n\n')

	# Output the installed parts:
	has_fractional_parts1 = \
	  self.assembly_summary_write_helper(True, final_choice_parts, board_file)

	# Output the uninstalled parts:
	board_file.write("\nDo Not Install\n")

	# Output the installed parts:
	has_fractional_parts2 = \
	  self.assembly_summary_write_helper(False, final_choice_parts, board_file)

	# Explain what a fractional part is:
	if has_fractional_parts1 or has_fractional_parts2:
            board_file.write(
	      '"","\nFractional parts are snipped off of 1xN or 2xN break-way headers"\n')

        # Close *board_file* and print out a summary announcement:
        board_file.close()
	print("Wrote out assembly file '{0}'".format(board_file_name))

    def assembly_summary_write_helper(self, install, final_choice_parts, board_file):
        """ *Board*: Write out an assembly summary .csv file for *Board* object (i.e. *self*)
	    out to *board_file*.  *install* is set *True* to list the installable parts from
	    *final_choice_parts* and *False* for an uninstallable parts listing.
	    This routine returns *True* if there are any fractional parts output to *board_file*.
	"""

	# Verify argument types:
	assert isinstance(install, bool)
        assert isinstance(final_choice_parts, list)
	assert isinstance(board_file, file)

	# Each *final_choice_part* that is part of the board (i.e. *self*) will wind up
        # in a list in *board_parts_table*.  The key is the *schematic_part_key*:
	board_parts_table = {}
	for final_choice_part in final_choice_parts:
	    # Now figure out if final choice part is part of *board_parts*:
	    board_parts = final_choice_part.board_parts
            for board_part in board_parts:
		# We only care care about *final_choice_part* if is used on *board* and
                # it matches the *install* selector:
		if board_part.board == self and board_part.install == install:
		    # We are on the board; create *schemati_part_key*:
		    schematic_part = board_part.schematic_part
		    schematic_part_key = "{0};{1}".format(
		      schematic_part.base_name, schematic_part.short_footprint)

		    # Create/append a list to *board_parts_table*, keyed on *schematic_part_key*:
		    if not schematic_part_key in board_parts_table:
                        board_parts_table[schematic_part_key] = []
		    pairs_list = board_parts_table[schematic_part_key]

		    # Append a pair of *board_part* and *final_choice_part* onto *pairs_list*:
		    board_final_pair = (board_part, final_choice_part)
		    pairs_list.append(board_final_pair)

	# Now organize everything around the *reference_list*:
	reference_board_parts = {}
	for pairs_list in board_parts_table.values():
	    # We want to sort base on *reference_value* which is converted into *reference_text*:
	    reference_list = \
	      [board_final_pair[0].reference.upper() for board_final_pair in pairs_list]
	    reference_text = ", ".join(reference_list)
	    #print("reference_text='{0}'".format(reference_text))
	    board_part = pairs_list[0]
	    reference_board_parts[reference_text] = board_part

	# Sort the *reference_parts_keys*:
	reference_board_parts_keys = reference_board_parts.keys()
	reference_board_parts_keys.sort()

	# Now dig down until we have all the information we need for output the next .csv file line:
	has_fractional_parts = False
        for reference_board_parts_key in reference_board_parts_keys:
	    # Extract the *board_part* and *final_choice_part*:
	    board_final_pair = reference_board_parts[reference_board_parts_key]
	    board_part = board_final_pair[0]
	    final_choice_part = board_final_pair[1]
	    assert isinstance(final_choice_part, Choice_Part)

	    # Now get the corresponding *schematic_part*:
	    schematic_part = board_part.schematic_part
	    schematic_part_key = "{0};{1}".format(
	      schematic_part.base_name, schematic_part.short_footprint)
	    assert isinstance(schematic_part, Schematic_Part)

	    # Now get the *actual_part*:
	    actual_part = final_choice_part.selected_actual_part
	    assert isinstance(actual_part, Actual_Part)

	    # Now get the Vendor_Part:
	    manufacturer_name = actual_part.manufacturer_name
	    manufacturer_part_name = actual_part.manufacturer_part_name
	    vendor_part = final_choice_part.selected_vendor_part
	    assert isinstance(vendor_part, Vendor_Part)

	    # Output the line for the .csv file:
	    vendor_name = vendor_part.vendor_name
	    vendor_part_name = vendor_part.vendor_part_name
	    quantity = final_choice_part.count_get()
	    fractional = "No"
            if len(final_choice_part.fractional_parts) > 0:
                fractional = "Yes"
                has_fractional_parts = True
	    board_file.write('"{0} x","{1}","{2}","{3}","{4}","{5}","{6}","{7}","{8}"\n'.
	      format(quantity,
	      reference_board_parts_key, schematic_part_key, final_choice_part.description,
	      fractional,
	      manufacturer_name, manufacturer_part_name, vendor_name, vendor_part_name))

	return has_fractional_parts


class Board_Part:
    # A Board_Part basically specifies the binding of a Schematic_Part
    # and is associated schemtatic reference.  Reference strings must
    # be unique for a given board.

    def __init__(self, board, schematic_part, reference, comment):
	""" *Board_Part*: Initialize *self* to contain *board*,
            *schematic_part*, *reference*, and *comment*. """

	# Verify argument types:
	assert isinstance(board, Board)
	assert isinstance(schematic_part, Schematic_Part)
	assert isinstance(reference, str)
	assert isinstance(comment, str)

	# Load up *self*:
	self.board = board
	self.schematic_part = schematic_part
	self.reference = reference
	self.comment = comment
	self.install = (comment != "DNI")

class Schematic_Part:
    # A *Schematic_Part* represents part with a footprint.  The schematic
    # part name must adhere to the format of "name;footprint:comment", where
    # ":comment" is optional.  The footprint name can be short (e.g. 1608,
    # QFP100, SOIC20, SOT3), since it only has to disambiguate the various
    # footprints associated with "name".  A *Schematic_Part* is always
    # sub-classed by one of *Choice_Part*, *Alias_Part*, or *Fractional_Part*.

    def __init__(self, schematic_part_name, kicad_footprint):
	""" *Schematic_Part*: Initialize *self* to contain
	    *schematic_part_name*, and *kicad_footprint*. """

	# Verify argument types:
	assert isinstance(schematic_part_name, str)
	assert isinstance(kicad_footprint, str)
	assert kicad_footprint != ""
	
	# Split *schematic_part_name" into *base_name* and *short_footprint*:
	base_name_short_footprint = schematic_part_name.split(';')
	if len(base_name_short_footprint) == 2:
	    base_name = base_name_short_footprint[0]
	    short_footprint = base_name_short_footprint[1]

	    # Load up *self*:
	    self.schematic_part_name = schematic_part_name
	    self.base_name = base_name
	    self.short_footprint = short_footprint
	    self.kicad_footprint = kicad_footprint
	    self.board_parts = []
	else:
	    print("Schematic Part Name '{0}' has no ';' separator!".
	      format(schematic_part_name))

    def __format__(self, format):
        """ *Schematic_Part*: Format the *Schematic_Part* object (i.e. *self*) using *format***. """

	if format == "s":
            # Short format:
	    return "{0};{1}".format(self.base_name, self.short_footprint)
	else:
	    # Long format:
	    return "{0};{1}::{2}".format(self.base_name, self.short_footprint, self.kicad_footprint)

        
class Choice_Part(Schematic_Part):
    # A *Choice_Part* specifies a list of *Actual_Part*'s to choose from.

    def __init__(self, schematic_part_name, kicad_footprint, location,
      description):
	""" *Choice_Part*: Initiailize *self* to contain *schematic_part_name*
	    *kicad_footprint* and *actual_parts*. """

	# Verify argument types:
	assert isinstance(schematic_part_name, str)
	assert isinstance(kicad_footprint, str)
	assert isinstance(location, str)
	assert isinstance(description, str)

	# Load up *self*:
	Schematic_Part.__init__(self, schematic_part_name, kicad_footprint)
	self.location = location
	self.description = description
	self.actual_parts = []

	# Fields used by algorithm:
	self.fractional_parts = []
	self.selected_total_cost = -0.01
	self.selected_order_quantity = -1
	self.selected_actual_part = None
	self.selected_vendor_part = None
	self.selected_vendor_name = ""
	self.selected_price_break_index = -1
	self.selected_price_break = None

    def __format__(self, format):
        """ *Choice_Part*: Return the *Choice_Part object (i.e. *self* as a string formatted by
	    *format*.
	"""
        
	if format == "s":
	    result = "{0};{1}".format(self.base_name, self.short_footprint)
        else:
	    result = "{0};{1}".format(self.base_name, self.short_footprint)
        return result


    def actual_part(self,
      manufacturer_name, manufacturer_part_name, vendor_triples = []):
	""" *Choice_Part*: ... """

	# Verify argument types:
	assert isinstance(manufacturer_name, str)
	assert isinstance(manufacturer_part_name, str)
	assert isinstance(vendor_triples, list)
	for vendor_triple in vendor_triples:
	    assert len(vendor_triple) == 3
	    assert isinstance(vendor_triple[0], str)
	    assert isinstance(vendor_triple[1], str)
	    assert isinstance(vendor_triple[2], str)

	actual_part = Actual_Part(manufacturer_name, manufacturer_part_name)
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
		    except:
			assert False, \
			  "Quantity '{0}' is not an integer". \
			  format(price_pair[0])

		    # Extract the *price* from *price_pair*:
		    price = 100.00
		    try:
			price = float(price_pair[1])
		    except:
			assert False, \
			  "Price '{0}' is not a float".format(price_pair[1])

		    # Construct the *price_break* and append to *price_breaks*:
		    price_break = Price_Break(quantity, price)
		    price_breaks.append(price_break)

		# Create the *vendor_part* and append it to *actual_part*:
		assert len(price_breaks) > 0
		vendor_part = Vendor_Part(actual_part,
		  vendor_name, vendor_part_name, 1000000, price_breaks)
		actual_part.vendor_part_append(vendor_part)

	return self

    def board_part_append(self, board_part):
	""" *Choice_Part*: Store *board_part* into the *Choice_Part* object
	    (i.e. *self*.)
	"""

	# Verify argument types:
	assert isinstance(board_part, Board_Part)

	# Append *board_part* to *board_parts*:
	self.board_parts.append(board_part)

    def board_parts_sort(self):
	""" *Choice_Part*: Sort the *board_parts* of the *Choice_Part* object
	    (i.e. *self*.)
	"""

	# Sort the *board_parts* using a key of
	# (board_name, reference, reference_number).  A reference of
	# "SW123" gets conferted to (..., "SW123", 123):
	board_parts = self.board_parts
	board_parts.sort(key = lambda board_part:
	  (board_part.board.name,
	  filter(str.isalpha, board_part.reference.upper()),
	  int(filter(str.isdigit, board_part.reference))) )

	#print("  {0}:{1};{2} {3}:{4}".\
	#  format(choice_part.schematic_part_name,
	#choice_part.kicad_footprint, choice_part.description,
	#  choice_part.count_get(), choice_part.references_text_get()))

    def count_get(self):
	""" *Choice_Part*: Return the number of needed instances of *self*. """

	count = 0

	fractional_parts = self.fractional_parts
	if len(fractional_parts) == 0:
	    for board_part in self.board_parts:
		count += board_part.board.count
	else:
	    #for fractional_part in fractional_parts:
	    #	print("{0}".format(fractional_part.schematic_part_name))

	    # This code is not quite right:
	    first_fractional_part = fractional_parts[0]
	    denominator = first_fractional_part.denominator
	    for fractional_part in fractional_parts[1:]:
		assert denominator == fractional_part.denominator, \
		  "'{0}' has a denominator of {1} and '{2}' has one of {3}". \
		  format(first_fractional_part.schematic_part_name,
		  first_fractional_part.denominator,
		  fractional_part.schematic_part_name,
		  fractional_part.denominator)
	    
	    # Compute the *count*:
	    numerator = 0
	    for board_part in self.board_parts:
		schematic_part = board_part.schematic_part
		#print("'{0}'".format(schematic_part.schematic_part_name))
		if isinstance(schematic_part, Alias_Part):
		    alias_parts = schematic_part
		    for schematic_part in alias_parts.schematic_parts:
			if isinstance(schematic_part, Fractional_Part):
			    fractional_part = schematic_part
		elif isinstance(schematic_part, Fractional_Part):
		    fractional_part = schematic_part
		else:
		    assert False, "Missing code"

		fractional_numerator = fractional_part.numerator
		for index in range(board_part.board.count):
		    if numerator + fractional_numerator > denominator:
			count += 1
			numerator = 0
		    numerator += fractional_numerator
	    if numerator > 0:
		numberator = 0
		count += 1

	return count

    def choice_parts(self):
	""" *Choice_Part*: Return a list of *Choice_Part* corresponding
	    to *self* """

	assert isinstance(self, Choice_Part)
	return [self]

    def references_text_get(self):
	""" *Choice_Part*: Return a string of references for *self*. """

	references_text = ""
	previous_board = None
	is_first = True
        for board_part in self.board_parts:
	    board = board_part.board
	    if board != previous_board:
		if not is_first:
		    references_text += "]"
		references_text += "[{0}:".format(board.name)
	    previous_board = board
	    is_first = False

	    # Now tack the reference to the end:
	    references_text += " {0}".format(board_part.reference)
	references_text += "]"
	return references_text

    def select(self, excluded_vendor_names, announce=False):
	""" *Choice_Part*: Select and return the best priced *Actual_Part*
	    for the *Choice_Part* (i.e. *self*) excluding any vendors
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

	quints = []
	required_quantity = self.count_get()
	actual_parts = self.actual_parts
	for actual_part_index in range(len(actual_parts)):
	    actual_part = actual_parts[actual_part_index]
	    vendor_parts = actual_part.vendor_parts
	    for vendor_part_index in range(len(vendor_parts)):
		vendor_part = vendor_parts[vendor_part_index]
		price_breaks = vendor_part.price_breaks
		for price_break_index in range(len(price_breaks)):
		    price_break = price_breaks[price_break_index]

		    # We not have an *actual_part*, *vendor_part* and
		    # *price_break* triple.  Compute *order_quantity*
		    # and *total_cost*:
		    price = price_break.price
		    quantity = price_break.quantity
		    order_quantity = max(required_quantity, quantity)
		    total_cost = order_quantity * price

		    # Assemble the *quint* and append to *quints* if there
		    # enough parts available:
		    if not vendor_part.vendor_name in excluded_vendor_names \
		      and vendor_part.quantity_available >= order_quantity:
			assert price_break_index < len(price_breaks)
		        quint = (total_cost, order_quantity,
		          actual_part_index, vendor_part_index,
			  price_break_index, len(price_breaks))
		        quints.append(quint)
			#print("quint={0}".format(quint))

	if len(quints) == 0:
	    choice_part_name = self.schematic_part_name
	    if announce:
		print("No vendor parts found for Part '{0}'".
		  format(choice_part_name))
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
	    assert selected_price_break_index < \
	      len(selected_vendor_part.price_breaks)

	    #print("selected_vendor_name='{0}'".format(selected_vendor_name))

	#actual_parts = self.actual_parts
	#for actual_part in actual_parts:
	#    print("       {0}:{1}".format(actual_part.manufacturer_name,
	#      actual_part.manufacturer_part_name))

	#actual_parts = self.actual_parts
	#selected_actual_part = actual_parts[0]
	#assert isinstance(selected_actual_part, Actual_Part)
	#self.selected_actual_part = selected_actual_part
	
	#vendor_parts = selected_actual_part.vendor_parts
	#if len(vendor_parts) == 0:
	#    key = selected_actual_part.key
	#    print("No vendor part for Actual Part '{0} {1}'". \
	#      format(key[0], key[1]))
	#else:
	#    selected_actual_part.selected_vendor_part = vendor_parts[0]

	#assert isinstance(selected_actual_part, Actual_Part)

	missing_part = 0
	if len(quints) == 0:
	    missing_part = 1
	return missing_part

    def vendor_names_load(self, vendor_names_table, excluded_vendor_names):
	""" *Choice_Part*: Add each possible vendor name possible for the
	    *Choice_Part* object (i.e. *self*) to *vendor_names_table*
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

class Alias_Part(Schematic_Part):
    # An *Alias_Part* specifies one or more *Schematic_Parts* to use.

    def __init__(self, schematic_part_name, schematic_parts, kicad_footprint):
	""" *Alias_Part*: Initialize *self* to contain *schematic_part_name*,
	    *kicad_footprint*, and *schematic_parts*. """

	# Verify argument types:
	assert isinstance(schematic_part_name, str)
	assert isinstance(schematic_parts, list)
	for schematic_part in schematic_parts:
	    assert isinstance(schematic_part, Schematic_Part)

	# Load up *self*:
	Schematic_Part.__init__(self, schematic_part_name, kicad_footprint)
	self.schematic_parts = schematic_parts
	
    def choice_parts(self):
	""" *Alias_Part*: Return a list of *Choice_Part* corresponding
	    to *self* """

	assert isinstance(self, Alias_Part)
	choice_parts = []
	for schematic_part in self.schematic_parts:
	    choice_parts += schematic_part.choice_parts()
		
	#assert False, \
	#  "No choice parts for '{0}'".format(self.schematic_part_name)
	return choice_parts

class Fractional_Part(Schematic_Part):
    # A *Fractional_Part* specifies a part that is constructed by
    # using a portion of another *Schematic_Part*.

    def __init__(self, schematic_part_name, kicad_footprint,
      choice_part, numerator, denominator, description):
	""" *Fractional_Part*: Initialize *self* to contain
	    *schematic_part_name*, *kicad_footprint*, *choie_part*,
	    *numerator*, *denomoniator*, and *description*. """

	# Verify argument types:
	assert isinstance(schematic_part_name, str)
	assert isinstance(kicad_footprint, str)
	assert isinstance(choice_part, Choice_Part)

	# Load up *self*:
	Schematic_Part.__init__(self, schematic_part_name, kicad_footprint)
	self.choice_part = choice_part
	self.numerator = numerator
	self.denominator = denominator
	self.description = description

    def choice_parts(self):
	""" *Fractional_Part*: Return the *Choice_Part* objects associated
	    with *self*.
	"""

	choice_part = self.choice_part
	choice_part.fractional_parts.append(self)
	return [choice_part]

class Actual_Part:
     # An *Actual_Part* represents a single manufacturer part.
     # A list of vendor parts specifies where the part can be ordered from.

    def __init__(self, manufacturer_name, manufacturer_part_name):
	""" *Actual_Part*: Initialize *self* to contain *manufacture* and
	    *manufacturer_part_name*. """

	# Verify argument_types:
	assert isinstance(manufacturer_name, str)
	assert isinstance(manufacturer_part_name, str)

	key = (manufacturer_name, manufacturer_part_name)
	
	# Load up *self*:
	self.manufacturer_name = manufacturer_name
	self.manufacturer_part_name = manufacturer_part_name
	self.key = key
	# Fields used by algorithm:
	self.quantity_needed = 0
	self.vendor_parts = []
	self.selected_vendor_part = None

    def vendor_part_append(self, vendor_part):
	""" *Actual_Part: Append *vendor_part* to the vendor parts
	    of *self*. """

	assert isinstance(vendor_part, Vendor_Part)
	self.vendor_parts.append(vendor_part)

    def vendor_names_load(self, vendor_names_table, excluded_vendor_names):
	""" *Actual_Part*:*: Add each possible to vendor name for the
	    *Actual_Part* object (i.e. *self*) to *vendor_names_table*:
	"""

	# Verify argument types:
	assert isinstance(vendor_names_table, dict)
	assert isinstance(excluded_vendor_names, dict)

	# Add the possible vendor names for *vendor_part* to
	# *vendor_names_table*:
	for vendor_part in self.vendor_parts:
	    vendor_name = vendor_part.vendor_name
	    if not vendor_name in excluded_vendor_names:
		vendor_names_table[vendor_name] = None

class Vendor_Part:
    # A vendor part represents a part that can be ordered from a vendor.

    def __init__(self, actual_part, vendor_name, vendor_part_name,
      quantity_available, price_breaks, timestamp=0.0):
	""" *Vendor_Part*: Initialize *self* to contain *actual_part"""

	#print("vendor_part_name=", vendor_part_name)

	# Check argument types:
	assert isinstance(actual_part, Actual_Part)
	assert isinstance(vendor_name, str)
	assert isinstance(vendor_part_name, str)
	assert isinstance(quantity_available, int)
	assert isinstance(price_breaks, list)
	assert isinstance(timestamp, float)
	for price_break in price_breaks:
	    assert isinstance(price_break, Price_Break)

	# Load up *self*:
	self.actual_part_key = actual_part.key
	self.vendor_key = (vendor_name, vendor_part_name)
	self.vendor_name = vendor_name
	self.vendor_part_name = vendor_part_name
	self.quantity_available = quantity_available
	self.price_breaks = price_breaks
	self.timestamp = timestamp

	# Append *self* to the vendor parts of *actual_part*:
	actual_part.vendor_part_append(self)

    def dump(self, out_stream, indent):
	""" *Vendor_Part*: Dump the *Vendor_Part* (i.e. *self*) out to
	    *out_stream* in human readable form indented by *indent* spaces.
	"""

	# Verify argument types:
	assert isinstance(out_stream, file)
	assert isinstance(indent, int)

	# Dump out *self*:
	out_stream.write("{0}Actual_Part_Key:{1}\n".
	  format(" " * indent, self.actual_part_key))
	out_stream.write("{0}Vendor_Key:{1}\n".
	  format(" " * indent, self.vendor_key))
	out_stream.write("{0}Vendor_Name:{1}\n".
	  format(" " * indent, self.vendor_name))
	out_stream.write("{0}Vendor_Part_Name:{1}\n".
	  format(" " * indent, self.vendor_part_name))
	out_stream.write("{0}Quantity_Available:{1}\n".
	  format(" " * indent, self.quantity_available))
	out_stream.write("{0}Price_Breaks: (skip)\n".
	  format(" " * indent))

    def price_breaks_text_get(self):
	""" *Vendor_Part*: Return the prices breaks for the *Vendor_Part*
	    object (i.e. *self*) as a text string:
	"""

	price_breaks_text = ""
	for price_break in self.price_breaks:
	    price_breaks_text += "{0}/${1:.3f} ".format(
	      price_break.quantity, price_break.price)
	return price_breaks_text

class Price_Break:
    # A price break is where a the pricing changes:
    
    def __init__(self, quantity, price):
	""" *Price_Break*: Initialize *self* to contain *quantity*
	    and *price*.  """

	# Verify argument types:
	assert isinstance(quantity, int)
	assert isinstance(price, float)

	# Load up *self*;
	self.quantity = quantity
	self.price = price
	self.order_quantity = 0
	self.order_price = 0.00

    def compute(self, needed):
	""" *Price_Break*: """

	assert isinstance(needed, int)

	self.order_quantity = order_quantity = max(needed, self.quantity)
	self.order_price = order_quantity * self.price

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

def main():
    database = Database()
    euros = database.exchange_rate("USD", "EUR")
    print("euros = {0}".format(euros))
    order = Order(database)
    order.board("bus_loki", "F.1", "bus_loki.net", 1)
    order.process()

if __name__ == "__main__":
    main()
