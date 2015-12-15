#!/usr/bin/env python

# Note: There is another BOM program at:
#
#  https://github.com/CrashBangProto/KiCad_BOM_Export
#
# This uses SupplyFrame's FindChips API!  Woo Hoo!!!
# Password API key is: lTnQFAMJIqyRG4rMFGxf

import kicost
import sys

def tiers_to_text(tiers):
    assert isinstance(tiers, dict)
    keys = tiers.keys()
    keys.sort()
    text = ""
    for key in keys:
	cost = tiers[key]
	assert isinstance(cost, float)
	text += " {0}:${1}".format(key, cost)
    return text

def main():
    print("Hello")
    arguments = sys.argv
    if len(arguments) < 2:
	print("usage: scrape part_number...")
	return 0

    for part_number in sys.argv[1:]:
	print("part_number='{0}'".format(part_number))

	try:
	    digikey_html_tree, digikey_url = \
	      kicost.get_digikey_part_html_tree(part_number)
	    digikey_price_tiers = \
	      kicost.get_digikey_price_tiers(digikey_html_tree)
	    digikey_quantity_available = \
	      kicost.get_digikey_qty_avail(digikey_html_tree)
	    digikey_part_number = kicost.get_digikey_part_num(digikey_html_tree)
	    print("DigiKey: VP#:{0} Avail:{1} Cost:{2}".format(
	      digikey_part_number, digikey_quantity_available,
	      tiers_to_text(digikey_price_tiers)))
	except kicost.PartHtmlError:
	    print("Digikey does not have part: {0}".format(part_number))

	try:
	    mouser_html_tree, mouser_url = \
	      kicost.get_mouser_part_html_tree(part_number)
	    mouser_price_tiers = kicost.get_mouser_price_tiers(mouser_html_tree)
	    mouser_quantity_available = \
	      kicost.get_mouser_qty_avail(mouser_html_tree)
	    mouser_part_number = kicost.get_mouser_part_num(mouser_html_tree)
	    print("Mouser: VP#:{0} Avail:{1} Cost:{2}".format(
	      mouser_part_number, mouser_quantity_available,
	      tiers_to_text(mouser_price_tiers)))
	except kicost.PartHtmlError:
	    print("Mouser does not have part: {0}".format(part_number))

	try:
	    newark_html_tree, newark_url = \
	      kicost.get_newark_part_html_tree(part_number)
	    newark_price_tiers = kicost.get_newark_price_tiers(newark_html_tree)
	    newark_quantity_available = \
	      kicost.get_newark_qty_avail(newark_html_tree)
	    newark_part_number = kicost.get_newark_part_num(newark_html_tree)
	    print("Newark: VP#:{0} Avail:{1} Cost:{2}".format(
	      newark_part_number, newark_quantity_available,
	      tiers_to_text(newark_price_tiers)))
	except kicost.PartHtmlError:
	    print("Newark does not have part: {0}".format(part_number))

if __name__ == "__main__":
    main()
