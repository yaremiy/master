/**
 * Базовий клас для всіх метрик доступності
 * Портований з Python коду
 */

class BaseMetrics {
    constructor() {
        this.helpers = window.AccessibilityHelpers;
    }

    /**
     * Базовий метод розрахунку метрики
     */
    calculateMetric(pageData) {
        throw new Error('Method calculateMetric must be implemented by subclass');
    }

    /**
     * Отримання всіх елементів певного типу
     */
    getElementsByType(types) {
        const elements = [];
        types.forEach(type => {
            const found = document.querySelectorAll(type);
            elements.push(...Array.from(found));
        });
        return elements;
    }

    /**
     * Фільтрація видимих елементів
     */
    filterVisibleElements(elements) {
        return elements.filter(element => this.helpers.isElementVisible(element));
    }

    /**
     * Розрахунок відсотка успішних елементів
     */
    calculateSuccessRate(successfulElements, totalElements) {
        if (totalElements === 0) return 1.0; // Якщо немає елементів, вважаємо 100%
        return successfulElements / totalElements;
    }

    /**
     * Перевірка наявності атрибута
     */
    hasAttribute(element, attribute) {
        return element.hasAttribute(attribute) && element.getAttribute(attribute).trim() !== '';
    }

    /**
     * Отримання тексту елемента
     */
    getElementText(element) {
        return element.textContent ? element.textContent.trim() : '';
    }

    /**
     * Перевірка чи елемент має доступне ім'я
     */
    hasAccessibleName(element) {
        const name = this.helpers.getAccessibleName(element);
        return name && name.length > 0;
    }

    /**
     * Створення детального звіту
     */
    createDetailedReport(metric, score, details) {
        return {
            metric: metric,
            score: score,
            details: details,
            timestamp: Date.now()
        };
    }

    /**
     * Логування результатів
     */
    logResult(metric, score, details = '') {
        this.helpers.log(`${metric}: ${(score * 100).toFixed(1)}% ${details}`, 'info');
    }

    /**
     * Перевірка чи елемент є формою
     */
    isFormElement(element) {
        const formTags = ['input', 'textarea', 'select', 'button'];
        return formTags.includes(element.tagName.toLowerCase());
    }

    /**
     * Перевірка чи елемент є медіа
     */
    isMediaElement(element) {
        const mediaTags = ['img', 'video', 'audio', 'canvas', 'svg'];
        return mediaTags.includes(element.tagName.toLowerCase());
    }

    /**
     * Отримання стилів елемента
     */
    getComputedStyles(element) {
        return window.getComputedStyle(element);
    }

    /**
     * Перевірка контрастності
     */
    checkContrast(element) {
        const styles = this.getComputedStyles(element);
        const color = styles.color;
        const backgroundColor = styles.backgroundColor;
        
        if (!color || !backgroundColor) return null;
        
        return this.helpers.calculateContrast(color, backgroundColor);
    }

    /**
     * Збір статистики по елементах
     */
    gatherElementStats(elements, checkFunction) {
        const stats = {
            total: elements.length,
            passed: 0,
            failed: 0,
            details: []
        };

        elements.forEach(element => {
            const result = checkFunction(element);
            if (result.passed) {
                stats.passed++;
            } else {
                stats.failed++;
            }
            stats.details.push({
                element: this.helpers.generateSelector(element),
                passed: result.passed,
                message: result.message,
                severity: result.severity || 'medium'
            });
        });

        return stats;
    }

    /**
     * Створення результату перевірки
     */
    createCheckResult(passed, message, severity = 'medium', data = {}) {
        return {
            passed: passed,
            message: message,
            severity: severity,
            data: data
        };
    }

    /**
     * Перевірка мови документа
     */
    getDocumentLanguage() {
        return document.documentElement.lang || 
               document.querySelector('html').getAttribute('lang') || 
               'unknown';
    }

    /**
     * Перевірка напрямку тексту
     */
    getTextDirection() {
        const dir = document.documentElement.dir || 
                   document.querySelector('html').getAttribute('dir') ||
                   this.getComputedStyles(document.documentElement).direction;
        return dir || 'ltr';
    }

    /**
     * Отримання всіх заголовків
     */
    getHeadings() {
        return this.getElementsByType(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']);
    }

    /**
     * Отримання всіх посилань
     */
    getLinks() {
        return this.getElementsByType(['a[href]']);
    }

    /**
     * Отримання всіх зображень
     */
    getImages() {
        return this.getElementsByType(['img']);
    }

    /**
     * Отримання всіх форм
     */
    getForms() {
        return this.getElementsByType(['form']);
    }

    /**
     * Отримання всіх полів форм
     */
    getFormFields() {
        return this.getElementsByType(['input', 'textarea', 'select']);
    }

    /**
     * Отримання всіх кнопок
     */
    getButtons() {
        return this.getElementsByType(['button', 'input[type="button"]', 'input[type="submit"]', 'input[type="reset"]']);
    }

    /**
     * Перевірка чи елемент має правильну роль
     */
    hasValidRole(element, expectedRoles = []) {
        const role = element.getAttribute('role');
        if (!role && expectedRoles.length === 0) return true;
        return expectedRoles.includes(role);
    }

    /**
     * Перевірка ARIA атрибутів
     */
    checkAriaAttributes(element, requiredAttributes = []) {
        const results = [];
        
        requiredAttributes.forEach(attr => {
            const hasAttr = this.hasAttribute(element, attr);
            results.push({
                attribute: attr,
                present: hasAttr,
                value: hasAttr ? element.getAttribute(attr) : null
            });
        });
        
        return results;
    }

    /**
     * Валідація ARIA значень
     */
    validateAriaValue(element, attribute, validValues = []) {
        const value = element.getAttribute(attribute);
        if (!value) return false;
        
        if (validValues.length === 0) return true;
        return validValues.includes(value);
    }

    /**
     * Перевірка семантичної структури
     */
    checkSemanticStructure() {
        const structure = {
            hasMain: document.querySelector('main, [role="main"]') !== null,
            hasNav: document.querySelector('nav, [role="navigation"]') !== null,
            hasHeader: document.querySelector('header, [role="banner"]') !== null,
            hasFooter: document.querySelector('footer, [role="contentinfo"]') !== null,
            headingStructure: this.analyzeHeadingStructure()
        };
        
        return structure;
    }

    /**
     * Аналіз структури заголовків
     */
    analyzeHeadingStructure() {
        const headings = this.getHeadings();
        const structure = [];
        
        headings.forEach(heading => {
            const level = parseInt(heading.tagName.charAt(1));
            const text = this.getElementText(heading);
            
            structure.push({
                level: level,
                text: text,
                element: this.helpers.generateSelector(heading)
            });
        });
        
        return structure;
    }
}

// Експортуємо для використання
window.BaseMetrics = BaseMetrics;