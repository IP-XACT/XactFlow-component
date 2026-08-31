from __future__ import annotations

from pathlib import Path
from typing import Union

from lxml import etree

from ipxact.schema.component import Component

from .businterface_writer import add_bus_interfaces, add_channels, add_indirect_interfaces
from .common_writer import (
    NAMESPACE,
    add_assertions,
    add_choices,
    add_file_sets,
    add_parameters,
    add_text,
    add_vlnv,
    element,
    write_vendor_extensions,
)
from .component_sections_writer import (
    add_clearbox_elements,
    add_component_generators,
    add_cpus,
    add_external_type_definitions,
    add_modes,
    add_other_clock_drivers,
    add_power_domains,
    add_reset_types,
)
from .memorymap_writer import add_address_spaces, add_memory_maps
from .model_writer import write_model


def write_component(component: Component) -> etree._Element:
    """Build the ipxact:component root element for a Component.

    Child order follows component.xsd's componentType sequence.
    """
    root = element("component")
    add_vlnv(root, component.vlnv)
    add_text(root, "displayName", component.display_name)
    add_text(root, "shortDescription", component.short_description)
    add_text(root, "description", component.description)
    add_external_type_definitions(root, component.external_type_definitions)
    add_power_domains(root, component.power_domains)
    add_bus_interfaces(root, component.bus_interfaces)
    add_indirect_interfaces(root, component.indirect_interfaces)
    add_channels(root, component.channels)
    add_modes(root, component.modes)
    add_address_spaces(root, component.address_spaces)
    add_memory_maps(root, component.memory_maps)
    if component.model is not None:
        root.append(write_model(component.model))
    add_component_generators(root, component.component_generators)
    add_choices(root, component.choices)
    add_file_sets(root, component.file_sets)
    add_clearbox_elements(root, component.clearbox_elements)
    add_cpus(root, component.cpus)
    add_other_clock_drivers(root, component.other_clock_drivers)
    add_reset_types(root, component.reset_types)
    add_parameters(root, component.parameters)
    add_assertions(root, component.assertions)
    write_vendor_extensions(root, component.vendor_extensions)
    etree.cleanup_namespaces(root, top_nsmap={"ipxact": NAMESPACE})
    return root


def component_to_bytes(component: Component) -> bytes:
    """Serialize a Component to a pretty-printed IP-XACT XML document."""
    return etree.tostring(
        write_component(component).getroottree(),
        pretty_print=True,
        xml_declaration=True,
        encoding="UTF-8",
    )


def write_component_file(component: Component, path: Union[str, Path]) -> Path:
    path = Path(path)
    path.write_bytes(component_to_bytes(component))
    return path
