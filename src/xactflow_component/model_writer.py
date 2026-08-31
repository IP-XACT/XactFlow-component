from __future__ import annotations

from lxml import etree

from ipxact.schema.model import (
    ComponentInstantiation,
    DesignConfigurationInstantiation,
    DesignInstantiation,
    Model,
    View,
)

from .common_writer import (
    add_file_builder,
    add_local_name_refs,
    add_module_parameters,
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
from .ports_writer import add_ports


def _add_view(parent: etree._Element, view: View) -> None:
    elem = sub(parent, "view")
    add_name_group(elem, view.name)
    add_texts(elem, "envIdentifier", view.env_identifiers)
    add_text(elem, "componentInstantiationRef", view.component_instantiation_ref)
    add_text(elem, "designInstantiationRef", view.design_instantiation_ref)
    add_text(elem, "designConfigurationInstantiationRef", view.design_configuration_instantiation_ref)
    write_vendor_extensions(elem, view.vendor_extensions)


def _add_component_instantiation(parent: etree._Element, instantiation: ComponentInstantiation) -> None:
    elem = sub(parent, "componentInstantiation")
    add_name_group(elem, instantiation.name)
    if instantiation.is_virtual:
        sub(elem, "isVirtual", bool_str(True))
    add_text(elem, "language", instantiation.language)
    add_text(elem, "libraryName", instantiation.library_name)
    add_text(elem, "packageName", instantiation.package_name)
    add_text(elem, "moduleName", instantiation.module_name)
    add_text(elem, "architectureName", instantiation.architecture_name)
    add_text(elem, "configurationName", instantiation.configuration_name)
    add_module_parameters(elem, instantiation.module_parameters)
    for builder in instantiation.default_file_builders:
        add_file_builder(elem, builder)
    add_local_name_refs(elem, "fileSetRef", instantiation.file_set_refs)
    add_local_name_refs(elem, "constraintSetRef", instantiation.constraint_set_refs)
    add_parameters(elem, instantiation.parameters)
    write_vendor_extensions(elem, instantiation.vendor_extensions)


def _add_design_instantiation(parent: etree._Element, instantiation: DesignInstantiation) -> None:
    elem = sub(parent, "designInstantiation")
    add_name_group(elem, instantiation.name)
    elem.append(write_vlnv_ref("designRef", instantiation.design_ref))
    write_vendor_extensions(elem, instantiation.vendor_extensions)


def _add_design_configuration_instantiation(
    parent: etree._Element, instantiation: DesignConfigurationInstantiation
) -> None:
    elem = sub(parent, "designConfigurationInstantiation")
    add_name_group(elem, instantiation.name)
    add_text(elem, "language", instantiation.language)
    elem.append(write_vlnv_ref("designConfigurationRef", instantiation.design_configuration_ref))
    add_parameters(elem, instantiation.parameters)
    write_vendor_extensions(elem, instantiation.vendor_extensions)


def write_model(model: Model) -> etree._Element:
    elem = element("model")
    if model.views:
        views = sub(elem, "views")
        for view in model.views:
            _add_view(views, view)
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
