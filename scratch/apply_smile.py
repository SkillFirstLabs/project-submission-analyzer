import re

# 1. Update index.html
with open('static/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

html = html.replace('Thumbs Up 👍', 'Smile 😊')
html = re.sub(r'<script.*?vision_bundle\.js.*?</script>\n?', '', html)

with open('static/index.html', 'w', encoding='utf-8') as f:
    f.write(html)


# 2. Update app.js
with open('static/app.js', 'r', encoding='utf-8') as f:
    app = f.read()

# Strip MediaPipe logic
app = re.sub(r'// --- GESTURE RECOGNITION.*?async function scanGestureLoop\(video\) \{.*?requestAnimationFrame\(\(\) => scanGestureLoop\(video\)\);\n  \}\n', '', app, flags=re.DOTALL)

# Add faceExpressionNet load
app = app.replace(
    'await faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL);',
    'await faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL);\n      await faceapi.nets.faceExpressionNet.loadFromUri(MODEL_URL);'
)

# Update runFaceLoop to detect smile
old_detect = 'const detections = await faceapi.detectAllFaces(video, options).withFaceLandmarks();'
new_detect = 'const detections = await faceapi.detectAllFaces(video, options).withFaceLandmarks().withFaceExpressions();'
app = app.replace(old_detect, new_detect)

old_identity_verified = """
      if (!identityVerified && resized.length === 1) {
        identityVerified = true;
        postEvent("id_verified", null, 0.95);
        logEvent("Identity verified", "success");
      }
"""

new_identity_verified = """
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

app = app.replace(old_identity_verified, new_identity_verified)

# Also remove calls to initGestureRecognizer and scanGestureLoop in startCamera (they might not be there anymore, but just in case)
app = app.replace('await initGestureRecognizer();\n', '')
app = app.replace('scanGestureLoop(video);\n', '')

with open('static/app.js', 'w', encoding='utf-8') as f:
    f.write(app)

print("Applied smile gesture changes.")
