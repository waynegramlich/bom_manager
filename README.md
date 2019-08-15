# BOM Manager

The BOM Manager is a program for managing a project Bill Of Materials and
generating vendor orders.

## Introduction

BOM stands for Bill Of Materials.  Essentially a bill of materials is just a
list of "parts" needed to build a project -- a building, a mechanical assembly,
a printed circuit board, etc.  Note that "parts" is in quotes and is discussed
in greater detail a bit further below.  The BOM manager takes this list of parts
and generates a list of vendor orders.  You send the order to each vendor and
they fulfill your order by shipping the requested parts back to you.  Once all
of the parts have arrived you can assemble your project.  In brief, the BOM manager
is a program that assists you in generating vendor orders for a project.

The BOM manager program is meant to work in conjunction with a CAD (Computer Aided
Design) program.  The initial CAD program supported is KiCAD which is an
ECAD (Electronic Computer Aided Design) program for designing PCB's (Printed
Circuit Boards.)  A longer term goal is to support FreeCAD which is primarily
an MCAD (Mechanical Computer Aided Design) program, although it also supports
architectural building design.

The BOM manager program has a plug in software module that allows it to collect
a BOM from a particular CAD package.  Currently, there is only a KiCAD plug in.
Over time, additional CAD plugins are expected to be developed.

The term "part" by itself is ambiguous, so an adjective is used to be more concise.
Immediately below are some of the more concise part names:

* Actual Part: An actual part is the part that a manufacturer creates and sells.
  The manufacturer (e.g. Intel, Texas Instruments, etc.) assigns there own unique
  name to the actual part.

* Vendor Part: A vendor part is a part that can be purchased.  Sometimes the
  vendor and the manufacturer are the same, in which case, the part purchased
  directly from the manufacturer.  More frequently, there vendors (typically
  called distributors or resellers) that purchase actual parts directly from
  manufacturers, store the parts, and resell them.  Each distributor/reseller
  vendor typically assigns their own part name to the actual part that is different
  manufacturer part name.

* Project Part: A project part is a named part within the CAD system.  Ultimately,
  BOM manager provides tools to map the project part into a pool of one or more actual
  parts.  A project part is "specific" if there is only one actual part in the pool.
  A project part is "generic" if there multiple actual parts in the pool, and the BOM
  manager will eventually pick one actual part from the pool based one pricing and
  availability considerations.

* Posed Part: Each project part may occur in multiple locations within a project.
  A "pose" specifies the X/Y/Z location and orientation (e.g. &alpha;/&beta;/&gamma;)
  of the project part.  The count of the number of posed parts associated with a
  specific posed part, determines the total number of the project parts that need
  to be ordered.

What BOM manager does is:

1. It starts with a list of posed parts.

2. The posed part list is converted into a list of project parts.

3. The project parts list is expended into a list of actual parts.

4. The BOM manager queries to find which vendors sell each actual part
   an generates a list of vendor parts, where each vendor part has pricing
   and availability information.

5. The BOM manager takes the list vendor parts and selects between them all to
   minimize overall cost.  It takes into account shipping costs and well as some
   other heuristics.

6. The BOM manager generates a list of vendor orders that can be sent to each vendor.

For now, BOM manager is summarized as:

     Posed Parts => Project Parts => Actual Parts => Vendor Parts => Vendor Orders

There are some further nuances in parts:

* Alias Part: Sometimes when multiple people are working on the same project,
  they can accidentally choose different names for the same part (e.g. "red-widget"
  vs. "RedWidget".)  Rather than forcing a sweep through the entire project and
  forcing everybody to use the same name, the BOM manager supports the concept of
  an alias part, where one of the parts "points" to another part to substitute
  in its place.  By the way, it is possible to have an alias chain where Part1
  aliases to Part2 which aliases to Part3, etc.  This is acceptable as long as
  there is no loop (e.g. Part1 points to Part2 and Part2 points back to Part1.)

* Multi-part: Sometimes a part in the CAD system is not really one part but
  a set of parts.  For example, sometimes an electrical connector consists of a
  shell and a bunch of pins that are mounted into the connector.  When the BOM
  manager encounters a multi-part, it expands into other parts and orders each
  of them individually (possibly from different vendors.)
  
* Fractional Part: A fractional part is one where the final part is produced
  on site by extracting it from another larger part.  For example, a wire is
  cut from spool of wire.  The BOM manager orders the spool of wire, and you
  cut a length of it off as needed.  This also happens with some electrical
  connectors, where the larger connector cut to length to get the desired number
  of pins.

Now that we have described parts in greater detail, it is time to introduce
the over all architecture of BOM manager:

* Project: The BOM manager orders parts for one or more projects.  A project is
  basically one-to-one with a CAD "file".  Note: some CAD systems do not reduce a
  project down to a single file, but instead to a collection of files in one
  or more directories/folders.

* Order: An order specifies a list of projects and the number of each project
  instance that is desired.

* Collection: A collection is typically (but not always) associated with a vendor.
  It is a more generic term for a catalog.  In the past, vendors would print up a
  catalog   that lists all of the parts and associated prices that a vendor would
  sell.  These days, most vendors have a web presence that allows people to order
  on-line with up-to-date pricing and availability.  Each collection has a
  software plug-in that plugs into the BOM manager that supports access to the
  collection.  (At the moment there is only a Digi-Key plug-in.)

* Table: Ultimately a collection is organized as a set of hierarchical directories
  and sub-directories to get to a bunch of tables.  Each table is organized as a
  matrix of rows and columns where each row corresponds to a vendor part and
  each column specifies some parameter about the part.
  
* Search: A search has a name that is unique across the entire collection and
  winnows rows of a specific table down to ones that meet project requirements.
  While search names must unique across an entire collection, the names m
  Each project part name in a project must match at least one search name in one
  of the collections.

With these new concepts the over all BOM manager algorithm is:

1. Each order specifies one or more projects.

2. All projects are scanned to generates a list named posed parts.

3. The posed parts list generates a list named project parts.

4. BOM manager searches all of the selected collections to find searches
   that match each project part.

5. Each search generates a list available manufacturer parts.

6. Manufacturer part names are converted into a list vendor parts.

7. Vendor parts are winnowed down to vendor orders.

With these new concepts, the BOM manager algorithm is summarized as:

        Order => Projects => Posed Parts => Project Parts =>
            Collections => Tables => Searches =>
                Manufacturer Parts => Vendor Parts => Vendor Orders

That wraps up the overall BOM manager conceptual algorithm.

The BOM manager should be viewed as just one step of an overall workflow that
goes from idea to an assembled project that is ready to use.  For large projects,
a team of people is responsible for performing the overall workflow.  For smaller
projects, one person usually gets to do most of the workflow steps.

There are a distinct roles that can given to different people:

* Project Designer Role: This person interacts with the CAD system to design a project.
  This person is responsible for ensuring that project part names match up with
  search names.

* Librarian Role: This person is responsible for constructing the collection searches.
  This person basically needs to ensure that each project part has an associated
  search associated with at least one collection.  This person is responsible for
  coming up with naming conventions.

* Order Management Role: This person is responsible for running BOM manager, submitting
  orders to vendors, etc.

In addition, there are some BOM manager plug-in integration roles:

* Collection Integrator: This person is responsible for constructing the collection
  information and developing the collection software plug-in for BOM manager.

* CAD Integrator: This person is responsible for constructing the software plug-in
  for accessing a particular CAD system.

* Pricing and Availability Integrator: This person is responsible for constructing
  the software plug-in for accessing a particular pricing and availability site.

## (Old Introduction)

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

Eventually, there will be `setup.py` file, but for now everything is done manually.

The *bom_manager* software is currently only installable as Python3 source code format.
Currently, it is spread across two repositories -- `bom_manager` and `digikey_tables`.

        cd someplace....
        mkdir projects
        cd projects
        git clone https://github.com/waynegramlich/digikey_tables.git
        git clone https://github.com/waynegramlich/bom_manager.git

In addition, you will have to install a bunch of python modules (i.e. libraries).
This the list below is probabably incomplete:

        sudo -H pip3 install -r bom_manager.rec

If everything is properly installed, you should be able to bring up the `bom_manager` GUI.

The command line arguments are listed with:

        python3 bom_manager.py -h

The current help message is reproduced below:

        usage: bom_manager.py [-h] [-c COLLECTION] [-n NET] [-s SEARCH]
        
        Bill of Materials (BOM) Manager.
        
        optional arguments:
          -h, --help            show this help message and exit
          -c COLLECTION, --collection COLLECTION
                                BOM Manager Collection Directory.
          -n NET, --net NET     KiCAD .net file. Preceed with 'NUMBER:' to increase
                                count.
          -s SEARCH, --search SEARCH
                                BOM Manager Searches Directory.

You need to specify at least one collection using the `-c` option.
You should also specify some place to store your searches with the
`-s` option.  Example:

        python3 bom_manager.py -c ../digikey_tables -s /tmp/mysearches

If you want to point at some KiCAD `.net` files, use one or more `-n` options.
The `.net` file can be preceeded with `N:` where `N` is the count of the number
of the specified to order for.  Thus, `-n 5:my_board.net` means order parts for
5 `my_board.net` boards.

If you do specify one or more `-n` options, you can click on `[Order Check]`
to scan the `.net` files to see which parts do not have corresponding searches
in the `bom_manager`.

## Data organization

The data is split into collections and searches:

* Collections:

  Each collection lives in its own directory tree.
  At the moment, only the collection is the Digi-Key collection that is located
  over in the `digikey_tables` repository.  You will need to specify something like
  `-c ../digikey_tables` on the command line to point `bom_manager` at the Digi-Key
  collection.

  If you dig around in the `digikey_tables` directory, you will see a nested set of
  directories. with `.xml` files in them.  These `.xml` files specify the information
  about a class of search (e.g. chip resistors, rectangular connectors, IC's, etc.)

  The `bom_manager` GUI (Graphical User Interface) has a tree browser that lets you
  browse collections until you find a part category you are interested.

  The collections directories are read only and are **NEVER** modified by `bom_manager`.

* Searches:

  The `searches` directory is currently specified on the command line with the `-s`
  option and specifies the root directory of where you will store your searches.
  It is expected the eventually it will point into are `git` repository somewhere.
  As you create, modify, and delete searches, the requisite information is
  added/modified/deleted down in the searches directory.  The searches directory
  is basically a mirror of the each collection listed by a `-c` option, but it is
  only partially populated since sub-directories only created as needed to store
  new searches.

  The `searches` directory is read and written by `bom_manager` and it is organized
  to be very friendly with regards to parallel development via `git`.  Since each
  search is stored in a separate file, people can easily merge searches without
  conflicts unless both branches created a search with the exact same name.

  Searches that start with an `@` character are considered to be templates that
  other searches rely on.  The every search sub-directory conceptually has an
  `@ALL` search that matches everything in the parent table.

  {Talk about hierarchical templates here.}

## Operation:

The `bom_manager` is operated in conjunction with a web browser (only
Chrome has been tested so far.)  When you click on an `@ALL` search,
the web browser will instructed to visit Digi-Key and bring up the
search for the catagory.

You can now refine the search using the Digi-Key web interfaces to
your heart's content.  When you are ready to save a search do the following:

1. Go to the web browser and select the entire Digi-Key URL.  This URL
   encodes all of the information about your part search in it.

2. Go to the `bom_manager` GUI, and type in a new search name.  If it is
   meant to be used as a template, place an `@` as the first character.

3. Click on the [New Search] button.

After you have created a few searches, go to the GUI and click on them
and you will see that each time you click on one, the web browser switches
over to that search.

{More documenation later.}


## Random Comment

IPC-2581 is the PCB board layup specification specification that has some
overlap with ODBC++.
