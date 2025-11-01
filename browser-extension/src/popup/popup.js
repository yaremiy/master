/**
 * Popup JavaScript для Accessibility Evaluator
 * Використовує Flask API для аналізу доступності
 */

class AccessibilityPopup {
  constructor() {
    this.isAnalyzing = false;
    this.currentResults = null;
    this.originalApiResults = null; // Зберігаємо оригінальний формат API для /api/report
    this.API_BASE_URL = "http://localhost:8001"; // Flask сервер
    this.init();
  }

  async init() {
    await this.initSettings();
    await this.cleanupOldResults();
    this.bindEvents();
    this.loadPreviousResults();
    this.checkServerStatus();
  }

  /**
   * Очищає старі результати при зміні структури даних
   */
  async cleanupOldResults() {
    try {
      const { dataVersion } = await chrome.storage.local.get("dataVersion");
      const CURRENT_VERSION = 2; // Інкрементуй при зміні структури

      if (dataVersion !== CURRENT_VERSION) {
        console.log("🧹 Очищення старих результатів (зміна структури даних)");
        await chrome.storage.local.clear();
        await chrome.storage.local.set({ dataVersion: CURRENT_VERSION });
      }
    } catch (error) {
      console.error("Помилка очищення:", error);
    }
  }

  /**
   * Ініціалізація налаштувань при першому запуску
   */
  async initSettings() {
    try {
      const result = await chrome.storage.sync.get("settings");

      // Якщо налаштувань немає - створюємо дефолтні
      if (!result.settings) {
        const defaultSettings = {
          apiUrl: "http://localhost:8001",
          detailedReports: true,
          language: "uk",
          version: chrome.runtime.getManifest().version,
        };

        await chrome.storage.sync.set({ settings: defaultSettings });
        console.log("⚙️ Створено початкові налаштування:", defaultSettings);
      } else {
        // Перевіряємо чи не змінилася версія
        const currentVersion = chrome.runtime.getManifest().version;
        if (result.settings.version !== currentVersion) {
          result.settings.version = currentVersion;
          await chrome.storage.sync.set({ settings: result.settings });
          console.log(`🔄 Оновлено версію до ${currentVersion}`);
        }
      }
    } catch (error) {
      console.error("❌ Помилка ініціалізації налаштувань:", error);
    }
  }

  bindEvents() {
    // Кнопка аналізу
    document.getElementById("analyze-btn").addEventListener("click", () => {
      this.analyzeCurrentPage();
    });

    // Перемикач детальних результатів
    document.getElementById("toggle-details").addEventListener("click", () => {
      this.toggleDetailedResults();
    });

    // Експорт звіту
    document.getElementById("export-btn").addEventListener("click", () => {
      this.exportReport();
    });

    // Альтернативний експорт (відкрити в новій вкладці)
    const exportAltBtn = document.getElementById("export-alt-btn");
    if (exportAltBtn) {
      exportAltBtn.addEventListener("click", () => {
        this.exportReportAsTab();
      });
    }

    // Підсвічування проблем
    document
      .getElementById("highlight-issues")
      .addEventListener("click", () => {
        this.highlightIssues();
      });

    // Налаштування
    document.getElementById("settings-btn").addEventListener("click", () => {
      this.openSettings();
    });

    // Допомога
    document.getElementById("help-btn").addEventListener("click", () => {
      this.openHelp();
    });

    // Клік по метриці для деталей
    document.querySelectorAll(".metric-card").forEach((card) => {
      card.addEventListener("click", () => {
        const metric = card.dataset.metric;
        this.showMetricDetails(metric);
      });
    });
  }

  async analyzeCurrentPage() {
    if (this.isAnalyzing) return;

    try {
      this.setAnalyzing(true);
      this.showProgress();

      // Отримуємо активну вкладку
      const [tab] = await chrome.tabs.query({
        active: true,
        currentWindow: true,
      });

      if (!tab) {
        throw new Error("Не вдалося отримати активну вкладку");
      }

      // Перевіряємо чи можна аналізувати цю сторінку
      if (!this.canAnalyzePage(tab.url)) {
        throw new Error(
          "Неможливо аналізувати цю сторінку (chrome://, extension://, etc.)"
        );
      }

      console.log(`🔍 Аналізуємо сторінку: ${tab.url}`);

      // Витягуємо HTML поточної сторінки
      console.log("📄 Витягуємо HTML сторінки...");
      const [{ result: htmlContent }] = await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: () => document.documentElement.outerHTML,
      });

      if (!htmlContent) {
        throw new Error("Не вдалося отримати HTML сторінки");
      }

      console.log(`📊 Розмір HTML: ${htmlContent.length} символів`);

      // Викликаємо Flask API для аналізу HTML
      const response = await fetch(`${this.API_BASE_URL}/api/evaluate-html`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({
          html_content: htmlContent,
          base_url: tab.url,
          title: tab.title,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          `HTTP ${response.status}: ${errorData.detail || response.statusText}`
        );
      }

      const results = await response.json();

      if (!results) {
        throw new Error("Не отримано результатів аналізу");
      }

      if (results.status === "error") {
        throw new Error(
          `Помилка аналізу: ${results.error || "Невідома помилка"}`
        );
      }

      // Зберігаємо оригінальні результати API для /api/report
      this.originalApiResults = results;

      // Конвертуємо результати Flask API у формат, який очікує UI
      const convertedResults = this.convertApiResultsToUIFormat(results);

      this.currentResults = convertedResults;
      this.displayResults(convertedResults);
      this.saveResults(convertedResults, results, tab.url); // Зберігаємо обидва формати
    } catch (error) {
      console.error("Помилка аналізу:", error);

      // Перевіряємо чи це помилка з'єднання з сервером
      if (
        error.message.includes("Failed to fetch") ||
        error.message.includes("NetworkError")
      ) {
        this.showError(
          "Не вдалося з'єднатися з сервером аналізу. Переконайтеся, що Flask сервер запущено на http://localhost:8001"
        );
      } else {
        this.showError(error.message);
      }
    } finally {
      this.setAnalyzing(false);
      this.hideProgress();
    }
  }

  canAnalyzePage(url) {
    const restrictedProtocols = [
      "chrome:",
      "chrome-extension:",
      "moz-extension:",
      "edge:",
      "about:",
    ];
    return !restrictedProtocols.some((protocol) => url.startsWith(protocol));
  }

  /**
   * Конвертує результати Flask API у формат, який очікує UI
   */
  convertApiResultsToUIFormat(apiResults) {
    return {
      totalScore: apiResults.final_score,
      metrics: {
        perceptibility: apiResults.subscores.perceptibility,
        operability: apiResults.subscores.operability,
        understandability: apiResults.subscores.understandability,
        localization: apiResults.subscores.localization,
      },
      detailedMetrics: apiResults.metrics,
      recommendations: apiResults.recommendations.map(
        (rec) => rec.recommendation
      ),
      issues: this.extractIssuesFromRecommendations(apiResults.recommendations),
      pageData: {
        title: apiResults.url,
        language: "auto-detected",
        direction: "ltr",
      },
      qualityLevel: apiResults.quality_level,
      qualityDescription: apiResults.quality_description,
      detailedAnalysis: apiResults.detailed_analysis || {},
    };
  }

  /**
   * Витягує проблеми з рекомендацій для підсвічування
   */
  extractIssuesFromRecommendations(recommendations) {
    return recommendations.map((rec) => ({
      severity:
        rec.priority === "Високий"
          ? "high"
          : rec.priority === "Середній"
          ? "medium"
          : "low",
      description: rec.recommendation,
      category: rec.category,
      wcag: rec.wcag_reference,
    }));
  }

  setAnalyzing(analyzing) {
    this.isAnalyzing = analyzing;
    const analyzeBtn = document.getElementById("analyze-btn");
    const btnText = analyzeBtn.querySelector(".btn-text");

    if (analyzing) {
      analyzeBtn.disabled = true;
      btnText.textContent = "Аналіз...";
      analyzeBtn.style.opacity = "0.6";
    } else {
      analyzeBtn.disabled = false;
      btnText.textContent = "Аналізувати сторінку";
      analyzeBtn.style.opacity = "1";
    }
  }

  showProgress() {
    document.getElementById("analyze-progress").style.display = "block";
  }

  hideProgress() {
    document.getElementById("analyze-progress").style.display = "none";
  }

  displayResults(results) {
    // Ховаємо помилки та показуємо результати
    document.getElementById("error-container").style.display = "none";
    document.getElementById("results-container").style.display = "block";

    // Загальний скор
    const totalScore = (results.totalScore * 100).toFixed(1);
    document.getElementById("total-score").textContent = totalScore;
    this.updateScoreInterpretation(totalScore);

    // Метрики
    const metrics = [
      "perceptibility",
      "operability",
      "understandability",
      "localization",
    ];
    metrics.forEach((metric) => {
      const score = ((results.metrics[metric] || 0) * 100).toFixed(1);
      document.getElementById(`${metric}-score`).textContent = score;
      this.updateMetricCard(metric, parseFloat(score));
    });

    // Детальні результати
    this.updateDetailedResults(results);
  }

  updateScoreInterpretation(score) {
    const interpretation = document.getElementById("score-interpretation");
    const totalScoreElement = document.getElementById("total-score");

    let text, className;

    if (score >= 90) {
      text = "Відмінна доступність";
      className = "score-excellent";
    } else if (score >= 75) {
      text = "Хороша доступність";
      className = "score-good";
    } else if (score >= 60) {
      text = "Задовільна доступність";
      className = "score-fair";
    } else if (score >= 40) {
      text = "Погана доступність";
      className = "score-poor";
    } else {
      text = "Критична доступність";
      className = "score-critical";
    }

    interpretation.textContent = text;
    totalScoreElement.className = `total-score ${className}`;
  }

  updateMetricCard(metric, score) {
    const card = document.querySelector(`[data-metric="${metric}"]`);
    const scoreElement = card.querySelector(".score-value");

    let className;
    if (score >= 80) className = "score-excellent";
    else if (score >= 65) className = "score-good";
    else if (score >= 50) className = "score-fair";
    else if (score >= 35) className = "score-poor";
    else className = "score-critical";

    scoreElement.className = `score-value ${className}`;
  }

  updateDetailedResults(results) {
    const detailedContainer = document.getElementById("detailed-results");

    let html = '<div class="detailed-content">';

    // Підсумок проблем
    if (results.issues && results.issues.length > 0) {
      html += `
                <div class="issues-summary">
                    <h4>🚨 Знайдені проблеми (${results.issues.length})</h4>
                    <div class="issues-list">
            `;

      results.issues.slice(0, 5).forEach((issue) => {
        html += `
                    <div class="issue-item ${issue.severity}">
                        <span class="issue-severity">${this.getSeverityIcon(issue.severity)}</span>
                        <span class="issue-text">${issue.description}</span>
                    </div>
                `;
      });

      if (results.issues.length > 5) {
        html += `<div class="more-issues">... та ще ${
          results.issues.length - 5
        } проблем</div>`;
      }

      html += "</div></div>";
    }

    // Статистика по метриках
    html += `
            <div class="metrics-details">
                <h4>📊 Детальна статистика</h4>
                <div class="stats-grid">
        `;

    const metricsInfo = {
      perceptibility: "Сприйнятність",
      operability: "Керованість",
      understandability: "Зрозумілість",
      localization: "Локалізація",
    };

    Object.entries(metricsInfo).forEach(([key, title]) => {
      const score = Math.round((results.metrics[key] || 0) * 100);
      html += `
                <div class="stat-item">
                    <span class="stat-label">${title}:</span>
                    <span class="stat-value">${score}%</span>
                </div>
            `;
    });

    html += "</div></div>";

    // Рекомендації
    if (results.recommendations && results.recommendations.length > 0) {
      html += `
                <div class="recommendations">
                    <h4>💡 Рекомендації</h4>
                    <ul class="recommendations-list">
            `;

      results.recommendations.slice(0, 3).forEach((rec) => {
        html += `<li class="recommendation-item">${rec}</li>`;
      });

      html += "</ul></div>";
    }

    html += "</div>";

    detailedContainer.innerHTML = html;
  }

  getSeverityIcon(severity) {
    const icons = {
      critical: "🔴",
      high: "🟠",
      medium: "🟡",
      low: "🔵",
      info: "ℹ️",
    };
    return icons[severity] || "ℹ️";
  }

  toggleDetailedResults() {
    const detailedResults = document.getElementById("detailed-results");
    const toggleBtn = document.getElementById("toggle-details");
    const isVisible = detailedResults.style.display !== "none";

    if (isVisible) {
      detailedResults.style.display = "none";
      toggleBtn.classList.remove("expanded");
    } else {
      detailedResults.style.display = "block";
      toggleBtn.classList.add("expanded");
    }
  }

  async exportReport() {
    if (!this.currentResults || !this.originalApiResults) {
      this.showError("Немає результатів для експорту");
      return;
    }

    try {
      const [tab] = await chrome.tabs.query({
        active: true,
        currentWindow: true,
      });

      console.log("🔄 Генеруємо звіт через API...");

      // Викликаємо backend для генерації HTML звіту
      // ВАЖЛИВО: відправляємо оригінальний API формат, не конвертований UI формат
      const response = await fetch(`${this.API_BASE_URL}/api/report`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(this.originalApiResults),
      });

      if (!response.ok) {
        throw new Error(`API помилка: ${response.status}`);
      }

      const reportHTML = await response.text();

      if (!reportHTML || reportHTML.length < 100) {
        throw new Error("Отриманий звіт порожній");
      }

      console.log("📄 Звіт отримано від API, розмір:", reportHTML.length);

      // Створюємо blob та завантажуємо
      const blob = new Blob([reportHTML], { type: "text/html;charset=utf-8" });
      const url = URL.createObjectURL(blob);

      const hostname = new URL(tab.url).hostname.replace(/[^a-zA-Z0-9]/g, "-");
      const timestamp = new Date().toISOString().split("T")[0];
      const filename = `accessibility-report-${hostname}-${timestamp}.html`;

      await chrome.downloads.download({
        url: url,
        filename: filename,
        saveAs: true,
      });

      setTimeout(() => URL.revokeObjectURL(url), 1000);
      this.showSuccess("Звіт успішно експортовано!");
    } catch (error) {
      console.error("❌ Помилка експорту:", error);
      this.showError(`Не вдалося експортувати звіт: ${error.message}`);
    }
  }

  async exportReportAsTab() {
    if (!this.currentResults || !this.originalApiResults) {
      this.showError("Немає результатів для експорту");
      return;
    }

    try {
      console.log("🔄 Відкриваємо звіт в новій вкладці...");

      // Викликаємо backend для генерації HTML звіту
      // ВАЖЛИВО: відправляємо оригінальний API формат, не конвертований UI формат
      const response = await fetch(`${this.API_BASE_URL}/api/report`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(this.originalApiResults),
      });

      if (!response.ok) {
        throw new Error(`API помилка: ${response.status}`);
      }

      const reportHTML = await response.text();
      const blob = new Blob([reportHTML], { type: "text/html;charset=utf-8" });
      const url = URL.createObjectURL(blob);

      await chrome.tabs.create({ url: url });
      setTimeout(() => URL.revokeObjectURL(url), 10000);

      this.showSuccess("Звіт відкрито в новій вкладці!");
    } catch (error) {
      console.error("❌ Помилка:", error);
      this.showError(`Не вдалося відкрити звіт: ${error.message}`);
    }
  }
  async highlightIssues() {
    if (!this.currentResults || !this.currentResults.issues) {
      this.showError("Немає результатів для підсвічування проблем");
      return;
    }

    try {
      const [tab] = await chrome.tabs.query({
        active: true,
        currentWindow: true,
      });

      // Ін'єктуємо простий скрипт для підсвічування проблем
      await chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: this.highlightIssuesOnPage,
        args: [this.currentResults.issues],
      });
    } catch (error) {
      console.error("Помилка підсвічування:", error);
      this.showError("Не вдалося підсвітити проблеми на сторінці");
    }
  }

  /**
   * Функція для ін'єкції - підсвічує проблеми на сторінці
   */
  highlightIssuesOnPage(issues) {
    // Видаляємо попередні підсвічування
    document.querySelectorAll(".accessibility-highlight").forEach((el) => {
      el.classList.remove("accessibility-highlight");
    });

    // Додаємо стилі для підсвічування
    if (!document.getElementById("accessibility-highlight-styles")) {
      const style = document.createElement("style");
      style.id = "accessibility-highlight-styles";
      style.textContent = `
                .accessibility-highlight {
                    outline: 3px solid #ff6b6b !important;
                    outline-offset: 2px !important;
                    background-color: rgba(255, 107, 107, 0.1) !important;
                }
                .accessibility-highlight-tooltip {
                    position: absolute;
                    background: #333;
                    color: white;
                    padding: 8px;
                    border-radius: 4px;
                    font-size: 12px;
                    z-index: 10000;
                    max-width: 300px;
                    word-wrap: break-word;
                }
            `;
      document.head.appendChild(style);
    }

    // Підсвічуємо елементи на основі категорій проблем
    issues.forEach((issue) => {
      let selector = "";

      // Визначаємо селектори на основі категорії проблеми
      if (
        issue.category === "Перцептивність" ||
        issue.description.includes("зображен")
      ) {
        selector = 'img:not([alt]), img[alt=""]';
      } else if (
        issue.category === "Керованість" ||
        issue.description.includes("клавіатур")
      ) {
        selector = "a:not([href]), button:not([type]), input:not([type])";
      } else if (
        issue.category === "Зрозумілість" ||
        issue.description.includes("форм")
      ) {
        selector = "form, input, textarea, select";
      } else if (
        issue.category === "Локалізація" ||
        issue.description.includes("мов")
      ) {
        selector = 'html:not([lang]), [lang=""]';
      }

      if (selector) {
        document.querySelectorAll(selector).forEach((element) => {
          element.classList.add("accessibility-highlight");
          element.title = `Проблема доступності: ${issue.description}`;
        });
      }
    });

    console.log(`Підсвічено проблеми доступності: ${issues.length} категорій`);
  }

  showMetricDetails(metric) {
    // TODO: Показати детальну інформацію про конкретну метрику
    console.log(`Показати деталі для метрики: ${metric}`);
  }

  openSettings() {
    // TODO: Відкрити сторінку налаштувань
    console.log("Відкрити налаштування");
  }

  /**
   * Перевіряє стан Flask сервера
   */
  async checkServerStatus() {
    try {
      const response = await fetch(`${this.API_BASE_URL}/api/health`, {
        method: "GET",
        headers: { Accept: "application/json" },
      });

      if (response.ok) {
        console.log("✅ Flask сервер доступний");
        this.showServerStatus("online");
      } else {
        throw new Error(`Server responded with ${response.status}`);
      }
    } catch (error) {
      console.warn("⚠️ Flask сервер недоступний:", error.message);
      this.showServerStatus("offline");
    }
  }

  /**
   * Показує статус сервера в UI
   */
  showServerStatus(status) {
    const statusElement = document.getElementById("server-status");
    if (!statusElement) {
      // Створюємо індикатор статусу якщо його немає
      const indicator = document.createElement("div");
      indicator.id = "server-status";
      indicator.style.cssText = `
                position: absolute;
                top: 10px;
                right: 10px;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                z-index: 1000;
            `;
      document.body.appendChild(indicator);
    }

    const indicator = document.getElementById("server-status");
    if (status === "online") {
      indicator.style.backgroundColor = "#28a745";
      indicator.title = "Сервер доступний";
    } else {
      indicator.style.backgroundColor = "#dc3545";
      indicator.title =
        "Сервер недоступний. Запустіть Flask сервер на порту 8001";
    }
  }

  openHelp() {
    // Відкриваємо веб-інтерфейс Flask сервера
    chrome.tabs.create({
      url: `${this.API_BASE_URL}/`,
    });
  }

  showError(message) {
    document.getElementById("results-container").style.display = "none";
    document.getElementById("error-container").style.display = "block";
    document.getElementById("error-text").textContent = message;
  }

  showSuccess(message) {
    // Створюємо тимчасове повідомлення про успіх
    const successDiv = document.createElement("div");
    successDiv.style.cssText = `
            position: fixed;
            top: 10px;
            left: 50%;
            transform: translateX(-50%);
            background: #28a745;
            color: white;
            padding: 10px 20px;
            border-radius: 5px;
            z-index: 10000;
            font-size: 14px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        `;
    successDiv.textContent = message;
    document.body.appendChild(successDiv);

    // Видаляємо через 3 секунди
    setTimeout(() => {
      if (successDiv.parentNode) {
        successDiv.parentNode.removeChild(successDiv);
      }
    }, 3000);
  }

  async loadPreviousResults() {
    try {
      const [tab] = await chrome.tabs.query({
        active: true,
        currentWindow: true,
      });
      const key = `results_${this.getUrlKey(tab.url)}`;
      const stored = await chrome.storage.local.get(key);

      if (stored[key]?.ui && stored[key]?.api) {
        this.currentResults = stored[key].ui;
        this.originalApiResults = stored[key].api;
        this.displayResults(stored[key].ui);
      }
    } catch (error) {
      console.log("Немає попередніх результатів");
    }
  }

  /**
   * Зберігає результати аналізу в двох форматах:
   * - ui: конвертований формат для відображення в popup
   * - api: оригінальний формат API для експорту звітів через /api/report
   */
  async saveResults(uiResults, apiResults, url) {
    try {
      const key = `results_${this.getUrlKey(url)}`;
      await chrome.storage.local.set({
        [key]: {
          ui: uiResults,
          api: apiResults,
          timestamp: Date.now(),
          url: url,
        },
      });
    } catch (error) {
      console.error("Помилка збереження результатів:", error);
    }
  }

  getUrlKey(url) {
    return btoa(url)
      .replace(/[^a-zA-Z0-9]/g, "")
      .substring(0, 50);
  }

  /**
   * Екранує HTML для безпечного відображення
   */
  escapeHtml(text) {
    if (!text) return "";
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }
}

// Ініціалізація popup при завантаженні
document.addEventListener("DOMContentLoaded", () => {
  new AccessibilityPopup();
});
