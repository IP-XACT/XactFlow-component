from __future__ import annotations

import os
from pathlib import Path

import pytest
from lxml import etree

# The IEEE 1685-2022 schema and ipxact-compiler are expected as siblings of this repo during
# development, matching the requirements-dev.txt convention of the other projects.
_SIBLINGS = Path(__file__).resolve().parents[2]

SCHEMA_PATH = Path(
    os.environ.get("IPXACT_SCHEMA_DIR", _SIBLINGS / "IEEE_1685-2022" / "schema" / "1685-2022")
) / "component.xsd"

FIXTURE_PATH = _SIBLINGS / "ipxact-compiler" / "tests" / "parser" / "xml" / "apb_uart.xml"


@pytest.fixture(scope="session")
def component_schema() -> etree.XMLSchema:
    if not SCHEMA_PATH.exists():
        pytest.skip(f"IEEE 1685-2022 component.xsd not found at {SCHEMA_PATH}")
    # lxml resolves the xs:include chain relative to the file it parsed, so no flattening.
    return etree.XMLSchema(etree.parse(str(SCHEMA_PATH)))


@pytest.fixture(scope="session")
def apb_uart_path() -> Path:
    if not FIXTURE_PATH.exists():
        pytest.skip(f"ipxact-compiler fixture not found at {FIXTURE_PATH}")
    return FIXTURE_PATH
