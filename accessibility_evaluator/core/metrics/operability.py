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
        Розрахунок метрики навігації з клавіатури (UAC-1.2.1-G) з реальним тестуванням фокусу
        
        Формула: X = A / B
        A = кількість інтерактивних елементів, доступних для керування клавіатурою
        B = загальна кількість інтерактивних елементів
        """
        
        print(f"\n⌨️ === ДЕТАЛЬНИЙ АНАЛІЗ КЛАВІАТУРНОЇ НАВІГАЦІЇ (РЕАЛЬНЕ ТЕСТУВАННЯ) ===")
        
        # Отримуємо результати реального тестування фокусу з web_scraper
        focus_test_results = page_data.get('focus_test_results', [])
        
        if not focus_test_results:
            print("⚠️ Результати тестування фокусу недоступні, використовуємо fallback")
            return await self._fallback_keyboard_analysis(page_data)
        
        total_elements = len(focus_test_results)
        focusable_elements = sum(1 for result in focus_test_results if result.get('focusable', False))
        
        print(f"📋 Знайдено потенційно інтерактивних елементів: {total_elements}")
        print(f"✅ Справді доступних з клавіатури: {focusable_elements}")
        print(f"❌ Недоступних з клавіатури: {total_elements - focusable_elements}")
        print()
        
        # Показуємо деталі доступних елементів
        focusable_list = [r for r in focus_test_results if r.get('focusable', False)]
        if focusable_list:
            print(f"✅ Доступні елементи (показуємо перші 5):")
            for i, result in enumerate(focusable_list[:5]):
                print(f"   {i+1}. {result.get('tag', 'unknown')} - {result.get('selector', 'невідомо')}")
                print(f"      HTML: {result.get('html', 'немає')[:80]}...")
                print(f"      Причина доступності: {result.get('focus_reason', 'Пройшов тест фокусу')}")
                print()
        
        # Показуємо деталі недоступних елементів
        non_focusable_list = [r for r in focus_test_results if not r.get('focusable', False)]
        if non_focusable_list:
            print(f"❌ Недоступні елементи (показуємо перші 5):")
            for i, result in enumerate(non_focusable_list[:5]):
                print(f"   {i+1}. {result.get('tag', 'unknown')} - {result.get('selector', 'невідомо')}")
                print(f"      HTML: {result.get('html', 'немає')[:80]}...")
                print(f"      Причина недоступності: {result.get('non_focus_reason', 'Не пройшов тест фокусу')}")
                print()
        
        if total_elements == 0:
            print("⚠️ Інтерактивні елементи не знайдено - повертаємо 1.0")
            score = 1.0
        else:
            score = focusable_elements / total_elements
            print(f"🎯 Фінальний розрахунок: {focusable_elements} / {total_elements} = {score:.3f}")
        
        print(f"=== КІНЕЦЬ АНАЛІЗУ КЛАВІАТУРНОЇ НАВІГАЦІЇ ===\n")
        return score
    
    async def _fallback_keyboard_analysis(self, page_data: Dict[str, Any]) -> float:
        """Fallback аналіз якщо реальне тестування недоступне"""
        
        print("🔄 Використовуємо fallback аналіз...")
        interactive_elements = page_data.get('interactive_elements', [])
        
        if not interactive_elements:
            return 1.0
        
        accessible_count = 0
        for element in interactive_elements:
            if self._is_keyboard_accessible(element):
                accessible_count += 1
        
        score = accessible_count / len(interactive_elements)
        print(f"📊 Fallback результат: {accessible_count}/{len(interactive_elements)} = {score:.3f}")
        return score
    
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
        Розрахунок метрики структурованої навігації (UAC-1.2.2-G) з використанням axe-core
        
        Формула: X = A / B
        A = кількість правильно структурованих заголовків (з axe-core passes)
        B = загальна кількість заголовків (passes + violations)
        """
        
        axe_results = page_data.get('axe_results', {})
        
        print(f"\n📋 === ДЕТАЛЬНИЙ АНАЛІЗ СТРУКТУРИ ЗАГОЛОВКІВ ===")
        
        # Отримуємо результати для правил структури заголовків
        heading_rules = ['heading-order', 'page-has-heading-one', 'empty-heading']
        
        total_headings = 0
        correct_headings = 0
        
        print(f"📋 Аналізуємо правила: {heading_rules}")
        
        for rule_id in heading_rules:
            print(f"\n🔍 Правило: {rule_id}")
            
            # Підраховуємо правильні заголовки (passes)
            passes = self._get_axe_rule_results(axe_results, 'passes', rule_id)
            if passes:
                passes_count = len(passes.get('nodes', []))
                correct_headings += passes_count
                total_headings += passes_count
                print(f"   ✅ Passes: {passes_count} елементів")
                
                # Показуємо деталі перших кількох елементів
                nodes = passes.get('nodes', [])[:3]  # Перші 3 елементи
                for i, node in enumerate(nodes):
                    target = node.get('target', ['невідомо'])
                    html = node.get('html', 'немає HTML')[:80] + '...' if len(node.get('html', '')) > 80 else node.get('html', 'немає HTML')
                    print(f"     {i+1}. Target: {target}")
                    print(f"        HTML: {html}")
            else:
                print(f"   ✅ Passes: 0 елементів")
            
            # Підраховуємо проблемні заголовки (violations)
            violations = self._get_axe_rule_results(axe_results, 'violations', rule_id)
            if violations:
                violations_count = len(violations.get('nodes', []))
                total_headings += violations_count
                print(f"   ❌ Violations: {violations_count} елементів")
                print(f"   📝 Опис проблеми: {violations.get('description', 'немає опису')}")
                
                # Показуємо деталі перших кількох проблемних елементів
                nodes = violations.get('nodes', [])[:3]  # Перші 3 елементи
                for i, node in enumerate(nodes):
                    target = node.get('target', ['невідомо'])
                    html = node.get('html', 'немає HTML')[:80] + '...' if len(node.get('html', '')) > 80 else node.get('html', 'немає HTML')
                    failure_summary = node.get('failureSummary', 'немає опису помилки')
                    print(f"     {i+1}. Target: {target}")
                    print(f"        HTML: {html}")
                    print(f"        Проблема: {failure_summary}")
                # correct_headings НЕ збільшуємо для violations
            else:
                print(f"   ❌ Violations: 0 елементів")
        
        print(f"\n📊 ПІДСУМОК СТРУКТУРИ ЗАГОЛОВКІВ:")
        print(f"   Правильних заголовків: {correct_headings}")
        print(f"   Загальних заголовків: {total_headings}")
        
        # Якщо немає заголовків, повертаємо 1.0
        if total_headings == 0:
            print(f"   ⚠️ Немає заголовків для аналізу - повертаємо 1.0")
            return 1.0
        
        score = correct_headings / total_headings
        print(f"   🎯 Розрахунок: {correct_headings} / {total_headings} = {score:.3f}")
        print(f"=== КІНЕЦЬ АНАЛІЗУ ЗАГОЛОВКІВ ===\n")
        
        return score
    
    def _get_axe_rule_results(self, axe_results: Dict[str, Any], result_type: str, rule_id: str) -> Dict[str, Any]:
        """Отримання результатів конкретного правила axe-core"""
        
        results = axe_results.get(result_type, [])
        for result in results:
            if result.get('id') == rule_id:
                return result
        return {}
    
