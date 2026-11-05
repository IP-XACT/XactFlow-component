from __future__ import annotations

__version__ = "0.2.0"

import re
from pathlib import Path

import ipxact
from lxml import etree
from xactflow import Exporter

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
    """Serialize an ipxact.Component into an IEEE 1685-2022 IP-XACT component XML file.

    The output file is named <vendor>_<library>_<name>_<version>.xml into output_dir.
    """

    name = "component"

    def export(self, subject: object, output_dir: Path, **options: object) -> None:
        if not isinstance(subject, ipxact.Component):
            # LinkedDesign support (flattening a resolved multi-instance design into one
            # boundary Component) is an agreed-on later addition.
            raise TypeError(
                f"xactflow-component only supports ipxact.Component, got {type(subject).__name__}"
            )
        output_dir = Path(output_dir)
        path = output_dir / _file_name(subject.vlnv)
        _check_overwrite(path, subject.vlnv)
        output_dir.mkdir(parents=True, exist_ok=True)
        write_component_file(subject, path)


_FILE_NAME_PART = re.compile(r"[A-Za-z0-9._-]+")


def _vlnv_parts(vlnv: ipxact.VLNV) -> list:
    return [vlnv.vendor, vlnv.library, vlnv.name, vlnv.version]


def _file_name(vlnv: ipxact.VLNV) -> str:
    """<vendor>_<library>_<name>_<version>.xml, each part only made of letters, digits, '.', '_' and '-'."""
    parts = _vlnv_parts(vlnv)
    if not all(_FILE_NAME_PART.fullmatch(part) for part in parts):
        raise ValueError(f"VLNV {':'.join(parts)!r} cannot be used as a file name")
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
    except etree.XMLSyntaxError:
        same = False
    if not same:
        raise FileExistsError(f"{path} already exists and is not the component {':'.join(_vlnv_parts(vlnv))}")
