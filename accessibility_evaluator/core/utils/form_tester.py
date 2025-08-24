"""
Клас для динамічного тестування форм та аналізу підтримки помилок
"""

from playwright.async_api import Page
from typing import Dict, Any, List, Optional
import asyncio
import json
from bs4 import BeautifulSoup


class FormTester:
    """Клас для систематичного тестування поведінки форм при помилках за новим алгоритмом"""
    
    def __init__(self):
        # Розширена бібліотека тестових значень
        self.invalid_test_scenarios = {
            'email': [
                {'value': '', 'type': 'empty', 'description': 'Порожнє поле'},
                {'value': 'abc', 'type': 'invalid_format', 'description': 'Невірний формат'},
                {'value': 'test@', 'type': 'incomplete', 'description': 'Неповний email'},
                {'value': '@domain.com', 'type': 'missing_local', 'description': 'Відсутня локальна частина'},
                {'value': 'a' * 255 + '@test.com', 'type': 'too_long', 'description': 'Занадто довгий'},
            ],
            'number': [
                {'value': '', 'type': 'empty', 'description': 'Порожнє поле'},
                {'value': 'abc', 'type': 'non_numeric', 'description': 'Не число'},
                {'value': '12.34.56', 'type': 'invalid_format', 'description': 'Невірний формат'},
                {'value': '999999999999999999999', 'type': 'too_large', 'description': 'Занадто велике число'},
            ],
            'tel': [
                {'value': '', 'type': 'empty', 'description': 'Порожнє поле'},
                {'value': '123', 'type': 'too_short', 'description': 'Занадто короткий'},
                {'value': 'abc-def-ghij', 'type': 'invalid_chars', 'description': 'Невірні символи'},
                {'value': '1' * 50, 'type': 'too_long', 'description': 'Занадто довгий'},
            ],
            'url': [
                {'value': '', 'type': 'empty', 'description': 'Порожнє поле'},
                {'value': 'not-url', 'type': 'invalid_format', 'description': 'Невірний формат'},
                {'value': 'http://', 'type': 'incomplete', 'description': 'Неповний URL'},
                {'value': 'ftp://invalid', 'type': 'unsupported_protocol', 'description': 'Непідтримуваний протокол'},
            ],
            'date': [
                {'value': '', 'type': 'empty', 'description': 'Порожнє поле'},
                {'value': '32/13/2023', 'type': 'invalid_date', 'description': 'Неіснуюча дата'},
                {'value': 'not-date', 'type': 'invalid_format', 'description': 'Невірний формат'},
                {'value': '2023-13-45', 'type': 'invalid_values', 'description': 'Невірні значення'},
            ],
            'time': [
                {'value': '', 'type': 'empty', 'description': 'Порожнє поле'},
                {'value': '25:99', 'type': 'invalid_time', 'description': 'Неіснуючий час'},
                {'value': 'not-time', 'type': 'invalid_format', 'description': 'Невірний формат'},
            ],
            'password': [
                {'value': '', 'type': 'empty', 'description': 'Порожній пароль'},
                {'value': '123', 'type': 'too_short', 'description': 'Занадто короткий'},
                {'value': '   ', 'type': 'whitespace_only', 'description': 'Тільки пробіли'},
            ],
            'text': [
                {'value': '', 'type': 'empty', 'description': 'Порожнє поле'},
                {'value': '   ', 'type': 'whitespace_only', 'description': 'Тільки пробіли'},
            ],
            'textarea': [
                {'value': '', 'type': 'empty', 'description': 'Порожнє поле'},
                {'value': '   ', 'type': 'whitespace_only', 'description': 'Тільки пробіли'},
            ]
        }
    
    async def test_form_error_behavior_systematic(self, page: Page, form_selector: str = 'form') -> Dict[str, Any]:
        """
        Систематичне тестування форми за новим алгоритмом:
        1. Ініціалізація аналізу
        2. Створення сценаріїв введення  
        3. Запуск перевірки
        4. Збір сигналів про помилку (HTML5 API, ARIA, DOM, CSS)
        5. Крос-перевірка
        6. Формування результату
        """
        
        print(f"🔬 Систематичне тестування форми: {form_selector}")
        
        try:
            # 1. Ініціалізація аналізу
            form_exists = await page.locator(form_selector).count() > 0
            if not form_exists:
                return self._create_systematic_result("Форма не знайдена", form_selector)
            
            # Визначити всі поля форми
            fields_data = await self._discover_form_fields(page, form_selector)
            if not fields_data:
                return self._create_systematic_result("Поля не знайдено", form_selector)
            
            print(f"📋 Знайдено {len(fields_data)} полів для тестування")
            
            # Результати тестування для кожного поля
            field_test_results = []
            
            for field_data in fields_data:
                print(f"🧪 Тестування поля: {field_data['selector']}")
                
                # 2-6. Тестування поля за алгоритмом
                field_result = await self._test_field_systematic(page, field_data)
                field_test_results.append(field_result)
            
            # Формування загального результату
            return self._compile_systematic_results(form_selector, field_test_results)
            
        except Exception as e:
            print(f"❌ Помилка систематичного тестування: {str(e)}")
            return self._create_systematic_result(f"Помилка: {str(e)}", form_selector)
    
    async def _discover_form_fields(self, page: Page, form_selector: str) -> List[Dict[str, Any]]:
        """1. Ініціалізація аналізу - визначення всіх полів форми"""
        
        fields_data = await page.evaluate(f"""
            () => {{
                const form = document.querySelector('{form_selector}');
                if (!form) return [];
                
                const fields = form.querySelectorAll('input, textarea, select');
                return Array.from(fields).map((field, index) => {{
                    const fieldType = field.type || field.tagName.toLowerCase();
                    const isTestable = (
                        field.required ||
                        field.pattern ||
                        field.minLength > 0 ||
                        field.maxLength > 0 && field.maxLength < 524288 ||
                        field.min !== '' ||
                        field.max !== '' ||
                        ['email', 'number', 'tel', 'url', 'date', 'time', 'datetime-local', 'password'].includes(fieldType)
                    );
                    
                    return {{
                        selector: field.id ? '#' + field.id : 
                                 field.name ? '[name="' + field.name + '"]' :
                                 '{form_selector} ' + field.tagName.toLowerCase() + ':nth-child(' + (index + 1) + ')',
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
                        isTestable: isTestable
                    }};
                }}).filter(field => field.isTestable);
            }}
        """)
        
        return fields_data
    
    async def _test_field_systematic(self, page: Page, field_data: Dict[str, Any]) -> Dict[str, Any]:
        """2-6. Систематичне тестування одного поля"""
        
        field_selector = field_data['selector']
        field_type = field_data['type']
        
        # 2. Створення сценаріїв введення
        test_scenarios = self._generate_test_scenarios(field_data)
        
        field_result = {
            'selector': field_selector,
            'type': field_type,
            'field_data': field_data,
            'test_scenarios': [],
            'error_detection_summary': {
                'html5_api': False,
                'aria_support': False,
                'dom_changes': False,
                'css_states': False
            },
            'overall_support': False,
            'quality_score': 0.0
        }
        
        # Тестуємо кожен сценарій
        for scenario in test_scenarios:
            print(f"   📝 Сценарій: {scenario['description']} -> '{scenario['value']}'")
            
            scenario_result = await self._test_scenario(page, field_selector, scenario)
            field_result['test_scenarios'].append(scenario_result)
            
            # Оновлюємо загальну інформацію про підтримку
            if scenario_result['error_detected']:
                field_result['error_detection_summary']['html5_api'] |= scenario_result['signals']['html5_api']['detected']
                field_result['error_detection_summary']['aria_support'] |= scenario_result['signals']['aria_support']['detected']
                field_result['error_detection_summary']['dom_changes'] |= scenario_result['signals']['dom_changes']['detected']
                field_result['error_detection_summary']['css_states'] |= scenario_result['signals']['css_states']['detected']
        
        # 5. Крос-перевірка
        field_result['overall_support'] = any(field_result['error_detection_summary'].values())
        field_result['quality_score'] = self._calculate_field_quality_score(field_result)
        
        return field_result
    
    def _generate_test_scenarios(self, field_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """2. Створення сценаріїв введення для поля"""
        
        field_type = field_data['type']
        scenarios = []
        
        # Базові сценарії з бібліотеки
        if field_type in self.invalid_test_scenarios:
            base_scenarios = self.invalid_test_scenarios[field_type]
        else:
            # Загальні сценарії для невідомих типів
            base_scenarios = [
                {'value': '', 'type': 'empty', 'description': 'Порожнє поле'},
                {'value': '   ', 'type': 'whitespace', 'description': 'Тільки пробіли'},
            ]
        
        # Фільтруємо сценарії залежно від атрибутів поля
        for scenario in base_scenarios:
            # Порожнє поле тестуємо тільки для required
            if scenario['type'] == 'empty' and not field_data.get('required'):
                continue
            
            scenarios.append(scenario)
        
        # Додаткові сценарії на основі атрибутів
        if field_data.get('maxLength') and field_data['maxLength'] > 0:
            scenarios.append({
                'value': 'a' * (field_data['maxLength'] + 10),
                'type': 'exceeds_maxlength',
                'description': f'Перевищує maxLength ({field_data["maxLength"]})'
            })
        
        if field_data.get('min') and field_type == 'number':
            try:
                min_val = float(field_data['min'])
                scenarios.append({
                    'value': str(min_val - 1),
                    'type': 'below_min',
                    'description': f'Менше мінімуму ({field_data["min"]})'
                })
            except:
                pass
        
        if field_data.get('max') and field_type == 'number':
            try:
                max_val = float(field_data['max'])
                scenarios.append({
                    'value': str(max_val + 1),
                    'type': 'above_max',
                    'description': f'Більше максимуму ({field_data["max"]})'
                })
            except:
                pass
        
        return scenarios[:3]  # Обмежуємо кількість сценаріїв для швидкості
    
    async def _test_scenario(self, page: Page, field_selector: str, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """3-4. Запуск перевірки та збір сигналів про помилку"""
        
        try:
            # 3. Запуск перевірки
            # Ввести некоректне значення
            await page.locator(field_selector).clear()
            if scenario['value']:  # Тільки якщо значення не порожнє
                await page.locator(field_selector).fill(scenario['value'])
            
            # Викликати події blur (імітація дій користувача)
            await page.locator(field_selector).blur()
            await page.wait_for_timeout(100)  # Дати час на реакцію
            
            # 4. Збір сигналів про помилку
            signals = await self._collect_error_signals(page, field_selector)
            
            # Визначити чи була виявлена помилка
            error_detected = any([
                signals['html5_api']['detected'],
                signals['aria_support']['detected'], 
                signals['dom_changes']['detected'],
                signals['css_states']['detected']
            ])
            
            return {
                'scenario': scenario,
                'field_selector': field_selector,
                'error_detected': error_detected,
                'signals': signals,
                'quality_score': self._calculate_scenario_quality(signals)
            }
            
        except Exception as e:
            print(f"⚠️ Помилка тестування сценарію: {str(e)}")
            return {
                'scenario': scenario,
                'field_selector': field_selector,
                'error_detected': False,
                'signals': self._empty_signals(),
                'error': str(e),
                'quality_score': 0.0
            }
    
    async def _collect_error_signals(self, page: Page, field_selector: str) -> Dict[str, Any]:
        """4. Збір сигналів про помилку (4 рівні)"""
        
        signals = await page.evaluate(f"""
            (fieldSelector) => {{
                const field = document.querySelector(fieldSelector);
                if (!field) return null;
                
                const signals = {{
                    html5_api: {{
                        detected: false,
                        valid: null,
                        validation_message: '',
                        details: {{}}
                    }},
                    aria_support: {{
                        detected: false,
                        aria_invalid: null,
                        aria_describedby: null,
                        describedby_content: '',
                        role_alert_elements: []
                    }},
                    dom_changes: {{
                        detected: false,
                        nearby_error_elements: [],
                        error_texts: []
                    }},
                    css_states: {{
                        detected: false,
                        invalid_pseudoclass: false,
                        error_classes: []
                    }}
                }};
                
                // 4.1. HTML5 Validity API
                try {{
                    signals.html5_api.valid = field.validity.valid;
                    signals.html5_api.validation_message = field.validationMessage || '';
                    signals.html5_api.detected = !field.validity.valid;
                    signals.html5_api.details = {{
                        valueMissing: field.validity.valueMissing,
                        typeMismatch: field.validity.typeMismatch,
                        patternMismatch: field.validity.patternMismatch,
                        tooLong: field.validity.tooLong,
                        tooShort: field.validity.tooShort,
                        rangeUnderflow: field.validity.rangeUnderflow,
                        rangeOverflow: field.validity.rangeOverflow,
                        stepMismatch: field.validity.stepMismatch
                    }};
                }} catch (e) {{
                    // HTML5 API недоступне
                }}
                
                // 4.2. ARIA та доступність
                const ariaInvalid = field.getAttribute('aria-invalid');
                signals.aria_support.aria_invalid = ariaInvalid;
                if (ariaInvalid === 'true') {{
                    signals.aria_support.detected = true;
                }}
                
                const ariaDescribedby = field.getAttribute('aria-describedby');
                signals.aria_support.aria_describedby = ariaDescribedby;
                if (ariaDescribedby) {{
                    const describedElements = ariaDescribedby.split(' ').map(id => document.getElementById(id)).filter(el => el);
                    if (describedElements.length > 0) {{
                        signals.aria_support.describedby_content = describedElements.map(el => el.textContent.trim()).join(' ');
                        if (signals.aria_support.describedby_content) {{
                            signals.aria_support.detected = true;
                        }}
                    }}
                }}
                
                // Пошук role="alert" елементів
                const alertElements = Array.from(document.querySelectorAll('[role="alert"]'));
                signals.aria_support.role_alert_elements = alertElements
                    .filter(el => el.textContent.trim())
                    .map(el => ({{
                        text: el.textContent.trim(),
                        id: el.id,
                        className: el.className
                    }}));
                
                if (signals.aria_support.role_alert_elements.length > 0) {{
                    signals.aria_support.detected = true;
                }}
                
                // 4.3. DOM-зміни біля інпуту
                const fieldContainer = field.closest('div, fieldset, section, form') || field.parentElement;
                if (fieldContainer) {{
                    const errorSelectors = [
                        '.error', '.invalid', '.warning', '.alert',
                        '.error-message', '.field-error', '.validation-error',
                        '.help-block', '.form-error', '.input-error'
                    ];
                    
                    const errorElements = [];
                    errorSelectors.forEach(selector => {{
                        const elements = fieldContainer.querySelectorAll(selector);
                        elements.forEach(el => {{
                            const text = el.textContent.trim();
                            if (text && text.length < 200) {{ // Розумна довжина для повідомлення про помилку
                                errorElements.push({{
                                    selector: selector,
                                    text: text,
                                    visible: el.offsetParent !== null,
                                    id: el.id,
                                    className: el.className
                                }});
                            }}
                        }});
                    }});
                    
                    signals.dom_changes.nearby_error_elements = errorElements;
                    signals.dom_changes.error_texts = errorElements.map(el => el.text);
                    
                    // Перевірка ключових слів у текстах
                    const errorKeywords = [
                        'invalid', 'required', 'must', 'error', 'wrong', 'incorrect',
                        'невірний', 'обов\\'язковий', 'помилка', 'неправильний', 'введіть', 'виберіть'
                    ];
                    
                    const hasErrorKeywords = signals.dom_changes.error_texts.some(text => 
                        errorKeywords.some(keyword => text.toLowerCase().includes(keyword.toLowerCase()))
                    );
                    
                    if (errorElements.length > 0 && hasErrorKeywords) {{
                        signals.dom_changes.detected = true;
                    }}
                }}
                
                // 4.4. CSS-статуси
                try {{
                    // Перевірка псевдокласу :invalid
                    const computedStyle = window.getComputedStyle(field, ':invalid');
                    const normalStyle = window.getComputedStyle(field);
                    
                    // Порівнюємо стилі для виявлення :invalid
                    const borderColorInvalid = computedStyle.borderColor;
                    const borderColorNormal = normalStyle.borderColor;
                    
                    if (borderColorInvalid !== borderColorNormal) {{
                        signals.css_states.invalid_pseudoclass = true;
                        signals.css_states.detected = true;
                    }}
                    
                    // Перевірка CSS класів помилок
                    const errorClasses = ['error', 'invalid', 'warning', 'has-error', 'is-invalid'];
                    const fieldClasses = Array.from(field.classList);
                    const foundErrorClasses = fieldClasses.filter(cls => 
                        errorClasses.some(errorCls => cls.toLowerCase().includes(errorCls))
                    );
                    
                    signals.css_states.error_classes = foundErrorClasses;
                    if (foundErrorClasses.length > 0) {{
                        signals.css_states.detected = true;
                    }}
                    
                }} catch (e) {{
                    // CSS перевірка не вдалася
                }}
                
                return signals;
            }}
        """, field_selector)
        
        return signals or self._empty_signals()
    
    def _empty_signals(self) -> Dict[str, Any]:
        """Порожня структура сигналів"""
        return {
            'html5_api': {'detected': False, 'valid': None, 'validation_message': '', 'details': {}},
            'aria_support': {'detected': False, 'aria_invalid': None, 'aria_describedby': None, 'describedby_content': '', 'role_alert_elements': []},
            'dom_changes': {'detected': False, 'nearby_error_elements': [], 'error_texts': []},
            'css_states': {'detected': False, 'invalid_pseudoclass': False, 'error_classes': []}
        }
    
    def _calculate_scenario_quality(self, signals: Dict[str, Any]) -> float:
        """Розрахунок якості для одного сценарію"""
        score = 0.0
        
        # HTML5 API (25%)
        if signals['html5_api']['detected']:
            score += 0.25
        
        # ARIA підтримка (35%)
        if signals['aria_support']['detected']:
            aria_score = 0.0
            if signals['aria_support']['aria_invalid'] == 'true':
                aria_score += 0.15
            if signals['aria_support']['describedby_content']:
                aria_score += 0.15
            if signals['aria_support']['role_alert_elements']:
                aria_score += 0.05
            score += min(aria_score, 0.35)
        
        # DOM зміни (25%)
        if signals['dom_changes']['detected']:
            score += 0.25
        
        # CSS стани (15%)
        if signals['css_states']['detected']:
            score += 0.15
        
        return min(score, 1.0)
    
    def _calculate_field_quality_score(self, field_result: Dict[str, Any]) -> float:
        """Розрахунок загальної якості поля"""
        if not field_result['test_scenarios']:
            return 0.0
        
        # Середня якість по всіх сценаріях
        scenario_scores = [s.get('quality_score', 0.0) for s in field_result['test_scenarios']]
        avg_scenario_score = sum(scenario_scores) / len(scenario_scores)
        
        # Бонус за різноманітність підтримки
        detection_methods = sum(field_result['error_detection_summary'].values())
        diversity_bonus = min(detection_methods * 0.1, 0.2)
        
        return min(avg_scenario_score + diversity_bonus, 1.0)
    
    def _compile_systematic_results(self, form_selector: str, field_test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """6. Формування результату"""
        
        total_fields = len(field_test_results)
        supported_fields = sum(1 for field in field_test_results if field['overall_support'])
        
        # Розрахунок загальної якості форми
        if total_fields > 0:
            total_quality = sum(field['quality_score'] for field in field_test_results)
            average_quality = total_quality / total_fields
        else:
            average_quality = 0.0
        
        # Статистика по методах виявлення
        detection_stats = {
            'html5_api': sum(1 for field in field_test_results if field['error_detection_summary']['html5_api']),
            'aria_support': sum(1 for field in field_test_results if field['error_detection_summary']['aria_support']),
            'dom_changes': sum(1 for field in field_test_results if field['error_detection_summary']['dom_changes']),
            'css_states': sum(1 for field in field_test_results if field['error_detection_summary']['css_states'])
        }
        
        return {
            'form_selector': form_selector,
            'systematic_analysis': True,
            'total_fields': total_fields,
            'supported_fields': supported_fields,
            'quality_score': average_quality,
            'field_results': field_test_results,
            'detection_statistics': detection_stats,
            'has_error_response': supported_fields > 0,
            'field_specific_errors': any(field['overall_support'] for field in field_test_results),
            'detailed_breakdown': {
                'error_response': {
                    'score': 0.3 if supported_fields > 0 else 0.0,
                    'description': f'{supported_fields}/{total_fields} полів підтримують виявлення помилок'
                },
                'error_localization': {
                    'score': 0.3 if supported_fields == total_fields else 0.2 if supported_fields > total_fields/2 else 0.1 if supported_fields > 0 else 0.0,
                    'description': f'Систематичний аналіз: {supported_fields}/{total_fields} полів'
                },
                'accessibility': {
                    'score': min(detection_stats['aria_support'] / max(total_fields, 1) * 0.2, 0.2),
                    'description': f'ARIA підтримка: {detection_stats["aria_support"]}/{total_fields} полів'
                },
                'message_quality': {
                    'score': min(average_quality * 0.2, 0.2),
                    'description': f'Середня якість повідомлень: {average_quality:.2f}'
                }
            }
        }
    
    def _create_systematic_result(self, reason: str, form_selector: str) -> Dict[str, Any]:
        """Створення результату для випадків помилок"""
        return {
            'form_selector': form_selector,
            'systematic_analysis': True,
            'total_fields': 0,
            'supported_fields': 0,
            'quality_score': 0.0,
            'field_results': [],
            'detection_statistics': {'html5_api': 0, 'aria_support': 0, 'dom_changes': 0, 'css_states': 0},
            'has_error_response': False,
            'field_specific_errors': False,
            'reason': reason,
            'detailed_breakdown': {
                'error_response': {'score': 0.0, 'description': reason},
                'error_localization': {'score': 0.0, 'description': 'Не тестувалося'},
                'accessibility': {'score': 0.0, 'description': 'Не тестувалося'},
                'message_quality': {'score': 0.0, 'description': 'Не тестувалося'}
            }
        }
    
    async def test_form_error_behavior(self, page: Page, form_selector: str = 'form') -> Dict[str, Any]:
        """
        Основний метод для тестування поведінки форми при помилках
        
        Args:
            page: Playwright page об'єкт
            form_selector: CSS селектор форми
            
        Returns:
            Детальний аналіз поведінки форми при помилках
        """
        
        print(f"🧪 Початок динамічного тестування форми: {form_selector}")
        
        try:
            # Перевіряємо чи існує форма
            form_exists = await page.locator(form_selector).count() > 0
            if not form_exists:
                print(f"⚠️ Форма {form_selector} не знайдена")
                return self._create_empty_result("Форма не знайдена")
            
            # Етап 1: Зберігаємо початковий стан
            print("📸 Збереження початкового стану форми...")
            initial_state = await self._capture_form_state(page, form_selector)
            
            # Етап 2: Знаходимо поля для тестування
            print("🔍 Аналіз полів форми...")
            testable_fields = await self._find_testable_fields(page, form_selector)
            
            if not testable_fields:
                print("⚠️ Не знайдено полів для тестування")
                return self._create_empty_result("Немає полів для тестування")
            
            print(f"📝 Знайдено {len(testable_fields)} полів для тестування")
            
            # Етап 3: Заповнюємо невалідними даними
            print("💥 Заповнення полів невалідними даними...")
            await self._fill_invalid_data(page, form_selector, testable_fields)
            
            # Етап 4: Спробуємо submit форму
            print("📤 Спроба відправки форми...")
            submit_result = await self._attempt_form_submit(page, form_selector)
            
            # Етап 5: Аналізуємо зміни після submit
            print("🔍 Аналіз змін після відправки...")
            final_state = await self._capture_form_state(page, form_selector)
            
            # Етап 6: Порівнюємо стани та оцінюємо якість
            print("📊 Оцінка якості підтримки помилок...")
            analysis = await self._analyze_error_response(
                initial_state, final_state, testable_fields, submit_result
            )
            
            print(f"✅ Динамічне тестування завершено. Якість: {analysis.get('quality_score', 0):.3f}")
            return analysis
            
        except Exception as e:
            print(f"❌ Помилка під час динамічного тестування: {str(e)}")
            return self._create_empty_result(f"Помилка тестування: {str(e)}")
    
    async def _capture_form_state(self, page: Page, form_selector: str) -> Dict[str, Any]:
        """Захоплює поточний стан форми"""
        
        try:
            # Отримуємо HTML форми
            form_html = await page.locator(form_selector).inner_html()
            
            # Отримуємо всі поля форми з їх значеннями
            fields_data = await page.evaluate(f"""
                () => {{
                    const form = document.querySelector('{form_selector}');
                    if (!form) return [];
                    
                    const fields = form.querySelectorAll('input, textarea, select');
                    return Array.from(fields).map(field => {{
                        return {{
                            selector: field.tagName.toLowerCase() + 
                                     (field.id ? '#' + field.id : '') + 
                                     (field.name ? '[name="' + field.name + '"]' : ''),
                            type: field.type || field.tagName.toLowerCase(),
                            value: field.value || '',
                            required: field.required || false,
                            'aria-invalid': field.getAttribute('aria-invalid'),
                            'aria-describedby': field.getAttribute('aria-describedby'),
                            className: field.className,
                            id: field.id,
                            name: field.name
                        }};
                    }});
                }}
            """)
            
            # Шукаємо елементи повідомлень про помилки
            error_elements = await page.evaluate("""
                () => {
                    const errorSelectors = [
                        '.error', '.invalid', '.warning', '.alert',
                        '[role="alert"]', '[aria-live]', '.form-error',
                        '.field-error', '.validation-error', '.help-block'
                    ];
                    
                    const errorElements = [];
                    errorSelectors.forEach(selector => {
                        const elements = document.querySelectorAll(selector);
                        elements.forEach(el => {
                            if (el.textContent.trim()) {
                                errorElements.push({
                                    selector: selector,
                                    text: el.textContent.trim(),
                                    visible: el.offsetParent !== null,
                                    id: el.id,
                                    className: el.className
                                });
                            }
                        });
                    });
                    
                    return errorElements;
                }
            """)
            
            return {
                'form_html': form_html,
                'fields': fields_data,
                'error_elements': error_elements,
                'timestamp': asyncio.get_event_loop().time()
            }
            
        except Exception as e:
            print(f"❌ Помилка захоплення стану форми: {str(e)}")
            return {'error': str(e)}
    
    async def _find_testable_fields(self, page: Page, form_selector: str) -> List[Dict[str, Any]]:
        """Знаходить поля, які можна тестувати на помилки"""
        
        testable_fields = await page.evaluate(f"""
            () => {{
                const form = document.querySelector('{form_selector}');
                if (!form) return [];
                
                const fields = form.querySelectorAll('input, textarea, select');
                const testableFields = [];
                
                fields.forEach(field => {{
                    const fieldType = field.type || field.tagName.toLowerCase();
                    const isTestable = (
                        field.required ||
                        field.pattern ||
                        ['email', 'number', 'tel', 'url', 'date', 'time', 'datetime-local'].includes(fieldType) ||
                        (fieldType === 'text' && field.required) ||
                        (fieldType === 'textarea' && field.required)
                    );
                    
                    if (isTestable) {{
                        testableFields.push({{
                            selector: field.tagName.toLowerCase() + 
                                     (field.id ? '#' + field.id : '') + 
                                     (field.name ? '[name="' + field.name + '"]' : ''),
                            type: fieldType,
                            required: field.required || false,
                            pattern: field.pattern || null,
                            id: field.id,
                            name: field.name,
                            placeholder: field.placeholder || ''
                        }});
                    }}
                }});
                
                return testableFields;
            }}
        """)
        
        return testable_fields
    
    async def _fill_invalid_data(self, page: Page, form_selector: str, testable_fields: List[Dict[str, Any]]):
        """Заповнює поля невалідними даними"""
        
        for field in testable_fields:
            try:
                field_type = field['type']
                field_selector = f"{form_selector} {field['selector']}"
                
                # Вибираємо невалідні дані залежно від типу поля
                if field['required'] and field_type in ['text', 'textarea']:
                    # Для required полів залишаємо порожніми
                    invalid_value = ''
                elif field_type in self.invalid_test_data:
                    # Вибираємо перше невалідне значення для типу
                    invalid_value = self.invalid_test_data[field_type][0]
                else:
                    # Загальне невалідне значення
                    invalid_value = 'invalid-test-data'
                
                print(f"   📝 Заповнення {field['selector']} ({field_type}) значенням: '{invalid_value}'")
                
                # Очищаємо поле та заповнюємо новим значенням
                await page.locator(field_selector).clear()
                if invalid_value:  # Тільки якщо значення не порожнє
                    await page.locator(field_selector).fill(invalid_value)
                
                # Викликаємо blur event для тригеру валідації
                await page.locator(field_selector).blur()
                
                # Невелика затримка для обробки JS валідації
                await page.wait_for_timeout(50)
                
            except Exception as e:
                print(f"⚠️ Не вдалося заповнити поле {field['selector']}: {str(e)}")
    
    async def _attempt_form_submit(self, page: Page, form_selector: str) -> Dict[str, Any]:
        """Спробує відправити форму та проаналізує результат"""
        
        try:
            # Шукаємо кнопку submit
            submit_button_locator = page.locator(f"{form_selector} button[type='submit'], {form_selector} input[type='submit']").first
            
            if await submit_button_locator.count() == 0:
                print("⚠️ Кнопка submit не знайдена")
                return {'success': False, 'reason': 'No submit button found'}
            
            # Зберігаємо поточний URL
            current_url = page.url
            
            # Натискаємо submit
            await submit_button_locator.click()
            
            # Чекаємо можливі зміни (зменшуємо timeout)
            await page.wait_for_timeout(500)
            
            # Перевіряємо чи змінився URL (можлива переадресація)
            new_url = page.url
            url_changed = current_url != new_url
            
            return {
                'success': True,
                'url_changed': url_changed,
                'initial_url': current_url,
                'final_url': new_url
            }
            
        except Exception as e:
            print(f"⚠️ Помилка при відправці форми: {str(e)}")
            return {'success': False, 'reason': str(e)}
    
    async def _analyze_error_response(
        self, 
        initial_state: Dict[str, Any], 
        final_state: Dict[str, Any], 
        testable_fields: List[Dict[str, Any]], 
        submit_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Аналізує відповідь форми на невалідні дані та розраховує якість"""
        
        if 'error' in initial_state or 'error' in final_state:
            return self._create_empty_result("Помилка захоплення стану")
        
        analysis = {
            'has_error_response': False,
            'field_specific_errors': False,
            'grouped_errors': False,
            'general_error_message': False,
            'aria_updates': False,
            'focus_management': False,
            'new_error_elements': [],
            'changed_fields': [],
            'error_messages': [],
            'quality_score': 0.0,
            'detailed_breakdown': {}
        }
        
        # Порівнюємо кількість елементів помилок
        initial_errors = len(initial_state.get('error_elements', []))
        final_errors = len(final_state.get('error_elements', []))
        
        if final_errors > initial_errors:
            analysis['has_error_response'] = True
            analysis['new_error_elements'] = final_state['error_elements'][initial_errors:]
            
            # Збираємо тексти повідомлень
            for error_elem in analysis['new_error_elements']:
                analysis['error_messages'].append(error_elem['text'])
        
        # Аналізуємо зміни в полях (aria-invalid, класи)
        initial_fields = {f['selector']: f for f in initial_state.get('fields', [])}
        final_fields = {f['selector']: f for f in final_state.get('fields', [])}
        
        for selector, final_field in final_fields.items():
            initial_field = initial_fields.get(selector, {})
            
            # Перевіряємо зміни aria-invalid
            initial_aria = initial_field.get('aria-invalid')
            final_aria = final_field.get('aria-invalid')
            
            if initial_aria != final_aria and final_aria == 'true':
                analysis['aria_updates'] = True
                analysis['changed_fields'].append({
                    'selector': selector,
                    'change': 'aria-invalid updated to true'
                })
            
            # Перевіряємо зміни класів (error, invalid тощо)
            initial_classes = initial_field.get('className', '')
            final_classes = final_field.get('className', '')
            
            error_classes = ['error', 'invalid', 'warning', 'has-error']
            has_error_class = any(cls in final_classes for cls in error_classes)
            had_error_class = any(cls in initial_classes for cls in error_classes)
            
            if has_error_class and not had_error_class:
                analysis['changed_fields'].append({
                    'selector': selector,
                    'change': f'Added error class: {final_classes}'
                })
        
        # Визначаємо тип відгуку на помилки
        if analysis['new_error_elements']:
            # Аналізуємо розташування повідомлень
            field_specific_count = 0
            general_count = 0
            
            for error_elem in analysis['new_error_elements']:
                # Евристика: якщо повідомлення містить ID поля або знаходиться поруч
                is_field_specific = any(
                    field['id'] in error_elem.get('id', '') or 
                    field['name'] in error_elem.get('text', '') or
                    field['id'] in error_elem.get('text', '')
                    for field in testable_fields
                    if field.get('id') or field.get('name')
                )
                
                if is_field_specific:
                    field_specific_count += 1
                else:
                    general_count += 1
            
            if field_specific_count > 0:
                analysis['field_specific_errors'] = True
            elif general_count > 0:
                analysis['general_error_message'] = True
        
        # Розраховуємо якість
        analysis['quality_score'] = self._calculate_dynamic_error_score(analysis)
        
        # Детальний розбір
        analysis['detailed_breakdown'] = {
            'error_response': {
                'score': 0.3 if analysis['has_error_response'] else 0.0,
                'description': 'Форма реагує на невалідні дані' if analysis['has_error_response'] else 'Форма не реагує на помилки'
            },
            'error_localization': {
                'score': self._score_error_localization(analysis),
                'description': self._describe_error_localization(analysis)
            },
            'accessibility': {
                'score': self._score_accessibility_features(analysis),
                'description': self._describe_accessibility_features(analysis)
            },
            'message_quality': {
                'score': self._score_message_quality(analysis['error_messages']),
                'description': f"Проаналізовано {len(analysis['error_messages'])} повідомлень"
            }
        }
        
        return analysis
    
    def _calculate_dynamic_error_score(self, analysis: Dict[str, Any]) -> float:
        """Розраховує загальний скор якості підтримки помилок"""
        
        score = 0.0
        
        # Базовий відгук (0.3)
        if analysis['has_error_response']:
            score += 0.3
        
        # Локалізація помилок (0.3)
        if analysis['field_specific_errors']:
            score += 0.3
        elif analysis['grouped_errors']:
            score += 0.2
        elif analysis['general_error_message']:
            score += 0.1
        
        # Доступність (0.2)
        if analysis['aria_updates']:
            score += 0.1
        if analysis['focus_management']:
            score += 0.1
        
        # Якість повідомлень (0.2)
        message_score = self._score_message_quality(analysis['error_messages'])
        score += message_score * 0.2
        
        return min(score, 1.0)
    
    def _score_error_localization(self, analysis: Dict[str, Any]) -> float:
        """Оцінює якість локалізації помилок"""
        if analysis['field_specific_errors']:
            return 0.3
        elif analysis['grouped_errors']:
            return 0.2
        elif analysis['general_error_message']:
            return 0.1
        return 0.0
    
    def _describe_error_localization(self, analysis: Dict[str, Any]) -> str:
        """Описує якість локалізації помилок"""
        if analysis['field_specific_errors']:
            return "Повідомлення прив'язані до конкретних полів"
        elif analysis['grouped_errors']:
            return "Повідомлення згруповані за типами помилок"
        elif analysis['general_error_message']:
            return "Загальне повідомлення про помилку"
        return "Відсутні повідомлення про помилки"
    
    def _score_accessibility_features(self, analysis: Dict[str, Any]) -> float:
        """Оцінює функції доступності"""
        score = 0.0
        if analysis['aria_updates']:
            score += 0.1
        if analysis['focus_management']:
            score += 0.1
        return score
    
    def _describe_accessibility_features(self, analysis: Dict[str, Any]) -> str:
        """Описує функції доступності"""
        features = []
        if analysis['aria_updates']:
            features.append("ARIA атрибути оновлюються")
        if analysis['focus_management']:
            features.append("Управління фокусом")
        
        if features:
            return "; ".join(features)
        return "Базові функції доступності відсутні"
    
    def _score_message_quality(self, messages: List[str]) -> float:
        """Оцінює якість повідомлень про помилки"""
        if not messages:
            return 0.0
        
        total_quality = 0.0
        for message in messages:
            # Базові критерії якості
            quality = 0.0
            
            # Довжина (не занадто коротке/довге)
            if 5 <= len(message) <= 100:
                quality += 0.3
            
            # Конструктивність
            constructive_words = ['введіть', 'виберіть', 'перевірте', 'має містити', 'формат', 'please', 'enter', 'select', 'check']
            if any(word in message.lower() for word in constructive_words):
                quality += 0.4
            
            # Специфічність
            specific_words = ['email', 'пароль', 'телефон', 'дата', 'символів', 'цифр', 'password', 'phone', 'date']
            if any(word in message.lower() for word in specific_words):
                quality += 0.3
            
            total_quality += min(quality, 1.0)
        
        return total_quality / len(messages)
    
    def _create_empty_result(self, reason: str) -> Dict[str, Any]:
        """Створює порожній результат з поясненням"""
        return {
            'has_error_response': False,
            'field_specific_errors': False,
            'grouped_errors': False,
            'general_error_message': False,
            'aria_updates': False,
            'focus_management': False,
            'new_error_elements': [],
            'changed_fields': [],
            'error_messages': [],
            'quality_score': 0.0,
            'reason': reason,
            'detailed_breakdown': {
                'error_response': {'score': 0.0, 'description': reason},
                'error_localization': {'score': 0.0, 'description': 'Не тестувалося'},
                'accessibility': {'score': 0.0, 'description': 'Не тестувалося'},
                'message_quality': {'score': 0.0, 'description': 'Не тестувалося'}
            }
        }