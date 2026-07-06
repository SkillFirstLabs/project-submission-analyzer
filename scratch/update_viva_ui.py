import re

with open("static/index.html", "r", encoding="utf-8") as f:
    html = f.read()

# Remove end-viva-btn
html = re.sub(r'<button id="end-viva-btn".*?</button>', '', html, flags=re.DOTALL)
html = html.replace('app.js?v=8', 'app.js?v=9')

with open("static/index.html", "w", encoding="utf-8") as f:
    f.write(html)


with open("static/app.js", "r", encoding="utf-8") as f:
    app_js = f.read()

# Fix next-q-btn handler
old_next_q = """if ($("#next-q-btn")) {
  $("#next-q-btn").addEventListener("click", () => {
    if (state.qIndex < state.questions.length - 1) { saveAnswer(); state.qIndex++; renderQuestion(); }
  });
}"""

new_next_q = """
async function submitSession() {
  saveAnswer();
  try {
    const video = $("#camera-feed");
    if (video && video.srcObject) video.srcObject.getTracks().forEach(t => t.stop());
    if (typeof proctorInterval !== "undefined" && proctorInterval) clearInterval(proctorInterval);

    const btn = $("#next-q-btn");
    if (btn) btn.innerHTML = `<span class="material-symbols-outlined mr-2 animate-spin">sync</span> Submitting...`;

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
"""
app_js = app_js.replace(old_next_q, new_next_q)

# Remove the old end-viva-btn handler if it exists
app_js = re.sub(r'if \(\$\("#end-viva-btn"\)\) \{.*?\n\}\n', '', app_js, flags=re.DOTALL)

# Fix renderReport to add the photo and animation
old_score = """if ($("#report-alignment-score")) $("#report-alignment-score").textContent = `${Math.round(data.evaluation_report.summary.alignment_score * 100)}%`;"""

new_score = """if ($("#report-alignment-score")) {
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
"""

app_js = app_js.replace(old_score, new_score)


with open("static/app.js", "w", encoding="utf-8") as f:
    f.write(app_js)

print("Updated app.js and index.html")
