/**
 * Мінімальний Background Service Worker для Accessibility Evaluator
 * Тепер popup використовує Flask API, тому background script спрощено
 */

class AccessibilityBackground {
    constructor() {
        this.init();
    }

    init() {
        this.setupInstallHandler();
        console.log('✅ Accessibility Evaluator background script ініціалізовано');
    }

    setupInstallHandler() {
        chrome.runtime.onInstalled.addListener((details) => {
            console.log('📦 Розширення встановлено/оновлено:', details.reason);
            
            if (details.reason === 'install') {
                this.handleFirstInstall();
            } else if (details.reason === 'update') {
                this.handleUpdate(details.previousVersion);
            }
        });
    }

    handleFirstInstall() {
        console.log('🎉 Перше встановлення Accessibility Evaluator');
        
        // Встановлюємо початкові налаштування
        chrome.storage.sync.set({
            settings: {
                apiUrl: 'http://localhost:8001',
                detailedReports: true,
                language: 'uk',
                version: chrome.runtime.getManifest().version
            }
        }).then(() => {
            console.log('⚙️ Початкові налаштування збережено');
        }).catch(error => {
            console.error('❌ Помилка збереження налаштувань:', error);
        });
    }

    handleUpdate(previousVersion) {
        const currentVersion = chrome.runtime.getManifest().version;
        console.log(`🔄 Оновлено з версії ${previousVersion} до ${currentVersion}`);
        
        // Оновлюємо версію в налаштуваннях
        chrome.storage.sync.set({
            'settings.version': currentVersion
        });
    }
}

// Ініціалізація background script
try {
    new AccessibilityBackground();
} catch (error) {
    console.error('❌ Помилка ініціалізації background script:', error);
}