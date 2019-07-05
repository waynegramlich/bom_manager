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
import bs4
import os
import glob
import subprocess
import time
import bom_manager as bm


class Digikey:
    # Digikey.__init__():
    def __init__(self):
        digikey = self
        digikey.products_html_file_name = "www.digikey.com_products_en.html"
        digikey.tables_directory = "/home/wayne/public_html/projects/digikey_tables"
        digikey.csvs_directory = "/home/wayne/public_html/projects/digikey_csvs"

    # Digikey.process():
    def process(self):
        # This starts with the top level page from Digi-Key.com:
        #
        #   https://www.digikey.com/products/en
        #
        # Which is manually copied out of the web browser and stored into the file named
        # *digikey_products_html_file_name*:

        digikey = self
        digikey.tables_directory_clear()
        soup = digikey.soup_read()
        hrefs_table = digikey.soup_extract(soup)
        # print("len(hrefs_table)={0}".format(len(hrefs_table)))
        assert isinstance(hrefs_table, dict)
        root_directory = digikey.root_directory_extract(hrefs_table)

        root_directory.csvs_download(digikey.csvs_directory)

        digikey.root_directory_reorganize(root_directory)
        # root_directory.show("")
        digikey.directories_create(root_directory)
        root_directory.csv_read_and_process(digikey.csvs_directory, bind=True)

    # Digikey.directories_create():
    def directories_create(self, directory):
        assert isinstance(directory, DigikeyDirectory)

        digikey = self
        path = directory.path
        if not os.path.isdir(path):
            os.mkdir(path)

        for node in directory.children:
            if isinstance(node, DigikeyDirectory):
                sub_directory = node
                digikey.directories_create(sub_directory)

    # Digikey.root_directory_extract():
    def root_directory_extract(self, hrefs_table):
        # Verify argument types:
        assert isinstance(hrefs_table, dict)

        # Now we construct *root_directory* which is a *DigikeyDirectory* that contains
        # a list of *DigkeyDirectory*'s.  Each of those nested *DigikeyDirectory*'s contains
        # a further list of *DigikeyTable*'s.
        #
        # The sorted keys from *hrefs_table* lare alphabetized by *base* an look basically
        # as follows:
        #
        #        None                                             # Null => Root directory
        #        audio-products                                   # *items* < 0 => directory
        #        audio-products-alarms-buzzers-and-sirens
        #        audio-products-buzzer-elements-piezo-benders
        #        audio-products-microphones
        #        audio-products-speakers
        #        battery-products                                 # *items* < 0 => directory
        #        battery-products-accessories
        #        battery-products-batteries-non-rechargeable-primary
        #        battery-products-batteries-rechargeable-secondary
        #
        # We need to group all the entries that match "audio-products" together,
        # all the entries that matach *battery-products* together, etc.

        # Create the *root_directory*:
        digikey = self
        tables_directory = digikey.tables_directory
        root_directory = DigikeyDirectory("", tables_directory, "Root", -1, parent=None)

        # Sweep through sorted *hrefs* and process each *matches* lists:
        current_directory = None
        for href_index, href in enumerate(sorted(hrefs_table.keys())):
            matches = hrefs_table[href]
            # print("HRef[{0}]: '{1}' {2}".format(href_index, href, matches))

            # There are one or more *matches*.  We'll take the first *a_content* that is non-null
            # and treat that as the *title*.  The number of *items* is taken from the first
            # *li_content* that end with " items)".  We visit *matches* in reverse order to work
            # around an obscure issue that is not worth describing.  If you feeling figuring it
            # out, please remove the called to `reversed()`:
            title = None
            items = -1
            url = None
            for match_index, match in enumerate(reversed(sorted(matches))):
                # Unpack *match*:
                base, id, a_content, li_content, url = match
                # print("  Match[{0}] '{1}' '{2}' {3}, '{4}'".
                #  format(match_index, href, a_content, li_content, url))

                # Fill in *title* and *items*:
                if title is None and not a_content.startswith("See"):
                    title = a_content
                    items_pattern = " items)"
                    if items < 0 and li_content.endswith(" items)"):
                        open_parenthesis_index = li_content.find('(')
                        items = int(li_content[open_parenthesis_index+1:-len(items_pattern)])
                    break

            # Dispatch based on *title* and *items*:
            if title is None:
                # We already created *root_directory* so there is nothing to do here:
                pass
            elif items < 0:
                # We have a new *DigikeyDirectory* to create and make the *current_directory*.
                # Note: the initailizer automatically appends *current_directory* to
                # *root_directory*.
                directory_file_name = root_directory.title2file_name(title)
                path = tables_directory + "/" + directory_file_name
                current_directory = DigikeyDirectory(base, path, title, id, parent=root_directory)
            else:
                # We have a *DigikeyTable* to create and append to *current_directory*:
                # Note: the initializer automatically appends *table* to *current_directory*:
                assert current_directory is not None
                # file_name = current_directory.title2file_name(title)
                path = current_directory.path
                # print("base='{0}' title='{1} file_name='{2}' path='{3}'".
                #  format(base, title, file_name, path))
                DigikeyTable(base, path, title, id, items, url, parent=current_directory)
                # print("len(current_directory)={0}".format(len(current_directory.children)))

        # *root_directory* is in its first incarnation and ready for reorganization:
        return root_directory

    def root_directory_reorganize(self, root_directory):
        # Verify argument types:
        assert isinstance(root_directory, DigikeyDirectory)

        # Reorganize each *DigikeyDirectory* in *root_directory*:
        directories = root_directory.children
        # print("len(directories)={0}".format(len(directories)))
        for directory_index, directory in enumerate(
          sorted(directories, key=lambda directory: directory.title)):
            assert isinstance(directory, DigikeyDirectory)
            # print("Root_Directory[{0}]: '{1}'".format(directory_index, directory.title))
            directory.reorganize()

    # Digikey.soup_extract():
    def soup_extract(self, soup):
        # Verify argument types:
        assert isinstance(soup, bs4.BeautifulSoup)

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
        # each *match* is a 4-tuple containing (*base*, *id*, *a_content_text*, *li_content_text*).
        # *id* is -1 if there was no "/*id*" present in the *href*.

        # Start with an empty *hrefs_table*:
        hrefs_table = dict()
        url_prefix = "/products/en/"
        url_prefix_size = len(url_prefix)

        # Find all of the <A HRef="..."> tags in *soup*:
        for a in soup.find_all("a"):
            assert isinstance(a, bs4.element.Tag)

            # We are only interested in *href*'s that start with *url_prefix*:
            href = a.get("href")
            if href is not None and href.startswith(url_prefix):
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
                if href in hrefs_table:
                    matches = hrefs_table[href]
                else:
                    matches = list()
                    hrefs_table[href] = matches
                url = "https://www.digikey.com/products/en/" + href
                if base.startswith("capacitors"):
                    print("url='{0}'".format(url))
                match = (base, id, a_contents_text, li_contents_text, url)
                matches.append(match)

        # We are done scraping information out of the the *soup*.  Everything we need is
        # now in *hrefs_table*.
        return hrefs_table

    # Digikey.soup_read():
    def soup_read(self):
        # Read in the *digikey_product_html_file_name* file into *html_text*.  This
        # file is obtained by going to `https://www.digkey.com/` and clickd on the
        # `[View All]` link next to `Products`.  This page is saved from the web browser
        # in the file named *digikey_product_html_file_name*:
        digikey = self
        products_html_file_name = digikey.products_html_file_name
        with open(products_html_file_name) as html_file:
            html_text = html_file.read()
        # print(html_text)

        # Parse *html_text* into a *soup*:
        soup = bs4.BeautifulSoup(html_text, features="lxml")

        # To aid in reading, write the *soup* back out to the `/tmp` directory in a prettified form:
        prettified_html_file_name = "/tmp/" + products_html_file_name
        with open(prettified_html_file_name, "w") as html_file:
            html_file.write(soup.prettify())

        return soup

    # Digikey.tables_directory_clear():
    def tables_directory_clear(self):
        # Scan the *tables_directory* of *digikey* (i.e. *self*) for all sub files and directories:
        digikey = self
        tables_directory = digikey.tables_directory
        file_names = glob.glob(tables_directory + "/**", recursive=True)

        # Sort *file_name* them so that the longest names come first (i.e. -negative length).
        file_names.sort(key=lambda file_name: -len(file_name))

        # Set *debug* to *True* for debug tracing:
        debug = False

        # Visit each *file_name* in *file_names* and delete them (if appropriate):
        for file_name_index, file_name in enumerate(file_names):
            # Hang onto the `README.md` and the top level directory (i.e. *file_name[:-1]*):
            delete = not (file_name.endswith("README.md") or file_name[:-1] == tables_directory)

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


class DigikeyDirectory(bm.Directory):
    # DigikeyDirectory.__init__():
    def __init__(self, base, path, title, id, parent=None):
        # Verify argument types:
        assert isinstance(base, str) or base is None
        assert isinstance(path, str)
        assert isinstance(title, str)
        assert isinstance(id, int)
        assert isinstance(parent, bm.Node) or parent is None

        # print("=>DigikeyDirectory(*, base='{0}', path='{1}', title='{2}', id={3}, parent='{4}'".
        #  format(base, path, title, id, "None" if parent is None else parent.name))

        # Initialize the parent *bm.Table* class:
        super().__init__(base, path, title, parent=parent)

        # Stuff values into *digikey_table*:
        digikey_table = self
        digikey_table.base = base
        digikey_table.id = id
        digikey_table.title = title

    # DigikeyDirectory.csvs_download():
    def csvs_download(self, csvs_directory):
        # Verify argument types:
        assert isinstance(csvs_directory, str)

        digikey_directory = self
        children = digikey_directory.children
        for sub_node in children:
            sub_node.csvs_download(csvs_directory)

    # DigikeyDirectory.csv_read_and_process():
    def csv_read_and_process(self, csv_directory, bind=False, tracing=None):
        # Verify argument types:
        assert isinstance(csv_directory, str)
        assert isinstance(tracing, str) or tracing is None

        # Perform an requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{0}=>DigikeyDirectory.csv_read_and_process(*, '{1}')".
                  format(tracing, csv_directory))

        # Process each *sub_node* of *digikey_directory* (i.e. *self*):
        digikey_directory = self
        for sub_node in digikey_directory.children:
            assert isinstance(sub_node, bm.Node)
            sub_node.csv_read_and_process(csv_directory, bind=bind, tracing=next_tracing)

        # Wrap up any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{0}<=DigikeyDirectory.csv_read_and_process(*, '{1}')".
                  format(tracing, csv_directory))

    # DigikeyDirectory.reorganize():
    def reorganize(self):
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

        # Start with *digikey_directory* (i.e. *self*) and construct *groups_table*
        # by scanning through *children*:
        digikey_directory = self
        groups_table = dict()
        children = sorted(digikey_directory.children, key=lambda table: table.title)
        for table_index, table in enumerate(children):
            assert isinstance(table, DigikeyTable)

            # Unpack *base* and *title* from *table*:
            title = table.title

            # Search for the first " - " in title.:
            hypen_index = title.find(" - ")
            if hypen_index >= 0:
                # We found "Level1 - ...", so split it into *group_title* (i.e. "Level1")
                # and *sub_group_title* (i.e. "...")
                group_title = title[:hypen_index].strip()
                sub_group_title = title[hypen_index+3:].strip()
                # print("[{0}]: '{1}' '{2}' => '{3}' '{4}".
                #  format(table_index, base, title, group_title, sub_group_title))

                # Load *group_title* into *groups_table* and make sure we have a *tables_list*
                # in there:
                if group_title in groups_table:
                    tables_list = groups_table[group_title]
                else:
                    tables_list = list()
                    groups_table[group_title] = tables_list

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
        for table in digikey_directory.children:
            assert isinstance(table, DigikeyTable)
            table_title = table.title
            if table_title in groups_table:
                tables_list = groups_table[table_title]
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
                digikey_directory.remove(table)

        # Now create a *sub_directory* for each *group_title* in *groups_table*:
        for group_title_index, group_title in enumerate(sorted(groups_table.keys())):
            tables_list = groups_table[group_title]
            # Convert *group_title* to *directory_name*:
            directory_name = digikey_directory.title2file_name(group_title)
            # print("  Group_Title[{0}]'{1}':".format(group_title_index, group_title))

            # Create the *sub_directory*:
            sub_directory_path = digikey_directory.path + "/" + directory_name
            sub_directory = DigikeyDirectory("", sub_directory_path, directory_name,
                                             -1, parent=digikey_directory)
            # Note: *DigikeyDirectory()* automatically appends to the
            # *digikey_directory* parent:

            # Now create a new *sub_table* for each *table* in *tables_list*:
            tables_list.sort(key=lambda table: table.title)
            for table_index, table in enumerate(tables_list):
                assert isinstance(table, DigikeyTable)

                # Extract the *sub_group_title* again:
                title = table.title
                hyphen_index = title.find(" - ")

                # When *hyphen_index* is < 0, we are dealing with table/directory match problem
                # (see above); otherwise, just grab the stuff to the right of the hyphen:
                if hyphen_index >= 0:
                    sub_group_title = title[hyphen_index+3:].strip()
                else:
                    sub_group_title = "Others"
                    # print("  Creating 'Others' title for group '{0}'".format(title))

                # Create the new *sub_table*:
                path = sub_directory_path
                url = table.url
                DigikeyTable(table.base, path, sub_group_title,
                             table.id, table.items, url, parent=sub_directory)
                # Note: *DigikeyTable()* automatically appends *sub_table* to the parent
                # *sub_directory*:

            # Sort *sub_directory* just for fun.  It probably does not do much of anything:
            sub_directory.sort()

        # Again, sort *digikey_directory* even though it is unlikely to change anything:
        digikey_directory.sort()
        # digikey_directory.show("  ")

    # DigikeyDirectory.show():
    def show(self, indent):
        # Verify argument types:
        assert isinstance(indent, str)

        digikey_directory = self
        assert isinstance(digikey_directory, bm.Node)
        children = digikey_directory.children
        assert isinstance(children, list)
        for node_index, node in enumerate(children):
            assert isinstance(node, bm.Node)
            if isinstance(node, DigikeyDirectory):
                print("{0}[{1:02d}] D:'{3}' '{2}'".
                      format(indent, node_index, node.title, node.path))
                node.show(indent + "    ")
            elif isinstance(node, DigikeyTable):
                print("{0}[{1:02d}] T:'{3}' '{2}'".
                      format(indent, node_index, node.title, node.path))
            else:
                assert False

    # DigikeyDirectory.sort():
    def sort(self):
        digikey_directory = self
        digikey_directory.children.sort(key=lambda table: table.title)

    # DigikeyDirectory.table_get():
    def table_get(self):
        digikey_directory = self
        return digikey_directory.file_name2title()


class DigikeyTable(bm.Table):
    # DigikeyTable.__init__():
    def __init__(self, base, path, title, id, items, url, parent=None):
        # Verify argument types:
        assert isinstance(base, str) or base is None
        assert isinstance(path, str)
        assert isinstance(title, str)
        assert isinstance(id, int)
        assert isinstance(items, int)
        assert isinstance(url, str)
        assert isinstance(parent, bm.Node) or parent is None

        # Initialize the parent *bm.Table* class:
        csv_file_name = base + ".csv"
        assert path.find(".xml") < 0, "path='{0}'".format(path)
        file_name = path + "/" + base + ".xml"
        # print("=>DigikeyTable.__init__(base='{0}', path='{1}')".format(base, path))

        comments = [bm.TableComment(language="EN", lines=[])]
        super().__init__(file_name=file_name, comments=comments, name=base,
                         csv_file_name=csv_file_name, parameters=list(),
                         path=path, parent=parent, url=url)

        # Stuff values into *digikey_table*:
        digikey_table = self
        digikey_table.base = base
        digikey_table.id = id
        digikey_table.items = items
        digikey_table.title = title
        digikey_table.url = url
        # print("<=DigikeyTable.__init__(base='{0}', path='{1}')".format(base, path))

    # DigikeyTable.csvs_download():
    def csvs_download(self, csvs_directory):
        # Verify argument types:
        assert isinstance(csvs_directory, str)

        digikey_table = self
        base = digikey_table.base
        id = digikey_table.id
        csv_file_name = csvs_directory + "/" + base + ".csv"
        if not os.path.isfile(csv_file_name):
            # Now we read in a chunk of each table and store it into *digikey_csvs_directory*.
            # We want to be semi-polite and avoid throttling by only performing one fetch per
            # minute.  This this step will take a while:
            print("DigikeyTable.csvs_download: '{0}':{1}".format(csv_file_name, id))
            curl_arguments = list()
            curl_arguments.append("curl")
            curl_arguments.append("https://www.digikey.com/product-search/download.csv?"
                                  "FV=ffe{0:05x}&quantity=0&ColumnSort=0&page=1&pageSize=500".
                                  format(id))
            curl_arguments.append("-H")
            curl_arguments.append("authority: www.digikey.com")
            curl_arguments.append("-H")
            curl_arguments.append("accept-encoding: gzip, deflate, br")
            curl_arguments.append("-H")
            curl_arguments.append("cookie: i10c.bdddb="
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
            curl_arguments.append("--compressed")
            curl_arguments.append("-s")
            curl_arguments.append("-o")
            curl_arguments.append(csv_file_name)
            # print(curl_arguments)
            subprocess.call(curl_arguments)
            time.sleep(60)

    # DigikeyTable.save():
    def save(self, tracing=None):
        # Verify argument types:
        assert isinstance(tracing, str) or tracing is None

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing is not None:
            print("{0}DigikeyTable.save(*)".format(tracing))

        # table = self
        # file_name = table.file_name
        # assert False, "file_name='{0}'".format(file_name)
        super().save(tracing=next_tracing)

        # Wrap any requested *tracing*:
        if tracing is not None:
            print("{0}DigikeyTable.save(*)".format(tracing))

    # DigikeyTable.title_get():
    def title_get(self):
        digikey_table = self
        return digikey_table.file_name2title()


def main():
    digikey = Digikey()
    digikey.process()
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
