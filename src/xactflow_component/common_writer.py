from __future__ import annotations

from typing import Callable, Iterable, Mapping, Optional, Sequence, TypeVar

from lxml import etree

from ipxact.schema.common import (
    AccessHandle,
    ArrayBound,
    Assertion,
    BuildCommand,
    Choice,
    DefinitionRef,
    Define,
    Expression,
    FieldReference,
    File,
    FileBuilder,
    FileSet,
    FileSetRefGroup,
    FileType,
    Function,
    FunctionArgument,
    IndexedRef,
    LocalReference,
    Location,
    MemoryArray,
    ModeRef,
    ModuleParameter,
    Parameter,
    PartSelect,
    Range,
    Slice,
    SourceFile,
    SubPortReference,
    TextValue,
    Vector,
)
from ipxact.schema.ports import (
    CellSpecification,
    DriveConstraint,
    LevelFlag,
    LoadConstraint,
    Payload,
    Protocol,
    Qualifier,
    TimingConstraint,
)
from ipxact.schema.vlnv import VLNVRef

NAMESPACE = "http://www.accellera.org/XMLSchema/IPXACT/1685-2022"
XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"
SCHEMA_LOCATION = f"{NAMESPACE} {NAMESPACE}/index.xsd"
XML_ID = "{http://www.w3.org/XML/1998/namespace}id"
_NSMAP = {"ipxact": NAMESPACE}

T = TypeVar("T")


def qn(tag: str) -> str:
    """Build a namespace-qualified IP-XACT tag, e.g. qn("component") -> "{ns}component"."""
    return f"{{{NAMESPACE}}}{tag}"


def element(tag: str, text: object = None, /, xml_id: Optional[str] = None, **attrs: object) -> etree._Element:
    """Create an ipxact-namespaced element; attributes whose value is None are dropped.

    tag and text are positional-only so that **attrs stays free for XML attributes that
    happen to be named "text", "help" or "tag" (ipxact:enumeration has two of them).
    """
    elem = etree.Element(qn(tag), nsmap=_NSMAP)
    if xml_id is not None:
        elem.set(XML_ID, xml_id)
    for name, value in attrs.items():
        if value is not None:
            elem.set(name, str(value))
    if text is not None:
        elem.text = str(text)
    return elem


def sub(
    parent: etree._Element, tag: str, text: object = None, /, xml_id: Optional[str] = None, **attrs: object
) -> etree._Element:
    child = element(tag, text, xml_id=xml_id, **attrs)
    parent.append(child)
    return child


def set_other_attributes(elem: etree._Element, attributes: Mapping[str, str]) -> None:
    """Write attributes from other namespaces (the schema's any.att), keyed by {namespace}name."""
    for name, value in attributes.items():
        elem.set(name, value)


def add_text(parent: etree._Element, tag: str, value: object, **attrs: object) -> None:
    """Append a simple text child, or nothing when the value is unset."""
    if value is not None:
        sub(parent, tag, value, **attrs)


def add_expression(
    parent: etree._Element, tag: str, expression: Optional[Expression], /, **attrs: object
) -> Optional[etree._Element]:
    """Append an expression element with its bounds, xml:id and foreign attributes, or nothing when unset."""
    if expression is None:
        return None
    elem = sub(
        parent,
        tag,
        expression.value,
        xml_id=expression.xml_id,
        minimum=expression.minimum,
        maximum=expression.maximum,
        **attrs,
    )
    set_other_attributes(elem, expression.other_attributes)
    return elem


def add_expressions(parent: etree._Element, tag: str, expressions: Iterable[Expression]) -> None:
    for expression in expressions:
        add_expression(parent, tag, expression)


def add_text_value(parent: etree._Element, tag: str, value: Optional[TextValue], **attrs: object) -> None:
    if value is not None:
        sub(parent, tag, value.value, xml_id=value.xml_id, **attrs)


def add_text_values(parent: etree._Element, tag: str, values: Iterable[TextValue]) -> None:
    for value in values:
        add_text_value(parent, tag, value)


def bool_str(value: bool) -> str:
    return "true" if value else "false"


def add_bool(parent: etree._Element, tag: str, value: Optional[bool], **attrs: object) -> None:
    if value is not None:
        sub(parent, tag, bool_str(value), **attrs)


def add_items(parent: etree._Element, container_tag: str, items: Sequence[T], writer: Callable[[T], etree._Element]) -> None:
    """Write container_tag holding one writer(item) per item, or nothing when items is empty.

    Mirrors ipxact.parser.common_parser.parse_children, the same shape in reverse.
    """
    if not items:
        return
    container = sub(parent, container_tag)
    for item in items:
        container.append(writer(item))


def check_choice(what: str, *arms: dict) -> None:
    """Raise ValueError when more than one arm of an XSD choice is set.

    Each arm maps the fields it is made of to their values; a field is set when it is not None
    or an empty list. Only one arm can be written, so the others would be silently dropped.
    """
    set_arms = [[name for name, value in arm.items() if value is not None and value != []] for arm in arms]
    set_arms = [", ".join(names) for names in set_arms if names]
    if len(set_arms) > 1:
        raise ValueError(f"{what} sets {' and '.join(set_arms)}, but the schema allows only one of them")


def add_name_group(parent: etree._Element, item: object) -> None:
    """Write ipxact:nameGroup (name, displayName, shortDescription, description) from item.

    Nearly every IP-XACT type opens with this group, but the matching ipxact-compiler
    dataclasses declare display_name/description as trailing optional fields. Element order
    therefore cannot be read off dataclass field order anywhere in this package; it comes
    from the XSD.
    """
    add_text(parent, "name", item.name)
    add_text(parent, "displayName", item.display_name)
    add_text(parent, "shortDescription", item.short_description)
    add_text(parent, "description", item.description)


def write_vendor_extensions(parent: etree._Element, extensions: Sequence[str]) -> None:
    """Re-insert opaque vendor extension fragments verbatim.

    Vendor extension content is not IP-XACT's to define, so it is kept byte-identical rather
    than re-derived. Giving every element that has children an empty text node switches
    libxml2's pretty printer off for the whole fragment, so serializing does not inject
    indentation into somebody else's markup.
    """
    if not extensions:
        return
    container = sub(parent, "vendorExtensions")
    _add_raw_fragments(container, extensions)


def _add_raw_fragments(parent: etree._Element, fragments: Sequence[str]) -> None:
    for fragment in fragments:
        # A fragment may be a processing instruction or a comment, which fromstring() rejects
        # without a root element, so it is parsed inside a wrapper and its nodes moved out.
        wrapper = etree.fromstring(b"<w>" + fragment.encode("utf-8") + b"</w>")
        parent.extend(list(wrapper))
    for node in parent.iter():
        if len(node) and node.text is None:
            node.text = ""


def add_raw_content(parent: etree._Element, fragments: Sequence[str]) -> None:
    """Append opaque XML fragments (e.g. a mirroredInitiator's any content) as children of parent."""
    if fragments:
        _add_raw_fragments(parent, fragments)


def add_vlnv(parent: etree._Element, vlnv: object) -> None:
    """Write ipxact:versionedIdentifier (vendor/library/name/version as child elements)."""
    sub(parent, "vendor", vlnv.vendor)
    sub(parent, "library", vlnv.library)
    sub(parent, "name", vlnv.name)
    sub(parent, "version", vlnv.version)


def write_vlnv_ref(tag: str, ref: VLNVRef) -> etree._Element:
    """Write a configurableLibraryRefType element (VLNV as attributes)."""
    elem = element(
        tag, xml_id=ref.xml_id, vendor=ref.vendor, library=ref.library, name=ref.name, version=ref.version
    )
    if ref.config_element_values:
        values = sub(elem, "configurableElementValues")
        for reference_id, value in ref.config_element_values.items():
            add_expression(values, "configurableElementValue", value, referenceId=reference_id)
    return elem


def add_range(parent: etree._Element, range_: Optional[Range]) -> None:
    if range_ is None:
        return
    range_elem = sub(parent, "range")
    add_expression(range_elem, "left", range_.left)
    add_expression(range_elem, "right", range_.right)


def add_vectors(parent: etree._Element, vectors: Sequence[Vector], with_ids: bool = True) -> None:
    if not vectors:
        return
    container = sub(parent, "vectors")
    for vector in vectors:
        vector_elem = sub(container, "vector", xml_id=vector.xml_id, vectorId=vector.vector_id if with_ids else None)
        add_expression(vector_elem, "left", vector.left)
        add_expression(vector_elem, "right", vector.right)


def add_array_bounds(parent: etree._Element, arrays: Sequence[ArrayBound], with_ids: bool = True) -> None:
    if not arrays:
        return
    container = sub(parent, "arrays")
    for array in arrays:
        array_elem = sub(container, "array", xml_id=array.xml_id, arrayId=array.array_id if with_ids else None)
        add_expression(array_elem, "left", array.left)
        add_expression(array_elem, "right", array.right)


def add_memory_array(parent: etree._Element, array: Optional[MemoryArray], stride_tag: str = "stride") -> None:
    """Write ipxact:array. Blocks, register files and registers use ipxact:stride, fields use ipxact:bitStride."""
    if array is None:
        return
    elem = sub(parent, "array")
    for dim in array.dims:
        add_expression(elem, "dim", dim.size, indexVar=dim.index_var)
    add_expression(elem, stride_tag, array.stride)


def add_mode_refs(parent: etree._Element, mode_refs: Sequence[ModeRef]) -> None:
    """Write ipxact:modeRef elements.

    priority is None on the modeRefs that have no priority attribute (an initiator's
    addressSpaceRef, a target's memoryMapRef), so it is simply left out there.
    """
    for mode_ref in mode_refs:
        sub(parent, "modeRef", mode_ref.name, xml_id=mode_ref.xml_id, priority=mode_ref.priority)


def add_indices(parent: etree._Element, indices: Sequence[Expression]) -> None:
    if not indices:
        return
    container = sub(parent, "indices")
    add_expressions(container, "index", indices)


def add_part_select(parent: etree._Element, part_select: Optional[PartSelect]) -> None:
    if part_select is None:
        return
    elem = sub(parent, "partSelect", xml_id=part_select.xml_id)
    add_indices(elem, part_select.indices)
    add_range(elem, part_select.range)


def add_sub_port_references(parent: etree._Element, refs: Sequence[SubPortReference]) -> None:
    for ref in refs:
        elem = sub(parent, "subPortReference", xml_id=ref.xml_id, subPortRef=ref.sub_port_ref)
        add_part_select(elem, ref.part_select)


def _add_indexed_ref(parent: etree._Element, tag: str, ref: Optional[IndexedRef]) -> None:
    """addressBlockRef/bankRef/registerFileRef/registerRef/fieldRef: the name sits in an attribute named like the tag."""
    if ref is None:
        return
    elem = sub(parent, tag, xml_id=ref.xml_id, **{tag: ref.name})
    add_indices(elem, ref.indices)


def add_field_reference_group(parent: etree._Element, reference: FieldReference, with_range: bool = False) -> None:
    """Write fieldReferenceGroup / fieldSliceReferenceGroup content directly into parent."""
    check_choice(
        "a field reference",
        {"address_space_ref": reference.address_space_ref},
        {"memory_map_ref": reference.memory_map_ref, "memory_remap_ref": reference.memory_remap_ref},
    )
    if reference.address_space_ref is not None:
        sub(parent, "addressSpaceRef", addressSpaceRef=reference.address_space_ref)
    elif reference.memory_map_ref is not None:
        sub(parent, "memoryMapRef", memoryMapRef=reference.memory_map_ref)
        if reference.memory_remap_ref is not None:
            sub(parent, "memoryRemapRef", memoryRemapRef=reference.memory_remap_ref)
    elif with_range:
        raise ValueError("a field slice reference requires address_space_ref or memory_map_ref")
    for bank_ref in reference.bank_refs:
        _add_indexed_ref(parent, "bankRef", bank_ref)
    if reference.address_block_ref is None and with_range:
        raise ValueError("a field slice reference requires address_block_ref")
    _add_indexed_ref(parent, "addressBlockRef", reference.address_block_ref)
    for register_file_ref in reference.register_file_refs:
        _add_indexed_ref(parent, "registerFileRef", register_file_ref)
    if reference.register_ref is None and with_range:
        raise ValueError("a field slice reference requires register_ref")
    _add_indexed_ref(parent, "registerRef", reference.register_ref)
    if reference.alternate_register_ref is not None:
        sub(parent, "alternateRegisterRef", alternateRegisterRef=reference.alternate_register_ref)
    _add_indexed_ref(parent, "fieldRef", reference.field_ref)
    if with_range:
        add_range(parent, reference.range)


def add_definition_ref(parent: etree._Element, tag: str, ref: Optional[DefinitionRef]) -> None:
    """Write a *DefinitionRef element: the definition's name, and the externalTypeDefinitions it lives in."""
    if ref is not None:
        sub(parent, tag, ref.name, typeDefinitions=ref.type_definitions)


def _add_slice(parent: etree._Element, slice_: Slice) -> None:
    elem = sub(parent, "slice", xml_id=slice_.xml_id)
    if slice_.path_segments:
        add_expressions(sub(elem, "pathSegments"), "pathSegment", slice_.path_segments)
    add_range(elem, slice_.range)


def add_location(parent: etree._Element, location: Location) -> None:
    elem = sub(parent, "location", xml_id=location.xml_id)
    for slice_ in location.slices:
        _add_slice(elem, slice_)


def _write_access_handle(handle: AccessHandle, with_force: bool) -> etree._Element:
    # The three schema flavors share this dataclass: a simpleAccessHandle only has
    # pathSegments, a sliced or port access handle has slices (and a port one indices).
    # Only the last two declare the force attribute.
    elem = element(
        "accessHandle",
        xml_id=handle.xml_id,
        force=bool_str(False) if with_force and not handle.force else None,
    )
    add_text_values(elem, "viewRef", handle.view_refs)
    if handle.path_segments:
        add_expressions(sub(elem, "pathSegments"), "pathSegment", handle.path_segments)
    add_indices(elem, handle.indices)
    if handle.slices:
        slices = sub(elem, "slices", xml_id=handle.slices_xml_id)
        for slice_ in handle.slices:
            _add_slice(slices, slice_)
    write_vendor_extensions(elem, handle.vendor_extensions)
    return elem


def add_access_handles(parent: etree._Element, handles: Sequence[AccessHandle], with_force: bool = True) -> None:
    add_items(parent, "accessHandles", handles, lambda handle: _write_access_handle(handle, with_force))


def _add_parameter_body(parent: etree._Element, parameter: Parameter, with_ids: bool) -> None:
    # A plain parameter's vectors/arrays carry no vectorId/arrayId: only moduleParameterType
    # declares those attributes, so they are dropped rather than written out invalidly.
    add_name_group(parent, parameter)
    add_vectors(parent, parameter.vectors, with_ids=with_ids)
    add_array_bounds(parent, parameter.arrays, with_ids=with_ids)
    add_expression(parent, "value", parameter.value)
    write_vendor_extensions(parent, parameter.vendor_extensions)


def _parameter_attributes(parameter: Parameter) -> dict:
    return {
        "xml_id": parameter.xml_id,
        "parameterId": parameter.parameter_id,
        "prompt": parameter.prompt,
        "choiceRef": parameter.choice_ref,
        "order": parameter.order,
        "configGroups": " ".join(parameter.config_groups) if parameter.config_groups else None,
        "minimum": parameter.minimum,
        "maximum": parameter.maximum,
        "type": parameter.type if parameter.type != "string" else None,
        "sign": parameter.sign,
        "prefix": parameter.prefix,
        "unit": parameter.unit,
        "resolve": parameter.resolve if parameter.resolve != "immediate" else None,
    }


def write_parameter(parameter: Parameter) -> etree._Element:
    elem = element("parameter", None, **_parameter_attributes(parameter))
    set_other_attributes(elem, parameter.other_attributes)
    _add_parameter_body(elem, parameter, with_ids=False)
    return elem


def write_module_parameter(parameter: ModuleParameter, tag: str = "moduleParameter") -> etree._Element:
    attrs = _parameter_attributes(parameter)
    attrs.update(
        dataType=parameter.data_type,
        usageType=parameter.usage_type if parameter.usage_type != "typed" else None,
        dataTypeDefinition=parameter.data_type_definition,
        constrained=" ".join(parameter.constrained) if parameter.constrained else None,
    )
    elem = element(tag, None, **attrs)
    set_other_attributes(elem, parameter.other_attributes)
    _add_parameter_body(elem, parameter, with_ids=True)
    return elem


def add_parameters(parent: etree._Element, parameters: Sequence[Parameter]) -> None:
    add_items(parent, "parameters", parameters, write_parameter)


def add_module_parameters(parent: etree._Element, parameters: Sequence[ModuleParameter]) -> None:
    add_items(parent, "moduleParameters", parameters, write_module_parameter)


def add_choices(parent: etree._Element, choices: Sequence[Choice]) -> None:
    if not choices:
        return
    container = sub(parent, "choices")
    for choice in choices:
        choice_elem = sub(container, "choice", xml_id=choice.xml_id)
        sub(choice_elem, "name", choice.name)
        for enumeration in choice.enumerations:
            add_expression(choice_elem, "enumeration", enumeration.value, text=enumeration.text, help=enumeration.help)


def add_assertions(parent: etree._Element, assertions: Sequence[Assertion]) -> None:
    if not assertions:
        return
    container = sub(parent, "assertions")
    for assertion in assertions:
        assertion_elem = sub(container, "assertion", xml_id=assertion.xml_id)
        add_name_group(assertion_elem, assertion)
        add_expression(assertion_elem, "assert", assertion.assert_expression)


def add_file_type(parent: etree._Element, file_type: FileType) -> None:
    sub(parent, "fileType", file_type.value, xml_id=file_type.xml_id, user=file_type.user, libext=file_type.libext)


def add_file_builder(parent: etree._Element, builder: FileBuilder, tag: str = "defaultFileBuilder") -> None:
    """Write fileBuilderType: ipxact:defaultFileBuilder, or a languageTools ipxact:fileBuilder."""
    elem = sub(parent, tag, xml_id=builder.xml_id)
    add_file_type(elem, builder.file_type)
    add_expression(elem, "command", builder.command)
    add_expression(elem, "flags", builder.flags)
    add_expression(elem, "replaceDefaultFlags", builder.replace_default_flags)
    write_vendor_extensions(elem, builder.vendor_extensions)


def _add_build_command(parent: etree._Element, build_command: Optional[BuildCommand]) -> None:
    if build_command is None:
        return
    elem = sub(parent, "buildCommand")
    add_expression(elem, "command", build_command.command)
    add_expression(
        elem,
        "flags",
        build_command.flags,
        append=bool_str(build_command.flags_append) if build_command.flags_append is not None else None,
    )
    add_expression(elem, "replaceDefaultFlags", build_command.replace_default_flags)
    add_text(elem, "targetName", build_command.target_name)


def _add_define(parent: etree._Element, define: Define) -> None:
    elem = sub(parent, "define", xml_id=define.xml_id)
    add_name_group(elem, define)
    add_expression(elem, "value", define.value)
    write_vendor_extensions(elem, define.vendor_extensions)


def _add_file(parent: etree._Element, file: File) -> None:
    elem = sub(parent, "file", xml_id=file.xml_id, fileId=file.file_id)
    set_other_attributes(elem, file.other_attributes)
    sub(elem, "name", file.name)
    for file_type in file.file_types:
        add_file_type(elem, file_type)
    if file.is_structural:
        sub(elem, "isStructural", bool_str(True))
    if file.is_include_file or file.include_has_external_declarations:
        sub(
            elem,
            "isIncludeFile",
            bool_str(file.is_include_file),
            externalDeclarations=bool_str(True) if file.include_has_external_declarations else None,
        )
    add_text(elem, "logicalName", file.logical_name, default=bool_str(True) if file.logical_name_default else None)
    add_text_values(elem, "exportedName", file.exported_names)
    _add_build_command(elem, file.build_command)
    add_text_values(elem, "dependency", file.dependencies)
    for define in file.defines:
        _add_define(elem, define)
    add_text_values(elem, "imageType", file.image_types)
    # Unlike every other element, a file's description is not part of a nameGroup: it comes last.
    add_text(elem, "description", file.description)
    write_vendor_extensions(elem, file.vendor_extensions)


def _add_function_argument(parent: etree._Element, argument: FunctionArgument) -> None:
    elem = sub(parent, "argument", xml_id=argument.xml_id, dataType=argument.data_type)
    add_name_group(elem, argument)
    add_expression(elem, "value", argument.value)
    write_vendor_extensions(elem, argument.vendor_extensions)


def _add_source_file(parent: etree._Element, source_file: SourceFile) -> None:
    elem = sub(parent, "sourceFile", xml_id=source_file.xml_id)
    sub(elem, "sourceName", source_file.source_name)
    add_file_type(elem, source_file.file_type)


def _add_function(parent: etree._Element, function: Function) -> None:
    elem = sub(parent, "function", xml_id=function.xml_id, replicate=bool_str(True) if function.replicate else None)
    add_text(elem, "entryPoint", function.entry_point)
    sub(elem, "fileRef", function.file_ref)
    add_text(elem, "returnType", function.return_type)
    for argument in function.arguments:
        _add_function_argument(elem, argument)
    add_expression(elem, "disabled", function.disabled)
    for source_file in function.source_files:
        _add_source_file(elem, source_file)


def write_file_set(file_set: FileSet) -> etree._Element:
    elem = element("fileSet", xml_id=file_set.xml_id)
    add_name_group(elem, file_set)
    add_text_values(elem, "group", file_set.groups)
    for file in file_set.files:
        _add_file(elem, file)
    for builder in file_set.default_file_builders:
        add_file_builder(elem, builder)
    add_text_values(elem, "dependency", file_set.dependencies)
    for function in file_set.functions:
        _add_function(elem, function)
    write_vendor_extensions(elem, file_set.vendor_extensions)
    return elem


def add_file_sets(parent: etree._Element, file_sets: Sequence[FileSet]) -> None:
    add_items(parent, "fileSets", file_sets, write_file_set)


def add_local_references(parent: etree._Element, tag: str, refs: Sequence[LocalReference]) -> None:
    """Write fileSetRef / constraintSetRef / busInterfaceRef elements around a localName."""
    for ref in refs:
        ref_elem = sub(parent, tag, xml_id=ref.xml_id)
        sub(ref_elem, "localName", ref.local_name)
        write_vendor_extensions(ref_elem, ref.vendor_extensions)


def add_file_set_ref_group(parent: etree._Element, group: Optional[FileSetRefGroup]) -> None:
    if group is None:
        return
    elem = sub(parent, "fileSetRefGroup", xml_id=group.xml_id)
    add_text(elem, "group", group.group)
    add_local_references(elem, "fileSetRef", group.file_set_refs)


def _add_level_flag(parent: etree._Element, tag: str, flag: Optional[LevelFlag], with_power_domain: bool) -> None:
    if flag is None:
        return
    sub(
        parent,
        tag,
        bool_str(flag.value),
        level=flag.level,
        powerDomainRef=flag.power_domain_ref if with_power_domain else None,
    )


def add_qualifier(parent: etree._Element, qualifier: Optional[Qualifier]) -> None:
    if qualifier is None:
        return
    elem = sub(parent, "qualifier", xml_id=qualifier.xml_id)
    add_bool(elem, "isAddress", qualifier.is_address)
    add_bool(elem, "isData", qualifier.is_data)
    add_bool(elem, "isClock", qualifier.is_clock)
    _add_level_flag(elem, "isReset", qualifier.is_reset, with_power_domain=False)
    add_bool(elem, "isValid", qualifier.is_valid)
    add_bool(elem, "isInterrupt", qualifier.is_interrupt)
    _add_level_flag(elem, "isClockEn", qualifier.is_clock_en, with_power_domain=True)
    _add_level_flag(elem, "isPowerEn", qualifier.is_power_en, with_power_domain=True)
    add_bool(elem, "isOpcode", qualifier.is_opcode)
    add_bool(elem, "isProtection", qualifier.is_protection)
    if qualifier.is_flow_control is not None:
        sub(
            elem,
            "isFlowControl",
            bool_str(qualifier.is_flow_control.value),
            flowType=qualifier.is_flow_control.flow_type,
            user=qualifier.is_flow_control.user,
        )
    if qualifier.is_user is not None:
        sub(elem, "isUser", bool_str(qualifier.is_user.value), user=qualifier.is_user.user)
    add_bool(elem, "isRequest", qualifier.is_request)
    add_bool(elem, "isResponse", qualifier.is_response)


def _add_cell_specification(parent: etree._Element, cell: CellSpecification) -> None:
    elem = sub(parent, "cellSpecification", cellStrength=cell.cell_strength)
    # cellSpecification is a required choice: exactly one of cellFunction or cellClass.
    check_choice(
        "a cell specification",
        {"cell_function": cell.cell_function, "cell_function_other": cell.cell_function_other},
        {"cell_class": cell.cell_class},
    )
    if cell.cell_function is not None:
        sub(elem, "cellFunction", cell.cell_function, other=cell.cell_function_other)
    elif cell.cell_class is not None:
        sub(elem, "cellClass", cell.cell_class)
    else:
        raise ValueError("a cell specification requires cell_function or cell_class")


def add_drive_constraint(parent: etree._Element, constraint: Optional[DriveConstraint]) -> None:
    if constraint is None:
        return
    _add_cell_specification(sub(parent, "driveConstraint"), constraint.cell)


def add_load_constraint(parent: etree._Element, constraint: Optional[LoadConstraint]) -> None:
    if constraint is None:
        return
    elem = sub(parent, "loadConstraint")
    _add_cell_specification(elem, constraint.cell)
    add_expression(elem, "count", constraint.count)


def add_timing_constraints(parent: etree._Element, constraints: Sequence[TimingConstraint]) -> None:
    for constraint in constraints:
        sub(
            parent,
            "timingConstraint",
            constraint.value,
            xml_id=constraint.xml_id,
            clockEdge=constraint.clock_edge,
            delayType=constraint.delay_type,
            clockName=constraint.clock_name,
        )


def _add_payload(parent: etree._Element, payload: Optional[Payload]) -> None:
    if payload is None:
        return
    elem = sub(parent, "payload")
    add_text(elem, "name", payload.name)
    sub(elem, "type", payload.type)
    if payload.extension is not None:
        sub(
            elem,
            "extension",
            payload.extension,
            mandatory=bool_str(True) if payload.extension_mandatory else None,
        )
    write_vendor_extensions(elem, payload.vendor_extensions)


def add_protocol(parent: etree._Element, protocol: Optional[Protocol]) -> None:
    if protocol is None:
        return
    elem = sub(parent, "protocol")
    sub(elem, "protocolType", protocol.protocol_type, custom=protocol.custom_type_name)
    _add_payload(elem, protocol.payload)


def add_clock_driver_body(parent: etree._Element, driver: object) -> None:
    """Write clockDriverType content, shared by ipxact:clockDriver and ipxact:otherClockDriver."""
    add_expression(parent, "clockPeriod", driver.clock_period, units=driver.period_units)
    add_expression(parent, "clockPulseOffset", driver.clock_pulse_offset, units=driver.offset_units)
    add_expression(parent, "clockPulseValue", driver.clock_pulse_value)
    add_expression(parent, "clockPulseDuration", driver.clock_pulse_duration, units=driver.duration_units)
