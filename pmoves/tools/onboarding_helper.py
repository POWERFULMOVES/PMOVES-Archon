"""Onboarding helper for PMOVES secret management."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from pmoves.chit.codec import decode_secret_map, load_cgp
from pmoves.tools import secrets_sync

REPO_ROOT = secrets_sync.REPO_ROOT


def format_missing(missing: Sequence[str]) -> str:
    if not missing:
        return "None"
    return "\n  - " + "\n  - ".join(sorted(missing))


def cmd_status(manifest: Path) -> int:
    cgp_path, entries = secrets_sync.load_manifest(manifest)
    secrets = decode_secret_map(load_cgp(cgp_path))
    outputs, missing = secrets_sync.build_outputs(secrets, entries, strict=False)
    total_entries = len(entries)
    decoded = len(secrets)
    targets = {file: len(values) for file, values in outputs.items()}

    print(f"Manifest: {manifest.relative_to(REPO_ROOT)}")
    print(f"CGP file: {cgp_path.relative_to(REPO_ROOT)}")
    print(f"Entries defined: {total_entries}")
    print(f"Secrets decoded: {decoded}")
    print("Planned outputs:")
    for file, count in sorted(targets.items()):
        print(f"  - {file}: {count} variables")
    print("Missing required labels:" + format_missing(missing))
    if missing:
        print(
            "\nAdd the missing labels to the CHIT bundle defined in pmoves/chit/secrets_manifest.yaml "
            "or relax `required: true` for optional keys."
        )
    return 0


def cmd_generate(manifest: Path) -> int:
    cgp_path, entries = secrets_sync.load_manifest(manifest)
    secrets = decode_secret_map(load_cgp(cgp_path))
    outputs, missing = secrets_sync.build_outputs(secrets, entries, strict=False)
    if missing:
        print("Cannot generate env files; required secrets missing:")
        for label in sorted(missing):
            print(f"  - {label}")
        print("Update the CHIT payload before rerunning.")
        return 1
    secrets_sync.write_env_files(outputs)
    print(secrets_sync.report(outputs))
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Automated onboarding helper for PMOVES secrets.")
    parser.add_argument(
        "command",
        choices=("status", "generate"),
        help="status → report manifest coverage, generate → write env files",
    )
    parser.add_argument(
        "--manifest",
        default="pmoves/chit/secrets_manifest.yaml",
        help="path to secrets manifest (default: pmoves/chit/secrets_manifest.yaml)",
    )
    args = parser.parse_args(argv)
    manifest_path = (REPO_ROOT / args.manifest).resolve()
    if args.command == "status":
        return cmd_status(manifest_path)
    return cmd_generate(manifest_path)


if __name__ == "__main__":
    sys.exit(main())
