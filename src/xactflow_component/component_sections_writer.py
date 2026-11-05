from __future__ import annotations

from typing import Optional, Sequence

from lxml import etree

from ipxact.schema.component_sections import (
    ClearboxElement,
    ComponentGenerator,
    Cpu,
    CpuRegion,
    ExecutableImage,
    ExternalTypeDefinitionsRef,
    FieldSlice,
    LanguageTools,
    LinkerCommandFile,
    Mode,
    ModeLink,
    OtherClockDriver,
    PortSlice,
    PowerDomain,
    ResetType,
    ResetTypeLink,
    ViewLink,
)

from .common_writer import (
    add_clock_driver_body,
    add_expression,
    add_field_reference_group,
    add_file_builder,
    add_file_set_ref_group,
    add_items,
    add_name_group,
    add_parameters,
    add_part_select,
    add_sub_port_references,
    add_text,
    add_text_value,
    add_text_values,
    bool_str,
    element,
    sub,
    write_vendor_extensions,
    write_vlnv_ref,
)


def _write_link(tag: str, xml_id: Optional[str], refs: Sequence[tuple[str, str, str]], vendor_extensions: Sequence[str]) -> etree._Element:
    """Write a viewLink/modeLink/resetTypeLink: two attribute-only references, external first."""
    elem = element(tag, xml_id=xml_id)
    for ref_tag, attribute, value in refs:
        sub(elem, ref_tag, **{attribute: value})
    write_vendor_extensions(elem, vendor_extensions)
    return elem


def _write_view_link(link: ViewLink) -> etree._Element:
    refs = [("externalViewReference", "viewRef", link.external_view_ref), ("viewReference", "viewRef", link.view_ref)]
    return _write_link("viewLink", link.xml_id, refs, link.vendor_extensions)


def _write_mode_link(link: ModeLink) -> etree._Element:
    refs = [("externalModeReference", "modeRef", link.external_mode_ref), ("modeReference", "modeRef", link.mode_ref)]
    return _write_link("modeLink", link.xml_id, refs, link.vendor_extensions)


def _write_reset_type_link(link: ResetTypeLink) -> etree._Element:
    refs = [
        ("externalResetTypeReference", "resetTypeRef", link.external_reset_type_ref),
        ("resetTypeReference", "resetTypeRef", link.reset_type_ref),
    ]
    return _write_link("resetTypeLink", link.xml_id, refs, link.vendor_extensions)


def _write_external_type_definitions(reference: ExternalTypeDefinitionsRef) -> etree._Element:
    elem = element("externalTypeDefinitions", xml_id=reference.xml_id)
    add_name_group(elem, reference)
    elem.append(write_vlnv_ref("typeDefinitionsRef", reference.type_definitions))
    add_items(elem, "viewLinks", reference.view_links, _write_view_link)
    add_items(elem, "modeLinks", reference.mode_links, _write_mode_link)
    add_items(elem, "resetTypeLinks", reference.reset_type_links, _write_reset_type_link)
    write_vendor_extensions(elem, reference.vendor_extensions)
    return elem


def add_external_type_definitions(
    parent: etree._Element, external_type_definitions: Sequence[ExternalTypeDefinitionsRef]
) -> None:
    add_items(parent, "typeDefinitions", external_type_definitions, _write_external_type_definitions)


def _write_power_domain(power_domain: PowerDomain) -> etree._Element:
    elem = element("powerDomain", xml_id=power_domain.xml_id)
    add_name_group(elem, power_domain)
    add_expression(elem, "alwaysOn", power_domain.always_on)
    add_text(elem, "subDomainOf", power_domain.sub_domain_of)
    add_parameters(elem, power_domain.parameters)
    write_vendor_extensions(elem, power_domain.vendor_extensions)
    return elem


def add_power_domains(parent: etree._Element, power_domains: Sequence[PowerDomain]) -> None:
    add_items(parent, "powerDomains", power_domains, _write_power_domain)


def _add_port_slice(parent: etree._Element, port_slice: PortSlice) -> None:
    elem = sub(parent, "portSlice", xml_id=port_slice.xml_id)
    add_name_group(elem, port_slice)
    sub(elem, "portRef", portRef=port_slice.port_ref)
    add_sub_port_references(elem, port_slice.sub_port_refs)
    add_part_select(elem, port_slice.part_select)


def _add_field_slice(parent: etree._Element, field_slice: FieldSlice) -> None:
    elem = sub(parent, "fieldSlice", xml_id=field_slice.xml_id)
    add_name_group(elem, field_slice)
    add_field_reference_group(elem, field_slice.field_ref, with_range=True)


def _write_mode(mode: Mode) -> etree._Element:
    elem = element("mode", xml_id=mode.xml_id)
    add_name_group(elem, mode)
    for port_slice in mode.port_slices:
        _add_port_slice(elem, port_slice)
    for field_slice in mode.field_slices:
        _add_field_slice(elem, field_slice)
    add_expression(elem, "condition", mode.condition)
    write_vendor_extensions(elem, mode.vendor_extensions)
    return elem


def add_modes(parent: etree._Element, modes: Sequence[Mode]) -> None:
    add_items(parent, "modes", modes, _write_mode)


def _write_cpu_region(region: CpuRegion) -> etree._Element:
    elem = element("region", xml_id=region.xml_id)
    add_name_group(elem, region)
    add_expression(elem, "addressOffset", region.address_offset)
    add_expression(elem, "range", region.range)
    write_vendor_extensions(elem, region.vendor_extensions)
    return elem


def _add_linker_command_file(parent: etree._Element, command_file: Optional[LinkerCommandFile]) -> None:
    if command_file is None:
        return
    elem = sub(parent, "linkerCommandFile", xml_id=command_file.xml_id)
    add_expression(elem, "name", command_file.name)
    add_expression(elem, "commandLineSwitch", command_file.command_line_switch)
    add_expression(elem, "enable", command_file.enable)
    add_text_values(elem, "generatorRef", command_file.generator_refs)
    write_vendor_extensions(elem, command_file.vendor_extensions)


def _add_language_tools(parent: etree._Element, language_tools: Optional[LanguageTools]) -> None:
    if language_tools is None:
        return
    elem = sub(parent, "languageTools")
    for builder in language_tools.file_builders:
        add_file_builder(elem, builder, tag="fileBuilder")
    add_expression(elem, "linker", language_tools.linker)
    add_expression(elem, "linkerFlags", language_tools.linker_flags)
    _add_linker_command_file(elem, language_tools.linker_command_file)


def _add_executable_image(parent: etree._Element, image: ExecutableImage) -> None:
    elem = sub(parent, "executableImage", xml_id=image.xml_id, imageId=image.image_id, imageType=image.image_type)
    add_name_group(elem, image)
    add_parameters(elem, image.parameters)
    _add_language_tools(elem, image.language_tools)
    add_file_set_ref_group(elem, image.file_set_ref_group)
    write_vendor_extensions(elem, image.vendor_extensions)


def _write_cpu(cpu: Cpu) -> etree._Element:
    elem = element("cpu", xml_id=cpu.xml_id)
    add_name_group(elem, cpu)
    add_expression(elem, "range", cpu.range)
    add_expression(elem, "width", cpu.width)
    add_items(elem, "regions", cpu.regions, _write_cpu_region)
    add_expression(elem, "addressUnitBits", cpu.address_unit_bits)
    for image in cpu.executable_images:
        _add_executable_image(elem, image)
    sub(elem, "memoryMapRef", cpu.memory_map_ref)
    add_parameters(elem, cpu.parameters)
    write_vendor_extensions(elem, cpu.vendor_extensions)
    return elem


def add_cpus(parent: etree._Element, cpus: Sequence[Cpu]) -> None:
    add_items(parent, "cpus", cpus, _write_cpu)


def _write_clearbox_element(clearbox_element: ClearboxElement) -> etree._Element:
    elem = element("clearboxElement", xml_id=clearbox_element.xml_id)
    add_name_group(elem, clearbox_element)
    sub(elem, "clearboxType", clearbox_element.clearbox_type)
    if clearbox_element.driveable:
        sub(elem, "driveable", bool_str(True))
    add_parameters(elem, clearbox_element.parameters)
    write_vendor_extensions(elem, clearbox_element.vendor_extensions)
    return elem


def add_clearbox_elements(parent: etree._Element, clearbox_elements: Sequence[ClearboxElement]) -> None:
    add_items(parent, "clearboxElements", clearbox_elements, _write_clearbox_element)


def _write_component_generator(generator: ComponentGenerator) -> etree._Element:
    elem = element(
        "componentGenerator",
        xml_id=generator.xml_id,
        hidden=bool_str(True) if generator.hidden else None,
        scope=generator.scope if generator.scope != "instance" else None,
    )
    add_name_group(elem, generator)
    add_expression(elem, "phase", generator.phase)
    add_parameters(elem, generator.parameters)
    add_text_value(elem, "apiType", generator.api_type)
    sub(elem, "apiService", generator.api_service)
    if generator.transport_methods:
        transport_methods = sub(elem, "transportMethods", xml_id=generator.transport_methods_xml_id)
        add_text_values(transport_methods, "transportMethod", generator.transport_methods)
    sub(elem, "generatorExe", generator.generator_exe)
    write_vendor_extensions(elem, generator.vendor_extensions)
    # instanceGeneratorType extends generatorType, so its group elements follow the
    # base type's content rather than sitting with the other name-like children.
    add_text_values(elem, "group", generator.groups)
    return elem


def add_component_generators(parent: etree._Element, generators: Sequence[ComponentGenerator]) -> None:
    add_items(parent, "componentGenerators", generators, _write_component_generator)


def _write_reset_type(reset_type: ResetType) -> etree._Element:
    elem = element("resetType", xml_id=reset_type.xml_id)
    add_name_group(elem, reset_type)
    write_vendor_extensions(elem, reset_type.vendor_extensions)
    return elem


def add_reset_types(parent: etree._Element, reset_types: Sequence[ResetType]) -> None:
    add_items(parent, "resetTypes", reset_types, _write_reset_type)


def _write_other_clock_driver(clock_driver: OtherClockDriver) -> etree._Element:
    elem = element(
        "otherClockDriver",
        xml_id=clock_driver.xml_id,
        clockName=clock_driver.clock_name,
        clockSource=clock_driver.clock_source,
    )
    add_clock_driver_body(elem, clock_driver)
    return elem


def add_other_clock_drivers(parent: etree._Element, clock_drivers: Sequence[OtherClockDriver]) -> None:
    add_items(parent, "otherClockDrivers", clock_drivers, _write_other_clock_driver)
