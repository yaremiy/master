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
        
        return forms_with_error_support / len(form_elements)