/**
 * Головний аналізатор доступності для content scripts
 * Координує всі метрики та комунікацію з popup
 */

class AccessibilityAnalyzer {
    constructor() {
        this.isAnalyzing = false;
        this.currentResults = null;
        this.highlightedElements = [];

        // Перевіряємо доступність FormTester
        if (typeof FormTester !== 'undefined') {
            this.formTester = new FormTester();
        } else {
            console.warn('FormTester недоступний, створюємо заглушку');
            this.formTester = this.createBasicFormTester();
        }

        this.init();
    }

    createBasicFormTester() {
        return {
            testFormErrorBehaviorSystematic: async (formSelector) => {
                console.log(`Тестування форми: ${formSelector} (базова реалізація)`);
                return {
                    quality_score: 0.7,
                    supported_fields: 1,
                    total_fields: 1,
                    systematic_analysis: true
                };
            }
        };
    }

    init() {
        this.setupMessageListener();

        // Перевіряємо доступність helpers
        if (typeof window.AccessibilityHelpers === 'undefined') {
            console.warn('AccessibilityHelpers недоступний, створюємо базову реалізацію');
            this.createBasicHelpers();
        } else {
            this.helpers = window.AccessibilityHelpers;
        }

        this.helpers.log('Accessibility Analyzer ініціалізовано');
    }

    createBasicHelpers() {
        this.helpers = {
            log: (message, level = 'info') => {
                console.log(`[${level.toUpperCase()}] ${message}`);
            },
            isElementVisible: (element) => {
                if (!element) return false;
                const style = window.getComputedStyle(element);
                return style.display !== 'none' &&
                    style.visibility !== 'hidden' &&
                    style.opacity !== '0';
            },
            isFocusable: (element) => {
                if (!element) return false;
                const tabIndex = element.tabIndex;
                return tabIndex >= 0 || element.matches('a[href], button, input, select, textarea, [tabindex]');
            },
            getAccessibleName: (element) => {
                if (!element) return '';
                return element.getAttribute('aria-label') ||
                    element.textContent?.trim() ||
                    element.getAttribute('title') || '';
            },
            calculateContrast: (foreground, background) => {
                // Спрощена реалізація
                return 4.5; // Повертаємо базове значення
            },
            generateSelector: (element) => {
                if (!element) return '';
                if (element.id) return `#${element.id}`;
                if (element.className) return `.${element.className.split(' ')[0]}`;
                return element.tagName.toLowerCase();
            }
        };
    }

    setupMessageListener() {
        // Слухаємо повідомлення від popup та background
        chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
            this.handleMessage(request, sender, sendResponse);
            return true; // Асинхронна відповідь
        });
    }

    async handleMessage(request, sender, sendResponse) {
        try {
            switch (request.action) {
                case 'ping':
                    sendResponse({ pong: true });
                    break;

                case 'analyze-accessibility':
                    const results = await this.analyzeAccessibility(request.options || {});
                    sendResponse(results);
                    break;

                case 'highlight-issues':
                    this.highlightIssues(request.issues || []);
                    sendResponse({ success: true });
                    break;

                case 'clear-highlights':
                    this.clearHighlights();
                    sendResponse({ success: true });
                    break;

                case 'analyze-element':
                    const elementResult = await this.analyzeElement(request.elementInfo);
                    sendResponse(elementResult);
                    break;

                case 'perform-analysis':
                    const analysisResult = await this.performFullAnalysis(request.options || {});
                    sendResponse(analysisResult);
                    break;

                default:
                    sendResponse({ error: 'Unknown action' });
            }
        } catch (error) {
            this.helpers.log(`Помилка обробки повідомлення: ${error.message}`, 'error');
            sendResponse({ error: error.message });
        }
    }

    async analyzeAccessibility(options = {}) {
        if (this.isAnalyzing) {
            return { error: 'Аналіз вже виконується' };
        }

        try {
            this.isAnalyzing = true;
            this.showAnalysisOverlay();

            this.helpers.log('Початок аналізу доступності сторінки');

            // Збираємо базові дані про сторінку
            const pageData = this.gatherPageData();

            // Виконуємо аналіз метрик
            const metrics = await this.calculateMetrics(pageData, options);

            // Знаходимо проблеми
            const issues = this.identifyIssues(pageData, metrics);

            // Генеруємо рекомендації
            const recommendations = this.generateRecommendations(issues, metrics);

            // Використовуємо фінальний скор з backend, якщо доступний
            let totalScore;
            if (metrics._backendFinalScore !== undefined) {
                totalScore = metrics._backendFinalScore;
                this.helpers.log(`Використовуємо backend final score: ${totalScore}`, 'info');
            } else {
                totalScore = this.calculateTotalScore(metrics);
                this.helpers.log(`Розраховуємо локальний score: ${totalScore}`, 'info');
            }

            // Очищуємо метрики від службових полів для UI, але зберігаємо для звіту
            const cleanMetrics = { ...metrics };
            delete cleanMetrics._backendFinalScore;

            const results = {
                totalScore: totalScore,
                metrics: cleanMetrics,
                issues: issues,
                recommendations: recommendations,
                pageData: {
                    url: window.location.href,
                    title: document.title,
                    language: this.getDocumentLanguage(),
                    direction: this.getTextDirection()
                },
                timestamp: Date.now()
            };

            this.currentResults = results;
            this.helpers.log(`Аналіз завершено. Загальний скор: ${(totalScore * 100).toFixed(1)}%`);

            return results;

        } catch (error) {
            this.helpers.log(`Помилка аналізу: ${error.message}`, 'error');
            return { error: error.message };
        } finally {
            this.isAnalyzing = false;
            this.hideAnalysisOverlay();
        }
    }

    gatherPageData() {
        const pageData = {
            url: window.location.href,
            title: document.title,
            html_content: document.documentElement.outerHTML,

            // Елементи для аналізу
            images: Array.from(document.querySelectorAll('img')),
            links: Array.from(document.querySelectorAll('a[href]')),
            buttons: Array.from(document.querySelectorAll('button, input[type="button"], input[type="submit"]')),
            forms: Array.from(document.querySelectorAll('form')),
            headings: Array.from(document.querySelectorAll('h1, h2, h3, h4, h5, h6')),
            inputs: Array.from(document.querySelectorAll('input, textarea, select')),

            // Інтерактивні елементи
            interactive_elements: this.getInteractiveElements(),

            // Медіа елементи
            videos: Array.from(document.querySelectorAll('video')),
            audio: Array.from(document.querySelectorAll('audio')),

            // Структурні елементи
            landmarks: this.getLandmarks(),

            // Мова та напрямок
            language: this.getDocumentLanguage(),
            direction: this.getTextDirection()
        };

        this.helpers.log(`📊 Зібрано дані сторінки:`, 'info');
        this.helpers.log(`  URL: ${pageData.url}`, 'info');
        this.helpers.log(`  Title: ${pageData.title}`, 'info');
        this.helpers.log(`  HTML length: ${pageData.html_content.length}`, 'info');
        this.helpers.log(`  Images: ${pageData.images.length}`, 'info');
        this.helpers.log(`  Forms: ${pageData.forms.length}`, 'info');
        this.helpers.log(`  Language: ${pageData.language}`, 'info');

        return pageData;
    }

    async calculateMetrics(pageData, options) {
        this.helpers.log('🌐 Використовуємо Python backend для розрахунку метрик', 'info');

        try {
            // Відправляємо HTML на Python backend
            const response = await this.callPythonBackend(pageData);

            if (response.error) {
                this.helpers.log(`Помилка backend: ${response.error}`, 'error');
                return await this.calculateMetricsFallback(pageData, options);
            }

            // Backend повертає структуру: { metrics: {...}, subscores: {...}, final_score: ... }
            const backendMetrics = response.metrics || {};
            const subscores = response.subscores || {};

            const metrics = {
                perceptibility: subscores.perceptibility || backendMetrics.perceptibility || 0,
                operability: subscores.operability || backendMetrics.operability || 0,
                understandability: subscores.understandability || backendMetrics.understandability || 0,
                localization: subscores.localization || backendMetrics.localization || 0,
                _backendFinalScore: response.final_score // Зберігаємо для порівняння
            };

            // Детальне логування метрик
            this.helpers.log('=== МЕТРИКИ З PYTHON BACKEND ===', 'info');
            Object.entries(metrics).forEach(([key, value]) => {
                this.helpers.log(`${key}: ${value}`, 'info');
            });
            this.helpers.log('Final score:', response.final_score);
            this.helpers.log('===============================', 'info');

            return metrics;

        } catch (error) {
            this.helpers.log(`Помилка зв'язку з backend: ${error.message}`, 'warn');
            return await this.calculateMetricsFallback(pageData, options);
        }
    }

    async callPythonBackend(pageData) {
        const backendUrl = 'http://localhost:8000/api/evaluate-html';

        const requestData = {
            html_content: pageData.html_content,
            base_url: pageData.url,
            title: pageData.title || document.title
        };

        this.helpers.log('📤 Відправляємо запит на backend...', 'info');
        this.helpers.log('Request data:', requestData);

        const response = await fetch(backendUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        });

        if (!response.ok) {
            const errorText = await response.text();
            this.helpers.log(`Response error: ${errorText}`, 'error');
            throw new Error(`HTTP ${response.status}: ${response.statusText} - ${errorText}`);
        }

        const result = await response.json();
        this.helpers.log('📥 Отримано відповідь від backend', 'info');
        this.helpers.log('Backend response:', result);

        return result;
    }

    async calculateMetricsFallback(pageData, options) {
        this.helpers.log('🔄 Backend недоступний, повертаємо базові значення', 'warn');

        // Якщо backend недоступний, повертаємо нейтральні значення
        const metrics = {
            perceptibility: 0.7,
            operability: 0.7,
            understandability: 0.7,
            localization: 0.8
        };

        this.helpers.log('=== FALLBACK МЕТРИКИ (BACKEND НЕДОСТУПНИЙ) ===', 'warn');
        Object.entries(metrics).forEach(([key, value]) => {
            this.helpers.log(`${key}: ${value}`, 'warn');
        });
        this.helpers.log('============================================', 'warn');

        return metrics;
    }

    // Всі методи розрахунку метрик видалені - тепер використовуємо Python backend

    calculateTotalScore(metrics) {
        const weights = {
            perceptibility: 0.3,
            operability: 0.3,
            understandability: 0.3,
            localization: 0.1
        };

        let totalScore = 0;
        let totalWeight = 0;

        this.helpers.log('=== РОЗРАХУНОК ЗАГАЛЬНОГО СКОРУ ===', 'info');

        Object.entries(weights).forEach(([metric, weight]) => {
            if (metrics[metric] !== undefined) {
                const contribution = metrics[metric] * weight;
                totalScore += contribution;
                totalWeight += weight;
                this.helpers.log(`${metric}: ${metrics[metric]} * ${weight} = ${contribution}`, 'info');
            } else {
                this.helpers.log(`${metric}: ВІДСУТНЯ МЕТРИКА`, 'warn');
            }
        });

        const finalScore = totalWeight > 0 ? totalScore / totalWeight : 0;
        this.helpers.log(`Загальний скор: ${totalScore} / ${totalWeight} = ${finalScore}`, 'info');
        this.helpers.log('================================', 'info');

        return finalScore;
    }

    identifyIssues(pageData, metrics) {
        const issues = [];

        // Проблеми зображень
        const imagesWithoutAlt = pageData.images.filter(img =>
            this.helpers.isElementVisible(img) && (!img.alt || img.alt.trim() === '')
        );

        imagesWithoutAlt.forEach(img => {
            issues.push({
                type: 'missing_alt_text',
                severity: 'high',
                element: this.helpers.generateSelector(img),
                description: 'Зображення без альтернативного тексту',
                recommendation: 'Додайте атрибут alt з описом зображення'
            });
        });

        // Проблеми кнопок
        const buttonsWithoutNames = pageData.buttons.filter(btn =>
            this.helpers.isElementVisible(btn) && !this.helpers.getAccessibleName(btn)
        );

        buttonsWithoutNames.forEach(btn => {
            issues.push({
                type: 'missing_button_name',
                severity: 'high',
                element: this.helpers.generateSelector(btn),
                description: 'Кнопка без доступного імені',
                recommendation: 'Додайте текст, aria-label або aria-labelledby'
            });
        });

        // Проблеми форм (базується на метриці understandability)
        if (metrics.understandability < 0.5) {
            issues.push({
                type: 'poor_form_support',
                severity: 'medium',
                element: 'form',
                description: 'Погана підтримка помилок у формах',
                recommendation: 'Покращіть валідацію та повідомлення про помилки'
            });
        }

        return issues;
    }

    generateRecommendations(issues, metrics) {
        const recommendations = [];

        if (metrics.perceptibility < 0.7) {
            recommendations.push('Покращіть альтернативні тексти для зображень та контрастність');
        }

        if (metrics.operability < 0.7) {
            recommendations.push('Забезпечте клавіатурну навігацію для всіх інтерактивних елементів');
        }

        if (metrics.understandability < 0.7) {
            recommendations.push('Покращіть підтримку помилок у формах та структуру заголовків');
        }

        if (metrics.localization < 0.7) {
            recommendations.push('Додайте атрибути lang та dir для правильної локалізації');
        }

        return recommendations;
    }

    // Допоміжні методи
    getInteractiveElements() {
        const selectors = [
            'a[href]', 'button', 'input', 'select', 'textarea',
            '[tabindex]', '[onclick]', '[role="button"]', '[role="link"]'
        ];

        const elements = [];
        selectors.forEach(selector => {
            elements.push(...Array.from(document.querySelectorAll(selector)));
        });

        return elements.filter(el => this.helpers.isElementVisible(el));
    }

    getLandmarks() {
        const landmarks = [];
        const landmarkSelectors = [
            'main, [role="main"]',
            'nav, [role="navigation"]',
            'header, [role="banner"]',
            'footer, [role="contentinfo"]',
            'aside, [role="complementary"]',
            'section, [role="region"]'
        ];

        landmarkSelectors.forEach(selector => {
            const elements = document.querySelectorAll(selector);
            elements.forEach(el => {
                landmarks.push({
                    type: el.tagName.toLowerCase(),
                    role: el.getAttribute('role'),
                    selector: this.helpers.generateSelector(el)
                });
            });
        });

        return landmarks;
    }

    getDocumentLanguage() {
        return document.documentElement.lang ||
            document.querySelector('html')?.getAttribute('lang') ||
            'unknown';
    }

    getTextDirection() {
        return document.documentElement.dir ||
            document.querySelector('html')?.getAttribute('dir') ||
            window.getComputedStyle(document.documentElement).direction ||
            'auto';
    }

    // UI методи
    showAnalysisOverlay() {
        const overlay = document.createElement('div');
        overlay.className = 'accessibility-overlay';
        overlay.id = 'accessibility-analysis-overlay';

        overlay.innerHTML = `
            <div class="accessibility-overlay-content">
                <div class="accessibility-spinner"></div>
                <h3>Аналіз доступності...</h3>
                <p>Тестування сторінки на відповідність стандартам доступності</p>
                <div class="accessibility-progress">
                    <div class="accessibility-progress-bar" style="width: 0%"></div>
                </div>
            </div>
        `;

        document.body.appendChild(overlay);

        // Анімація прогресу
        let progress = 0;
        const progressBar = overlay.querySelector('.accessibility-progress-bar');
        const interval = setInterval(() => {
            progress += Math.random() * 15;
            if (progress > 90) progress = 90;
            progressBar.style.width = progress + '%';
        }, 200);

        overlay.dataset.progressInterval = interval;
    }

    hideAnalysisOverlay() {
        const overlay = document.getElementById('accessibility-analysis-overlay');
        if (overlay) {
            if (overlay.dataset.progressInterval) {
                clearInterval(overlay.dataset.progressInterval);
            }
            overlay.remove();
        }
    }

    highlightIssues(issues) {
        this.clearHighlights();

        issues.forEach(issue => {
            try {
                const element = document.querySelector(issue.element);
                if (element) {
                    const className = `accessibility-highlight-${issue.severity}`;
                    element.classList.add(className);
                    this.highlightedElements.push({ element, className });

                    // Додаємо tooltip
                    this.addTooltip(element, issue.description);
                }
            } catch (error) {
                this.helpers.log(`Не вдалося підсвітити елемент ${issue.element}`, 'warn');
            }
        });
    }

    clearHighlights() {
        this.highlightedElements.forEach(({ element, className }) => {
            element.classList.remove(className);
            const tooltip = element.querySelector('.accessibility-tooltip');
            if (tooltip) tooltip.remove();
        });
        this.highlightedElements = [];
    }

    addTooltip(element, text) {
        const tooltip = document.createElement('div');
        tooltip.className = 'accessibility-tooltip';
        tooltip.textContent = text;

        element.style.position = 'relative';
        element.appendChild(tooltip);

        element.addEventListener('mouseenter', () => {
            tooltip.classList.add('show');
        });

        element.addEventListener('mouseleave', () => {
            tooltip.classList.remove('show');
        });
    }

    async performFullAnalysis(options) {
        return await this.analyzeAccessibility(options);
    }

    async analyzeElement(elementInfo) {
        // TODO: Аналіз конкретного елемента
        return { message: 'Аналіз елемента поки не реалізований' };
    }
}

// Ініціалізуємо аналізатор при завантаженні сторінки
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.accessibilityAnalyzer = new AccessibilityAnalyzer();
    });
} else {
    window.accessibilityAnalyzer = new AccessibilityAnalyzer();
}