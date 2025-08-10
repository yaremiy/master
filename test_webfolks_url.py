#!/usr/bin/env python3
"""
Тест конкретного URL з webfolks.io
"""

import asyncio
import sys
import os

# Додаємо шлях до проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_webfolks_url():
    """Тест URL з webfolks.io"""
    
    try:
        from accessibility_evaluator.core.evaluator import AccessibilityEvaluator
        print("✅ Імпорт успішний")
        
        evaluator = AccessibilityEvaluator()
        
        # Тестуємо оригінальний URL
        test_url = "https://www.webfolks.io/case-studies/allsetra"
        print(f"🔍 Тестуємо: {test_url}")
        
        result = await evaluator.evaluate_accessibility(test_url)
        
        if result['status'] == 'success':
            print("✅ Аналіз завершений успішно!")
            print(f"📊 Фінальний скор: {result['final_score']:.3f}")
            
            print(f"\n📈 Підскори:")
            for key, value in result['subscores'].items():
                print(f"   {key}: {value:.3f}")
            
            print(f"\n🔍 Детальні метрики:")
            for key, value in result['metrics'].items():
                print(f"   {key}: {value:.3f}")
            
            print(f"\n💡 Рекомендації ({len(result['recommendations'])}):")
            for i, rec in enumerate(result['recommendations'][:3], 1):
                print(f"   {i}. {rec['category']}: {rec['recommendation']}")
                
        else:
            print(f"❌ Помилка аналізу: {result.get('error', 'Невідома помилка')}")
            
    except Exception as e:
        print(f"❌ Критична помилка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🧪 Тестування URL: webfolks.io")
    print("=" * 50)
    asyncio.run(test_webfolks_url())