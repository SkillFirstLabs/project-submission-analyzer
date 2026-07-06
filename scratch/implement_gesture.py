import re

with open("static/index.html", "r", encoding="utf-8") as f:
    html = f.read()

# 1. Add script tags
if "@mediapipe/tasks-vision" not in html:
    html = html.replace(
        '<script src="https://cdn.jsdelivr.net/npm/face-api.js@0.22.2/dist/face-api.min.js"></script>',
        '<script src="https://cdn.jsdelivr.net/npm/face-api.js@0.22.2/dist/face-api.min.js"></script>\n'
        '<script src="https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.3/vision_bundle.js" crossorigin="anonymous"></script>'
    )

# 2. Update Verification Instruction
old_instruction = '<p class="font-body text-body-sm text-on-surface-variant">Position your face within the frame and hold your ID card \nif requested.</p>'
new_instruction = '<p class="font-body text-body-sm text-on-surface-variant">Position your face within the frame and hold a <b class="text-primary">Thumbs Up 👍</b> to verify identity.</p>\n  <canvas id="photo-capture-canvas" class="hidden"></canvas>'
html = html.replace(old_instruction, new_instruction)

# 3. Update Alignment Score UI (Animated glowing conic gradient)
old_score = """<div class="relative flex items-center justify-center">
  <svg class="w-20 h-20 transform -rotate-90">
  <circle class="text-surface-container-high" cx="40" cy="40" fill="transparent" r="36" stroke="currentColor" 
stroke-width="6"></circle>
  <circle class="text-primary" cx="40" cy="40" fill="transparent" r="36" stroke="currentColor" 
stroke-dasharray="226.2" stroke-dashoffset="31.6" stroke-width="6"></circle>
  </svg>
  <span id="report-alignment-score" class="absolute font-headline-md text-headline-md text-on-surface">--%</span>
  </div>"""

new_score = """<div class="relative flex items-center justify-center w-24 h-24 rounded-full bg-surface-container-high shadow-[0_0_20px_rgba(59,130,246,0.3)] p-2">
  <div id="score-gauge" class="w-full h-full rounded-full transition-all duration-[2000ms] ease-out shadow-inner" style="background: conic-gradient(#3b82f6 0%, transparent 0%);"></div>
  <div class="absolute inset-2 bg-surface-container-lowest rounded-full flex items-center justify-center shadow-md">
    <span id="report-alignment-score" class="font-headline-md text-headline-md text-on-surface font-bold">--%</span>
  </div>
</div>"""
html = html.replace(old_score, new_score)

# 4. Update the final report image placeholder to show the captured photo
old_img = """<img alt="Live monitor active" class="w-full h-full object-cover rounded-xl" src="https://images.unsplash.com/photo-1516321497487-e288fb19713f?auto=format&fit=crop&q=80&w=1200"/>"""
new_img = """<img id="final-photo-display" alt="Identity Verification Photo" class="w-full h-full object-cover rounded-xl border-4 border-surface-container-highest shadow-xl transition-all hover:scale-[1.02]" src="https://images.unsplash.com/photo-1516321497487-e288fb19713f?auto=format&fit=crop&q=80&w=1200"/>"""
html = html.replace(old_img, new_img)

html = html.replace('app.js?v=7', 'app.js?v=8')

with open("static/index.html", "w", encoding="utf-8") as f:
    f.write(html)


with open("static/app.js", "r", encoding="utf-8") as f:
    app_js = f.read()

# Insert MediaPipe GestureRecognizer initialization and loop
gesture_init = """
// --- GESTURE RECOGNITION (MediaPipe) ---
let gestureRecognizer = null;
let lastVideoTime = -1;

async function initGestureRecognizer() {
  try {
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
"""

if "// --- GESTURE RECOGNITION" not in app_js:
    app_js = gesture_init + "\n" + app_js
    
    # Replace the old fake verification with init and scan
    old_verify = """setTimeout(() => {
        if ($("#consent-btn")) {
          $("#consent-btn").classList.remove("opacity-50", "cursor-not-allowed");
          $("#consent-btn").disabled = false;
        }
      }, 3000);"""
    
    new_verify = """initGestureRecognizer().then(() => {
        if ($("#consent-btn")) {
          $("#consent-btn").innerHTML = `<span class="material-symbols-outlined mr-2 animate-spin">sync</span> Loading Vision AI...`;
        }
        setTimeout(() => {
          if ($("#consent-btn")) {
            $("#consent-btn").innerHTML = `<span class="material-symbols-outlined mr-2">back_hand</span> Hold Thumbs Up...`;
          }
          scanGestureLoop(video);
        }, 1500);
      });"""
    app_js = app_js.replace(old_verify, new_verify)

# Update renderReport to animate the score and inject the photo
old_score_update = """  if ($("#report-alignment-score")) {
    const scoreVal = Math.round((report.evaluation_report?.summary?.alignment_score || 0) * 100);
    $("#report-alignment-score").textContent = `${scoreVal}%`;
  }"""

new_score_update = """  if ($("#report-alignment-score")) {
    const scoreVal = Math.round((report.evaluation_report?.summary?.alignment_score || 0) * 100);
    
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
  }"""
app_js = app_js.replace(old_score_update, new_score_update)

with open("static/app.js", "w", encoding="utf-8") as f:
    f.write(app_js)

print("Gesture recognition and UI updates written.")
