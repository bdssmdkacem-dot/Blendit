#!/usr/bin/env python3
"""Audit exported Blendit GLBs for engine-facing structural quality.

This is a technical gate, not an artistic-quality score. A passing report must
still be paired with visual inspection of preview.png and the Godot play-scene.
"""
from __future__ import annotations

import json
import struct
import sys
from pathlib import Path


def read_glb(path: Path) -> dict:
    data = path.read_bytes()
    if len(data) < 20 or data[:4] != b"glTF":
        raise ValueError(f"{path.name}: invalid or truncated GLB")
    version, declared_length = struct.unpack_from("<II", data, 4)
    if version != 2 or declared_length != len(data):
        raise ValueError(f"{path.name}: invalid GLB version/length")
    chunk_length, chunk_type = struct.unpack_from("<II", data, 12)
    if chunk_type != 0x4E4F534A or 20 + chunk_length > len(data):
        raise ValueError(f"{path.name}: missing or invalid JSON chunk")
    return json.loads(data[20:20 + chunk_length].decode("utf-8").rstrip(" \x00"))


def audit_asset(path: Path) -> dict:
    gltf = read_glb(path)
    meshes = gltf.get("meshes", [])
    materials = gltf.get("materials", [])
    accessors = gltf.get("accessors", [])
    primitives = [primitive for mesh in meshes for primitive in mesh.get("primitives", [])]
    vertex_count = 0
    triangle_count = 0
    missing_position = 0
    missing_material = 0
    invalid_indices = 0
    invalid_modes = 0
    for primitive in primitives:
        attributes = primitive.get("attributes", {})
        position_index = attributes.get("POSITION")
        valid_position = (
            isinstance(position_index, int)
            and not isinstance(position_index, bool)
            and 0 <= position_index < len(accessors)
        )
        if not valid_position:
            missing_position += 1
        else:
            accessor = accessors[position_index]
            count = accessor.get("count", 0)
            if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
                missing_position += 1
            else:
                vertex_count += count
        material_index = primitive.get("material")
        valid_material = (
            isinstance(material_index, int)
            and not isinstance(material_index, bool)
            and 0 <= material_index < len(materials)
        )
        if not valid_material:
            missing_material += 1
        mode = primitive.get("mode", 4)
        if mode != 4:
            invalid_modes += 1
            continue
        index = primitive.get("indices")
        if index is not None:
            valid_index = (
                isinstance(index, int)
                and not isinstance(index, bool)
                and 0 <= index < len(accessors)
            )
            if not valid_index:
                invalid_indices += 1
                continue
            index_accessor = accessors[index]
            index_count = index_accessor.get("count", 0)
            if not isinstance(index_count, int) or isinstance(index_count, bool) or index_count < 3:
                invalid_indices += 1
                continue
            if index_count % 3:
                invalid_indices += 1
                continue
            triangle_count += index_count // 3
        elif valid_position:
            count = accessors[position_index].get("count", 0)
            if isinstance(count, int) and not isinstance(count, bool) and count >= 3:
                if count % 3:
                    invalid_indices += 1
                else:
                    triangle_count += count // 3
    issues = []
    if not meshes or not primitives:
        issues.append("no_mesh_primitives")
    if not materials:
        issues.append("no_materials")
    if missing_position:
        issues.append(f"{missing_position}_primitives_without_positions")
    if missing_material:
        issues.append(f"{missing_material}_primitives_without_material")
    if invalid_indices:
        issues.append(f"{invalid_indices}_primitives_with_invalid_index_data")
    if invalid_modes:
        issues.append(f"{invalid_modes}_primitives_not_triangle_lists")
    if vertex_count <= 0 or triangle_count <= 0:
        issues.append("no_renderable_triangles")
    return {
        "file": path.name,
        "bytes": path.stat().st_size,
        "mesh_count": len(meshes),
        "primitive_count": len(primitives),
        "material_count": len(materials),
        "texture_count": len(gltf.get("textures", [])),
        "vertex_count": vertex_count,
        "triangle_count": triangle_count,
        "issues": issues,
        "status": "fail" if issues else "pass",
    }


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: python3 tools/blender/audit_asset_quality.py <asset-output-dir>", file=sys.stderr)
        return 2
    root = Path(sys.argv[1]).resolve()
    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        print(f"Missing manifest: {manifest_path}", file=sys.stderr)
        return 2
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    results = []
    failures = []
    for asset in manifest.get("assets", []):
        filename = asset.get("glb_file")
        if not isinstance(filename, str) or Path(filename).name != filename:
            failures.append({"file": str(filename), "issues": ["invalid_manifest_filename"]})
            continue
        path = root / filename
        if not path.is_file():
            failures.append({"file": filename, "issues": ["missing_file"]})
            continue
        try:
            result = audit_asset(path)
        except (OSError, ValueError, json.JSONDecodeError, UnicodeDecodeError, struct.error) as exc:
            result = {"file": filename, "status": "fail", "issues": [str(exc)]}
        results.append(result)
        if result["status"] != "pass":
            failures.append({"file": filename, "issues": result["issues"]})
    report = {
        "schema_version": 1,
        "purpose": "technical export audit; not a substitute for visual/game-engine review",
        "asset_count": len(results),
        "passed": sum(item["status"] == "pass" for item in results),
        "failed": len(failures),
        "assets": results,
        "failures": failures,
    }
    (root / "asset_quality_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    for item in results:
        print(f'{item["status"].upper():4} {item["file"]}: meshes={item.get("mesh_count", 0)}, '
              f'vertices={item.get("vertex_count", 0)}, triangles={item.get("triangle_count", 0)}, '
              f'materials={item.get("material_count", 0)}, bytes={item.get("bytes", 0)}')
    print(f'Quality audit: {report["passed"]}/{report["asset_count"]} assets passed; report={root / "asset_quality_report.json"}')
    if failures:
        print(json.dumps(failures, indent=2), file=sys.stderr)
        return 1
    if report["asset_count"] == 0:
        print("No assets were audited.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
