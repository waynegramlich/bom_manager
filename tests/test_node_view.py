from bom_manager.node_view import (BomManager, Collection, Group, Directory, Node, Nodes,
                                   NodeTemplate, Parameter, ParameterComment, Table,
                                   TableComment, Search)
import lxml.etree as ETree   # type: ignore
from lxml.etree import _Element as Element  # type: ignore
from pathlib import Path
from typing import (Any, Dict, IO, List)
from bom_manager.tracing import trace_level_set, tracing_get, trace


# remove_directory_recursively():
def remove_recursively(path: Path) -> None:
    """Recursivly removed directories and files.

    If *path* exists, it will be recursively removed whether *path* is
    a directory or a file.

    Args:
        *path* (*Path*): The directory or file to remove.

    """
    if path.exists():
        if path.is_dir():
            sub_path: Path
            for sub_path in path.iterdir():
                remove_recursively(sub_path)
            path.rmdir()
        elif path.is_file():
            path.unlink()
        else:
            assert False, (f"'{path} is neither a file nor a directory")  # pragma: no cover


# temporary_directory_create():
def temporary_directory_create() -> Path:
    """Create an empty test directory and return the path.

    Returns:
        The *Path* to newly created empty temporary directory.
    """
    # Determine the *test_file_directory*:
    test_file_path: Path = Path(__file__)
    test_file_directory: Path = test_file_path.parent

    # Create an empty *temporary_directory*:
    temporary_directory: Path = test_file_directory / "TMP"
    remove_recursively(temporary_directory)
    temporary_directory.mkdir(parents=True, exist_ok=True)

    # Return the path to the newly created *temporary_directory*:
    return temporary_directory


# temporary_directory_destroy():
def temporary_directory_destroy() -> None:
    """Create an empty test directory and return the path.

    Returns:
        The *Path* to newly created empty temporary directory.
    """
    # Determine the *test_file_directory*:
    test_file_path: Path = Path(__file__)
    test_file_directory: Path = test_file_path.parent
    temporary_directory: Path = test_file_directory / "TMP"
    remove_recursively(temporary_directory)


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

    # Create the *temporary_directory* for writing miscellaneous stuff out to:
    temporary_directory: Path = temporary_directory_create()

    # Create a *node_template* and verify the *__str__*() method:
    node_template: NodeTemplate = NodeTemplate(Node, (), {})
    node_template_text: str = node_template.__str__()
    assert node_template_text == "NodeTemplate('Node')", ("node_template_text="
                                                          f"'{node_template_text}'")

    # Create *bom_manager* and *group* and verify:
    bom_manager: BomManager = BomManager()
    root_group: Group = Group(bom_manager, "Root")
    assert root_group.show_lines_get() == [
        "Group('Root')"
        ]

    # Create an *electronics_group":
    electronics_group = Group(bom_manager, "Electronics")
    root_group.sub_group_insert(electronics_group)

    # Create an empty *test_collection_root* directory:
    test_collection_root: Path = test_file_directory / "TMP_ROOT"
    remove_recursively(test_collection_root)
    test_collection_root.mkdir(parents=True, exist_ok=True)

    # Create *digikey_collection*, insert into *group* and verify:
    searches_root: Path = test_file_directory / "searches"
    digikey_collection: Collection = Collection(bom_manager,
                                                "Digi-Key", test_collection_root, searches_root)
    digikey_collection_key: int = digikey_collection.collection_key
    assert digikey_collection_key >= 0
    assert digikey_collection is bom_manager.collection_lookup(digikey_collection_key)
    electronics_group.collection_insert(digikey_collection)
    root_group_show_lines: List[str] = root_group.show_lines_get()
    assert root_group_show_lines == [
        "Group('Root')",
        " Group('Electronics')",
        "  Collection('Digi-Key')"
        ], f"root_group_show_lines = {root_group_show_lines}"

    # Create the *capacitors_directory* and *resistors_directory* and insert into
    # *digikey_colleciton*:
    capacitors_directory: Directory = Directory(bom_manager, "Capacitors", digikey_collection_key)
    digikey_collection.directory_insert(capacitors_directory)
    assert capacitors_directory.collection_get() is digikey_collection
    resistors_directory: Directory = Directory(bom_manager, "Resistors", digikey_collection_key)
    digikey_collection.directory_insert(resistors_directory)
    assert resistors_directory.collection_get() is digikey_collection
    assert root_group.show_lines_get() == [
        "Group('Root')",
        " Group('Electronics')",
        "  Collection('Digi-Key')",
        "   Directory('Capacitors')",
        "   Directory('Resistors')"
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
    assert root_group.show_lines_get() == [
        "Group('Root')",
        " Group('Electronics')",
        "  Collection('Digi-Key')",
        "   Directory('Capacitors')",
        "   Directory('Resistors')",
        "    Table('Chip Resistor - Surface Mount')",
        "     TableComment('EN')"
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
    assert root_group.show_lines_get() == [
        "Group('Root')",
        " Group('Electronics')",
        "  Collection('Digi-Key')",
        "   Directory('Capacitors')",
        "   Directory('Resistors')",
        "    Table('Chip Resistor - Surface Mount')",
        "     Parameter('Manufacturer No.')",
        "      ParameterComment('EN')",
        "      ParameterComment('RU')",
        "     Search('@ALL')",
        "     TableComment('EN')"
        ]

    # Remove a *Node* and verify its removal:
    manufacturer_parameter.remove(manufacturer_parameter_comment_ru)
    assert root_group.show_lines_get() == [
        "Group('Root')",
        " Group('Electronics')",
        "  Collection('Digi-Key')",
        "   Directory('Capacitors')",
        "   Directory('Resistors')",
        "    Table('Chip Resistor - Surface Mount')",
        "     Parameter('Manufacturer No.')",
        "      ParameterComment('EN')",
        "     Search('@ALL')",
        "     TableComment('EN')"
        ], f"{root_group.show_lines_get()}"

    # Create some nested sub-directories and verify:
    connectors_directory: Directory = Directory(bom_manager, "Connectors", digikey_collection_key)
    digikey_collection.directory_insert(connectors_directory)
    rectangular_connectors_sub_directory: Directory = Directory(bom_manager,
                                                                "Rectangular Connectors",
                                                                digikey_collection_key)
    connectors_directory.directory_insert(rectangular_connectors_sub_directory)
    assert root_group.show_lines_get() == [
        "Group('Root')",
        " Group('Electronics')",
        "  Collection('Digi-Key')",
        "   Directory('Capacitors')",
        "   Directory('Resistors')",
        "    Table('Chip Resistor - Surface Mount')",
        "     Parameter('Manufacturer No.')",
        "      ParameterComment('EN')",
        "     Search('@ALL')",
        "     TableComment('EN')",
        "   Directory('Connectors')",
        "    Directory('Rectangular Connectors')"
        ]

    # Perform a recursive data validity test for *group*:
    root_group.attributes_validate_recursively()

    # Test *tree_path_find* method and invoke the various *__str__* methods:
    tree_path: List[Node] = list()
    root_group.tree_path_find(all_search, tree_path)
    desired_path = [
        all_search,
        chip_resistors_table,
        resistors_directory,
        digikey_collection,
        electronics_group,
        root_group]
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

    # Write the current *group* *show_lines_append* output out to a file:
    show_lines_text_path: Path = temporary_directory / "show_lines.txt"
    root_group.show_lines_file_write(show_lines_text_path, "")

    # Now verify that XML writing and parsing works:
    # Step one: fill in *xml_lines1* from *group*:
    xml_lines1: List[str] = list()
    root_group.xml_lines_append(xml_lines1, "")
    xml_lines1.append("")
    xml_lines1_text: str = '\n'.join(xml_lines1)

    # For debugging write out *xml_lines1_text* to a file:
    xml_lines1_file: IO[Any]
    xml_lines1_xml_path: Path = temporary_directory / "xml_lines1.xml"
    with xml_lines1_xml_path.open("w") as xml_lines1_file:
        xml_lines1_file.write(xml_lines1_text)

    # Now parse *xml_lines2_text* into *group2*:
    group_element: Element = ETree.fromstring(xml_lines1_text)
    group2: Group = Group.xml_parse(group_element, bom_manager)

    # Now regenerate the *xml_lines2_text*:
    xml_lines2: List[str] = list()
    group2.xml_lines_append(xml_lines2, "")
    xml_lines2.append("")
    xml_lines2_text: str = "\n".join(xml_lines2)

    # For debugging write out *xml_lines2_text* to a file:
    xml_lines2_file: IO[Any]
    xml_lines2_xml_path: Path = temporary_directory / "xml_lines2.xml"
    with xml_lines2_xml_path.open("w") as xml_lines2_file:
        xml_lines2_file.write(xml_lines2_text)

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

    # Remove *test_collection_root* and the *temporary_directory*:
    remove_recursively(test_collection_root)
    temporary_directory_destroy()


# test_nodes():
def test_nodes():
    """Test out the *Nodes* data structure."""

    # Figure out the *collection_root* and *searches_root* *Path*'s to use:
    test_node_view_file_name: str = __file__
    test_node_view_file_path: Path = Path(test_node_view_file_name)
    tests_directory: Path = test_node_view_file_path.parent
    collection_root: Path = tests_directory / "ROOT"
    searches_root: Path = tests_directory / "searches"
    assert collection_root.is_dir(), f"collection_root='{collection_root}' does not exist"
    assert searches_root.is_dir(), f"searches_root='{searches_root}' does not exist"

    # Create a *bom_manager* and *collection*:
    bom_manager: BomManager = BomManager()
    collection: Collection = Collection(bom_manager,
                                        "Digi-Key", collection_root, searches_root)
    collection_key: int = collection.collection_key

    # Now start filling the *collection* with some directories and tables:
    directory: Directory = Directory(bom_manager, "Directory", collection_key)
    collection.directory_insert(directory)
    table_nodes: Nodes = directory.nodes_get(Table)
    assert table_nodes.size_get() == 0
    table1: Table = Table(bom_manager, "Table1", collection_key)
    directory.table_insert(table1)
    assert table_nodes.size_get() == 1
    table2: Table = Table(bom_manager, "Table2", collection_key)
    directory.table_insert(table2)
    assert table_nodes.size_get() == 2
    table3: Table = Table(bom_manager, "Table3", collection_key)
    directory.table_insert(table3)
    assert table_nodes.size_get() == 3

    # Now fetch some nodes with different sorting keys:
    def name_key(node: Node) -> Any:
        table: Table = Table.from_node(node)
        return table.name

    table1a: Table = Table.from_node(table_nodes.node_fetch(0, name_key))
    assert table1a.name == "Table1"
    table2a: Table = Table.from_node(table_nodes.node_fetch(1, name_key))
    assert table2a.name == "Table2"
    table3a: Table = Table.from_node(table_nodes.node_fetch(2, name_key))
    assert table3a.name == "Table3"

    # Now change the key sort function and verify that a resort occured:
    def last_character_invert_key(node: Node) -> Any:
        table: Table = Table.from_node(node)
        return -int(table.name[-1])

    table3b: Table = Table.from_node(table_nodes.node_fetch(0, last_character_invert_key))
    assert table3b.name == "Table3"
    table2b: Table = Table.from_node(table_nodes.node_fetch(1, last_character_invert_key))
    assert table2b.name == "Table2"
    table1b: Table = Table.from_node(table_nodes.node_fetch(2, last_character_invert_key))
    assert table1b.name == "Table1"

    # Now insert a new *table4* and verify that a resort occured:
    table4: Table = Table(bom_manager, "Table4", collection_key)
    directory.table_insert(table4)
    table4c: Table = Table.from_node(table_nodes.node_fetch(0, last_character_invert_key))
    assert table4c.name == "Table4"

    # Now remove *table1* and verify that a resort occurred:
    directory.table_remove(table4)
    table3c: Table = Table.from_node(table_nodes.node_fetch(0, last_character_invert_key))
    assert table3c.name == "Table3"


# test_packages_scan():
def test_packages_scan():
    """Verify that the packages scan code works."""

    # Figure out the *searches_path* to use:
    test_node_view_file_name: str = __file__
    test_node_view_path: Path = Path(test_node_view_file_name)
    test_node_view_directory: Path = test_node_view_path.parent
    searches_root: Path = test_node_view_directory / "searches"
    assert searches_root.is_dir()

    # Create a *bom_manager* and *group*:
    bom_manager: BomManager = BomManager()
    group: Group = Group(bom_manager, "Root")

    # Invoke the *packages_scan* method and verify that we got a collection:
    group.packages_scan(searches_root)
    collections: List[Collection] = group.collections_get(True)
    assert len(collections) == 0
    sub_groups: List[Group] = group.sub_groups_get(True)
    assert len(sub_groups) == 1
    electronics_group: Group = sub_groups[0]
    assert electronics_group.name == "Electronics"
    sub_groups = electronics_group.sub_groups_get(True)
    assert len(sub_groups) == 0
    collections = electronics_group.collections_get(True)
    assert len(collections) == 1
    digikey_collection: Collection = collections[0]
    assert digikey_collection.name == "Digi-Key"


# test_load_recursively():
@trace(1)
def test_load_recursively():
    test_file_path: Path = Path(__file__)
    test_file_directory: Path = test_file_path.parent

    # Create *bom_manager* and *group* and verify:
    bom_manager: BomManager = BomManager()
    group: Group = Group(bom_manager, "Root")

    # Create *digikey_collection* and verify:
    digikey_root: Path = test_file_directory / "ROOT"
    searches_root: Path = test_file_directory / "searches"
    digikey_collection: Collection = Collection(bom_manager,
                                                "Digi-Key", digikey_root, searches_root)
    group.collection_insert(digikey_collection)

    # Now perform parial *load_recursively* on *digikey_collection*:
    digikey_collection.load_recursively(True)

    # Verify that we get the correct values in *show_lines*:
    show_lines: List[str] = group.show_lines_get()
    show_lines.append("")
    with open("/tmp/partial_load", "w") as show_lines_file:
        show_line: str
        show_lines_text: str = "\n".join([f'        "{show_line}"' for show_line in show_lines])
        show_lines_file.write(show_lines_text)
    assert show_lines == [
        "Group('Root')",
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
    group2: Group = Group(bom_manager, "Root")
    digikey_collection2: Collection = Collection(bom_manager,
                                                 "Digi-Key", digikey_root, searches_root)
    group2.collection_insert(digikey_collection2)
    digikey_collection2.load_recursively(False)

    # Verify that we get the correct values in *show_lines*:
    trace_level_set(1)
    xml_lines: List[str] = list()
    group2.xml_lines_append(xml_lines, "")
    xxx_file: IO[Any]
    with open("/tmp/xxx.txt", "w") as xxx_file:
        xml_line: str
        for xml_line in xml_lines:
            xxx_file.write(f"        '{xml_line}',\n")
    assert xml_lines == [
        '<Group name="Root">',
        ('  <Collection name="Digi-Key" '
         'collection_root="/home/wayne/public_html/projects/bom_manager/tests/ROOT" '
         'searches_root="/home/wayne/public_html/projects/bom_manager/tests/searches">'),
        '    <Directory name="Digi-Key">',
        '      <Directory name="Capacitors">',
        '        <Table name="Accessories">',
        '          <Parameter name="&#65279;Datasheets" index="0" type_name="URL"/>',
        '          <Parameter name="Image" index="1" type_name="Empty"/>',
        '          <Parameter name="Digi-Key Part Number" index="2" type_name="String"/>',
        '          <Parameter name="Manufacturer Part Number" index="3" type_name="String"/>',
        '          <Parameter name="Manufacturer" index="4" type_name="String"/>',
        '          <Parameter name="Description" index="5" type_name="String"/>',
        '          <Parameter name="Quantity Available" index="6" type_name="Integer"/>',
        '          <Parameter name="Factory Stock" index="7" type_name="Integer"/>',
        '          <Parameter name="Unit Price (USD)" index="8" type_name="Float"/>',
        '          <Parameter name="@ qty" index="9" type_name="Integer"/>',
        '          <Parameter name="Minimum Quantity" index="10" type_name="Integer"/>',
        '          <Parameter name="Series" index="11" type_name="Integer"/>',
        '          <Parameter name="Part Status" index="12" type_name="String"/>',
        '          <Parameter name="Accessory Type" index="13" type_name="String"/>',
        '          <Parameter name="For Use With/Related Products" index="14" type_name="String"/>',
        '          <Parameter name="Device Size" index="15" type_name="String"/>',
        '          <Parameter name="Specifications" index="16" type_name="String"/>',
        '        </Table>',
        '        <Table name="Aluminum - Polymer Capacitors">',
        '          <Parameter name="&#65279;Datasheets" index="0" type_name="URL"/>',
        '          <Parameter name="Image" index="1" type_name="URL"/>',
        '          <Parameter name="Digi-Key Part Number" index="2" type_name="String"/>',
        '          <Parameter name="Manufacturer Part Number" index="3" type_name="String"/>',
        '          <Parameter name="Manufacturer" index="4" type_name="String"/>',
        '          <Parameter name="Description" index="5" type_name="String"/>',
        '          <Parameter name="Quantity Available" index="6" type_name="Integer"/>',
        '          <Parameter name="Factory Stock" index="7" type_name="Integer"/>',
        '          <Parameter name="Unit Price (USD)" index="8" type_name="Float"/>',
        '          <Parameter name="@ qty" index="9" type_name="Integer"/>',
        '          <Parameter name="Minimum Quantity" index="10" type_name="Integer"/>',
        '          <Parameter name="Packaging" index="11" type_name="String"/>',
        '          <Parameter name="Series" index="12" type_name="String"/>',
        '          <Parameter name="Part Status" index="13" type_name="String"/>',
        '          <Parameter name="Type" index="14" type_name="String"/>',
        '          <Parameter name="Capacitance" index="15" type_name="String"/>',
        '          <Parameter name="Tolerance" index="16" type_name="String"/>',
        '          <Parameter name="Voltage - Rated" index="17" type_name="IUnits"/>',
        ('          <Parameter name="ESR (Equivalent Series Resistance)" '
         'index="18" type_name="String"/>'),
        '          <Parameter name="Lifetime @ Temp." index="19" type_name="String"/>',
        '          <Parameter name="Operating Temperature" index="20" type_name="Range"/>',
        '          <Parameter name="Ratings" index="21" type_name="Empty"/>',
        '          <Parameter name="Applications" index="22" type_name="String"/>',
        ('          <Parameter name="Ripple Current @ Low Frequency" '
         'index="23" type_name="String"/>'),
        ('          <Parameter name="Ripple Current @ High Frequency"'
         ' index="24" type_name="String"/>'),
        '          <Parameter name="Impedance" index="25" type_name="Empty"/>',
        '          <Parameter name="Lead Spacing" index="26" type_name="Empty"/>',
        '          <Parameter name="Size / Dimension" index="27" type_name="String"/>',
        '          <Parameter name="Height - Seated (Max)" index="28" type_name="String"/>',
        '          <Parameter name="Surface Mount Land Size" index="29" type_name="String"/>',
        '          <Parameter name="Mounting Type" index="30" type_name="String"/>',
        '          <Parameter name="Package / Case" index="31" type_name="List"/>',
        '        </Table>',
        '        <Table name="Aluminum Electrolytic Capacitors">',
        '          <Parameter name="&#65279;Datasheets" index="0" type_name="URL"/>',
        '          <Parameter name="Image" index="1" type_name="URL"/>',
        '          <Parameter name="Digi-Key Part Number" index="2" type_name="String"/>',
        '          <Parameter name="Manufacturer Part Number" index="3" type_name="String"/>',
        '          <Parameter name="Manufacturer" index="4" type_name="String"/>',
        '          <Parameter name="Description" index="5" type_name="String"/>',
        '          <Parameter name="Quantity Available" index="6" type_name="Integer"/>',
        '          <Parameter name="Factory Stock" index="7" type_name="Integer"/>',
        '          <Parameter name="Unit Price (USD)" index="8" type_name="Float"/>',
        '          <Parameter name="@ qty" index="9" type_name="Integer"/>',
        '          <Parameter name="Minimum Quantity" index="10" type_name="Integer"/>',
        '          <Parameter name="Packaging" index="11" type_name="String"/>',
        '          <Parameter name="Series" index="12" type_name="String"/>',
        '          <Parameter name="Part Status" index="13" type_name="String"/>',
        '          <Parameter name="Capacitance" index="14" type_name="String"/>',
        '          <Parameter name="Tolerance" index="15" type_name="String"/>',
        '          <Parameter name="Voltage - Rated" index="16" type_name="IUnits"/>',
        ('          <Parameter name="ESR (Equivalent Series Resistance)" '
         'index="17" type_name="Empty"/>'),
        '          <Parameter name="Lifetime @ Temp." index="18" type_name="String"/>',
        '          <Parameter name="Operating Temperature" index="19" type_name="Range"/>',
        '          <Parameter name="Polarization" index="20" type_name="String"/>',
        '          <Parameter name="Ratings" index="21" type_name="String"/>',
        '          <Parameter name="Applications" index="22" type_name="String"/>',
        ('          <Parameter name="Ripple Current @ Low Frequency" '
         'index="23" type_name="String"/>'),
        ('          <Parameter name="Ripple Current @ High Frequency" '
         'index="24" type_name="String"/>'),
        '          <Parameter name="Impedance" index="25" type_name="Empty"/>',
        '          <Parameter name="Lead Spacing" index="26" type_name="Empty"/>',
        '          <Parameter name="Size / Dimension" index="27" type_name="String"/>',
        '          <Parameter name="Height - Seated (Max)" index="28" type_name="String"/>',
        '          <Parameter name="Surface Mount Land Size" index="29" type_name="String"/>',
        '          <Parameter name="Mounting Type" index="30" type_name="String"/>',
        '          <Parameter name="Package / Case" index="31" type_name="List"/>',
        '        </Table>',
        '        <Table name="Capacitor Networks, Arrays">',
        '          <Parameter name="&#65279;Datasheets" index="0" type_name="URL"/>',
        '          <Parameter name="Image" index="1" type_name="URL"/>',
        '          <Parameter name="Digi-Key Part Number" index="2" type_name="String"/>',
        '          <Parameter name="Manufacturer Part Number" index="3" type_name="String"/>',
        '          <Parameter name="Manufacturer" index="4" type_name="String"/>',
        '          <Parameter name="Description" index="5" type_name="String"/>',
        '          <Parameter name="Quantity Available" index="6" type_name="Integer"/>',
        '          <Parameter name="Factory Stock" index="7" type_name="Integer"/>',
        '          <Parameter name="Unit Price (USD)" index="8" type_name="Float"/>',
        '          <Parameter name="@ qty" index="9" type_name="Integer"/>',
        '          <Parameter name="Minimum Quantity" index="10" type_name="Integer"/>',
        '          <Parameter name="Packaging" index="11" type_name="String"/>',
        '          <Parameter name="Series" index="12" type_name="String"/>',
        '          <Parameter name="Part Status" index="13" type_name="String"/>',
        '          <Parameter name="Capacitance" index="14" type_name="IUnits"/>',
        '          <Parameter name="Tolerance" index="15" type_name="String"/>',
        '          <Parameter name="Voltage - Rated" index="16" type_name="IUnits"/>',
        '          <Parameter name="Dielectric Material" index="17" type_name="String"/>',
        '          <Parameter name="Number of Capacitors" index="18" type_name="Integer"/>',
        '          <Parameter name="Circuit Type" index="19" type_name="String"/>',
        '          <Parameter name="Temperature Coefficient" index="20" type_name="String"/>',
        '          <Parameter name="Ratings" index="21" type_name="Empty"/>',
        '          <Parameter name="Mounting Type" index="22" type_name="String"/>',
        '          <Parameter name="Package / Case" index="23" type_name="String"/>',
        '          <Parameter name="Size / Dimension" index="24" type_name="String"/>',
        '          <Parameter name="Height - Seated (Max)" index="25" type_name="String"/>',
        '        </Table>',
        '        <Table name="Ceramic Capacitors">',
        '          <Parameter name="&#65279;Datasheets" index="0" type_name="URL"/>',
        '          <Parameter name="Image" index="1" type_name="URL"/>',
        '          <Parameter name="Digi-Key Part Number" index="2" type_name="String"/>',
        '          <Parameter name="Manufacturer Part Number" index="3" type_name="String"/>',
        '          <Parameter name="Manufacturer" index="4" type_name="String"/>',
        '          <Parameter name="Description" index="5" type_name="String"/>',
        '          <Parameter name="Quantity Available" index="6" type_name="Integer"/>',
        '          <Parameter name="Factory Stock" index="7" type_name="Integer"/>',
        '          <Parameter name="Unit Price (USD)" index="8" type_name="Float"/>',
        '          <Parameter name="@ qty" index="9" type_name="Integer"/>',
        '          <Parameter name="Minimum Quantity" index="10" type_name="Integer"/>',
        '          <Parameter name="Packaging" index="11" type_name="String"/>',
        '          <Parameter name="Series" index="12" type_name="String"/>',
        '          <Parameter name="Part Status" index="13" type_name="String"/>',
        '          <Parameter name="Capacitance" index="14" type_name="IUnits"/>',
        '          <Parameter name="Tolerance" index="15" type_name="String"/>',
        '          <Parameter name="Voltage - Rated" index="16" type_name="IUnits"/>',
        '          <Parameter name="Temperature Coefficient" index="17" type_name="String"/>',
        '          <Parameter name="Operating Temperature" index="18" type_name="Range"/>',
        '          <Parameter name="Features" index="19" type_name="Empty"/>',
        '          <Parameter name="Ratings" index="20" type_name="Empty"/>',
        '          <Parameter name="Applications" index="21" type_name="String"/>',
        '          <Parameter name="Failure Rate" index="22" type_name="Empty"/>',
        '          <Parameter name="Mounting Type" index="23" type_name="List"/>',
        '          <Parameter name="Package / Case" index="24" type_name="String"/>',
        '          <Parameter name="Size / Dimension" index="25" type_name="String"/>',
        '          <Parameter name="Height - Seated (Max)" index="26" type_name="Empty"/>',
        '          <Parameter name="Thickness (Max)" index="27" type_name="String"/>',
        '          <Parameter name="Lead Spacing" index="28" type_name="Empty"/>',
        '          <Parameter name="Lead Style" index="29" type_name="Empty"/>',
        '          <Search name="@ALL"/>',
        '          <Search name="CAP CER 22UF 6.3V X5R 0603"/>',
        '        </Table>',
        '        <Table name="Electric Double Layer Capacitors (EDLC), Supercapacitors">',
        '          <Parameter name="&#65279;Datasheets" index="0" type_name="URL"/>',
        '          <Parameter name="Image" index="1" type_name="URL"/>',
        '          <Parameter name="Digi-Key Part Number" index="2" type_name="String"/>',
        '          <Parameter name="Manufacturer Part Number" index="3" type_name="String"/>',
        '          <Parameter name="Manufacturer" index="4" type_name="String"/>',
        '          <Parameter name="Description" index="5" type_name="String"/>',
        '          <Parameter name="Quantity Available" index="6" type_name="Integer"/>',
        '          <Parameter name="Factory Stock" index="7" type_name="Integer"/>',
        '          <Parameter name="Unit Price (USD)" index="8" type_name="Float"/>',
        '          <Parameter name="@ qty" index="9" type_name="Integer"/>',
        '          <Parameter name="Minimum Quantity" index="10" type_name="Integer"/>',
        '          <Parameter name="Packaging" index="11" type_name="String"/>',
        '          <Parameter name="Series" index="12" type_name="String"/>',
        '          <Parameter name="Part Status" index="13" type_name="String"/>',
        '          <Parameter name="Capacitance" index="14" type_name="IUnits"/>',
        '          <Parameter name="Tolerance" index="15" type_name="List"/>',
        '          <Parameter name="Voltage - Rated" index="16" type_name="FUnits"/>',
        ('          <Parameter name="ESR (Equivalent Series Resistance)" '
         'index="17" type_name="String"/>'),
        '          <Parameter name="Lifetime @ Temp." index="18" type_name="String"/>',
        '          <Parameter name="Termination" index="19" type_name="String"/>',
        '          <Parameter name="Mounting Type" index="20" type_name="String"/>',
        '          <Parameter name="Package / Case" index="21" type_name="List"/>',
        '          <Parameter name="Lead Spacing" index="22" type_name="String"/>',
        '          <Parameter name="Size / Dimension" index="23" type_name="String"/>',
        '          <Parameter name="Height - Seated (Max)" index="24" type_name="String"/>',
        '          <Parameter name="Operating Temperature" index="25" type_name="Range"/>',
        '        </Table>',
        '        <Table name="Film Capacitors">',
        '          <Parameter name="&#65279;Datasheets" index="0" type_name="URL"/>',
        '          <Parameter name="Image" index="1" type_name="URL"/>',
        '          <Parameter name="Digi-Key Part Number" index="2" type_name="String"/>',
        '          <Parameter name="Manufacturer Part Number" index="3" type_name="String"/>',
        '          <Parameter name="Manufacturer" index="4" type_name="String"/>',
        '          <Parameter name="Description" index="5" type_name="String"/>',
        '          <Parameter name="Quantity Available" index="6" type_name="Integer"/>',
        '          <Parameter name="Factory Stock" index="7" type_name="Integer"/>',
        '          <Parameter name="Unit Price (USD)" index="8" type_name="Float"/>',
        '          <Parameter name="@ qty" index="9" type_name="Integer"/>',
        '          <Parameter name="Minimum Quantity" index="10" type_name="Integer"/>',
        '          <Parameter name="Packaging" index="11" type_name="String"/>',
        '          <Parameter name="Series" index="12" type_name="String"/>',
        '          <Parameter name="Part Status" index="13" type_name="String"/>',
        '          <Parameter name="Capacitance" index="14" type_name="String"/>',
        '          <Parameter name="Tolerance" index="15" type_name="String"/>',
        '          <Parameter name="Voltage Rating - AC" index="16" type_name="IUnits"/>',
        '          <Parameter name="Voltage Rating - DC" index="17" type_name="IUnits"/>',
        '          <Parameter name="Dielectric Material" index="18" type_name="List"/>',
        ('          <Parameter name="ESR (Equivalent Series Resistance)" '
         'index="19" type_name="Empty"/>'),
        '          <Parameter name="Operating Temperature" index="20" type_name="Range"/>',
        '          <Parameter name="Mounting Type" index="21" type_name="String"/>',
        '          <Parameter name="Package / Case" index="22" type_name="String"/>',
        '          <Parameter name="Size / Dimension" index="23" type_name="String"/>',
        '          <Parameter name="Height - Seated (Max)" index="24" type_name="String"/>',
        '          <Parameter name="Termination" index="25" type_name="String"/>',
        '          <Parameter name="Lead Spacing" index="26" type_name="String"/>',
        '          <Parameter name="Applications" index="27" type_name="String"/>',
        '          <Parameter name="Ratings" index="28" type_name="Empty"/>',
        '          <Parameter name="Features" index="29" type_name="Empty"/>',
        '        </Table>',
        '        <Table name="Mica and PTFE Capacitors">',
        '          <Parameter name="&#65279;Datasheets" index="0" type_name="URL"/>',
        '          <Parameter name="Image" index="1" type_name="URL"/>',
        '          <Parameter name="Digi-Key Part Number" index="2" type_name="String"/>',
        '          <Parameter name="Manufacturer Part Number" index="3" type_name="String"/>',
        '          <Parameter name="Manufacturer" index="4" type_name="String"/>',
        '          <Parameter name="Description" index="5" type_name="String"/>',
        '          <Parameter name="Quantity Available" index="6" type_name="Integer"/>',
        '          <Parameter name="Factory Stock" index="7" type_name="Integer"/>',
        '          <Parameter name="Unit Price (USD)" index="8" type_name="Float"/>',
        '          <Parameter name="@ qty" index="9" type_name="Integer"/>',
        '          <Parameter name="Minimum Quantity" index="10" type_name="Integer"/>',
        '          <Parameter name="Packaging" index="11" type_name="String"/>',
        '          <Parameter name="Series" index="12" type_name="String"/>',
        '          <Parameter name="Part Status" index="13" type_name="String"/>',
        '          <Parameter name="Capacitance" index="14" type_name="IUnits"/>',
        '          <Parameter name="Tolerance" index="15" type_name="String"/>',
        '          <Parameter name="Voltage - Rated" index="16" type_name="IUnits"/>',
        '          <Parameter name="Dielectric Material" index="17" type_name="String"/>',
        '          <Parameter name="Operating Temperature" index="18" type_name="Range"/>',
        '          <Parameter name="Mounting Type" index="19" type_name="String"/>',
        '          <Parameter name="Package / Case" index="20" type_name="String"/>',
        '          <Parameter name="Lead Spacing" index="21" type_name="String"/>',
        '          <Parameter name="Features" index="22" type_name="String"/>',
        '          <Parameter name="Size / Dimension" index="23" type_name="String"/>',
        '          <Parameter name="Height - Seated (Max)" index="24" type_name="String"/>',
        '        </Table>',
        '        <Table name="Niobium Oxide Capacitors">',
        '          <Parameter name="&#65279;Datasheets" index="0" type_name="URL"/>',
        '          <Parameter name="Image" index="1" type_name="URL"/>',
        '          <Parameter name="Digi-Key Part Number" index="2" type_name="String"/>',
        '          <Parameter name="Manufacturer Part Number" index="3" type_name="String"/>',
        '          <Parameter name="Manufacturer" index="4" type_name="String"/>',
        '          <Parameter name="Description" index="5" type_name="String"/>',
        '          <Parameter name="Quantity Available" index="6" type_name="Integer"/>',
        '          <Parameter name="Factory Stock" index="7" type_name="Integer"/>',
        '          <Parameter name="Unit Price (USD)" index="8" type_name="Float"/>',
        '          <Parameter name="@ qty" index="9" type_name="Integer"/>',
        '          <Parameter name="Minimum Quantity" index="10" type_name="Integer"/>',
        '          <Parameter name="Packaging" index="11" type_name="String"/>',
        '          <Parameter name="Series" index="12" type_name="String"/>',
        '          <Parameter name="Part Status" index="13" type_name="String"/>',
        '          <Parameter name="Capacitance" index="14" type_name="String"/>',
        '          <Parameter name="Tolerance" index="15" type_name="String"/>',
        '          <Parameter name="Voltage - Rated" index="16" type_name="FUnits"/>',
        ('          <Parameter name="ESR (Equivalent Series Resistance)" '
         'index="17" type_name="String"/>'),
        '          <Parameter name="Current - Leakage" index="18" type_name="String"/>',
        '          <Parameter name="Dissipation Factor" index="19" type_name="String"/>',
        '          <Parameter name="Mounting Type" index="20" type_name="String"/>',
        '          <Parameter name="Package / Case" index="21" type_name="String"/>',
        '          <Parameter name="Manufacturer Size Code" index="22" type_name="String"/>',
        '          <Parameter name="Height - Seated (Max)" index="23" type_name="String"/>',
        '          <Parameter name="Features" index="24" type_name="Empty"/>',
        '          <Parameter name="Operating Temperature" index="25" type_name="Range"/>',
        '          <Parameter name="Supplier Device Package" index="26" type_name="String"/>',
        '          <Parameter name="Size / Dimension" index="27" type_name="String"/>',
        '        </Table>',
        '        <Table name="Silicon Capacitors">',
        '          <Parameter name="&#65279;Datasheets" index="0" type_name="URL"/>',
        '          <Parameter name="Image" index="1" type_name="URL"/>',
        '          <Parameter name="Digi-Key Part Number" index="2" type_name="String"/>',
        '          <Parameter name="Manufacturer Part Number" index="3" type_name="String"/>',
        '          <Parameter name="Manufacturer" index="4" type_name="String"/>',
        '          <Parameter name="Description" index="5" type_name="String"/>',
        '          <Parameter name="Quantity Available" index="6" type_name="Integer"/>',
        '          <Parameter name="Factory Stock" index="7" type_name="Integer"/>',
        '          <Parameter name="Unit Price (USD)" index="8" type_name="String"/>',
        '          <Parameter name="@ qty" index="9" type_name="Integer"/>',
        '          <Parameter name="Minimum Quantity" index="10" type_name="Integer"/>',
        '          <Parameter name="Packaging" index="11" type_name="String"/>',
        '          <Parameter name="Series" index="12" type_name="String"/>',
        '          <Parameter name="Part Status" index="13" type_name="String"/>',
        '          <Parameter name="Capacitance" index="14" type_name="FUnits"/>',
        '          <Parameter name="Tolerance" index="15" type_name="String"/>',
        '          <Parameter name="Voltage - Breakdown" index="16" type_name="IUnits"/>',
        ('          <Parameter name="ESR (Equivalent Series Resistance)" '
         'index="17" type_name="Empty"/>'),
        ('          <Parameter name="ESL (Equivalent Series Inductance)" '
         'index="18" type_name="Empty"/>'),
        '          <Parameter name="Applications" index="19" type_name="Empty"/>',
        '          <Parameter name="Features" index="20" type_name="Empty"/>',
        '          <Parameter name="Operating Temperature" index="21" type_name="Range"/>',
        '          <Parameter name="Package / Case" index="22" type_name="String"/>',
        '          <Parameter name="Height" index="23" type_name="String"/>',
        '          <Parameter name="Size / Dimension" index="24" type_name="String"/>',
        '        </Table>',
        '        <Table name="Tantalum - Polymer Capacitors">',
        '          <Parameter name="&#65279;Datasheets" index="0" type_name="URL"/>',
        '          <Parameter name="Image" index="1" type_name="URL"/>',
        '          <Parameter name="Digi-Key Part Number" index="2" type_name="String"/>',
        '          <Parameter name="Manufacturer Part Number" index="3" type_name="String"/>',
        '          <Parameter name="Manufacturer" index="4" type_name="String"/>',
        '          <Parameter name="Description" index="5" type_name="String"/>',
        '          <Parameter name="Quantity Available" index="6" type_name="Integer"/>',
        '          <Parameter name="Factory Stock" index="7" type_name="Integer"/>',
        '          <Parameter name="Unit Price (USD)" index="8" type_name="Float"/>',
        '          <Parameter name="@ qty" index="9" type_name="Integer"/>',
        '          <Parameter name="Minimum Quantity" index="10" type_name="Integer"/>',
        '          <Parameter name="Packaging" index="11" type_name="String"/>',
        '          <Parameter name="Series" index="12" type_name="String"/>',
        '          <Parameter name="Part Status" index="13" type_name="String"/>',
        '          <Parameter name="Capacitance" index="14" type_name="String"/>',
        '          <Parameter name="Tolerance" index="15" type_name="String"/>',
        '          <Parameter name="Voltage - Rated" index="16" type_name="FUnits"/>',
        '          <Parameter name="Type" index="17" type_name="String"/>',
        ('          <Parameter name="ESR (Equivalent Series Resistance)" '
         'index="18" type_name="String"/>'),
        '          <Parameter name="Operating Temperature" index="19" type_name="Range"/>',
        '          <Parameter name="Lifetime @ Temp." index="20" type_name="String"/>',
        '          <Parameter name="Mounting Type" index="21" type_name="String"/>',
        '          <Parameter name="Package / Case" index="22" type_name="String"/>',
        '          <Parameter name="Size / Dimension" index="23" type_name="String"/>',
        '          <Parameter name="Height - Seated (Max)" index="24" type_name="String"/>',
        '          <Parameter name="Lead Spacing" index="25" type_name="Empty"/>',
        '          <Parameter name="Manufacturer Size Code" index="26" type_name="String"/>',
        '          <Parameter name="Ratings" index="27" type_name="Empty"/>',
        '          <Parameter name="Features" index="28" type_name="String"/>',
        '        </Table>',
        '        <Table name="Tantalum Capacitors">',
        '          <Parameter name="&#65279;Datasheets" index="0" type_name="URL"/>',
        '          <Parameter name="Image" index="1" type_name="URL"/>',
        '          <Parameter name="Digi-Key Part Number" index="2" type_name="String"/>',
        '          <Parameter name="Manufacturer Part Number" index="3" type_name="String"/>',
        '          <Parameter name="Manufacturer" index="4" type_name="String"/>',
        '          <Parameter name="Description" index="5" type_name="String"/>',
        '          <Parameter name="Quantity Available" index="6" type_name="Integer"/>',
        '          <Parameter name="Factory Stock" index="7" type_name="Integer"/>',
        '          <Parameter name="Unit Price (USD)" index="8" type_name="Float"/>',
        '          <Parameter name="@ qty" index="9" type_name="Integer"/>',
        '          <Parameter name="Minimum Quantity" index="10" type_name="Integer"/>',
        '          <Parameter name="Packaging" index="11" type_name="String"/>',
        '          <Parameter name="Series" index="12" type_name="String"/>',
        '          <Parameter name="Part Status" index="13" type_name="String"/>',
        '          <Parameter name="Capacitance" index="14" type_name="String"/>',
        '          <Parameter name="Tolerance" index="15" type_name="String"/>',
        '          <Parameter name="Voltage - Rated" index="16" type_name="IUnits"/>',
        '          <Parameter name="Type" index="17" type_name="String"/>',
        ('          <Parameter name="ESR (Equivalent Series Resistance)" '
         'index="18" type_name="IUnits"/>'),
        '          <Parameter name="Operating Temperature" index="19" type_name="Range"/>',
        '          <Parameter name="Lifetime @ Temp." index="20" type_name="Empty"/>',
        '          <Parameter name="Mounting Type" index="21" type_name="String"/>',
        '          <Parameter name="Package / Case" index="22" type_name="String"/>',
        '          <Parameter name="Size / Dimension" index="23" type_name="String"/>',
        '          <Parameter name="Height - Seated (Max)" index="24" type_name="String"/>',
        '          <Parameter name="Lead Spacing" index="25" type_name="Empty"/>',
        '          <Parameter name="Manufacturer Size Code" index="26" type_name="String"/>',
        '          <Parameter name="Ratings" index="27" type_name="Empty"/>',
        '          <Parameter name="Features" index="28" type_name="String"/>',
        '          <Parameter name="Failure Rate" index="29" type_name="Empty"/>',
        '        </Table>',
        '        <Table name="Thin Film Capacitors">',
        '          <Parameter name="&#65279;Datasheets" index="0" type_name="URL"/>',
        '          <Parameter name="Image" index="1" type_name="URL"/>',
        '          <Parameter name="Digi-Key Part Number" index="2" type_name="String"/>',
        '          <Parameter name="Manufacturer Part Number" index="3" type_name="String"/>',
        '          <Parameter name="Manufacturer" index="4" type_name="String"/>',
        '          <Parameter name="Description" index="5" type_name="String"/>',
        '          <Parameter name="Quantity Available" index="6" type_name="Integer"/>',
        '          <Parameter name="Factory Stock" index="7" type_name="Integer"/>',
        '          <Parameter name="Unit Price (USD)" index="8" type_name="Float"/>',
        '          <Parameter name="@ qty" index="9" type_name="Integer"/>',
        '          <Parameter name="Minimum Quantity" index="10" type_name="Integer"/>',
        '          <Parameter name="Packaging" index="11" type_name="String"/>',
        '          <Parameter name="Series" index="12" type_name="String"/>',
        '          <Parameter name="Part Status" index="13" type_name="String"/>',
        '          <Parameter name="Capacitance" index="14" type_name="FUnits"/>',
        '          <Parameter name="Tolerance" index="15" type_name="String"/>',
        '          <Parameter name="Voltage - Rated" index="16" type_name="IUnits"/>',
        '          <Parameter name="Mounting Type" index="17" type_name="String"/>',
        '          <Parameter name="Package / Case" index="18" type_name="String"/>',
        '          <Parameter name="Operating Temperature" index="19" type_name="Range"/>',
        '          <Parameter name="Features" index="20" type_name="List"/>',
        '          <Parameter name="Size / Dimension" index="21" type_name="String"/>',
        '          <Parameter name="Height - Seated (Max)" index="22" type_name="String"/>',
        '        </Table>',
        '        <Table name="Trimmers, Variable Capacitors">',
        '          <Parameter name="&#65279;Datasheets" index="0" type_name="URL"/>',
        '          <Parameter name="Image" index="1" type_name="URL"/>',
        '          <Parameter name="Digi-Key Part Number" index="2" type_name="String"/>',
        '          <Parameter name="Manufacturer Part Number" index="3" type_name="String"/>',
        '          <Parameter name="Manufacturer" index="4" type_name="String"/>',
        '          <Parameter name="Description" index="5" type_name="String"/>',
        '          <Parameter name="Quantity Available" index="6" type_name="Integer"/>',
        '          <Parameter name="Factory Stock" index="7" type_name="Integer"/>',
        '          <Parameter name="Unit Price (USD)" index="8" type_name="Float"/>',
        '          <Parameter name="@ qty" index="9" type_name="Integer"/>',
        '          <Parameter name="Minimum Quantity" index="10" type_name="Integer"/>',
        '          <Parameter name="Packaging" index="11" type_name="String"/>',
        '          <Parameter name="Series" index="12" type_name="String"/>',
        '          <Parameter name="Part Status" index="13" type_name="String"/>',
        '          <Parameter name="Capacitance Range" index="14" type_name="Range"/>',
        '          <Parameter name="Adjustment Type" index="15" type_name="String"/>',
        '          <Parameter name="Voltage - Rated" index="16" type_name="IUnits"/>',
        '          <Parameter name="Dielectric Material" index="17" type_name="String"/>',
        '          <Parameter name="Q @ Freq" index="18" type_name="String"/>',
        '          <Parameter name="Size / Dimension" index="19" type_name="String"/>',
        '          <Parameter name="Height - Seated (Max)" index="20" type_name="String"/>',
        '          <Parameter name="Operating Temperature" index="21" type_name="Range"/>',
        '          <Parameter name="Mounting Type" index="22" type_name="String"/>',
        '          <Parameter name="Features" index="23" type_name="String"/>',
        '        </Table>',
        '      </Directory>',
        '      <Directory name="Resistors">',
        '        <Table name="Accessories">',
        '          <Parameter name="&#65279;Datasheets" index="0" type_name="URL"/>',
        '          <Parameter name="Image" index="1" type_name="Empty"/>',
        '          <Parameter name="Digi-Key Part Number" index="2" type_name="String"/>',
        '          <Parameter name="Manufacturer Part Number" index="3" type_name="String"/>',
        '          <Parameter name="Manufacturer" index="4" type_name="String"/>',
        '          <Parameter name="Description" index="5" type_name="String"/>',
        '          <Parameter name="Quantity Available" index="6" type_name="Integer"/>',
        '          <Parameter name="Factory Stock" index="7" type_name="Integer"/>',
        '          <Parameter name="Unit Price (USD)" index="8" type_name="Float"/>',
        '          <Parameter name="@ qty" index="9" type_name="Integer"/>',
        '          <Parameter name="Minimum Quantity" index="10" type_name="Integer"/>',
        '          <Parameter name="Series" index="11" type_name="List"/>',
        '          <Parameter name="Part Status" index="12" type_name="String"/>',
        '          <Parameter name="Accessory Type" index="13" type_name="String"/>',
        '          <Parameter name="For Use With/Related Products" index="14" type_name="List"/>',
        '        </Table>',
        '        <Table name="Chassis Mount Resistors">',
        '          <Parameter name="&#65279;Datasheets" index="0" type_name="URL"/>',
        '          <Parameter name="Image" index="1" type_name="URL"/>',
        '          <Parameter name="Digi-Key Part Number" index="2" type_name="String"/>',
        '          <Parameter name="Manufacturer Part Number" index="3" type_name="String"/>',
        '          <Parameter name="Manufacturer" index="4" type_name="String"/>',
        '          <Parameter name="Description" index="5" type_name="String"/>',
        '          <Parameter name="Quantity Available" index="6" type_name="Integer"/>',
        '          <Parameter name="Factory Stock" index="7" type_name="Integer"/>',
        '          <Parameter name="Unit Price (USD)" index="8" type_name="Float"/>',
        '          <Parameter name="@ qty" index="9" type_name="Integer"/>',
        '          <Parameter name="Minimum Quantity" index="10" type_name="Integer"/>',
        '          <Parameter name="Packaging" index="11" type_name="String"/>',
        '          <Parameter name="Series" index="12" type_name="String"/>',
        '          <Parameter name="Part Status" index="13" type_name="String"/>',
        '          <Parameter name="Resistance" index="14" type_name="IUnits"/>',
        '          <Parameter name="Tolerance" index="15" type_name="String"/>',
        '          <Parameter name="Power (Watts)" index="16" type_name="IUnits"/>',
        '          <Parameter name="Composition" index="17" type_name="String"/>',
        '          <Parameter name="Temperature Coefficient" index="18" type_name="String"/>',
        '          <Parameter name="Operating Temperature" index="19" type_name="Range"/>',
        '          <Parameter name="Features" index="20" type_name="Empty"/>',
        '          <Parameter name="Coating, Housing Type" index="21" type_name="String"/>',
        '          <Parameter name="Mounting Feature" index="22" type_name="String"/>',
        '          <Parameter name="Size / Dimension" index="23" type_name="String"/>',
        '          <Parameter name="Height - Seated (Max)" index="24" type_name="String"/>',
        '          <Parameter name="Lead Style" index="25" type_name="String"/>',
        '          <Parameter name="Package / Case" index="26" type_name="List"/>',
        '          <Parameter name="Failure Rate" index="27" type_name="Empty"/>',
        '          <Search name="@ALL"/>',
        '        </Table>',
        '        <Table name="Chip Resistor - Surface Mount">',
        '          <Parameter name="&#65279;Datasheets" index="0" type_name="URL"/>',
        '          <Parameter name="Image" index="1" type_name="URL"/>',
        '          <Parameter name="Digi-Key Part Number" index="2" type_name="String"/>',
        '          <Parameter name="Manufacturer Part Number" index="3" type_name="String"/>',
        '          <Parameter name="Manufacturer" index="4" type_name="String"/>',
        '          <Parameter name="Description" index="5" type_name="String"/>',
        '          <Parameter name="Quantity Available" index="6" type_name="Integer"/>',
        '          <Parameter name="Factory Stock" index="7" type_name="Integer"/>',
        '          <Parameter name="Unit Price (USD)" index="8" type_name="Float"/>',
        '          <Parameter name="@ qty" index="9" type_name="Integer"/>',
        '          <Parameter name="Minimum Quantity" index="10" type_name="Integer"/>',
        '          <Parameter name="Packaging" index="11" type_name="String"/>',
        '          <Parameter name="Series" index="12" type_name="String"/>',
        '          <Parameter name="Part Status" index="13" type_name="String"/>',
        '          <Parameter name="Resistance" index="14" type_name="IUnits"/>',
        '          <Parameter name="Tolerance" index="15" type_name="String"/>',
        '          <Parameter name="Power (Watts)" index="16" type_name="List"/>',
        '          <Parameter name="Composition" index="17" type_name="String"/>',
        '          <Parameter name="Features" index="18" type_name="String"/>',
        '          <Parameter name="Temperature Coefficient" index="19" type_name="String"/>',
        '          <Parameter name="Operating Temperature" index="20" type_name="Range"/>',
        '          <Parameter name="Package / Case" index="21" type_name="String"/>',
        '          <Parameter name="Supplier Device Package" index="22" type_name="Integer"/>',
        '          <Parameter name="Size / Dimension" index="23" type_name="String"/>',
        '          <Parameter name="Height - Seated (Max)" index="24" type_name="String"/>',
        '          <Parameter name="Number of Terminations" index="25" type_name="Integer"/>',
        '          <Parameter name="Failure Rate" index="26" type_name="Empty"/>',
        '        </Table>',
        '        <Table name="Resistor Networks, Arrays">',
        '          <Parameter name="&#65279;Datasheets" index="0" type_name="URL"/>',
        '          <Parameter name="Image" index="1" type_name="URL"/>',
        '          <Parameter name="Digi-Key Part Number" index="2" type_name="String"/>',
        '          <Parameter name="Manufacturer Part Number" index="3" type_name="String"/>',
        '          <Parameter name="Manufacturer" index="4" type_name="String"/>',
        '          <Parameter name="Description" index="5" type_name="String"/>',
        '          <Parameter name="Quantity Available" index="6" type_name="Integer"/>',
        '          <Parameter name="Factory Stock" index="7" type_name="Integer"/>',
        '          <Parameter name="Unit Price (USD)" index="8" type_name="Float"/>',
        '          <Parameter name="@ qty" index="9" type_name="Integer"/>',
        '          <Parameter name="Minimum Quantity" index="10" type_name="Integer"/>',
        '          <Parameter name="Packaging" index="11" type_name="String"/>',
        '          <Parameter name="Series" index="12" type_name="String"/>',
        '          <Parameter name="Part Status" index="13" type_name="String"/>',
        '          <Parameter name="Circuit Type" index="14" type_name="String"/>',
        '          <Parameter name="Resistance (Ohms)" index="15" type_name="IUnits"/>',
        '          <Parameter name="Tolerance" index="16" type_name="String"/>',
        '          <Parameter name="Number of Resistors" index="17" type_name="Integer"/>',
        '          <Parameter name="Resistor Matching Ratio" index="18" type_name="Empty"/>',
        '          <Parameter name="Resistor-Ratio-Drift" index="19" type_name="Empty"/>',
        '          <Parameter name="Number of Pins" index="20" type_name="Integer"/>',
        '          <Parameter name="Power Per Element" index="21" type_name="String"/>',
        '          <Parameter name="Temperature Coefficient" index="22" type_name="String"/>',
        '          <Parameter name="Operating Temperature" index="23" type_name="Range"/>',
        '          <Parameter name="Applications" index="24" type_name="Empty"/>',
        '          <Parameter name="Mounting Type" index="25" type_name="String"/>',
        '          <Parameter name="Package / Case" index="26" type_name="List"/>',
        '          <Parameter name="Supplier Device Package" index="27" type_name="Integer"/>',
        '          <Parameter name="Size / Dimension" index="28" type_name="String"/>',
        '          <Parameter name="Height - Seated (Max)" index="29" type_name="String"/>',
        '          <Search name="@ALL"/>',
        '        </Table>',
        '        <Table name="Specialized Resistors">',
        '          <Parameter name="&#65279;Datasheets" index="0" type_name="URL"/>',
        '          <Parameter name="Image" index="1" type_name="URL"/>',
        '          <Parameter name="Digi-Key Part Number" index="2" type_name="String"/>',
        '          <Parameter name="Manufacturer Part Number" index="3" type_name="String"/>',
        '          <Parameter name="Manufacturer" index="4" type_name="String"/>',
        '          <Parameter name="Description" index="5" type_name="String"/>',
        '          <Parameter name="Quantity Available" index="6" type_name="Integer"/>',
        '          <Parameter name="Factory Stock" index="7" type_name="Integer"/>',
        '          <Parameter name="Unit Price (USD)" index="8" type_name="String"/>',
        '          <Parameter name="@ qty" index="9" type_name="Integer"/>',
        '          <Parameter name="Minimum Quantity" index="10" type_name="Integer"/>',
        '          <Parameter name="Packaging" index="11" type_name="String"/>',
        '          <Parameter name="Series" index="12" type_name="String"/>',
        '          <Parameter name="Part Status" index="13" type_name="String"/>',
        '          <Parameter name="Type" index="14" type_name="String"/>',
        '          <Parameter name="Applications" index="15" type_name="String"/>',
        '          <Parameter name="Composition" index="16" type_name="String"/>',
        '          <Parameter name="Resistance" index="17" type_name="IUnits"/>',
        '          <Parameter name="Tolerance" index="18" type_name="String"/>',
        '          <Parameter name="Power (Watts)" index="19" type_name="List"/>',
        '          <Parameter name="Temperature Coefficient" index="20" type_name="String"/>',
        '          <Parameter name="Operating Temperature" index="21" type_name="Range"/>',
        '          <Parameter name="Mounting Type" index="22" type_name="String"/>',
        '        </Table>',
        '        <Table name="Through Hole Resistors">',
        '          <Parameter name="&#65279;Datasheets" index="0" type_name="URL"/>',
        '          <Parameter name="Image" index="1" type_name="URL"/>',
        '          <Parameter name="Digi-Key Part Number" index="2" type_name="String"/>',
        '          <Parameter name="Manufacturer Part Number" index="3" type_name="String"/>',
        '          <Parameter name="Manufacturer" index="4" type_name="String"/>',
        '          <Parameter name="Description" index="5" type_name="String"/>',
        '          <Parameter name="Quantity Available" index="6" type_name="Integer"/>',
        '          <Parameter name="Factory Stock" index="7" type_name="Integer"/>',
        '          <Parameter name="Unit Price (USD)" index="8" type_name="Float"/>',
        '          <Parameter name="@ qty" index="9" type_name="Integer"/>',
        '          <Parameter name="Minimum Quantity" index="10" type_name="Integer"/>',
        '          <Parameter name="Packaging" index="11" type_name="String"/>',
        '          <Parameter name="Series" index="12" type_name="String"/>',
        '          <Parameter name="Part Status" index="13" type_name="String"/>',
        '          <Parameter name="Resistance" index="14" type_name="IUnits"/>',
        '          <Parameter name="Tolerance" index="15" type_name="String"/>',
        '          <Parameter name="Power (Watts)" index="16" type_name="List"/>',
        '          <Parameter name="Composition" index="17" type_name="String"/>',
        '          <Parameter name="Features" index="18" type_name="List"/>',
        '          <Parameter name="Temperature Coefficient" index="19" type_name="String"/>',
        '          <Parameter name="Operating Temperature" index="20" type_name="Range"/>',
        '          <Parameter name="Package / Case" index="21" type_name="String"/>',
        '          <Parameter name="Supplier Device Package" index="22" type_name="String"/>',
        '          <Parameter name="Size / Dimension" index="23" type_name="String"/>',
        '          <Parameter name="Height - Seated (Max)" index="24" type_name="Empty"/>',
        '          <Parameter name="Number of Terminations" index="25" type_name="Integer"/>',
        '          <Parameter name="Failure Rate" index="26" type_name="Empty"/>',
        '        </Table>',
        '      </Directory>',
        '    </Directory>',
        '  </Collection>',
        '</Group>',
    ]


if __name__ == "__main__":
    trace_level_set(1)
    # test_file_name_converter()
    # test_load_recursively()
    test_packages_scan()
