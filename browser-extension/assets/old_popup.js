/**
 * Popup JavaScript для Accessibility Evaluator
 * Використовує Flask API для аналізу доступності
 */

class AccessibilityPopup {
  constructor() {
    this.isAnalyzing = false;
    this.currentResults = null;
    this.API_BASE_URL = "http://localhost:8001"; // Flask сервер
    this.init();
  }

  init() {
    this.bindEvents();
    this.loadPreviousResults();
    this.checkServerStatus();
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

      // Викликаємо Flask API для аналізу
      const response = await fetch(`${this.API_BASE_URL}/api/evaluate`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Accept: "application/json",
        },
        body: JSON.stringify({
          url: tab.url,
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

      // Конвертуємо результати Flask API у формат, який очікує UI
      const convertedResults = this.convertApiResultsToUIFormat(results);

      this.currentResults = convertedResults;
      this.displayResults(convertedResults);
      this.saveResults(convertedResults, tab.url);
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
                    <div class="issue-item">
                        <span class="issue-severity ${
                          issue.severity
                        }">${this.getSeverityIcon(issue.severity)}</span>
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
    if (!this.currentResults) {
      this.showError("Немає результатів для експорту");
      return;
    }

    try {
      const [tab] = await chrome.tabs.query({
        active: true,
        currentWindow: true,
      });

      console.log("🔄 Генеруємо звіт...");
      const report = this.generateReport(this.currentResults, tab.url);

      if (!report || report.length < 100) {
        throw new Error("Згенерований звіт порожній або некоректний");
      }

      console.log("📄 Звіт згенеровано, розмір:", report.length, "символів");

      // Створюємо blob з правильним MIME типом
      const blob = new Blob([report], {
        type: "text/html;charset=utf-8",
      });

      console.log("📦 Blob створено, розмір:", blob.size, "байт");

      // Створюємо URL для blob
      const url = URL.createObjectURL(blob);
      console.log("🔗 Blob URL створено:", url);

      // Генеруємо безпечне ім'я файлу
      const hostname = new URL(tab.url).hostname.replace(/[^a-zA-Z0-9]/g, "-");
      const timestamp = new Date().toISOString().split("T")[0];
      const filename = `accessibility-report-${hostname}-${timestamp}.html`;

      console.log("💾 Завантажуємо файл:", filename);

      // Завантажуємо файл
      const downloadId = await chrome.downloads.download({
        url: url,
        filename: filename,
        saveAs: true, // Дозволяємо користувачу вибрати місце збереження
      });

      console.log("✅ Файл завантажено, ID:", downloadId);

      // Очищуємо URL після невеликої затримки
      setTimeout(() => {
        URL.revokeObjectURL(url);
        console.log("🧹 Blob URL очищено");
      }, 1000);

      // Показуємо повідомлення про успіх
      this.showSuccess("Звіт успішно експортовано!");
    } catch (error) {
      console.error("❌ Помилка експорту:", error);
      console.error("Stack trace:", error.stack);

      // Детальніше повідомлення про помилку
      let errorMessage = "Не вдалося експортувати звіт";
      if (error.message.includes("downloads")) {
        errorMessage += ". Перевірте дозволи розширення для завантажень.";
      } else if (error.message.includes("blob")) {
        errorMessage += ". Помилка створення файлу.";
      } else {
        errorMessage += `: ${error.message}`;
      }

      this.showError(errorMessage);

      // Fallback: спробуємо відкрити звіт в новій вкладці
      try {
        console.log("🔄 Спробуємо fallback метод...");
        const report = this.generateReport(this.currentResults, tab.url);
        const blob = new Blob([report], { type: "text/html;charset=utf-8" });
        const url = URL.createObjectURL(blob);

        await chrome.tabs.create({ url: url });
        console.log("✅ Звіт відкрито в новій вкладці");

        setTimeout(() => URL.revokeObjectURL(url), 5000);
      } catch (fallbackError) {
        console.error("❌ Fallback також не спрацював:", fallbackError);
      }
    }
  }

  /**
   * Альтернативний метод експорту - відкриває звіт у новій вкладці
   */
  async exportReportAsTab() {
    if (!this.currentResults) {
      this.showError("Немає результатів для експорту");
      return;
    }

    try {
      const [tab] = await chrome.tabs.query({
        active: true,
        currentWindow: true,
      });

      console.log("🔄 Генеруємо звіт для нової вкладки...");
      const report = this.generateReport(this.currentResults, tab.url);

      if (!report || report.length < 100) {
        throw new Error("Згенерований звіт порожній або некоректний");
      }

      // Створюємо blob та відкриваємо в новій вкладці
      const blob = new Blob([report], { type: "text/html;charset=utf-8" });
      const url = URL.createObjectURL(blob);

      const newTab = await chrome.tabs.create({ url: url });
      console.log("✅ Звіт відкрито в новій вкладці, ID:", newTab.id);

      // Очищуємо URL через 10 секунд
      setTimeout(() => {
        URL.revokeObjectURL(url);
        console.log("🧹 Blob URL очищено");
      }, 10000);

      this.showSuccess("Звіт відкрито в новій вкладці!");
    } catch (error) {
      console.error("❌ Помилка відкриття звіту в новій вкладці:", error);
      this.showError(`Не вдалося відкрити звіт: ${error.message}`);
    }
  }

  generateReport(results, pageUrl) {
    const date = new Date().toLocaleDateString("uk-UA");
    const totalScore = (results.totalScore * 100).toFixed(1);

    return `
            <!DOCTYPE html>
            <html lang="uk">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>Детальний звіт доступності - ${pageUrl}</title>
                <style>
                    body { 
                        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                        margin: 0; 
                        padding: 20px; 
                        background-color: #f8f9fa;
                        line-height: 1.6;
                        color: #333;
                    }
                    .container {
                        max-width: 1400px;
                        margin: 0 auto;
                        background: white;
                        border-radius: 12px;
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                        overflow: hidden;
                    }
                    .header { 
                        background: linear-gradient(135deg, #2c3e50, #3498db);
                        color: white;
                        padding: 30px 40px;
                        text-align: center;
                    }
                    .header h1 { margin: 0 0 20px 0; font-size: 2.5em; font-weight: 300; }
                    .header p { margin: 5px 0; opacity: 0.9; }
                    .score-badge { 
                        display: inline-block;
                        background: rgba(255,255,255,0.2);
                        padding: 15px 30px;
                        border-radius: 50px;
                        font-size: 1.8em;
                        font-weight: bold;
                        margin-top: 20px;
                    }
                    .content { padding: 40px; }
                    
                    /* Стилі для детального аналізу */
                    .metric-section {
                        background: white;
                        border: 2px solid #e9ecef;
                        border-radius: 10px;
                        padding: 25px;
                        margin-bottom: 30px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
                    }
                    .metric-section-title {
                        color: #2c3e50;
                        margin-bottom: 20px;
                        font-size: 1.4rem;
                        border-bottom: 2px solid #ecf0f1;
                        padding-bottom: 10px;
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                    }
                    .metric-score-display {
                        font-size: 1.2rem;
                        font-weight: bold;
                        padding: 8px 16px;
                        border-radius: 20px;
                        color: white;
                    }
                    
                    /* Елементи списку */
                    .element-list {
                        margin-top: 20px;
                    }
                    .element-item {
                        background: #f8f9fa;
                        border: 1px solid #e9ecef;
                        border-radius: 8px;
                        padding: 15px;
                        margin-bottom: 15px;
                        transition: box-shadow 0.2s;
                    }
                    .element-item:hover {
                        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
                    }
                    .element-item.correct {
                        border-left: 4px solid #27ae60;
                        background: #f0f9f0;
                    }
                    .element-item.problematic {
                        border-left: 4px solid #e74c3c;
                        background: #fdf2f2;
                    }
                    .element-selector {
                        font-family: 'Courier New', monospace;
                        font-size: 14px;
                        color: #2c3e50;
                        font-weight: bold;
                        margin-bottom: 8px;
                        background: #ecf0f1;
                        padding: 4px 8px;
                        border-radius: 4px;
                        display: inline-block;
                    }
                    .element-html {
                        font-family: 'Courier New', monospace;
                        font-size: 12px;
                        background: #f1f3f4;
                        padding: 10px;
                        border-radius: 5px;
                        margin: 8px 0;
                        overflow-x: auto;
                        white-space: pre-wrap;
                        word-break: break-all;
                        border: 1px solid #ddd;
                    }
                    .element-status {
                        color: #27ae60;
                        font-size: 14px;
                        margin-top: 8px;
                        font-weight: 500;
                    }
                    .element-issue {
                        color: #e74c3c;
                        font-size: 14px;
                        margin-top: 8px;
                        font-weight: 500;
                    }
                    
                    /* Контраст деталі */
                    .contrast-info {
                        display: grid;
                        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                        gap: 10px;
                        margin-top: 15px;
                    }
                    .contrast-detail {
                        background: #f8f9fa;
                        padding: 10px;
                        border-radius: 5px;
                        font-size: 13px;
                        border: 1px solid #e9ecef;
                    }
                    .color-swatch {
                        display: inline-block;
                        width: 24px;
                        height: 24px;
                        border-radius: 4px;
                        border: 1px solid #ccc;
                        margin-left: 8px;
                        vertical-align: middle;
                    }
                    
                    /* Статистика */
                    .score-explanation {
                        background: #e3f2fd;
                        border: 1px solid #bbdefb;
                        border-radius: 6px;
                        padding: 15px;
                        margin-bottom: 20px;
                        font-weight: 500;
                        color: #1565c0;
                    }
                    
                    /* Кольори скорів */
                    .score-excellent { background-color: #27ae60; }
                    .score-good { background-color: #3498db; }
                    .score-fair { background-color: #f39c12; }
                    .score-poor { background-color: #e74c3c; }
                    .score-critical { background-color: #95a5a6; }
                    
                    /* Рекомендації */
                    .recommendations {
                        background: #fff3cd;
                        border: 2px solid #ffeaa7;
                        border-radius: 10px;
                        padding: 25px;
                        margin: 30px 0;
                    }
                    .recommendations h3 {
                        color: #856404;
                        margin-bottom: 20px;
                        font-size: 1.3rem;
                    }
                    .recommendation-item {
                        background: white;
                        border-left: 4px solid #f39c12;
                        padding: 15px;
                        margin-bottom: 15px;
                        border-radius: 5px;
                        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                    }
                    .recommendation-category {
                        font-weight: 600;
                        color: #e67e22;
                        font-size: 0.9rem;
                        margin-bottom: 5px;
                    }
                    .recommendation-text {
                        color: #2c3e50;
                        margin-bottom: 5px;
                    }
                    .recommendation-wcag {
                        font-size: 0.8rem;
                        color: #666;
                        font-style: italic;
                    }
                    
                    .footer {
                        text-align: center;
                        padding: 30px;
                        color: #6c757d;
                        font-size: 0.9em;
                        border-top: 1px solid #dee2e6;
                        margin-top: 40px;
                        background: #f8f9fa;
                    }
                    
                    /* Responsive */
                    @media (max-width: 768px) {
                        .content { padding: 20px; }
                        .header h1 { font-size: 2rem; }
                        .contrast-info { grid-template-columns: 1fr; }
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🔍 Детальний звіт доступності</h1>
                        <p><strong>URL:</strong> ${pageUrl}</p>
                        <p><strong>Дата аналізу:</strong> ${date}</p>
                        <p><strong>Рівень якості:</strong> ${
                          results.qualityLevel || "Невизначено"
                        }</p>
                        <div class="score-badge">
                            Загальний скор: ${totalScore}%
                        </div>
                    </div>
                    
                    <div class="content">
                        ${this.generateDetailedMetricsAnalysis(results)}
                        ${this.generateDetailedRecommendations(results)}
                    </div>
                    
                    <div class="footer">
                        <p><strong>Згенеровано Accessibility Evaluator v1.0.0</strong></p>
                        <p>${new Date().toLocaleString("uk-UA")}</p>
                        <p>Аналіз базується на принципах WCAG 2.1 та науковій методології оцінки доступності ISO 25023</p>
                        <p>Детальний аналіз включає перевірку всіх елементів сторінки з конкретними рекомендаціями</p>
                    </div>
                </div>
            </body>
            </html>
        `;
  }

  /**
   * Генерує детальний аналіз всіх метрик з елементами
   */
  generateDetailedMetricsAnalysis(results) {
    const detailedAnalysis = results.detailedAnalysis || {};
    let html = "";

    // Загальне пояснення про фокус звіту
    html += `
            <div style="background: #fff3cd; border: 1px solid #ffeaa7; border-radius: 6px; padding: 15px; margin-bottom: 25px; font-size: 14px;">
                <strong>💡 Фокус звіту:</strong> Нижче показані тільки елементи, які потребують покращення. 
                Успішно перевірені елементи підраховані в загальному скорі та відображені в підсумку.
            </div>
        `;

    // Перцептивність
    html += this.generateMetricSection(
      "🔍 Перцептивність",
      results.metrics.perceptibility,
      detailedAnalysis,
      ["alt_text", "contrast", "media_accessibility"]
    );

    // Керованість
    html += this.generateMetricSection(
      "⌨️ Керованість",
      results.metrics.operability,
      detailedAnalysis,
      ["keyboard_navigation", "structured_navigation"]
    );

    // Зрозумілість
    html += this.generateMetricSection(
      "💡 Зрозумілість",
      results.metrics.understandability,
      detailedAnalysis,
      ["instruction_clarity", "input_assistance", "error_support"]
    );

    // Локалізація
    html += this.generateMetricSection(
      "🌍 Локалізація",
      results.metrics.localization,
      detailedAnalysis,
      ["localization"]
    );

    return html;
  }

  /**
   * Генерує секцію для конкретної метрики
   */
  generateMetricSection(title, score, detailedAnalysis, subMetrics) {
    const scorePercent = (score * 100).toFixed(1);
    const scoreClass = this.getScoreClass(parseFloat(scorePercent));

    let html = `
            <div class="metric-section">
                <div class="metric-section-title">
                    <span>${title} (${scorePercent}%)</span>
                    <span class="metric-score-display ${scoreClass}">${scorePercent}%</span>
                </div>
        `;

    // Генеруємо деталі для кожної підметрики
    subMetrics.forEach((subMetric) => {
      const details = detailedAnalysis[subMetric];
      if (details) {
        html += this.generateSubMetricDetails(subMetric, details);
      }
    });

    html += "</div>";
    return html;
  }

  /**
   * Генерує деталі для підметрики
   */
  generateSubMetricDetails(subMetric, details) {
    const title = this.getSubMetricTitle(subMetric);
    let html = `<h4>${title}</h4>`;

    // Пояснення скору
    if (details.score_explanation) {
      html += `<div class="score-explanation">${details.score_explanation}</div>`;
    }

    // Проблемні елементи
    if (details.problematic_images && details.problematic_images.length > 0) {
      html += this.generateProblematicElements(
        "❌ Проблемні зображення",
        details.problematic_images
      );
    }
    if (
      details.problematic_elements &&
      details.problematic_elements.length > 0
    ) {
      html += this.generateProblematicElements(
        "❌ Проблемні елементи",
        details.problematic_elements
      );
    }
    if (
      details.problematic_headings &&
      details.problematic_headings.length > 0
    ) {
      html += this.generateProblematicElements(
        "❌ Проблемні заголовки",
        details.problematic_headings
      );
    }
    if (details.problematic_fields && details.problematic_fields.length > 0) {
      html += this.generateProblematicElements(
        "❌ Проблемні поля",
        details.problematic_fields
      );
    }
    if (details.problematic_forms && details.problematic_forms.length > 0) {
      html += this.generateProblematicForms(
        "❌ Проблемні форми",
        details.problematic_forms
      );
    }
    if (details.problematic_media && details.problematic_media.length > 0) {
      html += this.generateProblematicElements(
        "❌ Проблемні медіа",
        details.problematic_media
      );
    }
    if (
      details.problematic_instructions &&
      details.problematic_instructions.length > 0
    ) {
      html += this.generateProblematicElements(
        "❌ Незрозумілі інструкції",
        details.problematic_instructions
      );
    }

    // Показуємо тільки проблемні елементи для фокусу на покращеннях
    // Правильні елементи приховано для кращої читабельності звіту

    // Додаємо підсумок успішних перевірок
    html += this.generateSuccessSummary(details);

    return html;
  }

  /**
   * Генерує список проблемних елементів
   */
  generateProblematicElements(title, elements) {
    let html = `<h5 style="color: #e74c3c; margin-top: 20px;">${title} (${elements.length}):</h5>`;
    html += '<div class="element-list">';

    elements.forEach((element) => {
      html += `
                <div class="element-item problematic">
                    <div class="element-selector">${
                      element.selector || "Невідомий селектор"
                    }</div>
                    <div class="element-html">${this.escapeHtml(
                      element.html || "HTML недоступний"
                    )}</div>
                    <div class="element-issue"><strong>Проблема:</strong> ${
                      element.issue || element.rule || "Невідома проблема"
                    }</div>
            `;

      // Додаткова інформація для контрасту
      if (element.contrast_ratio) {
        html += `
                    <div class="contrast-info">
                        <div class="contrast-detail">
                            <strong>Поточний контраст:</strong> ${
                              element.contrast_ratio
                            }
                        </div>
                        <div class="contrast-detail">
                            <strong>Необхідний:</strong> ${
                              element.required_ratio || "Невідомо"
                            }
                        </div>
                        <div class="contrast-detail">
                            <strong>Колір тексту:</strong> ${
                              element.foreground || "Невідомо"
                            }
                            ${
                              element.foreground
                                ? `<span class="color-swatch" style="background-color: ${element.foreground}"></span>`
                                : ""
                            }
                        </div>
                        <div class="contrast-detail">
                            <strong>Колір фону:</strong> ${
                              element.background || "Невідомо"
                            }
                            ${
                              element.background
                                ? `<span class="color-swatch" style="background-color: ${element.background}"></span>`
                                : ""
                            }
                        </div>
                    </div>
                `;
      }

      html += "</div>";
    });

    html += "</div>";
    return html;
  }

  /**
   * Генерує список правильних елементів
   */
  generateCorrectElements(title, elements) {
    let html = `<h5 style="color: #27ae60; margin-top: 20px;">${title} (${elements.length}):</h5>`;
    html += '<div class="element-list">';

    // Показуємо максимум 10 елементів для економії місця
    const displayElements = elements.slice(0, 10);

    displayElements.forEach((element) => {
      html += `
                <div class="element-item correct">
                    <div class="element-selector">${
                      element.selector || "Невідомий селектор"
                    }</div>
                    <div class="element-html">${this.escapeHtml(
                      element.html || "HTML недоступний"
                    )}</div>
                    <div class="element-status"><strong>Статус:</strong> ${
                      element.status || element.alt_text || "Правильний елемент"
                    }</div>
            `;

      // Додаткова інформація для зображень
      if (element.alt_text) {
        html += `<div class="element-status"><strong>Alt текст:</strong> "${element.alt_text}"</div>`;
      }

      // Додаткова інформація для медіа
      if (element.type && element.platform) {
        html += `<div class="element-status"><strong>Тип:</strong> ${element.type} (${element.platform})</div>`;
      }
      if (element.title) {
        html += `<div class="element-status"><strong>Назва:</strong> ${element.title}</div>`;
      }
      if (element.src) {
        const shortSrc =
          element.src.length > 80
            ? element.src.substring(0, 80) + "..."
            : element.src;
        html += `<div class="element-status"><strong>URL:</strong> ${shortSrc}</div>`;
      }

      html += "</div>";
    });

    if (elements.length > 10) {
      html += `<p style="text-align: center; color: #666; margin-top: 10px;">... та ще ${
        elements.length - 10
      } елементів</p>`;
    }

    html += "</div>";
    return html;
  }

  /**
   * Генерує список проблемних форм
   */
  generateProblematicForms(title, forms) {
    let html = `<h5 style="color: #e74c3c; margin-top: 20px;">${title} (${forms.length}):</h5>`;

    forms.forEach((form) => {
      const qualityScore =
        typeof form.quality_score === "number" && !isNaN(form.quality_score)
          ? (form.quality_score * 100).toFixed(1)
          : "0.0";

      html += `
                <div style="margin: 15px 0; padding: 15px; background: #ffeaea; border-radius: 8px; border-left: 4px solid #e74c3c;">
                    <h6 style="margin: 0 0 10px 0; color: #e74c3c;">📋 ${
                      form.selector || "form"
                    }</h6>
                    <p><strong>Загальна якість:</strong> ${qualityScore}%</p>
                    <p><strong>Проблеми:</strong> ${
                      form.issue || form.features || "Невідомі проблеми"
                    }</p>
                </div>
            `;
    });

    return html;
  }

  /**
   * Генерує список правильних форм
   */
  generateCorrectForms(title, forms) {
    let html = `<h5 style="color: #27ae60; margin-top: 20px;">${title} (${forms.length}):</h5>`;

    forms.forEach((form) => {
      const qualityScore =
        typeof form.quality_score === "number" && !isNaN(form.quality_score)
          ? (form.quality_score * 100).toFixed(1)
          : "0.0";

      html += `
                <div style="margin: 15px 0; padding: 15px; background: #e8f5e8; border-radius: 8px; border-left: 4px solid #27ae60;">
                    <h6 style="margin: 0 0 10px 0; color: #27ae60;">📋 ${
                      form.selector || "form"
                    }</h6>
                    <p><strong>Загальна якість:</strong> ${qualityScore}%</p>
                    <p><strong>Функції:</strong> ${
                      form.features || "Хороша підтримка помилок"
                    }</p>
                </div>
            `;
    });

    return html;
  }

  /**
   * Генерує деталі мов
   */
  generateLanguageDetails(title, languages) {
    let html = `<h5 style="margin-top: 20px;">${title} (${languages.length}):</h5>`;
    html += '<div class="element-list">';

    languages.forEach((lang) => {
      const isDetected = title.includes("Виявлені");
      html += `
                <div class="element-item ${
                  isDetected ? "correct" : "problematic"
                }">
                    <div class="element-status"><strong>Мова:</strong> ${
                      lang.name
                    } (${lang.code})</div>
                    <div class="element-status"><strong>Потенційне покращення:</strong> +${(
                      lang.weight * 100
                    ).toFixed(1)}% до скору</div>
                </div>
            `;
    });

    html += "</div>";
    return html;
  }

  /**
   * Генерує підсумок успішних перевірок
   */
  generateSuccessSummary(details) {
    const successCounts = {
      images: details.correct_images_list?.length || 0,
      elements: details.correct_elements_list?.length || 0,
      headings: details.correct_headings_list?.length || 0,
      fields: details.assisted_fields_list?.length || 0,
      forms: details.supported_forms_list?.length || 0,
      media: details.accessible_media_list?.length || 0,
      instructions: details.clear_instructions_list?.length || 0,
      navigation: details.accessible_elements_list?.length || 0,
      languages: details.detected_languages?.length || 0,
    };

    const totalSuccess = Object.values(successCounts).reduce(
      (sum, count) => sum + count,
      0
    );

    if (totalSuccess === 0) {
      return "";
    }

    let html = `
            <div style="margin-top: 30px; padding: 20px; background: #e8f5e8; border-radius: 8px; border-left: 4px solid #27ae60;">
                <h5 style="color: #27ae60; margin-top: 0;">✅ Підсумок успішних перевірок</h5>
                <p style="color: #155724; margin-bottom: 15px;">
                    <strong>Загалом елементів пройшло перевірку: ${totalSuccess}</strong>
                </p>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; font-size: 14px;">
        `;

    if (successCounts.images > 0)
      html += `<div>🖼️ Зображення з alt-текстом: <strong>${successCounts.images}</strong></div>`;
    if (successCounts.elements > 0)
      html += `<div>🎨 Елементи з правильним контрастом: <strong>${successCounts.elements}</strong></div>`;
    if (successCounts.headings > 0)
      html += `<div>📋 Правильні заголовки: <strong>${successCounts.headings}</strong></div>`;
    if (successCounts.fields > 0)
      html += `<div>🆘 Поля з допомогою: <strong>${successCounts.fields}</strong></div>`;
    if (successCounts.forms > 0)
      html += `<div>⚠️ Форми з підтримкою помилок: <strong>${successCounts.forms}</strong></div>`;
    if (successCounts.media > 0)
      html += `<div>🎬 Доступні медіа: <strong>${successCounts.media}</strong></div>`;
    if (successCounts.instructions > 0)
      html += `<div>📝 Зрозумілі інструкції: <strong>${successCounts.instructions}</strong></div>`;
    if (successCounts.navigation > 0)
      html += `<div>⌨️ Доступна навігація: <strong>${successCounts.navigation}</strong></div>`;
    if (successCounts.languages > 0)
      html += `<div>🌍 Підтримувані мови: <strong>${successCounts.languages}</strong></div>`;

    html += `
                </div>
            </div>
        `;

    return html;
  }

  /**
   * Генерує детальні рекомендації
   */
  generateDetailedRecommendations(results) {
    let html = '<div class="recommendations">';
    html += "<h3>💡 Детальні рекомендації для покращення доступності</h3>";

    if (results.recommendations && results.recommendations.length > 0) {
      results.recommendations.forEach((rec) => {
        html += `
                    <div class="recommendation-item">
                        <div class="recommendation-category">${
                          rec.category || "Загальне"
                        } - ${rec.priority || "Середній"} пріоритет</div>
                        <div class="recommendation-text">${
                          rec.recommendation || rec
                        }</div>
                    </div>
                `;
      });
    }

    // Рекомендації про мови видалено - не показуємо їх у загальних рекомендаціях

    if (!results.recommendations || results.recommendations.length === 0) {
      // Генеруємо рекомендації на основі скорів (крім локалізації, яка додається окремо)
      Object.entries(results.metrics).forEach(([key, value]) => {
        const score = value * 100;
        if (score < 80 && key !== "localization") {
          // Виключаємо локалізацію
          html += `
                        <div class="recommendation-item">
                            <div class="recommendation-category">${this.getCategoryTitle(
                              key
                            )} - Високий пріоритет</div>
                            <div class="recommendation-text">${this.getRecommendationForMetric(
                              key,
                              score
                            )}</div>
                        </div>
                    `;
        }
      });

      // Перевіряємо чи всі метрики (крім локалізації) мають високий скор
      const nonLocalizationMetrics = Object.entries(results.metrics).filter(
        ([key]) => key !== "localization"
      );
      if (nonLocalizationMetrics.every(([key, value]) => value * 100 >= 80)) {
        html += `
                    <div class="recommendation-item">
                        <div class="recommendation-category">Загальне - Низький пріоритет</div>
                        <div class="recommendation-text">🎉 Відмінна робота! Ваш сайт має високий рівень доступності. Продовжуйте регулярно тестувати доступність при додаванні нового контенту.</div>
                    </div>
                `;
      }
    }

    html += "</div>";
    return html;
  }

  // Методи детального форматування видалені - повернулися до простого стану

  getSubMetricTitle(submetric) {
    const titles = {
      alt_text: "🖼️ Альтернативний текст зображень",
      contrast: "🎨 Контрастність тексту",
      media_accessibility: "🎬 Доступність медіа",
      keyboard_navigation: "⌨️ Клавіатурна навігація",
      structured_navigation: "📋 Структурована навігація",
      instruction_clarity: "📝 Зрозумілість інструкцій",
      input_assistance: "🆘 Допомога при введенні",
      error_support: "⚠️ Підтримка помилок",
      localization: "🌍 Локалізація контенту",
    };
    return titles[submetric] || submetric;
  }

  getSubmetricDescription(submetric, score) {
    if (score >= 90) {
      return '<br><span style="color: #28a745;">Відмінний результат!</span>';
    } else if (score >= 70) {
      return '<br><span style="color: #17a2b8;">Добрий результат</span>';
    } else if (score >= 50) {
      return '<br><span style="color: #ffc107;">Потребує покращення</span>';
    } else {
      return '<br><span style="color: #dc3545;">Критичні проблеми виявлені</span>';
    }
  }

  generateRecommendations(results) {
    let html = '<div class="recommendations">';
    html += "<h3>💡 Рекомендації для покращення доступності</h3>";

    if (results.recommendations && results.recommendations.length > 0) {
      html += "<ul>";
      results.recommendations.forEach((rec) => {
        html += `<li>${rec}</li>`;
      });
      html += "</ul>";
    } else {
      // Генеруємо рекомендації на основі скорів
      html += "<ul>";

      Object.entries(results.metrics).forEach(([key, value]) => {
        const score = value * 100;
        if (score < 80) {
          html += `<li>${this.getRecommendationForMetric(key, score)}</li>`;
        }
      });

      if (Object.values(results.metrics).every((v) => v * 100 >= 80)) {
        html +=
          "<li>🎉 Відмінна робота! Ваш сайт має високий рівень доступності.</li>";
        html +=
          "<li>Продовжуйте регулярно тестувати доступність при додаванні нового контенту.</li>";
      }

      html += "</ul>";
    }

    html += "</div>";
    return html;
  }

  getCategoryTitle(category) {
    const titles = {
      perceptibility: "👁️ Сприйнятність",
      operability: "⌨️ Керованість",
      understandability: "🧠 Зрозумілість",
      localization: "🌍 Локалізація",
    };
    return titles[category] || category;
  }

  formatDetailedMetrics(details) {
    if (typeof details === "object") {
      return Object.entries(details)
        .map(([key, value]) => `<strong>${key}:</strong> ${value}`)
        .join("<br>");
    }
    return details.toString();
  }

  getRecommendationForMetric(metric, score) {
    const recommendations = {
      perceptibility:
        "Покращіть альтернативний текст для зображень та контрастність тексту",
      operability:
        "Забезпечте повну підтримку клавіатурної навігації та зрозумілу структуру",
      understandability:
        "Зробіть інструкції більш зрозумілими та покращіть обробку помилок у формах",
      localization:
        "Додайте правильні мовні атрибути та покращіть локалізацію контенту",
    };
    return (
      recommendations[metric] || `Покращіть показники для категорії ${metric}`
    );
  }

  getScoreClass(score) {
    if (score >= 90) return "score-excellent";
    if (score >= 75) return "score-good";
    if (score >= 60) return "score-fair";
    if (score >= 40) return "score-poor";
    return "score-critical";
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

      if (stored[key]) {
        this.currentResults = stored[key];
        this.displayResults(stored[key]);
      }
    } catch (error) {
      console.log("Немає попередніх результатів");
    }
  }

  async saveResults(results, url) {
    try {
      const key = `results_${this.getUrlKey(url)}`;
      await chrome.storage.local.set({
        [key]: {
          ...results,
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
