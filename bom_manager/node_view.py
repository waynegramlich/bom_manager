"""Nodes and Views.

# Introduction

(This documentation is written in
[MarkDown](https://daringfireball.net/projects/markdown/.)

The data structures defined in this module are the core data structures
for representing BOM Manager data.  All developers who decide to work
on BOM Manager plugins, need to understand these data structures.

The top level data structures are:

* *BomManager*: There is exactly one of these objects in any given
  program instance.  This data structure provides the "global" state
  needed by all of the other data structures.
* *NodeTemplate*: A *NodeTemplate* object is used to specify how to
  create a *Node* object.  The *NodeTemplate*'s are stored in a table
  inside of the *BomManager* object.  There is exactly one
  *NodeTemplate* object for each *Node* sub-class.  (See immediately
  below.)
* *Node*: The *Node* object is the work horse object for storing data.
  All *Node* objects are sub-classed to provide additional attributes
  and methods.  In addition, each *Node* object may contain zero, one
  or more lists of sub-*Node*'s.
* *View*: The *View* object is used to bridge between the *Node*
  objects and any Graphical User Interface (i.e. GUI.)  The *View*
  object is designed to support multiple different GUI toolkit (e.g.
  PySide2, WxWidget, Web based frameworks, etc.)

Each of these data structures is discussed in separate sections below:

## *BomManager*

The *BomManager* object is where the global application data structures
are stored.  The following are important components of the *BomManager*
object:

* *node_templates* (*Dict*[*Type*, *NodeTemplate*]):
  *node_template* is a table that maps from a *Node* sub-class type
  to that *Node*'s associated *NodeTemplate* object.  This
  *NodeTemplate* is used by the *Node*.*__init__*() method to
  initialize a *Node* object.  (See *Node* object below.*

* *collection_table*: (*Dict*[*int*, *Collection*):
  The *collection_table* maintains a mapping between a unique
  colllection id and an associated *Collection*.  A *Collection* is
  sub-classed from a *Node* object (see below.)  Many methods use the
  *BomManager*.*collection_lookup*() method to map a collection key
  into the associated *Collection* object.

* Miscellaneous: Other miscellaneous and less interesting data is
  stored into the *BomManager* object as well -- precompiled regular
  expressions, etc.

The key thing to understand is that every *Node* has a back pointer to
the *BomManager* object.  Thus, *Node* sub-class objects can always
access the *BomManager* object to access "global" information.

## *NodeTemplate*:

The *NodeTemplate* object specifies all of the required attributes
and sub-*Node* lists associated with each object.  There is a
one-to-one correspondence between a *Node* sub-class and an associated
*NodeTemplate*.  All of the *NodeTemplate*'s are defined by the
*BomManager*.*__init__*() method and stored in the *node_templates*
table of the *BomManager* object.

Each *NodeTemplate* specifies the following:

* *node_type* (*Type*):
  The *node_type* is the type of the *Node*.

* *attributes_table* (*Dict*[*str*, *Type"]):
  This specifies required attributes for the *Node* sub-class and
  their associated type.  This is mostly used for data structure
  integrity checking.

* *sub_types* (*Tuple*[*Type*, ...]):
  The *sub_types* *Tuple* specifies one *Node* sub-class type for each
  permitted list of sub-*Node*'s.

* *views_table* (??):
  This lists all of the *View* objects used for Graphical User
  Interfaces (GUI's) that are registered for a given *Node* sub-class.
  See the *View* discussion further below for more about *View*
  objects.

## *Node*:

The *Node* object is the primary object for storing data.  Every
*Node* object is sub-classed.  These *Node* objects are organized
into acyclic trees.  An acylic tree has no cross links between
objects or objects that point back up to parent objects.  There
are no exceptions to this rule!

The primary data for the the BOM manager is stored in several root
*Node* trees.  These primary *Node* trees are quite persistent and
tend to stay in place for the life-time the application running.
In addition the Graphical User Interface may create some additional
*Node* trees that overlap with the primary *Node* trees to provide
alternative views into the BOM manager data structures.  These
alternative trees must still adhere to the no acyclic tree rule.

The core *Node* object is quite simple and consists of the following:

* *bom_manager* (*BomManager*):
  Every *Node* object points back to the one and only *BomManager*
  object.

* *nodes_table* (*Dict*[*Type*, *Nodes*]):
  The *nodes_table* is a dictionary that has one entry for each
  *Node* sub-type list that is supported.  The *Nodes* class is a
  helper class that is just a list of *Node* objects, all of the
  same type.

All other data in the *Node* object is provided by *Node* sub-class
attribute fields.

The *Node* class has a whole bunch of helper methods for use by the
*Node* sub-classes.  Please read the code for all of these methods
and what they do.

The data structures for managing collections, tables and searces are:

* *Group*: A *Group* is a collection of sub-*Group*'s and
  *Collection*s.  There are is one root *Group* object that contains
  all of the persistent data about *Group*'s, *Collection*'s, *Table*'s,
  *Parameters*'s, *Search*'s, etc.  Currently, the root *Group*
  tends to have a class sub-*Group* (e.g. "Engineering", "Food", etc.)
  and each class sub-*Group* has a further category sub-*Group*
  (e.g. "Electronics", "Mechanical", etc.)

* *Collection*: A *Collection* contains the information for a
  collection  of available parts.  Comceptully it very similar to a
  vendor catalog.  A *Collection* organized as a bunch of
  sub-*Directory*'s.

* *Directory*: A *Directory* contains an optional list of
  sub-*Directory*'s and an optional list of sub-*Table*'s.
  A *Directory* can be thought of as a section from a vendor catalog.

* *Table*: A *Table* object is the critical component of BOM Manager
  since is specifies a class of similar parts.  It has list of
  *Parameter*'s that specify various characteistics of each part.
  A *Search* (see immediately below) is used to narrow down the
  available parts to the one that is ultimately selected.

  Each *Table* object has the characteristic that it can be created
  and installed into its parent *Directory*, but it may not have
  read in all of the underlying table data yet.  This is called
  partial loading.  The underlying table data read in as it is needed.

* *Search*: A *Search* object specifies a set of characteristics
  needed to narrow down from a list of possible part candidates
  in a *Table* down to a list of acceptable part candidates.  The
  final selection of the final part occurs later in Bom Manager
  during the Pricing and Availability phase.

* *Comment*: A *Comment* is used to store textual information about
  a parent node.  Each *Comment* has a language specifier (e.g. "EN",
  "FR", etc.) so that a graphical user interface can be properly
  internationalized.  All of the *Nodes* above support *Comment*s.

There are other *Node* trees for other aspects of the Bom Manager.
They are discussed further below the *View* object discussion
immediately below.

## *View*

The *View* object is the intermediary between the *Node* object and
any Graphical User Interface (GUI.)  The *View* object is generic in
the sense that it is not tied down to any particular GUI toolkit
(e.g. QT, WxWidgets, Tkinter, etc.)  The current BOM Manager GUI
is implemented using QT using the PySide2 library, so it tends to
provide functionality needed for the PySide2 library.  However,
if someone gets enthusiastic and decides to impleant a differnt GUI
using a differnt GUI toolkit, it is assumed that some changes to
the View object will occur to accomedate the different GUI toolkit.

A *View* object contains the following:

* types_table (*Dict*[*Type*, *Callable*([*Node*], *Any) ):
  This is a mapping from a ...

The concept behind a *View* object is that it gets attached to one
or more *Node* sub-classes.  This is accomplished via the
*BomManager*.*view_attach*() method, which is called once for

## *Plugins*

The BOM Manager uses a plugin architecture to support expandability.
Each plugin can be registered at the
[Python Package Index Website](https://pypi.org/)
(e.g. `https://pypi.org/`.)
"""

# MIT License
#
# Copyright (c) 2019 Wayne C. Gramlich (Wayne@Gramlich.Net)
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
from bom_manager.tracing import tracing_get, trace  # , trace_level_set  # , tracing_get
import csv
import lxml.etree as ETree   # type: ignore
from lxml.etree import _Element as Element  # type: ignore
from pathlib import Path
import pkg_resources              # Used to find plug-ins.
import re
from typing import Any, Callable, Dict, IO, List, Optional, Tuple, Type
from typing import Any as PreCompiled
# Element = ETree._element
# from __future__ import annotations  # Needed for Python 3.7+


# BomManger:
class BomManager:
    """Contains top-level data structurs needed for the BOM Manager."""

    # @trace(1)
    def __init__(self) -> None:
        """Initialize the BomManger object."""
        group_node_template: NodeTemplate = NodeTemplate(Group, (Collection, Group),
                                                         {"name": str})
        collection_node_template: NodeTemplate = NodeTemplate(Collection, (Directory,),
                                                              {"name": str,
                                                               "collection_root": Path,
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
                                                          {"name": str})
        table_node_template: NodeTemplate = NodeTemplate(Table, (Parameter, Search, TableComment),
                                                         {"name": str,
                                                          "base": str,
                                                          "nonce": int,
                                                          "url": str})
        table_comment_node_template: NodeTemplate = NodeTemplate(TableComment, (),
                                                                 {"language": str,
                                                                  "lines": list})

        # All define *NodeTemplate*'s listed in alphabetical order:
        node_templates: Dict[Type, NodeTemplate] = {
            Collection: collection_node_template,
            Directory: directory_node_template,
            Group: group_node_template,
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
        self.collection_table: Dict[int, Collection] = dict()
        self.collection_table_nonce: int = 0
        self.empty_path = Path()

    # BomManager.collection_lookup():
    def collection_lookup(self, collection_key: int) -> "Collection":
        """Retreive a Collection using a key."""
        bom_manager: BomManager = self
        collection_table: Dict[int, Collection] = bom_manager.collection_table
        assert collection_key in collection_table, f"collection_key={collection_key} not present"
        collection: Collection = collection_table[collection_key]
        return collection

    # BomManager.collection_register():
    def collection_register(self, collection: "Collection") -> int:
        """Register a *Collection* and return its key.

        *bom_manager* (i.e. *self*) maintains a table of *Collection*
        objects.  Each one of these objects is given a unique
        integer *collection_key*.  This routine causes there to be a
        binding between *collection_key* and associated *collection* in
        *bom_manager*.  The *BomManager.collection_lookup*() method
        is used to retrieve this *collection* object.

        Args:
            *collection* (*Collecton*): The *collection* to register
                with *bom_manager*.

        Returns:
            (*int*) Returns the collection key.

        """
        # Grab some values from *bom_manager* (i.e. *self*):
        bom_manager: BomManager = self
        collection_table: Dict[int, Collection] = bom_manager.collection_table
        collection_key: int = bom_manager.collection_table_nonce
        collection_table[collection_key] = collection
        bom_manager.collection_table_nonce = collection_key + 1
        return collection_key

    # BomManager.collection_unregister()
    # def collection_unregister(self, collection_key: int):
    #     """Unregister a *Collection* using a key.
    #
    #     Args:
    #         *collection_key* (*int*): The key of the *Collection*
    #         to unregister.
    #
    #     """
    #     bom_manager: BomManager = self
    #     collection_table: Dict[int, Collection] = bom_manager.collection_table
    #     del collection_table[collection_key]

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
    # def node_template_add(self, node_template: "NodeTemplate") -> None:
    #     """TODO."""
    #     bom_manager: BomManager = self
    #     node_type: Type = node_template.node_type
    #     node_templates: Dict[Type, NodeTemplate] = bom_manager.node_templates
    #     assert node_type not in node_templates
    #     node_templates[node_type] = node_template

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


# NodeTemplate():
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
        self.attributes_table: Dict[str, Type] = attributes_table
        self.node_type: Type = node_type
        self.sub_types: Tuple[Type, ...] = sub_types
        self.views: Dict[View, View] = dict()

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


# Node:
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

    # Node.has_nodes():
    def has_nodes(self, nodes_type: Type) -> bool:
        """Verify that a node as specified sub-nodes.

        Args:
            *nodes_type* (*Type*): The type of nodes to verify
            the existance of.

        Returns:
            (*bool*) Returns *True* if the *nodes_type* is present and
                *False* otherwise.

        """
        node: Node = self
        nodes_table: Dict[Type, Nodes] = node.nodes_table
        match: bool = nodes_type in nodes_table
        return match

    # Node.name_get():
    def name_get(self) -> str:
        """Return the name of the node."""
        return "??"

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
        child_node_type: Type = child_node.__class__
        assert child_node_type in nodes_table, (f"node_type={child_node_type}, "
                                                f"nodes_table={nodes_table}")

        # Lookup the appropriate *nodes* object and stuff *child_node* into it:
        nodes: Nodes = nodes_table[child_node_type]
        nodes.insert(child_node)

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

    # Node.nodes_get():
    def nodes_get(self, node_type: Type) -> "Nodes":
        """Return a sub-*Nodes* object from a Node.

        This method returns the *Nodes* object from *node* (i.e. *self)
        that corresponds to *node_type*.

        This is an internal helper method that is meant to be used
        sparingly.  The manipulation of *Nodes* objects tend to be
        hidden away.

        Args:
            *node_type* (*Type*): The type selector to determine
                which *Nodes* object to return from *node*
                (i.e. *self*)

        Returns:
            Returns the selected *Nodes* object.

        """
        # Grab the appropriate *nodes* object from *node* (i.e. *self*) and return it:
        node: Node = self
        nodes_table: Dict[Type, Nodes] = node.nodes_table
        nodes: Nodes = nodes_table[node_type]
        return nodes

    # Node.Load():
    def load(self) -> None:
        """Place holder routine for nodes that can be partially loaded.

        This method is overridden by a sub-class if the sub-class *node*
        can be partially loaded.  If not, this method is called and does
        nothing.

        """
        pass

    # Node.remove():
    # @trace(1)
    def remove(self, sub_node: "Node") -> None:
        """Remove a sub-node from a Node.

        Args:
            *sub_node* (*Node*): Sub-node to remove.

        """
        node: Node = self
        nodes_table: Dict[Type, Nodes] = node.nodes_table
        sub_node_type: Type = sub_node.__class__
        assert sub_node_type in nodes_table, f"nodes_table={nodes_table}"
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

    # Node.tree_path_find():
    # @trace(1)
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

    # Node.type_letter_get():
    def type_letter_get(self):
        """Return a type letter for the node."""
        return '?'


# Collection:
class Collection(Node):
    """Represents a collection of parts tables."""

    # Collection.__init__():
    # @trace(1)
    def __init__(self, bom_manager: BomManager, name: str,
                 collection_root: Path, searches_root: Path) -> None:
        """Initialize the Collection.

        Initialize the *collection* (i.e. *self*) to have *bom_manager*,
        *name*, *collection_root*, and *searches_root*.  It is very
        important to call *Collection.key_set*() after the *collection*
        has been inserted into a *Group* object.

        Args:
            *bom_manager* (*BomManager*): The root of all the data
                structures.
            *name* (*str*): The name of the collection.
            *collection_root* (*Path*): The root directory where the
                collection directories and tables reside.
            *searches_root* (*Path*): The root directory of the
                mirror directory structure that contains the
                search related information.

        """
        # Initialize the *Node* super-class and stuff values into it.
        super().__init__(bom_manager)

        # Register *collection* (i.e. *self*) with *bom_manager*:
        collection: Collection = self
        collection_key: int = bom_manager.collection_register(collection)

        # Load up *collection* (i.e. *self*):
        self.collection_key: int = collection_key
        self.collection_root: Path = collection_root
        self.name: str = name
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

    # Collection.csvs_download():
    # @trace(1)
    def csvs_download(self, root_path: Path, csv_fetch: "Callable[[Table], str]") -> int:
        """Recursively download example .csv files for a collection.

        Recursively visit all of the *Tables* in *collection*
        (i.e. *self*) and ensure that example .csv files have been
        downloads and stored in the directory tree structure rooted
        at *root_path*.  *csv_fetch* is a function used to fetch the
        `.csv` file from a remote web server.

        Args:
            *root_path* (*Path*): Root of collection directory tree.
            *cvs_fetch* (*Callable*[[*Table*, *Path*, *int*], *int*]:
                A function used to fetch the `.csv` file for a given
                *table* from a provided *path*.  The third argument
                is a downloads count that is incremented and returned
                upon a successful load.

        """
        # Grab some values from *collection* (i.e. *self*):
        collection: Collection = self
        bom_manager: BomManager = collection.bom_manager

        # Create *collection_file_name*:
        collection_name: str = collection.name
        to_file_name: Callable[[str], str] = bom_manager.to_file_name
        collection_file_name: str = to_file_name(collection_name)

        # Create the *collection_root_path* which is an extra directory with
        # the collection name.  This is consistent with the organization of the
        # searches directories, where first directory specifies the collection name:
        collection_root_path: Path = root_path / collection_file_name

        # Recursively fetch `.csv` files for each table in *collection*:
        downloads_count: int = 0
        directories: List[Directory] = collection.directories_get(True)
        directory: Directory
        for directory in directories:
            # Create the *from_root_path* to the corresponding *directory* location
            # in the file system:
            directory_name: str = directory.name
            directory_file_name: str = to_file_name(directory_name)
            directory_path: Path = collection_root_path / directory_file_name

            # Now recursively visit each of the *directory* and fetch any appropiate `.csv` files:
            downloads_count += directory.csvs_download(directory_path, csv_fetch, downloads_count)
        return downloads_count

    # Collection.csvs_read_and_process():
    # @trace(1)
    def csvs_read_and_process(self, bind: bool) -> None:
        """Recusively catagorize tables from example .csv files.

        After all of the example `.csv` files have been recursively
        loaded by the *Collection*.*csvs_download* method, this
        method will recursively visit each of the example `.csv`
        and attempt to determine the type of each column
        (i.e. parameter.)

        Args:
            *bind* (*bool*): If *True*, the deduced types are actually
                bound the the table parameters.

        """
        # Grab the *csvs_directory* from *digikey* (i.e. *self*):
        collection: Collection = self
        bom_manager: BomManager = collection.bom_manager
        collection_root: Path = collection.collection_root

        # Convert the *digikey_collection* name into a *digikey_collection_file_path*:
        to_file_name: Callable[[str], str] = bom_manager.to_file_name
        collection_name: str = collection.name
        collection_file_name: str = to_file_name(collection_name)
        collection_directory_path: Path = collection_root / collection_file_name

        # Fetch example `.csv` files for each table in *digikey_collection*:
        sub_directories: List[Directory] = collection.directories_get(True)
        sub_directory: Directory
        for sub_directory in sub_directories:
            sub_directory_name: str = sub_directory.name
            sub_directory_file_name = to_file_name(sub_directory_name)
            sub_directory_path = collection_directory_path / sub_directory_file_name
            sub_directory.csv_read_and_process(sub_directory_path, bind)

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
        directories: List[Directory] = [Directory.from_node(directory_sub_node)
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

    # Collection.from_node():
    @staticmethod
    def from_node(node: Node) -> "Collection":
        """Cast a Node into a Colletion and return it."""
        assert isinstance(node, Collection)
        collection: Collection = node
        return collection

    # Collection.key_from_node():
    @staticmethod
    def key_from_node(node: Node) -> str:
        """TODO."""
        collection: Collection = Collection.from_node(node)
        key: str = collection.name
        return key

    # Collection.load_recursively():
    # @trace(1)
    def load_recursively(self, partial: bool) -> None:
        """Perform a partial load of the Collection.

        Recursively visit all of the associated directories, tables,
        and searches and load them.  If *partial* is *True*, the
        table/search is created but the associated `.xml`file is
        not read in.  If *partial* is *False*, the associated `.xml`
        is immediately read in.

        Args:
            *partial* (*bool*): Set to *True* to allow partial loading
                and *False* to force full immediate loading.

        """
        # Grab some values from *collection* (i.e. *self*):
        collection: Collection = self
        bom_manager: BomManager = collection.bom_manager
        collection_key: int = collection.collection_key
        collection_name: str = collection.name
        collection_root: Path = collection.collection_root
        searches_root: Path = collection.searches_root

        # Compute the *sub_collection_path* and *sub_searches_path*:
        collection_file_name: str = bom_manager.to_file_name(collection_name)
        sub_collection_path: Path = collection_root / collection_file_name
        sub_searches_path: Path = searches_root / collection_file_name

        # Perform a little *tracing*:
        tracing: str = tracing_get()
        if tracing:  # pragma: no cover
            print(f"{tracing}collection_name='{collection_name}'")
            print(f"{tracing}collection_root='{collection_root}'")
            print(f"{tracing}searches_root='{searches_root}'")
            print(f"{tracing}sub_collection_path='{sub_collection_path}'")
            print(f"{tracing}sub_searches_path='{sub_searches_path}'")

        assert sub_collection_path.is_dir(), f"'{sub_collection_path}' is not a directory"
        directory_name: str = collection_name
        directory: Directory = Directory(bom_manager, directory_name, collection_key)
        collection.directory_insert(directory)
        directory.load_recursively(sub_collection_path, sub_searches_path, collection_key, partial)

    # Collection.show_lines_append():
    def show_lines_append(self, show_lines: List[str], indent: str, text: str = "") -> None:
        """See node base class."""
        collection: Collection = self
        text = f"'{collection.name}'"
        super().show_lines_append(show_lines, indent, text=text)

    # Collection.xml_lines_append():
    def xml_lines_append(self, xml_lines: List[str], indent: str) -> None:
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
                         f'searches_root="{to_attribute(searches_root)}">')

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
        """Parse an XML Element into a *Collection*.

        Parse *collection_element* and stuff the resultes into
        a new *Collection* object.

        Args:
            *collect_element* (*Element*): The XML element to
                parse parse.
            *bom_manager* (*BomManager*): The root of all data
                structures.

        Returns:
            The created *Collection* object.

        """
        # Grab the attribute values from *collection_element*:
        assert collection_element.tag == "Collection"
        attributes_table: Dict[str, str] = collection_element.attrib
        assert "name" in attributes_table
        assert "collection_root" in attributes_table
        assert "searches_root" in attributes_table
        name: str = attributes_table["name"]
        collection_root: Path = Path(attributes_table["collection_root"])
        searches_root: Path = Path(attributes_table["searches_root"])

        # Create the *collection*:
        collection: Collection = Collection(bom_manager, name, collection_root, searches_root)
        collection_key: int = collection.collection_key

        # Visit each of the *collection* *sub_elements*:
        sub_elements: List[Element] = list(collection_element)
        sub_element: Element
        for sub_element in sub_elements:
            assert sub_element.tag == "Directory"
            directory: Directory = Directory.xml_parse(sub_element, bom_manager, collection_key)
            collection.directory_insert(directory)
        return collection


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

    # TableComment.from_node():
    def from_node(node: Node) -> "TableComment":
        """Cast a Node into at TableComment and return it."""
        assert isinstance(node, TableComment)
        table_comment: TableComment = node
        return table_comment

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

    # ParameterComment.from_node():
    def from_node(node: Node) -> "ParameterComment":
        """Cast a Node into a ParameterComment and return it."""
        assert isinstance(node, ParameterComment)
        parameter_comment: ParameterComment = node
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
    # @trace(1)
    def __init__(self, bom_manager: BomManager, name: str, collection_key: int,
                 url: str = "", nonce: int = -1) -> None:
        """Initialize a directory.

        Args:
            bom_manager (BomManager): The root of all of the data structures:
            name (str): A non-empty unicode string name.

        """
        # Initialize the super class and then stuff values into *directory* (i.e. *self*):
        # directory: Directory = self
        assert isinstance(name, str)
        assert isinstance(collection_key, int)
        super().__init__(bom_manager)
        self.collection_key: int = collection_key
        self.name: str = name
        self.nonce: int = nonce
        self.url: str = url

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

    # Directory.collection_get():
    def collection_get(self) -> "Collection":
        """Return the parent *Collection."""
        directory: Directory = self
        bom_manager: BomManager = directory.bom_manager
        collection_key: int = directory.collection_key
        assert isinstance(collection_key, int)
        collection: Collection = bom_manager.collection_lookup(collection_key)
        return collection

    # Directory.csvs_download():
    # @trace(1)
    def csvs_download(self, directory_path: Path,
                      csv_fetch: "Callable[[Table], str]", downloads_count: int) -> int:
        """TODO."""
        # Grab some values from *digikey_directory* (i.e. *self*):
        directory: Directory = self
        bom_manager: BomManager = directory.bom_manager
        to_file_name: Callable[[str], str] = bom_manager.to_file_name
        tracing: str = tracing_get()

        # First, visit all of the *sub_directories* from *directory*:
        sub_directories: List[Directory] = directory.sub_directories_get(True)
        sub_directory: Directory
        for sub_directory in sub_directories:
            sub_directory_name: str = sub_directory.name
            sub_directory_file_name: str = to_file_name(sub_directory_name)
            sub_directory_path: Path = directory_path / sub_directory_file_name
            if tracing:  # pragma: no cover
                print(f"{tracing}sub_directory_path='{sub_directory_path}")
            downloads_count += sub_directory.csvs_download(sub_directory_path,
                                                           csv_fetch, downloads_count)

        # Second, visit all of the *tables* of *directory*:
        tables: List[Table] = directory.tables_get(True)
        table: Table
        for table in tables:
            downloads_count += table.csv_download(directory_path, csv_fetch)
        return downloads_count

    # Directory.csv_read_and_process():
    # @trace(1)
    def csv_read_and_process(self, directory_path: Path, bind: bool) -> None:
        """Recursively process .csv files for column types.

        Recursiveily visit all of the tables and sub-directories of
        *directory* (i.e. *self*) and heruistically determine the
        column/parameter types.

        Args:
            *directory_path* (*Path*): The directory path for
                *directory* (i.e. *self*)
            *bind* (*bool*): If *True*, store the determined types
                into the associated table parameters.

        """
        # Grab some values from *directory* (i.e. *self*):
        directory: Directory = self
        bom_manager: BomManager = directory.bom_manager

        # Visit all of the *tables* in this *directory*:
        to_file_name: Callable[[str], str] = bom_manager.to_file_name
        sub_directories: List[Directory] = directory.sub_directories_get(True)
        sub_directory: Directory
        for sub_directory in sub_directories:
            sub_directory_name: str = sub_directory.name
            sub_directory_file_name: str = to_file_name(sub_directory_name)
            sub_directory_path: Path = directory_path / sub_directory_file_name
            sub_directory.csv_read_and_process(sub_directory_path, bind)

        # Visit all of the *digikey_tables* in this *digikey_directory*:
        tables: List[Table] = directory.tables_get(True)
        table: Table
        for table in tables:
            table.csv_read_and_process(directory_path, bind)

    # Directory.directory_insert():
    def directory_insert(self, sub_directory: "Directory") -> None:
        """Insert a sub_directory into a directory."""
        directory: Directory = self
        directory.node_insert(sub_directory)

    # Directory.from_node():
    @staticmethod
    def from_node(node: Node) -> "Directory":
        """Cast a Node into a Directory and return it."""
        assert isinstance(node, Directory)
        directory: Directory = node
        return directory

    # Directory.key_from_node():
    @staticmethod
    def key_from_node(node: Node) -> str:
        """Return a sort key for a directory Node."""
        directory: Directory = Directory.from_node(node)
        key: str = directory.name
        return key

    # Directory.load_recursively():
    # @trace(1)
    def load_recursively(self, collection_path: Path, searches_path: Path,
                         collection_key: int, partial: bool) -> None:
        """Recursively partially load a *Directory*.

        Recursively visit all of the associated directories, tables,
        and searches and load them.  If *partial* is *True*, the
        tables and searches are created but the backing `.xml`files
        are not read in.  If *partial* is *False*, the backing
        `.xml_files` are immediately read in.

        Args:
            *collection_path* (*Path*): The directory to look for
                sub-directories in.
            *searches_path (*Path*): The directory to eventually look for
                searches in.  This is recursively passed to lower levels
                for doing partial loads of searches.
            collection_key (*int*): The collection key needed to
                eventually create *Table* and *Search* objects.
            *partial* (*bool*): Set to *True* to allow partial loading
                and *False* to force full immediate loading.

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
                sub_path_name: str = bom_manager.from_file_name(sub_path_file_name)
                sub_directory: Directory = Directory(bom_manager, sub_path_name, collection_key)
                directory.directory_insert(sub_directory)

                # Now do a partial load of *sub_directory*:
                sub_searches_path = searches_path / sub_path_file_name
                sub_directory.load_recursively(sub_path, sub_searches_path, collection_key, partial)
            elif sub_path.suffix == ".xml":
                # We have a `.xml` file so we can create a *table* and insert it into *directory*:
                table_stem_file_name: str = sub_path.stem
                table_name: str = bom_manager.from_file_name(table_stem_file_name)
                table: Table = Table(bom_manager, table_name, collection_key)
                directory.table_insert(table)
                table.xml_path_set(sub_path)
                if not partial:
                    table.xml_load(collection_key)

                # Now do a partial load of *table*:
                sub_searches_path = searches_path / table_stem_file_name
                table.load_recursively(sub_searches_path, collection_key, partial)

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

    # Directory.table_insert():
    def table_remove(self, sub_table: "Table") -> None:
        """Remove a sub table from a directory.

        Args:
            sub_table (Table): The table to remove.

        """
        directory: Directory = self
        directory.remove(sub_table)

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
        tables: List[Table] = [Table.from_node(table_sub_node)
                               for table_sub_node in table_sub_nodes]

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
        sub_directories: List[Directory] = [Directory.from_node(sub_directory_node)
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
            table.xml_lines_append(xml_lines, next_indent)

        # Append the XML for any *sub_directories* to *xml_lines*:
        sub_directories: List[Directory] = directory.sub_directories_get(True)
        sub_directory: Directory
        for sub_directory in sub_directories:
            sub_directory.xml_lines_append(xml_lines, next_indent)

        # Output the closing *directory* XML element:
        xml_lines.append(f"{indent}</{directory_class_name}>")

    # Directory.xml_parse():
    @staticmethod
    def xml_parse(directory_element: Element, bom_manager: BomManager,
                  collection_key: int) -> "Directory":
        """Parse an XML Elment into a *Directory*.

        Parse *directory_element* (i.e. *self*) into new *Collection*
        object.

        Args:
            *directory_element* (*Element*): The XML element to parse.
            *bom_manager* (*BomManager*): The root of all data
                structures.
            *collection_key* (*int*): The key that can be used  to get
                the parent *Collection* object.

        Returns:
            The created *Directory* object.

        """
        assert directory_element.tag == "Directory"
        attributes_table: Dict[str, str] = directory_element.attrib
        assert "name" in attributes_table
        name: str = attributes_table["name"]
        directory: Directory = Directory(bom_manager, name, collection_key)

        sub_elements: List[Element] = list(directory_element)
        sub_element: Element
        for sub_element in sub_elements:
            sub_element_tag: str = sub_element.tag
            if sub_element_tag == "Directory":
                sub_directory: Directory = Directory.xml_parse(sub_element,
                                                               bom_manager, collection_key)
                directory.directory_insert(sub_directory)
            elif sub_element_tag == "Table":
                table: Table = Table.xml_parse(sub_element, bom_manager, collection_key)
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


# Group:
class Group(Node):
    """Represents a Group of  objects."""

    # Group.__init__():
    def __init__(self, bom_manager: BomManager, name: str) -> None:
        """Initialize a Group object.

        Initialize the *group* object.  Also register the
        the *group* object with *bom_manager*:

        Args:
            *name* (*str*): Name of the group object.
            *bom_manager* (*BomManager*): Contains all the root data
                structures.

        """
        # Initialize super-class of *group* (i.e. *self*):
        group: Group = self
        super().__init__(bom_manager)

        # Verify that *group* (i.e. *self*) has a *Nodes* object for containing
        # *Group*'s:
        assert group.has_nodes(Collection)
        assert group.has_nodes(Group)

        # Stuff values into *group* (i.e. *self*):
        self.name: str = name

    # Group.__str__():
    def __str__(self) -> str:
        """Return a string represention of a Group object."""
        # In order to support the *trace* decorator for the *__init__*() method, we can not
        # assume that the *name* attribute exists:
        group: Group = self
        name: str = "??"
        if hasattr(group, "name"):
            name = group.name
        return f"Group('{name}')"

    # Group.collection_insert():
    def collection_insert(self, collection: "Collection") -> None:
        """Insert a collection into a *Group* object.

        Insert *collection* into *group* (i.e. *self*.)

        Args:
            *collection* (*Collection*): The collection to insert.

        """
        # Grab some values from *group* (i.e. *self*):
        group: Group = self
        group.node_insert(collection)

    # Group.collections_get():
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
        group: Group = self
        collection_sub_nodes: List[Node] = group.sub_nodes_get(Collection)
        collection_sub_node: Node
        collections: List[Collection] = [Collection.from_node(collection_sub_node)
                                         for collection_sub_node in collection_sub_nodes]
        if sort:
            collections.sort(key=lambda collection: collection.name)
        return collections

    # Group.from_node():
    @staticmethod
    def from_node(node: Node) -> "Group":
        """Cast a Node into a Group and return it."""
        assert isinstance(node, Group)
        group: Group = node
        return group

    # Group.key_from_node():
    @staticmethod
    def key_from_node(node: Node) -> str:
        """Cast a Node into a Group and return it."""
        group: Group = Group.from_node(node)
        key: str = group.name
        return key

    # Group.name_get():
    def name_get(self) -> str:
        """Return the group name."""
        group: Group = self
        return group.name

    # Group.show_lines_append():
    def show_lines_append(self, show_lines: List[str], indent: str, text: str = "") -> None:
        """See node base class."""
        group: Group = self
        text = f"'{group.name}'"
        super().show_lines_append(show_lines, indent, text=text)

    # Group.show_lines_get():
    def show_lines_get(self) -> List[str]:
        """Return a list of lines for the Group object.

        For testing purposes, it is desirable to produce a textual
        representation of a tree.  This is the top level routine
        generates the reprensentation as a list of strings.

        Returns:
            A list of lines, where each line corresponds to one
            node in the tree.  The tree depth is indicated by
            the number preceeding spaces.

        """
        group: Group = self
        show_lines: List[str] = list()
        group.show_lines_append(show_lines, "")
        return show_lines

    # Group.show_lines_file_write():
    def show_lines_file_write(self, file_path: Path, indent: str) -> None:
        """Write *Group* out to file in show lines format.

        Generate a list of lines in show line format for the
        *Group* object (i.e. *self*).  Output this list of show
        lines to *file_path* with each line prefixed by *indent*.

        Args:
            *file_path* (Path): The file to write out to.
            *indent* (str): A string to prepend to each line.

        """
        group: Group = self
        show_lines: List[str] = group.show_lines_get()
        show_lines_text: str = "".join([f"{indent}{show_line}\n" for show_line in show_lines])
        show_lines_file: IO[Any]
        with file_path.open("w") as show_lines_file:
            show_lines_file.write(show_lines_text)

    # Group.sub_groups_get():
    def sub_groups_get(self, sort: bool) -> "List[Group]":
        """
        Return a list of sub-*Group*'s.

        Return a list of sub-*Group*'s associated with *group*
        (i.e. *self*.)  If *sort* is *True*, the returned list
        is sorted by sub-group name.

        Args:
            *sort* (*bool*): If *True*, the returned tables sorted by
                table name.

        Returns:
            Returns a list of *Group*'s that are sorted if *sort*
            is *True*:

        """
        # Extract *collections* from *collection
        group: Group = self
        group_sub_nodes: List[Node] = group.sub_nodes_get(Group)
        group_sub_node: Node
        sub_groups: List[Group] = [Group.from_node(group_sub_node)
                                   for group_sub_node in group_sub_nodes]
        if sort:
            sub_groups.sort(key=lambda sub_group: sub_group.name)
        return sub_groups

    # Group.sub_group_insert():
    def sub_group_insert(self, sub_group: "Group") -> None:
        """Insert a sub-*Group*.

        Insert *sub_group* into *group* (i.e. *self*).

        Args:
            *sub_group* (*Group*): The *Group* object to insert into
                *group* (i.e. *self*):

        """
        # Insert *sub_group* into *group* (i.e. *self*):
        group: Group = self
        group.node_insert(sub_group)

    # Group.type_letter_get():
    def type_letter_get(self) -> str:
        """Return the group type letter of 'G'."""
        return "G"

    # Group.packages_scan():
    @trace(1)
    def packages_scan(self, searches_root: Path) -> None:
        """Scan for collection packages.

        Using the magic of the *pkg_resources* module, find all of
        the Python modules that have been installed and have registered
        a "bom_manager_collection_get" entry point in their `setup.py`
        module configuration file.  Each such entry point is loaded
        and executed to create to obtain the collection name and its
        associated collection root directory *Path*.

        Args:
            *root_group* (*Group*): The ro
            *searches_root* (*Path*): The path to the searches root
                directory needed for creating each *Collection* object.

        """
        # Grab some values from *group* (i.e. *self*):
        group: Group = self
        bom_manager: BomManager = group.bom_manager

        # Sweep through *entry_point*'s that match *entry_point_key*:
        tracing: str = tracing_get()
        entry_point_key: str = "bom_manager_collection_get"
        index: int
        entry_point: pkg_resources.EntryPoint
        for index, entry_point in enumerate(pkg_resources.iter_entry_points(entry_point_key)):
            # Be parinoid and verify that the *entry_point* name is "collection_get":
            entry_point_name: str = entry_point.name
            if tracing:  # pragma: no cover
                print(f"{tracing}Collection_Entry_Point[{index}]: '{entry_point_name}'")
            assert entry_point_name == "collection_get"

            # Load the *entry_point* and verify that it is a function:
            collection_get: Callable[[], Tuple[str, str, Path]] = entry_point.load()
            assert callable(collection_get)

            # Invoke the *collection_get* entry point function to get the collection
            # name and root path:
            category_name: str
            collection_name: str
            collection_root: Path
            category_name, collection_name, collection_root = collection_get()
            if tracing:  # pragma: no cover
                print(f"{tracing}category_name='{category_name}'")
                print(f"{tracing}collection_name='{collection_name}'")
                print(f"{tracing}collection_root='{collection_root}'")

            # Since inter-module type checking not currenty performed by `mypy`, we get are
            # paranoid here and validate that we get acceptable return types:
            assert isinstance(category_name, str)
            assert isinstance(collection_name, str)
            assert isinstance(collection_root, Path)

            # Create the *catetgory_group* if necessary:
            if category_name != "":
                # We have *category_name* so we must find/create the matching *category_group*:
                sub_groups: List[Group] = group.sub_groups_get(False)
                sub_group: Group
                for sub_group in sub_groups:
                    # For now, disable test coverage on this code because we only have
                    # the Digi-Key collection.  Once we get a second electronics collection
                    # plug-in, we can remove the "# pragma: no cover" below:
                    if sub_group.name == category_name:  # pragma: no cover
                        group = sub_group
                        if tracing:  # pragma: no cover
                            print(f"{tracing}Found category group '{category_name}'")
                        break
                else:
                    if tracing:  # pragma: no cover
                        print(f"{tracing}Creating category group '{category_name}'")
                    category_group: Group = Group(bom_manager, category_name)
                    group.sub_group_insert(category_group)
                    group = category_group

            # Now we can create the new *collection* and insert it into *category_group*:
            collection: Collection = Collection(bom_manager, collection_name,
                                                collection_root, searches_root)
            group.collection_insert(collection)

    # Group.xml_lines_append():
    def xml_lines_append(self, xml_lines: List[str], indent: str) -> None:
        """Append XML for *Collection* to a list.

        Append the XML description of *collection* (i.e. *self*) to the *xml_lines* list.
        Each line is prefixed by *indent*.

        Args:
            *xml_lines*: *List*[*str*]: List of line to append individual XML lines to.
            *indent* (*str*): A prefix prepended to each line.

        """
        # Grab some values form *group* (i.e. *self*):
        group: Group = self
        bom_manager: BomManager = group.bom_manager

        # Append the initial element:
        to_attribute: Callable[[str], str] = bom_manager.to_attribute
        name: str = group.name
        xml_lines.append(f'{indent}<Group name="{to_attribute(name)}">')

        # First append any sorted sub-*Group*'s:
        next_indent: str = indent + "  "
        sub_groups: List[Group] = group.sub_groups_get(True)
        sub_group: Group
        for sub_group in sub_groups:
            sub_group.xml_lines_append(xml_lines, next_indent)

        # Now Append the sorted *collection*'s:
        collections: List[Collection] = group.collections_get(True)
        collection: Collection
        for collection in collections:
            collection.xml_lines_append(xml_lines, next_indent)

        # Append the closing element:
        xml_lines.append(f"{indent}</Group>")

    # Group.xml_parse():
    @staticmethod
    def xml_parse(group_element: Element, bom_manager: BomManager) -> "Group":
        """Parse an element tree into *Group* object.

        Parse the *group_element* into a *Group* object
        including all children *Node*'s.

        Args:
            *group_element* (*Element*): The XML Element object
                to parse.
            *bom_manager* (*BomManager*): The root of all data
                structures.

        Returns:
            The resulting parsed *Group* object.

        """
        # Perform the initial attribute extraction from *group* (i.e. *self*):
        assert group_element.tag == "Group", f"tag='{group_element.tag}'"
        attributes_table: Dict[str, str] = group_element.attrib
        assert "name" in attributes_table
        name: str = attributes_table["name"]

        # Now we create the *group* using *name*:
        group: Group = Group(bom_manager, name)

        # Parse each *sub-element* into either a *sub_group* or a *collection* and it into *group*:
        sub_elements: List[Element] = list(group_element)
        sub_element: Element
        for sub_element in sub_elements:
            sub_element_tag_name: str = sub_element.tag
            if sub_element_tag_name == "Collection":
                # We have *collection* to parse and insert into *group*:
                collection: Collection = Collection.xml_parse(sub_element, bom_manager)
                group.collection_insert(collection)
            elif sub_element_tag_name == "Group":
                # We have a *sub_group* to parse and insert into *group:
                sub_group: Group = Group.xml_parse(sub_element, bom_manager)
                group.sub_group_insert(sub_group)
            else:
                # This should never happen:
                assert False, f"Encountered bogus tag '{sub_element_tag_name}'"  # pragma: no cover
        return group


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
        parameter_comments: List[ParameterComment] = [
            ParameterComment.from_node(parameter_comment_sub_node)
            for parameter_comment_sub_node in parameter_comment_sub_nodes]

        # Perform any requested *sort* before returning:
        if sort:
            parameter_comments.sort(key=Comment.key)
        return parameter_comments

    # Parameter.from_node():
    @staticmethod
    def from_node(node: Node) -> "Parameter":
        """Cast Node into a Parameter and return it."""
        assert isinstance(node, Parameter)
        parameter: Parameter = node
        return parameter

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
    # @trace(1)
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

    # Parameter.xml_parse():
    @staticmethod
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
    def __init__(self, bom_manager: BomManager, name: str, collection_key: int) -> None:
        """Initailize a search object.

        Args:
            *bom_manager* (*BomManager*): The root of all of the data
                structures.
            *name* (*str*): The name of the search.
            *file_name* (*Path*): A path to a search `.xml` file.
            *collection_key* (*int*): The collection key for the
                *Collection* that contains this *search*.

        """
        # Intialize the super class:
        super().__init__(bom_manager)

        # Do some argument checking before stuffing the values into the *search* object:
        assert name, "Empty name!"
        # search: Search = self
        self.collection_key: int = collection_key
        self.loaded: bool = True
        self.name: str = name
        self.parent_name: str = ""
        self.xml_path: Path = bom_manager.empty_path

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

    # Search.collection_get():
    def collection_get(self) -> "Collection":
        """Return the parent collection."""
        search: Search = self
        bom_manager: BomManager = search.bom_manager
        collection_key: int = search.collection_key
        collection: Collection = bom_manager.collection_lookup(collection_key)
        return collection

    # Search.from_node():
    @staticmethod
    def from_node(node: Node) -> "Search":
        """Cast a Node into a Search and return it."""
        assert isinstance(node, Search)
        search: Search = node
        return search

    # Search.key_from_node():
    @staticmethod
    def key_from_node(node: Node) -> str:
        """Return a sort key for the Search Node."""
        search: Search = Search.from_node(node)
        key: str = search.name
        return key

    # Search.load():
    def load(self):
        """Ensure that Search is fully loaded."""
        assert False

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

    # Search.xml_load():
    # @trace(1)
    def xml_load(self, collection_key: int) -> None:
        """Ensure that the backing .xml file has been read in."""
        search: Search = self
        bom_manager: BomManager = search.bom_manager
        if not search.loaded:
            xml_path: Path = search.xml_path
            xml_text: str
            with xml_path.open() as xml_file:
                xml_text = xml_file.read()
            try:
                table_element: Element = ETree.fromstring(xml_text)
            except ETree.XMLSyntaxError:  # pragma: no cover
                assert False, f"XML Parse error in file '{xml_path}"
            Search.xml_parse(table_element, bom_manager, collection_key, search=search)
            search.loaded = True

    # Search.xml_parse():
    @staticmethod
    def xml_parse(search_element: Element, bom_manager: BomManager,
                  collection_key: int, search: "Optional[Search]" = None) -> "Search":
        """TODO."""
        assert search_element.tag == "Search"
        attributes_table: Dict[str, str] = search_element.attrib
        assert "name" in attributes_table
        name: str = attributes_table["name"]
        if search is None:
            search = Search(bom_manager, name, collection_key)
        else:
            assert search.name == name
        return search

    # Search.xml_path_set():
    # @trace(1)
    def xml_path_set(self, xml_path: Path) -> None:
        """Set the `.xml` path for the search.

        Set the full path name for *search* (i.e. *self*) to *xml_path*.
        This marks *search* as not being loaded.  The
        *Search*.*xml_load*() method is used to ensure that the
        associated `.xml` file has been read.

        Args:
            *xml_path* (*Path*): The *Path* for the `.xml` table associated
            for *search* (i.e. *self*.)

        """
        # Load values into *search* (i.e. *self*):
        search: Search = self
        search.loaded = False
        search.xml_path = xml_path


# Table:
class Table(Node):
    """Informatation about a parametric table of parts."""

    # Table.__init__():
    def __init__(self, bom_manager: BomManager, name: str, collection_key: int,
                 url: str = "", nonce: int = -1, base: str = "") -> None:
        """Initialize the Table.

        Initialize the table with a *bom_manager*, *name*,
        *collection_nonce*, etc.

        Args:
            *bom_manager* (BomManager): The top level data structure
                that is root of all of the trees.
            *name* (str): The non-empty name of the table.  Can
                contain *any* unicode characters.
            *collection_key* (*Tuple*[*int*, *int*]): The unique collection
                identifier that can be used to retrieve the parent
                *Collection* object.
            *url* (*str*) (Optional): A URL for accessing the parts
                associated with the table.
            *nonce* (*int*) (Optional): An optional identifier that
                that can be used for `.csv` file retrieval.
            *base*: (*str*) (Optional): An optional base string that
                can be sused for `.csv` file retreival.

        """
        # Initialize the *Node* super-class:
        super().__init__(bom_manager)

        # Do some argument verification:
        assert name, "Empty name string!"

        # Stuff values into *table* (i.e. *self*):
        # table: Table = self
        self.base: str = base
        self.collection_key: int = collection_key
        self.loaded: bool = True
        self.name: str = name
        self.nonce: int = nonce
        self.url: str = url
        self.xml_path: Path = bom_manager.empty_path

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

    # Table.collection_get():
    def collection_get(self) -> "Collection":
        """Return the parent *Collection*."""
        table: Table = self
        bom_manager: BomManager = table.bom_manager
        collection_key: int = table.collection_key
        collection: Collection = bom_manager.collection_lookup(collection_key)
        return collection

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
        assert rows, f"No data to extract for table '{table.name}'"
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
        table_comments: List[TableComment] = [TableComment.from_node(table_comment_sub_node)
                                              for table_comment_sub_node in table_comment_sub_nodes]

        # Perform any requested *sort* before returning *table_comments*:
        if sort:
            table_comments.sort(key=Comment.key)
        return table_comments

    # Table.csv_download():
    # @trace(1)
    def csv_download(self, directory_path: Path,
                     table_csv_fetch: "Callable[[Table], str]") -> int:
        """TODO."""
        # Grab some values from *table* (i.e. *self*):
        table: Table = self
        bom_manager: BomManager = table.bom_manager
        name: str = table.name

        # Construct the two likely file name locations:
        to_file_name: Callable[[str], str] = bom_manager.to_file_name
        name_csv_file_name: str = to_file_name(name) + ".csv"
        name_csv_file_path: Path = directory_path / name_csv_file_name

        # Perform any requested *tracing*:
        tracing: str = tracing_get()
        if tracing:  # pragma: no cover
            print(f"{tracing}directory_path='{directory_path}'")
            print(f"{tracing}name_csv_file_path='{name_csv_file_path}'")

        # See whether we already have the *name_csv_file_path*.
        downloads_count: int = 0
        if name_csv_file_path.is_file():
            # The *name_csv_file_path* file already exists and there nothing more to do:
            if tracing:  # pragma: no cover
                print(f"{tracing}File '{name_csv_file_path}' already exists.  Nothing to do.")
        else:
            # The *name_csv_file_path* does not exist and needs to be downloaded:
            if tracing:  # pragma: no cover
                print(f"{tracing}Download '{name_csv_file_path}'")
            csv_content: str = table_csv_fetch(table)
            name_csv_file: IO[Any]
            parent_directory_path: Path = name_csv_file_path.parent
            parent_directory_path.mkdir(parents=True, exist_ok=True)
            with name_csv_file_path.open("w") as name_csv_file:
                name_csv_file.write(csv_content)
            downloads_count = 1
        return downloads_count

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
                    else:  # pragma: no cover
                        print(f"Row {row_index+1} of '{csv_file_path}' has to many/few columns.")

        # Return the resulting *headers* and *rows*:
        return headers, rows

    # Table.csv_read_and_process():
    # @trace(1)
    def csv_read_and_process(self, directory_path: Path, bind: bool) -> None:
        """Determine table column/parameter types.

        Read in the associated example `.csv` file associated with
        *table* (i.e. *self*) and heuristically attempt to determine
        the type of each column (e.g. parameter).

        Args:
            *directory_path* (*Path*): The directory cont containing
                the example `.csv` to be read in.
            *bind* (*bool*): If *True*, the heuristically determined
                types are stored back into the the *table* *Parameter*'s.

        """
        # This delightful piece of code reads in a `.csv` file and attempts to categorize
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
        if tracing:  # pragma: no cover
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

    # Table.from_node():
    @staticmethod
    def from_node(node: Node) -> "Table":
        """Return a Node casted into a Table."""
        assert isinstance(node, Table)
        table: Table = node
        return table

    # Table.key_from_node():
    @staticmethod
    def key_from_node(node: Node) -> str:
        """Return a sort for the Table Node."""
        table: Table = Table.from_node(node)
        key: str = table.name
        return key

    # Table.load():
    def load(self):
        """Ensure that the Table is fully loaded."""
        assert False

    # Table.load_recursively():
    # @trace(1)
    def load_recursively(self, searches_path: Path, collection_key: int, partial: bool) -> None:
        """Partial load all of the searches from a directory.

        Recursively visit all of the associated searches and
        partially load them.   If *partial* is *True* the
        tables and searches are created, but the backing `.xml`
        file is not immediately read in.  If *partial* is *False*,
        the backing `.xml` file is immediately read int

        Args:
            *searches_path* (*Path*): The path to the directory
                containing the zero, one, or more, search `.xml` files.
            *collection_key* (*int*): The collection key need to create
                a new *Table* object.
            *partial* (*bool*): Set to *True* to allow partial loading
                and *False* to force full immediate loading.

        """
        # Make sure *searches_path* is actually a directory:
        if searches_path.is_dir():
            # *searches_path* is an existing directory that may have some search `.xml` files
            # in it.  So now we a scan *searches_path* looking for `.xml` files:
            table: Table = self
            bom_manager: BomManager = table.bom_manager
            all_search_encountered: bool = False
            searches_count: int = 0
            search_path: Path
            for search_path in searches_path.glob("*.xml"):
                # We have a *search* `.xml` file:
                search_stem_file_name: str = search_path.stem
                search_name: str = bom_manager.from_file_name(search_stem_file_name)
                if search_name == "@ALL":
                    all_search_encountered = True
                search: Search = Search(bom_manager, search_name, collection_key)
                table.search_insert(search)
                search.xml_path_set(search_path)
                if not partial:
                    search.xml_load(collection_key)
                searches_count += 1

            # If we found any search `.xml` files (i.e. *searches_count* >= 1), we need to ensure
            # that search named "@ALL" is created:
            if not all_search_encountered and searches_count:
                all_search: Search = Search(bom_manager, "@ALL", collection_key)
                table.search_insert(all_search)

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
            # else:
            #     assert False, f"headers={headers} length mismatch parameters{parameters}"
            #     parameter.type_name = type_name

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
        parameters: List[Parameter] = [Parameter.from_node(parameter_sub_node)
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
        searches: List[Search] = [Search.from_node(search_sub_node)
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

    # Table.type_tables_extract():
    # @trace(1)
    def type_tables_extract(self, column_tables: List[Dict[str, int]]) -> List[Dict[str, int]]:
        """TODO."""
        # The *re_table* comes from *gui* contains some regular expression for categorizing
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
        table.xml_lines_append(xml_lines, "")
        xml_lines.append("")
        xml_text: str = '\n'.join(xml_lines)

        # Now write *xml_text* out to the *xml_path* file::
        xml_file: IO[Any]
        with file_path.open("w") as xml_file:
            xml_file.write(xml_text)

    # Table.xml_lines_append():
    # @trace(1)
    def xml_lines_append(self, xml_lines: List[str], indent: str) -> None:
        """TODO."""
        # Grab some values from *table* (i.e. *self*):
        table: Table = self
        bom_manager: BomManager = table.bom_manager
        name: str = table.name
        nonce: int = table.nonce
        base: str = table.base
        url: str = table.url
        table_class_name: str = table.__class__.__name__

        # XML attributes need to be converted:
        to_attribute: Callable[[str], str] = bom_manager.to_attribute

        # Start by appending the `<TABLE_CLASS_NAME...>` element:
        name_text: str = f' name="{to_attribute(name)}"'
        nonce_text: str = f' nonce="{nonce}"' if nonce >= 0 else ""
        base_text: str = f' base="{to_attribute(base)}"' if base else ""
        url_text: str = f' url="{to_attribute(url)}"' if url else ""
        xml_lines.append(f'{indent}<{table_class_name}'
                         f'{name_text}{url_text}{nonce_text}{base_text}>')
        next_indent: str = indent + "  "

        # Append the *parameters* to the *xml_lines*:
        parameters: List[Parameter] = table.parameters_get(True)
        parameter: Parameter
        for parameter in parameters:
            parameter.xml_lines_append(xml_lines, next_indent)

        # Append the *table_comments* to *xml_lines*:
        table_comments: List[TableComment] = table.comments_get(True)
        table_comment: TableComment
        non_empty_table_comments: List[TableComment] = [table_comment
                                                        for table_comment in table_comments
                                                        if table_comment.lines]
        for table_comment in non_empty_table_comments:
            table_comment.xml_lines_append(xml_lines, next_indent)

        # Append the *searches* to *xml_lines*:
        searches: List[Search] = table.searches_get(True)
        search: Search
        for search in searches:
            search.xml_lines_append(xml_lines, next_indent)

        # Close out with the `</TABLE_CLASS_NAME>` element:
        xml_lines.append(f'{indent}</{table_class_name}>')

    # Table.xml_load():
    # @trace(1)
    def xml_load(self, collection_key: int) -> None:
        """Ensure that the backing .xml file has been read in."""
        table: Table = self
        bom_manager: BomManager = table.bom_manager
        if not table.loaded:
            xml_path: Path = table.xml_path
            xml_text: str
            with xml_path.open() as xml_file:
                xml_text = xml_file.read()
            table_element: Element = ETree.fromstring(xml_text)
            Table.xml_parse(table_element, bom_manager, collection_key, table=table)
            table.loaded = True

    # Table.xml_parse():
    @staticmethod
    # @trace(1)
    def xml_parse(table_element: Element, bom_manager: BomManager,
                  collection_key: int, table: "Optional[Table]" = None) -> "Table":
        """Parse an XML Elment into a *Table*.

        Parse *table_element* (i.e. *self*) intoe either new *Table*
        object or *Table* object that is passed in.

        Args:
            *table_element* (*Element*): The XML element to parse.
            *bom_manager* (*BomManager*): The root of all data
                structures.
            *collection_key* (*int*): The key that is used to get
                the parent *Collection*.
            *table* (*Optional*[*Table*]): (Optional) If present, the
                the parsed `.xml` is put into *table* rather than
                creating a new *Table* object.
        Returns:
            The *Table* object that has been created or updated.

        """
        # Make sure that *table_element* has the tag and appropriate attributes:
        assert table_element.tag == "Table"
        attributes_table: Dict[str, str] = table_element.attrib
        assert "name" in attributes_table
        base: str = attributes_table["base"] if "base" in attributes_table else ""
        name: str = attributes_table["name"]
        nonce: int = int(attributes_table["nonce"]) if "nonce" in attributes_table else -1
        url: str = attributes_table["url"] if "url" in attributes_table else ""

        # assert "file_name" in attributes_table
        tracing: str = tracing_get()
        if table is None:
            if tracing:  # pragma: no cover
                print(f"{tracing}Create table")
            table = Table(bom_manager, name, collection_key, url, nonce, base)
        else:
            if tracing:  # pragma: no cover
                print(f"{tracing}Use existing table")
            assert table.name == name, "Table name does not match"
            table.loaded = True

        sub_elements: List[Element] = list(table_element)
        sub_element: Element
        for sub_element in sub_elements:
            sub_element_tag: str = sub_element.tag
            # if sub_element_tag == "Search":
            #     # sub_directory: Search = Search.xml_parse(sub_element, bom_manager)
            #     # directory.directory.search_insert(sub_directory)
            if sub_element_tag == "Parameter":
                if tracing:  # pragma: no cover
                    print(f"{tracing}Parameter found")
                parameter: Parameter = Parameter.xml_parse(sub_element, bom_manager)
                table.parameter_insert(parameter)
            elif sub_element_tag == "TableComment":
                if tracing:  # pragma: no cover
                    print(f"{tracing}TableComment found")
                table_comment: TableComment = TableComment.xml_parse(sub_element, bom_manager)
                table.comment_insert(table_comment)
            elif sub_element_tag == "Search":
                if tracing:  # pragma: no cover
                    print(f"{tracing}Search found")
                search: Search = Search.xml_parse(sub_element, bom_manager, collection_key)
                table.search_insert(search)
            else:  # pragma: no cover
                assert False, f"Unprocessed tag='{sub_element_tag}'"
        return table

    # Table.xml_path_set():
    # @trace(1)
    def xml_path_set(self, xml_path: Path) -> None:
        """Set the `.xml` path for the table.

        Set the full path name for *table* (i.e. *self*) to *xml_path*.
        This marks *table* as not being loaded.  The
        *Table*.*xml_load*() method is used to ensure that the
        associated `.xml` file has been read.

        Args:
            *xml_path* (*Path*): The *Path* for the `.xml` table associated
            for *table* (i.e. *self*.)

        """
        # Load values into *table* (i.e. *self*):
        table: Table = self
        table.loaded = False
        table.xml_path = xml_path


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
        self.key_sort_function: Optional[Callable[[Node], Any]] = None
        self.sub_node_type: Type = sub_node_type
        self.sub_nodes: Dict[int, Node] = sub_nodes
        self.sorted_nodes: Optional[List[Node]] = None
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

        # Invalidate any previous *sorted_nodes*:
        nodes.sorted_nodes = None
        nodes.key_sort_function = None

    # Nodes.node_fetch():
    def node_fetch(self, index: int, key_sort_function: Callable[[Node], Any]) -> Node:
        """Return a Node from sorted Nodes list.

        This method returns the *index*'th *Node* from *nodes*
        (i.e. *self*) after it has been sorted using the
        *key_sort_function* for sort keys.  The *nodes* are cached
        so multiple calls using the same *key_sort_function* do not
        force a resort each time.  Any time the*key_sort_function*
        function changes or a *Node* is inserted/removed from *nodes*,
        a resort is forced.

        Args:
            *index* (*int*):
                The index into the sorted *nodes*'.
            *key_sort_function* (*Callable*[[*Node*], *Any*]):
                The function that returns a sorting key for each *Node*
                the *nodes* list.

        Returns:
            (*Node*):
                Returns *Node* at the *index*'th location of the sorted
                *nodes* list.

        """
        # Grab some values from *nodes*:
        nodes: Nodes = self
        sorted_nodes: Optional[List[Node]] = nodes.sorted_nodes

        # If *key_sort_function* changes, we must force a resort:
        if nodes.key_sort_function is not key_sort_function:
            # Remember the new *key_sort_function* and forget any previous *sorted_nodes*:
            nodes.key_sort_function = key_sort_function
            sorted_nodes = None

        # Make sure that we have *sorted_nodes* and that it is actually sorted:
        if sorted_nodes is None:
            sub_nodes: Dict[int, Node] = nodes.sub_nodes
            sorted_nodes = list(sub_nodes.values())
            nodes.sorted_nodes = sorted_nodes
            sorted_nodes.sort(key=key_sort_function)

        # Now *sorted_nodes* is sorted and we can perform the fetch operation:
        return sorted_nodes[index]

    # Nodes.nodes_collect_recursively():
    def nodes_collect_recursively(self, node_type: Type, nodes_list: List[Node]) -> None:
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

    # Nodes.remove():
    # @trace(1)
    def remove(self, remove_node: Node) -> None:
        """Remove a Node.

        Remove *remove_node* from *nodes* (i.e. *self*.)

        Args:
            *remove_node* (*Node*): The node to remove.

        """
        nodes: Nodes = self
        sub_nodes: Dict[int, Node] = nodes.sub_nodes
        nonce: int
        sub_node: Node
        for nonce, sub_node in sub_nodes.items():
            if remove_node is sub_node:
                del sub_nodes[nonce]
                break
        else:  # pragma: no cover
            assert False, "Node found in Nodes."

        # Invalidate any *sorted_nodes*:
        nodes.sorted_nodes = None
        nodes.key_sort_function = None

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

    # Nodes.size_get():
    def size_get(self) -> int:
        """Return the number of sub-nodes."""
        nodes: Nodes = self
        sub_nodes: Dict[int, Node] = nodes.sub_nodes
        sub_nodes_size: int = len(sub_nodes)
        return sub_nodes_size

    # Nodes.sub_nodes_get():
    def sub_nodes_get(self) -> List[Node]:
        """Return the sub nodes in arbitrary order."""
        nodes: Nodes = self
        sub_nodes: Dict[int, Node] = nodes.sub_nodes
        return list(sub_nodes.values())

    # Nodes.tree_path_find():
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


# View:
class View:
    """An interface to a GUI.

    This package has no explicit knowledge of a Graphic User Interface
    (i.e. GUI.)  The *View* class is used to bridge between the data
    structures in this package and the GUI.  The way it works is that
    most of the methods in this base class are templates that fail
    with an assertion failure.  A sub-class of the GUI must sub-class
    the *View* object and ..

    """

    # View.__init__():
    def __init__(self, name: str, root_node: Node,
                 view_selects_table: "Dict[Type, Tuple[ViewSelect, ...]]") -> None:
        """TODO."""
        # view: View = self
        self.name: str = name
        self.root_node: Node = root_node
        self.focus_path: List[Node] = [root_node]
        self.view_selects_table: Dict[Type, Tuple[ViewSelect, ...]] = view_selects_table

    # View.__str__():
    def __str__(self):
        """Return a string representation of a view."""
        name: str = "??"
        view: View = self
        if hasattr(view, "name"):
            name = view.name
        return f"View('{name}')"

    # View.can_fetch_more():
    @trace(2)
    def can_fetch_more(self, node: Node) -> bool:
        """Return True if the node has viewable sub-nodes.

        The *view* object (i.e. *self*) can specify which of any of the
        sub-*Node*'s in *node* need can be viewed.  Some *view* objects
        specify no viewable sub-*Nodes*, some specify that all
        sub-*Node*'s are viewable, and some specify a subset of all
        sub-*Nodes*s.  This method ensures that all sub-*Nodes* are
        loaded and the returns *True* if there at least one sub-*Node*
        in any of the *view* selected sub-*Nodes*; otherwise, *False*
        is returned.

        Args:
            *node* (*Node*): The *Node* object to examine for viewable
                sub-*Node*'s.

        Returns:
            (*bool*) Returns *True* if there are any viewable
                sub-*Node*'s

        """
        # Grab some values from *view* (i.e. *self*)
        view: View = self
        view_selects_table: Dict[Type, Tuple[ViewSelect, ...]] = view.view_selects_table

        # Force any partially loaded *node* to be fully loaded into memory.  This
        # ensures that any backing `.xml` files has been read:
        node.load()

        # Now figure out which *children_types* are allowed to be displayed:
        more_fetchable: bool = False
        node_type: Type = node.__class__
        assert node_type in view_selects_table, "Somehow View has encounterd an unexpected Node"
        view_selects: Tuple[ViewSelect, ...] = view_selects_table[node_type]

        # Note that *children_types* could be empty in which case the loop below exits immediately.
        # Otherwise, we visit the *child_nodes* for each *child_type* and see if there *Node*'s
        # present:
        view_select: ViewSelect
        for view_select in view_selects:
            view_type: Type = view_select.view_type
            view_nodes: Nodes = node.nodes_get(view_type)
            if view_nodes.size_get() >= 1:
                # We have at least one *Node*:
                more_fetchable = True
                break
        return more_fetchable

    # View.child_fetch()
    def child_fetch(self, parent_node: Node, row: int) -> Node:
        """TODO."""
        # Grab some values from *view* (i.e. *self*):
        view: View = self
        view_selects_table: Dict[Type, Tuple[ViewSelect, ...]] = view.view_selects_table

        # Grab the *viewable_children_types* associated with *parent_node_type*:
        parent_node_type: Type = parent_node.__class__
        assert parent_node_type in view_selects_table
        view_selects: Tuple[ViewSelect, ...] = view_selects_table[parent_node_type]

        # Iterate across each of the *viewable_children_types* summing up a total
        # *displayable_children_count:
        base_index: int = 0
        selected_child_node: Node
        view_select: ViewSelect
        for view_select in view_selects:
            view_type: Type = view_select.view_type
            view_nodes: Nodes = parent_node.nodes_get(view_type)
            view_nodes_size: int = view_nodes.size_get()
            if base_index <= row < base_index + view_nodes_size:
                # We can actually fetch *selected_child_node*:
                view_key_function: Callable[[Node], Any] = view_select.view_key_function
                selected_child_node = view_nodes.node_fetch(row - base_index, view_key_function)
                break
            base_index += view_nodes_size
        else:
            assert False, f"row={row} >= base_index={base_index}"
        return selected_child_node

    # View.has_children():
    @trace(2)
    def has_children(self, parent_node: Node) -> bool:
        """TODO."""
        view: View = self
        children_present: bool = view.row_count(parent_node) >= 1
        return children_present

    # View.row_count():
    @trace(2)
    def row_count(self, parent_node: Node) -> int:
        """Return the total number of displayable children.

        The *view* object (i.e. *self*) specifies which of the possible
        sub-*Node* lists in *parent_node* it is interested in displaying.
        The total number chilidren sub-*Node*'s across these *view*
        selected sub-*Node* lists is returned.

        Args:
            *parent_node* (*Node*): The parent *Node* object that
            contains the viewable children sub-*Node* lists.

        Returns:
            (*int*): Return the children count across all of the
            viewable childrent sub-*Node*s:

        """
        # Grab some values from *view*:
        view: View = self
        view_selects_table: Dict[Type, Tuple[ViewSelect, ...]] = view.view_selects_table

        # Grab the *viewable_children_types* associated with *parent_node_type*:
        parent_node_type: Type = parent_node.__class__
        view_selects: Tuple[ViewSelect, ...] = view_selects_table[parent_node_type]

        # Iterate across each of the *viewable_selects* summing up a total
        # *displayable_children_count:
        total_children_count: int = 0
        view_select: ViewSelect
        for view_select in view_selects:
            view_type: Type = view_select.view_type
            view_nodes: Nodes = parent_node.nodes_get(view_type)
            total_children_count += view_nodes.size_get()
        return total_children_count

    # parent_node_get()
    def parent_node_get(self, child_node: Node) -> Optional[Tuple[Node, int]]:
        """Return the parent node for the child node.

        Using *view* (i.e. *self*) find the appropriate parent *Node*
        object for *child_node*.  If the parent *Node* is found, the
        index to the child is returned as well.  If no parrent *Node*
        is found *None* is returned.

        Args:
            *child_node* (*Node*): The child *Node* object to find the
                *view* appropriate parent *Node* for.

        Returns:
            (*Optional*[*Node*, *int*]): Returns either the parent *Node* object
                and the index to the child.

        """
        # Grab some values from *view* (i.e. *self*):
        view: View = self
        view_selects_table: Dict[Type, Tuple[ViewSelect, ...]] = view.view_selects_table
        root_node: Node = view.root_node
        focus_path: List[Node] = view.focus_path

        # Leave *result* as *None* until we get a valid match:
        result: Optional[Tuple[Node, int]] = None

        # Quick lookup goes here.  For now stick with brute force:

        # If the quick lookup did not work, we perform a brute force recursive search:
        if result is None:
            # Clear out *focus_path* and then fill it in:
            focus_path = list()
            focus_path = root_node.tree_path_find(child_node, focus_path)
            child_node_type: Type = child_node.__class__
            if len(focus_path) >= 2:
                # We seem to have found *child_node*:
                assert focus_path[0] is child_node, "Something went wrong with Node.path_find()"
                probable_parent_node: Node = focus_path[1]

                # Now we need to find the *view_select* associated with *probably_parent_node*:
                probable_parent_node_type: Type = probable_parent_node.__class__
                if probable_parent_node_type in view_selects_table:
                    view_selects: Tuple[ViewSelect, ...]
                    view_selects = view_selects_table[probable_parent_node_type]

                    # Sweep through *view_select* looking for a match to *child_node_type*:
                    for view_select in view_selects:
                        view_type: Type = view_select.view_type
                        if view_type is child_node_type:
                            # This *view_type* matches the *child_node_type* so now we can
                            # extract the *nodes* that should contain the *child_node*:
                            nodes: Nodes = probable_parent_node.nodes_get(child_node_type)

                            # Now sweep through *nodes* looking for a match:
                            view_key_function: Callable[[Node], Any] = view_select.view_key_function
                            nodes_size: int = nodes.size_get()
                            index: int
                            for index in range(nodes_size):
                                possible_child_node: Node = nodes.node_fetch(index,
                                                                             view_key_function)
                                if possible_child_node is child_node:
                                    # We have a match, so set set *result* and break out of loops:
                                    result = (probable_parent_node, index)
                                    break
                            else:
                                assert False, (f"Child {child_node} not in parent "
                                               f"{probable_parent_node}")
                        else:
                            assert False, f"Parent node does not have child type"

                        # Break out of the outer loop if we have a *result*:
                        if result is not None:
                            break
                else:
                    assert False, "Child {child_node} not under root {root_node}"

        # Return the *result*:
        return result


class ViewSelect:
    """TODO."""

    def __init__(self, view_type: Type, view_key_function: Callable[[Node], Any]) -> None:
        """TODO."""
        self.view_type: Type = view_type
        self.view_key_function: Callable[[Node], Any] = view_key_function
