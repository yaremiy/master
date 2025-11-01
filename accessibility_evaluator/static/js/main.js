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

        // Генеруємо детальний звіт через /api/report (той самий template що й для експорту)
        const reportResponse = await fetch('/api/report', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(data)
        });

        const reportHTML = await reportResponse.text();

        // Вставляємо згенерований звіт
        resultsContent.innerHTML = reportHTML;

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
