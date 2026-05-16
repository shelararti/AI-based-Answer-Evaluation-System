from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

from pydantic import BaseModel
from model import grade_answer

# -----------------------------
# App initialization
# -----------------------------
app = FastAPI(title="AI Evaluation Engine")

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# -----------------------------
# Request schema
# -----------------------------
class EvalRequest(BaseModel):
    question: str
    reference: str
    student: str
    max_marks: float = 5.0  # default fallback

# -----------------------------
# Utility
# -----------------------------
def normalize_text(text: str) -> str:
    return " ".join(text.strip().split())

# -----------------------------
# Home route (UI)
# -----------------------------
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {"request": request}
    )

# -----------------------------
# Evaluation endpoint
# -----------------------------
@app.post("/evaluate")
async def evaluate(data: EvalRequest):
    try:
        # Core grading engine
        result = grade_answer(
            reference=data.reference,
            student=data.student,
            question=data.question
        )

        # Scale score
        final_score = round(result["score"] * data.max_marks, 2)

        # Clean feedback
        feedback = normalize_text(result["feedback"])

        return {
            "question": data.question,
            "score": final_score,
            "max_marks": data.max_marks,
            "feedback": feedback,
            "rubric": result["rubric"]
        }

    except Exception as e:
        # Fail gracefully instead of crashing frontend
        return {
            "error": "Evaluation failed",
            "details": str(e)
        }

# -----------------------------
# Health check endpoint
# -----------------------------
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "hybrid-ai-answer-evaluator"
    }