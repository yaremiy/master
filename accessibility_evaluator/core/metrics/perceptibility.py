"""
Метрики перцептивності (UAC-1.1-G)
"""

from bs4 import BeautifulSoup
from typing import Dict, Any, List
import re


class PerceptibilityMetrics:
    """Клас для розрахунку метрик перцептивності"""
    
    async def calculate_metrics(self, page_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Розрахунок всіх метрик перцептивності
        
        Args:
            page_data: Дані сторінки від WebScraper
            
        Returns:
            Словник з метриками перцептивності
        """
        
        return {
            'alt_text': self.calculate_alt_text_metric(page_data),
            'contrast': await self.calculate_contrast_metric(page_data),
            'media_accessibility': self.calculate_media_accessibility_metric(page_data)
        }
    
    def calculate_alt_text_metric(self, page_data: Dict[str, Any]) -> float:
        """
        Розрахунок метрики альтернативного тексту (UAC-1.1.1-G)
        
        Формула: X = A / B
        A = кількість мультимедійних елементів зі змістовними текстовими альтернативами
        B = загальна кількість мультимедійних елементів
        """
        
        media_elements = page_data.get('media_elements', [])
        
        if not media_elements:
            return 1.0  # Немає медіа = немає проблем
        
        meaningful_alt_count = 0
        
        for element in media_elements:
            if element['type'] == 'image':
                if self._has_meaningful_alt_text(element):
                    meaningful_alt_count += 1
            elif element['type'] in ['video', 'audio']:
                # Для відео/аудіо перевіряємо наявність описів
                if element.get('aria_label') or element.get('title'):
                    meaningful_alt_count += 1
        
        return meaningful_alt_count / len(media_elements)
    
    def _has_meaningful_alt_text(self, image_element: Dict[str, Any]) -> bool:
        """Перевірка чи має зображення змістовний альтернативний текст"""
        
        alt_text = image_element.get('alt', '')
        
        # Декоративні зображення
        if image_element.get('is_decorative'):
            return True  # Декоративні зображення повинні мати порожній alt
        
        # Перевірка наявності та якості alt тексту
        if not alt_text:
            return False
        
        # Фільтруємо неякісні alt тексти
        bad_alt_patterns = [
            r'^image\d*$',
            r'^img\d*$',
            r'^picture\d*$',
            r'^photo\d*$',
            r'^\w+\.(jpg|jpeg|png|gif|svg)$',
            r'^untitled$',
            r'^placeholder$'
        ]
        
        alt_lower = alt_text.lower().strip()
        
        for pattern in bad_alt_patterns:
            if re.match(pattern, alt_lower):
                return False
        
        # Alt текст повинен бути достатньо описовим
        return len(alt_text.strip()) >= 3
    
    async def calculate_contrast_metric(self, page_data: Dict[str, Any]) -> float:
        """
        Розрахунок метрики контрастності тексту (UAC-1.1.2-G)
        
        Формула: X = Σ(A × B+) / Σ(A × B)
        A = рівень контрасту
        B+ = кількість елементів, що задовольняють умови
        B = кількість всіх елементів
        """
        
        text_elements = page_data.get('text_elements', [])
        
        if not text_elements:
            return 1.0
        
        total_weighted_score = 0
        total_elements = 0
        
        for element in text_elements:
            if not element.get('is_visible', True):
                continue
                
            styles = element.get('styles', {})
            
            # Отримання кольорів
            text_color = self._parse_color(styles.get('color', 'rgb(0,0,0)'))
            bg_color = self._parse_color(styles.get('backgroundColor', 'rgb(255,255,255)'))
            
            # Розрахунок контрасту
            contrast_ratio = self._calculate_contrast_ratio(text_color, bg_color)
            
            # Визначення вимог до контрасту
            font_size = self._parse_font_size(styles.get('fontSize', '16px'))
            font_weight = styles.get('fontWeight', 'normal')
            
            required_ratio = self._get_required_contrast_ratio(font_size, font_weight)
            
            # Перевірка відповідності
            meets_requirement = 1 if contrast_ratio >= required_ratio else 0
            
            total_weighted_score += contrast_ratio * meets_requirement
            total_elements += contrast_ratio
        
        return total_weighted_score / total_elements if total_elements > 0 else 0
    
    def _parse_color(self, color_string: str) -> tuple:
        """Парсинг CSS кольору в RGB"""
        
        # Простий парсер для rgb() та rgba()
        if 'rgb' in color_string:
            numbers = re.findall(r'\d+', color_string)
            if len(numbers) >= 3:
                return (int(numbers[0]), int(numbers[1]), int(numbers[2]))
        
        # За замовчуванням
        return (0, 0, 0) if 'rgb(0' in color_string else (255, 255, 255)
    
    def _calculate_contrast_ratio(self, color1: tuple, color2: tuple) -> float:
        """Розрахунок контрасту згідно з WCAG"""
        
        def get_relative_luminance(rgb):
            """Розрахунок відносної яскравості"""
            r, g, b = [x / 255.0 for x in rgb]
            
            def gamma_correct(c):
                return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
            
            r = gamma_correct(r)
            g = gamma_correct(g)
            b = gamma_correct(b)
            
            return 0.2126 * r + 0.7152 * g + 0.0722 * b
        
        lum1 = get_relative_luminance(color1)
        lum2 = get_relative_luminance(color2)
        
        lighter = max(lum1, lum2)
        darker = min(lum1, lum2)
        
        return (lighter + 0.05) / (darker + 0.05)
    
    def _parse_font_size(self, font_size_string: str) -> float:
        """Парсинг розміру шрифту"""
        
        numbers = re.findall(r'\d+', font_size_string)
        return float(numbers[0]) if numbers else 16.0
    
    def _get_required_contrast_ratio(self, font_size: float, font_weight: str) -> float:
        """Визначення необхідного рівня контрасту"""
        
        # Великий текст (18pt+ або 14pt+ bold)
        is_large = font_size >= 18 or (font_size >= 14 and font_weight in ['bold', '600', '700', '800', '900'])
        
        return 3.0 if is_large else 4.5
    
    def calculate_media_accessibility_metric(self, page_data: Dict[str, Any]) -> float:
        """
        Розрахунок метрики доступності медіа (UAC-1.1.3-G)
        
        Формула: X = A / B
        A = кількість відео із субтитрами або аудіоописами
        B = загальна кількість відео
        """
        
        media_elements = page_data.get('media_elements', [])
        video_elements = [elem for elem in media_elements if elem['type'] == 'video']
        
        if not video_elements:
            return 1.0  # Немає відео = немає проблем
        
        accessible_videos = 0
        
        for video in video_elements:
            has_accessibility = False
            
            # Перевірка субтитрів
            tracks = video.get('tracks', [])
            for track in tracks:
                if track.get('kind') in ['subtitles', 'captions']:
                    has_accessibility = True
                    break
            
            # Перевірка аудіоописів
            if not has_accessibility:
                for track in tracks:
                    if track.get('kind') == 'descriptions':
                        has_accessibility = True
                        break
            
            if has_accessibility:
                accessible_videos += 1
        
        return accessible_videos / len(video_elements)