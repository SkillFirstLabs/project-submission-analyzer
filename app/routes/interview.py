from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
import app.data.interview_questions as interview_data

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


@router.get("/interview")
async def interview_page(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="interview.html",
        context={
            "request": request,
            "questions": interview_data.latest_questions
        }
    )