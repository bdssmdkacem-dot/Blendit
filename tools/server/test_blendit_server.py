import json
import struct
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import blendit_server as bridge


class BridgeApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        bridge.OUTPUT = __import__("pathlib").Path(cls.temp.name)
        bridge.TOKEN = "test-token-with-at-least-twenty-characters"
        cls.server = ThreadingHTTPServer(("127.0.0.1", 0), bridge.Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = "http://127.0.0.1:%s" % cls.server.server_port

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)
        cls.temp.cleanup()

    def request(self, path, token=None, method="GET", body=None):
        headers = {}
        if token:
            headers["Authorization"] = "Bearer " + token
        data = None
        if body is not None:
            data = json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        req = Request(self.base + path, data=data, headers=headers, method=method)
        return urlopen(req, timeout=3)

    def test_health_is_available_without_token(self):
        with self.request("/health") as response:
            payload = json.loads(response.read())
            self.assertEqual(response.status, 200)
            self.assertTrue(payload["ok"])

    def test_assets_require_token(self):
        with self.assertRaises(HTTPError) as caught:
            self.request("/api/assets")
        self.assertEqual(caught.exception.code, 401)

    def test_asset_listing_is_empty_before_generation(self):
        with self.request("/api/assets", token=bridge.TOKEN) as response:
            self.assertEqual(json.loads(response.read())["assets"], [])

    def test_unknown_download_is_rejected(self):
        with self.assertRaises(HTTPError) as caught:
            self.request("/api/download/not-allowed.bin", token=bridge.TOKEN)
        self.assertEqual(caught.exception.code, 400)

    def test_client_cannot_choose_arbitrary_generation_task(self):
        with self.assertRaises(HTTPError) as caught:
            self.request("/api/generate", token=bridge.TOKEN, method="POST",
                         body={"task": "run-arbitrary-python"})
        self.assertEqual(caught.exception.code, 400)

    def test_generation_rejects_non_object_json(self):
        request = Request(
            self.base + "/api/generate",
            data=json.dumps(["starter_pack"]).encode("utf-8"),
            headers={"Authorization": "Bearer " + bridge.TOKEN,
                     "Content-Type": "application/json"},
            method="POST",
        )
        with self.assertRaises(HTTPError) as caught:
            urlopen(request, timeout=3)
        self.assertEqual(caught.exception.code, 400)

    def test_generation_rejects_invalid_json(self):
        request = Request(
            self.base + "/api/generate",
            data=b"{invalid",
            headers={"Authorization": "Bearer " + bridge.TOKEN,
                     "Content-Type": "application/json"},
            method="POST",
        )
        with self.assertRaises(HTTPError) as caught:
            urlopen(request, timeout=3)
        self.assertEqual(caught.exception.code, 400)

    def _write_validatable_pack(self, output):
        for filename in bridge.ALLOWED_FILES:
            (output / filename).write_bytes(b"placeholder")
        (output / "manifest.json").write_text(json.dumps({
            "outputs": sorted(bridge.ALLOWED_FILES - {"manifest.json"})
        }), encoding="utf-8")
        (output / "blendit_asset_pack.glb").write_bytes(
            struct.pack("<4sII", b"glTF", 2, 12)
        )
        (output / "preview.png").write_bytes(
            bytes([137, 80, 78, 71, 13, 10, 26, 10]) + b"test"
        )

    def test_generated_pack_validation_accepts_correct_png_signature(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            self._write_validatable_pack(output)
            bridge.validate_generated_pack(output)

    def test_generated_pack_validation_rejects_invalid_png_signature(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            self._write_validatable_pack(output)
            (output / "preview.png").write_bytes(b"NOTPNG!!image-data")
            with self.assertRaisesRegex(RuntimeError, "PNG signature"):
                bridge.validate_generated_pack(output)

    def test_generated_pack_validation_rejects_missing_files(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(RuntimeError, "incomplete"):
                bridge.validate_generated_pack(Path(directory))

    def test_generated_pack_validation_rejects_invalid_glb(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            for filename in bridge.ALLOWED_FILES:
                (output / filename).write_bytes(b"placeholder")
            (output / "manifest.json").write_text(json.dumps({
                "outputs": sorted(bridge.ALLOWED_FILES - {"manifest.json"})
            }), encoding="utf-8")
            (output / "preview.png").write_bytes(b"\\x89PNG\\r\\n\\x1a\\nrest")
            (output / "blendit_asset_pack.glb").write_bytes(
                struct.pack("<4sII", b"NOPE", 2, 12)
            )
            with self.assertRaisesRegex(RuntimeError, "GLB"):
                bridge.validate_generated_pack(output)


if __name__ == "__main__":
    unittest.main()
