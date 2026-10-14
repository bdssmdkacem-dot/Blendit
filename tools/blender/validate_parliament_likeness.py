#!/usr/bin/env python3
"""Audit reference-led parliament likeness readiness without requiring Blender.

This tool deliberately separates anonymous archetypes from real-person likenesses.
A profile is never considered ready merely because a GLB exists.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REQUIRED_REFERENCE_FIELDS = (
    "reference_image",
    "reference_image_url",
    "reference_accessed_on",
    "reference_rights_status",
    "reference_credit",
)
REQUIRED_VIEWS = ("front", "three_quarter", "profile")
APPROVED_RIGHTS = {"public_domain", "licensed_for_redistribution", "permission_granted"}


def audit(data: dict, repo_root: Path) -> tuple[list[dict], list[str]]:
    problems: list[str] = []
    results: list[dict] = []
    if data.get("status") != "reference_catalog_only_not_3d_likenesses":
        problems.append("Catalog status must remain reference_catalog_only_not_3d_likenesses until reviewed.")
    ids: set[str] = set()
    for profile in data.get("profiles", []):
        pid = profile.get("id", "<missing-id>")
        missing = []
        if pid in ids:
            problems.append(f"{pid}: duplicate profile id")
        ids.add(pid)
        for field in REQUIRED_REFERENCE_FIELDS:
            if not profile.get(field):
                missing.append(field)
        image_path = profile.get("reference_image")
        if image_path:
            path = (repo_root / image_path).resolve()
            if not path.is_relative_to(repo_root.resolve()) or not path.is_file() or path.stat().st_size == 0:
                missing.append("existing_nonempty_reference_image")
        rights = profile.get("reference_rights_status", "")
        if rights and rights not in APPROVED_RIGHTS:
            missing.append("verified_reuse_rights")
        views = profile.get("preview_views", {})
        for view in REQUIRED_VIEWS:
            path_text = views.get(view)
            if not path_text:
                missing.append(f"{view}_preview")
            else:
                path = (repo_root / path_text).resolve()
                if not path.is_relative_to(repo_root.resolve()) or not path.is_file() or path.stat().st_size == 0:
                    missing.append(f"existing_{view}_preview")
        if profile.get("sculpt_status") != "complete":
            missing.append("sculpt_status_complete")
        if profile.get("approval_status") != "approved":
            missing.append("human_visual_approval")
        status = "ready_for_review" if not missing else "blocked_on_reference" if any(
            field in missing for field in REQUIRED_REFERENCE_FIELDS
        ) or "existing_nonempty_reference_image" in missing or "verified_reuse_rights" in missing else "incomplete"
        results.append({"id": pid, "status": status, "missing": sorted(set(missing))})
    if not results:
        problems.append("No named profiles found.")
    return results, problems


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", default="data/parliament/real_figure_profiles.json")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--json-out", help="Optional path for a machine-readable audit report.")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve()
    try:
        data = json.loads((root / args.catalog).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"ERROR: cannot read catalog: {exc}", file=sys.stderr)
        return 2
    results, problems = audit(data, root)
    report = {"schema_version": 1, "catalog_status": data.get("status"), "profiles": results, "errors": problems}
    if args.json_out:
        target = (root / args.json_out).resolve()
        if not target.is_relative_to(root):
            print("ERROR: --json-out must stay inside repository root.", file=sys.stderr)
            return 2
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    for item in results:
        missing = ", ".join(item["missing"]) or "all gates satisfied; human sign-off still required"
        print(f'{item["id"]}: {item["status"]}; missing: {missing}')
    for problem in problems:
        print(f"ERROR: {problem}", file=sys.stderr)
    # Missing production inputs are reported as blocked, not treated as a fake pass.
    # The CI audit passes if the catalog is valid and no profile is falsely approved.
    falsely_approved = [
        p["id"] for p in data.get("profiles", [])
        if p.get("approval_status") == "approved" and p.get("sculpt_status") != "complete"
    ]
    if falsely_approved:
        print("ERROR: approved profiles lack completed sculpt: " + ", ".join(falsely_approved), file=sys.stderr)
        return 1
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
