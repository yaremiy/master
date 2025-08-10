"""
Калькулятор для розрахунку скорів доступності
"""

from typing import Dict, Any


class ScoreCalculator:
    """Клас для розрахунку скорів доступності згідно з формулами з наукової статті"""
    
    def __init__(self, weights: Dict[str, float], metric_weights: Dict[str, float]):
        self.weights = weights
        self.metric_weights = metric_weights
    
    def calculate_subscores(self, metrics: Dict[str, float]) -> Dict[str, float]:
        """
        Розрахунок підскорів для кожної підвластивості
        
        Args:
            metrics: Словник з розрахованими метриками
            
        Returns:
            Словник з підскорами
        """
        
        # Перцептивність (UAC-1.1-G)
        perceptibility = (
            metrics.get('alt_text', 0) * 0.5 +
            metrics.get('contrast', 0) * 0.5 +
            metrics.get('media_accessibility', 0) * 0.4
        ) / 1.4
        
        # Керованість (UAC-1.2-G)
        operability = (
            metrics.get('keyboard_navigation', 0) * 0.6 +
            metrics.get('structured_navigation', 0) * 0.4
        )
        
        # Зрозумілість (UAC-1.3-G)
        understandability = (
            metrics.get('instruction_clarity', 0) * 0.4 +
            metrics.get('input_assistance', 0) * 0.3 +
            metrics.get('error_support', 0) * 0.3
        )
        
        # Локалізація (UAC-2.1-S)
        localization = metrics.get('localization', 0)
        
        return {
            'perceptibility': max(0, min(1, perceptibility)),
            'operability': max(0, min(1, operability)),
            'understandability': max(0, min(1, understandability)),
            'localization': max(0, min(1, localization))
        }
    
    def calculate_final_score(self, subscores: Dict[str, float]) -> float:
        """
        Розрахунок фінального скору згідно з формулою з наукової статті
        
        Формула: 0.6 × (0.3×Перцептивність + 0.3×Керованість + 0.4×Зрозумілість) + 0.4×Локалізація
        
        Args:
            subscores: Словник з підскорами
            
        Returns:
            Фінальний скор від 0 до 1
        """
        
        # Основний скор (без локалізації)
        main_score = (
            0.3 * subscores.get('perceptibility', 0) +
            0.3 * subscores.get('operability', 0) +
            0.4 * subscores.get('understandability', 0)
        )
        
        # Фінальний скор з урахуванням локалізації
        final_score = 0.6 * main_score + 0.4 * subscores.get('localization', 0)
        
        return max(0, min(1, final_score))
    
    def get_quality_level(self, score: float) -> str:
        """
        Визначення рівня якості згідно з шкалою з наукової статті
        
        Args:
            score: Скор від 0 до 1
            
        Returns:
            Рівень якості
        """
        
        if score >= 0.618:  # Золотий перетин
            return "Відмінно"
        elif score >= 0.382:
            return "Добре"
        elif score >= 0.236:
            return "Задовільно"
        elif score >= 0.146:
            return "Погано"
        else:
            return "Дуже погано"
    
    def get_quality_description(self, score: float) -> str:
        """
        Отримання опису рівня якості
        
        Args:
            score: Скор від 0 до 1
            
        Returns:
            Опис рівня якості
        """
        
        level = self.get_quality_level(score)
        
        descriptions = {
            "Відмінно": "Вебсайт повністю відповідає стандартам доступності",
            "Добре": "Вебсайт має хороший рівень доступності з незначними недоліками",
            "Задовільно": "Вебсайт потребує покращень для відповідності стандартам",
            "Погано": "Вебсайт має серйозні проблеми з доступністю",
            "Дуже погано": "Вебсайт не відповідає базовим вимогам доступності"
        }
        
        return descriptions.get(level, "Невизначено")