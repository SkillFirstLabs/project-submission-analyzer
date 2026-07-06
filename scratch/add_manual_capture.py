import re

# 1. Update index.html
with open('static/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Change instruction text
old_instruction = 'Position your face within the frame and hold a <b \nclass="text-primary">Smile dY~S</b> to verify identity.'
# Note: due to unicode rendering in powershell, the smile emoji was garbled in Get-Content as 'dY~S' or similar. 
# We'll just use regex to replace it.
html = re.sub(r'Position your face within the frame and hold a .*? to verify identity\.', 'Position your face within the frame and click <b>Capture Photo</b> to verify identity.', html)

# Insert manual capture button below camera feed
camera_end = '<!-- Verification Logs Removed -->\n  </div>'
if '<!-- Verification Logs Removed -->' not in html:
    # fallback
    camera_end = '<!-- Dark Overlay -->\n  <div class="absolute inset-0 bg-on-background/20 z-0"></div>\n  </div>'

capture_btn_html = """
  <div class="mt-4 flex justify-center">
      <button id="manual-capture-btn" class="bg-primary text-on-primary px-6 py-2 rounded-full font-headline hover:opacity-90 transition-opacity shadow-sm flex items-center">
          <span class="material-symbols-outlined mr-2">photo_camera</span> Capture Photo
      </button>
  </div>
"""

html = html.replace(camera_end, camera_end + capture_btn_html)

# Bump version
html = re.sub(r'app\.js\?v=\d+', 'app.js?v=13', html)

with open('static/index.html', 'w', encoding='utf-8') as f:
    f.write(html)


# 2. Update app.js
with open('static/app.js', 'r', encoding='utf-8') as f:
    app = f.read()

# Remove the smile check logic from runFaceLoop
old_smile_check = """
      if (!identityVerified && resized.length === 1) {
        // Check for smile (happy > 0.8)
        if (resized[0].expressions && resized[0].expressions.happy > 0.8) {
          identityVerified = true;
          postEvent("id_verified", null, 0.95);
          logEvent("Identity verified", "success");
          
          // Capture photo
          const captureCanvas = $("#photo-capture-canvas");
          if (captureCanvas) {
            captureCanvas.width = video.videoWidth;
            captureCanvas.height = video.videoHeight;
            const captureCtx = captureCanvas.getContext("2d");
            captureCtx.drawImage(video, 0, 0, captureCanvas.width, captureCanvas.height);
            state.capturedPhoto = captureCanvas.toDataURL("image/jpeg");
          }
          
          // Update Button
          const btn = $("#consent-btn");
          if (btn) {
            btn.innerHTML = `<span class="material-symbols-outlined mr-2">check_circle</span> Captured & Validated`;
            btn.classList.remove("opacity-50", "cursor-not-allowed");
            btn.disabled = false;
          }
        }
      }
"""

app = app.replace(old_smile_check, "")

# We need to add the click listener for manual capture in startCamera or init
# The best place is inside DOMContentLoaded, but we can put it globally or inside startCamera.
# Let's add it right after we bind #consent-check in STEP 2.

manual_capture_js = """
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
      
      manualCaptureBtn.innerHTML = `<span class="material-symbols-outlined mr-2">check_circle</span> Captured`;
      manualCaptureBtn.classList.replace("bg-primary", "bg-emerald-600");
      manualCaptureBtn.disabled = true;
      
      const btn = $("#consent-btn");
      if (btn) {
        btn.innerHTML = `<span class="material-symbols-outlined mr-2">check_circle</span> Verified & Start`;
        btn.classList.remove("opacity-50", "cursor-not-allowed");
        btn.disabled = false;
      }
    });
  }
"""

step2_end = 'const consentBtn = $("#consent-btn");'
app = app.replace(step2_end, step2_end + "\n" + manual_capture_js)

with open('static/app.js', 'w', encoding='utf-8') as f:
    f.write(app)

print("Applied manual capture button changes.")
