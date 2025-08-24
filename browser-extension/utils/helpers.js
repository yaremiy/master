/**
 * Допоміжні функції для Accessibility Evaluator
 * Портовані з Python коду
 */

class AccessibilityHelpers {
    /**
     * Розрахунок контрастності між двома кольорами
     */
    static calculateContrast(color1, color2) {
        const rgb1 = this.parseColor(color1);
        const rgb2 = this.parseColor(color2);
        
        const l1 = this.getLuminance(rgb1);
        const l2 = this.getLuminance(rgb2);
        
        const lighter = Math.max(l1, l2);
        const darker = Math.min(l1, l2);
        
        return (lighter + 0.05) / (darker + 0.05);
    }

    /**
     * Парсинг кольору з різних форматів
     */
    static parseColor(color) {
        if (!color) return { r: 255, g: 255, b: 255 };
        
        // RGB/RGBA
        const rgbMatch = color.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
        if (rgbMatch) {
            return {
                r: parseInt(rgbMatch[1]),
                g: parseInt(rgbMatch[2]),
                b: parseInt(rgbMatch[3])
            };
        }
        
        // HEX
        const hexMatch = color.match(/^#([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i);
        if (hexMatch) {
            return {
                r: parseInt(hexMatch[1], 16),
                g: parseInt(hexMatch[2], 16),
                b: parseInt(hexMatch[3], 16)
            };
        }
        
        // Короткий HEX
        const shortHexMatch = color.match(/^#([a-f\d])([a-f\d])([a-f\d])$/i);
        if (shortHexMatch) {
            return {
                r: parseInt(shortHexMatch[1] + shortHexMatch[1], 16),
                g: parseInt(shortHexMatch[2] + shortHexMatch[2], 16),
                b: parseInt(shortHexMatch[3] + shortHexMatch[3], 16)
            };
        }
        
        // Іменовані кольори
        const namedColors = {
            'white': { r: 255, g: 255, b: 255 },
            'black': { r: 0, g: 0, b: 0 },
            'red': { r: 255, g: 0, b: 0 },
            'green': { r: 0, g: 128, b: 0 },
            'blue': { r: 0, g: 0, b: 255 }
        };
        
        return namedColors[color.toLowerCase()] || { r: 255, g: 255, b: 255 };
    }

    /**
     * Розрахунок відносної яскравості
     */
    static getLuminance(rgb) {
        const { r, g, b } = rgb;
        
        const rsRGB = r / 255;
        const gsRGB = g / 255;
        const bsRGB = b / 255;
        
        const rLinear = rsRGB <= 0.03928 ? rsRGB / 12.92 : Math.pow((rsRGB + 0.055) / 1.055, 2.4);
        const gLinear = gsRGB <= 0.03928 ? gsRGB / 12.92 : Math.pow((gsRGB + 0.055) / 1.055, 2.4);
        const bLinear = bsRGB <= 0.03928 ? bsRGB / 12.92 : Math.pow((bsRGB + 0.055) / 1.055, 2.4);
        
        return 0.2126 * rLinear + 0.7152 * gLinear + 0.0722 * bLinear;
    }

    /**
     * Перевірка чи елемент видимий
     */
    static isElementVisible(element) {
        if (!element) return false;
        
        const style = window.getComputedStyle(element);
        
        return style.display !== 'none' &&
               style.visibility !== 'hidden' &&
               style.opacity !== '0' &&
               element.offsetParent !== null;
    }

    /**
     * Отримання всіх текстових вузлів елемента
     */
    static getTextNodes(element) {
        const textNodes = [];
        const walker = document.createTreeWalker(
            element,
            NodeFilter.SHOW_TEXT,
            null,
            false
        );
        
        let node;
        while (node = walker.nextNode()) {
            if (node.textContent.trim()) {
                textNodes.push(node);
            }
        }
        
        return textNodes;
    }

    /**
     * Генерація унікального селектора для елемента
     */
    static generateSelector(element) {
        if (!element) return '';
        
        // ID селектор
        if (element.id) {
            return `#${element.id}`;
        }
        
        // Клас селектор
        if (element.className && typeof element.className === 'string') {
            const classes = element.className.split(' ').filter(c => c.trim());
            if (classes.length > 0) {
                return `.${classes[0]}`;
            }
        }
        
        // Тег + позиція
        const tagName = element.tagName.toLowerCase();
        const parent = element.parentElement;
        
        if (!parent) return tagName;
        
        const siblings = Array.from(parent.children).filter(el => el.tagName === element.tagName);
        const index = siblings.indexOf(element);
        
        if (siblings.length > 1) {
            return `${tagName}:nth-of-type(${index + 1})`;
        }
        
        return tagName;
    }

    /**
     * Перевірка чи елемент є інтерактивним
     */
    static isInteractiveElement(element) {
        const interactiveTags = ['a', 'button', 'input', 'select', 'textarea', 'details', 'summary'];
        const tagName = element.tagName.toLowerCase();
        
        if (interactiveTags.includes(tagName)) {
            return true;
        }
        
        // Елементи з tabindex
        if (element.hasAttribute('tabindex')) {
            return true;
        }
        
        // Елементи з event listeners
        const hasClickHandler = element.onclick || 
                               element.getAttribute('onclick') ||
                               element.style.cursor === 'pointer';
        
        return hasClickHandler;
    }

    /**
     * Отримання доступного імені елемента
     */
    static getAccessibleName(element) {
        // aria-label
        if (element.getAttribute('aria-label')) {
            return element.getAttribute('aria-label');
        }
        
        // aria-labelledby
        const labelledBy = element.getAttribute('aria-labelledby');
        if (labelledBy) {
            const labelElement = document.getElementById(labelledBy);
            if (labelElement) {
                return labelElement.textContent.trim();
            }
        }
        
        // label for
        if (element.id) {
            const label = document.querySelector(`label[for="${element.id}"]`);
            if (label) {
                return label.textContent.trim();
            }
        }
        
        // label wrapper
        const parentLabel = element.closest('label');
        if (parentLabel) {
            return parentLabel.textContent.trim();
        }
        
        // title
        if (element.title) {
            return element.title;
        }
        
        // alt для зображень
        if (element.tagName.toLowerCase() === 'img' && element.alt) {
            return element.alt;
        }
        
        // текстовий контент
        if (element.textContent && element.textContent.trim()) {
            return element.textContent.trim();
        }
        
        return '';
    }

    /**
     * Перевірка чи елемент має фокус
     */
    static isFocusable(element) {
        if (!element) return false;
        
        const focusableTags = ['input', 'select', 'textarea', 'button', 'a'];
        const tagName = element.tagName.toLowerCase();
        
        // Природно фокусовані елементи
        if (focusableTags.includes(tagName)) {
            return !element.disabled && !element.hasAttribute('aria-hidden');
        }
        
        // Елементи з tabindex
        const tabindex = element.getAttribute('tabindex');
        if (tabindex !== null) {
            return parseInt(tabindex) >= 0;
        }
        
        return false;
    }

    /**
     * Симуляція натискання клавіші
     */
    static simulateKeyPress(element, key, options = {}) {
        const event = new KeyboardEvent('keydown', {
            key: key,
            code: key,
            keyCode: this.getKeyCode(key),
            which: this.getKeyCode(key),
            bubbles: true,
            cancelable: true,
            ...options
        });
        
        element.dispatchEvent(event);
        return event;
    }

    /**
     * Отримання коду клавіші
     */
    static getKeyCode(key) {
        const keyCodes = {
            'Tab': 9,
            'Enter': 13,
            'Escape': 27,
            'Space': 32,
            'ArrowLeft': 37,
            'ArrowUp': 38,
            'ArrowRight': 39,
            'ArrowDown': 40
        };
        
        return keyCodes[key] || key.charCodeAt(0);
    }

    /**
     * Затримка виконання
     */
    static async delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    /**
     * Debounce функція
     */
    static debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    /**
     * Перевірка чи елемент в viewport
     */
    static isInViewport(element) {
        const rect = element.getBoundingClientRect();
        return (
            rect.top >= 0 &&
            rect.left >= 0 &&
            rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
            rect.right <= (window.innerWidth || document.documentElement.clientWidth)
        );
    }

    /**
     * Отримання розміру шрифту в пікселях
     */
    static getFontSizeInPixels(element) {
        const fontSize = window.getComputedStyle(element).fontSize;
        return parseFloat(fontSize);
    }

    /**
     * Конвертація em/rem в пікселі
     */
    static convertToPixels(value, element) {
        if (typeof value === 'number') return value;
        
        const match = value.match(/^([\d.]+)(px|em|rem|%)$/);
        if (!match) return 0;
        
        const num = parseFloat(match[1]);
        const unit = match[2];
        
        switch (unit) {
            case 'px':
                return num;
            case 'em':
                return num * this.getFontSizeInPixels(element);
            case 'rem':
                return num * this.getFontSizeInPixels(document.documentElement);
            case '%':
                return num / 100 * this.getFontSizeInPixels(element.parentElement || element);
            default:
                return 0;
        }
    }

    /**
     * Логування з timestamp
     */
    static log(message, level = 'info') {
        const timestamp = new Date().toISOString();
        const prefix = `[AccessibilityEvaluator ${timestamp}]`;
        
        switch (level) {
            case 'error':
                console.error(prefix, message);
                break;
            case 'warn':
                console.warn(prefix, message);
                break;
            case 'debug':
                console.debug(prefix, message);
                break;
            default:
                console.log(prefix, message);
        }
    }
}

// Експортуємо для використання в інших модулях
window.AccessibilityHelpers = AccessibilityHelpers;