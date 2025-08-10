"""
Метрики зрозумілості (UAC-1.3-G)
"""

from bs4 import BeautifulSoup
from typing import Dict, Any, List
import re


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
        """Оцінка зрозумілості інструкції"""
        
        # Базові критерії зрозумілості
        word_count = len(instruction_text.split())
        sentence_count = len(re.split(r'[.!?]+', instruction_text))
        
        # Критерії зрозумілості
        is_clear = (
            word_count <= 20 and      # Не занадто довгий
            sentence_count <= 2 and   # Не більше 2 речень
            len(instruction_text) >= 5 and  # Не занадто короткий
            not self._contains_jargon(instruction_text)  # Без жаргону
        )
        
        return is_clear
    
    def _contains_jargon(self, text: str) -> bool:
        """Перевірка на наявність технічного жаргону"""
        
        jargon_words = [
            'api', 'json', 'xml', 'sql', 'regex', 'ajax',
            'backend', 'frontend', 'middleware', 'endpoint'
        ]
        
        text_lower = text.lower()
        return any(word in text_lower for word in jargon_words)
    
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