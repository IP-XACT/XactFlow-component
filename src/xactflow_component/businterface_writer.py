from __future__ import annotations

from typing import Sequence

from lxml import etree

from ipxact.schema.businterface import (
    AbstractionType,
    BusInterface,
    Channel,
    IndirectInterface,
    InitiatorInterface,
    InterfaceMode,
    MirroredInitiatorInterface,
    MirroredTargetInterface,
    MonitorInterface,
    PortMap,
    SystemInterface,
    TargetInterface,
    TransparentBridge,
)

from .common_writer import (
    add_expression,
    add_field_reference_group,
    add_file_set_ref_group,
    add_items,
    add_local_references,
    add_mode_refs,
    add_name_group,
    add_parameters,
    add_part_select,
    add_range,
    add_raw_content,
    add_text,
    add_text_values,
    bool_str,
    check_choice,
    element,
    set_other_attributes,
    sub,
    write_vendor_extensions,
    write_vlnv_ref,
)


def _add_transparent_bridges(parent: etree._Element, bridges: Sequence[TransparentBridge]) -> None:
    for bridge in bridges:
        elem = sub(parent, "transparentBridge", xml_id=bridge.xml_id, initiatorRef=bridge.initiator_ref)
        write_vendor_extensions(elem, bridge.vendor_extensions)


def _write_port_map(port_map: PortMap) -> etree._Element:
    elem = element("portMap", xml_id=port_map.xml_id, invert=bool_str(True) if port_map.invert else None)
    logical_port = sub(elem, "logicalPort", xml_id=port_map.logical_port_xml_id)
    sub(logical_port, "name", port_map.logical_port)
    add_range(logical_port, port_map.logical_range)
    # physicalPort and logicalTieOff are the two arms of a required choice.
    check_choice(
        f"the port map of {port_map.logical_port!r}",
        {
            "physical_port": port_map.physical_port,
            "physical_port_xml_id": port_map.physical_port_xml_id,
            "part_select": port_map.part_select,
            "sub_port_refs": port_map.sub_port_refs,
        },
        {"logical_tie_off": port_map.logical_tie_off},
    )
    if port_map.physical_port is not None:
        physical_port = sub(elem, "physicalPort", xml_id=port_map.physical_port_xml_id)
        sub(physical_port, "name", port_map.physical_port)
        add_part_select(physical_port, port_map.part_select)
        # Here a subPort names its subport in a <name> child, not in a subPortRef attribute.
        for sub_port_ref in port_map.sub_port_refs:
            sub_port_elem = sub(physical_port, "subPort", xml_id=sub_port_ref.xml_id)
            sub(sub_port_elem, "name", sub_port_ref.sub_port_ref)
            add_part_select(sub_port_elem, sub_port_ref.part_select)
    elif port_map.logical_tie_off is not None:
        add_expression(elem, "logicalTieOff", port_map.logical_tie_off)
    else:
        raise ValueError("a port map requires physical_port or logical_tie_off")
    if port_map.is_informative:
        sub(elem, "isInformative", bool_str(True))
    write_vendor_extensions(elem, port_map.vendor_extensions)
    return elem


def _write_abstraction_type(abstraction_type: AbstractionType) -> etree._Element:
    elem = element("abstractionType", xml_id=abstraction_type.xml_id)
    add_text_values(elem, "viewRef", abstraction_type.view_refs)
    elem.append(write_vlnv_ref("abstractionRef", abstraction_type.abstraction_ref))
    add_items(elem, "portMaps", abstraction_type.port_maps, _write_port_map)
    return elem


def _add_initiator(parent: etree._Element, initiator: InitiatorInterface) -> None:
    elem = sub(parent, "initiator")
    if initiator.address_space_ref is None:
        return
    ref_elem = sub(elem, "addressSpaceRef", xml_id=initiator.xml_id, addressSpaceRef=initiator.address_space_ref)
    # addrSpaceRefType's own vendorExtensions come first: the extension adds baseAddress and modeRef after them.
    write_vendor_extensions(ref_elem, initiator.vendor_extensions)
    add_expression(ref_elem, "baseAddress", initiator.base_address)
    add_mode_refs(ref_elem, initiator.mode_refs)


def _add_target(parent: etree._Element, target: TargetInterface) -> None:
    elem = sub(parent, "target")
    # memoryMapRef and transparentBridge are the two arms of an optional choice.
    check_choice(
        "a target interface",
        {"memory_map_ref": target.memory_map_ref, "mode_refs": target.mode_refs},
        {"transparent_bridges": target.transparent_bridges},
    )
    if target.memory_map_ref is not None:
        ref_elem = sub(elem, "memoryMapRef", memoryMapRef=target.memory_map_ref)
        add_mode_refs(ref_elem, target.mode_refs)
    else:
        _add_transparent_bridges(elem, target.transparent_bridges)
    for group in target.file_set_ref_groups:
        add_file_set_ref_group(elem, group)


def _add_mirrored_target(parent: etree._Element, mirrored_target: MirroredTargetInterface) -> None:
    elem = sub(parent, "mirroredTarget")
    if not mirrored_target.remap_addresses and mirrored_target.range is None:
        return
    if not mirrored_target.remap_addresses or mirrored_target.range is None:
        raise ValueError("a mirrored target's base addresses require both remap_addresses and range")
    base_addresses = sub(elem, "baseAddresses")
    for remap_address in mirrored_target.remap_addresses:
        remap_elem = sub(base_addresses, "remapAddresses", xml_id=remap_address.xml_id)
        add_expression(remap_elem, "remapAddress", remap_address.value)
        add_mode_refs(remap_elem, remap_address.mode_refs)
    add_expression(base_addresses, "range", mirrored_target.range)


def _add_mirrored_initiator(parent: etree._Element, mirrored_initiator: MirroredInitiatorInterface) -> None:
    # The schema leaves mirroredInitiator untyped, so it may carry any attributes and content.
    elem = sub(parent, "mirroredInitiator", mirrored_initiator.text)
    set_other_attributes(elem, mirrored_initiator.other_attributes)
    add_raw_content(elem, mirrored_initiator.content)


def _add_system(parent: etree._Element, tag: str, system: SystemInterface) -> None:
    sub(sub(parent, tag), "group", system.group)


def _add_monitor(parent: etree._Element, monitor: MonitorInterface) -> None:
    elem = sub(parent, "monitor", interfaceMode=monitor.interface_mode.value)
    add_text(elem, "group", monitor.group)


_MODE_FIELDS = {
    InterfaceMode.INITIATOR: "initiator",
    InterfaceMode.TARGET: "target",
    InterfaceMode.SYSTEM: "system",
    InterfaceMode.MIRRORED_TARGET: "mirrored_target",
    InterfaceMode.MIRRORED_INITIATOR: "mirrored_initiator",
    InterfaceMode.MIRRORED_SYSTEM: "mirrored_system",
    InterfaceMode.MONITOR: "monitor",
}


def _add_interface_mode(parent: etree._Element, bus_interface: BusInterface) -> None:
    mode = bus_interface.mode
    # The interface modes are the arms of a choice: only the one selected by mode is written.
    others = [name for other, name in _MODE_FIELDS.items() if other is not mode and getattr(bus_interface, name) is not None]
    if others:
        raise ValueError(f"bus interface {bus_interface.name!r} has mode {mode.name} but also sets {', '.join(others)}")
    if mode is InterfaceMode.INITIATOR:
        _add_initiator(parent, bus_interface.initiator or InitiatorInterface())
    elif mode is InterfaceMode.TARGET:
        _add_target(parent, bus_interface.target or TargetInterface())
    elif mode is InterfaceMode.SYSTEM:
        if bus_interface.system is None:
            raise ValueError("mode is SYSTEM but system is not set")
        _add_system(parent, "system", bus_interface.system)
    elif mode is InterfaceMode.MIRRORED_TARGET:
        _add_mirrored_target(parent, bus_interface.mirrored_target or MirroredTargetInterface())
    elif mode is InterfaceMode.MIRRORED_INITIATOR:
        _add_mirrored_initiator(parent, bus_interface.mirrored_initiator or MirroredInitiatorInterface())
    elif mode is InterfaceMode.MIRRORED_SYSTEM:
        if bus_interface.mirrored_system is None:
            raise ValueError("mode is MIRRORED_SYSTEM but mirrored_system is not set")
        _add_system(parent, "mirroredSystem", bus_interface.mirrored_system)
    elif mode is InterfaceMode.MONITOR:
        if bus_interface.monitor is None:
            raise ValueError("mode is MONITOR but monitor is not set")
        _add_monitor(parent, bus_interface.monitor)
    else:
        raise ValueError(f"unrecognized bus interface mode: {mode!r}")


def write_bus_interface(bus_interface: BusInterface) -> etree._Element:
    elem = element("busInterface", xml_id=bus_interface.xml_id)
    set_other_attributes(elem, bus_interface.other_attributes)
    add_name_group(elem, bus_interface)
    elem.append(write_vlnv_ref("busType", bus_interface.bus_type))
    add_items(elem, "abstractionTypes", bus_interface.abstraction_types, _write_abstraction_type)
    _add_interface_mode(elem, bus_interface)
    if bus_interface.connection_required:
        sub(elem, "connectionRequired", bool_str(True))
    add_expression(elem, "bitsInLau", bus_interface.bits_in_lau)
    add_expression(elem, "bitSteering", bus_interface.bit_steering)
    add_text(elem, "endianness", bus_interface.endianness)
    add_parameters(elem, bus_interface.parameters)
    write_vendor_extensions(elem, bus_interface.vendor_extensions)
    return elem


def add_bus_interfaces(parent: etree._Element, bus_interfaces: Sequence[BusInterface]) -> None:
    add_items(parent, "busInterfaces", bus_interfaces, write_bus_interface)


def write_indirect_interface(indirect_interface: IndirectInterface) -> etree._Element:
    elem = element("indirectInterface", xml_id=indirect_interface.xml_id)
    set_other_attributes(elem, indirect_interface.other_attributes)
    add_name_group(elem, indirect_interface)
    add_field_reference_group(sub(elem, "indirectAddressRef"), indirect_interface.indirect_address_ref)
    add_field_reference_group(sub(elem, "indirectDataRef"), indirect_interface.indirect_data_ref)
    # memoryMapRef and transparentBridge are the two arms of a required choice.
    check_choice(
        f"indirect interface {indirect_interface.name!r}",
        {"memory_map_ref": indirect_interface.memory_map_ref},
        {"transparent_bridges": indirect_interface.transparent_bridges},
    )
    if indirect_interface.memory_map_ref is not None:
        sub(elem, "memoryMapRef", indirect_interface.memory_map_ref)
    elif indirect_interface.transparent_bridges:
        _add_transparent_bridges(elem, indirect_interface.transparent_bridges)
    else:
        raise ValueError("an indirect interface requires memory_map_ref or transparent_bridges")
    add_expression(elem, "bitsInLau", indirect_interface.bits_in_lau)
    add_text(elem, "endianness", indirect_interface.endianness)
    add_parameters(elem, indirect_interface.parameters)
    write_vendor_extensions(elem, indirect_interface.vendor_extensions)
    return elem


def add_indirect_interfaces(parent: etree._Element, indirect_interfaces: Sequence[IndirectInterface]) -> None:
    add_items(parent, "indirectInterfaces", indirect_interfaces, write_indirect_interface)


def write_channel(channel: Channel) -> etree._Element:
    elem = element("channel", xml_id=channel.xml_id)
    add_name_group(elem, channel)
    add_local_references(elem, "busInterfaceRef", channel.bus_interface_refs)
    write_vendor_extensions(elem, channel.vendor_extensions)
    return elem


def add_channels(parent: etree._Element, channels: Sequence[Channel]) -> None:
    add_items(parent, "channels", channels, write_channel)
