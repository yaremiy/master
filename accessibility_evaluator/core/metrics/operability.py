"""
Метрики керованості (UAC-1.2-G)
"""

from bs4 import BeautifulSoup
from typing import Dict, Any, List
import re


class OperabilityMetrics:
    """Клас для розрахунку метрик керованості"""
    
    async def calculate_metrics(self, page_data: Dict[str, Any]) -> Dict[str, float]:
        """Розрахунок всіх метрик керованості"""
        
        return {
            'keyboard_navigation': await self.calculate_keyboard_navigation_metric(page_data),
            'structured_navigation': self.calculate_structured_navigation_metric(page_data)
        }
    
    async def calculate_keyboard_navigation_metric(self, page_data: Dict[str, Any]) -> float:
        """
        Розрахунок метрики навігації з клавіатури (UAC-1.2.1-G)
        
        Формула: X = A / B
        A = кількість інтерактивних елементів, доступних для керування клавіатурою
        B = загальна кількість інтерактивних елементів
        """
        
        interactive_elements = page_data.get('interactive_elements', [])
        
        if not interactive_elements:
            return 1.0
        
        accessible_count = 0
        
        for element in interactive_elements:
            if self._is_keyboard_accessible(element):
                accessible_count += 1
        
        return accessible_count / len(interactive_elements)
    
    def _is_keyboard_accessible(self, element: Dict[str, Any]) -> bool:
        """Перевірка доступності елемента з клавіатури"""
        
        # Нативно доступні елементи
        native_accessible = ['button', 'a', 'input', 'select', 'textarea']
        
        if element.get('tag') in native_accessible:
            # Перевірка чи не заблокований tabindex
            tabindex = element.get('tabindex')
            if tabindex == '-1':
                return False
            return True
        
        # Кастомні елементи з правильними ARIA ролями
        role = element.get('role')
        if role in ['button', 'link', 'menuitem', 'tab']:
            tabindex = element.get('tabindex')
            return tabindex is not None and tabindex != '-1'
        
        # Елементи з tabindex
        tabindex = element.get('tabindex')
        if tabindex is not None and tabindex != '-1':
            return True
        
        return False
    
    def calculate_structured_navigation_metric(self, page_data: Dict[str, Any]) -> float:
        """
        Розрахунок метрики структурованої навігації (UAC-1.2.2-G)
        
        Формули:
        - Для глибоких рівнів: X = 0.5 × A + 0.5 × (1 - B/C)
        - Для кореневих рівнів: X = 1 - B/C
        
        A = наявність хлібних крихт (1 або 0)
        B = кількість пропущених рівнів заголовків
        C = загальна кількість заголовків
        """
        
        html_content = page_data.get('html_content', '')
        page_depth = page_data.get('page_depth', 0)
        
        # Аналіз хлібних крихт
        has_breadcrumb = self._has_breadcrumbs(html_content)
        
        # Аналіз ієрархії заголовків
        skipped_levels, total_headings = self._analyze_heading_structure(html_content)
        
        if total_headings == 0:
            return 0.5  # Немає заголовків - середня оцінка
        
        heading_score = max(0, 1 - (skipped_levels / total_headings))
        
        # Вибір формули залежно від глибини сторінки
        if page_depth > 2:  # Глибокий рівень
            return 0.5 * (1 if has_breadcrumb else 0) + 0.5 * heading_score
        else:  # Кореневий рівень
            return heading_score
    
    def _has_breadcrumbs(self, html_content: str) -> bool:
        """Перевірка наявності хлібних крихт"""
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Типові селектори для breadcrumbs
        breadcrumb_selectors = [
            '[aria-label*="breadcrumb" i]',
            '[aria-label*="хлібні" i]',
            '.breadcrumb',
            '.breadcrumbs',
            '.breadcrumb-nav',
            'nav ol',
            'nav ul',
            '[role="navigation"] ol',
            '[role="navigation"] ul'
        ]
        
        for selector in breadcrumb_selectors:
            elements = soup.select(selector)
            for element in elements:
                # Перевірка чи містить типові слова breadcrumb
                text = element.get_text().lower()
                if any(word in text for word in ['home', 'головна', '>', '/', '→', '»']):
                    # Перевірка чи має достатньо елементів для breadcrumb
                    links = element.find_all(['a', 'span'])
                    if len(links) >= 2:
                        return True
        
        return False
    
    def _analyze_heading_structure(self, html_content: str) -> tuple:
        """Аналіз структури заголовків"""
        
        soup = BeautifulSoup(html_content, 'html.parser')
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        
        if not headings:
            return 0, 0
        
        heading_levels = []
        for heading in headings:
            level = int(heading.name[1])
            heading_levels.append(level)
        
        # Підрахунок пропущених рівнів
        skipped_levels = 0
        
        for i in range(1, len(heading_levels)):
            current_level = heading_levels[i]
            previous_level = heading_levels[i-1]
            
            # Якщо перескочили рівень (наприклад, з h2 одразу на h4)
            if current_level > previous_level + 1:
                skipped_levels += current_level - previous_level - 1
        
        return skipped_levels, len(headings)