import re

with open("static/app.js", "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add Toast, Speech Recognition, and Timer functions at the end of the file
features = """

// --- TOAST NOTIFICATIONS ---
function showToast(msg, type = 'error') {
  const container = $("#toast-container");
  if (!container) return;
  const t = document.createElement("div");
  const bg = type === 'error' ? 'bg-rose-600' : 'bg-emerald-600';
  t.className = `${bg} text-white px-4 py-2 rounded shadow-lg transition-all duration-300 transform translate-x-10 opacity-0 font-body-sm z-50`;
  t.innerText = msg;
  container.appendChild(t);
  setTimeout(() => { t.classList.remove('translate-x-10', 'opacity-0'); }, 10);
  setTimeout(() => {
    t.classList.add('opacity-0');
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
  const icon = $("#mic-icon");
  const text = $("#mic-text");
  if(icon) { icon.classList.remove("animate-pulse"); icon.style.color = ""; }
  if(text) text.innerText = "Click to speak...";
}

if ($("#mic-btn")) {
  $("#mic-btn").addEventListener("click", () => {
    if (!recognition) {
      alert("Speech recognition not supported in this browser. Try Chrome.");
      return;
    }
    const icon = $("#mic-icon");
    const text = $("#mic-text");
    if (isRecording) {
      stopRecording();
    } else {
      isRecording = true;
      recognition.start();
      if(icon) { icon.classList.add("animate-pulse"); icon.style.color = "#dc2626"; }
      if(text) text.innerText = "Listening...";
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
"""
if "function showToast" not in content:
    content += features

# 2. Add startTimer() to startVivaSession
content = content.replace('logEvent("Session started", "info");', 'logEvent("Session started", "info");\\n  startTimer();')

# 3. Add clearTimer and stopRecording to end viva click
end_repl = """
      if (video && video.srcObject) video.srcObject.getTracks().forEach(t => t.stop());
      if (proctorInterval) clearInterval(proctorInterval);
      if (timerInterval) clearInterval(timerInterval);
      if (typeof stopRecording === 'function') stopRecording();
"""
content = content.replace('if (video && video.srcObject) video.srcObject.getTracks().forEach(t => t.stop());\\n      if (proctorInterval) clearInterval(proctorInterval);', end_repl)

# 4. Update the catch block for alert
catch_repl = """
      let errStr = data.detail || "Could not end session.";
      if (typeof errStr !== "string") errStr = JSON.stringify(errStr);
      throw new Error(errStr);
"""
content = content.replace('throw new Error(data.detail || "Could not end session.");', catch_repl)

# 5. Add showToast to strike conditions
content = content.replace('logEvent("Face not detected", "warning");', 'logEvent("Face not detected", "warning");\\n        if(typeof showToast === "function") showToast("Warning: Face not detected!", "error");')
content = content.replace('logEvent("Gaze off-screen", "warning");', 'logEvent("Gaze off-screen", "warning");\\n          if(typeof showToast === "function") showToast("Warning: Please look at the screen.", "error");')
content = content.replace('logEvent("Multiple faces detected", "error");', 'logEvent("Multiple faces detected", "error");\\n      if(typeof showToast === "function") showToast("Warning: Multiple faces detected!", "error");')
content = content.replace('logEvent("Tab switch detected", "error");', 'logEvent("Tab switch detected", "error");\\n      if(typeof showToast === "function") showToast("Warning: Tab switch detected!", "error");')

with open("static/app.js", "w", encoding="utf-8") as f:
    f.write(content)
print("Updated app.js")
