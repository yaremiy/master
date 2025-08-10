#!/usr/bin/env python3
"""
Розробницький сервер з автоматичним перезапуском
"""

import sys
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import signal

# Додаємо поточну директорію до Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

class ServerHandler(FileSystemEventHandler):
    def __init__(self):
        self.process = None
        self.start_server()
    
    def on_modified(self, event):
        if event.is_directory:
            return
        
        # Перезапускаємо тільки для Python файлів
        if event.src_path.endswith('.py'):
            print(f"🔄 Файл змінено: {event.src_path}")
            self.restart_server()
    
    def start_server(self):
        print("🚀 Запуск сервера...")
        self.process = subprocess.Popen([
            sys.executable, "-m", "uvicorn",
            "accessibility_evaluator.web_interface.backend.app:app",
            "--host", "0.0.0.0",
            "--port", "8001",
            "--log-level", "info"
        ], cwd=current_dir)
    
    def restart_server(self):
        if self.process:
            print("⏹️  Зупинка сервера...")
            self.process.terminate()
            self.process.wait()
        
        time.sleep(1)
        self.start_server()
    
    def stop_server(self):
        if self.process:
            self.process.terminate()
            self.process.wait()

def main():
    print("🔧 Розробницький сервер з автоматичним перезапуском")
    print("📍 Веб-інтерфейс: http://localhost:8001")
    print("📊 API документація: http://localhost:8001/docs")
    print("🔄 Автоматичний перезапуск при змінах .py файлів")
    print("⏹️  Для зупинки натисніть Ctrl+C")
    print("-" * 60)
    
    handler = ServerHandler()
    observer = Observer()
    observer.schedule(handler, current_dir, recursive=True)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Зупинка сервера...")
        observer.stop()
        handler.stop_server()
    
    observer.join()
    print("👋 Сервер зупинено")

if __name__ == "__main__":
    main()