#!/usr/bin/env python

# Note: There is another BOM program at:
#
#  https://github.com/CrashBangProto/KiCad_BOM_Export
#
# This uses SupplyFrame's FindChips API!  Woo Hoo!!!
# Password API key is: lTnQFAMJIqyRG4rMFGxf

import re
import kicost
import sys
from bs4 import BeautifulSoup

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

def get_digikey_manufacturer(html_tree):
    '''Get the manufacture from the Digikey product page.'''
    manufacture = ""
    try:
	# Grab the product *details_tree*:
        details_tree = html_tree.find('table', class_='product-details')
	#print("details_tree:")
	#print(details_tree.prettify())

	# Visit *row_tree* in *details_tree*:
	for row_tree in details_tree.find_all('tr'):
	    try:
		# Grab *th_tree* that matches <th>...</th>:
		th_tree = row_tree.find('th')
		#print("th_tree:")
		#print(th_tree.prettify())
		th_text = th_tree.get_text().strip()

		# If we match the manufacture heading, dig deeper:
		if th_text == "Manufacturer":
		    # Grab the *a_tree* that matches <a>...</a>:
		    a_tree = row_tree.find("a")
		    #print("a_tree:")
		    #print(a_tree.prettify())

		    # Grab the *span_tree* that matches <span>...</span>:
		    span_tree = a_tree.find("span")
		    #print("span_tree:")
		    #print(span_tree.prettify())

                    # Grab the manufacture name:
		    manufacturer = span_tree.get_text().strip()
		    #print("manufacturer='{0}'".format(manufacturer))
		    break
	    except:
		pass
    except:
        pass
    return manufacturer

def get_mouser_manufacturer(html_tree):
    manufacturer = ""
    try:
	# Find the *product_desc_tree* <div>:
	product_desc_tree = html_tree.find("div", id="product-desc")
	#print("product_desc_tree:")
	#print(product_desc_tree.prettify())

	# Iterate though each <div class="row">:
	div_row_trees = product_desc_tree.find_all("div", class_="row")
	for div_row_tree in div_row_trees:
	    try:
		#print("div_row_tree:")
		#print(div_row_tree.prettify())

		# The first <b>...<b> is the row heading:
		b_tree = div_row_tree.find("b")
		#print("b_tree:")
		#print(b_tree.prettify())

		# Match the heading to "Manufacturer:":
		b_tree_text = b_tree.get_text().strip(" \n")
		#print("b_tree_text='{0}'".format(b_tree_text))
		if b_tree_text == "Manufacturer:":
		    #print("********************")
		    #print("Manufacturer div_row_tree:")
		    #print(div_row_tree.prettify())

		    # The <span>...</span> contains the *manufacturer*:
		    span_tree = div_row_tree.find("span")
		    #print("span_tree:")
		    #print(span_tree.prettify())

		    manufacturer = span_tree.get_text().strip(" \n")
		    break
	    except:
		#print("skip")
		pass
    except:
	pass
    return manufacturer

def get_newark_manufacturer(html_tree):
    manufacturer = ""
    try:
	# Find the *product_desc_tree* <div>:
	product_desc_tree = html_tree.find("div", id="productDescription")
	#print("product_desc_tree:")
	#print(product_desc_tree.prettify())

	li_trees = product_desc_tree.find_all("li")
	for li_tree in li_trees:
	    try:
		#print("li_tree:")
		#print(li_tree.prettify())
	        
		span_trees = li_tree.find_all("span")
		#for span_tree in span_trees:
		#    print("span_tree:")
		#    print(span_tree.prettify())

		span_tree0 = span_trees[0]
		heading_name = span_tree0.get_text().strip(" \n")
		#print("heading_name={0}".format(heading_name))

		if heading_name == "Manufacturer:":
		    a_tree = li_tree.find("a")
		    #print("a_tree:")
		    #print(a_tree.prettify())

		    span_tree = a_tree.find("span")
		    #print(span_tree.prettify())

		    manufacturer = span_tree.get_text().strip(" \n")
		    #print("manufacturer={0}".format(manufacturer))
		    break
	    except:
		pass
    except:
	pass
    return manufacturer

def main():
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
	    digikey_manufacturer = get_digikey_manufacturer(digikey_html_tree)
	    print("DigiKey: VP#:{0} Avail:{1} Mfr:{2} Cost:{3}".format(
	      digikey_part_number, digikey_quantity_available,
	      digikey_manufacturer,
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
	    mouser_manufacturer = get_mouser_manufacturer(mouser_html_tree)
	    print("Mouser: VP#:{0} Avail:{1} Mfr:{2} Cost:{3}".format(
	      mouser_part_number, mouser_quantity_available,
	      mouser_manufacturer,
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
	    newark_manufacturer = get_newark_manufacturer(newark_html_tree)
	    print("Newark: VP#:{0} Avail:{1} Mfr:{2} Cost:{3}".format(
	      newark_part_number, newark_quantity_available,
	      newark_manufacturer,
	      tiers_to_text(newark_price_tiers)))
	except kicost.PartHtmlError:
	    print("Newark does not have part: {0}".format(part_number))

if __name__ == "__main__":
    main()
