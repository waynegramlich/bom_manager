# # BOM Manager GUI
#
# BOM Manager GUI is a Graphial User Interface for managing one or more Bill of Materials.
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

# These are all of the imports from the parent bom engine module.  All of the types
# are explicitly listed to make the flake8 linting program happier:
from bom_manager.bom import (command_line_arguments_process, Collection, Collections, Directory,
                             Enumeration, EnumerationComment, Filter, Gui, Node, Order,
                             Parameter, ParameterComment,
                             Search, SearchComment, Table, TableComment)
from bom_manager.tracing import trace  # Tracing decorator module:
import csv                      # Parser for CSV (Comma Separated Values) files
from functools import partial   # Needed for window events
import lxml.etree as etree      # type: ignore
import os                       # General Operating system features:

# All of the PySide2 stuff provides the GUI technology used by the GUI.
from PySide2.QtUiTools import QUiLoader  # type: ignore
from PySide2.QtWidgets import (QApplication, QComboBox, QLineEdit, QMainWindow)  # type: ignore
from PySide2.QtWidgets import (QPlainTextEdit, QPushButton)                      # type: ignore
from PySide2.QtWidgets import (QTableWidget, QTableWidgetItem, QWidget)          # type: ignore
from PySide2.QtCore import (QAbstractItemModel, QCoreApplication, QFile)         # type: ignore
from PySide2.QtCore import (QItemSelectionModel, QModelIndex, Qt)                # type: ignore
from PySide2.QtGui import (QClipboard,)                                          # type: ignore
import re                       # Regular expressions
import sys                      # System utilities
from typing import Dict
import webbrowser               # Some tools to send messages to a web browser


# main():
def main(tracing=""):
    collection_directories, searches_root, order = command_line_arguments_process()

    # Now create the *bom_gui* graphical user interface (GUI) and run it:
    if tracing:
        print(f"{tracing}searches_root='{searches_root}'")
    tables = list()
    bom_gui = BomGui(tables, collection_directories, searches_root, order)

    # Start up the GUI:
    bom_gui.run()


# BomGui:
class BomGui(QMainWindow, Gui):

    # BomGui.__init__()
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

        tree_model = TreeModel()

        # Load all values into *bom_gui*:
        current_table = tables[0] if len(tables) >= 1 else None
        bom_gui = self
        bom_gui.application = application
        bom_gui.clicked_model_index = QModelIndex()
        bom_gui.collection_directories = collection_directories
        bom_gui.collections = None  # Filled in below
        bom_gui.current_comment = None
        bom_gui.current_enumeration = None
        bom_gui.current_model_index = None
        bom_gui.current_parameter = None
        bom_gui.current_search = None
        bom_gui.current_table = current_table
        bom_gui.current_tables = tables
        bom_gui.in_signal = True
        bom_gui.languages = ["English", "Spanish", "Chinese"]
        bom_gui.main_window = main_window
        bom_gui.order = order
        # bom_gui.original_tables = copy.deepcopy(tables)
        bom_gui.searches_root = searches_root
        bom_gui.searches = list()
        bom_gui.xsearches = None
        bom_gui.tree_model = tree_model
        bom_gui.tab_unload = None
        bom_gui.tables = tables
        # bom_gui.tracing_level = tracing_level
        # bom_gui.trace_signals = tracing_level >= 1

        # Initialze both the *QMainWindow* and *Gui* super classes:
        super().__init__()

        # Set up *tables* first, followed by *parameters*, followed by *enumerations*:

        # Set up *tables_combo_edit* and stuff into *bom_gui*:
        new_item_function = partial(BomGui.table_new, bom_gui)
        current_item_set_function = partial(BomGui.current_table_set, bom_gui)
        comment_get_function = partial(BomGui.table_comment_get, bom_gui)
        comment_set_function = partial(BomGui.table_comment_set, bom_gui)
        is_active_function = partial(BomGui.table_is_active, bom_gui)


        # Perform some global signal connections to *main_window* (abbreviated as *mw*):
        mw = main_window
        mw.collections_check.clicked.connect(bom_gui.collections_check_clicked)
        mw.collections_process.clicked.connect(bom_gui.collections_process_clicked)
        mw.root_tabs.currentChanged.connect(bom_gui.tab_changed)

        mw.collections_new.clicked.connect(bom_gui.collections_new_clicked)
        mw.collections_new.setEnabled(False)
        mw.collections_line.textChanged.connect(bom_gui.collections_line_changed)
        mw.collections_tree.clicked.connect(bom_gui.collections_tree_clicked)
        mw.collections_delete.clicked.connect(bom_gui.collections_delete_clicked)
        mw.collections_delete.setEnabled(False)

        # file_names = glob.glob("../digikey_tables/**", recursive=True)
        # file_names.sort()
        # print("file_names=", file_names)

        # Create the *tree_model* needed for *collections* and stuff into *bom_gui*:

        # Create the *collections* and stuff into *bom_gui*:
        partial_load: bool = True
        collections = Collections("Collections", collection_directories,
                                  searches_root, partial_load, bom_gui)
        bom_gui.collections = collections

        # Now stuff *collections* into *tree_model*:
        tree_model.collections_set(collections)

        # Now that both *collections* and *tree_mode* refer to one another we can safely
        # call *partial_load*():
        # collections.partial_load()

        # Now bind *tree_model* to the *collections_tree* widget:
        collections_tree = mw.collections_tree
        collections_tree.setModel(tree_model)
        collections_tree.setSortingEnabled(True)

        # FIXME: Used *bom_gui.current_update()* instead!!!
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

        # bom_gui.table_setup()

        # Read in `searches.xml` if it exists:
        # bom_gui.searches_file_load(os.path.join(order_root, "searches.xml"),
        #                                  )

        # Update the entire user interface:
        bom_gui.update()

        bom_gui.in_signal = False

    # BomGui.__str__():
    def __str__(self):
        return "BomGui"

    # BomGui.begin_rows_insert():
    def begin_rows_insert(self, node, start_row_index, end_row_index, tracing=""):
        # Verify argument types:
        assert isinstance(node, Node)
        assert isinstance(start_row_index, int)
        assert isinstance(end_row_index, int)
        assert isinstance(tracing, str)

        # Create a *model_index* for *node* and *insert_row_index* starting from
        # *bom_gui* (i.e. *self):
        bom_gui = self
        tree_model = bom_gui.tree_model
        model_index = tree_model.createIndex(0, 0, node)

        # Inform the *tree_model* that rows will be inserted from *start_row_index* through
        # *end_row_index*:
        tree_model.beginInsertRows(model_index, start_row_index, end_row_index)

    # BomGui.begin_rows_remove():
    def begin_rows_remove(self, node, start_row_index, end_row_index, tracing=""):
        # Verify argument types:
        assert isinstance(node, Node)
        assert isinstance(start_row_index, int)
        assert isinstance(end_row_index, int)
        assert isinstance(tracing, str)

        # Create a *model_index* for *node* and *insert_row_index* starting from
        # *bom_gui* (i.e. *self):
        bom_gui = self
        tree_model = bom_gui.tree_model
        model_index = tree_model.createIndex(0, 0, node)

        # Inform the *tree_model* that rows will be inserted from *start_row_index* through
        # *end_row_index*:
        tree_model.beginRemoveRows(model_index, start_row_index, end_row_index)

    # BomGui.comment_text_set()
    def comment_text_set(self, new_text, tracing=""):
        # Verify argument types:
        assert isinstance(new_text, str)
        assert isinstance(tracing, str)

        # Carefully set thet text:
        bom_gui = self
        main_window = bom_gui.main_window
        comment_text = main_window.parameters_comment_text
        comment_text.setPlainText(new_text)

    # BomGui.collections_delete_changed():
    @trace(1)
    def collections_delete_clicked(self, tracing=""):
        assert isinstance(tracing, str)
        # Perform any requested signal *tracing* for *bom_gui* (i.e. *self*):
        bom_gui = self

        # Grab the *current_model_index* from *bom_gui* and process it if it exists:
        current_model_index = bom_gui.current_model_index
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
                        bom_gui.current_model_index = None
                        bom_gui.current_search = None
                    else:
                        if tracing:
                            print(f"{tracing}Here 3")
                        search_parent_name = search_parent.name
                        if tracing:
                            print(f"{tracing}Parent is '{search_parent_name}'")
                        main_window = bom_gui.main_window
                        collections_tree = main_window.collections_tree
                        selection_model = collections_tree.selectionModel()
                        collections_line = main_window.collections_line
                        collections_line.setText(search_parent_name)
                        flags = (QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)
                        selection_model.setCurrentIndex(parent_search_model_index, flags)
                        bom_gui.current_model_index = parent_search_model_index
                        bom_gui.current_search = search_parent

                    # Remove the associated files `.xml` and `.csv` files (if they exist):
                    if tracing:
                        print(f"{tracing}Here 4")
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
        bom_gui.update()

    # BomGui.collections_line_changed():
    @trace(1)
    def collections_line_changed(self, text, tracing=""):
        # Verify argument types:
        assert isinstance(text, str)
        assert isinstance(tracing, str)

        # Make sure that *bom_gui* (i.e. *self*) is updated:
        bom_gui = self
        bom_gui.update()

    # BomGui.collections_new_clicked():
    @trace(1)
    def collections_new_clicked(self, tracing=""):
        # Perform any requested *tracing*:
        bom_gui = self
        # Grab some values from *bom_gui* (i.e. *self*):
        current_search = bom_gui.current_search

        # Make sure *current_search* exists (this button click should be disabled if not available):
        assert current_search is not None

        # clip_board = pyperclip.paste()
        # selection = os.popen("xsel").read()
        application = bom_gui.application
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
            # Grab some stuff from *bom_gui*:
            main_window = bom_gui.main_window
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

            model_index = bom_gui.current_model_index
            if model_index is not None:
                parent_model_index = model_index.parent()
                tree_model = model_index.model()
                tree_model.children_update(parent_model_index)

            # model = bom_gui.model
            # model.insertNodes(0, [ new_search ], parent_model_index)
            # if tracing:
            #    print("{0}2:len(searches)={1}".format(tracing, len(searches)))

            bom_gui.update()

    # BomGui.collections_check_clicked():
    @trace(1)
    def collections_check_clicked(self, tracing=""):
        # Perform any tracing requested by *bom_gui* (i.e. *self*):
        bom_gui = self

        # Delegate checking to *order* object:
        collections = bom_gui.collections
        order = bom_gui.order
        order.check(collections)

    # BomGui.collections_process_clicked():
    @trace(1)
    def collections_process_clicked(self, tracing=""):
        # Perform any tracing requested by *bom_gui* (i.e. *self*):
        bom_gui = self

        # Grab some values from *bom_gui*:
        collections = bom_gui.collections
        order = bom_gui.order

        # Now process *order* using *collections*:
        order.process(collections)

    # BomGui.collections_tree_clicked():
    @trace(1)
    def collections_tree_clicked(self, model_index, tracing=""):
        # Verify argument types:
        assert isinstance(model_index, QModelIndex)
        assert isinstance(tracing, str)

        # Stuff *model_index* into *bom_gui* (i.e. *self*):
        bom_gui = self
        bom_gui.current_model_index = model_index

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
        bom_gui.clicked_model_index = model_index
        node.clicked(bom_gui)

        # *Search* *node*'s get some additional treatment:
        if isinstance(node, Search):
            main_window = bom_gui.main_window
            collections_line = main_window.collections_line
            collections_line.setText(node.name)

        # Lastly, tell *bom_gui* to update the GUI:
        bom_gui.update()

    # BomGui.collections_update():
    @trace(1)
    def collections_update(self, tracing=""):
        # Perform argument testing:
        assert isinstance(tracing, str)

        # Grab some widgets from *bom_gui*:
        bom_gui = self
        main_window = bom_gui.main_window
        collections_delete = main_window.collections_delete
        collections_line = main_window.collections_line
        collections_new = main_window.collections_new

        # Grab the *current_search* object:
        current_search = bom_gui.current_search
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

    # BomGui.current_enumeration_set()
    def current_enumeration_set(self, enumeration, tracing=""):
        # Verify argument types:
        assert isinstance(enumeration, Enumeration) or enumeration is None, \
          "{0}".format(enumeration)
        assert isinstance(tracing, str)

        # Only do something if we are not in a signal:
        bom_gui = self
        if not bom_gui.in_signal:
            bom_gui.in_signal = True

            # Perform any tracing requested signal tracing:
            trace_signals = bom_gui.trace_signals
            if trace_signals:
                print("=>BomGui.current_enumeration_set('{0}')".
                      format("None" if enumeration is None else enumeration.name))

            # Finally, set the *current_enumeration*:
            bom_gui.current_enumeration = enumeration

            # Wrap up any requested tracing:
            if trace_signals:
                print("<=BomGui.current_enumeration_set('{0}')\n".
                      format("None" if enumeration is None else enumeration.name))
            bom_gui.in_signal = False

    # BomGui.current_parameter_set()
    def current_parameter_set(self, parameter, tracing=""):
        # Verify argument types:
        assert isinstance(parameter, Parameter) or parameter is None
        assert isinstance(tracing, str)

        # Perform any requested *tracing*:
        if tracing:
            name = "None" if parameter is None else parameter.name
            print("{0}=>BomGui.current_parameter_set(*, '{1}')".format(tracing, name))

        # Set the *current_parameter* in *bom_gui*:
        bom_gui = self
        bom_gui.current_parameter = parameter

    # BomGui.current_search_set()
    def current_search_set(self, new_current_search, tracing=""):
        # Verify argument types:
        assert isinstance(new_current_search, Search) or new_current_search is None, \
          print(new_current_search)
        assert isinstance(tracing, str)

        # Make sure *new_current_search* is in *searches*:
        bom_gui = self
        searches = bom_gui.searches
        if new_current_search is not None:
            for search_index, search in enumerate(searches):
                assert isinstance(search, Search)
                if tracing:
                    print("{0}Search[{1}]: '{2}'".format(tracing, search_index, search.name))
                if search is new_current_search:
                    break
            else:
                assert False
        bom_gui.current_search = new_current_search

    # BomGui.current_table_set()
    def current_table_set(self, new_current_table, tracing=""):
        # Verify argument types:
        assert isinstance(new_current_table, Table) or new_current_table is None
        assert isinstance(tracing, str)

        # Stuff *new_current_table* into *bom_gui*:
        bom_gui = self
        if new_current_table is not None:
            tables = bom_gui.tables
            for table in tables:
                if table is new_current_table:
                    break
            else:
                assert False, "table '{0}' not in tables list".format(new_current_table.name)
        bom_gui.current_table = new_current_table

    # BomGui.current_update()
    def current_update(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Make sure *current_table* is valid (or *None*):
        bom_gui = self
        tables = bom_gui.tables
        tables_size = len(tables)
        current_table = None
        if tables_size >= 1:
            # Figure out if *current_table* is in *tables):
            current_table = bom_gui.current_table
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
        bom_gui.current_table = current_table
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
                current_parameter = bom_gui.current_parameter
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
        bom_gui.current_parameter = current_parameter
        if tracing:
            print("{0}current_parameter='{1}'".
                  format(tracing, "None" if current_parameter is None else current_parameter.name))

        # Make sure *current_enumeration* is valid (or *None*):
        current_enumeration = None
        if current_parameter is None:
            enumerations = list()
        else:
            enumerations = current_parameter.enumerations
            enumerations_size = len(enumerations)
            if enumerations_size >= 1:
                current_enumeration = bom_gui.current_enumeration
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
        bom_gui.current_enumeration = current_enumeration

        # Make sure that *current_search* is valid (or *None*):
        # bom_gui.current_search = current_search

        if tracing:
            print("{0}current_enumeration'{1}'".format(
              tracing, "None" if current_enumeration is None else current_enumeration.name))

        # Make sure that *current_search* is valid (or *None*):
        searches = bom_gui.searches
        current_search = bom_gui.current_search
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
        bom_gui.current_search = current_search
        if tracing:
            print("{0}current_search='{1}'".
                  format(tracing, "None" if current_search is None else current_search.name))

    # BomGui.data_update()
    def data_update(self, tracing=""):
        # Verify artument types:
        assert isinstance(tracing, str)

        # Perform any tracing requested by *bom_gui* (i.e. *self*):
        bom_gui = self

        # Make sure that the *current_table*, *current_parameter*, and *current_enumeration*
        # in *bom_gui* are valid:
        bom_gui.current_update()

    # BomGui.directory_clicked():
    def directory_clicked(self, directory):
        # Verify argument types:
        assert isinstance(directory, Directory)

        bom_gui = self
        bom_gui.current_search = None

    # BomGui.end_rows_insert():
    def end_rows_insert(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Inform the *tree_model* associated with *bom_gui* (i.e. *self*) that we are
        # done inserting rows:
        bom_gui = self
        tree_model = bom_gui.tree_model
        tree_model.endInsertRows()

    # BomGui.end_rows_remove():
    def end_rows_remove(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Inform the *tree_model* associated with *bom_gui* (i.e. *self*) that we are
        # done inserting rows:
        bom_gui = self
        tree_model = bom_gui.tree_model
        tree_model.endRemoveRows()

    # BomGui.filters_cell_clicked():
    def filters_cell_clicked(self, row, column):
        # Verify argument types:
        assert isinstance(row, int)
        assert isinstance(column, int)

        # Perform any requested signal tracing:
        bom_gui = self

        # Just update the filters tab:
        bom_gui.filters_update()

    # BomGui.find_update():
    def find_update(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        bom_gui = self
        main_window = bom_gui.main_window
        find_tabs = main_window.find_tabs
        find_tabs_index = find_tabs.currentIndex()
        if find_tabs_index == 0:
            bom_gui.searches_update()
        elif find_tabs_index == 1:
            bom_gui.filters_update()
        elif find_tabs_index == 2:
            bom_gui.results_update()
        else:
            assert False

    # BomGui.quit_button_clicked():
    def quit_button_clicked(self):
        bom_gui = self
        print("BomGui.quit_button_clicked() called")
        application = bom_gui.application
        application.quit()

    # BomGui.results_update():
    def results_update(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        bom_gui = self
        main_window = bom_gui.main_window
        results_table = main_window.results_table
        results_table.clearContents()

        bom_gui.current_update()
        current_search = bom_gui.current_search
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
            print("{0}<=BomGui.results_update()".format(tracing))

    # BomGui.run():
    @trace(1)
    def run(self, tracing=""):
        # Show the *window* and exit when done:
        bom_gui = self
        main_window = bom_gui.main_window
        application = bom_gui.application
        # clipboard = application.clipboard()
        # print(f"type(clipboard)='{type(clipboard)}'")
        # assert isinstance(clipboard, QClipboard)

        main_window.show()

        sys.exit(application.exec_())

    # BomGui.save_button_clicked():
    def save_button_clicked(self):
        # Perform any requested signal tracing:
        bom_gui = self
        current_tables = bom_gui.current_tables

        # Save each *table* in *current_tables*:
        for table in current_tables:
            table.save()

        searches = bom_gui.searches
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

    # BomGui.schema_update():
    def schema_update(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Grab some values from *bom_gui* (i.e. *self*):
        bom_gui = self
        main_window = bom_gui.main_window
        schema_tabs = main_window.schema_tabs
        schema_tabs_index = schema_tabs.currentIndex()
        if schema_tabs_index == 0:
            bom_gui.tables_update()
        elif schema_tabs_index == 1:
            bom_gui.parameters_edit_update()
        elif schema_tabs_index == 2:
            bom_gui.enumerations_update()
        else:
            assert False
        # bom_gui.search_update()

    # BomGui.search_clicked():
    def search_clicked(self, search, tracing=""):
        # Verify argument types:
        assert isinstance(search, Search)
        assert isinstance(tracing, str)

        # Grab some values from *bom_gui* (i.e. *self*):
        bom_gui = self
        clicked_model_index = bom_gui.clicked_model_index
        main_window = bom_gui.main_window
        collections_tree = main_window.collections_tree
        collections_line = main_window.collections_line
        selection_model = collections_tree.selectionModel()

        # Grab some values from *search*:
        search_name = search.name
        table = search.parent
        url = search.url
        if tracing:
            print(f"{tracing}url='{url}' table.name='{table.name}'")

        # Force the *url* to open in the web browser:
        webbrowser.open(url, new=0, autoraise=True)

        # Remember that *search* and *model_index* are current:
        bom_gui.current_search = search
        bom_gui.current_model_index = clicked_model_index

        # Now tediously force the GUI to high-light *model_index*:
        flags = (QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)
        selection_model.setCurrentIndex(clicked_model_index, flags)
        flags = (QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)
        selection_model.setCurrentIndex(clicked_model_index, flags)

        # Force *search_name* into the *collections_line* widget:
        collections_line.setText(search_name)

    # BomGui.searches_comment_get():
    def searches_comment_get(self, search, tracing=""):
        # Verify argument types:
        assert isinstance(search, Search) or search is None
        assert isinstance(tracing, str)

        # Perform any requested *tracing*:
        # bom_gui = self

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

    # BomGui.searches_comment_set():
    def searches_comment_set(self, search, text, position, tracing=""):
        # Verify argument types:
        assert isinstance(search, Search) or search is None
        assert isinstance(text, str)
        assert isinstance(position, int)
        assert isinstance(tracing, str)

        # Perform any requested *tracing*:
        # bom_gui = self

        # Stuff *text* and *position* into *search*:
        if search is not None:
            comments = search.comments
            assert len(comments) >= 1
            comment = comments[0]
            assert isinstance(comment, SearchComment)
            comment.lines = text.split('\n')
            comment.position = position

    # BomGui.searches_file_save():
    def searches_file_save(self, file_name, tracing=""):
        # Verify argument types:
        assert isinstance(file_name, str)
        assert isinstance(tracing, str)

        xml_lines = list()
        xml_lines.append('<?xml version="1.0"?>')
        xml_lines.append('<Searches>')

        # Sweep through each *search* in *searches* and append the results to *xml_lines*:
        bom_gui = self
        searches = bom_gui.searches
        for search in searches:
            search.xml_lines_append(xml_lines, "  ")

        # Wrap up *xml_lines* and generate *xml_text*:
        xml_lines.append('</Searches>')
        xml_lines.append("")
        xml_text = '\n'.join(xml_lines)

        # Write out *xml_text* to *file_name*:
        with open(file_name, "w") as xml_file:
            xml_file.write(xml_text)

    # BomGui.searches_file_load():
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

            # Grab *searches* from *bom_gui* (i.e. *self*) and empty it out:
            bom_gui = self
            searches = bom_gui.searches
            assert isinstance(searches, list)
            del searches[:]

            # Parse each *search_tree* in *search_trees*:
            for search_tree in search_trees:
                assert isinstance(search_tree, etree._Element)
                search = Search(search_tree=search_tree,
                                tables=bom_gui.tables)
                assert False, "Old code"
                searches.append(search)

            # Set *current_search*
            bom_gui.current_search = searches[0] if len(searches) >= 1 else None

    # BomGui.searches_is_active():
    def searches_is_active(self):
        bom_gui = self
        bom_gui.current_update()
        # We can only edit searches if there is there is an active *current_table8:
        return bom_gui.current_table is not None

    # BomGui.searches_new():
    def searches_new(self, name, tracing=""):
        # Verify argument types:
        assert isinstance(name, str)
        assert isinstance(tracing, str)

        bom_gui = self
        bom_gui.current_update()
        current_table = bom_gui.current_table

        # Create *serach* with an empty English *serach_comment*:
        search_comment = SearchComment(language="EN", lines=list())
        search_comments = [search_comment]
        search = Search(name=name, comments=search_comments, table=current_table)
        search.filters_refresh()

        return search

    # BomGui.searches_save_button_clicked():
    def searches_save_button_clicked(self):
        # Peform an requested signal tracing:
        bom_gui = self
        tracing = " " if bom_gui.trace_signals else None
        # next_tracing = None if tracing is None else " "
        if tracing:
            print("=>BomGui.searches_save_button_clicked()".format(tracing))

        # Write out the searches to *file_name*:
        # file_name = os.path.join(order_root, "searches.xml")
        # bom_gui.searches_file_save(file_name)
        assert False

        if tracing:
            print("<=BomGui.searches_save_button_clicked()\n".format(tracing))

    # BomGui.searches_table_changed():
    def searches_table_changed(self, new_text):
        # Verify argument types:
        assert isinstance(new_text, str)

        # Do nothing if we are already in a signal:
        bom_gui = self
        if not bom_gui.in_signal:
            bom_gui.in_signal = True
            # Perform any requested *tracing*:

            # Make sure *current_search* is up to date:
            bom_gui = self
            bom_gui.current_update()
            current_search = bom_gui.current_search

            # Find the *table* that matches *new_text* and stuff it into *current_search*:
            if current_search is not None:
                match_table = None
                tables = bom_gui.tables
                for table_index, table in enumerate(tables):
                    assert isinstance(table, Table)
                    if table.name == new_text:
                        match_table = table
                        break
                current_search.table_set(match_table)

            bom_gui.in_signal = False

    # BomGui.searches_update():
    def searches_update(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Make sure that *current_search* is up to date:
        bom_gui = self
        bom_gui.current_update()
        current_search = bom_gui.current_search

        # Next: Update the table options:
        search_table = None if current_search is None else current_search.table
        tables = bom_gui.tables
        main_window = bom_gui.main_window
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

    # BomGui.tab_changed():
    def tab_changed(self, new_index):
        # Verify argument types:
        assert isinstance(new_index, int)

        # Note: *new_index* is only used for debugging.

        # Only deal with this siginal if we are not already *in_signal*:
        bom_gui = self
        if not bom_gui.in_signal:
            # Disable  *nested_signals*:
            bom_gui.in_signal = True

            # Deal with clean-up of previous tab (if requested):
            tab_unload = bom_gui.tab_unload
            if callable(tab_unload):
                tab_unload(bom_gui)

            # Perform the update:
            bom_gui.update()

            bom_gui.in_signal = False

    # BomGui.table_clicked():
    def table_clicked(self, table, tracing=""):
        # Verify argument types:
        assert isinstance(table, Table)
        assert isinstance(tracing, str)

        # Grab some values from *BomGui*:
        bom_gui = self
        bom_gui.current_search = None

        # Sweep through *tables* to see if *table* (i.e. *self*) is in it:
        tables = bom_gui.tables
        for sub_table in tables:
            if table is sub_table:
                # We found a match, so we are done searching:
                break
        else:
            # Nope, *table* is not in *tables*, so let's stuff it in:
            if tracing:
                print("{0}Before len(tables)={1}".format(tracing, len(tables)))
            if tracing:
                print("{0}After len(tables)={1}".format(tracing, len(tables)))

        # Force whatever is visible to be updated:
        bom_gui.update(tracing=tracing)

        # Make *table* the current one:
        bom_gui.current_table = table
        bom_gui.current_parameter = None
        bom_gui.current_enumeration = None
        bom_gui.current_comment = None
        bom_gui.current_search = None

    # BomGui.table_comment_get():
    def table_comment_get(self, table, tracing=""):
        # Verify argument types:
        assert isinstance(table, Table)
        assert isinstance(tracing, str)

        text = ""
        # Perform any requested *tracing*:
        # bom_gui = self

        # Extract the comment *text* from *table*:
        if table is not None:
            comments = table.comments
            assert len(comments) >= 1
            comment = comments[0]
            assert isinstance(comment, TableComment)
            text = '\n'.join(comment.lines)
            position = comment.position
        return text, position

    # BomGui.table_comment_set():
    def table_comment_set(self, table, text, position, tracing=""):
        # Verify argument types:
        assert isinstance(table, Table)
        assert isinstance(text, str)
        assert isinstance(position, int)
        assert isinstance(tracing, str)

        # Perform any requested *tracing*:
        # bom_gui = self
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

    # BomGui.table_new():
    def table_new(self, name, tracing=""):
        # Verify argument types:
        assert isinstance(name, str)

        # Perform an requested *tracing*:

        file_name = "{0}.xml".format(name)
        table_comment = TableComment(language="EN", lines=list())
        table = Table(file_name=file_name, name=name, path="", comments=[table_comment],
                      parameters=list(), csv_file_name="", parent=None)

        return table

    # BomGui.table_setup():
    def table_setup(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Perform any tracing requested from *bom_gui* (i.e. *self*):
        bom_gui = self

        # Grab the *table* widget and *current_table* from *bom_gui* (i.e. *self*):
        bom_gui = self
        main_window = bom_gui.main_window
        data_table = main_window.data_table
        assert isinstance(data_table, QTableWidget)
        current_table = bom_gui.current_table

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

    # BomGui.tables_update():
    def tables_update(self, table=None, tracing=""):
        # Verify argument types:
        assert isinstance(table, Table) or table is None
        assert isinstance(tracing, str)

        # Perform any tracing requested by *bom_gui* (i.e. *self*):
        bom_gui = self

        # Make sure that the *current_table*, *current_parameter*, and *current_enumeration*
        # in *bom_gui* are valid:
        bom_gui.current_update()

    # BomGui.update():
    @trace(1)
    def update(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Perform any requested *tracing*:
        bom_gui = self

        # Only update the visible tabs based on *root_tabs_index*:
        main_window = bom_gui.main_window
        root_tabs = main_window.root_tabs
        root_tabs_index = root_tabs.currentIndex()
        if root_tabs_index == 0:
            bom_gui.collections_update()
        elif root_tabs_index == 1:
            bom_gui.schema_update()
        elif root_tabs_index == 2:
            bom_gui.parameters_update()
        elif root_tabs_index == 3:
            bom_gui.find_update()
        else:
            assert False, "Illegal tab index: {0}".format(root_tabs_index)

    # BomGui.search_update():
    def xxx_search_update(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Make sure that the *current_table*, *current_parameter*, and *current_enumeration*
        # in *bom_gui* are valid:
        bom_gui = self
        bom_gui.current_update()

        # Grab the *current_table* *Table* object from *bom_gui* (i.e. *self*.)
        # Grab the *seach_table* widget from *bom_gui* as well:
        current_table = bom_gui.current_table
        main_window = bom_gui.main_window
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
                #  partial(BomGui.search_use_clicked, bom_gui, use_item, parameter))
                parameter.use = False
                search_table.setItem(parameter_index, 1, use_item)
                search_table.cellClicked.connect(
                  partial(BomGui.search_use_clicked, bom_gui, use_item, parameter))

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


if __name__ == "__main__":
    main()


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
