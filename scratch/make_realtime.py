import re

# 1. Update index.html
with open('static/index.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Add ID to payload pre block
html = html.replace(
    '<pre class="font-code text-code-md text-surface-variant text-[12px]">{',
    '<pre id="signal-payload" class="font-code text-code-md text-surface-variant text-[12px]">{',
)

# Add ID to system time
html = html.replace(
    'SYSTEM TIME: 14:22:01 UTC',
    '<span id="system-time">SYSTEM TIME: 14:22:01 UTC</span>'
)

# Insert the missing capture button below the camera overlay
# The camera overlay ends with </canvas>\n    </div>\n    \n<!-- Dark Overlay -->
# I will insert it right there.
camera_insertion = """
    </div>
    
    <div class="mt-4 flex justify-center relative z-20">
        <button id="manual-capture-btn" class="bg-primary text-on-primary px-6 py-2 rounded-full font-headline hover:opacity-90 transition-opacity shadow-sm flex items-center gap-2" type="button">
            <span class="material-symbols-outlined">photo_camera</span> Capture Photo
        </button>
    </div>
"""
html = html.replace('\n    </div>\n    \n<!-- Dark Overlay -->', camera_insertion + '\n<!-- Dark Overlay -->')

# Bump version
html = re.sub(r'app\.js\?v=\d+', 'app.js?v=14', html)

with open('static/index.html', 'w', encoding='utf-8') as f:
    f.write(html)


# 2. Update app.js
with open('static/app.js', 'r', encoding='utf-8') as f:
    app = f.read()

realtime_js = """
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
"""

# Append to end of DOMContentLoaded listener, right after the init code
# Let's just append it to the very bottom of the file
if "// Real-time payload" not in app:
    app += "\n\n" + realtime_js

with open('static/app.js', 'w', encoding='utf-8') as f:
    f.write(app)

print("Applied real-time UI changes and added capture button.")
