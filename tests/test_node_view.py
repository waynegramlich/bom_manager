from bom_manager.node_view import (BomManager, Collection, Collections, Directory, Node,
                                   NodeTemplate, Parameter, ParameterComment, Table,
                                   TableComment, Search)
from pathlib import Path
from typing import (Any, IO, List,)
from bom_manager.tracing import trace_level_set


trace_level_set(0)


# test_constrcutors():
def test_constructors():
    """Test the various *Node* sub-class constructors."""
    # Identify the *test_file_directory*:
    test_file_path: Path = Path(__file__)
    test_file_directory: Path = test_file_path.parent

    # Create *bom_manager* and *collections* and verify:
    bom_manager: BomManager = BomManager()
    collections: Collections = Collections(bom_manager)
    assert collections.show_lines_get() == [
        "Collections()"
        ]

    # Create a *node_template* and verify the *__str__*() method:
    node_template: NodeTemplate = NodeTemplate(Node, (), {})
    node_template_text: str = node_template.__str__()
    assert node_template_text == "NodeTemplate('Node')", ("node_template_text="
                                                          f"'{node_template_text}'")

    # Create *digikey_collection* and verify:
    digikey_root: Path = test_file_directory / "ROOT" / "Digi-Key"
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
    chip_resistors_table_path: Path = (digikey_root /
                                       "Resistors" / "Chip_Resistor_-_Surface_Mount.xml")
    chip_resistors_table: Table = Table(bom_manager, "Chip Resistor - Surface Mount",
                                        chip_resistors_table_path)
    table_comment: TableComment = TableComment(bom_manager, "EN")
    table_comment.lines_set(["Line 1", "Line 2"])
    table_comment.line_append("Line 3")
    assert table_comment.__str__() == "TableComment('EN')"
    chip_resistors_table.comment_insert(table_comment)

    resistors_directory.table_insert(chip_resistors_table)
    assert collections.show_lines_get() == [
        "Collections()",
        " Collection('Digi-Key')",
        "  Directory('Capacitors')",
        "  Directory('Resistors')",
        "   Table('Chip Resistor - Surface Mount')",
        "    TableComment('EN')"
        ]

    # Stuff *manufacturer_parameter* and *all_search* into *chip_resistor_table*:
    manufacturer_parameter: Parameter = Parameter(bom_manager, "Manufacturer No.", "String", 0)
    chip_resistors_table.parameter_insert(manufacturer_parameter)
    manufacturer_parameter_comment_en: ParameterComment = ParameterComment(bom_manager, "EN")
    manufacturer_parameter_comment_en.line_append("Manufacturer Part Number")
    manufacturer_parameter.comment_insert(manufacturer_parameter_comment_en)
    manufacturer_parameter_comment_ru: ParameterComment = ParameterComment(bom_manager, "RU")
    manufacturer_parameter.comment_insert(manufacturer_parameter_comment_ru)
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
        "     ParameterComment('EN')",
        "     ParameterComment('RU')",
        "    Search('@ALL')",
        "    TableComment('EN')"
        ]

    show_lines_file: IO[Any]
    with open("/tmp/show_lines.txt", "w") as show_lines_file:
        text: str = "\n".join(collections.show_lines_get()) + '\n'
        show_lines_file.write(text)


    # Create some nested sub-directories:
    connectors_directory: Directory = Directory(bom_manager, "Connectors")
    digikey_collection.directory_insert(connectors_directory)
    rectangular_connectors_sub_directory: Directory = Directory(bom_manager,
                                                                "Rectangular Connectors")
    connectors_directory.directory_insert(rectangular_connectors_sub_directory)

    assert collections.show_lines_get() == [
        "Collections()",
        " Collection('Digi-Key')",
        "  Directory('Capacitors')",
        "  Directory('Resistors')",
        "   Table('Chip Resistor - Surface Mount')",
        "    Parameter('Manufacturer No.')",
        "     ParameterComment('EN')",
        "     ParameterComment('RU')",
        "    Search('@ALL')",
        "    TableComment('EN')",
        "  Directory('Connectors')",
        "   Directory('Rectangular Connectors')"
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

    collections.show_lines_file_write(Path("/tmp/show_lines.txt"), "")

    xml_lines: List[str] = list()
    digikey_collection.xml_lines_append(xml_lines, "", "")

    table_nodes: List[Node] = list()
    digikey_collection.nodes_collect_recursively(Table, table_nodes)


# test_partial_load():
def xxx_test_partial_load():
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


# test_packages_scan():
def xxx_test_packages_scan():
    """Verify that the packages scan code works."""
    bom_manager: BomManager = BomManager()
    collections: Collections = Collections(bom_manager)
    collections.packages_scan()
