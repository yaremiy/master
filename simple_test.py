#!/usr/bin/env python3
"""
Спрощений тест з простішим URL
"""

import asyncio
import sys
import os

# Додаємо шлях до проекту
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def simple_test():
    """Тест з простішим URL"""
    
    try:
        from accessibility_evaluator.core.evaluator import AccessibilityEvaluator
        print("✅ Імпорт успішний")
        
        evaluator = AccessibilityEvaluator()
        
        # Тестуємо з простішим URL
        test_urls = [
            "https://example.com",
            "https://www.google.com",
            "https://httpbin.org/html"
        ]
        
        for url in test_urls:
            print(f"\n🔍 Тестуємо: {url}")
            try:
                result = await evaluator.evaluate_accessibility(url)
                
                if result['status'] == 'success':
                    print(f"✅ Успіх! Скор: {result['final_score']:.3f}")
                    break
                else:
                    print(f"❌ Помилка: {result.get('error', 'Невідома')}")
                    
            except Exception as e:
                print(f"❌ Виключення: {e}")
                continue
        
    except Exception as e:
        print(f"❌ Критична помилка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(simple_test())