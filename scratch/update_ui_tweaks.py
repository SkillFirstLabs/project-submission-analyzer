import re

with open("static/index.html", "r", encoding="utf-8") as f:
    content = f.read()

# Add IDs to the upload box text
content = content.replace(
    '<h3 class="font-headline-md text-headline-md mb-2">Upload your secure ZIP file</h3>',
    '<h3 id="upload-title" class="font-headline-md text-headline-md mb-2">Upload your secure ZIP file</h3>'
)

content = content.replace(
    '<p class="text-on-surface-variant font-body-md mb-6">Drag and drop your project archive here, or click to browse files.<br/><span class="font-body-sm text-body-sm">(Max size: 50MB)</span></p>',
    '<p id="upload-desc" class="text-on-surface-variant font-body-md mb-6">Drag and drop your project archive here, or click to browse files.<br/><span class="font-body-sm text-body-sm">(Max size: 50MB)</span></p>'
)

# Add ID to the terminal box
content = content.replace(
    '<div class="bg-black/20 rounded-lg p-3 font-code-md text-[12px] text-primary-fixed-dim/80 space-y-1">',
    '<div id="ai-proctor-terminal" class="bg-black/20 rounded-lg p-3 font-code-md text-[12px] text-primary-fixed-dim/80 space-y-1">'
)

with open("static/index.html", "w", encoding="utf-8") as f:
    f.write(content)
print("Updated index.html")

with open("static/app.js", "r", encoding="utf-8") as f:
    app_content = f.read()

# Update file change listener
old_change_listener = """$("input[name='zip_file']").addEventListener("change", (e) => {
  const form = $("#submit-form");
  if (e.target.files.length > 0 && form.checkValidity()) {
    $("#analyze-btn").click();
  }
});"""

new_change_listener = """$("input[name='zip_file']").addEventListener("change", (e) => {
  if (e.target.files.length > 0) {
    const file = e.target.files[0];
    const sizeMb = (file.size / (1024 * 1024)).toFixed(2);
    const title = $("#upload-title");
    const desc = $("#upload-desc");
    if(title) title.innerText = "1 file uploaded";
    if(desc) desc.innerHTML = `<span class="font-semibold text-primary">${file.name}</span> (${sizeMb} MB)<br/><span class="text-emerald-600">Ready for analysis</span>`;
  }
});"""
app_content = app_content.replace(old_change_listener, new_change_listener)

# Update analyze-btn listener to include terminal simulation
analyze_start = """  btn.innerHTML = `<span class="material-symbols-outlined mr-2 animate-spin">sync</span> Analyzing...`;"""
analyze_new = """  btn.innerHTML = `<span class="material-symbols-outlined mr-2 animate-spin">sync</span> Analyzing...`;
  
  const term = $("#ai-proctor-terminal");
  if (term) {
    term.innerHTML = "<p>&gt; Uploading payload...</p>";
    setTimeout(() => { if (term.parentElement) term.innerHTML += "<p>&gt; Extracting codebase...</p>"; }, 800);
    setTimeout(() => { if (term.parentElement) term.innerHTML += "<p>&gt; Analyzing architecture...</p>"; }, 1500);
    setTimeout(() => { if (term.parentElement) term.innerHTML += "<p>&gt; Evaluating skill alignment...</p>"; }, 2500);
  }
"""
app_content = app_content.replace(analyze_start, analyze_new)

with open("static/app.js", "w", encoding="utf-8") as f:
    f.write(app_content)
print("Updated app.js")
