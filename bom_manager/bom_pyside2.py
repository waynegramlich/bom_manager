# BOM Manager GUI
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

from bom_manager.node_view import (BomManager, Collection, Directory, Group, Node)
from bom_manager.node_view import (Search, Table, View, ViewSelect)
from pathlib import Path
# Lots of classes/types are imported from various portions of PySide2:
from PySide2.QtUiTools import QUiLoader                                               # type: ignore
# from PySide2.QtWidgets import (QApplication, QLabel, QLineEdit, QMainWindow)        # type: ignore
from PySide2.QtWidgets import (QApplication, QMainWindow)                             # type: ignore
from PySide2.QtWidgets import (QTreeView,)                                            # type: ignore
from PySide2.QtCore import (QAbstractItemModel, QCoreApplication, QFile)              # type: ignore
# from PySide2.QtCore import (QItemSelectionModel, QModelIndex, Qt)                   # type: ignore
from PySide2.QtCore import (QModelIndex, Qt)                                          # type: ignore
from typing import (Any, Dict, List, Optional, Tuple)
from bom_manager.tracing import trace, trace_level_set  # Tracing decorator module:
import sys

# main():
@trace(2)
def main() -> int:
    """Fire up the BOM manager GUI. """

    # Create the *bom_manager*:
    bom_manager: BomManager = BomManager()

    # Create the *root_group*:
    root_group: Group = Group(bom_manager, "Root")

    # Find the *searches_root*.  This code is incomplete.  There needs to be a way
    # to specify the *searches_root* from the command line:
    current_working_directory: Path = Path.cwd()
    searches_root: Path = current_working_directory / "searches"
    assert searches_root.is_dir(), f"{searches_root} does not exist"

    # Now scan for collections and add them into *root_group*:
    root_group.packages_scan(searches_root)

    # Do some paranoid checking that will break as soon as there is more than one *Collection*
    # plugin:
    root_sub_groups: List[Group] = root_group.sub_groups_get(False)
    assert len(root_sub_groups) == 1
    electronics_group: Group = root_sub_groups[0]
    assert electronics_group.name == "Electronics"
    electronics_collections: List[Collection] = electronics_group.collections_get(False)
    assert len(electronics_collections) == 1
    digikey_collection: Collection = electronics_collections[0]
    assert digikey_collection.name == "Digi-Key"

    # Force a partial load of *digikey_collection*:
    digikey_collection.load_recursively(True)

    trace_level_set(2)

    bom_pyside2: BomPyside2 = BomPyside2(bom_manager, root_group)

    bom_pyside2.run()

    return 0


# BomPyside2:
@trace(2)
class BomPyside2(QMainWindow):
    """Contains global GUI information."""

    # BomPyside2.__init__()
    def __init__(self, bom_manager: BomManager, root_group: Group) -> None:
        """Initialize the BOM Manager Graphical User Interface.

        Args:
            *bom_manager* (*BomManager*): The root of all basic data structures.
            *root_group* (*Group*): The root group of the basic data structures:
        """
        # Create the *application* first.  The call to *setAttribute* makes a bogus
        # warning message printout go away:
        QCoreApplication.setAttribute(Qt.AA_ShareOpenGLContexts)
        application: QApplication = QApplication(sys.argv)

        # Compute the path to the user interface file (i.e. `bom_pyside2.ui`) and create
        # *ui_q_file* (which is a *QFile* object):
        module_file_name: str = __file__
        module_file_path: Path = Path(module_file_name)
        print(f"module_file_path={module_file_path}")
        module_directory: Path = module_file_path.parent
        ui_file_path: Path = module_directory / "bom_pyside2.ui"
        ui_q_file: QFile = QFile(f"{ui_file_path}")
        print(f"ui_file_path={ui_file_path}")

        # Now load *ui_q_file* and get the *main_window*:
        q_ui_loader: QUiLoader = QUiLoader()
        main_window: QMainWindow = q_ui_loader.load(ui_q_file)
        mw: QMainWindow = main_window

        # Create the *collections_tree_model*:
        group_view_selects: Tuple[ViewSelect, ...]
        group_view_selects = (ViewSelect(Group, Group.key_from_node),
                              ViewSelect(Collection, Collection.key_from_node))
        collection_view_selects: Tuple[ViewSelect, ...]
        collection_view_selects = (ViewSelect(Directory, Directory.key_from_node),)
        directory_view_selects: Tuple[ViewSelect, ...]
        directory_view_selects = (ViewSelect(Directory, Directory.key_from_node),
                                  ViewSelect(Table, Table.key_from_node))
        table_view_selects: Tuple[ViewSelect, ...]
        table_view_selects = (ViewSelect(Search, Search.key_from_node),)

        collections_view: View = View("Collections", root_group, {
            Group: group_view_selects,
            Collection: collection_view_selects,
            Directory: directory_view_selects,
            Table: table_view_selects,
        })
        collections_tree_model: TreeModel = TreeModel(collections_view)

        # Attatch *collections_tree_model* to *collecdtions_tree*:n
        collections_tree: QTreeView = mw.collections_tree
        collections_tree.setModel(collections_tree_model)
        root_model_index: QModelIndex = collections_tree_model.createIndex(0, 0, root_group)
        collections_tree.setRootIndex(root_model_index)
        collections_tree.setSortingEnabled(True)

        # Load some values into *bom_pyside2* (i.e. *self*):
        # bom_pyside2: BomPyside2 = self
        self.application: QApplication = application
        self.main_window: QMainWindow = main_window
        self.root_group: Group = root_group

    # BomPyside2.run()
    def run(self) -> None:
        """Run the Bom Manager GUI program."""
        # Grab some values from *bom_pyside2* (i.e. *self*):
        bom_pyside2: BomPyside2 = self
        main_window: QMainWindow = bom_pyside2.main_window
        application: QApplication = bom_pyside2.application

        # Force *main_window* to be shown*:
        main_window.show()

        # When we are done with *main_window*, we can exit the application:
        sys.exit(application.exec_())


# TreeModel:
class TreeModel(QAbstractItemModel):

    FLAG_DEFAULT = Qt.ItemIsEnabled | Qt.ItemIsSelectable

    # TreeModel.__init__():
    @trace(2)
    @trace(1)
    def __init__(self, view: View) -> None:
        # Initialize the parent *QAbstraceItemModel*:
        super().__init__()

        # Stuff values into *tree_model* (i.e. *self*):
        # tree_model: TreeModel = self
        self.headers: Dict[int, str] = {0: "Type", 1: "Name"}
        self.view: View = view
        # self.collections: Optional[Collections] = None
        # self.tracing: str = tracing

    # TreeModel.__str__():
    def __str__(self) -> str:
        return "TreeModel()"

    # TreeModel.canFetchMore():
    # @trace(1)
    def canFetchMore(self, parent_model_index: QModelIndex) -> bool:
        """Return whether there are children sub-Node's to be fetched.

        This routine returns whether *True* if there are any children
        sub-*Node*'s associated with *parent_model_index* that need can
        be displayed.  *True* is returned if there are 1 or more child
        sub-*Node*'s and *False* for none.  The *View* object
        associated with *tree_model* (i.e. *self*) specifies which of
        the possible sub-*Node* lists associated with
        *parent_model_index* it is interested in displaying.

        Args:
            *parent_model_index* (*QModelIndex*):  The pointer to the
            *parent_node* object to query.

        Returns:
            (*bool*) Returns *True* if there are one or more children
            sub-*Node*'s to be desplayed and *False* for no child
            sub-*Node*'s.

        """
        # Grab some values from *tree_model*:
        tree_model: TreeModel = self
        view: View = tree_model.view

        # Grab *parent_node* from *parent_model_index*:
        parent_node: Optional[Node] = tree_model.node_get(parent_model_index)

        # Dispatch to the *view* object to compute *children_are_fetchable*:
        children_are_fetchable: bool = (False if parent_node is None
                                        else view.can_fetch_more(parent_node))
        return children_are_fetchable

    # TreeModel.columnCount():
    def columnCount(self, model_index: QModelIndex) -> int:
        return 2

    # TreeModel.data():
    @trace(2)
    def data(self, model_index: QModelIndex, role: int) -> Optional[str]:
        """Return data for model index.

        Args:
            *model_index* (*QModelIndex*): The mode index to obtain
                data for.
            *role* (*int*): The kind of data to return.

        Returns:
            (*Optional*[*str*]) Returns either a string of data or
            *None*.

        """
        # Initial return *value* to *None* and override it later if we have a better result.
        value: Optional[str] = None
        if model_index.isValid():
            # row: int = model_index.row()
            column: int = model_index.column()
            node: Node = model_index.internalPointer()
            if role == Qt.DisplayRole:
                if column == 0:
                    value = node.type_letter_get()
                elif column == 1:
                    value = node.name_get()
        return value

    # TreeModel.fetchMore():
    @trace(2)
    def fetchMore(self, model_index: QModelIndex) -> None:
        """Fetch the model index children.

        The Graphical user interface will call this method any time
        the user clicks to expand a parent node in the tree.

        Args:
            *model_index* (*QModelIndex*): The model index of a parent
                *Node* that should some child *Node*'s.

        """
        # fetchmore actually inserts the rows into the tree:
        # # Delegate fetching to the *node* associated with *model_index*:
        # tree_model: TreeModel = self
        # node: Optional[Node] = tree_model.node_get(model_index)
        # if isinstance(node, Node):
        #     node.fetch_more()
        # assert False
        pass

    # TreeModel.hasChildren():
    @trace(2)
    def hasChildren(self, model_index: QModelIndex) -> bool:
        # Delegate to *has_children*() method to the *view*:
        tree_model: TreeModel = self
        view: View = tree_model.view
        node: Optional[Node] = tree_model.node_get(model_index)
        children_available: bool = False if node is None else view.has_children(node)
        return children_available

    # TreeModel.headerData():
    @trace(2)
    def headerData(self, section: int, orientation: Qt.Orientation, role: int) -> Optional[str]:
        tree_model: TreeModel = self
        header_data: Optional[str] = (tree_model.headers[section]
                                      if orientation == Qt.Horizontal and role == Qt.DisplayRole
                                      else None)
        return header_data

    # TreeModel.flags():
    @trace(2)
    def flags(self, model_index: QModelIndex) -> int:
        return TreeModel.FLAG_DEFAULT

    # TreeModel.index():
    @trace(2)
    def index(self, row: int, column: int, parent_model_index: QModelIndex) -> QModelIndex:
        # Grab some values from *tree_model* (i.e. *self*):
        tree_model: TreeModel = self
        view: View = tree_model.view

        # Extract the *parent_node* from *parent_model_index*:
        parent_node: Optional[Node] = tree_model.node_get(parent_model_index)

        # Provided we got a valid *parent_node* fetch the *child_node* and use it
        # to build a valid *child_model_index*; otherwise, return a "null" one:
        child_model_index: QModelIndex
        if parent_node is None:
            child_model_index = QModelIndex()
        else:
            viewable_children_count: int = view.row_count(parent_node)
            if row >= viewable_children_count:
                child_model_index = QModelIndex()
            else:
                child_node: Node = view.child_fetch(parent_node, row)
                child_model_index = tree_model.createIndex(row, column, child_node)
        return child_model_index

    # TreeModel.node_get():
    @trace(2)
    def node_get(self, model_index: QModelIndex) -> Optional[Node]:
        node: Optional[Node] = None
        if model_index.isValid:
            internal_pointer: Any = model_index.internalPointer()
            if isinstance(internal_pointer, Node):
                node = internal_pointer
        return node

    # TreeModel.parent():
    def parent(self, child_model_index: QModelIndex) -> QModelIndex:
        """Return the parent model index.

        Using *child_model_index*, return the appropriate
        *parent_model_index*.  The underlying *Node* for
        *child_model_index* does not have a back pointer to its parent
        *Node* based on the *View*.  Instead, we work from the *View*
        root downwards until we find the parent *Node*.

        Args:
            *child_model* (*QModelIndex*): The *QModelIndex* that
                points to the *Node* in question.

        Returns:
            (*QModelIndex*): Returns the parent *QModelIndex*.

        """
        # Grab some values from *TreeModel* (i.e. *self*):
        tree_model: TreeModel = self
        view: View = tree_model.view
        child_node: Optional[Node] = tree_model.node_get(child_model_index)
        parent_model_index: QModelIndex
        if child_node is None:
            parent_model_index = QModelIndex()
        else:
            parent_node_index: Optional[Tuple[Node, int]] = view.parent_node_get(child_node)
            if parent_node_index is None:
                parent_model_index = QModelIndex()
            else:
                parent_node: Node = parent_node_index[0]
                parent_index: int = parent_node_index[1]
                parent_model_index = tree_model.createIndex(parent_index,
                                                            parent_index, parent_node)
        return parent_model_index

    # Return 0 if there is data to fetch (handled implicitly by check length of child list)
    # TreeModel.rowCount():
    @trace(2)
    def rowCount(self, parent_model_index: QModelIndex) -> int:
        """Return the total number of children for a parent *Node*.

        Using the *View* object associated with *tree_model*
        (i.e. *self*) return a count of the number child sub-*Nodes*
        for the parent *Node* object associated with
        *parent_model_index*. The *View* object specifies which of
        the possible sub-*Nodes* lists in the parent *Node* to count.

        Args:
            *parent_model_index* (*QModelIndex*): A pointer to the
                parent *Node* object.

        Returns:
            (*int*) Returns the total number of children for the
            to display for the parent *Node* object.

        """
        # Grab some values from *tree_model* (i.e. *self*).
        tree_model: TreeModel = self
        view: View = tree_model.view

        # Compute the *row* count provided *parent_node* is valid*:
        parent_node: Optional[Node] = tree_model.node_get(parent_model_index)
        row_count: int = 0 if parent_node is None else view.row_count(parent_node)
        return row_count
