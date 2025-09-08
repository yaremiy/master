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


class HTMLRequest(BaseModel):
    """Модель запиту для аналізу HTML контенту"""
    html_content: str
    base_url: str = "http://localhost"  # Базовий URL для відносних посилань
    title: str = "HTML Document"  # Заголовок документа


class EvaluationResponse(BaseModel):
    """Модель відповіді з результатами аналізу"""
    url: str
    metrics: Dict[str, float]
    subscores: Dict[str, float]
    final_score: float
    quality_level: str
    quality_description: str
    recommendations: list
    detailed_analysis: Dict[str, Any] = {}  # Додаємо детальний аналіз
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
            
            .tabs {
                display: flex;
                margin-bottom: 0;
                border-bottom: 2px solid #e9ecef;
            }
            
            .tab-button {
                background: #f8f9fa;
                border: 2px solid #e9ecef;
                border-bottom: none;
                padding: 15px 25px;
                cursor: pointer;
                font-size: 16px;
                font-weight: 600;
                color: #666;
                border-radius: 10px 10px 0 0;
                margin-right: 5px;
                transition: all 0.3s;
            }
            
            .tab-button:hover {
                background: #e9ecef;
                color: #333;
            }
            
            .tab-button.active {
                background: #3498db;
                color: white;
                border-color: #3498db;
            }
            
            .tab-content {
                display: none;
            }
            
            .tab-content.active {
                display: block;
            }
            
            .url-form {
                background: #f8f9fa;
                padding: 30px;
                border-radius: 0 10px 10px 10px;
                margin-bottom: 30px;
                border: 2px solid #e9ecef;
                border-top: none;
            }
            
            textarea {
                width: 100%;
                padding: 15px;
                border: 2px solid #ddd;
                border-radius: 8px;
                font-size: 14px;
                font-family: 'Courier New', monospace;
                transition: border-color 0.3s;
                resize: vertical;
                min-height: 200px;
            }
            
            textarea:focus {
                outline: none;
                border-color: #3498db;
                box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
            }
            
            input[type="file"] {
                width: 100%;
                padding: 15px;
                border: 2px dashed #ddd;
                border-radius: 8px;
                font-size: 16px;
                background: #f8f9fa;
                cursor: pointer;
                transition: all 0.3s;
            }
            
            input[type="file"]:hover {
                border-color: #3498db;
                background: #e3f2fd;
            }
            
            input[type="file"]:focus {
                outline: none;
                border-color: #3498db;
                box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
            }
            
            .file-drop-zone {
                border: 2px dashed #ddd;
                border-radius: 8px;
                padding: 40px;
                text-align: center;
                background: #f8f9fa;
                cursor: pointer;
                transition: all 0.3s;
            }
            
            .file-drop-zone:hover {
                border-color: #3498db;
                background: #e3f2fd;
            }
            
            .file-drop-zone.dragover {
                border-color: #27ae60;
                background: #e8f5e8;
            }
            
            /* Accordion стилі */
            .accordion {
                margin-top: 10px;
            }
            
            .accordion-header {
                background: #f8f9fa;
                border: 1px solid #dee2e6;
                border-radius: 5px;
                padding: 15px;
                cursor: pointer;
                display: flex;
                justify-content: space-between;
                align-items: center;
                transition: background-color 0.3s;
            }
            
            .accordion-header:hover {
                background: #e9ecef;
            }
            
            .accordion-header.active {
                background: #e3f2fd;
                border-color: #3498db;
            }
            
            .accordion-toggle {
                font-size: 18px;
                font-weight: bold;
                color: #666;
                transition: transform 0.3s;
            }
            
            .accordion-header.active .accordion-toggle {
                transform: rotate(90deg);
                color: #3498db;
            }
            
            .accordion-content {
                display: none;
                border: 1px solid #dee2e6;
                border-top: none;
                border-radius: 0 0 5px 5px;
                padding: 20px;
                background: white;
            }
            
            .accordion-content.active {
                display: block;
            }
            
            .element-list {
                margin-top: 15px;
            }
            
            .element-item {
                background: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 5px;
                padding: 15px;
                margin-bottom: 10px;
            }
            
            .element-item.problematic {
                border-left: 4px solid #e74c3c;
                background: #fdf2f2;
            }
            
            .element-item.correct {
                border-left: 4px solid #27ae60;
                background: #f0f9f0;
            }
            
            .element-selector {
                font-family: 'Courier New', monospace;
                font-size: 14px;
                color: #2c3e50;
                font-weight: bold;
                margin-bottom: 8px;
            }
            
            .element-html {
                font-family: 'Courier New', monospace;
                font-size: 12px;
                background: #f1f3f4;
                padding: 8px;
                border-radius: 3px;
                margin: 8px 0;
                overflow-x: auto;
                white-space: pre-wrap;
                word-break: break-all;
            }
            
            .element-issue {
                color: #e74c3c;
                font-size: 14px;
                margin-top: 8px;
            }
            
            .element-status {
                color: #27ae60;
                font-size: 14px;
                margin-top: 8px;
            }
            
            .contrast-info {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 10px;
                margin-top: 10px;
            }
            
            .contrast-detail {
                background: #f8f9fa;
                padding: 8px;
                border-radius: 3px;
                font-size: 12px;
            }
            
            .color-swatch {
                display: inline-block;
                width: 20px;
                height: 20px;
                border-radius: 3px;
                border: 1px solid #ccc;
                margin-left: 5px;
                vertical-align: middle;
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
                <!-- Вкладки для вибору типу аналізу -->
                <div class="tabs">
                    <button class="tab-button active" onclick="switchTab('url')">🌐 Аналіз URL</button>
                    <button class="tab-button" onclick="switchTab('html')">📄 Аналіз HTML</button>
                </div>
                
                <!-- Форма для аналізу URL -->
                <form class="url-form tab-content active" id="urlForm" data-tab="url">
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
                    
                    <button type="submit" class="btn" id="analyzeUrlBtn">
                        Проаналізувати доступність URL
                    </button>
                </form>
                
                <!-- Форма для аналізу HTML -->
                <form class="url-form tab-content" id="htmlForm" data-tab="html" enctype="multipart/form-data">
                    <div class="form-group">
                        <label for="htmlFile">Завантажити HTML файл:</label>
                        <input 
                            type="file" 
                            id="htmlFile" 
                            name="htmlFile" 
                            accept=".html,.htm"
                            required
                            aria-describedby="html-help"
                        >
                        <small id="html-help" style="color: #666; margin-top: 5px; display: block;">
                            Виберіть HTML файл (.html або .htm) для аналізу доступності
                        </small>
                        
                        <!-- Попередній перегляд файлу -->
                        <div id="filePreview" style="display: none; margin-top: 15px;">
                            <h4>Попередній перегляд:</h4>
                            <div id="fileInfo" style="background: #f8f9fa; padding: 10px; border-radius: 5px; margin-bottom: 10px;"></div>
                            <textarea 
                                id="htmlContent" 
                                readonly
                                style="height: 200px; font-size: 12px;"
                            ></textarea>
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label for="baseUrl">Базовий URL (опціонально):</label>
                        <input 
                            type="url" 
                            id="baseUrl" 
                            name="baseUrl" 
                            placeholder="http://localhost" 
                            value="http://localhost"
                            aria-describedby="base-url-help"
                        >
                        <small id="base-url-help" style="color: #666; margin-top: 5px; display: block;">
                            Базовий URL для відносних посилань у HTML
                        </small>
                    </div>
                    
                    <div class="form-group">
                        <label for="pageTitle">Заголовок сторінки (опціонально):</label>
                        <input 
                            type="text" 
                            id="pageTitle" 
                            name="pageTitle" 
                            placeholder="HTML Document" 
                            value="HTML Document"
                            aria-describedby="title-help"
                        >
                        <small id="title-help" style="color: #666; margin-top: 5px; display: block;">
                            Заголовок для ідентифікації документа в звіті
                        </small>
                    </div>
                    
                    <button type="submit" class="btn" id="analyzeHtmlBtn">
                        Проаналізувати HTML контент
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
            // Функція для перемикання вкладок
            function switchTab(tabName) {
                // Приховуємо всі вкладки
                const tabContents = document.querySelectorAll('.tab-content');
                tabContents.forEach(tab => {
                    tab.classList.remove('active');
                });
                
                // Деактивуємо всі кнопки вкладок
                const tabButtons = document.querySelectorAll('.tab-button');
                tabButtons.forEach(button => {
                    button.classList.remove('active');
                });
                
                // Показуємо активну вкладку
                const activeTab = document.querySelector(`[data-tab="${tabName}"]`);
                if (activeTab) {
                    activeTab.classList.add('active');
                }
                
                // Активуємо відповідну кнопку
                event.target.classList.add('active');
                
                console.log('Перемкнуто на вкладку:', tabName);
            }
            
            // Додаємо обробник після завантаження DOM
            document.addEventListener('DOMContentLoaded', function() {
                console.log('DOM завантажено, додаємо обробники подій');
                
                const urlForm = document.getElementById('urlForm');
                const htmlForm = document.getElementById('htmlForm');
                const loadingDiv = document.getElementById('loading');
                const resultsDiv = document.getElementById('results');
                
                // Обробник для URL форми
                if (urlForm) {
                    urlForm.addEventListener('submit', async function(e) {
                        e.preventDefault();
                        console.log('URL форма відправлена');
                        
                        const urlInput = document.getElementById('url');
                        const analyzeBtn = document.getElementById('analyzeUrlBtn');
                        const url = urlInput.value.trim();
                        
                        if (!url) {
                            alert('Будь ласка, введіть URL адресу');
                            return;
                        }
                        
                        await performAnalysis('/api/evaluate', { url: url }, analyzeBtn, 'Проаналізувати доступність URL');
                    });
                }
                
                // Обробник для HTML форми
                if (htmlForm) {
                    const htmlFileInput = document.getElementById('htmlFile');
                    const filePreview = document.getElementById('filePreview');
                    const fileInfo = document.getElementById('fileInfo');
                    const htmlContent = document.getElementById('htmlContent');
                    
                    // Обробник зміни файлу
                    htmlFileInput.addEventListener('change', function(e) {
                        const file = e.target.files[0];
                        if (file) {
                            handleFileSelect(file);
                        }
                    });
                    
                    // Функція обробки вибраного файлу
                    function handleFileSelect(file) {
                        // Перевірка типу файлу
                        if (!file.name.match(/\.(html|htm)$/i)) {
                            alert('Будь ласка, виберіть HTML файл (.html або .htm)');
                            return;
                        }
                        
                        // Показуємо інформацію про файл
                        fileInfo.innerHTML = `
                            <strong>Файл:</strong> ${file.name}<br>
                            <strong>Розмір:</strong> ${(file.size / 1024).toFixed(2)} KB<br>
                            <strong>Тип:</strong> ${file.type || 'text/html'}
                        `;
                        
                        // Читаємо вміст файлу
                        const reader = new FileReader();
                        reader.onload = function(e) {
                            const content = e.target.result;
                            htmlContent.value = content;
                            filePreview.style.display = 'block';
                            
                            // Автоматично заповнюємо заголовок з HTML
                            const titleMatch = content.match(/<title[^>]*>([^<]+)<\/title>/i);
                            if (titleMatch) {
                                document.getElementById('pageTitle').value = titleMatch[1].trim();
                            }
                        };
                        reader.readAsText(file);
                    }
                    
                    htmlForm.addEventListener('submit', async function(e) {
                        e.preventDefault();
                        console.log('HTML форма відправлена');
                        
                        const htmlContentInput = document.getElementById('htmlContent');
                        const baseUrlInput = document.getElementById('baseUrl');
                        const pageTitleInput = document.getElementById('pageTitle');
                        const analyzeBtn = document.getElementById('analyzeHtmlBtn');
                        
                        const htmlContentValue = htmlContentInput.value.trim();
                        const baseUrl = baseUrlInput.value.trim() || 'http://localhost';
                        const title = pageTitleInput.value.trim() || 'HTML Document';
                        
                        if (!htmlContentValue) {
                            alert('Будь ласка, завантажте HTML файл');
                            return;
                        }
                        
                        await performAnalysis('/api/evaluate-html', {
                            html_content: htmlContentValue,
                            base_url: baseUrl,
                            title: title
                        }, analyzeBtn, 'Проаналізувати HTML контент');
                    });
                }
                
                // Універсальна функція для виконання аналізу
                async function performAnalysis(endpoint, data, button, originalButtonText) {
                    // Показуємо індикатор завантаження
                    loadingDiv.style.display = 'block';
                    resultsDiv.style.display = 'none';
                    button.disabled = true;
                    button.textContent = 'Аналізуємо...';
                    
                    try {
                        console.log('Відправляємо запит до API:', endpoint);
                        
                        const response = await fetch(endpoint, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                                'Accept': 'application/json'
                            },
                            body: JSON.stringify(data)
                        });
                        
                        console.log('Отримано відповідь:', response.status);
                        
                        if (!response.ok) {
                            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
                        }
                        
                        const result = await response.json();
                        console.log('Дані отримано:', result);
                        
                        if (result.status === 'success') {
                            displayResults(result);
                        } else {
                            displayError(result.error || 'Невідома помилка сервера');
                        }
                        
                    } catch (error) {
                        console.error('Помилка:', error);
                        displayError('Помилка зєднання: ' + error.message);
                    } finally {
                        loadingDiv.style.display = 'none';
                        button.disabled = false;
                        button.textContent = originalButtonText;
                    }
                }
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
                        
                        <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 6px; padding: 15px; margin-bottom: 25px; font-size: 14px;">
                            <strong>💡 Фокус звіту:</strong> Нижче показані тільки елементи, які потребують покращення. 
                            Успішно перевірені елементи підраховані в загальному скорі та відображені в підсумку.
                        </div>
                        
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
                                    <div class="accordion">
                                        <div class="accordion-header" onclick="toggleAccordion(this)">
                                            <span>Детальний аналіз зображень</span>
                                            <span class="accordion-toggle">▶</span>
                                        </div>
                                        <div class="accordion-content">
                                            ${generateAltTextDetails(data.detailed_analysis?.alt_text)}
                                        </div>
                                    </div>
                                </div>
                                <div class="metric-detail-item">
                                    <span class="metric-detail-name">Контрастність тексту:</span>
                                    <span class="metric-detail-value">${(data.metrics.contrast * 100).toFixed(1)}%</span>
                                    <div class="metric-detail-bar">
                                        <div class="metric-detail-fill" style="width: ${data.metrics.contrast * 100}%; background: ${getScoreColor(data.metrics.contrast)};"></div>
                                    </div>
                                    <div class="accordion">
                                        <div class="accordion-header" onclick="toggleAccordion(this)">
                                            <span>Детальний аналіз контрасту</span>
                                            <span class="accordion-toggle">▶</span>
                                        </div>
                                        <div class="accordion-content">
                                            ${generateContrastDetails(data.detailed_analysis?.contrast)}
                                        </div>
                                    </div>
                                </div>
                                <div class="metric-detail-item">
                                    <span class="metric-detail-name">Доступність медіа:</span>
                                    <span class="metric-detail-value">${(data.metrics.media_accessibility * 100).toFixed(1)}%</span>
                                    <div class="metric-detail-bar">
                                        <div class="metric-detail-fill" style="width: ${data.metrics.media_accessibility * 100}%; background: ${getScoreColor(data.metrics.media_accessibility)};"></div>
                                    </div>
                                    <div class="accordion">
                                        <div class="accordion-header" onclick="toggleAccordion(this)">
                                            <span>Детальний аналіз медіа елементів</span>
                                            <span class="accordion-toggle">▶</span>
                                        </div>
                                        <div class="accordion-content">
                                            ${generateMediaDetails(data.detailed_analysis?.media_accessibility)}
                                        </div>
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
                                    <div class="accordion">
                                        <div class="accordion-header" onclick="toggleAccordion(this)">
                                            <span>Детальний аналіз клавіатурної навігації</span>
                                            <span class="accordion-toggle">▶</span>
                                        </div>
                                        <div class="accordion-content">
                                            ${generateKeyboardDetails(data.detailed_analysis?.keyboard_navigation)}
                                        </div>
                                    </div>
                                </div>
                                <div class="metric-detail-item">
                                    <span class="metric-detail-name">Структурована навігація:</span>
                                    <span class="metric-detail-value">${(data.metrics.structured_navigation * 100).toFixed(1)}%</span>
                                    <div class="metric-detail-bar">
                                        <div class="metric-detail-fill" style="width: ${data.metrics.structured_navigation * 100}%; background: ${getScoreColor(data.metrics.structured_navigation)};"></div>
                                    </div>
                                    <div class="accordion">
                                        <div class="accordion-header" onclick="toggleAccordion(this)">
                                            <span>Детальний аналіз заголовків</span>
                                            <span class="accordion-toggle">▶</span>
                                        </div>
                                        <div class="accordion-content">
                                            ${generateHeadingsDetails(data.detailed_analysis?.structured_navigation)}
                                        </div>
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
                                    <div class="accordion">
                                        <div class="accordion-header" onclick="toggleAccordion(this)">
                                            <span>Детальний аналіз інструкцій</span>
                                            <span class="accordion-toggle">▶</span>
                                        </div>
                                        <div class="accordion-content">
                                            ${generateInstructionsDetails(data.detailed_analysis?.instruction_clarity)}
                                        </div>
                                    </div>
                                </div>
                                <div class="metric-detail-item">
                                    <span class="metric-detail-name">Допомога при введенні:</span>
                                    <span class="metric-detail-value">${(data.metrics.input_assistance * 100).toFixed(1)}%</span>
                                    <div class="metric-detail-bar">
                                        <div class="metric-detail-fill" style="width: ${data.metrics.input_assistance * 100}%; background: ${getScoreColor(data.metrics.input_assistance)};"></div>
                                    </div>
                                    <div class="accordion">
                                        <div class="accordion-header" onclick="toggleAccordion(this)">
                                            <span>Детальний аналіз полів вводу</span>
                                            <span class="accordion-toggle">▶</span>
                                        </div>
                                        <div class="accordion-content">
                                            ${generateInputAssistanceDetails(data.detailed_analysis?.input_assistance)}
                                        </div>
                                    </div>
                                </div>
                                <div class="metric-detail-item">
                                    <span class="metric-detail-name">Підтримка помилок:</span>
                                    <span class="metric-detail-value">${(data.metrics.error_support * 100).toFixed(1)}%</span>
                                    <div class="metric-detail-bar">
                                        <div class="metric-detail-fill" style="width: ${data.metrics.error_support * 100}%; background: ${getScoreColor(data.metrics.error_support)};"></div>
                                    </div>
                                    <div class="accordion">
                                        <div class="accordion-header" onclick="toggleAccordion(this)">
                                            <span>Детальний аналіз обробки помилок</span>
                                            <span class="accordion-toggle">▶</span>
                                        </div>
                                        <div class="accordion-content">
                                            ${generateErrorSupportDetails(data.detailed_analysis?.error_support)}
                                        </div>
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
                                    <div class="accordion">
                                        <div class="accordion-header" onclick="toggleAccordion(this)">
                                            <span>Детальний аналіз локалізації</span>
                                            <span class="accordion-toggle">▶</span>
                                        </div>
                                        <div class="accordion-content">
                                            ${generateLocalizationDetails(data.detailed_analysis?.localization)}
                                        </div>
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
            
            // Функція для перемикання accordion
            function toggleAccordion(header) {
                const content = header.nextElementSibling;
                const isActive = header.classList.contains('active');
                
                if (isActive) {
                    header.classList.remove('active');
                    content.classList.remove('active');
                } else {
                    header.classList.add('active');
                    content.classList.add('active');
                }
            }
            
            // Генерація детального аналізу alt-text (тільки проблемні елементи)
            function generateAltTextDetails(details) {
                if (!details) return '<p>Детальна інформація недоступна</p>';
                
                let html = `
                    <div class="score-explanation">
                        <strong>${details.score_explanation}</strong>
                    </div>
                    <div style="background: #e3f2fd; border: 1px solid #bbdefb; border-radius: 6px; padding: 12px; margin: 15px 0; font-size: 14px;">
                        <strong>📊 Підсумок:</strong> Успішних зображень: <strong>${details.correct_images_list?.length || 0}</strong>
                    </div>
                `;
                
                if (details.problematic_images && details.problematic_images.length > 0) {
                    html += `
                        <h4 style="color: #e74c3c; margin-top: 20px;">❌ Зображення для виправлення (${details.problematic_images.length}):</h4>
                        <div class="element-list">
                    `;
                    
                    details.problematic_images.forEach(img => {
                        html += `
                            <div class="element-item problematic">
                                <div class="element-selector">${img.selector}</div>
                                <div class="element-html">${escapeHtml(img.html)}</div>
                                <div class="element-issue"><strong>Проблема:</strong> ${img.issue}</div>
                            </div>
                        `;
                    });
                    
                    html += '</div>';
                } else {
                    html += `
                        <div style="background: #e8f5e8; border: 1px solid #c3e6c3; border-radius: 6px; padding: 15px; margin: 15px 0; text-align: center;">
                            <strong style="color: #27ae60;">✅ Відмінно! Всі зображення мають правильний альтернативний текст</strong>
                        </div>
                    `;
                }
                
                return html;
            }
            
            // Генерація детального аналізу контрасту (тільки проблемні елементи)
            function generateContrastDetails(details) {
                if (!details) return '<p>Детальна інформація недоступна</p>';
                
                let html = `
                    <div class="score-explanation">
                        <strong>${details.score_explanation}</strong>
                    </div>
                    <div style="background: #e3f2fd; border: 1px solid #bbdefb; border-radius: 6px; padding: 12px; margin: 15px 0; font-size: 14px;">
                        <strong>📊 Підсумок:</strong> Елементів з правильним контрастом: <strong>${details.correct_elements_list?.length || 0}</strong>
                    </div>
                `;
                
                if (details.problematic_elements && details.problematic_elements.length > 0) {
                    html += `
                        <h4 style="color: #e74c3c; margin-top: 20px;">❌ Елементи для покращення контрасту (${details.problematic_elements.length}):</h4>
                        <div class="element-list">
                    `;
                    
                    details.problematic_elements.forEach(elem => {
                        html += `
                            <div class="element-item problematic">
                                <div class="element-selector">${elem.selector}</div>
                                <div class="element-html">${escapeHtml(elem.html)}</div>
                                <div class="contrast-info">
                                    <div class="contrast-detail">
                                        <strong>Поточний контраст:</strong> ${elem.contrast_ratio}
                                    </div>
                                    <div class="contrast-detail">
                                        <strong>Необхідний:</strong> ${elem.required_ratio}
                                    </div>
                                    <div class="contrast-detail">
                                        <strong>Колір тексту:</strong> ${elem.foreground}
                                        <span class="color-swatch" style="background-color: ${elem.foreground}"></span>
                                    </div>
                                    <div class="contrast-detail">
                                        <strong>Колір фону:</strong> ${elem.background}
                                        <span class="color-swatch" style="background-color: ${elem.background}"></span>
                                    </div>
                                </div>
                            </div>
                        `;
                    });
                    
                    html += '</div>';
                } else {
                    html += `
                        <div style="background: #e8f5e8; border: 1px solid #c3e6c3; border-radius: 6px; padding: 15px; margin: 15px 0; text-align: center;">
                            <strong style="color: #27ae60;">✅ Відмінно! Всі елементи мають достатній контраст</strong>
                        </div>
                    `;
                }
                
                return html;
            }
            
            // Генерація детального аналізу заголовків (тільки проблемні елементи)
            function generateHeadingsDetails(details) {
                if (!details) return '<p>Детальна інформація недоступна</p>';
                
                let html = `
                    <div class="score-explanation">
                        <strong>${details.score_explanation}</strong>
                    </div>
                    <div style="background: #e3f2fd; border: 1px solid #bbdefb; border-radius: 6px; padding: 12px; margin: 15px 0; font-size: 14px;">
                        <strong>📊 Підсумок:</strong> Правильних заголовків: <strong>${details.correct_headings_list?.length || 0}</strong>
                    </div>
                `;
                
                if (details.problematic_headings && details.problematic_headings.length > 0) {
                    html += `
                        <h4 style="color: #e74c3c; margin-top: 20px;">❌ Заголовки для виправлення (${details.problematic_headings.length}):</h4>
                        <div class="element-list">
                    `;
                    
                    details.problematic_headings.forEach(heading => {
                        html += `
                            <div class="element-item problematic">
                                <div class="element-selector">${heading.selector}</div>
                                <div class="element-html">${escapeHtml(heading.html)}</div>
                                <div class="element-issue"><strong>Правило:</strong> ${heading.rule}</div>
                                <div class="element-issue"><strong>Проблема:</strong> ${heading.issue}</div>
                            </div>
                        `;
                    });
                    
                    html += '</div>';
                } else {
                    html += `
                        <div style="background: #e8f5e8; border: 1px solid #c3e6c3; border-radius: 6px; padding: 15px; margin: 15px 0; text-align: center;">
                            <strong style="color: #27ae60;">✅ Відмінно! Всі заголовки мають правильну ієрархію</strong>
                        </div>
                    `;
                }
                
                return html;
            }
            
            // Генерація детального аналізу клавіатурної навігації
            function generateKeyboardDetails(details) {
                if (!details) return '<p>Детальна інформація недоступна</p>';
                
                let html = `
                    <div class="score-explanation">
                        <strong>${details.score_explanation}</strong>
                    </div>
                `;
                
                if (details.total_elements > 0) {
                    html += `
                        <div style="margin-top: 15px;">
                            <p><strong>Всього елементів:</strong> ${details.total_elements}</p>
                            <p><strong>Доступних з клавіатури:</strong> ${details.accessible_elements}</p>
                        </div>
                    `;
                    
                    // Правильні елементи приховано для фокусу на проблемах
                    if (details.accessible_elements_list && details.accessible_elements_list.length > 0) {
                        html += `
                            <div style="background: #e8f5e8; border: 1px solid #c3e6c3; border-radius: 6px; padding: 12px; margin: 15px 0; font-size: 14px;">
                                <strong>✅ Доступних елементів з клавіатури: ${details.accessible_elements_list.length}</strong>
                            </div>
                        `;
                    }
                    
                    if (details.problematic_elements && details.problematic_elements.length > 0) {
                        html += `
                            <h4 style="color: #e74c3c; margin-top: 20px;">❌ Проблемні елементи (${details.problematic_elements.length}):</h4>
                            <div class="element-list">
                        `;
                        
                        details.problematic_elements.forEach(element => {
                            html += `
                                <div class="element-item problematic">
                                    <div class="element-selector">
                                        <strong>Селектор:</strong> ${element.selector || 'невідомо'}
                                    </div>
                                    <div class="element-html">${escapeHtml(element.html || 'HTML недоступний')}</div>
                                    <div class="element-issue">
                                        <strong>Правило:</strong> ${element.rule || 'невідомо'}
                                    </div>
                                    <div class="element-issue">
                                        <strong>Проблема:</strong> ${element.issue || 'Проблема з клавіатурною навігацією'}
                                    </div>
                                </div>
                            `;
                        });
                        
                        html += '</div>';
                    }
                } else {
                    html += `
                        <p style="color: #666; margin-top: 15px;">
                            Інтерактивні елементи для клавіатурної навігації не знайдено в axe-core результатах.
                            Це може означати, що на сторінці немає елементів, які потребують клавіатурної навігації,
                            або всі елементи є стандартними та доступними за замовчуванням.
                        </p>
                    `;
                }
                
                return html;
            }
            
            // Генерація детального аналізу медіа елементів
            function generateMediaDetails(details) {
                if (!details) return '<p>Детальна інформація недоступна</p>';
                
                let html = `
                    <div class="score-explanation">
                        <strong>${details.score_explanation}</strong>
                    </div>
                `;
                
                if (details.total_media > 0) {
                    html += `
                        <div style="margin-top: 15px;">
                            <p><strong>Всього відео:</strong> ${details.total_media}</p>
                            <p><strong>Доступних:</strong> ${details.accessible_media}</p>
                        </div>
                    `;
                    
                    if (details.accessible_media_list && details.accessible_media_list.length > 0) {
                        html += `
                            <div style="background: #e8f5e8; border: 1px solid #c3e6c3; border-radius: 6px; padding: 12px; margin: 15px 0; font-size: 14px;">
                                <strong>✅ Доступних медіа елементів: ${details.accessible_media_list.length}</strong>
                            </div>
                        `;
                    }
                    
                    if (details.problematic_media && details.problematic_media.length > 0) {
                        html += `
                            <h4 style="color: #e74c3c; margin-top: 20px;">❌ Проблемні відео (${details.problematic_media.length}):</h4>
                            <div class="element-list">
                        `;
                        
                        details.problematic_media.forEach(video => {
                            html += `
                                <div class="element-item problematic">
                                    <div class="element-selector">
                                        <strong>Тип:</strong> ${video.type || 'невідомо'} (${video.platform || 'native'})
                                    </div>
                                    <div class="element-selector">
                                        <strong>Назва:</strong> ${video.title || 'Без назви'}
                                    </div>
                                    <div class="element-html">${escapeHtml(video.html || 'HTML недоступний')}</div>
                                    <div class="element-issue">
                                        <strong>URL:</strong> ${video.src ? video.src.substring(0, 80) + (video.src.length > 80 ? '...' : '') : 'Немає URL'}
                                    </div>
                                    <div class="element-issue">
                                        <strong>Проблема:</strong> ${video.issue || 'Проблема з доступністю медіа'}
                                    </div>
                                </div>
                            `;
                        });
                        
                        html += '</div>';
                    }
                } else {
                    html += `
                        <p style="color: #666; margin-top: 15px;">
                            Відео елементи не знайдено на сторінці. Аналіз доступності медіа включає перевірку 
                            наявності субтитрів, аудіоописів та альтернативних форматів для відео та аудіо контенту.
                        </p>
                    `;
                }
                
                return html;
            }
            
            // Генерація детального аналізу інструкцій
            function generateInstructionsDetails(details) {
                if (!details) return '<p>Детальна інформація недоступна</p>';
                
                let html = `
                    <div class="score-explanation">
                        <strong>${details.score_explanation}</strong>
                    </div>
                `;
                
                if (details.total_instructions > 0) {
                    html += `
                        <div style="margin-top: 15px;">
                            <p><strong>Всього інструкцій знайдено:</strong> ${details.total_instructions}</p>
                            <p><strong>Зрозумілих інструкцій:</strong> ${details.clear_instructions}</p>
                        </div>
                    `;
                    
                    if (details.problematic_instructions && details.problematic_instructions.length > 0) {
                        html += `
                            <h4 style="color: #e74c3c; margin-top: 20px;">❌ Незрозумілі інструкції (${details.problematic_instructions.length}):</h4>
                            <div class="element-list">
                        `;
                        
                        details.problematic_instructions.forEach(instruction => {
                            html += `
                                <div class="element-item problematic">
                                    <div class="element-selector">
                                        <strong>Тип:</strong> ${instruction.element_type || 'невідомо'}
                                    </div>
                                    <div class="element-html">
                                        <strong>Текст:</strong> "${escapeHtml(instruction.text || 'Текст недоступний')}"
                                    </div>
                                    <div class="element-issue">
                                        <strong>Результат оцінки:</strong> ❌ Незрозуміло
                                    </div>
                                    <div class="element-issue">
                                        <strong>Причина:</strong> ${instruction.issue || 'Складна для розуміння'}
                                    </div>
                                </div>
                            `;
                        });
                        
                        html += '</div>';
                    }
                    
                    if (details.clear_instructions_list && details.clear_instructions_list.length > 0) {
                        html += `
                            <h4 style="color: #27ae60; margin-top: 20px;">✅ Зрозумілі інструкції (${details.clear_instructions_list.length}):</h4>
                            <div class="element-list">
                        `;
                        
                        details.clear_instructions_list.forEach(instruction => {
                            html += `
                                <div class="element-item correct">
                                    <div class="element-selector">
                                        <strong>Тип:</strong> ${instruction.element_type || 'невідомо'}
                                    </div>
                                    <div class="element-html">
                                        <strong>Текст:</strong> "${escapeHtml(instruction.text || 'Текст недоступний')}"
                                    </div>
                                    <div class="element-status">
                                        <strong>Результат оцінки:</strong> ✅ Зрозуміло
                                    </div>
                                    <div class="element-status">
                                        <strong>Статус:</strong> ${instruction.status || 'Зрозуміла інструкція'}
                                    </div>
                                </div>
                            `;
                        });
                        
                        html += '</div>';
                    }
                } else {
                    html += `
                        <p style="color: #666; margin-top: 15px;">
                            Аналіз зрозумілості інструкцій використовує textstat бібліотеку для оцінки 
                            читабельності тексту за шкалою Flesch Reading Ease та іншими метриками.
                        </p>
                    `;
                }
                
                return html;
            }
            
            // Генерація детального аналізу полів вводу
            function generateInputAssistanceDetails(details) {
                if (!details) return '<p>Детальна інформація недоступна</p>';
                
                let html = `
                    <div class="score-explanation">
                        <strong>${details.score_explanation}</strong>
                    </div>
                `;
                
                if (details.total_fields > 0) {
                    html += `
                        <div style="margin-top: 15px;">
                            <p><strong>Всього полів:</strong> ${details.total_fields}</p>
                            <p><strong>З допомогою:</strong> ${details.assisted_fields}</p>
                        </div>
                    `;
                    
                    if (details.problematic_fields && details.problematic_fields.length > 0) {
                        html += `
                            <h4 style="color: #e74c3c; margin-top: 20px;">❌ Поля без допомоги (${details.problematic_fields.length}):</h4>
                            <div class="element-list">
                        `;
                        
                        details.problematic_fields.forEach(field => {
                            html += `
                                <div class="element-item problematic">
                                    <div class="element-selector">
                                        <strong>Селектор:</strong> ${field.selector || 'невідомо'}
                                    </div>
                                    <div class="element-html">${escapeHtml(field.html || 'HTML недоступний')}</div>
                                    <div class="element-issue">
                                        <strong>Результат оцінки:</strong> ❌ Без допомоги
                                    </div>
                                    <div class="element-issue">
                                        <strong>Проблема:</strong> ${field.issue || 'Відсутні підказки'}
                                    </div>
                                </div>
                            `;
                        });
                        
                        html += '</div>';
                    }
                    
                    if (details.assisted_fields_list && details.assisted_fields_list.length > 0) {
                        html += `
                            <div style="background: #e8f5e8; border: 1px solid #c3e6c3; border-radius: 6px; padding: 12px; margin: 15px 0; font-size: 14px;">
                                <strong>✅ Полів з допомогою: ${details.assisted_fields_list.length}</strong>
                            </div>
                        `;
                    }
                } else {
                    html += `
                        <p style="color: #666; margin-top: 15px;">
                            Аналіз допомоги при введенні перевіряє наявність placeholder текстів, 
                            autocomplete атрибутів, aria-label та інших підказок для користувачів.
                        </p>
                    `;
                }
                
                return html;
            }
            
            // Генерація детального аналізу підтримки помилок з новою структурою фаз
            function generateErrorSupportDetails(details) {
                if (!details) return '<p>Детальна інформація недоступна</p>';
                
                let html = `
                    <div class="score-explanation">
                        <strong>${details.score_explanation}</strong>
                    </div>
                `;
                
                if (details.total_forms > 0) {
                    html += `
                        <div style="margin-top: 15px;">
                            <p><strong>Всього форм:</strong> ${details.total_forms}</p>
                            <p><strong>Підтримуваних форм:</strong> ${details.supported_forms || 0}</p>
                            <p><strong>Тип аналізу:</strong> ${details.analysis_type === 'hybrid' ? '🔄 Гібридний (статичний + динамічний)' : 
                                                              details.analysis_type === 'static_only' ? '📊 Тільки статичний' : 
                                                              '❓ Невідомий'}</p>
                            ${details.dynamic_tests_count ? `<p><strong>Динамічних тестів:</strong> ${details.dynamic_tests_count}</p>` : ''}
                        </div>
                    `;
                    
                    // Форми з хорошою підтримкою
                    if (details.supported_forms_list && details.supported_forms_list.length > 0) {
                        html += `
                            <h4 style="color: #27ae60; margin-top: 20px;">✅ Форми з хорошою підтримкою помилок (${details.supported_forms_list.length}):</h4>
                        `;
                        
                        details.supported_forms_list.forEach((form, index) => {
                            const qualityScore = (typeof form.quality_score === 'number' && !isNaN(form.quality_score)) 
                                ? (form.quality_score * 100).toFixed(1) 
                                : '0.0';
                            
                            html += `
                                <div style="margin: 15px 0; padding: 15px; background: #e8f5e8; border-radius: 8px; border-left: 4px solid #27ae60;">
                                    <h5 style="margin: 0 0 10px 0; color: #27ae60;">📋 ${form.selector || 'form'}</h5>
                                    <p><strong>Загальна якість:</strong> ${qualityScore}%</p>
                            `;
                            
                            // Показуємо розбивку статичний/динамічний якщо доступно
                            if (typeof form.static_quality === 'number' || typeof form.dynamic_quality === 'number') {
                                html += `<div style="margin: 8px 0; padding: 8px; background: #f8f9fa; border-radius: 4px;">`;
                                if (typeof form.static_quality === 'number') {
                                    html += `<span style="margin-right: 15px;">📊 Статичний: ${(form.static_quality * 100).toFixed(1)}%</span>`;
                                }
                                if (typeof form.dynamic_quality === 'number') {
                                    html += `<span>🧪 Динамічний: ${(form.dynamic_quality * 100).toFixed(1)}%</span>`;
                                } else if (form.dynamic_error) {
                                    html += `<span style="color: #e74c3c;">❌ Динамічний: ${form.dynamic_error}</span>`;
                                }
                                html += `</div>`;
                            }
                            
                            html += `<p><strong>Функції:</strong> ${form.features || 'Немає даних'}</p>`;
                            
                            // Показуємо результати динамічного тестування
                            if (form.dynamic_test_result && form.dynamic_test_result.systematic_analysis) {
                                // Новий систематичний аналіз
                                const testResult = form.dynamic_test_result;
                                
                                html += `
                                    <div style="margin: 10px 0; padding: 15px; background: #e8f4fd; border-radius: 6px; border: 1px solid #bee5eb;">
                                        <h6 style="margin: 0 0 10px 0; color: #0c5460;">🔬 Систематичний аналіз помилок:</h6>
                                        
                                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px;">
                                            <div><strong>Полів протестовано:</strong> ${testResult.total_fields || 0}</div>
                                            <div><strong>Полів з підтримкою:</strong> ${testResult.supported_fields || 0}</div>
                                        </div>
                                        
                                        <h6 style="margin: 10px 0 5px 0; color: #0c5460;">📊 Статистика методів виявлення:</h6>
                                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 0.9em;">
                                `;
                                
                                const detectionStats = testResult.detection_statistics || {};
                                const statLabels = {
                                    'html5_api': 'HTML5 API',
                                    'aria_support': 'ARIA підтримка', 
                                    'dom_changes': 'DOM зміни',
                                    'css_states': 'CSS стани'
                                };
                                
                                Object.entries(statLabels).forEach(([key, label]) => {
                                    const count = detectionStats[key] || 0;
                                    const total = testResult.total_fields || 1;
                                    const percentage = ((count / total) * 100).toFixed(0);
                                    const color = count > 0 ? '#28a745' : '#6c757d';
                                    
                                    html += `
                                        <div style="color: ${color};">
                                            <strong>${label}:</strong> ${count}/${total} (${percentage}%)
                                        </div>
                                    `;
                                });
                                
                                html += `</div>`;
                                
                                // Детальний аналіз полів (скорочена версія для основного UI)
                                const fieldResults = testResult.field_results || [];
                                if (fieldResults.length > 0) {
                                    html += `
                                        <h6 style="margin: 15px 0 8px 0; color: #0c5460;">🔍 Аналіз полів (${fieldResults.length}):</h6>
                                        <div style="max-height: 200px; overflow-y: auto;">
                                    `;
                                    
                                    fieldResults.forEach((field, index) => {
                                        const fieldName = field.selector || `field-${index + 1}`;
                                        const fieldType = field.type || 'unknown';
                                        const fieldQuality = (field.quality_score * 100).toFixed(0);
                                        const isSupported = field.overall_support;
                                        const statusIcon = isSupported ? '✅' : '❌';
                                        
                                        html += `
                                            <div style="margin: 4px 0; padding: 6px; background: white; border-radius: 3px; font-size: 0.85em;">
                                                ${statusIcon} <strong>${fieldName}</strong> (${fieldType}): ${fieldQuality}%
                                            </div>
                                        `;
                                    });
                                    
                                    html += `</div>`;
                                }
                                
                                html += `</div>`;
                            } else if (form.dynamic_breakdown) {
                                // Старий формат динамічного тестування
                                html += `
                                    <div style="margin: 10px 0; padding: 10px; background: #fff3cd; border-radius: 4px; border: 1px solid #ffeaa7;">
                                        <h6 style="margin: 0 0 8px 0; color: #856404;">🧪 Результати динамічного тестування:</h6>
                                `;
                                
                                Object.entries(form.dynamic_breakdown).forEach(([category, data]) => {
                                    const score = (typeof data.score === 'number' && !isNaN(data.score)) ? (data.score * 100).toFixed(1) : '0.0';
                                    html += `
                                        <div style="margin: 4px 0; font-size: 0.9em;">
                                            <strong>${category}:</strong> ${score}% - ${data.description || 'Немає опису'}
                                        </div>
                                    `;
                                });
                                
                                html += `</div>`;
                            }
                            
                            html += `
                            `;
                            
                            // Деталі полів з фазовим аналізом
                            if (form.field_details && form.field_details.length > 0) {
                                html += `<h6 style="margin: 15px 0 10px 0;">Поля (${form.field_details.length}):</h6>`;
                                
                                form.field_details.forEach(field => {
                                    const fieldQualityScore = (typeof field.quality_score === 'number' && !isNaN(field.quality_score)) 
                                        ? (field.quality_score * 100).toFixed(1) 
                                        : '0.0';
                                    
                                    html += `
                                        <div style="margin: 10px 0; padding: 12px; background: white; border-radius: 6px; border: 1px solid #ddd;">
                                            <h6 style="margin: 0 0 8px 0; color: #2c3e50;">🔍 ${field.name || 'unnamed'} (${field.type || 'unknown'})</h6>
                                            <p style="margin: 5px 0;"><strong>Загальна якість:</strong> ${fieldQualityScore}%</p>
                                    `;
                                    
                                    // Фазовий аналіз
                                    const features = field.features;
                                    if (features) {
                                        ['phase1', 'phase2', 'phase3'].forEach(phaseName => {
                                            const phase = features[phaseName];
                                            if (phase) {
                                                const phaseScore = (typeof phase.score === 'number' && !isNaN(phase.score)) 
                                                    ? (phase.score * 100).toFixed(1) 
                                                    : '0.0';
                                                const maxScore = (typeof phase.max_score === 'number' && !isNaN(phase.max_score)) 
                                                    ? (phase.max_score * 100).toFixed(1) 
                                                    : '0.0';
                                                
                                                html += `
                                                    <div style="margin: 8px 0; padding: 8px; background: #f8f9fa; border-radius: 4px;">
                                                        <h6 style="margin: 0 0 5px 0; color: #495057;">📌 ${phase.title || phaseName}</h6>
                                                        <p style="margin: 3px 0; font-size: 0.9em;"><strong>Скор:</strong> ${phaseScore}%/${maxScore}%</p>
                                                        <p style="margin: 3px 0; font-size: 0.9em; color: #6c757d;">${phase.description || ''}</p>
                                                `;
                                                
                                                // Деталі кожної функції
                                                if (phase.details && phase.details.length > 0) {
                                                    phase.details.forEach(detail => {
                                                        const statusIcon = {
                                                            'success': '✅',
                                                            'warning': '⚠️',
                                                            'error': '❌',
                                                            'missing': '❌',
                                                            'info': 'ℹ️'
                                                        }[detail.status] || '❓';
                                                        
                                                        const detailScore = (typeof detail.score === 'number' && !isNaN(detail.score)) 
                                                            ? (detail.score * 100).toFixed(1) 
                                                            : '0.0';
                                                        
                                                        html += `
                                                            <div style="margin: 5px 0; padding: 6px; background: white; border-radius: 3px; font-size: 0.85em;">
                                                                <strong>${statusIcon} ${detail.feature || 'Unknown'}:</strong> ${detailScore}%<br>
                                                                <span style="color: #6c757d;">${detail.description || ''}</span><br>
                                                        `;
                                                        
                                                        if (detail.explanation) {
                                                            html += `<span style="color: #007bff; font-style: italic;">💡 ${detail.explanation}</span><br>`;
                                                        }
                                                        
                                                        html += `</div>`;
                                                    });
                                                }
                                                
                                                html += `</div>`;
                                            }
                                        });
                                    }
                                    
                                    html += `</div>`;
                                });
                            }
                            
                            html += `</div>`;
                        });
                    }
                    
                    // Проблемні форми
                    if (details.problematic_forms && details.problematic_forms.length > 0) {
                        html += `
                            <h4 style="color: #e74c3c; margin-top: 20px;">❌ Проблемні форми (${details.problematic_forms.length}):</h4>
                        `;
                        
                        details.problematic_forms.forEach((form, index) => {
                            const qualityScore = (typeof form.quality_score === 'number' && !isNaN(form.quality_score)) 
                                ? (form.quality_score * 100).toFixed(1) 
                                : '0.0';
                            
                            html += `
                                <div style="margin: 15px 0; padding: 15px; background: #ffeaea; border-radius: 8px; border-left: 4px solid #e74c3c;">
                                    <h5 style="margin: 0 0 10px 0; color: #e74c3c;">📋 ${form.selector || 'form'}</h5>
                                    <p><strong>Загальна якість:</strong> ${qualityScore}%</p>
                            `;
                            
                            // Показуємо розбивку статичний/динамічний для проблемних форм
                            if (typeof form.static_quality === 'number' || typeof form.dynamic_quality === 'number') {
                                html += `<div style="margin: 8px 0; padding: 8px; background: #fff5f5; border-radius: 4px;">`;
                                if (typeof form.static_quality === 'number') {
                                    html += `<span style="margin-right: 15px;">📊 Статичний: ${(form.static_quality * 100).toFixed(1)}%</span>`;
                                }
                                if (typeof form.dynamic_quality === 'number') {
                                    html += `<span>🧪 Динамічний: ${(form.dynamic_quality * 100).toFixed(1)}%</span>`;
                                } else if (form.dynamic_error) {
                                    html += `<span style="color: #e74c3c;">❌ Динамічний: ${form.dynamic_error}</span>`;
                                }
                                html += `</div>`;
                            }
                            
                            html += `<p><strong>Проблеми:</strong> ${form.issue || 'Невідомі проблеми'}</p>`;
                            
                            // Показуємо результати динамічного тестування для проблемних форм
                            if (form.dynamic_test_result && form.dynamic_test_result.systematic_analysis) {
                                // Новий систематичний аналіз для проблемних форм
                                const testResult = form.dynamic_test_result;
                                
                                html += `
                                    <div style="margin: 10px 0; padding: 15px; background: #f8d7da; border-radius: 6px; border: 1px solid #f5c6cb;">
                                        <h6 style="margin: 0 0 10px 0; color: #721c24;">🔬 Систематичний аналіз (проблемна форма):</h6>
                                        
                                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px;">
                                            <div><strong>Полів протестовано:</strong> ${testResult.total_fields || 0}</div>
                                            <div><strong>Полів з підтримкою:</strong> ${testResult.supported_fields || 0}</div>
                                        </div>
                                `;
                                
                                // Короткий огляд проблем
                                const detectionStats = testResult.detection_statistics || {};
                                const totalFields = testResult.total_fields || 1;
                                const issues = [];
                                
                                if (detectionStats.html5_api === 0) issues.push("Відсутня HTML5 валідація");
                                if (detectionStats.aria_support === 0) issues.push("Відсутня ARIA підтримка");
                                if (detectionStats.dom_changes === 0) issues.push("Немає DOM повідомлень");
                                if (detectionStats.css_states === 0) issues.push("Немає CSS індикаторів");
                                
                                if (issues.length > 0) {
                                    html += `
                                        <div style="margin: 10px 0; padding: 8px; background: #f5c6cb; border-radius: 4px;">
                                            <strong>Основні проблеми:</strong><br>
                                            ${issues.map(issue => `• ${issue}`).join('<br>')}
                                        </div>
                                    `;
                                }
                                
                                html += `</div>`;
                            } else if (form.dynamic_breakdown) {
                                // Старий формат для проблемних форм
                                html += `
                                    <div style="margin: 10px 0; padding: 10px; background: #f8d7da; border-radius: 4px; border: 1px solid #f5c6cb;">
                                        <h6 style="margin: 0 0 8px 0; color: #721c24;">🧪 Динамічне тестування:</h6>
                                `;
                                
                                Object.entries(form.dynamic_breakdown).forEach(([category, data]) => {
                                    const score = (typeof data.score === 'number' && !isNaN(data.score)) ? (data.score * 100).toFixed(1) : '0.0';
                                    html += `
                                        <div style="margin: 4px 0; font-size: 0.9em;">
                                            <strong>${category}:</strong> ${score}% - ${data.description || 'Немає опису'}
                                        </div>
                                    `;
                                });
                                
                                html += `</div>`;
                            }
                            
                            html += `
                            `;
                            
                            // Деталі полів для проблемних форм (скорочено)
                            if (form.field_details && form.field_details.length > 0) {
                                html += `<h6 style="margin: 15px 0 10px 0;">Поля (${form.field_details.length}):</h6>`;
                                
                                form.field_details.forEach(field => {
                                    const fieldQualityScore = (typeof field.quality_score === 'number' && !isNaN(field.quality_score)) 
                                        ? (field.quality_score * 100).toFixed(1) 
                                        : '0.0';
                                    
                                    html += `
                                        <div style="margin: 10px 0; padding: 12px; background: white; border-radius: 6px; border: 1px solid #ddd;">
                                            <h6 style="margin: 0 0 8px 0; color: #2c3e50;">🔍 ${field.name || 'unnamed'} (${field.type || 'unknown'})</h6>
                                            <p style="margin: 5px 0;"><strong>Якість:</strong> ${fieldQualityScore}%</p>
                                    `;
                                    
                                    // Скорочений фазовий аналіз для проблемних форм
                                    const features = field.features;
                                    if (features) {
                                        ['phase1', 'phase2', 'phase3'].forEach(phaseName => {
                                            const phase = features[phaseName];
                                            if (phase) {
                                                const phaseScore = (typeof phase.score === 'number' && !isNaN(phase.score)) 
                                                    ? (phase.score * 100).toFixed(1) 
                                                    : '0.0';
                                                
                                                const statusColor = phase.score > 0.7 ? '#27ae60' : phase.score > 0.3 ? '#f39c12' : '#e74c3c';
                                                
                                                html += `
                                                    <span style="display: inline-block; margin: 2px 5px 2px 0; padding: 3px 8px; background: ${statusColor}; color: white; border-radius: 12px; font-size: 0.8em;">
                                                        ${phase.title}: ${phaseScore}%
                                                    </span>
                                                `;
                                            }
                                        });
                                    }
                                    
                                    html += `</div>`;
                                });
                            }
                            
                            html += `</div>`;
                        });
                    }
                    
                } else {
                    html += `
                        <p style="color: #666; margin-top: 15px;">
                            Форми для валідації не знайдено на сторінці. Аналіз підтримки помилок включає 
                            перевірку валідації форм, повідомлень про помилки та механізмів їх відображення.
                        </p>
                    `;
                }
                
                // Додаємо пояснення критеріїв оцінки
                html += `
                    <div style="margin-top: 20px; padding: 15px; background: #f8f9fa; border-radius: 5px; border: 1px solid #dee2e6;">
                        <h5 style="margin-top: 0; color: #495057;">📋 Критерії оцінки підтримки помилок:</h5>
                        <ul style="margin: 10px 0; padding-left: 20px; color: #6c757d;">
                            <li><strong>Фаза 1 (40%):</strong> Базові функції - required/pattern валідація, aria-invalid, aria-describedby, role="alert"</li>
                            <li><strong>Фаза 2 (30%):</strong> Якість повідомлень - зрозумілість, конструктивність, специфічність</li>
                            <li><strong>Фаза 3 (30%):</strong> Динамічна валідація - live regions, JavaScript валідація</li>
                        </ul>
                        <p style="margin: 5px 0; color: #495057;"><strong>Поріг якості:</strong> ≥50% вважається хорошою підтримкою помилок</p>
                    </div>
                `;
                
                return html;
            }
            
            
            // Генерація детального аналізу локалізації
            function generateLocalizationDetails(details) {
                if (!details) return '<p>Детальна інформація недоступна</p>';
                
                let html = `
                    <div class="score-explanation">
                        <strong>${details.score_explanation}</strong>
                    </div>
                `;
                
                if (details.detected_languages && details.detected_languages.length > 0) {
                    html += `
                        <h4 style="color: #27ae60; margin-top: 20px;">✅ Виявлені мови:</h4>
                        <div class="element-list">
                    `;
                    
                    details.detected_languages.forEach(lang => {
                        html += `
                            <div class="element-item correct">
                                <div class="element-status"><strong>Мова:</strong> ${lang.name} (${lang.code})</div>
                                <div class="element-status"><strong>Вага в розрахунку:</strong> ${(lang.weight * 100).toFixed(1)}%</div>
                            </div>
                        `;
                    });
                    
                    html += '</div>';
                }
                
                if (details.missing_languages && details.missing_languages.length > 0) {
                    html += `
                        <h4 style="color: #f39c12; margin-top: 20px;">⚠️ Рекомендовані мови:</h4>
                        <div class="element-list">
                    `;
                    
                    details.missing_languages.forEach(lang => {
                        html += `
                            <div class="element-item" style="border-left: 4px solid #f39c12; background: #fff8e1;">
                                <div class="element-status"><strong>Мова:</strong> ${lang.name} (${lang.code})</div>
                                <div class="element-status"><strong>Потенційна вага:</strong> ${(lang.weight * 100).toFixed(1)}%</div>
                            </div>
                        `;
                    });
                    
                    html += '</div>';
                }
                
                if (!details.detected_languages || details.detected_languages.length === 0) {
                    html += `
                        <p style="color: #666; margin-top: 15px;">
                            Аналіз локалізації перевіряє наявність lang атрибутів, language switcher, 
                            hreflang посилань та автоматично визначає мову контенту.
                        </p>
                    `;
                }
                
                return html;
            }
            
            // Функція для екранування HTML
            function escapeHtml(text) {
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
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
            detailed_analysis=result.get('detailed_analysis', {}),  # Додаємо детальний аналіз
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


@app.post("/api/evaluate-html", response_model=EvaluationResponse)
async def evaluate_html_accessibility(request: HTMLRequest):
    """
    Аналіз доступності HTML контенту
    
    Args:
        request: Запит з HTML контентом для аналізу
        
    Returns:
        Результати аналізу доступності
    """
    
    print(f"🔍 Отримано запит на аналіз HTML контенту (довжина: {len(request.html_content)} символів)")
    
    try:
        # Виконання аналізу HTML
        print(f"📊 Початок аналізу HTML контенту")
        result = await evaluator.evaluate_html_content(
            html_content=request.html_content,
            base_url=request.base_url,
            title=request.title
        )
        
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
        
        print(f"✅ Аналіз HTML завершено. Скор: {result['final_score']:.3f}")
        
        return EvaluationResponse(
            url=result['url'],
            metrics=result['metrics'],
            subscores=result['subscores'],
            final_score=result['final_score'],
            quality_level=quality_level,
            quality_description=quality_description,
            recommendations=result['recommendations'],
            detailed_analysis=result.get('detailed_analysis', {}),  # Додаємо детальний аналіз
            status=result['status']
        )
        
    except HTTPException:
        # Перепередаємо HTTP помилки як є
        raise
    except Exception as e:
        print(f"❌ Критична помилка сервера при аналізі HTML: {str(e)}")
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