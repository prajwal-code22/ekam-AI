(() => {
  const KATHMANDU = { lat: 27.7172, lng: 85.324, approx: true };
  const MAX_SECONDS = 30;

  const $ = (id) => document.getElementById(id);
  const mic = $("mic");
  const statusEl = $("status");
  const errorEl = $("error");
  const resultEl = $("result");
  const csrf = document.querySelector('meta[name="csrf-token"]').content;

  let recorder = null;
  let chunks = [];
  let stopTimer = null;
  let locationPromise = null;

  const setStatus = (msg) => { statusEl.textContent = msg; };
  const showError = (msg) => { errorEl.textContent = msg; errorEl.hidden = !msg; };

  function getLocation() {
    return new Promise((resolve) => {
      if (!navigator.geolocation) return resolve(KATHMANDU);
      navigator.geolocation.getCurrentPosition(
        (p) => resolve({ lat: p.coords.latitude, lng: p.coords.longitude, approx: false }),
        () => resolve(KATHMANDU),
        { enableHighAccuracy: true, timeout: 8000, maximumAge: 60000 }
      );
    });
  }

  function pickMimeType() {
    const options = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/ogg"];
    return options.find((t) => window.MediaRecorder && MediaRecorder.isTypeSupported(t)) || "";
  }

  async function startRecording() {
    showError("");
    if (!navigator.mediaDevices || !window.MediaRecorder) {
      showError("This browser cannot record audio. Use the 'Type instead' option.");
      return;
    }
    // Ask for location at the same time so both permission prompts appear up front.
    locationPromise = getLocation();
    let stream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      showError("Microphone access was blocked. Allow it in your browser, or type your request.");
      return;
    }
    chunks = [];
    const mimeType = pickMimeType();
    recorder = new MediaRecorder(stream, mimeType ? { mimeType } : undefined);
    recorder.ondataavailable = (e) => { if (e.data.size) chunks.push(e.data); };
    recorder.onstop = () => {
      stream.getTracks().forEach((t) => t.stop());
      const blob = new Blob(chunks, { type: recorder.mimeType || "audio/webm" });
      submit({ audio: blob });
    };
    recorder.start();
    mic.setAttribute("aria-pressed", "true");
    mic.setAttribute("aria-label", "Stop recording");
    setStatus("Listening. Tap again when you are done.");
    stopTimer = setTimeout(stopRecording, MAX_SECONDS * 1000);
  }

  function stopRecording() {
    clearTimeout(stopTimer);
    if (recorder && recorder.state === "recording") recorder.stop();
    mic.setAttribute("aria-pressed", "false");
    mic.setAttribute("aria-label", "Start recording");
  }

  async function submit({ audio, text }) {
    mic.disabled = true;
    setStatus("Understanding your request...");
    showError("");
    try {
      const loc = await (locationPromise || getLocation());
      const form = new FormData();
      if (audio) form.append("audio", audio, "request.webm");
      if (text) form.append("text", text);
      form.append("lat", loc.lat);
      form.append("lng", loc.lng);
      form.append("approx", loc.approx ? "1" : "0");

      const res = await fetch("/api/jobs/voice/", {
        method: "POST",
        headers: { "X-CSRFToken": csrf },
        body: form,
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok) throw new Error(data.error || "Something went wrong. Please try again.");
      render(data);
      setStatus(loc.approx ? "Done. Location unavailable, so we used central Kathmandu." : "Done.");
    } catch (err) {
      setStatus("Ready");
      showError(err.message);
    } finally {
      mic.disabled = false;
      locationPromise = null;
    }
  }

  function el(tag, props = {}, ...children) {
    const node = document.createElement(tag);
    Object.assign(node, props);
    children.forEach((c) => node.append(c));
    return node;
  }

  const URGENCY = { now: "Right now", today: "Today", scheduled: "Later" };

  function field(label, value, className) {
    const dd = el("dd", { textContent: value, className: className || "" });
    if (className === "ne") dd.lang = "ne";
    return el("div", {}, el("dt", { textContent: label }), dd);
  }

  // All model output is inserted with textContent, never innerHTML.
  function render({ job, workers }) {
    const fields = $("job-fields");
    fields.replaceChildren(
      field("What you said", job.transcript),
      field("Job (Nepali)", job.description_ne, "ne"),
      field("Job (English)", job.description_en),
      field("Worker type", job.trade),
      field("When", URGENCY[job.urgency] || job.urgency),
      field("Fair price", `NPR ${job.price_min_npr.toLocaleString()} to ${job.price_max_npr.toLocaleString()}`)
    );

    const followUp = $("follow-up");
    followUp.hidden = !job.follow_up_question;
    followUp.textContent = job.follow_up_question || "";

    const list = $("workers");
    list.replaceChildren();
    if (!workers.length) {
      list.append(el("li", { textContent: "No workers available right now." }));
    }
    workers.forEach((w) => {
      list.append(
        el("li", {},
          el("span", { className: "w-name", textContent: w.name }),
          el("a", { className: "w-call", href: `tel:${w.phone}`, textContent: "Call" }),
          el("span", { className: "w-meta", textContent: `${w.trade}, ${w.area} · ${w.distance_km} km away · rated ${w.rating}` })
        )
      );
    });

    resultEl.hidden = false;
    resultEl.scrollIntoView({ behavior: "smooth", block: "start" });
  }

  mic.addEventListener("click", () => {
    if (recorder && recorder.state === "recording") stopRecording();
    else startRecording();
  });

  $("text-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const text = $("text-input").value.trim();
    if (!text) return showError("Write what you need first.");
    locationPromise = getLocation();
    submit({ text });
  });
})();
