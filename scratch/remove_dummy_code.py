import re

with open("static/index.html", "r", encoding="utf-8") as f:
    content = f.read()

# Delete the dummy <pre> block
pattern = r'<pre class="font-code-md text-code-md text-slate-300 leading-relaxed"><span class="text-blue-400">@app\.middleware.*?return await call_next\(request\)</pre>'
content = re.sub(pattern, "", content, flags=re.DOTALL)

with open("static/index.html", "w", encoding="utf-8") as f:
    f.write(content)

print("Dummy code block removed.")
