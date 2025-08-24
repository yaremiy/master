"""
Метрики зрозумілості (UAC-1.3-G)
"""

from bs4 import BeautifulSoup
from typing import Dict, Any, List
import re
import textstat


class UnderstandabilityMetrics:
    """Клас для розрахунку метрик зрозумілості"""
    
    async def calculate_metrics(self, page_data: Dict[str, Any]) -> Dict[str, float]:
        """Розрахунок всіх метрик зрозумілості"""
        
        return {
            'instruction_clarity': self.calculate_instruction_clarity_metric(page_data),
            'input_assistance': self.calculate_input_assistance_metric(page_data),
            'error_support': self.calculate_error_support_metric(page_data)
        }
    
    def calculate_instruction_clarity_metric(self, page_data: Dict[str, Any]) -> float:
        """
        Розрахунок метрики зрозумілих інструкцій (UAC-1.3.1-G)
        
        Формула: X = A / B
        A = кількість інструкцій, оцінених як зрозумілі
        B = загальна кількість інструкцій
        """
        
        html_content = page_data.get('html_content', '')
        instructions = self._extract_instructions_with_context(html_content)
        
        if not instructions:
            return 1.0  # Немає інструкцій = немає проблем
        
        clear_instructions = 0
        
        for instruction_data in instructions:
            text = instruction_data['text']
            context = instruction_data.get('context', {})
            
            if self._assess_instruction_clarity_with_context(text, context):
                clear_instructions += 1
        
        return clear_instructions / len(instructions)
    
    def _extract_instructions(self, html_content: str) -> List[str]:
        """Витягування інструкцій з HTML"""
        
        soup = BeautifulSoup(html_content, 'html.parser')
        instructions = []
        
        # Селектори для пошуку інструкцій
        instruction_selectors = [
            'label',
            '.help-text',
            '.instruction',
            '.form-help',
            '.hint',
            'small',
            '[aria-describedby]',
            '.description'
        ]
        
        for selector in instruction_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text().strip()
                if text and len(text) > 5:  # Фільтруємо короткі тексти
                    instructions.append(text)
        
        # Також шукаємо placeholder тексти
        inputs_with_placeholders = soup.find_all('input', placeholder=True)
        for input_elem in inputs_with_placeholders:
            placeholder = input_elem.get('placeholder', '').strip()
            if placeholder and len(placeholder) > 5:
                instructions.append(placeholder)
        
        return list(set(instructions))  # Видаляємо дублікати
    
    def _extract_instructions_with_context(self, html_content: str) -> List[Dict[str, Any]]:
        """Витягування інструкцій з HTML з контекстом про тип поля"""
        
        soup = BeautifulSoup(html_content, 'html.parser')
        instructions = []
        
        # Шукаємо labels пов'язані з input полями
        labels = soup.find_all('label')
        for label in labels:
            text = label.get_text().strip()
            if text and len(text) >= 2:
                # Знаходимо пов'язане поле
                field_id = label.get('for')
                field_type = 'unknown'
                
                if field_id:
                    field = soup.find(id=field_id)
                    if field:
                        field_type = field.get('type', field.name)
                
                instructions.append({
                    'text': text,
                    'element': 'label',
                    'context': {
                        'field_type': field_type,
                        'field_id': field_id
                    }
                })
        
        # Шукаємо placeholder тексти з контекстом
        inputs_with_placeholders = soup.find_all(['input', 'textarea'], placeholder=True)
        for input_elem in inputs_with_placeholders:
            placeholder = input_elem.get('placeholder', '').strip()
            if placeholder and len(placeholder) >= 2:
                field_type = input_elem.get('type', input_elem.name)
                
                instructions.append({
                    'text': placeholder,
                    'element': 'placeholder',
                    'context': {
                        'field_type': field_type,
                        'field_id': input_elem.get('id')
                    }
                })
        
        # Шукаємо aria-label з контекстом
        inputs_with_aria = soup.find_all(['input', 'textarea'], attrs={'aria-label': True})
        for input_elem in inputs_with_aria:
            aria_label = input_elem.get('aria-label', '').strip()
            if aria_label and len(aria_label) >= 2:
                field_type = input_elem.get('type', input_elem.name)
                
                instructions.append({
                    'text': aria_label,
                    'element': 'aria-label',
                    'context': {
                        'field_type': field_type,
                        'field_id': input_elem.get('id')
                    }
                })
        
        return instructions
    
    def _assess_instruction_clarity_with_context(self, instruction_text: str, context: Dict[str, Any]) -> bool:
        """Оцінка зрозумілості інструкції з урахуванням контексту поля"""
        
        field_type = context.get('field_type', 'unknown')
        
        # Спеціальна логіка для email полів
        if field_type == 'email':
            return self._assess_email_instruction(instruction_text)
        
        # Для інших полів використовуємо стандартну логіку
        return self._assess_instruction_clarity(instruction_text)
    
    def _assess_email_instruction(self, text: str) -> bool:
        """Спеціальна оцінка для email полів"""
        
        # Базові перевірки
        if len(text.strip()) < 2:
            return False
        if len(text) > 200:
            return False
        
        # Перевірка чи це email адреса або email-related інструкція
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        # Якщо це валідна email адреса - завжди зрозуміло
        if re.match(email_pattern, text.strip()):
            return True
        
        # Якщо містить @ символ - ймовірно email приклад
        if '@' in text:
            # Перевіряємо чи це схоже на email приклад
            email_examples = [
                'example.com', 'domain.com', 'gmail.com', 'email.com', 
                'yourname', 'username', 'user', 'name', 'john', 'jane'
            ]
            
            text_lower = text.lower()
            for example in email_examples:
                if example in text_lower:
                    return True  # Це email приклад - зрозуміло
        
        # Для звичайних email інструкцій використовуємо стандартну логіку
        return self._assess_instruction_clarity(text)
    
    def _assess_instruction_clarity(self, instruction_text: str) -> bool:
        """Оцінка зрозумілості інструкції з адаптованими критеріями для коротких текстів"""
        
        # Мінімальна довжина для аналізу
        if len(instruction_text.strip()) < 2:
            return False
            
        # Максимальна довжина (занадто довгі інструкції незрозумілі)
        if len(instruction_text) > 200:
            return False
        
        word_count = len(instruction_text.split())
        sentence_count = len(re.split(r'[.!?]+', instruction_text.strip()))
        
        # Базові критерії для всіх інструкцій
        basic_criteria = (
            word_count <= 25 and                           # Не більше 25 слів
            sentence_count <= 3                            # Не більше 3 речень
        )
        
        if not basic_criteria:
            return False
        
        # Для дуже коротких інструкцій (1-3 слова) - завжди зрозумілі якщо не містять складних термінів
        if word_count <= 3:
            return self._is_simple_short_text(instruction_text)
        
        # Для коротких інструкцій (4-8 слів) - м'якші критерії
        if word_count <= 8:
            return self._assess_short_instruction(instruction_text)
        
        # Для довших інструкцій (9+ слів) - використовуємо textstat з адаптованими критеріями
        return self._assess_long_instruction(instruction_text)
    
    def _is_simple_short_text(self, text: str) -> bool:
        """Перевірка простих коротких текстів (1-3 слова)"""
        
        # Список складних/технічних термінів, які роблять короткий текст незрозумілим
        complex_terms = [
            'дескриптивний', 'ідентифікація', 'узагальнений', 'субʼєкт', 'параметр',
            'конфігурація', 'аутентифікація', 'авторизація', 'валідація', 'верифікація',
            'інтеграція', 'імплементація', 'оптимізація', 'синхронізація', 'модифікація'
        ]
        
        text_lower = text.lower()
        
        # Якщо містить складні терміни - незрозумілий
        for term in complex_terms:
            if term in text_lower:
                return False
        
        # Якщо довжина слова більше 12 символів - може бути складним
        words = text.split()
        for word in words:
            if len(word) > 12:
                return False
        
        return True
    
    def _assess_short_instruction(self, text: str) -> bool:
        """Оцінка коротких інструкцій (4-8 слів)"""
        
        # Перевірка на складні терміни
        if not self._is_simple_short_text(text):
            return False
        
        # Додаткові критерії для коротких інструкцій
        words = text.split()
        
        # Перевірка середньої довжини слів
        avg_word_length = sum(len(word) for word in words) / len(words)
        if avg_word_length > 8:  # Середня довжина слова не більше 8 символів
            return False
        
        # Перевірка кількості складних слів (більше 8 символів)
        complex_words = [word for word in words if len(word) > 8]
        if len(complex_words) > 1:  # Не більше 1 складного слова
            return False
        
        return True
    
    def _assess_long_instruction(self, text: str) -> bool:
        """Оцінка довших інструкцій (9+ слів) з використанням textstat"""
        
        try:
            # Для довших текстів використовуємо textstat з м'якшими критеріями
            flesch_score = textstat.flesch_reading_ease(text)
            grade_level = textstat.flesch_kincaid_grade(text)
            ari_score = textstat.automated_readability_index(text)
            
            # М'якші критерії для інструкцій
            readability_criteria = (
                flesch_score >= 30 or       # Значно м'якший критерій (було 60)
                grade_level <= 10 or        # До 10 класу (було 8)
                ari_score <= 10             # ARI до 10 (було 8)
            )
            
            return readability_criteria
            
        except Exception:
            # Якщо textstat не працює - використовуємо базові критерії
            return self._basic_clarity_assessment(text)
    
    def calculate_error_support_metric_enhanced(self, page_data: Dict[str, Any]) -> float:
        """
        Розрахунок метрики підтримки помилок (UAC-1.3.3-G) з покращеним аналізом
        Використовує комбінацію статичного аналізу та динамічного тестування
        
        Формула: X = (static_score * 0.4) + (dynamic_score * 0.6)
        static_score = статичний аналіз HTML структури
        dynamic_score = результати динамічного тестування форм
        """
        
        html_content = page_data.get('html_content', '')
        form_error_test_results = page_data.get('form_error_test_results', [])
        
        print(f"\n🚨 === ДЕТАЛЬНИЙ АНАЛІЗ ПІДТРИМКИ ПОМИЛОК (ГІБРИДНИЙ) ===")
        
        # Витягуємо поля безпосередньо з HTML для більш точного контролю
        if not html_content:
            print("⚠️ HTML контент недоступний")
            return 1.0
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Знаходимо всі форми
        forms = soup.find_all('form')
        if not forms:
            # Якщо немає форм, шукаємо окремі поля
            individual_fields = soup.find_all(['input', 'textarea', 'select'])
            if individual_fields:
                print(f"📋 Знайдено {len(individual_fields)} полів без форм")
                # Обробляємо як одну віртуальну форму
                forms = [soup]  # Вся сторінка як одна форма
            else:
                print("⚠️ Поля для валідації не знайдено - повертаємо 1.0")
                return 1.0
        
        print(f"📋 Знайдено форм: {len(forms)}")
        print(f"🧪 Результати динамічного тестування: {len(form_error_test_results)} форм")
        
        # Статичний аналіз (40% ваги)
        print(f"\n📊 СТАТИЧНИЙ АНАЛІЗ (40% ваги):")
        static_total_quality = 0.0
        
        for i, form in enumerate(forms, 1):
            print(f"\n🔍 Статичний аналіз форми {i}:")
            
            # Аналізуємо якість підтримки помилок для цієї форми
            form_quality = self._analyze_form_error_support_quality(form, html_content)
            static_total_quality += form_quality
            
            print(f"   🎯 Статична якість: {form_quality:.3f}")
        
        static_average = static_total_quality / len(forms)
        print(f"📊 Середня статична якість: {static_average:.3f}")
        
        # Динамічний аналіз (60% ваги)
        print(f"\n🧪 ДИНАМІЧНИЙ АНАЛІЗ (60% ваги):")
        dynamic_average = 0.0
        
        if form_error_test_results:
            dynamic_total_quality = 0.0
            successful_tests = 0
            
            for i, test_result in enumerate(form_error_test_results, 1):
                if 'error' in test_result:
                    print(f"❌ Форма {i}: Помилка тестування - {test_result.get('error', 'Unknown')}")
                    continue
                
                dynamic_quality = test_result.get('quality_score', 0.0)
                dynamic_total_quality += dynamic_quality
                successful_tests += 1
                
                print(f"✅ Форма {i}: Динамічна якість = {dynamic_quality:.3f}")
                
                # Детальний розбір динамічного тестування
                breakdown = test_result.get('detailed_breakdown', {})
                for category, data in breakdown.items():
                    score = data.get('score', 0.0)
                    description = data.get('description', 'Немає опису')
                    print(f"   📋 {category}: {score:.3f} - {description}")
            
            if successful_tests > 0:
                dynamic_average = dynamic_total_quality / successful_tests
                print(f"📊 Середня динамічна якість: {dynamic_average:.3f} (з {successful_tests} успішних тестів)")
            else:
                print("⚠️ Жодного успішного динамічного тесту")
                dynamic_average = 0.0
        else:
            print("⚠️ Динамічне тестування не виконувалося")
            dynamic_average = 0.0
        
        # Комбінований скор
        if dynamic_average > 0:
            # Якщо є результати динамічного тестування, використовуємо гібридний підхід
            combined_score = (static_average * 0.4) + (dynamic_average * 0.6)
            print(f"\n🎯 ГІБРИДНИЙ СКОР:")
            print(f"   Статичний: {static_average:.3f} × 0.4 = {static_average * 0.4:.3f}")
            print(f"   Динамічний: {dynamic_average:.3f} × 0.6 = {dynamic_average * 0.6:.3f}")
            print(f"   Комбінований: {combined_score:.3f}")
        else:
            # Якщо немає динамічного тестування, використовуємо тільки статичний аналіз
            combined_score = static_average
            print(f"\n⚠️ Використовується тільки статичний аналіз: {combined_score:.3f}")
        
        print(f"\n📊 ПІДСУМОК ПІДТРИМКИ ПОМИЛОК:")
        print(f"   Фінальний скор: {combined_score:.3f}")
        print(f"=== КІНЕЦЬ АНАЛІЗУ ПІДТРИМКИ ПОМИЛОК ===\n")
        
        return combined_score
    
    def _analyze_form_error_support_quality(self, form, html_content: str) -> float:
        """Аналіз якості підтримки помилок для однієї форми"""
        
        # Знаходимо всі поля в формі
        fields = form.find_all(['input', 'textarea', 'select'])
        
        if not fields:
            print("   ⚠️ Поля не знайдено")
            return 1.0  # Немає полів = немає проблем
        
        print(f"   📝 Знайдено полів: {len(fields)}")
        
        total_field_quality = 0.0
        validatable_fields = 0
        
        for field in fields:
            # Аналізуємо тільки поля що потребують валідації
            if self._field_needs_validation(field):
                validatable_fields += 1
                field_quality = self._analyze_field_error_support(field, html_content)
                total_field_quality += field_quality
                
                field_name = field.get('name') or field.get('id') or f"{field.name}[{field.get('type', 'unknown')}]"
                print(f"     • {field_name}: {field_quality:.3f}")
        
        if validatable_fields == 0:
            print("   ⚠️ Поля що потребують валідації не знайдено")
            return 1.0  # Немає полів для валідації = немає проблем
        
        form_quality = total_field_quality / validatable_fields
        print(f"   📊 Середня якість полів: {form_quality:.3f}")
        
        return form_quality
    
    def _field_needs_validation(self, field) -> bool:
        """Перевіряє чи поле потребує валідації"""
        
        # Типи полів що потребують валідації
        validation_types = ['text', 'email', 'password', 'tel', 'url', 'number', 'date', 'datetime-local']
        
        field_type = field.get('type', 'text')
        
        # textarea завжди потребує валідації
        if field.name == 'textarea':
            return True
        
        # input поля певних типів
        if field.name == 'input' and field_type in validation_types:
            return True
        
        # Поля з required або pattern завжди потребують валідації
        if field.get('required') is not None or field.get('pattern'):
            return True
        
        return False
    
    def _analyze_field_error_support(self, field, html_content: str) -> float:
        """Детальний аналіз підтримки помилок для одного поля (Фази 1-3)"""
        
        quality_score = 0.0
        
        # ФАЗА 1: Базові покращення (0.4 максимум)
        quality_score += self._phase1_basic_error_support(field, html_content)
        
        # ФАЗА 2: Якість повідомлень (0.3 максимум)  
        quality_score += self._phase2_message_quality(field, html_content)
        
        # ФАЗА 3: Динамічна валідація (0.3 максимум)
        quality_score += self._phase3_dynamic_validation(field, html_content)
        
        return min(quality_score, 1.0)  # Максимум 1.0
    
    def _phase1_basic_error_support(self, field, html_content: str) -> float:
        """Фаза 1: Базові покращення - aria-invalid, aria-describedby, role=alert"""
        
        score = 0.0
        
        # 1. Валідація (required/pattern) - 0.1
        if field.get('required') is not None or field.get('pattern'):
            score += 0.1
        
        # 2. aria-invalid - 0.1
        if field.get('aria-invalid'):
            score += 0.1
        
        # 3. aria-describedby зв'язок - 0.1
        if aria_describedby := field.get('aria-describedby'):
            if self._check_aria_describedby_exists(aria_describedby, html_content):
                score += 0.1
        
        # 4. role="alert" елементи - 0.1
        if self._check_alert_elements_exist(html_content):
            score += 0.1
        
        return score
    
    def _phase2_message_quality(self, field, html_content: str) -> float:
        """Фаза 2: Якість повідомлень про помилки"""
        
        score = 0.0
        
        # Знаходимо пов'язані повідомлення про помилки
        error_messages = self._find_error_messages_for_field(field, html_content)
        
        if not error_messages:
            return 0.0
        
        # Оцінюємо якість кожного повідомлення
        total_message_quality = 0.0
        for message in error_messages:
            message_quality = self._assess_error_message_quality(message)
            total_message_quality += message_quality
        
        # Середня якість повідомлень (максимум 0.3)
        average_quality = total_message_quality / len(error_messages)
        score = average_quality * 0.3
        
        return score
    
    def _phase3_dynamic_validation(self, field, html_content: str) -> float:
        """Фаза 3: Динамічна валідація та live regions"""
        
        score = 0.0
        
        # 1. Live regions (aria-live, role="status") - 0.15
        if self._check_live_regions_exist(html_content):
            score += 0.15
        
        # 2. JavaScript валідація (евристика) - 0.15
        if self._detect_javascript_validation(field, html_content):
            score += 0.15
        
        return score
    
    def _check_aria_describedby_exists(self, aria_describedby: str, html_content: str) -> bool:
        """Перевіряє чи існує елемент з відповідним ID"""
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # aria-describedby може містити кілька ID через пробіл
        ids = aria_describedby.split()
        
        for element_id in ids:
            if soup.find(id=element_id):
                return True
        
        return False
    
    def _check_alert_elements_exist(self, html_content: str) -> bool:
        """Перевіряє наявність role="alert" елементів"""
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        alerts = soup.find_all(attrs={'role': 'alert'})
        return len(alerts) > 0
    
    def _find_error_messages_for_field(self, field, html_content: str) -> list:
        """Знаходить повідомлення про помилки для поля"""
        
        messages = []
        
        # 1. aria-describedby зв'язки
        if aria_describedby := field.get('aria-describedby'):
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')
            
            ids = aria_describedby.split()
            for element_id in ids:
                element = soup.find(id=element_id)
                if element:
                    text = element.get_text().strip()
                    if text:
                        messages.append(text)
        
        # 2. Пошук поблизу поля (евристика)
        # Можна додати пошук елементів з класами error, invalid тощо
        
        return messages
    
    def _assess_error_message_quality(self, message_text: str) -> float:
        """Оцінка якості повідомлення про помилку (0.0-1.0)"""
        
        if not message_text or len(message_text.strip()) < 3:
            return 0.0
        
        quality_score = 0.0
        
        # 1. Довжина (не занадто коротке/довге) - 0.3
        if 10 <= len(message_text) <= 100:
            quality_score += 0.3
        elif 5 <= len(message_text) <= 150:
            quality_score += 0.15
        
        # 2. Конструктивність (не тільки "Помилка!") - 0.4
        constructive_words = ['введіть', 'виберіть', 'перевірте', 'має містити', 'формат', 'please', 'enter', 'select', 'check']
        if any(word in message_text.lower() for word in constructive_words):
            quality_score += 0.4
        
        # 3. Специфічність (конкретна проблема) - 0.3
        specific_words = ['email', 'пароль', 'телефон', 'дата', 'символів', 'цифр', 'password', 'phone', 'date']
        if any(word in message_text.lower() for word in specific_words):
            quality_score += 0.3
        
        return min(quality_score, 1.0)
    
    def _check_live_regions_exist(self, html_content: str) -> bool:
        """Перевіряє наявність live regions"""
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # aria-live
        live_elements = soup.find_all(attrs={'aria-live': True})
        if live_elements:
            return True
        
        # role="status"
        status_elements = soup.find_all(attrs={'role': 'status'})
        if status_elements:
            return True
        
        return False
    
    def _detect_javascript_validation(self, field, html_content: str) -> bool:
        """Евристичне виявлення JavaScript валідації"""
        
        # Пошук скриптів що можуть містити валідацію
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        scripts = soup.find_all('script')
        validation_keywords = ['validate', 'validation', 'error', 'invalid', 'required']
        
        for script in scripts:
            script_text = script.get_text().lower()
            if any(keyword in script_text for keyword in validation_keywords):
                return True
        
        # Перевірка event handlers
        field_id = field.get('id')
        field_name = field.get('name')
        
        if field_id or field_name:
            # Пошук в скриптах посилань на це поле
            for script in scripts:
                script_text = script.get_text()
                if field_id and field_id in script_text:
                    return True
                if field_name and field_name in script_text:
                    return True
        
        return False
    
    def _basic_clarity_assessment(self, instruction_text: str) -> bool:
        """Базова оцінка зрозумілості як fallback"""
        
        word_count = len(instruction_text.split())
        sentence_count = len(re.split(r'[.!?]+', instruction_text.strip()))
        
        return (
            5 <= len(instruction_text) <= 150 and
            word_count <= 20 and
            sentence_count <= 2
        )
    
    
    def calculate_input_assistance_metric(self, page_data: Dict[str, Any]) -> float:
        """
        Розрахунок метрики допомоги при введенні (UAC-1.3.2-G)
        
        Формула: X = A / B
        A = кількість полів із функціями автозаповнення чи підказок
        B = загальна кількість полів (тільки звичайні input поля)
        """
        
        # Витягуємо поля безпосередньо з HTML для більш точного контролю
        html_content = page_data.get('html_content', '')
        if not html_content:
            return 1.0
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Типи input полів, які потребують допомоги при введенні
        text_input_types = [
            'text', 'email', 'password', 'tel', 'url', 'search', 
            'number', 'date', 'datetime-local', 'month', 'week', 'time'
        ]
        
        total_fields = 0
        assisted_fields = 0
        
        # Шукаємо тільки звичайні input поля та textarea
        input_elements = soup.find_all(['input', 'textarea'])
        
        for element in input_elements:
            # Для input перевіряємо тип
            if element.name == 'input':
                input_type = element.get('type', 'text').lower()
                # Пропускаємо checkbox, radio, submit, button тощо
                if input_type not in text_input_types:
                    continue
            
            # Для textarea завжди враховуємо
            total_fields += 1
            
            # Перевірка наявності допомоги
            has_assistance = (
                element.get('autocomplete') or
                element.get('placeholder') or
                element.get('aria-describedby') or
                element.get('aria-label') or
                element.get('title')
            )
            
            if has_assistance:
                assisted_fields += 1
        
        return assisted_fields / total_fields if total_fields > 0 else 1.0
    
    def calculate_error_support_metric(self, page_data: Dict[str, Any]) -> float:
        """
        Розрахунок метрики підтримки помилок (UAC-1.3.3-G)
        
        Формула: X = A / B
        A = кількість форм із повідомленнями про помилки
        B = загальна кількість форм
        """
        
        form_elements = page_data.get('form_elements', [])
        html_content = page_data.get('html_content', '')
        
        if not form_elements:
            return 1.0  # Немає форм = немає проблем
        
        forms_with_error_support = 0
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        for i, form_data in enumerate(form_elements):
            has_error_support = False
            
            # Пошук форми в DOM
            forms = soup.find_all('form')
            if i < len(forms):
                form = forms[i]
                
                # Перевірка наявності error handling
                error_indicators = [
                    form.find(class_=re.compile(r'error|invalid|warning')),
                    form.find('[aria-invalid]'),
                    form.find('[role="alert"]'),
                    form.select('[aria-describedby*="error"]'),
                    not form_data.get('novalidate', False)  # HTML5 валідація
                ]
                
                if any(error_indicators):
                    has_error_support = True
            
            if has_error_support:
                forms_with_error_support += 1
        
        # Використовуємо покращений метод
        return self.calculate_error_support_metric_enhanced(page_data)