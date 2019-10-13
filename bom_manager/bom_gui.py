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
from bom_manager.tracing import trace, tracing_get  # Tracing decorator module:
# import csv                      # Parser for CSV (Comma Separated Values) files
from functools import partial   # Needed for window events
# import lxml.etree as etree      # type: ignore
import os                       # General Operating system features:

# All of the PySide2 stuff provides the GUI technology used by the GUI.
from PySide2.QtUiTools import QUiLoader                                               # type: ignore
from PySide2.QtWidgets import (QApplication, QLabel, QLineEdit, QMainWindow)          # type: ignore
from PySide2.QtWidgets import (QPushButton, QStackedWidget, QTableWidget)             # type: ignore
from PySide2.QtWidgets import (QTabWidget, QTableWidgetItem, QTreeView, QWidget)      # type: ignore
from PySide2.QtCore import (QAbstractItemModel, QCoreApplication, QFile)              # type: ignore
from PySide2.QtCore import (QItemSelectionModel, QModelIndex, Qt)                     # type: ignore
from PySide2.QtGui import (QClipboard,)                                               # type: ignore
# import re                       # Regular expressions
import sys                      # System utilities
from typing import Callable, Dict, List, Optional
import webbrowser               # Some tools to send messages to a web browser


# main():
def main() -> int:
    # Process command line arguments:
    collections_directores: List[str]
    searches_root: str
    order: Order
    collection_directories, searches_root, order = command_line_arguments_process()

    # Now create the *bom_gui* graphical user interface (GUI) and run it:
    tracing: str = tracing_get()
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
    # @trace(1)
    def __init__(self, tables: List[Table], collection_directories: List[str],
                 searches_root: str, order: Order) -> None:
        # Create the *application* first.  The set attribute makes a bogus warning message
        # printout go away:
        QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
        application: QApplication = QApplication(sys.argv)

        # Construct *ui_file_name*:
        module_file_name: str = __file__
        module_directory: str = os.path.split(module_file_name)[0]
        ui_file_name: str = os.path.join(module_directory, "bom_manager.ui")
        tracing: str = tracing_get()
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

        # Initialze both the *QMainWindow* and *Gui* super classes:
        super().__init__()

        # Load all values into *bom_gui*:
        current_table: Optional[Table] = tables[0] if len(tables) >= 1 else None
        bom_gui: BomGui = self
        self.application: QApplication = application
        self.clicked_model_index: QModelIndex = QModelIndex()
        self.collection_directories: List[str] = collection_directories
        self.current_collection: Optional[Collection] = None
        self.current_model_index: Optional[QModelIndex] = None
        self.current_node: Optional[Node] = None
        self.current_search: Optional[Search] = None
        self.current_table: Optional[Table] = current_table
        self.in_signal: bool = True
        self.main_window: QMainWindow = main_window
        self.order: Order = order
        self.searches_root: str = searches_root
        self.searches: List[Search] = list()
        self.tree_model: TreeModel = tree_model
        self.tab_unload: Optional[Callable] = None
        self.tables: List[Table] = tables

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
        mw.tree_tabs.currentChanged.connect(bom_gui.tab_changed)

        bom_gui.panels_connect()

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
        root_model_index: QModelIndex = tree_model.createIndex(0, 0, collections)
        collections_tree.setRootIndex(root_model_index)
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
    @trace(1)
    def begin_rows_insert(self, node: Node, start_row_index: int, end_row_index: int) -> None:

        # Create a *model_index* for *node* and *insert_row_index* starting from
        # *bom_gui* (i.e. *self):
        bom_gui: BomGui = self
        tree_model: TreeModel = bom_gui.tree_model
        model_index: QModelIndex = tree_model.createIndex(0, 0, node)

        # Inform the *tree_model* that rows will be inserted from *start_row_index* through
        # *end_row_index*:
        tree_model.beginInsertRows(model_index, start_row_index, end_row_index)

    # BomGui.begin_rows_remove():
    @trace(1)
    def begin_rows_remove(self, node: Node, start_row_index: int, end_row_index: int) -> None:

        # Create a *model_index* for *node* and *insert_row_index* starting from
        # *bom_gui* (i.e. *self):
        bom_gui: BomGui = self
        tree_model: TreeModel = bom_gui.tree_model
        model_index: QModelIndex = tree_model.createIndex(0, 0, node)

        # Inform the *tree_model* that rows will be inserted from *start_row_index* through
        # *end_row_index*:
        tree_model.beginRemoveRows(model_index, start_row_index, end_row_index)

    # BomGui.comment_text_set()
    def comment_text_set(self, new_text: str) -> None:
        # Carefully set thet text:
        bom_gui: BomGui = self
        main_window: QMainWindow = bom_gui.main_window
        comment_text: QLineEdit = main_window.parameters_comment_text
        comment_text.setPlainText(new_text)

        # Update the collections tab:
        bom_gui.update()

    # BomGui.collection_panel_update():
    @trace(1)
    def collection_panel_update(self, collection: Collection):
        # Force the *panel_collection* widget to be displayed by *panels* stacked widget:
        bom_gui: BomGui = self
        main_window: QMainWindow = bom_gui.main_window
        panels: QStackedWidget = main_window.panels
        collection_panel: QWidget = main_window.collection_panel
        panels.setCurrentWidget(collection_panel)

        # As a sanity check make sure that *current_collection* is correct in *bom_gui*:
        assert bom_gui.current_collection is collection

        # Now update *panel_collection* name:
        collection_panel_name: QLabel = main_window.collection_panel_name
        name_text: str = f"Name: {collection.name}"
        collection_panel_name.setText(name_text)

    # BomGui.collection_clicked():
    @trace(1)
    def collection_clicked(self, collection: Collection) -> None:
        # Make sure that the current table and search are disabled for *bom_gui* (i.e. *self*):
        bom_gui: BomGui = self
        bom_gui.current_collection = collection
        bom_gui.current_directory = None
        bom_gui.current_node = collection
        bom_gui.current_search = None
        bom_gui.current_table = None

    # BomGui.collections_line_changed():
    @trace(1)
    def collections_line_changed(self, text: str) -> None:
        # Make sure that *bom_gui* (i.e. *self*) is updated:
        bom_gui: BomGui = self
        bom_gui.update()

    # BomGui.collections_new_clicked():
    @trace(1)
    def collections_new_clicked(self) -> None:
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
        tracing: str = tracing_get()
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
    def collections_check_clicked(self) -> None:
        # Grab some values from *bom_gui* (i.e. *self*):
        bom_gui: BomGui = self
        collections: Collections = bom_gui.collections
        order: Order = bom_gui.order

        # Delegate checking to *order* object:
        order.check(collections)

    # BomGui.collections_process_clicked():
    @trace(1)
    def collections_process_clicked(self) -> None:
        # Grab some values from *bom_gui* (i.e. *self*):
        bom_gui: BomGui = self
        collections: Collections = bom_gui.collections
        order: Order = bom_gui.order

        # Now process *order* using *collections*:
        order.process(collections)

    # BomGui.collections_tree_clicked():
    @trace(1)
    def collections_tree_clicked(self, model_index: QModelIndex) -> None:
        # Stuff *model_index* into *bom_gui* (i.e. *self*):
        bom_gui: BomGui = self
        bom_gui.current_model_index = model_index

        # If *tracing*, show the *row* and *column*:
        tracing: str = tracing_get()
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
        if tracing:
            print(f"{tracing}Calling {node.__class__.__name__}.clicked()")
        node.clicked(bom_gui)
        if tracing:
            print(f"{tracing}Returned from {node.__class__.__name__}.clicked()")

        # *Search* *node*'s get some additional treatment:
        if isinstance(node, Search):
            main_window: QMainWindow = bom_gui.main_window
            collections_line: QLineEdit = main_window.collections_line
            collections_line.setText(node.name)

        # Lastly, tell *bom_gui* to update the GUI:
        bom_gui.update()

    # BomGui.collections_update():
    @trace(1)
    def collections_update(self) -> None:
        # Grab some widgets from *bom_gui*:
        bom_gui: BomGui = self
        main_window: QMainWindow = bom_gui.main_window
        collections_delete: QPushButton = main_window.collections_delete
        collections_line: QLineEdit = main_window.collections_line
        collections_new: QPushButton = main_window.collections_new
        collections_tab: QTabWidget = main_window.collections_tab

        # Grab the *current_search* object:
        current_search: Optional[Search] = bom_gui.current_search
        tracing: str = tracing_get()
        if tracing:
            current_search_name: str = ("None" if current_search is None
                                        else f"'{current_search.name}'")
            print(f"{tracing}current_search={current_search_name}")

        # Grab the *search_title* from the *collections_line* widget*:
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

        # Force update of *collections_tab*:
        if tracing:
            print(f"{tracing}>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
            print(f"{tracing}collections_tab.update() called()")
        collections_tab.update()
        if tracing:
            print(f"{tracing}collections_tab.update() returned()")
            print(f"{tracing}<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<")
        if tracing:
            print(f"{tracing}delete_button_enable={delete_button_enable} why='{delete_button_why}'")

    # BomGui.current_update()
    def current_update(self) -> None:
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
        tracing: str = tracing_get()
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

    # BomGui.data_changed():
    @trace(1)
    def data_changed(self, node: Node, start_index: int, end_index: int) -> None:
        pass  # FIXME!!!

    # BomGui.data_update()
    def data_update(self) -> None:

        # Make sure that the data for *bom_gui* (i.e. *self*) is up-to-date:
        bom_gui: BomGui = self
        bom_gui.current_update()

    # BomGui.directory_clicked():
    @trace(1)
    def directory_clicked(self, directory: Directory) -> None:
        # Mark the current search in *bom_gui* (i.e. *self*) as not active:
        bom_gui: BomGui = self
        bom_gui.current_collection = directory.collection
        bom_gui.current_directory = directory
        bom_gui.current_node = directory
        bom_gui.current_search = None
        bom_gui.current_table = None

    # BomGui.directory_panel_update():
    def directory_panel_update(self, directory: Directory) -> None:
        # Force the *panels* stacked widget to display *panel_directory* widget:
        bom_gui: BomGui = self
        main_window: QMainWindow = bom_gui.main_window
        panels: QStackedWidget = main_window.panels
        directory_panel: QWidget = main_window.directory_panel
        panels.setCurrentWidget(directory_panel)

        # As a sanity check make sure that *current_directory* in *bom_gui* is correct:
        assert bom_gui.current_directory is directory

        # Now update the *panel_directory_name* field:
        directory_panel_name: QLabel = main_window.directory_panel_name
        name_text = f"Name: {directory.name}"
        directory_panel_name.setText(name_text)

    # BomGui.end_rows_insert():
    @trace(1)
    def end_rows_insert(self, node: Node, start_row_index: int, end_row_index: int) -> None:
        # Inform the *tree_model* associated with *bom_gui* (i.e. *self*) that we are
        # done inserting rows:
        bom_gui: BomGui = self
        tree_model: TreeModel = bom_gui.tree_model
        tree_model.endInsertRows()

    # BomGui.end_rows_remove():
    @trace(1)
    def end_rows_remove(self, node: Node, start_row_index: int, end_row_index: int) -> None:
        # Inform the *tree_model* associated with *bom_gui* (i.e. *self*) that we are
        # done inserting rows:
        bom_gui: BomGui = self
        tree_model: TreeModel = bom_gui.tree_model
        tree_model.endRemoveRows()

    # BomGui.panels_connect():
    @trace(1)
    def panels_connect(self) -> None:
        bom_gui: BomGui = self
        bom_gui.search_panel_connect()

    # BomGui.panels_update():
    @trace(1)
    def panels_update(self) -> None:
        # Dispatch on the *current_node* of *bom_gui* (i.e. *self*):
        bom_gui: BomGui = self
        current_node: Optional[Node] = bom_gui.current_node
        tracing: str = tracing_get()
        if current_node is None:
            # There is no *current_node* selected, so we display the *panel_none* widget:
            if tracing:
                print(f"{tracing}No Node currently set, show None panel")
            main_window: QMainWindow = bom_gui.main_window
            panels: QStackedWidget = main_window.panels
            none_panel: QWidget = main_window.none_panel
            panels.setCurrentWidget(none_panel)
        else:
            # There is a *current_node*, so invoke *panel_update* method which will
            # dispatch to the appropriate method that updates the panel for *current_node*:
            if tracing:
                print(f"{tracing}Calling {current_node.__class__.__name__}.panel_update")
            current_node.panel_update(bom_gui)
            if tracing:
                print(f"{tracing}Returned from {current_node.__class__.__name__}.panel_update")

    # BomGui.quit_button_clicked():
    def quit_button_clicked(self) -> None:
        bom_gui: BomGui = self
        tracing: str = tracing_get()
        if tracing:
            print(f"{tracing}BomGui.quit_button_clicked()")
        application: QApplication = bom_gui.application
        application.quit()

    # BomGui.run():
    @trace(1)
    def run(self) -> None:
        # Grab some values from *bom_gui* (i.e. *self*):
        bom_gui: BomGui = self
        main_window: QMainWindow = bom_gui.main_window
        application: QApplication = bom_gui.application

        # Force *main_window* to be shown*:
        main_window.show()

        # When we are done with *main_window*, we can exit the application:
        sys.exit(application.exec_())

    # BomGui.search_clicked():
    @trace(1)
    def search_clicked(self, search: Search) -> None:
        # Grab some values from *search*:
        current_table: Optional[Node] = search.parent
        assert isinstance(current_table, Table)
        current_directory: Optional[Node] = current_table.parent
        assert isinstance(current_directory, Directory)
        current_collection: Optional[Collection] = search.collection
        assert isinstance(current_collection, Collection)

        # Update the current nodes associated
        bom_gui: BomGui = self
        bom_gui.current_collection = current_collection
        bom_gui.current_directory = current_directory
        bom_gui.current_node = search
        bom_gui.current_table = current_table
        bom_gui.current_search = search

        # For now skip everything else:
        return

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
        tracing: str = tracing_get()
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

    # BomGui.search_panel_connect():
    @trace(1)
    def search_panel_connect(self) -> None:
        # Grab the various search panel widgets from the *main_window* of *bom_gui* (i.e. *self*):
        bom_gui: BomGui = self
        main_window: QMainWindow = bom_gui.main_window
        search_panel_new: QPushButton = main_window.search_panel_new
        search_panel_new_name_line: QLineEdit = main_window.search_panel_new_name_line
        search_panel_remove: QPushButton = main_window.search_panel_remove
        search_panel_rename: QPushButton = main_window.search_panel_rename
        search_panel_url_get: QPushButton = main_window.search_panel_url_get
        search_panel_url_send: QPushButton = main_window.search_panel_url_send

        # Connect the search panel events up to forwarding methods in *bom_gui*:
        search_panel_new.clicked.connect(bom_gui.search_panel_new_clicked)
        search_panel_new_name_line.textChanged.connect(bom_gui.search_panel_new_name_line_changed)
        search_panel_remove.clicked.connect(bom_gui.search_panel_remove_clicked)
        search_panel_rename.clicked.connect(bom_gui.search_panel_rename_clicked)
        search_panel_url_get.clicked.connect(bom_gui.search_panel_url_get_clicked)
        search_panel_url_send.clicked.connect(bom_gui.search_panel_url_send_clicked)

    # BomGui.search_panel_new_clicked():
    @trace(1)
    def search_panel_new_clicked(self) -> None:
        bom_gui: BomGui = self
        current_search: Optional[Search] = bom_gui.current_search
        assert isinstance(current_search, Search)
        main_window: QMainWindow = bom_gui.main_window
        search_panel_new_name_line: QLineEdit = main_window.search_panel_new_name_line
        search_panel_url: QLineEdit = main_window.search_panel_url
        new_name: str = search_panel_new_name_line.text()
        url: str = search_panel_url.text()
        assert url.startswith("http")
        table: Optional[Node] = current_search.parent
        assert isinstance(table, Table)
        new_search: Search = Search(new_name, table, current_search, url)
        table.sort()
        collection: Optional[Collection] = current_search.collection
        assert isinstance(collection, Collection)
        collection.url_insert(new_search)
        new_search.xml_file_save()
        bom_gui.update()

    # BomGui.search_panel_name_line_changed():
    # @trace(1)
    def search_panel_new_name_line_changed(self, text: str) -> None:
        bom_gui: BomGui = self
        # current_search: Optional[Search] = bom_gui.current_search
        # print(f"{tracing}text='{text}'")
        bom_gui.update()

    # BomGui.search_panel_remove_clicked():
    @trace(1)
    def search_panel_remove_clicked(self) -> None:
        bom_gui: BomGui = self
        current_search: Optional[Search] = bom_gui.current_search
        assert isinstance(current_search, Search)
        tracing: str = tracing_get()
        if tracing:
            print("******************************************************************************")
        collection: Optional[Collection] = current_search.collection
        assert isinstance(collection, Collection)
        current_search.file_delete()
        current_search_name: str = current_search.name
        collection.search_remove(current_search_name)
        assert collection.search_find(current_search_name) is None
        table: Optional[Node] = current_search.parent
        assert isinstance(table, Table)
        table.child_remove(current_search)
        table_searches: List[Node] = table.children_get()
        table_search: Node
        for table_search in table_searches:
            assert isinstance(table_search, Search)
            assert table_search is not current_search, "Somehow the current search is not deleted"
        bom_gui.current_search = None
        bom_gui.current_node = None
        bom_gui.update()

    # BomGui.search_panel_rename_clicked():
    @trace(1)
    def search_panel_rename_clicked(self) -> None:
        bom_gui: BomGui = self
        bom_gui.update()

    # BomGui.search_panel_update():
    @trace(1)
    def search_panel_update(self, search: Search) -> None:
        # Force the *panel_search* stacked widget to be displayed by *bom_gui* (i.e. *self*):
        bom_gui: BomGui = self
        main_window: QMainWindow = bom_gui.main_window
        panels: QStackedWidget = main_window.panels
        search_panel: QWidget = main_window.search_panel
        panels.setCurrentWidget(search_panel)

        # As a sanity check, ensure that the *current_search* in *bom_gui* is correct*:
        assert bom_gui.current_search is search

        # *search_panel_type* does not need to be updated, since it never changes:
        # search_panel_type: QLable = main_window.search_panel_type

        # Update the *search_panel_name*:
        search_panel_name: QLabel = main_window.search_panel_name
        search_panel_name.setText(f"Name: {search.name}")

        # Update *search_panel_parent_name*:
        search_parent: Optional[Search] = search.search_parent
        parent_name_text: str = "" if search_parent is None else search_parent.name
        main_window.search_panel_parent_name.setText(f"Parent Name: {parent_name_text}")

        # Update the *search_panel_children_counts:
        search_panel_children_counts: QLabel = main_window.search_panel_children_counts
        immediate_children: int
        all_children: int
        immediate_children, all_children = search.children_count()
        search_panel_children_counts.setText(f"Children: Immediate={immediate_children} "
                                             f"All={all_children}")

        # *search_panel_url_send*, *search_panel_get* do not need since they are always active:
        # search_panel_url_get: QPushButton = main_window.search_panel_url_get
        # search_panel_url_send: QPushButton = main_window.search_panel_url_send

        # Compute *search_panel_new_enable* and *search_panel_why_text*:
        # url: str = main_window.search_panel_url.text()
        search_name: str = search.name
        new_enable: bool = False
        new_name: str = main_window.search_panel_new_name_line.text()
        new_why: str = "?"
        rename_enable: bool = False
        rename_why: str = "?"
        if new_name == "":
            # Empty search names are not acceptable:
            new_why = rename_why = "No Search Name"
        elif new_name == "@ALL":
            # '@ALL' is not allowed:
            new_why = rename_why = "@ALL Reserved"
        else:
            # First verify that *search_name* does not match any of the *search* siblings:
            table: Optional[Node] = search.parent
            assert isinstance(table, Table)
            siblings: List[Node] = table.children_get()
            sibling: Node
            for sibling in siblings:
                if sibling.name == new_name:
                    new_why = rename_why = "Local Duplicate"
                    break
            else:
                # Now make sure there is no matching search in the overall *collection*:
                collection: Optional[Collection] = search.collection
                assert isinstance(collection, Collection)
                prior_search: Optional[Search] = collection.searches_find(new_name)
                if prior_search is None:
                    # There are no matches for *new_name*.  Now verify that there is no
                    # URL conflict:
                    url: str = main_window.search_panel_url.text()
                    if url.startswith("http"):
                        # *url* appears to be kind of valid; now figure out if it is
                        # already in use:
                        url_search: Optional[Search] = collection.url_find(url)
                        if url_search is None:
                            # *url* is not used by another search:
                            new_enable = rename_enable = True
                            new_why = rename_why = "Search Name OK"
                        else:
                            new_why = f"URL matches '{url_search.name}'"
                            rename_enable = True
                            rename_why = "Search Name OK"
                    else:
                        # URL appears to be invalid:
                        url_text = url if len(url) < 10 else url[:10] + "..."
                        new_why = f"Invalid URL '{url_text}'"
                        rename_enable = True
                        rename_why = "Search Name OK"
                else:
                    new_why = rename_why = "Global Duplicate"
        tracing: str = tracing_get()
        if tracing:
            print(f"{tracing}new_enable={new_enable}")
            print(f"{tracing}rename_enable={rename_enable}")
            print(f"{tracing}new_why='{new_why}'")
            print(f"{tracing}rename_whye='{rename_why}'")
        main_window.search_panel_new.setEnabled(new_enable)
        main_window.search_panel_new_why.setText(new_why)
        main_window.search_panel_rename.setEnabled(rename_enable)
        main_window.search_panel_rename_why.setText(rename_why)

        remove_enable: bool = False
        remove_why: str = "@ALL Reserved"
        if search_name != "@ALL":
            remove_enable = True
            remove_why = "Remove Allowed"
        main_window.search_panel_remove.setEnabled(remove_enable)
        main_window.search_panel_remove_why.setText(remove_why)

        # Force the visual update of *search_panel* widget:
        search_panel.update()

    # BomGui.search_panel_url_get_clicked():
    @trace(1)
    def search_panel_url_get_clicked(self):
        # Grab some values from *bom_gui* (i.e. *self*):
        bom_gui: BomGui = self
        current_search: Optional[Search] = bom_gui.current_search
        main_window: QMainWindow = bom_gui.main_window
        application: QApplication = bom_gui.application
        application_clipboard: QClipboard = application.clipboard()

        # As a sanity check, make sure *current_search* is valid:
        assert isinstance(current_search, Search)

        # Now grab both the *selection* and *clipboard* via *application_clipboard*:
        selection: str = application_clipboard.text(QClipboard.Selection)
        clipboard: str = application_clipboard.text(QClipboard.Clipboard)

        # Decide whether we got a reasonble looking *url*:
        url: str = ""
        if selection.startswith("http"):
            url = selection
        elif clipboard.startswith("http"):
            url = clipboard
        tracing: str = tracing_get()
        if tracing:
            print(f"{tracing}clipbboard='{clipboard}'")
            print(f"{tracing}selection='{selection}'")
            print(f"{tracing}url='{url}'")

        # Now update the *search_panel_url*:
        search_panel_url: QLineEdit = main_window.search_panel_url
        search_panel_url.setText(url)
        search_panel_url.setCursorPosition(0)

        # Force an update of the entire *bom_gui*:
        bom_gui.update()

    # BomGui.search_panel_url_send_clicked():
    @trace(1)
    def search_panel_url_send_clicked(self):
        bom_gui: BomGui = self
        current_search: Optional[Search] = bom_gui.current_search
        assert isinstance(current_search, Search)

        # Force the *url* to open in the web browser:
        url: str = current_search.url
        webbrowser.open(url, new=0, autoraise=True)

    # BomGui.tab_changed():
    def tab_changed(self, new_index: int) -> None:
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
    @trace(1)
    def table_clicked(self, table: Table) -> None:
        # Grab some values from *BomGui*:
        bom_gui: BomGui = self
        bom_gui.current_directory = table.parent
        bom_gui.current_node = table
        bom_gui.current_table = table
        bom_gui.current_search = None
        bom_gui.current_collection = table.collection

        # Force whatever is visible to be updated:
        bom_gui.update()

    def table_is_active(self) -> bool:
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

    # BomGui.table_panel_update():
    def table_panel_update(self, table: Table) -> None:
        # Force the *panel_directory* stacked widget to be shown by *bom_gui* (i.e. *self*):
        bom_gui: BomGui = self
        main_window: QMainWindow = bom_gui.main_window
        panels: QStackedWidget = main_window.panels
        table_panel: QWidget = main_window.table_panel
        panels.setCurrentWidget(table_panel)

        # As a sanity check, make sure that the *current_table* in *bom_gui* is correct:
        assert bom_gui.current_table is table

        # Now update the *panel_table_name*:
        table_panel_name: QLabel = main_window.table_panel_name
        name_text = f"Name: {table.name}"
        table_panel_name.setText(name_text)

    # BomGui.table_setup():
    def table_setup(self) -> None:
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
    def update(self) -> None:
        bom_gui: BomGui = self

        # Only update the visible tabs based on *tree_tabs_index*:
        main_window: QMainWindow = bom_gui.main_window
        tree_tabs: QTabWidget = main_window.tree_tabs
        tree_tabs_index: int = tree_tabs.currentIndex()
        if tree_tabs_index == 0:
            bom_gui.collections_update()
        else:
            assert False, "Illegal tab index: {0}".format(tree_tabs_index)

        # Update the *panels* stacked widget:
        bom_gui.panels_update()

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
    def __init__(self) -> None:
        # Initialize the parent *QAbstraceItemModel*:
        super().__init__()

        # Stuff values into *tree_model* (i.e. *self*):
        # tree_model: TreeModel = self
        self.headers: Dict[int, str] = {0: "Type", 1: "Name"}
        self.collections: Optional[Collections] = None
        # self.tracing: str = tracing

    # TreeMode.__str__():
    def __str__(self) -> str:
        return "TreeModel()"

    # check if the node has data that has not been loaded yet
    # TreeModel.canFetchMore():
    def canFetchMore(self, model_index: QModelIndex) -> bool:
        # We delegate the decision of whether we can fetch more stuff to the *node*
        # associated with *model_index*:
        tree_model: TreeModel = self
        node: Node = tree_model.getNode(model_index)
        can_fetch_more: bool = node.can_fetch_more()
        return can_fetch_more

    # TreeModel.collections_set():
    def collections_set(self, collections: Collections):
        # Stuff *collections* into *tree_model* (i.e. *self*):
        tree_model: TreeModel = self
        tree_model.collections = collections

    # TreeModel.columnCount():
    def columnCount(self, model_index: QModelIndex) -> int:
        return 2

    # TreeModel.data():
    # @trace(1)
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
    def delete(self, model_index: QModelIndex) -> None:
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
    def fetchMore(self, model_index: QModelIndex) -> None:
        # Delegate fetching to the *node* associated with *model_index*:
        tree_model: TreeModel = self
        node: Node = tree_model.getNode(model_index)
        node.fetch_more()

    # TreeModel.getNode():
    def getNode(self, model_index: QModelIndex) -> Node:
        tree_model: TreeModel = self
        node: Node = (model_index.internalPointer() if model_index.isValid()
                      else tree_model.collections)
        assert isinstance(node, Node), f"node.type={type(node)}"
        return node

    # TreeModel.hasChildren():
    def hasChildren(self, model_index: QModelIndex) -> bool:
        # Delegate to *has_children*() method to *node*:
        tree_model: TreeModel = self
        node: Node = tree_model.getNode(model_index)
        has_children: bool = node.has_children()
        return has_children

    # TreeModel.headerData():
    def headerData(self, section: int, orientation: Qt.Orientation, role: int) -> Optional[str]:
        tree_model: TreeModel = self
        header_data: Optional[str] = (tree_model.headers[section]
                                      if orientation == Qt.Horizontal and role == Qt.DisplayRole
                                      else None)
        return header_data

    # TreeModel.flags():
    def flags(self, model_index: QModelIndex) -> int:
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
    def children_update(self, parent_model_index: QModelIndex) -> None:
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
                    parent_model_index: QModelIndex = QModelIndex()) -> bool:
        tree_model: TreeModel = self
        node: Node = tree_model.getNode(parent_model_index)

        tree_model.beginInsertRows(parent_model_index, position, position + len(nodes) - 1)

        child: Node
        for child in reversed(nodes):
            node.child_insert(position, child)

        tree_model.endInsertRows()

        return True

    # TreeModel.parent():
    def parent(self, model_index: QModelIndex) -> QModelIndex:
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
    def rowCount(self, parent: QModelIndex) -> int:
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
