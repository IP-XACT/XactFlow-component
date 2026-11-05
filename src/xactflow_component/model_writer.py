from __future__ import annotations

from lxml import etree

from ipxact.schema.model import (
    ClearboxElementRef,
    ComponentInstantiation,
    DesignConfigurationInstantiation,
    DesignInstantiation,
    Model,
    View,
)

from .common_writer import (
    add_file_builder,
    add_items,
    add_local_references,
    add_location,
    add_module_parameters,
    add_name_group,
    add_parameters,
    add_text,
    add_text_values,
    bool_str,
    element,
    sub,
    write_vendor_extensions,
    write_vlnv_ref,
)
from .ports_writer import add_ports


def _write_view(view: View) -> etree._Element:
    elem = element("view", xml_id=view.xml_id)
    add_name_group(elem, view)
    add_text_values(elem, "envIdentifier", view.env_identifiers)
    add_text(elem, "componentInstantiationRef", view.component_instantiation_ref)
    add_text(elem, "designInstantiationRef", view.design_instantiation_ref)
    add_text(elem, "designConfigurationInstantiationRef", view.design_configuration_instantiation_ref)
    write_vendor_extensions(elem, view.vendor_extensions)
    return elem


def _add_language(parent: etree._Element, language: object, strict: bool) -> None:
    add_text(parent, "language", language, strict=bool_str(True) if strict else None)


def _write_clearbox_element_ref(ref: ClearboxElementRef) -> etree._Element:
    elem = element("clearboxElementRef", xml_id=ref.xml_id, name=ref.name)
    for location in ref.locations:
        add_location(elem, location)
    write_vendor_extensions(elem, ref.vendor_extensions)
    return elem


def _add_component_instantiation(parent: etree._Element, instantiation: ComponentInstantiation) -> None:
    elem = sub(parent, "componentInstantiation", xml_id=instantiation.xml_id)
    add_name_group(elem, instantiation)
    if instantiation.is_virtual:
        sub(elem, "isVirtual", bool_str(True))
    _add_language(elem, instantiation.language, instantiation.language_strict)
    add_text(elem, "libraryName", instantiation.library_name)
    add_text(elem, "packageName", instantiation.package_name)
    add_text(elem, "moduleName", instantiation.module_name)
    add_text(elem, "architectureName", instantiation.architecture_name)
    add_text(elem, "configurationName", instantiation.configuration_name)
    add_module_parameters(elem, instantiation.module_parameters)
    for builder in instantiation.default_file_builders:
        add_file_builder(elem, builder)
    add_local_references(elem, "fileSetRef", instantiation.file_set_refs)
    add_local_references(elem, "constraintSetRef", instantiation.constraint_set_refs)
    add_items(elem, "clearboxElementRefs", instantiation.clearbox_element_refs, _write_clearbox_element_ref)
    add_parameters(elem, instantiation.parameters)
    write_vendor_extensions(elem, instantiation.vendor_extensions)


def _add_design_instantiation(parent: etree._Element, instantiation: DesignInstantiation) -> None:
    elem = sub(parent, "designInstantiation", xml_id=instantiation.xml_id)
    add_name_group(elem, instantiation)
    elem.append(write_vlnv_ref("designRef", instantiation.design_ref))
    write_vendor_extensions(elem, instantiation.vendor_extensions)


def _add_design_configuration_instantiation(
    parent: etree._Element, instantiation: DesignConfigurationInstantiation
) -> None:
    elem = sub(parent, "designConfigurationInstantiation", xml_id=instantiation.xml_id)
    add_name_group(elem, instantiation)
    _add_language(elem, instantiation.language, instantiation.language_strict)
    elem.append(write_vlnv_ref("designConfigurationRef", instantiation.design_configuration_ref))
    add_parameters(elem, instantiation.parameters)
    write_vendor_extensions(elem, instantiation.vendor_extensions)


def write_model(model: Model) -> etree._Element:
    elem = element("model")
    add_items(elem, "views", model.views, _write_view)
    if model.component_instantiations or model.design_instantiations or model.design_configuration_instantiations:
        instantiations = sub(elem, "instantiations")
        for component_instantiation in model.component_instantiations:
            _add_component_instantiation(instantiations, component_instantiation)
        for design_instantiation in model.design_instantiations:
            _add_design_instantiation(instantiations, design_instantiation)
        for design_configuration_instantiation in model.design_configuration_instantiations:
            _add_design_configuration_instantiation(instantiations, design_configuration_instantiation)
    add_ports(elem, model.ports)
    return elem
