with open('static/app.js', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace('try {`n    const detections', 'try {\n    const detections')
with open('static/app.js', 'w', encoding='utf-8') as f:
    f.write(content)
print("Syntax fixed")
