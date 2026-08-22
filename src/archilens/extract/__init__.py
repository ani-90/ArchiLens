"""Directories that should never be treated as part of the scanned repo's
own code/infra: dependency trees, VCS metadata, and build output. Every
extractor across every tier must skip at least these -- a tier may extend
this set with its own additional skips (e.g. Terraform's .terraform cache,
k8s's Helm charts/templates dirs), but must never define a narrower one.
A narrower copy is exactly what let a third-party package's own bundled
docker-compose.yaml inside .venv get scanned as if it were the repo's own
infrastructure.
"""
COMMON_SKIP_DIRS = frozenset(
    {
        ".git",
        "node_modules",
        "vendor",
        "venv",
        ".venv",
        "__pycache__",
        "dist",
        "build",
    }
)
