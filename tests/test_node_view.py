from bom_manager.node_view import (BomManager, Collection, Collections, Directory, Node, Parameter,
                                   Table, Search)
from pathlib import Path
from typing import (List,)
from bom_manager.tracing import trace_level_set


trace_level_set(0)


def test_constructors():
    test_file_path: Path = Path(__file__)
    test_file_directory: Path = test_file_path.parent

    # Create *bom_manager* and *collections* and verify:
    bom_manager: BomManager = BomManager()
    collections: Collections = Collections(bom_manager)
    assert collections.show_lines_get() == [
        "Collections()"
        ]

    # Create *digikey_collection* and verify:
    digikey_root: Path = test_file_directory / "ROOT"
    searches_root: Path = test_file_directory / "searches"
    digikey_collection: Collection = Collection(bom_manager,
                                                "Digi-Key", digikey_root, searches_root)
    collections.collection_insert(digikey_collection)
    assert collections.show_lines_get() == [
        "Collections()",
        " Collection('Digi-Key')"
        ]

    # Create the *capacitors_directory* and *resistors_directory* and insert into
    # *digikey_colleciton*:
    capacitors_directory: Directory = Directory(bom_manager, "Capacitors")
    digikey_collection.directory_insert(capacitors_directory)
    resistors_directory: Directory = Directory(bom_manager, "Resistors")
    digikey_collection.directory_insert(resistors_directory)
    assert collections.show_lines_get() == [
        "Collections()",
        " Collection('Digi-Key')",
        "  Directory('Capacitors')",
        "  Directory('Resistors')"
        ]

    # Create  *chip_resistors_table* and stuff it into *resistors_directory*:
    chip_resistors_table_path: Path = digikey_root / "Resistors/Chip_Reisistor_-_Surface_Mount.xml"
    chip_resistors_table: Table = Table(bom_manager, "Chip Resistor - Surface Mount",
                                        chip_resistors_table_path)
    resistors_directory.table_insert(chip_resistors_table)
    assert collections.show_lines_get() == [
        "Collections()",
        " Collection('Digi-Key')",
        "  Directory('Capacitors')",
        "  Directory('Resistors')",
        "   Table('Chip Resistor - Surface Mount')"
        ]

    # Stuff *manufacturer_parameter* and *all_search* into *chip_resistor_table*:
    manufacturer_parameter: Parameter = Parameter(bom_manager, "Manufacturer No.")
    chip_resistors_table.parameter_insert(manufacturer_parameter)
    all_search_table_path: Path = (searches_root / "Digi-Key" / "Resistors" /
                                   "Chip_Resistor_-_Surface_Mount.xml" / "@ALL.xml")
    all_search: Search = Search(bom_manager, "@ALL", all_search_table_path)
    chip_resistors_table.search_insert(all_search)
    assert collections.show_lines_get() == [
        "Collections()",
        " Collection('Digi-Key')",
        "  Directory('Capacitors')",
        "  Directory('Resistors')",
        "   Table('Chip Resistor - Surface Mount')",
        "    Parameter('Manufacturer No.')",
        "    Search('@ALL')"
        ]

    # Perform a recursive data validity test for *collections*:
    collections.attributes_validate_recursively()

    # Test *tree_path_find* method and invoke the various *__str__* methods:
    tree_path: List[Node] = list()
    collections.tree_path_find(all_search, tree_path)
    desired_path = [
        all_search,
        chip_resistors_table,
        resistors_directory,
        digikey_collection,
        collections]
    tree_path_names: List[str] = [node.__str__() for node in tree_path]
    desired_path_names: List[str] = [node.__str__() for node in desired_path]
    assert tree_path_names == desired_path_names, (f"tree_path_names={tree_path_names} != "
                                                   f"desired_path_names={desired_path_names}")
    tree_path = list()
    resistors_directory.tree_path_find(manufacturer_parameter, tree_path)
    desired_path = [
        manufacturer_parameter,
        chip_resistors_table,
        resistors_directory]
    tree_path_names: List[str] = [node.__str__() for node in tree_path]
    desired_path_names: List[str] = [node.__str__() for node in desired_path]
    assert tree_path_names == desired_path_names, (f"tree_path_names={tree_path_names} != "
                                                   f"desired_path_names={desired_path_names}")


def test_partial_load():
    test_file_path: Path = Path(__file__)
    test_file_directory: Path = test_file_path.parent

    # Create *bom_manager* and *collections* and verify:
    bom_manager: BomManager = BomManager()
    collections: Collections = Collections(bom_manager)

    # Create *digikey_collection* and verify:
    digikey_root: Path = test_file_directory / "ROOT"
    searches_root: Path = test_file_directory / "searches"
    digikey_collection: Collection = Collection(bom_manager,
                                                "Digi-Key", digikey_root, searches_root)
    collections.collection_insert(digikey_collection)

    # Now perform *partial_load* on *digikey_collection*:
    digikey_collection.partial_load()

    # Verify that we get the correct values in *show_lines*:
    show_lines = collections.show_lines_get()
    with open("/tmp/partial_load", "w") as show_file:
        show_line: str
        for show_line in show_lines:
            show_file.write(f'        "{show_line}",\n')
    assert show_lines == [
        "Collections()",
        " Collection('Digi-Key')",
        "  Directory('Digi-Key')",
        "   Directory('Capacitors')",
        "    Table('Niobium Oxide Capacitors')",
        "    Table('Thin Film Capacitors')",
        "    Table('Tantalum Capacitors')",
        "    Table('Trimmers, Variable Capacitors')",
        "    Table('Aluminum Electrolytic Capacitors')",
        "    Table('Silicon Capacitors')",
        "    Table('Electric Double Layer Capacitors (EDLC), Supercapacitors')",
        "    Table('Tantalum - Polymer Capacitors')",
        "    Table('Capacitor Networks, Arrays')",
        "    Table('Accessories')",
        "    Table('Aluminum - Polymer Capacitors')",
        "    Table('Mica and PTFE Capacitors')",
        "    Table('Ceramic Capacitors')",
        "     Search('CAP CER 22UF 6.3V X5R 0603')",
        "     Search('@ALL')",
        "    Table('Film Capacitors')",
        "   Directory('Resistors')",
        "    Table('Resistor Networks, Arrays')",
        "     Search('@ALL')",
        "    Table('Chip Resistor - Surface Mount')",
        "     Search('220;1608')",
        "     Search('@1%Tol')",
        "     Search('@ActStkRohs')",
        "     Search('1k;1608')",
        "     Search('@ALL')",
        "     Search('@;1608')",
        "     Search('120;1608')",
        "     Search('470;1608')",
        "    Table('Specialized Resistors')",
        "    Table('Through Hole Resistors')",
        "    Table('Accessories')",
        "    Table('Chassis Mount Resistors')",
        "     Search('@ALL')",
        ], f"show_lines={show_lines}"
