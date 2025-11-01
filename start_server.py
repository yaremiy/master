#!/usr/bin/env python3
"""
Запуск сервера з правильними шляхами
"""

import sys
import os
import uvicorn

# Додаємо поточну директорію до Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Встановлюємо змінну середовища для Python path
os.environ['PYTHONPATH'] = current_dir

if __name__ == "__main__":
    print("🚀 Запуск Accessibility Evaluator...")
    print("📍 Веб-інтерфейс: http://localhost:8001")
    print("📊 API документація: http://localhost:8001/docs")
    print("🔧 Тест API: http://localhost:8001/api/health")
    print("⏹️  Для зупинки натисніть Ctrl+C")
    print("-" * 60)
    
    try:
        uvicorn.run(
            "accessibility_evaluator.api.app:app",
            host="0.0.0.0",
            port=8001,
            reload=True,
            reload_dirs=[current_dir],
            reload_includes=["*.py", "*.html", "*.css", "*.js"],
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n👋 Сервер зупинено")
    except Exception as e:
        print(f"❌ Помилка запуску сервера: {e}")
        print("\n🔧 Спробуйте:")
        print("   1. pip3 install -r requirements.txt")
        print("   2. playwright install chromium")
        print("   3. python3 start_server.py")