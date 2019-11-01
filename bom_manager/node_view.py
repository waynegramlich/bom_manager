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
from bom_manager.tracing import trace  # , tracing_get
# import csv
from pathlib import Path
# import pkg_resources              # Used to find plug-ins.
import re
from typing import Any, Dict, IO, List, Tuple, Type
from typing import Any as PreCompiled


class BomManager:
    """Contains top-level data structurs needed for the BOM Manager."""

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
        table_node_template: NodeTemplate = NodeTemplate(Table, (Parameter, Search, TableComment),
                                                         {"file_path": Path,
                                                          "name": str})
        table_comment_node_template: NodeTemplate = NodeTemplate(TableComment, (),
                                                                 {"language": str,
                                                                  "lines": list})
        parameter_node_template: NodeTemplate = NodeTemplate(Parameter, (ParameterComment,),
                                                             {"header_index": int,
                                                              "name": str,
                                                              "type_name": str})
        parameter_comment_node_template: NodeTemplate = NodeTemplate(ParameterComment, (),
                                                                     {"language": str,
                                                                      "lines": list})
        search_node_template: NodeTemplate = NodeTemplate(Search, (),
                                                          {"file_path": Path,
                                                           "name": str})

        node_templates: Dict[Type, NodeTemplate] = {
            Collection: collection_node_template,
            Collections: collections_node_template,
            Directory: directory_node_template,
            Parameter: parameter_node_template,
            ParameterComment: parameter_comment_node_template,
            Table: table_node_template,
            TableComment: table_comment_node_template,
            Search: search_node_template
        }

        # Initialize the *bom_manager* (i.e. *self*) attributes:
        re_table: Dict[str, PreCompiled] = dict()
        self.node_templates: Dict[type, NodeTemplate] = node_templates
        self.re_table: Dict[str, PreCompiled] = re_table

        # Initialize *re_table*:
        bom_manager: BomManager = self
        bom_manager.re_table_initialize()

    def re_table_initialize(self):
        """Initialize the BOM manager regular expresstion table."""
        # Construct a bunch of compiled regular expressions:
        si_units_re_text: str = Units.si_units_re_text_get()
        float_re_text: str = "-?([0-9]+\\.[0-9]*|\\.[0-9]+)"
        white_space_text: str = "[ \t]*"
        integer_re_text: str = "-?[0-9]+"
        integer_re: PreCompiled = re.compile(integer_re_text + "$")
        float_re: PreCompiled = re.compile(float_re_text + "$")
        url_re: PreCompiled = re.compile("(https?://)|(//).*$")
        empty_re: PreCompiled = re.compile("-?$")
        funits_re: PreCompiled = re.compile(float_re_text +
                                            white_space_text + si_units_re_text + "$")
        iunits_re: PreCompiled = re.compile(integer_re_text + white_space_text +
                                            si_units_re_text + "$")
        range_re: PreCompiled = re.compile("[^~]+~[^~]+$")
        list_re: PreCompiled = re.compile("([^,]+,)+[^,]+$")

        # Grab *re_table* from *bom_manager* (i.e. *self*) and fill it in:
        bom_manager: BomManager = self
        re_table: Dict[str, PreCompiled] = bom_manager.re_table
        re_table["Empty"] = empty_re
        re_table["Float"] = float_re
        re_table["FUnits"] = funits_re
        re_table["Integer"] = integer_re
        re_table["IUnits"] = iunits_re
        re_table["List"] = list_re
        re_table["Range"] = range_re
        re_table["URL"] = url_re

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
    def __init__(self, node_type: Type, sub_types: Tuple[Type, ...],
                 attributes_table: Dict[str, Type]) -> None:
        """Create a data structure that is used to create *Node*'s.

        Args:
            *node_type* (Type): The sub-class of the *Node* being
                instantiated.
            *sub_types* (Tuple[Type, ...]): The varaious *Nodes*
                allowed under the instantiated *Node*.
            *attributes_table* (Dict[str, Type]): A dictionary of the
                public attributes and their required types.

        """
        # node_template: NodeTemplate = self
        self.node_type: Type = node_type
        self.sub_types: Tuple[Type, ...] = sub_types
        self.attributes_table: Dict[str, Type] = attributes_table

    # NodeTemplate.__str__():
    def __str__(self) -> str:
        """Return a NodeTemplate string representation."""
        # In order to support the *trace* decorator for the *__init__*() method, we can not
        # assume that the *type_name* attribute exists:
        node_template: NodeTemplate = self
        node_type: Type = node_template.node_type
        # assert isinstance(node_type, Node), f"node_type={node_type}"
        node_type_name: str = "??"
        if hasattr(node_template, "node_type"):
            node_type_name = node_type.__name__
        return f"NodeTemplate('{node_type_name}')"

    # NodeTemplate.attributes_validate():
    def attributes_validate(self, node: "Node") -> None:
        """Recursively validate that a *Node* is correct.

        Using the *node_template* (i.e. *self*) verify that *node* has
        all of the correct attribitutes defined and with values that
        are have the correct type.

        Args:
            *node* (Node): The node to check attributes types for.

        """
        # Sweep through the *attributes_table* to validate each attribute:
        node_template: NodeTemplate = self
        attributes_table: Dict[str, Type] = node_template.attributes_table
        attribute_name: str
        desired_attribute_type: Type
        for attribute_name, desired_attribute_type in attributes_table.items():
            # Validate that *attribute_name* exists and has an acceptable type:
            attribute_present: bool = hasattr(node, attribute_name)
            assert attribute_present, (f"{node} does not have attribute '{attribute_name}'")
            actual_attribute: Type = getattr(node, attribute_name)
            # This comparison still works if *actual_attribute* is a sub-class of
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

        Initialize a *Node* using the appropriate *NodeTemplate*
        obtained from *bom_manager*.

        Args:
            *bom_manager* (BomManager): The location of all the
                *NodeTemplate* needed for initialiizing *node*
                (i.e. *self*.)

        """
        # Lookup the *node_tempate* for *node* (i.e. *self*) from *bom_manager*:
        node: Node = self
        node_templates: Dict[Type, NodeTemplate] = bom_manager.node_templates
        node_type: Type = type(node)
        assert node_type in node_templates, f"node_type={node_type} not in node_templates"
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
        nodes: Nodes
        for nodes in nodes_table.values():
            nodes.attributes_validate_recursively()

    # Node.sub_nodes_get():
    def sub_nodes_get(self, sub_node_type: Type) -> "List[Node]":
        """Return the sub-nodes that match a given type.

        Return a list of *Node*'s from *node* (i.e. *self*.)  Each of
        the *Node*'s in the returned list will be of type
        *sub_node_type*.

        Args:
            *sub_node_type* (Type): The type of *Node* to insert into
            the returned list.

        """
        node: Node = self
        nodes_table: Dict[Type, Nodes] = node.nodes_table
        assert sub_node_type in nodes_table, f"Invliad type '{sub_node_type}'"
        nodes: Nodes = nodes_table[sub_node_type]
        sub_nodes_list: List[Node] = nodes.sub_nodes_get()
        return sub_nodes_list

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

    # Node.nodes_get():
    def nodes_get(self, sub_type: Type) -> "Nodes":
        """Return the sub type Nodes object."""
        node: Node = self
        nodes_table: Dict[Type, Nodes] = node.nodes_table
        assert sub_type in nodes_table
        nodes: Nodes = nodes_table[sub_type]
        return nodes

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

    # Node.nodes_collect_recursively():
    def nodes_collect_recursively(self, node_type: Type, nodes_list: "List[Node]") -> None:
        """Recursively find Node's that match a type.

        Sweep down the data structure tree collecting all *Node*'s that
        match *node_type* and append them to *nodes_list8*.

        Args:
            *node_type* (Type): The *Node* type to match.
            *nodes_list* (List[Table]): The *Node*'s list to append each
                matching *Node* to.

        """
        # First, figure out if *node* (i.e. *self*) matches *node_type*:
        node: Node = self
        if isinstance(node, node_type):
            nodes_list.append(node)

        # Now recursively visit all *nodes* from *nodes_table* looking for *node_type*:
        nodes_table: Dict[type, Nodes] = node.nodes_table
        nodes: Nodes
        for nodes in nodes_table.values():
            nodes.nodes_collect_recursively(node_type, nodes_list)


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
        # In order to support the *trace* decorator for the *__init__*() method, we can not
        # assume that the *name* attribute exists:
        collection: Collection = self
        name: str = "??"
        if hasattr(collection, "name"):
            name = collection.name
        return f"Collection('{name}')"

    # Collection.directories_get():
    def directories_get(self, sort: bool) -> "List[Directory]":
        """Return immediate sub directories.

        Return the sub-directories of *collection* (i.e. *self*).  If
        *sort* is *True*, the returned sub-directores are sored by name.

        Args:
            *sort*: If *True* the return list is sorted by directory
                name.

        Returns:
            Returns a list of *Directory* objects, which sorted if
            *sort* is *True*.

        """
        # Get all of the *Directory*'s from *collection* (i.e. *self*) and stuff them
        # into *directory_nodes*:
        collection: Collection = self
        directory_nodes: List[Node] = collection.sub_nodes_get(Directory)

        # This ugly piece of code constructs the *directories* list forcing `mypy` to
        # notice that the each *Node* is, in fact, a *Directory*:
        directories: List[Directory] = list()
        directory: Node
        for directory in directory_nodes:
            assert isinstance(directory, Directory)
            directories.append(directory)

        # Perform any requested *sort* before returning *directories*:
        if sort:
            directories.sort(key=lambda directory: directory.name)
        return directories

    # Collection.directory_insert():
    def directory_insert(self, sub_directory: "Directory") -> None:
        """Insert a directory into the Collection."""
        collection: Collection = self
        collection.node_insert(sub_directory)

    # # Collection.partial_load():
    # @trace(1)
    # def partial_load(self) -> None:
    #     """Perform a partial load of the Collection.

    #     Recursively visit all of the associated directories, tables,
    #     and searches and partially load them.  This means that the
    #     data structure has been created, but the associated `.xml`
    #     file may not have been read in yet.
    #     """
    #     # Grab some values from *collection* (i.e. *self*):
    #     collection: Collection = self
    #     bom_manager: BomManager = collection.bom_manager
    #     collection_name: str = collection.name
    #     collection_root: Path = collection.collection_root
    #     searches_root: Path = collection.searches_root

    #     # Compute the *collection_path* and *searches_path*:
    #     collection_file_name: str = Encode.to_file_name(collection_name)
    #     collection_path: Path = collection_root
    #     searches_path: Path = searches_root / collection_file_name

    #     # Perform a little *tracing*:
    #     tracing: str = tracing_get()
    #     if tracing:  # pragma: no cover
    #         print(f"{tracing}collection_name='{collection_name}'")
    #         print(f"{tracing}collection_root='{collection_root}'")
    #         print(f"{tracing}searches_root='{searches_root}'")
    #         print(f"{tracing}collection_path='{collection_path}'")
    #         print(f"{tracing}searches_path='{searches_path}'")

    #     assert collection_path.is_dir(), f"'{collection_path}' is not a directory"
    #     directory_name: str = collection_name
    #     directory: Directory = Directory(bom_manager, directory_name)
    #     collection.directory_insert(directory)
    #     directory.partial_load(collection_path, searches_path)

    # Collection.show_lines_append():
    def show_lines_append(self, show_lines: List[str], indent: str, text: str = "") -> None:
        """See node base class."""
        collection: Collection = self
        text = f"'{collection.name}'"
        super().show_lines_append(show_lines, indent, text=text)

    # Collection.xml_lines_append():
    def xml_lines_append(self, xml_lines: List[str], indent: str, extra_attributes: str) -> None:
        """Append XML for *Collection* to a list.

        Append the XML description of *collection* (i.e. *self*) to the *xml_lines* list.
        Each line is prefixed by *indent*.  The initial element will have *extra_attributes*
        added to it.

        Args:
            *xml_lines*: *List*[*str*]: List of line to append individual XML lines to.
            *indent* (*str*): A prefix prepended to each line.
            *extra_attributes*: Some extra attributes to add to the *Collection* element.

        """
        # Output initiial element:
        collection: Collection = self
        collection_type_name: str = collection.__class__.__name__
        name: str = collection.name
        xml_lines.append(f'<{collection_type_name} name="{name}"{extra_attributes}>')

        # Now output the sorted *directories*:
        next_indent: str = indent + "  "
        directories: List[Directory] = collection.directories_get(True)
        directory: Directory
        for directory in directories:
            directory.xml_lines_append(xml_lines, next_indent)

        # Output the closing element:
        xml_lines.append(f'</{collection_type_name}>')


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

    # Collections.show_lines_file_write():
    def show_lines_file_write(self, file_path: Path, indent: str) -> None:
        """Write *Collections* out to file in show lines format.

        Generate a list of lines in show line format for the
        *Collections* object (i.e. *self*).  Output this list of show
        lines to *file_path* with each line prefixed by *indent*.

        Args:
            *file_path* (Path): The file to write out to.
            *indent* (str): A string to prepend to each line.

        """
        collections: Collections = self
        show_lines: List[str] = collections.show_lines_get()
        show_lines_text: str = "".join([f"{indent}{show_line}\n" for show_line in show_lines])
        show_lines_file: IO[Any]
        with file_path.open("w") as show_lines_file:
            show_lines_file.write(show_lines_text)

    # # Collections.packages_scan():
    # def packages_scan(self):
    #     """Scan for collection packages."""
    #     collections: Collections = self
    #     bom_manager: BomManager = collections.bom_manager
    #     tracing: str = tracing_get()
    #     entry_point_key: str = "bom_manager_collection_get"
    #     index: int
    #     entry_point: pkg_resources.EntryPoint
    #     for index, entry_point in enumerate(pkg_resources.iter_entry_points(entry_point_key)):
    #         entry_point_name: str = entry_point.name
    #         if tracing:
    #             print(f"{tracing}Collection_Entry_Point[{index}]: '{entry_point_name}'")
    #         assert entry_point_name == "collection_get"
    #         collection_get: Callable[[], Collection] = entry_point.load()
    #         assert callable(collection_get)
    #         collection: Collection = collection_get(bom_manager)
    #         assert isinstance(collection, Collection)
    #         collections.collection_insert(collection)


# Comment:
class Comment(Node):
    """Represents a comment from an XML file."""

    # Comment.__init__():
    def __init__(self, bom_manager: BomManager, language: str) -> None:
        """Initialize a *Comment*.

        Initialize a *Comment* object (i.e. *self*) to reference
        *bom_manager* and specify the 2 character IS)-639 *language*
        code.  Lines are added to the comment using the
        *Comment*.*lines_set*() or *Comment*.*line_append*() methods.

        Args:
            *bom_manager* (*BomManager*): The root of all data
                structures.
            *language* (*str*): A two character ISO-639 language code.

        """
        super().__init__(bom_manager)
        # comment: Comment = self
        assert language, "Empty language for comment"
        self.language: str = language
        self.lines: List[str] = list()

    # Comment.__str__():
    def __str__(self):
        """Return a string representation."""
        # In order to support the *trace* decorator for the *__init__*() method, we can not
        # assume that the *language* attribute exists:
        comment: Comment = self
        language: str = "??"
        if hasattr(comment, "language"):
            language = comment.language
        class_name: str = comment.__class__.__name__
        return f"{class_name}('{language}')"

    # Comment.line_append():
    def line_append(self, line: str) -> None:
        """Append a line to a comment.

        Append *line* to *comment* (i.e. *self*).  *line* have new-line
        characters stripped and white space trimmed from front and back.

        Args:
            *line* (*str*): One line of of text to append.

        """
        comment: Comment = self
        lines: List[str] = comment.lines
        lines.append(line.strip().replace('\n', ""))

    # Comment.lines_set():
    def lines_set(self, lines: List[str]) -> None:
        """Set the *Comment* *lines*.

        Replace the lines for *comment* (i.e. *self*) with *lines*
        Each line in *lines* has any new-line characters removed
        and white space trimmed from front and back.

        Args:
            *lines* (*List*[*str*]): The list of lines to install.

        """
        comment: Comment = self
        comment.lines = [line.strip().replace('\n', "") for line in lines]

    # Comment.key()
    def key(self) -> str:
        """Return a sorting key."""
        comment: Comment = self
        return comment.language

    # Comment.xml_lines_append():
    def xml_lines_append(self, xml_lines: List[str], indent: str):
        """Append XML to XML lines list.

        Append appropriate XML lines for *comment* (i.e. self*) to
        *xml_lines* where each line is prefixed by *indent*.

        Args:
            *xml_lines* (*List*[*str*]): List of lines to append to.
            *indent* (*str*): Prefix for each line.

        """
        # Start with the opening `<Comment ...>` for *comment (i.e. *self*):
        comment: Comment = self
        comment_class_name = comment.__class__.__name__
        language: str = comment.language
        xml_lines.append(f'{indent}<{comment_class_name} language="{language}">')

        # Append each *line* from *lines* to *xml_lines* indented by *next_indent*:
        lines: List[str] = comment.lines
        line: str
        next_indent: str = indent + "  "
        for line in lines:
            xml_lines.append(f'{next_indent}{line}')

        # End with the closing `</Comment>`:
        xml_lines.append(f'{indent}</{comment_class_name}">')


# TableComment:
class TableComment(Comment):
    """Rrepresents a comment for a Table."""

    # TableComment.__init__():
    def __init__(self, bom_manager: BomManager, language: str) -> None:
        """See *Comment* base class."""
        super().__init__(bom_manager, language)

    # TableComment.show_lines_append():
    def show_lines_append(self, show_lines: List[str], indent: str, text: str = "") -> None:
        """Recursively append table comment info. to show lines list.

        Args:
            show_lines (List[str]): The list of lines to append to.
            indent (str): The number of space to prepend to each line.
            text (Optional str): The tablename to use.

        """
        table_comment: TableComment = self
        language: str = table_comment.language
        super().show_lines_append(show_lines, indent, f"'{language}'")


# ParameterComment:
class ParameterComment(Comment):
    """Represents a parameter comment from a Table XML file."""

    # ParameterComment.__init__():
    def __init__(self, bom_manager: BomManager, language: str) -> None:
        """See *Comment* base class."""
        super().__init__(bom_manager, language=language)

    # ParameterComment.show_lines_append():
    def show_lines_append(self, show_lines: List[str], indent: str, text: str = "") -> None:
        """Recursively append parameter comment info. to lines list.

        Args:
            show_lines (List[str]): The list of lines to append to.
            indent (str): The number of space to prepend to each line.
            text (Optional str): The tablename to use.

        """
        parameter_comment: ParameterComment = self
        language: str = parameter_comment.language
        super().show_lines_append(show_lines, indent, f"'{language}'")


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

    # # Directory.partial_load():
    # @trace(1)
    # def partial_load(self, collection_path: Path, searches_path: Path) -> None:
    #     """Recursively partially load a *Directory*.

    #     Recursively visit all of the associated directories, tables,
    #     and searches and partially load them.  This means that the
    #     data structure has been created, but the associated `.xml`
    #     file may not have been read in yet.

    #     Args:
    #         collection_path (Path): The directory to look for
    #             sub-directories in.
    #         searches_path (Path): The directory to eventually look for
    #             searches in.  This is recursively passed to lower levels
    #             for doing partial loads of searches.

    #     """
    #     # Sweep through the contents of *collection_path* searching for other
    #     # *sub_directory*'s or *table*'s:
    #     directory: Directory = self
    #     bom_manager: BomManager = directory.bom_manager
    #     sub_path: Path
    #     for sub_path in collection_path.glob("*"):
    #         # Compute *sub_path_name* converting "%" notation into charactors:
    #         sub_path_file_name: str = sub_path.name

    #         # Dispatch on whether we have a directory or a `.xml` suffix:
    #         sub_searches_path: Path
    #         if sub_path.is_dir():
    #             # *sub_path* is a directory, so we create a *sub_directory* and insert it
    #             # into *directory*:
    #             sub_path_name: str = Encode.from_file_name(sub_path_file_name)
    #             sub_directory: Directory = Directory(bom_manager, sub_path_name)
    #             directory.directory_insert(sub_directory)

    #             # Now do a partial load of *sub_directory*:
    #             sub_searches_path = searches_path / sub_path_file_name
    #             sub_directory.partial_load(sub_path, sub_searches_path)
    #         elif sub_path.suffix == ".xml":
    #             # We have a `.xml` file so we can create a *table* and insert it into *directory*:
    #             table_stem_file_name: str = sub_path.stem
    #             table_name: str = Encode.from_file_name(table_stem_file_name)
    #             table: Table = Table(bom_manager, table_name, sub_path)
    #             directory.table_insert(table)

    #             # Now do a partial load of *table*:
    #             sub_searches_path = searches_path / table_stem_file_name
    #             table.partial_load(sub_searches_path)

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

    # Directory.tables_get():
    def tables_get(self, sort: bool) -> "List[Table]":
        """Return directory tables.

        Return a list of *Table*'s associated with *directory
        (i.e. *self*.)  If *sort* is *True*, the returned list
        is sorted by table name.

        Args:
            *sort* (*bool*): If *True*, the returned tables sorted by
                table name.

        Returns:
            Returns a list of *Table*'s that are sorted if *sort*
            is *True*:

        """
        # Extract *tables_nodes* from *directory* (i.e. *self*):
        directory: Directory = self
        table_nodes: List[Node] = directory.sub_nodes_get(Table)

        # To make `my_py` happy, convert *table_nodes* from a list of *Node*s to
        # *tables* which is a list of *Table*'s:
        tables: List[Table] = list()
        table: Node
        for table in table_nodes:
            assert isinstance(table, Table)
            tables.append(table)

        # Perform any request *sort* before returning *tables*:
        if sort:
            tables.sort(key=lambda table: table.name)
        return tables

    # Directory.sub_directories_get():
    def sub_directories_get(self, sort: bool) -> "List[Directory]":
        """Return directory sub-directories.

        Return a list of sub *Directory*'s associated with *directory*
        (i.e. *self*.)  If *sort* is *True*, the returned list
        is sorted by sub-directory name.

        Args:
            *sort* (*bool*): If *True*, the returned tables sorted by
                sub-directory name.

        Returns:
            Returns a list of *Directorys*'s that are sorted if *sort*
            is *True*:

        """
        # Extract *tables_nodes* from *directory* (i.e. *self*):
        directory: Directory = self
        sub_directory_nodes: List[Node] = directory.sub_nodes_get(Directory)

        # To make `my_py` happy, convert *sub_directory_nodes* from a list of *Node*s to
        # *sub_diretories* which is a list of *Directory*'s:
        sub_directories: List[Directory] = list()
        sub_directory: Node
        for sub_directory in sub_directory_nodes:
            assert isinstance(sub_directory, Directory)
            sub_directories.append(sub_directory)

        # Perform any request *sort* before returning *tables*:
        if sort:
            sub_directories.sort(key=lambda sub_directory: sub_directory.name)
        return sub_directories

    # Directory.xml_lines_append():
    def xml_lines_append(self, xml_lines: List[str], indent: str) -> None:
        """Append *Directory* XML lines to a list.

        Append XML lines for *directory* (i.e. *self*) to *xm_lines*.
        Each XML line is prefixed by *indent*.

        Args:
            *xml_lines*: (*List*[*str*]): List to append XML lines to.
            *indent* (*str*): Prefix to be prepended to each XML line.

        """
        # Output the initial *directory* (i.e. *self*) XML element:
        directory: Directory = self
        directory_class_name: str = directory.__class__.__name__
        name: str = directory.name
        xml_lines.append(f'<{directory_class_name} name="{name}>"')

        # Append the XML for any *tables* to *xml_lines*:
        next_indent: str = indent + "  "
        tables: List[Table] = directory.tables_get(True)
        table: Table
        for table in tables:
            table.xml_lines_append(xml_lines, next_indent, "")

        # Append the XML for any *sub_directories* to *xml_lines*:
        sub_directories: List[Directory] = directory.sub_directories_get(True)
        sub_directory: Directory
        for sub_directory in sub_directories:
            sub_directory.xml_lines_append(xml_lines, next_indent)

        # Output the closing *directory* XML element:
        xml_lines.append(f"</{directory_class_name}>")


# Enumeration:
# class Enumeration(Node):
#     """Represents a filter enumeration."""
#
#     def __init__(self, bom_manager: BomManager, name: str) -> None:
#         """Initialize *Enumeration* object.
#
#         Initialize the *Enumeration* object (i.e. *self*) with
#         *bom_manager* and *name*.
#
#         Args:
#             *bom_manager* (*BomManager*): The root of all data
#                 structures.
#             *name* (*str*): The name of the enumeration.
#
#         """
#         super().__init__(bom_manager)
#         # enumeration: Enumeration = self
#         self.name: str = name
#
#     def __str__(self):
#         """Return a string representation."""
#         # In order to support the *trace* decorator for the *__init__*() method, we can not
#         # assume that the *name* attribute exists:
#         enumeration: Enumeration = self
#         name: str = "??"
#         if hasattr(enumeration, "name"):
#             name = enumeration.name
#         return f"Enumeration('{name}')"


# Parameter:
class Parameter(Node):
    """Represents a parameter of a parameteric table."""

    # Parameter.__init__():
    def __init__(self, bom_manager: BomManager, name: str, type_name: str,
                 header_index: int) -> None:
        """Initialize a parameter.

        Initialize a *Parameter* object (i.e. *self*) to contain
        *bom_manager*, *type_name* and *header_index*:

        Args:
            *bom_manager* (*BomManager)* : The root of all of the data
                structures:
            *name* (*str*): The parameter name and it must be non-empty.
            *header_index* (*int*): The index to `.csv` table for the
                parameter.

        """
        super().__init__(bom_manager)
        assert name, "Empty String!"
        # parameter: Parameter = self
        self.header_index: int = header_index
        self.name: str = name
        self.type_name: str = type_name

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

    # Parameter.comments_get()
    def comments_get(self, sort: bool) -> List[ParameterComment]:
        """Return the parameter comments.

        Return the *ParameterComment*'s associated with *paraemeter*
        (i.e. *self*.)  If *sort* is *True*, sort the returned list
        by language key.

        Args:
            *sort* (*bool*): If *True* sort the comments by language
                key.

        Returns:
            List of *ParameterComment*'s.

        """
        parameter: Parameter = self
        parameter_comment_nodes: List[Node] = parameter.sub_nodes_get(ParameterComment)

        # To make the `mypy` type checker happy, convert *parameter_comment_nodes* (a list of
        # *Node*'s) to *parameter_comments* (a list of *ParameterComment*'s):
        parameter_comments: List[ParameterComment] = list()
        parameter_comment: Node
        for parameter_comment in parameter_comment_nodes:
            assert isinstance(parameter_comment, ParameterComment)
            parameter_comments.append(parameter_comment)

        # Perform any requested *sort* before returning:
        if sort:
            parameter_comments.sort(key=Comment.key)
        return parameter_comments

    # Parameter.key():
    def key(self) -> int:
        """Return the sorting key."""
        parameter: Parameter = self
        return parameter.header_index

    # Parameter.comment_insert():
    def comment_insert(self, parameter_comment: ParameterComment) -> None:
        """Insert a parameter comment into parameter.

        Insert *parameter_comment* into *parameter* (i.e. *self*):
        Verifies that there is no previous comment with the same
        language.

        Args:
            *parameter_comment* (*ParameterComment*): The
            to *ParameterComment* add.

        """
        # Grab the current unsorted *comments* from *parameter* (i.e. *self*):
        parameter: Parameter = self
        comments: List[ParameterComment] = parameter.comments_get(False)

        # Sweep *comments* and ensure that *language* is not duplicated:
        language: str = parameter_comment.language
        comment: ParameterComment
        for comment in comments:
            assert comment.language != language, f"Duplicate langauge comment('{language}'"

        # Finally, insert *parameter_comment* into *parameter*:
        parameter.node_insert(parameter_comment)

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

    # Parameter.xml_lines_append():
    def xml_lines_append(self, xml_lines: List[str], indent: str) -> None:
        """Append XML for *Parameter* to lines list.

        Append the XML lines associated with *parameter* (i.e. *self*)
        to *xml_lines* with each line prefixed by *indent*:

        Args:
            *xml_lines* (*List*[*str*]): List of XML lines to append to.
            *indent* (*str*): The prefix to put in front of each line.

        """
        # Grab some values from *parameter* (i.e. *self*):
        parameter: Parameter = self
        name: str = parameter.name
        header_index: int = parameter.header_index
        type_name: str = parameter.type_name

        # Start with the initial `<Parameter ...>`:
        xml_lines.append(f'{indent}<Parameter'
                         f' name="{name}" '
                         f' header_index="{header_index}'
                         f' type_name="{type_name}">')

        # Now output the sorted *parameter_comments*:
        next_indent = indent + "    "
        parameter_comments: List[ParameterComment] = parameter.comments_get(True)
        parameter_comment: ParameterComment
        for parameter_comment in parameter_comments:
            parameter_comment.xml_lines_append(xml_lines, next_indent)

        # Wrap up the with the closing `/<Parameter>`:
        xml_lines.append('f{indnet}</Parameter>')


# Search:
class Search(Node):
    """Information about a parametric search."""

    # Search.__init__():
    def __init__(self, bom_manager: BomManager, name: str, file_path: Path) -> None:
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
        assert file_path.suffix == ".xml", "No .xml suffix"
        # search: Search = self
        self.file_path: Path = file_path
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
    def __init__(self, bom_manager: BomManager, name: str, file_path: Path) -> None:
        """Initialize the Table.

        Initialize the table with a *bom_manager*, *name*, and XML
        *file_name* path.

        Args:
            *bom_manager* (BomManager): The top level data structure
                that is root of all of the trees.
            *name* (str): The non-empty name of the table.  Can
                contain *any* unicode characters.
            *file_path* (Path): The path to the associated `.xml` file.

        """
        # Initialize the *Node* super-class:
        super().__init__(bom_manager)

        # Verify that *name* is non-empty and stuff everything into *table* (i.e. *self*.)
        # table: Table = self
        assert name, "Empty name string!"
        assert file_path.exists(), f"xml file '{file_path}' does not exist"
        self.name: str = name
        self.file_path: Path = file_path

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

    # # Table.column_tables_extract():
    # @trace(1)
    # def column_tables_extract(self, rows: List[List[str]]) -> List[Dict[str, int]]:
    #     """TODO."""
    #     # Create and return a *column_tables* which has one dictionary for each column in *rows*.
    #     # Each *column_table* dictionary that contains an occurance count for each different
    #     # value in the column.

    #     # Figure out how many *columns* there are for each row.  Each row is assumed
    #     # to have the same number of *columns*:
    #     assert rows, "No data to extract"
    #     row0: List[str] = rows[0]
    #     columns: int = len(row0)

    #     # Create *column_tables* and fill in one *column_table* per *column*:
    #     column_tables: List[Dict[str, int]] = list()
    #     for column in range(columns):
    #         column_table: Dict[str, int] = dict()
    #         column_tables.append(column_table)

    #         # Sweep across each *row* in *rows* and fill in *column_table*:
    #         for row in rows:
    #             assert len(row) == columns
    #             value: str = row[column]
    #             if value in column_table:
    #                 # We have seen *value* before in this *column*, so increment its count:
    #                 column_table[value] += 1
    #             else:
    #                 # This is the first time we seen *value* in this *column*, so insert it
    #                 # into *column_table* as the first one:
    #                 column_table[value] = 1

    #     # Return *column_tables*:
    #     return column_tables

    # Table.comment_insert():
    def comment_insert(self, table_comment: TableComment) -> None:
        """Insert comment into table.

        Insert *table_comment* into *table* (i.e. *self*).

        Args:
            *table_comment* (*TableComment*): The table comment to
                insert.

        """
        table: Table = self
        table.node_insert(table_comment)

    # Table.comments_get():
    def comments_get(self, sort: bool) -> List[TableComment]:
        """Return comments from table.

        Return the *TableComment*'s from *table* (i.e. *self*) as a
        *List*[*TableComment*].  If *sort* is *True*, sort the list
        based on language key.

        Args:
            *sort* (*bool*): If *True* sort the comments by language
                key.

        Returns:
            List of *TableComment'*s.

        """
        # Grab the *table_comment_nodes* from *table*:
        table: Table = self
        table_comment_nodes: List[Node] = table.sub_nodes_get(TableComment)

        # To make the `mypy` the type checker happy, convert from *table_comment_nodes* (a list of
        # *Node*'s) to *table_comments* (a list *TableComment*'s):
        table_comments: List[TableComment] = list()
        table_comment: Node
        for table_comment in table_comment_nodes:
            assert isinstance(table_comment, TableComment)
            table_comments.append(table_comment)

        # Perform any requested *sort* before returning *table_comments*:
        if sort:
            table_comments.sort(key=Comment.key)
        return table_comments

    # # Table.csv_file_read():
    # @trace(1)
    # def csv_file_read(self) -> Tuple[List[str], List[List[str]]]:
    #     """TODO."""
    #     # Grab some values from *table* (i.e. *self*):
    #     table: Table = self
    #     file_path: Path = table.file_path
    #     assert file_path.exists(), f".xml file '{file_path}' does not exist"

    #     # Open *csv_full_name* and read in the *headers* and *rows*:
    #     headers: List[str]
    #     rows: List[List[str]] = list()
    #     csv_file: IO[Any]
    #     with file_path.open() as csv_file:
    #         row_index: int
    #         row: List[str]
    #         for row_index, row in enumerate(csv.reader(csv_file, delimiter=',', quotechar='"')):
    #             if row_index == 0:
    #                 # The first *row* is actually the *headers*:
    #                 headers = row
    #             else:
    #                 # All others are data *rows*:
    #                 rows.append(row)

    #     # Return the resulting *headers* and *rows*:
    #     return headers, rows

    # # Table.csv_read_and_process():
    # @trace(1)
    # def csv_read_and_process(self, csv_directory: Path, bind: bool) -> None:
    #     """TODO."""
    #     # This delightful piece of code reads in a `.csv` file and attempts to catagorize
    #     # each column of the table with a "type".  The types are stored in *re_table*
    #     # (from *gui*) as dictionary of named pre compiled regualar expressions.
    #     # If there is no good match for the table column contents, it is given a type
    #     # of "String".  This code is actually pretty involved and convoluted.

    #     # Read the example `.csv` file associated with *table* (i.e. *self*) into *headers* and
    #     # *rows*:
    #     table: Table = self
    #     headers: List[str]
    #     rows: List[List[str]]
    #     headers, rows = table.csv_file_read()

    #     # Extract *column_tables* which is a list of dictionaries where each dictionary
    #     # has an occurence count for each unique value in a column:
    #     column_tables: List[Dict[str, int]] = table.column_tables_extract(rows)

    #     # Extract *type_tables* which is a list of dictionaries, where each dictionary
    #     # has an occurence count for each unique type name in the column:
    #     types_tables: List[Dict[str, int]] = table.type_tables_extract(column_tables)

    #     # If requested, bind the *types_tables* to *parameters*:
    #     if bind:
    #         table.parameters_bind(headers, types_tables)

    #     # We are done and can write out *table* now:
    #     table.xml_file_save()

    # # Table.partial_load():
    # @trace(1)
    # def partial_load(self, searches_path: Path) -> None:
    #     """Partial load all of the searches from a directory.

    #     Recursively visit all of the associated searches and
    #     partially load them.  This means that the search
    #     data structures have been created, but the associated
    #     search `.xml` is not read in.  Note that the `.xml`
    #     associated with the table is not read in either.

    #     Args:
    #         searches_path (Path): The path to the directory containing the
    #             zero, one, or more, search `.xml` files.

    #     """
    #     # Make sure *searches_path* is actually a directory:
    #     if searches_path.is_dir():
    #         # *searches_path* is an existing directory that may have some search `.xml` files
    #         # in it.  So now we ascan *searches_path* looking for `.xml` files:
    #         table: Table = self
    #         bom_manager: BomManager = table.bom_manager
    #         all_search_encountered: bool = False
    #         searches_count: int = 0
    #         search_path: Path
    #         for search_path in searches_path.glob("*.xml"):
    #             # We have a *search* `.xml` file:
    #             search_stem_file_name: str = search_path.stem
    #             search_name: str = Encode.from_file_name(search_stem_file_name)
    #             if search_name == "@ALL":
    #                 all_search_encountered = True
    #             search: Search = Search(bom_manager, search_name, search_path)
    #             table.search_insert(search)
    #             searches_count += 1

    #         # If we found any search `.xml` files (i.e. *searches_count* >= 1), we need to ensure
    #         # that search named "@ALL" is created:
    #         if not all_search_encountered and searches_count:
    #             all_search: Search = Search(bom_manager, "@ALL", search_path)
    #             table.search_insert(all_search)

    # Table.parameter.insert():
    def parameter_insert(self, parameter: Parameter) -> None:
        """Insert *parameter* into the table.

        Args:
            parameter (Parameter): The parameter to insert:

        """
        table: Table = self
        table.node_insert(parameter)

    # # Table.parameters_bind():
    # @trace(1)
    # def parameters_bind(self, headers: List[str], type_tables: List[Dict[str, int]]) -> None:
    #     """TODO."""
    #     # Grab *parameters* from *table* and make sure that there is a 1-to-1 correspondance
    #     # between *parameters* and *type_tables*:
    #     table: Table = self
    #     bom_manager: BomManager = table.bom_manager
    #     parameters: List[Parameter] = table.parameters_get(False)

    #     # Sweep through *Parameters* finding the *type_name* with the best match:
    #     index: int
    #     header: str
    #     # csv: str = ""
    #     # default: str = ""
    #     # optional: bool = False
    #     for index, header in enumerate(headers):
    #         # Convert *type_table* into *type_counts*:
    #         type_table: Dict[str, int] = type_tables[index]
    #         type_counts: List[Tuple[str, int]] = list(type_table.items())

    #         # Sort *type_counts* based on count:
    #         type_counts.sort(key=lambda name_count: (name_count[1], name_count[0]))

    #         # Grab the *name_count_last* which will have the highest count, and stuff
    #         # the associated *type_name* into *parameter*:
    #         name_count_last: Tuple[str, int] = type_counts[-1]
    #         type_name: str = name_count_last[0]

    #         parameter: Parameter
    #         if len(parameters) <= index:
    #             parameter = Parameter(bom_manager, header, type_name, index)
    #             table.parameter_insert(parameter)

    #             # Create an empty *english_parameter_comment* and stuff it into *parameter*:
    #             english_parameter_comment: ParameterComment = ParameterComment(bom_manager,
    #                                                                            language="EN")
    #             parameter.comment_insert(english_parameter_comment)
    #         else:
    #             assert False, "How do we get here?"
    #             parameter.type_name = type_name

    # Table.parameters_get():
    def parameters_get(self, sort: bool) -> List[Parameter]:
        """Return the a list of Parameters."""
        table: Table = self
        parameter_nodes: Nodes = table.nodes_get(Parameter)
        parameter_nodes_list: List[Node] = parameter_nodes.sub_nodes_get()

        # To make the `mypy` type checker happy, convert *parameter_nodes_list* (a list *Node*'s)
        # into *parameters* (a list of *Parameter*'s):
        parameters: List[Parameter] = list()
        parameter: Node
        for parameter in parameter_nodes_list:
            assert isinstance(parameter, Parameter)
            parameters.append(parameter)

        # Perform any requested *sort* before returning:
        if sort:
            parameters.sort(key=Parameter.key)
        return parameters

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

    # # Table.type_tables_extract():
    # @trace(1)
    # def type_tables_extract(self, column_tables: List[Dict[str, int]]) -> List[Dict[str, int]]:
    #     """TODO."""
    #     # The *re_table* comes from *gui* contains some regular expression for catagorizing
    #     # values.  The key of *re_table* is the unique *type_name* associated with the regular
    #     # expression that matches a given type.  The regular expressions are *PreCompiled*
    #     # to improve efficiency:
    #     table: Table = self
    #     bom_manager: BomManager = table.bom_manager
    #     re_table: Dict[str, PreCompiled] = bom_manager.re_table

    #     # Constuct *type_tables*, which is a list *type_table* that is 1-to-1 with the columns
    #     # in *column_tables*.  Each *type_table* collects a count of the number of column entries
    #     # that match a given *type_name*.  If none of the *type_names* match a given *value*,
    #     # the default *type_name* of "String" is used:
    #     type_tables: List[Dict[str, int]] = list()
    #     column_table: Dict[str, int]
    #     for column_table in column_tables:
    #         # Create *type_table*, create the "String" *type_name*, and tack it onto
    #         # *type_tables*:
    #         type_table: Dict[str, int] = dict()
    #         type_table["String"] = 0
    #         type_tables.append(type_table)

    #         # Sweep through *column_table* characterizing which values match which *type_names*:
    #         value: str
    #         count: int
    #         for value, count in column_table.items():
    #             type_name: str
    #             regex: PreCompiled
    #             match: bool = False
    #             # Now test *value* against *re* to see if we have a match:
    #             for type_name, regex in re_table.items():
    #                 if regex.match(value) is not None:
    #                     # We have a match, so make sure *type_name* is in *type_table*
    #                     # update the count appropriately:
    #                     if type_name in type_table:
    #                         type_table[type_name] += count
    #                     else:
    #                         type_table[type_name] = count
    #                     match = True

    #             # If we did not *match*, mark the *value* as a "String" type:
    #             if not match:
    #                 type_table["String"] += count
    #     return type_tables

    # # Table.xml_file_save():
    # def xml_file_save(self, extra: str = "") -> None:
    #     """TODO."""
    #     # Compute *file_path_parent* directory for *file_path* and make sure it exists:
    #     table: Table = self
    #     file_path: Path = table.file_path
    #     file_path_parent: Path = file_path.parent
    #     tracing: str = tracing_get()
    #     if tracing:  # pragma: no cover
    #         print(f"{tracing}file_path='{file_path}'")
    #         print(f"{tracing}file_path_parent='{file_path_parent}'")
    #     file_path_parent.mkdir(parents=True, exist_ok=True)
    #     assert file_path_parent.is_dir(), f"'{file_path_parent}' is not a diretory"

    #     # Construct the final *xml_lines*:
    #     xml_lines: List[str] = list()
    #     xml_lines.append('<?xml version="1.0"?>')
    #     table.xml_lines_append(xml_lines, "", extra)
    #     xml_lines.append("")
    #     xml_text: str = '\n'.join(xml_lines)

    #     # Now write *xml_text* out to the *xml_path* file::
    #     xml_file: IO[Any]
    #     with file_path.open("w") as xml_file:
    #         xml_file.write(xml_text)

    # Table.xml_lines_append():
    def xml_lines_append(self, xml_lines: List[str], indent: str, extra: str) -> None:
        """TODO."""
        # Start by appending the `<TABLE_CLASS_NAME...>` element:
        table: Table = self
        table_class_name: str = table.__class__.__name__
        name_text: str = Encode.to_attribute(table.name)
        xml_lines.append(f'{indent}<{table_class_name} name="{name_text}"{extra}>')

        # Append the `<TableComments>` ... `</TableComments>` elements:
        table_comments: List[TableComment] = table.comments_get(True)
        xml_lines.append(f'{indent}  <TableComments>')
        next_indent: str = indent + "    "
        table_comment: TableComment
        for table_comment in table_comments:
            table_comment.xml_lines_append(xml_lines, next_indent)
        xml_lines.append(f'{indent}  </TableComments>')

        # Append the `<Parameters>` element:
        parameters: List[Parameter] = table.parameters_get(True)
        xml_lines.append(f'{indent}  <Parameters>')
        parameter: Parameter
        for parameter in parameters:
            parameter.xml_lines_append(xml_lines, next_indent)
        xml_lines.append(f'{indent}  </Parameters>')

        # Close out with the `</TABLE_CLASS_NAME>` element:
        xml_lines.append(f'{indent}</{table_class_name}>')


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

    # Nodes.nodes_collect_recursively():
    def nodes_collect_recursively(self, node_type: Type, nodes_list: List[Node]) -> None:
        """TODO."""
        """Recursively find all Node's that match a type.

        Starting from *nodes* (i.e. *self*) search for all *Nodes*
        that match *node_type*.  For each matching *Node*, append
        it to *nodes_list*

        Args:
            *node_type* (Type): The type to match for a *Node*.
            *nodes_list* (List[Node]): The list of *Node*'s to append
                each matching *Node* to.
        """
        # Recursively visit each *sub_node* in *sub_nodes* looking for a *Node* that
        # matches *node_type* and append it to append to *tables*:
        nodes: Nodes = self
        sub_nodes: Dict[int, Node] = nodes.sub_nodes
        sub_node: Node
        for sub_node in sub_nodes.values():
            sub_node.nodes_collect_recursively(node_type, nodes_list)

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
            # if isinstance(sub_node, TableComment):
            #     assert False, f"sub_node={sub_node}
            sub_node.show_lines_append(show_lines, indent)

    # Nodes.sub_nodes_get():
    def sub_nodes_get(self) -> List[Node]:
        """Return the sub nodes in arbitrary order."""
        nodes: Nodes = self
        sub_nodes: Dict[int, Node] = nodes.sub_nodes
        return list(sub_nodes.values())

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


# Units:
class Units:
    """Tools for manipulating ISO units."""

    # Units.__init():
    # def __init__(self) -> None:
    #     """Initialize *Units* object."""
    #     pass

    # Units.__str__():
    # def __str__(self) -> str:
    #     """Return a string represntation."""
    #     return "Units()"

    # Units.si_units_re_text_get():
    @staticmethod
    def si_units_re_text_get() -> str:
        """Return an ISO units regular expression."""
        base_units: List[str] = ["s(ecs?)?", "seconds?", "m(eters?)?", "g(rams?)?", "[Aa](mps?)?",
                                 "[Kk](elvin)?", "mol(es?)?", "cd", "candelas?"]
        derived_units: List[str] = ["rad", "sr", "[Hh]z", "[Hh]ertz", "[Nn](ewtons?)?",
                                    "Pa(scals?)?", "J(oules?)?", "W(atts?)?", "°C", "V(olts?)?",
                                    "F(arads?)?", "Ω", "O(hms?)?", "S", "Wb", "T(eslas?)?", "H",
                                    "degC", "lm", "lx", "Bq", "Gy", "Sv", "kat"]
        all_units: List[str] = base_units + derived_units
        all_units_re_text: str = "(" + "|".join(all_units) + ")"
        prefixes: List[Tuple[str, float]] = [
          ("Y", 1e24),
          ("Z", 1e21),
          ("E", 1e18),
          ("P", 1e15),
          ("T", 1e12),
          ("G", 1e9),
          ("M", 1e6),
          ("k", 1e3),
          ("h", 1e2),
          ("da", 1e1),
          ("c", 1e-2),
          ("u", 1e-6),
          ("n", 1e-9),
          ("p", 1e-12),
          ("f", 1e-15),
          ("a", 1e-18),
          ("z", 1e-21),
          ("y", 1e-24)
        ]
        single_letter_prefixes: List[str] = [prefix[0] for prefix in prefixes
                                             if len(prefix[0]) == 1]
        single_letter_re_text: str = "[" + "".join(single_letter_prefixes) + "]"
        multi_letter_prefixes: List[str] = [prefix[0] for prefix in prefixes if len(prefix[0]) >= 2]
        letter_prefixes: List[str] = [single_letter_re_text] + multi_letter_prefixes
        prefix_re_text: str = "(" + "|".join(letter_prefixes) + ")"
        # print("prefix_re_text='{0}'".format(prefix_re_text))
        si_units_re_text: str = prefix_re_text + "?" + all_units_re_text
        # print("si_units_re_text='{0}'".format(si_units_re_text))
        return si_units_re_text
