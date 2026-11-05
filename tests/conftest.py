from __future__ import annotations

from pathlib import Path

import ipxact
import pytest
from lxml import etree

# ipxact-compiler's apb_uart.xml fixture is expected in a sibling checkout during development,
# matching the requirements-dev.txt convention of the other projects.
_SIBLINGS = Path(__file__).resolve().parents[2]

FIXTURE_PATH = _SIBLINGS / "ipxact-compiler" / "tests" / "parser" / "xml" / "apb_uart.xml"


@pytest.fixture(scope="session")
def component_schema() -> etree.XMLSchema:
    # ipxact-compiler ships the IEEE 1685-2022 XSD; lxml resolves the xs:include chain
    # relative to the file it parsed, so no flattening.
    return etree.XMLSchema(etree.parse(str(ipxact.xsd_path() / "component.xsd")))


@pytest.fixture(scope="session")
def apb_uart_path() -> Path:
    if not FIXTURE_PATH.exists():
        pytest.skip(f"ipxact-compiler fixture not found at {FIXTURE_PATH}")
    return FIXTURE_PATH
