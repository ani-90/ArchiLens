"""Tier 0 extractor: docker-compose.yml.

Same authority as Terraform within tier 0 — a compose file declares services
and their dependencies explicitly. See spec Part II, Stage 1, Tier 0.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

from archilens.extract.schema import EdgeRecord, EvidenceRecord

TIER = 0
CONFIDENCE = 1.0

# Substring match against the service's image name. First match wins.
# Anything unmatched defaults to "service" (compose services are
# application code, not infra, unless the image says otherwise).
IMAGE_KIND_MAP = [
    ("postgres", "datastore"),
    ("mysql", "datastore"),
    ("mariadb", "datastore"),
    ("mongo", "datastore"),
    ("redis", "datastore"),
    ("dynamodb", "datastore"),
    ("cassandra", "datastore"),
    ("elasticsearch", "datastore"),
    ("opensearch", "datastore"),
    ("rabbitmq", "queue"),
    ("kafka", "queue"),
    ("sqs", "queue"),
    ("nats", "queue"),
    ("nginx", "gateway"),
    ("traefik", "gateway"),
    ("envoy", "gateway"),
]

_COMPOSE_FILE_RE = re.compile(r"^docker-compose.*\.ya?ml$|^compose\.ya?ml$", re.IGNORECASE)
_SKIP_DIRS = {".git", "node_modules"}


def _kind_for_image(image: str | None) -> str:
    if not image:
        return "service"
    lowered = image.lower()
    for needle, kind in IMAGE_KIND_MAP:
        if needle in lowered:
            return kind
    return "service"


def _find_service_line(raw: str, service_name: str) -> int | None:
    """Match the service's own key line, e.g. '  raw_telemetry:' under a
    'services:' block. Anchored at line start + indentation to avoid matching
    the same name if it also appears as a value elsewhere (env vars, etc.)."""
    pattern = re.compile(r"^[ \t]+" + re.escape(service_name) + r":[ \t]*$", re.MULTILINE)
    match = pattern.search(raw)
    if match is None:
        return None
    return raw.count("\n", 0, match.start()) + 1


def _iter_compose_files(repo_path: Path):
    for path in repo_path.rglob("*"):
        if not path.is_file():
            continue
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        if _COMPOSE_FILE_RE.match(path.name):
            yield path


def _normalize_depends_on(value: object) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    if isinstance(value, dict):
        return list(value.keys())
    return []


def parse_compose(repo_path: str | Path) -> tuple[list[EvidenceRecord], list[EdgeRecord]]:
    repo_path = Path(repo_path)
    nodes: list[EvidenceRecord] = []
    edges: list[EdgeRecord] = []

    for compose_file in _iter_compose_files(repo_path):
        try:
            raw = compose_file.read_text(encoding="utf-8")
            parsed = yaml.safe_load(raw)
        except Exception:
            continue

        if not isinstance(parsed, dict):
            continue
        services = parsed.get("services")
        if not isinstance(services, dict):
            continue

        file_str = str(compose_file)

        for service_name, config in services.items():
            config = config or {}
            image = config.get("image") if isinstance(config, dict) else None
            line = _find_service_line(raw, service_name)

            nodes.append(
                EvidenceRecord(
                    kind=_kind_for_image(image),
                    identity=f"compose:{service_name}",
                    file=file_str,
                    line=line,
                    tier=TIER,
                    confidence=CONFIDENCE,
                    attrs={"image": image} if image else {},
                )
            )

            depends_on = _normalize_depends_on(config.get("depends_on")) if isinstance(config, dict) else []
            for dep in depends_on:
                edges.append(
                    EdgeRecord(
                        src=f"compose:{service_name}",
                        dst=f"compose:{dep}",
                        file=file_str,
                        line=line,
                        tier=TIER,
                        confidence=CONFIDENCE,
                        attrs={"relation": "depends_on"},
                    )
                )

    return nodes, edges
