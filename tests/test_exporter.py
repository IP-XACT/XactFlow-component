from __future__ import annotations

import ipxact
import pytest
from xactflow import Exporter, Library, discover_exporters
from xactflow.cli import main

from build_components import build_wide_component
from xactflow_component import ComponentExporter, write_component_file


WIDE_FILE_NAME = "example.org_ip_wide_coverage_2.0.xml"


def _component(vendor="example.org", library="ip", name="c", version="1.0") -> ipxact.Component:
    return ipxact.Component(vlnv=ipxact.VLNV(vendor, library, name, version))


def _export(output_dir, *targets) -> None:
    library = Library()
    for document in targets:
        library.add(document, target=True)
    ComponentExporter().export(library, output_dir)


def test_exporter_writes_a_file_named_after_the_vlnv(tmp_path):
    component = build_wide_component()
    _export(tmp_path, component)

    written = tmp_path / WIDE_FILE_NAME
    assert written.exists()
    assert ipxact.parse_file(written) == component


def test_exporter_creates_a_missing_output_directory(tmp_path):
    output_dir = tmp_path / "nested" / "out"
    _export(output_dir, build_wide_component())
    assert (output_dir / WIDE_FILE_NAME).exists()


def test_components_differing_only_by_version_get_their_own_file(tmp_path):
    _export(tmp_path, _component(version="1.0"))
    _export(tmp_path, _component(version="2.0"))
    assert sorted(path.name for path in tmp_path.iterdir()) == ["example.org_ip_c_1.0.xml", "example.org_ip_c_2.0.xml"]


def test_exporting_the_same_component_again_replaces_its_file(tmp_path):
    _export(tmp_path, _component())
    _export(tmp_path, _component())
    assert [path.name for path in tmp_path.iterdir()] == ["example.org_ip_c_1.0.xml"]


@pytest.mark.parametrize("name", ["../../escaped", "a\\b", "", "with space", "a:b"])
def test_vlnv_that_is_not_a_single_file_name_is_rejected(tmp_path, name):
    with pytest.raises(ValueError, match="cannot be used as a file name"):
        _export(tmp_path / "out", _component(name=name))
    assert not (tmp_path / "out").exists()


def test_another_component_with_the_same_file_name_is_not_overwritten(tmp_path):
    _export(tmp_path, _component(library="a_b", name="c"))
    with pytest.raises(FileExistsError):
        _export(tmp_path, _component(library="a", name="b_c"))


@pytest.mark.parametrize("content", ["not xml", "<other/>"])
def test_a_file_that_is_not_a_component_is_not_overwritten(tmp_path, content):
    (tmp_path / "example.org_ip_c_1.0.xml").write_text(content)
    with pytest.raises(FileExistsError):
        _export(tmp_path, _component())
    assert (tmp_path / "example.org_ip_c_1.0.xml").read_text() == content


def test_a_directory_with_the_file_name_is_not_overwritten(tmp_path):
    (tmp_path / "example.org_ip_c_1.0.xml").mkdir()
    with pytest.raises(FileExistsError):
        _export(tmp_path, _component())


def test_every_component_target_is_written(tmp_path):
    _export(tmp_path, _component(name="a"), _component(name="b"))
    assert sorted(path.name for path in tmp_path.iterdir()) == ["example.org_ip_a_1.0.xml", "example.org_ip_b_1.0.xml"]


def test_only_component_targets_are_written(tmp_path):
    library = Library()
    library.add(_component(name="looked_up"))
    library.add(_component(name="target"), target=True)
    library.add(ipxact.Design(vlnv=ipxact.VLNV("example.org", "ip", "top", "1.0")), target=True)
    ComponentExporter().export(library, tmp_path)
    assert [path.name for path in tmp_path.iterdir()] == ["example.org_ip_target_1.0.xml"]


def test_two_targets_with_the_same_file_name_are_rejected_before_writing(tmp_path):
    with pytest.raises(FileExistsError, match="would both be written"):
        _export(tmp_path / "out", _component(library="a_b", name="c"), _component(library="a", name="b_c"))
    assert not (tmp_path / "out").exists()


def test_exporter_rejects_a_library_without_targets(tmp_path):
    library = Library()
    library.add(_component())
    with pytest.raises(TypeError, match=r"ipxact\.Component"):
        ComponentExporter().export(library, tmp_path)


def test_exporter_rejects_a_design_target(tmp_path):
    design = ipxact.Design(vlnv=ipxact.VLNV("example.org", "ip", "top", "1.0"))
    with pytest.raises(TypeError):
        _export(tmp_path, design)


def test_cli_exports_a_component_file(tmp_path):
    component = build_wide_component()
    source = write_component_file(component, tmp_path / "source.xml")
    assert main(["component", str(source), "--output", str(tmp_path / "out")]) == 0
    assert ipxact.parse_file(tmp_path / "out" / WIDE_FILE_NAME) == component


def test_exporter_is_registered_under_the_entry_point_group():
    assert discover_exporters()["component"] is ComponentExporter
    assert issubclass(ComponentExporter, Exporter)
    assert ComponentExporter.name == "component"
