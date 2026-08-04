from pathlib import Path

from archilens.extract.tier0_iac.compose import parse_compose

FIXTURE = Path(__file__).parent / "fixtures" / "compose"


def test_extracts_all_services():
    nodes, _ = parse_compose(FIXTURE)
    identities = {n.identity for n in nodes}
    assert identities == {"compose:api", "compose:db", "compose:cache", "compose:worker"}


def test_infers_kind_from_image_name():
    nodes, _ = parse_compose(FIXTURE)
    by_id = {n.identity: n for n in nodes}
    assert by_id["compose:db"].kind == "datastore"
    assert by_id["compose:cache"].kind == "datastore"
    assert by_id["compose:api"].kind == "service"
    assert by_id["compose:worker"].kind == "service"  # no image, build-only


def test_depends_on_becomes_edges():
    _, edges = parse_compose(FIXTURE)
    pairs = {(e.src, e.dst) for e in edges}
    assert ("compose:api", "compose:db") in pairs
    assert ("compose:api", "compose:cache") in pairs


def test_line_numbers_point_at_service_key():
    nodes, _ = parse_compose(FIXTURE)
    by_id = {n.identity: n for n in nodes}
    assert by_id["compose:api"].line == 2
    assert by_id["compose:db"].line == 8
    assert by_id["compose:cache"].line == 11
