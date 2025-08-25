/**
 * Popup JavaScript для Accessibility Evaluator
 * Управляє UI та комунікацією з content scripts
 */

class AccessibilityPopup {
    constructor() {
        this.isAnalyzing = false;
        this.currentResults = null;
        this.init();
    }

    init() {
        this.bindEvents();
        this.loadPreviousResults();
    }

    bindEvents() {
        // Кнопка аналізу
        document.getElementById('analyze-btn').addEventListener('click', () => {
            this.analyzeCurrentPage();
        });

        // Перемикач детальних результатів
        document.getElementById('toggle-details').addEventListener('click', () => {
            this.toggleDetailedResults();
        });

        // Експорт звіту
        document.getElementById('export-btn').addEventListener('click', () => {
            this.exportReport();
        });

        // Підсвічування проблем
        document.getElementById('highlight-issues').addEventListener('click', () => {
            this.highlightIssues();
        });

        // Налаштування
        document.getElementById('settings-btn').addEventListener('click', () => {
            this.openSettings();
        });

        // Допомога
        document.getElementById('help-btn').addEventListener('click', () => {
            this.openHelp();
        });

        // Клік по метриці для деталей
        document.querySelectorAll('.metric-card').forEach(card => {
            card.addEventListener('click', () => {
                const metric = card.dataset.metric;
                this.showMetricDetails(metric);
            });
        });
    }

    async analyzeCurrentPage() {
        if (this.isAnalyzing) return;

        try {
            this.setAnalyzing(true);
            this.showProgress();

            // Отримуємо активну вкладку
            const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
            
            if (!tab) {
                throw new Error('Не вдалося отримати активну вкладку');
            }

            // Перевіряємо чи можна аналізувати цю сторінку
            if (!this.canAnalyzePage(tab.url)) {
                throw new Error('Неможливо аналізувати цю сторінку (chrome://, extension://, etc.)');
            }

            // Спочатку перевіряємо чи content script завантажений
            let results;
            try {
                // Спробуємо ping content script
                await chrome.tabs.sendMessage(tab.id, { action: 'ping' });
            } catch (error) {
                // Content script не завантажений, ін'єктуємо його
                console.log('Content script не знайдено, ін\'єктуємо...');
                await this.injectContentScript(tab.id);
                // Чекаємо трохи для ініціалізації
                await new Promise(resolve => setTimeout(resolve, 1000));
            }

            // Відправляємо повідомлення content script з timeout
            results = await Promise.race([
                chrome.tabs.sendMessage(tab.id, {
                    action: 'analyze-accessibility',
                    options: {
                        includeDetailedAnalysis: true,
                        testForms: true,
                        checkImages: true,
                        testKeyboardNavigation: true
                    }
                }),
                new Promise((_, reject) => 
                    setTimeout(() => reject(new Error('Timeout: аналіз займає занадто довго')), 30000)
                )
            ]);

            if (!results) {
                throw new Error('Не отримано результатів аналізу');
            }

            if (results.error) {
                throw new Error(`Помилка аналізу: ${results.error}`);
            }

            this.currentResults = results;
            this.displayResults(results);
            this.saveResults(results, tab.url);

        } catch (error) {
            console.error('Помилка аналізу:', error);
            this.showError(error.message);
        } finally {
            this.setAnalyzing(false);
            this.hideProgress();
        }
    }

    canAnalyzePage(url) {
        const restrictedProtocols = ['chrome:', 'chrome-extension:', 'moz-extension:', 'edge:', 'about:'];
        return !restrictedProtocols.some(protocol => url.startsWith(protocol));
    }

    async injectContentScript(tabId) {
        try {
            // Ін'єктуємо всі необхідні файли в правильному порядку
            const files = [
                'utils/helpers.js',
                'content-scripts/metrics/base-metrics.js',
                'content-scripts/metrics/perceptibility-metrics.js',
                'content-scripts/metrics/operability-metrics.js',
                'content-scripts/metrics/understandability-metrics.js',
                'content-scripts/form-tester.js',
                'content-scripts/analyzer.js'
            ];

            for (const file of files) {
                await chrome.scripting.executeScript({
                    target: { tabId: tabId },
                    files: [file]
                });
            }

            // Ін'єктуємо CSS
            await chrome.scripting.insertCSS({
                target: { tabId: tabId },
                files: ['content-scripts/analyzer.css']
            });

            console.log('Content scripts успішно ін\'єктовано');
        } catch (error) {
            console.error('Помилка ін\'єкції content script:', error);
            throw new Error('Не вдалося завантажити аналізатор на цю сторінку');
        }
    }

    setAnalyzing(analyzing) {
        this.isAnalyzing = analyzing;
        const analyzeBtn = document.getElementById('analyze-btn');
        const btnText = analyzeBtn.querySelector('.btn-text');
        
        if (analyzing) {
            analyzeBtn.disabled = true;
            btnText.textContent = 'Аналіз...';
            analyzeBtn.style.opacity = '0.6';
        } else {
            analyzeBtn.disabled = false;
            btnText.textContent = 'Аналізувати сторінку';
            analyzeBtn.style.opacity = '1';
        }
    }

    showProgress() {
        document.getElementById('analyze-progress').style.display = 'block';
    }

    hideProgress() {
        document.getElementById('analyze-progress').style.display = 'none';
    }

    displayResults(results) {
        // Ховаємо помилки та показуємо результати
        document.getElementById('error-container').style.display = 'none';
        document.getElementById('results-container').style.display = 'block';

        // Загальний скор
        const totalScore = (results.totalScore * 100).toFixed(1);
        document.getElementById('total-score').textContent = totalScore;
        this.updateScoreInterpretation(totalScore);

        // Метрики
        const metrics = ['perceptibility', 'operability', 'understandability', 'localization'];
        metrics.forEach(metric => {
            const score = ((results.metrics[metric] || 0) * 100).toFixed(1);
            document.getElementById(`${metric}-score`).textContent = score;
            this.updateMetricCard(metric, parseFloat(score));
        });

        // Детальні результати
        this.updateDetailedResults(results);
    }

    updateScoreInterpretation(score) {
        const interpretation = document.getElementById('score-interpretation');
        const totalScoreElement = document.getElementById('total-score');
        
        let text, className;
        
        if (score >= 90) {
            text = 'Відмінна доступність';
            className = 'score-excellent';
        } else if (score >= 75) {
            text = 'Хороша доступність';
            className = 'score-good';
        } else if (score >= 60) {
            text = 'Задовільна доступність';
            className = 'score-fair';
        } else if (score >= 40) {
            text = 'Погана доступність';
            className = 'score-poor';
        } else {
            text = 'Критична доступність';
            className = 'score-critical';
        }
        
        interpretation.textContent = text;
        totalScoreElement.className = `total-score ${className}`;
    }

    updateMetricCard(metric, score) {
        const card = document.querySelector(`[data-metric="${metric}"]`);
        const scoreElement = card.querySelector('.score-value');
        
        let className;
        if (score >= 80) className = 'score-excellent';
        else if (score >= 65) className = 'score-good';
        else if (score >= 50) className = 'score-fair';
        else if (score >= 35) className = 'score-poor';
        else className = 'score-critical';
        
        scoreElement.className = `score-value ${className}`;
    }

    updateDetailedResults(results) {
        const detailedContainer = document.getElementById('detailed-results');
        
        let html = '<div class="detailed-content">';
        
        // Підсумок проблем
        if (results.issues && results.issues.length > 0) {
            html += `
                <div class="issues-summary">
                    <h4>🚨 Знайдені проблеми (${results.issues.length})</h4>
                    <div class="issues-list">
            `;
            
            results.issues.slice(0, 5).forEach(issue => {
                html += `
                    <div class="issue-item">
                        <span class="issue-severity ${issue.severity}">${this.getSeverityIcon(issue.severity)}</span>
                        <span class="issue-text">${issue.description}</span>
                    </div>
                `;
            });
            
            if (results.issues.length > 5) {
                html += `<div class="more-issues">... та ще ${results.issues.length - 5} проблем</div>`;
            }
            
            html += '</div></div>';
        }
        
        // Статистика по метриках
        html += `
            <div class="metrics-details">
                <h4>📊 Детальна статистика</h4>
                <div class="stats-grid">
        `;
        
        const metricsInfo = {
            perceptibility: 'Сприйнятність',
            operability: 'Керованість', 
            understandability: 'Зрозумілість',
            localization: 'Локалізація'
        };
        
        Object.entries(metricsInfo).forEach(([key, title]) => {
            const score = Math.round((results.metrics[key] || 0) * 100);
            html += `
                <div class="stat-item">
                    <span class="stat-label">${title}:</span>
                    <span class="stat-value">${score}%</span>
                </div>
            `;
        });
        
        html += '</div></div>';
        
        // Рекомендації
        if (results.recommendations && results.recommendations.length > 0) {
            html += `
                <div class="recommendations">
                    <h4>💡 Рекомендації</h4>
                    <ul class="recommendations-list">
            `;
            
            results.recommendations.slice(0, 3).forEach(rec => {
                html += `<li class="recommendation-item">${rec}</li>`;
            });
            
            html += '</ul></div>';
        }
        
        html += '</div>';
        
        detailedContainer.innerHTML = html;
    }

    getSeverityIcon(severity) {
        const icons = {
            critical: '🔴',
            high: '🟠', 
            medium: '🟡',
            low: '🔵',
            info: 'ℹ️'
        };
        return icons[severity] || 'ℹ️';
    }

    toggleDetailedResults() {
        const detailedResults = document.getElementById('detailed-results');
        const toggleBtn = document.getElementById('toggle-details');
        const isVisible = detailedResults.style.display !== 'none';
        
        if (isVisible) {
            detailedResults.style.display = 'none';
            toggleBtn.classList.remove('expanded');
        } else {
            detailedResults.style.display = 'block';
            toggleBtn.classList.add('expanded');
        }
    }

    async exportReport() {
        if (!this.currentResults) {
            this.showError('Немає результатів для експорту');
            return;
        }

        try {
            const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
            const report = this.generateReport(this.currentResults, tab.url);
            
            // Створюємо та завантажуємо файл
            const blob = new Blob([report], { type: 'text/html' });
            const url = URL.createObjectURL(blob);
            
            await chrome.downloads.download({
                url: url,
                filename: `accessibility-report-${new Date().toISOString().split('T')[0]}.html`
            });
            
        } catch (error) {
            console.error('Помилка експорту:', error);
            this.showError('Не вдалося експортувати звіт');
        }
    }

    generateReport(results, pageUrl) {
        const date = new Date().toLocaleDateString('uk-UA');
        const totalScore = (results.totalScore * 100).toFixed(1);
        
        return `
            <!DOCTYPE html>
            <html lang="uk">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Звіт доступності - ${pageUrl}</title>
                <style>
                    body { 
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                        margin: 0; 
                        padding: 40px; 
                        background-color: #f8f9fa;
                        line-height: 1.6;
                    }
                    .container {
                        max-width: 1200px;
                        margin: 0 auto;
                        background: white;
                        border-radius: 12px;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                        overflow: hidden;
                    }
                    .header { 
                        background: linear-gradient(135deg, #007bff, #0056b3);
                        color: white;
                        padding: 30px 40px;
                        text-align: center;
                    }
                    .header h1 { margin: 0 0 20px 0; font-size: 2.5em; }
                    .header p { margin: 5px 0; opacity: 0.9; }
                    .score-badge { 
                        display: inline-block;
                        background: rgba(255,255,255,0.2);
                        padding: 15px 30px;
                        border-radius: 50px;
                        font-size: 1.8em;
                        font-weight: bold;
                        margin-top: 20px;
                    }
                    .content { padding: 40px; }
                    .metrics-grid {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                        gap: 20px;
                        margin: 30px 0;
                    }
                    .metric-card {
                        background: #f8f9fa;
                        border-radius: 8px;
                        padding: 20px;
                        border-left: 5px solid #007bff;
                    }
                    .metric-title { 
                        font-weight: bold; 
                        color: #495057; 
                        margin-bottom: 10px;
                        font-size: 1.1em;
                    }
                    .metric-score { 
                        font-size: 2em; 
                        font-weight: bold; 
                        color: #28a745; 
                    }
                    .metric-details {
                        margin-top: 15px;
                        font-size: 0.9em;
                        color: #6c757d;
                    }
                    .section {
                        margin: 40px 0;
                        padding: 30px;
                        background: #f8f9fa;
                        border-radius: 8px;
                    }
                    .section h2 {
                        color: #495057;
                        border-bottom: 2px solid #dee2e6;
                        padding-bottom: 10px;
                        margin-bottom: 20px;
                    }
                    .detail-item {
                        background: white;
                        margin: 10px 0;
                        padding: 15px;
                        border-radius: 6px;
                        border-left: 4px solid #007bff;
                    }
                    .detail-label {
                        font-weight: bold;
                        color: #495057;
                        margin-bottom: 5px;
                    }
                    .detail-value {
                        color: #6c757d;
                    }
                    .recommendations {
                        background: #e3f2fd;
                        border-left: 4px solid #2196f3;
                        padding: 20px;
                        border-radius: 6px;
                        margin: 20px 0;
                    }
                    .recommendations h3 {
                        color: #1976d2;
                        margin-top: 0;
                    }
                    .recommendations ul {
                        margin: 0;
                        padding-left: 20px;
                    }
                    .recommendations li {
                        margin: 8px 0;
                        color: #424242;
                    }
                    .footer {
                        text-align: center;
                        padding: 20px;
                        color: #6c757d;
                        font-size: 0.9em;
                        border-top: 1px solid #dee2e6;
                        margin-top: 40px;
                    }
                    .score-excellent { color: #28a745; }
                    .score-good { color: #17a2b8; }
                    .score-fair { color: #ffc107; }
                    .score-poor { color: #fd7e14; }
                    .score-critical { color: #dc3545; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🔍 Звіт доступності веб-сайту</h1>
                        <p><strong>URL:</strong> ${pageUrl}</p>
                        <p><strong>Дата аналізу:</strong> ${date}</p>
                        <div class="score-badge">
                            Загальний скор: ${totalScore}%
                        </div>
                    </div>
                    
                    <div class="content">
                        ${this.generateMetricsSection(results)}
                        ${this.generateDetailedAnalysis(results)}
                        ${this.generateRecommendations(results)}
                    </div>
                    
                    <div class="footer">
                        <p>Згенеровано Accessibility Evaluator v1.0.0 • ${new Date().toLocaleString('uk-UA')}</p>
                        <p>Аналіз базується на принципах WCAG 2.1 та науковій методології оцінки доступності</p>
                    </div>
                </div>
            </body>
            </html>
        `;
    }

    generateMetricsSection(results) {
        const metricsInfo = {
            perceptibility: {
                title: '👁️ Сприйнятність (Perceptibility)',
                description: 'Наскільки легко користувачі можуть сприймати інформацію'
            },
            operability: {
                title: '⌨️ Керованість (Operability)', 
                description: 'Наскільки легко користувачі можуть взаємодіяти з інтерфейсом'
            },
            understandability: {
                title: '🧠 Зрозумілість (Understandability)',
                description: 'Наскільки легко користувачі можуть зрозуміти інформацію та інтерфейс'
            },
            localization: {
                title: '🌍 Локалізація (Localization)',
                description: 'Наскільки добре сайт адаптований для різних мов та культур'
            }
        };

        let html = '<h2>📊 Детальні метрики доступності</h2>';
        html += '<div class="metrics-grid">';

        Object.entries(results.metrics).forEach(([key, value]) => {
            const score = (value * 100).toFixed(1);
            const info = metricsInfo[key];
            const scoreClass = this.getScoreClass(parseFloat(score));
            
            html += `
                <div class="metric-card">
                    <div class="metric-title">${info?.title || key}</div>
                    <div class="metric-score ${scoreClass}">${score}%</div>
                    <div class="metric-details">${info?.description || ''}</div>
                </div>
            `;
        });

        html += '</div>';
        return html;
    }

    generateDetailedAnalysis(results) {
        let html = '<div class="section">';
        html += '<h2>🔍 Детальний аналіз</h2>';

        // Статистика сторінки
        if (results.pageData) {
            html += `
                <div class="detail-item">
                    <div class="detail-label">📄 Статистика сторінки</div>
                    <div class="detail-value">
                        <p><strong>Заголовок:</strong> ${results.pageData.title || 'Не вказано'}</p>
                        <p><strong>Мова:</strong> ${results.pageData.language || 'Не визначено'}</p>
                        <p><strong>Напрямок тексту:</strong> ${results.pageData.direction || 'Не визначено'}</p>
                    </div>
                </div>
            `;
        }

        html += '</div>';
        return html;
    }

    // Методи детального форматування видалені - повернулися до простого стану

    getSubmetricTitle(submetric) {
        const titles = {
            alt_text: 'Альтернативний текст зображень',
            contrast: 'Контрастність тексту',
            media_accessibility: 'Доступність медіа',
            keyboard_navigation: 'Клавіатурна навігація',
            structured_navigation: 'Структурована навігація',
            instruction_clarity: 'Зрозумілість інструкцій',
            input_assistance: 'Допомога при введенні',
            error_support: 'Підтримка помилок',
            localization: 'Локалізація контенту'
        };
        return titles[submetric] || submetric;
    }

    getSubmetricDescription(submetric, score) {
        if (score >= 90) {
            return '<br><span style="color: #28a745;">Відмінний результат!</span>';
        } else if (score >= 70) {
            return '<br><span style="color: #17a2b8;">Добрий результат</span>';
        } else if (score >= 50) {
            return '<br><span style="color: #ffc107;">Потребує покращення</span>';
        } else {
            return '<br><span style="color: #dc3545;">Критичні проблеми виявлені</span>';
        }
    }

    generateRecommendations(results) {
        let html = '<div class="recommendations">';
        html += '<h3>💡 Рекомендації для покращення доступності</h3>';

        if (results.recommendations && results.recommendations.length > 0) {
            html += '<ul>';
            results.recommendations.forEach(rec => {
                html += `<li>${rec}</li>`;
            });
            html += '</ul>';
        } else {
            // Генеруємо рекомендації на основі скорів
            html += '<ul>';
            
            Object.entries(results.metrics).forEach(([key, value]) => {
                const score = value * 100;
                if (score < 80) {
                    html += `<li>${this.getRecommendationForMetric(key, score)}</li>`;
                }
            });
            
            if (Object.values(results.metrics).every(v => v * 100 >= 80)) {
                html += '<li>🎉 Відмінна робота! Ваш сайт має високий рівень доступності.</li>';
                html += '<li>Продовжуйте регулярно тестувати доступність при додаванні нового контенту.</li>';
            }
            
            html += '</ul>';
        }

        html += '</div>';
        return html;
    }

    getCategoryTitle(category) {
        const titles = {
            perceptibility: '👁️ Сприйнятність',
            operability: '⌨️ Керованість',
            understandability: '🧠 Зрозумілість',
            localization: '🌍 Локалізація'
        };
        return titles[category] || category;
    }

    formatDetailedMetrics(details) {
        if (typeof details === 'object') {
            return Object.entries(details)
                .map(([key, value]) => `<strong>${key}:</strong> ${value}`)
                .join('<br>');
        }
        return details.toString();
    }

    getRecommendationForMetric(metric, score) {
        const recommendations = {
            perceptibility: 'Покращіть альтернативний текст для зображень та контрастність тексту',
            operability: 'Забезпечте повну підтримку клавіатурної навігації та зрозумілу структуру',
            understandability: 'Зробіть інструкції більш зрозумілими та покращіть обробку помилок у формах',
            localization: 'Додайте правильні мовні атрибути та покращіть локалізацію контенту'
        };
        return recommendations[metric] || `Покращіть показники для категорії ${metric}`;
    }

    getScoreClass(score) {
        if (score >= 90) return 'score-excellent';
        if (score >= 75) return 'score-good';
        if (score >= 60) return 'score-fair';
        if (score >= 40) return 'score-poor';
        return 'score-critical';
    }

    async highlightIssues() {
        try {
            const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
            
            await chrome.tabs.sendMessage(tab.id, {
                action: 'highlight-issues',
                issues: this.currentResults?.issues || []
            });
            
        } catch (error) {
            console.error('Помилка підсвічування:', error);
            this.showError('Не вдалося підсвітити проблеми');
        }
    }

    showMetricDetails(metric) {
        // TODO: Показати детальну інформацію про конкретну метрику
        console.log(`Показати деталі для метрики: ${metric}`);
    }

    openSettings() {
        // TODO: Відкрити сторінку налаштувань
        console.log('Відкрити налаштування');
    }

    openHelp() {
        // TODO: Відкрити сторінку допомоги
        chrome.tabs.create({
            url: 'https://github.com/your-repo/accessibility-evaluator/wiki'
        });
    }

    showError(message) {
        document.getElementById('results-container').style.display = 'none';
        document.getElementById('error-container').style.display = 'block';
        document.getElementById('error-text').textContent = message;
    }

    async loadPreviousResults() {
        try {
            const [tab] = await chrome.tabs.query({active: true, currentWindow: true});
            const key = `results_${this.getUrlKey(tab.url)}`;
            const stored = await chrome.storage.local.get(key);
            
            if (stored[key]) {
                this.currentResults = stored[key];
                this.displayResults(stored[key]);
            }
        } catch (error) {
            console.log('Немає попередніх результатів');
        }
    }

    async saveResults(results, url) {
        try {
            const key = `results_${this.getUrlKey(url)}`;
            await chrome.storage.local.set({
                [key]: {
                    ...results,
                    timestamp: Date.now(),
                    url: url
                }
            });
        } catch (error) {
            console.error('Помилка збереження результатів:', error);
        }
    }

    getUrlKey(url) {
        return btoa(url).replace(/[^a-zA-Z0-9]/g, '').substring(0, 50);
    }
}

// Ініціалізація popup при завантаженні
document.addEventListener('DOMContentLoaded', () => {
    new AccessibilityPopup();
});