from pathlib import Path
import ast


SOURCE = (
    Path(__file__).resolve().parents[1]
    / "app"
    / "api_reliability_v455311.py"
)


def _functions():
    tree = ast.parse(SOURCE.read_text())
    return {
        node.name: node
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
    }


def _source(name):
    source = SOURCE.read_text()
    node = _functions()[name]
    return ast.get_source_segment(source, node)


def test_canonical_health_functions_exist():
    functions = _functions()
    assert "build_capability_health" in functions
    assert "build_readiness" in functions


def test_capability_health_tracks_partial_and_unavailable_counts():
    source = _source("build_capability_health")
    assert "usable_capabilities" in source
    assert "partial_capabilities" in source
    assert "unavailable_capabilities" in source


def test_readiness_distinguishes_partial_from_degraded():
    source = _source("build_readiness")
    assert "domain-partial" in source
    assert "domain-degraded" in source


def test_readiness_consumes_capability_health():
    source = _source("build_readiness")
    assert "build_capability_health" in source


def test_attribution_remains_in_capability_health():
    source = _source("build_capability_health")
    assert "source_attribution" in source
    assert "_public_source_attribution" in source
