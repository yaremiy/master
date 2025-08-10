"""
Метрики локалізації (UAC-2.1-S)
"""

from bs4 import BeautifulSoup
from typing import Dict, Any, Set
import re


class LocalizationMetrics:
    """Клас для розрахунку метрик локалізації"""
    
    def __init__(self):
        # Вагові коефіцієнти для українського контексту
        self.weights = {
            'uk': 0.6,   # Українська мова
            'en': 0.2,   # Англійська мова
            'de': 0.08,  # Німецька мова
            'fr': 0.08,  # Французька мова
            'other': 0.04  # Інші мови
        }
    
    async def calculate_metrics(self, page_data: Dict[str, Any]) -> Dict[str, float]:
        """Розрахунок метрик локалізації"""
        
        return {
            'localization': self.calculate_localization_metric(page_data)
        }
    
    def calculate_localization_metric(self, page_data: Dict[str, Any]) -> float:
        """
        Розрахунок метрики локалізації (UAC-2.1-S)
        
        Формула: X = K1×A + K2×B + K3×C + K4×D
        
        Де для українського контексту:
        K1 = 0.6 (українська мова)
        K2 = 0.2 (англійська мова)
        K3 = 0.08 (німецька/французька)
        K4 = 0.04 (інші мови)
        """
        
        html_content = page_data.get('html_content', '')
        url = page_data.get('url', '')
        
        available_languages = self._detect_available_languages(html_content, url)
        
        score = 0
        
        # Перевіряємо наявність кожної мови
        if 'uk' in available_languages:
            score += self.weights['uk']
        
        if 'en' in available_languages:
            score += self.weights['en']
        
        # Європейські мови (німецька або французька)
        if any(lang in available_languages for lang in ['de', 'fr']):
            score += self.weights['de']
        
        # Інші мови
        other_languages = available_languages - {'uk', 'en', 'de', 'fr'}
        if other_languages:
            score += self.weights['other']
        
        return min(score, 1.0)  # Максимум 1.0
    
    def _detect_available_languages(self, html_content: str, url: str) -> Set[str]:
        """Визначення доступних мов на сайті"""
        
        soup = BeautifulSoup(html_content, 'html.parser')
        languages = set()
        
        # 1. Перевіряємо lang атрибут HTML
        html_tag = soup.find('html')
        if html_tag and html_tag.get('lang'):
            lang = html_tag.get('lang')[:2].lower()
            languages.add(lang)
        
        # 2. Шукаємо language switcher в навігації
        lang_patterns = [
            r'/(uk|en|de|fr|ru|pl)/',
            r'[?&]lang=(uk|en|de|fr|ru|pl)',
            r'[?&]language=(uk|en|de|fr|ru|pl)',
            r'/lang/(uk|en|de|fr|ru|pl)'
        ]
        
        # Перевіряємо посилання
        links = soup.find_all('a', href=True)
        for link in links:
            href = link.get('href', '')
            for pattern in lang_patterns:
                matches = re.findall(pattern, href)
                for match in matches:
                    languages.add(match.lower())
        
        # 3. Перевіряємо hreflang атрибути
        hreflang_links = soup.find_all('link', rel='alternate', hreflang=True)
        for link in hreflang_links:
            lang = link.get('hreflang')[:2].lower()
            if lang != 'x-':  # Виключаємо x-default
                languages.add(lang)
        
        # 4. Шукаємо language selector елементи
        lang_selectors = [
            '.language-selector',
            '.lang-switcher',
            '.language-menu',
            '[class*="lang"]',
            '[id*="lang"]'
        ]
        
        for selector in lang_selectors:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text().lower()
                
                # Пошук назв мов
                lang_names = {
                    'uk': ['українська', 'укр', 'ua', 'ukraine'],
                    'en': ['english', 'англійська', 'eng'],
                    'de': ['deutsch', 'german', 'німецька'],
                    'fr': ['français', 'french', 'французька'],
                    'ru': ['русский', 'russian', 'російська'],
                    'pl': ['polski', 'polish', 'польська']
                }
                
                for lang_code, names in lang_names.items():
                    if any(name in text for name in names):
                        languages.add(lang_code)
        
        # 5. Перевіряємо URL структуру
        for pattern in lang_patterns:
            matches = re.findall(pattern, url)
            for match in matches:
                languages.add(match.lower())
        
        # 6. Аналіз контенту для визначення мови
        main_content = soup.get_text()
        detected_lang = self._detect_content_language(main_content)
        if detected_lang:
            languages.add(detected_lang)
        
        return languages
    
    def _detect_content_language(self, text: str) -> str:
        """Простий детектор мови контенту"""
        
        # Характерні слова для різних мов
        language_indicators = {
            'uk': ['про', 'для', 'або', 'який', 'яка', 'яке', 'університет', 'освіта'],
            'en': ['about', 'for', 'or', 'which', 'university', 'education', 'the', 'and'],
            'ru': ['про', 'для', 'или', 'который', 'которая', 'которое', 'университет'],
            'de': ['über', 'für', 'oder', 'welche', 'universität', 'bildung', 'der', 'die'],
            'fr': ['sur', 'pour', 'ou', 'qui', 'université', 'éducation', 'le', 'la']
        }
        
        text_lower = text.lower()
        word_counts = {}
        
        for lang, words in language_indicators.items():
            count = sum(1 for word in words if word in text_lower)
            if count > 0:
                word_counts[lang] = count
        
        if word_counts:
            # Повертаємо мову з найбільшою кількістю збігів
            return max(word_counts, key=word_counts.get)
        
        return None