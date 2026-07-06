from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from io import BytesIO

from app.db.database import get_db
from app.db.models import User, Submission, VivaSession
from app.services.auth import require_role

router = APIRouter(prefix="/reports", tags=["Reports"])

@router.get("/{submission_id}/export")
async def export_report(
    submission_id: str,
    format: str = "json",
    current_user: User = Depends(require_role("mentor")),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(
        select(Submission)
        .options(selectinload(Submission.evaluation_report))
        .where(Submission.id == submission_id)
    )
    submission = result.scalars().first()
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
        
    viva_result = await db.execute(select(VivaSession).where(VivaSession.submission_id == submission_id))
    viva_session = viva_result.scalars().first()
    
    report_data = {
        "project_title": submission.project_title,
        "suggested_skills": submission.evaluation_report.suggested_skills,
        "evaluation_report": submission.evaluation_report.evaluation_report,
        "proctoring_score": viva_session.integrity_score if viva_session else None,
        "proctoring_risk_level": viva_session.risk_level if viva_session else None,
        "proctoring_flags": viva_session.flags if viva_session else []
    }
    
    if format == "json":
        return JSONResponse(content=report_data)
        
    elif format == "pdf":
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib.styles import getSampleStyleSheet
            from reportlab.lib import colors
            
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            styles = getSampleStyleSheet()
            elements = []
            
            elements.append(Paragraph(f"AIvaluate Final Report: {submission.project_title}", styles['Title']))
            elements.append(Spacer(1, 12))
            
            # Add skills
            elements.append(Paragraph("Suggested Skills", styles['Heading2']))
            for s in report_data["suggested_skills"]:
                elements.append(Paragraph(f"- {s['skill_name']} (Confidence: {s['confidence']})", styles['Normal']))
            
            elements.append(Spacer(1, 12))
            
            # Add proctoring details
            elements.append(Paragraph("Proctoring Summary", styles['Heading2']))
            score = report_data['proctoring_score']
            risk = report_data['proctoring_risk_level']
            elements.append(Paragraph(f"Integrity Score: {score}", styles['Normal']))
            elements.append(Paragraph(f"Risk Level: {risk}", styles['Normal']))
            
            doc.build(elements)
            buffer.seek(0)
            
            return StreamingResponse(
                buffer, 
                media_type="application/pdf", 
                headers={"Content-Disposition": f"attachment; filename=report_{submission_id}.pdf"}
            )
        except ImportError:
            raise HTTPException(status_code=500, detail="reportlab is not installed.")
            
    else:
        raise HTTPException(status_code=400, detail="Invalid format specified. Use 'json' or 'pdf'.")
