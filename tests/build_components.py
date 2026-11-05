"""Hand-built ipxact.Component objects used by the writer tests.

These are built directly rather than parsed from XML, so they exercise fields the
apb_uart.xml fixture does not reach. Between them, build_wide_component and
build_banked_component set every field of every component-side dataclass at least once
(test_component_writer checks it), so a field the writer forgets cannot go unnoticed.
"""

from __future__ import annotations

from typing import Optional

import ipxact

# ipxact-compiler serializes each vendorExtensions child with the namespace declarations that
# are in scope at that point, so an extension read back out of a component always carries the
# ipxact and xsi declarations too. Spelling them out here keeps round-trip comparison exact.
VENDOR_EXTENSION = (
    '<vendor:note xmlns:vendor="http://example.org/vendor"'
    ' xmlns:ipxact="http://www.accellera.org/XMLSchema/IPXACT/1685-2022"'
    ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">kept verbatim</vendor:note>'
)

# An attribute from another namespace (the schema's any.att). It is only put on elements
# without vendor extensions inside: its namespace declaration would otherwise be in scope
# for them, and end up in the extension strings read back.
FOREIGN_ATTRIBUTES = {"{http://example.org/tool}hint": "keep"}


def _t(value: str, xml_id: Optional[str] = None) -> ipxact.TextValue:
    return ipxact.TextValue(value, xml_id=xml_id)


def _range(left: str, right: str) -> ipxact.Range:
    return ipxact.Range(ipxact.Expression(left), ipxact.Expression(right))


def _ref(name: str, xml_id: Optional[str] = None) -> ipxact.LocalReference:
    return ipxact.LocalReference(name, xml_id=xml_id)


def _parameter(name: str, value: str = "1") -> ipxact.Parameter:
    return ipxact.Parameter(name=name, value=ipxact.Expression(value), parameter_id=name)


def _normal_mode_ref(priority: int = 0) -> ipxact.ModeRef:
    return ipxact.ModeRef(name="normal", priority=priority)


def _type_definitions_ref(name: str) -> ipxact.DefinitionRef:
    return ipxact.DefinitionRef(name=name, type_definitions="shared_types")


def _ctrl_field() -> ipxact.Field:
    return ipxact.Field(
        name="ENABLE",
        bit_offset=ipxact.Expression("0"),
        bit_width=ipxact.Expression("1", minimum="1", maximum="1"),
        access_handles=[
            ipxact.AccessHandle(
                view_refs=[_t("rtl")],
                slices=[ipxact.Slice(path_segments=[ipxact.Expression("u_ctrl"), ipxact.Expression("enable_q")], range=_range("0", "0"))],
                slices_xml_id="enable_slices",
                force=False,
                xml_id="enable_handle",
                vendor_extensions=[VENDOR_EXTENSION],
            )
        ],
        array=ipxact.MemoryArray(dims=[ipxact.ArrayDim(size=ipxact.Expression("2"), index_var="i")], stride=ipxact.Expression("1")),
        type_identifier="enable_t",
        volatile=True,
        resets=[ipxact.Reset(value=ipxact.Expression("0"), mask=ipxact.Expression("1"), reset_type_ref="HARD", xml_id="enable_reset")],
        field_access_policies=[
            ipxact.FieldAccessPolicy(
                mode_refs=[_normal_mode_ref()],
                access=ipxact.AccessType.READ_WRITE,
                modified_write_value=ipxact.ModifiedWriteValue.MODIFY,
                modified_write_value_modify="custom_write",
                write_value_constraint=ipxact.WriteValueConstraint(minimum=ipxact.Expression("0"), maximum=ipxact.Expression("1")),
                read_action=ipxact.ReadAction.MODIFY,
                read_action_modify="custom_read",
                read_response=ipxact.Expression("0"),
                broadcast_to=[
                    ipxact.FieldReference(
                        field_ref=ipxact.IndexedRef("ENABLE", indices=[ipxact.Expression("0")]),
                        register_ref=ipxact.IndexedRef("CTRL", indices=[ipxact.Expression("1")]),
                        alternate_register_ref="CTRL_ALT",
                        address_block_ref=ipxact.IndexedRef("regs"),
                        memory_map_ref="main_mm",
                        xml_id="broadcast0",
                    )
                ],
                access_restrictions=[
                    ipxact.AccessRestriction(
                        mode_refs=[_normal_mode_ref()],
                        read_access_mask=ipxact.Expression("1"),
                        write_access_mask=ipxact.Expression("1"),
                        xml_id="restriction0",
                    )
                ],
                testable=True,
                test_constraint=ipxact.TestConstraint.WRITE_AS_READ,
                reserved=ipxact.Expression("0"),
                xml_id="enable_policy",
                vendor_extensions=[VENDOR_EXTENSION],
            )
        ],
        field_access_policies_xml_id="enable_policies",
        enumerated_values=[
            ipxact.EnumeratedValue(
                name="OFF",
                value=ipxact.Expression("0"),
                usage="read",
                display_name="Off",
                short_description="off",
                description="disabled",
                xml_id="enable_off",
                vendor_extensions=[VENDOR_EXTENSION],
            ),
            ipxact.EnumeratedValue(name="ON", value=ipxact.Expression("1")),
        ],
        display_name="Enable",
        short_description="enable bit",
        description="Enables the block",
        parameters=[_parameter("FIELD_P")],
        xml_id="enable_field",
        vendor_extensions=[VENDOR_EXTENSION],
    )


def _regs_block() -> ipxact.AddressBlock:
    return ipxact.AddressBlock(
        name="regs",
        range=ipxact.Expression("0x100"),
        width=ipxact.Expression("32"),
        base_address=ipxact.Expression("0x0"),
        access_handles=[
            ipxact.AccessHandle(slices=[ipxact.Slice(path_segments=[ipxact.Expression("u_regs")], xml_id="regs_slice")])
        ],
        array=ipxact.MemoryArray(dims=[ipxact.ArrayDim(size=ipxact.Expression("1"))], stride=ipxact.Expression("0x100")),
        type_identifier="regs_t",
        usage=ipxact.UsageType.REGISTER,
        volatile=False,
        access_policies=[
            ipxact.AccessPolicy(
                mode_refs=[_normal_mode_ref()],
                access=ipxact.AccessType.READ_WRITE,
                xml_id="regs_policy",
                vendor_extensions=[VENDOR_EXTENSION],
            )
        ],
        registers=[
            ipxact.Register(
                name="CTRL",
                address_offset=ipxact.Expression("0x0"),
                size=ipxact.Expression("32", xml_id="ctrl_size", other_attributes=FOREIGN_ATTRIBUTES),
                access_handles=[ipxact.AccessHandle(path_segments=[ipxact.Expression("u_ctrl")])],
                array=ipxact.MemoryArray(dims=[ipxact.ArrayDim(size=ipxact.Expression("4"))], stride=ipxact.Expression("4")),
                type_identifier="ctrl_t",
                volatile=True,
                access_policies=[
                    ipxact.AccessPolicy(mode_refs=[_normal_mode_ref()], access=ipxact.AccessType.READ_WRITE)
                ],
                fields=[
                    _ctrl_field(),
                    ipxact.Field(
                        name="ALIAS",
                        bit_offset=ipxact.Expression("1"),
                        alias_of=ipxact.FieldReference(
                            field_ref=ipxact.IndexedRef("ENABLE"),
                            register_ref=ipxact.IndexedRef("CTRL"),
                            address_block_ref=ipxact.IndexedRef("regs"),
                            memory_map_ref="main_mm",
                        ),
                    ),
                    ipxact.Field(
                        name="TYPED",
                        bit_offset=ipxact.Expression("2"),
                        field_definition_ref=_type_definitions_ref("typed_field"),
                    ),
                    ipxact.Field(
                        name="MODE",
                        bit_offset=ipxact.Expression("3"),
                        bit_width=ipxact.Expression("2"),
                        field_access_policies=[
                            ipxact.FieldAccessPolicy(
                                field_access_policy_definition_ref=_type_definitions_ref("rw_policy")
                            ),
                            ipxact.FieldAccessPolicy(
                                write_value_constraint=ipxact.WriteValueConstraint(write_as_read=True)
                            ),
                            ipxact.FieldAccessPolicy(
                                write_value_constraint=ipxact.WriteValueConstraint(use_enumerated_values=True)
                            ),
                        ],
                        enumeration_definition_ref=_type_definitions_ref("mode_values"),
                    ),
                ],
                alternate_registers=[
                    ipxact.AlternateRegister(
                        name="CTRL_ALT",
                        access_handles=[ipxact.AccessHandle(path_segments=[ipxact.Expression("u_ctrl_alt")])],
                        mode_refs=[_normal_mode_ref()],
                        type_identifier="ctrl_alt_t",
                        volatile=False,
                        access_policies=[ipxact.AccessPolicy(access=ipxact.AccessType.READ_ONLY)],
                        fields=[ipxact.Field(name="ALT_BIT", bit_offset=ipxact.Expression("0"), bit_width=ipxact.Expression("1"))],
                        display_name="Alternate CTRL",
                        short_description="alternate",
                        description="mode-selected layout",
                        parameters=[_parameter("ALT_P", "0")],
                        xml_id="ctrl_alt",
                        vendor_extensions=[VENDOR_EXTENSION],
                    )
                ],
                display_name="Control",
                short_description="control",
                description="Control register",
                parameters=[_parameter("CTRL_P", "2")],
                xml_id="ctrl",
                vendor_extensions=[VENDOR_EXTENSION],
            ),
            ipxact.Register(
                name="TYPED_REG",
                address_offset=ipxact.Expression("0x10"),
                register_definition_ref=_type_definitions_ref("typed_register"),
            ),
            ipxact.RegisterFile(
                name="RF",
                address_offset=ipxact.Expression("0x40"),
                range=ipxact.Expression("0x40"),
                access_handles=[ipxact.AccessHandle(path_segments=[ipxact.Expression("u_rf")])],
                array=ipxact.MemoryArray(dims=[ipxact.ArrayDim(size=ipxact.Expression("2"))], stride=ipxact.Expression("0x20")),
                type_identifier="rf_t",
                access_policies=[ipxact.AccessPolicy(access=ipxact.AccessType.READ_ONLY)],
                registers=[
                    ipxact.Register(
                        name="STATUS",
                        address_offset=ipxact.Expression("0x0"),
                        size=ipxact.Expression("32"),
                        fields=[ipxact.Field(name="BUSY", bit_offset=ipxact.Expression("0"), bit_width=ipxact.Expression("1"))],
                    )
                ],
                display_name="Register file",
                short_description="register file",
                description="nested registers",
                parameters=[_parameter("RF_P", "3")],
                xml_id="rf",
                vendor_extensions=[VENDOR_EXTENSION],
            ),
            ipxact.RegisterFile(
                name="TYPED_RF",
                address_offset=ipxact.Expression("0x80"),
                register_file_definition_ref=_type_definitions_ref("typed_register_file"),
            ),
        ],
        misalignment_allowed=False,
        display_name="Registers",
        short_description="registers",
        description="Register block",
        parameters=[_parameter("BLOCK_P", "4")],
        xml_id="regs",
        vendor_extensions=[VENDOR_EXTENSION],
    )


def _ports() -> list[ipxact.Port]:
    return [
        ipxact.Port(
            name="clk",
            wire=ipxact.WirePort(
                direction=ipxact.Direction.IN,
                qualifier=ipxact.Qualifier(is_clock=True, xml_id="clk_qualifier"),
                wire_type_defs=[
                    ipxact.WireTypeDef(
                        type_name="logic",
                        type_name_constrained=["WIDTH"],
                        type_definitions=[_t("types_pkg.sv", xml_id="clk_type_def")],
                        view_refs=[_t("rtl")],
                        xml_id="clk_wire_type",
                    )
                ],
                domain_type_defs=[
                    ipxact.DomainTypeDef(
                        type_name=_t("electrical", xml_id="clk_domain_name"),
                        type_definitions=[_t("disciplines.vams")],
                        view_refs=[_t("rtl")],
                        xml_id="clk_domain_type",
                    )
                ],
                signal_type_defs=[
                    ipxact.SignalTypeDef(signal_type="digital", view_refs=[_t("rtl")], xml_id="clk_signal_type")
                ],
                drivers=[ipxact.Driver(default_value=ipxact.Expression("0"), view_refs=[_t("rtl", xml_id="clk_driver_view")])],
                power_constraints=[
                    ipxact.PowerConstraint(
                        power_domain_ref="PD_MAIN",
                        xml_id="clk_power",
                        vendor_extensions=[VENDOR_EXTENSION],
                    )
                ],
            ),
            display_name="Clock",
            short_description="clock",
            description="the clock",
            xml_id="clk_port",
        ),
        ipxact.Port(
            name="rst_n",
            wire=ipxact.WirePort(
                direction=ipxact.Direction.IN,
                qualifier=ipxact.Qualifier(is_reset=ipxact.LevelFlag(value=True, level="low")),
                drivers=[
                    ipxact.Driver(
                        single_shot_driver=ipxact.SingleShotDriver(
                            single_shot_offset=ipxact.Expression("0"),
                            single_shot_value=ipxact.Expression("1"),
                            single_shot_duration=ipxact.Expression("10"),
                            offset_units="ps",
                            duration_units="ps",
                        ),
                        xml_id="rst_driver",
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
                vectors=[ipxact.Vector(left=ipxact.Expression("31"), right=ipxact.Expression("0"), vector_id="V0", xml_id="data_vector")],
                drivers=[
                    ipxact.Driver(
                        clock_driver=ipxact.ClockDriver(
                            clock_period=ipxact.Expression("10"),
                            clock_pulse_offset=ipxact.Expression("0"),
                            clock_pulse_value=ipxact.Expression("1"),
                            clock_pulse_duration=ipxact.Expression("5"),
                            clock_name="clk",
                            period_units="ps",
                            offset_units="ps",
                            duration_units="ps",
                            xml_id="data_clock_driver",
                        ),
                        range=_range("31", "0"),
                        view_refs=[_t("rtl")],
                    )
                ],
                constraint_sets=[
                    ipxact.ConstraintSet(
                        name="timing",
                        vector=ipxact.Vector(left=ipxact.Expression("31"), right=ipxact.Expression("0")),
                        drive_constraint=ipxact.DriveConstraint(
                            cell=ipxact.CellSpecification(
                                cell_function="other", cell_function_other="my_buf", cell_strength="high"
                            )
                        ),
                        load_constraint=ipxact.LoadConstraint(
                            cell=ipxact.CellSpecification(cell_class="combinational"),
                            count=ipxact.Expression("4"),
                        ),
                        timing_constraints=[
                            ipxact.TimingConstraint(
                                value="10",
                                clock_name="clk",
                                clock_edge="rise",
                                delay_type="min",
                                xml_id="data_timing",
                            )
                        ],
                        constraint_set_id="cs0",
                        display_name="Timing",
                        short_description="timing",
                        description="timing constraints",
                        xml_id="data_constraints",
                    )
                ],
                power_constraints=[ipxact.PowerConstraint(power_domain_ref="PD_SUB", range=_range("7", "0"))],
                all_logical_directions_allowed=True,
            ),
            field_maps=[
                ipxact.FieldMap(
                    field_slice=ipxact.FieldReference(
                        field_ref=ipxact.IndexedRef("ENABLE"),
                        register_ref=ipxact.IndexedRef("CTRL"),
                        address_block_ref=ipxact.IndexedRef("regs"),
                        memory_map_ref="main_mm",
                        range=_range("0", "0"),
                    ),
                    part_select=ipxact.PartSelect(range=_range("0", "0")),
                    mode_refs=[_normal_mode_ref()],
                    xml_id="data_field_map",
                )
            ],
            arrays=[ipxact.ArrayBound(left=ipxact.Expression("3"), right=ipxact.Expression("0"), array_id="A0", xml_id="data_array")],
            access=ipxact.PortAccess(
                port_access_type="ref",
                access_handles=[
                    ipxact.AccessHandle(
                        indices=[ipxact.Expression("0")],
                        slices=[ipxact.Slice(path_segments=[ipxact.Expression("u_data")])],
                    )
                ],
            ),
            parameters=[_parameter("PORT_P")],
            vendor_extensions=[VENDOR_EXTENSION],
        ),
        ipxact.Port(
            name="tlm_socket",
            transactional=ipxact.TransactionalPort(
                initiative=ipxact.Initiative.BOTH,
                kind="custom",
                kind_custom="my_socket",
                bus_width=ipxact.Expression("32"),
                qualifier=ipxact.Qualifier(is_data=True),
                protocol=ipxact.Protocol(
                    protocol_type="custom",
                    custom_type_name="my_protocol",
                    payload=ipxact.Payload(
                        type="specific",
                        name="req",
                        extension="ext",
                        extension_mandatory=True,
                        vendor_extensions=[VENDOR_EXTENSION],
                    ),
                ),
                trans_type_defs=[
                    ipxact.TransTypeDef(
                        type_name="tlm_socket_t",
                        type_name_exact=False,
                        type_definitions=[_t("tlm.h")],
                        type_parameters=[
                            ipxact.ModuleParameter(name="BUSWIDTH", value=ipxact.Expression("32"), parameter_id="BUSWIDTH")
                        ],
                        service_type_defs=[
                            ipxact.ServiceTypeDef(
                                type_name="tlm_payload",
                                type_name_implicit=True,
                                type_definitions=[_t("tlm_payload.h")],
                                type_parameters=[
                                    ipxact.ModuleParameter(name="PAYLOAD_W", value=ipxact.Expression("8"), parameter_id="PAYLOAD_W")
                                ],
                                service_type_defs=[ipxact.ServiceTypeDef(type_name="tlm_phase")],
                                xml_id="tlm_service",
                            )
                        ],
                        view_refs=[_t("rtl")],
                        xml_id="tlm_type",
                    )
                ],
                max_connections=ipxact.Expression("4"),
                min_connections=ipxact.Expression("1"),
                power_constraints=[ipxact.PowerConstraint(power_domain_ref="PD_MAIN")],
                all_logical_initiatives_allowed=True,
            ),
        ),
    ]


def _model() -> ipxact.Model:
    return ipxact.Model(
        views=[
            ipxact.View(
                name="rtl",
                env_identifiers=[_t("::simulation", xml_id="rtl_env"), _t("verilog:*:*")],
                component_instantiation_ref="rtl_impl",
                display_name="RTL",
                short_description="rtl view",
                description="the RTL view",
                xml_id="rtl_view",
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
                language_strict=True,
                library_name="work",
                package_name="pkg",
                module_name="wide_coverage",
                architecture_name="rtl",
                configuration_name="cfg",
                module_parameters=[
                    ipxact.ModuleParameter(
                        name="WIDTH",
                        value=ipxact.Expression("8"),
                        parameter_id="WIDTH",
                        display_name="Width",
                        short_description="width",
                        description="bus width",
                        vectors=[ipxact.Vector(left=ipxact.Expression("7"), right=ipxact.Expression("0"), vector_id="MV0")],
                        arrays=[ipxact.ArrayBound(left=ipxact.Expression("1"), right=ipxact.Expression("0"), array_id="ARR0")],
                        prompt="Width:",
                        choice_ref="ch_values",
                        order=2.0,
                        config_groups=["basic"],
                        minimum="1",
                        maximum="64",
                        type="int",
                        sign="signed",
                        prefix="kilo",
                        unit="second",
                        resolve="user",
                        xml_id="width_param",
                        other_attributes=FOREIGN_ATTRIBUTES,
                        data_type="integer",
                        usage_type="runtime",
                        data_type_definition="pkg",
                        constrained=["low", "high"],
                    ),
                    ipxact.ModuleParameter(
                        name="DEPTH",
                        value=ipxact.Expression("4"),
                        parameter_id="DEPTH",
                        vendor_extensions=[VENDOR_EXTENSION],
                    ),
                ],
                default_file_builders=[
                    ipxact.FileBuilder(
                        file_type=ipxact.FileType("systemVerilogSource"),
                        command=ipxact.Expression("vlog"),
                        flags=ipxact.Expression("-sv"),
                        replace_default_flags=ipxact.Expression("0"),
                        xml_id="inst_builder",
                    )
                ],
                file_set_refs=[_ref("rtl_files", xml_id="inst_file_set_ref")],
                constraint_set_refs=[
                    ipxact.LocalReference("cs0", vendor_extensions=[VENDOR_EXTENSION])
                ],
                clearbox_element_refs=[
                    ipxact.ClearboxElementRef(
                        name="cb0",
                        locations=[
                            ipxact.Location(
                                slices=[ipxact.Slice(path_segments=[ipxact.Expression("u_core"), ipxact.Expression("sig")], range=_range("3", "0"))],
                                xml_id="cb0_location",
                            )
                        ],
                        xml_id="cb0_ref",
                        vendor_extensions=[VENDOR_EXTENSION],
                    )
                ],
                parameters=[_parameter("INST_P")],
                display_name="RTL implementation",
                short_description="rtl",
                description="the RTL instantiation",
                xml_id="rtl_impl",
                vendor_extensions=[VENDOR_EXTENSION],
            )
        ],
        design_instantiations=[
            ipxact.DesignInstantiation(
                name="hier_design",
                design_ref=ipxact.VLNVRef("example.org", "ip", "wide_coverage_design", "2.0", xml_id="design_ref"),
                display_name="Hierarchy",
                short_description="hierarchy",
                description="the hierarchical design",
                xml_id="hier_design",
                vendor_extensions=[VENDOR_EXTENSION],
            )
        ],
        design_configuration_instantiations=[
            ipxact.DesignConfigurationInstantiation(
                name="hier_config",
                design_configuration_ref=ipxact.VLNVRef("example.org", "ip", "wide_coverage_cfg", "2.0"),
                language="systemverilog",
                language_strict=True,
                parameters=[_parameter("CFG_P", "0")],
                display_name="Configuration",
                short_description="configuration",
                description="the design configuration",
                xml_id="hier_config",
                vendor_extensions=[VENDOR_EXTENSION],
            )
        ],
        ports=_ports(),
    )


def _file_sets() -> list[ipxact.FileSet]:
    return [
        ipxact.FileSet(
            name="rtl_files",
            groups=[_t("rtl", xml_id="rtl_group")],
            files=[
                ipxact.File(
                    name="wide_coverage.sv",
                    file_types=[ipxact.FileType("systemVerilogSource", xml_id="sv_type")],
                    is_structural=True,
                    is_include_file=True,
                    include_has_external_declarations=True,
                    logical_name="work",
                    logical_name_default=True,
                    exported_names=[_t("wide_coverage", xml_id="exported")],
                    build_command=ipxact.BuildCommand(
                        command=ipxact.Expression("vlog"),
                        flags=ipxact.Expression("-sv"),
                        flags_append=True,
                        replace_default_flags=ipxact.Expression("0"),
                        target_name="wide_coverage.o",
                    ),
                    dependencies=[_t("../include", xml_id="file_dependency")],
                    defines=[
                        ipxact.Define(
                            name="SYNTHESIS",
                            value=ipxact.Expression("1"),
                            display_name="Synthesis",
                            short_description="synthesis",
                            description="set when synthesizing",
                            xml_id="define0",
                            vendor_extensions=[VENDOR_EXTENSION],
                        )
                    ],
                    image_types=[_t("elf", xml_id="image_type")],
                    file_id="wide_sv",
                    description="the top-level source",
                    xml_id="wide_file",
                    vendor_extensions=[VENDOR_EXTENSION],
                ),
                ipxact.File(
                    name="driver.c",
                    file_types=[ipxact.FileType("user", user="cSourceUser", libext="c")],
                    file_id="driver_c",
                    other_attributes=FOREIGN_ATTRIBUTES,
                ),
            ],
            default_file_builders=[
                ipxact.FileBuilder(
                    file_type=ipxact.FileType("systemVerilogSource"),
                    command=ipxact.Expression("vlog"),
                    flags=ipxact.Expression("-sv"),
                    replace_default_flags=ipxact.Expression("0"),
                )
            ],
            dependencies=[_t("../include")],
            functions=[
                ipxact.Function(
                    file_ref="driver_c",
                    entry_point="main",
                    return_type="int",
                    arguments=[
                        ipxact.FunctionArgument(
                            name="argc",
                            value=ipxact.Expression("0"),
                            data_type="int",
                            display_name="Argument count",
                            short_description="argc",
                            description="number of arguments",
                            xml_id="argc",
                            vendor_extensions=[VENDOR_EXTENSION],
                        )
                    ],
                    disabled=ipxact.Expression("0"),
                    source_files=[
                        ipxact.SourceFile(
                            source_name="driver.c", file_type=ipxact.FileType("cSource"), xml_id="driver_source"
                        )
                    ],
                    replicate=True,
                    xml_id="main_function",
                )
            ],
            display_name="RTL files",
            short_description="rtl",
            description="the synthesizable sources",
            xml_id="rtl_files",
            vendor_extensions=[VENDOR_EXTENSION],
        )
    ]


def _bus_interfaces() -> list[ipxact.BusInterface]:
    apb = ipxact.VLNVRef("amba.com", "AMBA4", "APB4", "r0p0_0")
    return [
        ipxact.BusInterface(
            name="cpu_initiator",
            bus_type=ipxact.VLNVRef("amba.com", "AMBA4", "APB4", "r0p0_0", xml_id="cpu_bus_type"),
            mode=ipxact.InterfaceMode.INITIATOR,
            abstraction_types=[
                ipxact.AbstractionType(
                    abstraction_ref=ipxact.VLNVRef(
                        "amba.com", "AMBA4", "APB4_rtl", "r0p0_0", {"ABS_P": ipxact.Expression("1", xml_id="abs_value")}
                    ),
                    port_maps=[
                        ipxact.PortMap(logical_port="PCLK", physical_port="clk"),
                        ipxact.PortMap(
                            logical_port="PRESETn",
                            logical_tie_off=ipxact.Expression("1"),
                            invert=True,
                            logical_port_xml_id="presetn_logical",
                            xml_id="presetn_map",
                            vendor_extensions=[VENDOR_EXTENSION],
                        ),
                        ipxact.PortMap(
                            logical_port="PWDATA",
                            logical_range=_range("7", "0"),
                            physical_port="data",
                            part_select=ipxact.PartSelect(indices=[ipxact.Expression("0")], range=_range("7", "0"), xml_id="pwdata_select"),
                            sub_port_refs=[
                                ipxact.SubPortReference(
                                    sub_port_ref="lower",
                                    part_select=ipxact.PartSelect(range=_range("3", "0")),
                                    xml_id="lower_sub_port",
                                )
                            ],
                            is_informative=True,
                            physical_port_xml_id="pwdata_physical",
                        ),
                    ],
                    view_refs=[_t("rtl", xml_id="abstraction_view")],
                    xml_id="apb_rtl",
                )
            ],
            initiator=ipxact.InitiatorInterface(
                address_space_ref="sys_space",
                base_address=ipxact.Expression("0x0"),
                mode_refs=[ipxact.ModeRef("normal", xml_id="initiator_mode")],
                xml_id="initiator_space",
                vendor_extensions=[VENDOR_EXTENSION],
            ),
            connection_required=True,
            bits_in_lau=ipxact.Expression("8"),
            bit_steering=ipxact.Expression("0"),
            endianness="little",
            parameters=[_parameter("BUS_P")],
            display_name="CPU initiator",
            short_description="initiator",
            description="initiator side",
            xml_id="cpu_initiator",
            vendor_extensions=[VENDOR_EXTENSION],
        ),
        ipxact.BusInterface(
            name="regs_target",
            bus_type=apb,
            mode=ipxact.InterfaceMode.TARGET,
            target=ipxact.TargetInterface(
                memory_map_ref="main_mm",
                mode_refs=[ipxact.ModeRef("normal")],
                file_set_ref_groups=[
                    ipxact.FileSetRefGroup(group="rtl", file_set_refs=[_ref("rtl_files")], xml_id="target_group")
                ],
            ),
            bit_steering=ipxact.Expression("0"),
            other_attributes=FOREIGN_ATTRIBUTES,
        ),
        ipxact.BusInterface(
            name="bridge_target",
            bus_type=apb,
            mode=ipxact.InterfaceMode.TARGET,
            target=ipxact.TargetInterface(
                transparent_bridges=[
                    ipxact.TransparentBridge(
                        initiator_ref="cpu_initiator", xml_id="bridge0", vendor_extensions=[VENDOR_EXTENSION]
                    )
                ]
            ),
            bit_steering=ipxact.Expression("0"),
        ),
        ipxact.BusInterface(
            name="sys_if",
            bus_type=apb,
            mode=ipxact.InterfaceMode.SYSTEM,
            system=ipxact.SystemInterface(group="sysgroup"),
            bit_steering=ipxact.Expression("0"),
        ),
        ipxact.BusInterface(
            name="mirror_initiator",
            bus_type=apb,
            mode=ipxact.InterfaceMode.MIRRORED_INITIATOR,
            mirrored_initiator=ipxact.MirroredInitiatorInterface(other_attributes=FOREIGN_ATTRIBUTES, text="free text"),
            bit_steering=ipxact.Expression("0"),
        ),
        ipxact.BusInterface(
            name="mirror_initiator_content",
            bus_type=apb,
            mode=ipxact.InterfaceMode.MIRRORED_INITIATOR,
            mirrored_initiator=ipxact.MirroredInitiatorInterface(
                content=[
                    '<other:mirror xmlns:other="http://example.org/other"'
                    ' xmlns:ipxact="http://www.accellera.org/XMLSchema/IPXACT/1685-2022"'
                    ' xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">any content</other:mirror>'
                ]
            ),
            bit_steering=ipxact.Expression("0"),
        ),
        ipxact.BusInterface(
            name="mirror_target",
            bus_type=apb,
            mode=ipxact.InterfaceMode.MIRRORED_TARGET,
            mirrored_target=ipxact.MirroredTargetInterface(
                remap_addresses=[
                    ipxact.RemapAddress(value=ipxact.Expression("0x1000"), mode_refs=[_normal_mode_ref()], xml_id="remap0"),
                    ipxact.RemapAddress(value=ipxact.Expression("0x2000")),
                ],
                range=ipxact.Expression("0x100"),
            ),
            bit_steering=ipxact.Expression("0"),
        ),
        ipxact.BusInterface(
            name="mirror_system",
            bus_type=apb,
            mode=ipxact.InterfaceMode.MIRRORED_SYSTEM,
            mirrored_system=ipxact.SystemInterface(group="sysgroup"),
            bit_steering=ipxact.Expression("0"),
        ),
        ipxact.BusInterface(
            name="monitor_if",
            bus_type=apb,
            mode=ipxact.InterfaceMode.MONITOR,
            monitor=ipxact.MonitorInterface(interface_mode=ipxact.InterfaceMode.SYSTEM, group="sysgroup"),
            bit_steering=ipxact.Expression("0"),
        ),
    ]


def build_wide_component() -> ipxact.Component:
    """A Component covering every section that can be written as schema-valid IP-XACT."""
    return ipxact.Component(
        vlnv=ipxact.VLNV("example.org", "ip", "wide_coverage", "2.0"),
        display_name="Wide coverage",
        short_description="Every writable component section",
        description="Hand-built component exercising the writer end to end.",
        xml_id="wide_coverage",
        external_type_definitions=[
            ipxact.ExternalTypeDefinitionsRef(
                name="shared_types",
                type_definitions=ipxact.VLNVRef("example.org", "types", "shared", "1.0", {"SHARED_P": ipxact.Expression("8")}),
                view_links=[
                    ipxact.ViewLink(
                        external_view_ref="ext_rtl",
                        view_ref="rtl",
                        xml_id="view_link",
                        vendor_extensions=[VENDOR_EXTENSION],
                    )
                ],
                mode_links=[
                    ipxact.ModeLink(
                        external_mode_ref="ext_normal",
                        mode_ref="normal",
                        xml_id="mode_link",
                        vendor_extensions=[VENDOR_EXTENSION],
                    )
                ],
                reset_type_links=[
                    ipxact.ResetTypeLink(
                        external_reset_type_ref="ext_hard",
                        reset_type_ref="HARD",
                        xml_id="reset_type_link",
                        vendor_extensions=[VENDOR_EXTENSION],
                    )
                ],
                display_name="Shared types",
                short_description="shared",
                description="the shared type definitions",
                xml_id="shared_types",
                vendor_extensions=[VENDOR_EXTENSION],
            )
        ],
        power_domains=[
            ipxact.PowerDomain(
                name="PD_MAIN",
                always_on=ipxact.Expression("1"),
                parameters=[_parameter("PD_P")],
                display_name="Main domain",
                short_description="main",
                description="the main power domain",
                xml_id="pd_main",
                vendor_extensions=[VENDOR_EXTENSION],
            ),
            ipxact.PowerDomain(name="PD_SUB", sub_domain_of="PD_MAIN"),
        ],
        bus_interfaces=_bus_interfaces(),
        indirect_interfaces=[
            ipxact.IndirectInterface(
                name="indirect",
                indirect_address_ref=ipxact.FieldReference(
                    field_ref=ipxact.IndexedRef("ENABLE"),
                    register_ref=ipxact.IndexedRef("CTRL"),
                    address_block_ref=ipxact.IndexedRef("regs"),
                    memory_map_ref="main_mm",
                    memory_remap_ref="remap",
                ),
                indirect_data_ref=ipxact.FieldReference(
                    field_ref=ipxact.IndexedRef("BUSY"),
                    register_ref=ipxact.IndexedRef("STATUS"),
                    register_file_refs=[ipxact.IndexedRef("RF", indices=[ipxact.Expression("1")])],
                    address_block_ref=ipxact.IndexedRef("regs"),
                    memory_map_ref="main_mm",
                ),
                memory_map_ref="main_mm",
                bits_in_lau=ipxact.Expression("8"),
                endianness="little",
                display_name="Indirect",
                short_description="indirect",
                description="indirectly addressed map",
                parameters=[_parameter("IND_P")],
                xml_id="indirect",
                vendor_extensions=[VENDOR_EXTENSION],
            ),
            ipxact.IndirectInterface(
                name="bridged_indirect",
                indirect_address_ref=ipxact.FieldReference(
                    field_ref=ipxact.IndexedRef("BIT"),
                    register_ref=ipxact.IndexedRef("LOCAL"),
                    address_block_ref=ipxact.IndexedRef("local_regs"),
                    address_space_ref="sys_space",
                ),
                indirect_data_ref=ipxact.FieldReference(
                    field_ref=ipxact.IndexedRef("BIT"),
                    register_ref=ipxact.IndexedRef("BANKED"),
                    address_block_ref=ipxact.IndexedRef("banked_regs"),
                    bank_refs=[ipxact.IndexedRef("outer", xml_id="bank_ref")],
                    memory_map_ref="banked_mm",
                ),
                transparent_bridges=[ipxact.TransparentBridge(initiator_ref="cpu_initiator")],
                other_attributes=FOREIGN_ATTRIBUTES,
            ),
        ],
        channels=[
            ipxact.Channel(
                name="ch0",
                bus_interface_refs=[_ref("mirror_initiator", xml_id="ch0_first"), _ref("mirror_target")],
                display_name="Channel",
                short_description="channel",
                description="mirrored pair",
                xml_id="ch0",
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
                        sub_port_refs=[ipxact.SubPortReference(sub_port_ref="lower")],
                        part_select=ipxact.PartSelect(range=_range("7", "0")),
                        display_name="Data slice",
                        short_description="data slice",
                        description="low byte",
                        xml_id="data_slice",
                    )
                ],
                field_slices=[
                    ipxact.FieldSlice(
                        name="enable_slice",
                        field_ref=ipxact.FieldReference(
                            field_ref=ipxact.IndexedRef("ENABLE"),
                            register_ref=ipxact.IndexedRef("CTRL"),
                            address_block_ref=ipxact.IndexedRef("regs"),
                            memory_map_ref="main_mm",
                            range=_range("0", "0"),
                        ),
                        display_name="Enable slice",
                        short_description="enable slice",
                        description="the enable bit",
                        xml_id="enable_slice",
                    )
                ],
                condition=ipxact.Expression("1"),
                display_name="Normal",
                short_description="normal",
                description="the normal mode",
                xml_id="normal_mode",
                vendor_extensions=[VENDOR_EXTENSION],
            ),
            ipxact.Mode(name="turbo"),
        ],
        address_spaces=[
            ipxact.AddressSpace(
                name="sys_space",
                range=ipxact.Expression("0x10000"),
                width=ipxact.Expression("32"),
                segments=[
                    ipxact.Segment(
                        name="seg0",
                        address_offset=ipxact.Expression("0x0"),
                        range=ipxact.Expression("0x1000"),
                        display_name="Segment 0",
                        short_description="segment",
                        description="first segment",
                        xml_id="seg0",
                        vendor_extensions=[VENDOR_EXTENSION],
                    )
                ],
                address_unit_bits=ipxact.Expression("8"),
                local_memory_map=ipxact.LocalMemoryMap(
                    name="local_mm",
                    items=[
                        ipxact.AddressBlock(
                            name="local_regs",
                            range=ipxact.Expression("0x10"),
                            width=ipxact.Expression("32"),
                            base_address=ipxact.Expression("0x0"),
                            registers=[
                                ipxact.Register(
                                    name="LOCAL",
                                    address_offset=ipxact.Expression("0x0"),
                                    size=ipxact.Expression("32"),
                                    fields=[ipxact.Field(name="BIT", bit_offset=ipxact.Expression("0"), bit_width=ipxact.Expression("1"))],
                                )
                            ],
                        )
                    ],
                    display_name="Local map",
                    short_description="local",
                    description="address space local map",
                    xml_id="local_mm",
                    vendor_extensions=[VENDOR_EXTENSION],
                ),
                display_name="System space",
                short_description="system space",
                description="the cpu address space",
                parameters=[_parameter("AS_P")],
                xml_id="sys_space",
                vendor_extensions=[VENDOR_EXTENSION],
            )
        ],
        memory_maps=[
            ipxact.MemoryMap(
                name="main_mm",
                items=[
                    _regs_block(),
                    ipxact.AddressBlock(
                        name="typed_block",
                        base_address=ipxact.Expression("0x1000"),
                        address_block_definition_ref=_type_definitions_ref("typed_block"),
                    ),
                    ipxact.SubspaceMap(
                        name="bridged",
                        initiator_ref="cpu_initiator",
                        base_address=ipxact.Expression("0x2000"),
                        segment_ref="seg0",
                        display_name="Bridged space",
                        short_description="bridged",
                        description="mapped through the bridge",
                        parameters=[_parameter("SS_P")],
                        xml_id="bridged",
                        vendor_extensions=[VENDOR_EXTENSION],
                    ),
                ],
                memory_remaps=[
                    ipxact.MemoryRemap(
                        name="remap",
                        mode_refs=[_normal_mode_ref()],
                        items=[
                            ipxact.AddressBlock(
                                name="remapped",
                                range=ipxact.Expression("0x10"),
                                width=ipxact.Expression("32"),
                                base_address=ipxact.Expression("0x3000"),
                                registers=[
                                    ipxact.Register(
                                        name="REMAPPED",
                                        address_offset=ipxact.Expression("0x0"),
                                        size=ipxact.Expression("32"),
                                        fields=[ipxact.Field(name="BIT", bit_offset=ipxact.Expression("0"), bit_width=ipxact.Expression("1"))],
                                    )
                                ],
                            )
                        ],
                        display_name="Remap",
                        short_description="remap",
                        description="mode-selected extra content",
                        xml_id="remap",
                        vendor_extensions=[VENDOR_EXTENSION],
                    ),
                    ipxact.MemoryRemap(
                        name="typed_remap",
                        mode_refs=[ipxact.ModeRef(name="turbo", priority=0)],
                        remap_definition_ref=_type_definitions_ref("typed_remap"),
                    ),
                ],
                address_unit_bits=ipxact.Expression("8"),
                shared=ipxact.SharedType.YES,
                display_name="Main map",
                short_description="main",
                description="the component memory map",
                xml_id="main_mm",
                vendor_extensions=[VENDOR_EXTENSION],
            ),
            ipxact.MemoryMap(name="typed_mm", memory_map_definition_ref=_type_definitions_ref("typed_map")),
            # The banked map is shared with build_banked_component, so bank references resolve here too.
            _banked_memory_map(),
        ],
        model=_model(),
        component_generators=[
            ipxact.ComponentGenerator(
                name="gen0",
                generator_exe="./gen.py",
                phase=ipxact.Expression("1.0"),
                parameters=[_parameter("GEN_P")],
                api_type=_t("none", xml_id="gen_api"),
                api_service="REST",
                transport_methods=[_t("file", xml_id="gen_transport")],
                transport_methods_xml_id="gen_transports",
                groups=[_t("generators", xml_id="gen_group")],
                scope="entity",
                hidden=True,
                display_name="Generator",
                short_description="generator",
                description="a component generator",
                xml_id="gen0",
                vendor_extensions=[VENDOR_EXTENSION],
            )
        ],
        choices=[
            ipxact.Choice(
                name="ch_values",
                enumerations=[
                    ipxact.ChoiceEnumeration(value=ipxact.Expression("1"), text="one", help="the first value"),
                    ipxact.ChoiceEnumeration(value=ipxact.Expression("2")),
                ],
                xml_id="ch_values",
            )
        ],
        file_sets=_file_sets(),
        clearbox_elements=[
            ipxact.ClearboxElement(
                name="cb0",
                clearbox_type="signal",
                driveable=True,
                parameters=[_parameter("CB_P")],
                display_name="Clearbox",
                short_description="clearbox",
                description="an internal signal",
                xml_id="cb0",
                vendor_extensions=[VENDOR_EXTENSION],
            )
        ],
        cpus=[
            ipxact.Cpu(
                name="cpu0",
                range=ipxact.Expression("0x10000"),
                width=ipxact.Expression("32"),
                memory_map_ref="main_mm",
                regions=[
                    ipxact.CpuRegion(
                        name="region0",
                        address_offset=ipxact.Expression("0x0"),
                        range=ipxact.Expression("0x1000"),
                        display_name="Region 0",
                        short_description="region",
                        description="the first region",
                        xml_id="region0",
                        vendor_extensions=[VENDOR_EXTENSION],
                    )
                ],
                address_unit_bits=ipxact.Expression("8"),
                executable_images=[
                    ipxact.ExecutableImage(
                        name="firmware",
                        image_id="fw0",
                        image_type="elf",
                        parameters=[_parameter("IMAGE_P")],
                        language_tools=ipxact.LanguageTools(
                            file_builders=[
                                ipxact.FileBuilder(
                                    file_type=ipxact.FileType("cSource"),
                                    command=ipxact.Expression("gcc"),
                                    flags=ipxact.Expression("-O2"),
                                    vendor_extensions=[VENDOR_EXTENSION],
                                )
                            ],
                            linker=ipxact.Expression("ld"),
                            linker_flags=ipxact.Expression("-T"),
                            linker_command_file=ipxact.LinkerCommandFile(
                                name=ipxact.Expression("link.ld"),
                                command_line_switch=ipxact.Expression("-T"),
                                enable=ipxact.Expression("1"),
                                generator_refs=[_t("gen0", xml_id="linker_generator")],
                                xml_id="linker_file",
                                vendor_extensions=[VENDOR_EXTENSION],
                            ),
                        ),
                        file_set_ref_group=ipxact.FileSetRefGroup(file_set_refs=[_ref("rtl_files")]),
                        display_name="Firmware",
                        short_description="firmware",
                        description="the boot firmware",
                        xml_id="firmware",
                        vendor_extensions=[VENDOR_EXTENSION],
                    )
                ],
                parameters=[_parameter("CPU_P")],
                display_name="CPU",
                short_description="cpu",
                description="the processor",
                xml_id="cpu0",
                vendor_extensions=[VENDOR_EXTENSION],
            )
        ],
        other_clock_drivers=[
            ipxact.OtherClockDriver(
                clock_name="ref_clk",
                clock_period=ipxact.Expression("20"),
                clock_pulse_offset=ipxact.Expression("0"),
                clock_pulse_value=ipxact.Expression("1"),
                clock_pulse_duration=ipxact.Expression("10"),
                clock_source="external",
                period_units="ps",
                offset_units="ps",
                duration_units="ps",
                xml_id="ref_clk",
            )
        ],
        reset_types=[
            ipxact.ResetType(
                name="HARD",
                display_name="Hard reset",
                short_description="hard",
                description="power-on reset",
                xml_id="hard_reset",
                vendor_extensions=[VENDOR_EXTENSION],
            )
        ],
        parameters=[
            ipxact.Parameter(
                name="BAUD_RATE",
                value=ipxact.Expression("115200", xml_id="baud_value"),
                display_name="Baud rate",
                short_description="serial speed",
                description="the configured baud rate",
                vectors=[ipxact.Vector(left=ipxact.Expression("31"), right=ipxact.Expression("0"))],
                arrays=[ipxact.ArrayBound(left=ipxact.Expression("1"), right=ipxact.Expression("0"))],
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
                xml_id="baud_rate",
                vendor_extensions=[VENDOR_EXTENSION],
            ),
            ipxact.Parameter(name="TOOL_P", value=ipxact.Expression("0"), parameter_id="TOOL_P", other_attributes=FOREIGN_ATTRIBUTES),
        ],
        assertions=[
            ipxact.Assertion(
                name="baud_positive",
                assert_expression=ipxact.Expression("1"),
                display_name="Baud positive",
                short_description="positive",
                description="the baud rate must be positive",
                xml_id="baud_positive",
            )
        ],
        vendor_extensions=[VENDOR_EXTENSION],
    )


def _banked_memory_map() -> ipxact.MemoryMap:
    return ipxact.MemoryMap(
        name="banked_mm",
        items=[
            ipxact.Bank(
                name="outer",
                bank_alignment=ipxact.BankAlignment.SERIAL,
                base_address=ipxact.Expression("0x0"),
                access_handles=[ipxact.AccessHandle(path_segments=[ipxact.Expression("u_outer")])],
                items=[
                    ipxact.AddressBlock(
                        name="banked_regs",
                        range=ipxact.Expression("0x10"),
                        width=ipxact.Expression("32"),
                        registers=[
                            ipxact.Register(
                                name="BANKED",
                                address_offset=ipxact.Expression("0x0"),
                                size=ipxact.Expression("32"),
                                fields=[ipxact.Field(name="BIT", bit_offset=ipxact.Expression("0"), bit_width=ipxact.Expression("1"))],
                            )
                        ],
                    ),
                    ipxact.Bank(
                        name="inner",
                        bank_alignment=ipxact.BankAlignment.PARALLEL,
                        items=[ipxact.AddressBlock(name="inner_regs", range=ipxact.Expression("0x8"), width=ipxact.Expression("32"))],
                        usage=ipxact.UsageType.MEMORY,
                    ),
                    ipxact.Bank(
                        name="typed_inner",
                        bank_alignment=ipxact.BankAlignment.PARALLEL,
                        bank_definition_ref=_type_definitions_ref("typed_bank"),
                    ),
                ],
                usage=ipxact.UsageType.REGISTER,
                volatile=False,
                access_policies=[ipxact.AccessPolicy(access=ipxact.AccessType.READ_WRITE)],
                parameters=[_parameter("BANK_P")],
                display_name="Outer bank",
                short_description="outer",
                description="a bank of blocks",
                xml_id="outer_bank",
                vendor_extensions=[VENDOR_EXTENSION],
            )
        ],
    )


def build_banked_component() -> ipxact.Component:
    """A Component built around banks and a structured port, fully schema-valid."""
    return ipxact.Component(
        vlnv=ipxact.VLNV("example.org", "ip", "banked", "1.0"),
        bus_interfaces=[
            ipxact.BusInterface(
                name="init_if",
                bus_type=ipxact.VLNVRef("amba.com", "AMBA4", "APB4", "r0p0_0"),
                mode=ipxact.InterfaceMode.INITIATOR,
                initiator=ipxact.InitiatorInterface(),
                bit_steering=ipxact.Expression("0"),
            )
        ],
        memory_maps=[
            ipxact.MemoryMap(
                name="banked_mm",
                items=[
                    ipxact.Bank(
                        name="outer",
                        bank_alignment=ipxact.BankAlignment.SERIAL,
                        base_address=ipxact.Expression("0x0"),
                        items=[
                            ipxact.AddressBlock(
                                name="banked_regs",
                                range=ipxact.Expression("0x10"),
                                width=ipxact.Expression("32"),
                                registers=[
                                    ipxact.Register(
                                        name="BANKED",
                                        address_offset=ipxact.Expression("0x0"),
                                        size=ipxact.Expression("32"),
                                        fields=[ipxact.Field(name="BIT", bit_offset=ipxact.Expression("0"), bit_width=ipxact.Expression("1"))],
                                    )
                                ],
                            ),
                            ipxact.SubspaceMap(name="banked_sub", initiator_ref="init_if"),
                        ],
                    )
                ],
            )
        ],
        model=ipxact.Model(
            views=[ipxact.View(name="rtl")],
            ports=[
                ipxact.Port(
                    name="bus",
                    structured=ipxact.StructuredPort(
                        struct_type="struct",
                        vectors=[ipxact.Vector(left=ipxact.Expression("1"), right=ipxact.Expression("0"), vector_id="SV0")],
                        sub_ports=[
                            ipxact.SubPort(
                                name="valid",
                                wire=ipxact.WirePort(direction=ipxact.Direction.OUT),
                                arrays=[ipxact.ArrayBound(left=ipxact.Expression("7"), right=ipxact.Expression("0"))],
                                access=ipxact.PortAccess(port_access_type="ptr"),
                                display_name="Valid",
                                short_description="valid",
                                description="handshake valid",
                                is_io=True,
                                xml_id="valid_sub_port",
                                vendor_extensions=[VENDOR_EXTENSION],
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
                                    struct_port_type_defs=[
                                        ipxact.StructPortTypeDef(
                                            type_name="ready_if",
                                            role="consumer",
                                            view_refs=[_t("rtl")],
                                            xml_id="ready_type",
                                        )
                                    ],
                                    packed=False,
                                    phantom=True,
                                ),
                            ),
                        ],
                        struct_port_type_defs=[
                            ipxact.StructPortTypeDef(
                                type_name="bus_req_t",
                                constrained=["WIDTH", "DEPTH"],
                                type_definitions=[_t("bus_pkg.sv")],
                                type_parameters=[
                                    ipxact.ModuleParameter(name="WIDTH", value=ipxact.Expression("32"), data_type="int")
                                ],
                                view_refs=[_t("rtl")],
                            )
                        ],
                        packed=True,
                        direction=ipxact.Direction.OUT,
                    ),
                    field_maps=[
                        ipxact.FieldMap(
                            field_slice=ipxact.FieldReference(
                                field_ref=ipxact.IndexedRef("BIT"),
                                register_ref=ipxact.IndexedRef("BANKED"),
                                address_block_ref=ipxact.IndexedRef("banked_regs"),
                                bank_refs=[ipxact.IndexedRef("outer")],
                                memory_map_ref="banked_mm",
                            ),
                            sub_port_refs=[ipxact.SubPortReference(sub_port_ref="valid")],
                        )
                    ],
                )
            ],
        ),
    )
