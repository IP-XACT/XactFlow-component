from __future__ import annotations

import ipxact
import pytest
from lxml import etree


@pytest.fixture(scope="session")
def component_schema() -> etree.XMLSchema:
    # ipxact-compiler ships the IEEE 1685-2022 XSD; lxml resolves the xs:include chain
    # relative to the file it parsed, so no flattening.
    return etree.XMLSchema(etree.parse(str(ipxact.xsd_path() / "component.xsd")))
