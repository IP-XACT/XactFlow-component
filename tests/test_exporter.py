from __future__ import annotations

import ipxact
import pytest
from xactflow import Exporter, discover_exporters

from build_components import build_wide_component
from xactflow_component import ComponentExporter


def test_exporter_writes_a_file_named_after_the_vlnv(tmp_path):
    component = build_wide_component()
    ComponentExporter().export(component, tmp_path)

    written = tmp_path / "wide_coverage.xml"
    assert written.exists()
    assert ipxact.parse_file(written) == component


def test_exporter_creates_a_missing_output_directory(tmp_path):
    output_dir = tmp_path / "nested" / "out"
    ComponentExporter().export(build_wide_component(), output_dir)
    assert (output_dir / "wide_coverage.xml").exists()


def test_exporter_rejects_a_non_component_subject(tmp_path):
    with pytest.raises(TypeError, match=r"ipxact\.Component"):
        ComponentExporter().export(object(), tmp_path)


def test_exporter_rejects_a_design(tmp_path):
    design = ipxact.Design(vlnv=ipxact.VLNV("example.org", "ip", "top", "1.0"))
    with pytest.raises(TypeError):
        ComponentExporter().export(design, tmp_path)


def test_exporter_is_registered_under_the_entry_point_group():
    assert discover_exporters()["component"] is ComponentExporter
    assert issubclass(ComponentExporter, Exporter)
    assert ComponentExporter.name == "component"
