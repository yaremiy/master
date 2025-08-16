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
        Розрахунок метрики альтернативного тексту (UAC-1.1.1-G) з використанням axe-core
        
        Формула: X = A / B
        A = кількість зображень з правильним alt текстом (з axe-core passes)
        B = загальна кількість зображень (passes + violations)
        """
        
        axe_results = page_data.get('axe_results', {})
        
        print(f"\n🔍 === ДЕТАЛЬНИЙ АНАЛІЗ ALT-TEXT МЕТРИКИ ===")
        
        # Згідно з axe-core документацією, основні правила для зображень:
        alt_related_rules = ['image-alt', 'input-image-alt', 'area-alt']
        
        total_images = 0
        correct_images = 0
        
        print(f"📋 Аналізуємо правила: {alt_related_rules}")
        
        for rule_id in alt_related_rules:
            print(f"\n🔍 Правило: {rule_id}")
            
            # Підраховуємо правильні зображення (passes)
            passes = self._get_axe_rule_results(axe_results, 'passes', rule_id)
            if passes:
                passes_count = len(passes.get('nodes', []))
                correct_images += passes_count
                total_images += passes_count
                print(f"   ✅ Passes: {passes_count} елементів")
                
                # Показуємо деталі перших кількох елементів
                nodes = passes.get('nodes', [])[:3]  # Перші 3 елементи
                for i, node in enumerate(nodes):
                    target = node.get('target', ['невідомо'])
                    html = node.get('html', 'немає HTML')[:100] + '...' if len(node.get('html', '')) > 100 else node.get('html', 'немає HTML')
                    print(f"     {i+1}. Target: {target}")
                    print(f"        HTML: {html}")
            else:
                print(f"   ✅ Passes: 0 елементів")
            
            # Підраховуємо проблемні зображення (violations)
            violations = self._get_axe_rule_results(axe_results, 'violations', rule_id)
            if violations:
                violations_count = len(violations.get('nodes', []))
                total_images += violations_count
                print(f"   ❌ Violations: {violations_count} елементів")
                print(f"   📝 Опис проблеми: {violations.get('description', 'немає опису')}")
                
                # Показуємо деталі перших кількох проблемних елементів
                nodes = violations.get('nodes', [])[:3]  # Перші 3 елементи
                for i, node in enumerate(nodes):
                    target = node.get('target', ['невідомо'])
                    html = node.get('html', 'немає HTML')[:100] + '...' if len(node.get('html', '')) > 100 else node.get('html', 'немає HTML')
                    failure_summary = node.get('failureSummary', 'немає опису помилки')
                    print(f"     {i+1}. Target: {target}")
                    print(f"        HTML: {html}")
                    print(f"        Проблема: {failure_summary}")
                # correct_images НЕ збільшуємо для violations
            else:
                print(f"   ❌ Violations: 0 елементів")
        
        print(f"\n📊 ПІДСУМОК ALT-TEXT:")
        print(f"   Правильних зображень: {correct_images}")
        print(f"   Загальних зображень: {total_images}")
        
        # Якщо немає зображень, повертаємо 1.0
        if total_images == 0:
            print(f"   ⚠️ Немає зображень для аналізу - повертаємо 1.0")
            return 1.0
        
        # Формула: X = A / B
        score = correct_images / total_images
        print(f"   🎯 Розрахунок: {correct_images} / {total_images} = {score:.3f}")
        print(f"=== КІНЕЦЬ ALT-TEXT АНАЛІЗУ ===\n")
        
        return score
    
    def _get_axe_rule_results(self, axe_results: Dict[str, Any], result_type: str, rule_id: str) -> Dict[str, Any]:
        """Отримання результатів конкретного правила axe-core"""
        
        results = axe_results.get(result_type, [])
        for result in results:
            if result.get('id') == rule_id:
                return result
        return {}
    
    
    async def calculate_contrast_metric(self, page_data: Dict[str, Any]) -> float:
        """
        Розрахунок метрики контрастності тексту (UAC-1.1.2-G) з використанням axe-core
        
        Формула: X = A / B
        A = кількість текстових елементів з достатнім контрастом (з axe-core passes)
        B = загальна кількість текстових елементів (passes + violations)
        """
        
        axe_results = page_data.get('axe_results', {})
        
        print(f"\n🎨 === ДЕТАЛЬНИЙ АНАЛІЗ КОНТРАСТУ ===")
        
        # Отримуємо результати для правил контрасту
        contrast_rules = ['color-contrast', 'color-contrast-enhanced']
        
        total_elements = 0
        correct_elements = 0
        
        print(f"📋 Аналізуємо правила: {contrast_rules}")
        
        for rule_id in contrast_rules:
            print(f"\n🔍 Правило: {rule_id}")
            
            # Підраховуємо елементи з правильним контрастом (passes)
            passes = self._get_axe_rule_results(axe_results, 'passes', rule_id)
            if passes:
                passes_count = len(passes.get('nodes', []))
                correct_elements += passes_count
                total_elements += passes_count
                print(f"   ✅ Passes: {passes_count} елементів")
                
                # Показуємо деталі перших кількох елементів
                nodes = passes.get('nodes', [])[:2]  # Перші 2 елементи
                for i, node in enumerate(nodes):
                    target = node.get('target', ['невідомо'])
                    html = node.get('html', 'немає HTML')[:80] + '...' if len(node.get('html', '')) > 80 else node.get('html', 'немає HTML')
                    print(f"     {i+1}. Target: {target}")
                    print(f"        HTML: {html}")
            else:
                print(f"   ✅ Passes: 0 елементів")
            
            # Підраховуємо елементи з проблемним контрастом (violations)
            violations = self._get_axe_rule_results(axe_results, 'violations', rule_id)
            if violations:
                violations_count = len(violations.get('nodes', []))
                total_elements += violations_count
                print(f"   ❌ Violations: {violations_count} елементів")
                print(f"   📝 Опис проблеми: {violations.get('description', 'немає опису')}")
                
                # Показуємо деталі перших кількох проблемних елементів
                nodes = violations.get('nodes', [])[:2]  # Перші 2 елементи
                for i, node in enumerate(nodes):
                    target = node.get('target', ['невідомо'])
                    html = node.get('html', 'немає HTML')[:80] + '...' if len(node.get('html', '')) > 80 else node.get('html', 'немає HTML')
                    failure_summary = node.get('failureSummary', 'немає опису помилки')
                    print(f"     {i+1}. Target: {target}")
                    print(f"        HTML: {html}")
                    print(f"        Проблема: {failure_summary}")
                # correct_elements НЕ збільшуємо для violations
            else:
                print(f"   ❌ Violations: 0 елементів")
        
        print(f"\n📊 ПІДСУМОК КОНТРАСТУ:")
        print(f"   Правильних елементів: {correct_elements}")
        print(f"   Загальних елементів: {total_elements}")
        
        # Якщо немає текстових елементів, повертаємо 1.0
        if total_elements == 0:
            print(f"   ⚠️ Немає текстових елементів для аналізу - повертаємо 1.0")
            return 1.0
        
        score = correct_elements / total_elements
        print(f"   🎯 Розрахунок: {correct_elements} / {total_elements} = {score:.3f}")
        print(f"=== КІНЕЦЬ АНАЛІЗУ КОНТРАСТУ ===\n")
        
        return score
    
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