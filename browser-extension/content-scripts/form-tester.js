/**
 * FormTester - систематичне тестування форм на підтримку помилок
 * Портований з Python коду з повним збереженням логіки
 */

class FormTester {
    constructor() {
        this.helpers = window.AccessibilityHelpers;
        
        // Систематична бібліотека тестових сценаріїв
        this.invalidTestScenarios = {
            'email': [
                { value: '', type: 'empty', description: 'Порожнє поле' },
                { value: 'abc', type: 'invalid_format', description: 'Невірний формат' },
                { value: 'test@', type: 'incomplete', description: 'Неповний email' },
                { value: '@domain.com', type: 'missing_local', description: 'Відсутня локальна частина' },
                { value: 'a'.repeat(255) + '@test.com', type: 'too_long', description: 'Занадто довгий' }
            ],
            'number': [
                { value: '', type: 'empty', description: 'Порожнє поле' },
                { value: 'abc', type: 'non_numeric', description: 'Не число' },
                { value: '12.34.56', type: 'invalid_format', description: 'Невірний формат' },
                { value: '999999999999999999999', type: 'too_large', description: 'Занадто велике число' }
            ],
            'tel': [
                { value: '', type: 'empty', description: 'Порожнє поле' },
                { value: '123', type: 'too_short', description: 'Занадто короткий' },
                { value: 'abc-def-ghij', type: 'invalid_chars', description: 'Невірні символи' },
                { value: '1'.repeat(50), type: 'too_long', description: 'Занадто довгий' }
            ],
            'url': [
                { value: '', type: 'empty', description: 'Порожнє поле' },
                { value: 'not-url', type: 'invalid_format', description: 'Невірний формат' },
                { value: 'http://', type: 'incomplete', description: 'Неповний URL' },
                { value: 'ftp://invalid', type: 'unsupported_protocol', description: 'Непідтримуваний протокол' }
            ],
            'date': [
                { value: '', type: 'empty', description: 'Порожнє поле' },
                { value: '32/13/2023', type: 'invalid_date', description: 'Неіснуюча дата' },
                { value: 'not-date', type: 'invalid_format', description: 'Невірний формат' },
                { value: '2023-13-45', type: 'invalid_values', description: 'Невірні значення' }
            ],
            'time': [
                { value: '', type: 'empty', description: 'Порожнє поле' },
                { value: '25:99', type: 'invalid_time', description: 'Неіснуючий час' },
                { value: 'not-time', type: 'invalid_format', description: 'Невірний формат' }
            ],
            'password': [
                { value: '', type: 'empty', description: 'Порожній пароль' },
                { value: '123', type: 'too_short', description: 'Занадто короткий' },
                { value: '   ', type: 'whitespace_only', description: 'Тільки пробіли' }
            ],
            'text': [
                { value: '', type: 'empty', description: 'Порожнє поле' },
                { value: '   ', type: 'whitespace_only', description: 'Тільки пробіли' }
            ],
            'textarea': [
                { value: '', type: 'empty', description: 'Порожнє поле' },
                { value: '   ', type: 'whitespace_only', description: 'Тільки пробіли' }
            ]
        };
    }

    /**
     * Систематичне тестування форми за новим алгоритмом:
     * 1. Ініціалізація аналізу
     * 2. Створення сценаріїв введення  
     * 3. Запуск перевірки
     * 4. Збір сигналів про помилку (HTML5 API, ARIA, DOM, CSS)
     * 5. Крос-перевірка
     * 6. Формування результату
     */
    async testFormErrorBehaviorSystematic(formSelector = 'form') {
        this.helpers.log(`🔬 Систематичне тестування форми: ${formSelector}`);
        
        try {
            // 1. Ініціалізація аналізу
            const form = document.querySelector(formSelector);
            if (!form) {
                return this.createSystematicResult("Форма не знайдена", formSelector);
            }
            
            // Визначити всі поля форми
            const fieldsData = this.discoverFormFields(form);
            if (!fieldsData || fieldsData.length === 0) {
                return this.createSystematicResult("Поля не знайдено", formSelector);
            }
            
            this.helpers.log(`📋 Знайдено ${fieldsData.length} полів для тестування`);
            
            // Результати тестування для кожного поля
            const fieldTestResults = [];
            
            for (const fieldData of fieldsData) {
                this.helpers.log(`🧪 Тестування поля: ${fieldData.selector}`);
                
                // 2-6. Тестування поля за алгоритмом
                const fieldResult = await this.testFieldSystematic(fieldData);
                fieldTestResults.push(fieldResult);
            }
            
            // Формування загального результату
            return this.compileSystematicResults(formSelector, fieldTestResults);
            
        } catch (error) {
            this.helpers.log(`❌ Помилка систематичного тестування: ${error.message}`, 'error');
            return this.createSystematicResult(`Помилка: ${error.message}`, formSelector);
        }
    }

    /**
     * 1. Ініціалізація аналізу - визначення всіх полів форми
     */
    discoverFormFields(form) {
        const fields = form.querySelectorAll('input, textarea, select');
        const fieldsData = [];
        
        fields.forEach((field, index) => {
            const fieldType = field.type || field.tagName.toLowerCase();
            const isTestable = (
                field.required ||
                field.pattern ||
                field.minLength > 0 ||
                (field.maxLength > 0 && field.maxLength < 524288) ||
                field.min !== '' ||
                field.max !== '' ||
                ['email', 'number', 'tel', 'url', 'date', 'time', 'datetime-local', 'password'].includes(fieldType)
            );
            
            if (isTestable) {
                fieldsData.push({
                    selector: field.id ? `#${field.id}` : 
                             field.name ? `[name="${field.name}"]` :
                             `${field.tagName.toLowerCase()}:nth-child(${index + 1})`,
                    type: fieldType,
                    required: field.required || false,
                    pattern: field.pattern || null,
                    minLength: field.minLength || null,
                    maxLength: field.maxLength || null,
                    min: field.min || null,
                    max: field.max || null,
                    step: field.step || null,
                    id: field.id || null,
                    name: field.name || null,
                    placeholder: field.placeholder || '',
                    element: field
                });
            }
        });
        
        return fieldsData;
    }

    /**
     * 2-6. Систематичне тестування одного поля
     */
    async testFieldSystematic(fieldData) {
        const fieldSelector = fieldData.selector;
        const fieldType = fieldData.type;
        
        // 2. Створення сценаріїв введення
        const testScenarios = this.generateTestScenarios(fieldData);
        
        const fieldResult = {
            selector: fieldSelector,
            type: fieldType,
            field_data: fieldData,
            test_scenarios: [],
            error_detection_summary: {
                html5_api: false,
                aria_support: false,
                dom_changes: false,
                css_states: false
            },
            overall_support: false,
            quality_score: 0.0
        };
        
        // Тестуємо кожен сценарій
        for (const scenario of testScenarios) {
            this.helpers.log(`   📝 Сценарій: ${scenario.description} -> '${scenario.value}'`);
            
            const scenarioResult = await this.testScenario(fieldData.element, scenario);
            fieldResult.test_scenarios.push(scenarioResult);
            
            // Оновлюємо загальну інформацію про підтримку
            if (scenarioResult.error_detected) {
                fieldResult.error_detection_summary.html5_api |= scenarioResult.signals.html5_api.detected;
                fieldResult.error_detection_summary.aria_support |= scenarioResult.signals.aria_support.detected;
                fieldResult.error_detection_summary.dom_changes |= scenarioResult.signals.dom_changes.detected;
                fieldResult.error_detection_summary.css_states |= scenarioResult.signals.css_states.detected;
            }
        }
        
        // 5. Крос-перевірка
        fieldResult.overall_support = Object.values(fieldResult.error_detection_summary).some(Boolean);
        fieldResult.quality_score = this.calculateFieldQualityScore(fieldResult);
        
        return fieldResult;
    }

    /**
     * 2. Створення сценаріїв введення для поля
     */
    generateTestScenarios(fieldData) {
        const fieldType = fieldData.type;
        let scenarios = [];
        
        // Базові сценарії з бібліотеки
        if (this.invalidTestScenarios[fieldType]) {
            scenarios = [...this.invalidTestScenarios[fieldType]];
        } else {
            // Загальні сценарії для невідомих типів
            scenarios = [
                { value: '', type: 'empty', description: 'Порожнє поле' },
                { value: '   ', type: 'whitespace', description: 'Тільки пробіли' }
            ];
        }
        
        // Фільтруємо сценарії залежно від атрибутів поля
        scenarios = scenarios.filter(scenario => {
            // Порожнє поле тестуємо тільки для required
            if (scenario.type === 'empty' && !fieldData.required) {
                return false;
            }
            return true;
        });
        
        // Додаткові сценарії на основі атрибутів
        if (fieldData.maxLength && fieldData.maxLength > 0) {
            scenarios.push({
                value: 'a'.repeat(fieldData.maxLength + 10),
                type: 'exceeds_maxlength',
                description: `Перевищує maxLength (${fieldData.maxLength})`
            });
        }
        
        if (fieldData.min && fieldType === 'number') {
            try {
                const minVal = parseFloat(fieldData.min);
                scenarios.push({
                    value: String(minVal - 1),
                    type: 'below_min',
                    description: `Менше мінімуму (${fieldData.min})`
                });
            } catch (e) {
                // Ігноруємо помилки парсингу
            }
        }
        
        if (fieldData.max && fieldType === 'number') {
            try {
                const maxVal = parseFloat(fieldData.max);
                scenarios.push({
                    value: String(maxVal + 1),
                    type: 'above_max',
                    description: `Більше максимуму (${fieldData.max})`
                });
            } catch (e) {
                // Ігноруємо помилки парсингу
            }
        }
        
        return scenarios.slice(0, 3); // Обмежуємо кількість сценаріїв для швидкості
    }

    /**
     * 3-4. Запуск перевірки та збір сигналів про помилку
     */
    async testScenario(fieldElement, scenario) {
        try {
            // 3. Запуск перевірки
            // Зберігаємо початкове значення
            const originalValue = fieldElement.value;
            
            // Ввести некоректне значення
            fieldElement.value = scenario.value;
            
            // Викликати події для тригеру валідації
            fieldElement.dispatchEvent(new Event('input', { bubbles: true }));
            fieldElement.dispatchEvent(new Event('change', { bubbles: true }));
            fieldElement.dispatchEvent(new Event('blur', { bubbles: true }));
            
            // Дати час на реакцію
            await this.helpers.delay(100);
            
            // 4. Збір сигналів про помилку
            const signals = this.collectErrorSignals(fieldElement);
            
            // Відновлюємо початкове значення
            fieldElement.value = originalValue;
            
            // Визначити чи була виявлена помилка
            const errorDetected = [
                signals.html5_api.detected,
                signals.aria_support.detected,
                signals.dom_changes.detected,
                signals.css_states.detected
            ].some(Boolean);
            
            return {
                scenario: scenario,
                field_selector: this.helpers.generateSelector(fieldElement),
                error_detected: errorDetected,
                signals: signals,
                quality_score: this.calculateScenarioQuality(signals)
            };
            
        } catch (error) {
            this.helpers.log(`⚠️ Помилка тестування сценарію: ${error.message}`, 'warn');
            return {
                scenario: scenario,
                field_selector: this.helpers.generateSelector(fieldElement),
                error_detected: false,
                signals: this.emptySignals(),
                error: error.message,
                quality_score: 0.0
            };
        }
    }

    /**
     * 4. Збір сигналів про помилку (4 рівні)
     */
    collectErrorSignals(fieldElement) {
        const signals = {
            html5_api: {
                detected: false,
                valid: null,
                validation_message: '',
                details: {}
            },
            aria_support: {
                detected: false,
                aria_invalid: null,
                aria_describedby: null,
                describedby_content: '',
                role_alert_elements: []
            },
            dom_changes: {
                detected: false,
                nearby_error_elements: [],
                error_texts: []
            },
            css_states: {
                detected: false,
                invalid_pseudoclass: false,
                error_classes: []
            }
        };
        
        // 4.1. HTML5 Validity API
        try {
            if (fieldElement.validity) {
                signals.html5_api.valid = fieldElement.validity.valid;
                signals.html5_api.validation_message = fieldElement.validationMessage || '';
                signals.html5_api.detected = !fieldElement.validity.valid;
                signals.html5_api.details = {
                    valueMissing: fieldElement.validity.valueMissing,
                    typeMismatch: fieldElement.validity.typeMismatch,
                    patternMismatch: fieldElement.validity.patternMismatch,
                    tooLong: fieldElement.validity.tooLong,
                    tooShort: fieldElement.validity.tooShort,
                    rangeUnderflow: fieldElement.validity.rangeUnderflow,
                    rangeOverflow: fieldElement.validity.rangeOverflow,
                    stepMismatch: fieldElement.validity.stepMismatch
                };
            }
        } catch (e) {
            // HTML5 API недоступне
        }
        
        // 4.2. ARIA та доступність
        const ariaInvalid = fieldElement.getAttribute('aria-invalid');
        signals.aria_support.aria_invalid = ariaInvalid;
        if (ariaInvalid === 'true') {
            signals.aria_support.detected = true;
        }
        
        const ariaDescribedby = fieldElement.getAttribute('aria-describedby');
        signals.aria_support.aria_describedby = ariaDescribedby;
        if (ariaDescribedby) {
            const describedElements = ariaDescribedby.split(' ')
                .map(id => document.getElementById(id))
                .filter(el => el);
            
            if (describedElements.length > 0) {
                signals.aria_support.describedby_content = describedElements
                    .map(el => el.textContent.trim())
                    .join(' ');
                if (signals.aria_support.describedby_content) {
                    signals.aria_support.detected = true;
                }
            }
        }
        
        // Пошук role="alert" елементів
        const alertElements = Array.from(document.querySelectorAll('[role="alert"]'));
        signals.aria_support.role_alert_elements = alertElements
            .filter(el => el.textContent.trim())
            .map(el => ({
                text: el.textContent.trim(),
                id: el.id,
                className: el.className
            }));
        
        if (signals.aria_support.role_alert_elements.length > 0) {
            signals.aria_support.detected = true;
        }
        
        // 4.3. DOM-зміни біля інпуту
        const fieldContainer = fieldElement.closest('div, fieldset, section, form') || fieldElement.parentElement;
        if (fieldContainer) {
            const errorSelectors = [
                '.error', '.invalid', '.warning', '.alert',
                '.error-message', '.field-error', '.validation-error',
                '.help-block', '.form-error', '.input-error'
            ];
            
            const errorElements = [];
            errorSelectors.forEach(selector => {
                const elements = fieldContainer.querySelectorAll(selector);
                elements.forEach(el => {
                    const text = el.textContent.trim();
                    if (text && text.length < 200) { // Розумна довжина для повідомлення про помилку
                        errorElements.push({
                            selector: selector,
                            text: text,
                            visible: this.helpers.isElementVisible(el),
                            id: el.id,
                            className: el.className
                        });
                    }
                });
            });
            
            signals.dom_changes.nearby_error_elements = errorElements;
            signals.dom_changes.error_texts = errorElements.map(el => el.text);
            
            // Перевірка ключових слів у текстах
            const errorKeywords = [
                'invalid', 'required', 'must', 'error', 'wrong', 'incorrect',
                'невірний', 'обов\'язковий', 'помилка', 'неправильний', 'введіть', 'виберіть'
            ];
            
            const hasErrorKeywords = signals.dom_changes.error_texts.some(text => 
                errorKeywords.some(keyword => text.toLowerCase().includes(keyword.toLowerCase()))
            );
            
            if (errorElements.length > 0 && hasErrorKeywords) {
                signals.dom_changes.detected = true;
            }
        }
        
        // 4.4. CSS-статуси
        try {
            // Перевірка CSS класів помилок
            const errorClasses = ['error', 'invalid', 'warning', 'has-error', 'is-invalid'];
            const fieldClasses = Array.from(fieldElement.classList);
            const foundErrorClasses = fieldClasses.filter(cls => 
                errorClasses.some(errorCls => cls.toLowerCase().includes(errorCls))
            );
            
            signals.css_states.error_classes = foundErrorClasses;
            if (foundErrorClasses.length > 0) {
                signals.css_states.detected = true;
            }
            
            // Перевірка псевдокласу :invalid (спрощена)
            if (fieldElement.matches && fieldElement.matches(':invalid')) {
                signals.css_states.invalid_pseudoclass = true;
                signals.css_states.detected = true;
            }
            
        } catch (e) {
            // CSS перевірка не вдалася
        }
        
        return signals;
    }

    /**
     * Порожня структура сигналів
     */
    emptySignals() {
        return {
            html5_api: { detected: false, valid: null, validation_message: '', details: {} },
            aria_support: { detected: false, aria_invalid: null, aria_describedby: null, describedby_content: '', role_alert_elements: [] },
            dom_changes: { detected: false, nearby_error_elements: [], error_texts: [] },
            css_states: { detected: false, invalid_pseudoclass: false, error_classes: [] }
        };
    }

    /**
     * Розрахунок якості для одного сценарію
     */
    calculateScenarioQuality(signals) {
        let score = 0.0;
        
        // HTML5 API (25%)
        if (signals.html5_api.detected) {
            score += 0.25;
        }
        
        // ARIA підтримка (35%)
        if (signals.aria_support.detected) {
            let ariaScore = 0.0;
            if (signals.aria_support.aria_invalid === 'true') {
                ariaScore += 0.15;
            }
            if (signals.aria_support.describedby_content) {
                ariaScore += 0.15;
            }
            if (signals.aria_support.role_alert_elements.length > 0) {
                ariaScore += 0.05;
            }
            score += Math.min(ariaScore, 0.35);
        }
        
        // DOM зміни (25%)
        if (signals.dom_changes.detected) {
            score += 0.25;
        }
        
        // CSS стани (15%)
        if (signals.css_states.detected) {
            score += 0.15;
        }
        
        return Math.min(score, 1.0);
    }

    /**
     * Розрахунок загальної якості поля
     */
    calculateFieldQualityScore(fieldResult) {
        if (!fieldResult.test_scenarios || fieldResult.test_scenarios.length === 0) {
            return 0.0;
        }
        
        // Середня якість по всіх сценаріях
        const scenarioScores = fieldResult.test_scenarios.map(s => s.quality_score || 0.0);
        const avgScenarioScore = scenarioScores.reduce((a, b) => a + b, 0) / scenarioScores.length;
        
        // Бонус за різноманітність підтримки
        const detectionMethods = Object.values(fieldResult.error_detection_summary).filter(Boolean).length;
        const diversityBonus = Math.min(detectionMethods * 0.1, 0.2);
        
        return Math.min(avgScenarioScore + diversityBonus, 1.0);
    }

    /**
     * 6. Формування результату
     */
    compileSystematicResults(formSelector, fieldTestResults) {
        const totalFields = fieldTestResults.length;
        const supportedFields = fieldTestResults.filter(field => field.overall_support).length;
        
        // Розрахунок загальної якості форми
        let averageQuality = 0.0;
        if (totalFields > 0) {
            const totalQuality = fieldTestResults.reduce((sum, field) => sum + field.quality_score, 0);
            averageQuality = totalQuality / totalFields;
        }
        
        // Статистика по методах виявлення
        const detectionStats = {
            html5_api: fieldTestResults.filter(field => field.error_detection_summary.html5_api).length,
            aria_support: fieldTestResults.filter(field => field.error_detection_summary.aria_support).length,
            dom_changes: fieldTestResults.filter(field => field.error_detection_summary.dom_changes).length,
            css_states: fieldTestResults.filter(field => field.error_detection_summary.css_states).length
        };
        
        return {
            form_selector: formSelector,
            systematic_analysis: true,
            total_fields: totalFields,
            supported_fields: supportedFields,
            quality_score: averageQuality,
            field_results: fieldTestResults,
            detection_statistics: detectionStats,
            has_error_response: supportedFields > 0,
            field_specific_errors: fieldTestResults.some(field => field.overall_support),
            detailed_breakdown: {
                error_response: {
                    score: supportedFields > 0 ? 0.3 : 0.0,
                    description: `${supportedFields}/${totalFields} полів підтримують виявлення помилок`
                },
                error_localization: {
                    score: supportedFields === totalFields ? 0.3 : 
                           supportedFields > totalFields / 2 ? 0.2 : 
                           supportedFields > 0 ? 0.1 : 0.0,
                    description: `Систематичний аналіз: ${supportedFields}/${totalFields} полів`
                },
                accessibility: {
                    score: Math.min(detectionStats.aria_support / Math.max(totalFields, 1) * 0.2, 0.2),
                    description: `ARIA підтримка: ${detectionStats.aria_support}/${totalFields} полів`
                },
                message_quality: {
                    score: Math.min(averageQuality * 0.2, 0.2),
                    description: `Середня якість повідомлень: ${averageQuality.toFixed(2)}`
                }
            }
        };
    }

    /**
     * Створення результату для випадків помилок
     */
    createSystematicResult(reason, formSelector) {
        return {
            form_selector: formSelector,
            systematic_analysis: true,
            total_fields: 0,
            supported_fields: 0,
            quality_score: 0.0,
            field_results: [],
            detection_statistics: { html5_api: 0, aria_support: 0, dom_changes: 0, css_states: 0 },
            has_error_response: false,
            field_specific_errors: false,
            reason: reason,
            detailed_breakdown: {
                error_response: { score: 0.0, description: reason },
                error_localization: { score: 0.0, description: 'Не тестувалося' },
                accessibility: { score: 0.0, description: 'Не тестувалося' },
                message_quality: { score: 0.0, description: 'Не тестувалося' }
            }
        };
    }
}

// Експортуємо для використання
window.FormTester = FormTester;