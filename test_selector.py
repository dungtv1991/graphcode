#!/usr/bin/env python3
"""Unit tests for SmartContextSelector"""

import pytest
import json
import os
import tempfile
from unittest.mock import Mock, patch
from vector_context_manager import SmartContextSelector


@pytest.fixture
def mock_graph_data():
    return {
        "file_mapping": {
            "home_page": "lib/home.dart",
            "product_page": "lib/product.dart",
            "cart_page": "lib/cart.dart",
        },
        "edges": [
            {"from": "home_page", "to": "product_page", "type": "routes_to"},
            {"from": "product_page", "to": "cart_page", "type": "routes_to"},
            {"from": "cart_page", "to": "payment_page", "type": "depends_on"},
        ]
    }


@pytest.fixture
def selector(mock_graph_data):
    with patch('builtins.open', create=True):
        with patch('json.load', return_value=mock_graph_data):
            sel = SmartContextSelector()
            sel._graph = mock_graph_data
            sel._file_mapping = mock_graph_data["file_mapping"]
            sel._edges = mock_graph_data["edges"]
            return sel


def test_trace_flow(selector):
    flow = selector.trace_flow(["home_page"], max_depth=2)
    assert "home_page" in flow
    assert "product_page" in flow
    assert len(flow) <= 3


def test_trace_critical_path(selector):
    flow = selector.trace_critical_path(["home_page"], max_depth=2)
    assert "home_page" in flow
    assert "product_page" in flow
    # depends_on edge should NOT be followed
    assert "payment_page" not in flow


def test_nodes_to_files(selector):
    files = selector.nodes_to_files(["home_page", "product_page"])
    assert len(files) == 2
    assert all(f.endswith(".dart") for f in files)


def test_generate_graph_info(selector):
    info = selector.generate_graph_info(["home_page", "product_page"])
    assert "home_page" in info
    assert "product_page" in info
    assert "routes_to" in info


def test_detect_entry_nodes(selector):
    nodes = selector.detect_entry_nodes("go to home page")
    assert "home_page" in nodes


def test_health_check(selector):
    # Mock file existence
    with patch('os.path.exists', return_value=True):
        checks = selector.health_check()
        assert "graph_file" in checks
        assert "vector_db" in checks


if __name__ == "__main__":
    pytest.main([__file__, "-v"])