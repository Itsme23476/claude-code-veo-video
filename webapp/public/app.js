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
  const c = (RATE[$("#model").value] || 0.15) * Number(dur());
  $("#cost").textContent = "~$" + c.toFixed(2);
}
$("#model").addEventListener("change", cost);
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
