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

# from bom_manager.bom import Encode
from bom_manager.tracing import trace, tracing_get  # , trace_level_set  # , tracing_get
import csv
# import lxml.etree as ETree  # type: ignore
from lxml.etree import _Element as Element  # type: ignore
from pathlib import Path
# import pkg_resources              # Used to find plug-ins.
import re
from typing import Any, Callable, Dict, IO, List, Optional, Tuple, Type
from typing import Any as PreCompiled
# Element = ETree._element


class BomManager:
    """Contains top-level data structurs needed for the BOM Manager."""

    # @trace(1)
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
        parameter_node_template: NodeTemplate = NodeTemplate(Parameter, (ParameterComment,),
                                                             {"index": int,
                                                              "name": str,
                                                              "type_name": str})
        parameter_comment_node_template: NodeTemplate = NodeTemplate(ParameterComment, (),
                                                                     {"language": str,
                                                                      "lines": list})
        search_node_template: NodeTemplate = NodeTemplate(Search, (),
                                                          {"file_name": str,
                                                           "name": str})
        table_node_template: NodeTemplate = NodeTemplate(Table, (Parameter, Search, TableComment),
                                                         {"name": str})
        table_comment_node_template: NodeTemplate = NodeTemplate(TableComment, (),
                                                                 {"language": str,
                                                                  "lines": list})

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
        self.ENTITY_SUBSTITUTIONS: Dict[str, str] = {
            '&': "&amp;",
            '>': "&gt;",
            '<': "&lt;",
            '"': "&quot;",
            '#': "&num",
            ';': "&semi;"
        }
        self.UNICODE_MAXIMUM = 0x110000 - 1

        # Initialize *re_table*:
        bom_manager: BomManager = self
        bom_manager.re_table_initialize()

    # BomManager.from_attribute():
    # @trace(1)
    def from_attribute(self, text: str) -> str:
        """Convert attrbitute text into a standard string.

        Args:
            *text* (*str*): Attribute text to convert.

        Returns:
            (*str*) Returns string with entities converted into
            unicode characters.

        """
        # Sweep across *text* looking for amphersands ('&'), breaking *text* into *chunks*
        # where some chunks are copied from *text* and others are entity substitutions:
        bom_manager: BomManager = self
        ENTITY_SUBSTITUTIONS: Dict[str, str] = bom_manager.ENTITY_SUBSTITUTIONS
        chunks: List[str] = list()
        processed_index: int = 0
        text_size: int = len(text)
        tracing: str = tracing_get()
        current_index: int = 0
        while current_index < text_size:
            # Do not do anything until an '&' is encountered:
            character: str = text[current_index]
            is_amphersand: bool = character == '&'
            if tracing:  # pragma: no cover
                print(f"{tracing}[{current_index}]:'{character}' is_amphersand={is_amphersand}")
            if character == '&':
                # We have an entity starting at *current_index* in *text*.
                # Start by stuffing the preceed unprocess characters from *text* into *chunks*:
                preceeding_chunk: str = text[processed_index:current_index]
                chunks.append(preceeding_chunk)

                # We find an exact match from the *ENTITY_SUBSTITUTIONS* table or we match "&#NNN;"
                # where NNN is a decimal number. Star by searching *ENTITY_STITUTIONS*:
                remaining_text: str = text[current_index:]
                if tracing:  # pragma: no cover
                    print(f"{tracing}preceeding_chunk='{preceeding_chunk}'")
                    print(f"{tracing}remaining_text='{remaining_text}'")
                substitution_character: str
                entity: str
                for substitution_character, entity in ENTITY_SUBSTITUTIONS.items():
                    if remaining_text.startswith(entity):
                        # We found a matching *entity*, so we record the substitution into *chunks*:
                        if tracing:  # pragma: no cover
                            print(f"{tracing}substitution_character='{substitution_character}'")
                        chunks.append(substitution_character)
                        current_index += len(entity)
                        break
                else:
                    # Nothing was found in *ENTITY_SUBSTITUTIONS*, so now we assume that we
                    # will get an entity of the form "&#NNN;" where NNN is a decimal number:
                    assert remaining_text.startswith("&#")
                    semicolon_index: int = remaining_text.find(';')
                    assert semicolon_index > 0, "No closing semicolon found"
                    numeric_text: str = remaining_text[2:semicolon_index]
                    assert numeric_text.isnumeric()
                    substitution_character = chr(int(numeric_text))
                    if tracing:  # pragma: no cover
                        print(f"{tracing}substitution_character='{substitution_character}'")
                    chunks.append(substitution_character)
                    current_index += 2 + len(numeric_text) + 1
                processed_index = current_index
            else:
                current_index += 1

        # If substitutions occurred, convert *chunks* back into the final *text*:
        if chunks:
            final_chunk: str = text[processed_index:]
            if tracing:  # pragma: no cover
                print(f"{tracing}final_chunk='{final_chunk}'")
            chunks.append(final_chunk)
            text = "".join(chunks)
        if tracing:  # pragma: no cover
            print(f"{tracing}final_text='{text}'")
        return text

    # BomManager.from_file_name():
    # @trace(1)
    def from_file_name(self, file_name: str) -> str:
        """Convert an encoded file name into a text string.

        See *BomManager*.*to_file_name*() for the rules to convert
        a Python unicode string and an ASCII file name string.  This
        method converts and ASCII *file_name* back into a Python
        unicode string.

        Args:
            *file_name* (*self*): The encoded file name to convert.

        Returns:
            (*str*): Returns the Python unicode string converted from
            *file_name*.

        """
        # Break *file_name* into string *chunks* where some string chunks are taken
        # verbatim from *file_name* and others contain substitutions:
        tracing: str = tracing_get()
        chunks: List[str] = list()
        file_name_size = len(file_name)
        current_index: int = 0
        processed_index: int = 0
        while current_index < file_name_size:
            # Dispatch on the current *character*:
            character: str = file_name[current_index]
            substitute: Optional[str] = None
            next_index: int = current_index + 1
            if character == '_':
                # Simple underscore ('_') to (' ') conversion:
                substitute = ' '
            elif character == '%':
                # We have "%XX", "%%XXXX", or "%%%XXXXXX" hex number encoding.
                # First compute the *percent_count* of percent ('%') characters:
                percent_count: int = 0
                index: int = current_index
                while index < file_name_size and file_name[index] == '%':
                    percent_count += 1
                    index += 1

                # Compute *next_index* skips over preceeding percent characters and *digits_test*:
                next_index = current_index + 3*percent_count

                # Extract the *digits_text* and convert into a *substitute* character:
                digits_text: str = file_name[current_index+percent_count:next_index]
                substitute_ord: int = int(digits_text, 16)
                if tracing:  # pragma: no cover
                    print(f"{tracing}file_name='{file_name}'")
                    print(f"{tracing}current_index={current_index}")
                    print(f"{tracing}percent_count={percent_count}")
                    print(f"{tracing}next_index={next_index}")
                    print(f"{tracing}digits_text='{digits_text}'")
                    print(f"{tracing}substitute_ord={substitute_ord}")
                assert digits_text.isalnum(), f"digits_text='{digits_text}' not hex"
                substitute = chr(substitute_ord)

            # If we have an actual *substitute* character, we add sub-strings to *chunks*:
            if substitute is not None:
                # Tack the unprocessed *previous_chunk* and *substitute* onto *chunks*:
                previous_chunk: str = file_name[processed_index:current_index]
                chunks.append(previous_chunk)
                chunks.append(substitute)

                # Update *processed_index* to remember how many characters have been processed:
                processed_index = next_index
            current_index = next_index

        # Return the final *name* converted from *file_name*:
        name: str
        if chunks:
            # Substititutions occurred, so tack the *final_chunk* onto *chunks*
            # and genaerate final *name* value:
            final_chunk: str = file_name[processed_index:]
            chunks.append(final_chunk)
            name = "".join(chunks)
        else:
            # No substitutions occurred, so we can just return *file_name* as the final *name*:
            name = file_name
        return name

    # BomManager.node_template_add():
    def node_template_add(self, node_template: "NodeTemplate") -> None:
        """TODO."""
        bom_manager: BomManager = self
        node_type: Type = node_template.node_type
        node_templates: Dict[Type, NodeTemplate] = bom_manager.node_templates
        assert node_type not in node_templates
        node_templates[node_type] = node_template

    # BomManager.to_attribute():
    # @trace(1)
    def to_attribute(self, text: str) -> str:
        """Return string with entity replacements for HTML an attribute.

        HTML elements are generally of the form:

             <ElementName attribute1="value1" ... attributeN="valueN">

        Since *text* can contain any arbitrary unicode character.  To
        make life consistent the characters that cause parsing problems
        are converted into HTML entities.  Thus, '&' is converted to
        "&amp;", '"" is converted to ";&quot", and characters out of
        the normal ASCII character range are converted to '&#NNN;'
        where NNN is a decimal number.

        Args:
            *text* (*str*): The text to perform entity subsitutions on.

        Returns:
            (*str*): A string with entity substitions performed on it.

        """
        # Grab some values from *bom_manager*:
        bom_manager: BomManager = self
        ENTITY_SUBSTITUTIONS: Dict[str, str] = bom_manager.ENTITY_SUBSTITUTIONS
        # tracing: str = tracing_get()

        # Sweep across *text* one *character* at time.  The *text* is broken into the
        # *chunks* list with unmodified text and entity subsitutions intermixed:
        chunks: List[str] = list()
        processed_index: int = 0
        entity: Optional[str] = None
        index: int
        character: str
        for index, character in enumerate(text):
            # Dispatch on character to figure out if we need an *entity* substitution:
            # if tracing:  # pragma: no cover
            #     print(f"{tracing}to_attribute[{index}]'{character}'")
            entity = None
            if character in ENTITY_SUBSTITUTIONS:
                entity = ENTITY_SUBSTITUTIONS[character]
            elif not(' ' <= character <= '~'):
                entity = f"&#{ord(character)};"

            # If there is an *entity* subsitution, place the preceedeing unmodified text
            # into *chunks* followed by the *entity* substitution:
            if entity is not None:
                preceeding_chunk: str = text[processed_index:index]
                chunks.append(preceeding_chunk)
                chunks.append(entity)
                processed_index = index + 1

        # If substitutions occured update *text* from *chunks*:
        if chunks:
            # Create the *final_chunk* containing the remaining characters, and convert *chunks*
            # into *result_text*:
            final_chunk: str = text[processed_index:]
            chunks.append(final_chunk)
            text = "".join(chunks)
        return text

    # BomManager.to_file_name():
    # @trace(1)
    def to_file_name(self, text: str) -> str:
        """Convert Python unicode string to ASCII file name.

        Many of the *BomManager* data structures store their contents
        as file in a file system..  This routine is used to convert
        the name attached to the data structure into a ASCII file that
        can be seen and manipulated at the shell level without having
        to resort to weird shell quoting tricks.

        The conversion rules are:
        * Letters ('A-Z', 'a'-'z'), digits ('0'-'9') and the following
          punctuation characters plus ('+'), comma (','), period ('.'),
          and colon (':') go straight through.
        * A space (' ') is translated to an underscore '_'.
        * All other characters are translated to one of "%XX",
          "%%XXXX", or "%%%XXXXXX", where "XX", "XXXX", and "XXXXXX",
          are 2, 4 and 6 digit hexadecimal digits.  The smallest one
          that can contain the unicode character is always used.

        This method converts *text* from an Python unicode string into
        an ASCII file name using the rules listed above and returns
        the resulting string.

        Args:
            *text* (*str*): The Python unicode string to convert.

        Returns:
            (*str*): The ASCII representation of of *text*.

        """
        # Grab some values from *bom_manager*:
        bom_manager: BomManager = self
        UNICODE_MAXIMUM = bom_manager.UNICODE_MAXIMUM
        tracing: str = tracing_get()

        # Partion *text* into *chunks* where some chunks are take verbatim from *text*
        # and others are substitutions for individual characters in *text*.  Later all
        # *chunks* is joined together to for the converted string:
        chunks: List[str] = list()
        processed_index: int = 0
        current_index: int
        character: str
        for current_index, character in enumerate(text):
            # Skip over letters, digits, '+', ',', '.', and ':':
            if not (character.isalnum() or character in "+,.:"):
                # We will generate a *substitute* for *character*:
                substitute: str
                if character == ' ':
                    # Spaces are converted to underscores ('_'):
                    substitute = '_'
                else:
                    # All other characters are converted into a hex format of "%XX", "%%XXXX",
                    # or "%%%XXXXXX".  We dispatch using *character_ord* to figure out which
                    # format to use:
                    character_ord: int = ord(character)
                    # Dispatch using *character_ord* to figure out if we are going to use
                    if character_ord <= 0xff:
                        substitute = "%{0:02x}".format(character_ord)
                    elif character_ord <= 0xffff:
                        substitute = "%%{0:04x}".format(character_ord)
                    elif character_ord <= UNICODE_MAXIMUM:
                        substitute = "%%%{0:06x}".format(character_ord)
                    else:  # pragma: no cover
                        assert False, f"Unicode character that is too big: {character_ord}"
                    if tracing:  # pragma: no cover
                        print(f"{tracing}character_ord={character_ord}")
                        print(f"{tracing}substitute='{substitute}'")

                # Now tack the *preceeding_chunk* and *substitute* onto *chunks*:
                preceeding_chunk: str = text[processed_index:current_index]
                chunks.append(preceeding_chunk)
                chunks.append(substitute)

                # Update *processed_index* to remember how much of *text* has been processed:
                processed_index = current_index + 1

        # Now we generate the resulting *file_name*:
        file_name: str
        if chunks:
            # We have substitutions in *chunks*, so wrap up the *final_chunk* and perform the join:
            final_chunk: str = text[processed_index:]
            chunks.append(final_chunk)
            file_name = "".join(chunks)
        else:
            # No substitutions occured, so we can just return *text* as *file_name*:
            file_name = text
        return file_name

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

    # Node.collection_cast():
    def collection_cast(self) -> "Collection":
        """Fail when not properly overridden by *Collection* sub-class.

        Used for converting between a list of *Nodes* that happen
        to all be *TableComment*s.  If this method is called, the
        *Node* (i.e. *self*) is not a *Collection* object and we fail.

        """
        node: Node = self  # pragma: no cover
        assert False, f"Got a {node.__class__.__name__} instead of Collection"  # pragma: no cover

    # Node.directory_cast():
    def directory_cast(self) -> "Directory":
        """Fail when not properly overridden by *Directory* sub-class.

        Used for converting between a list of *Nodes* that happen
        to all be *Directory*s.  If this method is called, the
        *Node* (i.e. *self*) is not a *Directory* object and we fail.

        """
        node: Node = self  # pragma: no cover
        assert False, f"Got a {node.__class__.__name__} instead of Directory"  # pragma: no cover

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
    # def nodes_get(self, sub_type: Type) -> "Nodes":
    #     """Return the sub type Nodes object."""
    #     node: Node = self
    #     nodes_table: Dict[Type, Nodes] = node.nodes_table
    #     assert sub_type in nodes_table
    #     nodes: Nodes = nodes_table[sub_type]
    #     return nodes

    # Node.parameter_cast():
    def parameter_cast(self) -> "Parameter":
        """Fail when not overridden by *Parameter* sub-class.

        Used for converting between a list of *Nodes* that happen
        to all be *Parameter*s.  If this method is called, the
        *Node* (i.e. *self*) is not a *Parameter* object and we fail.

        """
        node: Node = self  # pragma: no cover
        assert False, (f"Got a {node.__class__.__name__} instead of Parameter")  # pragma: no cover

    # Node.parameter_comment_cast():
    def parameter_comment_cast(self) -> "ParameterComment":
        """Fail when not overridden by *ParameterCommetn* sub-class.

        Used for converting between a list of *Nodes* that happen
        to all be *ParameterComment*s.  If this method is called, the
        *Node* (i.e. *self*) is not a *ParameterComemnt* object and we
        fail.

        """
        node: Node = self  # pragma: no cover
        assert False, (f"Got a {node.__class__.__name__} "
                       "instead of ParameterComment")  # pragma: no cover

    # Node.remove():
    def remove(self, sub_node: "Node") -> None:
        """Remove a sub-node from a Node.

        Args:
            *sub_node* (*Node*): Sub-node to remove.

        """
        node: Node = self
        nodes_table: Dict[Type, Nodes] = node.nodes_table
        sub_node_type: Type = type(sub_node)
        assert sub_node_type in nodes_table
        nodes: Nodes = nodes_table[sub_node_type]
        nodes.remove(sub_node)

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

    # Node.search_cast():
    def search_cast(self) -> "Search":
        """Return the *Search* object.

        Used for converting between a list of *Nodes* that happen
        to all be *Search*s.  If this method is called, the
        *Node* (i.e. *self*) is not a *Search* and we fail.

        """
        node: Node = self  # pragma: no cover
        assert False, f"Got a {node.__class__.__name__} instead of Search"  # pragma: no cover

    # Node.table_cast():
    def table_cast(self) -> "Table":
        """Return the *Table* object.

        Used for converting between a list of *Nodes* that happen
        to all be *Table*s.  If this method is called, the
        *Node* (i.e. *self*) is not a *Table* and we fail.

        """
        node: Node = self  # pragma: no cover
        assert False, f"Got a {node.__class__.__name__} instead of Table"  # pragma: no cover

    # Node.table_comment_cast():
    def table_comment_cast(self) -> "TableComment":
        """Return the *TableComment* object.

        Used for converting between a list of *Nodes* that happen
        to all be *TableComment*s.  If this method is called, the
        *Node* (i.e. *self*) is not a *TableComment* and we fail.

        """
        node: Node = self  # pragma: no cover
        assert False, f"Got a {node.__class__.__name__} instead of TableComment"  # pragma: no cover

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

    # Collection.collection_cast():
    def collection_cast(self) -> "Collection":
        """Convert a *Node* to a *Collection*."""
        collection: Collection = self
        return collection

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
        # into *directories*:
        collection: Collection = self
        directory_sub_nodes: List[Node] = collection.sub_nodes_get(Directory)
        directory_sub_node: Node
        directories: List[Directory] = [directory_sub_node.directory_cast()
                                        for directory_sub_node in directory_sub_nodes]

        # Perform any requested *sort* before returning *directories*:
        directory: Directory
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
        # Grab some values from *collection* (i.e. *self*):
        collection: Collection = self
        bom_manager: BomManager = collection.bom_manager
        collection_type_name: str = collection.__class__.__name__
        collection_root: str = str(collection.collection_root)
        name: str = collection.name
        searches_root: str = str(collection.searches_root)

        # Attribute strings need to be converted:
        to_attribute: Callable[[str], str] = bom_manager.to_attribute

        # Output initiial element:
        xml_lines.append(f'{indent}<{collection_type_name} '
                         f'name="{to_attribute(name)}" '
                         f'collection_root="{to_attribute(collection_root)}" '
                         f'searches_root="{to_attribute(searches_root)}"'
                         f'{extra_attributes}>')

        # Now output the sorted *directories*:
        next_indent: str = indent + "  "
        directories: List[Directory] = collection.directories_get(True)
        directory: Directory
        for directory in directories:
            directory.xml_lines_append(xml_lines, next_indent)

        # Output the closing element:
        xml_lines.append(f'{indent}</{collection_type_name}>')

    # Collection.xml_parse():
    @staticmethod
    def xml_parse(collection_element: Element, bom_manager: BomManager) -> "Collection":
        """Parse an XML Elment into a *Collection*.

        Parse *collection_element* into new *Collection* object.

        Args:
            *collect_element* (*Element*): The XML element to
                parse parse.
            *bom_manager* (*BomManager*): The root of all data
                structures.

        Returns:
            The created *Collection* object.

        """
        # Create the *collection* from with *collection_element*:
        assert collection_element.tag == "Collection"
        attributes_table: Dict[str, str] = collection_element.attrib
        assert "name" in attributes_table
        assert "collection_root" in attributes_table
        assert "searches_root" in attributes_table
        name: str = attributes_table["name"]
        collection_root: Path = Path(attributes_table["collection_root"])
        searches_root: Path = Path(attributes_table["searches_root"])
        collection: Collection = Collection(bom_manager, name, collection_root, searches_root)

        # Visit each of the *collection* *sub_elements*:
        sub_elements: List[Element] = list(collection_element)
        sub_element: Element
        for sub_element in sub_elements:
            assert sub_element.tag == "Directory"
            directory: Directory = Directory.xml_parse(sub_element, bom_manager)
            collection.directory_insert(directory)
        return collection


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

    # Collections.collections_get():
    def collections_get(self, sort: bool) -> List[Collection]:
        """
        Return a list of *Collection*'s.

        Return a list of *Collection*'s associated with *collections*
        (i.e. *self*.)  If *sort* is *True*, the returned list
        is sorted by table name.

        Args:
            *sort* (*bool*): If *True*, the returned tables sorted by
                table name.

        Returns:
            Returns a list of *Table*'s that are sorted if *sort*
            is *True*:

        """
        # Extract *collections* from *collection
        collections: Collections = self
        collection_sub_nodes: List[Node] = collections.sub_nodes_get(Collection)
        collection_sub_node: Node
        collections_list: List[Collection] = [collection_sub_node.collection_cast()
                                              for collection_sub_node in collection_sub_nodes]
        if sort:
            collections_list.sort(key=lambda collection: collection.name)
        return collections_list

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

    # Collections.xml_lines_append():
    def xml_lines_append(self, xml_lines: List[str], indent: str) -> None:
        """Append XML for *Collection* to a list.

        Append the XML description of *collection* (i.e. *self*) to the *xml_lines* list.
        Each line is prefixed by *indent*.

        Args:
            *xml_lines*: *List*[*str*]: List of line to append individual XML lines to.
            *indent* (*str*): A prefix prepended to each line.

        """
        # Output the initial element:
        collections: Collections = self
        xml_lines.append(f"{indent}<Collections>")

        # Now output the sorted *collections*:
        next_indent: str = indent + "  "
        collections_list: List[Collection] = collections.collections_get(True)
        collection: Collection
        for collection in collections_list:
            collection.xml_lines_append(xml_lines, next_indent, "")

        # Output the closing element:
        xml_lines.append(f"{indent}</Collections>")

    # Collections.xml_parse():
    @staticmethod
    def xml_parse(collections_element: Element, bom_manager: BomManager) -> "Collections":
        """Parse an element tree into *Collections* object.

        Parse the *collections_element* into a *Collections* object
        including all children *Node*'s.

        Args:
            *collections_element* (*Element*): The XML Element object
                to parse.
            *bom_manager* (*BomManager*): The root of all data
                structures.

        Returns:
            The resulting parsed *Collections* object.

        """
        # Create *collectons*:
        assert collections_element.tag == "Collections", f"tag='{collections_element.tag}'"
        collections: Collections = Collections(bom_manager)

        # Parse each sub-*collection* and it into *collections*:
        collection_elements: List[Element] = list(collections_element)
        collection_element: Element
        for collection_element in collection_elements:
            collection: Collection = Collection.xml_parse(collection_element, bom_manager)
            collections.collection_insert(collection)
        return collections


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
        # Grab some values from *comment* (i.e. *self*):
        comment: Comment = self
        bom_manager: BomManager = comment.bom_manager
        comment_class_name = comment.__class__.__name__
        language: str = comment.language

        # Attributes need to be converted:
        to_attribute: Callable[[str], str] = bom_manager.to_attribute

        # Output the initial opening `<Comment ...>`:
        xml_lines.append(f'{indent}<{comment_class_name} '
                         f'language="{to_attribute(language)}">')

        # Append each *line* from *lines* to *xml_lines* indented by *next_indent*:
        lines: List[str] = comment.lines
        line: str
        next_indent: str = indent + "  "
        for line in lines:
            xml_lines.append(f'{next_indent}{line}')

        # End with the closing `</Comment>`:
        xml_lines.append(f'{indent}</{comment_class_name}>')

    # Comment.xml_language_lines_parse():
    @staticmethod
    def xml_language_lines_parse(comment_element: Element) -> Tuple[str, List[str]]:
        """Parse the lanaguage and text lines of an XML comment.

        This is a helper method to parse *Comment* and extract the
        language and comment lines.

        Args:
            *comment_element* (*Element*): The comment *Element* to be
                parsed.

        Returns:
            The lanaguage string and a list of comment lines:

        """
        # Extract the the *language* and comment *lines* from *comment_element*:
        attributes_table: Dict[str, str] = comment_element.attrib
        assert "language" in attributes_table
        language: str = attributes_table["language"]
        text = comment_element.text
        lines: List[str] = text.split('\n')
        lines = [line.strip() for line in lines]

        # Remove empty lines from the beginning and end of *lines* before returning results:
        if lines and lines[0] == "":
            del lines[0]
        if lines and lines[-1] == "":
            del lines[-1]
        return language, lines


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

    # TableComment.table_comment_cast():
    def table_comment_cast(self) -> "TableComment":
        """Return the *TableComment* object.

        Used for converting between a list of *Nodes* that happen
        to all be *TableComment*s.

        """
        table_comment: TableComment = self
        return table_comment

    # TableComment.xml_parse():
    @staticmethod
    def xml_parse(table_comment_element: Element, bom_manager: BomManager) -> "TableComment":
        """Parse table comment element into a *TableComment*.

        Args:
            *table_comment_element* (*Element*): The XML element to
                parse.
            *bom_manager* (*BOM_Manager*): The root of all data
                structures.

        Returns:
            Returns the resulting *TableComment* object.

        """
        language: str
        lines: List[str]
        language, lines = Comment.xml_language_lines_parse(table_comment_element)
        table_comment: TableComment = TableComment(bom_manager, language)
        table_comment.lines_set(lines)
        return table_comment


# ParameterComment:
class ParameterComment(Comment):
    """Represents a parameter comment from a Table XML file."""

    # ParameterComment.__init__():
    def __init__(self, bom_manager: BomManager, language: str) -> None:
        """See *Comment* base class."""
        super().__init__(bom_manager, language=language)

    # ParameterComment.parameter_comment_cast():
    def parameter_comment_cast(self) -> "ParameterComment":
        """Convert a *Node* into a *ParameterComment*."""
        parameter_comment: ParameterComment = self
        return parameter_comment

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

    # ParameterComment.xml_parse():
    @staticmethod
    def xml_parse(parameter_comment_element: Element,
                  bom_manager: BomManager) -> "ParameterComment":
        """Parse parameter comment element into a *ParameterComment*.

        Args:
            *parameter_comment_element* (*Element*): The XML element to
                parse.
            *bom_manager* (*BOM_Manager*): The root of all data
                structures.

        Returns:
            Returns the resulting *ParameterComment* object.

        """
        language: str
        lines: List[str]
        language, lines = Comment.xml_language_lines_parse(parameter_comment_element)
        parameter_comment: ParameterComment = ParameterComment(bom_manager, language)
        parameter_comment.lines_set(lines)
        return parameter_comment


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

    # Directory.directory_cast():
    def directory_cast(self) -> "Directory":
        """Convert a *Node* into a *Directory*."""
        directory: Directory = self
        return directory

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
        # Extract *tables* from *directory* (i.e. *self*):
        directory: Directory = self
        table_sub_nodes: List[Node] = directory.sub_nodes_get(Table)
        table_sub_node: Node
        tables: List[Table] = [table_sub_node.table_cast() for table_sub_node in table_sub_nodes]

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
        sub_directory_node: Node
        sub_directories: List[Directory] = [sub_directory_node.directory_cast()
                                            for sub_directory_node in sub_directory_nodes]

        # Perform any request *sort* before returning *sub_directories*:
        if sort:
            sub_directory: Directory
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
        # Grab some values from *directory* (i.e. *self*):
        directory: Directory = self
        bom_manager: BomManager = directory.bom_manager
        directory_class_name: str = directory.__class__.__name__
        name: str = directory.name

        # XML attributes need to be converted:
        to_attribute: Callable[[str], str] = bom_manager.to_attribute

        # Output the initial *directory* (i.e. *self*) XML element:
        xml_lines.append(f'{indent}<{directory_class_name} '
                         f'name="{to_attribute(name)}">')

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
        xml_lines.append(f"{indent}</{directory_class_name}>")

    # Directory.xml_parse():
    @staticmethod
    def xml_parse(directory_element: Element, bom_manager: BomManager) -> "Directory":
        """Parse an XML Elment into a *Directory*.

        Parse *directory_element* (i.e. *self*) into new *Collection*
        object.

        Args:
            *directory_element* (*Element*): The XML element to parse.
            *bom_manager* (*BomManager*): The root of all data
                structures.

        Returns:
            The created *Directory* object.

        """
        assert directory_element.tag == "Directory"
        attributes_table: Dict[str, str] = directory_element.attrib
        assert "name" in attributes_table
        name: str = attributes_table["name"]
        directory: Directory = Directory(bom_manager, name)

        sub_elements: List[Element] = list(directory_element)
        sub_element: Element
        for sub_element in sub_elements:
            sub_element_tag: str = sub_element.tag
            if sub_element_tag == "Directory":
                sub_directory: Directory = Directory.xml_parse(sub_element, bom_manager)
                directory.directory_insert(sub_directory)
            elif sub_element_tag == "Table":
                table: Table = Table.xml_parse(sub_element, bom_manager)
                directory.table_insert(table)
            else:  # pragma: no cover
                assert False, f"Unprocessed tag='{sub_element_tag}'"
        return directory


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
    def __init__(self, bom_manager: BomManager, name: str, type_name: str, index: int) -> None:
        """Initialize a parameter.

        Initialize a *Parameter* object (i.e. *self*) to contain
        *bom_manager*, *type_name* and *index*:

        Args:
            *bom_manager* (*BomManager)* : The root of all of the data
                structures:
            *name* (*str*): The parameter name and it must be non-empty.
            *index* (*int*): The column index to `.csv` table for the
                parameter.

        """
        super().__init__(bom_manager)
        assert name, "Empty String!"
        # parameter: Parameter = self
        self.index: int = index
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
        parameter_comment_sub_nodes: List[Node] = parameter.sub_nodes_get(ParameterComment)
        parameter_comment_sub_node: Node
        parameter_comments: List[ParameterComment] = [parameter_comment_sub_node.
                                                      parameter_comment_cast()
                                                      for parameter_comment_sub_node
                                                      in parameter_comment_sub_nodes]

        # Perform any requested *sort* before returning:
        if sort:
            parameter_comments.sort(key=Comment.key)
        return parameter_comments

    # Parameter.key():
    def key(self) -> int:
        """Return the sorting key."""
        parameter: Parameter = self
        return parameter.index

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

    # Parameter.parameter_cast():
    def parameter_cast(self) -> "Parameter":
        """Return the *Parameter* object.

        Used for converting from a *Node* that happens to be a
        *Parameter* to *Parameter*.

        """
        parameter: Parameter = self
        return parameter

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
        bom_manager: BomManager = parameter.bom_manager
        index: int = parameter.index
        name: str = parameter.name
        type_name: str = parameter.type_name

        # XML attributes need to be converted:
        to_attribute: Callable[[str], str] = bom_manager.to_attribute

        # Extract the *parameter_comments*:
        parameter_comment: ParameterComment
        parameter_comments: List[ParameterComment] = parameter.comments_get(True)
        non_empty_parameter_comments: List[ParameterComment] = [parameter_comment
                                                                for parameter_comment
                                                                in parameter_comments
                                                                if len(parameter_comment.lines)]
        has_comments: bool = len(non_empty_parameter_comments) >= 1
        trailing_slash: str = "" if has_comments else '/'

        # Start with the initial `<Parameter ...>`:
        xml_lines.append(f'{indent}<Parameter'
                         f' name="{to_attribute(name)}"'
                         f' index="{index}"'
                         f' type_name="{to_attribute(type_name)}"'
                         f'{trailing_slash}>')

        # Now output the sorted *parameter_comments*:
        if has_comments:
            next_indent = indent + "  "
            for parameter_comment in non_empty_parameter_comments:
                parameter_comment.xml_lines_append(xml_lines, next_indent)

            # Wrap up the with the closing `/<Parameter>`:
            xml_lines.append(f'{indent}</Parameter>')

    def xml_parse(parameter_element: Element, bom_manager: BomManager) -> "Parameter":
        """Parse an XML element into a *Parameter*.

        Parse *parameter_element* (i.e. *self*) into new *Parameter*
        object.

        Args:
            *paremeter_element* (*Element*): The XML element to parse.
            *bom_manager* (*BomManager*): The root of all data
                structures.

        Returns:
            The created *Parameter* object.

        """
        assert parameter_element.tag == "Parameter"
        attributes_table: Dict[str, str] = parameter_element.attrib
        assert "index" in attributes_table
        assert "name" in attributes_table
        assert "type_name" in attributes_table
        index: int = int(attributes_table["index"])
        name: str = attributes_table["name"]
        type_name: str = attributes_table["type_name"]
        parameter: Parameter = Parameter(bom_manager, name, type_name, index)
        sub_elements: List[Element] = list(parameter_element)
        sub_element: Element
        for sub_element in sub_elements:
            parameter_comment: ParameterComment = ParameterComment.xml_parse(sub_element,
                                                                             bom_manager)
            parameter.comment_insert(parameter_comment)
        return parameter


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
        self.file_name: str = str(file_path)
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

    # Search.search_cast():
    def search_cast(self) -> "Search":
        """Return the *Search* object.

        Used for converting from a *Node* that happens to be a
        *Search* to *Search*.

        """
        search: Search = self
        return search

    # Search.xml_lines_append():
    def xml_lines_append(self, xml_lines: List[str], indent: str) -> None:
        """Append XML lines for a *Search* to a list.

        Args:
            *xml_lines* (*List*[*str*]): List to append XML lines to.
            *indent* (*str*): Prefix to prepend to each line.

        """
        # Grab some values from *search* (i.e. *self*):
        search: Search = self
        bom_manager: BomManager = search.bom_manager
        name: str = search.name

        # XML attributes need to be converted:
        to_attribute: Callable[[str], str] = bom_manager.to_attribute

        # Output the XML for *search*:
        xml_lines.append(f'{indent}<Search '
                         f'name="{to_attribute(name)}"/>')

    # Search.xml_parse():
    @staticmethod
    def xml_parse(search_element: Element, bom_manager: BomManager) -> "Search":
        """TODO."""
        assert search_element.tag == "Search"
        attributes_table: Dict[str, str] = search_element.attrib
        assert "name" in attributes_table
        name: str = attributes_table["name"]
        file_path: Path = Path("foo.xml")
        search: Search = Search(bom_manager, name, file_path)
        return search


# Table:
class Table(Node):
    """Informatation about a parametric table of parts."""

    # Table.__init__():
    def __init__(self, bom_manager: BomManager, name: str) -> None:
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
        # assert file_path.exists(), f"xml file '{file_path}' does not exist"
        self.name: str = name

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

    # Table.column_tables_extract():
    # @trace(1)
    def column_tables_extract(self, rows: List[List[str]]) -> List[Dict[str, int]]:
        """TODO."""
        # Create and return a *column_tables* which has one dictionary for each column in *rows*.
        # Each *column_table* dictionary that contains an occurance count for each different
        # value in the column.

        # Figure out how many *columns* there are for each row.  Each row is assumed
        # to have the same number of *columns*:
        table: Table = self
        assert rows, "No data to extract"
        row0: List[str] = rows[0]
        columns: int = len(row0)

        # Create *column_tables* and fill in one *column_table* per *column*:
        column_tables: List[Dict[str, int]] = list()
        for column in range(columns):
            column_table: Dict[str, int] = dict()
            column_tables.append(column_table)

            # Sweep across each *row* in *rows* and fill in *column_table*:
            row: List[str]
            row_index: int
            for row_index, row in enumerate(rows):
                assert len(row) == columns, (f"Row[{row_index}]:table={table} "
                                             f"len(row)={len(row)} != columns={columns}, "
                                             f"row={row}")
                value: str = row[column]
                if value in column_table:
                    # We have seen *value* before in this *column*, so increment its count:
                    column_table[value] += 1
                else:
                    # This is the first time we seen *value* in this *column*, so insert it
                    # into *column_table* as the first one:
                    column_table[value] = 1

        # Return *column_tables*:
        return column_tables

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
        # Grab the *table_comment* from *table*:
        table: Table = self
        table_comment_sub_nodes: List[Node] = table.sub_nodes_get(TableComment)
        table_comment_sub_node: Node
        table_comments: List[TableComment] = [table_comment_sub_node.table_comment_cast()
                                              for table_comment_sub_node in table_comment_sub_nodes]

        # Perform any requested *sort* before returning *table_comments*:
        if sort:
            table_comments.sort(key=Comment.key)
        return table_comments

    # Table.csv_file_read():
    # @trace(1)
    def csv_file_read(self, csv_file_path: Path) -> Tuple[List[str], List[List[str]]]:
        """TODO."""
        # Grab some values from *table* (i.e. *self*):
        # table: Table = self
        assert csv_file_path.is_file(), f"'{csv_file_path}' does not exist"

        # Open *csv_full_name* and read in the *headers* and *rows*:
        headers: List[str]
        headers_size: int = -1
        rows: List[List[str]] = list()
        csv_file: IO[Any]
        with csv_file_path.open() as csv_file:
            row_index: int
            row: List[str]
            for row_index, row in enumerate(csv.reader(csv_file, delimiter=',', quotechar='"')):
                if row_index == 0:
                    # The first *row* is actually the *headers*:
                    headers = row
                    headers_size = len(headers)
                else:
                    # All others are data *rows*:
                    if len(row) == headers_size:
                        rows.append(row)
                    else:
                        print(f"Row {row_index+1} of '{csv_file_path}' has to many/few columns.")

        # Return the resulting *headers* and *rows*:
        return headers, rows

    # Table.csv_read_and_process():
    # @trace(1)
    def csv_read_and_process(self, directory_path: Path, bind: bool) -> None:
        """TODO."""
        # This delightful piece of code reads in a `.csv` file and attempts to catagorize
        # each column of the table with a "type".  The types are stored in *re_table*
        # (from *gui*) as dictionary of named pre compiled regualar expressions.
        # If there is no good match for the table column contents, it is given a type
        # of "String".  This code is actually pretty involved and convoluted.

        # Grab some values from *table* (i.e. *self*):
        table: Table = self
        bom_manager: BomManager = table.bom_manager
        table_name: str = table.name

        # Compute the *table_csv_file_path* and *table_xml_file_path*:
        to_file_name: Callable[[str], str] = bom_manager.to_file_name
        table_file_name: str = to_file_name(table_name)
        table_csv_file_path: Path = directory_path / (table_file_name + ".csv")
        table_xml_file_path: Path = directory_path / (table_file_name + ".xml")

        # Perform any requested *tracing*:
        tracing: str = tracing_get()
        if tracing:
            print(f"{tracing}table_csv_file_path='{table_csv_file_path}'")
            print(f"{tracing}table_xml_file_path='{table_xml_file_path}'")

        # Read the example `.csv` file associated with *table* (i.e. *self*) into *headers* and
        # *rows*:
        headers: List[str]
        rows: List[List[str]]
        headers, rows = table.csv_file_read(table_csv_file_path)

        # Extract *column_tables* which is a list of dictionaries where each dictionary
        # has an occurence count for each unique value in a column:
        column_tables: List[Dict[str, int]] = table.column_tables_extract(rows)

        # Extract *type_tables* which is a list of dictionaries, where each dictionary
        # has an occurence count for each unique type name in the column:
        types_tables: List[Dict[str, int]] = table.type_tables_extract(column_tables)

        # If requested, bind the *types_tables* to *parameters*:
        if bind:
            table.parameters_bind(headers, types_tables)

        # We are done and can write out *table* now:
        table.xml_file_save(table_xml_file_path)

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

    # Table.parameters_bind():
    # @trace(1)
    def parameters_bind(self, headers: List[str], type_tables: List[Dict[str, int]]) -> None:
        """TODO."""
        # Grab *parameters* from *table* and make sure that there is a 1-to-1 correspondance
        # between *parameters* and *type_tables*:
        table: Table = self
        bom_manager: BomManager = table.bom_manager
        parameters: List[Parameter] = table.parameters_get(False)

        # Sweep through *Parameters* finding the *type_name* with the best match:
        index: int
        header: str
        # csv: str = ""
        # default: str = ""
        # optional: bool = False
        for index, header in enumerate(headers):
            # Convert *type_table* into *type_counts*:
            type_table: Dict[str, int] = type_tables[index]
            type_counts: List[Tuple[str, int]] = list(type_table.items())

            # Sort *type_counts* based on count:
            type_counts.sort(key=lambda name_count: (name_count[1], name_count[0]))

            # Grab the *name_count_last* which will have the highest count, and stuff
            # the associated *type_name* into *parameter*:
            name_count_last: Tuple[str, int] = type_counts[-1]
            type_name: str = name_count_last[0]

            parameter: Parameter
            if len(parameters) <= index:
                parameter = Parameter(bom_manager, header, type_name, index)
                table.parameter_insert(parameter)

                # Create an empty *english_parameter_comment* and stuff it into *parameter*:
                english_parameter_comment: ParameterComment = ParameterComment(bom_manager,
                                                                               language="EN")
                parameter.comment_insert(english_parameter_comment)
            else:
                assert False, "How do we get here?"
                parameter.type_name = type_name

    # Table.parameters_get():
    def parameters_get(self, sort: bool) -> List[Parameter]:
        """Return the a list of Parameters.

        Return the list of *Parameter*'s associated with *table*
        (i.e. *self*.)  If *sort* is *True*, sort the returned
        list by table name.

        Args:
            *sort* (*bool*): If *True*, sort returned *Parameter*'s
                list by name.

        Returns:
            Returns a list of *Parameter*'s from *table*.  They are
            sorted by name if *sort* is *True* otherwise thare are
            in semi-random order.

        """
        # Extrat the *parameters* from *table*:
        table: Table = self
        parameter_sub_nodes: List[Node] = table.sub_nodes_get(Parameter)
        parameter_sub_node: Node
        parameters: List[Parameter] = [parameter_sub_node.parameter_cast()
                                       for parameter_sub_node in parameter_sub_nodes]

        # Perform any requested *sort* before returning *parameters*:
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

    # Table.searches_get():
    def searches_get(self, sort: bool) -> List[Search]:
        """Return the *Search*'s from the *Table*.

        Return the list of *Search* objects from *table* (i.e. *self*.)
        If *sort* is *True*, sort the searches by they their key.

        Args:
            *sort* (*bool*): If *True*, sort the resulting list
                by the *Sort*.*Key*() function.

        Returns:
            Returns a list of *Search* objects.  If *sort* is *True*,
            the returned objects are sorted.

        """
        # Extract the *searches* from *table* (i.e. *self*):
        table: Table = self
        search_sub_nodes: List[Node] = table.sub_nodes_get(Search)
        search_sub_node: Node
        searches: List[Search] = [search_sub_node.search_cast()
                                  for search_sub_node in search_sub_nodes]

        # Perform any requested *sort* prior to returning *searches*:
        if sort:
            search: Search
            searches.sort(key=lambda search: search.name)
        return searches

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

    # Table.table_cast():
    def table_cast(self) -> "Table":
        """Return the *Table* object.

        Used for converting from a *Node* that happens to be a
        *Table* to *Table*.

        """
        table: Table = self
        return table

    # Table.type_tables_extract():
    # @trace(1)
    def type_tables_extract(self, column_tables: List[Dict[str, int]]) -> List[Dict[str, int]]:
        """TODO."""
        # The *re_table* comes from *gui* contains some regular expression for catagorizing
        # values.  The key of *re_table* is the unique *type_name* associated with the regular
        # expression that matches a given type.  The regular expressions are *PreCompiled*
        # to improve efficiency:
        table: Table = self
        bom_manager: BomManager = table.bom_manager
        re_table: Dict[str, PreCompiled] = bom_manager.re_table

        # Constuct *type_tables*, which is a list *type_table* that is 1-to-1 with the columns
        # in *column_tables*.  Each *type_table* collects a count of the number of column entries
        # that match a given *type_name*.  If none of the *type_names* match a given *value*,
        # the default *type_name* of "String" is used:
        type_tables: List[Dict[str, int]] = list()
        column_table: Dict[str, int]
        for column_table in column_tables:
            # Create *type_table*, create the "String" *type_name*, and tack it onto
            # *type_tables*:
            type_table: Dict[str, int] = dict()
            type_table["String"] = 0
            type_tables.append(type_table)

            # Sweep through *column_table* characterizing which values match which *type_names*:
            value: str
            count: int
            for value, count in column_table.items():
                type_name: str
                regex: PreCompiled
                match: bool = False
                # Now test *value* against *re* to see if we have a match:
                for type_name, regex in re_table.items():
                    if regex.match(value) is not None:
                        # We have a match, so make sure *type_name* is in *type_table*
                        # update the count appropriately:
                        if type_name in type_table:
                            type_table[type_name] += count
                        else:
                            type_table[type_name] = count
                        match = True

                # If we did not *match*, mark the *value* as a "String" type:
                if not match:
                    type_table["String"] += count
        return type_tables

    # Table.xml_file_save():
    def xml_file_save(self, file_path: Path, extra: str = "") -> None:
        """TODO."""
        # Compute *file_path_parent* directory for *file_path* and make sure it exists:
        table: Table = self
        file_path_parent: Path = file_path.parent
        tracing: str = tracing_get()
        if tracing:  # pragma: no cover
            print(f"{tracing}file_path='{file_path}'")
            print(f"{tracing}file_path_parent='{file_path_parent}'")
        file_path_parent.mkdir(parents=True, exist_ok=True)
        assert file_path_parent.is_dir(), f"'{file_path_parent}' is not a diretory"

        # Construct the final *xml_lines*:
        xml_lines: List[str] = list()
        xml_lines.append('<?xml version="1.0"?>')
        table.xml_lines_append(xml_lines, "", extra)
        xml_lines.append("")
        xml_text: str = '\n'.join(xml_lines)

        # Now write *xml_text* out to the *xml_path* file::
        xml_file: IO[Any]
        with file_path.open("w") as xml_file:
            xml_file.write(xml_text)

    # Table.xml_lines_append():
    def xml_lines_append(self, xml_lines: List[str], indent: str, extra: str) -> None:
        """TODO."""
        # Grab some values from *table* (i.e. *self*):
        table: Table = self
        bom_manager: BomManager = table.bom_manager
        name: str = table.name
        table_class_name: str = table.__class__.__name__

        # XML attributes need to be converted:
        to_attribute: Callable[[str], str] = bom_manager.to_attribute

        # Start by appending the `<TABLE_CLASS_NAME...>` element:
        xml_lines.append(f'{indent}<{table_class_name} '
                         f'name="{to_attribute(name)}" '
                         f'{extra}>')

        # Append the *parameters* to the *xml_lines*:
        parameters: List[Parameter] = table.parameters_get(True)
        next_indent: str = indent + "  "
        parameter: Parameter
        for parameter in parameters:
            parameter.xml_lines_append(xml_lines, next_indent)

        # Append the *table_comments* to *xml_lines*:
        table_comments: List[TableComment] = table.comments_get(True)
        table_comment: TableComment
        for table_comment in table_comments:
            table_comment.xml_lines_append(xml_lines, next_indent)

        # Append the *searches* to *xml_lines*:
        searches: List[Search] = table.searches_get(True)
        search: Search
        for search in searches:
            search.xml_lines_append(xml_lines, next_indent)

        # Close out with the `</TABLE_CLASS_NAME>` element:
        xml_lines.append(f'{indent}</{table_class_name}>')

    # Table.xml_parse():
    @staticmethod
    def xml_parse(table_element: Element, bom_manager: BomManager) -> "Table":
        """Parse an XML Elment into a *Table*.

        Parse *table_element* (i.e. *self*) into new *Table*
        object.

        Args:
            *table_element* (*Element*): The XML element to parse.
            *bom_manager* (*BomManager*): The root of all data
                structures.

        Returns:
            The created *Table* object.

        """
        assert table_element.tag == "Table"
        attributes_table: Dict[str, str] = table_element.attrib
        assert "name" in attributes_table
        # assert "file_name" in attributes_table
        name: str = attributes_table["name"]
        table: Table = Table(bom_manager, name)

        sub_elements: List[Element] = list(table_element)
        sub_element: Element
        for sub_element in sub_elements:
            sub_element_tag: str = sub_element.tag
            # if sub_element_tag == "Search":
            #     # sub_directory: Search = Search.xml_parse(sub_element, bom_manager)
            #     # directory.directory.search_insert(sub_directory)
            if sub_element_tag == "Parameter":
                parameter: Parameter = Parameter.xml_parse(sub_element, bom_manager)
                table.parameter_insert(parameter)
            elif sub_element_tag == "TableComment":
                table_comment: TableComment = TableComment.xml_parse(sub_element, bom_manager)
                table.comment_insert(table_comment)
            elif sub_element_tag == "Search":
                search: Search = Search.xml_parse(sub_element, bom_manager)
                table.search_insert(search)
            else:  # pragma: no cover
                assert False, f"Unprocessed tag='{sub_element_tag}'"
        return table


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
    # @trace(1)
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
    def remove(self, remove_node: Node) -> None:
        """TODO."""
        nodes: Nodes = self
        sub_nodes: Dict[int, Node] = nodes.sub_nodes
        nonce: int
        sub_node: Node
        for nonce, sub_node in sub_nodes.items():
            if remove_node is sub_node:
                del sub_nodes[nonce]
                break
        else:
            assert False


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
