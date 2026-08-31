from __future__ import annotations

from typing import Optional, Sequence

from lxml import etree

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
from ipxact.schema.common import MemoryArray

from .common_writer import (
    add_bool,
    add_items,
    add_mode_refs,
    add_name_group,
    add_parameters,
    add_text,
    bool_str,
    element,
    sub,
    write_vendor_extensions,
)


def _add_memory_array(parent: etree._Element, array: Optional[MemoryArray], stride_tag: str = "stride") -> None:
    """Write ipxact:array. Registers use ipxact:stride, fields use ipxact:bitStride."""
    if array is None:
        return
    elem = sub(parent, "array")
    for dim in array.dims:
        sub(elem, "dim", dim.size, indexVar=dim.index_var)
    add_text(elem, stride_tag, array.stride)


def add_access_policies(parent: etree._Element, access_policies: Sequence[AccessPolicy]) -> None:
    if not access_policies:
        return
    container = sub(parent, "accessPolicies")
    for policy in access_policies:
        elem = sub(container, "accessPolicy")
        add_mode_refs(elem, policy.mode_refs)
        if policy.access is not None:
            sub(elem, "access", policy.access.value)


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


def _add_reset(parent: etree._Element, reset: Reset) -> None:
    elem = sub(parent, "reset", resetTypeRef=reset.reset_type_ref)
    sub(elem, "value", reset.value)
    add_text(elem, "mask", reset.mask)


def _add_enumerated_value(parent: etree._Element, enumerated_value: EnumeratedValue) -> None:
    elem = sub(
        parent,
        "enumeratedValue",
        usage=enumerated_value.usage if enumerated_value.usage != "read-write" else None,
    )
    add_name_group(
        elem,
        enumerated_value.name,
        enumerated_value.display_name,
        description=enumerated_value.description,
    )
    sub(elem, "value", enumerated_value.value)


def _add_write_value_constraint(parent: etree._Element, constraint: Optional[WriteValueConstraint]) -> None:
    if constraint is None:
        return
    elem = sub(parent, "writeValueConstraint")
    # A required choice: writeAsRead, useEnumeratedValues, or the minimum/maximum pair (both
    # required together, not independently optional, once that arm is the one in use).
    if constraint.write_as_read is not None:
        sub(elem, "writeAsRead", bool_str(constraint.write_as_read))
    elif constraint.use_enumerated_values is not None:
        sub(elem, "useEnumeratedValues", bool_str(constraint.use_enumerated_values))
    elif constraint.minimum is not None and constraint.maximum is not None:
        sub(elem, "minimum", constraint.minimum)
        sub(elem, "maximum", constraint.maximum)
    else:
        raise ValueError(
            "a write value constraint requires write_as_read, use_enumerated_values, "
            "or both minimum and maximum"
        )


def _add_access_restriction(parent: etree._Element, restriction: AccessRestriction) -> None:
    elem = sub(parent, "accessRestriction")
    add_mode_refs(elem, restriction.mode_refs)
    add_text(elem, "readAccessMask", restriction.read_access_mask)
    add_text(elem, "writeAccessMask", restriction.write_access_mask)


def _add_field_access_policy(parent: etree._Element, policy: FieldAccessPolicy) -> None:
    elem = sub(parent, "fieldAccessPolicy")
    add_mode_refs(elem, policy.mode_refs)
    if policy.access is not None:
        sub(elem, "access", policy.access.value)
    if policy.modified_write_value is not None:
        sub(elem, "modifiedWriteValue", policy.modified_write_value.value)
    _add_write_value_constraint(elem, policy.write_value_constraint)
    if policy.read_action is not None:
        sub(elem, "readAction", policy.read_action.value)
    add_text(elem, "readResponse", policy.read_response)
    if policy.broadcast_to:
        broadcasts = sub(elem, "broadcasts")
        for field_ref in policy.broadcast_to:
            sub(sub(broadcasts, "broadcastTo"), "fieldRef", fieldRef=field_ref)
    if policy.access_restrictions:
        restrictions = sub(elem, "accessRestrictions")
        for restriction in policy.access_restrictions:
            _add_access_restriction(restrictions, restriction)
    if policy.testable is not None:
        sub(
            elem,
            "testable",
            bool_str(policy.testable),
            testConstraint=policy.test_constraint.value if policy.test_constraint is not None else None,
        )
    add_text(elem, "reserved", policy.reserved)


def _add_field(parent: etree._Element, field: Field) -> None:
    elem = sub(parent, "field")
    add_name_group(elem, field.name, field.display_name, description=field.description)
    _add_memory_array(elem, field.array, stride_tag="bitStride")
    sub(elem, "bitOffset", field.bit_offset)
    sub(elem, "bitWidth", field.bit_width)
    add_bool(elem, "volatile", field.volatile)
    if field.resets:
        resets = sub(elem, "resets")
        for reset in field.resets:
            _add_reset(resets, reset)
    if field.field_access_policies:
        policies = sub(elem, "fieldAccessPolicies")
        for policy in field.field_access_policies:
            _add_field_access_policy(policies, policy)
    if field.enumerated_values:
        enumerated_values = sub(elem, "enumeratedValues")
        for enumerated_value in field.enumerated_values:
            _add_enumerated_value(enumerated_values, enumerated_value)
    add_parameters(elem, field.parameters)
    write_vendor_extensions(elem, field.vendor_extensions)


def _add_alternate_register(parent: etree._Element, alternate_register: AlternateRegister) -> None:
    elem = sub(parent, "alternateRegister")
    add_name_group(
        elem,
        alternate_register.name,
        alternate_register.display_name,
        description=alternate_register.description,
    )
    add_mode_refs(elem, alternate_register.mode_refs)
    add_bool(elem, "volatile", alternate_register.volatile)
    add_access_policies(elem, alternate_register.access_policies)
    for field in alternate_register.fields:
        _add_field(elem, field)
    add_parameters(elem, alternate_register.parameters)
    write_vendor_extensions(elem, alternate_register.vendor_extensions)


def _add_register(parent: etree._Element, register: Register) -> None:
    elem = sub(parent, "register")
    add_name_group(elem, register.name, register.display_name, description=register.description)
    _add_memory_array(elem, register.array)
    sub(elem, "addressOffset", register.address_offset)
    sub(elem, "size", register.size)
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
    elem = sub(parent, "registerFile")
    add_name_group(elem, register_file.name, register_file.display_name, description=register_file.description)
    _add_memory_array(elem, register_file.array)
    sub(elem, "addressOffset", register_file.address_offset)
    sub(elem, "range", register_file.range)
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

    A banked block uses the schema's separate bankedBlockType, which carries neither a
    baseAddress nor the misalignmentAllowed attribute.
    """
    elem = sub(
        parent,
        "addressBlock",
        misalignmentAllowed=None if banked or block.misalignment_allowed else bool_str(False),
    )
    add_name_group(elem, block.name, block.display_name, description=block.description)
    if not banked:
        add_text(elem, "baseAddress", block.base_address)
    sub(elem, "range", block.range)
    sub(elem, "width", block.width)
    _add_memory_block_data(elem, block.usage, block.volatile, block.access_policies, block.parameters)
    _add_registers(elem, block.registers)
    write_vendor_extensions(elem, block.vendor_extensions)


def _add_subspace_map(parent: etree._Element, subspace_map: SubspaceMap, banked: bool) -> None:
    elem = sub(
        parent,
        "subspaceMap",
        initiatorRef=subspace_map.initiator_ref,
        segmentRef=None if banked else subspace_map.segment_ref,
    )
    add_name_group(elem, subspace_map.name, subspace_map.display_name, description=subspace_map.description)
    if not banked:
        add_text(elem, "baseAddress", subspace_map.base_address)
    add_parameters(elem, subspace_map.parameters)
    write_vendor_extensions(elem, subspace_map.vendor_extensions)


def _add_bank(parent: etree._Element, bank: Bank, allow_subspace: bool) -> None:
    elem = sub(parent, "bank", bankAlignment=bank.bank_alignment.value)
    add_name_group(elem, bank.name, bank.display_name, description=bank.description)
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
            _add_bank(parent, item, allow_subspace=allow_subspace)
        elif isinstance(item, AddressBlock):
            _add_address_block(parent, item, banked=banked)
        elif isinstance(item, SubspaceMap):
            if not allow_subspace:
                raise TypeError("subspaceMap is not allowed inside a localMemoryMap")
            _add_subspace_map(parent, item, banked=banked)
        else:
            raise TypeError(f"unsupported memory map item: {type(item)}")


def _add_memory_remap(parent: etree._Element, memory_remap: MemoryRemap) -> None:
    elem = sub(parent, "memoryRemap")
    add_name_group(elem, memory_remap.name, memory_remap.display_name, description=memory_remap.description)
    add_mode_refs(elem, memory_remap.mode_refs)
    _add_memory_map_items(elem, memory_remap.items)
    write_vendor_extensions(elem, memory_remap.vendor_extensions)


def write_memory_map(memory_map: MemoryMap) -> etree._Element:
    elem = element("memoryMap")
    add_name_group(elem, memory_map.name, memory_map.display_name, description=memory_map.description)
    _add_memory_map_items(elem, memory_map.items)
    for memory_remap in memory_map.memory_remaps:
        _add_memory_remap(elem, memory_remap)
    add_text(elem, "addressUnitBits", memory_map.address_unit_bits)
    if memory_map.shared is not None:
        sub(elem, "shared", memory_map.shared.value)
    write_vendor_extensions(elem, memory_map.vendor_extensions)
    return elem


def add_memory_maps(parent: etree._Element, memory_maps: Sequence[MemoryMap]) -> None:
    add_items(parent, "memoryMaps", memory_maps, write_memory_map)


def _add_local_memory_map(parent: etree._Element, local_memory_map: LocalMemoryMap) -> None:
    elem = sub(parent, "localMemoryMap")
    add_name_group(
        elem,
        local_memory_map.name,
        local_memory_map.display_name,
        description=local_memory_map.description,
    )
    _add_memory_map_items(elem, local_memory_map.items, allow_subspace=False)
    write_vendor_extensions(elem, local_memory_map.vendor_extensions)


def _add_segment(parent: etree._Element, segment: Segment) -> None:
    elem = sub(parent, "segment")
    add_name_group(elem, segment.name, segment.display_name, description=segment.description)
    sub(elem, "addressOffset", segment.address_offset)
    sub(elem, "range", segment.range)
    write_vendor_extensions(elem, segment.vendor_extensions)


def write_address_space(address_space: AddressSpace) -> etree._Element:
    elem = element("addressSpace")
    add_name_group(elem, address_space.name, address_space.display_name, description=address_space.description)
    sub(elem, "range", address_space.range)
    sub(elem, "width", address_space.width)
    if address_space.segments:
        segments = sub(elem, "segments")
        for segment in address_space.segments:
            _add_segment(segments, segment)
    add_text(elem, "addressUnitBits", address_space.address_unit_bits)
    if address_space.local_memory_map is not None:
        _add_local_memory_map(elem, address_space.local_memory_map)
    add_parameters(elem, address_space.parameters)
    write_vendor_extensions(elem, address_space.vendor_extensions)
    return elem


def add_address_spaces(parent: etree._Element, address_spaces: Sequence[AddressSpace]) -> None:
    add_items(parent, "addressSpaces", address_spaces, write_address_space)
