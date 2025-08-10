"""
Головний клас для оцінки доступності вебсайтів
"""

from playwright.async_api import async_playwright
from typing import Dict, Any, List
import asyncio

from .metrics.perceptibility import PerceptibilityMetrics
from .metrics.operability import OperabilityMetrics  
from .metrics.understandability import UnderstandabilityMetrics
from .metrics.localization import LocalizationMetrics
from .utils.web_scraper import WebScraper
from .utils.calculator import ScoreCalculator


class AccessibilityEvaluator:
    """Головний клас для оцінки доступності вебсайтів"""
    
    def __init__(self):
        self.weights = {
            'perceptibility': 0.3,
            'operability': 0.3, 
            'understandability': 0.4,
            'localization': 0.4
        }
        
        self.metric_weights = {
            'alt_text': 0.15,
            'contrast': 0.15,
            'media_accessibility': 0.15,
            'keyboard_navigation': 0.05,
            'structured_navigation': 0.05,
            'instruction_clarity': 0.1,
            'input_assistance': 0.1,
            'error_support': 0.1,
            'localization': 0.15
        }
        
        # Ініціалізація аналізаторів метрик
        self.perceptibility = PerceptibilityMetrics()
        self.operability = OperabilityMetrics()
        self.understandability = UnderstandabilityMetrics()
        self.localization = LocalizationMetrics()
        
        self.web_scraper = WebScraper()
        self.calculator = ScoreCalculator(self.weights, self.metric_weights)
    
    async def evaluate_accessibility(self, url: str) -> Dict[str, Any]:
        """
        Головна функція для оцінки доступності вебсайту
        
        Args:
            url: URL вебсайту для аналізу
            
        Returns:
            Словник з результатами аналізу
        """
        try:
            # Отримання даних з вебсайту
            page_data = await self.web_scraper.scrape_page(url)
            
            # Розрахунок всіх метрик
            metrics = await self.calculate_all_metrics(page_data)
            
            # Розрахунок підскорів
            subscores = self.calculator.calculate_subscores(metrics)
            
            # Фінальний скор
            final_score = self.calculator.calculate_final_score(subscores)
            
            # Генерація рекомендацій
            recommendations = self.generate_recommendations(metrics)
            
            return {
                'url': url,
                'metrics': metrics,
                'subscores': subscores,
                'final_score': final_score,
                'recommendations': recommendations,
                'status': 'success'
            }
            
        except Exception as e:
            return {
                'url': url,
                'error': str(e),
                'status': 'error'
            }
    
    async def calculate_all_metrics(self, page_data: Dict[str, Any]) -> Dict[str, float]:
        """Розрахунок всіх метрик доступності"""
        
        metrics = {}
        
        # Перцептивність
        metrics.update(await self.perceptibility.calculate_metrics(page_data))
        
        # Керованість
        metrics.update(await self.operability.calculate_metrics(page_data))
        
        # Зрозумілість
        metrics.update(await self.understandability.calculate_metrics(page_data))
        
        # Локалізація
        metrics.update(await self.localization.calculate_metrics(page_data))
        
        return metrics
    
    def generate_recommendations(self, metrics: Dict[str, float]) -> List[Dict[str, str]]:
        """Генерація рекомендацій на основі результатів метрик"""
        
        recommendations = []
        
        # Рекомендації для альтернативного тексту
        if metrics.get('alt_text', 0) < 0.8:
            recommendations.append({
                'category': 'Перцептивність',
                'issue': 'Недостатньо альтернативного тексту',
                'recommendation': 'Додайте змістовні alt атрибути до всіх зображень',
                'priority': 'Високий',
                'wcag_reference': 'WCAG 1.1.1'
            })
        
        # Рекомендації для контрасту
        if metrics.get('contrast', 0) < 0.7:
            recommendations.append({
                'category': 'Перцептивність',
                'issue': 'Низький контраст тексту',
                'recommendation': 'Підвищте контраст до мінімум 4.5:1 для основного тексту',
                'priority': 'Високий',
                'wcag_reference': 'WCAG 1.4.3'
            })
        
        # Рекомендації для клавіатурної навігації
        if metrics.get('keyboard_navigation', 0) < 0.9:
            recommendations.append({
                'category': 'Керованість',
                'issue': 'Проблеми з клавіатурною навігацією',
                'recommendation': 'Забезпечте доступність всіх інтерактивних елементів через клавіатуру',
                'priority': 'Високий',
                'wcag_reference': 'WCAG 2.1.1'
            })
        
        # Рекомендації для зрозумілості
        if metrics.get('instruction_clarity', 0) < 0.7:
            recommendations.append({
                'category': 'Зрозумілість',
                'issue': 'Складні або незрозумілі інструкції',
                'recommendation': 'Спростіть мову інструкцій та зробіть їх більш зрозумілими',
                'priority': 'Середній',
                'wcag_reference': 'WCAG 3.1.5'
            })
        
        # Рекомендації для локалізації
        if metrics.get('localization', 0) < 0.6:
            recommendations.append({
                'category': 'Локалізація',
                'issue': 'Недостатня підтримка мов',
                'recommendation': 'Додайте підтримку української та англійської мов',
                'priority': 'Середній',
                'wcag_reference': 'WCAG 3.1.2'
            })
        
        return recommendations