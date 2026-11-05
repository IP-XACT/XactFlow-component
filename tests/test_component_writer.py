from __future__ import annotations

import dataclasses
import importlib
from collections import defaultdict
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


def test_wide_component_is_schema_valid(component_schema, tmp_path):
    path = write_component_file(build_wide_component(), tmp_path / "wide.xml")
    component_schema.assertValid(etree.parse(str(path)))


def test_wide_component_round_trips(tmp_path):
    component = build_wide_component()
    assert _write_and_reparse(component, tmp_path) == component


def test_wide_component_output_passes_scr_checks(tmp_path):
    reparsed = _write_and_reparse(build_wide_component(), tmp_path)
    assert xactflow.SCR.run_single_doc_checks(reparsed) == []


def test_banked_component_is_schema_valid(component_schema, tmp_path):
    path = write_component_file(build_banked_component(), tmp_path / "banked.xml")
    component_schema.assertValid(etree.parse(str(path)))


def test_banked_component_round_trips(tmp_path):
    component = build_banked_component()
    assert _write_and_reparse(component, tmp_path) == component


def _field_default(field: dataclasses.Field) -> object:
    if field.default is not dataclasses.MISSING:
        return field.default
    if field.default_factory is not dataclasses.MISSING:
        return field.default_factory()
    return dataclasses.MISSING


def _collect_set_fields(value: object, set_fields: dict) -> None:
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        for field in dataclasses.fields(value):
            field_value = getattr(value, field.name)
            if field_value != _field_default(field):
                set_fields[type(value)].add(field.name)
            _collect_set_fields(field_value, set_fields)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _collect_set_fields(item, set_fields)
    elif isinstance(value, dict):
        for item in value.values():
            _collect_set_fields(item, set_fields)


def test_fixtures_set_every_component_field():
    """A field the writer forgets only shows up in a round trip if some fixture sets it.

    So between them the hand-built components must set every field of every dataclass a
    Component can contain; when ipxact-compiler adds one, this fails until a fixture uses it.
    """
    set_fields: dict = defaultdict(set)
    _collect_set_fields(build_wide_component(), set_fields)
    _collect_set_fields(build_banked_component(), set_fields)

    unset = []
    for module_name in ("businterface", "common", "component", "component_sections", "memorymap", "model", "ports"):
        module = importlib.import_module(f"ipxact.schema.{module_name}")
        for name, cls in vars(module).items():
            if dataclasses.is_dataclass(cls) and cls.__module__ == module.__name__:
                unset += [f"{name}.{f.name}" for f in dataclasses.fields(cls) if f.name not in set_fields[cls]]
    assert unset == []


def test_structured_port_with_type_defs_is_schema_valid(component_schema, tmp_path):
    """A populated structPortTypeDefs makes a structured port satisfy the XSD on its own.

    build_banked_component's structured port isn't usable for this: it also has a Bank with
    no baseAddress, which fails validation for an unrelated reason. This isolates the
    structured port alone to prove structPortTypeDefs specifically is no longer a gap.
    """
    component = ipxact.Component(
        vlnv=ipxact.VLNV("example.org", "ip", "structured_port", "1.0"),
        model=ipxact.Model(
            ports=[
                ipxact.Port(
                    name="bus",
                    structured=ipxact.StructuredPort(
                        struct_type="struct",
                        sub_ports=[
                            ipxact.SubPort(name="valid", wire=ipxact.WirePort(direction=ipxact.Direction.OUT))
                        ],
                        struct_port_type_defs=[ipxact.StructPortTypeDef(type_name="bus_req_t")],
                        direction=ipxact.Direction.OUT,
                    ),
                )
            ]
        ),
    )
    path = write_component_file(component, tmp_path / "structured_port.xml")
    component_schema.assertValid(etree.parse(str(path)))
    assert ipxact.parse_file(path) == component


def test_expressions_are_written_verbatim(tmp_path):
    component = ipxact.Component(
        vlnv=ipxact.VLNV("example.org", "ip", "expressions", "1.0"),
        memory_maps=[
            ipxact.MemoryMap(
                name="mm",
                items=[
                    ipxact.AddressBlock(
                        name="block",
                        range=ipxact.Expression("WIDTH*4"),
                        width=ipxact.Expression("8 + OFFSET"),
                        base_address=ipxact.Expression("0x0000_0000"),
                        registers=[
                            ipxact.Register(
                                name="R",
                                address_offset=ipxact.Expression("BASE + 4"),
                                size=ipxact.Expression("32"),
                                fields=[
                                    ipxact.Field(name="F", bit_offset=ipxact.Expression("LSB"), bit_width=ipxact.Expression("MSB-LSB+1"))
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


def test_register_arrays_use_stride_and_field_arrays_use_bit_stride(component_schema, tmp_path):
    component = ipxact.Component(
        vlnv=ipxact.VLNV("example.org", "ip", "arrays", "1.0"),
        memory_maps=[
            ipxact.MemoryMap(
                name="mm",
                items=[
                    ipxact.AddressBlock(
                        name="block",
                        range=ipxact.Expression("0x10"),
                        width=ipxact.Expression("32"),
                        base_address=ipxact.Expression("0x0"),
                        registers=[
                            ipxact.Register(
                                name="R",
                                address_offset=ipxact.Expression("0x0"),
                                size=ipxact.Expression("32"),
                                array=ipxact.MemoryArray(dims=[ipxact.ArrayDim(size=ipxact.Expression("4"))], stride=ipxact.Expression("4")),
                                fields=[
                                    ipxact.Field(
                                        name="F",
                                        bit_offset=ipxact.Expression("0"),
                                        bit_width=ipxact.Expression("1"),
                                        array=ipxact.MemoryArray(
                                            dims=[ipxact.ArrayDim(size=ipxact.Expression("2"))], stride=ipxact.Expression("1")
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
    assert _write_and_reparse(component, tmp_path) == component


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


def test_vendor_extensions_keep_processing_instructions_and_comments(tmp_path):
    # ipxact-compiler returns a processing instruction in vendorExtensions as its own fragment.
    extensions = ["<?acme-tool keep?>", "<!-- note -->", '<acme:setting xmlns:acme="http://acme.example/ext">on</acme:setting>']
    component = ipxact.Component(
        vlnv=ipxact.VLNV("example.org", "ip", "pi", "1.0"),
        vendor_extensions=extensions,
    )
    assert "<ipxact:vendorExtensions>" + "".join(extensions) + "</ipxact:vendorExtensions>" in component_to_bytes(component).decode()

    reparsed = _write_and_reparse(component, tmp_path)
    assert reparsed.vendor_extensions[0] == "<?acme-tool keep?>"
    assert _write_and_reparse(reparsed, tmp_path) == reparsed


def test_unknown_memory_map_item_is_rejected():
    component = ipxact.Component(
        vlnv=ipxact.VLNV("example.org", "ip", "broken", "1.0"),
        memory_maps=[ipxact.MemoryMap(name="mm", items=[object()])],
    )
    with pytest.raises(TypeError):
        component_to_bytes(component)
