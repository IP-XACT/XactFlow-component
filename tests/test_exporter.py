from __future__ import annotations

import ipxact
import pytest
from xactflow import Exporter, discover_exporters

from build_components import build_wide_component
from xactflow_component import ComponentExporter


WIDE_FILE_NAME = "example.org_ip_wide_coverage_2.0.xml"


def _component(vendor="example.org", library="ip", name="c", version="1.0") -> ipxact.Component:
    return ipxact.Component(vlnv=ipxact.VLNV(vendor, library, name, version))


def test_exporter_writes_a_file_named_after_the_vlnv(tmp_path):
    component = build_wide_component()
    ComponentExporter().export(component, tmp_path)

    written = tmp_path / WIDE_FILE_NAME
    assert written.exists()
    assert ipxact.parse_file(written) == component


def test_exporter_creates_a_missing_output_directory(tmp_path):
    output_dir = tmp_path / "nested" / "out"
    ComponentExporter().export(build_wide_component(), output_dir)
    assert (output_dir / WIDE_FILE_NAME).exists()


def test_components_differing_only_by_version_get_their_own_file(tmp_path):
    ComponentExporter().export(_component(version="1.0"), tmp_path)
    ComponentExporter().export(_component(version="2.0"), tmp_path)
    assert sorted(path.name for path in tmp_path.iterdir()) == ["example.org_ip_c_1.0.xml", "example.org_ip_c_2.0.xml"]


def test_exporting_the_same_component_again_replaces_its_file(tmp_path):
    ComponentExporter().export(_component(), tmp_path)
    ComponentExporter().export(_component(), tmp_path)
    assert [path.name for path in tmp_path.iterdir()] == ["example.org_ip_c_1.0.xml"]


@pytest.mark.parametrize("name", ["../../escaped", "a\\b", "", "with space", "a:b"])
def test_vlnv_that_is_not_a_single_file_name_is_rejected(tmp_path, name):
    with pytest.raises(ValueError, match="cannot be used as a file name"):
        ComponentExporter().export(_component(name=name), tmp_path / "out")
    assert not (tmp_path / "out").exists()


def test_another_component_with_the_same_file_name_is_not_overwritten(tmp_path):
    ComponentExporter().export(_component(library="a_b", name="c"), tmp_path)
    with pytest.raises(FileExistsError):
        ComponentExporter().export(_component(library="a", name="b_c"), tmp_path)


@pytest.mark.parametrize("content", ["not xml", "<other/>"])
def test_a_file_that_is_not_a_component_is_not_overwritten(tmp_path, content):
    (tmp_path / "example.org_ip_c_1.0.xml").write_text(content)
    with pytest.raises(FileExistsError):
        ComponentExporter().export(_component(), tmp_path)
    assert (tmp_path / "example.org_ip_c_1.0.xml").read_text() == content


def test_a_directory_with_the_file_name_is_not_overwritten(tmp_path):
    (tmp_path / "example.org_ip_c_1.0.xml").mkdir()
    with pytest.raises(FileExistsError):
        ComponentExporter().export(_component(), tmp_path)


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
