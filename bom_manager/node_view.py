#!/usr/bin/env python3

# Nodes and Views:
#
# Any BOM Manager data structure that can be viewed via a Graphical User Interface (GUI) must
# be a sub-class off of the *Node* class.  When a *Node* is visible in the GUI, it has one or
# more *View* objects attached to it (one *View* object for each different view of the same
# *Node* object.)  A *View* object provides an abstract interface to the appropriate GUI library
# (e.g. QT, # WxWidgets, etc.) so that the details of the graphical presentation do not "leak"
# into the main data structures.  The command line version of the BOM manager has no need to
# load in a graphical user interface library.
#
# The overall model supported by a *View* is a nestable tree of tables.  Each node of
# of the tree can be expanded and contracted by clicking on the appropriate expand/contract
# icon on the the tree node.  As the underlying *Node* data structures get updated, the
# GUI visualization gets updated.
#
# There are two top level global objects:
# * *BomManager* (required): There is exactly one instance of the *BomManager* object and it
#   contains the root of all BOM Manager data structures.  Every *Node* data structure has
#   a back pointer to the *BomManagaer* object.
# * *GuiManager* (optional): If there is an active graphical user interface, there is exactly one
#   *GuiManager* object instance.  This code is responsible for initializing the graphic
#   user interace libarary and managing all of the *View* objects.
#
# The *Node* object has a helper object all *Nodes* which is an unordered list of *Node* objects:
# All *Node* objects are sub-classed to contain the actual important data about the node.

# <----------------------------------------100 Characters----------------------------------------> #

from bom_manager.bom import Encode
from pathlib import Path
from bom_manager.tracing import trace, tracing_get
from typing import Dict, List, Tuple, Type


class BomManager:
    @trace(1)
    def __init__(self) -> None:
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


class NodeTemplate:
    def __init__(self, type: Type, sub_types: Tuple[Type, ...],
                 attributes_table: Dict[str, Type]) -> None:
        # node_template: NodeTemplate = self
        self.type: Type = type
        self.sub_types: Tuple[Type, ...] = sub_types
        self.attributes_table: Dict[str, Type] = attributes_table

    def attributes_validate(self, node: "Node") -> None:
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
    def __init__(self, bom_manager: BomManager) -> None:
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

    def attributes_validate(self) -> None:
        # Look up the *node_template* associated with *node* (i.e. *self*):
        node: Node = self
        bom_manager: BomManager = node.bom_manager
        node_templates: Dict[Type, NodeTemplate] = bom_manager.node_templates
        node_type = type(node)
        assert node_type in node_templates
        node_template: NodeTemplate = node_templates[node_type]

        # Use *node_template* to validate that all of the required attributes of *node* are correct:
        node_template.attributes_validate(node)

    def attributes_validate_recursively(self) -> None:
        # Look up the *node_template* associated with *node* (i.e. *self*):
        node: Node = self
        node.attributes_validate()
        nodes_table: Dict[Type, Nodes] = node.nodes_table
        for nodes in nodes_table.values():
            nodes.attributes_validate_recursively()

    def node_insert(self, child_node: "Node") -> None:
        node: Node = self
        nodes_table: Dict[Type, Nodes] = node.nodes_table
        child_node_type: Type = type(child_node)
        assert child_node_type in nodes_table, (f"node_type={child_node_type}, "
                                                f"nodes_table={nodes_table}")
        nodes: Nodes = nodes_table[child_node_type]
        nodes.insert(child_node)

    # @trace(1)
    def show_lines_append(self, show_lines: List[str], indent: str, text: str = "") -> None:
        node: Node = self
        node_name: str = node.__class__.__name__
        show_line: str = f"{indent}{node_name}({text})"
        show_lines.append(show_line)

        nodes_table: Dict[Type, Nodes] = node.nodes_table
        nodes_list: List[Nodes] = list(nodes_table.values())
        nodes_list.sort(key=lambda nodes: nodes.type.__name__)
        next_indent: str = indent + " "
        for nodes in nodes_list:
            nodes.show_lines_append(show_lines, next_indent)

    @trace(1)
    def tree_path_find(self, search_node: "Node", path: "List[Node]") -> "List[Node]":
        node: Node = self
        if node is search_node:
            path.append(node)
        else:
            nodes_table: Dict[Type, Nodes] = node.nodes_table
            for nodes in nodes_table.values():
                nodes.tree_path_find(search_node, path)
                if path:
                    path.append(node)
                    break
        return path


class Collection(Node):
    @trace(1)
    def __init__(self, bom_manager: BomManager, name: str,
                 collection_root: Path, searches_root: Path) -> None:
        super().__init__(bom_manager)
        self.name: str = name
        self.collection_root: Path = collection_root
        self.searches_root: Path = searches_root

    def __str__(self) -> str:
        collection: Collection = self
        name: str = "??"
        if hasattr(collection, "name"):
            name = collection.name
        return f"Collection('{name}')"

    def directory_insert(self, sub_directory: "Directory") -> None:
        collection: Collection = self
        collection.node_insert(sub_directory)

    # Collection.partial_load():
    @trace(1)
    def partial_load(self) -> None:
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

    def show_lines_append(self, show_lines: List[str], indent: str, text: str = "") -> None:
        collection: Collection = self
        text = f"'{collection.name}'"
        super().show_lines_append(show_lines, indent, text=text)


class Collections(Node):
    def __init__(self, bom_manager: BomManager) -> None:
        super().__init__(bom_manager)

    def __str__(self) -> str:
        return "Collections()"

    def collection_insert(self, collection: "Collection") -> None:
        collections: Collections = self
        collections.node_insert(collection)

    def show_lines_get(self) -> List[str]:
        collections: Collections = self
        show_lines: List[str] = list()
        collections.show_lines_append(show_lines, "")
        return show_lines


class Directory(Node):
    @trace(1)
    def __init__(self, bom_manager: BomManager, name: str) -> None:
        super().__init__(bom_manager)
        self.name: str = name

    def __str__(self) -> str:
        directory: Directory = self
        name: str = "??"
        if hasattr(directory, "name"):
            name = directory.name
        return f"Directory('{name}')"

    def directory_insert(self, sub_directory: "Directory") -> None:
        directory: Directory = self
        directory.node_insert(sub_directory)

    @trace(1)
    def partial_load(self, collection_path: Path, searches_path: Path) -> None:
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

    def show_lines_append(self, show_lines: List[str], indent: str, text: str = "") -> None:
        directory: Directory = self
        text = f"'{directory.name}'"
        super().show_lines_append(show_lines, indent, text=text)

    def table_insert(self, sub_table: "Table") -> None:
        directory: Directory = self
        directory.node_insert(sub_table)


class Parameter(Node):
    def __init__(self, bom_manager: BomManager, name: str) -> None:
        super().__init__(bom_manager)
        self.name: str = name

    def __str__(self) -> str:
        parameter: Parameter = self
        name: str = "??"
        if hasattr(parameter, "name"):
            name = parameter.name
        return f"Parameter('{name}')"

    def show_lines_append(self, show_lines: List[str], indent: str, text: str = "") -> None:
        parameter: Parameter = self
        text = f"'{parameter.name}'"
        super().show_lines_append(show_lines, indent, text=text)


class Search(Node):
    def __init__(self, bom_manager: BomManager, name: str, file_name: Path) -> None:
        super().__init__(bom_manager)
        self.file_name: Path = file_name
        self.name: str = name
        self.parent_name: str = ""

    def __str__(self) -> str:
        search: Search = self
        name: str = "??"
        if hasattr(search, "name"):
            name = search.name
        return f"Search('{name}')"

    def show_lines_append(self, show_lines: List[str], indent: str, text: str = "") -> None:
        search: Search = self
        text = f"'{search.name}'"
        super().show_lines_append(show_lines, indent, text=text)


class Table(Node):
    def __init__(self, bom_manager: BomManager, name: str, file_name: Path) -> None:
        super().__init__(bom_manager)
        self.name: str = name
        self.file_name: Path = file_name

    def __str__(self) -> str:
        table: Table = self
        name: str = "??"
        if hasattr(table, "name"):
            name = table.name
        return f"Table('{name}')"

    @trace(1)
    def partial_load(self, searches_path: Path) -> None:
        if searches_path.is_dir():
            # *searches_path* is an existing directory that may have some search `.xml` files in it.
            # So now we ascan *searches_path* looking for `.xml` files:
            table: Table = self
            bom_manager: BomManager = table.bom_manager
            all_search_encountered: bool = False
            searches_count: int = 0
            search_path: Path
            for search_path in searches_path.glob("*"):
                if search_path.suffix == ".xml":
                    # We have a *search* `.xml` file:
                    search_stem_file_name: str = search_path.stem
                    search_name: str = Encode.from_file_name(search_stem_file_name)
                    if search_name == "@ALL":
                        all_search_encountered = True
                    search: Search = Search(bom_manager, search_name, search_path)
                    table.search_insert(search)
                    searches_count += 1

            # If we found any search `.xml` files (i.e. *searches_count* >= 1), we need to create
            # an *all_search* named "@ALL":
            if not all_search_encountered and searches_count:
                all_search: Search = Search(bom_manager, "@ALL", search_path)
                table.search_insert(all_search)

    def parameter_insert(self, parameter: Parameter) -> None:
        table: Table = self
        table.node_insert(parameter)

    def search_insert(self, search: Search) -> None:
        table: Table = self
        table.node_insert(search)

    def show_lines_append(self, show_lines: List[str], indent: str, text: str = "") -> None:
        table: Table = self
        text = f"'{table.name}'"
        super().show_lines_append(show_lines, indent, text=text)


class Nodes:
    def __init__(self, type: Type) -> None:
        # nodes: Nodes = self
        sub_nodes: Dict[int, Node] = dict()
        self.type: Type = type
        self.sub_nodes: Dict[int, Node] = sub_nodes
        self.nonce: int = 0

    def attributes_validate_recursively(self) -> None:
        nodes: Nodes = self
        sub_nodes: Dict[int, Node] = nodes.sub_nodes
        sub_node: Node
        for sub_node in sub_nodes.values():
            sub_node.attributes_validate_recursively()

    def insert(self, sub_node: Node) -> None:
        nodes: Nodes = self
        sub_nodes: Dict[int, Node] = nodes.sub_nodes
        nonce: int = nodes.nonce
        sub_nodes[nonce] = sub_node
        nodes.nonce = nonce + 1

    @trace(1)
    def tree_path_find(self, search_node: Node, path: List[Node]) -> List[Node]:
        nodes: Nodes = self
        sub_nodes: Dict[int, Node] = nodes.sub_nodes
        for sub_node in sub_nodes.values():
            sub_node.tree_path_find(search_node, path)
            if path:
                break
        return path

    # @trace(1)
    def show_lines_append(self, show_lines: List[str], indent: str) -> None:
        nodes: Nodes = self
        sub_nodes: Dict[int, Node] = nodes.sub_nodes
        tuples_list: List[Tuple[int, Node]] = list(sub_nodes.items())
        tuples_list.sort(key=lambda tuple: tuple[0])
        nonce: int
        sub_node: Node
        for nonce, sub_node in tuples_list:
            sub_node.show_lines_append(show_lines, indent)

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
