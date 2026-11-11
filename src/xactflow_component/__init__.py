from __future__ import annotations

__version__ = "0.2.1"

import re
from pathlib import Path

import ipxact
from lxml import etree
from xactflow import Exporter, Library

from .common_writer import qn
from .component_writer import component_to_bytes, write_component, write_component_file

__all__ = [
    "ComponentExporter",
    "__version__",
    "component_to_bytes",
    "write_component",
    "write_component_file",
]


class ComponentExporter(Exporter):
    """Serialize the ipxact.Component targets of a Library into IEEE 1685-2022 IP-XACT component
    XML files.

    Each component is written to <vendor>_<library>_<name>_<version>.xml into output_dir. Targets
    of another type, and components that are only there to be looked up, are not written.
    """

    name = "component"

    def export(self, library: Library, output_dir: Path, **options: object) -> None:
        components = list(library.targets(ipxact.Component))
        if not components:
            # Writing a design target as a component (flattening a resolved multi-instance design
            # into one boundary Component) is an agreed-on later addition.
            raise TypeError("xactflow-component needs an ipxact.Component target, the library has none")
        output_dir = Path(output_dir)
        # Every file name is checked before any file is written, so a rejected target leaves
        # output_dir as it was.
        paths = {}
        for component in components:
            path = output_dir / _file_name(component.vlnv)
            if path in paths:
                raise FileExistsError(
                    f"{paths[path].vlnv} and {component.vlnv} would both be written to {path}"
                )
            _check_overwrite(path, component.vlnv)
            paths[path] = component
        output_dir.mkdir(parents=True, exist_ok=True)
        for path, component in paths.items():
            write_component_file(component, path)


_FILE_NAME_PART = re.compile(r"[A-Za-z0-9._-]+")


def _vlnv_parts(vlnv: ipxact.VLNV) -> list:
    return [vlnv.vendor, vlnv.library, vlnv.name, vlnv.version]


def _file_name(vlnv: ipxact.VLNV) -> str:
    """<vendor>_<library>_<name>_<version>.xml, each part only made of letters, digits, '.', '_' and '-'."""
    parts = _vlnv_parts(vlnv)
    if not all(_FILE_NAME_PART.fullmatch(part) for part in parts):
        raise ValueError(f"VLNV {str(vlnv)!r} cannot be used as a file name")
    return "_".join(parts) + ".xml"


def _check_overwrite(path: Path, vlnv: ipxact.VLNV) -> None:
    """Refuse to replace an existing file unless it is a component with the same VLNV (a re-export).

    Two VLNVs can still share a file name when a part holds an underscore (a_b + c and a + b_c),
    and the file may not be a component at all.
    """
    if not path.exists():
        return
    try:
        root = etree.parse(str(path)).getroot()
        existing = [root.findtext(qn(tag)) for tag in ("vendor", "library", "name", "version")]
        same = root.tag == qn("component") and existing == _vlnv_parts(vlnv)
    except (etree.XMLSyntaxError, OSError):
        same = False
    if not same:
        raise FileExistsError(f"{path} already exists and is not the component {vlnv}")
