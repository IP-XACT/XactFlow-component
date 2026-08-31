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
    MirroredTargetInterface,
    MonitorInterface,
    PortMap,
    SystemInterface,
    TargetInterface,
    TransparentBridge,
)

from .common_writer import (
    add_field_reference_group,
    add_items,
    add_local_name_refs,
    add_mode_refs,
    add_name_group,
    add_parameters,
    add_text,
    add_texts,
    bool_str,
    element,
    sub,
    write_vendor_extensions,
    write_vlnv_ref,
)


def _add_transparent_bridges(parent: etree._Element, bridges: Sequence[TransparentBridge]) -> None:
    for bridge in bridges:
        sub(parent, "transparentBridge", initiatorRef=bridge.initiator_ref)


def _add_port_map(parent: etree._Element, port_map: PortMap) -> None:
    elem = sub(parent, "portMap", invert=bool_str(True) if port_map.invert else None)
    logical_port = sub(elem, "logicalPort")
    sub(logical_port, "name", port_map.logical_port)
    # physicalPort and logicalTieOff are the two arms of a required choice.
    if port_map.physical_port is not None:
        physical_port = sub(elem, "physicalPort")
        sub(physical_port, "name", port_map.physical_port)
    elif port_map.logical_tie_off is not None:
        sub(elem, "logicalTieOff", port_map.logical_tie_off)
    else:
        raise ValueError("a port map requires physical_port or logical_tie_off")
    if port_map.is_informative:
        sub(elem, "isInformative", bool_str(True))


def _add_abstraction_type(parent: etree._Element, abstraction_type: AbstractionType) -> None:
    elem = sub(parent, "abstractionType")
    add_texts(elem, "viewRef", abstraction_type.view_refs)
    elem.append(write_vlnv_ref("abstractionRef", abstraction_type.abstraction_ref))
    if abstraction_type.port_maps:
        port_maps = sub(elem, "portMaps")
        for port_map in abstraction_type.port_maps:
            _add_port_map(port_maps, port_map)


def _add_initiator(parent: etree._Element, initiator: InitiatorInterface) -> None:
    elem = sub(parent, "initiator")
    if initiator.address_space_ref is None:
        return
    ref_elem = sub(elem, "addressSpaceRef", addressSpaceRef=initiator.address_space_ref)
    add_text(ref_elem, "baseAddress", initiator.base_address)
    add_mode_refs(ref_elem, initiator.mode_refs, with_priority=False)


def _add_target(parent: etree._Element, target: TargetInterface) -> None:
    elem = sub(parent, "target")
    # memoryMapRef and transparentBridge are the two arms of an optional choice.
    if target.memory_map_ref is not None:
        sub(elem, "memoryMapRef", memoryMapRef=target.memory_map_ref)
    else:
        _add_transparent_bridges(elem, target.transparent_bridges)
    for group in target.file_set_ref_groups:
        group_elem = sub(elem, "fileSetRefGroup")
        add_text(group_elem, "group", group.group)
        add_local_name_refs(group_elem, "fileSetRef", group.file_set_refs)


def _add_mirrored_target(parent: etree._Element, mirrored_target: MirroredTargetInterface) -> None:
    elem = sub(parent, "mirroredTarget")
    if not mirrored_target.remap_addresses and mirrored_target.range is None:
        return
    if not mirrored_target.remap_addresses or mirrored_target.range is None:
        raise ValueError("a mirrored target's base addresses require both remap_addresses and range")
    base_addresses = sub(elem, "baseAddresses")
    for remap_address in mirrored_target.remap_addresses:
        remap_elem = sub(base_addresses, "remapAddresses")
        sub(remap_elem, "remapAddress", remap_address.value)
        add_mode_refs(remap_elem, remap_address.mode_refs)
    add_text(base_addresses, "range", mirrored_target.range)


def _add_system(parent: etree._Element, tag: str, system: SystemInterface) -> None:
    sub(sub(parent, tag), "group", system.group)


def _add_monitor(parent: etree._Element, monitor: MonitorInterface) -> None:
    elem = sub(parent, "monitor", interfaceMode=monitor.interface_mode.value)
    add_text(elem, "group", monitor.group)


def _add_interface_mode(parent: etree._Element, bus_interface: BusInterface) -> None:
    mode = bus_interface.mode
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
        sub(parent, "mirroredInitiator")
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
    elem = element("busInterface")
    add_name_group(elem, bus_interface.name, bus_interface.display_name, description=bus_interface.description)
    elem.append(write_vlnv_ref("busType", bus_interface.bus_type))
    if bus_interface.abstraction_types:
        abstraction_types = sub(elem, "abstractionTypes")
        for abstraction_type in bus_interface.abstraction_types:
            _add_abstraction_type(abstraction_types, abstraction_type)
    _add_interface_mode(elem, bus_interface)
    if bus_interface.connection_required:
        sub(elem, "connectionRequired", bool_str(True))
    add_text(elem, "bitsInLau", bus_interface.bits_in_lau)
    add_text(elem, "bitSteering", bus_interface.bit_steering)
    add_text(elem, "endianness", bus_interface.endianness)
    add_parameters(elem, bus_interface.parameters)
    write_vendor_extensions(elem, bus_interface.vendor_extensions)
    return elem


def add_bus_interfaces(parent: etree._Element, bus_interfaces: Sequence[BusInterface]) -> None:
    add_items(parent, "busInterfaces", bus_interfaces, write_bus_interface)


def write_indirect_interface(indirect_interface: IndirectInterface) -> etree._Element:
    elem = element("indirectInterface")
    add_name_group(
        elem,
        indirect_interface.name,
        indirect_interface.display_name,
        description=indirect_interface.description,
    )
    add_field_reference_group(sub(elem, "indirectAddressRef"), indirect_interface.indirect_address_ref)
    add_field_reference_group(sub(elem, "indirectDataRef"), indirect_interface.indirect_data_ref)
    # memoryMapRef and transparentBridge are the two arms of a required choice.
    if indirect_interface.memory_map_ref is not None:
        sub(elem, "memoryMapRef", indirect_interface.memory_map_ref)
    elif indirect_interface.transparent_bridges:
        _add_transparent_bridges(elem, indirect_interface.transparent_bridges)
    else:
        raise ValueError("an indirect interface requires memory_map_ref or transparent_bridges")
    add_text(elem, "bitsInLau", indirect_interface.bits_in_lau)
    add_text(elem, "endianness", indirect_interface.endianness)
    add_parameters(elem, indirect_interface.parameters)
    write_vendor_extensions(elem, indirect_interface.vendor_extensions)
    return elem


def add_indirect_interfaces(parent: etree._Element, indirect_interfaces: Sequence[IndirectInterface]) -> None:
    add_items(parent, "indirectInterfaces", indirect_interfaces, write_indirect_interface)


def write_channel(channel: Channel) -> etree._Element:
    elem = element("channel")
    add_name_group(elem, channel.name, channel.display_name, description=channel.description)
    add_local_name_refs(elem, "busInterfaceRef", channel.bus_interface_refs)
    write_vendor_extensions(elem, channel.vendor_extensions)
    return elem


def add_channels(parent: etree._Element, channels: Sequence[Channel]) -> None:
    add_items(parent, "channels", channels, write_channel)
