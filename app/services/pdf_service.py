import os
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet


def generate_pdf_report(result: dict, output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(output_path)

    story = []

    story.append(Paragraph("<b>AI Project Submission Analyzer Report</b>", styles["Title"]))

    story.append(Paragraph(f"<b>Overall Score:</b> {result.get('overall_score')}", styles["Normal"]))
    story.append(Paragraph(f"<b>Frameworks:</b> {', '.join(result.get('frameworks', []))}", styles["Normal"]))

    story.append(Paragraph("<b>Detected Skills</b>", styles["Heading2"]))
    for skill in result.get("skills", []):
        story.append(Paragraph(skill["skill_name"], styles["Normal"]))

    story.append(Paragraph("<b>Project Structure</b>", styles["Heading2"]))
    story.append(Paragraph(str(result.get("structure")), styles["Normal"]))

    story.append(Paragraph("<b>README Analysis</b>", styles["Heading2"]))
    story.append(Paragraph(str(result.get("readme")), styles["Normal"]))

    story.append(Paragraph("<b>Project Statistics</b>", styles["Heading2"]))
    story.append(Paragraph(str(result.get("project_statistics")), styles["Normal"]))

    story.append(Paragraph("<b>Code Quality</b>", styles["Heading2"]))
    story.append(Paragraph(str(result.get("code_quality")), styles["Normal"]))

    story.append(Paragraph("<b>AI Feedback</b>", styles["Heading2"]))
    story.append(Paragraph(str(result.get("ai_feedback")), styles["Normal"]))

    doc.build(story)