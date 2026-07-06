import os
import re

def extract_body(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    # Extract everything inside <body>...</body>
    body_match = re.search(r"<body[^>]*>(.*?)</body>", content, re.DOTALL | re.IGNORECASE)
    return body_match.group(1) if body_match else ""

def extract_styles(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    style_match = re.search(r"<style>(.*?)</style>", content, re.DOTALL | re.IGNORECASE)
    return style_match.group(1) if style_match else ""

def main():
    base_dir = "temp_ui_extract/stitch_ai_project_viva_proctor"
    screens = [
        ("student_submission_portal", "step-upload"),
        ("viva_setup_consent", "step-consent"),
        ("live_proctored_viva", "step-viva"),
        ("ai_evaluation_integrity_report", "step-report")
    ]
    
    combined_body = ""
    combined_styles = ""
    
    for folder, step_id in screens:
        path = os.path.join(base_dir, folder, "code.html")
        body_content = extract_body(path)
        # Wrap each screen in a step container
        combined_body += f'\n<div id="{step_id}" class="step-container {"hidden" if step_id != "step-upload" else ""}">\n{body_content}\n</div>\n'
        combined_styles += extract_styles(path) + "\n"

    # Use the tailwind config from the first template
    tailwind_config = ""
    with open(os.path.join(base_dir, "student_submission_portal", "code.html"), "r", encoding="utf-8") as f:
        config_match = re.search(r'(<script id="tailwind-config">.*?</script>)', f.read(), re.DOTALL)
        if config_match:
            tailwind_config = config_match.group(1)

    index_html = f"""<!DOCTYPE html>
<html class="light" lang="en">
<head>
    <meta charset="utf-8"/>
    <meta content="width=device-width, initial-scale=1.0" name="viewport"/>
    <title>EvalAI - Project Analyzer</title>
    <script src="https://cdn.tailwindcss.com?plugins=forms,container-queries"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Syne:wght@700;800&family=JetBrains+Mono&display=swap" rel="stylesheet"/>
    <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet"/>
    <script defer src="https://cdn.jsdelivr.net/npm/face-api.js@0.22.2/dist/face-api.min.js"></script>
    {tailwind_config}
    <style>
        .hidden {{ display: none !important; }}
        {combined_styles}
    </style>
</head>
<body class="bg-surface font-body-md text-on-surface">
    <form id="submit-form" onsubmit="event.preventDefault();">
        {combined_body}
    </form>
    <script src="/static/app.js"></script>
</body>
</html>"""

    with open("static/index.html", "w", encoding="utf-8") as f:
        f.write(index_html)
    print("UI built successfully.")

if __name__ == "__main__":
    main()
