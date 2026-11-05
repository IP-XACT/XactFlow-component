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
# writes out/<vendor>_<library>_<name>_<version>.xml
```

The output file is named after the component's full VLNV (`<vendor>_<library>_<name>_<version>.xml`)
inside `output_dir`, which is created if it does not exist. Each VLNV part may only hold letters,
digits, `.`, `_` and `-`; anything else raises `ValueError`. Exporting the same component again
replaces its file, but a file of that name holding anything else (another VLNV, or not a component)
raises `FileExistsError`.

Lower-level entry points are available for callers that want the tree or the bytes rather than a
file:

```python
from xactflow_component import component_to_bytes, write_component, write_component_file

element = write_component(component)              # the lxml ipxact:component root element
data = component_to_bytes(component)              # pretty-printed bytes, with an XML declaration
path = write_component_file(component, "out.xml") # writes and returns the path
```

Once installed, the exporter registers itself under the `xactflow.exporters` entry point group as
`component`. From the XactFlow CLI, use it after an importer with `--then component`:

```bash
xactflow sv uart.sv --option metadata=uart_ipxact.json --then component --output out/
# writes out/<vendor>_<library>_uart_<version>.xml
```

The `xactflow component <design>` subcommand links a design first and passes the result to the
exporter, so it fails until `LinkedDesign` is supported (see below).

`export()` raises `TypeError` for anything that is not an `ipxact.Component`. Accepting a
`LinkedDesign` (flattening a resolved multi-instance design into one boundary component) is a
planned later addition, not an oversight.

## Design notes

- **Element order comes from the XSD, not from the dataclasses.** `componentType`'s sequence puts
  `displayName`/`shortDescription`/`description` right after the VLNV and `typeDefinitions`/
  `powerDomains` before `busInterfaces`, while the `Component` dataclass declares those fields
  last. The same mismatch repeats in almost every nested type, because IP-XACT's `nameGroup` opens
  an element while the corresponding Python fields are trailing optionals. Every writer here
  follows the schema.
- **Expressions are written verbatim.** Anything typed `Expression` in `ipxact-compiler`
  (`addressOffset`, `size`, `range`, `width`, `bitOffset`, `bitWidth`, ...) keeps its raw text in
  `.value`, which is emitted unchanged, never evaluated or reformatted, together with its
  `minimum`/`maximum`, `xml:id` and attributes from other namespaces.
- **Vendor extensions stay identical.** Their content is not IP-XACT's to define, so each
  fragment is re-inserted as parsed (only a leading XML declaration is dropped).
- **Defaults are omitted.** Attributes and elements whose value equals the schema default
  (`resolve="immediate"`, `type="string"`, `misalignmentAllowed="true"`, `connectionRequired`
  false, and so on) are left out, which keeps the output close to hand-written IP-XACT and still
  round-trips exactly.
- **XSD choices raise `ValueError` when no arm or more than one arm is set, instead of emitting
  invalid XML or losing data.** Several dataclasses share one field across XSD contexts with
  different required-ness, expose independent sibling fields that the schema only allows
  together, or expose each arm of a choice (`wire`/`transactional`/`structured`, a
  `*DefinitionRef` and the content it replaces, ...) as its own field. Rather than silently writing
  an incomplete element, or writing one arm and dropping the others, the writer raises a specific
  error naming the fields involved. The same goes for a field set where the schema has no place
  for it, such as a `base_address` on a block inside a bank.

## Known gaps

Since `ipxact-compiler` 0.2.0, its object model covers the whole IEEE 1685-2022 `component` schema,
and this writer writes every part of it, `*DefinitionRef` references included (they are written
as references, not resolved). One gap is left:

- **`externalTypeDefinitions` has an optional name.** The schema's `nameGroup` requires one.

The writer also does not invent content the object model leaves out, so a `Component` that is
under-specified relative to the schema produces XML that says so: a `register` with no fields, a
`memoryRemap` with no `modeRef`, a `channel` with fewer than two `busInterfaceRef`s, a `file` with
no `fileType`, or a `componentGenerator` with more than one `transportMethod` will each fail
validation rather than being silently patched up. `ipxact.validate()` checks the output against
the XSD shipped with `ipxact-compiler`, and is the way to catch that.

## Development

```bash
pip install -r requirements-dev.txt -e .
pytest
```

The tests round-trip hand-built components through the writer and back through the parser,
validate the written XML against the `component.xsd` shipped with `ipxact-compiler`, and re-run
`xactflow.SCR.run_single_doc_checks` on the result. Between them, the hand-built components set
every field of every dataclass a `Component` can contain, and a test fails when one is not set, so
a field added to `ipxact-compiler` cannot be missed by the writer unnoticed.

## License

LGPL-3.0. See [LICENSE](LICENSE).
