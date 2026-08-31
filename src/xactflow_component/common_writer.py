from __future__ import annotations

from typing import Callable, Iterable, Optional, Sequence, TypeVar

from lxml import etree

from ipxact.schema.businterface import FieldReference
from ipxact.schema.common import (
    ArrayBound,
    Assertion,
    Choice,
    File,
    FileSet,
    ModeRef,
    ModuleParameter,
    Parameter,
    PartSelect,
    SubPortReference,
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
_NSMAP = {"ipxact": NAMESPACE}

T = TypeVar("T")


def qn(tag: str) -> str:
    """Build a namespace-qualified IP-XACT tag, e.g. qn("component") -> "{ns}component"."""
    return f"{{{NAMESPACE}}}{tag}"


def element(tag: str, text: object = None, /, **attrs: object) -> etree._Element:
    """Create an ipxact-namespaced element; attributes whose value is None are dropped.

    tag and text are positional-only so that **attrs stays free for XML attributes that
    happen to be named "text", "help" or "tag" (ipxact:enumeration has two of them).
    """
    elem = etree.Element(qn(tag), nsmap=_NSMAP)
    for name, value in attrs.items():
        if value is not None:
            elem.set(name, str(value))
    if text is not None:
        elem.text = str(text)
    return elem


def sub(parent: etree._Element, tag: str, text: object = None, /, **attrs: object) -> etree._Element:
    child = element(tag, text, **attrs)
    parent.append(child)
    return child


def add_text(parent: etree._Element, tag: str, value: object, **attrs: object) -> None:
    """Append a simple text child, or nothing when the value is unset."""
    if value is not None:
        sub(parent, tag, value, **attrs)


def bool_str(value: bool) -> str:
    return "true" if value else "false"


def add_bool(parent: etree._Element, tag: str, value: Optional[bool], **attrs: object) -> None:
    if value is not None:
        sub(parent, tag, bool_str(value), **attrs)


def add_texts(parent: etree._Element, tag: str, values: Iterable[object]) -> None:
    for value in values:
        sub(parent, tag, value)


def add_items(parent: etree._Element, container_tag: str, items: Sequence[T], writer: Callable[[T], etree._Element]) -> None:
    """Write container_tag holding one writer(item) per item, or nothing when items is empty.

    Mirrors ipxact.parser.common_parser.parse_children, the same shape in reverse.
    """
    if not items:
        return
    container = sub(parent, container_tag)
    for item in items:
        container.append(writer(item))


def add_name_group(
    parent: etree._Element,
    name: Optional[str],
    display_name: Optional[str] = None,
    short_description: Optional[str] = None,
    description: Optional[str] = None,
) -> None:
    """Write ipxact:nameGroup (name, displayName, shortDescription, description).

    Nearly every IP-XACT type opens with this group, but the matching ipxact-compiler
    dataclasses declare display_name/description as trailing optional fields. Element order
    therefore cannot be read off dataclass field order anywhere in this package; it comes
    from the XSD.
    """
    if name is not None:
        sub(parent, "name", name)
    add_text(parent, "displayName", display_name)
    add_text(parent, "shortDescription", short_description)
    add_text(parent, "description", description)


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
    for extension in extensions:
        container.append(etree.fromstring(extension.encode("utf-8")))
    for node in container.iter():
        if len(node) and node.text is None:
            node.text = ""


def add_vlnv(parent: etree._Element, vlnv: object) -> None:
    """Write ipxact:versionedIdentifier (vendor/library/name/version as child elements)."""
    sub(parent, "vendor", vlnv.vendor)
    sub(parent, "library", vlnv.library)
    sub(parent, "name", vlnv.name)
    sub(parent, "version", vlnv.version)


def write_vlnv_ref(tag: str, ref: VLNVRef) -> etree._Element:
    """Write a configurableLibraryRefType element (VLNV as attributes)."""
    elem = element(tag, vendor=ref.vendor, library=ref.library, name=ref.name, version=ref.version)
    if ref.config_element_values:
        values = sub(elem, "configurableElementValues")
        for reference_id, value in ref.config_element_values.items():
            sub(values, "configurableElementValue", value, referenceId=reference_id)
    return elem


def add_vectors(parent: etree._Element, vectors: Sequence[Vector], with_ids: bool = True) -> None:
    if not vectors:
        return
    container = sub(parent, "vectors")
    for vector in vectors:
        vector_elem = sub(container, "vector", vectorId=vector.vector_id if with_ids else None)
        sub(vector_elem, "left", vector.left)
        sub(vector_elem, "right", vector.right)


def add_array_bounds(parent: etree._Element, arrays: Sequence[ArrayBound], with_ids: bool = True) -> None:
    if not arrays:
        return
    container = sub(parent, "arrays")
    for array in arrays:
        array_elem = sub(container, "array", arrayId=array.array_id if with_ids else None)
        sub(array_elem, "left", array.left)
        sub(array_elem, "right", array.right)


def add_mode_refs(parent: etree._Element, mode_refs: Sequence[ModeRef], with_priority: bool = True) -> None:
    """Write ipxact:modeRef elements.

    Most places reuse the global modeRef element, whose priority attribute is required. The
    copies declared inline in busInterface.xsd (an initiator's addressSpaceRef, a target's
    memoryMapRef) have no priority attribute at all, hence the flag.
    """
    for mode_ref in mode_refs:
        sub(parent, "modeRef", mode_ref.name, priority=mode_ref.priority if with_priority else None)


def add_range(parent: etree._Element, left: Optional[str], right: Optional[str]) -> None:
    if left is None and right is None:
        return
    range_elem = sub(parent, "range")
    add_text(range_elem, "left", left)
    add_text(range_elem, "right", right)


def add_part_select(parent: etree._Element, part_select: Optional[PartSelect]) -> None:
    if part_select is None:
        return
    elem = sub(parent, "partSelect")
    if part_select.indices:
        indices = sub(elem, "indices")
        add_texts(indices, "index", part_select.indices)
    add_range(elem, part_select.range_left, part_select.range_right)


def add_sub_port_references(parent: etree._Element, refs: Sequence[SubPortReference]) -> None:
    for ref in refs:
        elem = sub(parent, "subPortReference", subPortRef=ref.sub_port_ref)
        add_part_select(elem, ref.part_select)


def add_field_reference_group(parent: etree._Element, reference: FieldReference, with_range: bool = False) -> None:
    """Write fieldReferenceGroup / fieldSliceReferenceGroup content directly into parent."""
    if reference.address_space_ref is not None:
        sub(parent, "addressSpaceRef", addressSpaceRef=reference.address_space_ref)
    elif reference.memory_map_ref is not None:
        sub(parent, "memoryMapRef", memoryMapRef=reference.memory_map_ref)
        if reference.memory_remap_ref is not None:
            sub(parent, "memoryRemapRef", memoryRemapRef=reference.memory_remap_ref)
    elif with_range:
        raise ValueError("a field slice reference requires address_space_ref or memory_map_ref")
    for bank_ref in reference.bank_refs:
        sub(parent, "bankRef", bankRef=bank_ref)
    if reference.address_block_ref is not None:
        sub(parent, "addressBlockRef", addressBlockRef=reference.address_block_ref)
    elif with_range:
        raise ValueError("a field slice reference requires address_block_ref")
    for register_file_ref in reference.register_file_refs:
        sub(parent, "registerFileRef", registerFileRef=register_file_ref)
    if reference.register_ref is not None:
        sub(parent, "registerRef", registerRef=reference.register_ref)
    elif with_range:
        raise ValueError("a field slice reference requires register_ref")
    if reference.alternate_register_ref is not None:
        sub(parent, "alternateRegisterRef", alternateRegisterRef=reference.alternate_register_ref)
    sub(parent, "fieldRef", fieldRef=reference.field_ref)
    if with_range and reference.range is not None:
        add_range(parent, reference.range.range_left, reference.range.range_right)


def _add_parameter_body(parent: etree._Element, parameter: Parameter, with_ids: bool) -> None:
    # A plain parameter's vectors/arrays carry no vectorId/arrayId: only moduleParameterType
    # declares those attributes, so they are dropped rather than written out invalidly.
    add_name_group(parent, parameter.name, parameter.display_name, parameter.short_description, parameter.description)
    add_vectors(parent, parameter.vectors, with_ids=with_ids)
    add_array_bounds(parent, parameter.arrays, with_ids=with_ids)
    sub(parent, "value", parameter.value)
    write_vendor_extensions(parent, parameter.vendor_extensions)


def _parameter_attributes(parameter: Parameter) -> dict:
    return {
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
    _add_parameter_body(elem, parameter, with_ids=False)
    return elem


def write_module_parameter(parameter: ModuleParameter) -> etree._Element:
    attrs = _parameter_attributes(parameter)
    attrs.update(
        dataType=parameter.data_type,
        usageType=parameter.usage_type if parameter.usage_type != "typed" else None,
        dataTypeDefinition=parameter.data_type_definition,
        constrained=" ".join(parameter.constrained) if parameter.constrained else None,
    )
    elem = element("moduleParameter", None, **attrs)
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
        choice_elem = sub(container, "choice")
        sub(choice_elem, "name", choice.name)
        for enumeration in choice.enumerations:
            sub(choice_elem, "enumeration", enumeration.value, text=enumeration.text, help=enumeration.help)


def add_assertions(parent: etree._Element, assertions: Sequence[Assertion]) -> None:
    if not assertions:
        return
    container = sub(parent, "assertions")
    for assertion in assertions:
        assertion_elem = sub(container, "assertion")
        add_name_group(assertion_elem, assertion.name, assertion.display_name, description=assertion.description)
        sub(assertion_elem, "assert", assertion.assert_expression)


def add_file_builder(parent: etree._Element, builder: object) -> None:
    """Write ipxact:defaultFileBuilder (fileBuilderType)."""
    elem = sub(parent, "defaultFileBuilder")
    sub(elem, "fileType", builder.file_type)
    add_text(elem, "command", builder.command)
    add_text(elem, "flags", builder.flags)
    add_text(elem, "replaceDefaultFlags", builder.replace_default_flags)


def _add_file(parent: etree._Element, file: File) -> None:
    elem = sub(parent, "file")
    sub(elem, "name", file.name)
    add_texts(elem, "fileType", file.file_types)
    if file.is_structural:
        sub(elem, "isStructural", bool_str(True))
    if file.is_include_file or file.include_has_external_declarations:
        sub(
            elem,
            "isIncludeFile",
            bool_str(file.is_include_file),
            externalDeclarations=bool_str(True) if file.include_has_external_declarations else None,
        )
    add_text(elem, "logicalName", file.logical_name)
    add_texts(elem, "exportedName", file.exported_names)
    if file.build_command is not None or file.build_flags is not None:
        build_command = sub(elem, "buildCommand")
        add_text(build_command, "command", file.build_command)
        add_text(build_command, "flags", file.build_flags)
    add_texts(elem, "dependency", file.dependencies)
    write_vendor_extensions(elem, file.vendor_extensions)


def write_file_set(file_set: FileSet) -> etree._Element:
    elem = element("fileSet")
    add_name_group(elem, file_set.name, file_set.display_name, description=file_set.description)
    add_texts(elem, "group", file_set.groups)
    for file in file_set.files:
        _add_file(elem, file)
    for builder in file_set.default_file_builders:
        add_file_builder(elem, builder)
    add_texts(elem, "dependency", file_set.dependencies)
    write_vendor_extensions(elem, file_set.vendor_extensions)
    return elem


def add_file_sets(parent: etree._Element, file_sets: Sequence[FileSet]) -> None:
    add_items(parent, "fileSets", file_sets, write_file_set)


def add_local_name_refs(parent: etree._Element, tag: str, names: Sequence[str]) -> None:
    """Write fileSetRef / constraintSetRef / busInterfaceRef style wrappers around a localName."""
    for name in names:
        ref_elem = sub(parent, tag)
        sub(ref_elem, "localName", name)


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
    elem = sub(parent, "qualifier")
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
    if cell.cell_function is not None:
        sub(elem, "cellFunction", cell.cell_function)
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
    add_text(elem, "count", constraint.count)


def add_timing_constraints(parent: etree._Element, constraints: Sequence[TimingConstraint]) -> None:
    for constraint in constraints:
        sub(
            parent,
            "timingConstraint",
            constraint.value,
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


def add_protocol(parent: etree._Element, protocol: Optional[Protocol]) -> None:
    if protocol is None:
        return
    elem = sub(parent, "protocol")
    sub(elem, "protocolType", protocol.protocol_type, custom=protocol.custom_type_name)
    _add_payload(elem, protocol.payload)


def add_clock_driver_body(parent: etree._Element, driver: object) -> None:
    """Write clockDriverType content, shared by ipxact:clockDriver and ipxact:otherClockDriver."""
    sub(parent, "clockPeriod", driver.clock_period, units=driver.period_units)
    sub(parent, "clockPulseOffset", driver.clock_pulse_offset, units=driver.offset_units)
    sub(parent, "clockPulseValue", driver.clock_pulse_value)
    sub(parent, "clockPulseDuration", driver.clock_pulse_duration, units=driver.duration_units)


