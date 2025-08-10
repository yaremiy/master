#!/usr/bin/env python3
"""
Простий запуск сервера
"""

import sys
import os
import uvicorn

# Додаємо поточну директорію до Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)
os.environ['PYTHONPATH'] = current_dir

if __name__ == "__main__":
    print("🚀 Accessibility Evaluator")
    print("📍 http://localhost:8001")
    print("⏹️  Ctrl+C для зупинки")
    print("-" * 40)
    
    uvicorn.run(
        "accessibility_evaluator.web_interface.backend.app:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )