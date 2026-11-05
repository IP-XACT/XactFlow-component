from __future__ import annotations

from typing import Optional, Sequence

from lxml import etree

from ipxact.schema.common import FieldReference
from ipxact.schema.memorymap import (
    AccessPolicy,
    AccessRestriction,
    AddressBlock,
    AddressSpace,
    AlternateRegister,
    Bank,
    EnumeratedValue,
    Field,
    FieldAccessPolicy,
    LocalMemoryMap,
    MemoryMap,
    MemoryRemap,
    Register,
    RegisterFile,
    Reset,
    Segment,
    SubspaceMap,
    WriteValueConstraint,
)

from .common_writer import (
    add_access_handles,
    add_bool,
    add_definition_ref,
    add_expression,
    add_field_reference_group,
    add_items,
    add_memory_array,
    add_mode_refs,
    add_name_group,
    add_parameters,
    add_text,
    bool_str,
    check_choice,
    element,
    sub,
    write_vendor_extensions,
)


def _write_access_policy(policy: AccessPolicy) -> etree._Element:
    elem = element("accessPolicy", xml_id=policy.xml_id)
    add_mode_refs(elem, policy.mode_refs)
    if policy.access is not None:
        sub(elem, "access", policy.access.value)
    write_vendor_extensions(elem, policy.vendor_extensions)
    return elem


def add_access_policies(parent: etree._Element, access_policies: Sequence[AccessPolicy]) -> None:
    add_items(parent, "accessPolicies", access_policies, _write_access_policy)


def _add_memory_block_data(
    parent: etree._Element,
    usage: object,
    volatile: Optional[bool],
    access_policies: Sequence[AccessPolicy],
    parameters: Sequence[object],
) -> None:
    """Write ipxact:memoryBlockData (usage, volatile, accessPolicies, parameters)."""
    if usage is not None:
        sub(parent, "usage", usage.value)
    add_bool(parent, "volatile", volatile)
    add_access_policies(parent, access_policies)
    add_parameters(parent, parameters)


def _write_reset(reset: Reset) -> etree._Element:
    elem = element("reset", xml_id=reset.xml_id, resetTypeRef=reset.reset_type_ref)
    add_expression(elem, "value", reset.value)
    add_expression(elem, "mask", reset.mask)
    return elem


def _write_enumerated_value(enumerated_value: EnumeratedValue) -> etree._Element:
    elem = element(
        "enumeratedValue",
        xml_id=enumerated_value.xml_id,
        usage=enumerated_value.usage if enumerated_value.usage != "read-write" else None,
    )
    add_name_group(elem, enumerated_value)
    add_expression(elem, "value", enumerated_value.value)
    write_vendor_extensions(elem, enumerated_value.vendor_extensions)
    return elem


def _add_write_value_constraint(parent: etree._Element, constraint: Optional[WriteValueConstraint]) -> None:
    if constraint is None:
        return
    elem = sub(parent, "writeValueConstraint")
    # A required choice: writeAsRead, useEnumeratedValues, or the minimum/maximum pair (both
    # required together, not independently optional, once that arm is the one in use).
    check_choice(
        "a write value constraint",
        {"write_as_read": constraint.write_as_read},
        {"use_enumerated_values": constraint.use_enumerated_values},
        {"minimum": constraint.minimum, "maximum": constraint.maximum},
    )
    if constraint.write_as_read is not None:
        sub(elem, "writeAsRead", bool_str(constraint.write_as_read))
    elif constraint.use_enumerated_values is not None:
        sub(elem, "useEnumeratedValues", bool_str(constraint.use_enumerated_values))
    elif constraint.minimum is not None and constraint.maximum is not None:
        add_expression(elem, "minimum", constraint.minimum)
        add_expression(elem, "maximum", constraint.maximum)
    else:
        raise ValueError(
            "a write value constraint requires write_as_read, use_enumerated_values, "
            "or both minimum and maximum"
        )


def _write_access_restriction(restriction: AccessRestriction) -> etree._Element:
    elem = element("accessRestriction", xml_id=restriction.xml_id)
    add_mode_refs(elem, restriction.mode_refs)
    add_expression(elem, "readAccessMask", restriction.read_access_mask)
    add_expression(elem, "writeAccessMask", restriction.write_access_mask)
    return elem


def _write_broadcast_to(reference: FieldReference) -> etree._Element:
    elem = element("broadcastTo", xml_id=reference.xml_id)
    add_field_reference_group(elem, reference)
    return elem


def _write_field_access_policy(policy: FieldAccessPolicy) -> etree._Element:
    elem = element("fieldAccessPolicy", xml_id=policy.xml_id)
    add_mode_refs(elem, policy.mode_refs)
    # The definition reference replaces the inline access/.../readResponse content.
    check_choice(
        "a field access policy",
        {"field_access_policy_definition_ref": policy.field_access_policy_definition_ref},
        {
            "access": policy.access,
            "modified_write_value": policy.modified_write_value,
            "modified_write_value_modify": policy.modified_write_value_modify,
            "write_value_constraint": policy.write_value_constraint,
            "read_action": policy.read_action,
            "read_action_modify": policy.read_action_modify,
            "read_response": policy.read_response,
        },
    )
    if policy.field_access_policy_definition_ref is not None:
        add_definition_ref(elem, "fieldAccessPolicyDefinitionRef", policy.field_access_policy_definition_ref)
    else:
        if policy.access is not None:
            sub(elem, "access", policy.access.value)
        if policy.modified_write_value is not None:
            sub(elem, "modifiedWriteValue", policy.modified_write_value.value, modify=policy.modified_write_value_modify)
        _add_write_value_constraint(elem, policy.write_value_constraint)
        if policy.read_action is not None:
            sub(elem, "readAction", policy.read_action.value, modify=policy.read_action_modify)
        add_expression(elem, "readResponse", policy.read_response)
    add_items(elem, "broadcasts", policy.broadcast_to, _write_broadcast_to)
    add_items(elem, "accessRestrictions", policy.access_restrictions, _write_access_restriction)
    if policy.testable is not None:
        sub(
            elem,
            "testable",
            bool_str(policy.testable),
            testConstraint=policy.test_constraint.value if policy.test_constraint is not None else None,
        )
    add_expression(elem, "reserved", policy.reserved)
    write_vendor_extensions(elem, policy.vendor_extensions)
    return elem


def _add_field(parent: etree._Element, field: Field) -> None:
    elem = sub(parent, "field", xml_id=field.xml_id)
    add_name_group(elem, field)
    add_access_handles(elem, field.access_handles)
    add_memory_array(elem, field.array, stride_tag="bitStride")
    add_expression(elem, "bitOffset", field.bit_offset)
    # The field definition reference replaces everything up to the parameters.
    check_choice(
        f"field {field.name!r}",
        {"field_definition_ref": field.field_definition_ref},
        {
            "type_identifier": field.type_identifier,
            "bit_width": field.bit_width,
            "volatile": field.volatile,
            "resets": field.resets,
            "alias_of": field.alias_of,
            "field_access_policies": field.field_access_policies,
            "field_access_policies_xml_id": field.field_access_policies_xml_id,
            "enumeration_definition_ref": field.enumeration_definition_ref,
            "enumerated_values": field.enumerated_values,
        },
    )
    if field.field_definition_ref is not None:
        add_definition_ref(elem, "fieldDefinitionRef", field.field_definition_ref)
    else:
        add_text(elem, "typeIdentifier", field.type_identifier)
        # bitWidth (with volatile and resets) and aliasOf are the two arms of a required choice.
        check_choice(
            f"field {field.name!r}",
            {"bit_width": field.bit_width, "volatile": field.volatile, "resets": field.resets},
            {"alias_of": field.alias_of},
        )
        check_choice(
            f"field {field.name!r}",
            {"enumeration_definition_ref": field.enumeration_definition_ref},
            {"enumerated_values": field.enumerated_values},
        )
        if field.bit_width is not None:
            add_expression(elem, "bitWidth", field.bit_width)
            add_bool(elem, "volatile", field.volatile)
            add_items(elem, "resets", field.resets, _write_reset)
        elif field.alias_of is not None:
            add_field_reference_group(sub(elem, "aliasOf"), field.alias_of)
        else:
            raise ValueError(f"field {field.name!r} requires bit_width, alias_of or field_definition_ref")
        if field.field_access_policies:
            policies = sub(elem, "fieldAccessPolicies", xml_id=field.field_access_policies_xml_id)
            for policy in field.field_access_policies:
                policies.append(_write_field_access_policy(policy))
        if field.enumeration_definition_ref is not None:
            add_definition_ref(sub(elem, "enumeratedValues"), "enumerationDefinitionRef", field.enumeration_definition_ref)
        else:
            add_items(elem, "enumeratedValues", field.enumerated_values, _write_enumerated_value)
    add_parameters(elem, field.parameters)
    write_vendor_extensions(elem, field.vendor_extensions)


def _add_alternate_register(parent: etree._Element, alternate_register: AlternateRegister) -> None:
    elem = sub(parent, "alternateRegister", xml_id=alternate_register.xml_id)
    add_name_group(elem, alternate_register)
    add_access_handles(elem, alternate_register.access_handles, with_force=False)
    add_mode_refs(elem, alternate_register.mode_refs)
    add_text(elem, "typeIdentifier", alternate_register.type_identifier)
    add_bool(elem, "volatile", alternate_register.volatile)
    add_access_policies(elem, alternate_register.access_policies)
    for field in alternate_register.fields:
        _add_field(elem, field)
    add_parameters(elem, alternate_register.parameters)
    write_vendor_extensions(elem, alternate_register.vendor_extensions)


def _add_register(parent: etree._Element, register: Register) -> None:
    elem = sub(parent, "register", xml_id=register.xml_id)
    add_name_group(elem, register)
    add_access_handles(elem, register.access_handles, with_force=False)
    add_memory_array(elem, register.array)
    add_expression(elem, "addressOffset", register.address_offset)
    check_choice(
        f"register {register.name!r}",
        {"register_definition_ref": register.register_definition_ref},
        {
            "type_identifier": register.type_identifier,
            "size": register.size,
            "volatile": register.volatile,
            "access_policies": register.access_policies,
            "fields": register.fields,
        },
    )
    if register.register_definition_ref is not None:
        add_definition_ref(elem, "registerDefinitionRef", register.register_definition_ref)
    else:
        add_text(elem, "typeIdentifier", register.type_identifier)
        add_expression(elem, "size", register.size)
        add_bool(elem, "volatile", register.volatile)
        add_access_policies(elem, register.access_policies)
        for field in register.fields:
            _add_field(elem, field)
    if register.alternate_registers:
        alternate_registers = sub(elem, "alternateRegisters")
        for alternate_register in register.alternate_registers:
            _add_alternate_register(alternate_registers, alternate_register)
    add_parameters(elem, register.parameters)
    write_vendor_extensions(elem, register.vendor_extensions)


def _add_register_file(parent: etree._Element, register_file: RegisterFile) -> None:
    elem = sub(parent, "registerFile", xml_id=register_file.xml_id)
    add_name_group(elem, register_file)
    add_access_handles(elem, register_file.access_handles, with_force=False)
    add_memory_array(elem, register_file.array)
    add_expression(elem, "addressOffset", register_file.address_offset)
    check_choice(
        f"register file {register_file.name!r}",
        {"register_file_definition_ref": register_file.register_file_definition_ref},
        {
            "type_identifier": register_file.type_identifier,
            "range": register_file.range,
            "access_policies": register_file.access_policies,
            "registers": register_file.registers,
        },
    )
    if register_file.register_file_definition_ref is not None:
        add_definition_ref(elem, "registerFileDefinitionRef", register_file.register_file_definition_ref)
    else:
        add_text(elem, "typeIdentifier", register_file.type_identifier)
        add_expression(elem, "range", register_file.range)
        add_access_policies(elem, register_file.access_policies)
        _add_registers(elem, register_file.registers)
    add_parameters(elem, register_file.parameters)
    write_vendor_extensions(elem, register_file.vendor_extensions)


def _add_registers(parent: etree._Element, registers: Sequence[object]) -> None:
    for item in registers:
        if isinstance(item, RegisterFile):
            _add_register_file(parent, item)
        elif isinstance(item, Register):
            _add_register(parent, item)
        else:
            raise TypeError(f"unsupported register list entry: {type(item)}")


def _add_address_block(parent: etree._Element, block: AddressBlock, banked: bool) -> None:
    """Write an addressBlock.

    A banked block uses the schema's separate bankedBlockType, which carries no baseAddress,
    array, typeIdentifier, definition reference or misalignmentAllowed attribute.
    """
    elem = sub(
        parent,
        "addressBlock",
        xml_id=block.xml_id,
        misalignmentAllowed=None if banked or block.misalignment_allowed else bool_str(False),
    )
    add_name_group(elem, block)
    add_access_handles(elem, block.access_handles)
    if not banked:
        add_memory_array(elem, block.array)
        add_expression(elem, "baseAddress", block.base_address)
        check_choice(
            f"address block {block.name!r}",
            {"address_block_definition_ref": block.address_block_definition_ref},
            {
                "type_identifier": block.type_identifier,
                "range": block.range,
                "width": block.width,
                "usage": block.usage,
                "volatile": block.volatile,
                "access_policies": block.access_policies,
                "parameters": block.parameters,
                "registers": block.registers,
            },
        )
        if block.address_block_definition_ref is not None:
            add_definition_ref(elem, "addressBlockDefinitionRef", block.address_block_definition_ref)
            write_vendor_extensions(elem, block.vendor_extensions)
            return
        add_text(elem, "typeIdentifier", block.type_identifier)
    add_expression(elem, "range", block.range)
    add_expression(elem, "width", block.width)
    _add_memory_block_data(elem, block.usage, block.volatile, block.access_policies, block.parameters)
    _add_registers(elem, block.registers)
    write_vendor_extensions(elem, block.vendor_extensions)


def _add_subspace_map(parent: etree._Element, subspace_map: SubspaceMap, banked: bool) -> None:
    elem = sub(
        parent,
        "subspaceMap",
        xml_id=subspace_map.xml_id,
        initiatorRef=subspace_map.initiator_ref,
        segmentRef=None if banked else subspace_map.segment_ref,
    )
    add_name_group(elem, subspace_map)
    if not banked:
        add_expression(elem, "baseAddress", subspace_map.base_address)
    add_parameters(elem, subspace_map.parameters)
    write_vendor_extensions(elem, subspace_map.vendor_extensions)


def _add_bank(parent: etree._Element, bank: Bank, banked: bool, allow_subspace: bool) -> None:
    """Write a bank.

    A bank nested inside another bank uses the schema's separate bankedBankType, which
    carries no baseAddress, matching AddressBlock/SubspaceMap's own banked distinction.
    """
    elem = sub(parent, "bank", xml_id=bank.xml_id, bankAlignment=bank.bank_alignment.value)
    add_name_group(elem, bank)
    add_access_handles(elem, bank.access_handles, with_force=False)
    if not banked:
        add_expression(elem, "baseAddress", bank.base_address)
    check_choice(
        f"bank {bank.name!r}",
        {"bank_definition_ref": bank.bank_definition_ref},
        {
            "items": bank.items,
            "usage": bank.usage,
            "volatile": bank.volatile,
            "access_policies": bank.access_policies,
            "parameters": bank.parameters,
        },
    )
    if bank.bank_definition_ref is not None:
        add_definition_ref(elem, "bankDefinitionRef", bank.bank_definition_ref)
    else:
        _add_memory_map_items(elem, bank.items, banked=True, allow_subspace=allow_subspace)
        _add_memory_block_data(elem, bank.usage, bank.volatile, bank.access_policies, bank.parameters)
    write_vendor_extensions(elem, bank.vendor_extensions)


def _add_memory_map_items(
    parent: etree._Element,
    items: Sequence[object],
    banked: bool = False,
    allow_subspace: bool = True,
) -> None:
    for item in items:
        if isinstance(item, Bank):
            _add_bank(parent, item, banked=banked, allow_subspace=allow_subspace)
        elif isinstance(item, AddressBlock):
            _add_address_block(parent, item, banked=banked)
        elif isinstance(item, SubspaceMap):
            if not allow_subspace:
                raise TypeError("subspaceMap is not allowed inside a localMemoryMap")
            _add_subspace_map(parent, item, banked=banked)
        else:
            raise TypeError(f"unsupported memory map item: {type(item)}")


def _add_memory_remap(parent: etree._Element, memory_remap: MemoryRemap) -> None:
    elem = sub(parent, "memoryRemap", xml_id=memory_remap.xml_id)
    add_name_group(elem, memory_remap)
    add_mode_refs(elem, memory_remap.mode_refs)
    check_choice(
        f"memory remap {memory_remap.name!r}",
        {"remap_definition_ref": memory_remap.remap_definition_ref},
        {"items": memory_remap.items},
    )
    if memory_remap.remap_definition_ref is not None:
        add_definition_ref(elem, "remapDefinitionRef", memory_remap.remap_definition_ref)
    else:
        _add_memory_map_items(elem, memory_remap.items)
    write_vendor_extensions(elem, memory_remap.vendor_extensions)


def write_memory_map(memory_map: MemoryMap) -> etree._Element:
    elem = element("memoryMap", xml_id=memory_map.xml_id)
    add_name_group(elem, memory_map)
    check_choice(
        f"memory map {memory_map.name!r}",
        {"memory_map_definition_ref": memory_map.memory_map_definition_ref},
        {
            "items": memory_map.items,
            "memory_remaps": memory_map.memory_remaps,
            "address_unit_bits": memory_map.address_unit_bits,
            "shared": memory_map.shared,
        },
    )
    if memory_map.memory_map_definition_ref is not None:
        add_definition_ref(elem, "memoryMapDefinitionRef", memory_map.memory_map_definition_ref)
    else:
        _add_memory_map_items(elem, memory_map.items)
        for memory_remap in memory_map.memory_remaps:
            _add_memory_remap(elem, memory_remap)
        add_expression(elem, "addressUnitBits", memory_map.address_unit_bits)
        if memory_map.shared is not None:
            sub(elem, "shared", memory_map.shared.value)
    write_vendor_extensions(elem, memory_map.vendor_extensions)
    return elem


def add_memory_maps(parent: etree._Element, memory_maps: Sequence[MemoryMap]) -> None:
    add_items(parent, "memoryMaps", memory_maps, write_memory_map)


def _add_local_memory_map(parent: etree._Element, local_memory_map: LocalMemoryMap) -> None:
    elem = sub(parent, "localMemoryMap", xml_id=local_memory_map.xml_id)
    add_name_group(elem, local_memory_map)
    _add_memory_map_items(elem, local_memory_map.items, allow_subspace=False)
    write_vendor_extensions(elem, local_memory_map.vendor_extensions)


def _write_segment(segment: Segment) -> etree._Element:
    elem = element("segment", xml_id=segment.xml_id)
    add_name_group(elem, segment)
    add_expression(elem, "addressOffset", segment.address_offset)
    add_expression(elem, "range", segment.range)
    write_vendor_extensions(elem, segment.vendor_extensions)
    return elem


def write_address_space(address_space: AddressSpace) -> etree._Element:
    elem = element("addressSpace", xml_id=address_space.xml_id)
    add_name_group(elem, address_space)
    add_expression(elem, "range", address_space.range)
    add_expression(elem, "width", address_space.width)
    add_items(elem, "segments", address_space.segments, _write_segment)
    add_expression(elem, "addressUnitBits", address_space.address_unit_bits)
    if address_space.local_memory_map is not None:
        _add_local_memory_map(elem, address_space.local_memory_map)
    add_parameters(elem, address_space.parameters)
    write_vendor_extensions(elem, address_space.vendor_extensions)
    return elem


def add_address_spaces(parent: etree._Element, address_spaces: Sequence[AddressSpace]) -> None:
    add_items(parent, "addressSpaces", address_spaces, write_address_space)
