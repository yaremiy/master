#!/usr/bin/env python3
"""
Тестовий скрипт для перевірки API
"""

import asyncio
import sys
import os

# Додаємо шлях до проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_evaluator():
    """Тест основного функціоналу"""
    
    try:
        from accessibility_evaluator.core.evaluator import AccessibilityEvaluator
        print("✅ Імпорт AccessibilityEvaluator успішний")
        
        evaluator = AccessibilityEvaluator()
        print("✅ Створення екземпляра успішне")
        
        # Тест на простому URL
        test_url = "https://www.webfolks.io/case-studies/allsetra"
        print(f"🔍 Тестуємо URL: {test_url}")
        
        result = await evaluator.evaluate_accessibility(test_url)
        
        if result['status'] == 'success':
            print("✅ Аналіз завершений успішно!")
            print(f"📊 Фінальний скор: {result['final_score']:.3f}")
            print(f"📈 Підскори:")
            for key, value in result['subscores'].items():
                print(f"   {key}: {value:.3f}")
            print(f"💡 Рекомендацій: {len(result['recommendations'])}")
        else:
            print(f"❌ Помилка аналізу: {result.get('error', 'Невідома помилка')}")
            
    except Exception as e:
        print(f"❌ Критична помилка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 Тестування Accessibility Evaluator")
    print("=" * 50)
    asyncio.run(test_evaluator())