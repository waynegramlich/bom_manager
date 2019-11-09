from bom_manager.node_view import (BomManager, Collection, Collections, Directory, Node,
                                   NodeTemplate, Parameter, ParameterComment, Table,
                                   TableComment, Search)
import lxml.etree as ETree   # type: ignore
from lxml.etree import _Element as Element  # type: ignore
from pathlib import Path
from typing import (Any, Dict, IO, List, Tuple)
from bom_manager.tracing import trace, trace_level_set, tracing_get

# test_attribute_converter():
@trace(4)
def test_attribute_converter():
    """Test the *BomManager* attribute converter methods."""
    # @trace(1)
    def check_both_ways(bom_manager: BomManager, text: str, substituted_text: str) -> None:
        tracing: str = tracing_get()
        attribute_text: str = bom_manager.to_attribute(text)
        reversed_text: str = bom_manager.from_attribute(attribute_text)
        if tracing:
            print(f"{tracing}text='{text}'")
            print(f"{tracing}attribute_text='{attribute_text}'")
            print(f"{tracing}reversed_text='{reversed_text}'")
        assert attribute_text == substituted_text, (f"attribute_text='{text}' "
                                                    f"subsituted_text='{substituted_text}'")
        assert text == reversed_text, (f"text='{text}' reversed_text='{reversed_text}'")

    # Perform a nasty convertion:
    bom_manager: BomManager = BomManager()
    check_both_ways(bom_manager, "before&amp;middle&semi;after",
                    "before&amp;amp&semi;middle&amp;semi&semi;after")

    # Verify that the empty string works:
    check_both_ways(bom_manager, "", "")

    # Verify that the entities in *ENTITY_SUBISTITUTIONS* are properly processed:
    ENTITY_SUBSTITUTIONS: Dict[str, str] = bom_manager.ENTITY_SUBSTITUTIONS
    character: str
    entity: str
    for character, entity in ENTITY_SUBSTITUTIONS.items():
        check_both_ways(bom_manager, character, entity)

    # Verify that "&#NNN;" is properly processed:
    maximum_unicode_ord: int = 0x110000 - 1
    index: int
    for index in range(8, 32):
        character_ord: int = 1 << index
        if character_ord <= maximum_unicode_ord:
            character = chr(character_ord)
            # print(f"Ord[{index}]:character_ord={character_ord} character='{character}'")
            assert ord(character) == character_ord, (f"character='{character}' "
                                                     f"character_ord={character_ord}")
            entity_text: str = f"&#{character_ord};"
            check_both_ways(bom_manager, character, entity_text)


# test_file_name_converter():
@trace(1)
def test_file_name_converter():
    """Test the *BomManager* file name converter."""

    def file_convert_check(bom_manager: BomManager, text: str) -> None:
        file_name: str = bom_manager.to_file_name(text)
        converted_text: str = bom_manager.from_file_name(file_name)
        assert text == converted_text, (f"text='{text}' file_name='{file_name}' "
                                        f"converted_text='{converted_text}'")

    # Grab some values from *bom_manager* (i.e. *self*):
    bom_manager: BomManager = BomManager()
    UNICODE_MAXIMUM = bom_manager.UNICODE_MAXIMUM

    # Convert null character:
    null_character: str = chr(0)
    null_character_file_name: str = bom_manager.to_file_name(null_character)
    assert null_character_file_name == "%00"
    null_character_file_name_converted: str = bom_manager.from_file_name(null_character_file_name)
    assert null_character_file_name_converted == null_character

    # Sweep through the ASCII space:
    tracing: str = tracing_get()
    if tracing:  # pragma: no cover
        print(f"{tracing}Started test_file_name_converter")
    character_ord: int
    character: str
    for character_ord in range(128):
        character = chr(character_ord)
        file_convert_check(bom_manager, character)

    # Sweep through some more of the Unicode space:
    for index in range(32):
        character_ord = 1 << index
        if character_ord <= UNICODE_MAXIMUM:
            character = chr(character_ord)
            file_convert_check(bom_manager, character)

    # Do some additional tests:
    bom_manager.to_file_name("") == ""
    bom_manager.from_file_name("") == ""
    bom_manager.to_file_name("abc - def") == "abc_%2d_def"
    bom_manager.from_file_name("abc_%2d_def") == "abc - def"
    bom_manager.to_file_name("foo/bar") == "foo%2fbar"
    bom_manager.from_file_name("foo%2fbar") == "foo/bar"


# Test_constrcutors():
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
    collection_root: Path = test_file_directory / "ROOT"
    searches_root: Path = test_file_directory / "searches"
    digikey_collection: Collection = Collection(bom_manager,
                                                "Digi-Key", collection_root, searches_root)
    digikey_collection_key: Tuple[int, int] = collections.collection_insert(digikey_collection)
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
    # chip_resistors_table_path: Path = (digikey_root /
    #                                    "Resistors" / "Chip_Resistor_-_Surface_Mount.xml")
    chip_resistors_table: Table = Table(bom_manager, "Chip Resistor - Surface Mount",
                                        digikey_collection_key)
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
    collections.xml_lines_append(xml_lines, "")
    xml_lines.append("")
    xml_text: str = '\n'.join(xml_lines)
    xml_file: IO[Any]
    with open("/tmp/xml_lines.xml", "w") as xml_file:
        xml_file.write(xml_text)
    table_nodes: List[Node] = list()
    digikey_collection.nodes_collect_recursively(Table, table_nodes)

    collections_element: Element = ETree.fromstring(xml_text)
    foo_collections: Collections = Collections.xml_parse(collections_element, bom_manager)
    reread_xml_lines: List[str] = list()
    foo_collections.xml_lines_append(reread_xml_lines, "")
    reread_xml_lines.append("")
    with open("/tmp/xml_lines2.xml", "w") as xml_file:
        xml_file.write('\n'.join(reread_xml_lines))

    assert xml_lines == reread_xml_lines


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


if __name__ == "__main__":
    trace_level_set(0)
    test_file_name_converter()
