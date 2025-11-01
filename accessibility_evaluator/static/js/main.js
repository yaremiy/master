// Tab switching
function switchTab(tabName) {
    const tabs = document.querySelectorAll('.tab-content');
    const buttons = document.querySelectorAll('.tab-button');

    tabs.forEach(tab => tab.classList.remove('active'));
    buttons.forEach(btn => btn.classList.remove('active'));

    document.getElementById(`${tabName}-tab`).classList.add('active');
    event.target.classList.add('active');
}

// Form submission
document.getElementById('analyze-form')?.addEventListener('submit', async (e) => {
    e.preventDefault();

    const url = document.getElementById('url-input').value;
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    const resultsContent = document.getElementById('results-content');

    // Show loading
    loading.style.display = 'block';
    results.style.display = 'none';

    try {
        const response = await fetch('/api/evaluate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url })
        });

        const data = await response.json();

        if (data.status === 'error') {
            throw new Error(data.error || 'Помилка аналізу');
        }

        // Display results
        resultsContent.innerHTML = `
            <div class="score-card">
                <h2>Загальний скор: ${(data.final_score * 100).toFixed(1)}%</h2>
                <p class="quality-level">${data.quality_level}</p>
            </div>

            <div class="metrics-grid">
                <div class="metric">
                    <h4>👁️ Перцептивність</h4>
                    <div class="score">${(data.subscores.perceptibility * 100).toFixed(1)}%</div>
                </div>
                <div class="metric">
                    <h4>⌨️ Керованість</h4>
                    <div class="score">${(data.subscores.operability * 100).toFixed(1)}%</div>
                </div>
                <div class="metric">
                    <h4>💡 Зрозумілість</h4>
                    <div class="score">${(data.subscores.understandability * 100).toFixed(1)}%</div>
                </div>
                <div class="metric">
                    <h4>🌍 Локалізація</h4>
                    <div class="score">${(data.subscores.localization * 100).toFixed(1)}%</div>
                </div>
            </div>

            <div class="recommendations">
                <h3>Рекомендації:</h3>
                <ul>
                    ${data.recommendations.map(r => `<li>${r.recommendation}</li>`).join('')}
                </ul>
            </div>
        `;

        results.style.display = 'block';

    } catch (error) {
        resultsContent.innerHTML = `
            <div class="error">
                <h3>❌ Помилка</h3>
                <p>${error.message}</p>
            </div>
        `;
        results.style.display = 'block';
    } finally {
        loading.style.display = 'none';
    }
});
