import re

with open("static/index.html", "r", encoding="utf-8") as f:
    content = f.read()

# Instead of regex, we can just split at '<div id="step-technical_precision_system"'
if '<div id="step-technical_precision_system"' in content:
    content = content.split('<div id="step-technical_precision_system"')[0]
    # And we also need to append the closing body/html tags that might have been at the end!
    content += "</body>\n</html>"

with open("static/index.html", "w", encoding="utf-8") as f:
    f.write(content)

print("Removed technical_precision_system from index.html")
