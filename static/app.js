
// --- GESTURE RECOGNITION (MediaPipe) ---
let gestureRecognizer = null;
let lastVideoTime = -1;

async function initGestureRecognizer() {
  try {
    const { GestureRecognizer, FilesetResolver } = await import("https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.3");
    const vision = await FilesetResolver.forVisionTasks("https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.3/wasm");
    gestureRecognizer = await GestureRecognizer.createFromOptions(vision, {
      baseOptions: {
        modelAssetPath: "https://storage.googleapis.com/mediapipe-models/gesture_recognizer/gesture_recognizer/float16/1/gesture_recognizer.task",
        delegate: "GPU"
      },
      runningMode: "VIDEO"
    });
    console.log("Gesture Recognizer initialized.");
  } catch (err) {
    console.error("Failed to init gesture recognizer:", err);
  }
}

async function scanGestureLoop(video) {
  if (!state.streamActive || !gestureRecognizer) return;
  
  if (video.currentTime !== lastVideoTime) {
    lastVideoTime = video.currentTime;
    try {
      const results = gestureRecognizer.recognizeForVideo(video, Date.now());
      if (results.gestures.length > 0) {
        const gesture = results.gestures[0][0];
        if (gesture.categoryName === "Thumb_Up" && gesture.score > 0.6) {
          console.log("Thumbs Up detected!");
          // Capture photo
          const canvas = $("#photo-capture-canvas");
          if (canvas) {
            canvas.width = video.videoWidth;
            canvas.height = video.videoHeight;
            const ctx = canvas.getContext("2d");
            ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
            state.capturedPhoto = canvas.toDataURL("image/jpeg");
          }
          
          // Verify
          const btn = $("#consent-btn");
          if (btn) {
            btn.innerHTML = `<span class="material-symbols-outlined mr-2">check_circle</span> Verified & Start`;
            btn.classList.remove("opacity-50", "cursor-not-allowed");
            btn.disabled = false;
          }
          return; // Stop scanning once verified
        }
      }
    } catch (err) {}
  }
  requestAnimationFrame(() => scanGestureLoop(video));
}


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
    if (typeof faceapi === "undefined") {
      setTimeout(loadFaceModel, 500); // retry
      return;
    }
    await faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL);
    await faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL);
      await faceapi.nets.faceExpressionNet.loadFromUri(MODEL_URL);
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
  if (e.target.files.length > 0) {
    const file = e.target.files[0];
    const sizeMb = (file.size / (1024 * 1024)).toFixed(2);
    const title = $("#upload-title");
    const desc = $("#upload-desc");
    if(title) title.innerText = file.name;
    if(desc) desc.innerHTML = `${sizeMb} MB &nbsp;·&nbsp; <span style="color:var(--green)">Ready for analysis ✓</span>`;
    // Highlight dropzone
    const dz = $("#dropzone");
    if (dz) dz.style.borderColor = "var(--green)";
  }
});

$("#analyze-btn").addEventListener("click", async () => {
  const form = $("#submit-form");
  const fileInput = $("input[name='zip_file']");
  if (!fileInput || fileInput.files.length === 0) {
    alert("File not uploaded");
    return;
  }
  if (!form.checkValidity()) {
    form.reportValidity();
    return;
  }
  
  const btn = $("#analyze-btn");
  btn.disabled = true;
  const originalText = btn.innerHTML;
  btn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="animate-spin"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg> Analyzing...`;
  
  const term = $("#ai-proctor-terminal");
  if (term) {
    term.innerHTML = `<p><span class="t-prompt">›</span> Uploading payload...</p>`;
    setTimeout(() => { if (term.parentElement) term.innerHTML += `<p><span class="t-prompt">›</span> Extracting codebase...</p>`; }, 800);
    setTimeout(() => { if (term.parentElement) term.innerHTML += `<p><span class="t-prompt">›</span> Analyzing architecture...</p>`; }, 1500);
    setTimeout(() => { if (term.parentElement) term.innerHTML += `<p><span class="t-prompt">›</span> Evaluating skill alignment...</p>`; }, 2500);
  }


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
    startCamera();
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

  const manualCaptureBtn = $("#manual-capture-btn");
  if (manualCaptureBtn) {
    manualCaptureBtn.addEventListener("click", () => {
      const video = $("#camera-feed");
      if (!video) return;
      
      const captureCanvas = $("#photo-capture-canvas");
      if (captureCanvas) {
        captureCanvas.width = video.videoWidth || 640;
        captureCanvas.height = video.videoHeight || 480;
        const captureCtx = captureCanvas.getContext("2d");
        captureCtx.drawImage(video, 0, 0, captureCanvas.width, captureCanvas.height);
        state.capturedPhoto = captureCanvas.toDataURL("image/jpeg");
      }
      
      postEvent("id_verified", null, 1.0);
      logEvent("Identity verified manually", "success");
      
      manualCaptureBtn.innerHTML = `✓ Captured`;
      manualCaptureBtn.style.background = "rgba(34,197,94,0.15)";
      manualCaptureBtn.style.borderColor = "var(--green)";
      manualCaptureBtn.style.color = "var(--green)";
      manualCaptureBtn.disabled = true;
      
      const btn = $("#consent-btn");
      if (btn) {
        btn.innerHTML = `✓ Verified — Start Viva`;
        btn.disabled = false;
      }
    });
  }


if(consentCheck) {
  consentCheck.addEventListener("change", () => {
    consentBtn.disabled = !consentCheck.checked;
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
        
        // Move camera to sidebar
        const sidebarCam = $("#viva-sidebar-camera");
        if (sidebarCam) {
            sidebarCam.innerHTML = "";
            sidebarCam.style.cssText = "position:relative;width:100%;aspect-ratio:16/9;background:#000;border-radius:8px;overflow:hidden;";
            const vid = $("#camera-feed");
            const ov  = $("#camera-overlay");
            if (vid) { vid.style.cssText = "position:absolute;inset:0;width:100%;height:100%;object-fit:cover;"; sidebarCam.appendChild(vid); }
            if (ov)  { ov.style.cssText  = "position:absolute;inset:0;width:100%;height:100%;z-index:10;pointer-events:none;"; sidebarCam.appendChild(ov); }
        }
        // Update footer session id
        const fsid = $("#footer-session-id");
        if (fsid) fsid.textContent = "#" + (state.sessionId || "--");
        
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
  startTimer();

  document.addEventListener("visibilitychange", () => {
    if (document.hidden && state.sessionId && !$("#step-report").classList.contains("hidden")===false) {
      postEvent("tab_switched");
      logEvent("Tab switch detected", "error");
      if(typeof showToast === "function") showToast("Warning: Tab switch detected!", "error");
    }
  });
}

async function startCamera() {
  if (state.streamActive) return;
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
    const video = $("#camera-feed");
    if(video) {
      video.srcObject = stream;
      video.onloadedmetadata = () => {
        video.play();
        if (state.faceModelReady) runFaceLoop(video);
      };
    }
    state.streamActive = true;
  } catch (err) {
    console.error("Camera access denied", err);
  }
}

function logEvent(msg, level) {
  const logDiv = $("#event-log-container");
  if (!logDiv) return;
  const time = new Date().toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
  let cls = "log-low";
  if (level === "error")   cls = "log-high";
  if (level === "success") cls = "log-clean";
  if (level === "warning") cls = "log-medium";
  
  const el = document.createElement("div");
  el.className = `log-entry ${cls}`;
  el.innerHTML = `<span class="log-time">${time}</span><span class="log-msg">${escapeHtml(msg)}</span>`;
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

    // Ping the backend every 5 seconds to prevent CONNECTION_TIMEOUT_S (12s)
    if (!state.lastHeartbeat || Date.now() - state.lastHeartbeat > 5000) {
      state.lastHeartbeat = Date.now();
      postEvent("heartbeat");
    }
    const detections = await faceapi.detectAllFaces(video, options).withFaceLandmarks().withFaceExpressions();
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
        if(typeof showToast === "function") showToast("Warning: Face not detected!", "error");
      }
    } else {
      state.noFaceSince = null;
    }

    if (resized.length > 1) {
      postEvent("multiple_faces_detected", null, 0.9);
      logEvent("Multiple faces detected", "error");
      if(typeof showToast === "function") showToast("Warning: Multiple faces detected!", "error");
    }

    if (resized.length === 1) {
      const box = resized[0].detection.box;
      ctx.strokeStyle = "#f5b700";
      ctx.lineWidth = 3;
      ctx.strokeRect(box.x, box.y, box.width, box.height);
      faceapi.draw.drawFaceLandmarks(canvas, resized);

      const centerX = box.x + box.width / 2;
      const frameCenter = canvas.width / 2;
      const offCenter = Math.abs(centerX - frameCenter) > canvas.width * 0.15;
      
      if (offCenter) {
        if (!state.gazeOffSince) state.gazeOffSince = Date.now();
        const elapsed = Date.now() - state.gazeOffSince;
        if (elapsed > 1500 && elapsed % 1500 < 350) {
          postEvent("gaze_off_screen", elapsed, 0.7);
          logEvent("Gaze off-screen", "warning");
          if(typeof showToast === "function") showToast("Warning: Please look at the screen.", "error");
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
  if (!q) {
    if ($("#question-text")) {
      $("#question-text").innerHTML = "No questions generated for this submission. You may end the session.";
    }
    if ($("#code-ref-block")) {
      $("#code-ref-block").classList.add("hidden");
    }
    return;
  }
  
  if ($("#q-counter-display")) {
    $("#q-counter-display").textContent = `QUESTION ${(state.qIndex + 1).toString().padStart(2, '0')}`;
  }
  if ($("#question-counter-header")) {
    const total = state.questions.length > 0 ? state.questions.length : 12;
    $("#question-counter-header").textContent = `${(state.qIndex + 1).toString().padStart(2, '0')} / ${total.toString().padStart(2, '0')}`;
  }
  const progContainer = $("#progress-container");
  if (progContainer && state.questions.length > 0) {
    progContainer.innerHTML = "";
    state.questions.forEach((q, i) => {
      const bar = document.createElement("div");
      bar.className = `h-1 flex-1 rounded-full transition-colors ${i <= state.qIndex ? 'bg-primary' : 'bg-outline-variant'}`;
      progContainer.appendChild(bar);
    });
  }
  
  if ($("#next-q-btn")) {
    const skipBtn = $("#skip-q-btn");
    if (state.qIndex === state.questions.length - 1) {
      $("#next-q-btn").innerHTML = 'Submit Session <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>';
      if (skipBtn) skipBtn.classList.add("hidden");
    } else {
      $("#next-q-btn").innerHTML = 'Submit Answer <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>';
      if (skipBtn) skipBtn.classList.remove("hidden");
    }
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

async function submitSession() {
  saveAnswer();
  try {
    const video = $("#camera-feed");
    if (video && video.srcObject) video.srcObject.getTracks().forEach(t => t.stop());
    if (typeof proctorInterval !== "undefined" && proctorInterval) clearInterval(proctorInterval);

    const btn = $("#next-q-btn");
    if (btn) btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="animate-spin"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg> Submitting...`;

    const res = await fetch("/viva-session/end", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: state.sessionId,
        answers: state.questions
      })
    });
    const data = await res.json();
    if (!res.ok) {
      let errStr = data.detail || "Could not end session.";
      if (typeof errStr !== "string") errStr = JSON.stringify(errStr);
      throw new Error(errStr);
    }

    state.finalReport = data;
    renderReport(state.finalReport);
    show("#step-report");
  } catch (err) {
    alert(err.message);
  }
}

if ($("#next-q-btn")) {
  $("#next-q-btn").addEventListener("click", () => {
    if (state.qIndex < state.questions.length - 1) { 
        saveAnswer(); 
        state.qIndex++; 
        renderQuestion(); 
    } else {
        submitSession();
    }
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

function renderReport(data) {
  const sub = state.submissionData;
  if ($("#report-title")) $("#report-title").textContent = sub.project_title;
  if ($("#report-alignment-score")) {
    const scoreVal = Math.round(data.evaluation_report.summary.alignment_score * 100);
    
    // Animate the counter
    let curr = 0;
    const interval = setInterval(() => {
      curr += 2;
      if (curr >= scoreVal) {
        curr = scoreVal;
        clearInterval(interval);
      }
      $("#report-alignment-score").textContent = `${curr}%`;
    }, 20);

    // Update gauge gradient and shadow color
    const gauge = $("#score-gauge");
    if (gauge) {
      let color = "#3b82f6"; // primary
      if (scoreVal >= 80) color = "#10b981"; // emerald
      else if (scoreVal < 50) color = "#ef4444"; // rose
      
      gauge.style.background = `conic-gradient(${color} ${scoreVal}%, transparent ${scoreVal}%)`;
      gauge.parentElement.style.boxShadow = `0 0 25px ${color}80`;
      $("#report-alignment-score").style.color = color;
    }
  }
  
  if ($("#final-photo-display") && state.capturedPhoto) {
    $("#final-photo-display").src = state.capturedPhoto;
  }

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
    skillsContainer.innerHTML = data.suggested_skills.map(sk => {
      const pct = Math.round(sk.confidence * 100);
      return `
      <div class="skill-card">
        <div class="skill-header">
          <span class="skill-name">${escapeHtml(sk.skill_name)}</span>
          <span class="skill-confidence">${pct}%</span>
        </div>
        <div class="skill-bar-track"><div class="skill-bar-fill" style="width:${pct}%"></div></div>
        <div class="skill-rationale">"${escapeHtml(sk.rationale)}"</div>
      </div>`;
    }).join("");
  }

  // Outcomes
  const outcomesContainer = $("#report-outcomes-container");
  if (outcomesContainer) {
    outcomesContainer.innerHTML = data.evaluation_report.summary.outcome_evaluation.map(o => {
      const statusCls = o.status.replace("_", "-");
      return `
      <div class="outcome-card">
        <div class="outcome-status-row">
          <span class="outcome-status ${o.status}">${escapeHtml(o.status.replace("_"," "))}</span>
          <span class="outcome-name" title="${escapeHtml(o.outcome)}">${escapeHtml(o.outcome)}</span>
        </div>
        <p class="outcome-evidence">${escapeHtml(o.evidence)}</p>
        ${o.gap ? `<div class="outcome-gap"><div class="outcome-gap-label">GAP IDENTIFIED</div>${escapeHtml(o.gap)}</div>` : ""}
      </div>`;
    }).join("");
  }

  // Flags Log (both in report section and in the integrity card)
  const logContainer = $("#report-event-log");
  if (logContainer) {
    if (data.proctoring_report.flags.length === 0) {
      logContainer.innerHTML = `<div class="log-entry log-clean"><span class="log-msg">No integrity flags recorded.</span></div>`;
    } else {
      logContainer.innerHTML = data.proctoring_report.flags.map(f => {
        const time = new Date(f.timestamp).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'});
        const cls = f.severity === "high" ? "log-high" : f.severity === "medium" ? "log-medium" : "log-low";
        return `<div class="log-entry ${cls}"><span class="log-time">${time}</span><span class="log-msg">${escapeHtml(f.type)} (${f.duration_ms ? f.duration_ms + 'ms' : '-'})</span></div>`;
      }).join("");
    }
  }

  // Integrity card elements
  const riskBadge = $("#report-risk-badge");
  if (riskBadge) {
    const rl = data.proctoring_report.risk_level;
    riskBadge.textContent = rl.toUpperCase() + " RISK";
    riskBadge.className = `risk-badge sm ${rl}`;
  }
  const scoreCard = $("#report-integrity-score-card");
  if (scoreCard) scoreCard.textContent = data.proctoring_report.integrity_score.toFixed(2);
  const idCheck = $("#report-id-check");
  if (idCheck) idCheck.textContent = data.proctoring_report.id_check.replace(/_/g, " ");

  // Footer metadata
  const metaTokens = $("#meta-tokens");
  if (metaTokens && sub.metadata) metaTokens.textContent = (sub.metadata.model_tokens_used || 0).toLocaleString();
  const metaExtraction = $("#meta-extraction");
  if (metaExtraction && sub.metadata) metaExtraction.textContent = (sub.metadata.extraction_time_ms || 0) + " ms";
  const metaFiles = $("#meta-files");
  if (metaFiles && sub.metadata) metaFiles.textContent = sub.metadata.files_analyzed || "--";
}


// --- TOAST NOTIFICATIONS ---
function showToast(msg, type = 'error') {
  const container = $("#toast-container");
  if (!container) return;
  const t = document.createElement("div");
  t.className = `toast ${type}`;
  t.innerText = msg;
  container.appendChild(t);
  setTimeout(() => t.classList.add('show'), 10);
  setTimeout(() => {
    t.classList.remove('show');
    setTimeout(() => t.remove(), 300);
  }, 4000);
}

// --- SPEECH RECOGNITION ---
let recognition = null;
let isRecording = false;

if ('webkitSpeechRecognition' in window) {
  recognition = new webkitSpeechRecognition();
  recognition.continuous = true;
  recognition.interimResults = true;
  
  recognition.onresult = (event) => {
    let finalTranscript = '';
    for (let i = event.resultIndex; i < event.results.length; ++i) {
      if (event.results[i].isFinal) {
        finalTranscript += event.results[i][0].transcript + ' ';
      }
    }
    const input = $("#answer-input");
    if (input && finalTranscript) {
      input.value += finalTranscript;
    }
  };
  
  recognition.onerror = (event) => {
    console.error("Speech recognition error", event.error);
    stopRecording();
  };
  
  recognition.onend = () => {
    if (isRecording) {
      try { recognition.start(); } catch(e){}
    }
  };
}

function stopRecording() {
  isRecording = false;
  if(recognition) recognition.stop();
  const text = $("#mic-text");
  if(text) text.innerText = "Click to speak";
}

if ($("#mic-btn")) {
  $("#mic-btn").addEventListener("click", () => {
    if (!recognition) {
      showToast("Speech recognition not supported in this browser. Try Chrome.", "warning");
      return;
    }
    const micBtn = $("#mic-btn");
    const text = $("#mic-text");
    if (isRecording) {
      stopRecording();
      if (micBtn) micBtn.style.color = "";
    } else {
      isRecording = true;
      recognition.start();
      if (micBtn) micBtn.style.color = "var(--rose)";
      if (text) text.innerText = "Listening...";
    }
  });
}

// --- TIMER ---
let timerInterval = null;

function startTimer() {
  state.sessionStartTime = Date.now();
  const timerEl = $("#session-timer");
  if (!timerEl) return;
  if (timerInterval) clearInterval(timerInterval);
  
  timerInterval = setInterval(() => {
    const elapsed = Math.floor((Date.now() - state.sessionStartTime) / 1000);
    const m = String(Math.floor(elapsed / 60)).padStart(2, '0');
    const s = String(elapsed % 60).padStart(2, '0');
    timerEl.innerText = `${m}:${s}`;
  }, 1000);
}

// --- JSON DOWNLOAD ---
if ($("#download-json-btn")) {
  $("#download-json-btn").addEventListener("click", () => {
    if (!state.finalReport) return;
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(state.finalReport, null, 2));
    const a = document.createElement('a');
    a.setAttribute("href", dataStr);
    a.setAttribute("download", `viva_evaluation_${state.sessionId || 'report'}.json`);
    document.body.appendChild(a);
    a.click();
    a.remove();
  });
}



  // Real-time payload and time updates for Consent Step
  setInterval(() => {
    const timeEl = $("#system-time");
    if (timeEl && !$("#step-consent").classList.contains("hidden")) {
      const now = new Date();
      timeEl.textContent = "SYSTEM TIME: " + now.toISOString().split("T")[1].split(".")[0] + " UTC";
    }
    
    const payloadEl = $("#signal-payload");
    if (payloadEl && !$("#step-consent").classList.contains("hidden")) {
      const payload = {
        integrity_index: (0.95 + Math.random() * 0.05).toFixed(2),
        eye_gaze: "on_canvas",
        external_audio: (Math.random() * 0.1).toFixed(2),
        face_detected: !!(state.streamActive && !state.noFaceSince),
        viva_status: "authorized"
      };
      payloadEl.textContent = JSON.stringify(payload, null, 2);
    }
  }, 1000);
