const $ = (s) => document.querySelector(s);

function group(id) {
  const g = document.getElementById(id);
  g.addEventListener("click", (e) => {
    if (e.target.tagName !== "BUTTON") return;
    [...g.children].forEach((b) => b.classList.remove("on"));
    e.target.classList.add("on");
    cost();
  });
  return () => g.querySelector(".on").dataset.v;
}
const dur = group("duration"), asp = group("aspect"), res = group("resolution");

// rough $/sec by model (audio included) — for the on-screen estimate only
const RATE = {
  "veo-3.1-fast-generate-001": 0.15, "veo-3.1-generate-001": 0.40,
  "veo-3.1-lite-generate-001": 0.10, "veo-3.0-fast-generate-001": 0.15,
  "veo-3.0-generate-001": 0.40,
};
function cost() {
  const eff = extData ? 7 : (refData.some(Boolean) ? 8 : Number(dur()));
  const c = (RATE[$("#model").value] || 0.15) * eff;
  $("#cost").textContent = "~$" + c.toFixed(2);
}
$("#model").addEventListener("change", cost);

// --- optional inputs: start/end frames, reference images, video extension ---
let startData = null, endData = null, extData = null;
const refData = [null, null, null];

function upslot(slotId, inputId, thumbId, xId, label, set) {
  const slot = document.getElementById(slotId), inp = document.getElementById(inputId),
        thumb = document.getElementById(thumbId), x = document.getElementById(xId);
  slot.addEventListener("click", (e) => {
    if (e.target === x) {
      set(null); inp.value = ""; thumb.style.backgroundImage = "";
      thumb.classList.remove("set"); thumb.textContent = label; x.hidden = true; cost();
      return;
    }
    inp.click();
  });
  inp.addEventListener("change", () => {
    const f = inp.files[0]; if (!f) return;
    const r = new FileReader();
    r.onload = () => {
      set(r.result);
      if (f.type.startsWith("video/")) {
        thumb.textContent = "✓ " + f.name.slice(0, 22);
        thumb.classList.remove("set"); thumb.style.backgroundImage = "";
      } else {
        thumb.style.backgroundImage = `url(${r.result})`;
        thumb.classList.add("set"); thumb.textContent = "";
      }
      x.hidden = false; cost();
    };
    r.readAsDataURL(f);
  });
}
upslot("startSlot", "startImg", "startThumb", "startX", "+ Start", (d) => (startData = d));
upslot("endSlot", "endImg", "endThumb", "endX", "+ End", (d) => (endData = d));
upslot("ref0Slot", "ref0Img", "ref0Thumb", "ref0X", "+ Ref", (d) => (refData[0] = d));
upslot("ref1Slot", "ref1Img", "ref1Thumb", "ref1X", "+ Ref", (d) => (refData[1] = d));
upslot("ref2Slot", "ref2Img", "ref2Thumb", "ref2X", "+ Ref", (d) => (refData[2] = d));
upslot("extSlot", "extVid", "extThumb", "extX", "+ Video to continue", (d) => (extData = d));
const refType = group("refType");
cost();

const esc = (s) => s.replace(/[&<>"]/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

$("#go").addEventListener("click", generate);

async function generate() {
  const prompt = $("#prompt").value.trim();
  if (!prompt) { $("#prompt").focus(); return; }
  const body = {
    prompt, model: $("#model").value, duration: Number(dur()),
    aspect: asp(), resolution: res(), audio: $("#audio").checked,
  };
  if (startData) body.startImage = startData;
  if (endData) body.endImage = endData;
  const refs = refData.filter(Boolean);
  if (refs.length) { body.referenceImages = refs; body.referenceType = refType(); }
  if (extData) body.extendVideo = extData;
  const neg = $("#negPrompt").value.trim(); if (neg) body.negativePrompt = neg;
  const sd = $("#seed").value.trim(); if (sd) body.seed = Number(sd);
  const pg = $("#personGen").value; if (pg) body.personGeneration = pg;
  $("#go").disabled = true;
  $("#glabel").textContent = "Generating…";
  $("#empty")?.remove();

  const card = document.createElement("div");
  card.className = "card";
  card.innerHTML = `<div class="media"><div class="spinner"></div></div><div class="cap">${esc(prompt)}</div>`;
  $("#gallery").prepend(card);

  try {
    const r = await fetch("/api/generate", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const j = await r.json();
    if (j.error) throw new Error(j.error);
    poll(j.jobId, card);
  } catch (e) {
    card.querySelector(".media").innerHTML = `<div class="err">⚠ ${esc(e.message)}</div>`;
    reset();
  }
}

function poll(id, card) {
  const iv = setInterval(async () => {
    let s;
    try { s = await (await fetch("/api/status?job=" + id)).json(); } catch { return; }
    if (s.status === "done") {
      clearInterval(iv);
      card.querySelector(".media").innerHTML =
        `<video src="${s.videoUrl}" controls autoplay muted loop></video>`;
      reset();
    } else if (s.status === "error") {
      clearInterval(iv);
      card.querySelector(".media").innerHTML = `<div class="err">⚠ ${esc(s.error || "failed")}</div>`;
      reset();
    }
  }, 4000);
}

function reset() {
  $("#go").disabled = false;
  $("#glabel").textContent = "Generate";
  cost();
}
