# # BOM Manager Tracing Module
#
# This module provides a Python decorator for tracing routine calls and returns.
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
# ## Installation
#
# To install:
#
#        pip install bom_manager
#
# ## Code Setup
# 
# For each module, add the following `import` to the code:
#
#        from bom_manager.tracing import trace
#
# Somewhere early in your code execution (i.e. *main*), the tracer module is enabled by:
#
#        global trace_level
#        trace_level = N
#
# where N is a non-negative integer that specifies the level of tracing detail.
# The conventional values for *trace_level* are:
#
# * 0: No tracing at all.
# * 1: Basic tracing.
# * 2: More detailed tracing.
# * 3: Extremely detailed tracing
#
# These are conventions, but you welcome to define additional levels tracing detail,
# for example:
#
# * 11: Over the top, insanely detailed annoying tracing, likely to cause spontaeous combustion.
#
# It is up to you.
#
# ## Code decoration:
#
# Place the Python decoration in front of each Python function or method method that
# you want to trace:
#
#        @trace(LEVEL)
#        def function_or_method(...):
#            ...
#
# where LEVEL is a number from 0 to 3 matches the trecing level conventiou that
# you have adopted for you code.
#
# If you want to enable additional tracing messages as a function/method is executed,
# you need to add a *tracing* argument to your function or method:
#
#        @trace(LEVEL)
#        def function_or_method(..., tracing=""):
#            ...
#            if tracing:
#                 print(f"{tracing}A tracing message.")
#            ...
#
# The global variable *tracing* is the empty string when *trace_level* is 0; otherwise
# *trace* contains a string of spaces that can be prefixed to the front of *print* string
# to properly indent the message.  If you are unfamiliar with Python 3 formatted strings,
# now might be a good time to familiarize yourself with them.
#
# Additional control of the tracing messages can also be keyed off the *trace_level* variable.
# For example:
#
#        global trace_level
#        ...
#        if tracing and trace_level >= 11:
#            print(f"{tracing}This is beyond impossible!!!")
#        ...
#
# ## Acknowledgements:
#
# The following simple example provided an exampletemplate for figuring out how to do a Python
# tracing decorator:
#
# [Python Tracing Decorator](https://cscheid.net/2017/12/11/minimal-tracing-decorator-python-3.html)
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
#   * Variables:
#     * Variables are lower case with underscores between words.
# * Comments:
#   * All code comments are written in [Markdown](https://en.wikipedia.org/wiki/Markdown).
#   * Code is organized into blocks are preceeded by comment that explains the code block.
# * Misc:
#   * The relatively new formatted string style `f"..."` is heavily used.
#   * Generally, single character strings are in single quotes (`'`) and multi characters in double
#     quotes (`"`).  Empty strings are represented as `""`.  Strings with multiple double quotes
#     can be enclosed in single quotes (e.g. `  f'<Tag foo="{foo}" bar="{bar}"/>'  `.)

import inspect                    # Python object inspection library used by *trace*:

# This module uses a couple of global variables for easy access:
global indent, trace_level, tracing
trace_level = 0
tracing = ""

import functools   # Clean up some introspection stuff with wrapper:

def trace(level):
    def value2text(value):
        """Convert a value to a human readable string."""
        # Start with *text* to something weird to start with:
        text = "?"

        # Dispatch on type of *value*:
        if isinstance(value, list):
            # We have a *list* and need to set *text* to "[]", "[value0]", or "[value0,...]":
            value_size = len(value)
            if value_size == 0:
                text="[]"
            else:
                elipsis = "" if value_size <= 1 else ",..."
                text = f"{value_size}:[{value2text(value[0])}{elipsis}]"
        elif isinstance(value, tuple):
            # We have a *tuple* and need to set *text* to "()", "(value0,)", or "(value0,...)":
            value_size = len(value)
            if value_size == 0:
                text="(,)"
            else:
                elipsis = "" if value_size <= 1 else "..."
                text = f"{value_size}({value2text(value[0])}{elipsis}]"
        elif isinstance(value, dict):
            # We have a *dict*, and need to set *text* to "{}", "{key0: value0}", or
            # "{key0: value0,...}":
            value_size = len(value)
            if value_size == 0:
                text="{}"
            else:
                elipsis = "" if value_size <= 1 else ",..."
                for key in value:
                    text = (f"{value_size}:"
                            f"{{{value2text(key)}:{value2text(value[key])}){elipsis}}}")
        elif isinstance(value, str):
            # We have a *str*, and need to set *text* to "value" or "val...ue" depending
            # upon *value_size*:
            value_size = len(value)
            text = f'"{value[:10]}...{value[-10:]}"' if value_size >= 20 else f'"{value}"'
        else:
            # All others just use the standard conversion:
            text = f"{value}"
        return text

    def decorator_wrapper(function):
        @functools.wraps(function)
        def wrapper(*arguments, **keyword_arguments):
            global trace_level
            global tracing

            # A *trace_level* of 0, means no tracing:
            if trace_level <= 0:
                results = function(*arguments, **keyword_arguments)
            else:
                # A *trace_level* greater than zero means tracing:
                signature = inspect.signature(function)
                tracing += " "
                function_name = function.__name__
                function_type = type(function)
                arguments_size = len(arguments)
                keyword_arguments_size = len(keyword_arguments)
                parameters_values = list(signature.parameters.values())
                parameters_values_size = len(parameters_values)
                is_method = inspect.ismethod(function)
                is_function = inspect.isfunction(function)
                class_name = fucntion.__class__.__name__ if is_method else "None"

                # print(f"trace_indent={trace_indent}")
                # print(f"function_name='{function_name}'")
                # print(f"function_type='{function_type}'")
                # print(f"arguments_size={arguments_size}")
                # print(f"keyword_arguments_size={keyword_arguments_size}")
                # print(f"parameters_values_size={parameters_values_size}")
                # print(f"is_method={is_method}")
                # print(f"is_function={is_function}")
                # print(f"class_name='{class_name}'")

                # Compute a list of *value_texts* for each *parameter_value* in *parameter_values*:
                value_texts = list()
                for index, parameter_value in enumerate(parameters_values):
                    # Dispatch on *index* to fetch the *value* from either *arguments* or
                    # *keyword_arguments*:
                    if index < arguments_size:
                        # Grab *value* from *arguments* and append it to *value_texts*:
                        value = arguments[index]
                        value_texts.append(value2text(value))
                    else:
                        # Grab *value* from *keyword_arguments* and append it to *value_texts*:
                        parameter_name = parameter_value.name
                        if parameter_name in keyword_arguments:
                            value = keyword_arguments[parameter_name]
                            value_texts.append(f"{parameter_name}={value2text(value)}")
                        elif parameter_value.default != inspect.Parameter.empty:
                            value = parameter_value.default
                        else:
                            value_texts.append(f"{parameter_name}=??")

                # Construct the final comma separated *arguments_text* string:
                arguments_text = ",".join(value_texts)

                # Print out the call trace line:
                print(f"{tracing}=>{function_name}({arguments_text})")

                # Call *function* with its positional *arguments* and its *keyword_arguments*)
                # and save the *results*:
                keyword_arguments["tracing"] = tracing
                results = function(*arguments, **keyword_arguments)

                # Now construct the *results_text* and print out the return line:
                results_text = ""
                if results is not None:
                    results_text = f"=>{value2text(results)}"
                print(f"{tracing}<={function_name}({arguments_text}){results_text}")

                # Kludge to get an extra blank line for GUI's:
                if len(tracing) <= 2:
                    print("")

                # Strip off one space from *tracing* and return *results*:
                tracing = tracing[:-1]
            
            # We are done, so just return *results*:
            return results
        return wrapper
    return decorator_wrapper

def trace_level_get():
    global trace_level
    return trace_level

def trace_level_set(new_trace_level):
    global trace_level, tracing
    trace_level = new_trace_level
    tracing = "" if trace_level <= 0 else " "
