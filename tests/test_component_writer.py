from __future__ import annotations

from pathlib import Path

import ipxact
import pytest
import xactflow.SCR
from lxml import etree

from build_components import build_banked_component, build_wide_component
from xactflow_component import component_to_bytes, write_component_file


def _write_and_reparse(component: ipxact.Component, tmp_path: Path) -> ipxact.Component:
    path = write_component_file(component, tmp_path / "written.xml")
    return ipxact.parse_file(path)


def test_fixture_round_trips(apb_uart_path, component_schema, tmp_path):
    component = ipxact.parse_file(apb_uart_path)
    path = write_component_file(component, tmp_path / "apb_uart.xml")

    component_schema.assertValid(etree.parse(str(path)))
    assert ipxact.parse_file(path) == component


def test_fixture_output_passes_scr_checks(apb_uart_path, tmp_path):
    component = ipxact.parse_file(apb_uart_path)
    assert xactflow.SCR.run_single_doc_checks(_write_and_reparse(component, tmp_path)) == []


def test_wide_component_is_schema_valid(component_schema, tmp_path):
    path = write_component_file(build_wide_component(), tmp_path / "wide.xml")
    component_schema.assertValid(etree.parse(str(path)))


def test_wide_component_round_trips(tmp_path):
    component = build_wide_component()
    assert _write_and_reparse(component, tmp_path) == component


def test_wide_component_output_passes_scr_checks(tmp_path):
    reparsed = _write_and_reparse(build_wide_component(), tmp_path)
    assert xactflow.SCR.run_single_doc_checks(reparsed) == []


def test_banked_component_round_trips(tmp_path):
    component = build_banked_component()
    assert _write_and_reparse(component, tmp_path) == component


def test_expressions_are_written_verbatim(tmp_path):
    component = ipxact.Component(
        vlnv=ipxact.VLNV("example.org", "ip", "expressions", "1.0"),
        memory_maps=[
            ipxact.MemoryMap(
                name="mm",
                items=[
                    ipxact.AddressBlock(
                        name="block",
                        range="WIDTH*4",
                        width="8 + OFFSET",
                        base_address="0x0000_0000",
                        registers=[
                            ipxact.Register(
                                name="R",
                                address_offset="BASE + 4",
                                size="32",
                                fields=[
                                    ipxact.Field(name="F", bit_offset="LSB", bit_width="MSB-LSB+1")
                                ],
                            )
                        ],
                    )
                ],
            )
        ],
    )
    text = component_to_bytes(component).decode()
    for expression in ("WIDTH*4", "8 + OFFSET", "0x0000_0000", "BASE + 4", "MSB-LSB+1"):
        assert f">{expression}<" in text


def test_register_arrays_use_stride_and_field_arrays_use_bit_stride(component_schema):
    component = ipxact.Component(
        vlnv=ipxact.VLNV("example.org", "ip", "arrays", "1.0"),
        memory_maps=[
            ipxact.MemoryMap(
                name="mm",
                items=[
                    ipxact.AddressBlock(
                        name="block",
                        range="0x10",
                        width="32",
                        base_address="0x0",
                        registers=[
                            ipxact.Register(
                                name="R",
                                address_offset="0x0",
                                size="32",
                                array=ipxact.MemoryArray(dims=[ipxact.ArrayDim(size="4")], stride="4"),
                                fields=[
                                    ipxact.Field(
                                        name="F",
                                        bit_offset="0",
                                        bit_width="1",
                                        array=ipxact.MemoryArray(
                                            dims=[ipxact.ArrayDim(size="2")], stride="1"
                                        ),
                                    )
                                ],
                            )
                        ],
                    )
                ],
            )
        ],
    )
    written = component_to_bytes(component)
    component_schema.assertValid(etree.fromstring(written).getroottree())

    text = written.decode()
    assert "<ipxact:stride>4</ipxact:stride>" in text
    assert "<ipxact:bitStride>1</ipxact:bitStride>" in text


def test_vendor_extensions_are_not_reformatted(tmp_path):
    extension = '<vendor:tag xmlns:vendor="http://example.org/vendor" n="1"><vendor:inner/></vendor:tag>'
    component = ipxact.Component(
        vlnv=ipxact.VLNV("example.org", "ip", "extended", "1.0"),
        vendor_extensions=[extension],
    )
    assert extension in component_to_bytes(component).decode()

    # Reading an extension back adds the ipxact declaration that was in scope around it, which
    # is ipxact-compiler's own behavior; from there the fragment must stay byte-stable.
    reparsed = _write_and_reparse(component, tmp_path)
    assert "<vendor:inner/></vendor:tag>" in reparsed.vendor_extensions[0]
    assert _write_and_reparse(reparsed, tmp_path) == reparsed


def test_unknown_memory_map_item_is_rejected():
    component = ipxact.Component(
        vlnv=ipxact.VLNV("example.org", "ip", "broken", "1.0"),
        memory_maps=[ipxact.MemoryMap(name="mm", items=[object()])],
    )
    with pytest.raises(TypeError):
        component_to_bytes(component)
