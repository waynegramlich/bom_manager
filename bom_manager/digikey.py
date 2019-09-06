#!/usr/bin/env python3

# <------------------------------------------- 100 characters -----------------------------------> #

# Coding standards:
# * In general, the coding guidelines for PEP 8 are used.
# * All code and docmenation lines must be on lines of 100 characters or less.
# * Comments:
#   * All code comments are written in [Markdown](https://en.wikipedia.org/wiki/Markdown).
#   * Code is organized into blocks are preceeded by comment that explains the code block.
#   * For methods, a comment of the form `# CLASS_NAME.METHOD_NAME():` is before each method
#     definition.  This is to disambiguate overloaded methods that implemented in different classes.
# * Class/Function standards:
#   * Indentation levels are multiples of 4 spaces and continuation lines have 2 more spaces.
#   * All classes are listed alphabetically.
#   * All methods within a class are listed alphabetically.
#   * No duck typing!  All function/method arguments are checked for compatibale types.
#   * Inside a method, *self* is usually replaced with more descriptive variable name.
#   * Generally, single character strings are in single quotes (`'`) and multi characters in double
#     quotes (`"`).  Empty strings are represented as `""`.  Strings with multiple double quotes
#     can be enclosed in single quotes.
#   * Lint with:
#
#       flake8 --max-line-length=100 digikey.py | fgrep -v :3:1:
#
import bom_manager as bom
import bs4
import glob
import requests
import time
import os

# Digikey:
class Digikey:

    # Digikey.__init__():
    def __init__(self):
        digikey = self
        top_directory = "/home/wayne/public_html/projects/bom_digikey_plugin"
        digikey.top_directory = top_directory
        digikey.products_html_file_name = os.path.join(top_directory,
                                                       "www.digikey.com_products_en.html")
        digikey.root_directory = os.path.join(top_directory, "ROOT")
        digikey.csvs_directory = os.path.join(top_directory, "CSVS")

    # Digikey.collection_extract():
    def collection_extract(self, hrefs_table, tracing=None):
        # Now we construct *collection* which is a *bom.Collection* that contains a list of
        # *DigkeyDirectory*'s (which are sub-classed from *bom.Directory*.  Each of those
        # nested *DigikeyDirectory*'s contains a further list of *DigikeyTable*'s.
        #

        # The sorted keys from *hrefs_table* are alphabetized by '*base*/*id*' an look basically
        # as follows:
        #
        #        None/-1                                          # Null => Root directory
        #        audio-products/10                                # *items* < 0 => directory
        #        audio-product/accessories/159
        #        audio-products-buzzers-and-sirends/157
        #        audio-products-buzzer-ellements-piezo-benders/160
        #        audio-products-microphones/159
        #        audio-products-speakers/156
        #        battery-products/6                               # *items* < 0 => directory
        #        battery-products-accessories/87
        #        battery-products-batteries-non-rechargeable-primary/90
        #        battery-products-batteries-rechargeable-secondary/91
        #        battery-products-battery-chargers/85
        #        battery-products-battery-holders-clips-contacts/86
        #        battery-products-battery-packas/89
        #        battery-products-cigarette-ligheter-assemblies/88
        #        boxes-enclosures-rackes/27
        #        boxes-enclosures-rackes-backplanes/587
        #        ....
        #
        # We need to group all the entries that match "audio-products" together,
        # all the entries that matach *battery-products* together, etc.
        #
        # Drilling down another level, each *key* (i.e. '*base*/*id*') can have multiple
        # entries.  We scan through these entries to extract the information we want:
        #
        #     HRef[0]:key=''
        #      Match[0]: '', -1,
        #                 'See All', '',
        #                 'https://www.digikey.com/products/en/')
        #     HRef[1]:key='audio-products/10'
        #      Match[0]: 'audio-products', 10,
        #                 'Audio Products', '',
        #                 'https://www.digikey.com/products/en/audio-products/10')
        #      Match[1]: 'audio-products', 10,
        #                 'Audio Products', '',
        #                 'https://www.digikey.com/products/en/audio-products/10')
        #      Match[2]: 'audio-products', 10,
        #                 'Audio Products', '',
        #                 'https://www.digikey.com/products/en/audio-products/10')
        #      Match[3]: 'audio-products', 10,
        #                 'Audio Products', '',
        #                 'https://www.digikey.com/products/en/audio-products/10')
        #      Match[4]: 'audio-products', 10,
        #                 'Audio Products', '',
        #                 'https://www.digikey.com/products/en/audio-products/10')
        #      Match[5]: 'audio-products', 10,
        #                 '613 New Products', '',
        #                 'https://www.digikey.com/products/en/audio-products/10')
        #     HRef[2]:key='audio-products/accessories/159'
        #      Match[0]: 'audio-products-accessories', 159,
        #                 'Accessories', '',
        #                 'https://www.digikey.com/products/en/audio-products/accessories/159')
        #      Match[1]: 'audio-products-accessories', 159,
        #                 'Accessories', '(295 items)',
        #                 'https://www.digikey.com/products/en/audio-products/accessories/159')
        #     ...

        # Verify argument types:
        assert isinstance(hrefs_table, dict)

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>Digikey.collection_extract(*,*)")

        # Grab some values from *digikey* (i.e. *self*):
        digikey = self
        root_directory = digikey.root_directory

        # Create the *collection* (*collections* is temporary and is not really used):
        collections = bom.Collections("Collections", [], "", None)
        collection = bom.Collection("Digi-Key", collections, root_directory, "", None)
        parent = collection
        assert collections.has_child(collection)

        # Create the sorted *hrefs_table_keys*.  The first 20 entries look like:
        hrefs_table_keys = enumerate(sorted(hrefs_table.keys()))

        # Sweep through sorted *hrefs* and process each *matches* lists:
        current_directory = None
        for href_index, hrefs_key in hrefs_table_keys:
            matches = hrefs_table[hrefs_key]
            if tracing is not None:
                print(f"{tracing}HRef[{href_index}]: '{hrefs_key}' len(matches)={len(matches)}")

            # There are one or more *matches*.  We'll take the first *a_content* that is non-null
            # and treat that as the *name*.  The number of *items* is taken from the first
            # *li_content* that end with " items)".  We visit *matches* in reverse order to work
            # around an obscure issue that is not worth describing.  If you feeling figuring it
            # out, please remove the call to `reversed()`:
            name = None
            items = -1
            url = None
            for match_index, match in enumerate(reversed(sorted(matches))):
                # Unpack *match*:
                href, base, id, a_content, li_content, url = match
                assert href == "" or href == hrefs_key, f"href='{href}' hrefs_key='{hrefs_key}'"
                if tracing is not None:
                    print(f"Match[{match_index}]: "
                          f"'{base}', {id}, '{a_content}', '{li_content}', '{url}'")

                # Fill in *name* and *items*:
                if name is None and not a_content.startswith("See"):
                    name = a_content.strip(" \t\n")
                    items_pattern = " items)"
                    if items < 0 and li_content.endswith(" items)"):
                        open_parenthesis_index = li_content.find('(')
                        items = int(li_content[open_parenthesis_index+1:-len(items_pattern)])
                    break

            # Dispatch based on *name* and *items*:
            if name is None:
                # We already created *root_directory* so there is nothing to do here:
                pass
            elif items < 0:
                # We have a new *DigikeyDirectory* to create and make the *current_directory*.
                current_directory = DigikeyDirectory(name, collection, id, url, tracing=next_tracing)
            else:
                # We create a new *DigikeyTable* that is appended to *current_directory*.
                # Note: the initializer automatically appends *table* to *current_directory*:
                assert current_directory is not None
                DigikeyTable(name, current_directory, base, id, href, url, tracing=next_tracing)

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=Digikey.collection_extract(*,*)=>*")

        # *collection* is in its first incarnation and ready for reorganization:
        return collection

    # Digikey.collection_reorganize():
    def collection_reorganize(self, collection, tracing=None):
        # Verify argument types:
        assert isinstance(collection, bom.Collection)
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>Digikey.collection_reorganize('{collection.name}')")

        # Extract a sorted list of *directories* from *collection*:
        directories = collection.children_get()
        directories.sort(key=lambda directory: directory.name)

        # print("len(directories)={0}".format(len(directories)))
        for directory_index, directory in enumerate(directories):
            assert isinstance(directory, DigikeyDirectory)
            if tracing is not None:
                print(f"Directory[{directory_index}]: '{directory.name}'")
            directory.reorganize(tracing=next_tracing)

        # Wrap up requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=Digikey.root_directory_reorganize('{collection.name}')")

    # Digikey.collection_verify():
    def collection_verify(self, digikey_collection, hrefs_table, tracing=None):
        # Verify argument types:
        assert isinstance(digikey_collection, bom.Collection)
        assert isinstance(hrefs_table, dict)
        assert isinstance(tracing, str) or tracing is None
    
        # Perform any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}=>Digikey.collection_verify()")

        # For testing only, grab all of the *directories* and *tables* from *root_directory*,
        # count them up, and validate that the sizes all match:
        directories = digikey_collection.directories_get()
        directories_size = len(directories)
        tables = digikey_collection.tables_get() 
        tables_size= len(tables)
        hrefs_table_size = len(hrefs_table)

        # Verify that we did not loose anything during extraction:
        if tracing is not None:
            print(f"{tracing}directories_size={directories_size}")
            print(f"{tracing}tables_size={tables_size}")
            print(f"{tracing}hrefs_table_size={hrefs_table_size}")

        # For debugging only:
        if hrefs_table_size != directories_size + tables_size:
            # Make a copy of *hrefs_table*:
            hrefs_table_copy = hrefs_table.copy()

            # Remove all of the *tables* from *hrefs_table_copy*:
            errors = 0
            url_prefix = "https://www.digikey.com/products/en/"
            url_prefix_size = len(url_prefix)
            for table in tables:
                table_key = table.url[url_prefix_size:]
                if table_key in hrefs_table_copy:
                    del hrefs_table_copy[table_key]
                else:
                    errors += 1
                    print(f"table_key='{table_key}' not found")

            # Remove all of the *directories* from * *hrefs_table_copy*:
            for directory in directories:
                directory_key = directory.url[url_prefix_size:]
                if directory_key in hrefs_table_copy:
                    del hrefs_table_copy[directory_key]
                else:
                    errors += 1
                    print(f"directory_key='{directory_key}' not found")

            # Print out the remaining unumatched keys:
            print(f"hrefs_table_copy.keys={list(hrefs_table_copy.keys())}")

            assert errors == 0, f"{errors} Error found"

        # Perform any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}=>Digikey.collection_verify()")

    # Digikey.csvs_download():
    def csvs_download(self, collection, tracing=None):
        # Verify argument types:
        assert isinstance(collection, bom.Collection)
        assert isinstance(tracing, str) or tracing is not None

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>Digikey.csvs_download(*, '{collection.name}')")

        # Grab the *csvs_directory* from *digikey* (i.e. *self*):
        digikey = self
        csvs_directory = digikey.csvs_directory

        # Fetch example `.csv` files for each table in *collection*:
        downloads_count = 0
        for directory in collection.children_get():
            downloads_count = directory.csvs_download(csvs_directory, downloads_count,
                                                      tracing=next_tracing)

        # Wrap up any requested *tracing*:
        result = downloads_count
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}<=Digikey.csvs_download(*, *, '{collection.name}')=>{downloads_count}")
        return downloads_count

    # Digikey.read_and_process():
    def csvs_read_and_process(self, collection, tracing=None):
        # Verify argument types:
        assert isinstance(collection, bom.Collection)
        assert isinstance(tracing, str) or tracing is not None

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>Digikey.csvs_read_and_process(*, '{collection.name}')")

        # Grab the *csvs_directory* from *digikey* (i.e. *self*):
        digikey = self
        csvs_directory = digikey.csvs_directory

        # Fetch example `.csv` files for each table in *collection*:
        for directory in collection.children_get():
            directory.csv_read_and_process(csvs_directory, tracing=next_tracing)

        # Wrap up any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}<=Digikey.csvs_read_and_process(*, '{collection.name}')")

    @staticmethod
    # Digikey.hrefs_table_show():
    def hrefs_table_show(hrefs_table, limit, tracing=None):
        # Verify rgument types:
        assert isinstance(hrefs_table, dict)
        assert isinstance(limit, int)

        # Perform any requested_tracing:
        if tracing is not None:
            print(f"{tracing}=>Digikey.hrefs_table_show=>(*, {limit})")

        # Iterate over a sorted *hrefs_table_keys*:
        hrefs_table_keys = sorted(hrefs_table.keys())
        for index, hrefs_table_key in enumerate(hrefs_table_keys):
            matches = hrefs_table[hrefs_table_key]
            print(f"{tracing}HRef[{index}]:key='{hrefs_table_key}'")
            for match_index, match in enumerate(matches):
                # Unpack *match*:
                href, base, id, a_content, li_content, url = match
                print(f"{tracing} Match[{match_index}]: '{href}', '{base}', {id},")
                print(f"{tracing}            '{a_content}', '{li_content}',")
                print(f"{tracing}            '{url}')")
            if index >= limit:
                break

        # Wrap up any requested_tracing:
        if tracing is not None:
            print(f"{tracing}<=Digikey.hrefs_table_show=>(*, {limit})")

    # Digikey.process():
    def process(self, tracing=None):
        # This starts with the top level page from Digi-Key.com:
        #
        #   https://www.digikey.com/products/en
        #
        # Which is manually copied qout of the web browser and stored into the file named
        # *digikey_products_html_file_name*:

        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>Digikey.process()")

        # Read the `.html` file that contains the top level origanziation and convert it
        # into a Beautiful *soup* tree:
        digikey = self
        soup = digikey.soup_read(tracing=next_tracing)

        # Sweep through the *soup* tree and get a href information stuffed into *href_tables*:
        hrefs_table = digikey.soup_extract(soup, tracing=next_tracing)
        assert isinstance(hrefs_table, dict)

        # Extract the *digikey_collection* structure using *hrefs_table*:
        collection = digikey.collection_extract(hrefs_table, tracing=next_tracing)
        digikey.collection_verify(collection, hrefs_table, tracing=next_tracing)
        assert isinstance(collection, bom.Collection)

        # Reorganize and verify *collection*:
        digikey.collection_reorganize(collection, tracing=next_tracing)

        # Make sure we have an example `.csv` file for each table in *collection*:
        downloads_count = digikey.csvs_download(collection, tracing=next_tracing)
        if tracing is not None:
            print(f"{tracing}downloads_count={downloads_count}")

        # Clear out the root directory and repoulate it with updated tables:
        digikey.root_directory_clear(tracing=next_tracing)
        digikey.csvs_read_and_process(collection, tracing=next_tracing)

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=Digikey.process()")

    # Digikey.root_directory_clear():
    def root_directory_clear(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}=>Digikey.root_directory_clear(*)")

        # Scan the *root_directory* of *digikey* (i.e. *self*) for all sub files and directories:
        digikey = self
        root_directory = digikey.root_directory
        file_names = glob.glob(root_directory + "/**", recursive=True)

        # Sort *file_name* them so that the longest names come first (i.e. -negative length).
        file_names.sort(key=lambda file_name: -len(file_name))

        # Set *debug* to *True* for debug tracing:
        debug = False

        # Visit each *file_name* in *file_names* and delete them (if appropriate):
        for file_name_index, file_name in enumerate(file_names):
            # Hang onto the `README.md` and the top level directory (i.e. *file_name[:-1]*):
            delete = not (file_name.endswith("README.md") or file_name[:-1] == root_directory)

            # *delete* *file_name* if appropiate:
            if delete:
                # *file_name* is a directory:
                if os.path.isdir(file_name):
                    if debug:
                        print("[{0}]: Remove file '{1}'".format(file_name_index, file_name))
                    os.rmdir(file_name)
                else:
                    # *file_name* is a file:
                    if debug:
                        print("[{0}]: Remove directory '{1}'".format(file_name_index, file_name))
                    os.remove(file_name)
            else:
                # *file_name* is to be kept:
                if debug:
                    print("[{0}]: Keep '{1}'".format(file_name_index, file_name))

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=Digikey.root_directory_clear(*)")

    # Digikey.soup_extract():
    def soup_extract(self, soup, tracing=None):
        # Now we use the *bs4* module to screen scrape the information we want from *soup*.
        # We are interested in sections of HTML that looks as follows:
        #
        #        <LI>
        #            <A class="..." href="*href*">
        #                *a_content*
        #            </A>
        #          *li_content*
        #        </LI>
        #
        # where:
        #
        # * *href*: is a hypertext link reference of the form:
        #
        #        /products/en/*base*/*id*?*search*
        #
        #   * "*?search*": *?search* is some optional search arguments that can safely be ignored.
        #   * "/*id*": *id* is a decimal number that is 1-to-1 with the *base*.  The *id* is used
        #     by Digikey for specifying were to start.  When the *href* specifies a directory
        #     this is simply not present.
        #   * "*base*": *base* is a hyphen separeted list of words (i.e. "audio-products",
        #     "audio_products-speakers", etc.)  Note: most of the words are lower case, but
        #     there are a few that are mixed upper/lower case.
        #   * The prefix "/products/en" is present for each *href* and can be ignored.
        #
        # * *a_content*: *a_content* is the human readable name for the *href* and is typically
        #   of the form "Audio Products", "Audio Products - Speakers", etc.  This is typically
        #   considerd to be the *title* of the table or directory.
        #
        # * *li_content*: *li_content* is frequently empty, but sometimes specifies the
        #   number of items in the associated table.  It is of the form "(*items* Items)"
        #   where *items* is a decimal number.  We only care about the decimal number.
        #
        # The output of scanning the *soup* is *hrefs_table*, which is a list *matches*, where the
        # each *match* is a 5-tuple containing:
        #
        #    (*base*, *id*, *a_content_text*, *li_content_text*, *url*)
        #
        # *id* is -1 if there was no "/*id*" present in the *href*.

        # Verify argument types:
        assert isinstance(soup, bs4.BeautifulSoup)
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}Digikey.soup_extract(*, *)")

        # Start with an empty *hrefs_table*:
        hrefs_table = dict()
        url_prefix = "/products/en/"
        url_prefix_size = len(url_prefix)

        # Find all of the <A HRef="..."> tags in *soup*:
        for a in soup.find_all("a"):
            assert isinstance(a, bs4.element.Tag)

            # We are only interested in *href*'s that start with *url_prefix*:
            href = a.get("href")
            if href is not None and href.startswith(url_prefix) and href != url_prefix:
                # Strip off the "?*search" from *href*:
                question_mark_index = href.find('?')
                if question_mark_index >= 0:
                    href = href[:question_mark_index]

                # Strip the *url_prefix* from the beginning of *href*:
                href = href[url_prefix_size:]

                # Split out the *base* and *id* (if it exists):
                # print("href3='{0}'".format(href))
                slash_index = href.rfind('/')
                if slash_index >= 0:
                    # *id* exists, so store it as a positive integer:
                    base = href[:slash_index].replace('/', '-')
                    # print("href[slash_index+1:]='{0}'".format(href[slash_index+1:]))
                    id = int(href[slash_index+1:])
                else:
                    # *id* does not exist, so store -1 into *id*:
                    base = href
                    id = -1

                # Construct *a_contents_text* from the contents of *a* tag.  In general this
                # text is a reasonable human readable summary of what the table/directory is about:
                a_contents_text = ""
                for a_content in a.contents:
                    if isinstance(a_content, bs4.element.NavigableString):
                        a_contents_text += a_content.string
                a_contents_text = a_contents_text.strip()

                # Construct the *li* content which is the text between the end of the </A>
                # tag and the </LI> tag.  In general, we only care if there is a class
                # attribute in the <A> tag (i.e. <A class="..." href="...".)
                # Sometimes the <A> tag is nested in an <LI> tag.  This text when present
                # will frequently have the basic form of "...(*items* items)...".
                li_contents_text = ""
                xclass = a.get("class")
                if xclass is not None:
                    # We have a `class="..."` attribute, so now look for the *parent* *li* tag:
                    parent = a.parent
                    assert isinstance(parent, bs4.element.Tag)
                    if parent.name == "li":
                        # We have an *li* tag, so extract its contents into *li_contents_text*:
                        li = parent
                        for li_content in li.contents:
                            if isinstance(li_content, bs4.element.NavigableString):
                                li_contents_text += li_content.string
                        li_contents_text = li_contents_text.strip()

                # Now stuff *base*, *id*, *a_contents_text*, *li_contents_text*, and *url*
                # into *hrefs_table* using *href* as the key.  Since same *href* can occur multiple
                # times in the *soup* we store everything in a the *matches* list containing
                # a *match* of 5-tuples:
                #href_key = f"{base}/{id}"
                if href in hrefs_table:
                    matches = hrefs_table[href]
                else:
                    matches = list()
                    hrefs_table[href] = matches
                url = "https://www.digikey.com/products/en/" + href
                #if base.startswith("capacitors"):
                #    print("url='{0}'".format(url))
                match = (href, base, id, a_contents_text, li_contents_text, url)
                matches.append(match)
        # We are done scraping information out of the the *soup*.  Everything we need is
        # now in *hrefs_table*.

        # Wrap up any requested *tracing* and return *hrefs_table*:
        if tracing is not None:
            print(f"{tracing}<=Digikey.soup_extract(*, *)=>dict")
        return hrefs_table

    # Digikey.soup_read():
    def soup_read(self, tracing=None):
        # Read in the *digikey_product_html_file_name* file into *html_text*.  This
        # file is obtained by going to `https://www.digkey.com/` and clickd on the
        # `[View All]` link next to `Products`.  This page is saved from the web browser
        # in the file named *digikey_product_html_file_name*:

        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None
        
        # Perform any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}=>Digikey.soup_read(*)")

        # Grab some values from *digikey* (i.e. *self*):
        digikey = self
        products_html_file_name = digikey.products_html_file_name

        # Read *products_html_file_name* in and convert it into *soup*:
        soup = None
        with open(products_html_file_name) as html_file:
            html_text = html_file.read()

            # Parse *html_text* into a *soup*:
            soup = bs4.BeautifulSoup(html_text, features="lxml")

            # To aid in reading the HTML, write the *soup* back out to the `/tmp` directory
            # in a prettified form:
            prettified_html_file_name = "/tmp/prettified.html"
            with open(prettified_html_file_name, "w") as html_file:
                html_file.write(soup.prettify())
        assert soup is not None

        # Wrap up any requested *tracing* and return *soup*:
        if tracing is not None:
            print(f"{tracing}<=Digikey.soup_read(*)")
        return soup

# DigikeyDirectory:
class DigikeyDirectory(bom.Directory):

    # DigikeyDirectory.__init__():
    def __init__(self, name, parent, id, url, tracing=None):
        # Verify argument types:
        assert isinstance(name, str)
        assert (isinstance(parent, bom.Collection) or
                isinstance(parent, bom.Directory)), f"type(parent)={type(parent)}"
        assert isinstance(id, int)
        assert isinstance(url, str)
        assert isinstance(tracing, str) or tracing is None

        # Preform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>DigikeyDirectory.__init__('{name}', '{parent.name}', {id})")

        # Initialize the parent class for *digikey_directory* (i.e. *self*):
        digikey_directory = self
        super().__init__(name, parent, tracing=next_tracing)

        # Stuff values into *digikey_table* (i.e. *self*):
        digikey_directory.id = id
        digikey_directory.url = url

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=DigikeyDirectory.__init__('{name}', '{parent.name}', {id})")

    # DigikeyDirectory.csvs_download():
    def csvs_download(self, csvs_directory, downloads_count, tracing=None):
        # Verify argument types:
        assert isinstance(csvs_directory, str)
        assert isinstance(downloads_count, int)
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing* for *digikey_directory* (i.e. *self*):
        digikey_directory = self
        name = digikey_directory.name
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>DigikeyDirectory.csvs_download('{name}', '{csvs_directory}', "
                  f"{downloads_count})")

        digikey_directory = self
        children = digikey_directory.children_get()
        for sub_node in children:
            downloads_count = sub_node.csvs_download(csvs_directory, downloads_count,
                                                     tracing=next_tracing)

        # Wrap up any requested *tracing*":
        if tracing is not None:
            print(f"{tracing}<=DigkikeyDirectory.csvs_download('{name}', "
                  f"'{csvs_directory}', *)=>{downloads_count}")
        return downloads_count

    # DigikeyDirectory.csv_read_and_process():
    def csv_read_and_process(self, csvs_directory, bind=False, tracing=None):
        # Verify argument types:
        assert isinstance(csvs_directory, str)
        assert isinstance(tracing, str) or tracing is None

        # Perform an requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{0}=>DigikeyDirectory.csv_read_and_process(*, '{1}')".
                  format(tracing, csvs_directory))

        # Process each *sub_node* of *digikey_directory* (i.e. *self*):
        digikey_directory = self
        for sub_node in digikey_directory.children_get():
            assert isinstance(sub_node, bom.Node)
            sub_node.csv_read_and_process(csvs_directory, bind=bind, tracing=next_tracing)

        # Wrap up any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{0}<=DigikeyDirectory.csv_read_and_process(*, '{1}')".
                  format(tracing, csvs_directory))

    # DigikeyDirectory.reorganize():
    def reorganize(self, tracing=None):
        # This lovely piece of code takes a *DigikeyDirectory* (i.e. *self*) and attempts
        # to further partition it into some smaller directories.

        # A *title* can be of form:
        #
        #        "Level 1 Only"
        #        "Level 1 - Level 2"
        #        "Level 1 - Level 2 -Level 3"
        #        ...
        # This routine finds all *title*'s that have the initial " - " and rearranges the
        # *digikey_directory* so that all the tables that have the same "Level 1" prefix
        # in their *title* are grouped together.

        # Step 1: The first step is to build *groups_table* than is a table that contains a list
        # of "Level 1" keys with a list of *DigikeyTable*'s as the value.  Thus,
        #
        #        "Level 1a"
        #        "Level 1b - Level2a"
        #        "Level 1c - Level2b"
        #        "Level 1c - Level2c"
        #        "Level 1d"
        #        "Level 1e - Level2d"
        #        "Level 1e - Level2e"
        #        "Level 1e - Level2f"
        #        "Level 1e
        #
        # Will basically generate the following table:
        #
        #        {"Level 1b": ["Level2a"]
        #         "Level 1c": ["Level2b", "Level2c"],
        #         "Level 1e": ["Level2d", "Level2e", "Level2f"}
        #
        # Where the lists actually contain the appropriate *DigikeyTable* objects rather
        # than simple strings.  Notice that we throw the "Level 1b" entry out since it
        # only has one match.  This operation takes place in Step3.

        # Perform any requeted *tracing*:
        digikey_directory = self
        name = digikey_directory.name
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>DigikeyDirectory.reorganize('{name}')")

        # Start with *digikey_directory* (i.e. *self*) and construct *groups_table*
        # by scanning through *children*:
        groups_table = dict()
        children = sorted(digikey_directory.children_get(), key=lambda table: table.name)
        for table_index, table in enumerate(children):
            # Grab some values from *table*:
            assert isinstance(table, DigikeyTable)
            name = table.name
            id = table.id
            base = table.base
            url = table.url

            # Search for the first " - " in *name*.:
            hypen_index = name.find(" - ")
            if hypen_index >= 0:
                # We found "Level1 - ...", so split it into *group_name* (i.e. "Level1")
                # and *sub_group_name* (i.e. "...")
                group_name = name[:hypen_index].strip()
                sub_group_name = name[hypen_index+3:].strip()
                if tracing is not None:
                    print(f"{tracing}[{table_index}]:'{name}'=>'{group_name}'/'{sub_group_name}")

                # Load *group_title* into *groups_table* and make sure we have a *tables_list*
                # in there:
                if group_name in groups_table:
                    tables_list = groups_table[group_name]
                else:
                    tables_list = list()
                    groups_table[group_name] = tables_list

                # Finally, tack *table* onto *tables_list*:
                tables_list.append(table)

        # This deals with a fairly obscure case where it is possible to have both a table and
        # directory with the same name.  This is called the table/directory match problem.
        # An example would help:
        #
        #        Fiber Optic Connectors
        #        Fiber Optic Connectors - Accessories
        #        Fiber Optic Connectors - Contacts
        #        Fiber Optic Connectors - Housings
        #
        # Conceptually, we want to change the first line to "Fiber Optic_Connectors - Others".
        # The code does this by finding the table, and just adding it to the appropriate
        # group list in *groups_table*.  Later below, we detect that there is no hypen in the
        # title and magically add " - Others" to the title.  Yes, this is obscure:
        for table in digikey_directory.children_get():
            assert isinstance(table, DigikeyTable)
            table_name = table.name
            if table_name in groups_table:
                tables_list = groups_table[table_name]
                tables_list.append(table)
                # print("Print '{0}' is a table/directory matach".format(table_title))

        # Ignore any *group_title* that only has one match (i.e *len(tables_list)* <= 1):
        group_titles_to_delete = list()
        for group_title, tables_list in groups_table.items():
            if len(tables_list) <= 1:
                # print("groups_table['{0}'] only has one match; delete it".format(group_title))
                group_titles_to_delete.append(group_title)
        for group_title in group_titles_to_delete:
            del groups_table[group_title]

        # Now sweep through *digikey_directory* deleting the *tables* that are going to
        # be reinserted in the *sub_directories*:
        for group_title, tables_list in groups_table.items():
            for table_index, table in enumerate(tables_list):
                digikey_directory.remove(table, tracing=next_tracing)

        # Now create a *sub_directory* for each *group_title* in *groups_table*:
        for index, group_name in enumerate(sorted(groups_table.keys())):
            tables_list = groups_table[group_name]
            # Convert *group_title* to *directory_name*:
            #directory_name = digikey_directory.title2file_name(group_title)
            # print("  Group_Title[{0}]'{1}':".format(group_title_index, group_title))

            # Create the *sub_directory*:
            #sub_directory_path = digikey_directory.path + "/" + directory_name
            sub_directory = DigikeyDirectory(group_name, digikey_directory, id, url,
                                             tracing=next_tracing)
            # Note: *DigikeyDirectory()* automatically appends to the
            # *digikey_directory* parent:

            # Now create a new *sub_table* for each *table* in *tables_list*:
            tables_list.sort(key=lambda table: table.name)
            for table_index, table in enumerate(tables_list):
                assert isinstance(table, DigikeyTable)

                # Extract the *sub_group_title* again:
                name = table.name
                hyphen_index = name.find(" - ")

                # When *hyphen_index* is < 0, we are dealing with table/directory match problem
                # (see above); otherwise, just grab the stuff to the right of the hyphen:
                if hyphen_index >= 0:
                    sub_group_title = name[hyphen_index+3:].strip()
                else:
                    sub_group_title = "Others"
                    # print("  Creating 'Others' title for group '{0}'".format(title))

                # Create the new *sub_table*:
                #path = sub_directory_path
                #url = table.url
                href = ""
                DigikeyTable(name, sub_directory, base, id, href, url, tracing=next_tracing)
                # Note: *DigikeyTable()* automatically appends *sub_table* to the parent
                # *sub_directory*:

            # Sort *sub_directory* just for fun.  It probably does not do much of anything:
            #sub_directory.sort(lambda title: title.name, tracing=next_tracing)

        # Again, sort *digikey_directory* even though it is unlikely to change anything:
        # digikey_directory.sort(lambda table: table.name)
        # digikey_directory.show("  ")

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=DigikeyDirectory.reorganize('{name}')")

    # DigikeyDirectory.show():
    def show(self, indent):
        # Verify argument types:
        assert isinstance(indent, str)

        digikey_directory = self
        assert isinstance(digikey_directory, bom.Node)
        children = digikey_directory.children
        assert isinstance(children, list)
        for node_index, node in enumerate(children):
            assert isinstance(node, bom.Node)
            if isinstance(node, DigikeyDirectory):
                print(f"{0}[{1:02d}] D:'{3}' '{2}'".
                      format(indent, node_index, node.title, node.path))
                node.show(indent + "    ")
            elif isinstance(node, DigikeyTable):
                print("{0}[{1:02d}] T:'{3}' '{2}'".
                      format(indent, node_index, node.title, node.path))
            else:
                assert False

    # DigikeyDirectory.table_get():
    def table_get(self):
        digikey_directory = self
        return digikey_directory.file_name2title()


# DigikeyTable:
class DigikeyTable(bom.Table):

    # DigikeyTable.__init__():
    def __init__(self, name, parent, base, id, href, url, tracing=None):
        # Verify argument types:
        assert isinstance(name, str)
        assert isinstance(parent, DigikeyDirectory)
        assert isinstance(base, str)
        assert isinstance(id, int)
        assert isinstance(href, str)
        assert isinstance(url, str)
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>DigikeyTable.__init__('{name}', '{parent.name}', "
                  f"'{base}', {id}, '{url}')")


        # Initialize the parent *bom.Table* class for *digikey_table* (i.e. *self*):
        digikey_table = self
        super().__init__(name, parent, url)

        # Stuff values into *digikey_table*:
        digikey_table.base = base
        digikey_table.id = id
        digikey_table.href = href
        digikey_table.url = url

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=DigikeyTable.__init__('{name}', '{parent.name}', "
                  f"'{base}', {id}, '{url}')")

    # DigikeyTable.csvs_download():
    def csvs_download(self, csvs_directory, downloads_count, tracing=None):
        # Verify argument types:
        assert isinstance(csvs_directory, str)
        assert isinstance(downloads_count, int)
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing* for *digikey_table* (i.e. *self*):
        digikey_table = self
        name = digikey_table.name
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>DigikeyTable.csvs_download('{name}', '{csvs_directory}',"
                  f" {downloads_count})")

        base = digikey_table.base
        id = digikey_table.id
        csv_file_name = csvs_directory + "/" + base + ".csv"
        if not os.path.isfile(csv_file_name):
            # The first download happens immediately and the subsequent ones are delayed by
            # 60 seconds:
            if downloads_count >= 1:
                print("Waiting 60 seconds....")
                time.sleep(60)

            # Compute the *url*, *parameters*, and *headers* needed for the *request*:
            url = "https://www.digikey.com/product-search/download.csv"
            parameters = {
                "FV": "ffe{0:05x}".format(id),
                "quantity": 0,
                "ColumnSort": 0,
                "page": 1,
                "pageSize": 500
            }
            headers = {
                "authority": "www.digikey.com",
                "accept-encoding": "gzip, deflate, br",
                "cookie": ("i10c.bdddb="
                  "c2-94990ugmJW7kVZcVNxn4faE4FqDhn8MKnfIFvs7GjpBeKHE8KVv5aK34FQDgF"
                  "PFsXXF9jma8opCeDMnVIOKCaK34GOHjEJSFoCA9oxF4ir7hqL8asJs4nXy9FlJEI"
                  "8MujcFW5Bx9imDEGHDADOsEK9ptrlIgAEuIjcp4olPJUjxXDMDVJwtzfuy9FDXE5"
                  "sHKoXGhrj3FpmCGDMDuQJs4aLb7AqsbFDhdjcF4pJ4EdrmbIMZLbAQfaK34GOHbF"
                  "nHKo1rzjl24jP7lrHDaiYHK2ly9FlJEADMKpXFmomx9imCGDMDqccn4fF4hAqIgF"
                  "JHKRcFFjl24iR7gIfTvaJs4aLb4FqHfADzJnXF9jqd4iR7gIfz8t0TzfKyAnpDgp"
                  "8MKEmA9og3hdrCbLvCdJSn4FJ6EFlIGEHKOjcp8sm14iRBkMT8asNwBmF3jEvJfA"
                  "DwJtgD4oL1Eps7gsLJaKJvfaK34FQDgFfcFocAAMr27pmCGDMD17GivaK34GOGbF"
                  "nHKomypOTx9imDEGHDADOsTpF39ArqeADwFoceWjl24jP7gIHDbDPRzfwy9JlIlA"
                  "DTFocAEP")
                }

            # Perform the download:
            print("DigikeyTable.csvs_download: '{0}':{1}".format(csv_file_name, id))
            response = requests.get(url, params=parameters, headers=headers)
            #print(f"response.headers={response.headers}")
            #print(f"rsponse.content='{response.content}")

            # Write the content out to *csv_file_name*:
            with open(csv_file_name, "wb") as csv_file:
                csv_file.write(response.content)
            downloads_count += 1

        # Wrap up any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=DigikeyTable.csvs_download('{name}', '{csvs_directory}', *)"
                  f"=>{downloads_count}")
        return downloads_count

    # DigikeyTable.csv_full_name_get():
    def csv_full_name_get(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform an requested *tracing* for *digikey_table* (i.e. *self*):
        digikey_table = self
        name = digikey_table.name
        if tracing is not None:
            print(f"{tracing}=>DigikeyTable.csv_full_name_get('{name}')")

        # Compute the *csv_full_name*:
        base = digikey_table.base
        collection = digikey_table.collection
        collection_root = collection.collection_root
        csvs_root = os.path.join(collection_root, os.path.join("..", "CSVS"))
        csv_full_name = os.path.join(csvs_root, base + ".csv")

        # Wrap up any requested *tracing* and return *csv_full_name*:
        if tracing is not None:
            print(f"{tracing}<=DigikeyTable.csv_full_name_get('{name}')=>'{csv_full_name}'")
        return csv_full_name

    # DigikeyTable.file_save():
    def file_save(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing* for *digikey_table* (i.e. *self*):
        digikey_table = self
        name = digikey_table.name
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print(f"{tracing}=>DigikeyTable.save('{name}')")

        # Convert *digikey_table* (i.e. *self*) into a single *xml_text* string:
        xml_lines = list()
        digikey_table.xml_lines_append(xml_lines, "")
        xml_lines.append("")
        xml_text = '\n'.join(xml_lines)

        # Compute the *xml_file_name*:
        collection = digikey_table.collection
        collection_root = collection.collection_root
        relative_path = digikey_table.relative_path
        xml_file_name = os.path.join(collection_root, relative_path + ".xml")
        if tracing is not None:
            print(f"{tracing}collection_root='{collection_root}'")
            print(f"{tracing}relative_path='{relative_path}'")
            print(f"{tracing}xml_file_name='{xml_file_name}'")
        
        # Write out *xml_text* to *xml_file_name*:
        digikey_table.directory_create(collection_root)
        with open(xml_file_name, "w") as xml_file:
            xml_file.write(xml_text)

        # Wrap any requested *tracing*:
        if tracing is not None:
            print(f"{tracing}<=DigikeyTable.save('{name}')")

    # DigikeyTable.title_get():
    def title_get(self):
        digikey_table = self
        return digikey_table.file_name2title()

    
    # DigikeyTable.xml_lines_append():
    def xxx_xml_lines_append(self, xml_lines, indent):
        # Verify argument types:
        assert isinstance(xml_lines, list)
        assert isinstance(indent, str)

        # Grab some values from *digikey_table* (i.e. *self*):
        digikey_table = self
        name = digikey_table.name
        parameters = digikey_table.parameters
        url = digikey_table.url

        # Start with the `<DigikeyTable ... >` tag:
        xml_lines.append(f'{indent}<DigikeyTable '
                         f'name="{bom.Encode.to_attribute(name)}"'
                         f'url="{bom.Encode.to_attribute(url)}"'
                         f'>')

        # Append the *parameters*:
        xml_lines.append(f'{indent} <Parameters>')
        next_indent = indent + "  "
        for parameter in parameters:
            parameter.xml_lines_append(xml_lines, next_indent)
        xml_lines.append(f'{indent} </Parameters>')

        # Close out `</DigikeyTable>` tag:
        xml_lines.append(f'{indent}</DigikeyTable>')

# main():
def main():
    digikey = Digikey()
    digikey.process(tracing="")
    return 0

#    <form name="downloadform" class="method-chooser" method="post"
#     action="/product-search/download.csv">
#     <input type="hidden" name="FV" value="ffe0003c" />
#     <input type="hidden" name="quantity" value="0" />
#     <input type="hidden" name="ColumnSort" value="0" />
#     <input type="hidden" name="page" value="1" />
#     <input type="hidden" name="pageSize" value="25" />
#    </form>

#     https://www.digikey.com/product-search/download.csv?FV=ffe0003c&quantity=0&ColumnSort=0&page=1&pageSize=500


if __name__ == "__main__":
    main()
