# ДОДАТКИ ДО РОЗДІЛУ 4

## Додаток А. Діаграма архітектури системи

Повна діаграма компонентів системи оцінювання доступності міститься у файлі:
`context/architecture_diagram.png`

Діаграма відображає взаємодію між наступними компонентами:
- Клієнтські додатки (веб-інтерфейс, браузерне розширення)
- REST API сервер (FastAPI)
- Модуль AccessibilityEvaluator
- Спеціалізовані аналізатори метрик
- WebScraper з інтеграцією Playwright та axe-core
- Система збереження та кешування результатів

## Додаток Б. Структура каталогів проекту

Детальний опис структури проекту наведено у файлі:
`STRUCTURE.md`

Основні директорії:
```
accessibility_evaluator/      # Python backend
├── api/                      # REST API (рядки 1-289)
├── core/                     # Основна логіка
│   ├── evaluator.py         # Головний клас (рядки 1-1887)
│   ├── metrics/             # Аналізатори метрик
│   └── utils/               # Допоміжні утиліти
├── templates/               # Jinja2 шаблони
└── static/                  # Статичні ресурси

browser-extension/           # Chrome/Firefox розширення
├── manifest.json           # Конфігурація (рядки 1-39)
├── src/popup/             # Інтерфейс popup
│   ├── popup.html
│   ├── popup.css
│   └── popup.js           # Основна логіка (рядки 1-687)
└── assets/                # Іконки та зображення
```

## Додаток В. UML-діаграма класів основного модуля

### Клас AccessibilityEvaluator

**Файл**: `accessibility_evaluator/core/evaluator.py` (рядки 17-91)

**Поля класу**:
```python
weights: Dict[str, float]              # Вагові коефіцієнти підвластивостей
metric_weights: Dict[str, float]       # Вагові коефіцієнти індивідуальних метрик
perceptibility: PerceptibilityMetrics  # Аналізатор перцептивності
operability: OperabilityMetrics        # Аналізатор керованості
understandability: UnderstandabilityMetrics  # Аналізатор зрозумілості
localization: LocalizationMetrics      # Аналізатор локалізації
web_scraper: WebScraper               # Модуль збору даних
calculator: ScoreCalculator           # Калькулятор скорів
```

**Основні методи**:
- `evaluate_accessibility(url: str)` — рядки 49-91
- `calculate_all_metrics(page_data)` — рядки 93-112
- `generate_recommendations(metrics)` — рядки 114-242
- `_generate_detailed_analysis(page_data)` — рядки 281-298

### Клас ScoreCalculator

**Файл**: `accessibility_evaluator/core/utils/calculator.py` (рядки 8-124)

**Методи**:
- `calculate_subscores(metrics)` — рядки 15-54
- `calculate_final_score(subscores)` — рядки 56-79
- `get_quality_level(score)` — рядки 81-101
- `get_quality_description(score)` — рядки 103-124

Формула фінального скору (рядки 70-77):
```python
main_score = (
    0.3 * subscores['perceptibility'] +
    0.3 * subscores['operability'] +
    0.4 * subscores['understandability']
)
final_score = 0.6 * main_score + 0.4 * subscores['localization']
```

## Додаток Г. Формули агрегації метрик у підскори

### Перцептивність (UAC-1.1-G)

**Файл**: `accessibility_evaluator/core/utils/calculator.py` (рядки 27-31)

```python
perceptibility = (
    metrics['alt_text'] * 0.5 +
    metrics['contrast'] * 0.5 +
    metrics['media_accessibility'] * 0.4
) / 1.4
```

### Керованість (UAC-1.2-G)

**Файл**: `accessibility_evaluator/core/utils/calculator.py` (рядки 34-37)

```python
operability = (
    metrics['keyboard_navigation'] * 0.6 +
    metrics['structured_navigation'] * 0.4
)
```

### Зрозумілість (UAC-1.3-G)

**Файл**: `accessibility_evaluator/core/utils/calculator.py` (рядки 40-44)

```python
understandability = (
    metrics['instruction_clarity'] * 0.4 +
    metrics['input_assistance'] * 0.3 +
    metrics['error_support'] * 0.3
)
```

### Локалізація (UAC-2.1-S)

**Файл**: `accessibility_evaluator/core/utils/calculator.py` (рядок 47)

```python
localization = metrics['localization']
```

## Додаток Д. Алгоритми розрахунку метрик

### Метрика альтернативного тексту (UAC-1.1.1-G)

**Файл**: `accessibility_evaluator/core/metrics/perceptibility.py` (рядки 30-107)

**Алгоритм**:
1. Отримання результатів axe-core для правил image-alt, input-image-alt, area-alt (рядки 44-91)
2. Підрахунок коректних зображень з секції passes (рядки 54-68)
3. Підрахунок проблемних зображень з секції violations (рядки 73-90)
4. Обчислення метрики як correct_images / total_images (рядки 93-107)

**Fallback-механізм** (рядки 109-142):
При відсутності результатів axe-core:
1. Парсинг HTML через BeautifulSoup (рядок 117)
2. Пошук всіх тегів `<img>` (рядок 118)
3. Перевірка наявності атрибута alt (рядки 128-135)
4. Обчислення fallback-метрики (рядки 137-142)

### Метрика контрастності (UAC-1.1.2-G)

**Файл**: `accessibility_evaluator/core/metrics/perceptibility.py` (рядки 194-230)

**Алгоритм**:
1. Аналіз правил color-contrast та color-contrast-enhanced (рядки 133-180)
2. Підрахунок елементів з достатнім контрастом (рядки 144-158)
3. Підрахунок елементів з недостатнім контрастом (рядки 161-180)
4. Обчислення метрики (рядки 217-230)

**Fallback-механізм** (рядки 144-182):
При відсутності результатів:
1. Пошук текстових елементів у HTML (рядки 155-167)
2. Консервативна оцінка 0.8 (80% прийнятного контрасту) (рядки 176-182)

### Метрика доступності медіа (UAC-1.1.3-G)

**Файл**: `accessibility_evaluator/core/metrics/perceptibility.py` (рядки 232-287)

**Алгоритм**:
1. Фільтрація відео-елементів (рядок 209)
2. Для HTML5 відео: перевірка наявності `<track>` елементів (рядки 232-251)
3. Для embedded відео: евристична перевірка URL параметрів (рядки 253-271)
4. Обчислення метрики як accessible_videos / total_videos (рядок 279)

## Додаток Е. Приклади генерації рекомендацій

### Генерація рекомендацій для низької перцептивності

**Файл**: `accessibility_evaluator/core/evaluator.py` (рядки 114-242)

**Логіка визначення пріоритету** (рядки 133-137):
```python
if score < 0.5:
    priority = "high"
elif score < 0.7:
    priority = "medium"
else:
    priority = "low"
```

**Приклад рекомендації для метрики alt_text** (рядки 149-161):
```python
if metrics.get('alt_text', 1.0) < 0.7:
    recommendations.append({
        'category': 'Перцептивність',
        'priority': 'high' if metrics['alt_text'] < 0.5 else 'medium',
        'recommendation': (
            'На сторінці виявлено зображення без альтернативного тексту. '
            'Додайте атрибут alt до всіх інформативних зображень. '
            'Для декоративних зображень використовуйте порожній атрибут alt="".'
        ),
        'wcag_reference': 'WCAG 2.1 Критерій успіху 1.1.1 Non-text Content (Рівень A)'
    })
```

**Приклад рекомендації для метрики contrast** (рядки 163-175):
```python
if metrics.get('contrast', 1.0) < 0.7:
    recommendations.append({
        'category': 'Перцептивність',
        'priority': 'high' if metrics['contrast'] < 0.5 else 'medium',
        'recommendation': (
            'Виявлено текстові елементи з недостатнім контрастом відносно фону. '
            'Забезпечте мінімальне контрастне співвідношення 4.5:1 для звичайного тексту '
            'та 3:1 для великого тексту (18pt або 14pt жирний).'
        ),
        'wcag_reference': 'WCAG 2.1 Критерій успіху 1.4.3 Contrast (Minimum) (Рівень AA)'
    })
```

## Додаток Ж. Формати даних модуля WebScraper

### Структура page_data

**Файл**: `accessibility_evaluator/core/utils/web_scraper.py` (рядки 75-97)

```python
page_data = {
    'url': str,                           # URL сторінки
    'html_content': str,                  # Повний HTML контент
    'title': str,                         # Заголовок сторінки
    'page_depth': int,                    # Глибина сторінки в ієрархії
    'interactive_elements': List[Dict],   # Інтерактивні елементи
    'text_elements': List[Dict],          # Текстові елементи
    'media_elements': List[Dict],         # Медіа елементи
    'form_elements': List[Dict],          # Елементи форм
    'computed_styles': Dict,              # Обчислені стилі
    'axe_results': Dict,                  # Результати axe-core
    'focus_test_results': Dict,           # Результати тестування фокусу
    'form_error_test_results': Dict       # Результати тестування форм
}
```

### Структура interactive_elements

**Файл**: `accessibility_evaluator/core/utils/web_scraper.py` (рядки 113-139)

```python
{
    'tag': str,              # Назва HTML тегу
    'type': str,             # Тип елемента
    'tabindex': str,         # Значення tabindex
    'role': str,             # ARIA роль
    'aria_label': str,       # ARIA label
    'text': str,             # Текстовий вміст
    'is_visible': bool,      # Чи видимий елемент
    'is_enabled': bool       # Чи активний елемент
}
```

### Структура text_elements

**Файл**: `accessibility_evaluator/core/utils/web_scraper.py` (рядки 141-175)

```python
{
    'tag': str,              # HTML тег
    'text': str,             # Текстовий вміст
    'styles': {
        'color': str,             # Колір тексту (RGB)
        'backgroundColor': str,   # Колір фону (RGB)
        'fontSize': str,          # Розмір шрифту
        'fontWeight': str         # Товщина шрифту
    },
    'is_visible': bool       # Видимість елемента
}
```

### Структура axe_results

**Файл**: `accessibility_evaluator/core/utils/web_scraper.py` (рядки 636-730)

Результати axe-core містять (рядки 669-686):
```python
{
    'violations': [          # Виявлені порушення
        {
            'id': str,           # Ідентифікатор правила
            'impact': str,       # Рівень впливу (critical, serious, moderate, minor)
            'description': str,  # Опис проблеми
            'help': str,         # Текст допомоги
            'helpUrl': str,      # URL з детальною інформацією
            'nodes': [           # Проблемні елементи
                {
                    'target': List[str],      # CSS селектор
                    'html': str,              # HTML код елемента
                    'failureSummary': str,    # Опис помилки
                    'impact': str             # Вплив конкретного елемента
                }
            ]
        }
    ],
    'passes': [              # Успішні перевірки (аналогічна структура)
    ],
    'incomplete': [          # Неповні перевірки
    ],
    'inapplicable': []       # Неприкладні правила
}
```

## Додаток З. Блок-схеми алгоритмів метрик

### Алгоритм розрахунку метрики альтернативного тексту

**Псевдокод**:
```
FUNCTION calculate_alt_text_metric(page_data):
    axe_results = page_data['axe_results']
    total_images = 0
    correct_images = 0

    FOR EACH rule IN ['image-alt', 'input-image-alt', 'area-alt']:
        passes = get_axe_rule_results(axe_results, 'passes', rule)
        IF passes EXISTS:
            correct_images += LENGTH(passes['nodes'])
            total_images += LENGTH(passes['nodes'])

        violations = get_axe_rule_results(axe_results, 'violations', rule)
        IF violations EXISTS:
            total_images += LENGTH(violations['nodes'])

    IF total_images == 0:
        RETURN fallback_alt_text_analysis(page_data)

    RETURN correct_images / total_images
END FUNCTION

FUNCTION fallback_alt_text_analysis(page_data):
    html = page_data['html_content']
    images = parse_html_find_all_images(html)

    IF LENGTH(images) == 0:
        RETURN 1.0

    correct = 0
    FOR EACH img IN images:
        IF img HAS ATTRIBUTE 'alt':
            correct += 1

    RETURN correct / LENGTH(images)
END FUNCTION
```

**Реалізація**: `accessibility_evaluator/core/metrics/perceptibility.py` (рядки 30-142)

### Алгоритм тестування клавіатурної навігації

**Псевдокод**:
```
FUNCTION test_keyboard_focus(page):
    interactive_elements = find_all_interactive(page)
    focusable_count = 0

    FOR EACH element IN interactive_elements:
        IF element IS visible AND element NOT disabled:
            tabindex = element.getAttribute('tabindex')

            IF tabindex >= 0 OR element IS naturally focusable:
                focusable_count += 1

    total_interactive = LENGTH(interactive_elements)

    IF total_interactive == 0:
        RETURN 1.0

    RETURN focusable_count / total_interactive
END FUNCTION
```

**Реалізація**: `accessibility_evaluator/core/utils/web_scraper.py` (рядки 732-823)

## Додаток И. Специфікація API endpoints

### POST /api/evaluate

**Файл**: `accessibility_evaluator/api/app.py` (рядки 119-150)

**Request**:
```json
{
    "url": "https://example.com"
}
```

**Response** (рядки 98-108):
```json
{
    "url": "string",
    "final_score": 0.75,
    "quality_level": "Добре",
    "quality_description": "Сайт має хорошу доступність з незначними проблемами",
    "subscores": {
        "perceptibility": 0.82,
        "operability": 0.75,
        "understandability": 0.68,
        "localization": 0.80
    },
    "metrics": {
        "alt_text": 0.90,
        "contrast": 0.85,
        "media_accessibility": 0.70,
        "keyboard_navigation": 0.80,
        "structured_navigation": 0.65,
        "instruction_clarity": 0.75,
        "input_assistance": 0.70,
        "error_support": 0.60,
        "localization": 0.80
    },
    "recommendations": [
        {
            "category": "string",
            "priority": "high|medium|low",
            "recommendation": "string",
            "wcag_reference": "string"
        }
    ],
    "detailed_analysis": { },
    "status": "success"
}
```

### POST /api/evaluate-html

**Файл**: `accessibility_evaluator/api/app.py` (рядки 153-213)

**Request** (рядки 78-81):
```json
{
    "html_content": "<!DOCTYPE html>...",
    "base_url": "https://example.com",  // опціонально
    "title": "Page Title"               // опціонально
}
```

**Response**: Аналогічний до /api/evaluate

### POST /api/report

**Файл**: `accessibility_evaluator/api/app.py` (рядки 216-269)

**Request**: Приймає результати оцінювання у форматі EvaluationResponse

**Response**: HTML документ з повним звітом

### GET /api/health

**Файл**: `accessibility_evaluator/api/app.py` (рядки 272-284)

**Response**:
```json
{
    "status": "healthy",
    "version": "1.0.0",
    "timestamp": "2024-01-01T12:00:00"
}
```

## Додаток К. Скріншоти веб-інтерфейсу

Скріншоти інтерфейсу зберігаються у директорії:
`context/screenshots/`

1. `web_interface_initial.png` — Початковий стан вебінтерфейсу
2. `web_interface_analyzing.png` — Процес аналізу з індикатором завантаження
3. `web_interface_results.png` — Відображення результатів аналізу
4. `web_interface_details.png` — Детальний звіт з метриками
5. `web_interface_recommendations.png` — Список рекомендацій

## Додаток Л. Структура браузерного розширення

### Manifest конфігурація

**Файл**: `browser-extension/manifest.json` (рядки 1-39)

```json
{
  "manifest_version": 3,
  "name": "Accessibility Evaluator",
  "version": "1.0.0",
  "description": "Комплексна оцінка доступності вебсайтів",
  "permissions": [
    "activeTab",
    "storage",
    "scripting"
  ],
  "action": {
    "default_popup": "src/popup/popup.html",
    "default_icon": {
      "16": "assets/icon-16.png",
      "48": "assets/icon-48.png",
      "128": "assets/icon-128.png"
    }
  }
}
```

### Клас AccessibilityPopup

**Файл**: `browser-extension/src/popup/popup.js` (рядки 5-687)

**Основні методи**:
- `init()` — Ініціалізація розширення (рядки 14-20)
- `initSettings()` — Налаштування за замовчуванням (рядки 43-70)
- `analyzeCurrentPage()` — Аналіз активної вкладки (рядки 126-268)
- `sendHtmlToApi()` — Відправка HTML на API (рядки 270-317)
- `displayResults()` — Відображення результатів (рядки 335-449)
- `exportReport()` — Експорт звіту (рядки 481-556)

### Конвертація відносних URL в абсолютні

**Файл**: `browser-extension/src/popup/popup.js` (рядки 151-190)

```javascript
const pageData = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => {
      const clone = document.documentElement.cloneNode(true);

      // Обробка зображень
      clone.querySelectorAll("img[src]").forEach((img) => {
        img.src = new URL(img.getAttribute("src"), document.baseURI).href;
      });

      // Обробка стилів
      clone.querySelectorAll("link[href]").forEach((link) => {
        link.href = new URL(link.getAttribute("href"), document.baseURI).href;
      });

      // Обробка скриптів
      clone.querySelectorAll("script[src]").forEach((script) => {
        script.src = new URL(script.getAttribute("src"), document.baseURI).href;
      });

      return {
        html: clone.outerHTML,
        baseUrl: document.baseURI
      };
    }
});
```

## Додаток М. Послідовність взаємодії розширення з API

### Сценарій аналізу сторінки

1. **Перевірка доступності сервера** (popup.js рядки 100-124):
```javascript
fetch(`${API_BASE_URL}/api/health`)
  .then(response => response.json())
  .then(data => {
    // Сервер доступний
  });
```

2. **Отримання HTML активної вкладки** (popup.js рядки 151-190):
```javascript
chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => {
      // Витягування та обробка HTML
      return { html, baseUrl };
    }
});
```

3. **Відправка на аналіз** (popup.js рядки 270-317):
```javascript
fetch(`${API_BASE_URL}/api/evaluate-html`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      html_content: htmlContent,
      base_url: baseUrl,
      title: title
    })
});
```

4. **Збереження результатів** (popup.js рядки 560-575):
```javascript
chrome.storage.local.set({
    [key]: {
      ui: uiResults,
      api: apiResults,
      timestamp: Date.now(),
      url: url
    }
});
```

## Додаток Н. Тестові сценарії

### Модульні тести метрик

**Тестування метрики alt_text**:

Тестові дані:
```python
# Сторінка без зображень
page_data_no_images = {
    'axe_results': {'passes': [], 'violations': []},
    'html_content': '<html><body><p>Text only</p></body></html>'
}
expected_score = 1.0

# Сторінка з коректними зображеннями
page_data_correct = {
    'axe_results': {
        'passes': [{
            'id': 'image-alt',
            'nodes': [
                {'html': '<img src="1.jpg" alt="Image 1">'},
                {'html': '<img src="2.jpg" alt="Image 2">'}
            ]
        }],
        'violations': []
    }
}
expected_score = 1.0

# Сторінка з проблемними зображеннями
page_data_problems = {
    'axe_results': {
        'passes': [{
            'id': 'image-alt',
            'nodes': [{'html': '<img src="1.jpg" alt="OK">'}]
        }],
        'violations': [{
            'id': 'image-alt',
            'nodes': [
                {'html': '<img src="2.jpg">'},  # Без alt
                {'html': '<img src="3.jpg">'}   # Без alt
            ]
        }]
    }
}
expected_score = 1/3 = 0.333
```

### Інтеграційні тести

**Тест повного циклу аналізу**:

Вхідні дані:
- URL: `http://test-server.local/sample-page.html`
- Сторінка містить: 3 зображення (2 з alt, 1 без), 5 посилань, 1 форму

Очікувані результати:
```python
{
    'metrics': {
        'alt_text': 0.667,  # 2/3 зображень коректні
        'keyboard_navigation': 1.0,  # Всі елементи доступні
        'instruction_clarity': 1.0,  # Форма має labels
        # ...
    },
    'final_score': 0.72,  # Обчислений згідно формули
    'recommendations': [
        # Рекомендація щодо зображення без alt
    ]
}
```

## Додаток О. Приклади лог-файлів

### Успішний аналіз сторінки

```
2024-11-01 12:00:00 INFO: 🔍 Початок оцінки доступності для URL: https://example.com
2024-11-01 12:00:01 INFO: 🌐 Завантаження сторінки: https://example.com
2024-11-01 12:00:05 INFO: 📄 Отримання HTML контенту...
2024-11-01 12:00:05 INFO: 🔍 Збір інтерактивних елементів...
2024-11-01 12:00:06 INFO: 📝 Збір текстових елементів...
2024-11-01 12:00:07 INFO: 🎬 Збір медіа елементів...
2024-11-01 12:00:08 INFO: 🔍 Запуск axe-core аналізу...
2024-11-01 12:00:10 INFO: ✅ axe-core аналіз завершено:
2024-11-01 12:00:10 INFO:    ❌ Порушення: 3
2024-11-01 12:00:10 INFO:    ✅ Пройдено: 42
2024-11-01 12:00:11 INFO: ✅ Збір даних завершено. Знайдено:
2024-11-01 12:00:11 INFO:    📝 Текстових елементів: 156
2024-11-01 12:00:11 INFO:    🔗 Інтерактивних елементів: 24
2024-11-01 12:00:11 INFO:    🎬 Медіа елементів: 5
2024-11-01 12:00:12 INFO: ✅ Оцінка завершена успішно для https://example.com
2024-11-01 12:00:12 INFO: 📊 Загальний скор: 75%
```

### Аналіз з помилками

```
2024-11-01 12:05:00 INFO: 🔍 Початок оцінки доступності для URL: https://slow-site.com
2024-11-01 12:05:01 INFO: 🌐 Завантаження сторінки: https://slow-site.com
2024-11-01 12:05:31 WARNING: ⚠️ Networkidle failed, trying domcontentloaded: Timeout 30000ms exceeded
2024-11-01 12:05:35 INFO: 📄 Отримання HTML контенту...
2024-11-01 12:05:35 INFO: ✅ Збір даних завершено
2024-11-01 12:05:36 WARNING: ⚠️ axe-core не знайшов зображень. Використовуємо fallback аналіз HTML...
2024-11-01 12:05:36 INFO: Знайдено <img> тегів у HTML: 8
2024-11-01 12:05:36 INFO: 📊 Загальний скор: 68%
```

## Додаток П. Інструкції з розгортання

### Розгортання на Ubuntu Server

**Файл**: `deployment/ubuntu_deploy.sh`

```bash
#!/bin/bash
# Встановлення системних залежностей
sudo apt update
sudo apt install -y python3.9 python3-pip nodejs npm

# Створення віртуального середовища
python3 -m venv venv
source venv/bin/activate

# Встановлення Python залежностей
pip install -r requirements.txt

# Встановлення Playwright браузерів
playwright install chromium
playwright install-deps

# Встановлення axe-core
npm install axe-core

# Налаштування змінних середовища
cat > .env << EOF
API_PORT=8001
LOG_LEVEL=INFO
MAX_TIMEOUT=60000
EOF

# Запуск сервера
python start_server.py
```

### Розгортання через Docker

**Файл**: `Dockerfile`

```dockerfile
FROM python:3.9-slim

# Встановлення системних залежностей для Playwright
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Робоча директорія
WORKDIR /app

# Копіювання requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Встановлення Playwright
RUN playwright install chromium
RUN playwright install-deps

# Копіювання коду
COPY . .

# Встановлення axe-core
RUN npm install axe-core

# Запуск
EXPOSE 8001
CMD ["python", "start_server.py"]
```

**Файл**: `docker-compose.yml`

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8001:8001"
    environment:
      - LOG_LEVEL=INFO
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
```

## Додаток Р. Конфігураційні файли

### Конфігурація Nginx

**Файл**: `deployment/nginx.conf`

```nginx
upstream api_backend {
    server localhost:8001;
}

server {
    listen 80;
    server_name accessibility-evaluator.com;

    # Перенаправлення на HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name accessibility-evaluator.com;

    # SSL сертифікати
    ssl_certificate /etc/letsencrypt/live/accessibility-evaluator.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/accessibility-evaluator.com/privkey.pem;

    # Заголовки безпеки
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Статичні файли
    location /static {
        alias /var/www/accessibility-evaluator/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # API проксі
    location /api {
        proxy_pass http://api_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Таймаути для довгих запитів
        proxy_read_timeout 120s;
        proxy_connect_timeout 120s;
    }

    # Головна сторінка
    location / {
        proxy_pass http://api_backend;
        proxy_set_header Host $host;
    }
}
```

### Конфігурація systemd service

**Файл**: `deployment/accessibility-evaluator.service`

```ini
[Unit]
Description=Accessibility Evaluator API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/var/www/accessibility-evaluator
Environment="PATH=/var/www/accessibility-evaluator/venv/bin"
ExecStart=/var/www/accessibility-evaluator/venv/bin/python start_server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Встановлення та запуск:
```bash
sudo cp deployment/accessibility-evaluator.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable accessibility-evaluator
sudo systemctl start accessibility-evaluator
```
