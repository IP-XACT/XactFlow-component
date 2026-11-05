from __future__ import annotations

from typing import Optional, Sequence

from lxml import etree

from ipxact.schema.ports import (
    ClockDriver,
    ConstraintSet,
    DomainTypeDef,
    Driver,
    FieldMap,
    Port,
    PortAccess,
    PowerConstraint,
    ServiceTypeDef,
    SignalTypeDef,
    SingleShotDriver,
    StructPortTypeDef,
    StructuredPort,
    SubPort,
    TransactionalPort,
    TransTypeDef,
    WirePort,
    WireTypeDef,
)

from .common_writer import (
    add_access_handles,
    add_array_bounds,
    add_clock_driver_body,
    add_drive_constraint,
    add_expression,
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
    add_text_value,
    add_text_values,
    add_timing_constraints,
    add_vectors,
    bool_str,
    element,
    sub,
    write_module_parameter,
    write_vendor_extensions,
)


def _add_clock_driver(parent: etree._Element, clock_driver: ClockDriver) -> None:
    elem = sub(parent, "clockDriver", xml_id=clock_driver.xml_id, clockName=clock_driver.clock_name)
    add_clock_driver_body(elem, clock_driver)


def _add_single_shot_driver(parent: etree._Element, single_shot: SingleShotDriver) -> None:
    elem = sub(parent, "singleShotDriver")
    add_expression(elem, "singleShotOffset", single_shot.single_shot_offset, units=single_shot.offset_units)
    add_expression(elem, "singleShotValue", single_shot.single_shot_value)
    add_expression(elem, "singleShotDuration", single_shot.single_shot_duration, units=single_shot.duration_units)


def _write_driver(driver: Driver) -> etree._Element:
    elem = element("driver", xml_id=driver.xml_id)
    has_value = driver.default_value is not None or driver.clock_driver is not None or driver.single_shot_driver is not None
    # driverType's content is optional as a whole (an empty <driver/> is legal), but once any
    # of it is used, the trailing value choice becomes required.
    if not has_value and driver.range is None and not driver.view_refs:
        return elem
    add_range(elem, driver.range)
    add_text_values(elem, "viewRef", driver.view_refs)
    # defaultValue, clockDriver and singleShotDriver are the three arms of that choice.
    if driver.default_value is not None:
        add_expression(elem, "defaultValue", driver.default_value)
    elif driver.clock_driver is not None:
        _add_clock_driver(elem, driver.clock_driver)
    elif driver.single_shot_driver is not None:
        _add_single_shot_driver(elem, driver.single_shot_driver)
    else:
        raise ValueError("a driver with range or view_refs requires default_value, clock_driver, or single_shot_driver")
    return elem


def _write_constraint_set(constraint_set: ConstraintSet) -> etree._Element:
    elem = element(
        "constraintSet",
        xml_id=constraint_set.xml_id,
        constraintSetId=constraint_set.constraint_set_id if constraint_set.constraint_set_id != "default" else None,
    )
    add_name_group(elem, constraint_set)
    if constraint_set.vector is not None:
        vector = sub(elem, "vector")
        add_expression(vector, "left", constraint_set.vector.left)
        add_expression(vector, "right", constraint_set.vector.right)
    add_drive_constraint(elem, constraint_set.drive_constraint)
    add_load_constraint(elem, constraint_set.load_constraint)
    add_timing_constraints(elem, constraint_set.timing_constraints)
    return elem


def _write_wire_type_def(type_def: WireTypeDef) -> etree._Element:
    elem = element("wireTypeDef", xml_id=type_def.xml_id)
    add_text(
        elem,
        "typeName",
        type_def.type_name,
        constrained=" ".join(type_def.type_name_constrained) if type_def.type_name_constrained else None,
    )
    add_text_values(elem, "typeDefinition", type_def.type_definitions)
    add_text_values(elem, "viewRef", type_def.view_refs)
    return elem


def _write_domain_type_def(type_def: DomainTypeDef) -> etree._Element:
    elem = element("domainTypeDef", xml_id=type_def.xml_id)
    add_text_value(elem, "typeName", type_def.type_name)
    add_text_values(elem, "typeDefinition", type_def.type_definitions)
    add_text_values(elem, "viewRef", type_def.view_refs)
    return elem


def _write_signal_type_def(type_def: SignalTypeDef) -> etree._Element:
    elem = element("signalTypeDef", xml_id=type_def.xml_id)
    sub(elem, "signalType", type_def.signal_type)
    add_text_values(elem, "viewRef", type_def.view_refs)
    return elem


def _write_power_constraint(constraint: PowerConstraint) -> etree._Element:
    elem = element("powerConstraint", xml_id=constraint.xml_id)
    sub(elem, "powerDomainRef", constraint.power_domain_ref)
    add_range(elem, constraint.range)
    write_vendor_extensions(elem, constraint.vendor_extensions)
    return elem


def add_wire_port(parent: etree._Element, wire: WirePort) -> None:
    elem = sub(
        parent,
        "wire",
        allLogicalDirectionsAllowed=bool_str(True) if wire.all_logical_directions_allowed else None,
    )
    sub(elem, "direction", wire.direction.value)
    add_qualifier(elem, wire.qualifier)
    add_vectors(elem, wire.vectors)
    add_items(elem, "wireTypeDefs", wire.wire_type_defs, _write_wire_type_def)
    add_items(elem, "domainTypeDefs", wire.domain_type_defs, _write_domain_type_def)
    add_items(elem, "signalTypeDefs", wire.signal_type_defs, _write_signal_type_def)
    add_items(elem, "drivers", wire.drivers, _write_driver)
    add_items(elem, "constraintSets", wire.constraint_sets, _write_constraint_set)
    add_items(elem, "powerConstraints", wire.power_constraints, _write_power_constraint)


def _add_type_parameters(
    parent: etree._Element, type_parameters: Sequence[object], service_type_defs: Sequence[ServiceTypeDef]
) -> None:
    """Write ipxact:typeParameters: typeParameter elements, then serviceTypeDef elements."""
    if not type_parameters and not service_type_defs:
        return
    container = sub(parent, "typeParameters")
    for type_parameter in type_parameters:
        container.append(write_module_parameter(type_parameter, tag="typeParameter"))
    for service_type_def in service_type_defs:
        container.append(_write_service_type_def(service_type_def))


def _write_service_type_def(type_def: ServiceTypeDef) -> etree._Element:
    elem = element("serviceTypeDef", xml_id=type_def.xml_id)
    sub(elem, "typeName", type_def.type_name, implicit=bool_str(True) if type_def.type_name_implicit else None)
    add_text_values(elem, "typeDefinition", type_def.type_definitions)
    _add_type_parameters(elem, type_def.type_parameters, type_def.service_type_defs)
    return elem


def _write_trans_type_def(type_def: TransTypeDef) -> etree._Element:
    elem = element("transTypeDef", xml_id=type_def.xml_id)
    add_text(elem, "typeName", type_def.type_name, exact=None if type_def.type_name_exact else bool_str(False))
    add_text_values(elem, "typeDefinition", type_def.type_definitions)
    _add_type_parameters(elem, type_def.type_parameters, type_def.service_type_defs)
    add_text_values(elem, "viewRef", type_def.view_refs)
    return elem


def add_transactional_port(parent: etree._Element, transactional: TransactionalPort) -> None:
    elem = sub(
        parent,
        "transactional",
        allLogicalInitiativesAllowed=bool_str(True) if transactional.all_logical_initiatives_allowed else None,
    )
    sub(elem, "initiative", transactional.initiative.value)
    add_text(elem, "kind", transactional.kind, custom=transactional.kind_custom)
    add_expression(elem, "busWidth", transactional.bus_width)
    add_qualifier(elem, transactional.qualifier)
    add_protocol(elem, transactional.protocol)
    add_items(elem, "transTypeDefs", transactional.trans_type_defs, _write_trans_type_def)
    if transactional.max_connections is not None or transactional.min_connections is not None:
        connection = sub(elem, "connection")
        add_expression(connection, "maxConnections", transactional.max_connections)
        add_expression(connection, "minConnections", transactional.min_connections)
    add_items(elem, "powerConstraints", transactional.power_constraints, _write_power_constraint)


def write_struct_port_type_def(type_def: StructPortTypeDef) -> etree._Element:
    elem = element("structPortTypeDef", xml_id=type_def.xml_id)
    sub(
        elem,
        "typeName",
        type_def.type_name,
        constrained=" ".join(type_def.constrained) if type_def.constrained else None,
    )
    add_text_values(elem, "typeDefinition", type_def.type_definitions)
    add_items(elem, "typeParameters", type_def.type_parameters, lambda p: write_module_parameter(p, tag="typeParameter"))
    add_text(elem, "role", type_def.role)
    add_text_values(elem, "viewRef", type_def.view_refs)
    return elem


def add_structured_port(parent: etree._Element, structured: StructuredPort) -> None:
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
    # structPortTypeDefs is required by portStructuredType; an empty struct_port_type_defs
    # here produces a document that fails validation rather than one this writer patches up.
    add_items(elem, "structPortTypeDefs", structured.struct_port_type_defs, write_struct_port_type_def)


def _add_port_access(parent: etree._Element, access: Optional[PortAccess]) -> None:
    if access is None:
        return
    elem = sub(parent, "access")
    add_text(elem, "portAccessType", access.port_access_type)
    add_access_handles(elem, access.access_handles)


def _add_sub_port(parent: etree._Element, sub_port: SubPort) -> None:
    elem = sub(
        parent,
        "subPort",
        xml_id=sub_port.xml_id,
        isIO=bool_str(sub_port.is_io) if sub_port.is_io is not None else None,
    )
    add_name_group(elem, sub_port)
    if sub_port.wire is not None:
        add_wire_port(elem, sub_port.wire)
    elif sub_port.structured is not None:
        add_structured_port(elem, sub_port.structured)
    else:
        raise ValueError("a sub port requires wire or structured")
    add_array_bounds(elem, sub_port.arrays)
    _add_port_access(elem, sub_port.access)
    write_vendor_extensions(elem, sub_port.vendor_extensions)


def _write_field_map(field_map: FieldMap) -> etree._Element:
    elem = element("fieldMap", xml_id=field_map.xml_id)
    add_field_reference_group(sub(elem, "fieldSlice"), field_map.field_slice, with_range=True)
    add_sub_port_references(elem, field_map.sub_port_refs)
    add_part_select(elem, field_map.part_select)
    add_mode_refs(elem, field_map.mode_refs)
    return elem


def write_port(port: Port) -> etree._Element:
    elem = element("port", xml_id=port.xml_id)
    add_name_group(elem, port)
    # wire, transactional and structured are the three arms of a required choice.
    if port.wire is not None:
        add_wire_port(elem, port.wire)
    elif port.transactional is not None:
        add_transactional_port(elem, port.transactional)
    elif port.structured is not None:
        add_structured_port(elem, port.structured)
    else:
        raise ValueError("a port requires wire, transactional, or structured")
    add_items(elem, "fieldMaps", port.field_maps, _write_field_map)
    add_array_bounds(elem, port.arrays)
    _add_port_access(elem, port.access)
    add_parameters(elem, port.parameters)
    write_vendor_extensions(elem, port.vendor_extensions)
    return elem


def add_ports(parent: etree._Element, ports: Sequence[Port]) -> None:
    add_items(parent, "ports", ports, write_port)
