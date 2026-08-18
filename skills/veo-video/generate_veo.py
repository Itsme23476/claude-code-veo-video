#!/usr/bin/env python3
"""Generate a video with Google Veo on Vertex AI (billed to your Google Cloud project).

Auth: uses Application Default Credentials (run `gcloud auth application-default login` first).
Flow: submit predictLongRunning -> poll fetchPredictOperation -> download the mp4.
Stdlib only. The operation name is saved to <output>.op immediately so a slow generation is
never lost — if this script is interrupted, re-run with --resume <op-file> to fetch the result.
"""
import argparse, base64, json, os, subprocess, sys, time, urllib.error, urllib.request


def adc_token() -> str:
    try:
        return subprocess.check_output(
            ["gcloud", "auth", "application-default", "print-access-token"],
            text=True, stderr=subprocess.DEVNULL).strip()
    except Exception:
        sys.exit("❌ No ADC token. Run: gcloud auth application-default login")


def post(url: str, body: dict, tok: str) -> dict:
    req = urllib.request.Request(url, data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {tok}",
                                          "Content-Type": "application/json"})
    try:
        return json.load(urllib.request.urlopen(req, timeout=120))
    except urllib.error.HTTPError as e:
        sys.exit(f"❌ HTTP {e.code}: {e.read().decode()[:600]}")


def load_image(path: str) -> dict:
    import mimetypes
    mime = mimetypes.guess_type(path)[0] or "image/png"
    with open(path, "rb") as f:
        return {"bytesBase64Encoded": base64.b64encode(f.read()).decode(), "mimeType": mime}


def extract_and_save(resp: dict, out: str) -> bool:
    """Handle the possible Veo response shapes; save mp4 if bytes are present."""
    print("  response keys:", list(resp.keys()))
    for v in (resp.get("videos") or []):
        b64 = v.get("bytesBase64Encoded")
        if b64:
            data = base64.b64decode(b64)
            with open(out, "wb") as f:
                f.write(data)
            print(f"✅ saved {out} ({len(data):,} bytes, {v.get('mimeType','video/mp4')})")
            return True
        if v.get("gcsUri") or v.get("uri"):
            print(f"✅ video in GCS: {v.get('gcsUri') or v.get('uri')}")
            return True
    for s in (resp.get("generatedSamples") or []):
        vid = s.get("video", {})
        if vid.get("uri"):
            print(f"✅ video in GCS: {vid['uri']}")
            return True
    filtered = resp.get("raiMediaFilteredCount", 0)
    if filtered:
        print(f"⚠️ {filtered} sample(s) filtered by safety: {resp.get('raiMediaFilteredReasons')}")
    print("⚠️ no downloadable video found. Full response (truncated):")
    print(json.dumps(resp)[:1200])
    return False


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--prompt")
    p.add_argument("--model", default="veo-3.1-fast-generate-preview")
    p.add_argument("--project", default=os.environ.get("GOOGLE_CLOUD_PROJECT"))
    p.add_argument("--location", default="us-central1")
    p.add_argument("--duration", type=int, default=8)
    p.add_argument("--aspect", default="16:9")
    p.add_argument("--resolution", default="720p")
    p.add_argument("--no-audio", action="store_true")
    p.add_argument("--samples", type=int, default=1)
    p.add_argument("--output", default="veo_output.mp4")
    p.add_argument("--image", help="starting (first-frame) image path — image-to-video")
    p.add_argument("--last-frame", help="ending (last-frame) image path — Veo 3.1 first->last interpolation")
    p.add_argument("--resume", help="path to a saved .op file to fetch an existing generation")
    a = p.parse_args()

    if not a.project:
        pf = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".project")
        if os.path.exists(pf):
            a.project = open(pf).read().strip()
    if not a.project:
        sys.exit("❌ No project. Run connect-vertex.sh, or pass --project / export GOOGLE_CLOUD_PROJECT")
    tok = adc_token()
    base = (f"https://{a.location}-aiplatform.googleapis.com/v1/projects/{a.project}"
            f"/locations/{a.location}/publishers/google/models/{a.model}")

    if a.resume:
        opname = open(a.resume).read().strip()
        print(f"→ resuming operation: {opname}")
    else:
        if not a.prompt:
            sys.exit("❌ --prompt is required")
        extras = ("" + (", +image" if a.image else "") + (", +lastFrame" if a.last_frame else ""))
        print(f"→ submitting to {a.model} ({a.duration}s, {a.resolution}, audio={not a.no_audio}{extras})")
        params = {"sampleCount": a.samples, "durationSeconds": a.duration,
                  "aspectRatio": a.aspect, "resolution": a.resolution,
                  "generateAudio": not a.no_audio}
        instance = {"prompt": a.prompt}
        if a.image:
            instance["image"] = load_image(a.image)
        if a.last_frame:
            instance["lastFrame"] = load_image(a.last_frame)
        op = post(base + ":predictLongRunning",
                  {"instances": [instance], "parameters": params}, tok)
        opname = op["name"]
        with open(a.output + ".op", "w") as f:
            f.write(opname)
        print(f"  operation: {opname}")
        print(f"  (saved to {a.output}.op — resume with: --resume {a.output}.op)")

    for i in range(90):  # up to ~15 min
        r = post(base + ":fetchPredictOperation", {"operationName": opname}, tok)
        if r.get("done"):
            if "error" in r:
                sys.exit(f"❌ generation error: {r['error']}")
            ok = extract_and_save(r.get("response", {}), a.output)
            if ok and os.path.exists(a.output + ".op"):
                os.remove(a.output + ".op")
            sys.exit(0 if ok else 2)
        print(f"  ...generating ({(i + 1) * 10}s elapsed)")
        time.sleep(10)
    sys.exit("❌ timed out after 15 min (resume with the .op file)")


if __name__ == "__main__":
    main()
