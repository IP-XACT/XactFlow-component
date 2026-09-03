# xactflow-component

A [XactFlow](https://github.com/IP-XACT/XactFlow) exporter plugin that serializes an
`ipxact.Component` object into a valid [IEEE 1685-2022](https://standards.ieee.org/ieee/1685/10307/)
IP-XACT `component` XML document.

[`ipxact-compiler`](https://github.com/IP-XACT/ipxact-compiler) reads IP-XACT XML and hands back
Python objects, it never writes XML. This package is the other direction: given a `Component`,
it writes the XML back out.

## Installation

```bash
pip install xactflow-component
```

For local development, `requirements-dev.txt` overrides `ipxact-compiler` and `xactflow` to
local installations. It can be modified to adapt the paths or to keep either version on PyPI.

```bash
pip install -r requirements-dev.txt -e .
```

Requires Python >= 3.9.

## Usage

```python
from pathlib import Path

import ipxact
from xactflow_component import ComponentExporter

component = ipxact.parse_file("apb_uart.xml")   # or get one from an importer
ComponentExporter().export(component, Path("out"))
# writes out/apb_uart.xml
```

The output file is named after the component's VLNV name (`<vlnv.name>.xml`) inside `output_dir`,
which is created if it does not exist.

Lower-level entry points are available for callers that want the tree or the bytes rather than a
file:

```python
from xactflow_component import component_to_bytes, write_component, write_component_file

element = write_component(component)              # the lxml ipxact:component root element
data = component_to_bytes(component)              # pretty-printed bytes, with an XML declaration
path = write_component_file(component, "out.xml") # writes and returns the path
```

Once installed, the exporter registers itself under the `xactflow.exporters` entry point group as
`component`, so `xactflow component ...` becomes available as a XactFlow CLI subcommand. Note that
XactFlow's CLI always elaborates a design before calling an exporter, so for now the way to use
this package is to call `ComponentExporter().export(...)` directly on a `Component`.

`export()` raises `TypeError` for anything that is not an `ipxact.Component`. Accepting an
`ElaboratedDesign` (flattening a resolved multi-instance design into one boundary component) is a
planned later addition, not an oversight.

## Design notes

- **Element order comes from the XSD, not from the dataclasses.** `componentType`'s sequence puts
  `displayName`/`shortDescription`/`description` right after the VLNV and `typeDefinitions`/
  `powerDomains` before `busInterfaces`, while the `Component` dataclass declares those fields
  last. The same mismatch repeats in almost every nested type, because IP-XACT's `nameGroup` opens
  an element while the corresponding Python fields are trailing optionals. Every writer here
  follows the schema.
- **Expressions are written verbatim.** Anything typed `Expression` in `ipxact-compiler`
  (`addressOffset`, `size`, `range`, `width`, `bitOffset`, `bitWidth`, ...) is a raw string and is
  emitted unchanged, never evaluated or reformatted.
- **Vendor extensions stay identical.** Their content is not IP-XACT's to define, so each
  fragment is re-inserted as parsed.
- **No `xsi:schemaLocation`.** The root element declares only the IP-XACT namespace, matching the
  fixtures in `ipxact-compiler`. A document is identified by its namespace and root element, and a
  hard-coded schema location would point at a path that does not exist on the reader's machine.
- **Defaults are omitted.** Attributes and elements whose value equals the schema default
  (`resolve="immediate"`, `type="string"`, `misalignmentAllowed="true"`, `connectionRequired`
  false, and so on) are left out, which keeps the output close to hand-written IP-XACT and still
  round-trips exactly.
- **Required XSD choices raise `ValueError` when no arm is set, instead of emitting invalid
  XML.** Several dataclasses share one field across XSD contexts with different required-ness,
  or expose independent sibling fields that the schema only allows together. Rather than silently
  writing an incomplete element for these, the writer raises a specific error naming the missing
  field.

## Known gaps

These come from constructs the IEEE 1685-2022 schema requires but `ipxact-compiler`'s object model
deliberately does not carry. Such a component still round-trips through this writer and back
through the parser unchanged, but the XML it produces will not satisfy the XSD:

- **Banks have no `baseAddress`.** `ipxact.Bank` does not model one, while the schema's
  `addressBankType` (a bank directly inside a `memoryMap`, `memoryRemap` or `localMemoryMap`)
  requires it. Banks nested inside another bank are unaffected.
- **Structured ports have no `structPortTypeDefs`.** `ipxact.StructuredPort` leaves out the
  language-specific type bindings that `portStructuredType` requires.
- **`externalTypeDefinitions` has an optional name.** The schema's `nameGroup` requires one.
- **`File.dependencies` is write-only.** `ipxact-compiler`'s `parse_file` does not read `dependency`
  children of a `file` back, so setting them means the value is written but does not survive a
  re-parse. (`FileSet.dependencies` round-trips normally.)
- **`MemoryArray.stride` on a register or register file is write-only.** This writer emits
  `ipxact:stride` correctly, but `ipxact-compiler` reads it with a truth test on the element, which
  is false for a childless element, so the value comes back as `None`. `bitStride` on a field is
  unaffected.

The writer also does not invent content the object model leaves out, so a `Component` that is
under-specified relative to the schema produces XML that says so: a `register` with no fields, a
`memoryRemap` with no `modeRef`, a `channel` with fewer than two `busInterfaceRef`s, a `file` with
no `fileType`, or a `componentGenerator` with more than one `transportMethod` will each fail
validation rather than being silently patched up. Validating the output against `component.xsd` is
the way to catch that.

Other deliberate simplifications, all inherited from `ipxact-compiler`'s object model, so there is
nothing to write: `accessHandles`, `executableImage`, `powerConstraints`, `wireTypeDefs`/
`domainTypeDefs`/`signalTypeDefs`/`transTypeDefs`, `portPackets`, a port's `arrays`/`access`, a
`portMap`'s logical `range` and physical `partSelect`/`subPort`, `clearboxElementRefs`,
`fileSet/function`, a `file`'s `define`/`imageType`/`targetName`, `viewLinks`/`modeLinks`/
`resetTypeLinks`, a field's `aliasOf` alternative, and the `*DefinitionRef` type-definition
indirection on memory map elements.

## Development

```bash
pip install -r requirements-dev.txt -e .
pytest
```

The tests round-trip both `ipxact-compiler`'s `apb_uart.xml` fixture and hand-built components
through the writer and back through the parser, validate the written XML against `component.xsd`
with `lxml.etree.XMLSchema.assertValid`, and re-run `xactflow.SCR.run_single_doc_checks` on the
result. They expect `ipxact-compiler` and the IEEE 1685-2022 schema (`IEEE_1685-2022/schema/
1685-2022/`) as sibling checkouts; set `IPXACT_SCHEMA_DIR` to point the schema somewhere else.

## License

LGPL-3.0. See [LICENSE](LICENSE).
