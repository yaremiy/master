/**
 * Perceptibility Metrics - Метрики сприйнятності
 * Портовано з Python коду з повним збереженням логіки
 */

class PerceptibilityMetrics extends BaseMetrics {
    constructor() {
        super();
        this.metricName = 'perceptibility';
    }

    /**
     * Розрахунок загальної метрики сприйнятності
     */
    async calculateMetric(pageData) {
        this.helpers.log('🔍 Розрахунок метрики сприйнятності...');

        const metrics = {
            imageAlternatives: await this.calculateImageAlternatives(pageData),
            textContrast: await this.calculateTextContrast(pageData),
            mediaAlternatives: await this.calculateMediaAlternatives(pageData),
            colorUsage: await this.calculateColorUsage(pageData)
        };

        // Вагові коефіцієнти для підметрик
        const weights = {
            imageAlternatives: 0.4,  // 40% - найважливіше
            textContrast: 0.35,      // 35% - дуже важливо
            mediaAlternatives: 0.15, // 15% - менше медіа контенту
            colorUsage: 0.1          // 10% - додаткова перевірка
        };

        let totalScore = 0;
        let totalWeight = 0;

        Object.entries(weights).forEach(([metric, weight]) => {
            if (metrics[metric] !== undefined && metrics[metric] !== null) {
                totalScore += metrics[metric] * weight;
                totalWeight += weight;
            }
        });

        const finalScore = totalWeight > 0 ? totalScore / totalWeight : 1.0;

        this.logResult('Perceptibility', finalScore, 
            `Images: ${(metrics.imageAlternatives * 100).toFixed(1)}%, ` +
            `Contrast: ${(metrics.textContrast * 100).toFixed(1)}%, ` +
            `Media: ${(metrics.mediaAlternatives * 100).toFixed(1)}%`
        );

        return finalScore;
    }

    /**
     * Розрахунок альтернатив для зображень
     */
    async calculateImageAlternatives(pageData) {
        const images = pageData.images.filter(img => this.helpers.isElementVisible(img));
        
        if (images.length === 0) {
            return 1.0; // Немає зображень = немає проблем
        }

        const imageStats = this.gatherElementStats(images, (img) => {
            return this.checkImageAlternative(img);
        });

        return this.calculateSuccessRate(imageStats.passed, imageStats.total);
    }

    /**
     * Перевірка альтернативного тексту для зображення
     */
    checkImageAlternative(img) {
        const alt = img.getAttribute('alt');
        const ariaLabel = img.getAttribute('aria-label');
        const ariaLabelledby = img.getAttribute('aria-labelledby');
        const title = img.getAttribute('title');
        const role = img.getAttribute('role');

        // Декоративні зображення
        if (role === 'presentation' || role === 'none' || alt === '') {
            return this.createCheckResult(true, 'Декоративне зображення правильно позначене', 'info');
        }

        // Зображення з альтернативним текстом
        if (alt && alt.trim() !== '') {
            const altLength = alt.trim().length;
            if (altLength < 5) {
                return this.createCheckResult(false, 'Alt-текст занадто короткий', 'medium', { alt });
            }
            if (altLength > 125) {
                return this.createCheckResult(false, 'Alt-текст занадто довгий', 'low', { alt });
            }
            
            // Перевірка якості alt-тексту
            const qualityIssues = this.checkAltTextQuality(alt);
            if (qualityIssues.length > 0) {
                return this.createCheckResult(false, `Проблеми з якістю alt-тексту: ${qualityIssues.join(', ')}`, 'medium', { alt, issues: qualityIssues });
            }
            
            return this.createCheckResult(true, 'Якісний alt-текст', 'info', { alt });
        }

        // ARIA альтернативи
        if (ariaLabel && ariaLabel.trim() !== '') {
            return this.createCheckResult(true, 'Використовується aria-label', 'info', { ariaLabel });
        }

        if (ariaLabelledby) {
            const labelElement = document.getElementById(ariaLabelledby);
            if (labelElement && labelElement.textContent.trim()) {
                return this.createCheckResult(true, 'Використовується aria-labelledby', 'info', { ariaLabelledby });
            }
        }

        // Title як останній варіант
        if (title && title.trim() !== '') {
            return this.createCheckResult(false, 'Використовується тільки title (недостатньо)', 'medium', { title });
        }

        // Немає альтернативи
        return this.createCheckResult(false, 'Відсутній альтернативний текст', 'high');
    }

    /**
     * Перевірка якості alt-тексту
     */
    checkAltTextQuality(altText) {
        const issues = [];
        const lowerAlt = altText.toLowerCase();

        // Погані практики
        const badPhrases = [
            'image of', 'picture of', 'photo of', 'graphic of',
            'зображення', 'картинка', 'фото', 'малюнок'
        ];

        badPhrases.forEach(phrase => {
            if (lowerAlt.includes(phrase)) {
                issues.push(`містить "${phrase}"`);
            }
        });

        // Файлові розширення
        const fileExtensions = ['.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp'];
        fileExtensions.forEach(ext => {
            if (lowerAlt.includes(ext)) {
                issues.push('містить розширення файлу');
            }
        });

        // Повторювані символи
        if (/(.)\1{3,}/.test(altText)) {
            issues.push('містить повторювані символи');
        }

        return issues;
    }

    /**
     * Розрахунок контрастності тексту
     */
    async calculateTextContrast(pageData) {
        const textElements = this.getTextElements();
        
        if (textElements.length === 0) {
            return 1.0;
        }

        // Обмежуємо кількість елементів для перевірки (продуктивність)
        const elementsToCheck = textElements.slice(0, 50);
        
        const contrastStats = this.gatherElementStats(elementsToCheck, (element) => {
            return this.checkTextContrast(element);
        });

        return this.calculateSuccessRate(contrastStats.passed, contrastStats.total);
    }

    /**
     * Отримання текстових елементів для перевірки контрастності
     */
    getTextElements() {
        const selectors = [
            'p', 'span', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
            'a', 'button', 'label', 'li', 'td', 'th', 'caption',
            'input[type="text"]', 'input[type="email"]', 'textarea'
        ];

        const elements = [];
        selectors.forEach(selector => {
            const found = document.querySelectorAll(selector);
            elements.push(...Array.from(found));
        });

        return elements.filter(el => 
            this.helpers.isElementVisible(el) && 
            this.getElementText(el).length > 0
        );
    }

    /**
     * Перевірка контрастності тексту елемента
     */
    checkTextContrast(element) {
        try {
            const styles = this.getComputedStyles(element);
            const color = styles.color;
            const backgroundColor = this.getEffectiveBackgroundColor(element);
            
            if (!color || !backgroundColor) {
                return this.createCheckResult(false, 'Не вдалося визначити кольори', 'low');
            }

            const contrast = this.helpers.calculateContrast(color, backgroundColor);
            const fontSize = this.helpers.getFontSizeInPixels(element);
            const fontWeight = styles.fontWeight;
            
            // Визначаємо чи текст великий
            const isLargeText = fontSize >= 18 || (fontSize >= 14 && (fontWeight === 'bold' || parseInt(fontWeight) >= 700));
            
            // Мінімальні вимоги контрастності
            const minContrast = isLargeText ? 3.0 : 4.5;  // WCAG AA
            const enhancedContrast = isLargeText ? 4.5 : 7.0;  // WCAG AAA

            if (contrast >= enhancedContrast) {
                return this.createCheckResult(true, `Відмінна контрастність: ${contrast.toFixed(2)}:1`, 'info', 
                    { contrast, fontSize, isLargeText, level: 'AAA' });
            } else if (contrast >= minContrast) {
                return this.createCheckResult(true, `Достатня контрастність: ${contrast.toFixed(2)}:1`, 'info', 
                    { contrast, fontSize, isLargeText, level: 'AA' });
            } else {
                const severity = contrast < minContrast * 0.7 ? 'high' : 'medium';
                return this.createCheckResult(false, `Низька контрастність: ${contrast.toFixed(2)}:1 (потрібно ${minContrast}:1)`, severity,
                    { contrast, fontSize, isLargeText, required: minContrast });
            }

        } catch (error) {
            return this.createCheckResult(false, `Помилка перевірки контрастності: ${error.message}`, 'low');
        }
    }

    /**
     * Отримання ефективного кольору фону (з урахуванням батьківських елементів)
     */
    getEffectiveBackgroundColor(element) {
        let currentElement = element;
        
        while (currentElement && currentElement !== document.body) {
            const styles = this.getComputedStyles(currentElement);
            const bgColor = styles.backgroundColor;
            
            // Якщо фон не прозорий
            if (bgColor && bgColor !== 'rgba(0, 0, 0, 0)' && bgColor !== 'transparent') {
                return bgColor;
            }
            
            currentElement = currentElement.parentElement;
        }
        
        // Якщо не знайдено, використовуємо білий як за замовчуванням
        return 'rgb(255, 255, 255)';
    }

    /**
     * Розрахунок альтернатив для медіа
     */
    async calculateMediaAlternatives(pageData) {
        const videos = pageData.videos || [];
        const audios = pageData.audio || [];
        const allMedia = [...videos, ...audios];

        if (allMedia.length === 0) {
            return 1.0; // Немає медіа = немає проблем
        }

        const mediaStats = this.gatherElementStats(allMedia, (media) => {
            return this.checkMediaAlternatives(media);
        });

        return this.calculateSuccessRate(mediaStats.passed, mediaStats.total);
    }

    /**
     * Перевірка альтернатив для медіа елемента
     */
    checkMediaAlternatives(media) {
        const tagName = media.tagName.toLowerCase();
        
        // Перевірка субтитрів для відео
        if (tagName === 'video') {
            const tracks = media.querySelectorAll('track[kind="captions"], track[kind="subtitles"]');
            if (tracks.length > 0) {
                return this.createCheckResult(true, `Знайдено ${tracks.length} доріжок субтитрів`, 'info');
            }
            
            // Перевірка controls
            if (!media.hasAttribute('controls')) {
                return this.createCheckResult(false, 'Відео без елементів управління', 'medium');
            }
            
            return this.createCheckResult(false, 'Відео без субтитрів', 'high');
        }

        // Перевірка для аудіо
        if (tagName === 'audio') {
            // Перевірка controls
            if (!media.hasAttribute('controls')) {
                return this.createCheckResult(false, 'Аудіо без елементів управління', 'medium');
            }
            
            // Перевірка транскрипції (евристично)
            const parent = media.parentElement;
            const transcript = parent?.querySelector('.transcript, .transcription, [data-transcript]');
            if (transcript) {
                return this.createCheckResult(true, 'Знайдено транскрипцію', 'info');
            }
            
            return this.createCheckResult(false, 'Аудіо без транскрипції', 'medium');
        }

        return this.createCheckResult(true, 'Медіа елемент перевірено', 'info');
    }

    /**
     * Розрахунок використання кольору
     */
    async calculateColorUsage(pageData) {
        // Перевірка чи інформація передається тільки через колір
        const colorOnlyElements = this.findColorOnlyInformation();
        
        if (colorOnlyElements.length === 0) {
            return 1.0; // Немає проблем з кольором
        }

        // Спрощена оцінка - якщо знайдено елементи, що покладаються тільки на колір
        const problematicElements = colorOnlyElements.filter(el => !this.hasNonColorIndicators(el));
        
        return this.calculateSuccessRate(
            colorOnlyElements.length - problematicElements.length,
            colorOnlyElements.length
        );
    }

    /**
     * Пошук елементів, що можуть покладатися тільки на колір
     */
    findColorOnlyInformation() {
        const suspiciousElements = [];
        
        // Шукаємо елементи з кольоровими класами
        const colorClasses = [
            'red', 'green', 'blue', 'yellow', 'orange', 'purple',
            'success', 'error', 'warning', 'danger', 'info',
            'valid', 'invalid', 'required', 'optional'
        ];

        colorClasses.forEach(colorClass => {
            const elements = document.querySelectorAll(`[class*="${colorClass}"]`);
            suspiciousElements.push(...Array.from(elements));
        });

        // Шукаємо елементи з inline стилями кольорів
        const styledElements = document.querySelectorAll('[style*="color"]');
        suspiciousElements.push(...Array.from(styledElements));

        return suspiciousElements.filter(el => this.helpers.isElementVisible(el));
    }

    /**
     * Перевірка чи елемент має не-кольорові індикатори
     */
    hasNonColorIndicators(element) {
        // Перевірка тексту
        const text = this.getElementText(element);
        const indicatorWords = [
            'required', 'optional', 'error', 'success', 'warning',
            'обов\'язково', 'помилка', 'успіх', 'попередження',
            '*', '!', '✓', '✗', '⚠'
        ];

        if (indicatorWords.some(word => text.toLowerCase().includes(word.toLowerCase()))) {
            return true;
        }

        // Перевірка іконок
        const icons = element.querySelectorAll('i, .icon, [class*="icon"], svg');
        if (icons.length > 0) {
            return true;
        }

        // Перевірка ARIA атрибутів
        if (element.getAttribute('aria-label') || 
            element.getAttribute('aria-describedby') ||
            element.getAttribute('title')) {
            return true;
        }

        return false;
    }

    /**
     * Детальний аналіз для UI
     */
    async getDetailedAnalysis(pageData) {
        const analysis = {
            images: await this.analyzeImages(pageData),
            contrast: await this.analyzeContrast(pageData),
            media: await this.analyzeMedia(pageData),
            colorUsage: await this.analyzeColorUsage(pageData)
        };

        return analysis;
    }

    async analyzeImages(pageData) {
        const images = pageData.images.filter(img => this.helpers.isElementVisible(img));
        const results = {
            total: images.length,
            withAlt: 0,
            decorative: 0,
            problematic: [],
            good: []
        };

        images.forEach(img => {
            const check = this.checkImageAlternative(img);
            const selector = this.helpers.generateSelector(img);
            
            if (check.passed) {
                results.good.push({
                    selector,
                    message: check.message,
                    data: check.data
                });
                
                if (img.getAttribute('alt') === '') {
                    results.decorative++;
                } else {
                    results.withAlt++;
                }
            } else {
                results.problematic.push({
                    selector,
                    message: check.message,
                    severity: check.severity,
                    data: check.data
                });
            }
        });

        return results;
    }

    async analyzeContrast(pageData) {
        const textElements = this.getTextElements().slice(0, 30); // Обмежуємо для продуктивності
        const results = {
            total: textElements.length,
            aaa: 0,
            aa: 0,
            failed: 0,
            problematic: []
        };

        textElements.forEach(element => {
            const check = this.checkTextContrast(element);
            const selector = this.helpers.generateSelector(element);
            
            if (check.passed) {
                if (check.data?.level === 'AAA') {
                    results.aaa++;
                } else {
                    results.aa++;
                }
            } else {
                results.failed++;
                results.problematic.push({
                    selector,
                    message: check.message,
                    severity: check.severity,
                    data: check.data
                });
            }
        });

        return results;
    }

    async analyzeMedia(pageData) {
        const videos = pageData.videos || [];
        const audios = pageData.audio || [];
        
        return {
            videos: {
                total: videos.length,
                withCaptions: videos.filter(v => v.querySelectorAll('track').length > 0).length,
                withControls: videos.filter(v => v.hasAttribute('controls')).length
            },
            audio: {
                total: audios.length,
                withControls: audios.filter(a => a.hasAttribute('controls')).length
            }
        };
    }

    async analyzeColorUsage(pageData) {
        const colorOnlyElements = this.findColorOnlyInformation();
        const problematic = colorOnlyElements.filter(el => !this.hasNonColorIndicators(el));
        
        return {
            total: colorOnlyElements.length,
            problematic: problematic.length,
            issues: problematic.map(el => ({
                selector: this.helpers.generateSelector(el),
                message: 'Інформація може передаватися тільки через колір'
            }))
        };
    }
}

// Експортуємо для використання
window.PerceptibilityMetrics = PerceptibilityMetrics;