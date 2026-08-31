"""Writer functions raise a clear error for objects that leave a required XSD choice or
sibling-field pair entirely unset, instead of silently emitting XML that only a schema
validator would catch later. Each test below reproduces one such gap found during review.
"""

from __future__ import annotations

import ipxact
import pytest

from xactflow_component import component_to_bytes


def _vlnv(name: str) -> ipxact.VLNV:
    return ipxact.VLNV("example.org", "ip", name, "1.0")


def _bus_type() -> ipxact.VLNVRef:
    return ipxact.VLNVRef("amba.com", "AMBA4", "APB4", "r0p0_0")


def test_field_slice_reference_without_address_block_ref_is_rejected():
    component = ipxact.Component(
        vlnv=_vlnv("bad-field-slice"),
        modes=[
            ipxact.Mode(
                name="turbo",
                field_slices=[
                    ipxact.FieldSlice(
                        name="fs0",
                        field_ref=ipxact.FieldReference(field_ref="EN", memory_map_ref="mm0"),
                    )
                ],
            )
        ],
    )
    with pytest.raises(ValueError, match="address_block_ref"):
        component_to_bytes(component)


def test_cell_specification_without_function_or_class_is_rejected():
    component = ipxact.Component(
        vlnv=_vlnv("bad-cell-spec"),
        model=ipxact.Model(
            ports=[
                ipxact.Port(
                    name="p",
                    wire=ipxact.WirePort(
                        direction=ipxact.Direction.OUT,
                        constraint_sets=[
                            ipxact.ConstraintSet(
                                drive_constraint=ipxact.DriveConstraint(cell=ipxact.CellSpecification())
                            )
                        ],
                    ),
                )
            ]
        ),
    )
    with pytest.raises(ValueError, match="cell_function or cell_class"):
        component_to_bytes(component)


def test_port_map_without_physical_port_or_tie_off_is_rejected():
    component = ipxact.Component(
        vlnv=_vlnv("bad-port-map"),
        bus_interfaces=[
            ipxact.BusInterface(
                name="apb",
                bus_type=_bus_type(),
                mode=ipxact.InterfaceMode.TARGET,
                abstraction_types=[
                    ipxact.AbstractionType(
                        abstraction_ref=_bus_type(),
                        port_maps=[ipxact.PortMap(logical_port="PSEL")],
                    )
                ],
            )
        ],
    )
    with pytest.raises(ValueError, match="physical_port or logical_tie_off"):
        component_to_bytes(component)


def test_mirrored_target_with_range_but_no_remap_addresses_is_rejected():
    component = ipxact.Component(
        vlnv=_vlnv("bad-mirrored-target"),
        bus_interfaces=[
            ipxact.BusInterface(
                name="mtgt0",
                bus_type=_bus_type(),
                mode=ipxact.InterfaceMode.MIRRORED_TARGET,
                mirrored_target=ipxact.MirroredTargetInterface(range="0x1000"),
            )
        ],
    )
    with pytest.raises(ValueError, match="remap_addresses and range"):
        component_to_bytes(component)


def test_system_mode_without_system_payload_is_rejected():
    component = ipxact.Component(
        vlnv=_vlnv("bad-system-mode"),
        bus_interfaces=[
            ipxact.BusInterface(
                name="sys0",
                bus_type=_bus_type(),
                mode=ipxact.InterfaceMode.SYSTEM,
                system=None,
            )
        ],
    )
    with pytest.raises(ValueError, match="SYSTEM"):
        component_to_bytes(component)


def test_monitor_mode_without_monitor_payload_is_rejected():
    component = ipxact.Component(
        vlnv=_vlnv("bad-monitor-mode"),
        bus_interfaces=[
            ipxact.BusInterface(
                name="mon0",
                bus_type=_bus_type(),
                mode=ipxact.InterfaceMode.MONITOR,
                monitor=None,
            )
        ],
    )
    with pytest.raises(ValueError, match="MONITOR"):
        component_to_bytes(component)


def test_indirect_interface_without_memory_map_ref_or_bridges_is_rejected():
    component = ipxact.Component(
        vlnv=_vlnv("bad-indirect"),
        indirect_interfaces=[
            ipxact.IndirectInterface(
                name="ind0",
                indirect_address_ref=ipxact.FieldReference(field_ref="ADDR"),
                indirect_data_ref=ipxact.FieldReference(field_ref="DATA"),
            )
        ],
    )
    with pytest.raises(ValueError, match="memory_map_ref or transparent_bridges"):
        component_to_bytes(component)


def test_port_without_wire_transactional_or_structured_is_rejected():
    component = ipxact.Component(
        vlnv=_vlnv("bad-port"),
        model=ipxact.Model(ports=[ipxact.Port(name="clk_in")]),
    )
    with pytest.raises(ValueError, match="wire, transactional, or structured"):
        component_to_bytes(component)


def test_driver_with_range_but_no_value_is_rejected():
    component = ipxact.Component(
        vlnv=_vlnv("bad-driver"),
        model=ipxact.Model(
            ports=[
                ipxact.Port(
                    name="p",
                    wire=ipxact.WirePort(
                        direction=ipxact.Direction.OUT,
                        drivers=[ipxact.Driver(range_left="7", range_right="0")],
                    ),
                )
            ]
        ),
    )
    with pytest.raises(ValueError, match="default_value, clock_driver, or single_shot_driver"):
        component_to_bytes(component)


def _component_with_write_value_constraint(constraint: ipxact.WriteValueConstraint) -> ipxact.Component:
    return ipxact.Component(
        vlnv=_vlnv("bad-write-value-constraint"),
        memory_maps=[
            ipxact.MemoryMap(
                name="mm",
                items=[
                    ipxact.AddressBlock(
                        name="block",
                        range="0x10",
                        width="32",
                        base_address="0x0",
                        registers=[
                            ipxact.Register(
                                name="R",
                                address_offset="0x0",
                                size="32",
                                fields=[
                                    ipxact.Field(
                                        name="F",
                                        bit_offset="0",
                                        bit_width="1",
                                        field_access_policies=[
                                            ipxact.FieldAccessPolicy(write_value_constraint=constraint)
                                        ],
                                    )
                                ],
                            )
                        ],
                    )
                ],
            )
        ],
    )


def test_write_value_constraint_with_no_arm_set_is_rejected():
    component = _component_with_write_value_constraint(ipxact.WriteValueConstraint())
    with pytest.raises(ValueError, match="write_as_read, use_enumerated_values"):
        component_to_bytes(component)


def test_write_value_constraint_with_only_minimum_is_rejected():
    component = _component_with_write_value_constraint(ipxact.WriteValueConstraint(minimum="0"))
    with pytest.raises(ValueError, match="write_as_read, use_enumerated_values"):
        component_to_bytes(component)
