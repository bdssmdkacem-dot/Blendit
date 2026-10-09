#!/usr/bin/env python3
"""Small authenticated bridge between the Blendit Android app and a local Blender install.

Run from the repository root:
  BLENDIT_TOKEN='choose-a-long-random-token' python3 tools/server/blendit_server.py
"""
from __future__ import annotations

import json
import os
import secrets
import struct
import subprocess
import sys
import threading
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[2]
GENERATOR = ROOT / "tools" / "blender" / "generate_asset_pack.py"
AUDITOR = ROOT / "tools" / "blender" / "audit_asset_quality.py"
OUTPUT = ROOT / "build" / "assets"
BLENDER = os.environ.get("BLENDIT_BLENDER", "blender")
HOST = os.environ.get("BLENDIT_HOST", "0.0.0.0")
PORT = int(os.environ.get("BLENDIT_PORT", "8765"))
TOKEN = os.environ.get("BLENDIT_TOKEN", "")
MAX_JOBS = 2
jobs: dict[str, dict] = {}
jobs_lock = threading.Lock()
job_slots = threading.BoundedSemaphore(MAX_JOBS)
ALLOWED_FILES = {
    "blendit_asset_pack.blend", "blendit_asset_pack.glb", "preview.png", "manifest.json",
    "crate.glb", "lantern.glb", "crystal.glb", "barrel.glb", "carriage.glb",
    "rock_cluster.glb", "pine_tree.glb", "stone_wall.glb", "bridge_segment.glb",
    "asset_quality_report.json",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def public_job(job: dict) -> dict:
    return {key: value for key, value in job.items() if key != "process"}


def validate_generated_pack(output: Path) -> None:
    required = set(ALLOWED_FILES)
    missing = sorted(name for name in required
                     if not (output / name).is_file() or (output / name).stat().st_size == 0)
    if missing:
        raise RuntimeError("Generated pack is incomplete; missing or empty: " + ", ".join(missing))

    manifest_path = output / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise RuntimeError("Generated manifest is unreadable: " + str(exc)) from exc
    outputs = manifest.get("outputs")
    if not isinstance(outputs, list) or not outputs:
        raise RuntimeError("Generated manifest has no output list")
    for name in outputs:
        if not isinstance(name, str) or name not in ALLOWED_FILES:
            raise RuntimeError("Manifest contains an unsupported output name")
        path = output / name
        if not path.is_file() or path.stat().st_size == 0:
            raise RuntimeError("Manifest output is missing or empty: " + name)

    glb_path = output / "blendit_asset_pack.glb"
    with glb_path.open("rb") as handle:
        header = handle.read(12)
    if len(header) != 12:
        raise RuntimeError("Combined GLB header is truncated")
    magic, version, declared_length = struct.unpack("<4sII", header)
    if magic != b"glTF" or version != 2 or declared_length != glb_path.stat().st_size:
        raise RuntimeError("Combined GLB file failed structural validation")
    with (output / "preview.png").open("rb") as handle:
        if handle.read(8) != bytes([137, 80, 78, 71, 13, 10, 26, 10]):
            raise RuntimeError("Preview PNG signature is invalid")


def generate(job_id: str) -> None:
    with jobs_lock:
        jobs[job_id]["status"] = "running"
        jobs[job_id]["started_at"] = now()
    try:
        if not job_slots.acquire(blocking=False):
            raise RuntimeError("The generation queue is busy. Try again when another job finishes.")
        try:
            OUTPUT.mkdir(parents=True, exist_ok=True)
            result = subprocess.run(
                [BLENDER, "--background", "--factory-startup", "--python", str(GENERATOR),
                 "--", "--output-dir", str(OUTPUT)],
                cwd=str(ROOT), capture_output=True, text=True, timeout=900, check=False,
            )
            if result.returncode != 0:
                tail = (result.stderr or result.stdout or "Blender failed without a log.")[-5000:]
                raise RuntimeError(tail)
            if "BLENDIT_GENERATION_OK" not in result.stdout:
                raise RuntimeError("Blender exited without the generator success marker.")
            audit = subprocess.run(
                [sys.executable, str(AUDITOR), str(OUTPUT)],
                cwd=str(ROOT), capture_output=True, text=True, timeout=120, check=False,
            )
            if audit.returncode != 0:
                details = (audit.stderr or audit.stdout or "Asset quality audit failed.")[-5000:]
                raise RuntimeError("Asset quality audit failed; pack is not ready for delivery.\n" + details)
            validate_generated_pack(OUTPUT)
            with jobs_lock:
                jobs[job_id].update(status="ready", message="Asset pack generated and validated.",
                                    log=result.stdout[-5000:], finished_at=now())
        finally:
            job_slots.release()
    except Exception as exc:
        with jobs_lock:
            jobs[job_id].update(status="failed", message=str(exc)[:5000], finished_at=now())


class Handler(BaseHTTPRequestHandler):
    server_version = "BlenditLocal/1.0"

    def log_message(self, fmt: str, *args) -> None:
        print("%s - %s" % (self.address_string(), fmt % args))

    def send_json(self, status: int, payload: dict) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def authorized(self) -> bool:
        supplied = self.headers.get("Authorization", "")
        return secrets.compare_digest(supplied, "Bearer " + TOKEN)

    def require_auth(self) -> bool:
        if not self.authorized():
            self.send_json(401, {"error": "Unauthorized. Configure the same BLENDIT_TOKEN in the server and app."})
            return False
        return True

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self.send_json(200, {"ok": True, "service": "Blendit Local Blender Bridge", "version": 1})
            return
        if not self.require_auth():
            return
        if parsed.path == "/api/jobs":
            with jobs_lock:
                items = sorted((public_job(job) for job in jobs.values()),
                               key=lambda item: item.get("created_at", ""), reverse=True)
            self.send_json(200, {"jobs": items[:30]})
            return
        if parsed.path.startswith("/api/jobs/"):
            job_id = parsed.path.rsplit("/", 1)[-1]
            with jobs_lock:
                job = jobs.get(job_id)
                snapshot = public_job(job) if job else None
            if not snapshot:
                self.send_json(404, {"error": "Job not found"})
            else:
                self.send_json(200, snapshot)
            return
        if parsed.path == "/api/assets":
            OUTPUT.mkdir(parents=True, exist_ok=True)
            files = [{"name": name, "size": (OUTPUT / name).stat().st_size,
                      "url": "/api/download/" + name}
                     for name in sorted(ALLOWED_FILES)
                     if (OUTPUT / name).is_file() and (OUTPUT / name).stat().st_size > 0]
            self.send_json(200, {"assets": files, "preview_url": "/api/download/preview.png" if any(f["name"] == "preview.png" for f in files) else None})
            return
        if parsed.path.startswith("/api/download/"):
            name = unquote(parsed.path.rsplit("/", 1)[-1])
            if name not in ALLOWED_FILES:
                self.send_json(400, {"error": "File is not in the allowed asset list"})
                return
            file_path = OUTPUT / name
            if not file_path.is_file():
                self.send_json(404, {"error": "Asset not generated yet"})
                return
            data = file_path.read_bytes()
            content_type = "image/png" if name.endswith(".png") else "application/octet-stream"
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Disposition", 'attachment; filename="' + name + '"')
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)
            return
        self.send_json(404, {"error": "Not found"})

    def do_POST(self) -> None:
        if not self.require_auth():
            return
        if urlparse(self.path).path != "/api/generate":
            self.send_json(404, {"error": "Not found"})
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self.send_json(400, {"error": "Invalid Content-Length"})
            return
        if length < 0:
            self.send_json(400, {"error": "Invalid Content-Length"})
            return
        if length > 4096:
            self.send_json(413, {"error": "Request too large"})
            return
        try:
            body = json.loads(self.rfile.read(length) or b"{}")
        except (json.JSONDecodeError, UnicodeDecodeError):
            self.send_json(400, {"error": "Invalid JSON"})
            return
        if not isinstance(body, dict):
            self.send_json(400, {"error": "JSON body must be an object"})
            return
        # The first release only runs the reviewed repository generator; it never executes client-supplied code.
        if body.get("task", "starter_pack") != "starter_pack":
            self.send_json(400, {"error": "This server version supports task=starter_pack only."})
            return
        with jobs_lock:
            active = sum(1 for job in jobs.values() if job["status"] in ("queued", "running"))
            if active >= MAX_JOBS:
                self.send_json(429, {"error": "Generation queue is full. Wait for an active job to finish."})
                return
            job_id = str(uuid.uuid4())
            jobs[job_id] = {"id": job_id, "task": "starter_pack", "status": "queued",
                            "message": "Queued for Blender.", "created_at": now()}
        threading.Thread(target=generate, args=(job_id,), daemon=True).start()
        self.send_json(202, public_job(jobs[job_id]))


def main() -> None:
    if not TOKEN or len(TOKEN) < 20:
        raise SystemExit("Set BLENDIT_TOKEN to a private random token of at least 20 characters before starting.")
    if not GENERATOR.is_file():
        raise SystemExit("Generator not found: " + str(GENERATOR))
    if not AUDITOR.is_file():
        raise SystemExit("Asset quality auditor not found: " + str(AUDITOR))
    try:
        version = subprocess.run([BLENDER, "--version"], capture_output=True, text=True, timeout=15, check=False)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise SystemExit("Could not run Blender. Install Blender and set BLENDIT_BLENDER if needed: " + str(exc))
    if version.returncode:
        raise SystemExit("Blender check failed: " + version.stderr[-1000:])
    print(version.stdout.splitlines()[0] if version.stdout else "Blender available")
    print("Blendit bridge listening on http://%s:%s" % (HOST, PORT))
    print("On your phone, enter this computer's LAN IP and port %s." % PORT)
    print("Keep the token private and allow port %s only on your trusted private network." % PORT)
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()
