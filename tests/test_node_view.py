from bom_manager.node_view import (BomManager, Collection, Collections, Directory, Node,
                                   NodeTemplate, Parameter, ParameterComment, Table,
                                   TableComment, Search)
import lxml.etree as ETree   # type: ignore
from lxml.etree import _Element as Element  # type: ignore
from pathlib import Path
from typing import (Any, Dict, IO, List)
from bom_manager.tracing import trace_level_set, tracing_get, trace


# directory_remove_entirely():
def directory_remove_entirely(directory_path: Path) -> None:
    """Remove a directory and all of its children.

    Recursively visit all of the files and sub-directories of
    *directory_path* followed by removing *directory_path* itself.

    Args:
        *directory_path* (*Path*): The directory to entirely remove.

    """
    if directory_path.is_dir():
        sub_path: Path
        for sub_path in directory_path.iterdir():
            if sub_path.is_dir():
                directory_remove_entirely(sub_path)
            else:
                sub_path.unlink()
        directory_path.rmdir()


# test_attribute_converter():
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
    # Determine the *test_file_directory*:
    test_file_path: Path = Path(__file__)
    test_file_directory: Path = test_file_path.parent

    # Create a *node_template* and verify the *__str__*() method:
    node_template: NodeTemplate = NodeTemplate(Node, (), {})
    node_template_text: str = node_template.__str__()
    assert node_template_text == "NodeTemplate('Node')", ("node_template_text="
                                                          f"'{node_template_text}'")

    # Create *bom_manager* and *collections* and verify:
    bom_manager: BomManager = BomManager()
    collections: Collections = Collections(bom_manager, "Root")
    assert collections.show_lines_get() == [
        "Collections('Root')"
        ]

    # Create an empty *test_collection_root* directory:
    test_collection_root: Path = test_file_directory / "TMP_ROOT"
    directory_remove_entirely(test_collection_root)
    test_collection_root.mkdir(parents=True, exist_ok=True)

    # Create *digikey_collection*, insert into *collections* and verify:
    searches_root: Path = test_file_directory / "searches"
    digikey_collection: Collection = Collection(bom_manager,
                                                "Digi-Key", test_collection_root, searches_root)
    digikey_collection_key: int = digikey_collection.collection_key
    assert digikey_collection_key >= 0
    assert digikey_collection is bom_manager.collection_lookup(digikey_collection_key)
    collections.collection_insert(digikey_collection)
    assert collections.show_lines_get() == [
        "Collections('Root')",
        " Collection('Digi-Key')"
        ]

    # Create the *capacitors_directory* and *resistors_directory* and insert into
    # *digikey_colleciton*:
    capacitors_directory: Directory = Directory(bom_manager, "Capacitors", digikey_collection_key)
    digikey_collection.directory_insert(capacitors_directory)
    assert capacitors_directory.collection_get() is digikey_collection
    resistors_directory: Directory = Directory(bom_manager, "Resistors", digikey_collection_key)
    digikey_collection.directory_insert(resistors_directory)
    assert resistors_directory.collection_get() is digikey_collection
    assert collections.show_lines_get() == [
        "Collections('Root')",
        " Collection('Digi-Key')",
        "  Directory('Capacitors')",
        "  Directory('Resistors')"
        ]

    # Create  *chip_resistors_table* and stuff it into *resistors_directory*:
    # chip_resistors_table_path: Path = (digikey_root /
    #                                    "Resistors" / "Chip_Resistor_-_Surface_Mount.xml")
    chip_resistors_table: Table = Table(bom_manager, "Chip Resistor - Surface Mount",
                                        digikey_collection_key, "URL", 123, "base")
    assert chip_resistors_table.collection_get() is digikey_collection
    table_comment: TableComment = TableComment(bom_manager, "EN")
    table_comment.lines_set(["Line 1", "Line 2"])
    table_comment.line_append("Line 3")
    assert table_comment.__str__() == "TableComment('EN')"
    chip_resistors_table.comment_insert(table_comment)

    resistors_directory.table_insert(chip_resistors_table)
    assert collections.show_lines_get() == [
        "Collections('Root')",
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
    all_search: Search = Search(bom_manager, "@ALL", digikey_collection_key)
    chip_resistors_table.search_insert(all_search)
    assert all_search.collection_get() is digikey_collection
    assert collections.show_lines_get() == [
        "Collections('Root')",
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

    # Remove a *Node* and verify its removal:
    manufacturer_parameter.remove(manufacturer_parameter_comment_ru)
    assert collections.show_lines_get() == [
        "Collections('Root')",
        " Collection('Digi-Key')",
        "  Directory('Capacitors')",
        "  Directory('Resistors')",
        "   Table('Chip Resistor - Surface Mount')",
        "    Parameter('Manufacturer No.')",
        "     ParameterComment('EN')",
        "    Search('@ALL')",
        "    TableComment('EN')"
        ], f"{collections.show_lines_get()}"

    # Create some nested sub-directories and verify:
    connectors_directory: Directory = Directory(bom_manager, "Connectors", digikey_collection_key)
    digikey_collection.directory_insert(connectors_directory)
    rectangular_connectors_sub_directory: Directory = Directory(bom_manager,
                                                                "Rectangular Connectors",
                                                                digikey_collection_key)
    connectors_directory.directory_insert(rectangular_connectors_sub_directory)
    assert collections.show_lines_get() == [
        "Collections('Root')",
        " Collection('Digi-Key')",
        "  Directory('Capacitors')",
        "  Directory('Resistors')",
        "   Table('Chip Resistor - Surface Mount')",
        "    Parameter('Manufacturer No.')",
        "     ParameterComment('EN')",
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

    # Do a similar test again:
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

    # Write the current *collections* *show_lines_append* output out to a file:
    collections.show_lines_file_write(Path("/tmp/show_lines.txt"), "")

    # Now verify that XML writing and parsing works:
    # Step one: fill in *xml_lines1* from *collections*:
    xml_lines1: List[str] = list()
    collections.xml_lines_append(xml_lines1, "")
    xml_lines1.append("")
    xml_lines1_text: str = '\n'.join(xml_lines1)

    # For debugging write out *xml_lines1_text* to a file:
    xml_file: IO[Any]
    with open("/tmp/xml_lines1.xml", "w") as xml_file:
        xml_file.write(xml_lines1_text)

    # Now parse *xml_lines2_text* into *collections2*:
    collections_element: Element = ETree.fromstring(xml_lines1_text)
    collections2: Collections = Collections.xml_parse(collections_element, bom_manager)

    # Now regenerate the *xml_lines2_text*:
    xml_lines2: List[str] = list()
    collections2.xml_lines_append(xml_lines2, "")
    xml_lines2.append("")
    xml_lines2_text: str = "\n".join(xml_lines2)

    # For debugging write out *xml_lines2_text* to a file:
    with open("/tmp/xml_lines2.xml", "w") as xml_file:
        xml_file.write(xml_lines2_text)

    # Finally verify that *xml_lines1* matches *xml_lines2*:
    assert xml_lines1 == xml_lines2

    # Just execute *nodes_collect_recursively* and verify that it finds all of the *directory_nodes*
    # and *table_nodes*:
    directory_nodes: List[Node] = list()
    digikey_collection.nodes_collect_recursively(Directory, directory_nodes)
    assert len(directory_nodes) == 4
    table_nodes: List[Node] = list()
    digikey_collection.nodes_collect_recursively(Table, table_nodes)
    assert len(table_nodes) == 1
    search_nodes: List[Node] = list()
    digikey_collection.nodes_collect_recursively(Search, search_nodes)
    assert len(search_nodes) == 1

    # Create a simple `.csv` file text:
    csv_lines: List[str] = [
        "Header1,Header2,Header3",
        "123,abc,-",
        "456,def,-",
        ""]
    csv_text: str = "\n".join(csv_lines)

    # Define *bogus_table_csv_fetch* which simply returns *csv_text*:
    def bogus_table_csv_fetch(table: Table) -> str:
        return csv_text

    # Force the population of the *temporary_root directory* with a single `.csv` file:
    downloads: int = digikey_collection.csvs_download(test_collection_root, bogus_table_csv_fetch)
    assert downloads == 1

    # Make sure that the correct *csv_file_path* was produced:
    csv_file_paths: List[Path] = list(test_collection_root.glob("**/*.csv"))
    assert len(csv_file_paths) == 1
    csv_file_path: Path = csv_file_paths[0]
    assert csv_file_path == (test_collection_root / "Digi%2dKey" / "Resistors" /
                             "Chip_Resistor_%2d_Surface_Mount.csv")

    # Read in *csv_file_path* into *reread_csv_text* and verify that it matches *csv_text*:
    reread_csv_text: str = ""
    csv_file: IO[Any]
    with csv_file_path.open() as csv_file:
        reread_csv_text = csv_file.read()
    assert csv_text == reread_csv_text

    # Now cause the table `.xml` file be generated:
    assert digikey_collection.collection_root == test_collection_root
    digikey_collection.csvs_read_and_process(True)

    # Now verify that the correct *xml_file_path* .xml file was produced:
    xml_file_paths: List[Path] = list(test_collection_root.glob("**/*.xml"))
    assert len(xml_file_paths) == 1
    xml_file_path: Path = xml_file_paths[0]
    assert xml_file_path == (test_collection_root / "Digi%2dKey" / "Resistors" /
                             "Chip_Resistor_%2d_Surface_Mount.xml")

    xml_text: str = ""
    xml_file: IO[Any]
    with xml_file_path.open() as xml_file:
        xml_text = xml_file.read()
    print(xml_text)
    xml_lines: List[str] = xml_text.split("\n")

    # Set to *True* to print out the desired values *target_xml_lines* and *False* to use the
    # values that were cut and pasted back into the code below:
    target_xml_lines: List[str] = list()
    if False:
        xml_line: str
        print("        target_xml_lines = [")
        for xml_line in xml_lines:
            print(f"            '{xml_line}',")  # *xml_line* can contain double quote characters.
        print("        ]")
        assert False
    else:
        # Cut and paste the output from above here:
        target_xml_lines = [
            '<?xml version="1.0"?>',
            '<Table name="Chip Resistor - Surface Mount" url="URL" nonce="123" base="base">',
            '  <Parameter name="Manufacturer No." index="0" type_name="String">',
            '    <ParameterComment language="EN">',
            '      Manufacturer Part Number',
            '    </ParameterComment>',
            '  </Parameter>',
            '  <Parameter name="Header2" index="1" type_name="String"/>',
            '  <Parameter name="Header3" index="2" type_name="Empty"/>',
            '  <TableComment language="EN">',
            '    Line 1',
            '    Line 2',
            '    Line 3',
            '  </TableComment>',
            '  <Search name="@ALL"/>',
            '</Table>',
            '',
        ]

    # Now verify that nothing has changed:
    assert xml_lines == target_xml_lines

    # Remove *test_collection_root*:
    directory_remove_entirely(test_collection_root)


# test_packages_scan():
def test_packages_scan():
    """Verify that the packages scan code works."""

    # Figure out the *searches_path* to use:
    test_node_view_file_name: str = __file__
    test_node_view_path: Path = Path(test_node_view_file_name)
    test_node_view_directory: Path = test_node_view_path.parent
    searches_root: Path = test_node_view_directory / "searches"
    assert searches_root.is_dir()

    # Create a *bom_manager* and *collections*:
    bom_manager: BomManager = BomManager()
    collections: Collections = Collections(bom_manager, "Root")

    # Invoke the *packages_scan* method and verify that we got a collection:
    collections.packages_scan(searches_root)
    collections: List[Collection] = collections.collections_get(True)
    assert len(collections) == 1
    digikey_collection: Collection = collections[0]
    assert digikey_collection.name == "Digi-Key"


# test_load_recursively():
@trace(1)
def test_load_recursively():
    test_file_path: Path = Path(__file__)
    test_file_directory: Path = test_file_path.parent

    # Create *bom_manager* and *collections* and verify:
    bom_manager: BomManager = BomManager()
    collections: Collections = Collections(bom_manager, "Root")

    # Create *digikey_collection* and verify:
    digikey_root: Path = test_file_directory / "ROOT"
    searches_root: Path = test_file_directory / "searches"
    digikey_collection: Collection = Collection(bom_manager,
                                                "Digi-Key", digikey_root, searches_root)
    collections.collection_insert(digikey_collection)

    # Now perform parial *load_recursively* on *digikey_collection*:
    digikey_collection.load_recursively(True)

    # Verify that we get the correct values in *show_lines*:
    show_lines: List[str] = collections.show_lines_get()
    show_lines.append("")
    with open("/tmp/partial_load", "w") as show_lines_file:
        show_line: str
        show_lines_text: str = "\n".join([f'        "{show_line}"' for show_line in show_lines])
        show_lines_file.write(show_lines_text)
    assert show_lines == [
        "Collections('Root')",
        " Collection('Digi-Key')",
        "  Directory('Digi-Key')",
        "   Directory('Capacitors')",
        "    Table('Aluminum - Polymer Capacitors')",
        "    Table('Niobium Oxide Capacitors')",
        "    Table('Thin Film Capacitors')",
        "    Table('Tantalum - Polymer Capacitors')",
        "    Table('Tantalum Capacitors')",
        "    Table('Trimmers, Variable Capacitors')",
        "    Table('Aluminum Electrolytic Capacitors')",
        "    Table('Silicon Capacitors')",
        "    Table('Electric Double Layer Capacitors (EDLC), Supercapacitors')",
        "    Table('Capacitor Networks, Arrays')",
        "    Table('Accessories')",
        "    Table('Mica and PTFE Capacitors')",
        "    Table('Ceramic Capacitors')",
        "     Search('CAP CER 22UF 6.3V X5R 0603')",
        "     Search('@ALL')",
        "    Table('Film Capacitors')",
        "   Directory('Resistors')",
        "    Table('Resistor Networks, Arrays')",
        "     Search('@ALL')",
        "    Table('Specialized Resistors')",
        "    Table('Chip Resistor - Surface Mount')",
        "    Table('Through Hole Resistors')",
        "    Table('Accessories')",
        "    Table('Chassis Mount Resistors')",
        "     Search('@ALL')",
        "",
        ], f"show_lines={show_lines}"

    # Now perform a non-partial (i.e. ful)l *load_recursively* on *digikey_collection*:
    collections2: Collections = Collections(bom_manager, "Root")
    digikey_collection2: Collection = Collection(bom_manager,
                                                 "Digi-Key", digikey_root, searches_root)
    collections2.collection_insert(digikey_collection2)
    digikey_collection2.load_recursively(False)

    # Verify that we get the correct values in *show_lines*:
    trace_level_set(1)
    xml_lines: List[str] = list()
    collections2.xml_lines_append(xml_lines, "")
    xml_lines.append("")
    xml_text: str = '\n'.join(xml_lines)
    xml_file: IO[Any]
    with open("/tmp/full_load.xml", "w") as xml_file:
        xml_file.write(xml_text)


if __name__ == "__main__":
    trace_level_set(1)
    # test_file_name_converter()
    test_load_recursively()
