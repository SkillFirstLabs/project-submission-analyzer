js_code = """
const state = {
  submissionData: null,
  questions: [],
  qIndex: 0,
  finalReport: null,
  sessionId: null,
  faceModelReady: false,
  gazeOffSince: null,
  noFaceSince: null,
  strikeCount: 0,
};

function $(selector) { return document.querySelector(selector); }
function show(id) {
  document.querySelectorAll(".step-container").forEach(el => el.classList.add("hidden"));
  $(id).classList.remove("hidden");
}
function escapeHtml(unsafe) {
  if (!unsafe) return "";
  return unsafe.toString()
       .replace(/&/g, "&amp;")
       .replace(/</g, "&lt;")
       .replace(/>/g, "&gt;")
       .replace(/"/g, "&quot;")
       .replace(/'/g, "&#039;");
}

// -------------------------------------------------------------
// Initialize Face-API
// -------------------------------------------------------------
async function loadFaceModel() {
  try {
    const MODEL_URL = "https://justadudewhohacks.github.io/face-api.js/models";
    if (typeof faceapi === "undefined") return;
    await faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL);
    state.faceModelReady = true;
  } catch (err) {
    console.error("Face-api load failed:", err);
  }
}
loadFaceModel();

// -------------------------------------------------------------
// STEP 1: Upload and Analyze
// -------------------------------------------------------------
$("input[name='zip_file']").addEventListener("change", (e) => {
  const form = $("#submit-form");
  if (e.target.files.length > 0 && form.checkValidity()) {
    $("#analyze-btn").click();
  }
});

$("#analyze-btn").addEventListener("click", async () => {
  const form = $("#submit-form");
  if (!form.checkValidity()) {
    form.reportValidity();
    return;
  }
  
  const btn = $("#analyze-btn");
  btn.disabled = true;
  const originalText = btn.innerHTML;
  btn.innerHTML = `<span class="material-symbols-outlined mr-2 animate-spin">sync</span> Analyzing...`;

  try {
    const fd = new FormData();
    fd.append("project_title", form.querySelector("[name='project_title']").value);
    fd.append("project_description", form.querySelector("[name='project_description']").value);
    fd.append("project_outcomes", form.querySelector("[name='project_outcomes']").value);
    fd.append("zip_file", form.querySelector("[name='zip_file']").files[0]);

    const res = await fetch("/analyze-submission", { method: "POST", body: fd });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || "Analysis failed.");

    state.submissionData = data;
    prepareVivaSession(data);
    show("#step-consent");
  } catch (err) {
    alert(err.message);
  } finally {
    btn.disabled = false;
    btn.innerHTML = originalText;
  }
});

function prepareVivaSession(data) {
  state.questions = [];
  data.evaluation_report.skills.forEach(sk => {
    sk.questions.forEach(q => state.questions.push({ skill_name: sk.skill_name, answer: "", ...q }));
  });
}

// -------------------------------------------------------------
// STEP 2: Consent & Verification
// -------------------------------------------------------------
const consentCheck = $("#consent-check");
const consentBtn = $("#consent-btn");

if(consentCheck) {
  consentCheck.addEventListener("change", () => {
    consentBtn.disabled = !consentCheck.checked;
    if(consentCheck.checked) {
      consentBtn.classList.remove("opacity-50", "cursor-not-allowed");
    } else {
      consentBtn.classList.add("opacity-50", "cursor-not-allowed");
    }
  });
}

if(consentBtn) {
  consentBtn.addEventListener("click", async () => {
    const overlay = $("#success-overlay");
    const modal = $("#success-modal");
    const bar = $("#loading-bar");
    
    if(overlay) {
      overlay.classList.remove("hidden");
      setTimeout(() => {
        overlay.classList.replace("opacity-0", "opacity-100");
        modal.classList.replace("scale-95", "scale-100");
        setTimeout(() => { if(bar) bar.style.width = "100%"; }, 200);
      }, 10);
    }
    
    try {
      const res = await fetch("/viva-session/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          submission_id: state.submissionData.submission_id,
          consent_acknowledged: true
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Could not start session.");
      state.sessionId = data.session_id;

      setTimeout(() => {
        show("#step-viva");
        if(overlay) {
          overlay.classList.add("hidden");
          overlay.classList.replace("opacity-100", "opacity-0");
        }
        startVivaSession();
      }, 2000);
    } catch (err) {
      alert(err.message);
      if(overlay) overlay.classList.add("hidden");
    }
  });
}

// -------------------------------------------------------------
// STEP 3: Live Viva Session (Proctoring & Questions)
// -------------------------------------------------------------
let proctorInterval = null;

async function startVivaSession() {
  state.qIndex = 0;
  state.strikeCount = 0;
  renderQuestion();
  
  if ($("#event-log-container")) $("#event-log-container").innerHTML = "";
  postEvent("interview_started", null, 1.0);
  logEvent("Session started", "info");

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
    const video = $("#camera-feed");
    if(video) {
      video.srcObject = stream;
      video.onloadedmetadata = () => {
        video.play();
        if (state.faceModelReady) {
          runFaceLoop(video);
        }
      };
    }
  } catch (err) {
    logEvent("Camera access denied", "error");
  }

  document.addEventListener("visibilitychange", () => {
    if (document.hidden && state.sessionId && !$("#step-report").classList.contains("hidden")===false) {
      postEvent("tab_switched");
      logEvent("Tab switch detected", "error");
    }
  });
}

function logEvent(msg, level) {
  const logDiv = $("#event-log-container");
  if (!logDiv) return;
  const time = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
  let color = "text-on-surface";
  if (level === "error") color = "text-rose-400";
  if (level === "success") color = "text-emerald-400";
  if (level === "warning") color = "text-amber-400";
  
  const el = document.createElement("div");
  el.className = `flex gap-3 ${color}`;
  el.innerHTML = `<span class="font-code-md text-body-sm opacity-70">${time}</span><span class="font-body-sm">${msg}</span>`;
  logDiv.appendChild(el);
  logDiv.scrollTop = logDiv.scrollHeight;
}

async function runFaceLoop(video) {
  const canvas = $("#camera-overlay");
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  const options = new faceapi.TinyFaceDetectorOptions({ inputSize: 224, scoreThreshold: 0.5 });
  let identityVerified = false;

  proctorInterval = setInterval(async () => {
    if (!video.srcObject) return;
    
    const displaySize = { width: video.videoWidth || 320, height: video.videoHeight || 240 };
    if (canvas.width !== displaySize.width) {
      canvas.width = displaySize.width;
      canvas.height = displaySize.height;
    }

    const detections = await faceapi.detectAllFaces(video, options);
    const resized = faceapi.resizeResults(detections, displaySize);
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    if (!identityVerified && resized.length === 1) {
      identityVerified = true;
      postEvent("id_verified", null, 0.95);
      logEvent("Identity verified", "success");
    }

    if (resized.length === 0) {
      if (!state.noFaceSince) state.noFaceSince = Date.now();
      const elapsed = Date.now() - state.noFaceSince;
      if (elapsed > 2000 && elapsed % 2000 < 350) {
        postEvent("face_not_detected", elapsed);
        logEvent("Face not detected", "warning");
      }
    } else {
      state.noFaceSince = null;
    }

    if (resized.length > 1) {
      postEvent("multiple_faces_detected", null, 0.9);
      logEvent("Multiple faces detected", "error");
    }

    if (resized.length === 1) {
      const box = resized[0].box;
      ctx.strokeStyle = "#f5b700";
      ctx.lineWidth = 3;
      ctx.strokeRect(box.x, box.y, box.width, box.height);

      const centerX = box.x + box.width / 2;
      const frameCenter = canvas.width / 2;
      const offCenter = Math.abs(centerX - frameCenter) > canvas.width * 0.15;
      
      if (offCenter) {
        if (!state.gazeOffSince) state.gazeOffSince = Date.now();
        const elapsed = Date.now() - state.gazeOffSince;
        if (elapsed > 1500 && elapsed % 1500 < 350) {
          postEvent("gaze_off_screen", elapsed, 0.7);
          logEvent("Gaze off-screen", "warning");
        }
      } else {
        state.gazeOffSince = null;
      }
    }
  }, 700);
}

async function postEvent(eventType, durationMs, confidence) {
  if (!state.sessionId) return;
  try {
    const res = await fetch("/viva-session/event", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: state.sessionId,
        event_type: eventType,
        timestamp: new Date().toISOString(),
        duration_ms: Math.floor(durationMs || 0),
        confidence: confidence || null
      })
    });
    const data = await res.json();
    if (data.severity) {
      state.strikeCount++;
    }
  } catch (err) {}
}

function renderQuestion() {
  const q = state.questions[state.qIndex];
  if (!q) return;
  
  if ($("#q-counter-display")) {
    $("#q-counter-display").textContent = `QUESTION ${(state.qIndex + 1).toString().padStart(2, '0')}`;
  }
  if ($("#question-text")) {
    $("#question-text").innerHTML = escapeHtml(q.question);
  }
  
  const refBlock = $("#code-ref-block");
  if (refBlock) {
    if (q.references && q.references.length > 0) {
      refBlock.classList.remove("hidden");
      $("#code-ref-filename").textContent = q.references.join(", ");
      $("#code-ref-content").textContent = `// Context cited from: ${q.references.join(", ")}`;
    } else {
      refBlock.classList.add("hidden");
    }
  }

  const answerInput = $("#answer-input");
  if (answerInput) {
    answerInput.value = q.answer || "";
  }
}

function saveAnswer() {
  const answerInput = $("#answer-input");
  if (answerInput && state.questions[state.qIndex]) {
    state.questions[state.qIndex].answer = answerInput.value;
  }
}

if ($("#prev-q-btn")) {
  $("#prev-q-btn").addEventListener("click", () => {
    if (state.qIndex > 0) { saveAnswer(); state.qIndex--; renderQuestion(); }
  });
}
if ($("#next-q-btn")) {
  $("#next-q-btn").addEventListener("click", () => {
    if (state.qIndex < state.questions.length - 1) { saveAnswer(); state.qIndex++; renderQuestion(); }
  });
}
if ($("#skip-q-btn")) {
  $("#skip-q-btn").addEventListener("click", () => {
    if (state.qIndex < state.questions.length - 1) { state.qIndex++; renderQuestion(); }
  });
}

// -------------------------------------------------------------
// STEP 4: End Session -> Report
// -------------------------------------------------------------
if ($("#end-viva-btn")) {
  $("#end-viva-btn").addEventListener("click", async () => {
    if (!confirm("End the viva session and generate the final report?")) return;
    saveAnswer();
    
    try {
      const video = $("#camera-feed");
      if (video && video.srcObject) video.srcObject.getTracks().forEach(t => t.stop());
      if (proctorInterval) clearInterval(proctorInterval);

      const res = await fetch("/viva-session/end?session_id=" + encodeURIComponent(state.sessionId), {
        method: "POST"
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Could not end session.");

      state.finalReport = data;
      renderReport(state.finalReport);
      show("#step-report");
    } catch (err) {
      alert(err.message);
    }
  });
}

function renderReport(data) {
  const sub = state.submissionData;
  if ($("#report-title")) $("#report-title").textContent = sub.project_title;
  if ($("#report-alignment-score")) $("#report-alignment-score").textContent = `${Math.round(data.evaluation_report.summary.alignment_score * 100)}%`;
  if ($("#report-narrative")) $("#report-narrative").textContent = data.evaluation_report.summary.narrative;
  if ($("#report-integrity-score")) $("#report-integrity-score").textContent = data.proctoring_report.integrity_score.toFixed(2);
  if ($("#report-risk-level")) {
    const rl = data.proctoring_report.risk_level;
    $("#report-risk-level").textContent = rl.toUpperCase() + " RISK";
    if (rl === "high") $("#report-risk-level").className = "px-3 py-1 bg-rose-100 text-rose-700 font-bold rounded-lg text-sm";
    else if (rl === "medium") $("#report-risk-level").className = "px-3 py-1 bg-amber-100 text-amber-700 font-bold rounded-lg text-sm";
    else $("#report-risk-level").className = "px-3 py-1 bg-emerald-100 text-emerald-700 font-bold rounded-lg text-sm";
  }

  // Skills
  const skillsContainer = $("#report-skills-container");
  if (skillsContainer) {
    skillsContainer.innerHTML = data.suggested_skills.map(sk => `
      <div class="bg-surface-container-lowest p-container-padding rounded-xl shadow-sm border border-outline-variant hover:shadow-md transition-shadow group">
          <div class="flex justify-between items-start mb-4">
              <div>
                  <h3 class="font-headline-sm text-headline-sm">${escapeHtml(sk.skill_name)}</h3>
              </div>
              <span class="text-headline-sm text-primary">${Math.round(sk.confidence * 100)}%</span>
          </div>
          <div class="w-full bg-surface-container-high h-2 rounded-full mb-6 overflow-hidden">
              <div class="bg-primary h-full transition-all duration-1000" style="width: ${sk.confidence * 100}%"></div>
          </div>
          <div class="bg-surface-container-low p-4 rounded-lg">
              <span class="font-label-md text-label-md text-primary block mb-1">Rationale</span>
              <p class="text-on-surface-variant font-body-md italic leading-relaxed">
                  "${escapeHtml(sk.rationale)}"
              </p>
          </div>
      </div>
    `).join("");
  }

  // Outcomes
  const outcomesContainer = $("#report-outcomes-container");
  if (outcomesContainer) {
    outcomesContainer.innerHTML = data.evaluation_report.summary.outcome_evaluation.map(o => {
      let statusColor = "emerald";
      if (o.status === "partial") statusColor = "amber";
      if (o.status === "not_met" || o.status === "not_verifiable") statusColor = "rose";
      
      return `
      <div class="bg-surface-container-lowest p-6 rounded-xl shadow-sm status-border-${statusColor} flex flex-col justify-between">
          <div>
              <div class="flex items-center gap-2 mb-2">
                  <span class="bg-${statusColor}-100 text-${statusColor}-700 font-label-md text-label-md px-2 py-0.5 rounded-full capitalize">${escapeHtml(o.status)}</span>
                  <span class="text-on-surface-variant font-label-md truncate block">${escapeHtml(o.outcome)}</span>
              </div>
              <p class="text-on-surface-variant font-body-sm mb-4 line-clamp-3">${escapeHtml(o.evidence)}</p>
          </div>
          ${o.gap ? `
          <div class="bg-inverse-surface text-surface-variant p-3 rounded-lg font-code-md text-code-md mt-4">
              <span class="text-primary-fixed-dim text-xs block mb-1">Identified Gap</span>
              ${escapeHtml(o.gap)}
          </div>
          ` : ""}
      </div>
      `;
    }).join("");
  }

  // Flags Log
  const logContainer = $("#report-event-log");
  if (logContainer) {
    logContainer.innerHTML = data.proctoring_report.flags.map(f => {
      const time = new Date(f.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
      let color = "";
      if (f.severity === "high") color = "text-rose-400";
      else if (f.severity === "medium") color = "text-amber-400";
      return `
      <div class="flex gap-3 ${color}">
          <span class="opacity-40">${time}</span>
          <span>${escapeHtml(f.type)} (${f.duration_ms ? f.duration_ms + 'ms' : '-'})</span>
      </div>
      `;
    }).join("");
    if (data.proctoring_report.flags.length === 0) {
      logContainer.innerHTML = `<div class="flex gap-3 text-emerald-400"><span>No integrity flags recorded.</span></div>`;
    }
  }
}
"""
with open("static/app.js", "w", encoding="utf-8") as f:
    f.write(js_code)
print("app.js updated.")
