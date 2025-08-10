#!/usr/bin/env python3
"""
Скрипт для налаштування середовища розробки
"""

import subprocess
import sys
import os


def run_command(command, description):
    """Виконання команди з описом"""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - успішно")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - помилка:")
        print(f"   {e.stderr}")
        return False


def main():
    print("🔧 Налаштування середовища для Accessibility Evaluator")
    print("=" * 60)
    
    # Перевірка Python версії
    if sys.version_info < (3, 8):
        print("❌ Потрібна версія Python 3.8 або новіша")
        sys.exit(1)
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} - підходить")
    
    # Встановлення Python залежностей
    if not run_command("pip3 install -r requirements.txt", "Встановлення Python пакетів"):
        print("❌ Не вдалося встановити Python залежності")
        sys.exit(1)
    
    # Встановлення Playwright браузерів
    if not run_command("playwright install chromium", "Встановлення Playwright браузерів"):
        print("❌ Не вдалося встановити Playwright браузери")
        sys.exit(1)
    
    # Встановлення Node.js залежностей (якщо є package.json)
    if os.path.exists("package.json"):
        if not run_command("npm install", "Встановлення Node.js пакетів"):
            print("⚠️  Не вдалося встановити Node.js залежності (не критично)")
    
    print("\n🎉 Налаштування завершено успішно!")
    print("\n📋 Наступні кроки:")
    print("   1. Запустіть сервер: python run_server.py")
    print("   2. Відкрийте браузер: http://localhost:8000")
    print("   3. Введіть URL для аналізу доступності")
    print("\n📚 Додаткові команди:")
    print("   • API документація: http://localhost:8000/docs")
    print("   • Тестування API: http://localhost:8000/api/health")


if __name__ == "__main__":
    main()