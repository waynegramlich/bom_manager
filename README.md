# Bill of Materials Manager

## Introduction

For ECAD (Electronic Computer Aided Design) system, a project
consists of the following broad steps:

* Draw a schematic the describes the design.

* Select parts and footprints for the design.

* Lay out the printed circuit board.

* Order the selected parts from one or more vendors.

The BOM (Bill Of Materials) is the binding between the
schematic symbol labels (called references), a PCB footprint,
a manufacturer part number, and ultimately a vendor (e.g.
distributor) part number.

A schematic consists of one or more sheets, where each
filled with schematic symbols and lines (i.e. wires) that
interconnect the schematic symbols.  A schematic symbol
is a graphical representation of an electronic component
(e.g. resistor, capacitor, transistor, integrated circuit,
connector, sensor, etc.)  Each electronic component has
a physical implementation with one or more electrical
connection points (e.g. pins.)  Each pin has a name which
is usually (but not always) a number.

On a schematic, each schematic symbol has the following:

* A graphical representation.

* A short reference name (e.g. C7, R12, Q13, U7, etc.)

* A descriptive value (e.g 10uF, 1mH, 74HC00, etc.)

* Pin numbers (e.g. 7, E, etc.)

* An optional footprint name (e.g. DPAK, SOT23-3, etc.)

While all schematics have the graphical representations, reference names,
values, and pin numbers, the footprint name is frequently not present.
Frequently the pin numbers for simple parts such as resistors and capacitors
are not shown.

The ECAD system will take all of the schematic sheets and output
a file called a net list.  A *net* is a ultimately a list of
(reference name, pin number) pairs that indicate which electrical
component pins are electrically wired together.  A *net list* is
a list of all of the nets.  Each ECAD system typically has its own
nique file format for the net list file.

Each electrical component has a *footprint* that consist of a
list of *landings*.  A *landing* is an
oval/circular/rectangular/trapezoidal copper area which can be
soldered to an electronic component pin.  A through hole landing
has a hole through which a component pin is inserted, whereas a
surface mount landings do not have holes.  Some holes have no
copper associated with them and are used for mechanical attachment
only (e.g. screws, bolts, etc.)

When it comes to footprint naming strategies, about the only
standard that is seeing any use is the IPC-7351 standard.
Frankly, IPC-7351 is pretty well done and should be used more.
IPC-7351 is primarily a standard for surface mount footprints.

## Strategy

There is no one universally agreed upon workflow for designing
an electronic project.  Most ECAD systems start out supporting
one specific workflow and then get forced by the user community
to support multiple alternative workflows.

When it comes to schematics there two broad strategies:

* The schematic specifies a specific manufacturer part number
  for each schematic symbol.

* The schematic specifies a logical part name (e.g. "10uF") and
  leaves the selection of the manufacturer part number until much
  later the workflow (e.g. BOM generation.)

The advantage of the manufacturer part number strategy is that
each manufacturer part has an explicit footprint associated with it.
The disadvantage is that the schematic must be updated every time
a manufacturer part is changed.

The advantage of using a logical part number is that manufacturer
parts can swapped without requiring schematic changes.  The disadvantage
is that footprint selection must be done as a separate step.  It
is really easy to get a footprint that does not match the selected
manufacturer part.

We will cut to the chase here.  We are going to use a hybrid
strategy here.  The schematic value is going to specify a
logical name (e.g. 10uF) and a short footprint name (e.g.
SOIC8).  The format is represented as "logical_name;short_footprint"
(e.g. 74HC74;SOIC8, BSS138;SOT23-3, etc.)  This means that
the BOM management software can select between different manufacturers
as long as they match the logical name and short footprint name.

For example, surface mount resistors are typically rectangular.
Originally, they were specified by the their length and width in
mils (1 mil = .001" inch.)  Thus, popular surface mount resistor
sizes are 0805 (= .008" x .005"), 0603 (= .006" x .003"), 0402, etc.
More recently, the industry is pushing towards using metric values
that are specified in hundredths of a millimeter.  Thus, the
inch based 0603 has been renamed to the metric based 1608
(= .16mm x .08mm = .006" x .003").  Thus, for this system,
"10K;1608" means a 10K Ohm resistor in a metic 1608 package.

The *bom_manager* software maintains a database of
"logical_name;short_footprint" pairs.  Associated with each pair
is long footprint name (e.g. IPC-7351) and a list of acceptable
manufacturer part numbers.

The software does the following:

1. Reads net list file.

2. Looks up each name;footprint pair.

3. Updates the net list file with the correct long footprint name.

4. Accesses a part management selection system (currently Octopart)
   to identify vendors and prices.

5. Selects the vendors and generates an order for each vendor.

## Installation Issues

All the code lives in one file -- `bom_manager.py`.  However, you have
to install a bunch of libraries:

    sudo pip install bs4 requests sexpdata


