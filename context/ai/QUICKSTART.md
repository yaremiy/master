# 🚀 Швидкий старт

## Встановлення залежностей

```bash
# 1. Python залежності
pip3 install -r requirements.txt

# 2. Playwright браузери
playwright install chromium

# 3. Node.js залежності (для axe-core)
npm install
```

## Запуск сервера

```bash
python3 start_server.py
```

Сервер запуститься на `http://localhost:8001`

## Використання екстеншина

1. Відкрийте Chrome → Extensions → Developer mode
2. Load unpacked → виберіть папку `browser-extension`
3. Переконайтеся що сервер запущено
4. Клікніть на іконку екстеншина і натисніть "Аналізувати сторінку"

## API Endpoints

- `GET /` - Веб-інтерфейс
- `POST /api/evaluate` - Аналіз за URL
- `POST /api/report` - Генерація HTML звіту
- `GET /api/health` - Статус API
- `GET /docs` - Swagger документація

## Приклад API запиту

```bash
curl -X POST http://localhost:8001/api/evaluate \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'
```

## Виправлення помилок

### "No module named 'playwright'"
```bash
pip3 install playwright
playwright install chromium
```

### "axe-core не знайдено"
```bash
npm install
```

### Сервер не запускається
```bash
# Перевірте порт
lsof -i :8001

# Перевірте Python версію (потрібен 3.11+)
python3 --version
```

---

Детальніша документація: [STRUCTURE.md](STRUCTURE.md)
