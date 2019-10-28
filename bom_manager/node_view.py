"""Nodes and Views.

Any BOM Manager data structure that can be viewed via a Graphical User Interface (GUI) must
be a sub-class off of the *Node* class.  When a *Node* is visible in the GUI, it has one or
more *View* objects attached to it (one *View* object for each different view of the same
*Node* object.)  A *View* object provides an abstract interface to the appropriate GUI library
(e.g. QT, # WxWidgets, etc.) so that the details of the graphical presentation do not "leak"
into the main data structures.  The command line version of the BOM manager has no need to
load in a graphical user interface library.

The overall model supported by a *View* is a nestable tree of tables.  Each node of
of the tree can be expanded and contracted by clicking on the appropriate expand/contract
icon on the the tree node.  As the underlying *Node* data structures get updated, the
GUI visualization gets updated.

There are two top level global objects:
* *BomManager* (required): There is exactly one instance of the *BomManager* object and it
  contains the root of all BOM Manager data structures.  Every *Node* data structure has
  a back pointer to the *BomManagaer* object.
* *GuiManager* (optional): If there is an active graphical user interface, there is exactly one
  *GuiManager* object instance.  This code is responsible for initializing the graphic
  user interace libarary and managing all of the *View* objects.
The *Node* object has a helper object all *Nodes* which is an unordered list of *Node* objects:
All *Node* objects are sub-classed to contain the actual important data about the node.
"""

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

# <----------------------------------------100 Characters----------------------------------------> #

from bom_manager.bom import Encode
from pathlib import Path
from bom_manager.tracing import trace, tracing_get
from typing import Dict, List, Tuple, Type


class BomManager:
    """Represents the top-level data structurs needed for the BOM Manager."""

    @trace(1)
    def __init__(self) -> None:
        """Initialize the BomManger object."""
        collections_node_template: NodeTemplate = NodeTemplate(Collections, (Collection,),
                                                               {})
        collection_node_template: NodeTemplate = NodeTemplate(Collection, (Directory,),
                                                              {"collection_root": Path,
                                                               "name": str,
                                                               "searches_root": Path})
        directory_node_template: NodeTemplate = NodeTemplate(Directory, (Directory, Table),
                                                             {"name": str})
        table_node_template: NodeTemplate = NodeTemplate(Table, (Parameter, Search),
                                                         {"file_name": Path,
                                                          "name": str})
        parameter_node_template: NodeTemplate = NodeTemplate(Parameter, (),
                                                             {"name": str})
        search_node_template: NodeTemplate = NodeTemplate(Search, (),
                                                          {"file_name": Path,
                                                           "name": str,
                                                           "parent_name": str})
        node_templates: Dict[Type, NodeTemplate] = {
            Collection: collection_node_template,
            Collections: collections_node_template,
            Directory: directory_node_template,
            Parameter: parameter_node_template,
            Table: table_node_template,
            Search: search_node_template
        }

        # Initialize the *bom_manager* (i.e. *self*) attributes:
        self.node_templates: Dict[type, NodeTemplate] = node_templates


# class GuiManager:
#     def __init__(self) -> None:
#         pass


# class View:
#    def __init__(self, gui_manager: GuiManager, name: str, view_nodes: "Tuple[Node, ...]") -> None:
#        # view: View = self
#        self.gui_manager = GuiManager
#        self.name = name
#
#    def __str__(self) -> str:
#        view: View = self
#        name: str = "??"
#        if hasattr(view, "name"):
#            name = view.name
#        return f"View('{name}')"


# Node_Template():
class NodeTemplate:
    """Provide a template for instatiating new *Node* objects."""

    # NodeTemplate.__init__():
    def __init__(self, type: Type, sub_types: Tuple[Type, ...],
                 attributes_table: Dict[str, Type]) -> None:
        """Create a data structure that is used to create *Node*'s.

        Args:
            type (Type): The sub-class of the *Node* being instantiated.
            sub_types (Tuple[Type, ...]): The varaious *Nodes* under the
                instantiated *Node*.
            attributes_table (Dict[str, Type]): A dictionary of the public
                attributes and their required types.

        """
        # node_template: NodeTemplate = self
        self.type: Type = type
        self.sub_types: Tuple[Type, ...] = sub_types
        self.attributes_table: Dict[str, Type] = attributes_table

    # NodeTemplate.attributes_validate():
    def attributes_validate(self, node: "Node") -> None:
        """Recursively validate that a *Node* is correct.

        Args:
            node (Node): The node to check attributes types for.

        """
        node_template: NodeTemplate = self
        attributes_table: Dict[str, Type] = node_template.attributes_table
        attribute_name: str
        desired_attribute_type: Type
        for attribute_name, desired_attribute_type in attributes_table.items():
            attribute_present: bool = hasattr(node, attribute_name)
            assert attribute_present, (f"{node} does not have attribute '{attribute_name}'")
            actual_attribute: Type = getattr(node, attribute_name)
            # This comparison works if *actual_attribute* is a sub-class of
            # *desired_attribtue_type*:
            types_match: bool = isinstance(actual_attribute, desired_attribute_type)
            assert types_match, (f"{node} attribute '{attribute_name}' "
                                 f"has actual type of '{type(actual_attribute)}' "
                                 f"instead of desired type of '{desired_attribute_type}'")


class Node:
    """Represents some data that can be displayed by a GUI."""

    # Node.__init__():
    def __init__(self, bom_manager: BomManager) -> None:
        """Initialize a *Node*.

        Args (BomManager): The object that is used for accessing the
            *NodeTempate* used to initialize the *Node*.

        """
        # Lookup the *node_tempate* for *node* (i.e. *self*) from *bom_manager*:
        node: Node = self
        node_templates: Dict[Type, NodeTemplate] = bom_manager.node_templates
        node_type: Type = type(node)
        assert node_type in node_templates
        node_template: NodeTemplate = node_templates[node_type]

        # Insert a new *nodes* object into *nodes_table* for each *sub_type* in *sub_types*:
        nodes_table: Dict[Type, Nodes] = dict()
        sub_types: Tuple[Type, ...] = node_template.sub_types
        sub_type: Type
        for sub_type in sub_types:
            nodes: Nodes = Nodes(sub_type)
            nodes_table[sub_type] = nodes

        # Initialize the *bom_manager* (i.e. *self*) attributes:
        self.bom_manager: BomManager = bom_manager
        self.nodes_table: Dict[Type, Nodes] = nodes_table

    # Node.__str__():
    def __str__(self) -> str:  # pragma: no cover
        """Place holder method to be subsumed by sub-classes."""
        node: Node = self
        class_name: str = node.__class__.__name__
        assert False, f"{class_name}.__str__() is not implemented yet."

    # Node.attributes_validate():
    def attributes_validate(self) -> None:
        """Validate that all attributes are present and correctly typed."""
        # Look up the *node_template* associated with *node* (i.e. *self*):
        node: Node = self
        bom_manager: BomManager = node.bom_manager
        node_templates: Dict[Type, NodeTemplate] = bom_manager.node_templates
        node_type = type(node)
        assert node_type in node_templates
        node_template: NodeTemplate = node_templates[node_type]

        # Use *node_template* to validate that all of the required attributes of *node* are correct:
        node_template.attributes_validate(node)

    # Node.attributes_validate_recursively():
    def attributes_validate_recursively(self) -> None:
        """Recursivley validate attributes."""
        # First make sure all of the public attributes of *node* (i.e. *self*) both
        # exist and have the correct type:
        node: Node = self
        node.attributes_validate()

        # Next, visit each of the *nodes* and validate them as well:
        nodes_table: Dict[Type, Nodes] = node.nodes_table
        for nodes in nodes_table.values():
            nodes.attributes_validate_recursively()

    # Node.node_insert():
    def node_insert(self, child_node: "Node") -> None:
        """Insert a child node.

        Attach a child node to the current node.  The node must be of a type that expected
        as defined by the appropriate *NodeTemplate*.

        Args:
            child_node (Node): Child *Node* to insert.

        """
        # Verify that *child_node* is allowed to be inserted into *node* (i.e. *self*):
        node: Node = self
        nodes_table: Dict[Type, Nodes] = node.nodes_table
        child_node_type: Type = type(child_node)
        assert child_node_type in nodes_table, (f"node_type={child_node_type}, "
                                                f"nodes_table={nodes_table}")

        # Lookup the appropriate *nodes* object and stuff *child_node* into it:
        nodes: Nodes = nodes_table[child_node_type]
        nodes.insert(child_node)

    # Node.show_lines_append():
    # @trace(1)
    def show_lines_append(self, show_lines: List[str], indent: str, text: str = "") -> None:
        """Recursively append one line for each node.

        For testing purposes, it is desirable to produce a textual
        representation of a tree.  This is the base routine
        generates the representation as a list of strings.
        It is called recursively to generate each additional
        level of tree representation.  This method is sub-classed
        where each sub-class method provides at value for the text
        argument.

        Args:
            show_lines (List[str]): The list that collects the tree
                representation with each line corresponding to a
                tree node.
            indent (str): The prefix string to indent each line by.
            text (Optional str): If present, provides the content
                that identifes a given Node.

        """
        # Append one *show_line* for this *node* (i.e. *self*) to *show_lines*:
        node: Node = self
        node_name: str = node.__class__.__name__
        show_line: str = f"{indent}{node_name}({text})"
        show_lines.append(show_line)

        # Produce a sorted *nodes_list* that has been sorted by the nodes type:
        nodes_table: Dict[Type, Nodes] = node.nodes_table
        nodes_list: List[Nodes] = list(nodes_table.values())
        nodes_list.sort(key=lambda nodes: nodes.sub_node_type.__name__)

        # Finally, recursively visit each *nodes* in *nodes_list* with another indentation level:
        next_indent: str = indent + " "
        for nodes in nodes_list:
            nodes.show_lines_append(show_lines, next_indent)

    # Node.tree_path_find():
    @trace(1)
    def tree_path_find(self, find_node: "Node", path: "List[Node]") -> "List[Node]":
        """Return a tree path to a Node.

        Recursively search to find a node.  When it is found the
        path list is filled in with the resulting path of nodes
        where the first item is the *find_node* and the last item
        is the root the search.

        Args:
            find_node (Node): The node to find in the tree.
            path (List[Node]): The resulting tree path of nodes.

        Returns:
            The path argument as a convenience which contains
            the resulting tree path of nodes.

        """
        node: Node = self
        if node is find_node:
            path.append(node)
        else:
            nodes_table: Dict[Type, Nodes] = node.nodes_table
            for nodes in nodes_table.values():
                nodes.tree_path_find(find_node, path)
                if path:
                    path.append(node)
                    break
        return path


# Collection:
class Collection(Node):
    """Represents a collection of parts tables."""

    # Collection.__init__():
    @trace(1)
    def __init__(self, bom_manager: BomManager, name: str,
                 collection_root: Path, searches_root: Path) -> None:
        """Initialize the Collection.

        Args:
            bom_manager (BomManager): The root of all the data
                structures.
            collection_root (Path): The root directory where the
                collection directories and tables reside.
            searches_root (Path): The root directory of the
                mirror directory structure that contains the
                search related information.

        """
        super().__init__(bom_manager)
        self.name: str = name
        self.collection_root: Path = collection_root
        self.searches_root: Path = searches_root

    # Collection.__str__():
    def __str__(self) -> str:
        """Return a string representation of the Collection."""
        collection: Collection = self
        name: str = "??"
        if hasattr(collection, "name"):
            name = collection.name
        return f"Collection('{name}')"

    # Collection.directory_insert():
    def directory_insert(self, sub_directory: "Directory") -> None:
        """Insert a directory into the Collection."""
        collection: Collection = self
        collection.node_insert(sub_directory)

    # Collection.partial_load():
    @trace(1)
    def partial_load(self) -> None:
        """Perform a partial load of the Collection.

        Recursively visit all of the associated directories, tables,
        and searches and partially load them.  This means that the
        data structure has been created, but the associated `.xml`
        file may not have been read in yet.
        """
        # Grab some values from *collection* (i.e. *self*):
        collection: Collection = self
        bom_manager: BomManager = collection.bom_manager
        collection_name: str = collection.name
        collection_root: Path = collection.collection_root
        searches_root: Path = collection.searches_root

        # Compute the *collection_path* and *searches_path*:
        collection_file_name: str = Encode.to_file_name(collection_name)
        collection_path: Path = collection_root / collection_file_name
        searches_path: Path = searches_root / collection_file_name

        # Perform a little *tracing*:
        tracing: str = tracing_get()
        if tracing:  # pragma: no cover
            print(f"{tracing}collection_name='{collection_name}'")
            print(f"{tracing}collection_root='{collection_root}'")
            print(f"{tracing}searches_root='{searches_root}'")
            print(f"{tracing}collection_path='{collection_path}'")
            print(f"{tracing}searches_path='{searches_path}'")

        assert collection_path.is_dir(), f"'{collection_path}' is not a directory"
        directory_name: str = collection_name
        directory: Directory = Directory(bom_manager, directory_name)
        collection.directory_insert(directory)
        directory.partial_load(collection_path, searches_path)

    # Collection.show_lines_append():
    def show_lines_append(self, show_lines: List[str], indent: str, text: str = "") -> None:
        """See node base class."""
        collection: Collection = self
        text = f"'{collection.name}'"
        super().show_lines_append(show_lines, indent, text=text)


# Collections:
class Collections(Node):
    """Represents a set of Collection objects."""

    # Collections.__init__():
    def __init__(self, bom_manager: BomManager) -> None:
        """Initialize a Collections object.

        Args:
            bom_manager (BomManager): Contains all the root data
                structures.

        """
        super().__init__(bom_manager)

    # Collections.__str__():
    def __str__(self) -> str:
        """Return a string represention of a Collections object."""
        return "Collections()"

    # Collections.collection_insert():
    def collection_insert(self, collection: "Collection") -> None:
        """Insert a collection into a Collections object."""
        collections: Collections = self
        collections.node_insert(collection)

    # Collections.show_lines_get():
    def show_lines_get(self) -> List[str]:
        """Return a list of lines for the Collections object.

        For testing purposes, it is desirable to produce a textual
        representation of a tree.  This is the top level routine
        generates the reprensentation as a list of strings.

        Returns:
            A list of lines, where each line corresponds to one
            node in the tree.  The tree depth is indicated by
            the number preceeding spaces.

        """
        collections: Collections = self
        show_lines: List[str] = list()
        collections.show_lines_append(show_lines, "")
        return show_lines


# Directory:
class Directory(Node):
    """A directory containting either tables or other sub-directores."""

    # Directory.__init__():
    @trace(1)
    def __init__(self, bom_manager: BomManager, name: str) -> None:
        """Initialize a directory.

        Args:
            bom_manager (BomManager): The root of all of the data structures:
            name (str): A non-empty unicode string name.

        """
        super().__init__(bom_manager)
        self.name: str = name

    # Directory.__str__():
    def __str__(self) -> str:
        """Return a string representation of the parameter."""
        # In order to support the *trace* decorator for the *__init__*() method, we can not
        # assume that the *name* attribute exists:
        directory: Directory = self
        name: str = "??"
        if hasattr(directory, "name"):
            name = directory.name
        return f"Directory('{name}')"

    # Directory.directory_insert()
    def directory_insert(self, sub_directory: "Directory") -> None:
        """Insert a sub_directory into a directory."""
        directory: Directory = self
        directory.node_insert(sub_directory)

    # Directory.partial_load():
    @trace(1)
    def partial_load(self, collection_path: Path, searches_path: Path) -> None:
        """Recursively partially load a *Directory*.

        Recursively visit all of the associated directories, tables,
        and searches and partially load them.  This means that the
        data structure has been created, but the associated `.xml`
        file may not have been read in yet.

        Args:
            collection_path (Path): The directory to look for
                sub-directories in.
            searches_path (Path): The directory to eventually look for
                searches in.  This is recursively passed to lower levels
                for doing partial loads of searches.

        """
        # Sweep through the contents of *collection_path* searching for other
        # *sub_directory*'s or *table*'s:
        directory: Directory = self
        bom_manager: BomManager = directory.bom_manager
        sub_path: Path
        for sub_path in collection_path.glob("*"):
            # Compute *sub_path_name* converting "%" notation into charactors:
            sub_path_file_name: str = sub_path.name

            # Dispatch on whether we have a directory or a `.xml` suffix:
            sub_searches_path: Path
            if sub_path.is_dir():
                # *sub_path* is a directory, so we create a *sub_directory* and insert it
                # into *directory*:
                sub_path_name: str = Encode.from_file_name(sub_path_file_name)
                sub_directory: Directory = Directory(bom_manager, sub_path_name)
                directory.directory_insert(sub_directory)

                # Now do a partial load of *sub_directory*:
                sub_searches_path = searches_path / sub_path_file_name
                sub_directory.partial_load(sub_path, sub_searches_path)
            elif sub_path.suffix == ".xml":
                # We have a `.xml` file so we can create a *table* and insert it into *directory*:
                table_stem_file_name: str = sub_path.stem
                table_name: str = Encode.from_file_name(table_stem_file_name)
                table: Table = Table(bom_manager, table_name, sub_path)
                directory.table_insert(table)

                # Now do a partial load of *table*:
                sub_searches_path = searches_path / table_stem_file_name
                table.partial_load(sub_searches_path)

    # Directory.show_lines_append():
    def show_lines_append(self, show_lines: List[str], indent: str, text: str = "") -> None:
        """Recursively append search information to show lines list.

        Args:
            show_lines (List[str]): The list of lines to append to.
            indent (str): The number of space to prepend to each line.
            text (Optional str): The tablename to use.

        """
        directory: Directory = self
        text = f"'{directory.name}'"
        super().show_lines_append(show_lines, indent, text=text)

    # Directory.table_insert():
    def table_insert(self, sub_table: "Table") -> None:
        """Insert a sub table into a directory.

        Args:
            sub_table (Table): The table to insert.

        """
        directory: Directory = self
        directory.node_insert(sub_table)


# Parameter:
class Parameter(Node):
    """Represents a parameter of a parameteric table."""

    # Parameter.__init__():
    def __init__(self, bom_manager: BomManager, name: str) -> None:
        """Initialize a parameter.

        Args:
            bom_manager (BomManager): The root of all of the data structures:
            name (str): A non-empty unicode string name.

        """
        super().__init__(bom_manager)
        assert name, "Empty String!"
        # parameter: Parameter = self
        self.name: str = name

    # Parameter.__str__():
    def __str__(self) -> str:
        """Return a string representation of the parameter."""
        # In order to support the *trace* decorator for the *__init__*() method, we can not
        # assume that the *name* attribute exists:
        parameter: Parameter = self
        name: str = "??"
        if hasattr(parameter, "name"):
            name = parameter.name
        return f"Parameter('{name}')"

    # Parameter.show_lines_append():
    def show_lines_append(self, show_lines: List[str], indent: str, text: str = "") -> None:
        """Recursively append search information to show lines list.

        Args:
            show_lines (List[str]): The list of lines to append to.
            indent (str): The number of space to prepend to each line.
            text (Optional str): The tablename to use.

        """
        parameter: Parameter = self
        text = f"'{parameter.name}'"
        super().show_lines_append(show_lines, indent, text=text)


# Search:
class Search(Node):
    """Information about a parametric search."""

    # Search.__init__():
    def __init__(self, bom_manager: BomManager, name: str, file_name: Path) -> None:
        """Initailize a search object.

        Args:
            bom_manager (BomManager): The root of all of the data structures.
            name (str): A non-empty unicode string.
            file_name (Path): A path to a search `.xml` file.

        """
        # Intialize the super class:
        super().__init__(bom_manager)

        # Do some argument checking before stuffing the values into the *search* object:
        assert name, "Empty name!"
        assert file_name.suffix == ".xml", "No .xml suffix"
        # search: Search = self
        self.file_name: Path = file_name
        self.name: str = name
        self.parent_name: str = ""

    # Search.__str__():
    def __str__(self) -> str:
        """Return a string representation of a search."""
        # In order to support the *trace* decorator for the *__init__*() method, we can not
        # assume that the *name* attribute exists:
        search: Search = self
        name: str = "??"
        if hasattr(search, "name"):
            name = search.name
        return f"Search('{name}')"

    # Search.show_lines_append():
    def show_lines_append(self, show_lines: List[str], indent: str, text: str = "") -> None:
        """Recursively append search information to show lines list.

        Args:
            show_lines (List[str]): The list of lines to append to.
            indent (str): The number of space to prepend to each line.
            text (Optional str): The tablename to use.

        """
        search: Search = self
        text = f"'{search.name}'"
        super().show_lines_append(show_lines, indent, text=text)


# Table:
class Table(Node):
    """Informatation about a parametric table of parts."""

    # Table.__init__():
    def __init__(self, bom_manager: BomManager, name: str, file_name: Path) -> None:
        """Initialize the Table.

        Initializethe table with a *bom_manager*, *name*, and XML
        *file_name* path.

        Args:
            bom_manager (BomManager): The top level data structure that is
                root of all of the trees.
            name (str): The non-empty name of the table.  Can contain *any*
                unicode characters.

        """
        # Initialize the *Node* super-class:
        super().__init__(bom_manager)

        # Verify that *name* is non-empty and stuff everything into *table* (i.e. *self*.)
        # table: Table = self
        assert name, "Empty string!"
        self.name: str = name
        self.file_name: Path = file_name

    # Table.__str__():
    def __str__(self) -> str:
        """Return a string representation of the table."""
        # In order to support the *trace* decorator for the *__init__*() method, we can not
        # assume that the *name* attribute exists:
        table: Table = self
        name: str = "??"
        if hasattr(table, "name"):
            name = table.name
        return f"Table('{name}')"

    @trace(1)
    # Table.partial_load():
    def partial_load(self, searches_path: Path) -> None:
        """Partial load all of the searches from a directory.

        Recursively visit all of the associated searches and
        partially load them.  This means that the search
        data structures have been created, but the associated
        search `.xml` is not read in.  Note that the `.xml`
        associated with the table is not read in either.

        Args:
            searches_path (Path): The path to the directory containing the
                zero, one, or more, search `.xml` files.

        """
        # Make sure *searches_path* is actually a directory:
        if searches_path.is_dir():
            # *searches_path* is an existing directory that may have some search `.xml` files in it.
            # So now we ascan *searches_path* looking for `.xml` files:
            table: Table = self
            bom_manager: BomManager = table.bom_manager
            all_search_encountered: bool = False
            searches_count: int = 0
            search_path: Path
            for search_path in searches_path.glob("*.xml"):
                # We have a *search* `.xml` file:
                search_stem_file_name: str = search_path.stem
                search_name: str = Encode.from_file_name(search_stem_file_name)
                if search_name == "@ALL":
                    all_search_encountered = True
                search: Search = Search(bom_manager, search_name, search_path)
                table.search_insert(search)
                searches_count += 1

            # If we found any search `.xml` files (i.e. *searches_count* >= 1), we need to ensure
            # that search named "@ALL" is created:
            if not all_search_encountered and searches_count:
                all_search: Search = Search(bom_manager, "@ALL", search_path)
                table.search_insert(all_search)

    # Table.parameter.insert():
    def parameter_insert(self, parameter: Parameter) -> None:
        """Insert *parameter* into the table.

        Args:
            parameter (Parameter): The parameter to insert:

        """
        table: Table = self
        table.node_insert(parameter)

    # Table.search_insert():
    def search_insert(self, search: Search) -> None:
        """Insert *search* into the table.

        Args:
            search (Search): The search to insert:

        """
        table: Table = self
        table.node_insert(search)

    # Table.show_lines_append():
    def show_lines_append(self, show_lines: List[str], indent: str, text: str = "") -> None:
        """Recursively append table information to show lines list.

        Args:
            show_lines (List[str]): The list of lines to append to.
            indent (str): The number of space to prepend to each line.
            text (Optional str): The tablename to use.

        """
        # Format *text* to be the table name and pass it to the super class method:
        table: Table = self
        text = f"'{table.name}'"
        super().show_lines_append(show_lines, indent, text=text)


# Nodes:
class Nodes:
    """A list of Node's that all have the same sub-class type."""

    # Nodes.__init__():
    def __init__(self, sub_node_type: Type) -> None:
        """Initialize a *Nodes* object to contain typed sub-nodes.

        Args:
            sub_node_type (Type): The type that all sub-nodes must be.

        """
        # nodes: Nodes = self
        sub_nodes: Dict[int, Node] = dict()
        self.sub_node_type: Type = sub_node_type
        self.sub_nodes: Dict[int, Node] = sub_nodes
        self.nonce: int = 0

    # Nodes.attributes_validate_recursively():
    def attributes_validate_recursively(self) -> None:
        """Recursively validate the attributes."""
        # Sweep through *sub_nodes* recursively validating attributes:
        nodes: Nodes = self
        sub_nodes: Dict[int, Node] = nodes.sub_nodes
        sub_node: Node
        for sub_node in sub_nodes.values():
            sub_node.attributes_validate_recursively()

    # Nodes.insert():
    def insert(self, sub_node: Node) -> None:
        """Insert a sub node into another node.

        Args:
            sub_node (Node): The sub node to insert.

        """
        # Make sure that *sub_node* is the correct *sub_node_type*:
        nodes: Nodes = self
        sub_nodes_type: Type = nodes.sub_node_type
        assert type(sub_node) is sub_nodes_type

        # Make sure that we do not accidentally insert *sub_node* twice:
        sub_nodes: Dict[int, Node] = nodes.sub_nodes
        assert sub_node not in sub_nodes

        # Now insert *sub_node* into *sub_nodes8 with a unique *nonce*:
        nonce: int = nodes.nonce
        sub_nodes[nonce] = sub_node
        nodes.nonce = nonce + 1

    # Nodes.treep_path_find():
    @trace(1)
    def tree_path_find(self, search_node: Node, path: List[Node]) -> List[Node]:
        """Recursively construct a path between to *Nodes*.

        The resulting *path* will have *search_node* as the first *Node* and the
        the tree root *Node* as the last node.

        Args:
            search_node (Node): The node that terminate the search.
            path (List[Node]): The resulting path of *Node*'s.

        Returns:
            Returns input argument *path*.

        """
        # Recursively sweep through *sub_nodes*:
        nodes: Nodes = self
        sub_nodes: Dict[int, Node] = nodes.sub_nodes
        for sub_node in sub_nodes.values():
            sub_node.tree_path_find(search_node, path)
            if path:
                # *search_node* has been found, so we can stop sweeping:
                break
        return path

    # Nodes.show_lines_append():
    # @trace(1)
    def show_lines_append(self, show_lines: List[str], indent: str) -> None:
        """Recursively append line of for each *Node*.

        Args:
            show_lines (List[str]): List to append lines to.

        """
        # Grab some values from *nodes* and create a sorted *tuples_list*:
        nodes: Nodes = self
        sub_nodes: Dict[int, Node] = nodes.sub_nodes
        tuples_list: List[Tuple[int, Node]] = list(sub_nodes.items())
        tuples_list.sort(key=lambda tuple: tuple[0])

        # Sweep through *tuples_list* recursively appending to *show_lines*:
        nonce: int
        sub_node: Node
        for nonce, sub_node in tuples_list:
            sub_node.show_lines_append(show_lines, indent)

    # Nodes.remove():
    # def remove(self, remove_node: Node) -> None:
    #     nodes: Nodes = self
    #     sub_nodes: Dict[int, Node] = nodes.sub_nodes
    #      nonce: int
    #     sub_node: Node
    #     for nonce, sub_node in sub_nodes.items():
    #         if remove_node is sub_node:
    #             del sub_nodes[nonce]
    #             break
    #     else:
    #         assert False
