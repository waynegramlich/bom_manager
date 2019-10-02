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
                             Gui, Node, Order, Search, Table, TableComment)
from bom_manager.tracing import trace  # Tracing decorator module:
# import csv                      # Parser for CSV (Comma Separated Values) files
from functools import partial   # Needed for window events
# import lxml.etree as etree      # type: ignore
import os                       # General Operating system features:

# All of the PySide2 stuff provides the GUI technology used by the GUI.
from PySide2.QtUiTools import QUiLoader                                            # type: ignore
from PySide2.QtWidgets import (QApplication, QLineEdit, QMainWindow, QPushButton)  # type: ignore
from PySide2.QtWidgets import (QTableWidget, QTabWidget, QTableWidgetItem)         # type: ignore
from PySide2.QtWidgets import (QTreeView,)                                         # type: ignore
from PySide2.QtCore import (QAbstractItemModel, QCoreApplication, QFile)           # type: ignore
from PySide2.QtCore import (QItemSelectionModel, QModelIndex, Qt)                  # type: ignore
from PySide2.QtGui import (QClipboard,)                                            # type: ignore
# import re                       # Regular expressions
import sys                      # System utilities
from typing import Dict, List, Optional
import webbrowser               # Some tools to send messages to a web browser


# main():
def main(tracing: str = "") -> int:
    # Process command line arguments:
    collections_directores: List[str]
    searches_root: str
    order: Order
    collection_directories, searches_root, order = command_line_arguments_process()

    # Now create the *bom_gui* graphical user interface (GUI) and run it:
    if tracing:
        print(f"{tracing}searches_root='{searches_root}'")
    tables: List[Table] = list()
    bom_gui: BomGui = BomGui(tables, collection_directories, searches_root, order)

    # Start up the GUI:
    bom_gui.run()

    # Return 0 on successful exit from GUI application:
    return 0


# BomGui:
class BomGui(QMainWindow, Gui):

    # BomGui.__init__()
    @trace(1)
    def __init__(self, tables: List[Table], collection_directories: List[str],
                 searches_root: str, order: Order, tracing: str = "") -> None:
        # Create the *application* first.  The set attribute makes a bogus warning message
        # printout go away:
        QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
        application: QApplication = QApplication(sys.argv)

        # Construct *ui_file_name*:
        module_file_name: str = __file__
        module_directory: str = os.path.split(module_file_name)[0]
        ui_file_name: str = os.path.join(module_directory, "bom_manager.ui")
        if tracing:
            print(f"{tracing}module_file_name='{module_file_name}'")
            print(f"{tracing}module_directory='{module_directory}'")
            print(f"{tracing}ui_file_name='{ui_file_name}'")

        # Create *main_window* from thie `.ui` file:
        # ui_qfile = QFile("bom_manager.ui")
        ui_qfile: QFile = QFile(ui_file_name)
        ui_qfile.open(QFile.ReadOnly)
        loader: QUiLoader = QUiLoader()
        main_window: QMainWindow = loader.load(ui_qfile)

        # Get *working_directory_path*:
        working_directory_path: str = os.getcwd()
        assert os.path.isdir(working_directory_path)

        # Figure out *searches_root* and make sure it exists:
        if os.path.isdir(searches_root):
            # *searches_path* already exists:
            if tracing:
                print(f"{tracing}Using '{searches_root}' directory to store searches into.")
        else:
            # Create directory *searches_root*:
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

        tree_model: TreeModel = TreeModel()

        # Load all values into *bom_gui*:
        current_table: Optional[Table] = tables[0] if len(tables) >= 1 else None
        bom_gui: BomGui = self
        self.application: QApplication = application
        self.clicked_model_index: QModelIndex = QModelIndex()
        self.collection_directories: List[str] = collection_directories
        bom_gui.current_comment = None
        bom_gui.current_enumeration = None
        bom_gui.current_model_index = None
        bom_gui.current_parameter = None
        bom_gui.current_search = None
        self.current_table: Optional[Table] = current_table
        bom_gui.current_tables = tables
        self.in_signal: bool = True
        bom_gui.main_window = main_window
        self.order: Order = order
        self.searches_root: str = searches_root
        self.searches: List[Search] = list()
        self.tree_model: TreeModel = tree_model
        bom_gui.tab_unload = None
        self.tables: List[Table] = tables

        # Initialze both the *QMainWindow* and *Gui* super classes:
        super().__init__()

        # Perform some global signal connections to *main_window* (abbreviated as *mw*):
        mw: QMainWindow = main_window
        mw.collections_check.clicked.connect(bom_gui.collections_check_clicked)
        mw.collections_process.clicked.connect(bom_gui.collections_process_clicked)
        mw.collections_new.clicked.connect(bom_gui.collections_new_clicked)
        mw.collections_new.setEnabled(False)
        mw.collections_line.textChanged.connect(bom_gui.collections_line_changed)
        mw.collections_tree.clicked.connect(bom_gui.collections_tree_clicked)
        # mw.collections_delete.clicked.connect(bom_gui.collections_delete_clicked)
        # mw.collections_delete.setEnabled(False)
        mw.root_tabs.currentChanged.connect(bom_gui.tab_changed)

        # Grap *collections* and stuff into both *bom_gui* and *tree_model*:
        partial_load: bool = True
        collections: Collections = Collections("Collections", collection_directories,
                                               searches_root, partial_load, bom_gui)
        self.collections: Collections = collections
        tree_model.collections_set(collections)

        # Now that both *collections* and *tree_mode* refer to one another we can safely
        # call *partial_load*():
        # collections.partial_load()

        # Now bind *tree_model* to the *collections_tree* widget:
        collections_tree: QTreeView = mw.collections_tree
        collections_tree.setModel(tree_model)
        collections_tree.setSortingEnabled(True)

        # FIXME: Used *bom_gui.current_update()* instead!!!
        current_table = None
        # current_parameter = None
        # current_enumeration = None
        # if len(tables) >= 1:
        #    table = tables[0]
        #     parameters = table.parameters
        #     if len(parameters) >= 1:
        #         parameter = parameters[0]
        #         # current_parameter = parameter
        #         enumerations = parameter.enumerations
        #         # if len(enumerations) >= 1:
        #             enumeration = enumerations[0]
        #             # current_enumeration = enumeration
        #     # table.current_table = current_table
        #     # table.current_parameter = current_parameter
        #     # table.current_enumeration = current_enumeration

        # bom_gui.table_setup()

        # Read in `searches.xml` if it exists:
        # bom_gui.searches_file_load(os.path.join(order_root, "searches.xml"),
        #                                  )

        # Update the entire user interface:
        bom_gui.update()

        self.in_signal = False

    # BomGui.__str__():
    def __str__(self) -> str:
        return "BomGui()"

    # BomGui.begin_rows_insert():
    def begin_rows_insert(self, node: Node, start_row_index: int, end_row_index: int,
                          tracing: str = "") -> None:

        # Create a *model_index* for *node* and *insert_row_index* starting from
        # *bom_gui* (i.e. *self):
        bom_gui: BomGui = self
        tree_model: TreeModel = bom_gui.tree_model
        model_index: QModelIndex = tree_model.createIndex(0, 0, node)

        # Inform the *tree_model* that rows will be inserted from *start_row_index* through
        # *end_row_index*:
        tree_model.beginInsertRows(model_index, start_row_index, end_row_index)

    # BomGui.begin_rows_remove():
    def begin_rows_remove(self, node: Node, start_row_index: int, end_row_index: int,
                          tracing: str = "") -> None:

        # Create a *model_index* for *node* and *insert_row_index* starting from
        # *bom_gui* (i.e. *self):
        bom_gui: BomGui = self
        tree_model: TreeModel = bom_gui.tree_model
        model_index: QModelIndex = tree_model.createIndex(0, 0, node)

        # Inform the *tree_model* that rows will be inserted from *start_row_index* through
        # *end_row_index*:
        tree_model.beginRemoveRows(model_index, start_row_index, end_row_index)

    # BomGui.comment_text_set()
    def comment_text_set(self, new_text: str, tracing: str = "") -> None:
        # Carefully set thet text:
        bom_gui: BomGui = self
        main_window: QMainWindow = bom_gui.main_window
        comment_text: QLineEdit = main_window.parameters_comment_text
        comment_text.setPlainText(new_text)

        # Update the collections tab:
        bom_gui.update()

    # BomGui.collection_clicked():
    def collection_clicked(self, collection: Collection, tracing: str = "") -> None:
        # Make sure that the current table and search are disabled for *bom_gui* (i.e. *self*):
        bom_gui: BomGui = self
        bom_gui.current_search = None
        bom_gui.current_table = None

    # BomGui.collections_line_changed():
    @trace(1)
    def collections_line_changed(self, text: str, tracing: str = "") -> None:
        # Make sure that *bom_gui* (i.e. *self*) is updated:
        bom_gui: BomGui = self
        bom_gui.update()

    # BomGui.collections_new_clicked():
    @trace(1)
    def collections_new_clicked(self, tracing: str = "") -> None:
        # Perform any requested *tracing*:
        bom_gui: BomGui = self
        # Grab some values from *bom_gui* (i.e. *self*):
        current_search: Optional[Search] = bom_gui.current_search

        # Make sure *current_search* exists (this button click should be disabled if not available):
        assert current_search is not None

        # clip_board = pyperclip.paste()
        # selection = os.popen("xsel").read()
        application: QApplication = bom_gui.application
        application_clipboard: QClipboard = application.clipboard()
        selection: str = application_clipboard.text(QClipboard.Selection)
        clipboard: str = application_clipboard.text(QClipboard.Clipboard)

        url: str = ""
        if selection.startswith("http"):
            url = selection
        elif clipboard.startswith("http"):
            url = clipboard
        if tracing:
            print(f"{tracing}clipbboard='{clipboard}'")
            print(f"{tracing}selection='{selection}'")
            print(f"{tracing}url='{url}'")

        # Process *url* (if it is valid):
        if url == "":
            print("URL: No valid URL found!")
        else:
            # Grab some stuff from *bom_gui*:
            main_window: QMainWindow = bom_gui.main_window
            collections_line: QLineEdit = main_window.collections_line
            new_search_name: str = collections_line.text().strip()

            # Grab some values from *current_search*:
            table: Optional[Node] = current_search.parent
            assert isinstance(table, Table)

            # Construct *new_search_name*:
            new_search: Search = Search(new_search_name, table, current_search, url)
            assert table.has_child(new_search)

            # if tracing:
            #    print("{0}1:len(searches)={1}".format(tracing, len(searches)))
            table.sort()
            new_search.xml_file_save()

            model_index: QModelIndex = bom_gui.current_model_index
            if model_index is not None:
                parent_model_index: QModelIndex = model_index.parent()
                tree_model: TreeModel = model_index.model()
                tree_model.children_update(parent_model_index)

            # model = bom_gui.model
            # model.insertNodes(0, [ new_search ], parent_model_index)
            # if tracing:
            #    print("{0}2:len(searches)={1}".format(tracing, len(searches)))

            bom_gui.update()

    # BomGui.collections_check_clicked():
    @trace(1)
    def collections_check_clicked(self, tracing: str = "") -> None:
        # Grab some values from *bom_gui* (i.e. *self*):
        bom_gui: BomGui = self
        collections: Collections = bom_gui.collections
        order: Order = bom_gui.order

        # Delegate checking to *order* object:
        order.check(collections)

    # BomGui.collections_process_clicked():
    @trace(1)
    def collections_process_clicked(self, tracing: str = "") -> None:
        # Grab some values from *bom_gui* (i.e. *self*):
        bom_gui: BomGui = self
        collections: Collections = bom_gui.collections
        order: Order = bom_gui.order

        # Now process *order* using *collections*:
        order.process(collections)

    # BomGui.collections_tree_clicked():
    @trace(1)
    def collections_tree_clicked(self, model_index: QModelIndex, tracing: str = "") -> None:
        # Stuff *model_index* into *bom_gui* (i.e. *self*):
        bom_gui: BomGui = self
        bom_gui.current_model_index = model_index

        # If *tracing*, show the *row* and *column*:
        if tracing:
            row: int = model_index.row()
            column: int = model_index.column()
            print(f"{tracing}row={row} column={column}")

        # Now grab the associated *node* from *model_index*:
        model: TreeModel = model_index.model()
        node: Optional[Node] = model.getNode(model_index)
        assert isinstance(node, Node)

        # Let the *node* know it has been clicked:
        bom_gui.clicked_model_index = model_index
        node.clicked(bom_gui)

        # *Search* *node*'s get some additional treatment:
        if isinstance(node, Search):
            main_window: QMainWindow = bom_gui.main_window
            collections_line: QLineEdit = main_window.collections_line
            collections_line.setText(node.name)

        # Lastly, tell *bom_gui* to update the GUI:
        bom_gui.update()

    # BomGui.collections_update():
    @trace(1)
    def collections_update(self, tracing: str = "") -> None:
        # Grab some widgets from *bom_gui*:
        bom_gui: BomGui = self
        main_window: QMainWindow = bom_gui.main_window
        collections_delete: QPushButton = main_window.collections_delete
        collections_line: QLineEdit = main_window.collections_line
        collections_new: QPushButton = main_window.collections_new

        # Grab the *current_search* object:
        current_search: Optional[Search] = bom_gui.current_search
        if tracing:
            current_search_name: str = ("None" if current_search is None
                                        else f"'{current_search.name}'")
            print(f"{tracing}current_search={current_search_name}")

        # Grab the *search_tile* from the *collections_line* widget*:
        search_title: str = collections_line.text()

        # We can only create a search if:
        # * the search *search_title* not empty,
        # * the search *search_title* is not named "@ALL",
        # * there is a preexisting *current_search* to depend upon
        # * the *search_title* is not a duplicate:
        new_button_enable: bool = False
        new_button_why: str = "Default off"
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
            table: Optional[Node] = current_search.parent
            assert isinstance(table, Table)
            collection: Optional[Collection] = table.collection
            assert isinstance(collection, Collection)
            searches_table: Dict[str, Search] = collection.searches_table
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
        delete_button_enable: bool = False
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

    # BomGui.current_update()
    def current_update(self, tracing: str = "") -> None:
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
        # current_parameter = None
        # if current_table is None:
        #     parameters = list()
        # else:
        #     parameters = current_table.parameters
        #     parameters_size = len(parameters)
        #     if parameters_size >= 1:
        #         current_parameter = bom_gui.current_parameter
        #         if current_parameter is not None:
        #             for parameter in parameters:
        #                 assert isinstance(parameter, Parameter)
        #                 if parameter is current_parameter:
        #                     break
        #             else:
        #                 # *current_parameter* is invalid:
        #                 current_parameter = None
        #     if current_parameter is None and parameters_size >= 1:
        #         current_parameter = parameters[0]
        # bom_gui.current_parameter = current_parameter
        # if tracing:
        #     print("{0}current_parameter='{1}'".
        #          format(tracing, "None" if current_parameter is None else current_parameter.name))

        # Make sure *current_enumeration* is valid (or *None*):
        # current_enumeration = None
        # if current_parameter is None:
        #     enumerations = list()
        # else:
        #     enumerations = current_parameter.enumerations
        #     enumerations_size = len(enumerations)
        #     if enumerations_size >= 1:
        #         current_enumeration = bom_gui.current_enumeration
        #         if current_enumeration is not None:
        #             for enumeration in enumerations:
        #                 assert isinstance(enumeration, Enumeration)
        #                 if enumeration is current_enumeration:
        #                     break
        #             else:
        #                 # *current_enumeration* is invalid:
        #                 current_enumeration = None
        #         if current_enumeration is None and enumerations_size >= 1:
        #             current_enumeration = enumerations[0]
        # bom_gui.current_enumeration = current_enumeration

        # Make sure that *current_search* is valid (or *None*):
        # bom_gui.current_search = current_search

        # if tracing:
        #     print("{0}current_enumeration'{1}'".format(
        #       tracing, "None" if current_enumeration is None else current_enumeration.name))

        # Make sure that *current_search* is valid (or *None*):
        searches: List[Search] = bom_gui.searches
        current_search: Optional[Search] = bom_gui.current_search
        if current_search is None:
            if len(searches) >= 1:
                current_search = searches[0]
        else:
            search_index: int
            search: Search
            for search_index, search in enumerate(searches):
                if search is current_search:
                    break
            else:
                # *current_search* is not in *searches* and must be invalid:
                current_search = None
        bom_gui.current_search = current_search
        if tracing:
            current_search_text: str = "None" if current_search is None else current_search.name
            print(f"{tracing}current_search='{current_search_text}'")

    # BomGui.data_update()
    def data_update(self, tracing: str = "") -> None:

        # Make sure that the data for *bom_gui* (i.e. *self*) is up-to-date:
        bom_gui: BomGui = self
        bom_gui.current_update()

    # BomGui.directory_clicked():
    def directory_clicked(self, directory: Directory, tracing: str = "") -> None:
        # Mark the current search in *bom_gui* (i.e. *self*) as not active:
        bom_gui: BomGui = self
        bom_gui.current_search = None

    # BomGui.end_rows_insert():
    def end_rows_insert(self, tracing: str = "") -> None:
        # Inform the *tree_model* associated with *bom_gui* (i.e. *self*) that we are
        # done inserting rows:
        bom_gui: BomGui = self
        tree_model: TreeModel = bom_gui.tree_model
        tree_model.endInsertRows()

    # BomGui.end_rows_remove():
    def end_rows_remove(self, tracing: str = "") -> None:
        # Inform the *tree_model* associated with *bom_gui* (i.e. *self*) that we are
        # done inserting rows:
        bom_gui: BomGui = self
        tree_model: TreeModel = bom_gui.tree_model
        tree_model.endRemoveRows()

    # BomGui.quit_button_clicked():
    def quit_button_clicked(self, tracing: str = "") -> None:
        bom_gui: BomGui = self
        if tracing:
            print(f"{tracing}BomGui.quit_button_clicked()")
        application: QApplication = bom_gui.application
        application.quit()

    # BomGui.run():
    @trace(1)
    def run(self, tracing: str = "") -> None:
        # Grab some values from *bom_gui* (i.e. *self*):
        bom_gui: BomGui = self
        main_window: QMainWindow = bom_gui.main_window
        application: QApplication = bom_gui.application

        # Force *main_window* to be shown*:
        main_window.show()

        # When we are done with *main_window*, we can exit the application:
        sys.exit(application.exec_())

    # BomGui.search_clicked():
    def search_clicked(self, search: Search, tracing: str = "") -> None:
        # Grab some values from *bom_gui* (i.e. *self*):
        bom_gui: BomGui = self
        clicked_model_index: QModelIndex = bom_gui.clicked_model_index
        main_window: QMainWindow = bom_gui.main_window
        collections_tree: QTreeView = main_window.collections_tree
        collections_line: QLineEdit = main_window.collections_line
        selection_model: QItemSelectionModel = collections_tree.selectionModel()

        # Grab some values from *search*:
        search_name: str = search.name
        table: Optional[Node] = search.parent
        assert isinstance(table, Table)
        url: str = search.url
        if tracing:
            print(f"{tracing}url='{url}' table.name='{table.name}'")

        # Force the *url* to open in the web browser:
        webbrowser.open(url, new=0, autoraise=True)

        # Remember that *search* and *model_index* are current:
        bom_gui.current_search = search
        bom_gui.current_model_index = clicked_model_index

        # Now tediously force the GUI to high-light *model_index*:
        flags: int = (QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)
        selection_model.setCurrentIndex(clicked_model_index, flags)
        # flags: int = (QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)
        # selection_model.setCurrentIndex(clicked_model_index, flags)

        # Force *search_name* into the *collections_line* widget:
        collections_line.setText(search_name)

    # BomGui.tab_changed():
    def tab_changed(self, new_index: int, tracing: str = "") -> None:
        # Note: *new_index* is only used for debugging.

        # Only deal with this siginal if we are not already *in_signal*:
        bom_gui: BomGui = self
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
    def table_clicked(self, table: Table, tracing: str = "") -> None:
        # Grab some values from *BomGui*:
        bom_gui: BomGui = self
        bom_gui.current_search = None

        # FIXME: Is this code needed any more???!!!:
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
        bom_gui.update()

        # Make *table* the current one:
        bom_gui.current_table = table
        bom_gui.current_search = None

    def table_is_active(self, tracing: str = "") -> bool:
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

    # BomGui.update():
    @trace(1)
    def update(self, tracing: str = "") -> None:
        # Perform any requested *tracing*:
        bom_gui: BomGui = self

        # Only update the visible tabs based on *root_tabs_index*:
        main_window: QMainWindow = bom_gui.main_window
        root_tabs: QTabWidget = main_window.root_tabs
        root_tabs_index: int = root_tabs.currentIndex()
        if root_tabs_index == 0:
            bom_gui.collections_update()
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
    def __init__(self, tracing: str = "") -> None:
        # Initialize the parent *QAbstraceItemModel*:
        super().__init__()

        # Stuff values into *tree_model* (i.e. *self*):
        # tree_model: TreeModel = self
        self.headers: Dict[int, str] = {0: "Type", 1: "Name"}
        self.collections: Optional[Collections] = None
        self.tracing: str = tracing

    # TreeMode.__str__():
    def __str__(self) -> str:
        return "TreeModel()"

    # check if the node has data that has not been loaded yet
    # TreeModel.canFetchMore():
    def canFetchMore(self, model_index: QModelIndex, tracing: str = "") -> bool:
        # We delegate the decision of whether we can fetch more stuff to the *node*
        # associated with *model_index*:
        tree_model: TreeModel = self
        node: Node = tree_model.getNode(model_index)
        can_fetch_more: bool = node.can_fetch_more()
        return can_fetch_more

    # TreeModel.collections_set():
    def collections_set(self, collections: Collections, tracing: str = ""):
        # Stuff *collections* into *tree_model* (i.e. *self*):
        tree_model: TreeModel = self
        tree_model.collections = collections

    # TreeModel.columnCount():
    def columnCount(self, model_index: QModelIndex, tracing: str = "") -> int:
        return 2

    # TreeModel.data():
    def data(self, model_index: QModelIndex, role: int) -> Optional[str]:
        # Perform any *tracing* requested by *tree_model* (i.e. *self*):
        # tree_model: TreeModel = self
        value: Optional[str] = None
        if model_index.isValid():
            # row = model_index.row()
            column: int = model_index.column()
            node: Node = model_index.internalPointer()
            if role == Qt.DisplayRole:
                if column == 0:
                    value = node.type_letter_get()
                elif column == 1:
                    value = node.name_get()
        return value

    # TreeModel.delete():
    def delete(self, model_index: QModelIndex, tracing: str = "") -> None:
        # Perform any *tracing* requested by *tree_model* (i.e. *self*):
        tree_model: TreeModel = self

        # Carefully delete the row associated with *model_index*:
        if model_index.isValid():
            # row = model_index.row()
            node: Node = tree_model.getNode(model_index)
            assert isinstance(node, Node)
            parent: Optional[Node] = node.parent
            if parent is not None:
                parent.child_remove(node)

    # TreeModel.fetchMore():
    def fetchMore(self, model_index: QModelIndex, tracing: str = "") -> None:
        # Delegate fetching to the *node* associated with *model_index*:
        tree_model: TreeModel = self
        node: Node = tree_model.getNode(model_index)
        node.fetch_more()

    # TreeModel.getNode():
    def getNode(self, model_index: QModelIndex, tracing: str = "") -> Node:
        tree_model: TreeModel = self
        node: Node = (model_index.internalPointer() if model_index.isValid()
                      else tree_model.collections)
        assert isinstance(node, Node), f"node.type={type(node)}"
        return node

    # TreeModel.hasChildren():
    def hasChildren(self, model_index: QModelIndex, tracing: str = "") -> bool:
        # Delegate to *has_children*() method to *node*:
        tree_model: TreeModel = self
        node: Node = tree_model.getNode(model_index)
        has_children: bool = node.has_children()
        return has_children

    # TreeModel.headerData():
    def headerData(self, section: int, orientation: Qt.Orientation, role: int,
                   tracing: str = "") -> Optional[str]:
        tree_model: TreeModel = self
        header_data: Optional[str] = (tree_model.headers[section]
                                      if orientation == Qt.Horizontal and role == Qt.DisplayRole
                                      else None)
        return header_data

    # TreeModel.flags():
    def flags(self, model_index: QModelIndex, tracing: str = "") -> int:
        return TreeModel.FLAG_DEFAULT

    # TreeModel.index():
    def index(self, row: int, column: int, parent_model_index: QModelIndex) -> QModelIndex:
        tree_model: TreeModel = self
        node: Node = tree_model.getNode(parent_model_index)
        # FIXME: child method should be sibling method!!!
        child = node.child(row)
        model_index: QModelIndex = (QModelIndex() if child is None
                                    else tree_model.createIndex(row, column, child))
        assert isinstance(parent_model_index, QModelIndex)
        return model_index

    # TreeModel.children_update():
    def children_update(self, parent_model_index: QModelIndex, tracing: str = "") -> None:
        # Grab the *parent_node* using *parent_model_index* and *tree_model* (i.e. *self*):
        tree_model: TreeModel = self
        parent_node: Node = tree_model.getNode(parent_model_index)
        children: List[Node] = parent_node.children_get()
        children_size: int = len(children)

        # For now do something really simple and just delete everything and reinsert it:
        if children_size >= 1:
            tree_model.beginRemoveRows(parent_model_index, 0, children_size - 1)
            tree_model.endRemoveRows()
        tree_model.beginInsertRows(parent_model_index, 0, children_size - 1)
        tree_model.endInsertRows()

    # TreeModel.insertNodes():
    def insertNodes(self, position: int, nodes: List[Node],
                    parent_model_index: QModelIndex = QModelIndex(),
                    tracing: str = "") -> bool:
        tree_model: TreeModel = self
        node: Node = tree_model.getNode(parent_model_index)

        tree_model.beginInsertRows(parent_model_index, position, position + len(nodes) - 1)

        child: Node
        for child in reversed(nodes):
            node.child_insert(position, child)

        tree_model.endInsertRows()

        return True

    # TreeModel.parent():
    def parent(self, model_index: QModelIndex, tracing: str = "") -> QModelIndex:
        tree_model: TreeModel = self
        node: Node = tree_model.getNode(model_index)
        parent: Optional[Node] = node.parent
        parent_model_index: QModelIndex
        if parent is None or isinstance(parent, Collections):
            parent_model_index = QModelIndex()
        else:
            parent_model_index = tree_model.createIndex(parent.row(), 0, parent)
        return parent_model_index

    # Return 0 if there is data to fetch (handled implicitly by check length of child list)
    # TreeModel.rowCount():
    def rowCount(self, parent: QModelIndex, tracing: str = "") -> int:
        tree_model: TreeModel = self
        node: Node = tree_model.getNode(parent)
        count: int = node.child_count()
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
