#!/usr/bin/env python3
"""Local web UI backend for Veo video generation. Stdlib only — no pip installs.
Serves the front-end and runs the validated generate_veo.py per request (async jobs)."""
import json, os, subprocess, sys, uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

HERE = os.path.dirname(os.path.abspath(__file__))
PUBLIC = os.path.join(HERE, "public")
OUTPUTS = os.path.join(HERE, "outputs")
GEN = os.path.normpath(os.path.join(HERE, "..", "skills", "veo-video", "generate_veo.py"))
os.makedirs(OUTPUTS, exist_ok=True)

def project():
    p = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if p:
        return p
    for c in (os.path.join(os.path.expanduser("~"), ".claude", "skills", "veo-video", ".project"),
              os.path.join(HERE, "..", ".veo-project")):
        if os.path.exists(c):
            return open(c).read().strip()
    return None

JOBS = {}  # id -> {proc, output}
CT = {"html": "text/html", "css": "text/css", "js": "application/javascript"}


class H(BaseHTTPRequestHandler):
    def _s(self, code, body, ctype="application/json"):
        b = body if isinstance(body, bytes) else body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        u = urlparse(self.path)
        path = "/index.html" if u.path == "/" else u.path
        if path.startswith("/api/status"):
            jid = parse_qs(u.query).get("job", [""])[0]
            job = JOBS.get(jid)
            if not job:
                return self._s(404, json.dumps({"status": "error", "error": "unknown job"}))
            rc = job["proc"].poll()
            if rc is None:
                return self._s(200, json.dumps({"status": "running"}))
            if rc == 0 and os.path.exists(job["output"]):
                return self._s(200, json.dumps({"status": "done",
                                                 "videoUrl": "/outputs/" + os.path.basename(job["output"])}))
            err = (job["proc"].stderr.read().decode()[-400:] if job["proc"].stderr else "") or "generation failed"
            return self._s(200, json.dumps({"status": "error", "error": err}))
        if path.startswith("/outputs/"):
            fp = os.path.join(OUTPUTS, os.path.basename(path))
            return self._s(200, open(fp, "rb").read(), "video/mp4") if os.path.exists(fp) \
                else self._s(404, b"not found", "text/plain")
        fp = os.path.join(PUBLIC, path.lstrip("/"))
        if os.path.isfile(fp):
            return self._s(200, open(fp, "rb").read(), CT.get(fp.rsplit(".", 1)[-1], "text/plain"))
        self._s(404, b"not found", "text/plain")

    def do_POST(self):
        if self.path != "/api/generate":
            return self._s(404, b"", "text/plain")
        n = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(n) or "{}")
        proj = project()
        if not proj:
            return self._s(400, json.dumps({"error": "No project. Run ./connect-vertex.sh first."}))
        prompt = (body.get("prompt") or "").strip()
        if not prompt:
            return self._s(400, json.dumps({"error": "prompt required"}))
        jid = uuid.uuid4().hex[:12]
        out = os.path.join(OUTPUTS, jid + ".mp4")
        cmd = [sys.executable, GEN, "--prompt", prompt, "--project", proj,
               "--model", body.get("model", "veo-3.1-fast-generate-001"),
               "--duration", str(body.get("duration", 4)),
               "--aspect", body.get("aspect", "16:9"),
               "--resolution", body.get("resolution", "720p"),
               "--output", out]
        if not body.get("audio", True):
            cmd.append("--no-audio")
        JOBS[jid] = {"proc": subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE),
                     "output": out}
        self._s(200, json.dumps({"jobId": jid}))

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8787"))
    print(f"🎬  Veo Studio → http://localhost:{port}   (project: {project()})")
    print("    Ctrl+C to stop.")
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()
