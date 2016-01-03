#!/usr/bin/env python

from bom_manager import *

def main():
    database = Database()
    order = Order(database)
    order.board("bom_test", "A.1", "bom_test.net", 1)
    #order.vendor_exclude("Verical")
    #order.vendor_exclude("WPG Americas, Inc.")
    #order.vendor_exclude("Newark element14")
    #order.vendor_exclude("Farnell element14")
    #order.vendor_exclude("Quest Components")
    order.process()

if __name__ == "__main__":
    main()
