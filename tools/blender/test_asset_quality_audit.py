"""Unit tests for the standalone GLB technical quality audit."""
from __future__ import annotations

import importlib.util
import json
import struct
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).with_name("audit_asset_quality.py")
SPEC = importlib.util.spec_from_file_location("blendit_asset_quality_audit", MODULE_PATH)
AUDIT = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(AUDIT)


def write_glb(path: Path, *, index_count: int = 3, material_index: int = 0) -> None:
    document = {
        "asset": {"version": "2.0", "generator": "Blendit audit tests"},
        "scene": 0,
        "scenes": [{"nodes": [0]}],
        "nodes": [{"mesh": 0}],
        "meshes": [{
            "primitives": [{
                "attributes": {"POSITION": 0},
                "indices": 1,
                "material": material_index,
                "mode": 4,
            }]
        }],
        "materials": [{"name": "Test material"}],
        "accessors": [
            {"componentType": 5126, "count": 3, "type": "VEC3",
             "min": [0, 0, 0], "max": [1, 1, 0]},
            {"componentType": 5123, "count": index_count, "type": "SCALAR",
             "min": [0], "max": [2]},
        ],
        "buffers": [{"byteLength": 0}],
    }
    encoded = json.dumps(document, separators=(",", ":")).encode("utf-8")
    encoded += b" " * ((4 - len(encoded) % 4) % 4)
    total_length = 12 + 8 + len(encoded)
    path.write_bytes(
        struct.pack("<4sII", b"glTF", 2, total_length)
        + struct.pack("<II", len(encoded), 0x4E4F534A)
        + encoded
    )


class AssetQualityAuditTests(unittest.TestCase):
    def test_accepts_renderable_triangle_with_material(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "valid.glb"
            write_glb(path)
            report = AUDIT.audit_asset(path)
            self.assertEqual(report["status"], "pass")
            self.assertEqual(report["triangle_count"], 1)
            self.assertEqual(report["material_count"], 1)

    def test_rejects_index_count_not_divisible_by_three(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid-indices.glb"
            write_glb(path, index_count=4)
            report = AUDIT.audit_asset(path)
            self.assertEqual(report["status"], "fail")
            self.assertIn("1_primitives_with_invalid_index_data", report["issues"])

    def test_rejects_missing_material_reference(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid-material.glb"
            write_glb(path, material_index=4)
            report = AUDIT.audit_asset(path)
            self.assertEqual(report["status"], "fail")
            self.assertIn("1_primitives_without_material", report["issues"])

    def test_rejects_truncated_glb(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "truncated.glb"
            path.write_bytes(b"glTF")
            with self.assertRaises(ValueError):
                AUDIT.audit_asset(path)


if __name__ == "__main__":
    unittest.main()
