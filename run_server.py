#!/usr/bin/env python3
"""
Скрипт для запуску веб-сервера
"""

import uvicorn
import sys
import os

# Додаємо поточну директорію до Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("🚀 Запуск сервера оцінки доступності...")
    print("📍 Сервер буде доступний за адресою: http://localhost:8000")
    print("📊 API документація: http://localhost:8000/docs")
    print("⏹️  Для зупинки натисніть Ctrl+C")
    print("-" * 50)
    
    uvicorn.run(
        "accessibility_evaluator.web_interface.backend.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )