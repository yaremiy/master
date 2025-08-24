/**
 * Understandability Metrics - Метрики зрозумілості
 * Портовано з Python коду з повним збереженням гібридної логіки
 */

class UnderstandabilityMetrics extends BaseMetrics {
    constructor() {
        super();
        this.metricName = 'understandability';
        this.formTester = new FormTester();
    }

    /**
     * Розрахунок загальної метрики зрозумілості
     */
    async calculateMetric(pageData) {
        this.helpers.log('🧠 Розрахунок метрики зрозумілості...');

        const metrics = {
            errorSupport: await this.calculateErrorSupportMetricEnhanced(pageData),
            headingStructure: await this.calculateHeadingStructure(pageData),
            linkPurpose: await this.calculateLinkPurpose(pageData),
            readability: await this.calculateReadability(pageData)
        };

        // Вагові коефіцієнти для підметрик
        const weights = {
            errorSupport: 0.4,      // 40% - найважливіше (форми)
            headingStructure: 0.25, // 25% - структура контенту
            linkPurpose: 0.2,       // 20% - зрозумілість посилань
            readability: 0.15       // 15% - читабельність тексту
        };

        let totalScore = 0;
        let totalWeight = 0;

        Object.entries(weights).forEach(([metric, weight]) => {
            if (metrics[metric] !== undefined && metrics[metric] !== null) {
                totalScore += metrics[metric] * weight;
                totalWeight += weight;
            }
        });

        const finalScore = totalWeight > 0 ? totalScore / totalWeight : 1.0;

        this.logResult('Understandability', finalScore,
            `ErrorSupport: ${(metrics.errorSupport * 100).toFixed(1)}%, ` +
            `Headings: ${(metrics.headingStructure * 100).toFixed(1)}%, ` +
            `Links: ${(metrics.linkPurpose * 100).toFixed(1)}%`
        );

        return finalScore;
    }

    /**
     * Розрахунок метрики підтримки помилок з покращеним аналізом
     * Використовує комбінацію статичного аналізу та динамічного тестування
     * 
     * Формула: X = (static_score * 0.4) + (dynamic_score * 0.6)
     */
    async calculateErrorSupportMetricEnhanced(pageData) {
        this.helpers.log('🚨 Детальний аналіз підтримки помилок (гібридний)...');

        const htmlContent = pageData.html_content || document.documentElement.outerHTML;
        const forms = pageData.forms || [];

        if (forms.length === 0) {
            // Шукаємо окремі поля
            const individualFields = document.querySelectorAll('input, textarea, select');
            if (individualFields.length === 0) {
                this.helpers.log('⚠️ Поля для валідації не знайдено - повертаємо 1.0');
                return 1.0;
            }
            // Обробляємо як одну віртуальну форму
            forms.push(document.body);
        }

        this.helpers.log(`📋 Знайдено форм: ${forms.length}`);

        // Статичний аналіз (40% ваги)
        this.helpers.log('📊 Статичний аналіз (40% ваги):');
        let staticTotalQuality = 0.0;

        for (let i = 0; i < forms.length; i++) {
            const form = forms[i];
            this.helpers.log(`🔍 Статичний аналіз форми ${i + 1}:`);
            
            const formQuality = this.analyzeFormErrorSupportQuality(form, htmlContent);
            staticTotalQuality += formQuality;
            
            this.helpers.log(`   🎯 Статична якість: ${formQuality.toFixed(3)}`);
        }

        const staticAverage = staticTotalQuality / forms.length;
        this.helpers.log(`📊 Середня статична якість: ${staticAverage.toFixed(3)}`);

        // Динамічний аналіз (60% ваги)
        this.helpers.log('🧪 Динамічний аналіз (60% ваги):');
        let dynamicAverage = 0.0;
        const dynamicResults = [];

        for (let i = 0; i < forms.length; i++) {
            const form = forms[i];
            try {
                const formSelector = form.id ? `#${form.id}` : 
                                   form.tagName === 'FORM' ? `form:nth-of-type(${i + 1})` : 
                                   'body';
                
                this.helpers.log(`🧪 Динамічне тестування форми ${i + 1}: ${formSelector}`);
                
                const testResult = await this.formTester.testFormErrorBehaviorSystematic(formSelector);
                
                if (testResult.error || testResult.reason) {
                    this.helpers.log(`❌ Форма ${i + 1}: Помилка тестування - ${testResult.error || testResult.reason}`);
                    dynamicResults.push(0.0);
                } else {
                    const dynamicQuality = testResult.quality_score || 0.0;
                    dynamicResults.push(dynamicQuality);
                    
                    this.helpers.log(`✅ Форма ${i + 1}: Динамічна якість = ${dynamicQuality.toFixed(3)}`);
                    
                    // Детальний розбір динамічного тестування
                    const breakdown = testResult.detailed_breakdown || {};
                    Object.entries(breakdown).forEach(([category, data]) => {
                        const score = data.score || 0.0;
                        const description = data.description || 'Немає опису';
                        this.helpers.log(`   📋 ${category}: ${score.toFixed(3)} - ${description}`);
                    });
                }
            } catch (error) {
                this.helpers.log(`❌ Помилка динамічного тестування форми ${i + 1}: ${error.message}`, 'error');
                dynamicResults.push(0.0);
            }
        }

        if (dynamicResults.length > 0) {
            const dynamicTotal = dynamicResults.reduce((sum, score) => sum + score, 0);
            dynamicAverage = dynamicTotal / dynamicResults.length;
            this.helpers.log(`📊 Середня динамічна якість: ${dynamicAverage.toFixed(3)}`);
        } else {
            this.helpers.log('⚠️ Жодного успішного динамічного тесту');
            dynamicAverage = 0.0;
        }

        // Комбінований скор
        let combinedScore;
        if (dynamicAverage > 0) {
            // Якщо є результати динамічного тестування, використовуємо гібридний підхід
            combinedScore = (staticAverage * 0.4) + (dynamicAverage * 0.6);
            this.helpers.log('🎯 Гібридний скор:');
            this.helpers.log(`   Статичний: ${staticAverage.toFixed(3)} × 0.4 = ${(staticAverage * 0.4).toFixed(3)}`);
            this.helpers.log(`   Динамічний: ${dynamicAverage.toFixed(3)} × 0.6 = ${(dynamicAverage * 0.6).toFixed(3)}`);
            this.helpers.log(`   Комбінований: ${combinedScore.toFixed(3)}`);
        } else {
            // Якщо немає динамічного тестування, використовуємо тільки статичний аналіз
            combinedScore = staticAverage;
            this.helpers.log(`⚠️ Використовується тільки статичний аналіз: ${combinedScore.toFixed(3)}`);
        }

        this.helpers.log(`📊 Фінальний скор підтримки помилок: ${combinedScore.toFixed(3)}`);
        return combinedScore;
    }

    /**
     * Аналіз якості підтримки помилок для форми (статичний)
     */
    analyzeFormErrorSupportQuality(form, htmlContent) {
        // Знаходимо всі поля в формі
        const fields = form.querySelectorAll('input, textarea, select');
        const validatableFields = Array.from(fields).filter(field => this.fieldNeedsValidation(field));

        if (validatableFields.length === 0) {
            return 1.0; // Немає полів для валідації
        }

        let totalQuality = 0.0;

        validatableFields.forEach(field => {
            const fieldQuality = this.analyzeFieldErrorSupport(field, htmlContent);
            totalQuality += fieldQuality;
        });

        return totalQuality / validatableFields.length;
    }

    /**
     * Перевірка чи поле потребує валідації
     */
    fieldNeedsValidation(field) {
        const fieldType = field.type || field.tagName.toLowerCase();
        
        return field.required ||
               field.pattern ||
               ['email', 'url', 'tel', 'number', 'date', 'time', 'datetime-local'].includes(fieldType) ||
               (field.minLength && field.minLength > 0) ||
               (field.maxLength && field.maxLength > 0 && field.maxLength < 524288) ||
               field.min !== '' ||
               field.max !== '';
    }

    /**
     * Аналіз підтримки помилок для окремого поля
     */
    analyzeFieldErrorSupport(field, htmlContent) {
        // Фазовий аналіз
        const phase1Score = this.phase1BasicErrorSupport(field, htmlContent);
        const phase2Score = this.phase2MessageQuality(field, htmlContent);
        const phase3Score = this.phase3DynamicValidation(field, htmlContent);

        return phase1Score + phase2Score + phase3Score;
    }

    /**
     * Фаза 1: Базові покращення (максимум 0.4)
     */
    phase1BasicErrorSupport(field, htmlContent) {
        let score = 0.0;

        // 1. Валідація (required/pattern) - 0.1
        if (field.required || field.pattern) {
            score += 0.1;
        }

        // 2. aria-invalid - 0.1
        if (field.hasAttribute('aria-invalid')) {
            score += 0.1;
        }

        // 3. aria-describedby зв'язок - 0.1
        const ariaDescribedby = field.getAttribute('aria-describedby');
        if (ariaDescribedby && this.checkAriaDescribedbyExists(ariaDescribedby, htmlContent)) {
            score += 0.1;
        }

        // 4. role="alert" елементи - 0.1
        if (this.checkAlertElementsExist(htmlContent)) {
            score += 0.1;
        }

        return score;
    }

    /**
     * Фаза 2: Якість повідомлень (максимум 0.3)
     */
    phase2MessageQuality(field, htmlContent) {
        const errorMessages = this.findErrorMessagesForField(field, htmlContent);
        
        if (errorMessages.length === 0) {
            return 0.0;
        }

        let totalQuality = 0.0;
        errorMessages.forEach(message => {
            totalQuality += this.assessErrorMessageQuality(message);
        });

        const averageQuality = totalQuality / errorMessages.length;
        return averageQuality * 0.3;
    }

    /**
     * Фаза 3: Динамічна валідація (максимум 0.3)
     */
    phase3DynamicValidation(field, htmlContent) {
        let score = 0.0;

        // 1. Live regions - 0.15
        if (this.checkLiveRegionsExist(htmlContent)) {
            score += 0.15;
        }

        // 2. JavaScript валідація - 0.15
        if (this.detectJavaScriptValidation(field, htmlContent)) {
            score += 0.15;
        }

        return score;
    }

    /**
     * Перевірка існування aria-describedby елементів
     */
    checkAriaDescribedbyExists(ariaDescribedby, htmlContent) {
        const ids = ariaDescribedby.split(' ');
        return ids.some(id => document.getElementById(id) !== null);
    }

    /**
     * Перевірка існування alert елементів
     */
    checkAlertElementsExist(htmlContent) {
        return document.querySelector('[role="alert"]') !== null;
    }

    /**
     * Пошук повідомлень про помилки для поля
     */
    findErrorMessagesForField(field, htmlContent) {
        const messages = [];

        // 1. aria-describedby
        const ariaDescribedby = field.getAttribute('aria-describedby');
        if (ariaDescribedby) {
            const ids = ariaDescribedby.split(' ');
            ids.forEach(id => {
                const element = document.getElementById(id);
                if (element && element.textContent.trim()) {
                    messages.push(element.textContent.trim());
                }
            });
        }

        // 2. Пошук поруч з полем
        const container = field.closest('div, fieldset, section') || field.parentElement;
        if (container) {
            const errorSelectors = [
                '.error', '.invalid', '.warning', '.alert',
                '.error-message', '.field-error', '.validation-error'
            ];

            errorSelectors.forEach(selector => {
                const errorElements = container.querySelectorAll(selector);
                errorElements.forEach(el => {
                    const text = el.textContent.trim();
                    if (text && !messages.includes(text)) {
                        messages.push(text);
                    }
                });
            });
        }

        return messages;
    }

    /**
     * Оцінка якості повідомлення про помилку
     */
    assessErrorMessageQuality(message) {
        let quality = 0.0;

        // Довжина (не занадто коротке/довге)
        const length = message.length;
        if (length >= 10 && length <= 100) {
            quality += 0.3;
        } else if (length >= 5 && length <= 150) {
            quality += 0.15;
        }

        // Конструктивність
        const constructiveWords = [
            'введіть', 'виберіть', 'перевірте', 'має містити', 'формат',
            'please', 'enter', 'select', 'check', 'must contain', 'format'
        ];
        if (constructiveWords.some(word => message.toLowerCase().includes(word.toLowerCase()))) {
            quality += 0.4;
        }

        // Специфічність
        const specificWords = [
            'email', 'пароль', 'телефон', 'дата', 'символів', 'цифр',
            'password', 'phone', 'date', 'characters', 'digits'
        ];
        if (specificWords.some(word => message.toLowerCase().includes(word.toLowerCase()))) {
            quality += 0.3;
        }

        return Math.min(quality, 1.0);
    }

    /**
     * Перевірка існування live regions
     */
    checkLiveRegionsExist(htmlContent) {
        return document.querySelector('[aria-live], [role="status"], [role="alert"]') !== null;
    }

    /**
     * Виявлення JavaScript валідації
     */
    detectJavaScriptValidation(field, htmlContent) {
        // Перевірка event listeners
        if (field.onblur || field.oninput || field.onchange) {
            return true;
        }

        // Перевірка атрибутів
        const eventAttributes = ['onblur', 'oninput', 'onchange', 'onkeyup'];
        if (eventAttributes.some(attr => field.hasAttribute(attr))) {
            return true;
        }

        // Евристичний пошук в HTML
        const validationKeywords = [
            'validate', 'validation', 'error', 'invalid',
            'валідація', 'перевірка', 'помилка'
        ];

        return validationKeywords.some(keyword => 
            htmlContent.toLowerCase().includes(keyword.toLowerCase())
        );
    }

    /**
     * Розрахунок структури заголовків
     */
    async calculateHeadingStructure(pageData) {
        const headings = pageData.headings || this.getHeadings();
        
        if (headings.length === 0) {
            return 1.0; // Немає заголовків = немає проблем
        }

        const headingStats = this.gatherElementStats(headings, (heading) => {
            return this.checkHeadingStructure(heading, headings);
        });

        return this.calculateSuccessRate(headingStats.passed, headingStats.total);
    }

    /**
     * Перевірка структури заголовка
     */
    checkHeadingStructure(heading, allHeadings) {
        const level = parseInt(heading.tagName.charAt(1));
        const text = this.getElementText(heading);
        const index = allHeadings.indexOf(heading);

        // Перевірка наявності тексту
        if (!text) {
            return this.createCheckResult(false, 'Заголовок без тексту', 'high');
        }

        // Перевірка довжини
        if (text.length < 2) {
            return this.createCheckResult(false, 'Заголовок занадто короткий', 'medium');
        }

        if (text.length > 120) {
            return this.createCheckResult(false, 'Заголовок занадто довгий', 'low');
        }

        // Перевірка логічної структури
        if (index > 0) {
            const prevHeading = allHeadings[index - 1];
            const prevLevel = parseInt(prevHeading.tagName.charAt(1));
            
            // Перевірка пропуску рівнів
            if (level > prevLevel + 1) {
                return this.createCheckResult(false, 
                    `Пропущено рівень заголовка (з h${prevLevel} на h${level})`, 'medium');
            }
        } else {
            // Перший заголовок має бути h1
            if (level !== 1) {
                return this.createCheckResult(false, 
                    `Перший заголовок має бути h1, а не h${level}`, 'medium');
            }
        }

        return this.createCheckResult(true, 'Заголовок правильно структурований', 'info', {
            level,
            text: text.substring(0, 50) + (text.length > 50 ? '...' : '')
        });
    }

    /**
     * Розрахунок призначення посилань
     */
    async calculateLinkPurpose(pageData) {
        const links = pageData.links || this.getLinks();
        
        if (links.length === 0) {
            return 1.0; // Немає посилань = немає проблем
        }

        const linkStats = this.gatherElementStats(links, (link) => {
            return this.checkLinkPurpose(link);
        });

        return this.calculateSuccessRate(linkStats.passed, linkStats.total);
    }

    /**
     * Перевірка призначення посилання
     */
    checkLinkPurpose(link) {
        const href = link.getAttribute('href');
        const text = this.getElementText(link);
        const ariaLabel = link.getAttribute('aria-label');
        const title = link.getAttribute('title');

        // Перевірка наявності href
        if (!href || href === '#') {
            return this.createCheckResult(false, 'Посилання без призначення (href="#" або відсутнє)', 'high');
        }

        // Отримання доступного імені
        const accessibleName = ariaLabel || text || title;
        
        if (!accessibleName) {
            return this.createCheckResult(false, 'Посилання без доступного імені', 'high');
        }

        // Перевірка якості тексту посилання
        const textQuality = this.assessLinkTextQuality(accessibleName, href);
        
        if (textQuality.score < 0.5) {
            return this.createCheckResult(false, 
                `Неякісний текст посилання: ${textQuality.issues.join(', ')}`, 'medium', textQuality);
        }

        return this.createCheckResult(true, 'Призначення посилання зрозуміле', 'info', {
            text: accessibleName,
            href: href.substring(0, 50) + (href.length > 50 ? '...' : ''),
            quality: textQuality.score
        });
    }

    /**
     * Оцінка якості тексту посилання
     */
    assessLinkTextQuality(text, href) {
        const issues = [];
        let score = 1.0;

        // Погані практики
        const badTexts = [
            'click here', 'here', 'read more', 'more', 'link',
            'клікніть тут', 'тут', 'читати далі', 'далі', 'посилання'
        ];

        if (badTexts.some(bad => text.toLowerCase().includes(bad.toLowerCase()))) {
            issues.push('загальний текст');
            score -= 0.4;
        }

        // Занадто короткий текст
        if (text.length < 3) {
            issues.push('занадто короткий');
            score -= 0.3;
        }

        // URL як текст
        if (text.includes('http') || text.includes('www.')) {
            issues.push('URL як текст');
            score -= 0.2;
        }

        // Повторювані символи
        if (/(.)\1{3,}/.test(text)) {
            issues.push('повторювані символи');
            score -= 0.1;
        }

        return {
            score: Math.max(score, 0),
            issues
        };
    }

    /**
     * Розрахунок читабельності
     */
    async calculateReadability(pageData) {
        const textElements = this.getTextElements();
        
        if (textElements.length === 0) {
            return 1.0;
        }

        // Обмежуємо кількість елементів для аналізу
        const elementsToCheck = textElements.slice(0, 20);
        
        const readabilityStats = this.gatherElementStats(elementsToCheck, (element) => {
            return this.checkTextReadability(element);
        });

        return this.calculateSuccessRate(readabilityStats.passed, readabilityStats.total);
    }

    /**
     * Отримання текстових елементів
     */
    getTextElements() {
        const selectors = ['p', 'div', 'span', 'li', 'td', 'th'];
        const elements = [];
        
        selectors.forEach(selector => {
            const found = document.querySelectorAll(selector);
            elements.push(...Array.from(found));
        });

        return elements.filter(el => 
            this.helpers.isElementVisible(el) && 
            this.getElementText(el).length > 20 // Тільки елементи з достатнім текстом
        );
    }

    /**
     * Перевірка читабельності тексту
     */
    checkTextReadability(element) {
        const text = this.getElementText(element);
        const styles = this.getComputedStyles(element);
        
        // Перевірка розміру шрифту
        const fontSize = this.helpers.getFontSizeInPixels(element);
        if (fontSize < 12) {
            return this.createCheckResult(false, `Шрифт занадто малий: ${fontSize}px`, 'medium', { fontSize });
        }

        // Перевірка довжини рядка
        const lineLength = this.estimateLineLength(element, text);
        if (lineLength > 80) {
            return this.createCheckResult(false, `Рядок занадто довгий: ~${lineLength} символів`, 'low', { lineLength });
        }

        // Перевірка міжрядкового інтервалу
        const lineHeight = parseFloat(styles.lineHeight);
        if (lineHeight < 1.2) {
            return this.createCheckResult(false, `Малий міжрядковий інтервал: ${lineHeight}`, 'low', { lineHeight });
        }

        return this.createCheckResult(true, 'Текст читабельний', 'info', {
            fontSize,
            lineLength,
            lineHeight
        });
    }

    /**
     * Оцінка довжини рядка
     */
    estimateLineLength(element, text) {
        try {
            const rect = element.getBoundingClientRect();
            const styles = this.getComputedStyles(element);
            const fontSize = this.helpers.getFontSizeInPixels(element);
            
            // Приблизна оцінка символів на рядок
            const avgCharWidth = fontSize * 0.6; // Приблизна ширина символа
            const availableWidth = rect.width - 
                parseFloat(styles.paddingLeft) - 
                parseFloat(styles.paddingRight);
            
            return Math.floor(availableWidth / avgCharWidth);
        } catch (error) {
            return 50; // За замовчуванням
        }
    }

    /**
     * Детальний аналіз для UI
     */
    async getDetailedAnalysis(pageData) {
        return {
            errorSupport: await this.analyzeErrorSupport(pageData),
            headings: await this.analyzeHeadings(pageData),
            links: await this.analyzeLinks(pageData),
            readability: await this.analyzeReadability(pageData)
        };
    }

    async analyzeErrorSupport(pageData) {
        const forms = pageData.forms || [];
        const results = {
            total: forms.length,
            withSupport: 0,
            problematic: []
        };

        for (const form of forms) {
            const quality = this.analyzeFormErrorSupportQuality(form, pageData.html_content);
            if (quality >= 0.5) {
                results.withSupport++;
            } else {
                results.problematic.push({
                    selector: this.helpers.generateSelector(form),
                    quality: quality,
                    message: `Низька якість підтримки помилок: ${(quality * 100).toFixed(1)}%`
                });
            }
        }

        return results;
    }

    async analyzeHeadings(pageData) {
        const headings = pageData.headings || this.getHeadings();
        const results = {
            total: headings.length,
            proper: 0,
            problematic: []
        };

        headings.forEach(heading => {
            const check = this.checkHeadingStructure(heading, headings);
            if (check.passed) {
                results.proper++;
            } else {
                results.problematic.push({
                    selector: this.helpers.generateSelector(heading),
                    message: check.message,
                    severity: check.severity
                });
            }
        });

        return results;
    }

    async analyzeLinks(pageData) {
        const links = pageData.links || this.getLinks();
        const results = {
            total: links.length,
            clear: 0,
            problematic: []
        };

        links.forEach(link => {
            const check = this.checkLinkPurpose(link);
            if (check.passed) {
                results.clear++;
            } else {
                results.problematic.push({
                    selector: this.helpers.generateSelector(link),
                    message: check.message,
                    severity: check.severity
                });
            }
        });

        return results;
    }

    async analyzeReadability(pageData) {
        const textElements = this.getTextElements().slice(0, 10);
        const results = {
            total: textElements.length,
            readable: 0,
            problematic: []
        };

        textElements.forEach(element => {
            const check = this.checkTextReadability(element);
            if (check.passed) {
                results.readable++;
            } else {
                results.problematic.push({
                    selector: this.helpers.generateSelector(element),
                    message: check.message,
                    severity: check.severity
                });
            }
        });

        return results;
    }
}

// Експортуємо для використання
window.UnderstandabilityMetrics = UnderstandabilityMetrics;