from __future__ import annotations

from typing import Sequence

from lxml import etree

from ipxact.schema.ports import (
    ClockDriver,
    ConstraintSet,
    Driver,
    FieldMap,
    Port,
    SingleShotDriver,
    StructuredPort,
    SubPort,
    TransactionalPort,
    WirePort,
)

from .common_writer import (
    add_clock_driver_body,
    add_drive_constraint,
    add_field_reference_group,
    add_items,
    add_load_constraint,
    add_mode_refs,
    add_name_group,
    add_parameters,
    add_part_select,
    add_protocol,
    add_qualifier,
    add_range,
    add_sub_port_references,
    add_text,
    add_texts,
    add_timing_constraints,
    add_vectors,
    bool_str,
    element,
    sub,
    write_vendor_extensions,
)


def _add_clock_driver(parent: etree._Element, clock_driver: ClockDriver) -> None:
    add_clock_driver_body(sub(parent, "clockDriver", clockName=clock_driver.clock_name), clock_driver)


def _add_single_shot_driver(parent: etree._Element, single_shot: SingleShotDriver) -> None:
    elem = sub(parent, "singleShotDriver")
    sub(elem, "singleShotOffset", single_shot.single_shot_offset, units=single_shot.offset_units)
    sub(elem, "singleShotValue", single_shot.single_shot_value)
    sub(elem, "singleShotDuration", single_shot.single_shot_duration, units=single_shot.duration_units)


def _add_driver(parent: etree._Element, driver: Driver) -> None:
    elem = sub(parent, "driver")
    has_value = driver.default_value is not None or driver.clock_driver is not None or driver.single_shot_driver is not None
    # driverType's content is optional as a whole (an empty <driver/> is legal), but once any
    # of it is used, the trailing value choice becomes required.
    if not has_value and driver.range_left is None and driver.range_right is None and not driver.view_refs:
        return
    add_range(elem, driver.range_left, driver.range_right)
    add_texts(elem, "viewRef", driver.view_refs)
    # defaultValue, clockDriver and singleShotDriver are the three arms of that choice.
    if driver.default_value is not None:
        sub(elem, "defaultValue", driver.default_value)
    elif driver.clock_driver is not None:
        _add_clock_driver(elem, driver.clock_driver)
    elif driver.single_shot_driver is not None:
        _add_single_shot_driver(elem, driver.single_shot_driver)
    else:
        raise ValueError("a driver with range or view_refs requires default_value, clock_driver, or single_shot_driver")


def _add_constraint_set(parent: etree._Element, constraint_set: ConstraintSet) -> None:
    elem = sub(
        parent,
        "constraintSet",
        constraintSetId=constraint_set.constraint_set_id if constraint_set.constraint_set_id != "default" else None,
    )
    add_name_group(elem, constraint_set.name)
    if constraint_set.vector_left is not None or constraint_set.vector_right is not None:
        vector = sub(elem, "vector")
        add_text(vector, "left", constraint_set.vector_left)
        add_text(vector, "right", constraint_set.vector_right)
    add_drive_constraint(elem, constraint_set.drive_constraint)
    add_load_constraint(elem, constraint_set.load_constraint)
    add_timing_constraints(elem, constraint_set.timing_constraints)


def add_wire_port(parent: etree._Element, wire: WirePort) -> None:
    elem = sub(
        parent,
        "wire",
        allLogicalDirectionsAllowed=bool_str(True) if wire.all_logical_directions_allowed else None,
    )
    sub(elem, "direction", wire.direction.value)
    add_qualifier(elem, wire.qualifier)
    add_vectors(elem, wire.vectors)
    if wire.drivers:
        drivers = sub(elem, "drivers")
        for driver in wire.drivers:
            _add_driver(drivers, driver)
    if wire.constraint_sets:
        constraint_sets = sub(elem, "constraintSets")
        for constraint_set in wire.constraint_sets:
            _add_constraint_set(constraint_sets, constraint_set)


def add_transactional_port(parent: etree._Element, transactional: TransactionalPort) -> None:
    elem = sub(
        parent,
        "transactional",
        allLogicalInitiativesAllowed=bool_str(True) if transactional.all_logical_initiatives_allowed else None,
    )
    sub(elem, "initiative", transactional.initiative.value)
    add_text(elem, "kind", transactional.kind)
    add_text(elem, "busWidth", transactional.bus_width)
    add_qualifier(elem, transactional.qualifier)
    add_protocol(elem, transactional.protocol)
    if transactional.max_connections is not None or transactional.min_connections is not None:
        connection = sub(elem, "connection")
        add_text(connection, "maxConnections", transactional.max_connections)
        add_text(connection, "minConnections", transactional.min_connections)


def add_structured_port(parent: etree._Element, structured: StructuredPort) -> None:
    """Write ipxact:structured.

    portStructuredType also requires a structPortTypeDefs child, which ipxact-compiler
    deliberately does not model (language-specific type bindings are out of its scope), so
    structured ports round-trip faithfully but do not satisfy the XSD on their own.
    """
    elem = sub(parent, "structured", packed=None if structured.packed else bool_str(False))
    if structured.struct_type == "interface":
        sub(
            elem,
            "interface",
            phantom=bool_str(structured.phantom) if structured.phantom is not None else None,
        )
    else:
        sub(
            elem,
            structured.struct_type,
            direction=structured.direction.value if structured.direction is not None else None,
        )
    add_vectors(elem, structured.vectors)
    if structured.sub_ports:
        sub_ports = sub(elem, "subPorts")
        for sub_port in structured.sub_ports:
            _add_sub_port(sub_ports, sub_port)


def _add_sub_port(parent: etree._Element, sub_port: SubPort) -> None:
    elem = sub(
        parent,
        "subPort",
        isIO=bool_str(sub_port.is_io) if sub_port.is_io is not None else None,
    )
    add_name_group(elem, sub_port.name, sub_port.display_name, description=sub_port.description)
    if sub_port.wire is not None:
        add_wire_port(elem, sub_port.wire)
    elif sub_port.structured is not None:
        add_structured_port(elem, sub_port.structured)


def _add_field_map(parent: etree._Element, field_map: FieldMap) -> None:
    elem = sub(parent, "fieldMap")
    add_field_reference_group(sub(elem, "fieldSlice"), field_map.field_slice, with_range=True)
    add_sub_port_references(elem, field_map.sub_port_refs)
    add_part_select(elem, field_map.part_select)
    add_mode_refs(elem, field_map.mode_refs)


def write_port(port: Port) -> etree._Element:
    elem = element("port")
    add_name_group(elem, port.name, port.display_name, description=port.description)
    # wire, transactional and structured are the three arms of a required choice.
    if port.wire is not None:
        add_wire_port(elem, port.wire)
    elif port.transactional is not None:
        add_transactional_port(elem, port.transactional)
    elif port.structured is not None:
        add_structured_port(elem, port.structured)
    else:
        raise ValueError("a port requires wire, transactional, or structured")
    if port.field_maps:
        field_maps = sub(elem, "fieldMaps")
        for field_map in port.field_maps:
            _add_field_map(field_maps, field_map)
    add_parameters(elem, port.parameters)
    write_vendor_extensions(elem, port.vendor_extensions)
    return elem


def add_ports(parent: etree._Element, ports: Sequence[Port]) -> None:
    add_items(parent, "ports", ports, write_port)
