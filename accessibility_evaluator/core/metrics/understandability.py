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
        instructions = self._extract_instructions(html_content)
        
        if not instructions:
            return 1.0  # Немає інструкцій = немає проблем
        
        clear_instructions = 0
        
        for instruction in instructions:
            if self._assess_instruction_clarity(instruction):
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
    
    def _assess_instruction_clarity(self, instruction_text: str) -> bool:
        """Оцінка зрозумілості інструкції з використанням textstat"""
        
        # Мінімальна довжина для аналізу
        if len(instruction_text.strip()) < 5:
            return False
            
        # Максимальна довжина (занадто довгі інструкції незрозумілі)
        if len(instruction_text) > 200:
            return False
        
        try:
            # Flesch Reading Ease Score (0-100, чим вище - тим легше читати)
            # 90-100: Дуже легко, 80-89: Легко, 70-79: Досить легко
            # 60-69: Стандартно, 50-59: Досить важко, 30-49: Важко, 0-29: Дуже важко
            flesch_score = textstat.flesch_reading_ease(instruction_text)
            
            # Flesch-Kincaid Grade Level (рівень освіти для розуміння)
            # Чим менше число - тим простіше текст
            grade_level = textstat.flesch_kincaid_grade(instruction_text)
            
            # Automated Readability Index
            ari_score = textstat.automated_readability_index(instruction_text)
            
            # Критерії для зрозумілих інструкцій:
            readability_criteria = (
                flesch_score >= 60 and      # Стандартний рівень читабельності або вище
                grade_level <= 8 and        # Не вище 8 класу освіти
                ari_score <= 8              # ARI не вище 8 класу
            )
            
            # Додаткові критерії
            word_count = len(instruction_text.split())
            sentence_count = len(re.split(r'[.!?]+', instruction_text.strip()))
            
            basic_criteria = (
                word_count <= 25 and                           # Не більше 25 слів
                sentence_count <= 3                            # Не більше 3 речень
            )
            
            return readability_criteria and basic_criteria
            
        except Exception:
            # Якщо textstat не може проаналізувати текст, використовуємо базові критерії
            return self._basic_clarity_assessment(instruction_text)
    
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
        B = загальна кількість полів
        """
        
        form_elements = page_data.get('form_elements', [])
        
        total_fields = 0
        assisted_fields = 0
        
        for form in form_elements:
            fields = form.get('fields', [])
            
            for field in fields:
                total_fields += 1
                
                # Перевірка наявності допомоги
                has_assistance = (
                    field.get('autocomplete') or
                    field.get('placeholder') or
                    field.get('aria_describedby') or
                    field.get('aria_label') or
                    field.get('title')
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