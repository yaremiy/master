/**
 * Background Service Worker для Accessibility Evaluator
 * Координує роботу між popup та content scripts
 */

class AccessibilityBackground {
    constructor() {
        this.init();
    }

    init() {
        this.setupMessageHandlers();
        this.setupContextMenus();
        this.setupInstallHandler();
    }

    setupMessageHandlers() {
        // Обробка повідомлень від popup та content scripts
        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            this.handleMessage(request, sender, sendResponse);
            return true; // Асинхронна відповідь
        });
    }

    async handleMessage(request, sender, sendResponse) {
        try {
            switch (request.action) {
                case 'analyze-page':
                    await this.analyzePage(request, sender, sendResponse);
                    break;
                
                case 'save-results':
                    await this.saveResults(request.data);
                    sendResponse({ success: true });
                    break;
                
                case 'get-results':
                    const results = await this.getResults(request.url);
                    sendResponse({ results });
                    break;
                
                case 'export-report':
                    await this.exportReport(request.data);
                    sendResponse({ success: true });
                    break;
                
                default:
                    sendResponse({ error: 'Unknown action' });
            }
        } catch (error) {
            console.error('Background script error:', error);
            sendResponse({ error: error.message });
        }
    }

    async analyzePage(request, sender, sendResponse) {
        try {
            // Інжектуємо необхідні скрипти якщо потрібно
            await this.ensureContentScriptsLoaded(sender.tab.id);
            
            // Передаємо запит на аналіз content script
            const results = await chrome.tabs.sendMessage(sender.tab.id, {
                action: 'perform-analysis',
                options: request.options
            });
            
            // Зберігаємо результати
            await this.saveResults({
                url: sender.tab.url,
                results: results,
                timestamp: Date.now()
            });
            
            sendResponse(results);
            
        } catch (error) {
            console.error('Analysis error:', error);
            sendResponse({ error: error.message });
        }
    }

    async ensureContentScriptsLoaded(tabId) {
        try {
            // Перевіряємо чи завантажені content scripts
            const response = await chrome.tabs.sendMessage(tabId, { action: 'ping' });
            if (response && response.pong) {
                return; // Скрипти вже завантажені
            }
        } catch (error) {
            // Скрипти не завантажені, інжектуємо їх
        }

        // Інжектуємо content scripts
        await chrome.scripting.executeScript({
            target: { tabId: tabId },
            files: [
                'utils/helpers.js',
                'content-scripts/metrics/base-metrics.js',
                'content-scripts/metrics/perceptibility-metrics.js',
                'content-scripts/metrics/operability-metrics.js',
                'content-scripts/metrics/understandability-metrics.js',
                'content-scripts/metrics/localization-metrics.js',
                'content-scripts/form-tester.js',
                'content-scripts/analyzer.js'
            ]
        });

        // Інжектуємо CSS
        await chrome.scripting.insertCSS({
            target: { tabId: tabId },
            files: ['content-scripts/analyzer.css']
        });
    }

    setupContextMenus() {
        // Створюємо контекстне меню
        chrome.runtime.onInstalled.addListener(() => {
            chrome.contextMenus.create({
                id: 'analyze-accessibility',
                title: '🔍 Аналізувати доступність',
                contexts: ['page']
            });

            chrome.contextMenus.create({
                id: 'analyze-element',
                title: '🎯 Аналізувати елемент',
                contexts: ['all']
            });
        });

        // Обробка кліків по контекстному меню
        chrome.contextMenus.onClicked.addListener(async (info, tab) => {
            switch (info.menuItemId) {
                case 'analyze-accessibility':
                    await this.openPopupAnalysis(tab);
                    break;
                
                case 'analyze-element':
                    await this.analyzeElement(info, tab);
                    break;
            }
        });
    }

    async openPopupAnalysis(tab) {
        // Відкриваємо popup для аналізу
        chrome.action.openPopup();
    }

    async analyzeElement(info, tab) {
        try {
            // Аналізуємо конкретний елемент
            await chrome.tabs.sendMessage(tab.id, {
                action: 'analyze-element',
                elementInfo: {
                    x: info.clientX,
                    y: info.clientY,
                    selectionText: info.selectionText
                }
            });
        } catch (error) {
            console.error('Element analysis error:', error);
        }
    }

    setupInstallHandler() {
        chrome.runtime.onInstalled.addListener((details) => {
            if (details.reason === 'install') {
                this.handleFirstInstall();
            } else if (details.reason === 'update') {
                this.handleUpdate(details.previousVersion);
            }
        });
    }

    handleFirstInstall() {
        // Відкриваємо welcome сторінку
        chrome.tabs.create({
            url: chrome.runtime.getURL('welcome.html')
        });

        // Встановлюємо початкові налаштування
        chrome.storage.sync.set({
            settings: {
                autoAnalyze: false,
                detailedReports: true,
                highlightIssues: true,
                language: 'uk'
            }
        });
    }

    handleUpdate(previousVersion) {
        console.log(`Updated from version ${previousVersion} to ${chrome.runtime.getManifest().version}`);
        
        // Міграція налаштувань якщо потрібно
        this.migrateSettings(previousVersion);
    }

    async migrateSettings(previousVersion) {
        // TODO: Міграція налаштувань між версіями
    }

    async saveResults(data) {
        try {
            const key = `analysis_${this.getUrlKey(data.url)}_${Date.now()}`;
            await chrome.storage.local.set({ [key]: data });
            
            // Очищуємо старі результати (зберігаємо тільки останні 50)
            await this.cleanupOldResults();
            
        } catch (error) {
            console.error('Error saving results:', error);
        }
    }

    async getResults(url) {
        try {
            const urlKey = this.getUrlKey(url);
            const allData = await chrome.storage.local.get();
            
            // Знаходимо результати для цього URL
            const results = Object.entries(allData)
                .filter(([key, value]) => key.includes(urlKey))
                .map(([key, value]) => value)
                .sort((a, b) => b.timestamp - a.timestamp);
            
            return results[0] || null; // Повертаємо найновіший результат
            
        } catch (error) {
            console.error('Error getting results:', error);
            return null;
        }
    }

    async cleanupOldResults() {
        try {
            const allData = await chrome.storage.local.get();
            const analysisKeys = Object.keys(allData)
                .filter(key => key.startsWith('analysis_'))
                .sort((a, b) => {
                    const timestampA = parseInt(a.split('_').pop());
                    const timestampB = parseInt(b.split('_').pop());
                    return timestampB - timestampA;
                });
            
            // Видаляємо старі результати (залишаємо тільки 50 найновіших)
            if (analysisKeys.length > 50) {
                const keysToRemove = analysisKeys.slice(50);
                await chrome.storage.local.remove(keysToRemove);
            }
            
        } catch (error) {
            console.error('Error cleaning up results:', error);
        }
    }

    async exportReport(data) {
        try {
            // Генеруємо HTML звіт
            const reportHtml = this.generateReportHtml(data);
            
            // Створюємо blob та завантажуємо
            const blob = new Blob([reportHtml], { type: 'text/html' });
            const url = URL.createObjectURL(blob);
            
            await chrome.downloads.download({
                url: url,
                filename: `accessibility-report-${new Date().toISOString().split('T')[0]}.html`,
                saveAs: true
            });
            
        } catch (error) {
            console.error('Export error:', error);
            throw error;
        }
    }

    generateReportHtml(data) {
        const { results, url, timestamp } = data;
        const date = new Date(timestamp).toLocaleDateString('uk-UA');
        
        return `
            <!DOCTYPE html>
            <html lang="uk">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Звіт доступності - ${url}</title>
                <style>
                    body { 
                        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                        line-height: 1.6; 
                        margin: 0; 
                        padding: 40px; 
                        background: #f8f9fa; 
                    }
                    .container { 
                        max-width: 800px; 
                        margin: 0 auto; 
                        background: white; 
                        padding: 40px; 
                        border-radius: 8px; 
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1); 
                    }
                    .header { 
                        border-bottom: 3px solid #007bff; 
                        padding-bottom: 20px; 
                        margin-bottom: 30px; 
                    }
                    .score { 
                        font-size: 48px; 
                        font-weight: bold; 
                        color: #28a745; 
                        text-align: center; 
                        margin: 20px 0; 
                    }
                    .metrics { 
                        display: grid; 
                        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                        gap: 20px; 
                        margin: 30px 0; 
                    }
                    .metric { 
                        padding: 20px; 
                        border: 2px solid #e9ecef; 
                        border-radius: 8px; 
                        text-align: center; 
                    }
                    .metric-score { 
                        font-size: 24px; 
                        font-weight: bold; 
                        margin: 10px 0; 
                    }
                    .issues { 
                        margin-top: 30px; 
                    }
                    .issue { 
                        margin: 10px 0; 
                        padding: 15px; 
                        background: #f8f9fa; 
                        border-left: 4px solid #dc3545; 
                        border-radius: 4px; 
                    }
                    .footer { 
                        margin-top: 40px; 
                        padding-top: 20px; 
                        border-top: 1px solid #dee2e6; 
                        text-align: center; 
                        color: #6c757d; 
                        font-size: 14px; 
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🔍 Звіт доступності веб-сторінки</h1>
                        <p><strong>URL:</strong> ${url}</p>
                        <p><strong>Дата аналізу:</strong> ${date}</p>
                    </div>
                    
                    <div class="score">${Math.round(results.totalScore * 100)}%</div>
                    
                    <div class="metrics">
                        ${Object.entries(results.metrics).map(([key, value]) => `
                            <div class="metric">
                                <h3>${this.getMetricTitle(key)}</h3>
                                <div class="metric-score">${Math.round(value * 100)}%</div>
                            </div>
                        `).join('')}
                    </div>
                    
                    ${results.issues && results.issues.length > 0 ? `
                        <div class="issues">
                            <h2>🚨 Виявлені проблеми (${results.issues.length})</h2>
                            ${results.issues.map(issue => `
                                <div class="issue">
                                    <strong>${issue.severity}:</strong> ${issue.description}
                                    ${issue.element ? `<br><small>Елемент: ${issue.element}</small>` : ''}
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}
                    
                    <div class="footer">
                        <p>Згенеровано Accessibility Evaluator v${chrome.runtime.getManifest().version}</p>
                        <p>Більше інформації: <a href="https://github.com/your-repo/accessibility-evaluator">GitHub</a></p>
                    </div>
                </div>
            </body>
            </html>
        `;
    }

    getMetricTitle(key) {
        const titles = {
            perceptibility: '👁️ Сприйнятність',
            operability: '⚡ Керованість',
            understandability: '🧠 Зрозумілість',
            localization: '🌍 Локалізація'
        };
        return titles[key] || key;
    }

    getUrlKey(url) {
        return btoa(url).replace(/[^a-zA-Z0-9]/g, '').substring(0, 50);
    }
}

// Ініціалізація background script
new AccessibilityBackground();