# План імплементації метрик доступності

## Загальна архітектура

### Структура проекту:
```
accessibility_evaluator/
├── core/
│   ├── metrics/
│   │   ├── perceptibility.py
│   │   ├── operability.py
│   │   ├── understandability.py
│   │   └── localization.py
│   ├── analyzers/
│   │   ├── contrast_analyzer.py
│   │   ├── structure_analyzer.py
│   │   ├── text_analyzer.py
│   │   └── image_analyzer.py
│   └── utils/
│       ├── web_scraper.py
│       └── calculator.py
├── web_interface/
│   ├── backend/
│   └── frontend/
└── tests/
```

## 1. ПЕРЦЕПТИВНІСТЬ (UAC-1.1-G)

### 1.1 Альтернативний текст (UAC-1.1.1-G)

**Формула з статті**: `X = A / B`
- A = кількість мультимедійних елементів зі змістовними текстовими альтернативами
- B = загальна кількість мультимедійних елементів

**Бібліотеки для використання:**
- `Beautiful Soup` - парсинг HTML
- `axe-core` - базова перевірка alt атрибутів
- `Tesseract OCR` - аналіз тексту в зображеннях
- `Azure Computer Vision API` - AI оцінка якості alt-тексту

**План імплементації:**
1. **Збір даних**:
   - Знайти всі `<img>`, `<video>`, `<audio>`, `<canvas>`, `<svg>` елементи
   - Витягти alt атрибути, aria-labels, figcaptions
   - Ідентифікувати декоративні vs змістовні елементи

2. **Аналіз якості alt-тексту**:
   - Перевірити наявність alt атрибуту
   - Оцінити змістовність (не порожній, не "image", не дублює назву файлу)
   - Використати AI для порівняння alt-тексту з реальним вмістом зображення

3. **Розрахунок метрики**:
   ```python
   def calculate_alt_text_metric(page_content):
       multimedia_elements = extract_multimedia_elements(page_content)
       meaningful_alt_count = 0
       
       for element in multimedia_elements:
           if has_meaningful_alt_text(element):
               meaningful_alt_count += 1
       
       return meaningful_alt_count / len(multimedia_elements) if multimedia_elements else 0
   ```

### 1.2 Контрастність тексту (UAC-1.1.2-G)

**Формула з статті**: `X = Σ(A × B+) / Σ(A × B)`
- A = рівень контрасту
- B+ = кількість елементів, що задовольняють умови (≥4.5:1 для основного, ≥3:1 для допоміжного)
- B = кількість всіх елементів

**Бібліотеки для використання:**
- `color-contrast-analyzer` - точні розрахунки контрасту
- `colorjs.io` - робота з колірними просторами
- `Beautiful Soup` - витягування стилів
- `Playwright` - отримання computed styles

**План імплементації:**
1. **Збір кольорових даних**:
   - Витягти всі текстові елементи
   - Отримати computed styles (color, background-color)
   - Врахувати градієнти, зображення як фон
   - Ідентифікувати розмір тексту (основний/допоміжний)

2. **Розрахунок контрасту**:
   ```python
   def calculate_contrast_ratio(foreground_color, background_color):
       # Використання WCAG формули
       luminance1 = get_relative_luminance(foreground_color)
       luminance2 = get_relative_luminance(background_color)
       
       lighter = max(luminance1, luminance2)
       darker = min(luminance1, luminance2)
       
       return (lighter + 0.05) / (darker + 0.05)
   
   def calculate_contrast_metric(page_elements):
       total_weighted_score = 0
       total_elements = 0
       
       for element in page_elements:
           contrast_ratio = calculate_contrast_ratio(
               element.text_color, 
               element.background_color
           )
           
           required_ratio = 4.5 if element.is_normal_text else 3.0
           meets_requirement = 1 if contrast_ratio >= required_ratio else 0
           
           total_weighted_score += contrast_ratio * meets_requirement
           total_elements += contrast_ratio
       
       return total_weighted_score / total_elements if total_elements > 0 else 0
   ```

### 1.3 Субтитри та аудіоописи (UAC-1.1.3-G)

**Формула з статті**: `X = A / B`
- A = кількість відео із субтитрами або аудіоописами
- B = загальна кількість відео

**Бібліотеки для використання:**
- `Beautiful Soup` - пошук video/audio елементів
- `axe-core` - перевірка accessibility features
- `requests` - перевірка наявності subtitle файлів

**План імплементації:**
1. **Ідентифікація медіа контенту**:
   - Знайти всі `<video>`, `<audio>` елементи
   - Перевірити `<track>` елементи з kind="subtitles" або "captions"
   - Шукати посилання на .srt, .vtt файли
   - Перевірити aria-describedby для аудіоописів

2. **Розрахунок метрики**:
   ```python
   def calculate_media_accessibility_metric(page_content):
       media_elements = extract_media_elements(page_content)
       accessible_media_count = 0
       
       for media in media_elements:
           if has_subtitles_or_captions(media) or has_audio_description(media):
               accessible_media_count += 1
       
       return accessible_media_count / len(media_elements) if media_elements else 1
   ```

## 2. КЕРОВАНІСТЬ (UAC-1.2-G)

### 2.1 Навігація з клавіатури (UAC-1.2.1-G)

**Формула з статті**: `X = A / B`
- A = кількість інтерактивних елементів, доступних для керування клавіатурою
- B = загальна кількість інтерактивних елементів

**Бібліотеки для використання:**
- `Playwright` - симуляція клавіатурної навігації
- `axe-core` - перевірка keyboard accessibility
- `Beautiful Soup` - аналіз tabindex та focusable елементів

**План імплементації:**
1. **Ідентифікація інтерактивних елементів**:
   - Знайти всі `<button>`, `<a>`, `<input>`, `<select>`, `<textarea>`
   - Елементи з `tabindex`, `onclick`, `role="button"`
   - Кастомні інтерактивні елементи

2. **Тестування клавіатурної доступності**:
   ```python
   async def test_keyboard_navigation(page):
       interactive_elements = await page.query_selector_all(
           'button, a, input, select, textarea, [tabindex], [onclick], [role="button"]'
       )
       
       accessible_count = 0
       
       for element in interactive_elements:
           # Перевірка чи можна сфокусуватися
           try:
               await element.focus()
               is_focused = await page.evaluate('document.activeElement === arguments[0]', element)
               
               # Перевірка чи можна активувати клавіатурою
               if is_focused:
                   # Тест Enter та Space
                   can_activate = await test_keyboard_activation(page, element)
                   if can_activate:
                       accessible_count += 1
           except:
               continue
       
       return accessible_count / len(interactive_elements) if interactive_elements else 1
   ```

### 2.2 Структурована навігація (UAC-1.2.2-G)

**Формули з статті**:
- Для глибоких рівнів: `X = 0.5 × A + 0.5 × (1 - B/C)`
- Для кореневих рівнів: `X = 1 - B/C`

Де:
- A = наявність хлібних крихт (1 або 0)
- B = кількість пропущених рівнів заголовків
- C = загальна кількість заголовків

**Бібліотеки для використання:**
- `Beautiful Soup` - аналіз структури заголовків
- `axe-core` - перевірка heading hierarchy
- `html5lib` - валідація HTML5 структури

**План імплементації:**
1. **Аналіз хлібних крихт**:
   ```python
   def has_breadcrumbs(page_content):
       # Шукаємо типові паттерни breadcrumbs
       breadcrumb_selectors = [
           '[aria-label*="breadcrumb"]',
           '.breadcrumb',
           '.breadcrumbs',
           'nav ol',
           '[role="navigation"] ol'
       ]
       
       soup = BeautifulSoup(page_content, 'html.parser')
       for selector in breadcrumb_selectors:
           if soup.select(selector):
               return True
       return False
   ```

2. **Аналіз ієрархії заголовків**:
   ```python
   def analyze_heading_structure(page_content):
       soup = BeautifulSoup(page_content, 'html.parser')
       headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
       
       if not headings:
           return 0, 0
       
       heading_levels = []
       for heading in headings:
           level = int(heading.name[1])
           heading_levels.append(level)
       
       # Підрахунок пропущених рівнів
       skipped_levels = 0
       for i in range(1, len(heading_levels)):
           current_level = heading_levels[i]
           previous_level = heading_levels[i-1]
           
           if current_level > previous_level + 1:
               skipped_levels += current_level - previous_level - 1
       
       return skipped_levels, len(headings)
   
   def calculate_structured_navigation_metric(page_content, page_depth):
       has_breadcrumb = has_breadcrumbs(page_content)
       skipped_levels, total_headings = analyze_heading_structure(page_content)
       
       if total_headings == 0:
           return 0
       
       heading_score = 1 - (skipped_levels / total_headings)
       
       if page_depth > 2:  # Глибокий рівень
           return 0.5 * (1 if has_breadcrumb else 0) + 0.5 * heading_score
       else:  # Кореневий рівень
           return heading_score
   ```

## 3. ЗРОЗУМІЛІСТЬ (UAC-1.3-G)

### 3.1 Зрозумілі інструкції (UAC-1.3.1-G)

**Формула з статті**: `X = A / B`
- A = кількість інструкцій, оцінених як зрозумілі
- B = загальна кількість інструкцій

**Бібліотеки для використання:**
- `textstat` - аналіз складності тексту
- `spaCy` - NLP аналіз
- `Beautiful Soup` - пошук інструкцій у формах
- `NLTK` - лінгвістичний аналіз

**План імплементації:**
1. **Ідентифікація інструкцій**:
   ```python
   def extract_instructions(page_content):
       soup = BeautifulSoup(page_content, 'html.parser')
       
       instructions = []
       
       # Шукаємо labels, help text, placeholders
       instruction_selectors = [
           'label',
           '.help-text',
           '.instruction',
           '[aria-describedby]',
           'small',
           '.form-help'
       ]
       
       for selector in instruction_selectors:
           elements = soup.select(selector)
           for element in elements:
               text = element.get_text().strip()
               if text and len(text) > 5:  # Фільтруємо короткі тексти
                   instructions.append(text)
       
       # Також шукаємо placeholder тексти
       inputs_with_placeholders = soup.find_all('input', placeholder=True)
       for input_elem in inputs_with_placeholders:
           placeholder = input_elem.get('placeholder', '').strip()
           if placeholder:
               instructions.append(placeholder)
       
       return instructions
   ```

2. **Оцінка зрозумілості**:
   ```python
   def assess_instruction_clarity(instruction_text):
       # Використовуємо кілька метрик
       flesch_score = textstat.flesch_reading_ease(instruction_text)
       gunning_fog = textstat.gunning_fog(instruction_text)
       sentence_count = textstat.sentence_count(instruction_text)
       word_count = textstat.lexicon_count(instruction_text)
       
       # Критерії зрозумілості
       is_clear = (
           flesch_score >= 60 and  # Достатньо легкий для читання
           gunning_fog <= 12 and   # Не занадто складний
           word_count <= 20 and    # Не занадто довгий
           sentence_count <= 2     # Не більше 2 речень
       )
       
       return is_clear
   
   def calculate_instruction_clarity_metric(page_content):
       instructions = extract_instructions(page_content)
       
       if not instructions:
           return 1  # Немає інструкцій = немає проблем
       
       clear_instructions = 0
       for instruction in instructions:
           if assess_instruction_clarity(instruction):
               clear_instructions += 1
       
       return clear_instructions / len(instructions)
   ```

### 3.2 Допомога при введенні даних (UAC-1.3.2-G)

**Формула з статті**: `X = A / B`
- A = кількість полів із функціями автозаповнення чи підказок
- B = загальна кількість полів

**Бібліотеки для використання:**
- `Beautiful Soup` - аналіз форм та полів
- `axe-core` - перевірка accessibility features

**План імплементації:**
```python
def calculate_input_assistance_metric(page_content):
    soup = BeautifulSoup(page_content, 'html.parser')
    
    # Знаходимо всі поля введення
    input_fields = soup.find_all(['input', 'textarea', 'select'])
    
    if not input_fields:
        return 1  # Немає полів = немає проблем
    
    assisted_fields = 0
    
    for field in input_fields:
        has_assistance = (
            field.get('autocomplete') or  # Автозаповнення
            field.get('placeholder') or   # Підказка
            field.get('aria-describedby') or  # Опис
            field.get('list') or          # Datalist
            field.get('pattern') or       # Паттерн валідації
            field.get('title')            # Підказка в title
        )
        
        if has_assistance:
            assisted_fields += 1
    
    return assisted_fields / len(input_fields)
```

### 3.3 Підтримка коректного введення (UAC-1.3.3-G)

**Формула з статті**: `X = A / B`
- A = кількість форм із повідомленнями про помилки
- B = загальна кількість форм

**План імплементації:**
```python
def calculate_error_support_metric(page_content):
    soup = BeautifulSoup(page_content, 'html.parser')
    
    forms = soup.find_all('form')
    
    if not forms:
        return 1  # Немає форм = немає проблем
    
    forms_with_error_support = 0
    
    for form in forms:
        has_error_support = (
            form.find(class_=re.compile(r'error|invalid|warning')) or
            form.find('[aria-invalid]') or
            form.find('[role="alert"]') or
            form.select('[aria-describedby*="error"]') or
            form.get('novalidate') is None  # HTML5 валідація увімкнена
        )
        
        if has_error_support:
            forms_with_error_support += 1
    
    return forms_with_error_support / len(forms)
```

## 4. ЛОКАЛІЗАЦІЯ (UAC-2.1-S)

**Формула з статті**: `X = K1×A + K2×B + K3×C + K4×D`

Де для українського контексту:
- K1 = 0.6 (українська мова)
- K2 = 0.2 (англійська мова)  
- K3 = 0.08 (німецька/французька)
- K4 = 0.04 (інші мови)

**Бібліотеки для використання:**
- `langdetect` - визначення мови контенту
- `Beautiful Soup` - аналіз lang атрибутів
- `requests` - перевірка наявності мовних версій

**План імплементації:**
```python
def calculate_localization_metric(page_content, base_url):
    soup = BeautifulSoup(page_content, 'html.parser')
    
    # Визначаємо доступні мови
    available_languages = detect_available_languages(soup, base_url)
    
    # Вагові коефіцієнти для українського контексту
    weights = {
        'uk': 0.6,   # Українська
        'en': 0.2,   # Англійська
        'de': 0.08,  # Німецька
        'fr': 0.08,  # Французька
        'other': 0.04  # Інші мови
    }
    
    score = 0
    
    # Перевіряємо наявність кожної мови
    if 'uk' in available_languages:
        score += weights['uk']
    if 'en' in available_languages:
        score += weights['en']
    if any(lang in available_languages for lang in ['de', 'fr']):
        score += weights['de']  # Один з європейських
    
    # Додаємо бонус за інші мови
    other_languages = set(available_languages) - {'uk', 'en', 'de', 'fr'}
    if other_languages:
        score += weights['other']
    
    return min(score, 1.0)  # Максимум 1.0

def detect_available_languages(soup, base_url):
    languages = set()
    
    # Перевіряємо lang атрибут
    html_lang = soup.find('html')
    if html_lang and html_lang.get('lang'):
        languages.add(html_lang.get('lang')[:2])
    
    # Шукаємо language switcher
    lang_links = soup.find_all('a', href=re.compile(r'/(uk|en|de|fr|ru)/'))
    for link in lang_links:
        href = link.get('href', '')
        match = re.search(r'/(uk|en|de|fr|ru)/', href)
        if match:
            languages.add(match.group(1))
    
    # Перевіряємо hreflang
    hreflang_links = soup.find_all('link', rel='alternate', hreflang=True)
    for link in hreflang_links:
        lang = link.get('hreflang')[:2]
        languages.add(lang)
    
    return languages
```

## 5. ЗАГАЛЬНА ІНТЕГРАЦІЯ ТА РОЗРАХУНОК ФІНАЛЬНОГО СКОРУ

### 5.1 Головний клас для розрахунку всіх метрик

```python
class AccessibilityEvaluator:
    def __init__(self):
        self.weights = {
            'perceptibility': 0.3,
            'operability': 0.3, 
            'understandability': 0.4,
            'localization': 0.4
        }
        
        self.metric_weights = {
            'alt_text': 0.15,
            'contrast': 0.15,
            'media_accessibility': 0.15,
            'keyboard_navigation': 0.05,
            'structured_navigation': 0.05,
            'instruction_clarity': 0.1,
            'input_assistance': 0.1,
            'error_support': 0.1,
            'localization': 0.15
        }
    
    async def evaluate_accessibility(self, url):
        # Ініціалізація браузера
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(url)
            
            # Отримання контенту
            content = await page.content()
            
            # Розрахунок всіх метрик
            metrics = await self.calculate_all_metrics(page, content, url)
            
            # Розрахунок підскорів
            subscores = self.calculate_subscores(metrics)
            
            # Фінальний скор
            final_score = self.calculate_final_score(subscores)
            
            await browser.close()
            
            return {
                'metrics': metrics,
                'subscores': subscores,
                'final_score': final_score,
                'recommendations': self.generate_recommendations(metrics)
            }
    
    async def calculate_all_metrics(self, page, content, url):
        return {
            # Перцептивність
            'alt_text': calculate_alt_text_metric(content),
            'contrast': await calculate_contrast_metric(page),
            'media_accessibility': calculate_media_accessibility_metric(content),
            
            # Керованість
            'keyboard_navigation': await test_keyboard_navigation(page),
            'structured_navigation': calculate_structured_navigation_metric(
                content, self.get_page_depth(url)
            ),
            
            # Зрозумілість
            'instruction_clarity': calculate_instruction_clarity_metric(content),
            'input_assistance': calculate_input_assistance_metric(content),
            'error_support': calculate_error_support_metric(content),
            
            # Локалізація
            'localization': calculate_localization_metric(content, url)
        }
    
    def calculate_subscores(self, metrics):
        return {
            'perceptibility': (
                metrics['alt_text'] * 0.5 +
                metrics['contrast'] * 0.5 +
                metrics['media_accessibility'] * 0.4
            ) / 1.4,
            
            'operability': (
                metrics['keyboard_navigation'] * 0.6 +
                metrics['structured_navigation'] * 0.4
            ),
            
            'understandability': (
                metrics['instruction_clarity'] * 0.4 +
                metrics['input_assistance'] * 0.3 +
                metrics['error_support'] * 0.3
            ),
            
            'localization': metrics['localization']
        }
    
    def calculate_final_score(self, subscores):
        # Формула з наукової статті
        main_score = (
            0.3 * subscores['perceptibility'] +
            0.3 * subscores['operability'] +
            0.4 * subscores['understandability']
        )
        
        return 0.6 * main_score + 0.4 * subscores['localization']
```

### 5.2 Система рекомендацій

```python
def generate_recommendations(self, metrics):
    recommendations = []
    
    # Рекомендації для альтернативного тексту
    if metrics['alt_text'] < 0.8:
        recommendations.append({
            'category': 'Перцептивність',
            'issue': 'Недостатньо альтернативного тексту',
            'recommendation': 'Додайте змістовні alt атрибути до всіх зображень',
            'priority': 'Високий',
            'wcag_reference': 'WCAG 1.1.1'
        })
    
    # Рекомендації для контрасту
    if metrics['contrast'] < 0.7:
        recommendations.append({
            'category': 'Перцептивність',
            'issue': 'Низький контраст тексту',
            'recommendation': 'Підвищте контраст до мінімум 4.5:1 для основного тексту',
            'priority': 'Високий',
            'wcag_reference': 'WCAG 1.4.3'
        })
    
    # Рекомендації для клавіатурної навігації
    if metrics['keyboard_navigation'] < 0.9:
        recommendations.append({
            'category': 'Керованість',
            'issue': 'Проблеми з клавіатурною навігацією',
            'recommendation': 'Забезпечте доступність всіх інтерактивних елементів через клавіатуру',
            'priority': 'Високий',
            'wcag_reference': 'WCAG 2.1.1'
        })
    
    return recommendations
```

## 6. ЕТАПИ ІМПЛЕМЕНТАЦІЇ

### Етап 1: Базова інфраструктура (1-2 тижні)
1. **Налаштування проекту**:
   - Створення структури папок
   - Встановлення залежностей
   - Налаштування тестового середовища

2. **Базові утиліти**:
   - Web scraper з Playwright
   - HTML парсер з Beautiful Soup
   - Базовий клас для метрик

### Етап 2: Метрики перцептивності (2-3 тижні)
1. **Альтернативний текст**:
   - Імплементація пошуку мультимедіа
   - Аналіз якості alt-тексту
   - Інтеграція з AI сервісами

2. **Контраст кольорів**:
   - Витягування кольорів з CSS
   - Розрахунок контрасту за WCAG
   - Обробка складних випадків (градієнти, зображення)

3. **Медіа доступність**:
   - Пошук відео/аудіо елементів
   - Перевірка субтитрів
   - Аналіз аудіоописів

### Етап 3: Метрики керованості (1-2 тижні)
1. **Клавіатурна навігація**:
   - Автоматизоване тестування з Playwright
   - Симуляція клавіатурних подій
   - Перевірка focus management

2. **Структурована навігація**:
   - Аналіз ієрархії заголовків
   - Пошук breadcrumbs
   - Розрахунок складних формул

### Етап 4: Метрики зрозумілості (2-3 тижні)
1. **Аналіз тексту**:
   - Інтеграція з textstat та spaCy
   - Оцінка складності інструкцій
   - NLP обробка українського тексту

2. **Форми та помилки**:
   - Аналіз полів введення
   - Перевірка валідації
   - Пошук error handling

### Етап 5: Локалізація (1 тиждень)
1. **Визначення мов**:
   - Аналіз lang атрибутів
   - Пошук мовних перемикачів
   - Перевірка hreflang

### Етап 6: Інтеграція та тестування (2-3 тижні)
1. **Загальний калькулятор**:
   - Об'єднання всіх метрик
   - Розрахунок фінального скору
   - Система рекомендацій

2. **Веб-інтерфейс**:
   - FastAPI backend
   - React frontend
   - Візуалізація результатів

### Етап 7: Оптимізація та документація (1-2 тижні)
1. **Продуктивність**:
   - Кешування результатів
   - Асинхронна обробка
   - Оптимізація запитів

2. **Документація**:
   - API документація
   - Інструкції користувача
   - Технічна документація

## 7. ТЕСТУВАННЯ ТА ВАЛІДАЦІЯ

### 7.1 Unit тести
```python
# Приклад тестів для кожної метрики
def test_alt_text_calculation():
    html_content = """
    <img src="test.jpg" alt="Meaningful description">
    <img src="test2.jpg" alt="">
    <img src="test3.jpg">
    """
    result = calculate_alt_text_metric(html_content)
    assert result == 1/3  # Тільки одне зображення має змістовний alt
```

### 7.2 Інтеграційні тести
- Тестування на реальних вебсайтах
- Порівняння з результатами інших інструментів
- Валідація відповідно до WCAG guidelines

### 7.3 Продуктивність
- Бенчмарки швидкості аналізу
- Тести навантаження
- Оптимізація для великих сайтів

Цей план забезпечує поетапну імплементацію всіх метрик з наукової статті з використанням сучасних бібліотек та інструментів.