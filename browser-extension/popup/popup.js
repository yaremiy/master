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
        const totalScore = Math.round(results.totalScore * 100);
        
        return `
            <!DOCTYPE html>
            <html lang="uk">
            <head>
                <meta charset="UTF-8">
                <title>Звіт доступності - ${pageUrl}</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; }
                    .header { border-bottom: 2px solid #007bff; padding-bottom: 20px; }
                    .score { font-size: 24px; font-weight: bold; color: #28a745; }
                    .metric { margin: 10px 0; padding: 10px; border-left: 4px solid #007bff; }
                    .issue { margin: 5px 0; padding: 8px; background: #f8f9fa; border-radius: 4px; }
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>🔍 Звіт доступності</h1>
                    <p><strong>URL:</strong> ${pageUrl}</p>
                    <p><strong>Дата:</strong> ${date}</p>
                    <p><strong>Загальний скор:</strong> <span class="score">${totalScore}%</span></p>
                </div>
                
                <h2>📊 Метрики</h2>
                ${Object.entries(results.metrics).map(([key, value]) => 
                    `<div class="metric"><strong>${key}:</strong> ${Math.round(value * 100)}%</div>`
                ).join('')}
                
                ${results.issues && results.issues.length > 0 ? `
                    <h2>🚨 Проблеми</h2>
                    ${results.issues.map(issue => 
                        `<div class="issue"><strong>${issue.severity}:</strong> ${issue.description}</div>`
                    ).join('')}
                ` : ''}
                
                <p style="margin-top: 40px; color: #666; font-size: 12px;">
                    Згенеровано Accessibility Evaluator v1.0.0
                </p>
            </body>
            </html>
        `;
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