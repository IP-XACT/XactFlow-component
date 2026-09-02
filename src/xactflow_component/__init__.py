from __future__ import annotations

__version__ = "0.1.0"

from pathlib import Path

import ipxact
from xactflow import Exporter

from .component_writer import component_to_bytes, write_component, write_component_file

__all__ = [
    "ComponentExporter",
    "__version__",
    "component_to_bytes",
    "write_component",
    "write_component_file",
]


class ComponentExporter(Exporter):
    """Serialize an ipxact.Component into an IEEE 1685-2022 IP-XACT component XML file.

    The output file is named after the component's VLNV name into output_dir.
    """

    name = "component"

    def export(self, subject: object, output_dir: Path, **options: object) -> None:
        if not isinstance(subject, ipxact.Component):
            # ElaboratedDesign support (flattening a resolved multi-instance design into one
            # boundary Component) is an agreed-on later addition.
            raise TypeError(
                f"xactflow-component only supports ipxact.Component, got {type(subject).__name__}"
            )
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        write_component_file(subject, output_dir / f"{subject.vlnv.name}.xml")
