"""Writer functions raise a clear error for objects that leave a required XSD choice or
sibling-field pair entirely unset, instead of silently emitting XML that only a schema
validator would catch later, and for objects that set more than one arm of a choice, instead of
silently dropping all but one. Each test below reproduces one such gap found during review.
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
                        field_ref=ipxact.FieldReference(field_ref=ipxact.IndexedRef("EN"), memory_map_ref="mm0"),
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
                mirrored_target=ipxact.MirroredTargetInterface(range=ipxact.Expression("0x1000")),
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
                indirect_address_ref=ipxact.FieldReference(field_ref=ipxact.IndexedRef("ADDR")),
                indirect_data_ref=ipxact.FieldReference(field_ref=ipxact.IndexedRef("DATA")),
            )
        ],
    )
    with pytest.raises(ValueError, match="memory_map_ref or transparent_bridges"):
        component_to_bytes(component)


def test_sub_port_without_wire_or_structured_is_rejected():
    component = ipxact.Component(
        vlnv=_vlnv("bad-sub-port"),
        model=ipxact.Model(
            ports=[
                ipxact.Port(
                    name="bus",
                    structured=ipxact.StructuredPort(
                        struct_type="struct",
                        sub_ports=[ipxact.SubPort(name="valid")],
                        struct_port_type_defs=[ipxact.StructPortTypeDef(type_name="bus_req_t")],
                        direction=ipxact.Direction.OUT,
                    ),
                )
            ]
        ),
    )
    with pytest.raises(ValueError, match="wire or structured"):
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
                        drivers=[ipxact.Driver(range=ipxact.Range(ipxact.Expression("7"), ipxact.Expression("0")))],
                    ),
                )
            ]
        ),
    )
    with pytest.raises(ValueError, match="default_value, clock_driver, or single_shot_driver"):
        component_to_bytes(component)


def _component_with_field(field: ipxact.Field) -> ipxact.Component:
    return ipxact.Component(
        vlnv=_vlnv("bad-field"),
        memory_maps=[
            ipxact.MemoryMap(
                name="mm",
                items=[
                    ipxact.AddressBlock(
                        name="block",
                        range=ipxact.Expression("0x10"),
                        width=ipxact.Expression("32"),
                        base_address=ipxact.Expression("0x0"),
                        registers=[ipxact.Register(name="R", address_offset=ipxact.Expression("0x0"), size=ipxact.Expression("32"), fields=[field])],
                    )
                ],
            )
        ],
    )


def _component_with_write_value_constraint(constraint: ipxact.WriteValueConstraint) -> ipxact.Component:
    return _component_with_field(
        ipxact.Field(
            name="F",
            bit_offset=ipxact.Expression("0"),
            bit_width=ipxact.Expression("1"),
            field_access_policies=[ipxact.FieldAccessPolicy(write_value_constraint=constraint)],
        )
    )


def test_write_value_constraint_with_no_arm_set_is_rejected():
    component = _component_with_write_value_constraint(ipxact.WriteValueConstraint())
    with pytest.raises(ValueError, match="write_as_read, use_enumerated_values"):
        component_to_bytes(component)


def test_write_value_constraint_with_only_minimum_is_rejected():
    component = _component_with_write_value_constraint(ipxact.WriteValueConstraint(minimum=ipxact.Expression("0")))
    with pytest.raises(ValueError, match="write_as_read, use_enumerated_values"):
        component_to_bytes(component)


def test_field_without_bit_width_alias_or_definition_ref_is_rejected():
    component = _component_with_field(ipxact.Field(name="F", bit_offset=ipxact.Expression("0")))
    with pytest.raises(ValueError, match="bit_width, alias_of or field_definition_ref"):
        component_to_bytes(component)


def _component_with_port(port: ipxact.Port) -> ipxact.Component:
    return ipxact.Component(vlnv=_vlnv("bad-port"), model=ipxact.Model(ports=[port]))


def _wire_with_driver(driver: ipxact.Driver) -> ipxact.WirePort:
    return ipxact.WirePort(direction=ipxact.Direction.OUT, drivers=[driver])


def test_port_with_two_types_is_rejected():
    port = ipxact.Port(
        name="p",
        wire=ipxact.WirePort(direction=ipxact.Direction.IN),
        transactional=ipxact.TransactionalPort(initiative=ipxact.Initiative.PROVIDES),
    )
    with pytest.raises(ValueError, match="sets wire and transactional"):
        component_to_bytes(_component_with_port(port))


def test_sub_port_with_wire_and_structured_is_rejected():
    port = ipxact.Port(
        name="bus",
        structured=ipxact.StructuredPort(
            struct_type="struct",
            sub_ports=[
                ipxact.SubPort(
                    name="valid",
                    wire=ipxact.WirePort(direction=ipxact.Direction.OUT),
                    structured=ipxact.StructuredPort(struct_type="struct"),
                )
            ],
            struct_port_type_defs=[ipxact.StructPortTypeDef(type_name="bus_req_t")],
            direction=ipxact.Direction.OUT,
        ),
    )
    with pytest.raises(ValueError, match="sets wire and structured"):
        component_to_bytes(_component_with_port(port))


def test_driver_with_two_values_is_rejected():
    clock = ipxact.ClockDriver(
        clock_period=ipxact.Expression("10"),
        clock_pulse_offset=ipxact.Expression("0"),
        clock_pulse_value=ipxact.Expression("1"),
        clock_pulse_duration=ipxact.Expression("5"),
    )
    driver = ipxact.Driver(default_value=ipxact.Expression("0"), clock_driver=clock)
    port = ipxact.Port(name="p", wire=_wire_with_driver(driver))
    with pytest.raises(ValueError, match="sets default_value and clock_driver"):
        component_to_bytes(_component_with_port(port))


def test_cell_specification_with_function_and_class_is_rejected():
    cell = ipxact.CellSpecification(cell_function="nand2", cell_class="combinational")
    port = ipxact.Port(
        name="p",
        wire=ipxact.WirePort(
            direction=ipxact.Direction.OUT,
            constraint_sets=[ipxact.ConstraintSet(drive_constraint=ipxact.DriveConstraint(cell=cell))],
        ),
    )
    with pytest.raises(ValueError, match="sets cell_function and cell_class"):
        component_to_bytes(_component_with_port(port))


def test_target_with_memory_map_ref_and_bridges_is_rejected():
    component = ipxact.Component(
        vlnv=_vlnv("bad-target"),
        bus_interfaces=[
            ipxact.BusInterface(
                name="apb",
                bus_type=_bus_type(),
                mode=ipxact.InterfaceMode.TARGET,
                target=ipxact.TargetInterface(
                    memory_map_ref="mm0", transparent_bridges=[ipxact.TransparentBridge(initiator_ref="init0")]
                ),
            )
        ],
    )
    with pytest.raises(ValueError, match="sets memory_map_ref and transparent_bridges"):
        component_to_bytes(component)


def test_bus_interface_with_a_second_mode_is_rejected():
    component = ipxact.Component(
        vlnv=_vlnv("bad-mode"),
        bus_interfaces=[
            ipxact.BusInterface(
                name="apb",
                bus_type=_bus_type(),
                mode=ipxact.InterfaceMode.TARGET,
                initiator=ipxact.InitiatorInterface(address_space_ref="as0"),
            )
        ],
    )
    with pytest.raises(ValueError, match="mode TARGET but also sets initiator"):
        component_to_bytes(component)


def test_field_reference_with_address_space_and_memory_map_is_rejected():
    component = ipxact.Component(
        vlnv=_vlnv("bad-field-reference"),
        modes=[
            ipxact.Mode(
                name="turbo",
                field_slices=[
                    ipxact.FieldSlice(
                        name="fs0",
                        field_ref=ipxact.FieldReference(
                            address_space_ref="as0",
                            memory_map_ref="mm0",
                            address_block_ref=ipxact.IndexedRef("block"),
                            register_ref=ipxact.IndexedRef("R"),
                            field_ref=ipxact.IndexedRef("EN"),
                        ),
                    )
                ],
            )
        ],
    )
    with pytest.raises(ValueError, match="sets address_space_ref and memory_map_ref"):
        component_to_bytes(component)


def test_write_value_constraint_with_two_arms_is_rejected():
    constraint = ipxact.WriteValueConstraint(
        write_as_read=True, minimum=ipxact.Expression("0"), maximum=ipxact.Expression("1")
    )
    with pytest.raises(ValueError, match="sets write_as_read and minimum, maximum"):
        component_to_bytes(_component_with_write_value_constraint(constraint))


def test_field_with_bit_width_and_alias_of_is_rejected():
    field = ipxact.Field(
        name="F",
        bit_offset=ipxact.Expression("0"),
        bit_width=ipxact.Expression("1"),
        alias_of=ipxact.FieldReference(field_ref=ipxact.IndexedRef("G")),
    )
    with pytest.raises(ValueError, match="sets bit_width and alias_of"):
        component_to_bytes(_component_with_field(field))


def test_field_with_definition_ref_and_inline_content_is_rejected():
    field = ipxact.Field(
        name="F",
        bit_offset=ipxact.Expression("0"),
        bit_width=ipxact.Expression("1"),
        field_definition_ref=ipxact.DefinitionRef(name="f_def", type_definitions="defs"),
    )
    with pytest.raises(ValueError, match="sets field_definition_ref and bit_width"):
        component_to_bytes(_component_with_field(field))
