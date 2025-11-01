"""
FastAPI додаток для оцінки доступності вебсайтів
З використанням Jinja2 templates замість inline HTML
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Optional, List, Dict, Any
import sys
import os
from pathlib import Path

# Додаємо батьківську директорію до Python path
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

from accessibility_evaluator.core.evaluator import AccessibilityEvaluator

# Ініціалізація FastAPI
app = FastAPI(
    title="Accessibility Evaluator API",
    description="API для комплексної оцінки доступності вебсайтів згідно WCAG 2.1",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Templates та static files
templates_dir = current_dir.parent / "templates"
static_dir = current_dir.parent / "static"

templates = Jinja2Templates(directory=str(templates_dir))
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Helper Functions

def get_quality_level(score: float) -> tuple:
    """
    Визначає рівень якості та опис на основі скору

    Args:
        score: Скор від 0 до 1

    Returns:
        Tuple (quality_level, quality_description)
    """
    if score >= 0.9:
        return ("Відмінно", "Сайт має відмінну доступність")
    elif score >= 0.75:
        return ("Добре", "Сайт має хорошу доступність з незначними проблемами")
    elif score >= 0.6:
        return ("Задовільно", "Сайт має задовільну доступність, потрібні покращення")
    elif score >= 0.4:
        return ("Погано", "Сайт має значні проблеми з доступністю")
    else:
        return ("Критично", "Сайт має критичні проблеми з доступністю")


# Pydantic models


class URLRequest(BaseModel):
    url: HttpUrl


class HTMLRequest(BaseModel):
    html_content: str
    base_url: Optional[str] = None
    title: Optional[str] = None


class Recommendation(BaseModel):
    category: str
    priority: str
    recommendation: str
    wcag_reference: str


class Subscores(BaseModel):
    perceptibility: float
    operability: float
    understandability: float
    localization: float


class EvaluationResponse(BaseModel):
    url: str
    final_score: float
    quality_level: Optional[str] = None
    quality_description: Optional[str] = None
    subscores: Subscores
    metrics: Dict[str, Any]
    recommendations: List[Recommendation]
    detailed_analysis: Optional[Dict[str, Any]] = None
    status: str = "success"
    error: Optional[str] = None

# Routes


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Головна сторінка з веб-інтерфейсом"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/api/evaluate", response_model=EvaluationResponse)
async def evaluate_accessibility(request: URLRequest):
    """
    Оцінка доступності веб-сторінки за URL

    Args:
        request: URLRequest з URL для аналізу

    Returns:
        EvaluationResponse з результатами оцінки
    """
    try:
        url = str(request.url)
        print(f"\n🔍 Початок оцінки доступності для URL: {url}")

        evaluator = AccessibilityEvaluator()
        result = await evaluator.evaluate_accessibility(url)

        print(f"✅ Оцінка завершена успішно для {url}")
        print(f"📊 Загальний скор: {result['final_score']:.2%}")

        # Додаємо quality_level та quality_description
        quality_level, quality_description = get_quality_level(result['final_score'])
        result['quality_level'] = quality_level
        result['quality_description'] = quality_description

        return EvaluationResponse(**result)

    except Exception as e:
        error_message = f"Помилка при оцінці доступності: {str(e)}"
        print(f"❌ {error_message}")

        return EvaluationResponse(
            url=str(request.url),
            final_score=0.0,
            quality_level="Помилка",
            quality_description=error_message,
            subscores=Subscores(
                perceptibility=0.0,
                operability=0.0,
                understandability=0.0,
                localization=0.0
            ),
            metrics={},
            recommendations=[],
            status="error",
            error=error_message
        )


@app.post("/api/evaluate-html", response_model=EvaluationResponse)
async def evaluate_html(request: HTMLRequest):
    """
    Оцінка доступності HTML контенту

    Args:
        request: HTMLRequest з HTML контентом

    Returns:
        EvaluationResponse з результатами оцінки
    """
    try:
        print(f"\n🔍 Початок оцінки доступності HTML контенту")
        print(f"📄 Розмір HTML: {len(request.html_content)} символів")

        evaluator = AccessibilityEvaluator()
        result = await evaluator.evaluate_html_content(
            html_content=request.html_content,
            base_url=request.base_url,
            title=request.title
        )

        print(f"✅ Оцінка HTML завершена успішно")
        print(f"📊 Загальний скор: {result['final_score']:.2%}")

        # Додаємо quality_level та quality_description
        quality_level, quality_description = get_quality_level(result['final_score'])
        result['quality_level'] = quality_level
        result['quality_description'] = quality_description

        return EvaluationResponse(**result)

    except Exception as e:
        error_message = f"Помилка при оцінці HTML: {str(e)}"
        print(f"❌ {error_message}")

        return EvaluationResponse(
            url=request.base_url or "HTML Content",
            final_score=0.0,
            quality_level="Помилка",
            quality_description=error_message,
            subscores=Subscores(
                perceptibility=0.0,
                operability=0.0,
                understandability=0.0,
                localization=0.0
            ),
            metrics={},
            recommendations=[],
            status="error",
            error=error_message
        )


@app.post("/api/report", response_class=HTMLResponse)
async def generate_report(request: Request, data: EvaluationResponse):
    """
    Генерує HTML звіт з результатів аналізу

    Args:
        data: EvaluationResponse з результатами аналізу

    Returns:
        HTML звіт
    """
    from datetime import datetime

    def get_score_class(score):
        if score >= 0.9:
            return 'excellent'
        if score >= 0.75:
            return 'good'
        if score >= 0.6:
            return 'fair'
        if score >= 0.4:
            return 'poor'
        return 'critical'

    # Якщо quality_level або quality_description відсутні - генеруємо їх
    quality_level = data.quality_level
    quality_description = data.quality_description

    if not quality_level or not quality_description:
        quality_level, quality_description = get_quality_level(data.final_score)

    return templates.TemplateResponse("report.html", {
        "request": request,
        "url": data.url,
        "date": datetime.now().strftime("%d.%m.%Y"),
        "quality_level": quality_level,
        "quality_description": quality_description,
        "final_score": round(data.final_score * 100, 1),
        "subscores": data.subscores,
        "metrics": data.metrics,  # Додаємо metrics для детального аналізу
        "detailed_analysis": data.detailed_analysis or {},  # Додаємо detailed_analysis
        "recommendations": data.recommendations,
        "timestamp": datetime.now().strftime("%d.%m.%Y %H:%M:%S"),
        "get_score_class": get_score_class
    })


@app.get("/api/health")
async def health_check():
    """Перевірка статусу API"""
    return {
        "status": "healthy",
        "service": "Accessibility Evaluator API",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
