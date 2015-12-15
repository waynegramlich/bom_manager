#!/usr/bin/env python

from bom_manager import *

def main():
    database = Database()
    order = Order(database)
    order.board("bom_test", "A.1", "bom_test.net", 1)
    order.process()

if __name__ == "__main__":
    main()
