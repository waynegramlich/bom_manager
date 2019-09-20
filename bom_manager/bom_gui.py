#!/usr/bin/env python

# # BOM Manager GUI
#
# BOM Manager is a program for managing one or more Bill of Materials.
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

from bom_manager.bom import *
from bom_manager.tracing import trace, trace_level_get
from PySide2.QtUiTools import QUiLoader
from PySide2.QtWidgets import (QApplication, QComboBox, QLineEdit, QMainWindow,
                               QPlainTextEdit, QPushButton,
                               QTableWidget, QTableWidgetItem, QWidget)  # QTreeView
from PySide2.QtCore import (QAbstractItemModel, QCoreApplication, QFile, QItemSelectionModel,
                            QModelIndex, Qt)
from PySide2.QtGui import (QClipboard,)

def main(tracing=""):
    collection_directories, searches_root, order = command_line_arguments_process()

    # Now create the *tables_editor* graphical user interface (GUI) and run it:
    if tracing:
        print(f"{tracing}searches_root='{searches_root}'")
    tables = list()
    tables_editor = TablesEditor(tables, collection_directories, searches_root, order)

    # Start up the GUI:
    tables_editor.run()


# ComboEdit:
class ComboEdit:
    """ A *ComboEdit* object repesents the GUI controls for manuipulating a combo box widget.
    """

    # *WIDGET_CALLBACKS* is defined at the end of this class after all of the callback routines
    # are defined.
    WIDGET_CALLBACKS = dict()

    # ComboEdit.__init__():
    def __init__(self, name, tables_editor, items,
                 new_item_function, current_item_set_function, comment_get_function,
                 comment_set_function, is_active_function, tracing="", **widgets):
        """ Initialize the *ComboEdit* object (i.e. *self*.)

        The arguments are:
        * *name*: A name for the *ComboEdit* object (i.e. *self*) for debugging.
        * *tables_editor*: The root *TablesEditor* object.
        * *items*: A list of item objects to manage.
        * *new_item_function*: A function that is called to create a new item.
        * *is_active_function*: A function that returns *True* if combo box should be active.
        * *current_item_set_function*: A function that is called each time the current item is set.
        * *comment_get_function*: A function that is called to get the comment text.
        * *comment_set_function*: A function that is called to set the comment new comment text.
        * *tracing* (optional): The amount to indent when tracing otherwise *None* for no tracing:
        * *widgets*: A dictionary of widget names to widgets.  The following widget names
          are required:
          * "combo_box":    The *QComboBox* widget to be edited.
          * "comment_text": The *QComboPlainText* widget for comments.
          * "delete_button: The *QPushButton* widget that deletes the current entry.
          * "first_button": The *QPushButton* widget that moves to the first entry.
          * "last_button":  The *QPushButton* widget that moves to the last entry.
          * "line_edit":    The *QLineEdit* widget that supports new entry names and entry renames.
          * "next_button":  The *QPushButton* widget that moves to the next entry.
          * "new_button":   The *QPushButton* widget that create a new entry.
          * "previous_button": The *QPushButton* widget that moves tot the pervious entry.
          * "rename_button": The *QPushButton* widget that   rename_button_clicked,
        """

        # Verify argument types:
        assert isinstance(name, str)
        assert isinstance(items, list)
        assert callable(new_item_function)
        assert callable(current_item_set_function)
        assert callable(comment_get_function)
        assert callable(comment_set_function)
        assert callable(is_active_function)
        assert isinstance(tracing, str)
        widget_callbacks = ComboEdit.WIDGET_CALLBACKS
        widget_names = list(widget_callbacks)
        for widget_name, widget in widgets.items():
            assert widget_name in widget_names, (
              "Invalid widget name '{0}'".format(widget_name))
            assert isinstance(widget, QWidget), (
              "'{0}' is not a QWidget {1}".format(widget_name, widget))

        # Load some values into *combo_edit* (i.e. *self*):
        combo_edit = self
        combo_edit.comment_get_function = comment_get_function
        combo_edit.comment_set_function = comment_set_function
        combo_edit.comment_position = 0
        combo_edit.current_item_set_function = current_item_set_function
        combo_edit.is_active_function = is_active_function
        combo_edit.items = items
        combo_edit.name = name
        combo_edit.new_item_function = new_item_function
        combo_edit.tables_editor = tables_editor

        # Set the current item after *current_item_set_function* has been set.
        combo_edit.current_item_set(items[0] if len(items) > 0 else None)

        # Stuff each *widget* into *combo_edit* and connect the *widget* to the associated
        # callback routine from *widget_callbacks*:
        for widget_name, widget in widgets.items():
            # Store *widget* into *combo_edit* with an attribute name of *widget_name*:
            setattr(combo_edit, widget_name, widget)

            # Lookup the *callback* routine from *widget_callbacks*:
            callback = widget_callbacks[widget_name]

            # Using *widget* widget type, perform appropraite signal connection to *widget*:
            if isinstance(widget, QComboBox):
                # *widget* is a *QcomboBox* and generate a callback each time it changes:
                assert widget_name == "combo_box"
                widget.currentTextChanged.connect(partial(callback, combo_edit))
            elif isinstance(widget, QLineEdit):
                # *widget* is a *QLineEdit* and generate a callback for each character changed:
                assert widget_name == "line_edit"
                widget.textEdited.connect(partial(callback, combo_edit))
            elif isinstance(widget, QPushButton):
                # *widget* is a *QPushButton* and generat a callback for each click:
                widget.clicked.connect(partial(callback, combo_edit))
            elif isinstance(widget, QPlainTextEdit):
                # *widget* is a *QPushButton* and generate a callback for each click:
                widget.textChanged.connect(partial(callback, combo_edit))
                widget.cursorPositionChanged.connect(
                                                    partial(ComboEdit.position_changed, combo_edit))
            else:
                assert False, "'{0}' is not a valid widget".format(widget_name)

        # Wrap-up any requested *tracing*:
        if tracing:
            print("{0}<=ComboEdit.__init__(*, {1}, ...)".format(tracing, name))

    # ComboEdit.combo_box_changed():
    def combo_box_changed(self, new_name):
        """ Callback method invoked when the *QComboBox* widget changes:

        The arguments are:
        * *new_name*: The *str* that specifies the new *QComboBox* widget value selected.
        """

        # Verify argument types:
        assert isinstance(new_name, str)

        # Only do something if we are not already *in_signal*:
        combo_edit = self
        tables_editor = combo_edit.tables_editor
        if not tables_editor.in_signal:
            tables_editor.in_signal = True

            # Perform any requested signal tracing:
            trace_signals = tables_editor.trace_signals
            if trace_signals:
                print("=>ComboEdit.combo_box_changed('{0}', '{1}')".
                      format(combo_edit.name, new_name))

                # Grab *attributes* (and compute *attributes_size*) from *combo_edit* (i.e. *self*):
                items = combo_edit.items
                for index, item in enumerate(items):
                    if item.name == new_name:
                        # We have found the new *current_item*:
                        print("  items[{0}] '{1}'".format(index, item.name))
                        combo_edit.current_item_set(item)
                        break

            # Update the the GUI:
            tables_editor.update()

            # Wrap up any signal tracing:
            if trace_signals:
                print("<=ComboEdit.combo_box_changed('{0}', '{1}')\n".
                      format(combo_edit.name, new_name))
            tables_editor.in_signal = False

    # ComboEdit.comment_text_changed():
    def comment_text_changed(self):
        # Do nothing if we are in a signal:
        combo_edit = self
        tables_editor = combo_edit.tables_editor
        in_signal = tables_editor.in_signal
        if not in_signal:
            tables_editor.in_signal = True

            # Perform any requested signal tracing:
            trace_signals = tables_editor.trace_signals
            if trace_signals:
                print("=>ComboEdit.comment_text_changed()")

            # Extract *actual_text* from the *comment_plain_text* widget:
            comment_text = combo_edit.comment_text
            actual_text = comment_text.toPlainText()
            cursor = comment_text.textCursor()
            position = cursor.position()

            # Store *actual_text* into *current_comment* associated with *current_parameter*:
            item = combo_edit.current_item_get()
            if item is not None:
                combo_edit.comment_set_function(item, actual_text, position)

            # Force the GUI to be updated:
            tables_editor.update()

            # Wrap up any signal tracing:
            if trace_signals:
                print(" <=ComboEditor.comment_text_changed():{0}\n".format(cursor.position()))
            tables_editor.in_signal = False

    # ComboEdit.current_item_get():
    def current_item_get(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Perform any requested tracing:
        combo_edit = self
        current_item = combo_edit.current_item
        items = combo_edit.items

        # In general, we just want to return *current_item*. However, things can get
        # messed up by accident.  So we want to be darn sure that *current_item* is
        # either *None* or a valid item from *items*.

        # Step 1: Search for *current_item* in *tems:
        new_current_item = None
        for item in items:
            if item is current_item:
                # Found it:
                new_current_item = current_item

        # Just in case we did not find it, we attempt to grab the first item in *items* instead:
        if new_current_item is None and len(items) >= 1:
            new_current_item = items[0]

        # If the *current_item* has changed, we let the parent know:
        if new_current_item is not current_item:
            combo_edit.current_item_set(new_current_item)

        # Wrap up any requested *tracing*:
        if tracing:
            print("{0}=>ComboEdit.current_item_get".format(tracing, combo_edit.name))
        return new_current_item

    # ComboEdit.current_item_set():
    def current_item_set(self, current_item, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Perform any requested *tracing*:
        combo_edit = self
        combo_edit.current_item = current_item
        combo_edit.current_item_set_function(current_item)

    # ComboEdit.delete_button_clicked():
    def delete_button_clicked(self):
        # Perform any requested tracing from *combo_edit* (i.e. *self*):
        combo_edit = self
        tables_editor = combo_edit.tables_editor
        trace_signals = tables_editor.trace_signals
        if trace_signals:
            print("=>ComboEdit.delete_button_clicked('{0}')".format(combo_edit.name))

        # Find the matching *item* in *items* and delete it:
        tables_editor.in_signal = True
        items = combo_edit.items
        items_size = len(items)
        current_item = combo_edit.current_item_get()
        for index, item in enumerate(items):
            if item == current_item:
                # Delete the *current_item* from *items*:
                del items[index]
                items_size = len(items)

                # Update *current_item* in *combo_edit*:
                if 0 <= index < items_size:
                    current_item = items[index]
                elif 0 <= index - 1 < items_size:
                    current_item = items[index - 1]
                else:
                    current_item = None
                combo_edit.current_item_set(current_item)
                break

        # Update the GUI:
        tables_editor.update()

        # Wrap up any requested tracing;
        if trace_signals:
            print("<=ComboEdit.delete_button_clicked('{0}')\n".format(combo_edit.name))
        tables_editor.in_signal = False

    # ComboEdit.first_button_clicked():
    def first_button_clicked(self):
        # Perform any tracing requested by *combo_edit* (i.e. *self*):
        combo_edit = self
        tables_editor = combo_edit.tables_editor
        trace_signals = tables_editor.trace_signals
        if trace_signals:
            print("=>ComboEdit.first_button_clicked('{0}')".format(combo_edit.name))

        # If possible, select the *first_item*:
        tables_editor.in_signal = True
        items = combo_edit.items
        items_size = len(items)
        if items_size > 0:
            first_item = items[0]
            combo_edit.current_item_set(first_item)

        # Update the user interface:
        tables_editor.update()

        # Wrap up any requested tracing:
        if trace_signals:
            print("<=ComboEdit.first_button_clicked('{0})\n".format(combo_edit.name))
        tables_editor.in_signal = False

    # ComboEdit.gui_update():
    def gui_update(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Perform any requested *tracing* of *combo_edit* (i.e. *self*):
        combo_edit = self

        # Grab the widgets from *combo_edit* (i.e. *self*):
        combo_box = combo_edit.combo_box
        delete_button = combo_edit.delete_button
        first_button = combo_edit.first_button
        last_button = combo_edit.last_button
        line_edit = combo_edit.line_edit
        new_button = combo_edit.new_button
        next_button = combo_edit.next_button
        previous_button = combo_edit.previous_button
        rename_button = combo_edit.rename_button

        # If *current_item* *is_a_valid_item* we can enable most of the item widgets:
        current_item = combo_edit.current_item_get()
        items = combo_edit.items
        items_size = len(items)
        is_a_valid_item = current_item is not None
        combo_box.setEnabled(is_a_valid_item)
        # if tracing:
        #    print("{0}current_item='{1}'".
        #      format(tracing, "None" if current_item is None else current_item.name))

        # Changing the *combo_box* generates a bunch of spurious callbacks to
        # *ComboEdit.combo_box_changed()* callbacks.  The *combo_box_being_updated* attribute
        # is set to *True* in *combo_edit* so that these spurious callbacks can be ignored.
        combo_edit.combo_box_being_updated = True
        # print("combo_edit.combo_box_being_updated={0}".
        #  format(combo_edit.combo_box_being_updated))

        # Empty out *combo_box* and then refill it from *items*:
        combo_box.clear()
        current_item_index = -1
        for index, item in enumerate(items):
            combo_box.addItem(item.name)
            # if tracing:
            #    print("{0}[{1}]: '{2}".format(tracing, index,
            #      "--" if item is None else item.name))
            if item is current_item:
                combo_box.setCurrentIndex(index)
                current_item_index = index
                if tracing:
                    print("{0}match".format(tracing))
                break
        assert not is_a_valid_item or current_item_index >= 0
        # print("current_item_index={0}".format(current_item_index))
        # print("items_size={0}".format(items_size))

        # Read the comment *current_text* out:
        if current_item is None:
            current_text = ""
            position = 0
        else:
            current_text, position = combo_edit.comment_get_function(
              current_item)

        # Make sure that *current_text* is being displayed by the *comment_text* widget:
        comment_text = combo_edit.comment_text
        previous_text = comment_text.toPlainText()
        if previous_text != current_text:
            comment_text.setPlainText(current_text)

        # Set the cursor to be at *position* in the *comment_text* widget.  *cursor* is a
        # copy of the cursor from *comment_text*.  *position* is loaded into *cursor* which
        # is then loaded back into *comment_text* to actually move the cursor position:
        cursor = comment_text.textCursor()
        cursor.setPosition(position)
        comment_text.setTextCursor(cursor)

        # Figure out if *_new_button_is_visible*:
        line_edit_text = line_edit.text()
        # print("line_edit_text='{0}'".format(line_edit_text))
        no_name_conflict = line_edit_text != ""
        for index, item in enumerate(items):
            item_name = item.name
            # print("[{0}] attribute_name='{1}'".format(index, item_name))
            if item_name == line_edit_text:
                no_name_conflict = False
                # print("new is not allowed")
        # print("no_name_conflict={0}".format(no_name_conflict))

        # If *current_attribute* *is_a_valid_attribute* we can enable most of the attribute
        # widgets.  The first, next, previous, and last buttons depend upon the
        # *current_attribute_index*:
        combo_box.setEnabled(is_a_valid_item)
        delete_button.setEnabled(is_a_valid_item)
        first_button.setEnabled(is_a_valid_item and current_item_index > 0)
        last_button.setEnabled(is_a_valid_item and current_item_index + 1 < items_size)
        new_button.setEnabled(no_name_conflict)
        next_button.setEnabled(is_a_valid_item and current_item_index + 1 < items_size)
        previous_button.setEnabled(is_a_valid_item and current_item_index > 0)
        next_button.setEnabled(is_a_valid_item and current_item_index + 1 < items_size)
        rename_button.setEnabled(no_name_conflict)

        # Wrap up any requeted *tracing*:
        if tracing:
            print("{0}<=ComboEdit.gui_update('{1}')".format(tracing, combo_edit.name))

    # ComboEdit.items_replace():
    def items_replace(self, new_items):
        # Verify argument types:
        assert isinstance(new_items, list)

        # Stuff *new_items* into *combo_item*:
        combo_item = self
        combo_item.items = new_items

    # ComboEdit.items_set():
    def items_set(self, new_items, update_function, new_item_function, current_item_set_function):
        # Verify argument types:
        assert isinstance(new_items, list)
        assert callable(update_function)
        assert callable(new_item_function)
        assert callable(current_item_set_function)

        # Load values into *items*:
        combo_edit = self
        combo_edit.current_item_set_function = current_item_set_function
        combo_edit.items = new_items
        combo_edit.new_item_function = new_item_function
        combo_edit.update_function = update_function

        # Set the *current_item* last to be sure that the call back occurs:
        combo_edit.current_item_set(new_items[0] if len(new_items) > 0 else None, "items_set")

    # ComboEdit.last_button_clicked():
    def last_button_clicked(self):
        # Perform any tracing requested by *combo_edit* (i.e. *self*):
        combo_edit = self
        tables_editor = combo_edit.tables_editor
        trace_signals = tables_editor.trace_signals
        if trace_signals:
            print("=>ComboEdit.last_button_clicked('{0}')".format(combo_edit.name))

        # If possible select the *last_item*:
        tables_editor.in_signal = True
        items = combo_edit.items
        items_size = len(items)
        if items_size > 0:
            last_item = items[-1]
            combo_edit.current_item_set(last_item)

        # Update the user interface:
        tables_editor.update()

        # Wrap up any requested tracing:
        if trace_signals:
            print("<=ComboEdit.last_button_clicked('{0}')\n".format(combo_edit.name))
        tables_editor.in_signal = False

    # ComboEdit.line_edit_changed():
    def line_edit_changed(self, text):
        # Verify argument types:
        assert isinstance(text, str)

        # Make sure that we are not already in a signal before doing anything:
        combo_edit = self
        tables_editor = combo_edit.tables_editor
        if not tables_editor.in_signal:
            tables_editor.in_signal = True

            # Perform any requested siginal tracing:
            trace_signals = tables_editor.trace_signals

            # Make sure that the *combo_edit* *is_active*:
            is_active = combo_edit.is_active_function()
            if not is_active:
                # We are not active, so do not let the user type anything in:
                line_edit = combo_edit.line_edit
                line_edit.setText("")  # Erase whatever was just typed in!

            # Now just update *combo_edit*:
            combo_edit.gui_update()

            # Wrap up any requested signal tracing:
            if trace_signals:
                print("<=ComboEditor.line_edit_changed('{0}')\n".format(text))
            tables_editor.in_signal = False

    # ComboEdit.item_append():
    def item_append(self, new_item, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Perform any requested *tracing*:

        # Append *item* to *items* and make it current for *combo_edit* (i.e. *self*):
        combo_edit = self
        items = combo_edit.items
        items.append(new_item)
        combo_edit.current_item_set(new_item)

    # ComboEdit.new_button_clicked():
    def new_button_clicked(self):
        # Perform any tracing requested by *combo_edit* (i.e. *self*):
        combo_edit = self
        tables_editor = combo_edit.tables_editor
        trace_signals = tables_editor.trace_signals

        # Grab some values from *combo_edit*:
        tables_editor.in_signal = True
        items = combo_edit.items
        line_edit = combo_edit.line_edit
        new_item_function = combo_edit.new_item_function
        print("items.id=0x{0:x}".format(id(items)))

        # Create a *new_item* and append it to *items*:
        new_item_name = line_edit.text()
        # print("new_item_name='{0}'".format(new_item_name))
        new_item = new_item_function(new_item_name)
        combo_edit.item_append(new_item)

        # Update the GUI:
        tables_editor.update()

        # Wrap up any requested signal tracing:
        if trace_signals:
            print("<=ComboEdit.new_button_clicked('{0}')\n".format(combo_edit.name))
        tables_editor.in_signal = False

    # ComboEdit.next_button_clicked():
    def next_button_clicked(self):
        # Perform any tracing requested by *combo_edit* (i.e. *self*):
        combo_edit = self
        tables_editor = combo_edit.tables_editor
        trace_signals = tables_editor.trace_signals

        # ...
        tables_editor.in_signal = True
        items = combo_edit.items
        items_size = len(items)
        current_item = combo_edit.current_item_get()
        for index, item in enumerate(items):
            if item == current_item:
                if index + 1 < items_size:
                    current_item = items[index + 1]
                break
        combo_edit.current_item_set(current_item)

        # Update the GUI:
        tables_editor.update()

        # Wrap up any requested tracing:
        if trace_signals:
            print("<=ComboEdit.next_button_clicked('{0}')\n".format(combo_edit.name))
        tables_editor.in_signal = False

    # ComboEdit.position_changed():
    def position_changed(self):
        # Do nothing if we already in a signal:
        combo_edit = self
        tables_editor = combo_edit.tables_editor
        if not tables_editor.in_signal:
            tables_editor.in_signal = True

            # Perform any requested signal tracing:
            trace_signals = tables_editor.trace_signals

            # Grab the *actual_text* and *position* from the *comment_text* widget and stuff
            # both into the comment field of *item*:
            item = combo_edit.current_item_get()
            comment_text = combo_edit.comment_text
            cursor = comment_text.textCursor()
            position = cursor.position()
            actual_text = comment_text.toPlainText()
            combo_edit.comment_set_function(item, actual_text, position)

            # Wrap up any signal tracing:
            tables_editor.in_signal = False

    # ComboEdit.previous_button_clicked():
    def previous_button_clicked(self):
        # Perform any tracing requested by *combo_edit* (i.e. *self*):
        combo_edit = self
        tables_editor = combo_edit.tables_editor
        trace_signals = tables_editor.trace_signals

        # ...
        tables_editor.in_signal = True
        items = combo_edit.items
        current_item = combo_edit.current_item_get()
        for index, item in enumerate(items):
            if item == current_item:
                if index > 0:
                    current_item = items[index - 1]
                break
        combo_edit.current_item_set(current_item)

        # Update the GUI:
        tables_editor.update()

        tables_editor.in_signal = False

    # ComboEdit.rename_button_clicked():
    def rename_button_clicked(self):
        # Perform any tracing requested by *combo_edit* (i.e. *self*):
        combo_edit = self
        tables_editor = combo_edit.tables_editor
        trace_signals = tables_editor.trace_signals

        tables_editor.in_signal = True
        combo_edit = self
        line_edit = combo_edit.line_edit
        new_item_name = line_edit.text()

        current_item = combo_edit.current_item_get()
        if current_item is not None:
            current_item.name = new_item_name

        # Update the GUI:
        tables_editor.update()

        tables_editor.in_signal = False

    # ComboEdit.WIDGET_CALLBACKS:
    # *WIDGET_CALLBACKS* is defined here **after** the actual callback routines are defined:
    WIDGET_CALLBACKS = {
      "combo_box":       combo_box_changed,
      "comment_text":    comment_text_changed,
      "delete_button":   delete_button_clicked,
      "first_button":    first_button_clicked,
      "last_button":     last_button_clicked,
      "line_edit":       line_edit_changed,
      "next_button":     next_button_clicked,
      "new_button":      new_button_clicked,
      "previous_button": previous_button_clicked,
      "rename_button":   rename_button_clicked,
    }


# TablesEditor:
class TablesEditor(QMainWindow):

    # TablesEditor.__init__()
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

        # ui_qfile = QFile(os.path.join(order_root, "test.ui"))
        # ui_qfile.open(QFile.ReadOnly)
        # loader.registerCustomWidget(CheckableComboBox)
        # search_window = loader.load(ui_qfile)

        # for table in tables:
        #    break
        #    for parameter in table.parameters:
        #        if parameter.type == "enumeration":
        #            name = parameter.name
        #            checkable_combo_box = getattr(search_window, name + "_combo_box")
        #            enumerations = parameter.enumerations
        #            for enumeration in enumerations:
        #                checkable_combo_box.addItem(enumeration.name)
        #                #checkable_combo_box.setCheckable(True)

        # For debugging:
        # for table in tables:
        #    break
        #    parameters = table.parameters
        #    for index, parameter in enumerate(parameters):
        #        name = parameter.name
        #        radio_button = getattr(search_window, name + "_radio_button")
        #        print("[{0}]: Radio Button '{1}' {2}".format(index, name, radio_button))
        #        check_box = getattr(search_window, name + "_check_box")
        #        print("[{0}]: Check Box '{1}' {2}".format(index, name, check_box))
        #        if parameter.type == "enumeration":
        #            line_edit = getattr(search_window, name + "_combo_box")
        #        else:
        #            line_edit = getattr(search_window, name + "_line_edit")
        #        print("[{0}]: Line Edit '{1}' {2}".format(index, name, line_edit))

        # Grab the file widgets from *main_window*:

        # file_line_edit = main_window.file_line_edit
        # file_new_button = main_window.file_new_button
        # file_open_button = main_window.file_open_button

        # Connect file widgets to their callback routines:
        # file_line_edit.textEdited.connect(
        #  partial(TablesEditor.file_line_edit_changed, tables_editor))
        # file_new_button.clicked.connect(
        #  partial(TablesEditor.file_new_button_clicked, tables_editor))
        # file_open_button.clicked.connect(
        #  partial(TablesEditor.file_open_button_clicked, tables_editor))

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

        # Load all values into *tables_editor* before creating *combo_edit*.
        # The *ComboEdit* initializer needs to access *tables_editor.main_window*:
        current_table = tables[0] if len(tables) >= 1 else None
        tables_editor = self
        tables_editor.application = application
        tables_editor.collection_directories = collection_directories
        tables_editor.collections = None  # Filled in below
        tables_editor.current_comment = None
        tables_editor.current_enumeration = None
        tables_editor.current_model_index = None
        tables_editor.current_parameter = None
        tables_editor.current_search = None
        tables_editor.current_table = current_table
        tables_editor.current_tables = tables
        tables_editor.in_signal = True
        tables_editor.languages = ["English", "Spanish", "Chinese"]
        tables_editor.main_window = main_window
        tables_editor.order = order
        # tables_editor.original_tables = copy.deepcopy(tables)
        tables_editor.re_table = TablesEditor.re_table_get()
        tables_editor.searches_root = searches_root
        tables_editor.searches = list()
        tables_editor.xsearches = None
        tables_editor.tab_unload = None
        tables_editor.tables = tables
        # tables_editor.tracing_level = tracing_level
        # tables_editor.trace_signals = tracing_level >= 1

        # Set up *tables* first, followed by *parameters*, followed by *enumerations*:

        # Set up *tables_combo_edit* and stuff into *tables_editor*:
        new_item_function = partial(TablesEditor.table_new, tables_editor)
        current_item_set_function = partial(TablesEditor.current_table_set, tables_editor)
        comment_get_function = partial(TablesEditor.table_comment_get, tables_editor)
        comment_set_function = partial(TablesEditor.table_comment_set, tables_editor)
        is_active_function = partial(TablesEditor.table_is_active, tables_editor)
        tables_combo_edit = ComboEdit(
          "tables",
          tables_editor,
          tables,
          new_item_function,
          current_item_set_function,
          comment_get_function,
          comment_set_function,
          is_active_function,
          combo_box=main_window.tables_combo,
          comment_text=main_window.tables_comment_text,
          delete_button=main_window.tables_delete,
          first_button=main_window.tables_first,
          last_button=main_window.tables_last,
          line_edit=main_window.tables_line,
          next_button=main_window.tables_next,
          new_button=main_window.tables_new,
          previous_button=main_window.tables_previous,
          rename_button=main_window.tables_rename,
          )
        tables_editor.tables_combo_edit = tables_combo_edit

        # Set up *parameters_combo_edit* and stuff into *tables_editor*:
        parameters = list() if current_table is None else current_table.parameters
        new_item_function = partial(TablesEditor.parameter_new, tables_editor)
        current_item_set_function = partial(TablesEditor.current_parameter_set, tables_editor)
        comment_get_function = partial(TablesEditor.parameter_comment_get, tables_editor)
        comment_set_function = partial(TablesEditor.parameter_comment_set, tables_editor)
        is_active_function = partial(TablesEditor.parameter_is_active, tables_editor)
        parameters_combo_edit = ComboEdit(
          "parameters",
          tables_editor,
          parameters,
          new_item_function,
          current_item_set_function,
          comment_get_function,
          comment_set_function,
          is_active_function,
          combo_box=main_window.parameters_combo,
          comment_text=main_window.parameters_comment_text,
          delete_button=main_window.parameters_delete,
          first_button=main_window.parameters_first,
          last_button=main_window.parameters_last,
          line_edit=main_window.parameters_line,
          next_button=main_window.parameters_next,
          new_button=main_window.parameters_new,
          previous_button=main_window.parameters_previous,
          rename_button=main_window.parameters_rename,
          )
        tables_editor.parameters_combo_edit = parameters_combo_edit

        # Set up *enumerations_combo_edit* and stuff into *tables_editor*:
        enumerations = (
          list() if parameters is None or len(parameters) == 0 else parameters[0].enumerations)
        new_item_function = partial(TablesEditor.enumeration_new, tables_editor)
        current_item_set_function = partial(TablesEditor.current_enumeration_set, tables_editor)
        comment_get_function = partial(TablesEditor.enumeration_comment_get, tables_editor)
        comment_set_function = partial(TablesEditor.enumeration_comment_set, tables_editor)
        is_active_function = partial(TablesEditor.enumeration_is_active, tables_editor)
        enumerations_combo_edit = ComboEdit(
          "enumerations",
          tables_editor,
          enumerations,
          new_item_function,
          current_item_set_function,
          comment_get_function,
          comment_set_function,
          is_active_function,
          combo_box=main_window.enumerations_combo,
          comment_text=main_window.enumerations_comment_text,
          delete_button=main_window.enumerations_delete,
          first_button=main_window.enumerations_first,
          last_button=main_window.enumerations_last,
          line_edit=main_window.enumerations_line,
          next_button=main_window.enumerations_next,
          new_button=main_window.enumerations_new,
          previous_button=main_window.enumerations_previous,
          rename_button=main_window.enumerations_rename,
          )
        tables_editor.enumerations_combo_edit = enumerations_combo_edit

        # Now build the *searches_combo_edit* and stuff into *tables_editor*:
        searches = tables_editor.searches
        new_item_function = partial(TablesEditor.searches_new, tables_editor)
        current_item_set_function = partial(TablesEditor.current_search_set, tables_editor)
        comment_get_function = partial(TablesEditor.searches_comment_get, tables_editor)
        comment_set_function = partial(TablesEditor.searches_comment_set, tables_editor)
        is_active_function = partial(TablesEditor.searches_is_active, tables_editor)
        searches_combo_edit = ComboEdit(
          "searches",
          tables_editor,
          searches,
          new_item_function,
          current_item_set_function,
          comment_get_function,
          comment_set_function,
          is_active_function,
          combo_box=main_window.searches_combo,
          comment_text=main_window.searches_comment_text,
          delete_button=main_window.searches_delete,
          first_button=main_window.searches_first,
          last_button=main_window.searches_last,
          line_edit=main_window.searches_line,
          next_button=main_window.searches_next,
          new_button=main_window.searches_new,
          previous_button=main_window.searches_previous,
          rename_button=main_window.searches_rename,
          )
        tables_editor.searches = searches
        tables_editor.searches_combo_edit = searches_combo_edit

        # Perform some global signal connections to *main_window* (abbreviated as *mw*):
        mw = main_window
        mw.common_save_button.clicked.connect(tables_editor.save_button_clicked)
        mw.common_quit_button.clicked.connect(tables_editor.quit_button_clicked)
        mw.find_tabs.currentChanged.connect(tables_editor.tab_changed)
        mw.filters_down.clicked.connect(tables_editor.filters_down_button_clicked)
        mw.filters_up.clicked.connect(tables_editor.filters_up_button_clicked)
        mw.collections_check.clicked.connect(tables_editor.collections_check_clicked)
        mw.collections_process.clicked.connect(tables_editor.collections_process_clicked)
        mw.parameters_csv_line.textChanged.connect(tables_editor.parameter_csv_changed)
        mw.parameters_default_line.textChanged.connect(tables_editor.parameter_default_changed)
        mw.parameters_long_line.textChanged.connect(tables_editor.parameter_long_changed)
        mw.parameters_optional_check.clicked.connect(tables_editor.parameter_optional_clicked)
        mw.parameters_short_line.textChanged.connect(tables_editor.parameter_short_changed)
        mw.parameters_type_combo.currentTextChanged.connect(tables_editor.parameters_type_changed)
        mw.schema_tabs.currentChanged.connect(tables_editor.tab_changed)
        mw.searches_save.clicked.connect(tables_editor.searches_save_button_clicked)
        mw.searches_table_combo.currentTextChanged.connect(tables_editor.searches_table_changed)
        mw.root_tabs.currentChanged.connect(tables_editor.tab_changed)

        mw.collections_new.clicked.connect(tables_editor.collections_new_clicked)
        mw.collections_new.setEnabled(False)
        mw.collections_line.textChanged.connect(tables_editor.collections_line_changed)
        mw.collections_tree.clicked.connect(tables_editor.collections_tree_clicked)
        mw.collections_delete.clicked.connect(tables_editor.collections_delete_clicked)
        mw.collections_delete.setEnabled(False)

        # file_names = glob.glob("../digikey_tables/**", recursive=True)
        # file_names.sort()
        # print("file_names=", file_names)

        # Create the *tree_model* needed for *collections* and stuff into *tables_editor*:
        tree_model = TreeModel()
        tables_editor.model = tree_model

        # Create the *collections* and stuff into *tables_editor*:
        collections = Collections("Collections", collection_directories, searches_root, tree_model,
                                  )
        tables_editor.collections = collections

        # Now stuff *collections* into *tree_model*:
        tree_model.collections_set(collections)

        # Now that both *collections* and *tree_mode* refer to one another we can safely
        # call *partial_load*():
        collections.partial_load()

        # Now bind *tree_model* to the *collections_tree* widget:
        collections_tree = mw.collections_tree
        collections_tree.setModel(tree_model)
        collections_tree.setSortingEnabled(True)

        # FIXME: Used *tables_editor.current_update()* instead!!!
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

        # tables_editor.table_setup()

        # Read in `searches.xml` if it exists:
        # tables_editor.searches_file_load(os.path.join(order_root, "searches.xml"),
        #                                  )

        # Update the entire user interface:
        tables_editor.update()

        tables_editor.in_signal = False

    # TablesEditor.__str__():
    def __str__(self):
        return "TablesEditor"

    # TablesEditor.comment_text_set()
    def comment_text_set(self, new_text, tracing=""):
        # Verify argument types:
        assert isinstance(new_text, str)
        assert isinstance(tracing, str)

        # Carefully set thet text:
        tables_editor = self
        main_window = tables_editor.main_window
        comment_text = main_window.parameters_comment_text
        comment_text.setPlainText(new_text)

    # TablesEditor.collections_delete_changed():
    @trace(1)
    def collections_delete_clicked(self, tracing=""):
        assert isinstance(tracing, str)
        # Perform any requested signal *tracing* for *tables_editor* (i.e. *self*):
        tables_editor = self

        # Grab the *current_model_index* from *tables_editor* and process it if it exists:
        current_model_index = tables_editor.current_model_index
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
                        tables_editor.current_model_index = None
                        tables_editor.current_search = None
                    else:
                        if tracing:
                            print(f"Here 3")
                        search_parent_name = search_parent.name
                        if tracing:
                            print(f"{tracing}Parent is '{search_parent_name}'")
                        main_window = tables_editor.main_window
                        collections_tree = main_window.collections_tree
                        selection_model = collections_tree.selectionModel()
                        collections_line = main_window.collections_line
                        collections_line.setText(search_parent_name)
                        flags = (QItemSelectionModel.ClearAndSelect | QItemSelectionModel.Rows)
                        selection_model.setCurrentIndex(parent_search_model_index, flags)
                        tables_editor.current_model_index = parent_search_model_index
                        tables_editor.current_search = search_parent

                    # Remove the associated files `.xml` and `.csv` files (if they exist):
                    if tracing:
                        print(f"Here 4")
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
        tables_editor.update()

    # TablesEditor.collections_line_changed():
    @trace(1)
    def collections_line_changed(self, text, tracing=""):
        # Verify argument types:
        assert isinstance(text, str)
        assert isinstance(tracing, str)

        # Make sure that *tables_editor* (i.e. *self*) is updated:
        tables_editor = self
        tables_editor.update()

    # TablesEditor.collections_new_clicked():
    @trace(1)
    def collections_new_clicked(self, tracing=""):
        # Perform any requested *tracing*:
        tables_editor = self
        # Grab some values from *tables_editor* (i.e. *self*):
        current_search = tables_editor.current_search

        # Make sure *current_search* exists (this button click should be disabled if not available):
        assert current_search is not None

        # clip_board = pyperclip.paste()
        # selection = os.popen("xsel").read()
        application = tables_editor.application
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
            # Grab some stuff from *tables_editor*:
            main_window = tables_editor.main_window
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

            model_index = tables_editor.current_model_index
            if model_index is not None:
                parent_model_index = model_index.parent()
                tree_model = model_index.model()
                tree_model.children_update(parent_model_index)

            # model = tables_editor.model
            # model.insertNodes(0, [ new_search ], parent_model_index)
            # if tracing:
            #    print("{0}2:len(searches)={1}".format(tracing, len(searches)))

            tables_editor.update()

    # TablesEditor.collections_check_clicked():
    @trace(1)
    def collections_check_clicked(self, tracing=""):
        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self

        # Delegate checking to *order* object:
        collections = tables_editor.collections
        order = tables_editor.order
        order.check(collections)

    # TablesEditor.collections_process_clicked():
    @trace(1)
    def collections_process_clicked(self, tracing=""):
        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self

        # Grab some values from *tables_editor*:
        collections = tables_editor.collections
        order = tables_editor.order

        # Now process *order* using *collections*:
        order.process(collections)

    # TablesEditor.collections_tree_clicked():
    @trace(1)
    def collections_tree_clicked(self, model_index, tracing=""):
        # Verify argument types:
        assert isinstance(model_index, QModelIndex)
        assert isinstance(tracing, str)

        # Stuff *model_index* into *tables_editor* (i.e. *self*):
        tables_editor = self
        tables_editor.current_model_index = model_index

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
        node.clicked(tables_editor, model_index)

        # *Search* *node*'s get some additional treatment:
        if isinstance(node, Search):
            main_window = tables_editor.main_window
            collections_line = main_window.collections_line
            collections_line.setText(node.name)

        # Lastly, tell *tables_editor* to update the GUI:
        tables_editor.update()

    # TablesEditor.collections_update():
    @trace(1)
    def collections_update(self, tracing=""):
        # Perform argument testing:
        assert isinstance(tracing, str)

        # Grab some widgets from *tables_editor*:
        tables_editor = self
        main_window = tables_editor.main_window
        collections_delete = main_window.collections_delete
        collections_line = main_window.collections_line
        collections_new = main_window.collections_new

        # Grab the *current_search* object:
        current_search = tables_editor.current_search
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

    # TablesEditor.current_enumeration_set()
    def current_enumeration_set(self, enumeration, tracing=""):
        # Verify argument types:
        assert isinstance(enumeration, Enumeration) or enumeration is None, \
          "{0}".format(enumeration)
        assert isinstance(tracing, str)

        # Only do something if we are not in a signal:
        tables_editor = self
        if not tables_editor.in_signal:
            tables_editor.in_signal = True

            # Perform any tracing requested signal tracing:
            trace_signals = tables_editor.trace_signals
            if trace_signals:
                print("=>TablesEditor.current_enumeration_set('{0}')".
                      format("None" if enumeration is None else enumeration.name))

            # Finally, set the *current_enumeration*:
            tables_editor.current_enumeration = enumeration

            # Wrap up any requested tracing:
            if trace_signals:
                print("<=TablesEditor.current_enumeration_set('{0}')\n".
                      format("None" if enumeration is None else enumeration.name))
            tables_editor.in_signal = False

    # TablesEditor.current_parameter_set()
    def current_parameter_set(self, parameter, tracing=""):
        # Verify argument types:
        assert isinstance(parameter, Parameter) or parameter is None
        assert isinstance(tracing, str)

        # Perform any requested *tracing*:
        if tracing:
            name = "None" if parameter is None else parameter.name
            print("{0}=>TablesEditor.current_parameter_set(*, '{1}')".format(tracing, name))

        # Set the *current_parameter* in *tables_editor*:
        tables_editor = self
        tables_editor.current_parameter = parameter

    # TablesEditor.current_search_set()
    def current_search_set(self, new_current_search, tracing=""):
        # Verify argument types:
        assert isinstance(new_current_search, Search) or new_current_search is None, \
          print(new_current_search)
        assert isinstance(tracing, str)

        # Make sure *new_current_search* is in *searches*:
        tables_editor = self
        searches = tables_editor.searches
        if new_current_search is not None:
            for search_index, search in enumerate(searches):
                assert isinstance(search, Search)
                if tracing:
                    print("{0}Search[{1}]: '{2}'".format(tracing, search_index, search.name))
                if search is new_current_search:
                    break
            else:
                assert False
        tables_editor.current_search = new_current_search

    # TablesEditor.current_table_set()
    def current_table_set(self, new_current_table, tracing=""):
        # Verify argument types:
        assert isinstance(new_current_table, Table) or new_current_table is None
        assert isinstance(tracing, str)

        # Stuff *new_current_table* into *tables_editor*:
        tables_editor = self
        if new_current_table is not None:
            tables = tables_editor.tables
            for table in tables:
                if table is new_current_table:
                    break
            else:
                assert False, "table '{0}' not in tables list".format(new_current_table.name)
        tables_editor.current_table = new_current_table


    # TablesEditor.current_update()
    def current_update(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Make sure *current_table* is valid (or *None*):
        tables_editor = self
        tables = tables_editor.tables
        tables_size = len(tables)
        current_table = None
        if tables_size >= 1:
            # Figure out if *current_table* is in *tables):
            current_table = tables_editor.current_table
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
        tables_editor.current_table = current_table
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
                current_parameter = tables_editor.current_parameter
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
        tables_editor.current_parameter = current_parameter
        if tracing:
            print("{0}current_parameter='{1}'".
                  format(tracing, "None" if current_parameter is None else current_parameter.name))

        # Update *parameters* in *parameters_combo_edit*:
        parameters_combo_edit = tables_editor.parameters_combo_edit
        parameters_combo_edit.items_replace(parameters)

        # Make sure *current_enumeration* is valid (or *None*):
        current_enumeration = None
        if current_parameter is None:
            enumerations = list()
        else:
            enumerations = current_parameter.enumerations
            enumerations_size = len(enumerations)
            if enumerations_size >= 1:
                current_enumeration = tables_editor.current_enumeration
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
        tables_editor.current_enumeration = current_enumeration

        # Make sure that *current_search* is valid (or *None*):
        # tables_editor.current_search = current_search

        if tracing:
            print("{0}current_enumeration'{1}'".format(
              tracing, "None" if current_enumeration is None else current_enumeration.name))

        # Update *enumerations* into *enumerations_combo_edit*:
        enumerations_combo_edit = tables_editor.enumerations_combo_edit
        enumerations_combo_edit.items_replace(enumerations)

        # Make sure that *current_search* is valid (or *None*):
        searches = tables_editor.searches
        current_search = tables_editor.current_search
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
        tables_editor.current_search = current_search
        if tracing:
            print("{0}current_search='{1}'".
                  format(tracing, "None" if current_search is None else current_search.name))

    # TablesEditor.data_update()
    def data_update(self, tracing=""):
        # Verify artument types:
        assert isinstance(tracing, str)

        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self

        # Make sure that the *current_table*, *current_parameter*, and *current_enumeration*
        # in *tables_editor* are valid:
        tables_editor.current_update()

    # TablesEditor.enumeration_changed()
    def enumeration_changed(self):
        assert False

    # TablesEditor.enumeration_comment_get()
    def enumeration_comment_get(self, enumeration, tracing=""):
        # Verify argument types:
        assert isinstance(enumeration, Enumeration) or enumeration is None
        assert isinstance(tracing, str)

        # Perform any requested *tracing*:
        # tables_editor = self

        # Extract the comment *text* associated with *enumeration*:
        position = 0
        text = ""
        if enumeration is not None:
            comments = enumeration.comments
            assert len(comments) >= 1
            comment = comments[0]
            assert isinstance(comment, EnumerationComment)
            text = '\n'.join(comment.lines)
            position = comment.position

        return text, position

    # TablesEditor.enumeration_comment_set()
    def enumeration_comment_set(self, enumeration, text, position, tracing=""):
        # Verify argument types:
        assert isinstance(enumeration, Enumeration) or enumeration is None
        assert isinstance(text, str)
        assert isinstance(position, int)
        assert isinstance(tracing, str)

        # Perform any requested *tracing*:
        # tables_editor = self

        # Stuff *text* into *enumeration*:
        if enumeration is not None:
            comments = enumeration.comments
            assert len(comments) >= 1
            comment = comments[0]
            assert isinstance(comment, EnumerationComment)
            comment.lines = text.split('\n')
            comment.position = position

    # TablesEditor.enumeration_is_active():
    def enumeration_is_active(self):
        tables_editor = self
        tables_editor.current_update()
        current_parameter = tables_editor.current_parameter
        return current_parameter is not None and current_parameter.type == "enumeration"

    # TablesEditor.enumeration_new()
    def enumeration_new(self, name):
        # Verify argument types:
        assert isinstance(name, str)

        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self
        trace_level = tables_editor.trace_level
        if trace_level >= 1:
            print("=>TablesEditor.enumeration_new('{0}')".format(name))

        # Create *new_parameter* named *name*:
        comments = [EnumerationComment(language="EN", lines=list())]
        new_enumeration = Enumeration(name=name, comments=comments)

        # Wrap up any requested tracing and return *new_parameter*:
        if trace_level >= 1:
            print("<=TablesEditor.enumeration_new('{0}')=>'{1}'".format(new_enumeration.name))
        return new_enumeration

    # TablesEditor.enumerations_update()
    def enumerations_update(self, enumeration=None, tracing=""):
        # Verify argument types:
        assert isinstance(enumeration, Enumeration) or enumeration is None
        assert isinstance(tracing, str)

        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self

        # Make sure that the *current_table*, *current_parameter*, and *current_enumeration*
        # in *tables_editor* are valid:
        tables_editor.current_update()

        # Grab some widgets from *main_window*:
        main_window = tables_editor.main_window
        table_name = main_window.enumerations_table_name
        parameter_name = main_window.enumerations_parameter_name
        combo = main_window.enumerations_combo

        # Upbdate the *table_name* and *parameter_name* widgets:
        current_table = tables_editor.current_table
        table_name.setText("" if current_table is None else current_table.name)
        current_parameter = tables_editor.current_parameter
        parameter_name.setText("" if current_parameter is None else current_parameter.name)

        # Empty out *enumeration_combo* widgit:
        main_window = tables_editor.main_window
        while combo.count() > 0:
            combo.removeItem(0)

        # Grab *enumerations* from *current_parameter* (if possible):
        if current_parameter is not None and current_parameter.type.lower() == "enumeration":
            enumerations = current_parameter.enumerations

            # Now fill in *enumerations_combo_box* from *enumerations*:
            for index, enumeration in enumerate(enumerations):
                enumeration_name = enumeration.name
                if tracing:
                    print("{0}[{1}]'{2}'".format(tracing, index, enumeration.name))
                # print("[{0}]'{1}'".format(index, enumeration_name))
                combo.addItem(enumeration_name)

        # Update the *enumerations_combo_edit*:
        tables_editor.enumerations_combo_edit.gui_update()

    # TablesEditor.filters_cell_clicked():
    def filters_cell_clicked(self, row, column):
        # Verify argument types:
        assert isinstance(row, int)
        assert isinstance(column, int)

        # Perform any requested signal tracing:
        tables_editor = self

        # Just update the filters tab:
        tables_editor.filters_update()

    # TablesEditor.filters_down_button_clicked():
    def filters_down_button_clicked(self):
        tables_editor = self
        trace_signals = tables_editor.trace_signals

        # Note: The code here is very similar to the code in
        # *TablesEditor.filters_down_button_clicked*:

        # Grab some values from *tables_editor*:
        tables_editor.current_update()
        main_window = tables_editor.main_window
        filters_table = main_window.filters_table
        current_search = tables_editor.current_search

        # If there is no *current_search* there is nothing to be done:
        if current_search is not None:
            # We have a valid *current_search*, so grab *filters* and *current_row*:
            filters = current_search.filters
            current_row_index = filters_table.currentRow()

            # Dispactch on *current_row*:
            last_row_index = max(0, filters_table.rowCount() - 1)
            if current_row_index < 0:
                # No *current_row* is selected, so select the last row:
                filters_table.setCurrentCell(last_row_index, 0, QItemSelectionModel.SelectCurrent)
            else:
                # We can only move a filter up if it is not the last one:
                if current_row_index < last_row_index:
                    # Save all the stuff we care about from *filters_table* back into *filters*:
                    tables_editor.filters_unload()

                    # Swap *filter_at* with *filter_before*:
                    filter_after = filters[current_row_index + 1]
                    filter_at = filters[current_row_index]
                    filters[current_row_index + 1] = filter_at
                    filters[current_row_index] = filter_after

                    # Force the *filters_table* to be updated:
                    tables_editor.filters_update()
                    filters_table.setCurrentCell(current_row_index + 1, 0,
                                                 QItemSelectionModel.SelectCurrent)

    # TablesEditor.filters_unload()
    def filters_unload(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        tables_editor = self
        tables_editor.current_update()
        current_search = tables_editor.current_search
        if current_search is not None:
            filters = current_search.filters
            for filter in filters:
                use_item = filter.use_item
                use = False
                if use_item is not None:
                    check_state = use_item.checkState()
                    if check_state == Qt.CheckState.Checked:
                        use = True
                filter.use = use

                select = ""
                select_item = filter.select_item
                if select_item is not None:
                    select = select_item.text()
                filter.select = select

    # TablesEditor.filters_up_button_clicked():
    def filters_up_button_clicked(self):
        # Perform any requested signal tracing:
        tables_editor = self
        trace_signals = tables_editor.trace_signals

        # Note: The code here is very similar to the code in
        # *TablesEditor.filters_down_button_clicked*:

        # Grab some values from *tables_editor*:
        tables_editor.current_update()
        main_window = tables_editor.main_window
        filters_table = main_window.filters_table
        current_search = tables_editor.current_search

        # If there is no *current_search* there is nothing to be done:
        if current_search is not None:
            # We have a valid *current_search*, so grab *filters* and *current_row*:
            filters = current_search.filters
            current_row_index = filters_table.currentRow()
            # if trace_signals:
            #    print(" filters_before={0}".format([filter.parameter.name for filter in filters]))

            # Dispactch on *current_row_index*:
            if current_row_index < 0:
                # No *current_row_index* is selected, so select the first row:
                filters_table.setCurrentCell(0, 0, QItemSelectionModel.SelectCurrent)
            else:
                # We can only move a filter up if it is not the first one:
                if current_row_index >= 1:
                    # Save all the stuff we care about from *filters_table* back into *filters*:
                    tables_editor.filters_unload()

                    # Swap *filter_at* with *filter_before*:
                    filter_before = filters[current_row_index - 1]
                    filter_at = filters[current_row_index]
                    filters[current_row_index - 1] = filter_at
                    filters[current_row_index] = filter_before

                    # Force the *filters_table* to be updated:
                    tables_editor.filters_update()
                    filters_table.setCurrentCell(current_row_index - 1, 0,
                                                 QItemSelectionModel.SelectCurrent)

            # if trace_signals:
            #    print(" filters_after={0}".format([filter.parameter.name for filter in filters]))

    # TablesEditor.filters_update()
    def filters_update(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Empty out *filters_table* widget:
        tables_editor = self
        main_window = tables_editor.main_window
        filters_table = main_window.filters_table
        filters_table.clearContents()
        filters_table.setColumnCount(4)
        filters_table.setHorizontalHeaderLabels(["Parameter", "Type", "Use", "Select"])

        # Only fill in *filters_table* if there is a valid *current_search*:
        tables_editor.current_update()
        current_search = tables_editor.current_search
        if current_search is None:
            # No *current_search* so there is nothing to show:
            filters_table.setRowCount(0)
        else:
            # Let's update the *filters* and load them into the *filters_table* widget:
            # current_search.filters_update(tables_editor)
            filters = current_search.filters
            filters_size = len(filters)
            filters_table.setRowCount(filters_size)
            if tracing:
                print("{0}current_search='{1}' filters_size={2}".
                      format(tracing, current_search.name, filters_size))

            # Fill in one *filter* at a time:
            for filter_index, filter in enumerate(filters):
                # Create the header label in the first column:
                parameter = filter.parameter
                # if tracing:
                #    print("{0}[{1}]: '{2}'".format(tracing, filter_index, parameter_name))
                parameter_comments = parameter.comments
                assert len(parameter_comments) >= 1
                parameter_comment = parameter_comments[0]
                assert isinstance(parameter_comment, ParameterComment)

                # Figure out what *heading* to use:
                parameter_name = parameter.name
                short_heading = parameter_comment.short_heading
                long_heading = parameter_comment.long_heading
                heading = short_heading
                if heading is None:
                    heading = long_heading
                if heading is None:
                    heading = parameter_name
                # if tracing:
                #    print("{0}[{1}]: sh='{2}' lh='{3}' pn='{4}".format(
                #      tracing, filter_index, short_heading, long_heading, parameter_name))

                # Stuff the *heading* into the first column:
                header_item = QTableWidgetItem(heading)
                filter.header_item = header_item
                filters_table.setItem(filter_index, 0, filter.header_item)

                # Stuff the *type* into the second column:
                type = parameter.type
                type_item = QTableWidgetItem(type)
                filters_table.setItem(filter_index, 1, type_item)

                use = filter.use
                use_item = QTableWidgetItem("")
                filter.use_item = use_item
                use_item.setData(Qt.UserRole, filter)
                # print(type(use_item))
                # print(use_item.__class__.__bases__)
                flags = use_item.flags()
                use_item.setFlags(flags | Qt.ItemIsUserCheckable)
                check_state = Qt.CheckState.Checked if use else Qt.CheckState.Unchecked
                use_item.setCheckState(check_state)
                filters_table.setItem(filter_index, 2, use_item)

                select_item = QTableWidgetItem(filter.select)
                filter.select_item = select_item
                select_item.setData(Qt.UserRole, filter)
                filters_table.setItem(filter_index, 3, select_item)

            # if current_row_index >= 0 and current_row_index < filters_size:
            #    #filters_table.setCurrentCell(current_row_index, 0)
            #    filters_down.setEnabled(True)
            #    filters_up.setEnabled(True)
            # else:
            #    #filters_table.setCurrentCell(-1, -1)
            #    filters_down.setEnabled(False)
            #    filters_up.setEnabled(False)

        # Remember to unload the filters before changing from the [Filters] tab:
        tables_editor.tab_unload = TablesEditor.filters_unload

    # TablesEditor.filter_use_clicked()
    def filter_use_clicked(self, use_item, filter, row, column):
        # Verify argument types:
        assert isinstance(use_item, QTableWidgetItem)
        assert isinstance(filter, Filter)
        assert isinstance(row, int)
        assert isinstance(column, int)

        # FIXME: This routine probably no longer used!!!

        # Do nothing if we are already in a signal:
        tables_editor = self
        if not tables_editor.in_signal:
            tables_editor.in_signal = True

            # Perform an requested signal tracing:
            trace_signals = tables_editor.trace_signals
            if trace_signals:
                print("=>TablesEditor.filter_use_clicked(*, '{0}', {1}, {2})".
                      format(filter.parameter.name, row, column))

            check_state = use_item.checkState()
            print("check-state=", check_state)
            if check_state == Qt.CheckState.Checked:
                result = "checked"
                filter.use = True
            elif check_state == Qt.CheckState.Unchecked:
                result = "unchecked"
                filter.use = False
            elif check_state == Qt.CheckState.PartiallyChecked:
                result = "partially checked"
            else:
                result = "unknown"
            print("filter.name='{0}' filter.use={1}".format(filter.parameter.name, filter.use))

            # Wrap up any signal tracing:
            if trace_signals:
                print("parameter check state={0}".format(result))
                print("<=TablesEditor.filter_use_clicked(*, '{0}', {1}, {2})\n".
                      format(filter.parameter.name, row, column))
            tables_editor.in_signal = False

    # TablesEditor.find_update():
    def find_update(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        tables_editor = self
        main_window = tables_editor.main_window
        find_tabs = main_window.find_tabs
        find_tabs_index = find_tabs.currentIndex()
        if find_tabs_index == 0:
            tables_editor.searches_update()
        elif find_tabs_index == 1:
            tables_editor.filters_update()
        elif find_tabs_index == 2:
            tables_editor.results_update()
        else:
            assert False

    # TablesEditor.import_bind_clicked():
    def import_bind_button_clicked(self):
        # Perform any requested signal tracing:
        tables_editor = self
        trace_signals = tables_editor.trace_signals

        # Update *current_table* an *parameters* from *tables_editor*:
        tables_editor.current_update()
        current_table = tables_editor.current_table
        if current_table is not None:
            parameters = current_table.parameters
            headers = tables_editor.import_headers
            column_triples = tables_editor.import_column_triples
            for column_index, triples in enumerate(column_triples):
                header = headers[column_index]
                if len(triples) >= 1:
                    triple = triples[0]
                    count, name, value = triple
                    for parameter_index, parameter in enumerate(parameters):
                        if parameter.csv == name:
                            break
                    else:
                        scrunched_name = \
                          "".join([character for character in header if character.isalnum()])
                        comments = [ParameterComment(language="EN",
                                    long_heading=scrunched_name, lines=list())]
                        parameter = Parameter(name=scrunched_name, type=name, csv=header,
                                              csv_index=column_index, comments=comments)
                        parameters.append(parameter)

            tables_editor.update()

    # TablesEditor.import_file_line_changed():
    def import_csv_file_line_changed(self, text):
        # Verify argument types:
        assert isinstance(text, str)

        tables_editor = self
        in_signal = tables_editor.in_signal
        if not in_signal:
            tables_editor.in_signal = True

            # Perform any requested signal tracing:
            trace_signals = tables_editor.trace_signals
            if trace_signals:
                print("=>TablesEditor.import_csv_file_line_changed('{0}')".format(text))

            # Make sure *current_table* is up-to-date:
            # tables_editor.current_update()
            # current_table = tables_editor.current_table

            # Read *csv_file_name* out of the *import_csv_file_line* widget and stuff into *table*:
            # if current_table is not None:
            #     main_window = tables_editor.main_window
            #     import_csv_file_line = main_window.import_csv_file_line
            #     xxx = import_csv_file_line.text()
            #     print("xxx='{0}' text='{1}'".format(xxx, text))
            #    current_table.csv_file_name = csv_file_name

            # Force an update:
            # tables_editor.update()

            # Wrap up any requested signal tracing:
            if trace_signals:
                print("<=TablesEditor.import_csv_file_line_changed('{0}')\n".format(text))
            tables_editor.in_signal = False

    # TablesEditor.parameter_default_changed():
    def parameter_csv_changed(self, new_csv):
        # Verify argument types:
        assert isinstance(new_csv, str)

        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self
        in_signal = tables_editor.in_signal
        if not in_signal:
            tables_editor.in_signal = True

            # Perform any requested *tracing*:
            trace_signals = tables_editor.trace_signals

            # Stuff *new_csv* into *current_parameter* (if possible):
            tables_editor.current_parameter()
            current_parameter = tables_editor.current_parameter
            if current_parameter is not None:
                current_parameter.csv = new_csv

            tables_editor.update()
            # Wrap up any requested signal tracing:
            if trace_signals:
                print("=>TablesEditor.parameter_csv_changed('{0}')\n".format(new_csv))
                tables_editor.in_signal = False

    # TablesEditor.parameter_default_changed():
    def parameter_default_changed(self, new_default):
        # Verify argument types:
        assert isinstance(new_default, str)

        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self
        trace_level = tables_editor.trace_level
        trace_level = 1
        if trace_level >= 1:
            print("=>TablesEditor.parameter_default_changed('{0}')".format(new_default))

        # Stuff *new_default* into *current_parameter* (if possible):
        current_parameter = tables_editor.current_parameter
        if current_parameter is not None:
            current_parameter.default = new_default

        # Wrap up any requested tracing:
        if trace_level >= 1:
            print("<=TablesEditor.parameter_default_changed('{0}')\n".format(new_default))

    # TablesEditor.parameter_comment_get():
    def parameter_comment_get(self, parameter, tracing=""):
        # Verify argument types:
        assert isinstance(parameter, Parameter) or parameter is None
        assert isinstance(tracing, str)

        # Perform any requested *tracing*:
        text = ""

        # Grab the comment *text* from *parameter*:
        position = 0
        text = ""
        if parameter is not None:
            comments = parameter.comments
            assert len(comments) >= 1
            comment = comments[0]
            assert isinstance(comment, ParameterComment)
            text = '\n'.join(comment.lines)
            position = comment.position

        # Return *text* and *position*:
        return text, position

    # TablesEditor.parameter_comment_set():
    def parameter_comment_set(self, parameter, text, position, tracing=""):
        # Verify argument types:
        assert isinstance(parameter, Parameter) or parameter is None
        assert isinstance(text, str)
        assert isinstance(position, int)
        assert isinstance(tracing, str)

        # Perform any requested *tracing*:
        tables_editor = self

        # Stuff *text* into *parameter*:
        if parameter is not None:
            comments = parameter.comments
            assert len(comments) >= 1
            comment = comments[0]
            assert isinstance(comment, ParameterComment)
            comment.lines = text.split('\n')
            comment.position = position

        if tracing:
            main_window = tables_editor.main_window
            comment_text = main_window.parameters_comment_text
            cursor = comment_text.textCursor()
            actual_position = cursor.position()
            print("{0}position={1}".format(tracing, actual_position))

    # TablesEditor.parameter_is_active():
    def parameter_is_active(self):
        tables_editor = self
        tables_editor.current_update()
        # We can only create/edit parameters when there is an active *current_table*:
        return tables_editor.current_table is not None

    # TablesEditor.parameter_long_changed():
    def parameter_long_changed(self, new_long_heading):
        # Verify argument types:
        assert isinstance(new_long_heading, str)

        # Only do something if we are not already in a signal:
        tables_editor = self
        in_signal = tables_editor.in_signal
        if not in_signal:
            tables_editor.in_signal = True
            trace_signals = tables_editor.trace_signals

            # Update the correct *parameter_comment* with *new_long_heading*:
            current_parameter = tables_editor.current_parameter
            assert isinstance(current_parameter, Parameter)
            parameter_comments = current_parameter.comments
            assert len(parameter_comments) >= 1
            parameter_comment = parameter_comments[0]
            assert isinstance(parameter_comment, ParameterComment)
            parameter_comment.long_heading = new_long_heading

            # Update the user interface:
            tables_editor.update()


    # TablesEditor.parameters_edit_update():
    def parameters_edit_update(self, parameter=None, tracing=""):
        # Verify argument types:
        assert isinstance(parameter, Parameter) or parameter is None
        assert isinstance(tracing, str)

        # Make sure that the *current_table*, *current_parameter*, and *current_enumeration*
        # in *tables_editor* are valid:
        tables_editor = self

        tables_editor.current_update()
        current_table = tables_editor.current_table
        current_parameter = tables_editor.current_parameter
        parameter = current_parameter

        # Initialize all fields to an "empty" value:
        csv = ""
        is_valid_parameter = False
        default = ""
        optional = False
        type = ""

        # If we have a valid *parameter*, copy the field values out:
        if parameter is not None:
            # Grab some values from *parameter*:
            csv = parameter.csv
            is_valid_parameter = True
            default = parameter.default
            optional = parameter.optional
            type = parameter.type
            # print("type='{0}' optional={1}".format(type, optional))
        if tracing:
            print("{0}Parameter.name='{1}' csv='{2}'".
                  format(tracing, "None" if parameter is None else parameter.name, csv))

        # Grab some widgets from *main_window*:
        main_window = tables_editor.main_window
        csv_line = main_window.parameters_csv_line
        default_line = main_window.parameters_default_line
        optional_check = main_window.parameters_optional_check
        table_name = main_window.parameters_table_name
        type_combo = main_window.parameters_type_combo

        # The top-level update routine should have already called *TablesEditor*.*current_update*
        # to enusure that *current_table* is up-to-date:
        current_table = tables_editor.current_table
        table_name.setText("" if current_table is None else current_table.name)

        # Set the *csv_line* widget:
        previous_csv = csv_line.text()
        if previous_csv != csv:
            csv_line.setText(csv)
            if tracing:
                print("{0}Set csv to '{1}'".format(tracing, csv))

        # Stuff the values in to the *type_combo* widget:
        type_combo_size = type_combo.count()
        assert type_combo_size >= 1
        type_lower = type.lower()
        match_index = 0
        for type_index in range(type_combo_size):
            type_text = type_combo.itemText(type_index)
            if type_text.lower() == type_lower:
                match_index = type_index
                break
        type_combo.setCurrentIndex(match_index)

        default_line.setText(default)
        optional_check.setChecked(optional)

        # Enable/disable the parameter widgets:
        type_combo.setEnabled(is_valid_parameter)
        default_line.setEnabled(is_valid_parameter)
        optional_check.setEnabled(is_valid_parameter)

        # Update the *comments* (if they exist):
        if parameter is not None:
            comments = parameter.comments
            # Kludge for now, select the first comment
            assert len(comments) >= 1
            comment = comments[0]
            assert isinstance(comment, ParameterComment)

            # Update the headings:
            tables_editor.parameters_long_set(comment.long_heading)
            tables_editor.parameters_short_set(comment.short_heading)

            previous_csv = csv_line.text()
            if csv != previous_csv:
                csv_line.setText(csv)

            # Deal with comment text edit area:
            tables_editor.current_comment = comment
            lines = comment.lines
            text = '\n'.join(lines)

            tables_editor.comment_text_set(text)

        # Changing the *parameter* can change the enumeration combo box, so update it as well:
        # tables_editor.enumeration_update()

        # Update the *tables_combo_edit*:
        tables_editor.parameters_combo_edit.gui_update()

    # TablesEditor.parameters_long_set():
    def parameters_long_set(self, new_long_heading, tracing=""):
        # Verify argument types:
        assert isinstance(new_long_heading, str)
        assert isinstance(tracing, str)

        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self

        # Stuff *new_long_heading* into *current_parameter*:
        current_parameter = tables_editor.current_parameter
        if current_parameter is None:
            new_long_heading = ""
        else:
            assert isinstance(current_parameter, Parameter)
            current_parameter.long_heading = new_long_heading

        # Now update the user interface to shove *new_long_heading* into the *parameter_long_line*
        # widget:
        main_window = tables_editor.main_window
        long_line = main_window.parameters_long_line
        previous_long_heading = long_line.text()
        if previous_long_heading != new_long_heading:
            long_line.setText(new_long_heading)

    # TablesEditor.parameter_new():
    def parameter_new(self, name, tracing=""):
        # Verify argument types:
        assert isinstance(name, str)
        assert isinstance(tracing, str)

        # Create *new_parameter* named *name*:
        comments = [ParameterComment(language="EN", long_heading=name, lines=list())]
        new_parameter = Parameter(name=name, type="boolean", csv="",
                                  csv_index=-1, comments=comments)
        return new_parameter

    # TablesEditor.parameter_optional_clicked():
    def parameter_optional_clicked(self):
        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self

        current_parameter = tables_editor.current_parameter
        if current_parameter is not None:
            main_window = tables_editor.main_window
            parameter_optional_check = main_window.parameter_optional_check
            optional = parameter_optional_check.isChecked()
            current_parameter.optional = optional

    # TablesEditor.parameter_short_changed():
    def parameter_short_changed(self, new_short_heading):
        # Verify argument types:
        assert isinstance(new_short_heading, str)

        # Do not do anything when we are already in a signal:
        tables_editor = self
        if not tables_editor.in_signal:
            tables_editor.in_signal = True

            # Perform any requested tracing from *tables_editor* (i.e. *self*):
            trace_signals = tables_editor.trace_signals

            # Update *current_parameter* to have *new_short_heading*:
            current_parameter = tables_editor.current_parameter
            assert isinstance(current_parameter, Parameter)
            parameter_comments = current_parameter.comments
            assert len(parameter_comments) >= 1
            parameter_comment = parameter_comments[0]
            assert isinstance(parameter_comment, ParameterComment)
            parameter_comment.short_heading = new_short_heading

            # Update the user interface:
            tables_editor.update()

            tables_editor.in_signal = False

    # TablesEditor.parameters_short_set():
    def parameters_short_set(self, new_short_heading, tracing=""):
        # Verify argument types:
        assert isinstance(new_short_heading, str) or new_short_heading is None
        assert isinstance(tracing, str)

        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self

        # Stuff *new_short_heading* into *current_parameter*:
        current_parameter = tables_editor.current_parameter
        if new_short_heading is None or current_parameter is None:
            new_short_heading = ""
        else:
            current_parameter.short_heading = new_short_heading

        # Now update the user interface to show *new_short_heading* into the *parameter_short_line*
        # widget:
        main_window = tables_editor.main_window
        short_line = main_window.parameters_short_line
        previous_short_heading = short_line.text()
        if previous_short_heading != new_short_heading:
            short_line.setText(new_short_heading)

    # TablesEditor.parameters_type_changed():
    def parameters_type_changed(self):
        # Perform any requested *signal_tracing* from *tables_editor* (i.e. *self*):
        tables_editor = self
        if tables_editor.in_signal == 0:
            tables_editor.in_signal = True
            current_parameter = tables_editor.current_parameter
            trace_signals = tables_editor.trace_signals
            if trace_signals:
                print("=>TablesEditor.parameters_type_changed('{0}')".
                      format(None if current_parameter is None else current_parameter.name))

            # Load *type* into *current_parameter*:
            if current_parameter is not None:
                main_window = tables_editor.main_window
                parameters_type_combo = main_window.parameters_type_combo
                type = parameters_type_combo.currentText().lower()
                current_parameter.type = type

            # Wrap-up any requested *signal_tracing*:
            if trace_signals:
                print("<=TablesEditor.parameters_type_changed('{0}')\n".
                      format(None if current_parameter is None else current_parameter.name))
            tables_editor.in_signal = False

    # TablesEditor.parameters_update():
    def parameters_update(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Perform any requested *tracing*:
        if tracing:
            print("{0}=>TabledsEditor.parameters_update".format(tracing))

            # Make sure *current_table* is up to date:
            tables_editor = self
            tables_editor.current_update()
            current_table = tables_editor.current_table

            # The [import] tab does not do anything if there is no *current_table*:
            if current_table is not None:
                # Do some *tracing* if requested:
                if tracing:
                    print("{0}current_table='{1}'".format(tracing, current_table.name))

                # Grab some widgets from *tables_editor*:
                main_window = tables_editor.main_window
                # import_bind = main_window.import_bind
                # import_csv_file_line = main_window.import_csv_file_line
                # import_read = main_window.import_read
                parameters_table = main_window.parameters_table

                # Update the *import_csv_file_name* widget:
                # csv_file_name = current_table.csv_file_name
                # if tracing:
                #    print("{0}csv_file_name='{1}'".format(tracing, csv_file_name))
                assert False
                current_table.csv_read_and_process(
                  "/home/wayne/public_html/projects/digikey_csvs")

                # Load up *import_table*:
                headers = current_table.import_headers
                # rows = current_table.import_rows
                column_triples = current_table.import_column_triples
                # if tracing:
                #    print("{0}headers={1} rows={2} column_triples={3}".
                #      format(tracing, headers, rows, column_triples))

                parameters_table.clearContents()
                if headers is not None and column_triples is not None:
                    if tracing:
                        print("{0}Have column_triples".format(tracing))
                    parameters_table.setRowCount(len(headers))
                    parameters_table.setColumnCount(6)
                    # Fill in the left size row headers for *parameters_table*:
                    parameters_table.setVerticalHeaderLabels(headers)

                    assert len(column_triples) == len(headers)
                    for column_index, triples in enumerate(column_triples):
                        for triple_index, triple in enumerate(triples):
                            assert len(triple) == 3
                            count, name, value = triple

                            if count >= 1:
                                item = QTableWidgetItem("{0} x {1} '{2}'".
                                                        format(count, name, value))
                                parameters_table.setItem(column_index, triple_index, item)

                            # print("Column[{0}]: '{1}':{2} => {3}".
                            #  format(column_index, value, count, matches))

                            # print("Column[{0}]: {1}".format(column_index, column_table))
                            # print("Column[{0}]: {1}".format(column_index, column_list))

                            # assert column_index < len(parameters)
                            # parameter = parameters[column_index]
                            # type = "String"
                            # if len(matches) >= 1:
                            #    match = matches[0]
                            #    if match == "Integer":
                            #        type = "Integer"
                            #    elif match == "Float":
                            #        type = "Float"
                            # parameter.type = type

            # Enable/Disable *import_read* button widget depending upon whether *csv_file_name*
            # exists:
            # import_read.setEnabled(
            #  csv_file_name is not None and os.path.isfile(csv_file_name))
            # import_bind.setEnabled(current_table.import_headers is not None)

    # TablesEditor.quit_button_clicked():
    def quit_button_clicked(self):
        tables_editor = self
        print("TablesEditor.quit_button_clicked() called")
        application = tables_editor.application
        application.quit()

    # TablesEditor.results_update():
    def results_update(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        tables_editor = self
        main_window = tables_editor.main_window
        results_table = main_window.results_table
        results_table.clearContents()

        tables_editor.current_update()
        current_search = tables_editor.current_search
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
            print("{0}<=TablesEditor.results_update()".format(tracing))

    # TablesEditor.re_table_get():
    @staticmethod
    def re_table_get():
        # Create some regular expressions and stuff the into *re_table*:
        si_units_re_text = Units.si_units_re_text_get()
        float_re_text = "-?([0-9]+\\.[0-9]*|\\.[0-9]+)"
        white_space_text = "[ \t]*"
        integer_re_text = "-?[0-9]+"
        integer_re = re.compile(integer_re_text + "$")
        float_re = re.compile(float_re_text + "$")
        url_re = re.compile("(https?://)|(//).*$")
        empty_re = re.compile("-?$")
        funits_re = re.compile(float_re_text + white_space_text + si_units_re_text + "$")
        iunits_re = re.compile(integer_re_text + white_space_text + si_units_re_text + "$")
        range_re = re.compile("[^~]+~[^~]+$")
        list_re = re.compile("([^,]+,)+[^,]+$")
        re_table = {
          "Empty": empty_re,
          "Float": float_re,
          "FUnits": funits_re,
          "Integer": integer_re,
          "IUnits": iunits_re,
          "List": list_re,
          "Range": range_re,
          "URL": url_re,
        }
        return re_table

    # TablesEditor.run():
    @trace(1)
    def run(self, tracing=""):
        # Show the *window* and exit when done:
        tables_editor = self
        main_window = tables_editor.main_window
        application = tables_editor.application
        # clipboard = application.clipboard()
        # print(f"type(clipboard)='{type(clipboard)}'")
        # assert isinstance(clipboard, QClipboard)

        main_window.show()

        sys.exit(application.exec_())

    # TablesEditor.save_button_clicked():
    def save_button_clicked(self):
        # Perform any requested signal tracing:
        tables_editor = self
        trace_signals = tables_editor.trace_signals
        next_tracing = " " if trace_signals else None
        if trace_signals:
            print("=>TablesEditor.save_button_clicked()")
        current_tables = tables_editor.current_tables

        # Save each *table* in *current_tables*:
        for table in current_tables:
            table.save()

        searches = tables_editor.searches
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

    # TablesEditor.schema_update():
    def schema_update(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Grab some values from *tables_editor* (i.e. *self*):
        tables_editor = self
        main_window = tables_editor.main_window
        schema_tabs = main_window.schema_tabs
        schema_tabs_index = schema_tabs.currentIndex()
        if schema_tabs_index == 0:
            tables_editor.tables_update()
        elif schema_tabs_index == 1:
            tables_editor.parameters_edit_update()
        elif schema_tabs_index == 2:
            tables_editor.enumerations_update()
        else:
            assert False
        # tables_editor.combo_edit.update()
        # tables_editor.parameters_update(None)
        # tables_editor.search_update()

    # TablesEditor.searches_comment_get():
    def searches_comment_get(self, search, tracing=""):
        # Verify argument types:
        assert isinstance(search, Search) or search is None
        assert isinstance(tracing, str)

        # Perform any requested *tracing*:
        # tables_editor = self

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

    # TablesEditor.searches_comment_set():
    def searches_comment_set(self, search, text, position, tracing=""):
        # Verify argument types:
        assert isinstance(search, Search) or search is None
        assert isinstance(text, str)
        assert isinstance(position, int)
        assert isinstance(tracing, str)

        # Perform any requested *tracing*:
        # tables_editor = self

        # Stuff *text* and *position* into *search*:
        if search is not None:
            comments = search.comments
            assert len(comments) >= 1
            comment = comments[0]
            assert isinstance(comment, SearchComment)
            comment.lines = text.split('\n')
            comment.position = position

    # TablesEditor.searches_file_save():
    def searches_file_save(self, file_name, tracing=""):
        # Verify argument types:
        assert isinstance(file_name, str)
        assert isinstance(tracing, str)

        # Perform any requested *tracing*:
        next_tracing = None if tracing is None else tracing + " "
        if tracing:
            print("{0}=>TablesEditor.searches_file_save('{1}')".format(tracing, file_name))

        xml_lines = list()
        xml_lines.append('<?xml version="1.0"?>')
        xml_lines.append('<Searches>')

        # Sweep through each *search* in *searches* and append the results to *xml_lines*:
        tables_editor = self
        searches = tables_editor.searches
        for search in searches:
            search.xml_lines_append(xml_lines, "  ")

        # Wrap up *xml_lines* and generate *xml_text*:
        xml_lines.append('</Searches>')
        xml_lines.append("")
        xml_text = '\n'.join(xml_lines)

        # Write out *xml_text* to *file_name*:
        with open(file_name, "w") as xml_file:
            xml_file.write(xml_text)

        # Wrqp up any requested *tracing*:
        if tracing:
            print("{0}<=TablesEditor.searches_file_save('{1}')".format(tracing, file_name))

    # TablesEditor.searches_file_load():
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

            # Grab *searches* from *tables_editor* (i.e. *self*) and empty it out:
            tables_editor = self
            searches = tables_editor.searches
            assert isinstance(searches, list)
            del searches[:]

            # Parse each *search_tree* in *search_trees*:
            for search_tree in search_trees:
                assert isinstance(search_tree, etree._Element)
                search = Search(search_tree=search_tree,
                                tables=tables_editor.tables)
                assert False, "Old code"
                searches.append(search)

            # Set *current_search*
            tables_editor.current_search = searches[0] if len(searches) >= 1 else None

    # TablesEditor.searches_is_active():
    def searches_is_active(self):
        tables_editor = self
        tables_editor.current_update()
        # We can only edit searches if there is there is an active *current_table8:
        return tables_editor.current_table is not None

    # TablesEditor.searches_new():
    def searches_new(self, name, tracing=""):
        # Verify argument types:
        assert isinstance(name, str)
        assert isinstance(tracing, str)

        tables_editor = self
        tables_editor.current_update()
        current_table = tables_editor.current_table

        # Create *serach* with an empty English *serach_comment*:
        search_comment = SearchComment(language="EN", lines=list())
        search_comments = [search_comment]
        search = Search(name=name, comments=search_comments, table=current_table)
        search.filters_refresh()

        return search

    # TablesEditor.searches_save_button_clicked():
    def searches_save_button_clicked(self):
        # Peform an requested signal tracing:
        tables_editor = self
        tracing = " " if tables_editor.trace_signals else None
        # next_tracing = None if tracing is None else " "
        if tracing:
            print("=>TablesEditor.searches_save_button_clicked()".format(tracing))

        # Write out the searches to *file_name*:
        # file_name = os.path.join(order_root, "searches.xml")
        # tables_editor.searches_file_save(file_name)
        assert False

        if tracing:
            print("<=TablesEditor.searches_save_button_clicked()\n".format(tracing))

    # TablesEditor.searches_table_changed():
    def searches_table_changed(self, new_text):
        # Verify argument types:
        assert isinstance(new_text, str)

        # Do nothing if we are already in a signal:
        tables_editor = self
        if not tables_editor.in_signal:
            tables_editor.in_signal = True
            # Perform any requested *tracing*:
            trace_signals = tables_editor.trace_signals
            next_tracing = " " if trace_signals else None
            if trace_signals:
                print("=>TablesEditor.searches_table_changed('{0}')".format(new_text))

            # Make sure *current_search* is up to date:
            tables_editor = self
            tables_editor.current_update()
            current_search = tables_editor.current_search

            # Find the *table* that matches *new_text* and stuff it into *current_search*:
            if current_search is not None:
                match_table = None
                tables = tables_editor.tables
                for table_index, table in enumerate(tables):
                    assert isinstance(table, Table)
                    if table.name == new_text:
                        match_table = table
                        break
                current_search.table_set(match_table)

            # Wrap up any requested *tracing*:
            if trace_signals:
                print("<=TablesEditor.searches_table_changed('{0}')\n".format(new_text))
            tables_editor.in_signal = False

    # TablesEditor.searches_update():
    def searches_update(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Make sure that *current_search* is up to date:
        tables_editor = self
        tables_editor.current_update()
        current_search = tables_editor.current_search

        # Update *searches_combo_edit*:
        searches_combo_edit = tables_editor.searches_combo_edit
        searches_combo_edit.gui_update()

        # Next: Update the table options:
        search_table = None if current_search is None else current_search.table
        tables = tables_editor.tables
        main_window = tables_editor.main_window
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

    # TablesEditor.tab_changed():
    def tab_changed(self, new_index):
        # Verify argument types:
        assert isinstance(new_index, int)

        # Note: *new_index* is only used for debugging.

        # Only deal with this siginal if we are not already *in_signal*:
        tables_editor = self
        if not tables_editor.in_signal:
            # Disable  *nested_signals*:
            tables_editor.in_signal = True

            # Perform any requested signal tracing:
            trace_signals = tables_editor.trace_signals
            next_tracing = " " if trace_signals else None
            if trace_signals:
                print("=>TablesEditor.tab_changed(*, {0})".format(new_index))

            # Deal with clean-up of previous tab (if requested):
            tab_unload = tables_editor.tab_unload
            if callable(tab_unload):
                tab_unload(tables_editor)

            # Perform the update:
            tables_editor.update()

            # Wrap up any requested signal tracing and restore *in_signal*:
            if trace_signals:
                print("<=TablesEditor.tab_changed(*, {0})\n".format(new_index))
            tables_editor.in_signal = False

    # TablesEditor.table_comment_get():
    def table_comment_get(self, table, tracing=""):
        # Verify argument types:
        assert isinstance(table, Table)
        assert isinstance(tracing, str)

        text = ""
        # Perform any requested *tracing*:
        # tables_editor = self

        # Extract the comment *text* from *table*:
        if table is not None:
            comments = table.comments
            assert len(comments) >= 1
            comment = comments[0]
            assert isinstance(comment, TableComment)
            text = '\n'.join(comment.lines)
            position = comment.position
        return text, position

    # TablesEditor.table_comment_set():
    def table_comment_set(self, table, text, position, tracing=""):
        # Verify argument types:
        assert isinstance(table, Table)
        assert isinstance(text, str)
        assert isinstance(position, int)
        assert isinstance(tracing, str)

        # Perform any requested *tracing*:
        # tables_editor = self
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

    # TablesEditor.table_new():
    def table_new(self, name, tracing=""):
        # Verify argument types:
        assert isinstance(name, str)

        # Perform an requested *tracing*:

        file_name = "{0}.xml".format(name)
        table_comment = TableComment(language="EN", lines=list())
        table = Table(file_name=file_name, name=name, path="", comments=[table_comment],
                      parameters=list(), csv_file_name="", parent=None)

        return table

    # TablesEditor.table_setup():
    def table_setup(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Perform any tracing requested from *tables_editor* (i.e. *self*):
        tables_editor = self

        # Grab the *table* widget and *current_table* from *tables_editor* (i.e. *self*):
        tables_editor = self
        main_window = tables_editor.main_window
        data_table = main_window.data_table
        assert isinstance(data_table, QTableWidget)
        current_table = tables_editor.current_table

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

    # TablesEditor.tables_update():
    def tables_update(self, table=None, tracing=""):
        # Verify argument types:
        assert isinstance(table, Table) or table is None
        assert isinstance(tracing, str)

        # Perform any tracing requested by *tables_editor* (i.e. *self*):
        tables_editor = self

        # Make sure that the *current_table*, *current_parameter*, and *current_enumeration*
        # in *tables_editor* are valid:
        tables_editor.current_update()

        # Update the *tables_combo_edit*:
        tables_editor.tables_combo_edit.gui_update()

    # TablesEditor.update():
    @trace(1)
    def update(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Perform any requested *tracing*:
        tables_editor = self

        # Only update the visible tabs based on *root_tabs_index*:
        main_window = tables_editor.main_window
        root_tabs = main_window.root_tabs
        root_tabs_index = root_tabs.currentIndex()
        if root_tabs_index == 0:
            tables_editor.collections_update()
        elif root_tabs_index == 1:
            tables_editor.schema_update()
        elif root_tabs_index == 2:
            tables_editor.parameters_update()
        elif root_tabs_index == 3:
            tables_editor.find_update()
        else:
            assert False, "Illegal tab index: {0}".format(root_tabs_index)

    # TablesEditor.search_update():
    def xxx_search_update(self, tracing=""):
        # Verify argument types:
        assert isinstance(tracing, str)

        # Make sure that the *current_table*, *current_parameter*, and *current_enumeration*
        # in *tables_editor* are valid:
        tables_editor = self
        tables_editor.current_update()

        # Grab the *current_table* *Table* object from *tables_editor* (i.e. *self*.)
        # Grab the *seach_table* widget from *tables_editor* as well:
        current_table = tables_editor.current_table
        main_window = tables_editor.main_window
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
                #  partial(TablesEditor.search_use_clicked, tables_editor, use_item, parameter))
                parameter.use = False
                search_table.setItem(parameter_index, 1, use_item)
                search_table.cellClicked.connect(
                  partial(TablesEditor.search_use_clicked, tables_editor, use_item, parameter))

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

        # Update the *search_combo_edit*:
        tables_editor.search_combo_edit.gui_update()


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
        tree_model = self
        tracing = tree_model.tracing
        tracing = None   # Disable *tracing* for now:
        next_tracing = None if tracing is None else tracing + " "
        if tracing:
            print(f"{tracing}=>Tree_model.data(*, *, {role}')")

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

        # Wrap up any requested *tracing*:
        if tracing:
            print(f"{tracing}<=Tree_model.data(*, *, {role}')=>{value}")
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
