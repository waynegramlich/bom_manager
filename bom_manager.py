#!/usr/bin/env python

# The problem that is being addressed is:
#
#       Schematic Symbol =>
#         Footprint =>
#           Manufacturer Part Number =>
#             Vendor Part Number =>
#               Vendor Order
#
# In KiCad, the schematic does not care about footprints.  Conceptually,
# it is possible to use the same KiCad schematic to produce multiple
# different PCB layouts (e.g. through hole parts or surface mount parts.)
# This is possible because KiCad allows the user to delay the footprint
# binding until after schematic capture using the CvPcb sub-system.
# However, once the binding has occurred, it is difficult to change because
# the footprints become embedded in the PCB.  Thus, while it is possible
# to reuse KiCad schematics, realistically nobody does anything other
# than a 1-to-1 between a schematic and a PCB.  Hence, I've reluctantly
# come to the conclusion that the Schematic symbol should explicitly specify
# the footprint in KiCad (e.g. "10K;1608" instead of "10K" or
# "ATMEGA328-16PU;QFP32" instead of "ATMEGA328-16PU".)  This clutters up
# the schematic somewhat, but removes all ambiguity and makes the rest of
# the BOM managment easier.  Once the footprint has been selected,
# KiCad simply does not care about the rest of the part selection
# and purchasing workflow.
#
# As evidenced by Rohan's Aleopile library, it is possible to assign
# Footprint, Manufacturer, Manufacture Part Number, Vendor and Vendor
# Part Number into a schematic symbol.  Alas, this is a brittle binding
# in that any change to library, does not automatically get updated
# to the schematic.  If a part goes obsolete, it is necessary to
# change the schematic library and manually update the schematic to
# force the schematic symbol update.  This brittleness is not acceptable.
#
# The next issue is that many components are generic.  We really do not care
# who is the manufacturer for a 10K 1608 resistor.  Other components only have
# a single manufacturer source.  For the Aleopile library, schematic
# symbols are 1-to-1 with manufacturer part numbers.
#
# Once you have MPN (Manufacturer Part Number), Octopart can be used to find
# the vendors and associated prices.  There is an internet API for this.
# Octopart limits the free accounts to 5K accesses per month.  Paid Octopart
# access is actually quite expensive.  An access is allowed to lookup 20
# parts.  In order to make it all work, we need to cache previous lookup
# values.  In theory, Digikey has totally free part lookup, but the
# documentation is awful.
#
# Once we have the vendor costs, the final step is to do vendor selection.
# If shipping costs were $0, this step would be unnecessary.  However,
# ordering a part to save $.01, but pay $7 for shipping is kind of stupid.
# So, I have the ability to kick out vendors due to shipping costs.
# Usually, I get stuck with one or two vendors that make sense (DigiKey,
# Mouser, Arrow.)
#
# Finally, there are issues of supporting multiple differenct PCB's in one
# order, inventory managment, etc.
#
# Inventory management is an area that needs some more work.  I've come
# to the conclusion that for generic parts, we should just buy one reel
# and store them on a rod.
#
# Pieces of this system are kind of working, but the whole system is not. 

# Import some libraries:
from sexpdata import Symbol
import sexpdata
import fnmatch
import math

# Data Structure and Algorith Overview;
#
# For an *Order*, the user specifies a list of *Board*'s.  For each *Board*,
# the number of boards to be poplulated is specified.  Also, the user
# can specify a list of additional parts to add to the order.
# Likewise, parts in the inventory can be specified to reduce the
# number of ordered parts.
#
# The list of excluded vendors starts out empty.  As the ordering process
# nears completion, the user manually excludes vendors in order to eliminate
# vendors where shipping costs exceed part cost savings.
#
# For each *Board*, the algorithm reads in the KiCad .net file and extracts
# the list of *Board_Part*'s.  For each *Board_Part*, the parts database
# is queried to look up the *Schamtic_Part* by name (e.g. R12;1608).
# Missing entries are flagged as errors.  When there are no outstanding
# errors, the .net file is updated to place the correct KiCad footprint
# for each part.
#
# There are three sub_classes of *Schematic_Part*:
#
# * Choice_Part*: A list of possible Actual_Part's to choose from.
#
# * Alias_Part*: An alias specifies one or more schematic parts to
#    redirect to.
#
# * Fractional_Part*: A fractional part is an alias to another schematic
#    part that specifes a fraction of the part.  A fractional part is
#    usually a 1x40 or 2x40 break-away male header.  They are so common
#    they must be supported.
#
# Now the algorithm iterates through each *Schematic_Part* to convert
# each *Fractional_Part* and *Alias_Part* into *Choice_Part*.
# Errors are flagged.
#
# For each *Choice_Part*, the *Actual_Part* list is iterated over.
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

	# Initialize the various tables:
	self.actual_parts = {}
	self.schematic_parts = {}
	self.vendor_parts = {}

	# Boxes:

	self.choice_part("JB-3955;102Lx152Wx152H", "102Lx152Wx152H", "",
	  "BOX STEEL GRAY 102Lx152Wx152H").actual_part(
	  "Bud Industries", "JB-3955", [
	  ("Digkey", "377-1838-ND",
	   "1/12.35 6/10.25000 100/9.25")])

	# Buttons:

	# Change KiCAD Footprint name -- it is totally wrong:
	self.choice_part("BUTTON;6X6MM", "FCI214376569", "",
	  "SWITCH TACTILE SPST-NO 0.05A 12V").actual_part(
	  "TE", "2-1437565-9", [
	  ("Digikey", "450-1792-1-ND",
	   "1/.26 10/.249 25/.2408 50/.232 100/.219 200/.206")]).actual_part(
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
	self.alias_part("6MM_4LED_BUTTON;6X6MM", ["BUTTON;6X6MM"])

	# Capacitors:

	self.choice_part("18pF;1608", "CAPC1608X86N", "",
	  "CAP CER 18PF 25V+ 10% SMD 0603").actual_part(
	  "Kamet", "C0603C180J5GACTU", [
	   ("Digikey", "399-1052-1-ND",
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
	self.choice_part(".1uF;1608", "CAPC1608X86N", "",
	  "CAP CER 0.1UF 25V+ 10% SMD 0603").actual_part(
	  "Murata", "GRM188R71E104KA01D", [
	  ("Digikey", "490-1524-1-ND",
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
	self.choice_part("1uF;1608", "CAPC1608X86N", "",
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
	  ("Digikey", "565-3307-ND",
	   "1/12.10 10/11.495 100/9.075")])

	# Connectors:

	## Male Connectors:

	### Create the fractional parts for 1XN male headers:
	self.choice_part("M1X40;M1X40", "Pin_Header_Straight_1x40", "",
	  "CONN HEADER .100\" SNGL STR 40POS").actual_part(
	  "Sullins", "PREC040SAAN-RC", [
	   ("Digikey", "S1012EC-40-ND",
	    "1/.56 10/.505 100/.4158 500/.32868 1000/.28215")])

	self.fractional_part("M1X1;M1X1", "Pin_Header_Straight_1x01",
	   "M1X40;M1X40", 1, 40, "CONN HEADER .100\" SNGL STR 1POS")
	self.fractional_part("M1X2;M1X2", "Pin_Header_Straight_1x02",
	   "M1X40;M1X40", 2, 40, "CONN HEADER .100\" SNGL STR 2POS")
	self.fractional_part("M1X3;M1X3", "Pin_Header_Straight_1x03",
	   "M1X40;M1X40", 3, 40, "CONN HEADER .100\" SNGL STR 3POS")
	self.fractional_part("M1X4;M1X4", "Pin_Header_Straight_1x04",
	   "M1X40;M1X40", 4, 40, "CONN HEADER .100\" SNGL STR 4POS")
	self.fractional_part("M1X5;M1X5", "Pin_Header_Straight_1x05",
	   "M1X40;M1X40", 5, 40, "CONN HEADER .100\" SNGL STR 5POS")
	self.fractional_part("M1X6;M1X6", "Pin_Header_Straight_1x06",
	   "M1X40;M1X40", 6, 40, "CONN HEADER .100\" SNGL STR 6POS")

	# Test points M1X1:
	self.alias_part("CAN_RXD;M1X1", ["M1X1;M1X1"])
	self.alias_part("TEST_POINT;M1X1", ["M1X1;M1X1"])

	# M1X2:
	self.alias_part("CURRENT_SHUNT;M1X2", ["M1X2;M1X2"])

	# M1X3:
	self.alias_part("TERMINATE_JUMPER;M1X3", ["M1X3;M1X3"])
	self.alias_part("SERVO;M1X3", ["M1X3;M1X3"])

	# M1X4:
	self.alias_part("I2C_CONN;M1X4", ["M1X4;M1X4"])

	# M1X6:
	self.alias_part("ENCODER_CONNECTOR;M1X6", ["M1X6;M1X6"])
	self.alias_part("FTDI_HEADER;M1X6", ["M1X6;M1X6"])
	self.alias_part("FTDI_HEADER_ALT;M1X6", ["M1X6;M1X6"])

	self.choice_part("M2X5S;M2X5S", "Pin_header_Straight_2x05_Shrouded", "",
	  "BOX HEADER .100\" MALE STR 10POS").actual_part(
	  "On Shore", "302-S101", [
	   ("Digikey", "ED1543-ND",
	    "1/.28 10/.263 50/.1912 100/.1838 250/.165")]).actual_part(
	  "Assmann", "AWHW-10G-0202-T").actual_part(
	  "CNC Tech", "3020-10-0100-00").actual_part(
	  "Sullins", "SBH11-PBPC-D05-ST-BK").actual_part(
	  "3M", "30310-6002HB").actual_part(
	  "TE Tech", "5103308-1").actual_part(
	  "CNC Tech", "3010-10-001-11-00").actual_part(
	  "Wurth", "61201021621")
	self.alias_part("BUS_MASTER_HEADER;M2X5S", ["M2X5S;M2X5S"])

	### Create the fractional parts for the 2XN male headers:
	self.choice_part("M2X40;M2X40", "Pin_Header_Straight_2x40", "",
	  "CONN HEADER .100\" DUAL STR 80POS").actual_part(
	  "Sullins", "PREC040DAAN-RC", [
	   ("Digikey", "S2212EC-40-ND",
	    "1/1.28 10/1.14200 100/.9408 500/.74368 1000/.63840")]).actual_part(
	  "Sullins", "PREC040DFAN-RC").actual_part(
	  "Sullins", "PRPC040DAAN-RC").actual_part(
	  "Sullins", "PRPC040DABN-RC").actual_part(
	  "Sullins", "PRPC040DFAN-RC").actual_part(
	  "Sullins", "PRPC040DFBN-RC").actual_part(
	  "Wurth", "61308021121").actual_part(
	  "TE", "4-103322-2").actual_part(
	  "TE", "9-146258-0")

	self.fractional_part("M2X3;M2X3", "Pin_Header_Straight_2x03",
	  "M2X40;M2X40", 6, 80, "CONN HEADER .100\" DBL STR 6POS")

	self.fractional_part("AVR_SPI;M2X3", "Pin_Header_Straight_2x03",
	  "M2X40;M2X40", 6, 80, "CONN HEADER .100\" DBL STR 6POS")

	self.fractional_part("M2X6;M2X6", "Pin_Header_Straight_2x06",
	  "M2X40;M2X40", 12, 80, "CONN HEADER .100\" DBL STR 12POS")

	## Female connectors:

	self.choice_part("F1X3;F1X3", "Pin_Header_Straight_1x03", "",
	  "CONN HEADER FEMALE 3POS .1\"").actual_part(
	  "Sullins", "PPPC031LFBN-RC").actual_part(
	  "Sullins", "PPTC031LFBN-RC").actual_part(
	  "3M", "960103-6202-AR").actual_part(
	  "Harwin", "M20-7820342").actual_part(
	  "TE", "5-535541-1").actual_part(
	  "3M", "929850-01-03-RA").actual_part(
	  "FCI", "66951-003LF")
	self.alias_part("REGULATOR;F1X3", ["F1X3;F1X3"])

	self.choice_part("F2X4;F2X4", "Pin_Header_Straight_2x04", "",
	  "CONN RCPT .100\" 8POS DUAL").actual_part(
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
	self.alias_part("HC_SR04;F2X4", ["F2X4;F2X4"])

	self.choice_part("2POS_TERM_BLOCK;5MM", "5MM_TERM_BLOCK", "",
	  "TERM BLOCK PCB 2POS 5.0MM").actual_part(
	  "Phoenix Contact", "1935161").actual_part(
	  "On Shore", "OSTTA020161").actual_part(
	  "Phoenix Contact", "1935776").actual_part(
	  "On Shore", "OSTTC020162").actual_part(
	  "TE", "1546216-2").actual_part(
	  "TE", "282836-2").actual_part(
	  "On Shore", "ED100/2DS").actual_part(
	  "On Shore", "ED500/2DS")

	# There is a flipped/non-flipped issue here:
	self.choice_part("F2X20RAK;F2X20RAK",
	  "Pin_Receptacle_Angle_2x20_Flipped", "",
	  "CONN HEADER FEMALE 40POS 0.100\" ANGLED KEYED").actual_part(
	  "Sullins", "SFH11-PBPC-D20-RA-BK")
	self.alias_part("SBC_CONNECTOR40;F2X20RAKF", ["F2X20RAK;F2X20RAK"],
	  "Pin_Receptacle_Angle_2x20_Flipped")

	# Crystals:

	self.choice_part("16MHZ;HC49S", "XTAL1150X480X430N", "",
	  "CRYSTAL 16.0000MHZ SMD").actual_part(
	  "TXC", "9C-16.000MBBK-T", [
	   ("Digikey", "887-2425-1-ND",
	    "1/.38 10/.316 50/.2832 100/.252 500/.24")]).actual_part(
	  "TXC", "9C-16.000MAAE-T").actual_part(
	  "TXC", "9C-16.000MAGJ-T").actual_part(
	  "Cardinal", "CSM1Z-A5B2C5-40-16.0D18").actual_part(
	  "Cardinal", "CSM1Z-A0B2C3-50-16.0D18").actual_part(
	  "Cardinal", "CSM1Z-A5B2C3-40-16.0D18").actual_part(
	  "Cardinal", "CSM4Z-A2B3C3-40-16.0D18")
	# This alias should be removed:
	self.alias_part("16MHZ;HC49", ["16MHZ;HC49S"])

	# Miscellaneous connectors:

        self.choice_part("VAC_FUSE_SW;10C1", "10C1", "",
	  "MODULE PWR ENTRY SCREW-ON").actual_part(
	  "Delta Electronics", "10C2", [
	   ("Digikey", "603-1262-ND",
	    "1/8.28 10/7.454 50/5.6318 100/5.3005")])

	# Diodes:

	self.choice_part("4.56V_ZENER;SOD323F", "SOD323F", "",
	  "DIODE ZENER 4.56V 500MW SOD323F").actual_part(
	  "Diodes Inc", "DDZ4V7ASF-7", [
	  ("Digikey", "DDZ4V7ASF-7DICT-ND",
	   "1/.16 10/.143 100/.0781 500/.04802 1000/.03275")])

	self.choice_part("BRIDGE_35A_1000V;GBPC", "GBPC", "",
	  "RECT BRIDGE GPP 1000V 35A GBPC").actual_part(
	  "Comchip Tech", "GBPC3510-G", [
	  ("Digikey", "641-1380-ND",
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
	  "Panasonic", "DB3Y313KEL").actual_part(
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
	self.choice_part("SCHOTTKY_3A_200V;DO214AA", "DO214AA", "",
	  "DIODE SCHOTTKY 200V 3A DO214AA").actual_part(
	  "Fairchild", "S320").actual_part(
	  "Micro Commercial", "SK3200B-LTP")

	# Grommets:

	self.choice_part("GROMMET;GR9.5MM", "GR9.5MM", "",
	  "BUSHING SPLIT 0.260\" NYLON BLACK").actual_part(
	  "Essentra", "PGSB-0609A", [
	  ("Digikey", "RPC1251-ND",
	   "1/.18 10/.166 25/.1536 100/.1281")])

	# Holes:

	self.choice_part("HOLE;3MM", "MountingHole_3mm", "",
	  "3MM HOLE").actual_part(
	  "McMaster-Carr", "3MM_Hole")
	self.choice_part("HOLE;2MM", "MountingHole_2mm", "",
	  "2MM HOLE").actual_part(
	  "McMaster-Carr", "2MM_Hole")

	# Fuses:

	self.choice_part("3A;LF649", "LF649", "",
	  "FUSE BLOCK CART 250V 6.3A PCB").actual_part(
	  "Littelfuse", "64900001039", [
	  ("Digikey", "WK0011-ND",
	    "1/.40 10/.378 25/.348 50/.318 100/.264 250/.24 500/.204")])
	# This alias should be removed:
	self.alias_part("3A;LF349", ["3A;LF649"])

	# Inductors:

	self.choice_part("?uH;I1X10", "Inductor_1x10", "",
	  "INLINE INDUCTER").actual_part(
	  "Bourns", "5258-RC", [
	  ("Digikey", "M8275-ND",
	   "1/1.51 10/1.392 25/1.276 50/1.0904 100/.97440")])

	self.choice_part("CIB10P100NC;1608", "INDC1608X95", "",
	  "FERRITE CHIP 10 OHM 1000MA 0603").actual_part(
	  "Samsung", "CIB10P100NC")

	# Integrated Circuits:

	self.choice_part("5V_LDO;SOT223", "SOT223", "",
	  "IC REG LDO 5V SOT223-3").actual_part(
	  "Diodes Inc", "AP1117E50G-13", [
	   ("Digikey", "AP1117E50GDICT-ND",
	    "1/.47 10/.377 100/.2571 500/.19242 1000/.14412")]).actual_part(
	  "Diodes Inc", "ZLDO1117G50TA").actual_part(
	  "Microchip", "MCP1824ST-5002E/DB").actual_part(
	  "Microchip", "MCP1825S-5002E/DB").actual_part(
	  "Microchip", "TC1262-5.0VDB").actual_part(
	  "Microchip", "MCP1703-5002E/DB").actual_part(
	  "Microchip", "MCP1703T-5002E/DB")


	self.choice_part("74xHC08;SOIC8", "SOIC127P600X174-14N", "",
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

	self.choice_part("74HC1G14;SOT23-5", "SOT95P280X145-5N", "",
	  "IC INVERTER SGL SCHMITT SOT23-5").actual_part(
	  "On Semi", "MC74HC1G14DTT1G", [
	   ("Digikey", "MC74HC1G14DTT1GOSCT-ND",
	    "1/.39 10/.319 100/.1691 500/.11116 1000/.07574")])

	self.choice_part("74HC1G175;SOT23-6", "SOT95P280X145-6N", "",
	  "IC D-TYPE POS TRG SNGL SOT23-6").actual_part(
	  "TI", "SN74LVC1G175DBVR").actual_part(
	  "TI", "SN74LVC1G175DBVT")

	self.choice_part("ATMEGA328;QFP32", "QFP80P90X900X120-32N", "",
	  "IC MCU 8BIT 32KB FLASH 32QFP").actual_part(
	  "Atmel", "ATMEGA328-AUR", [
	  ("Digikey", "ATMEGA328-AURCT-ND",
	   "1/3.38 10/3.015 25/2.7136 100/2.4723 250/2.23112")])

	self.choice_part("LM311;SOIC8", "SOIC127P600X173-8N", "",
	  "IC COMPARATOR SGL 8SOIC").actual_part(
	  "TI", "LM311DR",[
	   ("Digikey", "296-1388-1-ND",
	    "1/.47000 10/.361 100/.19 1000/.17")]).actual_part(
	  "On Semi", "LM311DR2G").actual_part(
	  "TI", "LM311DRG4").actual_part(
	  "TI", "LM311MX/NOPB")

	self.choice_part("MCP2562;SOIC8", "SOIC127P600X175", "",
	  "IC TXRX CAN 8SOIC").actual_part(
	  "Microchip", "MCP2562T-E/SN", [
	  ("Digikey", "MCP2562T-E/SNCT-ND",
	   "1/1.08 10/.90 25/.75 100/.68")])
	self.choice_part("MCP7940;SOIC8", "SOIC127P600X175", "",
	  "IC RTC CLK/CALENDAR I2C 8-SOIC").actual_part(
	  "Microchip", "MCP7940M-I/SN").actual_part(
	  "Microchip", "MCP7940N-I/SN").actual_part(
	  "Microchip", "MCP7940N-E/SN").actual_part(
	  "Microchip", "MCP79400-I/SN").actual_part(
	  "Microchip", "MCP79402-I/SN").actual_part(
	  "Microchip", "MCP79401-I/SN")
	
	# LED's:
	
	self.choice_part("GREEN_LED;1608", "DIOC1608X55N", "",
	  "LED 0603 GRN WATER CLEAR").actual_part(
	  "Wurth", "150060GS75000", [
	   ("Digikey", "732-4971-1-ND",
	    "1/.24 50/.21 100/.192 500/.17400 1000/.162")]).actual_part(
	  "Wurth", "150060VS75000").actual_part(
	  "Rohm", "SML-310MTT86").actual_part(
	  "Rohm", "SML-310FTT86").actual_part(
	  "QTB", "QBLP601-YG").actual_part(
	  "Rohm", "SML-310PTT86").actual_part(
	  "QTB", "QBLP601-IG").actual_part(
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
	self.alias_part("LED;1608", ["GREEN_LED;1608"])

	self.choice_part("CREE_3050;CXA3050", "CXA3050", "",
	  "CREE XLAMP CXA3050 23MM WHITE").actual_part(
	  "Cree", "CXA3050-0000-000N0HW440F")

	# Potentiometers:

	self.choice_part("10K;9MM", "10X5MM_TRIM_POT", "",
	  "TRIMMER 10K OHM 0.2W PC PIN").actual_part(
	  "Bourns", "3319P-1-103", [
	   ("Digikey", "3319P-103-ND",
	    "1/.40 10/.366 25/.33 50/.319 100/.308 250/.286")]).actual_part(
	  "Bourns", "3309P-1-103")

	# Power Supplies:

	self.choice_part("9V_444MA_4W;RAC04", "RAC04", "",
	  "AC/DC CONVERTER 9V 4W").actual_part(
	  "Recom Power", "RAC04-09SC/W", [
	   ("Digikey", "945-2211-ND",
	    "1/14.35 5/14.146 10/13.94 50/12.71 100/12.30")])

	# Resistors:

	self.choice_part("0;1608", "RESC1608X50N", "",
	  "RES SMD 0.0 OHM JUMPER 1/10W").actual_part(
	  "Vishay Dale", "CRCW06030000Z0EA").actual_part(
	  "Rohm", "MCR03EZPJ000").actual_part(
	  "Panasonic", "ERJ-3GEY0R00V").actual_part(
	  "Stackpole", "RMCF0603ZT0R00").actual_part(
	  "Bourns", "CR0603-J/-000ELF").actual_part(
	  "Yageo", "RC0603JR-070RL")
	self.choice_part("0.20_1W;6432", "RESC6432X70N", "",
	  "RES SMD 0.02 OHM 1% 1W 6432").actual_part(
	  "TE", "2176057-8", [
	    ("Digikey", "A109677CT-ND",
	     "1/.30 10/.27 100/.241")]).actual_part(
	  "TT/Welwyn", "LRMAM2512-R02FT4").actual_part(
	  "Bourns", "CRA2512-FZ-R020ELF").actual_part(
	  "Yageo", "PE2512FKE070R02L").actual_part(
	  "TE", "RLP73V3AR020JTE").actual_part(
	  "TT/Welwyn", "LRMAP2512-R02FT4").actual_part(
	  "Yageo", "PLRMAP2512-R02FT4").actual_part(
	  "Bourns", "CRF2512-FZ-R020ELF").actual_part(
	  "Yageo", "RL2512FK-070R02L").actual_part(
	  "TT/IRC", "LRC-LRF2512LF-01-R020F").actual_part(
	  "Stackpole", "CSRN2512FK20L0")
	
	self.choice_part("120;1608", "RESC1608X50N", "",
	  "RES SMD 120 OHM 5% 1/10W 1608").actual_part(
	  "Vishay Dale", "CRCW0603120RJNEA", [
	   ("Digikey", "541-120GCT-ND",
	    "10/.074 50/.04 200/.02295 1000/.01566")]).actual_part(
	  "Vishay Dale", "CRCW0603120RFKEA").actual_part(
	  "Rohm", "MCR03ERTJ121").actual_part(
	  "Rohm", "MCR03ERTF1200").actual_part(
	  "Samsung", "RC1608J121CS").actual_part(
	  "Samsung", "RC1608F121CS").actual_part(
	  "Rohm", "KTR03EZPF1200")
	self.choice_part("470;1608", "RESC1608X50N", "",
	  "RES SMD 470 5% 1/10W 1608").actual_part(
	  "Vishay Dale", "CRCW0603470RJNEA", [
	   ("Digikey", "541-470GCT-ND",
	    "10/.074 50/.04 200/.02295 1000/.01566")]).actual_part(
	  "Rohm", "MCR03ERTJ471").actual_part(
	  "Samsung", "RC1608J471CS").actual_part(
	  "Yageo", "RC0603JR-07470RP").actual_part(
	  "Vishay Dale", "RCG0603470RJNEA").actual_part(
	  "Rohm", "KTR03EZPJ471")
	self.choice_part("1K;1608", "RESC1608X50N", "",
	  "RES SMD 1K 5% 1/10W 0603").actual_part(
	  "Vishay Dale", "CRCW06031K00JNEA").actual_part(
	  "Rohm", "MCR03ERTJ102").actual_part(
	  "Yageo", "RC0603JR-071KP").actual_part(
	  "Samsung", "RC1608J102CS").actual_part(
	  "Rohm", "TRR03EZPJ102").actual_part(
	  "Vishay Dale", "RCG06031K00JNEA").actual_part(
	  "Rohm", "KTR03EZPJ102")
	self.choice_part("4K7;1608", "RESC1608X50N", "",
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
	self.choice_part("10K;1608", "RESC1608X50N", "",
	  "RES SMD 10K OHM 5% 1/10W 1608").actual_part(
	  "Vishay Dale", "RCG060310K0JNEA", [
	    ("Digikey", "541-1804-1-ND",
	     "1/.10 10/.067 25/.0484 50/.037 100/.0273")]).actual_part(
	  "Yageo", "RC0603JR-0710KL").actual_part(
	  "Panasonic", "ERJ-3GEYJ103V").actual_part(
	  "Rohm", "MCR03ERTJ103").actual_part(
	  "Rohm", "MCR03EZPJ103").actual_part(
	  "Stackpole", "RMCF0603JT10K0").actual_part(
	  "Yageo", "RC0603JR-0710KP").actual_part(
	  "Bourns", "CR0603-JW-103ELF").actual_part(
	  "Samsung", "RC1608J103CS").actual_part(
	  "Bourns", "CR0603-JW-103GLF").actual_part(
	  "Rohm", "TRR03EZPJ103").actual_part(
	  "Yageo", "AC0603JR-0710KL")
	self.choice_part("22K;1608", "RESC1608X50N", "",
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
	self.choice_part("100K;1608", "RESC1608X50N", "",
	  "RES SMD 100K OHM 5% 1/10W 1608").actual_part(
	  "Vishay Dale", "CRCW0603100KJNEAIF", [
	     ("Digikey", "541-100KAQCT-ND",
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
	  "Rohm", "MCR03ERTJ104	").actual_part(
	  "Vishay Dale", "RCA0603100KJNEA").actual_part(
	  "Rohm", "KTR03EZPJ104")

	# Switches

	# Test Points:

	self.alias_part("0.5V;M1X1", ["M1X1;M1X1"])
	self.alias_part("170VDC_FUSED;M1X1", ["M1X1;M1X1"])
	self.alias_part("170VDC_IN;M1X1", ["M1X1;M1X1"])
	self.alias_part("CAN_RDX;M1X1", ["M1X1;M1X1"])
	self.alias_part("CLEAR;M1X1", ["M1X1;M1X1"])
	self.alias_part("CURRENT_SENSE;M1X1", ["M1X1;M1X1"])
	self.alias_part("CURRENT_SET;M1X1", ["M1X1;M1X1"])
	self.alias_part("GATE;M1X1", ["M1X1;M1X1"])
	self.alias_part("GND;M1X1", ["M1X1;M1X1"])
	self.alias_part("+5V;M1X1", ["M1X1;M1X1"])
	self.alias_part("INDUCTOR_HIGH;M1X1", ["M1X1;M1X1"])
	self.alias_part("INDUCTOR_LOW;M1X1", ["M1X1;M1X1"])
	self.alias_part("MODULATE1;M1X1", ["M1X1;M1X1"])
	self.alias_part("MODULATE2;M1X1", ["M1X1;M1X1"])
	self.alias_part("RESET;M1X1", ["M1X1;M1X1"])
	self.alias_part("RXD0;M1X1", ["M1X1;M1X1"])
	self.alias_part("STOP;M1X1", ["M1X1;M1X1"])
	self.alias_part("TRIGGER;M1X1", ["M1X1;M1X1"])
	self.alias_part("TXD0;M1X1", ["M1X1;M1X1"])
	self.alias_part("XTAL1;M1X1", ["M1X1;M1X1"])

	self.alias_part("FTDI;M1X6", ["M1X6;M1X6"])
	self.alias_part("ISP_CONN;M2X3", ["M2X3;M2X3"])
	self.alias_part("ID6;M2X6", ["M2X6;M2X6"])
	self.alias_part("BUS_SLAVE;M2X5S", ["M2X5S;M2X5S"])

	# Transistors:

	self.choice_part("BSS138;SOT23", "SOT95P280X145-3N", "",
	  "MOSFET N-CH 50V+ 200MA+ SOT23").actual_part(
	  "Fairchild", "BSS138L", [
            ("Digikey", "BSS138CT-ND",
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
	   ("Digikey", "FDD7N20TMCT-ND",
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
	vendor_parts = self.vendor_parts
	for schematic_part in self.schematic_parts.values():
	    if isinstance(schematic_part, Choice_Part):
		choice_part = schematic_part
		for actual_part in choice_part.actual_parts:
		    actual_part_key = (actual_part.manufacturer_name, \
		      actual_part.manufacturer_part_name)
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
	self.vendor_part("Phoenix Contact", "1935161",
	  "Digikey", "277-1667-ND",
	  ".37/1 .352/10 .3366/50 .3274/100 .306/250 .28152/500 .255/1000")

	# Diodes:
	self.vendor_part("Fairchild", "S320",
	  "Digikey", "S320FSCT-ND",
	  ".70/1 .614/10 .5424/25 .4726/100 .4114/250 .3502/500 .2805/1000")
	self.vendor_part("Diodes Inc", "BAT54-7-F",
	  "Digikey", "BAT54-FDICT-ND",
	  ".15/1 .142/10 .128/25 .0927/100 .0546/250 .0453/500 .0309/1000")
	  
	# Holes:
	self.vendor_part("McMaster-Carr", "3MM_Hole",
	  "MMC", "123", "0./1")

	# Integrated Circuits:
	self.vendor_part("TI", "SN74LVC1G175DBVR",
	  "Digikey", "296-17617-1-ND",
	  ".40/1 .315/10 .266/25 .2166/100 .1794/250 .1482/500 .1236/750")
	self.vendor_part("Fairchild", "MM74HCT08MX",
	  "Digikey", "MM74HCT08MXCT-ND",
	  ".49/1 .412/10 .3612/25 .309/100 .268/250 .227/500 .175/1000")

	# LED's:
	self.vendor_part("Cree", "CXA3050-0000-000N0HW440F",
	  "Digikey", "CXA3050-0000-000N0HW440F-ND",
	  "36./1 34.2/10 33.23/50 30.6/100 27.83/200 26.06/500 24/1000")

	# Resistors:
	self.vendor_part("Vishay Dale", "CRCW060322K0JNEA",
	  "Digikey", "541-22KGCT-ND",
	  ".074/10 .04/50 .02295/200 .01566/1000")

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

	choice_part = Choice_Part(schematic_part_name,
	  kicad_footprint, location, description)

	return self.insert(choice_part)

    def fractional_part(self, schematic_part_name, kicad_footprint,
      whole_part_name, numerator, denominator, description):
	""" *Fractional_Part*: Insert a new *Fractional_Part* named
	    *schematic_part_name* and containing *whole_part_name*,
	    *numerator*, *denominator*, and *description*. """

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
	self.vendor_excludes = [] # List[String]: Excluded vendors
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

    def process(self):
	""" *Order*: Process the order. """

	# Sort *boards* by name:
	boards = self.boards
	boards.sort(key = lambda board:board.name)

	choice_parts_table = {}
	for board in boards:
	    #print("board:{0}".format(board.name))
	
	    # Sort board parts by reference.  A reference is a sequence
	    # letters followed by an integer.  Sort alphabetically followed
	    # by numerically:
	    board_parts = board.board_parts
	    board_parts.sort(key = lambda board_part:
	      (board_part.reference.upper(),
	       int(filter(str.isdigit, board_part.reference))) )

	    for board_part in board_parts:
		schematic_part = board_part.schematic_part
		#print("  {0}: {1}".format(board_part.reference,
		#  schematic_part.schematic_part_name))

		choice_parts = schematic_part.choice_parts()
		for choice_part in choice_parts:
		    # Make sure *choice_part* is in *choice_parts_table*
		    # exactly once:
		    schematic_part_name = choice_part.schematic_part_name
		    if not schematic_part_name in choice_parts_table:
			assert isinstance(choice_part, Choice_Part), \
			  "Not a choice part '{0}'". \
			  format(choice_part.schematic_part_name)	
			choice_parts_table[schematic_part_name] = choice_part

		    # Remember *board_part* in *choice_part*:
		    choice_part.board_parts.append(board_part)

	# Sort by *choice_parts_list* by schematic part name:
	choice_parts_list = choice_parts_table.values()
	choice_parts_list.sort(key = lambda choice_part:
	  choice_part.schematic_part_name)

	# Open the CSV (Comma Separated Value) file for BOM uploading:
	csv_file = open("/tmp/order.csv", "wa")
	# Output a one line header
	csv_file.write("Quantity,Vendor Part Name,Reference\n")

	# Open each vendor output file:
	vendor_files = {}

	# Now generate a BOM summary:
	total_cost = 0.0
	for choice_part in choice_parts_list:
	    # Sort the *board_parts* by *board* followed by reference:
	    board_parts = choice_part.board_parts
	    board_parts.sort(key = lambda board_part:
	      (board_part.board.name, board_part.reference.upper(),
	       int(filter(str.isdigit, board_part.reference))))

	    assert isinstance(choice_part, Choice_Part)
	    print("  {0}:{1};{2} {3}:{4}".\
	      format(choice_part.schematic_part_name,
	      choice_part.kicad_footprint, choice_part.description,
	      choice_part.count_get(), choice_part.references_text_get()))

	    selected_actual_part = choice_part.select()
	    assert isinstance(selected_actual_part, Actual_Part)
	    selected_vendor_part = selected_actual_part.selected_vendor_part
	    if not isinstance(selected_vendor_part, Vendor_Part):
		actual_part.select()
	    vendor_name = selected_vendor_part.vendor_name
	    if not vendor_name in vendor_files:
		vendor_files[vendor_name] = \
		  open("{0}.csv".format(vendor_name), "wa")
	    csv_file = vendor_files[vendor_name]

	    # Print out the price breaks:
	    price_breaks = selected_vendor_part.price_breaks
	    print("    {0}:{1} {2}".format(selected_vendor_part.vendor_name,
	      selected_vendor_part.vendor_part_name,
	      selected_vendor_part.price_breaks_text_get()))

	    needed = choice_part.count_get()
	    selected_price_break = price_breaks[0]
	    selected_price_break.compute(needed)
	    for price_break in price_breaks[1:]:
		price_break.compute(needed)
		if price_break.order_price < selected_price_break.order_price:
		    selected_price_break = price_break

	    # Print out the result:
	    print("        {0}@({1}/${2:.3f})={3:.2f}".format(
	      selected_price_break.order_quantity,
	      selected_price_break.quantity, selected_price_break.price,
	      selected_price_break.order_price))

	    total_cost += selected_price_break.order_price

	    # Write out another line in the *csv_file*:
	    csv_file.write("{0},{1},{2}\n".format(
	      selected_price_break.order_quantity,
	      selected_vendor_part.vendor_part_name,
	      choice_part.schematic_part_name))

	# Close all the vendor files:
	for csv_file in vendor_files.values():
	    csv_file.close()

	print("Total: ${0:.2f}".format(total_cost))

    def request(self, name, amount):
	""" *Order*: Request *amount* parts named *name*. """

	assert isinstance(name, str)
	assert isinstance(amount, int)
	inventory = Inventory(name, str)

    def vendor_exclude(self, vendor):
	""" *Order*: Exclude *vendor* from order. """

	assert isinstance(vendor, str)
	self.vendor_excludes.append(vendor)

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
	self.board_parts = []	    # List[Board_Part] board parts needed

	self.net_file_read()

    def net_file_read(self):
	""" *Board*: Read in net file for{self}. """

	# Prevent accidental double read:
	board_parts = self.board_parts
	assert len(board_parts) == 0

	errors = 0

	# Read the contents *net_file_name* into *net_text*:
	net_file_name = self.net_file_name
	if net_file_name.endswith(".net"):
	    net_stream = open(net_file_name, "ra")
	    net_text = net_stream.read()
	    net_stream.close()

	    # Parse *net_text*:
	    net_se = sexpdata.loads(net_text)
	    #print(sexpdata.dumps(net_se))
	    #print(net_se)
	    net_text = ""

	    database = self.order.database
	    components_se = se_find(net_se, "export", "components")
	    #print("components=", components_se)
	    for component_se in components_se[1:]:
		#print(component_se)

		# Grab the *ref*:
		reference_se = se_find(component_se, "comp", "ref")
		reference = reference_se[1].value()
	
		# Grab the footprint:
		footprint_se = se_find(component_se, "comp", "footprint")	
		footprint = footprint_se[1].value()

		# Strip off preceeding footprint locator:
		index = footprint.find(':')
		if index >= 0:
		    footprint = footprint[index + 1:]

		# Grab the *value*:
		part_name_se = se_find(component_se, "comp", "value")
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

		comment = ""
		colon_index = part_name.find(':')
		if colon_index >= 0:
		    comment = part_name[colon_index + 1:]
		    part_name = part_name[0:colon_index]

		part = database.lookup(part_name)
		if part == None:
		    # {part_name} is not in {database}; output an error message:
		    print(("File '{0}: Part Name '{2}' ({3} {4})" +
		      " not in database").format(net_file_name, 0,
		      part_name, reference, footprint))
		    errors = errors + 1
		else:
                    # Create the *board_part*:
                    board_part = Board_Part(self, part, reference, comment)
		    board_parts.append(board_part)
		    #part.board_parts.append(board_part)

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
			    board_parts.append(board_part)
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

class Schematic_Part:
    # A *Schematic_Part* represents part with a footprint.
    # The schematic part name must adhere to the format of "name;footprint". 
    # The footprint name can be short (e.g. 1608, QFP100, SOIC20, SOT3),
    # since it only has to disambiguate the various footprints associated
    # with "name".  A *Schematic_Part* is always sub-classed by one of
    # *Choice_Part*, *Alias_Part*, or *Fractional_Part*.

    def __init__(self, schematic_part_name, kicad_footprint):
	""" *Schematic_Part*: Initialize *self* to contain
	    *schematic_part_name*, and *kicad_footprint*. """

	# Verify argument types:
	assert isinstance(schematic_part_name, str)
	assert isinstance(kicad_footprint, str)
	
	# Split *schematic_part_name" into *base_name* and *short_footprint*:
	base_name_short_footprint = schematic_part_name.split(';')
	if len(base_name_short_footprint) == 2:
	    base_name = base_name_short_footprint[0]
	    short_footprint = base_name_short_footprint[1]

	    # Load up *self*:
	    self.schematic_part_name = schematic_part_name
	    self.base_name = base_name
	    self.kicad_footprint = kicad_footprint
	    self.board_parts = []
	else:
	    print("Schematic Part Name '{0}' has no ';' separator!".
	      format(schematic_part_name))

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
		      "Quantity '{0}' is not an integer".format(price_pair[0])

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
	last_board = None
        for board_part in self.board_parts:
	    board = board_part.board
	    if board != last_board:
		if not board:
		    references_text += "]"
		references_text += "[{0}:".format(board.name)
		last_board = board
	    references_text += " {0}".format(board_part.reference)
	references_text += "]"
	return references_text

    def select(self):
	""" *Choice_Part: Return the selected *Actual_Part* for *self*. """

	#actual_parts = self.actual_parts
	#for actual_part in actual_parts:
	#    print("       {0}:{1}".format(actual_part.manufacturer_name,
	#      actual_part.manufacturer_part_name))

	actual_parts = self.actual_parts
	selected_actual_part = actual_parts[0]
	assert isinstance(selected_actual_part, Actual_Part)
	self.selected_actual_part = selected_actual_part
	
	vendor_parts = selected_actual_part.vendor_parts
	if len(vendor_parts) == 0:
	    print("No vendor part for Actual Part '{0} {1}'". \
	      format(selected_actual_part.manufacturer_name,
	       selected_actual_part.manufacturer_part_name))
	else:
	    selected_actual_part.selected_vendor_part = vendor_parts[0]

	assert isinstance(selected_actual_part, Actual_Part)
	return selected_actual_part

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
	Schematic_Part.__init__(self, schematic_part_name, "")
	self.schematic_parts = schematic_parts
	self.kicad_footprint = kicad_footprint
	
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
     # An Actual_Part represents a single manufacturer part.
     # A list of vendor parts specifies where the part can be ordered from.

    def __init__(self, manufacturer_name, manufacturer_part_name):
	""" *Actual_Part*: Initialize *self* to contain *manufacture* and
	    *manufacturer_part_name*. """

	# Verify argument_types:
	assert isinstance(manufacturer_name, str)
	assert isinstance(manufacturer_part_name, str)

	# Load up *self*:
	self.manufacturer_name = manufacturer_name
	self.manufacturer_part_name = manufacturer_part_name
	# Fields used by algorithm:
	self.quantity_needed = 0
	self.vendor_parts = []
	self.selected_vendor_part = None

    def vendor_part_append(self, vendor_part):
	""" *Actual_Part: Append *vendor_part* to the vendor parts
	    of *self*. """

	assert isinstance(vendor_part, Vendor_Part)
	self.vendor_parts.append(vendor_part)

class Vendor_Part:
    # A vendor part represents a part that can be ordered from a vendor.

    def __init__(self, actual_part, vendor_name, vendor_part_name,
      quantity_available, price_breaks):
	""" *Vendor_Part*: Initialize *self* to contain *actual_part"""

	# Check argument types:
	assert isinstance(actual_part, Actual_Part)
	assert isinstance(vendor_name, str)
	assert isinstance(vendor_part_name, str)
	assert isinstance(quantity_available, int)
	assert isinstance(price_breaks, list)
	for price_break in price_breaks:
	    assert isinstance(price_break, Price_Break)

	# Load up *self*:
	self.actual_part = actual_part
	self.vendor_name = vendor_name
	self.vendor_part_name = vendor_part_name
	self.quantity_available = quantity_available
	self.price_breaks = price_breaks

	# Append *self* to the vendor parts of *actual_part*:
	actual_part.vendor_part_append(self)

    def price_breaks_text_get(self):
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

# class Board:
#     """ A printed circuit board. """
# 
#     def __init__(self, database, name, revision, quantity):
# 	""" {Board}: Initialize {self} to contain {name}, {database},
# 	    {revision, and {quantity}. """
# 
# 	self.board_parts = []
# 	self.database = database
# 	self.name = name
# 	self.quantity = quantity
# 	self.revision = revision
# 
#     def read(self, file_name):
# 	""" {Board}: Read {cmp_file_name} into {self}. """
# 
# 	# Prevent accidental double read:
# 	board_parts = self.board_parts
# 	assert len(board_parts) == 0
# 
# 	errors = 0
# 	database = self.database
# 
# 	# Read in the the *net_file_name*:
# 	if file_name.endswith(".net"):
# 	    net_stream = open(file_name, "ra")
# 	    net_text = net_stream.read()
# 	    net_stream.close()
# 
# 	    # Parse *net_text*:
# 	    net_se = sexpdata.loads(net_text)
# 	    #print(sexpdata.dumps(net_se))
# 	    #print(net_se)
# 	    net_text = ""
# 
# 	    components_se = se_find(net_se, "export", "components")
# 	    #print("components=", components_se)
# 	    for component_se in components_se[1:]:
# 		#print(component_se)
# 
# 		# Grab the *ref*:
# 		reference_se = se_find(component_se, "comp", "ref")
# 		reference = reference_se[1].value()
# 	
# 		# Grab the footprint:
# 		footprint_se = se_find(component_se, "comp", "footprint")	
# 		footprint = footprint_se[1].value()
# 
# 		# Strip off preceeding footprint locator:
# 		index = footprint.find(':')
# 		if index >= 0:
# 		    footprint = footprint[index + 1:]
# 
# 		# Grab the *value*:
# 		part_name_se = se_find(component_se, "comp", "value")
# 		if isinstance(part_name_se[1], Symbol):
# 		    part_name = part_name_se[1].value()
# 		elif isinstance(part_name_se[1], int):
# 		    part_name = str(part_name_se[1])
# 		elif isinstance(part_name_se[1], float):
# 		    part_name = str(part_name_se[1])
# 		elif isinstance(part_name_se[1], str):
# 		    part_name = part_name_se[1]
# 		else:
# 		    assert False, "strange part_name: {0}". \
# 		      format(part_name_se[1])
# 
# 		#print(reference, part_name, footprint)
# 
# 		double_underscore_index = part_name.find("__")
# 		if double_underscore_index >= 0:
# 		    shortened_part_name = part_name[:double_underscore_index]
# 		    #print("Shorten part name '{0}' => '{1}'".
# 		    #  format(part_name, shortened_part_name))
# 		    part_name = shortened_part_name
# 
# 		part = database.part_lookup(part_name)
# 		if part == None:
# 		    # {part_name} is not in {database}; output an error message:
# 		    print(("File '{0}: Part Name '{2}' ({3} {4})" +
# 		      " not in database").format(file_name, 0,
# 		      part_name, reference, footprint))
# 		    errors = errors + 1
# 		else:
# 		    footprint_pattern = part.footprint_pattern
# 		    if fnmatch.fnmatch(footprint, footprint_pattern):
# 			# The footprints match:
# 			board_part = \
# 			  Board_Part(self, part, reference, footprint)
# 			board_parts.append(board_part)
# 			part.board_parts.append(board_part)
# 		    else:
# 			print ("File '{0}': {2}:{3} Footprint" +
# 			  "'{4}' does not match database '{5}'").\
# 			  format(file_name, 0, \
# 			  reference, part_name, footprint, footprint_pattern)
# 			errors = errors + 1
# 
#         elif file_name.ends_with(".cmp"):
# 	    # Read in {cmp_file_name}:
# 	    cmp_stream = open(file_name, "r")
# 	    cmp_lines = cmp_stream.readlines()
# 	    cmp_stream.close()
# 
# 	    # Process each {line} in {cmp_lines}:
# 	    database = self.database
# 	    errors = 0
# 	    line_number = 0
# 	    for line in cmp_lines:
# 		# Keep track of {line} number for error messages:
# 		line_number = line_number + 1
# 
# 		# There are three values we care about:
# 		if line.startswith("BeginCmp"):
# 		    # Clear out the values:	
# 		    reference = None
# 		    part_name = None
# 		    footprint = None
# 		elif line.startswith("Reference = "):
# 		    reference = line[12:-2]
# 		elif line.startswith("ValeurCmp = "):
# 		    part_name = line[12:-2]
# 		    #print("part_name:{0}".format(part_name))
# 		    double_underscore_index = part_name.find("__")
# 		    if double_underscore_index >= 0:
# 			shortened_part_name = \
# 			  part_name[:double_underscore_index]
# 			#print("Shorten part name '{0}' => '{1}'".
# 			#  format(part_name, shortened_part_name))
# 			part_name = shortened_part_name
# 		elif line.startswith("IdModule  "):
# 		    footprint = line[12:-2].split(':')[1]
# 		    #print("footprint='{0}'".format(footprint))
# 		elif line.startswith("EndCmp"):
# 		    part = database.part_lookup(part_name)
# 		    if part == None:
# 			# {part_name} not in {database}; output error message:
# 			print(("File '{0}', line {1}: Part Name {2} ({3} {4})" +
# 			  " not in database").format(cmp_file_name, line_number,
# 			  part_name, reference, footprint))
# 			errors = errors + 1
# 		    else:
# 			footprint_pattern = part.footprint_pattern
# 			if fnmatch.fnmatch(footprint, footprint_pattern):
# 			    # The footprints match:
# 			    board_part = \
# 			      Board_Part(self, part, reference, footprint)
# 			    board_parts.append(board_part)
# 			    part.board_parts.append(board_part)
# 			else:
# 			    print ("File '{0}',  line {1}: {2}:{3} Footprint" +
# 			      "'{4}' does not match database '{5}'"). \
# 			      format(cmp_file_name, line_number,
# 			      reference, part_name, footprint,
# 			      footprint_pattern)
# 			    errors = errors + 1
# 		elif line == "\n" or line.startswith("TimeStamp") or \
# 		  line.startswith("EndListe") or line.startswith("Cmp-Mod V01"):
# 		    # Ignore these lines:
# 		    line = line
# 		else:
# 		    # Unrecognized {line}:
# 		    print "'{0}', line {1}: Unrecognized line '{2}'". \
# 		      format(cmp_file_name, line_number, line)
# 		    errors = errors + 1
# 
# 	return errors
# 
# class Board_Part:
#     """ A part located on a board.  """
# 
#     def __init__(self, board, part, reference, footprint):
# 	""" {Board_Part}: Initialize {self} to contain {board}, {part_name},
# 	    {reference}, and {footprint}. """
# 
# 	# Make sure that no bogus values are passed in:
# 	assert board != None
# 	assert part != None
# 	assert reference != None
# 	assert footprint != None
# 
# 	# Load up {self}:
# 	self.board = board
# 	self.part = part
# 	self.reference = reference
# 	self.footprint = footprint
# 
# class Database:
#     """ Parts databse. """
# 
#     def __init__(self):
# 	""" {Database}: Initialize {self}.  """
# 	self.parts = {}
# 	self.vendor_parts = {}
# 	self.date = None
# 
#     def date_set(self, date):
# 	""" {Database}: Set date for {self} to {date}. """
# 
# 	self.date = date
# 
#     def fractional_part(self, part_name, footprint_pattern, parent_part_name, \
#       fraction_numerator, fraction_denominator):
# 	""" {Database}: Create a fractional part named {part_name}
# 	    that is a {fraction_numerator}/{fraction_denominator}'th
# 	    of the part named {part_part_name}.  An error occurs
# 	    if {part_name} is already defined or {parent_part_name}
# 	    is not defined. """
# 
# 	# Check fraction to make sure it makes sense:
# 	assert fraction_denominator >= fraction_numerator and \
# 	  fraction_numerator > 0, \
# 	  "Numerator ({0}) is too big for denominator ({1}) for part '{2}'". \
# 	  format(fraction_numerator, fraction_denominator, parent_part_name)
# 
# 	# Verify that {part_name} does not exist:
# 	assert self.part_lookup(part_name) == None, \
# 	  "Fractional part '{0}' already exists".format(part_name)
# 
# 	# Verify that {parent_part_exists}:
# 	parent_part = self.part_lookup(parent_part_name)
# 	assert parent_part != None, "Parent part '{0}' does not exist". \
# 	  format(parent_part_name)
# 
# 	# Create the new part and fill in the fraction fields:
# 	part = self.part_create(part_name, footprint_pattern)
# 	part.fraction_numerator = fraction_numerator
# 	part.fraction_denominator = fraction_denominator
# 	part.fraction_parent = parent_part
# 
# 	# Make sure that {part} is taked onto {fraction_parts}
# 	# of {parent_part}:
# 	fraction_parts = parent_part.fraction_parts
# 	if fraction_parts == None:
# 	    fraction_parts = []
# 	    parent_part.fraction_parts = fraction_parts
# 	fraction_parts.append(part)
# 
#     def multiple_part(self, part_name, footprint_pattern, parent_part_names):
# 	""" {Database}: Create a multiple part named {part_name} with a
# 	    footprint pattern of {footprint_pattern} and contains the parts
# 	    named {parent_part_names}.  An error occurs if {part_name}
# 	    is already defined or if any of the parts named in
# 	    {parent_part_names} does not exist. """
# 
# 	# Lookup the {part} associated with {part_name}:
# 	assert self.part_lookup(part_name) == None, \
# 	  "Mulitple part '{0}' already exists".format(part_name)
# 	part = self.part_create(part_name, footprint_pattern)
# 	multiple_parts = []
# 	part.multiple_parts = multiple_parts
# 
# 	# Build up {multiple_parts} by iterating over {parent_part_names}:
# 	for parent_part_name in parent_part_names:
# 	    parent_part = self.part_lookup(parent_part_name)
# 	    assert parent_part != None, \
# 	      "Multiple part '{0}' does not exits".format(parent_part_name)
# 	    multiple_parts.append(parent_part)
# 
#     def part(self, part_name, footprint_pattern, mfg_part_name,
#       vendor_name, vendor_part_name, vendor_part_prices,
#       mfg="", description=""):
# 	""" {Database}: If necessary, create a new {Part} for {part_name}.
# 	    If the {Part} for {part_name} already exists, ensure that
# 	    {footprint_pattern} matches the previous definition.  Create
# 	    (or reuse) a {Vendor_Part} that contains {vendor_name},
# 	    {mfg_part_name}, {vendor_part_name}, and {vendor_part_prices}.
# 	    {vendor_part_prices} is of the form
# 	    "cost1/quantity1 ... costN/quantityN", where cost is
# 	    a decimal number (in dollars) and quantity is an integer. """
# 
# 	# Lookup {part}:
# 	part = self.part_lookup(part_name)
# 	if part == None:
# 	    # {part} does not exist yet; create it:
# 	    part = self.part_create(part_name, footprint_pattern)
# 	else:
# 	    # Make sure the {part} values do not conflict:
# 	    assert part.footprint_pattern == footprint_pattern, \
# 	      "'{0}' != '{1}'".format(part.footprint_pattern, footprint_pattern)
# 
# 	# Lookup {vendor_part}:
# 	vendor_part = self.vendor_part_lookup(vendor_name, vendor_part_name)
# 	if vendor_part == None:
# 	    # {vendor_part} does not exist yet:
# 	    vendor_part = Vendor_Part(mfg_part_name, vendor_name, \
# 	      vendor_part_name, vendor_part_prices, self.date, part, mfg,
# 	      description)
# 	    self.vendor_parts[ (vendor_name, vendor_part_name) ] = vendor_part
# 	else:
# 	    # {vendor_part} exists, make sure the prices have not changed:
# 	    assert vendor_part.vendor_part_prices == vendor_part_prices, \
# 	      "Part '{0}': prices '{1}' do not match previous prices '{2}'". \
# 	      format(part_name, vendor_part.vendor_part_prices, \
# 	      vendor_part_prices)
# 
# 	# Keep a list of all valid {Vendor_Part}'s associated with {part}:
# 	part.vendor_parts.append(vendor_part)
# 
# 
#     def part_create(self, part_name, footprint_pattern):
# 	""" {Database}: Create a new {Part} named {part_name} that
# 	    contains {footprint_pattern} and insert it into {self}.
# 	    The created {Part} is returned. """
# 
# 	parts = self.parts
# 	assert not (part_name in parts), \
# 	  "Part '{0}' already exists". format(part_name)
# 	part = Part(part_name, footprint_pattern)
# 	self.parts[part_name] = part
# 
# 	return part
# 
#     def part_lookup(self, part_name):
# 	""" {Database}: Return {Part} associated with {part_name} or {None}
# 	    if {part_name} is not in {self}. """
# 
# 	parts = self.parts
# 	part = None
# 	if part_name in parts:
# 	    part = parts[part_name]
# 	#print("Database.part_lookup('{0}')=>{1}".format(part_name, part))
# 	return part
# 
#     def vendor_part_lookup(self, vendor_name, vendor_part_name):
# 	""" {Database}: Return the {Vendor_Part} associated with
# 	    {vendor_name} and {vendor_part_name} or {None}
# 	    if it does not exist. """
# 
# 	vendor_parts = self.vendor_parts
# 	vendor_part = None
# 	vendor_part_key = (vendor_name, vendor_part_name)
# 	if vendor_part_key in vendor_parts:
# 	    vendor_part = vendor_parts[vendor_part_key]
# 	return vendor_part
# 
# class Drawer:
#     """ A parts drawer """
# 
#     def __init__(self, part, catagory_name, name_override, mfg_override):
# 	""" {Drawer}: Initialize {self} to contain {part}, {catagory_name},
# 	    {name_override} and {mfg_override}. """
# 
# 	self.part = part
# 	self.catagory_name = catagory_name
# 	self.name_override = name_override
# 	self.mfg_override = mfg_override
# 	self.width = 1.875
# 	self.height = 4.500
# 
#     def write(self, svg, x, y):
# 	""" {Drawer}:  Write out {self} to {svg} with upper left corner
# 	    at ({x}, {y}).  """
# 
# 	width = self.width
# 	height = self.height
# 	svg.rectangle(x, y, width, height, "black", "white")
# 	svg.rectangle(x, y, width, 0.500, "black", "white")
# 
# 	part = self.part
# 	part_name = part.name
# 	vendor_parts = part.vendor_parts
# 	mfg_part_name = ""
# 	if len(vendor_parts) != 0:
# 	    mfg_part_name = vendor_parts[0].mfg_part_name
# 
# 	catagory_name = self.catagory_name
# 	name_override = self.name_override
# 	mfg_override = self.mfg_override
# 	
# 	if name_override != None:
# 	    part_name = name_override
# 	if mfg_override != None:
# 	    mfg_part_name = mfg_override
# 
# 	x_center = x + width / 2.0
# 	svg.text("{0}: {1}".format(catagory_name, part_name), \
# 	  x_center, y + .200, "ariel", 15)
# 	svg.text(mfg_part_name, x_center, y + .440, "ariel", 15)
# 
# 	dy = 0.75
# 	for vendor_part in vendor_parts:
# 	    svg.text("{0}:".format(vendor_part.vendor_name), \
# 	      x_center, y + dy, "ariel", 15)
# 	    dy += 0.20
# 	    svg.text(vendor_part.vendor_part_name, \
# 	      x_center, y + dy, "ariel", 15)
# 	    dy += 0.250
# 
# class Order:
#     """ A parts order. """
# 
#     def __init__(self, database, name):
# 	""" {Order}: Initialize {self} to contain {name}. """
# 
# 	self.actual_parts_table = {}
# 	self.boards = []
# 	self.database = database
# 	self.drawers = []
# 	self.fractional_parts_table = {}
# 	self.errors = 0
# 	self.name = name
# 	self.vendor_excludes = {}
# 
#     def board(self, name, cmp_file_name, revision, quantity):
# 	""" {Order}: Read in a {Board} named {name} from {cmp_file_name}.
# 	    Set the board quantity to {quantity}. """
# 
# 	board = Board(self.database, name, revision, quantity)
# 	self.errors = self.errors + board.read(cmp_file_name)
# 	self.boards.append(board)
# 
#     def board_part_needed(self, board_part):
# 	""" {Order}: Register that {boad_part} is needed with {self}. """
# 
# 	# Extract some values from {board_part}:
# 	board = board_part.board
# 	needed_quantity = board.quantity
# 	part = board_part.part
# 
# 	# Grab a couple of tables from {self}:
# 	actual_parts_table = self.actual_parts_table
# 	fractional_parts_table = self.fractional_parts_table
# 
# 	# A stand-alone {Part} has both {fraction_parent} and {multiple_parts}
# 	# set to {None}:
# 	fraction_parent = part.fraction_parent
# 	multiple_parts = part.multiple_parts
# 
# 	# There are three kinds of {part} -- fractional, multiple,
# 	# and stand-alone:
# 	if fraction_parent != None:
# 	    # {part} is a fractional part, make sure {fraction_parent} is
# 	    # in {actual_parts}:
# 	    actual_parts_table[fraction_parent.name] = fraction_parent
# 	    part.needed_quantity += needed_quantity
# 	    fractional_parts_table[fraction_parent.name] = fraction_parent
# 	elif multiple_parts != None:
# 	    # {part} is a multiple part; copy the {board_parts}
# 	    # into each {Part} in {multiple_parts}:
# 	    for multiple_part in multiple_parts:
# 		multiple_part.board_parts.append(board_part)
# 		multiple_part.needed_quantity += needed_quantity
# 		actual_parts_table[multiple_part.name] = multiple_part
# 	else:
# 	    # {part} is a stand-alone part:
# 	    actual_parts_table[part.name] = part
# 	    part.needed_quantity += needed_quantity
# 
#     def generate(self):
# 	""" {Order}: Generate the order recommendations for {self}. """
# 
# 	errors = self.errors
# 	if errors != 0:
# 	    print "Order '{0}' has {1} errors".format(self.name, errors)
# 	print "Database has {0} parts".format(len(self.database.parts.keys()))
# 
# 	# Iterate over all the {boards_parts} for all of the {boards}:
# 	for board in self.boards:
# 	    board_quantity = board.quantity
# 
# 	    # Visit each {board_part} in {board}:
# 	    for board_part in board.board_parts:
# 		# Extract some values from {part}:
# 		self.board_part_needed(board_part)
# 
# 	# Now deal with {fractional_parts_table}:
# 	for parent_part in self.fractional_parts_table.values():
# 	    needed_quantity = 0
# 	    for fraction_part in parent_part.fraction_parts:
# 		# Fractional physical parts for one logical part:
# 		items_per_whole = fraction_part.fraction_denominator /  \
# 		  fraction_part.fraction_numerator
# 		fractional_wholes = \
# 		  float(fraction_part.needed_quantity) / float(items_per_whole)
# 		needed_quantity += int(math.ceil(fractional_wholes))
# 	    parent_part.needed_quantity += needed_quantity
# 
# 	# For each {part} select the low cost {vender_part}:
# 	actual_parts = self.actual_parts_table.values()
# 	total_cost = 0.0
# 	for part in actual_parts:
# 	    # Figure out {order_quantity}:
# 	    #trace = part.name == "TTL-232R-3V3"
# 
# 	    order_quantity = max(0, part.requested_quantity, \
# 	      part.needed_quantity - part.inventory_quantity)
# 	    part.order_quantity = order_quantity
# 
# 	    #if trace:
# 	    #	print("{0}: order_quantity={0}".format(
# 	    #	  part.name, order_quantity))
# 
# 	    # Now compute {order_cost} for {order_quantiy} {part}'s:
# 	    order_cost = part.cost_compute(order_quantity, self.vendor_excludes)
# 	    #if trace:
# 	    #	print("{0}: order_cost={1}".format(part.name, order_cost))
# 	    #print "{0} r={1} n={2} i={3} o={4} c={5:.2f}".format(part.name, \
# 	    #  part.requested_quantity, part.needed_quantity, \
# 	    #  part.inventory_quantity, part.order_quantity, \
# 	    #  part.order_quantity, order_cost)
# 
# 	    # Update {total_cost}:
# 	    total_cost += order_cost
# 	print "{0} parts need to be ordered".format(len(actual_parts))
# 	print "Total Cost=${0:.2f}".format(total_cost)
# 	
# 	# Output the vendor part sorted by part name:
# 	actual_parts.sort(key = lambda part: part.name)
# 	self.write(actual_parts, "by_name")
# 	self.csv_write(actual_parts, "bom")
# 
# 	# Output the vendor parts sorted by vendor name and vendor part name:
# 	actual_parts.sort(key = lambda part: part.selected_vendor_part.key)
# 	self.write(actual_parts, "by_vendor")
# 
# 	# Output the vendor part sorted by total cost:
# 	actual_parts.sort(key = lambda part: part.order_cost)
# 	self.write(actual_parts, "by_cost")
# 	     
# 	# Output the vendor part sorted by total cost:
# 	actual_parts.sort(key = lambda part: part.name)
# 	self.short_write(actual_parts, "by_short")
# 	     
# 	# Output by board, by part name, by reference:
# 	# Iterate over all the {boards_parts} for all of the {boards}:
# 	for board in self.boards:
# 	    board_quantity = board.quantity
# 
# 	    # Visit each {board_part} in {board}:
# 	    board_parts_by_part_name = {}
# 	    for board_part in board.board_parts:
# 		part_name = board_part.part.name
# 		if part_name in board_parts_by_part_name:
# 		    # Append to preexisting list:
# 		    board_parts_by_part_name[part_name].append(board_part)
# 		else:
# 		    # Create the list and fill it with {board_part}:
# 		    board_parts_by_part_name[part_name] = [board_part]
# 
# 	    # Sort {part_names}:
# 	    part_names = board_parts_by_part_name.keys()
# 	    part_names.sort()
# 
# 	    # Now construct a list of part name, and board parts list pairs:
# 	    pairs = []
# 	    for part_name in part_names:
# 		board_parts = board_parts_by_part_name[part_name]
# 		pair = (board_parts[0].reference, part_name)
# 		#print "pair=", pair
# 		pairs.append(pair)
# 
# 	    # Sort by first part reference:
# 	    pairs.sort()
# 	    #print "pairs=", pairs
# 
# 	    # Output the board file:
# 	    board_stream = open(board.name.lower() + "_board.parts", "w")
# 	    board_stream.write("{0} Rev. {1}:\n\n". \
# 	      format(board.name, board.revision))
# 	    for pair in pairs:
# 		part_name = pair[1]
# 		board_parts = board_parts_by_part_name[part_name]
# 		board_stream.write("{0}\n".format(part_name))
# 		board_stream.write("    {0}:".format(len(board_parts)))
# 		for board_part in board_parts:
# 		    board_stream.write(" {0}".format(board_part.reference))
# 		board_stream.write("\n")
# 	    board_stream.close()		    
# 
# 	# Output any {drawers}:
# 	x_across = 4
# 	y_span = 2
# 	drawers_per_page = x_across * y_span
# 
# 	svg = None
# 
# 	# Output each {drawer} in {drawers}:
# 	drawers = self.drawers
# 	for index in range(0, len(drawers)):
# 	    drawer = drawers[index]
# 	    page_index = index % drawers_per_page
# 
# 	    # Make sure {svg} is open to correct page:
# 	    if page_index == 0:
# 		if svg != None:
# 		    svg.close()
# 		svg = SVG("drawer{0}.svg". \
# 		  format(index / drawers_per_page + 1), 8.5, 11.0, "in")
# 
# 	    # Output {drawer} to {svg} to correct {row} and {column}:
# 	    column = page_index % x_across
# 	    row = page_index / x_across
# 	    drawer.write(svg, \
# 	      0.5 + column * drawer.width, 0.5 + row * drawer.height)
# 
# 	# Make sure we close out {svg} if it is still open:
# 	if svg != None:
# 	    svg.close()
# 
#     def inventory(self, part_name, inventory_quantity):
# 	""" {Order}: Record that {part_name} has a current inventory
# 	    count of {inventory_quantity}.  """
# 
# 	database = self.database
# 	part = database.part_lookup(part_name)
# 	assert part != None, \
# 	  "No part named '{0}' in inventory".format(part_name)
# 	part.inventory_quantity = inventory_quantity
# 
#     def drawer(self, part_name, catagory_name, name_override, mfg_override):
# 	""" """
# 
# 	part = self.database.part_lookup(part_name)
# 	drawer = Drawer(part, catagory_name, name_override, mfg_override)
# 	self.drawers.append(drawer)
# 
#     def request(self, part_name, requested_quantity):
# 	""" {Order}: Request that at lease {requested_quantity}
# 	    {part_name}'s be ordered for {self}. """
# 
# 	# Check for errors:
# 	part = self.database.part_lookup(part_name)
# 	assert part != None, \
# 	  "No part named '{0}' in database to add".format(part_name)
# 	assert part.fraction_parent == None and part.multiple_parts == None, \
# 	  "'{0}' is not a stand-alone part".format(part.name)
# 
# 	# Set the {requested_quantity}:
# 	part.requested_quantity = requested_quantity
# 
# 	# Make sure that we know that we need {part}:
# 	self.actual_parts_table[part.name] = part
# 
#     def csv_write(self, vendor_parts, csv_name):
# 	""" {Order}: Write *vendor_parts* out to *csv_name*.csv . """
# 
# 	out_stream = open(self.name + "_" + csv_name + ".csv", "wa")
# 	out_stream.write(
# 	  "Quanity,Distributor,Distributor PN,Manufacturer," +
# 	  "Manufacturer PN,Schematic Name,Footprint,Description," + 
# 	  "PCB References\n\n")
# 	for vendor_part in vendor_parts:
# 	    assert isinstance(vendor_part, Part), \
# 	      "{0}".format(vendor_part)
# 	    vendor_part.csv_write(out_stream)
# 	out_stream.close()
# 
#     def short_write(self, vendor_parts, suffix):
# 	""" {Order}: Write out {vendor_parts} with a file name that
# 	    ends with {suffix}. """
# 
# 	out_stream = open(self.name + "." + suffix, "w")
# 	for vendor_part in vendor_parts:
# 	    vendor_part.short_write(out_stream)	
# 	out_stream.close()
# 
#     def vendor_exclude(self, vendor):
# 	""" {Order}: Exclude {vendor} from order {self}. """
# 
# 	self.vendor_excludes[vendor] = "excluded"
# 
#     def write(self, vendor_parts, suffix):
# 	""" {Order}: Write out {vendor_parts} with a file name that
# 	    ends with {suffix}. """
# 
# 	out_stream = open(self.name + "." + suffix, "w")
# 	for vendor_part in vendor_parts:
# 	    vendor_part.write(out_stream)	
# 	out_stream.close()
# 
# class Part:
#     """ A Part """
# 
#     def __init__(self, name, footprint_pattern):
# 	""" {Part}: Initialize {self} to contain {name} and
# 	    {footprint_pattern}. """
# 
# 	# Load up {self}:
# 	self.board_parts = []
# 	self.footprint_pattern = footprint_pattern
# 	self.name = name
# 
# 	# {inventory_quantity} is the number of parts currently in inventory.
# 	# {order_cost} is the cost of the parts:
# 	# {order_quantity} the final number of parts to order.
# 	# {needed_quantity} is the number of parts actually needed.
# 	# {requested_quantity} is user requested number of needed parts.
# 	self.inventory_quantity = 0
# 	self.needed_quantity = 0
# 	self.order_cost = 0.0
# 	self.order_quantity = 0
# 	self.requested_quantity = 0
# 
# 	# A fractional part is really an alias for another part.
# 	# A fractional part sets the {fraction_numerator},
# 	# {fraction_denonominator} and {fraction_parent}.
# 	# The parent part adds the fractional part to {fraction_parts}:
# 	self.fraction_denominator = 1
# 	self.fraction_numerator = 1
# 	self.fraction_parent = None
# 	self.fraction_parts = None
# 
# 	# A multiple part is really an alias for multiple parts grouped
# 	# together.  {mulitple_parts} is set to the list of needed parts.
# 	# There can be duplicates in {mulitple_parts}:
# 	self.multiple_parts = None
# 
# 	# A stand-alone part (i.e. neither a multiple part nor a fractional    
# 	# part) occurs when both {fraction_parts} and {multiple_parts} is set
# 	# to {None}.
# 
# 	# {vendor_parts} contains all the acceptable vendors for {self}:
# 	self.vendor_parts = []
# 
# 	# The selected low cost {Vendor_Part} selected from {vendor_parts}:
# 	self.selected_vendor_part = None
# 
#     def cost_compute(self, order_quantity, vendor_excludes):
# 	""" {Part}: Compute the price of {order_quantity} {self}'s
# 	    and return it. {vendor_excludes} is a table of excluded vendors. """
# 
# 	#trace = self.name = "TTL-232R-3V3"
# 
# 	# Compute the costs for all the possible vendors:
# 	vendor_parts = self.vendor_parts
# 	assert len(vendor_parts) > 0, \
# 	  "Part {0} has no vendor parts".format(self.name)
# 	for vendor_part in vendor_parts:
# 	    vendor_part.cost_compute(order_quantity)
# 
#             # Exclude a vendor by increasing cost 1000 fold:
# 	    if vendor_part.vendor_name in vendor_excludes:
# 		vendor_part.order_cost *= 1000.0
# 
# 	# Sort by {order} cost and select the lowest one:
# 	vendor_parts.sort(key = lambda vendor_part: vendor_part.order_cost)
# 	selected_vendor_part = vendor_parts[0]
# 	self.selected_vendor_part = selected_vendor_part
# 
# 	# Treat case of {order_quantity} zero separately:
# 	if order_quantity == 0:
# 	    self.order_quantity = 0
# 	    self.order_cost = 0.0
# 	else:
# 	    # Update the final {order_cost} and {order_quantity}:
# 	    self.order_cost = selected_vendor_part.order_cost
# 	    self.order_quantity = selected_vendor_part.order_quantity
# 
# 	return self.order_cost
# 
#     def csv_write(self, out_stream):
# 	""" {Part}: Write {self} to {out_stream} as comma separated values. """
# 
# 	# Output the first line:
# 	order_quantity = self.order_quantity
# 	selected_vendor_part = self.selected_vendor_part
# 	selected_price_quantity = selected_vendor_part.selected_price_quantity
# 	selected_price = selected_price_quantity.price
# 	field1 = "{0}@${1:.2f}/{2}".format(order_quantity, \
# 	  selected_price_quantity.price, selected_price_quantity.quantity)
# 	if order_quantity == 0:
# 	    field1 = "---"
# 	field2 = " " * max(15 - len(field1), 0)
# 	needed = self.needed_quantity
# 	requested = self.requested_quantity
# 	#out_stream.write( \
# 	#  "{0}{1}=${2:.2f}\t{3} (needed={4} inventory={5} requested={6})\n". \
# 	#  format(field1, field2, self.order_cost, self.name, \
# 	#  needed, self.inventory_quantity, requested))
# 	name = self.name
# 	#out_stream.write("{0}{1}\t".format(name, ' ' * (20 - len(name))))
# 
# 	# Output the vendor line:
# 	#selected_vendor_part.write(max(needed, requested), out_stream)
# 
# 	self.csv_board_parts_write(selected_vendor_part, name, out_stream)
# 
# 	# Output the fractional parts:
# 	fraction_parts = self.fraction_parts
# 	if fraction_parts != None:
# 	    for fraction_part in fraction_parts:
# 		if fraction_part.needed_quantity > 0:
# 		    #out_stream.write("\t\t\t\t{0}/{1} {2} (needed={3})\n". \
# 		    #  format(fraction_part.fraction_numerator, \
# 		    #  fraction_part.fraction_denominator, \
# 		    #  fraction_part.name, fraction_part.needed_quantity))
# 		    fraction_part.csv_board_parts_write(
# 		      selected_vendor_part, name, out_stream)
# 
#     def write(self, out_stream):
# 	""" {Part}: Write {self} to {out_stream}. """
# 
# 	# Output the first line:
# 	order_quantity = self.order_quantity
# 	selected_vendor_part = self.selected_vendor_part
# 	selected_price_quantity = selected_vendor_part.selected_price_quantity
# 	selected_price = selected_price_quantity.price
# 	field1 = "{0}@${1:.2f}/{2}".format(order_quantity, \
# 	  selected_price_quantity.price, selected_price_quantity.quantity)
# 	if order_quantity == 0:
# 	    field1 = "---"
# 	field2 = " " * max(15 - len(field1), 0)
# 	needed = self.needed_quantity
# 	requested = self.requested_quantity
# 	out_stream.write( \
# 	  "{0}{1}=${2:.2f}\t{3} (needed={4} inventory={5} requested={6})\n". \
# 	  format(field1, field2, self.order_cost, self.name, \
# 	  needed, self.inventory_quantity, requested))
# 
# 	# Output the vendor line:
# 	selected_vendor_part.write(max(needed, requested), out_stream)
# 
# 	self.board_parts_write("\t\t\t\t", out_stream)
# 
# 	# Output the fractional parts:
# 	fraction_parts = self.fraction_parts
# 	if fraction_parts != None:
# 	    for fraction_part in fraction_parts:
# 		out_stream.write("\t\t\t\t{0}/{1} {2} (needed={3})\n". \
# 		  format(fraction_part.fraction_numerator, \
# 		    fraction_part.fraction_denominator, \
# 		    fraction_part.name, fraction_part.needed_quantity))
# 		fraction_part.board_parts_write("\t\t\t\t\t", out_stream)
# 	
#     def short_write(self, out_stream):
# 	""" {Part}: Write {self} to {out_stream}. """
# 
# 	# Output the first line:
# 	order_quantity = self.order_quantity
# 	selected_vendor_part = self.selected_vendor_part
# 	selected_price_quantity = selected_vendor_part.selected_price_quantity
# 	selected_price = selected_price_quantity.price
# 	field1 = "{0}@${1:.2f}/{2}".format(order_quantity, \
# 	  selected_price_quantity.price, selected_price_quantity.quantity)
# 	if order_quantity == 0:
# 	    field1 = "---"
# 	field2 = " " * max(15 - len(field1), 0)
# 	needed = self.needed_quantity
# 	requested = self.requested_quantity
# 	#out_stream.write( \
# 	#  "{0}{1}=${2:.2f}\t{3} (needed={4} inventory={5} requested={6})\n". \
# 	#  format(field1, field2, self.order_cost, self.name, \
# 	#  needed, self.inventory_quantity, requested))
# 	name = self.name
# 	#out_stream.write("{0}{1}\t".format(name, ' ' * (20 - len(name))))
# 
# 	# Output the vendor line:
# 	#selected_vendor_part.write(max(needed, requested), out_stream)
# 
# 	self.short_board_parts_write("\t\t\t\t", name, out_stream)
# 
# 	# Output the fractional parts:
# 	fraction_parts = self.fraction_parts
# 	if fraction_parts != None:
# 	    for fraction_part in fraction_parts:
# 		if fraction_part.needed_quantity > 0:
# 		    #out_stream.write("\t\t\t\t{0}/{1} {2} (needed={3})\n". \
# 		    #  format(fraction_part.fraction_numerator, \
# 		    #  fraction_part.fraction_denominator, \
# 		    #  fraction_part.name, fraction_part.needed_quantity))
# 		    fraction_part.short_board_parts_write(
# 		      "\t\t\t\t\t", name, out_stream)
# 
#     def board_parts_write(self, indent, out_stream):
# 	""" {Part}: Write the board parts for {self} to {out_stream}
# 	    indented by {indent}. """
# 
# 	# Now we figure out how many {boards} we have:
# 	board_parts = self.board_parts
# 	boards_table = {}
# 	for board_part in board_parts:
# 	    # Grab {board} and its_name:
# 	    board = board_part.board
# 	    board_name = board.name
# 
# 	    # Is this the first time we have seen {board}:
# 	    if board_name in boards_table:
# 		# No; grab the previous {board_parts_list}:
# 		board_parts_list = boards_table[board_name]
# 	    else:
# 		# Yes; create {board_parts_list}:
# 		board_parts_list = []
# 		boards_table[board_name] = board_parts_list
# 
# 	    # Stuff {board_part} onto the list:
# 	    board_parts_list.append(board_part)
# 
# 	# Visit the boards in alphabetical order:
# 	board_names = boards_table.keys()
# 	board_names.sort()
# 	for board_name in board_names:
# 	    board_parts_list = boards_table[board_name]
# 
# 	    # Contruct a list of {references}:
# 	    prefix = ""
# 	    references = ""
# 	    for board_part in board_parts_list:
# 		# We need {board} for the print statment below:
# 		board = board_part.board
# 		references = references + prefix + board_part.reference
# 		prefix = " "
# 		references = references
# 
# 	    # Output the board line:
# 	    out_stream.write("{0}{1} {2} {3} ({4})\n". \
# 	      format(indent, board.quantity, board_name, \
# 	      len(board_parts_list), references))
# 
#     def csv_board_parts_write(self, vendor_part, name, out_stream):
# 	""" *Part*: Write the board parts for *self* to *out_stream*
# 	    indented by {indent}. """
# 
# 	# Check argument types:
# 	assert isinstance(vendor_part, Vendor_Part)
# 	assert isinstance(name, str)
# 	assert isinstance(out_stream, file)
# 
# 	# Now we figure out how many {boards} we have:
# 	board_parts = self.board_parts
# 	boards_table = {}
# 	for board_part in board_parts:
# 	    # Grab {board} and its_name:
# 	    board = board_part.board
# 	    board_name = board.name
# 
# 	    # Is this the first time we have seen {board}:
# 	    if board_name in boards_table:
# 		# No; grab the previous {board_parts_list}:
# 		board_parts_list = boards_table[board_name]
# 	    else:
# 		# Yes; create {board_parts_list}:
# 		board_parts_list = []
# 		boards_table[board_name] = board_parts_list
# 
# 	    # Stuff {board_part} onto the list:
# 	    board_parts_list.append(board_part)
# 
# 	# Visit the boards in alphabetical order:
# 	board_names = boards_table.keys()
# 	board_names.sort()
# 	for board_name in board_names:
# 	    board_parts_list = boards_table[board_name]
# 
# 	    # Contruct a list of {references}:
# 	    prefix = ""
# 	    references = ""
# 	    count = 0
# 	    footprint = ""
# 	    for board_part in board_parts_list:
# 		# We need {board} for the print statment below:
# 		board = board_part.board
# 		footprint = board_part.footprint
# 		references = references + prefix + board_part.reference
# 		prefix = " "
# 		references = references
# 		count += 1
# 
# 	    # Output the board line:
# 	    if vendor_part.vendor_name != "McMaster":
# 		out_stream.write("{0},{1},{2},{3},{4},{5},{6},{7},{8}\n".format(
# 		  count, vendor_part.vendor_name, vendor_part.vendor_part_name,
# 		  vendor_part.mfg, vendor_part.mfg_part_name, name, footprint,
# 		  vendor_part.description, references))
# 
#     def short_board_parts_write(self, indent, name, out_stream):
# 	""" {Part}: Write the board parts for {self} to {out_stream}
# 	    indented by {indent}. """
# 
# 	# Now we figure out how many {boards} we have:
# 	board_parts = self.board_parts
# 	boards_table = {}
# 	for board_part in board_parts:
# 	    # Grab {board} and its_name:
# 	    board = board_part.board
# 	    board_name = board.name
# 
# 	    # Is this the first time we have seen {board}:
# 	    if board_name in boards_table:
# 		# No; grab the previous {board_parts_list}:
# 		board_parts_list = boards_table[board_name]
# 	    else:
# 		# Yes; create {board_parts_list}:
# 		board_parts_list = []
# 		boards_table[board_name] = board_parts_list
# 
# 	    # Stuff {board_part} onto the list:
# 	    board_parts_list.append(board_part)
# 
# 	# Visit the boards in alphabetical order:
# 	board_names = boards_table.keys()
# 	board_names.sort()
# 	for board_name in board_names:
# 	    board_parts_list = boards_table[board_name]
# 
# 	    # Contruct a list of {references}:
# 	    prefix = ""
# 	    references = ""
# 	    count = 0
# 	    for board_part in board_parts_list:
# 		# We need {board} for the print statment below:
# 		board = board_part.board
# 		references = references + prefix + board_part.reference
# 		prefix = " "
# 		references = references
# 		count += 1
# 
# 	    # Output the board line:
# 	    out_stream.write("{0}{1}".format(name,
# 	      ' ' * (max(1, 20 - len(name)))))
# 	    count_text = format("{0}".format(count))
# 	    out_stream.write("{0} {1}{2}".format(count_text,
# 	      ' ' * (3 - len(count_text)), references))
# 	    out_stream.write("\n")
# 
# class Price_Quantity:
#     """ A part price at a given quantity. """
# 
#     def __init__(self, price, quantity):
# 	self.price = price
# 	self.quantity = quantity
# 	self.order_cost = 0.0
# 	self.order_quantity = 0
# 
#     def __format__(self, format):
# 	return "[{0}/{1}]".format(self.price, self.quantity)
# 
#     @staticmethod
#     def parse(vendor_part_price):
# 	""" {Price_Quantity}: Parse {vendor_part_price} and return
# 	    the associated list of {Price_Quantity}'s. """
# 
# 	pair = vendor_part_price.split('/')
# 	assert len(pair) == 2, \
# 	  "Price/quantity '{0}' has wrong format". format(vendor_part_price)
# 	return Price_Quantity(float(pair[0]), int(pair[1]))
# 
# class SVG:
#     """ Scalable Vector Graphics """
# 
#     def __init__(self, file_name, width, height, units):
# 	""" {SVG}: Initialize {self} to output {file_name} with a canvas
# 	    area that is {width} by {height} {units} in area.  """
# 	
# 	svg_stream = open(file_name, "w")
# 	self.stream = svg_stream
# 	self.units = units
# 
# 	svg_stream.write('<?xml version="1.0" standalone="no"?>\n\n')
# 	svg_stream.write('<!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN"\n')
# 	svg_stream.write( \
# 	  ' "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd">\n\n')
# 	svg_stream.write('<svg width="{0}{1}" height="{2}{3}"\n'. \
# 	  format(width, units, height, units))
# 	svg_stream.write(' version="1.1"\n')
# 	svg_stream.write(' xmlns="http://www.w3.org/2000/svg">\n\n')
# 
#     def close(self):
# 	""" {SVG}: Close {self}. """
# 
# 	svg_stream = self.stream
# 	svg_stream.write("</svg>\n")
# 	svg_stream.close()
# 
#     def rectangle(self, x, y, width, height, stroke_color, fill_color):
# 	""" {SVG}: Draw a {width} by {height} rectangle with one corner
# 	    at ({x},{y}) and an exterior color of {stroke_color} and an
# 	    interior color of {fill_color}. """
# 
# 	svg_stream = self.stream
# 	units = self.units
# 	svg_stream.write('<rect x="{0}{1}" y="{2}{3}"'. \
# 	  format(x, units, y, units))
# 	svg_stream.write(' width="{0}{1}" height="{2}{3}"'. \
# 	  format(width, units, height, units))
# 	svg_stream.write(' style="stroke:{0}; fill:{1}"/>\n'. \
# 	  format(stroke_color, fill_color))
# 
#     def text(self, message, x, y, font_family, font_size):
# 	""" {SVG}: Draw a text {message} at ({x},{y}) with {font_size} font
# 	    of type {font_family}. """
# 
# 	svg_stream = self.stream
# 	units = self.units
# 	svg_stream.write('<text x="{0}{1}" y="{2}{3}"'. \
# 	  format(x, units, y, units))
# 	svg_stream.write(' style="font-family:{0}; font-size:{1};'. \
# 	  format(font_family, font_size))
# 	svg_stream.write(' text-anchor: middle;">')
# 
# 	svg_stream.write('{0}</text>\n'.format(message))
# 
# class Vendor_Part:
#     """ Information about a vendor part. """
# 
#     def __init__(self, mfg_part_name, vendor_name, vendor_part_name,
#      vendor_part_prices, date, part, mfg, description):
# 	""" {Vendor_Part}: Initialize {self} to contain {mfg_part_name},
# 	    {vendor_name}, {vendor_part_name}, {vendor_part_prices},
# 	    {date}, and {part}.  {vendor_part_prices} is of the form
# 	    "Cost1/Quantity1 ... CostN/QuantityN", where costI is
# 	    a decimal number and QuantityI is an integer.  """
# 
# 	#trace = vendor_part_prices == "20.00/1"
# 
# 	# Parse vendor prices:
# 	price_quantities = []
# 	part_prices = vendor_part_prices.split(' ')
# 	for part_price in part_prices:
# 	    price_quantity = Price_Quantity.parse(part_price)
# 	    #if trace:
# 	    #    print("price_quantity={0}".format(price_quantity))
# 	    price_quantities.append(price_quantity)
# 	#if trace:
# 	#    print("\n")
# 
# 	# Load up {self}:
# 	self.date = date
# 	self.description = description
# 	self.key = (vendor_name, vendor_part_name)
# 	self.mfg = mfg
# 	self.mfg_part_name = mfg_part_name
# 	self.order_cost = 0.0
# 	self.order_quantity = 0
# 	self.part = part
# 	self.price_quantities = price_quantities
# 	self.vendor_name = vendor_name
# 	self.vendor_part_name = vendor_part_name
# 	self.vendor_part_prices = vendor_part_prices
# 
#     def cost_compute(self, order_quantity):
# 	""" {Vendor_Part}: Compute the cost of buying {order_quantity}
# 	    {self}'s. """
# 
# 	# Scan all through {price_quantities}:
# 	price_quantities = list(self.price_quantities)
# 	for price_quantity in price_quantities:
# 	    # Compute the total cost for each price quantity pair.
# 	    # If {order_quantity} is too small, "bump" it up to
# 	    # the minimum quantity for that pair:
# 	    current_quantity = max(order_quantity, price_quantity.quantity)
# 	    price_quantity.order_quantity = current_quantity
# 	    price_quantity.order_cost = price_quantity.price * current_quantity
# 
# 	# Now sort by total cost:
# 	price_quantities.sort(key=lambda x:x.order_cost)
# 
# 	# The select the lowest cost:
# 	selected_price_quantity = price_quantities[0]
# 	self.selected_price_quantity = selected_price_quantity
# 
# 	# Treat {order_quantity} of 0 separately:
# 	if order_quantity == 0:
# 	    self.order_cost = 0.0
# 	    self.order_quantity = 0
# 	else:
# 	    # Compute the final order quantity and cost:
# 	    selected_order_quantity = \
# 	      max(order_quantity, selected_price_quantity.quantity)
# 	    order_cost = selected_order_quantity * selected_price_quantity.price
# 
# 	    # Update {order_cost} and {order_quantity} in {self}:
# 	    self.order_cost = order_cost
# 	    self.order_quantity = selected_order_quantity
# 
# 	return self.order_cost
# 
#     def write(self, needed, out_stream):
# 	""" {Vendor_Part}: Write the contents of {self} to {out_stream}. """
# 	assert isinstance(needed, int)
# 	# Output the first line:
# 	price_quantities = self.price_quantities
# 	price_quantities_size = len(price_quantities)
# 	price_quantities_written = 0
# 	center_index = -1
# 	for index in range(price_quantities_size):
# 	    price_quantity = price_quantities[index]
# 	    if price_quantity.quantity >= needed:
# 		out_stream.write("\t\t\t{0}: {1} {2}\n". \
# 		  format(self.vendor_name, self.vendor_part_name,
# 		  self.mfg_part_name))
# 
# 		prefix = "\t\t\t    "
# 		for side_index in (index - 1, index, index + 1):
# 		    if 0 <= side_index < price_quantities_size:
# 			price_quantity = price_quantities[side_index]
# 			price = price_quantity.price
# 			quantity = price_quantity.quantity
# 			out_stream.write("{0}{1}/{2}".
# 			  format(prefix, price, quantity))
# 			if price_quantity.quantity > 1:
# 			    out_stream.write("=${0:.2f}".
# 			      format(price *quantity))
# 			prefix = " "
# 
# 		out_stream.write("\n")
# 		break
# 
# def main():
#     """ The main program. """
# 
#     db = Database()
#     db.date_set("2012/01/2012")
# 
#     # Batteries:
#     db.part("CR-2032/VCN", "10MM_BATTERY", "P660-ND",
#       "DigiKey", "CR-2032/VCN",
#       "1.11/1 .997/10 .8858/50 .77510/100")
#     db.part("BU2032-1", "BU2032-1", "BU2032-1",
#       "DigiKey", "BU2032-1-ND",
#       ".73/1 .679/10 .612/100 .5508/500 .4896/1000",
#       "MPD (Memory Protection Devices)", "HOLDER CR2032 W/ PC PINS")
# 
#     # Buttons:
# 
#     db.part("PTS645SK43SMTLFS", "PTS645SK43SMTRLFS", "PTS645SK43SMTRLFS",
#       "DigiKey", "CKN9084CT-ND",
#       ".31/1 .293/10 .2508/25 .2132/50 .2048/100 .18392/250 .17556/500")
#     db.part("KSS221GLFS", "KSS221GLFS", "KSS221GLFS",
#       "DigiKey", "401-1097-1-ND",
#       ".76/1 .713/10 .6416/25 .5702/50 .5465/100 .49896/250 .4752/500")
#     db.part("KSS221GLFS", "KSS221GLFS", "KSS221GLFS",
#       "Mouser", "611-KSS221GLFS",
#       ".56/1 .463/25 .391/100 .35/250 .329/500 .267/1000 .267/2000")
#     #db.part("KRS-3550-BK-R", "BUTTON_6.5MM", "KRS-3550-BK-R",
#     #  "Jameco", "155249", ".39/1 .35/10 .29/100 .25/250")
#     #db.part("MJTP1243", "BUTTON_6.5MM", "MJTP1243",
#     #  "DigiKey", "679-2452-ND",
#     #  ".25/1 .238/10 .2296/25 .2214/50 .2091/100 .1968/250 .1886/500")
#     db.part("BUTTON_6.5MM", "B*_6.5MM", "MJTP1243",
#       "DigiKey", "679-2452-ND",
#       ".25/1 .238/10 .2296/25 .2214/50 .2091/100 .1968/250 .1886/500")
#     db.part("BUTTON_6.5MM", "B*_6.5MM", "MJTP1243",
#       "Mouser", "642-MJTP1243",
#       ".23/1 .221/25 .197/100 .188/500 .143/1000")
#     db.fractional_part("MJTP1243", "B*_6.5MM", "BUTTON_6.5MM", 1, 1)
# 
#     db.part("EVQ-11U05R", "Button_5MM", "EVQ-11U05R",
#       "DigiKey", "P8083SCT-ND",
#       ".29/1 .273/10 .2344/25 .1992/50 .1913/100 .17184/250 .16402/500",
#       "Panasonic", "SWITCH TACTILE SPST-NO 0.02A 15V")
#     db.fractional_part("2_LEAD_PUSH_BUTTON", "Button_5MM", "EVQ-11U05R", 1, 1)
# 
#     db.part("2-1437565-9", "TE_Connectivity_2-1437565-9", "2-1437565-9",
#       "DigiKey", "450-1792-1-ND",
#       ".26/1 .249/10 .2408/25 .232/50 .219/100 .206/200 .198/500",
#       "TE Connectivity", "SWITCH TACTILE SPST-NO 0.05A 24V")
# 
#     # Cables:
# 
#     db.part("TTL-232R-5V", "-", "TTL-232R-5V",
#       "Digikey", "768-1028-ND", "20.0/1 18.0/10")
#     db.part("TTL-232R-3V3", "-", "TTL-232R-3V3",
#       "Digikey", "768-1015-ND", "20.0/1 18.0/10")
#     db.part("TTL-232R-3V3", "-", "TTL-RS232R-3V3",
#       "Mouser", "895-TTL-232R-3V3", "20.00/1 18.00/10 16.50/50 15.00/100")
# 
#     # Capacitors:
# 
#     db.part("18pF", "CAPC1608X*", "C0603C180J5GACTU",
#       "DigiKey", "399-1052-2-ND",
#       ".10/1 .034/10 .0182/50 .0154/100 .01260/250 .01078/500 .00840/1000",
#       "Kemet", "CAP CER 18PF 50V 5% NP0 0603")
#     #db.part("18pF", "CAPC1608X*", "C0603C180J5GACTU",
#     #  "DigiKey", "399-1052-1-ND",
#     #  ".10/1 .034/10 .0182/50 .0154/100 .0126/250 .01078/500 .0084/1000")
#     #db.part("18pF", "Capacitor*", "FK18C0G1H180J",
#     #  "DigiKey", "445-4762-ND",
#     #  ".29/1 .20/10 .113/100 .09/250 .08/500 .06999/1000")
# 
#     db.part("22pF", "CAPC1608X*", "C0603C220J5GACTU",
#       "DigiKey", "399-1053-1-ND",
#       ".05/1 .04/10 .0214/50 .01820/100 .01484/250 .0127/500 .0099/1000")
#     db.part("470pF", "CAPC1608X*", "C0603C471K3RACTU",
#       "DigiKey", "399-9086-1-ND",
#       ".10/1 .042/10 .0228/50 .0186/100 .0156/250 .0133/500 .01045/1000")
# 
#     db.part(".1uF", "CAPC1608X*", "GRM188R71C104KA01D",
#       "DigiKey", "490-1532-1-ND",
#       ".10/1 .019/10 .0102/50 .0086/100 .00704/250 .006/500 .00468/1000",
#       "Murata", "CAP CER 0.1UF 16V 10% X7R 0603")
# 
#     #db.part(".1uF", "Capacitor*", "SR295E104MAR",
#     #  "DigiKey", "478-5741-ND",
#     #  ".24/1 .167/10 .0945/100 .07508/250 .06672/500 .05838/1000")
#     #db.part(".1uF", "Capacitor*", "K104K15X7RF5UH5",
#     #  "Mouser", "594-K104K15X7RF5UH5", ".04/1 .03/1000")
#     #db.part(".1uF", "Capacitor*", "C322C104M5U4CA",
#     #  "Jameco", "2162581", ".15/10 .12/100 .09/1000")
#     #db.part("1uF", "Capacitor*", "FK18X5R0J105K",
#     #  "DigiKey", "445-8395-ND",
#     #  ".30/1 .0204/10 .0115/100 .0918/250 .0816/500 .06999/1000")
# 
#     db.part(".33uF", "CAPC1608X*", "C1608X5R1E334K",
#       "DigiKey", "445-5142-1-ND",
#       ".11/1 .075/10 .0356/100 .03/250 .02512/500 .02063/1000")
#     db.part("1uF", "CAPC1608X*", "GRM188R61A105KA61D",
#       "DigiKey", "490-1543-1-ND",
#       ".10/1 .041/10 .0224/50 .019/100 .01552/250 .01328/500 .01035/1000",
#       "Murata", "CAP CER 1UF 10V 10% X5R 0603")
#     #db.part("1uF", "CAPC1608X*", "CC0603ZRY5V7BB105",
#     #  "DigiKey", "311-1372-1-ND",
#     #  ".041/10 .01860/100 .01302/500 .01014/1000")
#     db.part("2.2uF", "CAPC1608X90N", "CC0603ZRY5V5BB225",
#       "DigiKey", "311-1452-1-ND",
#       ".11/1 .078/10 .036/100 .02518/500 .01962/1000")
# 
#     #db.part("22uF", "C2", "TAP226K006SCS",
#     #  "DigiKey", "478-1873-ND",
#     #  ".79/1 .601/10 .4301/100 .38852/250 .333/500 .28674/1000 .26825/2500")
#     #db.part("22uF", "Capacitor*RM2*", "TAP226K006SCS",
#     #  "DigiKey", "478-1873-ND",
#     #  ".79/1 .601/10 .4301/100 .38852/250 .333/500 .28674/1000 .26825/2500")
#     #db.part("22uF", "Capacitor*RM2*", "TM22/6.3",
#     #  "Jameco", "33751", ".15/10 .12/100 .09/500")
#     #db.part("22uF", "Capacitor4x2RM2-5_RevB", "TAP226K006SCS",
#     #  "DigiKey", "478-1873-ND",
#     #  ".79/1 .601/10 .4301/100 .38852/250 .333/500 .28674/1000 .26825/2500")
# 
#     #db.part("22uF_35V_ALUM", "CAPAE530X540*", "EEV226M035A9DAA",
#     #  "DigiKey", "399-6706-1-ND",
#     #   ".35/1 .307/10 .1862/50 .12264/250 .11170/500")
#     #db.part("22uF_35V_ALUM", "CAPAE530X540*", "EEV226M035A9DAA",
#     #  "Mouser", "??",
#     #   ".35/1 .19/10 .123/100 .112/500")
#     #db.part("22uF_6.3V_TANT", "CAPMP3216X180N*", "TAJA226K006rNJ",
#     #  "DigiKey", "478-3856-1-ND",
#     #  ".34/1 .301/10 .1505/100 .1204/250 .10966/500 .09890/1000")
#     #db.part("22uF_6.3V_TANT", "CAPMP3216X180N*", "TAJA226K006rNJ",
#     #  "Mouser", "581-TAJA226K006R",
#     #  ".69/1 .318/100 .265/200 .24/500 .22/1000 .078/2000")
# 
#     db.part("22uF_35V_ALUM", "Capacitor*RM2*", "ECE-A1HKA220",
#       "DigiKey", "P837-ND",
#        ".25/1 .1124/50 .0955/100 .06744/500 .05901/1000")
#     db.part("22uF_6.3V_TANT", "Capacitor*RM2*", "TM22/6.3",
#       "Jameco", "33751", ".15/10 .12/100 .09/500")
# 
#     db.part("470uF", "CAP_D10_P5", "UVR1E471MPD",
#       "DigiKey", "493-1064-ND",
#       ".32/1 .225/10 .184/25 .1572/50 .1347/100 .11224/250 .10102/500",
#       "Nichicon", "CAP ALUM 470UF 20% 25V RADIAL")
# 
#     # Connectors:
#     db.part("USB_MICRO_B", "FCI_10118194_0001LF", "10118194-0001LF",
#       "DigiKey", "609-4618-1-ND",
#       ".46/1 .433/10 .3712/25 .3156/50 .30320/100 .27224/250 .25988/500",
#       "FCI", "Connector Receptacle USB - micro B 2.0 5" +
#       " Position Surface Mount Right Angle Horizontal")
# 
#     # Note: acutal part is "AU...", not "AY...":
#     db.part("DUAL_USB_A", "DUAL_USB_A", "AU-Y1008-2-R",
#       "Digikey", "AE10334-ND",
#       "1.07/1 .938/10 .8832/25 .08464/50 .8096/100 .736/250 .6624/500")
#     db.fractional_part("AU-Y1008-2-R", "DUAL_USB_A", "DUAL_USB_A", 1, 1)
#     db.fractional_part("AY-Y1008-2-R", "DUAL_USB_A", "DUAL_USB_A", 1, 1)
# 
#     db.part("USB_B", "USB_B", "E8144-B02022-L",
#       "Digikey", "553-2272-ND",
#       ".45/1 .434/10 .3532/25 .3086/50 .2965/100 .2662/250 .2541/500",
#       "Pulse Electronics",
#       "Connector Receptacle USB TypeB 4 Position Through Hole" +
#       " Right Angle Horizontal")
#     db.fractional_part("USB_B_ALT", "USB_B", "USB_B", 1, 1)
# 
#     # Parent parts for fractional 1Xn headers:
#     db.part("HEADER_1X40", "HEADER_1X40", "PREC040SAAN-RC",
#       "DigiKey", "S1012EC-40-ND",
#       ".51/1 .459/10 .378/100 .2988/500 .2565/1000 .234/5000 .225/10000",
#       "Sullins Connector Solutions", "CONN HEADER .100\" SNGL STR 40POS")
#     #db.part("HEADER_1X40", "HEADER_1X40", "PH1-40-UA",
#     #  "Jameco", "2168211", ".45/1 .29/10 .25/100", "Adam Tech")
#     db.part("HEADER_1X64_PISTON_430", "-", "816-22-064-10-009101",
#       "DigiKey", "ED90371-ND", "25.62/1 24.766/10")
#     db.part("HEADER_1X64_PISTON_315", "-", "816-22-064-10-003101",
#       "DigiKey", "ED90365-ND", "24.27/1 23.46/10")
# 
#     db.fractional_part("TEST_POINT",
#       "Pin_Header_Straight_1x01", "HEADER_1X40", 1, 40)
#     #db.fractional_part("TEST_POINT", "TEST_POINT", "HEADER_1X40", 1, 40)
#     db.fractional_part("KEY", "Pin_Header_Straight_1x01", "HEADER_1X40", 1, 40)
#     db.fractional_part("TP", "TEST_POINT", "HEADER_1X40", 1, 40)
#     db.fractional_part("GND", "Pin_Header_Straight_1x01", "HEADER_1X40", 1, 40)
#     db.fractional_part("CURRENT_SHUNT",
#       "Pin_Header_Straight_1x02", "HEADER_1X40", 2, 40)
# 
#     db.fractional_part("HEADER_1X2", "HEADER_1X2", "HEADER_1X40", 2, 40)
#     db.fractional_part("KEY2", "Pin_Header_Straight_1x02", "HEADER_1X40", 2, 40)
#     db.part("HEADER_1X2_FEMALE", "HEADER_1X2", "PPTC021LFBN-RC",
#       "DigiKey", "S7000-ND",
#       ".49/1 .34/10 .2912/25 .262/50 .228/100 .194/250 .1843/500 .1649/1000")
#     db.part("MOTOR_CONNECTOR", "Pin_Header_Straight_1x02",  "PPTC021LFBN-RC",
#       "DigiKey",  "S7000-ND",
#       ".49/1 .34/10 .2912/25 .262/50 .228/100 .194/250 .1843/500 .1649/1000")
#     db.part("HEADER_1X2_MTA", "HEADER_1X2_MTA", "640456-2",
#       "DigiKey", "A1921-ND",
#       ".14/1 .12/10 .0972/25 .0832/50 .0804/100 .06936/250 .06658/500")
#     db.part("HEADER_1X2_MTA_HOUSING", "-", "770602-2",
#       "DigiKey", "A19490-ND",
#       ".13/1 .126/10 .094/25 .0806/50 .078/100 .0672/250 .0652/500 .05645/1000")
#     db.part("HEADER_1X2_TERM_BLOCK", "TERM_BLOCK_HEADER_2", "EDSTL950/2",
#       "DigiKey", "ED1801-ND",
#       ".52/1 .48/10 .4376/25 .3888/50 .3726/100 .3402/250 .324/500 .2673/1000")
# 
#     db.part("5MM_TERMINAL_BLOCK_2_POS",
#       "5MM_TERMINAL_BLOCK_2_POS", "EDSTL950/2",
#       "DigiKey", "ED1801-ND",
#       ".52/1 .48/10 .4376/25 .3888/50 .3726/100 .3402/250 .324/500 .2673/1000")
#     db.fractional_part("2POS_5MM_TERM_BLK", "5MM_TERMINAL_BLOCK_2_POS",
#       "5MM_TERMINAL_BLOCK_2_POS", 1, 1)
#     db.fractional_part("5MM_TERMINAL_BLOCK", "5MM_TERMINAL_BLOCK_2_POS",
#       "5MM_TERMINAL_BLOCK_2_POS", 1, 1)
#     db.fractional_part("5mm Term. Block", "5MM_TERMINAL_BLOCK_2_POS",
#       "5MM_TERMINAL_BLOCK_2_POS", 1, 1)
# 
#     db.fractional_part("HEADER_1X3",
#       "Pin_Header_Straight_1x03", "HEADER_1X40", 3, 40)
#     db.fractional_part("BGND_JUMPER",
#       "Pin_Header_Straight_1x03", "HEADER_1X40", 3, 40)
#     db.fractional_part("BPWR_JUMPER",
#       "Pin_Header_Straight_1x03", "HEADER_1X40", 3, 40)
#     db.fractional_part("LGND_JUMPER",
#       "Pin_Header_Straight_1x03", "HEADER_1X40", 3, 40)
#     db.fractional_part("LPWR_JUMPER",
#       "Pin_Header_Straight_1x03", "HEADER_1X40", 3, 40)
#     db.fractional_part("PPWR_JUMPER",	# Should be {L,M,B}PWR_JUMPER
#       "Pin_Header_Straight_1x03", "HEADER_1X40", 3, 40)
#     db.fractional_part("TERMINATE_JUMPER",
#       "Pin_Header_Straight_1x03", "HEADER_1X40", 3, 40)
#     db.fractional_part("POWER_SELECT",
#       "Pin_Header_Straight_1x03", "HEADER_1X40", 3, 40)
#     db.fractional_part("SERVO",
#       "Pin_Header_Straight_1x03", "HEADER_1X40", 3, 40)
# 
#     #db.fractional_part("LED_JUMPER",
#     #  "Pin_Header_Straight_1x03", "HEADER_1X40", 3, 40)
#     db.part("HEADER_1X3_FEMALE", "HEADER_1X3", "PPTC031LFBN-RC",
#       "DigiKey", "S7001-ND",
#       ".64/1 .445/10 .3812/25 .343/50 .2985/100 .254/250 .241/3500 .2159/1000",
#       "Sullins Connector Solutions",
#       "Connector Header 3 Position 0.100\" (2.54mm) Tin Through Hole")
#     db.part("HEADER_1X3_MTA", "HEADER_1X3_MTA", "640456-3",
#       "DigiKey", "A19470-ND",
#       ".2/1 .185/10 .1376/25 .118/50 .11410/100 .09832/250 .0944/500")
#     db.part("HEADER_1X3_MTA_HOUSING", "-", "770602-3",
#       "DigiKey", "A19491-ND",
#       ".16/1 .154/10 .1315/25 .115/50 .1068/100 .09448/250 .09038/500")
#     db.fractional_part("REGULATOR",
#        "Pin_Header_Straight_1x03", "HEADER_1X3_FEMALE", 1, 1)
# 
#     db.fractional_part("HEADER_1X4", "HEADER_1X4", "HEADER_1X40", 4, 40)
#     db.part("HEADER_1X4_FEMALE", "HEADER_1X4", "PPTC041LFBN-RC",
#       "DigiKey", "S7002-ND",
#       ".60/1 .463/10 .4316/25 .3926/50 .3433/100 .29832/250 .2826/500")
#     db.part("HEADER_1X4_FEMALE", "HEADER_1X4", "3M-929974-01-04-RK",
#       "Allied", "70237672", ".36/1 .35/5 .34/10")
#     db.part("HEADER_1X4_FEMALE", "HEADER_1X4", "3M-929974-01-04-RK",
#       "Mouser", "517-974-01-04-RK",
#       ".43/1 .40/10 .38/25 .36/50 .34/150 .32/250 .30/500 .28/1000")
#     db.part("HEADER_1X4_FEMALE", "HEADER_1X4", "RS1-04-G",
#       "Jameco", "2169758", ".49/1 .45/10 .39/100 .29/500 .25/1000")
# 
#     db.part("HC_SR04_2X4", "Pin_Header_Straight_2x04_SR04", "PPTC042LFBN-RC",
#       "DigiKey", "S7072-ND",
#       ".83/1 .691/10 .64/25 .576/50 .512/100 .448/250 .4096/500 .3712/1000",
#       "Sullins Connector Solutions",
#       "Connector Header 8 Position 0.100\" (2.54mm) Tin Through Hole")
# 
#     db.fractional_part("HC_SR04_CONNECTOR",
#       "Pin_Header_Straight_1x04", "HEADER_1X4_FEMALE", 4, 4)
#     db.fractional_part("SONAR_SLAVE",
#       "Pin_Header_Straight_1x04", "HEADER_1X40", 4, 40)
# 
#     db.fractional_part("I2C_CONN",
#       "Pin_Header_Straight_1x04", "HEADER_1X40", 4, 40)
# 
#     db.part("Grove_Header_Straight_1x4", "Grove_Connector",
#       "Grove_Header_Straight_1x4", "SeeedStudio", "ACC391450", ".90/10")
#     db.fractional_part("A0/A1", "Grove_Connector",
#       "Grove_Header_Straight_1x4", 4, 4)
#     db.fractional_part("A2/A3", "Grove_Connector",
#       "Grove_Header_Straight_1x4", 4, 4)
#     db.fractional_part("D2/D3", "Grove_Connector",
#       "Grove_Header_Straight_1x4", 4, 4)
#     db.fractional_part("D4/D5", "Grove_Connector",
#       "Grove_Header_Straight_1x4", 4, 4)
#     db.fractional_part("D6/D7", "Grove_Connector",
#       "Grove_Header_Straight_1x4", 4, 4)
#     db.fractional_part("D8/D9", "Grove_Connector",
#       "Grove_Header_Straight_1x4", 4, 4)
#     db.fractional_part("D10/D11", "Grove_Connector",
#       "Grove_Header_Straight_1x4", 4, 4)
#     db.fractional_part("D12/D13", "Grove_Connector",
#       "Grove_Header_Straight_1x4", 4, 4)
#     db.fractional_part("I2C_A", "Grove_Connector",
#       "Grove_Header_Straight_1x4", 4, 4)
#     db.fractional_part("I2C_B", "Grove_Connector",
#       "Grove_Header_Straight_1x4", 4, 4)
#     db.fractional_part("I2C_C", "Grove_Connector",
#       "Grove_Header_Straight_1x4", 4, 4)
#     db.fractional_part("I2C_D", "Grove_Connector",
#       "Grove_Header_Straight_1x4", 4, 4)
# 
#     db.part("HEADER_1X4_MTA", "HEADER_1X4_MTA", "640456-4",
#       "DigiKey", "A1922-ND",
#       ".20/1 .189/10 .1616/25 .1414/50 .1313/100 .11616/250 .11112/500")
#     db.part("HEADER_1X4_MTA_HOUSING", "-", "770602-4",
#       "DigiKey", "A19492-ND",
#       ".23/1 .213/10 .1812/25 .15860/50 .1473/100 .13036/250 .12468/500")
# 
#     db.fractional_part("HEADER_1X5", "HEADER_1X5", "HEADER_1X40", 5, 40)
#     db.part("HEADER_1X5_FEMALE", "HEADER_1X6", "PPTC051LFBN-RC",
#       "DigiKey", "S6103-ND",
#       ".62/1 .481/10 .4484/25 .4076/50 .3668/100 .30972/250 .30972/250")
#     db.part("HEADER_1X5_MTA", "HEADER_1X5_MTA", "640456-5",
#       "DigiKey", "A19471-ND",
#       ".28/1 .262/10 .2248/25 .191/50 .1835/100 .16472/250 .15724/500")
#     db.part("HEADER_1X5_MTA_HOUSING", "-", "770602-5",
#       "DigiKey", "A19493-ND",
#       ".26/1 .248/10 .2124/25 .1806/50 .1736/100 .15584/250 .14876/500")
# 
#     db.fractional_part("HEADER_1X6",
#       "Pin_Header_Straight_1x06", "HEADER_1X40", 6, 40)
#     db.fractional_part("FTDI_HEADER",
#       "Pin_Header_Straight_1x06", "HEADER_1X40", 6, 40)
#     db.fractional_part("SERIAL_CONNECTOR",
#       "Pin_Header_Straight_1x06", "HEADER_1X40", 6, 40)
#     db.fractional_part("FTDI_HEADER_ALT",
#       "Pin_Header_Straight_1x06", "HEADER_1X40", 6, 40)
# 
#     db.part("HEADER_1X6_FEMALE", "HEADER_1X6", "PPPC061LFBN-RC",
#       "DigiKey", "S7039-ND",
#       ".70/1 .546/10 .5088/25 .4626/50 .4163/100 .35152/250 .333/500",
#       "Sullins Connector Solutions",
#       "Connector Header 6 Position 0.100\" (2.54mm) Gold Through Hole")
#     #db.part("HEADER_1X6_FEMALE", "HEADER_1X6", "RS1-06-G-.561-A11596",
#     #  "Jameco", "2144614",
#     #  ".49/1 .45/10 .39/100 .35/500 .29/1000")
#     db.fractional_part("A0_A5_HEADER",
#       "Pin_Header_Straight_1x06", "HEADER_1X6_FEMALE", 6, 6)
#     db.fractional_part("ARD_PWR_HEADER",
#       "Pin_Header_Straight_1x06", "HEADER_1X6_FEMALE", 6, 6)
#     db.fractional_part("ARD_PWR",
#       "Pin_Header_Straight_1x06", "HEADER_1X6_FEMALE", 6, 6)
#     db.fractional_part("ARD_A0_A5",
#       "Pin_Header_Straight_1x06", "HEADER_1X6_FEMALE", 6, 6)
#     db.fractional_part("ENCODER_CONNECTOR",
#       "MICRO_GEARMOTOR", "HEADER_1X6_FEMALE", 1, 1) 
# 
#     db.part("HEADER_1X6_MTA", "HEADER_1X6_MTA", "640456-6",
#       "DigiKey", "A1923-ND",
#       ".30/1 .286/10 .2452/25 .2084/50 .2001/100 .17972/250 .17154/500")
#     db.part("HEADER_1X6_MTA_HOUSING", "-", "770602-6",
#       "DigiKey", "A19494-ND",
#       ".35/1 .32/10 .2747/25 .2334/50 .2243/100 .20144/250 .19228/500")
# 
#     db.fractional_part("HEADER_1X8", "HEADER_1X8", "HEADER_1X40", 8, 40)
# 
#     db.part("HEADER_1X8_FEMALE", "Pin_Header_Straight_1x08", "PPPC081LFBN-RC",
#       "DigiKey", "S7041-ND",
#       ".89/1 .69/10 .6436/25 .585/50 .5265/100 .4446/250 .4212/500 .3744/1000")
#     db.part("HEADER_1X8_FEMALE", "Pin_Header_Straight_1x08",
#        "RS1-08-G-.561-A11596", "Jameco", "2144631", ".55/1 .45/10 .35/100")
#     db.fractional_part("D0_D7_HEADER",
#       "Pin_Header_Straight_1x08", "HEADER_1X8_FEMALE", 8, 8)
#     db.fractional_part("D8_D13_HEADER",
#       "Pin_Header_Straight_1x08", "HEADER_1X8_FEMALE", 8, 8)
#     db.fractional_part("ARD_D0_8_CONN",
#       "Pin_Header_Straight_1x08", "HEADER_1X8_FEMALE", 8, 8)
#     db.fractional_part("ARD_DO_D7",
#       "Pin_Header_Straight_1x08", "HEADER_1X8_FEMALE", 8, 8)
#     db.fractional_part("ARD_D9_13_CONN",
#       "Pin_Header_Straight_1x08", "HEADER_1X8_FEMALE", 8, 8)
#     db.fractional_part("ARD_D8_D13",
#       "Pin_Header_Straight_1x08", "HEADER_1X8_FEMALE", 8, 8)
# 
#     db.multiple_part("MIKROBUS", "mikrobus",
#       ["HEADER_1X8_FEMALE", "HEADER_1X8_FEMALE"])
# 
#     db.part("HEADER_1X8_MTA", "HEADER_1X8_MTA", "640456-8",
#       "DigiKey", "A1924-ND",
#       ".39/1 .367/10 .314/25 .267/50 .2566/100 .2304/250 .21994/500")
#     db.part("HEADER_1X8_MTA_HOUSING", "-", "770602-9",
#       "DigiKey", "A19497-ND",
#       ".44/1 .412/10 .3708/25 .3296/50 .31590/100 .2884/250 .27466/500")
# 
#     # Parent Part for HEADER_2Xn parts:
#     db.part("HEADER_2X40", "HEADER_2X40", "PREC040DAAN-RC",
#       "DigiKey", "S2012EC-40-ND",
#       "1.13/1 1.012/10 .8337/100 .65902/500 .56573/1000",
#       "Sullins Connector Solutions", "CONN HEADER .100\" DUAL STR 80POS")
#     #db.part("HEADER_2X40", "HEADER_2X40", "PH2-230/135-805",
#     #  "Jameco", "2120284", ".85/1 .69/10 .55/100")
#     #db.part("HEADER_2X40", "HEADER_2X40", "PH2-230/135-805",
#     #  "Jameco", "2120284", ".85/1 .69/10 .55/100")
#     db.part("HEADER_2X36_PISTON_255", "-", "818-22-072-10-000101",
#       "DigiKey", "ED90372-ND", "26.28/1 25.404/10")
#     db.part("HEADER_2X40_RA", "HEADER_2X8", "PREC040DBAN-M71RC",
#       "DigiKey", "S2112EC-40-ND",
#       "1.71/1 1.533/10 1.2621/100 .99766/500 .85643/1000 .78130/5000")
# 
#     db.fractional_part("LED_CONN_2X2",
#       "Pin_Header_Straight_2x02", "HEADER_2X40", 4, 80)
# 
#     db.fractional_part("SONAR_MASTER",
#       "Pin_Header_Straight_2x02", "HEADER_2X40_RA", 4, 80)
# 
#     db.part("HEADER_2X8_FEMALE", "Pin_Header_Straight_2x08", "PPTC082LFBN-RC",
#       "DigiKey", "S7076-ND",
#       "1.23/1 1.023/10 .9476/25 .8528/50 .758/100 .66324/250 .6064/500")
#     db.part("HEADER_2X8_FEMALE", "Pin_Header_Straight_2x08", "ValuePro",
#       "Jameco", "70721",
#       ".95/1 .85/10 .75/100")
# 
# 
#     db.part("HEADER_2X20_FEMALE", "Pin_Header_Straight_2x20",
#       "SFH11-PBPC-D20-ST-BK",
#       "Digikey", "S9200-ND",
#       "2.81/1 2.374/10 2.266/25 2.0502/50 1.8343/100 1.61852/250 1.5106/500")
#     db.part("HEADER_2X20_FEMALE_RA", "Pin_Header_Straight_2x20",
#       "SFH11-PBPC-D20-RA-BK",
#       "Digikey", "S9208-ND",
#       "2.81/1 2.374/10 2.266/25 2.0502/50 1.8343/100 1.61852/250 1.5106/500",
#       "Sullins Connector Solutions",
#       "Connector Header 40 Position 0.100\"" +
#       " (2.54mm) Gold Through Hole Right Angle")
#     db.fractional_part("RASPI_CONNECTOR_40", "Pin_Header_Straight_2x20",
#       "HEADER_2X20_FEMALE_RA", 1, 1)
#     db.fractional_part("SBC_CONNECTOR40", "Pin_Receptacle_Angled_2x20_Flipped",
#       "HEADER_2X20_FEMALE_RA", 1, 1)
# 
#     db.part("HEADER_2X20_IDC", "-", "3030-40-0103-00",
#       "DigiKey", "1175-1431-ND",
#       ".64/1 .60/10 .54/25 .48/50 .46/100 .42/250 .4/500 .33/1000")
# 
#     db.fractional_part("LED_JUMPER", "Pin_Header_Straight_2x02",
#       "HEADER_2X40", 4, 80)
# 
#     db.fractional_part("SRV_HDR2",
#       "Pin_Header_Straight_2x03", "HEADER_2X40", 6, 80)
#     db.fractional_part("HEADER_2X3", "HEADER_2X3", "HEADER_2X40", 6, 80)
#     db.fractional_part("ARD_SPI_HEADER", "Pin_Header_Straight_2x03",
#       "HEADER_2X40", 6, 80)
#     db.fractional_part("AVR_ISP_HEADER", "Pin_Header_Straight_2x03",
#       "HEADER_2X40", 6, 80)
#     db.fractional_part("AVR_ISP_2X3", "Pin_Header_Straight_2x03",
#       "HEADER_2X40", 6, 80)
#     db.fractional_part("ISP_CONN", "Pin_Header_Straight_2x03",
#       "HEADER_2X40", 6, 80)
# 
#     db.part("HEADER_2X4_IDC", "-", "71600-408LF",
#       "Arrow", "71600-408LF", ".2058/1")
#     db.part("HEADER_2X4_IDC", "-", "71600-108LF",
#       "Arrow", "71600-108LF", ".3435/1")
#     db.part("HEADER_2X4_IDC", "-", "903270308",
#       "Arrow", "903270308",   ".3673/1")
#     db.part("HEADER_2X4_IDC", "-", "71600-008LF",
#       "Arrow", "71600-008LF", ".4563/1")
#     db.part("HEADER_2X4_IDC", "-", "0903270308",
#       "Arrow", "0903270308",  ".4705/1")
#     db.part("HEADER_2X4_IDC", "-", "1445350-8",
#       "Arrow", "1445350-8",   ".525/1")
# 
#     db.fractional_part("HEADER_2X5", "HEADER_2X5", "HEADER_2X40", 10, 80)
#     db.part("HEADER_2X5_IDC", "-", "101-106",
#       "DigiKey", "ED10500-ND",
#       ".30/1 .28/10 .204/50 .196/100 .176/250 .168/500 .14/1000")
#     db.fractional_part("HEADER_2X5_PISTON_255", "HEADER_2X5", 
#       "HEADER_2X36_PISTON_255", 10, 72)
# 
#     db.part("HEADER_2X5_IDC", "-", "101-106",
#       "Digikey", "ED10500-ND",
#       ".32/1 .302/10 .219/50 .2107/100 .1892/250 .1806/500 .1505/1000")
# 
#     db.part("HEADER_2X5_SHROUDED", "Pin_Header_Straight_2x05_Shrouded",
#       "7110-10SG", "Jameco", "67812", ".59/1 .49/10 .39/100")
#     db.part("HEADER_2X5_SHROUDED", "Pin_Header_Straight_2x05_Shrouded",
#       "3020-10-0100-00",
#       "DigiKey", "1175-1609-ND",
#       ".48/1 .45/10 .36/50 .345/100 .315/250 .30/500 .2475/1000",
#       "CNC Tech", "IDC BOX HEADER .100\" 10POS")
#     db.multiple_part("BUS_HEADER", "Pin_Header_Straight_2x05_Shrouded",
#       ["HEADER_2X5_SHROUDED", "HEADER_2X5_IDC"])
#     #db.multiple_part("BUS_MASTER_HEADER", "Pin_Header_Straight_2x05_Shrouded",
#     #  ["HEADER_2X5_SHROUDED", "HEADER_2X5_IDC"])
#     db.multiple_part("BUS_MASTER_HEADER", "Pin_Header_Straight_2x05_Shrouded",
#       ["HEADER_2X5_SHROUDED"])
#     db.multiple_part("BUS_SLAVE_HEADER", "Pin_Header_Straight_2x05_Shrouded",
#       ["HEADER_2X5_SHROUDED", "HEADER_2X5_IDC"])
#     db.multiple_part("JTAG_HEADER", "Pin_Header_Straight_2x05_Shrouded",
#       ["HEADER_2X5_SHROUDED", "HEADER_2X5_IDC"])
#     db.multiple_part("MOTOR_ENCODER_CONN", "Pin_Header_Straight_2x04_Shrouded",
#       ["HEADER_2X5_SHROUDED", "HEADER_2X5_IDC"])
# 
#     db.part("MOTOR_ENCODER_CONN_2X5",
#        "Pin_Header_Straight_2x05_Shrouded", "SBH11-PBPC-D05-ST-BK",
#       "DigiKey", "S9169-ND",
#       ".64/1 .445/10 .3812/25 .343/50 .2985/100 .254/250 .2413/500 .2159/1000")
# 
#     db.part("HEADER_2X5_SHROUDED_RA", "HEADER_2X5_SHROUDED", "302-R101",
#       "DigiKey", "ED10533-ND",
#       ".42/1 .39/10 .312/50 .299/100 .273/250 .26/500 .2145/1000 .195/2500")
# 
# 
#     db.fractional_part("HEADER_2X5_2.54MM",
#       "ARM_JTAG_2X5_2.54MM", "HEADER_2X40", 10, 80)
#     db.part("HEADER_2X5_1.27MM", "SMT_VERT_M1.27_2x5", "20021121-00010T4LF",
#       "DigiKey", "609-3729-ND",
#       ".74/1 .69/10 .529/100 .483/250 .46/500 .3795/1000")
# 
#     db.fractional_part("HEADER_2X7", "HEADER_2X7", "HEADER_2X40", 14, 80)
# 
#     db.part("FLAT_CABLE40_10FT", "-", "3365/40 300SF",
#       "Digikey", "MC40G-10-ND", "13.13/1 11.716/5")
# 
#     #db.fractional_part("HEADER_2X8", "HEADER_2X8", "HEADER_2X40", 16, 80)
# 
#     # This one is funky, it uses a 1x8 instead of a 2x8:
#     db.fractional_part("HEADER_2X8_ICSP", "HEADER_2X40",
#       "HEADER_1X64_PISTON_430", 8, 64)
#     db.part("HEADER_2X8_FEMALE_RA", "HEADER_2X8*", "PPTC082LJBN-RC",
#       "DigiKey", "S5522-ND",
#       "1.58/1 1.306/10 1.224/25 1.088/50 .9792/100 .90304/250 .816/500")
# 
#     db.fractional_part("HEADER_2X8_RA", "HEADER_2X8", "HEADER_2X40_RA", 16, 80)
# 
#     db.fractional_part("MS_DATA_HEADER", "Pin_Header_Straight_2x08",
#       "HEADER_2X40",16, 80)
#     db.fractional_part("MS_PWR_HEADER", "Pin_Header_Straight_2x08",
#       "HEADER_2X40",16, 80)
#     db.fractional_part("MS_DATA_HEADER_POWER", "Pin_Header_Straight_2x08",
#       "HEADER_2X40",16, 80)
#     db.fractional_part("MS_PWR_HEADER_POWER", "Pin_Header_Straight_2x08",
#       "HEADER_2X40",16, 80)
# 
#     db.fractional_part("MS_NE_DATA_HEADER",
#       "Pin_Header_Straight_2x08", "HEADER_2X8_FEMALE", 16, 16)
#     db.fractional_part("MS_NE_PWR_HEADER",
#       "Pin_Header_Straight_2x08", "HEADER_2X8_FEMALE", 16, 16)
#     db.fractional_part("MS_NW_DATA_HEADER",
#       "Pin_Header_Straight_2x08", "HEADER_2X8_FEMALE", 16, 16)
#     db.fractional_part("MS_NW_PWR_HEADER",
#       "Pin_Header_Straight_2x08", "HEADER_2X8_FEMALE", 16, 16)
#     db.fractional_part("MS_SE_DATA_HEADER",
#       "Pin_Header_Straight_2x08", "HEADER_2X8_FEMALE", 16, 16)
#     db.fractional_part("MS_SEPWR_HEADER",
#       "Pin_Header_Straight_2x08", "HEADER_2X8_FEMALE", 16, 16)
#     db.fractional_part("MS_SW_DATA_HEADER",
#       "Pin_Header_Straight_2x08", "HEADER_2X8_FEMALE", 16, 16)
#     db.fractional_part("MS_SW_PWR_HEADER",
#       "Pin_Header_Straight_2x08", "HEADER_2X8_FEMALE", 16, 16)
# 
#     db.part("AVR_JTAG_CONNECTOR", "Pin_Header_Straight_2x05_Shrouded",
#       "AWHW-10G-0202-T",
#       "DigiKey", "HRP10H-ND",
#       ".51/1 .474/10 .4268/25 .3792/50 .3635/100 .3318/250 .316/500 .2607/1000")
#     db.part("BUS_MASTER_HEADER", "Pin_Header_Straight_2x05_Shrouded",
#       "AWHW-10G-0202-T",
#       "DigiKey", "HRP10H-ND",
#       ".51/1 .474/10 .4268/25 .3792/50 .3635/100 .3318/250 .316/500 .2607/1000")
#     db.part("BHR-10-HUA", "Pin_Header_Straight_2x05_Shrouded",
#       "AWHW-10G-0202-T",
#       "DigiKey", "HRP10H-ND",
#       ".51/1 .474/10 .4268/25 .3792/50 .3635/100 .3318/250 .316/500 .2607/1000")
#     db.part("BUS_SLAVE_HEADER", "Pin_Header_Straight_2x05_Shrouded",
#       "AWHW-10G-0202-T",
#       "DigiKey", "HRP10H-ND",
#       ".51/1 .474/10 .4268/25 .3792/50 .3635/100 .3318/250 .316/500 .2607/1000")
#     db.fractional_part("HEADER_2X10", "HEADER_2X10", "HEADER_2X40", 20, 80)
# 
# 
#     db.part("HEADER_2X20__SHROUDED", "Pin_Header_Straight_2x20_Shrouded",
#       "S02-S401", "DigiKey", "ED10529-ND",
#       ".45/1 .42/10 .336/50 .322/100 .294/250 .28/500 .231/1000")
#     db.multiple_part("HEADER_2X20_SHROUDED",	# Sonar needs 5 2x4 IDC's
#       "Pin_Header_Straight_2x20_Shrouded",
#       ["HEADER_2X20__SHROUDED", "HEADER_2X20_IDC", "HEADER_2X4_IDC",
#       "HEADER_2X4_IDC", "HEADER_2X4_IDC", "HEADER_2X4_IDC", "HEADER_2X4_IDC"])
#     db.multiple_part("302-S401", "Pin_Header_Straight_2x20_Shrouded",
#       ["HEADER_2X20__SHROUDED", "HEADER_2X20_IDC", "HEADER_2X4_IDC",
#       "HEADER_2X4_IDC", "HEADER_2X4_IDC", "HEADER_2X4_IDC", "HEADER_2X4_IDC"])
# 
#     #db.part("HEADER_2X5_FEMALE_IDC", "HEADER_2X10", "1658621-1",
#     #  "DigiKey", "AKC10H-ND",
#     #  "1.40/1 1.063/10 .8596/50 .8144/100 .67868/250 .63342/500 .58817/1000")
#     #db.part("HEADER_2X5_FEMALE_IDC", "HEADER_2X10", "1658621-1",
#     #  "AvNet", "1658621-1", ".6307/1 .5809/5000")
#     #db.part("HEADER_2X5_FEMALE_IDC", "HEADER_2X5", "101-106",
#     #  "DigiKey", "ED10500-ND",
#     #  ".30/1 .28/10 .204/50 .196/100 .176/250 .168/500 .14/1000")
# 
#     # Note: the footprint really should be OMRON_X4GA_2634:
#     db.part("HEADER_2X13_OMRON", "OMRON_X4GA_2632", "XG4A-2631",
#       "DigiKey", "OR961-ND",
#       "1.59/1 1.444/10 1.297/50 1.1238/100 1.12004/250 1.03162/500 .88425/1000")
#     db.part("HEADER_2X13_OMRON", "OMRON_X4GA_2632", "XG4A-2631",
#       "Mouser", "653-XG4A-2631",
#       "1.37/1 1.33/25 1.26/50 1.120/100 1.12/500 .88425/1000")
#     db.part("HEADER_2X13_OMRON", "OMRON_X4GA_2632", "XG4A-2631",
#       "OnlineComponents", "XG4A-2631",
#       "1.29/1 1.20/25 1.12/50 1.05/60 .99/100 .91/250 .88/500 .84/750")
#     db.part("HEADER_2X13_OMRON", "OMRON_X4GA_2632", "XG4A-2631",
#       "TodayComponents", "omron-xg4a-2631",
#       "1.05/1 1.03/5 1.01/10 .97/25 .95/50 .93/100")
# 
#     db.part("RASPI_CONNECTOR",
#        "Pin_Header_Straight_2x13", "SFH11-PBPC-D13-ST-BK",
#       "Digikey", "S9198-ND",
#       "1.66/1 1.373/10 1.2872/25 1.144/50 1.0296/100 .94952/250 .858/500")
#     db.fractional_part("RASPI_HEADER", "Pin_Header_Straight_2x13",
#       "HEADER_2X40", 26, 80)
# 
#     # Technically this is not an OMRON part, it should be named "..._EJECTOR":
#     db.part("HEADER_2X13_OMRON", "OMRON_X4GA_2632", "7200-26SG",
#       "Jameco", "71933", "1.09/1 .99/10 .89/100 .79/500 .65/1000")
#     db.part("HEADER_2X5_EJECTOR", "Pin_Header_Straight_2x05", "7200-10S-R",
#       "Jameco", "117664", ".69/1 .59/10 .55/100 .49/500 .45/1000")
# 
#     db.fractional_part("BBB_P9_HEADER", "Pin_Header_Straight_2x23",
#       "HEADER_2X40", 46, 80)
# 
#     db.part("HEADER_2X4_IDC", "-", "71600-008LF",
#       "Digikey", "609-3568-ND",
#       ".94/1 .827/10 .7458/50 .7135/100 .6486/250 .58374/500 .51888/1000")
#     db.part("HEADER_2X4_IDC", "-", "8000-8R",
#       "Jameco", "2203928", ".29/1 .25/10 .19/100")
# 
#     db.part("PLUG_2X5_IDC", "", "8000-10-R",
#       "Jameco", "32492", ".35/1 .29/10 .25/100 .19/500 .15/1000")
#     db.part("PLUG_2X13_IDC", "", "8000-26-R",
#       "Jameco", "32564", ".55/1 .49/10 .45/100 .39/500 .35/1000")
# 
#     db.part("PLUG_2X13_OMRON", "", "XG4M-2630",
#       "DigiKey", "OR918-ND",
#       "1.44/1 1.303/10 1.17/50 1.1168/100 1.01044/250 .93066/500 .78722/1000")
# 
#     db.part("PLUG_2X13_OMRON", "", "XG4M-2630",
#       "TodayComponents", "omron-xg4m-2631",
#       "1.05/1 1.03/5 1.01/10 .99/25 .97/50 .95/100")
#     db.part("STRAIN_2X13_OMRON", "", "XG4T-2604",
#       "TodayComponents", "omron-xg4t-2604",
#       ".21/1 .19/5 .17/10 .13/25 .11/50 .09/100")
#     db.part("PLUG_2X13_OMRON", "", "XG4M-2630-T",
#       "TodayComponents", "omron-xg4m-2631-t",
#       "1.19/1 1.17/5 1.15/10 1.11/25 1.09/50 1.07/100")
# 
#     db.part("HEADER_2X5_OMRON", "OMRON_X4GA_2632", "XG4A-1031",
#       "TodayComponents", "omron-xg4a-1031",
#       ".98/1 1.03/5 .96/5 .94/10 .92/25 .90/50 .89/100")
#     db.part("PLUG_2X5_OMRON", "", "XG4M-1030",
#       "TodayComponents", "omron-xg4m-1030",
#       ".57/1 .56/5 .55/10 .54/25 .53/50 .52/100")
#     db.part("STRAIN_2X5_OMRON", "", "XG4T-1004",
#       "TodayComponents", "omron-xg4t-1004",
#       ".17/1 .15/5 .13/10 .11/25 .09/50 .07/100")
#     db.part("PLUG_2X5_OMRON", "", "XG4M-1030-T",
#       "TodayComponents", "omron-xg4m-1031-t",
#       ".72/1 .70/5 .68/10 .66/25 .64/50 .62/100")
# 
#     db.part("HEADER_2X13_FEMALE", "HEADER_2X13", "PPTC132LFBN-RC",
#       "DigiKey", "S7081-ND",
#       "1.87/1 1.548/10 1.4512/25 1.29/50 1.616/100 1.07072/250 .96750/1000")
# 
#     db.part("MOTOR_CONN", "5MM_TERMINAL_BLOCK_2_POS", "OSTTC020162",
#       "Digikey", "ED2600-ND",
#       ".41/1 .385/10 .2806/50 .2695/100 .242/250 .231/500 .1925/1000")
#     db.part("MOTOR_CONN", "5MM_TERMINAL_BLOCK_2_POS", "OSTTC020162",
#       "Jameco", "189668", ".45/1 .35/10 .20/100")
#     db.part("MOTOR_CONN", "5MM_TERMINAL_BLOCK_2_POS", "1935161",
#       "Arrow", "1935161", ".3853/1")
# 
#     db.part("OSTTC020162", "5MM_TERMINAL_BLOCK_2_POS", "OSTTC020162",
#       "Digikey", "ED2600-ND",
#       ".41/1 .385/10 .2806/50 .2695/100 .242/250 .231/500 .1925/1000")
#     db.part("OSTTC020162", "5MM_TERMINAL_BLOCK_2_POS", "OSTTC020162",
#       "Jameco", "189668", ".45/1 .35/10 .20/100")
#     db.part("OSTTC020162", "5MM_TERMINAL_BLOCK_2_POS", "MSG02001",
#       "Arrow", "MSG02001", ".1499/1")
#     db.part("OSTTC020162", "5MM_TERMINAL_BLOCK_2_POS", "1935161",
#       "Arrow", "1935161", ".3853/1")
# 
#     # The contact pins needed for the MTA Housings:
#     db.part("HEADER_MTA_CONTACT", "-", "770666-1",
#       "DigiKey", "A19520-ND",
#       ".078/25 .0692/50 .062/100 .0519/500 .03892/1000")
# 
#     db.part("HEADER_1X2_KK",
#       "Socket_MOLEX-KK-RM2-54mm_Lock_2pin_straight", "171856-0002",
#       "DigiKey", "WM10153-ND",
#       ".26/1 .248/25 .2124/25 .1806/50 .1735/100 .15576/250 .14868/500")
#     db.part("HEADER_1X2_KK",
#       "Socket_MOLEX-KK-RM2-54mm_Lock_2pin_straight", "171856-0002",
#       "Mouser", "538-171856-0002",
#       ".20/1 .117/25 .105/50 .096/100")
# 
#     db.part("MOLEX_22_03_5035", "MOLEX_22_03_5035", "0022035035",
#       "DigiKey", "WM18887-ND",
#       ".83/1 .58/10 .4972/25 .4474/50 .3894/100 .3314/250 .31484/500")
#     db.part("MOLEX_22_03_5045", "MOLEX_22_03_5045", "0022035045",
#       "DigiKey", "WM18888-ND",
#       ".98/1 .683/10 .5852/25 .5268/50 .4585/100 .3902/250 .3707/500")
# 
#     db.part("PJ-102A", "PJ-102A", "PJ-102A",
#       "DigiKey", "CP-102A-ND",
#       ".92/1 .644/10 .4324/100 .34960/500 .3128/1000 .2484/2500")
# 
#     db.part("TERMBLK2", "TERMBLK2", "OSTTC030162",
#       "Jameco", "189668", ".45/1 .35/10 .20/100")
#     # Old price:  "Jameco", "189668", ".29/1 .25/10 .19/100")
#     pb4 = db.multiple_part("PWRBLK4", "PWRBLK4", ["TERMBLK2", "TERMBLK2"] )
# 
#     db.part("PLUG_1X2_TERM_BLOCK", "", "ED950/2",
#       "DigiKey", "ED1701-ND",
#       "1.26/1 1.104/10 1.039/25 .996/50 .9526/100 .866/250 .7784/500")
# 
#     # Crystals:
#     #db.part("16MHz", "XTAL1150X480X*", "ABLS-16.000MHZ-B4-T",
#     #  "DigiKey", "535-10226-1-ND",
#     #  ".41/1 .358/10 .31360/50 .2475/100 .209/500")
#     db.part("32.768KHz", "RTC_CRYSTAL", "CFS206-32.768KDZBB", 
#       "DigiKey", "300-8301-ND",
#       ".24/1 .20/10 .18/50 .16/100 .152/500 .128/1000")
#     db.part("16MHz", "XTAL1150X480X430N", "ABLS-16.000MHZ-B4-T",
#       "DigiKey", "535-10226-1-ND",
#       ".35/1 .289/10 .2596/50 .231/100 .22/500", "Abracon",
#       "Crystal 16.0000MHz 30ppm 18pF 40 Ohm -20C - 70C Surface Mount HC49/US")
#     db.part("RTC_CRYSTAL", "OSCL550P380X800X250-4N", "ABS25-32.768KHZ-T",
#       "DigiKey", "535-9166-2-ND",
#       ".71/1 .624/10 .54/50 .432/100 .36/50", "Abracon",
#       "Crystal 32.7680kHz 20ppm 12.5pF 50 kOhm -40C - 85C" +
#       " Surface Mount 4-SOJ 5.50mm pitch")
# 
#     #db.part("16MHz", "Crystal_HC49-U*", "ATS16B",
#     #  "DigiKey", "CTX1085-ND",
#     #  ".36/1 .30/10 .27/50 .24/100 .228/500 .192/500")
#     #db.fractional_part("CRYSTAL", "Crystal_HC49-U*", "16MHz", 1, 1)
#     #db.part("20MHz", "XTAL1150X480X*", "ABLS-20.000MHZ-B4-T",
#     #  "DigiKey", "535-10232-1-ND",
#     #  ".35/1 .289/10 .259/50 .231/100 .22/500")
# 
#     # Diodes:
#     db.part("CDBB240-G", "DO214AA", "CDBB240-G",
#       "DigiKey", "641-1111-1-ND",
#       ".42/1 .331/10 .2792/25 .22740/100 .18836/250 .15562/500 .11655/1000",
#       "Comchip", "DIODE SCHOTTKY 40V 2A DO214AA")
#     db.part("SCHOTTKY_DIODE", "Diode_DO-41_SOD81_Horizontal_*", "SD101C-TR",
#       "DigiKey", "SD101CVSCT-ND",
#       ".38/1 .341/10 .2456/25 .1911/100 .12004/250 .1023/500 .06970/1000")
#     db.part("SCHOTTKY_DIODE", "Diode_DO-41_SOD81_Horizontal_*", "1N5817-TP",
#       "DigiKey", "1N5817-TPCT-ND",
#       ".39/1 .278/10 .2165/25 .1638/100 .1158/250 .0927/500 .0711/1000")
#     db.part("SCHOTTKY_DIODE", "Diode_DO-41_SOD81_Horizontal_*", "SD101C-TR",
#       "Mouser", "625-SD101C",
#       ".10/1 .066/10 .056/100 .049/500 .045/1000")
#     db.fractional_part("SCHOTTKY_DIODE_VERT", "Diode_DO-41_SOD81_Horizontal_*",
#        "SCHOTTKY_DIODE", 1, 1)
#     db.fractional_part("SD101C-TR", "Diode_DO-41_SOD81_Horizontal_*",
#        "SCHOTTKY_DIODE", 1, 1)
# 
#     db.part("MUR105G", "D4", "MUR105GOS-ND",
#       "DigiKey", "MUR105G",
#       ".41/1 .323/10 .272/25 .2216/100 .18356/250 .15192/500 .11394/1000")
#     db.part("PMEG3015EH", "SOD123F", "PMEG3015,115",
#       "DigiKey", "568-4127-1-ND",
#       ".44/1 .343/10 .2896/25 .2361/100 .19556/250 .16154/500 .12099/1000")
#     db.part("PMEG3030EP", "DIOM5027X*", "PMEG3030EP,115",
#       "DigiKey", "568-6761-1-ND",
#       ".45/1 .376/10 .3292/25 .2818/100 .2444/250 .20702/500 .1596/1000")
# 
#     #db.part("PMEG3030EP", "DIOM5027X*", "PMEG3030EP,115",
#     #  "Mouser", "771-PMEG3030EP115",
#     #  ".35/1 .28/25 .236/100 .199/250 .172/500 .145/1000")
# 
#     # Fuses:
#     db.part("2920L075DR", "FUSM8055X13", "2920L075DR",
#       "DigikKey", "F2867CT-ND",
#       ".66/1 .617/10 .5684/25 .5198/50 .432/100 .39272/250 .33286/500")
#     db.part("0ZCC0110FF2C", "FUSM4532X90N", "0ZCC0110FF2C",
#       "DigiKey", "507-1363-1-ND",
#       ".15/1 .136/10 .12560/25 .11290/100 .10056/250 .08380/500 .07940/1000")
#     db.part("RA160-60", "POLYFUSE_5.1X1.4MM", "ERFRA160-60Z",
#       "Jameco", "199938", ".59/1 .55/10 .49/100 .45/500")
#     #db.part("RESETABLE_FUSE", "MF_R300", "MF-R300",
#     #  "DigiKey", "MF-R300-ND",
#     #  ".37/1 .343/10 .315/25 .3888/50 .2398/100 .218/500 .1635/1000")
#     db.part("MF-R300", "MF_R300", "MF-R300",
#       "DigiKey", "MF-R300-ND",
#       ".38/1 .36/10 .3312/25 .303/50 .2518/100 .22892/250 .19402/500")
#     db.part("MF-R300", "MF_R300", "MF-R300",
#       "Newark", "61J7414",
#       ".277/1 .257/10 .23/25 .225/50 .215/100 .201/250 .181/500 .167/1000")
# 
#     # Integrated Circuits:
#     #db.part("MCP24XX32A", "DIP-8__300",  "24LC32A-I/P",
#     #  "DigiKey", "24LC32A-I/P-ND", ".48/1 .40/10 .39/25 .37/100")
#     db.part("MCP24XX32A", "SOIC127P600X175-8N",  "24LC32A/SN-ND",
#       "DigiKey", "24LC32A/SN-ND", ".41/1 .34/10 .33/25 .31/100")
#     db.part("74HCT03", "DIP-14__300", "74HCT03N,652",
#       "DigiKey", "568-7826-5-ND", ".99/1 .865/10 .7656/25 .6669/100")
#     db.part("74HCT03", "DIP-14__300", "74HCT03N,652",
#       "Arrow", "74HCT03N,652", ".4481/1")
#     db.part("74x05", "DIP-14__300", "MM74HCT05",
#       "Gerber", "MM74HCT05N-ND", "0.135/1")
#     db.part("74HC08", "DIP-14__300", "SN74HT08",
#       "Digikey", "296-1606-5-ND",
#       ".52/1 .344/25 .28/100 .232/250 .192/500 .16/750 .144/1000")
# 
#     db.part("74HC08", "DIP-14__300", "TC74HC08APF",
#       "Digikey", "TC74HC08APF-ND",
#       ".49/1 .326/25 .266/100 .2204/250 .1824/500 .1368/1000")
#     db.part("74HCT08", "DIP-14__300", "SN74HCT08",
#       "Arrow", "SN74HCT08", ".1553/25")
#     db.part("74HCT08", "DIP-14__300", "SN74HCT08N",
#       "Digikey", "296-1606-5-ND",
#       ".52/1 .344/25 .28/100 .232/250 .192/500 .16/750 .144/1000")
#     db.part("74HCT08", "DIP-14__300", "SN74HCT08",
#       "Newark", "60K6805",
#       ".526/1 .355/10 .192/100 .144/1000")
#     db.part("74x06", "DIP-14__300", "SN74HC05N",
#       "Digikey", "296-1568-5-ND",
#       ".57/1 .374/25 .3045/100 .25232/250 .2088/500 .174/750 .1566/1000")
#     db.part("74X125", "DIP-14__300", "SN74HCT125",
#       "Digikey", "296-ND",
#       ".43/1 .3152/25 .27/100 .234/250 .198/500 .171/750 .153/1000")
#     db.part("74HCT32", "DIP-14__300", "SN74HCG32N",
#       "Digikey", "296-1615-5-ND",
#       ".52/1 .344/25 .28/100 .232/250 .192/500 .16/750 .144/1000")
#     db.part("74HCT32", "DIP-14__300", "SN74HCT32N",
#       "Newark", "60K6811",
#       ".134/1 .134/10 .134/100 .115/1000")
#     db.part("74HCT32", "DIP-14__300", "74HCT32N",
#       "MCM", "118-74HCT32N", ".19/1")
# 
#     db.part("SN74HC32", "SOIC127P600X175-14N", "SN74HC32D",
#       "DigiKey", "296-1199-5-ND",
#       ".46/1 .357/10 .3012/25 .245/100 .203/250 .168/500 .14/750 .126/1000",
#       "Texas Instruments", "IC GATE OR 4CH 2-INP 14-SOIC")
# 
#     db.part("74HC74", "SOIC127P600X175-14*", "SN74HC74D",
#       "Digikey", "296-1204-5-ND",
#       ".45/1 .357/10 .3012/25 .245/100 .203/250 .168/500 .126/1000")
#     db.part("74HC74", "SOIC127P600X175-14*", "SN74HC74D",
#       "Mouser", "595-SN74HC74D",
#       ".46/1 .31/10 .168/100 .126/1000")
# 
#     db.part("74X08_SOT23", "SOT95P280X145-5*", "SN74AHC1G08DBVR",
#       "DigiKey", "296-1091-1-ND",
#       ".08/1 .07/10 .062/25 .0419/100 .04108/250 .0403/500 .03952/750")
#     #db.part("74LVC2G241", "SOIC127P600X175-8*", "SN74LVC2G241DCUR",
#     #  "DigiKey", "296-11936-1-ND", 
#     #  ".28/1 .234/10 .208/25 .10404/100 .1378/250 .1352/500 .1325/750")
#     db.part("74LVC2G241", "SOP65P400X135-8N", "SN74LVC2G241DCTR",
#       "DigiKey", "296-11935-1-ND", 
#       ".64/1 .536/10 .4692/25 .40170/100 .3840/250 .29510/500 .22750/1000")
#     db.part("AS5040", "SOP65P780X199-16*", "AS5040-ASST",
#       "DigiKey", "AS5040-ASSTCT-ND",
#       "10.42/1 8.6488/25 7.8624/100 7.0716/250 6.48648/500 5.70024/1000")
#     db.part("AS5048A", "SOP65P640X120-14*", "AS5048A-HTSP-500",
#       "DigiKey", "AS5048A-HTSP-500CT-ND",
#       "12.93/1 10.7308/25 9.7552/100 8.77968/250")
#     db.part("AS5050", "QFN65P400X400X80-16*", "AS5050-EQFT",
#       "DigiKey", "AS5050-EQFTCT-ND",
#       "6.0/1 5.399/10 4.8996/25 4.39960/100 3.9960/250")
#     db.part("AS5055", "QFN65P400X400X100-17A*", "AS5055-ASST",
#       "DigiKey", "AS5055-ASSTCT-ND",
#       "6.67/1 5.5392/25 5.03570/100 4.53212/250")
# 
#     db.part("ATmega2560", "QFP50P1600X1600X120-100N", "ATMEGA2560-16AU",
#       "DigiKey", "ATMEGA2560-16AURTR-ND",
#       "16.55/1 15.048/10 12.7908/100 11.6622/250 10.9098/500 10.54/1000",
#       "Atmel", "IC MCU 8BIT 256KB FLASH 100TQFP")
# 
#     db.part("ATMEGA324_DIP40", "DIP-40__600", "ATMEGA324P-20PU",
#       "Arrow", "ATMEGA324P-20PU", "5.04/1")
#     db.part("ATMEGA324_DIP40", "DIP-40__600", "ATMEGA324P-20PU",
#       "Newark", "68T2867", "5.55/1 4.76/10 4.44/25 4.23/100")
#     db.part("ATMEGA324_QFP44", "QFP80P1200X1200X120-44*", "ATMEGA324A-AU",
#       "AvNet", "ATMEGA324A-AU", "3.88/1 3.60/25 3.50/50 3.36/100 3.27/200")
#     db.part("ATMEGA324_QFP44", "QFP80P1200X1200X120-44*", "ATMEGA324A-AU",
#       "DigiKey", "ATMEGA324A-AU-ND", "5.42/1 3.40320/25 3.02520/100")
#     db.part("ATMEGA324_DIP40", "DIP-40__600", "ATMEGA324PA-PU",
#       "DigiKey", "ATMEGA324PA-PU-ND",
#       "6.22/1 5.594/10 4.5993/100 4.2264/250 3.85348/500 3.45294/1000")
#     db.part("ATMEGA324_DIP40", "DIP-40__600", "ATMEGA324P-20PU",
#       "Verical", "ATMEGA324P-20PU", "4.7371/20")
# 
#     db.part("ATMEGA328_DIP28", "DIP-28__300", "ATMEGA328P-PU",
#       "Arrow", "ATMEGA328P-PU", "2.08/1")
#     db.part("ATMEGA328_DIP28", "DIP-28__300", "ATMEGA328P-PU",
#       "AvNet", "ATMEGA328P-PU", "3.4040/1 2.4268/10 2.1859/50 2.1222/100")
#     db.part("ATMEGA328_DIP28", "DIP-28__300", "ATMEGA328P-PU",
#       "DigiKey", "ATMEGA328P-PU-ND", "3.41/1 3.045/10 2.7405/50 2.497/100")
#     db.part("ATMEGA328_DIP28", "DIP-28__300", "ATMEGA328P-PU",
#       "Future", "ATMEGA328P-PU", "1.99/10")
#     db.part("ATMEGA328_DIP28", "DIP-28__300", "ATMEGA328P-PU",
#       "Mouser", "556-ATMEGA328P-PU", "2.95/1 2.68/10 1.88/25 1.74/50 1.68/100")
#     db.part("ATMEGA328_DIP28", "DIP-28__300", "ATMEGA328P-PU",
#       "Newark", "68T2944", "3.00/1 2.63/10 1.97/100 1.78/100")
#     db.part("ATMEGA328_DIP28", "DIP-28__300", "ATMEGA328P-PU",
#       "Verical", "ATMEGA328P-PU", "1.8644/27")
# 
#     db.part("ATMEGA644A-AU", "QFP80P1200X1200X120-44*", "ATMEGA644A-AU",
#       "DigiKey", "ATMEGA644A-AU-ND", "6.34/1 3.9824/25 3.54/100")
#     db.part("ELD207(TA)-V", "SOIC127P600X175-8*", "ELD207(TA)-V",
#       "DigiKey", "1080-1200-1-ND",
#       ".81/1 .62/10 .4428/100 .38640/250 .33810/500 .26565/1000")
#     db.part("ELD207(TA)-V", "SOIC127P600X175-8*", "ELD207(TA)-V",
#       "Mouser", "638-ELD207TAV",
#       ".68/1 .569/50 .489/100 .369/500 .329/1000")
# 
#     db.part("DS1307", "DIP-8__300", "DS1307+",
#       "DigiKey", "DS1307+-ND",
#       "4.23/1 4.01/10")
# 
#     db.part("ELD207", "SOIC127P600X175-8*", "ELD207(TA)-V",
#       "DigiKey", "1080-1200-1-ND",
#       ".81/1 .62/10 .4428/100 .38640/250 .33810/500 .26565/1000")
# 
#     db.part("GP1S094HCZ0F", "GP1S094HCZ0F", "GP1S094HCZ0F",
#       "DigiKey", "425-1964-5-ND",
#       ".60/1 .48/10 .412/25 .33/100 .2625/500 .24/750 .225/1000")
#     db.part("GP1S094HCZ0F", "GP1S094HCZ0F", "GP1S094HCZ0F",
#       "Arrow", "GP1S094HCZ0F", ".2896/100")
#     db.part("GPS1S97HCZ0F", "GP1S097HCZ0F", "GP1S097HCZ0F",
#       "DigiKey", "425-1966-5-ND",
#       ".64/1 .512/10 .44/25 .352/100 .28/500 .256/750 .24/1000")
#     # Temporarily out of stock:
#     #db.part("GPS1S97HCZ0F", "GP1S097HCZ0F", "GP1S097HCZ0F",
#     #  "Arrow", "GP1S097HCZ0F", ".309/1")
# 
#     db.part("L293_DIP16", "DIP-16__300", "L293DNE",
#       "DigiKey", "296-9518-5-ND",
#       "3.75/1 3.0152/25 2.749/250 2.2244/500 2.01/750 1.876/1000",
#       "Texas Instruments", "IC MOTOR DRIVER PAR 16-DIP")
#     db.part("L293_SOIC20", "SOIC127P1032X265-20N", "L293DD013TR",
#       "DigiKey", "497-2937-2-ND",
#       "3.70/1 3.316/20 2.9816/25 2.7118/100 2.45472/250 2.1977/500",
#       "STMicroelectronics", "IC MOTOR DRIVER PAR 20-SOIC")
# 
#     db.part("L298", "MULTIWATT15", "L298N",
#       "DigiKey", "497-1395-5-ND",
#       "4.67/1 4.168/10 3.7508/25 3.4174/100 3.08396/250 2.76722/500")
#     db.part("L298", "MULTIWATT15", "L298N",
#       "Arrow", "L298N", "2.26/1")
#     db.part("L298", "MULTIWATT15", "L298N",
#       "AvNet", "L298N", "2.63/1 2.42/25")
#     db.part("L298", "MULTIWATT15", "L298N",
#       "Jameco", "245403", "2.75/1 2.49/10 2.35/100")
# 
#     db.part("L4940_D2PAK", "DPAK2", "L4940D2T5-TR",
#       "DigiKey", "497-1166-1-ND",
#       "1.71/1 1.509/10 1.3624/25 1.192/100 1.04532/250 .92708/500")
#     #db.part("L78L05AC", "SOT89", "L78L05ACUTR",
#     #  "DigiKey", "497-1183-1-ND",
#     #  ".47/1 .368/10 .31/25 .2527/100 .20932/250 .1729/500 .12950/1000")
#     db.part("L78L05AC", "TO92_123", "L78L05ACZTR",
#       "DigiKey", "497-1184-1-ND",
#       ".11/1 .10/5 .092/10 .0828/25 .0786/50 .0761/100")
#     db.fractional_part("78L05AC", "TO92_123", "L78L05AC", 1, 1)
#     #db.part("L78L33AC", "SOT89", "L78L33ACUTR",
#     #  "DigiKey", "497-1200-1-ND",
#     #  ".53/1 .415/10 .35/25 .2852/100 .2362/250 .19514/500 .14615/1000")
#     db.part("L78L33AC", "TO92_123", "L78L33ACZ",
#       "DigiKey", "497-7288-ND",
#       ".39/1 .306/10 .258/25 .21/100 .174/250 .144/500 .108/1000")
#     db.part("L78M05CDT-TR", "DPAK", "L78L33ACUTR",
#       "DigiKey", "MC78M05CDTGOS-ND",
#       ".49/1 .36240/25 .31050/100 .26912/250 .22770/500 .17595/1000")
#     db.part("LPC1112_QFN33", "QFN65P700X700X100-33*", "LPC1112FHN33/102,5",
#       "AvNet", "LPC1112FHN33/102,5", "1.04/1 1.00/100 .9615/500")
#     db.part("LPC1112_QFN33", "QFN65P700X700X100-33*", "LPC1112FHN33/102,5",
#       "DigiKey", "568-5144-ND",
#       "2.33/1 2.10/10 1.6875/100 1.50/250 1.3124/500 1.0875/1000")
#     db.part("LPC1754", "QFP50P1400X1400X160-80*", "LPC1754FBD80,551",
#       "DigiKey", "568-4790-ND",
#       "8.25/1 7.425/10 6.104/100 5.61/250 5.11/500 4.455/1000 4.29/2500")
#     db.part("LPC1754", "QFP50P1400X1400X160-80*", "LPC1754FBD80,551",
#       "Arrow", "LPC1754FBD80,551", "5.08/1")
#     db.part("LPC1754", "QFP50P1400X1400X160-80*", "LPC1754FBD80,551",
#       "AvNet", "LPC1754FBD80,551", "4.58/1 4.40/100 4.23/500")
# 
#     db.part("LM117T-3.3", "TO-220_Neutral123_Horizontal_LargePads",
#        "LM1117T-3.3/NOPB", "DigiKey", "LM1117T-3.3/NOPB-ND",
#       "1.49/1 1.324/10 1.1956/50 1.0462/100 .91804/500 .70883/750 .6405/1000")
#     db.part("LM1117T-3.3", "Regulator_TO_220_Horizontal", "LM1117T-3.3",
#       "Arrow", "LM1117T-3.3", ".725/1")
#     db.part("LM1117T-3.3", "Regulator_TO_220_Horizontal", "LM1117T-3.3",
#       "Jameco", "242115", "1.39/1 1.15/10 .85/100")
# 
#     db.part("LM2931", "DPAK*", "LM2931DT-5.0G",
#       "Digikey", "LM2931DT-5.0G",
#        "0.69/1 0.5348/25 0.4658/100 0.40536/250 0.345/500 0.276/1000")
#     db.part("LM2931", "DPAK*", "LM2931DT-5.0G",
#       "Mouser", "863-LM2931DT-5.0G",
#       "0.690/1 0.535/10 0.345/100 0.276/1000")
#     db.part("LM2931", "DPAK*", "LM2931DT-5.0G",
#       "Mouser", "26k3621",
#       "0.288/1 0.288/10 0.288/100 0.247/250 0.23/10000")
# 
#     #db.part("LM2940-5.0-TO220", "TO220_SPLAYED", "LM2940CT-5.0/NOPB",
#     #  "DigiKey", "M2940CT-5.0-ND",
#     #  "1.65/1 1.457/10 1.1515/100 1.01052/250 .893/500 .705/1000 .658/2500")
#     db.part("LM2940", "TO-220_*", "LM2940CT-5.0/NOPB",
#       "DigiKey", "LM2940CT-5.0/NOPB-ND",
#       "1.65/1 1.457/10 1.316/50 1.1515/100 1.01052/250 .893/500 .780/750")
#     db.part("LM2940CT-5.0", "Regulator_TO_220_*", "LM2940CT-5.0/NOPB",
#       "DigiKey", "LM2940CT-5.0/NOPB-ND",
#       "1.65/1 1.457/10 1.316/50 1.1515/100 1.01052/250 .893/500 .780/750")
#     db.part("LM2940", "TO-220_*", "LM2940CG-5.0-NOPB",
#       "Arrow", "LM2940CT-5.0/NOPB-ND",".79/1")
#     db.part("LM2940CT-5.0", "Regulator_TO_220_*", "LM2940CT-5.0/NOPB",
#       "Arrow", "LM2940CT-5.0/NOPB-ND",".79/1")
# 
#     db.part("LM340MP_SOT223", "SOT223", "LM340MP-5.0/NOPB",
#       "DigiKey", "LM340MP-5.0CT-ND",
#       "1.31/1 1.16/10 1.048/25 .91730/100")
# 
#     db.part("LTV-826", "DIP-8__300", "LTV-826",
#       "Mouser", "859-LTV-826",
#       ".35/1 .315/10 .28/50 .225/100 .193/500 .149/1000")
#     db.part("LTV-826", "DIP-8__300", "LTV-826",
#       "WPG_Cloud", "859-LTV-826", ".1837/1 .1705/1000")
#     db.part("LTV-826", "DIP-8__300", "LTV-826",
#       "Arrow", "LTV-826", ".1925/25")
#     db.fractional_part("LTV-816", "DIP-8__300", "LTV-826", 1, 1)
# 
#     db.part("MAX3051ESA", "SOIC127P600X175-8*", "MAX3051EKA+",
#       "DigiKey", "MAX3051EKA+-ND",
#       "2.43/1 1.71/25 1.24/100 1.09438/500")
#     db.part("MAX3051ESA", "SOIC127P600X175-8*", "MAX3051EKA+",
#       "AvNet", "MAX3051EKA+-ND",
#       "2.36/1 1.63/25 1.18/100")
#     db.part("MCP1700T-3302E", "SOT95P280X175-3*", "MCP1700T-3302E/TT",
#       "DigiKey", "MCP1700T3302ETTCT-ND", ".45/1 .37/10 .31/25 .28/100")
#     db.part("MCP1700T-3302E-SOT89", "SOT89", "MCP1700T-3302E/MB",
#       "DigiKey", "MCP1700T3302EMBCT-ND", ".45/1 .37/10 .31/25 .28/100")
#     db.part("MCP2551_SOIC8", "SOIC127P600X175-8*", "MCP2551-I/SN",
#       "DigiKey", "MCP2551-I/SN-ND", "1.12/1 1.02/10 .85/25 .78/100")
# 
#     #db.part("MCP2562", "DIP-8__300", "MCP2562-E/P",
#     #  "DigiKey", "MCP2562-E/P-ND", "1.12/1 .93/10 .78/25 .71/100")
#     db.part("MCP2562", "SOIC127P600X175-8N", "MCP2562-E/SN",
#       "DigiKey", "MCP2562-E/SN-ND", "1.08/1 .90/10 .25/75 .68/100",
#       "Microchip", "IC TXRX CAN 8SOIC")
#     #db.part("MCP2562", "DIP-8__300", "MCP2562-E/P",
#     #  "Avnet", "MCP2562-E/P", ".93/1 .78/25 .71/100")
#     #db.part("MCP2562", "DIP-8__300", "MCP2562-E/P",
#     #  "Mouser", "579-MCP2562-E/P", "1.02/1 .93/10 .78/25 .71/100")
#     #db.part("MCP2562", "DIP-8__300", "MCP2562-E/P",
#     #  "Microchip", "MCP2562-E/P", ".93/1 .78/25 .71/100")
# 
#     #db.part("MCP2562", "SOIC127P600X175-8*", "MCP2562-E/SN",
#     #  "DigiKey", "MCP2562-E/SN-ND",
#     #  "1.08/1 0.90/10 0.75/25 0.68/100")
#     #db.part("MCP2562", "SOIC127P600X175-8*", "MCP2562-E/SN",
#     #  "Mouser", "579-MCP2562-E/SN",
#     #  "0.98/1 0.90/10 0.75/25 0.68/100")
# 
#     db.part("MCP4802", "SOIC127P600X175-8*", "MCP4802-E/SN",
#       "Digikey", "MCP4802-E/SN-ND",
#       "1.78/1 1.48/10 1.23/25 1.12/100")
#     db.part("MCP4802", "SOIC127P600X175-8*", "MCP4802-E/SN",
#       "Microchip", "MCP4802-E/SN",
#       "1.48/1 1.23/26 1.12/100")
# 
#     db.part("MCP6321_DIP8", "DIP-8__300", "MCP6231-E/P",
#       "Digikey", "MCP6231-E/P-ND",
#       ".38/1 .32/10 .26/25 .24/100")
# 
#     db.part("MCP6542", "SOIC127P600X175-8*", "MCP6542-E/SN",
#       "Arrow", "MCP6542-E/SN", ".57/1")
#     db.part("MCP6542", "SOIC127P600X175-8*", "MCP6542-E/SN",
#       "Digikey", "MCP6542-E/SN-ND",
#       ".68/1 .57/10 .48/25 .44/100")
#     db.part("MCP6542", "SOIC127P600X175-8*", "MCP6542-E/SN",
#       "Microchip", "MCP6542-E/SN",
#       ".57/1 .48/26 .44/100")
#     db.part("MCP6542", "SOIC127P600X175-8*", "MCP6542-E/SN",
#       "Mouser", "579-MCP6542-E/SN",
#       ".62/1 .57/106 .48/25 .44/100")
#     #db.part("MCP7940", "DIP-8__300", "MCP7940M-I/P",
#     #  "Digikey", "MCP7940M-I/P-ND",
#     #  ".77/1 .64/10 .59/25 .5625/100")
#     db.part("MCP7940", "SOIC127P600X175-8N", "MCP7940M-I/SN",
#       "DigiKey", "MCP7940M-I/SN-ND",
#       ".70/1 .58/10 .54/25 .5125/100",
#       "Microchip", "IC RTC CLK/CALENDAR I2C 8-SOIC")
# 
#     #db.part("OKI-78SR-5/1.5-W36", "HEADER_1X3", "OKI-78SR-5/1.5-W36-C",
#     #  "DigiKey", "811-2196-5-ND",
#     #  "4.30/1 4.26/5 4.23/10 4.17/25 4.04/100 3.78/100 3.60432/250")
#     db.part("OKI-78SR-5/1.5-W36-C", "OKI_DC_TO_DC_CONNECTOR",
#       "OKI-78SR-5/1.5-W36-C",
#       "DigiKey", "811-2196-5-ND",
#       "4.30/1 4.26/5 4.23/10 4.17/25 4.04/100 3.78/100 3.60432/250")
#     db.fractional_part("REGULATOR_CONNECTOR", "OKI_DC_TO_DC_CONNECTOR",
#       "OKI-78SR-5/1.5-W36-C", 1, 1)
# 
#     db.part("SI8420", "SOIC127P600X175-8*", "SI8420BB-D-IS",
#       "DigiKey", "336-1754-5-ND",
#       "1.46/1 1.4048/25 1.3508/100 1.2636/1000")
# 
#     db.part("SI8421_SOIC8", "SOIC127P600X175-8*", "SI8421BB-D-IS",
#       "DigiKey", "336-1756-5-ND",
#       "1.46/1 1.4048/25 1.3408/100 1.2636/1000")
#     db.part("ST1480ACDR", "SOIC127P600X175-8*", "ST1480ACDR",
#       "DigiKey", "497-3726-1-ND",
#       "1.62/1 1.432/10 1.29320/25 1.1315/100 .99228/250 .88004/500 .69595/1000")
#     db.part("STM32F417VET6", "QFP50P1600X1600X145-100*", "STM32F407VET6",
#       "DigiKey", "497-12075-ND",
#       "10.99/1 9.893/10 8.1345/100 7.47492/250 6.81536/500 5.93595/1000")
#     db.part("STM32F417VET6", "QFP50P1600X1600X145-100*", "STM32F407VET6",
#       "Arrow", "STM32F407VET6", "7.03/1")
# 
#     db.part("754410", "DIP-16__300", "SN754410NE",
#       "DigiKey", "296-9911-5-ND",
#       "2.56/1 2.06/25 1.8563/100 1.65/250 1.44376/500 1.30351/750 1.19625/1000")
#     db.part("754410", "DIP-16__300", "SN754410NE",
#       "Arrow", "SN754410NE", "1.08/1")
#     db.part("754410", "DIP-16__300", "SN754410NE",
#       "Freelance", "SN754410NE", "0.55/1")
# 
#     db.part("TC1015-3.3V", "SOT95P280X145-5*", "TC1015-3.3VCT713",
#       "DigiKey", "TC1015-3.3VCT713CT-ND",
#       ".43/1 .36/10 .30/25 .27/100")
#     db.part("TC1015-3.3V", "SOT95P280X145-5*", "TC1015-3.3VCT713",
#       "Microchip", "TC1015-3.3VCT713",
#       ".36/1 .30/26 .27/100 .26/1000")
#     db.part("TC1015-3.3V", "SOT95P280X145-5*", "TC1015-3.3VCT713",
#       "Mouser", "579-TC1015-3.3VCT713CT",
#       ".38/1 .36/10 .30/25 .27/100 .246/250")
# 
#     db.part("TM4C123GH6PM", "QFP50P1200X1200X145-64*", "TM4C123GH6PMI",
#       "Arrow", "TM4C123GH6PMI",
#       "6.79/1")
#     db.part("TM4C123GH6PM", "QFP50P1200X1200X145-64*", "TM4C123GH6PMI",
#       "Digikey", "256-35848-ND",
#       "11.43/1 10.273/10 8.45/100 7.769/250 7.0835/500 6.1695/10000")
#     db.part("TM4C123GH6PM", "QFP50P1200X1200X145-64*", "TM4C123GH6PMI",
#       "Mouser", "595-TM4C123GH6PMI",
#       "11.43/1 10.29/10 9.36/25 8.46/100")
# 
#     # LED's:
# 
#     db.part("LED", "T1_LED", "WP710A10GD",
#       "DigiKey", "754-1603-ND",
#       ".13/1 .094/10 .0808/25 .0715/100 .065/250 .0611/500 .0481/1000")
#     db.part("WP710A10GD", "T1_LED", "WP710A10GD",
#       "DigiKey", "754-1603-ND",
#       ".13/1 .094/10 .0808/25 .0715/100 .065/250 .0611/500 .0481/1000")
# 
#     db.part("R971-KN-1", "DIOM2012X160*", "LG R971-KN-1",
#       "DigiKey", "475-1410-1-ND",
#       ".08/1 .068/10 .0546/100 .0478/250 .0437/500")
# 
#     db.part("LTST-C191KGKT", "DIOC1608X55N", "LTST-C191KGKT",
#       "DigiKey", "160-1446-1-ND",
#       ".30/1 .238/10 .1296/100 .0864/250 .07344/500 .05616/1000",
#       "Lite-On", "LED GREEN CLEAR THIN 0603 SMD")
# 
#     db.part("LED_HEADER_BICOLOR", "HEADER_1X2", "WP57EGW",
#       "DigiKey", "754-1469-ND", ".33/1 .234/10 .2016/25 .17552/250 .14950/500")
#     #db.part("LED_HEADER_BICOLOR", "HEADER_1X2", "LHG2062",
#     #  "Jameco", "94553",".19/10 .15/100 .12/1000")
#     db.part("LED_3MM_GREEN", "LED-3MM", "HLMP-1503",
#       "Jameco", "253631", ".10/10 .08/100 .06/1000")
#     db.part("LED_3MM_RED", "LED-3MM", "LTL-4211N",
#       "Jameco", "697565", ".10/10 .08/100 .06/1000")
#     db.part("LED_3MM_YELLOW", "LED-3MM", "LTL5241N",
#       "Jameco", "697688", ".08/10 .06/100 .05/1000")
#     db.part("LG_R971-KN-1-0-20-R18", "DIOM2012X160N", "LG R971-KN-1-0-20-R18",
#       "Digikey", "475-1401-1-ND",
#       ".09/1 .074/10 .059/100 .05164/250 .04720/500")
# 
#     # Mechancial:
# 
#     # M1.0 is not for a screw, so create a bogus entry:
#     db.part("M1.0_BOX", "M1.0_HOLE", "?",
#       "McMaster", "1234", ".01/1")
#     db.fractional_part("M1.0_HOLE", "M1.0_HOLE", "M1.0_BOX", 1, 100)
#     # M1.0 is not for a screw, so create a bogus entry:
#     db.part("M2.2_BOX", "Grove_Hole", "?", "McMaster", "1234", ".01/1")
#     # Grove hole:
#     db.fractional_part("GH", "Grove_Hole", "M2.2_BOX", 1, 100)
# 
#     db.part("2MM_HOLE", "MountingHole_2mm", "BoxOfHoles",
#       "McMaster", "1234", ".01/1")
# 
#     db.part("M3.0_#4_BOX", "M3.0_#4_HOLE", "?",
#       "McMaster", "90272A110", ".01/1")
#     db.fractional_part("M3.0_#4_HOLE", "M3.0_#4_HOLE", "M3.0_#4_BOX", 1, 100)
#     db.fractional_part("3MM_HOLE", "MountingHole_3mm",
#       "M3.0_#4_BOX", 1, 100)
#     db.fractional_part("ARD_NE_3MM_HOLE", "MountingHole_3mm",
#       "M3.0_#4_BOX", 1, 100)
#     db.fractional_part("ARD_NW_3MM_HOLE", "MountingHole_3mm",
#       "M3.0_#4_BOX", 1, 100)
#     db.fractional_part("ARD_SE_3MM_HOLE", "MountingHole_3mm",
#       "M3.0_#4_BOX", 1, 100)
#     db.fractional_part("ARD_SW_3MM_HOLE", "MountingHole_3mm",
#       "M3.0_#4_BOX", 1, 100)
#     db.fractional_part("MS_NE_3MM_HOLE", "MountingHole_3mm",
#       "M3.0_#4_BOX", 1, 100)
#     db.fractional_part("MS_NW_3MM_HOLE", "MountingHole_3mm",
#       "M3.0_#4_BOX", 1, 100)
#     db.fractional_part("MS_SE_3MM_HOLE", "MountingHole_3mm",
#       "M3.0_#4_BOX", 1, 100)
#     db.fractional_part("MS_SW_3MM_HOLE", "MountingHole_3mm",
#       "M3.0_#4_BOX", 1, 100)
#     db.fractional_part("BASE_NE_3MM_HOLE", "MountingHole_3mm",
#       "M3.0_#4_BOX", 1, 100)
#     db.fractional_part("BASE_NW_3MM_HOLE", "MountingHole_3mm",
#       "M3.0_#4_BOX", 1, 100)
#     db.fractional_part("BASE_SE_3MM_HOLE", "MountingHole_3mm",
#       "M3.0_#4_BOX", 1, 100)
#     db.fractional_part("BASE_SW_3MM_HOLE", "MountingHole_3mm",
#       "M3.0_#4_BOX", 1, 100)
# 
#     db.part("M3.5_#6_BOX", "M3.5_#6_HOLE", "?",
#       "McMaster", "91772A142", ".01/1")
#     db.fractional_part("M3.5_#6_HOLE", "M3.5_#6_HOLE", "M3.5_#6_BOX", 1, 100)
#     db.part("M5.0_#10_BOX", "M5.0_#10_HOLE", "?",
#       "McMaster", "90272A238", ".01/1")
#     db.fractional_part("M5.0_#10_HOLE", "M5.0_#10_HOLE", "M5.0_#10_BOX", 1, 100)
# 
#     db.part("SLOT_HOLE_10X20MM", "Velcro_Strap", "Air",
#       "McMaster", "Air", "0.01/1")
# 
#     # Optics:
# 
#     db.part("CMT821", "CMT821", "CMT821", "Sunex", "CMT821", "6.00/1")
#     db.part("LCM_S01602DTR", "LMC_S01602DTR", "LCM-S01602DTR/M",
#       "DigiKey", "67-1781-ND",
#       "8.31/1 7.524/10 5.016/100 4.70252/250 4.31062/500 4.0755/1000")
#     #db.part("MT9V034M", "LCC80P1143X1143X229-48*", "557-1454-ND",
#     #  "DigiKey", "MT9V034C12STM", "12.43/1")
#     db.part("MT9V034M", "LCC80P1143X1143X229-48*", "Arrow",
#       "Arrow", "MT9V034C12STM", "12.55/1")
# 
#     # Potentiometers:
# 
#     db.part("EVN-D8AA03B14", "EVND", "EVN-D8AA03B14",
#       "Digikey", "D4AA14-ND",
#       ".54/1 .254/50 .2002/100 .1694/250 .1386/500 .1078/1000 .10241/5000")
# 
#     # Resistors:
# 
#     db.part("0", "RESC1608X50N", "CRCW06030000Z0EA",
#       "Digikey", "541-0.0GCT-ND",
#       ".074/10 .04/50 .02295/200 .01566/1000",
#       "Vishay Dale", "RES SMD 0.0 OHM JUMPER 1/10W")
# 
#     db.part(".47", "Resistor_*_*", "KNP1WSJR-52-0R47",
#       "DigiKey", "0.47GCCT-ND",
#       ".26/1 .222/10 .1616/25 .0868/100 .06664/250 .05250/500 .03635/1000")
#     db.part(".47", "Resistor_*_*", "MOSX1/2CT52RR47J",
#       "Mouser", "660-MOSX1/2CT52RR47J", ".08/1")
#     db.part(".47", "Resistor_*_*", "MOSX1/2CT52RR47J",
#       "Mouser", "660-MOSX1/2CT52RR47J", ".08/1")
# 
#     db.part(".56", "RESC6432X76*", "RLP73K3AR56JTE",
#       "DigiKey", "A109909CT-ND",
#       ".58/1 .413/10 .322/25 .2728/50 .2149/100")
# 
#     #db.part("100", "Resistor_Horizontal_*", "CF14JT100R",
#     #  "DigiKey", "CF14JT100RCT-ND",
#     #  ".1/1 .053/10 .0288/50 0.219/100 .01624/250 .012/500 .008/1000")
# 
#     db.part("120", "RESC1608X*", "MCT06030C1200FP500",
#       "DigiKey", "MCT0603-120-CFCT-ND",
#       ".08/1 .069/10 .0516/50 .0408/100 .033/500 .024/1000",
#       "Vishay Beyschag", "RES SMD 120 OHM 1% 1/8W 0603")
#     db.part("120_1%_.1W", "RESC1608X*", "RMCF0603FT120R",
#       "DigiKey", "RMCF0603FT120RCT-ND",
#       ".04/1 .025/10 .0138/50 .0105/100 .0078/250 .00576/500 .00324/1000")
#     # Technically, this is a 5% resistor:
#     db.part("120_1%_.125W", "RES_10MM", "CF18JT120R",
#       "DigiKey", "CF18JT120RCT-ND",
#       ".09/1 .065/10 .0356/50 .0271/100 .02016/250 .01488/500 .00992/1000")
#     #db.part("120", "R*_*00", "CF18JT120R",
#     #  "DigiKey", "CF18JT120RCT-ND",
#     #  ".09/1 .065/10 .0356/50 .0271/100 .02016/250 .01488/500 .00992/1000")
#     #db.fractional_part("120 1%", "Resistor_Horizontal*", "120", 1, 1)
# 
#     db.part("124", "RESC1608X*", "RC0603FR-07124RL",
#       "DigiKey", "311-124HRCT-ND",
#       ".10/1 .014/10 .0063/100 .00382/500 .00270/1000")
#     db.part("124_AXIAL", "R4", "MFR-25FBF-124R",
#       "DigiKey", "124XBK-ND",
#       ".098/5 .082/10 .0315/200 .01953/600 .01386/1000 .01071/5000")
#     db.part("180", "Resistor_Horizontal*", "CF14JT180R",
#       "DigiKey", "CF14JT180RCT-ND",
#       ".08/1 .053/10 .0288/50 .0219/100 .01624/250 .012/500 .008/100")
#     db.part("200", "Resistor_Horizontal_400", "CF14JT20",
#       "DigiKey", "CF14JT200RCT-ND",
#       ".10/1 .053/10 .0288/50 .0219/100 .01624/250 .012/500 .008/1000")
#     #db.part("220", "Resistor_*_*", "CFR-25JB-52-220R",
#     #  "DigiKey", "220QBK-ND",
#     #  ".1/1 .061/10 .044/25 .0247/100 .0188/250 .01504/500 .01108/1000")
# 
#     # Should be 220_ISO_SIP6
#     db.part("220", "Resistor_Vertical__100", "CF14JT220R",
#       "DigiKey", "CF14JT220RCT-ND",
#       ".10/1 .053/10 .0288/50 .0219/100 .01624/250 .012/500 .008/1000")
#     db.part("220_BUS_SIP6", "Pin_Header_Straight_1x06", "4606X-101-221LF",
#       "DigiKey", "4606X-1-221LF-ND",
#       ".27/1 .259/10 .234/25 .2232/50 .216/100 .2016/250 .1836/500 .1656/1000")
# 
#     db.part("470", "RESC1608X*", "MCT06030C4700FP500",
#       "DigiKey", "MCT0603-470-CFCT-ND",
#       ".08/1 .069/10 .0516/50 .0408/100 .033/500 .024/1000",
#       "Vishay Beyschlag", "RES SMD 470 OHM 1% 1/8W 0603")
#     #db.part("470", "RESC1608X*", "RMCF0603JT470R",
#     #  "DigiKey", "RMCF0603JT470RCT-ND",
#     #  ".02/1 .017/10 .0092/50 .007/100 .0052/250 .00384/500 .0256/1000")
#     #db.part("470", "R*_H*", "CF18JT470R",
#     #  "DigiKey", "CF18JT470RCT-ND",
#     #  ".09/1 .065/10 .0356/50 .0271/100 .02016/250 .01488/500 .00992/1000")
#     #db.part("470", "Resistor_Horizontal*", "CF18JT470R",
#     #  "DigiKey", "CF18JT470RCT-ND",
#     #  ".09/1 .065/10 .0356/50 .0271/100 .02016/250 .01488/500 .00992/1000")
#     db.part("470_DIP16", "DIP-16__300", "4116R-1-471",
#       "DigiKey", "4116R-1-471-ND",
#       ".76/1 .616/25 .594/50 .561/100 .539/250 .506/500 .418/1000")
#     db.part("470_DIP16", "DIP-16__300", "4116R-1-471",
#       "Arrow", "4116R-1-471LF", ".3898/25")
#     #db.part("R_VERT", "Resistor_Horizontal*", "CF18JT470R",
#     #  "DigiKey", "CF18JT470RCT-ND",
#     #  ".09/1 .065/10 .0356/50 .0271/100 .02016/250 .01488/500 .00992/1000")
# 
#     db.part("1K", "RESC1608X*", "MCT06030C1001FP500",
#       "DigiKey", "MCT0603-1.00K-CFCT-ND",
#       ".08/1 .069/10 .0516/50 .0408/100 .033/500 .024/1000",
#       "Vishay Beyschlag", "RES SMD 1K OHM 1% 1/8W 0603")
#     #db.part("1K", "Resistor_Horizontal*", "CF14JT1K00",
#     #  "DigiKey", "CF14JT1K00CT-ND",
#     #  ".08/1 .053/10 .0288/50 .0219/100 .01624/250 .012/500 .008/1000")
#     #db.part("1K", "R_HORIZ_300", "CF14JT1K00",
#     #  "DigiKey", "CF14JT1K00CT-ND",
#     #  ".08/1 .053/10 .0288/50 .0219/100 .01624/250 .012/500 .008/1000")
#     #db.part("1K", "RESC1608X*", "RMCF0603JT1K00",
#     #  "DigiKey", "RMCF0603JT1K00CT-ND",
#     #  ".02/1 .017/10 .0092/50 .007/100 .0052/250 .00384/500 .0256/1000")
#     #db.part("2K2", "RESC1608X*", "RMCF0603JT2K20",
#     #  "DigiKey", "RMCF0603JT2K20CT-ND",
#     #  ".02/1 .017/10 .0092/50 .007/100 .0052/250 .00384/500 .0256/1000")
#     db.part("2K2 1%", "Resistor_Horizontal_RM10mm", "RNMF14FTC2K20",
#       "DigiKey", "S2.2KCACT-ND",
#       ".14/1 .095/10 .0518/50 .0394/100 .02924/250 .0216/500 .01440/1000")
# 
#     db.part("22K", "Resistor_*_*", "RNMF14FTC22K0",
#       "DigiKey", "S22KCACT-ND",
#       ".14/1 .095/10 .0518/50 .0394/100 .02924/250 .0216/500 .0144/1000")
#     db.part("22K_SIP5", "Pin_Header_Straight_1x05", "4605X-101-223LF",
#       "DigiKey", "4605X-101-223LF-ND",
#       ".27/1 .259/10 .234/25 .2232/50 .216/100 .2016/250 .18360/500 .1656/1000")
#     db.part("22Kx", "Pin_Header_Straight_1x08", "4608X-101-223LF",
#       "DigiKey", "4608X-1-223LF-ND",
#       ".33/1 .324/10 .2924/25 .279/40 .27/100 .252/250 .2295/500 .207/1000")
# 
#     db.part("33K_SIP5", "Pin_Header_Straight_1x05", "4605X-101-333LF",
#       "DigiKey", "4605X-101-333LF-ND",
#       ".27/1 .259/10 .234/25 .2232/50 .216/100 .2016/250 .18360/500 .1656/1000")
#     db.part("3K3x4", "Pin_Header_Straight_1x05", "4605X-101-332LF",
#       "DigiKey", "4605X-101-332LF-ND",
#       ".27/1 .259/10 .234/25 .223/50 .216/100 .2016/250 .1836/500 .1656/1000")
#     db.part("3K3", "Resistor_Horizontal_*", "CFR-25JB-52-3K3",
#       "DigiKey", "3.3KQBK-ND",
#       ".1/1 .051/10 .044/25 .0247/100 .0188/250 .01504/500 .01108/1000")
#     db.part("3K3 1%", "Resistor_*_*", "RNMF14FTC3K30",
#       "DigiKey", "S3.3KCACT-ND",
#       ".14/1 .095/10 .0518/50 .0394/100 .02924/250 .0216/500 .01440/1000")
#     #Note: substituting a 4K7 array since 3K9 does not come in SIP5:
#     db.part("3K9_SIP5", "Pin_Header_Straight_1x05", "CSC05A014K70GEK",
#       "DigiKey", "CSC4.7KC-ND",
#       ".26/1 .228/10 .1828/50 .1587/100 .11454/500 .09315/1000")
#     db.part("33K", "Resistor_*_*", "RNMF14FTC33K0",
#       "DigiKey", "RNMF14FTC33K0CT-ND",
#       ".14/1 .095/10 .0518/50 .0394/100 .02924/250 .0216/500 .0144/1000")
#     db.part("33Kx", "Pin_Header_Straight_1x08", "4608X-101-333LF",
#       "DigiKey", "4608X-1-333LF-ND",
#       ".33/1 .324/10 .2924/25 .279/40 .27/100 .252/250 .2295/500 .207/1000")
# 
#     db.part("3K7", "Resistor_Horizontal_*", "SFR2500003741FR500",
#       "DigiKey", "PPC3.74KYCT-ND",
#       ".26/1 .179/10 .0978/50 .0744/100 .05524/250")
# 
#     db.part("3K9", "RESC1608X*", "CRCW06033K90JNEA",
#       "DigiKey", "541-3.9KGCT-ND",
#       ".074/10 .04/50 .02295/200 .01566/100")
# 
#     db.part("4K7", "RESC1608X*", "MCR03ERTJ472",
#       "DigiKey", "RHM4.7KCGCT-ND",
#       ".10/1 .01/10 .0072/25 .0042/100 .00316/25 .00254/500 .00187/1000",
#       "Rohm", "RES SMD 4.7K OHM 5% 1/10W 0603")
#     #db.part("4K7", "Resistor_Horizontal_400", "CFR-25JB-52-4K7",
#     #  "DigiKey", "4.7KQBK-ND",
#     #  ".1/1 .061/10 .044/25 .0247/100 .01880/250 .01504/500 .01108/1000")
#     #db.part("4K7", "Resistor_Horizontal_400", "RMCF0603JT4K70",
#     #  "DigiKey", "RMCF0603JT4K70CT-ND",
#     #  ".02/1 .017/10 .0092/50 .007/100 .0052/250 .00384/500 .0256/1000")
#     db.part("4K7_SIP5", "Pin_Header_Straight_1x05", "CSC05A014K70GEK",
#       "DigiKey", "CSC4.7KC-ND",
#       ".26/1 .228/10 .1828/50 .1587/100 .11454/500 .09315/1000")
# 
#     db.part("10K", "RESC1608X*", "MCR03ERTJ103",
#       "DigiKey", "RHM10KCGCT-ND",
#       ".01/1 .01/10 .0072/25 .0042/100 .00316/250 .00254/500 .0187/1000",
#       "Rohm", "RES SMD 10K OHM 5% 1/10W 0603")
#     #db.part("24K", "RESC1608X*", "RC0603JR-0724KL",
#     #  "DigiKey", "311-24KGRCT-ND",
#     #  ".1/1 .01/10 .0048/100 .00294/500 .00207/1000")
#     #db.part("10K", "Resistor_*_*", "CF18JT10K0",
#     #  "DigiKey", "CF18JT10K0CT-ND",
#     #  ".09/1 .065/10 .0356/50 .0271/100 .02016/250 .01488/500 .00992/1000")
#     #db.part("10K", "R*_*00", "CF18JT10K0",
#     #  "DigiKey", "CF18JT10K0CT-ND",
#     #  ".09/1 .065/10 .0356/50 .0271/100 .02016/250 .01488/500 .00992/1000")
#     db.part("10K_SIP7",  "Pin_Header_Straight_1x07", "4607X-101-103LF",
#       "DigiKey", "4607X-101-103LF-ND",
#       ".33/1 .324/10 .2924/25 .279/50 .27/100 .252/250 .2295/500 .207/1000")
#     db.part("10K_SIP7",  "Pin_Header_Straight_1x07", "4607X-101-103LF",
#       "Newark", "62J2841",
#       ".15/1 .15/10 .129/25 .129/50 .129/100 .129/250 .12/500 .12/1000")
#     db.fractional_part("10Kx6",  "Pin_Header_Straight_1x07", "10K_SIP7", 1, 1)
#     db.part("10K_SIP9",  "Pin_Header_Straight_1x09", "4609X-101-103LF",
#       "Digikey", "4609X-101-103LF-ND",
#       ".39/1 .36/10 .3272/25 .3162/50 .3052/100 .2834/250 .2616/500")
#     db.fractional_part("10Kx8",  "Pin_Header_Straight_1x09", "10K_SIP9", 1, 1)
# 
#     db.part("13K", "RESC1608X50N", "MCR03ERTF1302",
#       "DigiKey", "RHM13KCFCT-ND",
#       ".10/1 .011/10 .0084/25 .0047/100 .00356/250 .00286/500 .0021/1000")
# 
#     db.part("20K", "RESC1608X50N", "MCR03ERTF2002",
#       "DigiKey", "RHM20.0KCFCT-ND",
#       ".10/1 .011/10 .0084/25 .0047/100 .00356/250 .00286/500 .0021/1000")
# 
#     db.part("30K9", "RESC1608X50N", "MCR03ERTF3092",
#       "DigiKey", "RHM30.9KCFCT-ND",
#       ".10/1 .011/10 .0084/25 .0047/100 .00356/250 .00286/500 .0021/1000")
# 
#     db.part("82K", "R_HORIZ_300", "CFR-25JB-52-82K",
#       "DigiKey", "82KQBK-ND",
#       ".10/1 .061/10 .044/25 .0247/100 .0188/250 .01504/500 .01108/1000")
# 
#     db.part("100K", "RESC1608X50N", "MCR03ERTJ104",
#       "DigiKey", "RHM100KCGCT-ND",
#       ".10/1 .01/10 .0720/25 .00420/100 .00316/250 .00254/500 .00187/1000",
#       "Rohm", "RES SMD 100K OHM 5% 1/10W 0603")
#     #db.part("100K", "Resistor_*_*", "CF14JT100K",
#     #  "DigiKey", "CF14JT100KTR-ND",
#     #  ".10/1 .053/10 .0288/50 .02190/100 .01624/250 .012/500 .008/1000")
#     #db.part("100K_SIP6", "Pin_Header_Straight_1x06", "CSC06A01100KGEK",
#     #  "DigiKey", "CSC100KE-ND",
#     #  ".20/1 .175/10 .1404/50 .1219/100 .106/250 .08798/500 .07155/1000")
#     #db.part("100K_SIP9", "Pin_Header_Straight_1x09", "4609X-101-104LF",
#     #  "DigiKey", "4609X-101-104LF-ND",
#     #  ".39/1 .363/10 .3272/25 .3162/50 .3052/100 .2834/250 .2616/500")
#     #db.fractional_part("100Kx8", "Pin_Header_Straight_1x09",
#     #   "100K_SIP9", 1, 1)
# 
#     db.part("143K", "RESC1608X*", "MCR03ERTF1433",
#       "DigiKey", "RHM143KCFCT-ND",
#       ".10/1 .011/10 .0084/25 .0047/100 .00356/250 .00286/500 .00210/1000")
# 
#     # Regulators:
#     db.part("S7V8A", "Pin_Header_Straight_1x04", "S7V8A",
#       "Pololu", "S7V8A",
#       "5.95/1 4.95/5 4.49/25 4.15/100")
#     db.part("S7VVF5", "Pin_Header_Straight_1x04", "S7V8F5",
#       "Pololu", "S7V8F5",
#       "5.95/1 4.95/5 4.49/25 4.15/100")
#     db.part("S18V20F5", "S18V20Fx", "S18V20F5",
#       "Pololu", "S17V20F5", "14.95/1 13.46/5 12.33/25 11.21/100")
#     db.part("S18V20F6", "S18V20Fx", "S18V20F6",
#       "Pololu", "S17V20F6", "14.95/1 13.46/5 12.33/25 11.21/100")
#     db.part("S18V20ALV", "S18V20Fx", "S18V20ALV",
#       "Pololu", "S17V20ALV", "15.95/1 14.46/5 13.16/25 11.96/100")
# 
#     # Sockets:
# 
#     db.part("DIP_SOCKET_8", "-", "8LPD",
#       "Jameco", "51571", ".13/10 .10/100 .08/1000")
#     db.part("DIP_SOCKET_14", "-", "14LPD",
#       "Jameco", "112214", ".14/1 .11/100 .10/1000")
#     db.part("DIP_SOCKET_16", "-", "16LPD",
#       "Jameco", "37373", ".18/1 .12/100 .08/1000")
#     db.part("DIP_SOCKET_28", "-", "28LPD",
#       "Jameco", "112299", ".25/1 .23/100 .21/1000")
#     db.part("DIP_SOCKET_40", "-", "40LPD",
#       "Jameco", "41111", ".33/1 .30/100 .26/1000")
# 
#     # Switches:
# 
#     db.part("DPDT_4A", "GF_426_0020", "GF-426-0020",
#       "Digikey", "CWI448-ND",
#       ".87/1 .838/10 .82/25 .733/50 .698/100 .68056/250 .57586/500")
#     db.fractional_part("F-426-0020", "GF_426_0020", "DPDT_4A", 1, 1)
# 
#     # Transistors:
# 
#     db.part("BSS138", "SOT95P280X145-3N", "BSS138",
#       "DigiKey", "BSS138CT-ND",
#       ".22/1 .196/10 .1408/25 .1095/100 .06884/250 .05868/500 .03998/1000",
#       "Fairchild", "MOSFET N-CH 50V 220MA SOT-23")
# 
#     db.part("PN2222", "TO92_123", "PN2222ATF",
#       "DigiKey", "PN2222ATFCT-ND",
#       ".22/1 .196/10 .1408/25 .1096/100 .06884/250 .05868/500 .03998/1000")
#     db.part("PN2222", "TO92_123", "PN2222ATF",
#       "Newark", "58K2048",
#       ".224/1 .149/10 .062/100 .042/1000")
#     db.part("PN2222", "TO92_123", "PN2222ATFR",
#       "Mouser", "512-PN2222ATFR",
#       ".22/1 .181/10 .064/100 .037/1000")
# 
#     db.part("FQP47P06", "TO-220_FET-GDS*", "FQP47P06",
#       "DigiKey", "FQP47P06-ND",
#       "2.15/1 1.94/10 1.7324/25 1.5593/100 1.385/250 1.21276/500 1.00485/1000")
#     db.part("FQP47P06", "TO-220_FET-GDS*", "FQP47P06",
#       "Arrow", "FQP47P06", "1.05/1")
# 
#     # Miscellaneous:
#     db.part("TLE4906K", "SOT95P280X145-3N", "TLE4906K",
#       "DigiKey", "TLE4906KCT-ND",
#       "1.18/1 1.118/5 .973/10 .8548/25 .7102/50 .60590/100 .55232/250")
#       # TLE4946K seems to be cheaper...
#     db.part("744045210", "INDP3245X260N", "744045210",
#       "DigiKey", "732-3072-1-ND",
#       ".91/1 .878/10 .8126/50 .7475/100 .68252/250")
#     db.part("SRR1280-221K", "SRR1280", "SRR128-221K",
#       "DigiKey", "SRR1280-221KLCT-ND",
#       ".99/1 .93/10 .868/25 .744/50 .70680/100",
#       "Bourns", "SRR1280-221KLCT-ND")
#     db.part("HC_SR04", "HC_SR04", "PPTC041LFBN-RC",
#       "Digikey", "S7002-ND",
#       ".60/1 .463/10 .4316/25 .3926/50 .3533/100 .29832/250 .38260/500")
#     db.part("CIB10P100NC", "INDC1608X95N", "CIB10P100NC",
#       "Digikey", "1276-6388-1-ND",
#       ".10/1 .072/10 .0624/25 .0294/100 .01794/500 .0132/100",
#       "Samsung", "FERRITE CHIP 10 OHM 1000MA 0603")
#     db.part("D24V25F6", "D24V25F6", "D24V25F6",
#       "Pololu", "D24V25F6",
#       "11.95/1 10.95/5 9.95/25 8.95/100")
#     db.part("OSHW_LOGO", "OSHW_LOGO_*", "", "Free", "OSHW_LOGO", "0.0/1")
#     db.part("OSHW", "OSHW_LOGO_*", "", "Free", "OSHW_LOGO", "0.0/1")
#     db.part("BEAGLEBONE_BLACK", "-", "BB-BBLK-000-C",
#       "Jameco", "2207970", "54.95/1")
#     db.part("SHORTING_BLOCK_WITH_TAB", "-", "2012JH-R",
#       "Jameco", "152671", ".15/10 .12/100 .09/500 .07/1000")
# 
#     # Order 2:
# 
#     if False:
# 	order = Order(db, "order2")
# 	# Panel2:
# 	order.board("Eye1", "eye1/rev_a/eye1.cmp", 'A', 2)
# 	order.board("LCD32", "lcd32/rev_a/lcd32.cmp", 'A', 1)
# 	# Panel3:
# 	order.board("Motor3", "motor3/rev_c/motor3.cmp", 'C', 3)
# 	order.board("Programmer", "programmer/rev_a/programmer.cmp", 'A', 2)
# 	order.board("RasPi", "raspi/rev_a/raspi.cmp", 'A', 1)
# 	order.board("Servo8", "servo8/rev_a/servo8.cmp", 'A', 1)
# 	# Panel4:
# 	order.board("Power_Chain", "power_chain/rev_b/power_chain.cmp", 'B', 1)
# 	order.board("Servo_Bus2", "servo_bus2/rev_a/servo_bus2.cmp", 'A', 1)
# 	order.board("JTag_Adapter", \
# 	  "jtag_adapter/rev_a/jtag_adapter.cmp", 'A', 2)
# 	order.board("Splice2", "splice2/rev_b/splice2.cmp", 'B', 1)
# 	order.board("RB2", "rb2/rev_b/rb2.cmp", 'B', 1)
# 	order.board("Rotary", "rotary/rev_a/rotary.cmp", 'A', 1)
# 	# Panel5:
# 	order.board("BusDuino", "busduino/rev_a/busduino.cmp", 'B', 5)
# 
# 	order.inventory(".1uF", 60)
# 	order.inventory("1uF", 60)
# 	order.inventory(".47uF", 10)
# 	order.inventory("22uF", 10)
# 	order.inventory("470", 100)
# 	order.inventory("10K", 50)
# 	order.inventory("AS5040", 5)
# 	order.inventory("ELD207(TA)-V", 5)
# 	order.inventory("EVN-D8AA03B14", 5)
# 
# 	order.inventory("HEADER_1X2_FEMALE", 0)
# 	order.inventory("HEADER_1X2_MTA", 30)
# 	order.inventory("HEADER_1X2_MTA_HOUSING", 50)
# 
# 	order.inventory("HEADER_1X3_FEMALE", 11)
# 	order.inventory("HEADER_1X3_MTA", 30)
# 	order.inventory("HEADER_1X3_MTA_HOUSING", 15)
# 
# 	order.inventory("HEADER_1X4_FEMALE", 27)
# 	order.inventory("HEADER_1X4_MTA", 12)
# 	order.inventory("HEADER_1X4_MTA_HOUSING", 8)
# 
# 	order.inventory("HEADER_1X5_FEMALE", 9)
# 	order.inventory("HEADER_1X5_MTA", 10)
# 	order.inventory("HEADER_1X5_MTA_HOUSING", 2)
# 
# 	order.inventory("HEADER_1X6_FEMALE", 29)
# 	order.inventory("HEADER_1X6_MTA", 16)
# 	order.inventory("HEADER_1X6_MTA_HOUSING", 3)
# 
# 	order.inventory("HEADER_1X8_FEMALE", 19)
# 	order.inventory("HEADER_2X5_SHROUDED", 90)
# 	order.inventory("HEADER_2X40", 5)
# 
# 	order.inventory("KRS-3550-BK-R", 6)
# 	order.inventory("L298", 3)
# 	order.inventory("LCM_S01602DTR", 2)
# 	order.inventory("LED_3MM_GREEN", 20)
# 	order.inventory("LED_3MM_RED", 20)
# 	order.inventory("LED_3MM_YELLOW", 20)
# 	order.inventory("LM2940-5.0-TO220", 3)
# 	order.inventory("LPC1754", 8)
# 	order.inventory("M3.0_#4_HOLE", 100)
# 	order.inventory("MCP1700T-3302E", 9)
# 	order.inventory("MCP2551_SOIC8", 11)
# 	order.inventory("PJ-102A", 10)
# 	order.inventory("PMEG3030EP", 8)
# 	order.inventory("TERMBLK2", 100)
# 	order.inventory("RA160-60", 5)
# 	order.inventory("HEADER_1X40", 7)
# 
# 	# Parts requests go here:
# 	order.request(".1uF", 100)
# 	order.request(".33uF", 100)
# 	order.request("124", 50)
# 	order.request("124_AXIAL", 10)
# 	order.request("1K", 50)
# 	order.request("20MHz", 20)
# 	order.request("22pF", 50)
# 	order.request("2920L075DR", 10)
# 	order.request("2K2", 50)
# 	order.request("4K7", 50)
# 	order.request("74X08_SOT23", 5)
# 	order.request("ATMEGA324_QFP44", 10)
# 	order.request("ELD207(TA)-V", 10)
# 	order.request("HEADER_1X4_MTA_HOUSING", 10)
# 	order.request("HEADER_1X5_MTA_HOUSING", 10)
# 	order.request("HEADER_1X6_MTA_HOUSING", 10)
# 	order.request("HEADER_2X5_IDC", 100)
# 	order.request("HEADER_MTA_CONTACT", 100)
# 	order.request("L78L33AC", 25)
# 	order.request("L78L05AC", 25)
# 	order.request("LED_HEADER_BICOLOR", 10)
# 	order.request("LPC1112_QFN33", 10)
# 	order.request("MAX3051ESA", 25)
# 	order.request("PMEG3030EP", 25)
# 	order.request("PTS645SK43SMTRLFS", 25)
# 
#     if False:
# 	order = Order(db, "order3")
# 	# Panel6:
# 	order.board("BusDuino", "busduino/rev_b/busduino.cmp", 'B', 5)
# 
# 	# Panel8:
# 	order.board("LCD32", "lcd32/rev_b/lcd32.cmp", 'B', 1)
# 	#order.board("Servo_Bus2", "servo_bus2/rev_b/servo_bus2.cmp", 'B', 1)
# 	order.board("Rotary", "rotary/rev_b/rotary.cmp", 'B', 1)
# 	order.board("Splice2", "splice2/rev_b/splice2.cmp", 'B', 1)
# 
# 	# Panel7:
# 	order.board("RasPi", "raspi/rev_b/raspi.cmp", 'B', 3)
# 	order.board("Programmer", "programmer/rev_b/programmer.cmp", 'B', 1)
# 	order.board("Motor3", "motor3/rev_d/motor3.cmp", 'D', 8)
# 	order.board("Servo8", "servo8/rev_b/servo8.cmp", 'B', 1)
# 
# 	# Inventory
# 	order.inventory("2K2", 50)
# 	order.inventory("4K7", 45)
# 	order.inventory("1K", 45)
# 	order.inventory("124", 90)
# 	order.inventory("HEADER_1X6_MTA", 5)
# 	order.inventory("LG_R971-KN-1-0-20-R18", 16)
# 	order.inventory("124_AXIAL", 9)
# 	order.inventory("EVN-D8AA03B14", 1)
# 	order.inventory("2.2uF", 0)	############
# 	order.inventory("10K", 0)
# 	order.inventory("74LVC2G241", 0)
# 	order.inventory("1uF", 50)
# 	order.inventory("MJTP1243", 2)
# 	order.inventory("LED_3MM_YELLOW", 10)
# 	order.inventory("MOLEX_22_03_5035", 1)
# 	order.inventory("MOLEX_22_03_5045", 1)
# 	order.inventory("LED_3MM_GREEN", 10)
# 	order.inventory("LED_3MM_RED", 10)
# 	order.inventory("HEADER_2X40", 3)
# 	order.inventory("22pF", 0)
# 	order.inventory("TERMBLK2", 8)
# 	order.inventory("LM340MP_SOT223", 0)
# 	order.inventory("0ZCC0110FF2C", 0)
# 	order.inventory("HEADER_1X3_MTA", 15)
# 	order.inventory("ST1480ACDR", 0)
# 	order.inventory("M3.0_#4_BOX", 100)
# 	order.inventory("PTS645SK43SMTRLFS", 17)
# 	order.inventory("HEADER_2X13_FEMALE", 0)
# 	order.inventory("16MHz", 3)
# 	order.inventory("LPC1112_QFN33", 8)
# 	order.inventory("MCP1700T-3302E-SOT89", 0)
# 	order.inventory("LED_HEADER_BICOLOR", 0)
# 	order.inventory(".1uF", 21)
# 	order.inventory("HEADER_1X2_MTA", 29)
# 	order.inventory("L78M05CDT-TR", 0)
# 	order.inventory("KSS221GLFS", 0)
# 	order.inventory("PMEG3015EH", 0)	       #######??
# 	order.inventory(".33uF", 70)
# 	order.inventory("HEADER_1X8_MTA", 0)
# 	order.inventory("HEADER_1X40", 7)
# 	order.inventory("OKI-78SR-5/1.5-W36", 0)
# 	order.inventory("20MHz", 12)
# 	order.inventory("HEADER_1X6_FEMALE", 25)
# 	order.inventory("L78L33AC", 14)
# 	order.inventory("MCP2551_SOIC8", 9)
# 	order.inventory("PJ-102A", 8)
# 	order.inventory("L78L05AC", 17)
# 	order.inventory("AS5055", 0)
# 	order.inventory("HEADER_1X8_FEMALE", 0)
# 	order.inventory("HEADER_2X40_RA", 2)
# 	order.inventory("LCM_S01602DTR", 2)
# 	order.inventory("AS5040", 4)
# 	order.inventory("PMEG3030EP", 14)
# 	order.inventory("AS5048A", 1)
# 	order.inventory("ELD207(TA)-V", 5)
# 	order.inventory("L298", 2)
# 	order.inventory("HEADER_2X5_SHROUDED", 90)
# 	order.inventory("HEADER_1X64_PISTON_430", 1)
# 	order.inventory("HEADER_2X36_PISTON_255", 1)
# 	order.inventory("ATMEGA324_QFP44", 8)
# 	order.inventory("MAX3051ESA", 17)
# 	order.inventory("LPC1754", 3)
# 
# 	order.request("HEADER_1X8_MTA", 10)
# 	order.request("HEADER_2X5_FEMALE_IDC", 50)
# 	order.request("L298", 10)
# 	order.request("TTL-232R-5V", 1)
# 	order.request("HEADER_1X64_PISTON_315", 1)
# 	order.request("LPC1754", 10)
# 	order.request("HEADER_1X8_MTA_HOUSING", 20)
# 
# 	order.vendor_exclude("Arrow")
# 	order.vendor_exclude("Jameco")
# 
#     if False:
# 	order = Order(db, "order4")
# 	# Panel6:
# 	order.board("RasPi", "raspi/rev_b/raspi.cmp", 'B', 100)
# 	#order.board("BusDuino", "busduino/rev_b/busduino.cmp", 'B', 100)
# 
#     if False:
# 	order = Order(db, "order5")
# 
# 	order.board("Synchro2",
# 	  "../../synchro_drive_motor_driver_pcb/rev_a/synchro2.cmp", 'A', 2)
# 	order.board("Synchro_Power4",
# 	  "../../synchro_drive_power_pcb/rev_a/synchro_power4.cmp", 'A', 1)
# 
# 	order.inventory(".1uF", 50)
# 	order.inventory("1uF", 20)
# 	order.inventory("10K", 100)
# 	order.inventory("120_1%_.125W", 9)
# 	order.inventory("20MHz", 4)
# 	order.inventory("470", 5)
# 	order.inventory("AS5050", 1)
# 	order.inventory("ELD207", 12)
# 	order.inventory("HEADER_2X5_SHROUDED", 10)
# 	order.inventory("L298", 6)
# 	order.inventory("LM2931", 6)
# 	order.inventory("PMEG3030EP", 16)
# 	order.inventory("R971-KN-1", 10)
# 	order.inventory("20MHz", 4)
# 
# 	order.request(".56", 5)
# 	order.request("18pF", 10)
# 	order.request("22uF_35V_ALUM", 10)
# 	order.request("22uF_6.3V_TANT", 10)
# 	order.request("470", 20)
# 	order.request("470pF", 10)
# 	order.request("74HC74", 4)
# 	order.request("AS5050", 4)
# 	order.request("HEADER_1X2_KK", 4)
# 	order.request("HEADER_1X2_TERM_BLOCK", 10)
# 	order.request("HEADER_2X5_1.27MM", 4)
# 	order.request("HEADER_2X5_EJECTOR", 10)
# 	order.request("HEADER_2X13_OMRON", 20)
# 	order.request("SI8420", 5)
# 	order.request("MCP2562", 3)
# 	order.request("MCP4802", 3)
# 	order.request("L298", 15)
# 	order.request("TC1015-3.3V", 4)
# 	order.request("TM4C123GH6PM", 5)
# 	order.request("PLUG_1X2_TERM_BLOCK", 10)
# 	order.request("PLUG_2X13_IDC", 20)
# 	order.request("PLUG_2X5_IDC", 10)
# 	order.request("BEAGLEBONE_BLACK", 1)
# 
# 	#order.request("STRAIN_2X13_OMRON", 20)
# 	
# 	#order.request("STRAIN_2X5_OMRON", 10)
# 
# 	order.vendor_exclude("TodayComponents")
# 	order.vendor_exclude("Microchip")
# 	order.vendor_exclude("Mouser")
# 
#     if False:
# 	order = Order(db, "2014_itead_100032679")
# 
# 	order.board("busino",
# 	  "../../../busino/rev_a/busino.cmp", 'A', 10)
# 	order.board("dual_slot_encoders",
# 	  "../../../dual_slot_encoders/rev_a/dual_slot_encoders.cmp", 'A', 10)
# 	order.board("mini_beaglebone_black",
# 	  "../../../mini_beaglebone_black/rev_a/mini_beaglebone_black.cmp", 
# 	  'A', 2)
# 	order.board("mini_bridge_encoders_sonar",
# 	  "../../../mini_bridge_encoders_sonar/rev_a/" + \
# 	  "mini_bridge_encoders_sonar.cmp", 'B', 5)
# 	order.board("mini_power",
# 	  "../../../mini_power/rev_a/mini_power.cmp", 'A', 5)
# 	order.board("mini_raspberry_pi",
# 	  "../../../mini_raspberry_pi/rev_a/mini_raspberry_pi.cmp", 'A', 3)
# 
# 	order.vendor_exclude("Allied")
# 	order.vendor_exclude("Freelance")
# 	order.vendor_exclude("Mouser")
# 	order.vendor_exclude("WPG_Cloud")
# 
#     if False:
# 	order = Order(db, "2014_itead_100037853")
# 
# 	#order.board("busino",
# 	#  "../../../busino/rev_c/busino.cmp", 'C', 2)
# 	#order.board("dual_slot_encoders",
#         #  "../../../dual_slot_encoders/rev_d/dual_slot_encoders.cmp", 'D', 20)
# 	#order.board("bus_beaglebone",
# 	#  "../../../bus_beaglebone/rev_c/bus_beaglebone.cmp", 'C', 8)
# 	#order.board("bus_bridge_encoders_sonar",
# 	#  "../../../bus_bridge_encoders_sonar/rev_c/" + \
# 	#  "bus_bridge_encoders_sonar.cmp", 'C', 8)
# 	#order.board("bus_power",	
# 	#  "../../../bus_power/rev_b/bus_power.cmp", 'B', 8)
# 	order.board("bus_sonar10",	
# 	  "../../../bus_sonar10/rev_c/bus_sonar10.cmp", 'C', 4)
# 
# 	order.inventory(".1uF", 100)
# 	order.inventory(".47", 25)
# 	order.inventory("100", 100)
# 	order.inventory("100K", 20)
# 	order.inventory("100Kx8", 0)
# 	order.inventory("10K", 100)
# 	order.inventory("10Kx6", 0)
# 	order.inventory("120 1%", 6)
# 	order.inventory("16MHz", 14)
# 	order.inventory("180", 3)
# 	order.inventory("18pF", 35)
# 	order.inventory("1K", 100)
# 	order.inventory("1uF", 20)
# 	order.inventory("220", 100)
# 	order.inventory("22K", 100)
# 	order.inventory("22K_SIP5", 0)
# 	order.inventory("22uF", 70)
# 	order.inventory("302-S401", 6)	# 2x20 Shrouded Male Header
# 	order.inventory("33K", 100)
# 	order.inventory("33K_SIP5", 0)
# 	order.inventory("3K3x4", 0)
# 	order.inventory("3K7", 0)
# 	order.inventory("470", 100)
# 	order.inventory("4K7", 100)
# 	order.inventory("4K7x4", 0)
# 	order.inventory("74HCT03", 0)
# 	order.inventory("74HCT08", 17)
# 	order.inventory("74HCT32", 22)
# 	order.inventory("754410", 4)
# 	order.inventory("ATMEGA324_DIP40", 5)
# 	order.inventory("ATMEGA328_DIP28", 7)
# 	order.inventory("AVR_JTAG_CONNECTOR", 1000)	# 2x5 Shrouded  0
# 	order.inventory("BHR-10-HUA", 1000)		# 2x5 Shrouded  16
# 	order.inventory("BUS_MASTER_HEADER", 1000)	# 2x5 Shrouded  8
# 	order.inventory("BUS_SLAVE_HEADER", 60)		# 2x5 Shrouded  12
# 	order.inventory("CR-2032/VCN", 0)
# 	order.inventory("F-426-0020", 2)
# 	order.inventory("FQP47P06", 13)
# 	order.inventory("GP1S094HCZ0F", 25)
# 	order.inventory("GPS1S97HCZ0F", 1000)	# Force it to go away
# 	order.inventory("HEADER_1X40", 7)
# 	order.inventory("HEADER_1X4_FEMALE", 8)
# 	order.inventory("HEADER_1X6_FEMALE", 15)
# 	order.inventory("HEADER_1X8_FEMALE", 13)
# 	#order.inventory("HEADER_2X4_IDC", 0)
# 	order.inventory("HEADER_2X40", 1)
# 	order.inventory("HEADER_2X5_IDC", 23)
# 	order.inventory("HEADER_2X8_FEMALE", 40)
# 	order.inventory("LED", 25)
# 	order.inventory("LM1117T-3.3", 25)
# 	order.inventory("LM2940", 0)
# 	order.inventory("LM2940", 23)
# 	order.inventory("LM2940CT-5.0", 1000)
# 	order.inventory("M3.0_#4_BOX", 100)
# 	order.inventory("MCP2562", 3)
# 	order.inventory("MCP7940", 0)
# 	order.inventory("MF-R300", 4)
# 	order.inventory("MJTP1243", 9)		# 6mm SW
# 	order.inventory("MOTOR_CONN", 40)	# 5mm terminal block
# 	order.inventory("MOTOR_ENCODER_CONN_2X5", 50) # 2x5 Shrouded 
# 	order.inventory("OKI-78SR-5/1.5-W36-C", 2)
# 	order.inventory("OSHW_LOGO", 1000)
# 	order.inventory("OSTTC020162", 100)	# Covered by MOTOR_CONN
# 	order.inventory("PN2222", 26)
# 	order.inventory("SD101C-TR", 18)	# Shottky Diodes
# 	order.inventory("WP710A10GD", 30)	# Green LED
# 
# 	order.request(".1uF", 100)
# 	order.request(".47", 10)
# 	order.request("100K", 100)
# 	order.request("100Kx8", 10)
# 	order.request("10Kx6", 10)
# 	order.request("120 1%", 20)
# 	order.request("16MHz", 10)
# 	order.request("180", 10)
# 	order.request("18pF", 10)
# 	order.request("1uF", 10)
# 	order.request("22K_SIP5", 10)
# 	order.request("32.768KHz", 10)
# 	order.request("33K_SIP5", 10)
# 	order.request("3K3x4", 10)
# 	order.request("470_DIP16", 10)
# 	order.request("4K7x4", 10)
# 	order.request("74HCT03", 5)
# 	order.request("74HCT08", 25)
# 	order.request("754410", 10)
# 	order.request("ATMEGA328_DIP28", 10)
# 	order.request("BEAGLEBONE_BLACK", 1)
# 	order.request("CR-2032/VCN", 10)
# 	order.request("DIP_SOCKET_14", 20)
# 	order.request("DIP_SOCKET_28", 10)
# 	order.request("DIP_SOCKET_40", 20)
# 	order.request("DIP_SOCKET_8", 20)
# 	order.request("F-426-0020", 10)
# 	order.request("FQP47P06", 20)
# 	order.request("GP1S094HCZ0F", 100)
# 	order.request("HEADER_1X40", 10)
# 	order.request("HEADER_1X4_FEMALE", 20)
# 	order.request("HEADER_2X20_IDC", 0)
# 	#order.request("HEADER_2X4_IDC", 40)
# 	order.request("HEADER_2X40", 20)
# 	order.request("HEADER_2X5_IDC", 10)
# 	order.request("HEADER_2X5_SHROUDED", 100)
# 	order.request("LTV-826", 20)
# 	order.request("MCP2562", 25)
# 	order.request("MCP7940", 10)
# 	order.request("MF-R300", 20)
# 	order.request("MJTP1243", 20)
# 	order.request("MOTOR_CONN", 50)
# 	order.request("OKI-78SR-5/1.5-W36-C", 8)
# 	order.request("PN2222", 20)
# 	order.request("SD101C-TR", 25)
# 	order.request("SHORTING_BLOCK_WITH_TAB", 100)
# 	order.request("TTL-232R-3V3", 2)
# 	order.request("DS1307", 1)
# 
# 	order.vendor_exclude("Allied")
# 	#order.vendor_exclude("AvNet")
# 	order.vendor_exclude("Freelance")
# 	order.vendor_exclude("Future")
# 	#order.vendor_exclude("Jameco")
# 	order.vendor_exclude("Mouser")
# 	order.vendor_exclude("Newark")
# 	order.vendor_exclude("WPG_Cloud")
# 
#     if False:
# 	order = Order(db, "2015_itead_100043169")
# 
# 	#order.board("busino",
# 	#  "../../../busino/rev_c/busino.cmp", 'C', 2)
# 	#order.board("dual_slot_encoders",
#         #  "../../../dual_slot_encoders/rev_f/dual_slot_encoders.cmp", 'F', 20)
# 	order.board("bus_beaglebone",
# 	  "../../../bus_beaglebone/rev_d/bus_beaglebone.cmp", 'D', 2)
# 	order.board("bus_raspberry_pi",
# 	  "../../../bus_raspberry_pi/rev_b/bus_raspberry_pi.cmp", 'B', 2)
# 	#order.board("bus_bridge_encoders_sonar",
# 	#  "../../../bus_bridge_encoders_sonar/rev_c/" + \
# 	#  "bus_bridge_encoders_sonar.cmp", 'C', 8)
# 	order.board("bus_usb_power",	
# 	  "../../../bus_usb_power/rev_a/bus_usb_power.cmp", 'A', 2)
# 	#order.board("bus_sonar10",	
# 	#  "../../../bus_sonar10/rev_c/bus_sonar10.cmp", 'C', 4)
# 
# 	order.inventory(".1uF", 80)
# 	#order.inventory(".47", 25)
# 	#order.inventory("100", 100)
# 	#order.inventory("100K", 20)
# 	#order.inventory("100Kx8", 0)
# 	order.inventory("10K", 50)
# 	#order.inventory("10Kx6", 0)
# 	#order.inventory("120 1%", 6)
# 	order.inventory("120 1%", 10)
# 	order.inventory("16MHz", 10)
# 	#order.inventory("180", 3)
# 	order.inventory("18pF", 20)
# 	#order.inventory("1K", 100)
# 	order.inventory("1uF", 20)
# 	order.inventory("2POS_5MM_TERM_BLK", 50)
# 	#order.inventory("220", 100)
# 	#order.inventory("22K", 100)
# 	#order.inventory("22K_SIP5", 0)
# 	#order.inventory("22uF", 70)
# 	#order.inventory("302-S401", 6)	# 2x20 Shrouded Male Header
# 	order.inventory("32.768KHz", 6)
# 	#order.inventory("33K", 100)
# 	#order.inventory("33K_SIP5", 0)
# 	#order.inventory("3K3x4", 0)
# 	#order.inventory("3K7", 0)
# 	order.inventory("470", 100)
# 	order.inventory("4K7", 100)
# 	#order.inventory("4K7x4", 0)
# 	#order.inventory("74HCT03", 0)
# 	order.inventory("74HCT08", 0)	# Mislabeled, should be 74HC08
# 	#order.inventory("74HCT08", 17)
# 	#order.inventory("74HCT32", 22)
# 	#order.inventory("754410", 4)
# 	order.inventory("ATMEGA324_DIP40", 8)
# 	#order.inventory("ATMEGA328_DIP28", 7)
# 	#order.inventory("AVR_JTAG_CONNECTOR", 1000)	# 2x5 Shrouded  0
# 	#order.inventory("BHR-10-HUA", 1000)		# 2x5 Shrouded  16
# 	order.inventory("BUS_HEADER", 1000)		# 2x5 Shrouded  8
# 	order.inventory("BUS_MASTER_HEADER", 1000)	# 2x5 Shrouded  8
# 	#order.inventory("BUS_SLAVE_HEADER", 60)	# 2x5 Shrouded  12
# 	order.inventory("CR-2032/VCN", 8)
# 	order.inventory("D24V25F6", 2)
# 	order.inventory("F-426-0020", 20)
# 	order.inventory("FQP47P06", 20)
# 	#order.inventory("GP1S094HCZ0F", 25)
# 	#order.inventory("GPS1S97HCZ0F", 1000)	# Force it to go away
# 	order.inventory("HEADER_1X40", 8)
# 	order.inventory("HEADER_1X4_FEMALE", 20)
# 	#order.inventory("HEADER_1X6_FEMALE", 15)
# 	#order.inventory("HEADER_1X8_FEMALE", 13)
# 	#order.inventory("HEADER_2X4_IDC", 0)
# 	order.inventory("HEADER_2X40", 10)
# 	#order.inventory("HEADER_2X5_IDC", 23)
# 	#order.inventory("HEADER_2X8_FEMALE", 40)
# 	order.inventory("JTAG_HEADER", 1000)
# 	order.inventory("LED", 20)
# 	#order.inventory("LM1117T-3.3", 25)
# 	#order.inventory("LM2940", 0)
# 	#order.inventory("LM2940", 23)
# 	#order.inventory("LM2940CT-5.0", 1000)
# 	order.inventory("M3.0_#4_BOX", 100)
# 	order.inventory("MCP2562", 20)
# 	order.inventory("MCP7940", 10)
# 	order.inventory("MF-R300", 8)
# 	order.inventory("MJTP1243", 20)		# 6mm SW
# 	#order.inventory("MOTOR_CONN", 40)	# 5mm terminal block
# 	#order.inventory("MOTOR_ENCODER_CONN_2X5", 50) # 2x5 Shrouded 
# 	order.inventory("OKI-78SR-5/1.5-W36-C", 8)
# 	order.inventory("OSHW_LOGO", 1000)
# 	#order.inventory("OSTTC020162", 100)	# Covered by MOTOR_CONN
# 	#order.inventory("PN2222", 26)
# 	order.inventory("SD101C-TR", 8)		# Shottky Diodes
# 	#order.inventory("WP710A10GD", 30)	# Green LED
# 
# 	#order.request(".1uF", 100)
# 	#order.request(".47", 10)
# 	#order.request("100K", 100)
# 	#order.request("100Kx8", 10)
# 	#order.request("10Kx6", 10)
# 	#order.request("120 1%", 20)
# 	#order.request("16MHz", 10)
# 	#order.request("180", 10)
# 	#order.request("18pF", 10)
# 	#order.request("1uF", 10)
# 	#order.request("22K_SIP5", 10)
# 	#order.request("32.768KHz", 10)
# 	#order.request("33K_SIP5", 10)
# 	#order.request("3K3x4", 10)
# 	#order.request("470_DIP16", 10)
# 	#order.request("4K7x4", 10)
# 	#order.request("74HCT03", 5)
# 	#order.request("74HCT08", 25)
# 	#order.request("754410", 10)
# 	#order.request("ATMEGA328_DIP28", 10)
# 	#order.request("BEAGLEBONE_BLACK", 1)
# 	#order.request("CR-2032/VCN", 10)
# 	#order.request("DIP_SOCKET_14", 20)
# 	#order.request("DIP_SOCKET_28", 10)
# 	#order.request("DIP_SOCKET_40", 20)
# 	#order.request("DIP_SOCKET_8", 20)
# 	#order.request("F-426-0020", 10)
# 	#order.request("FQP47P06", 20)
# 	#order.request("GP1S094HCZ0F", 100)
# 	#order.request("HEADER_1X40", 10)
# 	#order.request("HEADER_1X4_FEMALE", 20)
# 	#order.request("HEADER_2X20_IDC", 0)
# 	#order.request("HEADER_2X4_IDC", 40)
# 	#order.request("HEADER_2X40", 20)
# 	#order.request("HEADER_2X5_IDC", 10)
# 	#order.request("HEADER_2X5_SHROUDED", 100)
# 	#order.request("LTV-826", 20)
# 	#order.request("MCP2562", 25)
# 	#order.request("MCP7940", 10)
# 	#order.request("MF-R300", 20)
# 	#order.request("MJTP1243", 20)
# 	#order.request("MOTOR_CONN", 50)
# 	#order.request("OKI-78SR-5/1.5-W36-C", 8)
# 	#order.request("PN2222", 20)
# 	#order.request("SD101C-TR", 25)
# 	#order.request("SHORTING_BLOCK_WITH_TAB", 100)
# 	#order.request("TTL-232R-3V3", 2)
# 	#order.request("DS1307", 1)
# 
# 	#order.vendor_exclude("Allied")
# 	#order.vendor_exclude("AvNet")
# 	#order.vendor_exclude("Freelance")
# 	#order.vendor_exclude("Future")
# 	#order.vendor_exclude("Jameco")
# 	#order.vendor_exclude("Mouser")
# 	#order.vendor_exclude("Newark")
# 	#order.vendor_exclude("WPG_Cloud")
# 
#     if False:
# 	order = Order(db, "2015_itead_100044961")
# 
# 	order.board("bus_battery",
# 	  "../../../bus_battery/rev_a/bus_battery.cmp", 'A', 2)
# 	order.board("bus_bridge_encoders_sonar",
# 	  "../../../bus_bridge_encoders_sonar/rev_d/bus_bridge_encoders_sonar.cmp", 'D', 4)
# 	order.board("bus_grove12",
# 	  "../../../bus_grove12/rev_b/bus_grove12.cmp", 'B', 1)
# 	order.board("bus_microbus2",
# 	  "../../../bus_microbus2/rev_a/bus_microbus2.cmp", 'A', 1)
# 	order.board("bus_raspberry_pi",
# 	  "../../../bus_raspberry_pi/rev_b/bus_raspberry_pi.cmp", 'B', 4)
# 	order.board("bus_servo8",
# 	  "../../../bus_servo8/rev_a/bus_servo8.cmp", 'A', 2)
# 	order.board("bus_shield",
# 	  "../../../bus_shield/rev_a/bus_shield.cmp", 'A', 1)
# 	order.board("bus_sonar10",
# 	  "../../../bus_sonar10/rev_d/bus_sonar10.cmp", 'C', 8)
# 	order.board("bus_splice",
# 	  "../../../bus_splice/rev_b/bus_splice.cmp", 'B', 2)
# 	order.board("bus_usb_power",
# 	  "../../../bus_usb_power/rev_b/bus_usb_power.cmp", 'B', 4)
# 	order.board("sonar_riser",	
# 	  "../../../sonar_riser/rev_a/sonar_riser.cmp", 'C', 50)
# 
#         order.inventory(".1uF", 10)
# 	order.inventory(".47", 10)	# ?
# 	order.inventory("100K", 60)
# 	order.inventory("100K_SIP6", 0)	# ?
# 	order.inventory("100K_SIP9", 7)
# 	order.inventory("10K", 50)
# 	order.inventory("10K_SIP7", 7)
# 	order.inventory("10K_SIP9", 0)
# 	order.inventory("120", 100)
# 	order.inventory("16MHz", 7)
# 	order.inventory("180", 8)
#         order.inventory("18pF", 13)
# 	order.inventory("1K", 150)
#         order.inventory("1uF", 20)
# 	order.inventory("200", 120)
# 	order.inventory("220", 100)
# 	order.inventory("22K", 100)
# 	order.inventory("22uF_35V_ALUM", 0)
# 	order.inventory("22uF_6.3V_TANT", 30)
# 	order.inventory("32.768KHz", 8)
# 	order.inventory("33K", 30)
# 	order.inventory("3K9_SIP5", 0)
# 	order.inventory("470", 40)
# 	order.inventory("470_DIP16", 40)
# 	order.inventory("4K7", 100)
# 	order.inventory("5MM_TERMINAL_BLOCK_2_POS", 25)
# 	order.inventory("74HC08", 25)	# + 4 from Anchor?
# 	order.inventory("74HCT03", 3)
# 	order.inventory("74HCT08", 6)
# 	order.inventory("74HCT32", 7)
# 	order.inventory("754410", 20)
# 	order.inventory("78L05AC", 0)	# Convert to L78L05AC
# 	order.inventory("82K", 10)
# 	order.inventory("ATMEGA324_DIP40", 4)
# 	order.inventory("ATMEGA328_DIP28", 20)
# 	order.inventory("CR-2032/VCN", 8)
# 	order.inventory("CRYSTAL", 0)	# Map to 16MHz
# 	order.inventory("DPDT_4A", 6)
# 	order.inventory("F-426-0020", 5)
# 	order.inventory("FQP47P06", 17)
# 	order.inventory("Grove_Header_Straight_1x4", 100) # Disable for now
# 	order.inventory("HEADER_1X40", 8)
# 	order.inventory("HEADER_1X4_FEMALE", 20)
# 	order.inventory("HEADER_1X6_FEMALE", 20)
# 	order.inventory("HEADER_1X8_FEMALE", 10)
# 	order.inventory("HEADER_2X20_FEMALE_RA", 0)
# 	order.inventory("HEADER_2X20_IDC", 7)	# From Jameco
# 	order.inventory("HEADER_2X20__SHROUDED", 0)
# 	order.inventory("HEADER_2X40", 6)
# 	order.inventory("HEADER_2X40_RA", 5)
# 	order.inventory("HEADER_2X4_IDC", 90)
# 	order.inventory("HEADER_2X5_IDC", 100)
# 	order.inventory("HEADER_2X5_SHROUDED", 70)
# 	order.inventory("L78L05AC", 20)
# 	order.inventory("L78L33AC", 8)
# 	order.inventory("LED", 20)
# 	order.inventory("LM1117T-3.3", 20)
# 	order.inventory("LM2940", 12)
# 	order.inventory("LM2940", 18)
# 	order.inventory("LTV-816", 0)	# Map to LTV-826
# 	order.inventory("LTV-826", 30)
# 	order.inventory("MCP24XX32A", 10)
# 	order.inventory("MCP2562", 25)
# 	order.inventory("MCP6321_DIP8", 0)
# 	order.inventory("MCP7940", 10)
# 	order.inventory("MF-R300", 10)
# 	order.inventory("OKI-78SR-5/1.5-W36-C", 8)
# 	order.inventory("OSHW", 1000)
# 	order.inventory("OSHW_LOGO", 1000)
# 	order.inventory("S18V20ALV", 10)	# Shut down Pololu for now
# 	order.inventory("S18V20F5",10)
# 	order.inventory("S18V20F6", 10)
# 	order.inventory("S7V8A", 10)
# 	order.inventory("S7VVF5", 10)
# 	order.inventory("SCHOTTKY_DIODE", 1)
# 	order.inventory("USB_B", 0)
# 
# 	order.vendor_exclude("Arrow")
# 	order.vendor_exclude("Allied")
# 	order.vendor_exclude("AvNet")
# 	order.vendor_exclude("Freelance")
# 	order.vendor_exclude("Future")
# 	order.vendor_exclude("Jameco")
# 	order.vendor_exclude("MCM")
# 	order.vendor_exclude("Mouser")
# 	order.vendor_exclude("Newark")
# 	order.vendor_exclude("WPG_Cloud")
# 
# 
# 	#order.board("bus_bridge_encoders_sonar",
# 	#  "../../../bus_bridge_encoders_sonar/rev_c/" + \
# 	#  "bus_bridge_encoders_sonar.cmp", 'C', 8)
# 
#     if False:
# 	order = Order(db, "2015_bay_area_1234")
# 
# 	order.board("bus_loki",
# 	  "../../../catkin_ws/src/bus_loki_pcb/rev_c/bus_loki.cmp", 'C', 10)
# 
# 	if False:
# 	    order.inventory(".1uF", 50 + 25)
# 	    order.inventory("100K", 100 + 70)
# 	    order.inventory("10K", 100 + 70)
# 	    order.inventory("120", 10 + 9)
# 	    order.inventory("124", 25 + 24)
# 	    order.inventory("13K", 25 + 10)
# 	    order.inventory("143K", 25 + 10)
# 	    order.inventory("16 MHz", 2 + 1)
# 	    order.inventory("18pF", 10 + 8)
# 	    order.inventory("1K", 10 + 5)
# 	    order.inventory("1uF", 3 + 2)
# 	    order.inventory("20K", 10 + 5)
# 	    order.inventory("2MM_HOLE", 1000)
# 	    order.inventory("3K9", 10 + 5)
# 	    order.inventory("30K9", 25 + 10)
# 	    order.inventory("3MM_HOLE", 1000)
# 	    order.inventory("470", 25 + 10)
# 	    order.inventory("470uF", 12 + 6)
# 	    order.inventory("4K7", 25 + 10)
# 	    order.inventory("5MM_TERMINAL_BLOCK_2_POS", 6)
# 	    #order.inventory("744045210", 2 + 1)
# 
# 	    order.inventory("ATmega2560", 2 + 1)
# 	    order.inventory("BSS138", 10 + 8)
# 	    order.inventory("CDBB240-G", 5 + 3)
# 	    order.inventory("CIB10P100NC", 10 + 10)
# 	    order.inventory("EVQ-11U05R", 2 + 1)
# 	    order.inventory("GP1S094HCZ0F", 20)
# 	    order.inventory("HEADER_1X3_FEMALE", 6)
# 	    order.inventory("HEADER_1X40", 10)	# Test points do not need pins
# 	    order.inventory("HEADER_1X6_FEMALE", 10)
# 	    order.inventory("HEADER_2X20_FEMALE_RA", 2 + 1)
# 	    order.inventory("HEADER_2X40", 8)
# 	    order.inventory("HEADER_2X5_IDC", 50)
# 	    order.inventory("HEADER_2X5_SHROUDED", 50)
# 	    order.inventory("L293_DIP16", 4)	# Substitute SN754410 if needed
# 	    order.inventory("L293_SOIC20", 2 + 2)
# 	    order.inventory("LTST-C191KGKT", 25 + 17)
# 	    order.inventory("M3.0_#4_BOX", 1000)
# 	    order.inventory("MCP2562", 5 + 3)
# 	    order.inventory("MCP24XX32A", 2 + 1)
# 	    order.inventory("RTC_CRYSTAL", 2 + 1)
# 	    order.inventory("SLOT_HOLE_10X20MM", 1000)
# 
# 	    order.request("SN74HC32", 10)
# 	    order.request("MCP7940", 10)
# 	    order.request("TLE4906K", 10)
# 	    order.request("HEADER_1X3_FEMALE", 10)
# 	    order.request("1K", 50)
# 	    order.request("USB_B", 10)
# 	    order.request("SRR1280-221K", 4)
# 	    order.request("MCP6542", 10)
# 
# 	    order.vendor_exclude("Arrow")
# 	    order.vendor_exclude("Allied")
# 	    order.vendor_exclude("AvNet")
# 	    order.vendor_exclude("Freelance")
# 	    order.vendor_exclude("Future")
# 	    order.vendor_exclude("Jameco")
# 	    order.vendor_exclude("MCM")
# 	    order.vendor_exclude("Mouser")
# 	    order.vendor_exclude("Newark")
# 	    order.vendor_exclude("WPG_Cloud")
# 
#     if True:
# 	order = Order(db, "2015_china_1234")
# 
# 	order.board("bus_loki",
# 	  "../../../catkin_ws/src/bus_loki_pcb/rev_d/bus_loki.net", 'D', 10)
# 
# 	if False:
# 	    order.inventory(".1uF", 50 + 25)
# 	    order.inventory("100K", 100 + 70)
# 	    order.inventory("10K", 100 + 70)
# 	    order.inventory("120", 10 + 9)
# 	    order.inventory("124", 25 + 24)
# 	    order.inventory("13K", 25 + 10)
# 	    order.inventory("143K", 25 + 10)
# 	    order.inventory("16 MHz", 2 + 1)
# 	    order.inventory("18pF", 10 + 8)
# 	    order.inventory("1K", 10 + 5)
# 	    order.inventory("1uF", 3 + 2)
# 	    order.inventory("20K", 10 + 5)
# 	    order.inventory("2MM_HOLE", 1000)
# 	    order.inventory("3K9", 10 + 5)
# 	    order.inventory("30K9", 25 + 10)
# 	    order.inventory("3MM_HOLE", 1000)
# 	    order.inventory("470", 25 + 10)
# 	    order.inventory("470uF", 12 + 6)
# 	    order.inventory("4K7", 25 + 10)
# 	    order.inventory("5MM_TERMINAL_BLOCK_2_POS", 6)
# 	    #order.inventory("744045210", 2 + 1)
# 
# 	    order.inventory("ATmega2560", 2 + 1)
# 	    order.inventory("BSS138", 10 + 8)
# 	    order.inventory("CDBB240-G", 5 + 3)
# 	    order.inventory("CIB10P100NC", 10 + 10)
# 	    order.inventory("EVQ-11U05R", 2 + 1)
# 	    order.inventory("GP1S094HCZ0F", 20)
# 	    order.inventory("HEADER_1X3_FEMALE", 6)
# 	    order.inventory("HEADER_1X40", 10)	# Test points do not need pins
# 	    order.inventory("HEADER_1X6_FEMALE", 10)
# 	    order.inventory("HEADER_2X20_FEMALE_RA", 2 + 1)
# 	    order.inventory("HEADER_2X40", 8)
# 	    order.inventory("HEADER_2X5_IDC", 50)
# 	    order.inventory("HEADER_2X5_SHROUDED", 50)
# 	    order.inventory("L293_DIP16", 4)	# Substitute SN754410 if needed
# 	    order.inventory("L293_SOIC20", 2 + 2)
# 	    order.inventory("LTST-C191KGKT", 25 + 17)
# 	    order.inventory("M3.0_#4_BOX", 1000)
# 	    order.inventory("MCP2562", 5 + 3)
# 	    order.inventory("MCP24XX32A", 2 + 1)
# 	    order.inventory("RTC_CRYSTAL", 2 + 1)
# 	    order.inventory("SLOT_HOLE_10X20MM", 1000)
# 
# 	    order.request("SN74HC32", 10)
# 	    order.request("MCP7940", 10)
# 	    order.request("TLE4906K", 10)
# 	    order.request("HEADER_1X3_FEMALE", 10)
# 	    order.request("1K", 50)
# 	    order.request("USB_B", 10)
# 	    order.request("SRR1280-221K", 4)
# 	    order.request("MCP6542", 10)
# 
# 	    order.vendor_exclude("Arrow")
# 	    order.vendor_exclude("Allied")
# 	    order.vendor_exclude("AvNet")
# 	    order.vendor_exclude("Freelance")
# 	    order.vendor_exclude("Future")
# 	    order.vendor_exclude("Jameco")
# 	    order.vendor_exclude("MCM")
# 	    order.vendor_exclude("Mouser")
# 	    order.vendor_exclude("Newark")
# 	    order.vendor_exclude("WPG_Cloud")
# 
# 
#     #order.drawer(".1uF", "CAP", None, "")
#     #order.drawer("22uF", "CAP", None, "")
#     #order.drawer("HEADER_1X2", "CON", None, "")
#     #order.drawer("ELD207(TA)-V", "OPT", "Isolator2_SOIC8", "ELD207")
#     #order.drawer("L298", "IC", None, "")
#     #order.drawer("L78L05AC", "VR", None, "")
#     #order.drawer("L78L33AC", "VR", None, "")
# 
#     # Huge price means no vendor found:
#     order.generate()
# 
# main()

def main():
    print("Hello")
    database = Database()
    order = Order(database)
    order.board("Loki", "E.1", "bus_loki.net", 10)

if __name__ == "__main__":
    main()
