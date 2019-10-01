# # BOM Manager Entry Points
#
# This file provides both a GUI and an non-GUI entry point to the BOM Manager.
#
# ## MIT License
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

# Import both the *bom* and *bom_gui* modules from the *bom_manager* package:
from bom_manager import bom, bom_gui


# main():
def main() -> int:
    """Non-GUI entry point for the BOM Manager."""
    # Forward to *bom.main*:
    result: int = bom.main()
    return result


# gui_main():
def gui_main() -> int:
    """GUI entry point for the BOM Manager."""
    # Forward to *bom_gui.main*:
    result: int = bom_gui.main()
    return result
