from fastapi import FastAPI, Request, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import logging
import sys
from utils.code_fixer import CodeFixer
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('app.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="Editor di Codice Intelligente")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Initialize CodeFixer
code_fixer = CodeFixer()

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Render the main editor page"""
    return templates.TemplateResponse(
        "editor.html",
        {
            "request": request,
            "code": "def esempio():\n    print('Hello World!')"
        }
    )

@app.post("/analyze")
async def analyze_code(request: Request, code: str = Form(...)):
    """Analyze the code and return suggestions"""
    try:
        # Get analysis from CodeFixer
        analysis = code_fixer.analyze_code(code)

        # Extract suggestions
        suggestions = []
        if "potential_issues" in analysis:
            suggestions.extend(analysis["potential_issues"])
        if "suggestions" in analysis:
            suggestions.extend(analysis["suggestions"])
        if "best_practices" in analysis:
            suggestions.extend(analysis["best_practices"])

        return templates.TemplateResponse(
            "suggestions.html",
            {
                "request": request,
                "suggestions": suggestions
            }
        )
    except Exception as e:
        logger.error(f"Error analyzing code: {str(e)}")
        return templates.TemplateResponse(
            "suggestions.html",
            {
                "request": request,
                "error": f"Errore nell'analisi: {str(e)}"
            }
        )

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting FastAPI application")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8501,
        reload=True
    )