"""
FastAPI веб-додаток для оцінки доступності
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, HttpUrl
from typing import Dict, Any
import asyncio
import os
import sys

# Додаємо шлях до core модулів
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, '..', '..')
sys.path.insert(0, project_root)

try:
    from accessibility_evaluator.core.evaluator import AccessibilityEvaluator
except ImportError:
    # Fallback для локального запуску
    sys.path.insert(0, os.path.join(current_dir, '..', '..'))
    from core.evaluator import AccessibilityEvaluator

app = FastAPI(
    title="Accessibility Evaluator API",
    description="API для оцінки доступності вебсайтів згідно з ISO 25023",
    version="1.0.0"
)

# CORS middleware для frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшені обмежити до конкретних доменів
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

# Додаємо middleware для логування запитів
@app.middleware("http")
async def log_requests(request, call_next):
    print(f"📨 {request.method} {request.url}")
    response = await call_next(request)
    print(f"📤 Відповідь: {response.status_code}")
    return response

# Ініціалізація evaluator
evaluator = AccessibilityEvaluator()


class URLRequest(BaseModel):
    """Модель запиту для аналізу URL"""
    url: HttpUrl


class EvaluationResponse(BaseModel):
    """Модель відповіді з результатами аналізу"""
    url: str
    metrics: Dict[str, float]
    subscores: Dict[str, float]
    final_score: float
    quality_level: str
    quality_description: str
    recommendations: list
    status: str


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """Головна сторінка з веб-інтерфейсом"""
    
    html_content = """
    <!DOCTYPE html>
    <html lang="uk">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Оцінка доступності вебсайтів</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                border-radius: 15px;
                box-shadow: 0 20px 40px rgba(0,0,0,0.1);
                overflow: hidden;
            }
            
            .header {
                background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
                color: white;
                padding: 40px;
                text-align: center;
            }
            
            .header h1 {
                font-size: 2.5rem;
                margin-bottom: 10px;
                font-weight: 300;
            }
            
            .header p {
                font-size: 1.1rem;
                opacity: 0.9;
            }
            
            .main-content {
                padding: 40px;
            }
            
            .url-form {
                background: #f8f9fa;
                padding: 30px;
                border-radius: 10px;
                margin-bottom: 30px;
                border: 2px solid #e9ecef;
            }
            
            .form-group {
                margin-bottom: 20px;
            }
            
            label {
                display: block;
                margin-bottom: 8px;
                font-weight: 600;
                color: #2c3e50;
            }
            
            input[type="url"] {
                width: 100%;
                padding: 15px;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-size: 16px;
                transition: border-color 0.3s;
            }
            
            input[type="url"]:focus {
                outline: none;
                border-color: #3498db;
                box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
            }
            
            .btn {
                background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s, box-shadow 0.2s;
                width: 100%;
            }
            
            .btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(52, 152, 219, 0.3);
            }
            
            .btn:disabled {
                opacity: 0.6;
                cursor: not-allowed;
                transform: none;
            }
            
            .loading {
                display: none;
                text-align: center;
                padding: 20px;
            }
            
            .spinner {
                border: 4px solid #f3f3f3;
                border-top: 4px solid #3498db;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto 10px;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .results {
                display: none;
                margin-top: 30px;
            }
            
            .score-card {
                background: linear-gradient(135deg, #27ae60 0%, #2ecc71 100%);
                color: white;
                padding: 30px;
                border-radius: 10px;
                text-align: center;
                margin-bottom: 30px;
            }
            
            .score-value {
                font-size: 3rem;
                font-weight: bold;
                margin-bottom: 10px;
            }
            
            .score-level {
                font-size: 1.2rem;
                margin-bottom: 5px;
            }
            
            .score-description {
                opacity: 0.9;
            }
            
            .metrics-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            
            .metric-card {
                background: white;
                border: 2px solid #e9ecef;
                border-radius: 10px;
                padding: 20px;
                text-align: center;
                transition: transform 0.2s;
            }
            
            .metric-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 25px rgba(0,0,0,0.1);
            }
            
            .metric-name {
                font-weight: 600;
                color: #2c3e50;
                margin-bottom: 10px;
            }
            
            .metric-value {
                font-size: 2rem;
                font-weight: bold;
                color: #3498db;
            }
            
            .recommendations {
                background: #fff3cd;
                border: 2px solid #ffeaa7;
                border-radius: 10px;
                padding: 20px;
            }
            
            .recommendations h3 {
                color: #856404;
                margin-bottom: 15px;
            }
            
            .detailed-metrics {
                margin: 30px 0;
            }
            
            .metric-section {
                background: white;
                border: 2px solid #e9ecef;
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.05);
            }
            
            .metric-section-title {
                color: #2c3e50;
                margin-bottom: 15px;
                font-size: 1.2rem;
                border-bottom: 2px solid #ecf0f1;
                padding-bottom: 10px;
            }
            
            .metric-details {
                display: flex;
                flex-direction: column;
                gap: 15px;
            }
            
            .metric-detail-item {
                display: flex;
                align-items: center;
                gap: 15px;
                padding: 10px;
                background: #f8f9fa;
                border-radius: 8px;
            }
            
            .metric-detail-name {
                flex: 1;
                font-weight: 600;
                color: #2c3e50;
            }
            
            .metric-detail-value {
                font-weight: bold;
                color: #3498db;
                min-width: 60px;
                text-align: right;
            }
            
            .metric-detail-bar {
                flex: 2;
                height: 20px;
                background: #ecf0f1;
                border-radius: 10px;
                overflow: hidden;
                position: relative;
            }
            
            .metric-detail-fill {
                height: 100%;
                border-radius: 10px;
                transition: width 0.5s ease;
                position: relative;
            }
            
            .metric-detail-fill::after {
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,0.3) 50%, transparent 100%);
                animation: shimmer 2s infinite;
            }
            
            @keyframes shimmer {
                0% { transform: translateX(-100%); }
                100% { transform: translateX(100%); }
            }
            
            .recommendation-item {
                background: white;
                border-left: 4px solid #f39c12;
                padding: 15px;
                margin-bottom: 10px;
                border-radius: 5px;
            }
            
            .recommendation-category {
                font-weight: 600;
                color: #e67e22;
                font-size: 0.9rem;
            }
            
            .recommendation-text {
                margin-top: 5px;
                color: #2c3e50;
            }
            
            .error {
                background: #f8d7da;
                border: 2px solid #f5c6cb;
                color: #721c24;
                padding: 20px;
                border-radius: 10px;
                margin-top: 20px;
            }
            
            @media (max-width: 768px) {
                .header h1 {
                    font-size: 2rem;
                }
                
                .main-content {
                    padding: 20px;
                }
                
                .metrics-grid {
                    grid-template-columns: 1fr;
                }
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>Оцінка доступності вебсайтів</h1>
                <p>Інструмент для аналізу відповідності вебресурсів стандартам доступності ISO 25023 та WCAG</p>
            </div>
            
            <div class="main-content">
                <form class="url-form" id="evaluationForm">
                    <div class="form-group">
                        <label for="url">URL адреса вебсайту для аналізу:</label>
                        <input 
                            type="url" 
                            id="url" 
                            name="url" 
                            placeholder="https://example.com" 
                            required
                            aria-describedby="url-help"
                        >
                        <small id="url-help" style="color: #666; margin-top: 5px; display: block;">
                            Введіть повну URL адресу включно з протоколом (http:// або https://)
                        </small>
                    </div>
                    
                    <button type="submit" class="btn" id="analyzeBtn">
                        Проаналізувати доступність
                    </button>
                </form>
                
                <div class="loading" id="loading">
                    <div class="spinner"></div>
                    <p>Аналізуємо доступність вебсайту...</p>
                    <p style="font-size: 0.9rem; color: #666; margin-top: 10px;">
                        Це може зайняти кілька хвилин
                    </p>
                </div>
                
                <div class="results" id="results">
                    <!-- Результати будуть вставлені тут через JavaScript -->
                </div>
            </div>
        </div>
        
        <script>
            // Додаємо обробник після завантаження DOM
            document.addEventListener('DOMContentLoaded', function() {
                console.log('DOM завантажено, додаємо обробники подій');
                
                const form = document.getElementById('evaluationForm');
                const urlInput = document.getElementById('url');
                const loadingDiv = document.getElementById('loading');
                const resultsDiv = document.getElementById('results');
                const analyzeBtn = document.getElementById('analyzeBtn');
                
                if (!form) {
                    console.error('Форма не знайдена!');
                    return;
                }
                
                form.addEventListener('submit', async function(e) {
                    console.log('Форма відправлена');
                    e.preventDefault(); // Запобігаємо стандартній відправці форми
                    e.stopPropagation();
                    
                    const url = urlInput.value.trim();
                    console.log('URL для аналізу:', url);
                    
                    if (!url) {
                        alert('Будь ласка, введіть URL адресу');
                        return;
                    }
                    
                    // Показуємо індикатор завантаження
                    loadingDiv.style.display = 'block';
                    resultsDiv.style.display = 'none';
                    analyzeBtn.disabled = true;
                    analyzeBtn.textContent = 'Аналізуємо...';
                    
                    try {
                        console.log('Відправляємо запит до API...');
                        
                        const response = await fetch('/api/evaluate', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'Accept': 'application/json'
                            },
                            body: JSON.stringify({ url: url })
                        });
                        
                        console.log('Отримано відповідь:', response.status);
                        
                        if (!response.ok) {
                            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                        }
                        
                        const data = await response.json();
                        console.log('Дані отримано:', data);
                        
                        if (data.status === 'success') {
                            displayResults(data);
                        } else {
                            displayError(data.error || 'Невідома помилка сервера');
                        }
                        
                    } catch (error) {
                        console.error('Помилка:', error);
                        displayError('Помилка зєднання: ' + error.message);
                    } finally {
                        loadingDiv.style.display = 'none';
                        analyzeBtn.disabled = false;
                        analyzeBtn.textContent = 'Проаналізувати доступність';
                    }
                });
                
                // Додаємо обробник для кнопки
                analyzeBtn.addEventListener('click', function(e) {
                    console.log('Кнопка натиснута');
                    // Форма буде оброблена через submit event
                });
            });
            
            function displayResults(data) {
                const resultsDiv = document.getElementById('results');
                
                // Визначення кольору для скору
                const scoreColor = getScoreColor(data.final_score);
                
                resultsDiv.innerHTML = `
                    <div class="score-card" style="background: linear-gradient(135deg, ${scoreColor} 0%, ${scoreColor}dd 100%);">
                        <div class="score-value">${(data.final_score * 100).toFixed(1)}%</div>
                        <div class="score-level">${data.quality_level}</div>
                        <div class="score-description">${data.quality_description}</div>
                        <div style="margin-top: 15px; font-size: 0.9rem; opacity: 0.9;">
                            Проаналізовано: ${data.url}
                        </div>
                    </div>
                    
                    <div class="detailed-metrics">
                        <h3 style="margin-bottom: 20px; color: #2c3e50;">Детальний звіт по метриках</h3>
                        
                        <!-- Перцептивність -->
                        <div class="metric-section">
                            <h4 class="metric-section-title">
                                🔍 Перцептивність (${(data.subscores.perceptibility * 100).toFixed(1)}%)
                            </h4>
                            <div class="metric-details">
                                <div class="metric-detail-item">
                                    <span class="metric-detail-name">Альтернативний текст:</span>
                                    <span class="metric-detail-value">${(data.metrics.alt_text * 100).toFixed(1)}%</span>
                                    <div class="metric-detail-bar">
                                        <div class="metric-detail-fill" style="width: ${data.metrics.alt_text * 100}%; background: ${getScoreColor(data.metrics.alt_text)};"></div>
                                    </div>
                                </div>
                                <div class="metric-detail-item">
                                    <span class="metric-detail-name">Контрастність тексту:</span>
                                    <span class="metric-detail-value">${(data.metrics.contrast * 100).toFixed(1)}%</span>
                                    <div class="metric-detail-bar">
                                        <div class="metric-detail-fill" style="width: ${data.metrics.contrast * 100}%; background: ${getScoreColor(data.metrics.contrast)};"></div>
                                    </div>
                                </div>
                                <div class="metric-detail-item">
                                    <span class="metric-detail-name">Доступність медіа:</span>
                                    <span class="metric-detail-value">${(data.metrics.media_accessibility * 100).toFixed(1)}%</span>
                                    <div class="metric-detail-bar">
                                        <div class="metric-detail-fill" style="width: ${data.metrics.media_accessibility * 100}%; background: ${getScoreColor(data.metrics.media_accessibility)};"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Керованість -->
                        <div class="metric-section">
                            <h4 class="metric-section-title">
                                ⌨️ Керованість (${(data.subscores.operability * 100).toFixed(1)}%)
                            </h4>
                            <div class="metric-details">
                                <div class="metric-detail-item">
                                    <span class="metric-detail-name">Клавіатурна навігація:</span>
                                    <span class="metric-detail-value">${(data.metrics.keyboard_navigation * 100).toFixed(1)}%</span>
                                    <div class="metric-detail-bar">
                                        <div class="metric-detail-fill" style="width: ${data.metrics.keyboard_navigation * 100}%; background: ${getScoreColor(data.metrics.keyboard_navigation)};"></div>
                                    </div>
                                </div>
                                <div class="metric-detail-item">
                                    <span class="metric-detail-name">Структурована навігація:</span>
                                    <span class="metric-detail-value">${(data.metrics.structured_navigation * 100).toFixed(1)}%</span>
                                    <div class="metric-detail-bar">
                                        <div class="metric-detail-fill" style="width: ${data.metrics.structured_navigation * 100}%; background: ${getScoreColor(data.metrics.structured_navigation)};"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Зрозумілість -->
                        <div class="metric-section">
                            <h4 class="metric-section-title">
                                💡 Зрозумілість (${(data.subscores.understandability * 100).toFixed(1)}%)
                            </h4>
                            <div class="metric-details">
                                <div class="metric-detail-item">
                                    <span class="metric-detail-name">Зрозумілі інструкції:</span>
                                    <span class="metric-detail-value">${(data.metrics.instruction_clarity * 100).toFixed(1)}%</span>
                                    <div class="metric-detail-bar">
                                        <div class="metric-detail-fill" style="width: ${data.metrics.instruction_clarity * 100}%; background: ${getScoreColor(data.metrics.instruction_clarity)};"></div>
                                    </div>
                                </div>
                                <div class="metric-detail-item">
                                    <span class="metric-detail-name">Допомога при введенні:</span>
                                    <span class="metric-detail-value">${(data.metrics.input_assistance * 100).toFixed(1)}%</span>
                                    <div class="metric-detail-bar">
                                        <div class="metric-detail-fill" style="width: ${data.metrics.input_assistance * 100}%; background: ${getScoreColor(data.metrics.input_assistance)};"></div>
                                    </div>
                                </div>
                                <div class="metric-detail-item">
                                    <span class="metric-detail-name">Підтримка помилок:</span>
                                    <span class="metric-detail-value">${(data.metrics.error_support * 100).toFixed(1)}%</span>
                                    <div class="metric-detail-bar">
                                        <div class="metric-detail-fill" style="width: ${data.metrics.error_support * 100}%; background: ${getScoreColor(data.metrics.error_support)};"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Локалізація -->
                        <div class="metric-section">
                            <h4 class="metric-section-title">
                                🌍 Локалізація (${(data.subscores.localization * 100).toFixed(1)}%)
                            </h4>
                            <div class="metric-details">
                                <div class="metric-detail-item">
                                    <span class="metric-detail-name">Багатомовність:</span>
                                    <span class="metric-detail-value">${(data.metrics.localization * 100).toFixed(1)}%</span>
                                    <div class="metric-detail-bar">
                                        <div class="metric-detail-fill" style="width: ${data.metrics.localization * 100}%; background: ${getScoreColor(data.metrics.localization)};"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    ${data.recommendations.length > 0 ? `
                        <div class="recommendations">
                            <h3>💡 Рекомендації для покращення</h3>
                            ${data.recommendations.map(rec => `
                                <div class="recommendation-item">
                                    <div class="recommendation-category">${rec.category} - ${rec.priority} пріоритет</div>
                                    <div class="recommendation-text">${rec.recommendation}</div>
                                    <small style="color: #666;">WCAG: ${rec.wcag_reference}</small>
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}
                `;
                
                resultsDiv.style.display = 'block';
            }
            
            function displayError(errorMessage) {
                const resultsDiv = document.getElementById('results');
                resultsDiv.innerHTML = `
                    <div class="error">
                        <h3>Помилка аналізу</h3>
                        <p>${errorMessage}</p>
                        <p style="margin-top: 10px; font-size: 0.9rem;">
                            Перевірте правильність URL адреси та спробуйте ще раз.
                        </p>
                    </div>
                `;
                resultsDiv.style.display = 'block';
            }
            
            function getScoreColor(score) {
                if (score >= 0.618) return '#27ae60';  // Відмінно - зелений
                if (score >= 0.382) return '#3498db';  // Добре - синій
                if (score >= 0.236) return '#f39c12';  // Задовільно - помаранчевий
                if (score >= 0.146) return '#e74c3c';  // Погано - червоний
                return '#95a5a6';  // Дуже погано - сірий
            }
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)


@app.post("/api/evaluate", response_model=EvaluationResponse)
async def evaluate_accessibility(request: URLRequest):
    """
    Аналіз доступності вебсайту
    
    Args:
        request: Запит з URL для аналізу
        
    Returns:
        Результати аналізу доступності
    """
    
    print(f"🔍 Отримано запит на аналіз: {request.url}")
    
    try:
        # Виконання аналізу
        print(f"📊 Початок аналізу для {request.url}")
        result = await evaluator.evaluate_accessibility(str(request.url))
        
        if result['status'] == 'error':
            print(f"❌ Помилка аналізу: {result['error']}")
            raise HTTPException(status_code=400, detail=result['error'])
        
        # Додавання рівня якості
        try:
            from accessibility_evaluator.core.utils.calculator import ScoreCalculator
        except ImportError:
            from core.utils.calculator import ScoreCalculator
        calculator = ScoreCalculator(evaluator.weights, evaluator.metric_weights)
        
        quality_level = calculator.get_quality_level(result['final_score'])
        quality_description = calculator.get_quality_description(result['final_score'])
        
        print(f"✅ Аналіз завершено. Скор: {result['final_score']:.3f}")
        
        return EvaluationResponse(
            url=result['url'],
            metrics=result['metrics'],
            subscores=result['subscores'],
            final_score=result['final_score'],
            quality_level=quality_level,
            quality_description=quality_description,
            recommendations=result['recommendations'],
            status=result['status']
        )
        
    except HTTPException:
        # Перепередаємо HTTP помилки як є
        raise
    except Exception as e:
        print(f"❌ Критична помилка сервера: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Помилка сервера: {str(e)}")


@app.get("/api/health")
async def health_check():
    """Перевірка стану сервера"""
    return {"status": "healthy", "message": "Сервер працює нормально"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)