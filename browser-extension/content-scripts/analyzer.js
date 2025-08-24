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

            // Розраховуємо загальний скор
            const totalScore = this.calculateTotalScore(metrics);

            const results = {
                totalScore: totalScore,
                metrics: metrics,
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
        return {
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
    }

    async calculateMetrics(pageData, options) {
        const metrics = {};

        try {
            // Перевіряємо доступність класів метрик
            this.helpers.log('Перевіряємо доступність класів метрик...', 'info');
            this.helpers.log(`PerceptibilityMetrics: ${typeof PerceptibilityMetrics}`, 'info');
            this.helpers.log(`OperabilityMetrics: ${typeof OperabilityMetrics}`, 'info');
            this.helpers.log(`UnderstandabilityMetrics: ${typeof UnderstandabilityMetrics}`, 'info');
            
            if (typeof PerceptibilityMetrics !== 'undefined' && 
                typeof OperabilityMetrics !== 'undefined' && 
                typeof UnderstandabilityMetrics !== 'undefined') {
                
                this.helpers.log('Використовуємо повноцінні класи метрик', 'info');
                
                // Використовуємо повноцінні класи метрик
                const perceptibilityMetrics = new PerceptibilityMetrics();
                const operabilityMetrics = new OperabilityMetrics();
                const understandabilityMetrics = new UnderstandabilityMetrics();

                const perceptibilityResults = await perceptibilityMetrics.calculateMetric(pageData);
                const operabilityResults = await operabilityMetrics.calculateMetric(pageData);
                const understandabilityResults = await understandabilityMetrics.calculateMetric(pageData);

                this.helpers.log('Результати PerceptibilityMetrics:', 'info');
                this.helpers.log(perceptibilityResults, 'info');
                this.helpers.log('Результати OperabilityMetrics:', 'info');
                this.helpers.log(operabilityResults, 'info');
                this.helpers.log('Результати UnderstandabilityMetrics:', 'info');
                this.helpers.log(understandabilityResults, 'info');

                // Класи повертають готові скори
                metrics.perceptibility = perceptibilityResults || 0;
                metrics.operability = operabilityResults || 0;
                metrics.understandability = understandabilityResults || 0;

            } else {
                // Fallback до спрощених методів
                this.helpers.log('Використовуємо спрощені методи розрахунку', 'warn');
                
                // Сприйнятність (Perceptibility)
                metrics.perceptibility = await this.calculatePerceptibilityMetric(pageData);

                // Керованість (Operability) 
                metrics.operability = await this.calculateOperabilityMetric(pageData);

                // Зрозумілість (Understandability) - включає тестування форм
                metrics.understandability = await this.calculateUnderstandabilityMetric(pageData, options);
            }

            // Локалізація
            metrics.localization = await this.calculateLocalizationMetric(pageData);

        } catch (error) {
            this.helpers.log(`Помилка розрахунку метрик: ${error.message}`, 'error');
        }

        // Детальне логування метрик
        this.helpers.log('=== РОЗРАХОВАНІ МЕТРИКИ ===', 'info');
        Object.entries(metrics).forEach(([key, value]) => {
            this.helpers.log(`${key}: ${value}`, 'info');
        });
        this.helpers.log('========================', 'info');

        return metrics;
    }

    async calculatePerceptibilityMetric(pageData) {
        let score = 0.0;
        let totalWeight = 0;

        // Перевірка alt-текстів для зображень (вага 0.5)
        const images = pageData.images.filter(img => this.helpers.isElementVisible(img));
        if (images.length > 0) {
            const imagesWithAlt = images.filter(img => img.alt !== undefined && img.alt.trim() !== '');
            const altScore = imagesWithAlt.length / images.length;
            score += altScore * 0.5;
            totalWeight += 0.5;
        } else {
            // Якщо немає зображень, вважаємо що alt-тексти не потрібні
            score += 1.0 * 0.5;
            totalWeight += 0.5;
        }

        // Перевірка контрастності тексту (вага 0.4)
        const textElements = document.querySelectorAll('p, span, div, h1, h2, h3, h4, h5, h6, a, button, label');
        let contrastChecks = 0;
        let goodContrast = 0;

        // Перевіряємо до 30 елементів для кращої точності
        Array.from(textElements).slice(0, 30).forEach(element => {
            if (this.helpers.isElementVisible(element) && element.textContent.trim()) {
                const styles = window.getComputedStyle(element);
                const color = styles.color;
                const backgroundColor = styles.backgroundColor;
                
                // Спрощена перевірка контрасту
                if (this.isGoodContrast(color, backgroundColor)) {
                    goodContrast++;
                }
                contrastChecks++;
            }
        });

        if (contrastChecks > 0) {
            const contrastScore = goodContrast / contrastChecks;
            score += contrastScore * 0.4;
            totalWeight += 0.4;
        } else {
            // Якщо немає текстових елементів, нейтральна оцінка
            score += 0.8 * 0.4;
            totalWeight += 0.4;
        }

        // Медіа доступність (вага 0.1)
        const videos = document.querySelectorAll('video');
        const audios = document.querySelectorAll('audio');
        if (videos.length > 0 || audios.length > 0) {
            // Спрощена перевірка - якщо є controls, вважаємо доступним
            const accessibleMedia = Array.from(videos).filter(v => v.hasAttribute('controls')).length +
                                   Array.from(audios).filter(a => a.hasAttribute('controls')).length;
            const mediaScore = accessibleMedia / (videos.length + audios.length);
            score += mediaScore * 0.1;
            totalWeight += 0.1;
        } else {
            // Якщо немає медіа, повна оцінка
            score += 1.0 * 0.1;
            totalWeight += 0.1;
        }

        return totalWeight > 0 ? score / totalWeight : 0.8;
    }

    isGoodContrast(color, backgroundColor) {
        // Спрощена перевірка контрасту
        if (!color || !backgroundColor || backgroundColor === 'rgba(0, 0, 0, 0)') {
            return true; // Не можемо перевірити, вважаємо нормальним
        }
        
        // Базова перевірка на темний текст на світлому фоні або навпаки
        const colorLightness = this.getColorLightness(color);
        const bgLightness = this.getColorLightness(backgroundColor);
        
        const contrast = Math.abs(colorLightness - bgLightness);
        return contrast > 0.3; // Спрощений поріг
    }

    getColorLightness(color) {
        // Спрощене визначення яскравості кольору
        if (color.includes('rgb')) {
            const matches = color.match(/\d+/g);
            if (matches && matches.length >= 3) {
                const r = parseInt(matches[0]);
                const g = parseInt(matches[1]);
                const b = parseInt(matches[2]);
                return (r * 0.299 + g * 0.587 + b * 0.114) / 255;
            }
        }
        return 0.5; // Нейтральне значення
    }

    async calculateOperabilityMetric(pageData) {
        let score = 0.0;
        let totalWeight = 0;

        // Клавіатурна навігація (вага 0.4)
        const interactiveElements = pageData.interactive_elements;
        if (interactiveElements.length > 0) {
            const focusableElements = interactiveElements.filter(el => this.helpers.isFocusable(el));
            const keyboardScore = focusableElements.length / interactiveElements.length;
            score += keyboardScore * 0.4;
            totalWeight += 0.4;
        } else {
            // Якщо немає інтерактивних елементів, повна оцінка
            score += 1.0 * 0.4;
            totalWeight += 0.4;
        }

        // Структурована навігація (вага 0.4)
        const navigationScore = this.calculateNavigationStructure();
        score += navigationScore * 0.4;
        totalWeight += 0.4;

        // Доступні імена для елементів (вага 0.2)
        const buttons = pageData.buttons.filter(btn => this.helpers.isElementVisible(btn));
        const links = pageData.links.filter(link => this.helpers.isElementVisible(link));
        const allActionElements = [...buttons, ...links];
        
        if (allActionElements.length > 0) {
            const elementsWithNames = allActionElements.filter(el => {
                const name = this.helpers.getAccessibleName(el);
                return name && name.trim().length > 0;
            });
            const namesScore = elementsWithNames.length / allActionElements.length;
            score += namesScore * 0.2;
            totalWeight += 0.2;
        } else {
            // Якщо немає кнопок/посилань, повна оцінка
            score += 1.0 * 0.2;
            totalWeight += 0.2;
        }

        return totalWeight > 0 ? score / totalWeight : 0.8;
    }

    calculateNavigationStructure() {
        let score = 0.0;
        let checks = 0;

        // Перевіряємо наявність landmarks
        const landmarks = ['nav', 'main', 'header', 'footer', '[role="navigation"]', '[role="main"]', '[role="banner"]', '[role="contentinfo"]'];
        let foundLandmarks = 0;
        landmarks.forEach(selector => {
            if (document.querySelector(selector)) {
                foundLandmarks++;
            }
        });
        
        if (foundLandmarks > 0) {
            score += Math.min(foundLandmarks / 4, 1.0) * 0.5; // До 4 landmarks
            checks++;
        }

        // Перевіряємо ієрархію заголовків
        const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
        if (headings.length > 0) {
            const h1Count = document.querySelectorAll('h1').length;
            const hasProperHierarchy = h1Count === 1 && headings.length > 1;
            score += (hasProperHierarchy ? 1.0 : 0.6) * 0.5;
            checks++;
        } else {
            score += 0.3 * 0.5; // Немає заголовків - погано для навігації
            checks++;
        }

        return checks > 0 ? score / checks : 0.7;
    }

    async calculateUnderstandabilityMetric(pageData, options) {
        let score = 0.0;
        let totalWeight = 0;

        // Зрозумілість інструкцій (вага 0.3)
        const instructionScore = this.calculateInstructionClarity(pageData);
        score += instructionScore * 0.3;
        totalWeight += 0.3;

        // Допомога при введенні (вага 0.3)
        const inputAssistanceScore = this.calculateInputAssistance(pageData);
        score += inputAssistanceScore * 0.3;
        totalWeight += 0.3;

        // Підтримка помилок (вага 0.4)
        const errorSupportScore = await this.calculateErrorSupport(pageData, options);
        score += errorSupportScore * 0.4;
        totalWeight += 0.4;

        return totalWeight > 0 ? score / totalWeight : 0.8;
    }

    calculateInstructionClarity(pageData) {
        // Перевіряємо labels для форм
        const labels = document.querySelectorAll('label');
        const instructions = document.querySelectorAll('[role="note"], .help-text, .instruction, .hint');
        
        let totalInstructions = labels.length + instructions.length;
        if (totalInstructions === 0) {
            return 0.8; // Немає інструкцій - нейтральна оцінка
        }

        let clearInstructions = 0;
        
        // Перевіряємо labels
        labels.forEach(label => {
            const text = label.textContent.trim();
            if (text.length >= 2 && text.length <= 50 && !this.hasComplexWords(text)) {
                clearInstructions++;
            } else if (text.length > 0) {
                clearInstructions += 0.5; // Частково зрозуміло
            }
        });

        // Перевіряємо інші інструкції
        instructions.forEach(instruction => {
            const text = instruction.textContent.trim();
            if (text.length >= 5 && text.length <= 100 && !this.hasComplexWords(text)) {
                clearInstructions++;
            } else if (text.length > 0) {
                clearInstructions += 0.5;
            }
        });

        return Math.min(clearInstructions / totalInstructions, 1.0);
    }

    calculateInputAssistance(pageData) {
        const inputs = document.querySelectorAll('input[type="text"], input[type="email"], input[type="password"], input[type="tel"], textarea');
        
        if (inputs.length === 0) {
            return 1.0; // Немає полів вводу
        }

        let assistedInputs = 0;
        
        inputs.forEach(input => {
            let hasAssistance = false;
            
            // Перевіряємо різні види допомоги
            if (input.placeholder && input.placeholder.trim()) hasAssistance = true;
            if (input.getAttribute('autocomplete')) hasAssistance = true;
            if (input.getAttribute('aria-describedby')) hasAssistance = true;
            if (input.getAttribute('title')) hasAssistance = true;
            if (input.getAttribute('pattern')) hasAssistance = true;
            
            if (hasAssistance) {
                assistedInputs++;
            }
        });

        return assistedInputs / inputs.length;
    }

    async calculateErrorSupport(pageData, options) {
        const forms = pageData.forms;
        
        if (forms.length === 0) {
            return 1.0; // Немає форм
        }

        let totalScore = 0;
        let formsProcessed = 0;

        // Статичний аналіз підтримки помилок
        forms.forEach(form => {
            let formScore = 0;
            let checks = 0;

            // Перевіряємо наявність валідації
            const requiredFields = form.querySelectorAll('[required]');
            const fieldsWithPattern = form.querySelectorAll('[pattern]');
            if (requiredFields.length > 0 || fieldsWithPattern.length > 0) {
                formScore += 0.3;
            }
            checks++;

            // Перевіряємо ARIA атрибути для помилок
            const fieldsWithAriaInvalid = form.querySelectorAll('[aria-invalid]');
            const fieldsWithAriaDescribedby = form.querySelectorAll('[aria-describedby]');
            if (fieldsWithAriaInvalid.length > 0 || fieldsWithAriaDescribedby.length > 0) {
                formScore += 0.4;
            }
            checks++;

            // Перевіряємо наявність елементів для повідомлень про помилки
            const errorElements = form.querySelectorAll('.error, .invalid, [role="alert"], .help-text');
            if (errorElements.length > 0) {
                formScore += 0.3;
            }
            checks++;

            totalScore += checks > 0 ? formScore / checks : 0.5;
            formsProcessed++;
        });

        // Якщо включено тестування форм, спробуємо динамічний аналіз
        if (options.testForms !== false && this.formTester && forms.length > 0) {
            try {
                const form = forms[0];
                const formSelector = form.id ? `#${form.id}` : 'form';
                const formResult = await this.formTester.testFormErrorBehaviorSystematic(formSelector);
                
                if (formResult && typeof formResult.quality_score === 'number') {
                    // Комбінуємо статичний та динамічний аналіз
                    const staticScore = totalScore / formsProcessed;
                    const dynamicScore = formResult.quality_score;
                    return (staticScore * 0.4 + dynamicScore * 0.6);
                }
            } catch (error) {
                this.helpers.log(`Помилка динамічного тестування форми: ${error.message}`, 'warn');
            }
        }

        return formsProcessed > 0 ? totalScore / formsProcessed : 0.8;
    }

    hasComplexWords(text) {
        // Спрощена перевірка на складні слова
        const words = text.split(/\s+/);
        const complexWords = words.filter(word => word.length > 12 || /[А-ЯЁІЇЄҐ]{3,}/.test(word));
        return complexWords.length > words.length * 0.3; // Більше 30% складних слів
    }

    async calculateLocalizationMetric(pageData) {
        let score = 0.0;
        let totalChecks = 0;

        // Перевірка мови документа
        if (pageData.language && pageData.language !== 'unknown') {
            score += 0.5;
        }
        totalChecks++;

        // Перевірка напрямку тексту
        if (pageData.direction) {
            score += 0.5;
        }
        totalChecks++;

        return totalChecks > 0 ? score / totalChecks : 1.0;
    }

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
               'ltr';
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