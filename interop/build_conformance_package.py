"""Build a deterministic Protocol 0.1 conformance-review archive."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INTEROP_ROOT = REPO_ROOT / "interop"
OUTPUT_PATH = REPO_ROOT / "dist" / "atmanatic-protocol-0.1-conformance.zip"
PACKAGE_ROOT = "atmanatic-protocol-0.1-conformance"

STATIC_FILES = (
    "ATMANATIC_PROTOCOL_0.1_DRAFT.md",
    "atmanatic_research/canonical.py",
    "atmanatic_research/error_codes.py",
    "atmanatic_research/timestamps.py",
    "interop/README.md",
    "interop/INTEROPERABILITY_REPORT.md",
    "interop/schemas/common_envelope.schema.json",
    "interop/schemas/evidence_card.schema.json",
    "interop/schemas/proposal_envelope.schema.json",
    "interop/schemas/review_outcome.schema.json",
    "interop/schemas/verification_result.schema.json",
    "interop/schemas/promotion_record.schema.json",
    "interop/reference-ts/package.json",
    "interop/reference-ts/package-lock.json",
    "interop/reference-ts/tsconfig.json",
    "interop/reference-ts/src/checkFixtures.ts",
    "interop/reference-ts/src/index.ts",
)


def _included_files() -> tuple[str, ...]:
    fixture_files = tuple(
        path.relative_to(REPO_ROOT).as_posix()
        for path in sorted((INTEROP_ROOT / "fixtures").rglob("*.json"))
    )
    return STATIC_FILES + fixture_files


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _manifest() -> dict[str, object]:
    files = []
    for relative_path in _included_files():
        source = REPO_ROOT / relative_path
        if not source.is_file():
            raise FileNotFoundError(f"conformance package input is missing: {relative_path}")
        files.append({"path": relative_path, "sha256": _sha256(source)})
    return {
        "protocol": "Atmanatic Protocol 0.1",
        "status": "working-draft-conformance-review",
        "implementation_scope": [
            "artifact_lineage",
            "evidence_card",
            "proposal_envelope",
            "review_outcome",
            "verification_result",
            "promotion_record",
            "canonical_content_hash",
        ],
        "fixture_count": len(json.loads((INTEROP_ROOT / "fixtures" / "manifest.json").read_text(encoding="utf-8"))),
        "files": files,
        "instructions": "Run npm ci && npm test in reference-ts, then implement the same fixtures independently.",
    }


def build() -> Path:
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="atmanatic-conformance-") as temporary:
        root = Path(temporary) / PACKAGE_ROOT
        root.mkdir()
        for relative_path in _included_files():
            destination = root / relative_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(REPO_ROOT / relative_path, destination)

        manifest_path = root / "CONFORMANCE_MANIFEST.json"
        manifest_path.write_text(json.dumps(_manifest(), indent=2) + "\n", encoding="utf-8")
        readme = root / "EXTERNAL_REVIEW.md"
        readme.write_text(
            "# External Protocol 0.1 Conformance Review\n\n"
            "This archive freezes the current protocol-core schemas, fixtures, "
            "canonical hash vector, and independent TypeScript reference slice.\n\n"
            "Reviewers should verify every listed SHA-256, run the TypeScript "
            "reference tests, and implement the fixture corpus independently. "
            "Agreement must include the verdict and machine-readable error code.\n",
            encoding="utf-8",
        )

        with zipfile.ZipFile(OUTPUT_PATH, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(root.rglob("*")):
                if path.is_file():
                    entry = path.relative_to(Path(temporary)).as_posix()
                    info = zipfile.ZipInfo(entry, date_time=(2026, 1, 1, 0, 0, 0))
                    info.compress_type = zipfile.ZIP_DEFLATED
                    info.external_attr = 0o644 << 16
                    archive.writestr(info, path.read_bytes())
    return OUTPUT_PATH


if __name__ == "__main__":
    print(build())
