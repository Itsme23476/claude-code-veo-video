---
name: veo-video
description: Generate an AI video (with sound) from a text prompt using Google Veo 3 on Vertex AI, billed to the user's own Google Cloud project / $300 credit. Use whenever the user asks to generate, create, or make a video, an AI video, a Veo clip, b-roll, a Short/Reel, or to animate a scene from a description.
---

# Veo Video Generation (Google Veo 3 on Vertex AI)

Generates real MP4 videos **with native audio** using Google Veo 3.1, billed to the user's Google
Cloud project (their $300 credit). Wraps the bundled `generate_veo.py` (submit → poll → download).

## When to use
Requests like: "generate a video of…", "make an 8-second clip of…", "create b-roll of…",
"a Veo video of…", "vertical video for Shorts of…".

## Prerequisites (check quietly; fix if missing)
1. **ADC works** — `gcloud auth application-default print-access-token` returns a token.
   If not, tell the user to run `gcloud auth application-default login` (opens the browser).
2. **A project id** with Vertex AI enabled + billing. It comes from `GOOGLE_CLOUD_PROJECT`, or the
   `.project` file next to the script. If neither is set, run the repo's `connect-vertex.sh`.

## How to generate
Run the bundled script (it sits in this skill's own directory):
```
python3 "<skill-dir>/generate_veo.py" --prompt "<vivid cinematic description>" --output "<slug>.mp4"
```
Turn the user's idea into a rich prompt: subject, action, setting, camera move, lighting, mood.

Options:
- `--model`  (default `veo-3.1-fast-generate-001`)
- `--duration` 4 | 6 | 8   (seconds — longer costs more)
- `--aspect` 16:9 | 9:16   (use 9:16 for Shorts/Reels/TikTok)
- `--resolution` 720p | 1080p
- `--no-audio`  (audio is ON by default — Veo 3's signature feature)
- `--samples` N  (generate N variations)
- `--image <path>`  (**image-to-video** — animate starting FROM this image)
- `--last-frame <path>`  (**first→last interpolation** — also end ON this image; Veo 3.1)
- `--reference-image <path>` (repeatable, up to 3) + `--reference-type asset|style` — keep a
  **subject** (`asset`) or **style** consistent across the video (auto-forces 8s output)
- `--extend-video <path>` — **continue an existing clip** by +7s (auto-forces 7s; total = input + 7s)

Pick the right one for the request:
- "turn this photo into a video" / "animate this image" → `--image` (optionally `--last-frame` to morph A→B)
- "keep this character/product/style consistent" → `--reference-image` (up to 3, `--reference-type asset|style`)
- "make it longer" / "continue this video" → `--extend-video`
The tool auto-sets the duration each feature requires, so you don't have to.

The script prints and saves the operation id to `<output>.mp4.op`; if a run is interrupted, resume with
`--resume <output>.mp4.op` (no re-charge).

## Models (cheapest → best)
| id | notes |
|---|---|
| `veo-3.1-lite-generate-001` | cheapest (public preview) |
| `veo-3.1-fast-generate-001` | **default** — fast, cheap, great quality |
| `veo-3.1-generate-001` | highest quality (most expensive) |
| `veo-3.0-generate-001`, `veo-3.0-fast-generate-001` | previous generation |
| `veo-2.0-generate-001` | oldest (no audio) |

## Cost — ALWAYS mention before generating
Veo bills per second: roughly ~$0.15/sec (fast) to ~$0.40/sec (standard), audio included. An 8-second
fast clip ≈ ~$1.20. For anything long or 1080p, give the user the estimate and confirm first.

## After generating
Report the saved path, note it has audio, and offer variations (tweak the prompt, or `--samples 2`).
