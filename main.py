from playwright.sync_api import sync_playwright
import json
import sys
import os
from metrics import calculate_custom_metrics, compute_overall_score

def run_accessibility_checks(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()

        print(f"Navigating to: {url}")
        page.goto(url, wait_until="networkidle")

        # Inject axe-core script
        axe_path = os.path.abspath("node_modules/axe-core/axe.min.js")
        if not os.path.exists(axe_path):
            print("ERROR: axe-core not found. Did you run 'npm install axe-core'?")
            return

        page.add_script_tag(path=axe_path)

        # Run axe-core evaluation
        result = page.evaluate("""() => {
            return new Promise((resolve) => {
                axe.run().then(results => resolve(results));
            });
        }""")

        browser.close()
        return result

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py <URL>")
        sys.exit(1)

    url = sys.argv[1]
    results = run_accessibility_checks(url)

    if not results:
        print("❌ Axe-core analysis failed. Make sure axe-core is installed and the page loaded properly.")
        sys.exit(1)

    output_file = "report.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"✅ Accessibility report saved to '{output_file}'")

    metrics = calculate_custom_metrics(results)
    full_score, sub_scores = compute_overall_score(metrics)

    print("\n📊 Accessibility Metrics:")
    for key, val in metrics.items():
        print(f"  {key}: {val}")

    print("\n🧮 Subscores:")
    for key, val in sub_scores.items():
        print(f"  {key}: {val:.2f}")

    print(f"\n🏁 Final Accessibility Score: {full_score:.3f}")

    output_file = "report.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"✅ Accessibility report saved to '{output_file}'")

    metrics = calculate_custom_metrics(results)
    full_score, sub_scores = compute_overall_score(metrics)

    print("\n📊 Accessibility Metrics:")
    for key, val in metrics.items():
        print(f"  {key}: {val}")

    print("\n🧮 Subscores:")
    for key, val in sub_scores.items():
        print(f"  {key}: {val:.2f}")

    print(f"\n🏁 Final Accessibility Score: {full_score:.3f}")
