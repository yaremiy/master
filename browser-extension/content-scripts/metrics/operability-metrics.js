/**
 * Operability Metrics - Метрики керованості
 * Портовано з Python коду з повним збереженням логіки
 */

class OperabilityMetrics extends BaseMetrics {
    constructor() {
        super();
        this.metricName = 'operability';
        this.focusTestResults = [];
    }

    /**
     * Розрахунок загальної метрики керованості
     */
    async calculateMetric(pageData) {
        this.helpers.log('⚡ Розрахунок метрики керованості...');

        const metrics = {
            keyboardNavigation: await this.calculateKeyboardNavigation(pageData),
            focusManagement: await this.calculateFocusManagement(pageData),
            interactiveElements: await this.calculateInteractiveElements(pageData),
            timingAndMotion: await this.calculateTimingAndMotion(pageData)
        };

        // Вагові коефіцієнти для підметрик
        const weights = {
            keyboardNavigation: 0.4,   // 40% - найважливіше
            focusManagement: 0.3,      // 30% - дуже важливо
            interactiveElements: 0.2,  // 20% - доступні імена та ролі
            timingAndMotion: 0.1       // 10% - додаткові перевірки
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

        this.logResult('Operability', finalScore,
            `Keyboard: ${(metrics.keyboardNavigation * 100).toFixed(1)}%, ` +
            `Focus: ${(metrics.focusManagement * 100).toFixed(1)}%, ` +
            `Interactive: ${(metrics.interactiveElements * 100).toFixed(1)}%`
        );

        return finalScore;
    }

    /**
     * Розрахунок клавіатурної навігації
     */
    async calculateKeyboardNavigation(pageData) {
        const interactiveElements = this.getInteractiveElements();
        
        if (interactiveElements.length === 0) {
            return 1.0; // Немає інтерактивних елементів = немає проблем
        }

        // Тестуємо клавіатурну доступність
        const keyboardStats = this.gatherElementStats(interactiveElements, (element) => {
            return this.checkKeyboardAccessibility(element);
        });

        return this.calculateSuccessRate(keyboardStats.passed, keyboardStats.total);
    }

    /**
     * Отримання всіх інтерактивних елементів
     */
    getInteractiveElements() {
        const selectors = [
            'a[href]',
            'button',
            'input:not([type="hidden"])',
            'select',
            'textarea',
            '[tabindex]:not([tabindex="-1"])',
            '[onclick]',
            '[role="button"]',
            '[role="link"]',
            '[role="menuitem"]',
            '[role="tab"]',
            '[role="option"]'
        ];

        const elements = [];
        selectors.forEach(selector => {
            const found = document.querySelectorAll(selector);
            elements.push(...Array.from(found));
        });

        // Фільтруємо видимі та унікальні елементи
        const uniqueElements = [...new Set(elements)];
        return uniqueElements.filter(el => this.helpers.isElementVisible(el));
    }

    /**
     * Перевірка клавіатурної доступності елемента
     */
    checkKeyboardAccessibility(element) {
        const tagName = element.tagName.toLowerCase();
        const type = element.type;
        const tabindex = element.getAttribute('tabindex');
        const role = element.getAttribute('role');

        // Природно фокусовані елементи
        const naturallyFocusable = [
            'a', 'button', 'input', 'select', 'textarea', 'details', 'summary'
        ];

        // Перевірка чи елемент може отримати фокус
        if (naturallyFocusable.includes(tagName)) {
            // Перевірка чи елемент не відключений
            if (element.disabled) {
                return this.createCheckResult(false, 'Елемент відключений', 'low');
            }

            // Перевірка чи не заборонений tabindex
            if (tabindex === '-1') {
                return this.createCheckResult(false, 'Елемент виключений з табуляції (tabindex="-1")', 'medium');
            }

            return this.createCheckResult(true, 'Природно фокусований елемент', 'info');
        }

        // Елементи з ролями
        const interactiveRoles = [
            'button', 'link', 'menuitem', 'tab', 'option', 'checkbox', 'radio'
        ];

        if (role && interactiveRoles.includes(role)) {
            // Має бути фокусованим
            if (tabindex === null || tabindex === undefined) {
                return this.createCheckResult(false, `Елемент з роллю "${role}" без tabindex`, 'high');
            }

            if (tabindex === '-1') {
                return this.createCheckResult(false, `Елемент з роллю "${role}" виключений з табуляції`, 'medium');
            }

            return this.createCheckResult(true, `Елемент з роллю "${role}" доступний з клавіатури`, 'info');
        }

        // Елементи з onclick без клавіатурної підтримки
        if (element.onclick || element.getAttribute('onclick')) {
            if (!tabindex || tabindex === '-1') {
                return this.createCheckResult(false, 'Клікабельний елемент без клавіатурної підтримки', 'high');
            }

            // Перевірка обробників клавіатури
            const hasKeyboardHandlers = this.checkKeyboardEventHandlers(element);
            if (!hasKeyboardHandlers) {
                return this.createCheckResult(false, 'Клікабельний елемент без обробників клавіатури', 'medium');
            }

            return this.createCheckResult(true, 'Клікабельний елемент з клавіатурною підтримкою', 'info');
        }

        return this.createCheckResult(true, 'Елемент перевірено', 'info');
    }

    /**
     * Перевірка обробників клавіатурних подій
     */
    checkKeyboardEventHandlers(element) {
        // Перевірка JavaScript обробників
        return !!(element.onkeydown || 
                 element.onkeyup || 
                 element.onkeypress ||
                 element.getAttribute('onkeydown') ||
                 element.getAttribute('onkeyup') ||
                 element.getAttribute('onkeypress'));
    }

    /**
     * Розрахунок управління фокусом
     */
    async calculateFocusManagement(pageData) {
        const focusableElements = this.getFocusableElements();
        
        if (focusableElements.length === 0) {
            return 1.0;
        }

        // Тестуємо управління фокусом
        const focusStats = this.gatherElementStats(focusableElements, (element) => {
            return this.checkFocusManagement(element);
        });

        // Додаткові перевірки фокусу
        const additionalChecks = await this.performFocusTests();
        
        // Комбінуємо результати
        const baseScore = this.calculateSuccessRate(focusStats.passed, focusStats.total);
        const additionalScore = additionalChecks.score;
        
        return (baseScore * 0.7) + (additionalScore * 0.3);
    }

    /**
     * Отримання фокусованих елементів
     */
    getFocusableElements() {
        const focusableSelectors = [
            'a[href]',
            'button:not([disabled])',
            'input:not([disabled]):not([type="hidden"])',
            'select:not([disabled])',
            'textarea:not([disabled])',
            '[tabindex]:not([tabindex="-1"])',
            'details',
            'summary'
        ];

        const elements = [];
        focusableSelectors.forEach(selector => {
            const found = document.querySelectorAll(selector);
            elements.push(...Array.from(found));
        });

        return [...new Set(elements)].filter(el => this.helpers.isElementVisible(el));
    }

    /**
     * Перевірка управління фокусом для елемента
     */
    checkFocusManagement(element) {
        const tagName = element.tagName.toLowerCase();
        const tabindex = element.getAttribute('tabindex');

        // Перевірка видимості фокусу
        const focusVisible = this.checkFocusVisibility(element);
        if (!focusVisible.visible) {
            return this.createCheckResult(false, 'Фокус не видимий', 'medium', focusVisible);
        }

        // Перевірка логічного порядку табуляції
        const tabOrder = this.checkTabOrder(element);
        if (!tabOrder.logical) {
            return this.createCheckResult(false, 'Нелогічний порядок табуляції', 'medium', tabOrder);
        }

        // Перевірка доступного імені
        const accessibleName = this.helpers.getAccessibleName(element);
        if (!accessibleName) {
            return this.createCheckResult(false, 'Відсутнє доступне ім\'я', 'high');
        }

        return this.createCheckResult(true, 'Управління фокусом правильне', 'info', {
            accessibleName,
            tabindex,
            focusVisible: focusVisible.visible
        });
    }

    /**
     * Перевірка видимості фокусу
     */
    checkFocusVisibility(element) {
        try {
            // Симулюємо фокус
            const originalFocus = document.activeElement;
            element.focus();
            
            const styles = this.getComputedStyles(element);
            const pseudoStyles = this.getFocusStyles(element);
            
            // Відновлюємо фокус
            if (originalFocus && originalFocus.focus) {
                originalFocus.focus();
            }

            // Перевірка чи є видимі стилі фокусу
            const hasOutline = styles.outline !== 'none' && styles.outline !== '0px';
            const hasBoxShadow = styles.boxShadow !== 'none';
            const hasBorder = this.checkBorderChange(element);
            const hasBackground = this.checkBackgroundChange(element);

            const visible = hasOutline || hasBoxShadow || hasBorder || hasBackground;

            return {
                visible,
                details: {
                    outline: hasOutline,
                    boxShadow: hasBoxShadow,
                    border: hasBorder,
                    background: hasBackground
                }
            };

        } catch (error) {
            return { visible: true, error: error.message };
        }
    }

    /**
     * Отримання стилів фокусу (спрощена версія)
     */
    getFocusStyles(element) {
        // В браузері складно отримати :focus стилі без фактичного фокусу
        // Тому робимо спрощену перевірку
        return this.getComputedStyles(element);
    }

    /**
     * Перевірка зміни рамки при фокусі
     */
    checkBorderChange(element) {
        // Спрощена перевірка - шукаємо CSS класи або стилі
        const className = element.className;
        return className.includes('focus') || className.includes('active');
    }

    /**
     * Перевірка зміни фону при фокусі
     */
    checkBackgroundChange(element) {
        // Спрощена перевірка
        const styles = this.getComputedStyles(element);
        return styles.backgroundColor !== 'rgba(0, 0, 0, 0)' && styles.backgroundColor !== 'transparent';
    }

    /**
     * Перевірка логічного порядку табуляції
     */
    checkTabOrder(element) {
        const tabindex = element.getAttribute('tabindex');
        
        // Позитивні tabindex можуть порушувати логічний порядок
        if (tabindex && parseInt(tabindex) > 0) {
            return {
                logical: false,
                issue: 'Позитивний tabindex може порушувати природний порядок',
                tabindex: parseInt(tabindex)
            };
        }

        return { logical: true, tabindex: tabindex || 0 };
    }

    /**
     * Виконання додаткових тестів фокусу
     */
    async performFocusTests() {
        const tests = {
            skipLinks: this.checkSkipLinks(),
            focusTrap: this.checkFocusTrap(),
            modalFocus: this.checkModalFocus()
        };

        let passedTests = 0;
        let totalTests = 0;

        Object.values(tests).forEach(test => {
            if (test.applicable) {
                totalTests++;
                if (test.passed) passedTests++;
            }
        });

        return {
            score: totalTests > 0 ? passedTests / totalTests : 1.0,
            details: tests
        };
    }

    /**
     * Перевірка skip links
     */
    checkSkipLinks() {
        const skipLinks = document.querySelectorAll('a[href^="#"], a[href*="skip"], a[href*="main"]');
        const visibleSkipLinks = Array.from(skipLinks).filter(link => {
            const text = link.textContent.toLowerCase();
            return text.includes('skip') || text.includes('main') || text.includes('content');
        });

        return {
            applicable: true,
            passed: visibleSkipLinks.length > 0,
            count: visibleSkipLinks.length,
            message: visibleSkipLinks.length > 0 ? 
                `Знайдено ${visibleSkipLinks.length} skip links` : 
                'Skip links не знайдено'
        };
    }

    /**
     * Перевірка focus trap в модальних вікнах
     */
    checkFocusTrap() {
        const modals = document.querySelectorAll('[role="dialog"], .modal, .popup');
        
        if (modals.length === 0) {
            return { applicable: false, passed: true, message: 'Модальні вікна не знайдено' };
        }

        // Спрощена перевірка - шукаємо видимі модалі
        const visibleModals = Array.from(modals).filter(modal => this.helpers.isElementVisible(modal));
        
        if (visibleModals.length === 0) {
            return { applicable: false, passed: true, message: 'Видимі модалі не знайдено' };
        }

        // Перевіряємо чи є фокусовані елементи в модалі
        const modalWithFocus = visibleModals.some(modal => {
            const focusableInModal = modal.querySelectorAll(
                'a[href], button, input, select, textarea, [tabindex]:not([tabindex="-1"])'
            );
            return focusableInModal.length > 0;
        });

        return {
            applicable: true,
            passed: modalWithFocus,
            count: visibleModals.length,
            message: modalWithFocus ? 
                'Модальні вікна мають фокусовані елементи' : 
                'Модальні вікна без фокусованих елементів'
        };
    }

    /**
     * Перевірка фокусу в модальних вікнах
     */
    checkModalFocus() {
        // Перевіряємо чи активний елемент знаходиться в модальному вікні
        const activeElement = document.activeElement;
        const modals = document.querySelectorAll('[role="dialog"], .modal, .popup');
        
        if (modals.length === 0) {
            return { applicable: false, passed: true, message: 'Модальні вікна не знайдено' };
        }

        const visibleModals = Array.from(modals).filter(modal => this.helpers.isElementVisible(modal));
        
        if (visibleModals.length === 0) {
            return { applicable: false, passed: true, message: 'Видимі модалі не знайдено' };
        }

        // Якщо є видимий модаль, фокус має бути в ньому
        const focusInModal = visibleModals.some(modal => modal.contains(activeElement));

        return {
            applicable: true,
            passed: focusInModal || activeElement === document.body,
            message: focusInModal ? 
                'Фокус правильно управляється в модалі' : 
                'Фокус може бути поза модальним вікном'
        };
    }

    /**
     * Розрахунок інтерактивних елементів
     */
    async calculateInteractiveElements(pageData) {
        const interactiveElements = this.getInteractiveElements();
        
        if (interactiveElements.length === 0) {
            return 1.0;
        }

        const elementStats = this.gatherElementStats(interactiveElements, (element) => {
            return this.checkInteractiveElement(element);
        });

        return this.calculateSuccessRate(elementStats.passed, elementStats.total);
    }

    /**
     * Перевірка інтерактивного елемента
     */
    checkInteractiveElement(element) {
        const issues = [];

        // Перевірка доступного імені
        const accessibleName = this.helpers.getAccessibleName(element);
        if (!accessibleName) {
            issues.push('відсутнє доступне ім\'я');
        }

        // Перевірка ролі
        const role = this.checkElementRole(element);
        if (!role.appropriate) {
            issues.push(role.issue);
        }

        // Перевірка розміру цілі (мінімум 44x44px)
        const targetSize = this.checkTargetSize(element);
        if (!targetSize.adequate) {
            issues.push(`розмір цілі ${targetSize.width}x${targetSize.height}px (мінімум 44x44px)`);
        }

        if (issues.length === 0) {
            return this.createCheckResult(true, 'Інтерактивний елемент правильно налаштований', 'info', {
                accessibleName,
                role: role.role,
                size: `${targetSize.width}x${targetSize.height}px`
            });
        }

        const severity = issues.length > 2 ? 'high' : issues.length > 1 ? 'medium' : 'low';
        return this.createCheckResult(false, `Проблеми: ${issues.join(', ')}`, severity, { issues });
    }

    /**
     * Перевірка ролі елемента
     */
    checkElementRole(element) {
        const tagName = element.tagName.toLowerCase();
        const role = element.getAttribute('role');
        const type = element.type;

        // Природні ролі
        const naturalRoles = {
            'a': 'link',
            'button': 'button',
            'input': type === 'button' || type === 'submit' ? 'button' : 'textbox',
            'select': 'combobox',
            'textarea': 'textbox'
        };

        const expectedRole = naturalRoles[tagName];
        
        if (expectedRole && role && role !== expectedRole) {
            return {
                appropriate: false,
                issue: `неочікувана роль "${role}" для елемента ${tagName}`,
                role: role,
                expected: expectedRole
            };
        }

        return {
            appropriate: true,
            role: role || expectedRole || 'generic'
        };
    }

    /**
     * Перевірка розміру цілі
     */
    checkTargetSize(element) {
        try {
            const rect = element.getBoundingClientRect();
            const width = Math.round(rect.width);
            const height = Math.round(rect.height);

            // WCAG рекомендує мінімум 44x44px
            const minSize = 44;
            const adequate = width >= minSize && height >= minSize;

            return {
                adequate,
                width,
                height,
                area: width * height
            };

        } catch (error) {
            return {
                adequate: true, // Припускаємо що все ОК якщо не можемо виміряти
                width: 0,
                height: 0,
                error: error.message
            };
        }
    }

    /**
     * Розрахунок часових обмежень та руху
     */
    async calculateTimingAndMotion(pageData) {
        const checks = {
            autoplay: this.checkAutoplayMedia(),
            animations: this.checkAnimations(),
            timeouts: this.checkTimeouts()
        };

        let passedChecks = 0;
        let totalChecks = 0;

        Object.values(checks).forEach(check => {
            if (check.applicable) {
                totalChecks++;
                if (check.passed) passedChecks++;
            }
        });

        return totalChecks > 0 ? passedChecks / totalChecks : 1.0;
    }

    /**
     * Перевірка автовідтворення медіа
     */
    checkAutoplayMedia() {
        const autoplayElements = document.querySelectorAll('video[autoplay], audio[autoplay]');
        
        if (autoplayElements.length === 0) {
            return { applicable: false, passed: true, message: 'Автовідтворення не знайдено' };
        }

        // Перевіряємо чи є елементи управління або можливість зупинки
        const problematicElements = Array.from(autoplayElements).filter(element => {
            return !element.hasAttribute('controls') && !element.hasAttribute('muted');
        });

        return {
            applicable: true,
            passed: problematicElements.length === 0,
            total: autoplayElements.length,
            problematic: problematicElements.length,
            message: problematicElements.length === 0 ? 
                'Автовідтворення правильно налаштоване' : 
                `${problematicElements.length} елементів з проблемним автовідтворенням`
        };
    }

    /**
     * Перевірка анімацій
     */
    checkAnimations() {
        // Спрощена перевірка - шукаємо CSS анімації
        const animatedElements = document.querySelectorAll('[style*="animation"], .animate, .animated');
        
        if (animatedElements.length === 0) {
            return { applicable: false, passed: true, message: 'Анімації не знайдено' };
        }

        // Перевіряємо чи є можливість вимкнути анімації
        const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        
        return {
            applicable: true,
            passed: prefersReducedMotion || animatedElements.length < 5, // Спрощена логіка
            count: animatedElements.length,
            prefersReducedMotion,
            message: prefersReducedMotion ? 
                'Користувач вимкнув анімації' : 
                `Знайдено ${animatedElements.length} анімованих елементів`
        };
    }

    /**
     * Перевірка часових обмежень
     */
    checkTimeouts() {
        // Спрощена перевірка - шукаємо елементи з таймерами
        const timerElements = document.querySelectorAll('[data-timeout], .timer, .countdown');
        
        if (timerElements.length === 0) {
            return { applicable: false, passed: true, message: 'Таймери не знайдено' };
        }

        // Перевіряємо чи є можливість продовжити час
        const extendableTimers = Array.from(timerElements).filter(element => {
            return element.querySelector('button, .extend, .continue') !== null;
        });

        return {
            applicable: true,
            passed: extendableTimers.length === timerElements.length,
            total: timerElements.length,
            extendable: extendableTimers.length,
            message: extendableTimers.length === timerElements.length ? 
                'Всі таймери мають можливість продовження' : 
                `${timerElements.length - extendableTimers.length} таймерів без можливості продовження`
        };
    }

    /**
     * Детальний аналіз для UI
     */
    async getDetailedAnalysis(pageData) {
        return {
            keyboard: await this.analyzeKeyboardNavigation(pageData),
            focus: await this.analyzeFocusManagement(pageData),
            interactive: await this.analyzeInteractiveElements(pageData),
            timing: await this.analyzeTimingAndMotion(pageData)
        };
    }

    async analyzeKeyboardNavigation(pageData) {
        const interactiveElements = this.getInteractiveElements();
        const results = {
            total: interactiveElements.length,
            accessible: 0,
            problematic: []
        };

        interactiveElements.forEach(element => {
            const check = this.checkKeyboardAccessibility(element);
            const selector = this.helpers.generateSelector(element);
            
            if (check.passed) {
                results.accessible++;
            } else {
                results.problematic.push({
                    selector,
                    message: check.message,
                    severity: check.severity
                });
            }
        });

        return results;
    }

    async analyzeFocusManagement(pageData) {
        const focusableElements = this.getFocusableElements();
        const additionalTests = await this.performFocusTests();
        
        return {
            focusableElements: focusableElements.length,
            additionalTests: additionalTests.details,
            score: additionalTests.score
        };
    }

    async analyzeInteractiveElements(pageData) {
        const interactiveElements = this.getInteractiveElements();
        const results = {
            total: interactiveElements.length,
            withNames: 0,
            adequateSize: 0,
            problematic: []
        };

        interactiveElements.forEach(element => {
            const check = this.checkInteractiveElement(element);
            const selector = this.helpers.generateSelector(element);
            
            if (check.passed) {
                results.withNames++;
                const targetSize = this.checkTargetSize(element);
                if (targetSize.adequate) results.adequateSize++;
            } else {
                results.problematic.push({
                    selector,
                    message: check.message,
                    severity: check.severity
                });
            }
        });

        return results;
    }

    async analyzeTimingAndMotion(pageData) {
        return {
            autoplay: this.checkAutoplayMedia(),
            animations: this.checkAnimations(),
            timeouts: this.checkTimeouts()
        };
    }
}

// Експортуємо для використання
window.OperabilityMetrics = OperabilityMetrics;