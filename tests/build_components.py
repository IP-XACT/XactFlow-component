"""Hand-built ipxact.Component objects used by the writer tests.

These are built directly rather than parsed from XML, so they exercise fields the
apb_uart.xml fixture does not reach.
"""

from __future__ import annotations

import ipxact

# ipxact-compiler serializes each vendorExtensions child with the namespace declarations that
# are in scope at that point, so an extension read back out of a component always carries the
# ipxact declaration too. Spelling it out here keeps round-trip comparison exact.
VENDOR_EXTENSION = (
    '<vendor:note xmlns:vendor="http://example.org/vendor"'
    ' xmlns:ipxact="http://www.accellera.org/XMLSchema/IPXACT/1685-2022">kept verbatim</vendor:note>'
)


def _normal_mode_ref(priority: int = 0) -> ipxact.ModeRef:
    return ipxact.ModeRef(name="normal", priority=priority)


def _ctrl_field() -> ipxact.Field:
    return ipxact.Field(
        name="ENABLE",
        bit_offset="0",
        bit_width="1",
        array=ipxact.MemoryArray(dims=[ipxact.ArrayDim(size="2", index_var="i")], stride="1"),
        volatile=True,
        resets=[ipxact.Reset(value="0", mask="1", reset_type_ref="HARD")],
        field_access_policies=[
            ipxact.FieldAccessPolicy(
                mode_refs=[_normal_mode_ref()],
                access=ipxact.AccessType.READ_WRITE,
                modified_write_value=ipxact.ModifiedWriteValue.ONE_TO_CLEAR,
                write_value_constraint=ipxact.WriteValueConstraint(minimum="0", maximum="1"),
                read_action=ipxact.ReadAction.CLEAR,
                read_response="0",
                broadcast_to=["ENABLE"],
                access_restrictions=[
                    ipxact.AccessRestriction(
                        mode_refs=[_normal_mode_ref()],
                        read_access_mask="1",
                        write_access_mask="1",
                    )
                ],
                testable=True,
                test_constraint=ipxact.TestConstraint.WRITE_AS_READ,
                reserved="0",
            )
        ],
        enumerated_values=[
            ipxact.EnumeratedValue(name="OFF", value="0", usage="read", display_name="Off", description="disabled"),
            ipxact.EnumeratedValue(name="ON", value="1"),
        ],
        display_name="Enable",
        description="Enables the block",
        parameters=[ipxact.Parameter(name="FIELD_P", value="1", parameter_id="FIELD_P")],
        vendor_extensions=[VENDOR_EXTENSION],
    )


def _regs_block() -> ipxact.AddressBlock:
    return ipxact.AddressBlock(
        name="regs",
        range="0x100",
        width="32",
        base_address="0x0",
        usage=ipxact.UsageType.REGISTER,
        volatile=False,
        access_policies=[
            ipxact.AccessPolicy(mode_refs=[_normal_mode_ref()], access=ipxact.AccessType.READ_WRITE)
        ],
        registers=[
            ipxact.Register(
                name="CTRL",
                address_offset="0x0",
                size="32",
                array=ipxact.MemoryArray(dims=[ipxact.ArrayDim(size="4")]),
                volatile=True,
                access_policies=[
                    ipxact.AccessPolicy(mode_refs=[_normal_mode_ref()], access=ipxact.AccessType.READ_WRITE)
                ],
                fields=[_ctrl_field()],
                alternate_registers=[
                    ipxact.AlternateRegister(
                        name="CTRL_ALT",
                        mode_refs=[_normal_mode_ref()],
                        volatile=False,
                        access_policies=[ipxact.AccessPolicy(access=ipxact.AccessType.READ_ONLY)],
                        fields=[ipxact.Field(name="ALT_BIT", bit_offset="0", bit_width="1")],
                        display_name="Alternate CTRL",
                        description="mode-selected layout",
                        parameters=[ipxact.Parameter(name="ALT_P", value="0", parameter_id="ALT_P")],
                    )
                ],
                display_name="Control",
                description="Control register",
                parameters=[ipxact.Parameter(name="CTRL_P", value="2", parameter_id="CTRL_P")],
            ),
            ipxact.RegisterFile(
                name="RF",
                address_offset="0x40",
                range="0x40",
                array=ipxact.MemoryArray(dims=[ipxact.ArrayDim(size="2")]),
                access_policies=[ipxact.AccessPolicy(access=ipxact.AccessType.READ_ONLY)],
                registers=[
                    ipxact.Register(
                        name="STATUS",
                        address_offset="0x0",
                        size="32",
                        fields=[ipxact.Field(name="BUSY", bit_offset="0", bit_width="1")],
                    )
                ],
                display_name="Register file",
                description="nested registers",
                parameters=[ipxact.Parameter(name="RF_P", value="3", parameter_id="RF_P")],
            ),
        ],
        misalignment_allowed=False,
        display_name="Registers",
        description="Register block",
        parameters=[ipxact.Parameter(name="BLOCK_P", value="4", parameter_id="BLOCK_P")],
        vendor_extensions=[VENDOR_EXTENSION],
    )


def _model() -> ipxact.Model:
    return ipxact.Model(
        views=[
            ipxact.View(
                name="rtl",
                env_identifiers=["::simulation", "verilog:*:*"],
                component_instantiation_ref="rtl_impl",
                vendor_extensions=[VENDOR_EXTENSION],
            ),
            ipxact.View(
                name="hier",
                design_instantiation_ref="hier_design",
                design_configuration_instantiation_ref="hier_config",
            ),
        ],
        component_instantiations=[
            ipxact.ComponentInstantiation(
                name="rtl_impl",
                is_virtual=True,
                language="systemverilog",
                library_name="work",
                package_name="pkg",
                module_name="wide_coverage",
                architecture_name="rtl",
                configuration_name="cfg",
                module_parameters=[
                    ipxact.ModuleParameter(
                        name="WIDTH",
                        value="8",
                        parameter_id="WIDTH",
                        display_name="Width",
                        description="bus width",
                        arrays=[ipxact.ArrayBound(left="1", right="0", array_id="ARR0")],
                        data_type="integer",
                        usage_type="runtime",
                        data_type_definition="pkg",
                        constrained=["low", "high"],
                    )
                ],
                default_file_builders=[
                    ipxact.FileBuilderOverride(
                        file_type="systemVerilogSource",
                        command="vlog",
                        flags="-sv",
                        replace_default_flags="0",
                    )
                ],
                file_set_refs=["rtl_files"],
                constraint_set_refs=["cs0"],
                parameters=[ipxact.Parameter(name="INST_P", value="1", parameter_id="INST_P")],
            )
        ],
        design_instantiations=[
            ipxact.DesignInstantiation(
                name="hier_design",
                design_ref=ipxact.VLNVRef("example.org", "ip", "wide_coverage_design", "2.0"),
            )
        ],
        design_configuration_instantiations=[
            ipxact.DesignConfigurationInstantiation(
                name="hier_config",
                design_configuration_ref=ipxact.VLNVRef("example.org", "ip", "wide_coverage_cfg", "2.0"),
                language="systemverilog",
                parameters=[ipxact.Parameter(name="CFG_P", value="0", parameter_id="CFG_P")],
            )
        ],
        ports=[
            ipxact.Port(
                name="clk",
                wire=ipxact.WirePort(
                    direction=ipxact.Direction.IN,
                    qualifier=ipxact.Qualifier(is_clock=True),
                    drivers=[ipxact.Driver(default_value="0", view_refs=["rtl"])],
                ),
                display_name="Clock",
                description="the clock",
            ),
            ipxact.Port(
                name="rst_n",
                wire=ipxact.WirePort(
                    direction=ipxact.Direction.IN,
                    qualifier=ipxact.Qualifier(is_reset=ipxact.LevelFlag(value=True, level="low")),
                    drivers=[
                        ipxact.Driver(
                            single_shot_driver=ipxact.SingleShotDriver(
                                single_shot_offset="0",
                                single_shot_value="1",
                                single_shot_duration="10",
                                offset_units="ps",
                                duration_units="ps",
                            )
                        )
                    ],
                ),
            ),
            ipxact.Port(
                name="pwr_en",
                wire=ipxact.WirePort(
                    direction=ipxact.Direction.IN,
                    qualifier=ipxact.Qualifier(
                        is_power_en=ipxact.LevelFlag(value=True, level="high", power_domain_ref="PD_MAIN"),
                        is_clock_en=ipxact.LevelFlag(value=False, level="low"),
                        is_flow_control=ipxact.FlowControlFlag(value=True, flow_type="user", user="credit"),
                        is_user=ipxact.UserFlag(value=True, user="tag"),
                        is_address=False,
                        is_data=True,
                        is_valid=True,
                        is_interrupt=False,
                        is_opcode=False,
                        is_protection=True,
                        is_request=True,
                        is_response=False,
                    ),
                ),
            ),
            ipxact.Port(
                name="data",
                wire=ipxact.WirePort(
                    direction=ipxact.Direction.OUT,
                    vectors=[ipxact.Vector(left="31", right="0", vector_id="V0")],
                    drivers=[
                        ipxact.Driver(
                            clock_driver=ipxact.ClockDriver(
                                clock_period="10",
                                clock_pulse_offset="0",
                                clock_pulse_value="1",
                                clock_pulse_duration="5",
                                clock_name="clk",
                                period_units="ns",
                                offset_units="ps",
                                duration_units="ns",
                            ),
                            range_left="31",
                            range_right="0",
                            view_refs=["rtl"],
                        )
                    ],
                    constraint_sets=[
                        ipxact.ConstraintSet(
                            name="timing",
                            vector_left="31",
                            vector_right="0",
                            drive_constraint=ipxact.DriveConstraint(
                                cell=ipxact.CellSpecification(cell_function="buf", cell_strength="high")
                            ),
                            load_constraint=ipxact.LoadConstraint(
                                cell=ipxact.CellSpecification(cell_class="combinational"),
                                count="4",
                            ),
                            timing_constraints=[
                                ipxact.TimingConstraint(
                                    value="10",
                                    clock_name="clk",
                                    clock_edge="rise",
                                    delay_type="min",
                                )
                            ],
                            constraint_set_id="cs0",
                        )
                    ],
                    all_logical_directions_allowed=True,
                ),
                field_maps=[
                    ipxact.FieldMap(
                        field_slice=ipxact.FieldReference(
                            field_ref="ENABLE",
                            register_ref="CTRL",
                            address_block_ref="regs",
                            memory_map_ref="main_mm",
                            range=ipxact.PartSelect(range_left="0", range_right="0"),
                        ),
                        part_select=ipxact.PartSelect(range_left="0", range_right="0"),
                        mode_refs=[_normal_mode_ref()],
                    )
                ],
                parameters=[ipxact.Parameter(name="PORT_P", value="1", parameter_id="PORT_P")],
                vendor_extensions=[VENDOR_EXTENSION],
            ),
            ipxact.Port(
                name="tlm_socket",
                transactional=ipxact.TransactionalPort(
                    initiative=ipxact.Initiative.BOTH,
                    kind="tlm_socket",
                    bus_width="32",
                    qualifier=ipxact.Qualifier(is_data=True),
                    protocol=ipxact.Protocol(
                        protocol_type="custom",
                        custom_type_name="my_protocol",
                        payload=ipxact.Payload(
                            type="specific",
                            name="req",
                            extension="ext",
                            extension_mandatory=True,
                        ),
                    ),
                    max_connections="4",
                    min_connections="1",
                    all_logical_initiatives_allowed=True,
                ),
            ),
        ],
    )


def build_wide_component() -> ipxact.Component:
    """A Component covering every section that can be written as schema-valid IP-XACT."""
    return ipxact.Component(
        vlnv=ipxact.VLNV("example.org", "ip", "wide_coverage", "2.0"),
        display_name="Wide coverage",
        short_description="Every writable component section",
        description="Hand-built component exercising the writer end to end.",
        external_type_definitions=[
            ipxact.ExternalTypeDefinitionsRef(
                name="shared_types",
                type_definitions=ipxact.VLNVRef(
                    "example.org", "types", "shared", "1.0", {"SHARED_P": "8"}
                ),
            )
        ],
        power_domains=[
            ipxact.PowerDomain(
                name="PD_MAIN",
                always_on="1",
                parameters=[ipxact.Parameter(name="PD_P", value="1", parameter_id="PD_P")],
                vendor_extensions=[VENDOR_EXTENSION],
            ),
            ipxact.PowerDomain(name="PD_SUB", sub_domain_of="PD_MAIN"),
        ],
        bus_interfaces=[
            ipxact.BusInterface(
                name="cpu_initiator",
                bus_type=ipxact.VLNVRef("amba.com", "AMBA4", "APB4", "r0p0_0"),
                mode=ipxact.InterfaceMode.INITIATOR,
                abstraction_types=[
                    ipxact.AbstractionType(
                        abstraction_ref=ipxact.VLNVRef(
                            "amba.com", "AMBA4", "APB4_rtl", "r0p0_0", {"ABS_P": "1"}
                        ),
                        port_maps=[
                            ipxact.PortMap(logical_port="PCLK", physical_port="clk"),
                            ipxact.PortMap(logical_port="PRESETn", logical_tie_off="1", invert=True),
                            ipxact.PortMap(logical_port="PWDATA", physical_port="data", is_informative=True),
                        ],
                        view_refs=["rtl"],
                    )
                ],
                initiator=ipxact.InitiatorInterface(
                    address_space_ref="sys_space",
                    base_address="0x0",
                    mode_refs=[_normal_mode_ref()],
                ),
                connection_required=True,
                bits_in_lau="8",
                bit_steering="0",
                endianness="little",
                parameters=[ipxact.Parameter(name="BUS_P", value="1", parameter_id="BUS_P")],
                display_name="CPU initiator",
                description="initiator side",
                vendor_extensions=[VENDOR_EXTENSION],
            ),
            ipxact.BusInterface(
                name="regs_target",
                bus_type=ipxact.VLNVRef("amba.com", "AMBA4", "APB4", "r0p0_0"),
                mode=ipxact.InterfaceMode.TARGET,
                target=ipxact.TargetInterface(
                    memory_map_ref="main_mm",
                    file_set_ref_groups=[
                        ipxact.FileSetRefGroup(group="rtl", file_set_refs=["rtl_files"])
                    ],
                ),
            ),
            ipxact.BusInterface(
                name="bridge_target",
                bus_type=ipxact.VLNVRef("amba.com", "AMBA4", "APB4", "r0p0_0"),
                mode=ipxact.InterfaceMode.TARGET,
                target=ipxact.TargetInterface(
                    transparent_bridges=[ipxact.TransparentBridge(initiator_ref="cpu_initiator")]
                ),
            ),
            ipxact.BusInterface(
                name="sys_if",
                bus_type=ipxact.VLNVRef("amba.com", "AMBA4", "APB4", "r0p0_0"),
                mode=ipxact.InterfaceMode.SYSTEM,
                system=ipxact.SystemInterface(group="sysgroup"),
            ),
            ipxact.BusInterface(
                name="mirror_initiator",
                bus_type=ipxact.VLNVRef("amba.com", "AMBA4", "APB4", "r0p0_0"),
                mode=ipxact.InterfaceMode.MIRRORED_INITIATOR,
            ),
            ipxact.BusInterface(
                name="mirror_target",
                bus_type=ipxact.VLNVRef("amba.com", "AMBA4", "APB4", "r0p0_0"),
                mode=ipxact.InterfaceMode.MIRRORED_TARGET,
                mirrored_target=ipxact.MirroredTargetInterface(
                    remap_addresses=[
                        ipxact.RemapAddress(value="0x1000", mode_refs=[_normal_mode_ref()]),
                        ipxact.RemapAddress(value="0x2000"),
                    ],
                    range="0x100",
                ),
            ),
            ipxact.BusInterface(
                name="mirror_system",
                bus_type=ipxact.VLNVRef("amba.com", "AMBA4", "APB4", "r0p0_0"),
                mode=ipxact.InterfaceMode.MIRRORED_SYSTEM,
                mirrored_system=ipxact.SystemInterface(group="sysgroup"),
            ),
            ipxact.BusInterface(
                name="monitor_if",
                bus_type=ipxact.VLNVRef("amba.com", "AMBA4", "APB4", "r0p0_0"),
                mode=ipxact.InterfaceMode.MONITOR,
                monitor=ipxact.MonitorInterface(
                    interface_mode=ipxact.InterfaceMode.SYSTEM,
                    group="sysgroup",
                ),
            ),
        ],
        indirect_interfaces=[
            ipxact.IndirectInterface(
                name="indirect",
                indirect_address_ref=ipxact.FieldReference(
                    field_ref="ENABLE",
                    register_ref="CTRL",
                    address_block_ref="regs",
                    memory_map_ref="main_mm",
                ),
                indirect_data_ref=ipxact.FieldReference(
                    field_ref="BUSY",
                    register_ref="STATUS",
                    register_file_refs=["RF"],
                    address_block_ref="regs",
                    memory_map_ref="main_mm",
                ),
                memory_map_ref="main_mm",
                bits_in_lau="8",
                endianness="little",
                display_name="Indirect",
                description="indirectly addressed map",
                parameters=[ipxact.Parameter(name="IND_P", value="1", parameter_id="IND_P")],
                vendor_extensions=[VENDOR_EXTENSION],
            )
        ],
        channels=[
            ipxact.Channel(
                name="ch0",
                bus_interface_refs=["mirror_initiator", "mirror_target"],
                display_name="Channel",
                description="mirrored pair",
                vendor_extensions=[VENDOR_EXTENSION],
            )
        ],
        modes=[
            ipxact.Mode(
                name="normal",
                port_slices=[
                    ipxact.PortSlice(
                        name="data_slice",
                        port_ref="data",
                        part_select=ipxact.PartSelect(range_left="7", range_right="0"),
                        display_name="Data slice",
                        description="low byte",
                    )
                ],
                field_slices=[
                    ipxact.FieldSlice(
                        name="enable_slice",
                        field_ref=ipxact.FieldReference(
                            field_ref="ENABLE",
                            register_ref="CTRL",
                            address_block_ref="regs",
                            memory_map_ref="main_mm",
                            range=ipxact.PartSelect(range_left="0", range_right="0"),
                        ),
                        display_name="Enable slice",
                        description="the enable bit",
                    )
                ],
                condition="1",
                vendor_extensions=[VENDOR_EXTENSION],
            )
        ],
        address_spaces=[
            ipxact.AddressSpace(
                name="sys_space",
                range="0x10000",
                width="32",
                segments=[
                    ipxact.Segment(
                        name="seg0",
                        address_offset="0x0",
                        range="0x1000",
                        display_name="Segment 0",
                        description="first segment",
                        vendor_extensions=[VENDOR_EXTENSION],
                    )
                ],
                address_unit_bits="8",
                local_memory_map=ipxact.LocalMemoryMap(
                    name="local_mm",
                    items=[
                        ipxact.AddressBlock(
                            name="local_regs",
                            range="0x10",
                            width="32",
                            base_address="0x0",
                            registers=[
                                ipxact.Register(
                                    name="LOCAL",
                                    address_offset="0x0",
                                    size="32",
                                    fields=[ipxact.Field(name="BIT", bit_offset="0", bit_width="1")],
                                )
                            ],
                        )
                    ],
                    display_name="Local map",
                    description="address space local map",
                ),
                display_name="System space",
                description="the cpu address space",
                parameters=[ipxact.Parameter(name="AS_P", value="1", parameter_id="AS_P")],
                vendor_extensions=[VENDOR_EXTENSION],
            )
        ],
        memory_maps=[
            ipxact.MemoryMap(
                name="main_mm",
                items=[
                    _regs_block(),
                    ipxact.SubspaceMap(
                        name="bridged",
                        initiator_ref="cpu_initiator",
                        base_address="0x2000",
                        segment_ref="seg0",
                        display_name="Bridged space",
                        description="mapped through the bridge",
                        parameters=[ipxact.Parameter(name="SS_P", value="1", parameter_id="SS_P")],
                    ),
                ],
                memory_remaps=[
                    ipxact.MemoryRemap(
                        name="remap",
                        mode_refs=[_normal_mode_ref()],
                        items=[
                            ipxact.AddressBlock(
                                name="remapped",
                                range="0x10",
                                width="32",
                                base_address="0x3000",
                                registers=[
                                    ipxact.Register(
                                        name="REMAPPED",
                                        address_offset="0x0",
                                        size="32",
                                        fields=[ipxact.Field(name="BIT", bit_offset="0", bit_width="1")],
                                    )
                                ],
                            )
                        ],
                        display_name="Remap",
                        description="mode-selected extra content",
                    )
                ],
                address_unit_bits="8",
                shared=ipxact.SharedType.YES,
                display_name="Main map",
                description="the component memory map",
                vendor_extensions=[VENDOR_EXTENSION],
            )
        ],
        model=_model(),
        component_generators=[
            ipxact.ComponentGenerator(
                name="gen0",
                generator_exe="./gen.py",
                phase="1.0",
                parameters=[ipxact.Parameter(name="GEN_P", value="1", parameter_id="GEN_P")],
                api_type="none",
                api_service="REST",
                transport_methods=["file"],
                groups=["generators"],
                scope="entity",
                hidden=True,
                vendor_extensions=[VENDOR_EXTENSION],
            )
        ],
        choices=[
            ipxact.Choice(
                name="ch_values",
                enumerations=[
                    ipxact.ChoiceEnumeration(value="1", text="one", help="the first value"),
                    ipxact.ChoiceEnumeration(value="2"),
                ],
            )
        ],
        file_sets=[
            ipxact.FileSet(
                name="rtl_files",
                groups=["rtl"],
                files=[
                    ipxact.File(
                        name="wide_coverage.sv",
                        file_types=["systemVerilogSource"],
                        is_structural=True,
                        is_include_file=True,
                        include_has_external_declarations=True,
                        logical_name="work",
                        exported_names=["wide_coverage"],
                        build_command="vlog",
                        build_flags="-sv",
                        vendor_extensions=[VENDOR_EXTENSION],
                    )
                ],
                default_file_builders=[
                    ipxact.FileBuilder(
                        file_type="systemVerilogSource",
                        command="vlog",
                        flags="-sv",
                        replace_default_flags="0",
                    )
                ],
                dependencies=["../include"],
                display_name="RTL files",
                description="the synthesizable sources",
                vendor_extensions=[VENDOR_EXTENSION],
            )
        ],
        clearbox_elements=[
            ipxact.ClearboxElement(
                name="cb0",
                clearbox_type="signal",
                driveable=True,
                parameters=[ipxact.Parameter(name="CB_P", value="1", parameter_id="CB_P")],
                vendor_extensions=[VENDOR_EXTENSION],
            )
        ],
        cpus=[
            ipxact.Cpu(
                name="cpu0",
                range="0x10000",
                width="32",
                memory_map_ref="main_mm",
                regions=[
                    ipxact.CpuRegion(
                        name="region0",
                        address_offset="0x0",
                        range="0x1000",
                        vendor_extensions=[VENDOR_EXTENSION],
                    )
                ],
                address_unit_bits="8",
                parameters=[ipxact.Parameter(name="CPU_P", value="1", parameter_id="CPU_P")],
                vendor_extensions=[VENDOR_EXTENSION],
            )
        ],
        other_clock_drivers=[
            ipxact.OtherClockDriver(
                clock_name="ref_clk",
                clock_period="20",
                clock_pulse_offset="0",
                clock_pulse_value="1",
                clock_pulse_duration="10",
                clock_source="external",
                period_units="ns",
                offset_units="ps",
                duration_units="ns",
            )
        ],
        reset_types=[
            ipxact.ResetType(
                name="HARD",
                display_name="Hard reset",
                description="power-on reset",
                vendor_extensions=[VENDOR_EXTENSION],
            )
        ],
        parameters=[
            ipxact.Parameter(
                name="BAUD_RATE",
                value="115200",
                display_name="Baud rate",
                short_description="serial speed",
                description="the configured baud rate",
                vectors=[ipxact.Vector(left="31", right="0")],
                arrays=[ipxact.ArrayBound(left="1", right="0")],
                parameter_id="BAUD_RATE",
                prompt="Baud rate:",
                choice_ref="ch_values",
                order=1.5,
                config_groups=["basic", "serial"],
                minimum="0",
                maximum="1000000",
                type="int",
                sign="unsigned",
                prefix="kilo",
                unit="hertz",
                resolve="user",
                vendor_extensions=[VENDOR_EXTENSION],
            )
        ],
        assertions=[
            ipxact.Assertion(
                name="baud_positive",
                assert_expression="1",
                display_name="Baud positive",
                description="the baud rate must be positive",
            )
        ],
        vendor_extensions=[VENDOR_EXTENSION],
    )


def build_banked_component() -> ipxact.Component:
    """A Component built around banks and a structured port.

    Both constructs round-trip through the writer and the parser, but neither can be written
    as schema-valid XML from ipxact-compiler's object model: ipxact.Bank carries no
    baseAddress (which addressBankType requires) and ipxact.StructuredPort carries no
    structPortTypeDefs (which portStructuredType requires). See the README notes.
    """
    return ipxact.Component(
        vlnv=ipxact.VLNV("example.org", "ip", "banked", "1.0"),
        memory_maps=[
            ipxact.MemoryMap(
                name="banked_mm",
                items=[
                    ipxact.Bank(
                        name="outer",
                        bank_alignment=ipxact.BankAlignment.SERIAL,
                        items=[
                            ipxact.AddressBlock(
                                name="banked_regs",
                                range="0x10",
                                width="32",
                                registers=[
                                    ipxact.Register(
                                        name="BANKED",
                                        address_offset="0x0",
                                        size="32",
                                        fields=[ipxact.Field(name="BIT", bit_offset="0", bit_width="1")],
                                    )
                                ],
                            ),
                            ipxact.Bank(
                                name="inner",
                                bank_alignment=ipxact.BankAlignment.PARALLEL,
                                items=[
                                    ipxact.AddressBlock(name="inner_regs", range="0x8", width="32")
                                ],
                                usage=ipxact.UsageType.MEMORY,
                            ),
                            ipxact.SubspaceMap(name="banked_sub", initiator_ref="init_if"),
                        ],
                        usage=ipxact.UsageType.REGISTER,
                        volatile=False,
                        access_policies=[ipxact.AccessPolicy(access=ipxact.AccessType.READ_WRITE)],
                        parameters=[ipxact.Parameter(name="BANK_P", value="1", parameter_id="BANK_P")],
                        display_name="Outer bank",
                        description="a bank of blocks",
                    )
                ],
            )
        ],
        model=ipxact.Model(
            ports=[
                ipxact.Port(
                    name="bus",
                    structured=ipxact.StructuredPort(
                        struct_type="struct",
                        vectors=[ipxact.Vector(left="1", right="0", vector_id="SV0")],
                        sub_ports=[
                            ipxact.SubPort(
                                name="valid",
                                wire=ipxact.WirePort(direction=ipxact.Direction.OUT),
                                display_name="Valid",
                                description="handshake valid",
                                is_io=True,
                            ),
                            ipxact.SubPort(
                                name="nested",
                                structured=ipxact.StructuredPort(
                                    struct_type="interface",
                                    sub_ports=[
                                        ipxact.SubPort(
                                            name="ready",
                                            wire=ipxact.WirePort(direction=ipxact.Direction.IN),
                                        )
                                    ],
                                    packed=False,
                                    phantom=True,
                                ),
                            ),
                        ],
                        packed=True,
                        direction=ipxact.Direction.OUT,
                    ),
                )
            ]
        ),
    )
