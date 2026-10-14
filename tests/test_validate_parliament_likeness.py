import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "blender"))

from validate_parliament_likeness import audit  # noqa: E402


class ParliamentLikenessAuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.catalog = {
            "status": "reference_catalog_only_not_3d_likenesses",
            "profiles": [{"id": "ahmed_touizi"}],
        }

    def tearDown(self):
        self.temp.cleanup()

    def complete_profile(self, approval="not_reviewed"):
        profile = {
            "id": "ahmed_touizi",
            "reference_image": "refs/touizi.jpg",
            "reference_image_url": "https://example.org/portrait",
            "reference_accessed_on": "2026-10-14",
            "reference_rights_status": "permission_granted",
            "reference_credit": "Photographer name; permission recorded",
            "preview_views": {
                "front": "previews/front.png",
                "three_quarter": "previews/three_quarter.png",
                "profile": "previews/profile.png",
            },
            "sculpt_status": "complete",
            "approval_status": approval,
        }
        for rel in [
            profile["reference_image"],
            *profile["preview_views"].values(),
        ]:
            path = self.root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"test-image-bytes")
        return profile

    def test_missing_portrait_and_rights_are_blocked(self):
        results, errors = audit(self.catalog, self.root)
        self.assertEqual(errors, [])
        self.assertEqual(results[0]["status"], "blocked_on_reference")
        self.assertIn("reference_image_url", results[0]["missing"])
        self.assertIn("verified_reuse_rights", results[0]["missing"])

    def test_complete_sculpt_waits_for_human_visual_approval(self):
        self.catalog["profiles"] = [self.complete_profile()]
        results, errors = audit(self.catalog, self.root)
        self.assertEqual(errors, [])
        self.assertEqual(results[0]["status"], "ready_for_review")
        self.assertEqual(results[0]["missing"], ["human_visual_approval"])

    def test_approved_profile_requires_all_gates(self):
        self.catalog["profiles"] = [self.complete_profile(approval="approved")]
        results, errors = audit(self.catalog, self.root)
        self.assertEqual(errors, [])
        self.assertEqual(results[0]["status"], "approved")
        self.assertEqual(results[0]["missing"], [])

    def test_approval_without_verified_rights_is_never_approved(self):
        profile = self.complete_profile(approval="approved")
        profile["reference_rights_status"] = "unknown"
        self.catalog["profiles"] = [profile]
        results, _ = audit(self.catalog, self.root)
        self.assertEqual(results[0]["status"], "blocked_on_reference")
        self.assertIn("verified_reuse_rights", results[0]["missing"])


if __name__ == "__main__":
    unittest.main()
