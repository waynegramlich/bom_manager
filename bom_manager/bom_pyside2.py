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

from pathlib import Path
# Lots of classes/types are imported from various portions of PySide2:
from PySide2.QtUiTools import QUiLoader                                               # type: ignore
# from PySide2.QtWidgets import (QApplication, QLabel, QLineEdit, QMainWindow)        # type: ignore
from PySide2.QtWidgets import (QApplication, QMainWindow)                             # type: ignore
# from PySide2.QtCore import (QAbstractItemModel, QCoreApplication, QFile)            # type: ignore
from PySide2.QtCore import (QCoreApplication, QFile)                                  # type: ignore
# from PySide2.QtCore import (QItemSelectionModel, QModelIndex, Qt)                   # type: ignore
from PySide2.QtCore import (Qt,)                                                      # type: ignore
import sys


# main():
def main() -> int:
    """Fire up the BOM manager GUI. """
    print("Hello")

    bom_pyside2: BomPyside2 = BomPyside2()

    bom_pyside2.run()

    return 0


# BomPyside2:
class BomPyside2(QMainWindow):
    """Contains global GUI information."""

    # BomPyside2.__init__()
    def __init__(self) -> None:
        """Initialize the BOM Manager Graphical User Interface."""
        # Create the *application* first.  The call to *setAttribute* makes a bogus warning message
        # printout go away:
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

        # Load some values into *bom_pyside2* (i.e. *self*):
        # bom_pyside2: BomPyside2 = self
        self.application: QApplication = application
        self.main_window: QMainWindow = main_window

    # BomPyside2.rung()
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
