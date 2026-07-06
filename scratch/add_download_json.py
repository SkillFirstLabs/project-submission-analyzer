import re

with open("static/index.html", "r", encoding="utf-8") as f:
    content = f.read()

# Find the header div and replace it to add the button
old_header = """  <div class="flex flex-col items-center justify-center p-6 bg-surface-container-lowest rounded-xl shadow-sm border 
border-outline-variant min-w-[200px]">"""

new_header = """  <div class="flex flex-col gap-3">
  <div class="flex flex-col items-center justify-center p-6 bg-surface-container-lowest rounded-xl shadow-sm border border-outline-variant min-w-[200px] flex-1">"""

content = content.replace(old_header, new_header)

old_svg_end = """  <span id="report-score" class="absolute font-headline-lg text-headline-lg font-bold text-primary">20%</span>
  </div>
  </div>"""

new_svg_end = """  <span id="report-score" class="absolute font-headline-lg text-headline-lg font-bold text-primary">20%</span>
  </div>
  </div>
  <button id="download-json-btn" type="button" class="w-full py-3 bg-primary-container text-on-primary-container font-label-lg rounded-xl shadow-sm hover:brightness-95 transition-all flex items-center justify-center gap-2 border border-primary/20">
    <span class="material-symbols-outlined text-[20px]">download</span> Download JSON
  </button>
  </div>"""

content = content.replace(old_svg_end, new_svg_end)

# Bump version
content = content.replace('src="/static/app.js?v=5"', 'src="/static/app.js?v=6"')

with open("static/index.html", "w", encoding="utf-8") as f:
    f.write(content)


with open("static/app.js", "r", encoding="utf-8") as f:
    app_js = f.read()

# Add download logic at the end of the file
download_js = """
  // JSON Download Button
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
});
"""
# Replace the very last line '});' with the new logic + closing the init function
app_js = re.sub(r'\}\);\s*$', download_js, app_js)

with open("static/app.js", "w", encoding="utf-8") as f:
    f.write(app_js)

print("Added JSON download button")
