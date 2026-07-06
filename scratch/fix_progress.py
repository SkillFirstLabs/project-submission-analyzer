import re

# 1. Update index.html
with open("static/index.html", "r", encoding="utf-8") as f:
    content = f.read()

progress_html = """<div class="flex items-center gap-2">
                            <div class="h-1 w-24 bg-primary rounded-full"></div>
                            <div class="h-1 w-24 bg-primary rounded-full"></div>
                            <div class="h-1 w-24 bg-primary rounded-full"></div>
                            <div class="h-1 w-24 bg-primary rounded-full"></div>
                            <div class="h-1 w-24 bg-outline-variant rounded-full"></div>
                        </div>"""

new_progress_html = """<div id="progress-container" class="flex items-center gap-2 w-full max-w-[600px] overflow-hidden">
                            <div class="h-1 flex-1 bg-outline-variant rounded-full"></div>
                        </div>"""

content = content.replace(progress_html, new_progress_html)

# Add ID to end-viva-btn if it doesn't exist? Wait, I didn't see end-viva-btn in the screenshot. 
# It's probably in the sidebar. Let's make sure app.js handles version bump.
content = content.replace('src="/static/app.js?v=3"', 'src="/static/app.js?v=4"')

with open("static/index.html", "w", encoding="utf-8") as f:
    f.write(content)


# 2. Update app.js
with open("static/app.js", "r", encoding="utf-8") as f:
    app_js = f.read()

# Replace next-q-btn and skip-q-btn listeners
old_listeners = """  if ($("#next-q-btn")) {
    $("#next-q-btn").addEventListener("click", () => {
      if (state.qIndex < state.questions.length - 1) { saveAnswer(); state.qIndex++; renderQuestion(); }
    });
  }
  if ($("#skip-q-btn")) {
    $("#skip-q-btn").addEventListener("click", () => {
      if (state.qIndex < state.questions.length - 1) { state.qIndex++; renderQuestion(); }
    });
  }"""

new_listeners = """  if ($("#next-q-btn")) {
    $("#next-q-btn").addEventListener("click", () => {
      saveAnswer();
      if (state.qIndex < state.questions.length - 1) { 
        state.qIndex++; 
        renderQuestion(); 
      } else {
        endSession();
      }
    });
  }
  if ($("#skip-q-btn")) {
    $("#skip-q-btn").addEventListener("click", () => {
      if (state.qIndex < state.questions.length - 1) { 
        state.qIndex++; 
        renderQuestion(); 
      } else {
        endSession();
      }
    });
  }"""

app_js = app_js.replace(old_listeners, new_listeners)

# Update renderQuestion to render progress bars
render_q_search = """  if ($("#question-counter-header")) {
    const total = state.questions.length > 0 ? state.questions.length : 12;
    $("#question-counter-header").textContent = `${(state.qIndex + 1).toString().padStart(2, '0')} / ${total.toString().padStart(2, '0')}`;
  }"""

render_q_new = render_q_search + """
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
    if (state.qIndex === state.questions.length - 1) {
      $("#next-q-btn").innerHTML = 'SUBMIT SESSION <span class="material-symbols-outlined text-[18px]">done_all</span>';
    } else {
      $("#next-q-btn").innerHTML = 'SUBMIT ANSWER <span class="material-symbols-outlined text-[18px]">send</span>';
    }
  }
"""

app_js = app_js.replace(render_q_search, render_q_new)

# Abstract endSession function
old_end_viva = """  if ($("#end-viva-btn")) {
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
    });
  }"""

new_end_viva = """  async function endSession() {
    if (!confirm("End the viva session and generate the final report?")) return;
    
    const btn = $("#next-q-btn");
    if (btn) {
      btn.disabled = true;
      btn.innerHTML = `<span class="material-symbols-outlined mr-2 animate-spin">sync</span> Evaluating...`;
    }
    
    try {
      const video = $("#camera-feed");
      if (video && video.srcObject) video.srcObject.getTracks().forEach(t => t.stop());
      if (proctorInterval) clearInterval(proctorInterval);

      const res = await fetch("/viva-session/end?session_id=" + encodeURIComponent(state.sessionId), {
        method: "POST"
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
    } finally {
      if (btn) btn.disabled = false;
    }
  }

  if ($("#end-viva-btn")) {
    $("#end-viva-btn").addEventListener("click", () => {
      saveAnswer();
      endSession();
    });
  }
  // Expose endSession globally so next-q-btn can call it
  window.endSession = endSession;
"""

app_js = app_js.replace(old_end_viva, new_end_viva)

with open("static/app.js", "w", encoding="utf-8") as f:
    f.write(app_js)

print("Updated JS and HTML")
