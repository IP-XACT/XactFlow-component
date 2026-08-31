from __future__ import annotations

from typing import Sequence

from lxml import etree

from ipxact.schema.component_sections import (
    ClearboxElement,
    ComponentGenerator,
    Cpu,
    ExternalTypeDefinitionsRef,
    Mode,
    OtherClockDriver,
    PowerDomain,
    ResetType,
)

from .common_writer import (
    add_clock_driver_body,
    add_field_reference_group,
    add_name_group,
    add_parameters,
    add_part_select,
    add_sub_port_references,
    add_text,
    add_texts,
    bool_str,
    sub,
    write_vendor_extensions,
    write_vlnv_ref,
)


def add_external_type_definitions(
    parent: etree._Element, external_type_definitions: Sequence[ExternalTypeDefinitionsRef]
) -> None:
    if not external_type_definitions:
        return
    container = sub(parent, "typeDefinitions")
    for reference in external_type_definitions:
        elem = sub(container, "externalTypeDefinitions")
        add_name_group(elem, reference.name)
        elem.append(write_vlnv_ref("typeDefinitionsRef", reference.type_definitions))


def add_power_domains(parent: etree._Element, power_domains: Sequence[PowerDomain]) -> None:
    if not power_domains:
        return
    container = sub(parent, "powerDomains")
    for power_domain in power_domains:
        elem = sub(container, "powerDomain")
        add_name_group(elem, power_domain.name)
        add_text(elem, "alwaysOn", power_domain.always_on)
        add_text(elem, "subDomainOf", power_domain.sub_domain_of)
        add_parameters(elem, power_domain.parameters)
        write_vendor_extensions(elem, power_domain.vendor_extensions)


def add_modes(parent: etree._Element, modes: Sequence[Mode]) -> None:
    if not modes:
        return
    container = sub(parent, "modes")
    for mode in modes:
        elem = sub(container, "mode")
        add_name_group(elem, mode.name)
        for port_slice in mode.port_slices:
            slice_elem = sub(elem, "portSlice")
            add_name_group(slice_elem, port_slice.name, port_slice.display_name, description=port_slice.description)
            sub(slice_elem, "portRef", portRef=port_slice.port_ref)
            add_sub_port_references(slice_elem, port_slice.sub_port_refs)
            add_part_select(slice_elem, port_slice.part_select)
        for field_slice in mode.field_slices:
            slice_elem = sub(elem, "fieldSlice")
            add_name_group(slice_elem, field_slice.name, field_slice.display_name, description=field_slice.description)
            add_field_reference_group(slice_elem, field_slice.field_ref, with_range=True)
        add_text(elem, "condition", mode.condition)
        write_vendor_extensions(elem, mode.vendor_extensions)


def add_cpus(parent: etree._Element, cpus: Sequence[Cpu]) -> None:
    if not cpus:
        return
    container = sub(parent, "cpus")
    for cpu in cpus:
        elem = sub(container, "cpu")
        add_name_group(elem, cpu.name)
        sub(elem, "range", cpu.range)
        sub(elem, "width", cpu.width)
        if cpu.regions:
            regions = sub(elem, "regions")
            for region in cpu.regions:
                region_elem = sub(regions, "region")
                add_name_group(region_elem, region.name)
                sub(region_elem, "addressOffset", region.address_offset)
                sub(region_elem, "range", region.range)
                write_vendor_extensions(region_elem, region.vendor_extensions)
        add_text(elem, "addressUnitBits", cpu.address_unit_bits)
        sub(elem, "memoryMapRef", cpu.memory_map_ref)
        add_parameters(elem, cpu.parameters)
        write_vendor_extensions(elem, cpu.vendor_extensions)


def add_clearbox_elements(parent: etree._Element, clearbox_elements: Sequence[ClearboxElement]) -> None:
    if not clearbox_elements:
        return
    container = sub(parent, "clearboxElements")
    for clearbox_element in clearbox_elements:
        elem = sub(container, "clearboxElement")
        add_name_group(elem, clearbox_element.name)
        sub(elem, "clearboxType", clearbox_element.clearbox_type)
        if clearbox_element.driveable:
            sub(elem, "driveable", bool_str(True))
        add_parameters(elem, clearbox_element.parameters)
        write_vendor_extensions(elem, clearbox_element.vendor_extensions)


def add_component_generators(parent: etree._Element, generators: Sequence[ComponentGenerator]) -> None:
    if not generators:
        return
    container = sub(parent, "componentGenerators")
    for generator in generators:
        elem = sub(
            container,
            "componentGenerator",
            hidden=bool_str(True) if generator.hidden else None,
            scope=generator.scope if generator.scope != "instance" else None,
        )
        add_name_group(elem, generator.name)
        add_text(elem, "phase", generator.phase)
        add_parameters(elem, generator.parameters)
        add_text(elem, "apiType", generator.api_type)
        sub(elem, "apiService", generator.api_service)
        if generator.transport_methods:
            transport_methods = sub(elem, "transportMethods")
            add_texts(transport_methods, "transportMethod", generator.transport_methods)
        sub(elem, "generatorExe", generator.generator_exe)
        write_vendor_extensions(elem, generator.vendor_extensions)
        # instanceGeneratorType extends generatorType, so its group elements follow the
        # base type's content rather than sitting with the other name-like children.
        add_texts(elem, "group", generator.groups)


def add_reset_types(parent: etree._Element, reset_types: Sequence[ResetType]) -> None:
    if not reset_types:
        return
    container = sub(parent, "resetTypes")
    for reset_type in reset_types:
        elem = sub(container, "resetType")
        add_name_group(elem, reset_type.name, reset_type.display_name, description=reset_type.description)
        write_vendor_extensions(elem, reset_type.vendor_extensions)


def add_other_clock_drivers(parent: etree._Element, clock_drivers: Sequence[OtherClockDriver]) -> None:
    if not clock_drivers:
        return
    container = sub(parent, "otherClockDrivers")
    for clock_driver in clock_drivers:
        elem = sub(
            container,
            "otherClockDriver",
            clockName=clock_driver.clock_name,
            clockSource=clock_driver.clock_source,
        )
        add_clock_driver_body(elem, clock_driver)
