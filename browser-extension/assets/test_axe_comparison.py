#!/usr/bin/env python3
"""
Тестовий скрипт для порівняння axe-core результатів:
1. page.goto(url) - стандартний підхід
2. page.set_content(html) - наш підхід з розширення
"""

import asyncio
from playwright.async_api import async_playwright
import json
import os

TEST_URL = "https://jobs.dou.ua/companies/ninetwothree/"


async def run_axe_analysis(page):
    """Запускає axe-core на сторінці"""

    axe_path = "node_modules/axe-core/axe.min.js"
    if not os.path.exists(axe_path):
        print(f"❌ axe-core не знайдено: {axe_path}")
        return {}

    # Завантажуємо axe-core
    await page.add_script_tag(path=axe_path)

    # Запускаємо аналіз
    axe_results = await page.evaluate("""
        () => {
            return new Promise((resolve) => {
                if (typeof axe !== 'undefined') {
                    axe.run().then(results => {
                        resolve(results);
                    }).catch(error => {
                        console.error('Axe error:', error);
                        resolve({});
                    });
                } else {
                    resolve({});
                }
            });
        }
    """)

    return axe_results


def analyze_axe_results(results, label):
    """Аналізує результати axe-core"""

    print(f"\n{'='*60}")
    print(f"{label}")
    print(f"{'='*60}")

    if not results:
        print("❌ Немає результатів axe-core")
        return {
            'image_alt_violations': 0,
            'image_alt_passes': 0,
            'contrast_violations': 0,
            'contrast_passes': 0,
        }

    violations = results.get('violations', [])
    passes = results.get('passes', [])

    print(f"\n📊 Загальна статистика:")
    print(f"   Violations: {len(violations)} правил")
    print(f"   Passes: {len(passes)} правил")

    # Шукаємо image-alt та color-contrast
    image_alt_v = None
    image_alt_p = None
    contrast_v = None
    contrast_p = None

    for v in violations:
        if v.get('id') == 'image-alt':
            image_alt_v = v
        elif v.get('id') == 'color-contrast':
            contrast_v = v

    for p in passes:
        if p.get('id') == 'image-alt':
            image_alt_p = p
        elif p.get('id') == 'color-contrast':
            contrast_p = p

    # Image-alt аналіз
    print(f"\n🖼️  IMAGE-ALT:")
    if image_alt_v:
        nodes_count = len(image_alt_v.get('nodes', []))
        print(f"   ❌ Violations: {nodes_count} зображень без alt")
        for i, node in enumerate(image_alt_v.get('nodes', [])[:3]):
            print(f"      {i+1}. {node.get('html', '')[:80]}...")
    else:
        print(f"   ✅ Violations: 0")

    if image_alt_p:
        nodes_count = len(image_alt_p.get('nodes', []))
        print(f"   ✅ Passes: {nodes_count} зображень з alt")
        for i, node in enumerate(image_alt_p.get('nodes', [])[:3]):
            print(f"      {i+1}. {node.get('html', '')[:80]}...")
    else:
        print(f"   ❌ Passes: 0")

    # Color-contrast аналіз
    print(f"\n🎨 COLOR-CONTRAST:")
    if contrast_v:
        nodes_count = len(contrast_v.get('nodes', []))
        print(f"   ❌ Violations: {nodes_count} елементів з поганим контрастом")
        for i, node in enumerate(contrast_v.get('nodes', [])[:3]):
            print(f"      {i+1}. {node.get('html', '')[:80]}...")
    else:
        print(f"   ✅ Violations: 0")

    if contrast_p:
        nodes_count = len(contrast_p.get('nodes', []))
        print(f"   ✅ Passes: {nodes_count} елементів з нормальним контрастом")
    else:
        print(f"   ❌ Passes: 0")

    return {
        'image_alt_violations': len(image_alt_v.get('nodes', [])) if image_alt_v else 0,
        'image_alt_passes': len(image_alt_p.get('nodes', [])) if image_alt_p else 0,
        'contrast_violations': len(contrast_v.get('nodes', [])) if contrast_v else 0,
        'contrast_passes': len(contrast_p.get('nodes', [])) if contrast_p else 0,
    }


async def test_approach_1_url():
    """Підхід 1: page.goto(url) - стандартний"""

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print(f"\n🌐 Завантаження сторінки через page.goto(url)...")
        await page.goto(TEST_URL, wait_until="networkidle", timeout=60000)

        # Отримуємо HTML для збереження
        html_content = await page.content()

        # Запускаємо axe-core
        axe_results = await run_axe_analysis(page)

        await browser.close()

        return html_content, axe_results


async def test_approach_2_set_content(html_content):
    """Підхід 2: page.set_content(html) - наш підхід"""

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print(f"\n📄 Завантаження HTML через page.set_content()...")
        await page.set_content(html_content, wait_until="domcontentloaded")

        # Запускаємо axe-core
        axe_results = await run_axe_analysis(page)

        await browser.close()

        return axe_results


async def test_approach_3_saved_html():
    """Підхід 3: Використання збереженого HTML з розширення"""

    html_file = "temp_html_content.html"
    if not os.path.exists(html_file):
        print(f"❌ Файл {html_file} не знайдено")
        return None

    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        print(f"\n📄 Завантаження збереженого HTML з розширення...")
        await page.set_content(html_content, wait_until="domcontentloaded")

        # Запускаємо axe-core
        axe_results = await run_axe_analysis(page)

        await browser.close()

        return axe_results


async def main():
    print(f"\n{'#'*60}")
    print(f"# ПОРІВНЯННЯ AXE-CORE РЕЗУЛЬТАТІВ")
    print(f"# URL: {TEST_URL}")
    print(f"{'#'*60}")

    # Тест 1: page.goto(url)
    html_from_goto, results_1 = await test_approach_1_url()
    stats_1 = analyze_axe_results(results_1, "ПІДХІД 1: page.goto(url)")

    # Зберігаємо HTML для порівняння
    with open('test_html_from_goto.html', 'w', encoding='utf-8') as f:
        f.write(html_from_goto)
    print(f"\n💾 HTML збережено в test_html_from_goto.html")

    # Тест 2: page.set_content(html) з HTML отриманого через goto
    results_2 = await test_approach_2_set_content(html_from_goto)
    stats_2 = analyze_axe_results(results_2, "ПІДХІД 2: page.set_content(html з goto)")

    # Тест 3: page.set_content() з HTML з розширення
    results_3 = await test_approach_3_saved_html()
    if results_3:
        stats_3 = analyze_axe_results(results_3, "ПІДХІД 3: page.set_content(html з розширення)")

    # Порівняння
    print(f"\n{'='*60}")
    print(f"ПОРІВНЯННЯ РЕЗУЛЬТАТІВ")
    print(f"{'='*60}")

    print(f"\n{'Метрика':<30} {'goto(url)':<15} {'set_content':<15}")
    print(f"{'-'*60}")
    print(f"{'Image-alt violations':<30} {stats_1['image_alt_violations']:<15} {stats_2['image_alt_violations']:<15}")
    print(f"{'Image-alt passes':<30} {stats_1['image_alt_passes']:<15} {stats_2['image_alt_passes']:<15}")
    print(f"{'Contrast violations':<30} {stats_1['contrast_violations']:<15} {stats_2['contrast_violations']:<15}")
    print(f"{'Contrast passes':<30} {stats_1['contrast_passes']:<15} {stats_2['contrast_passes']:<15}")

    if results_3:
        print(f"\n{'Метрика':<30} {'Розширення HTML':<15}")
        print(f"{'-'*60}")
        stats_3_dict = analyze_axe_results(results_3, "")
        print(f"{'Image-alt violations':<30} {stats_3_dict['image_alt_violations']:<15}")
        print(f"{'Image-alt passes':<30} {stats_3_dict['image_alt_passes']:<15}")
        print(f"{'Contrast violations':<30} {stats_3_dict['contrast_violations']:<15}")
        print(f"{'Contrast passes':<30} {stats_3_dict['contrast_passes']:<15}")

    # Висновок
    print(f"\n{'='*60}")
    print(f"ВИСНОВОК")
    print(f"{'='*60}")

    if stats_1 == stats_2:
        print("✅ Результати ІДЕНТИЧНІ! page.set_content() працює як page.goto()")
    else:
        print("❌ Результати РІЗНІ!")

        if stats_2['image_alt_passes'] == 0 and stats_2['contrast_passes'] == 0:
            print("\n⚠️  ПРОБЛЕМА: axe-core не знаходить елементи при page.set_content()")
            print("   Можливі причини:")
            print("   1. Відносні URL не завантажуються (img src, link href)")
            print("   2. CSS не завантажується (потрібен для color-contrast)")
            print("   3. JavaScript не виконується (може змінювати DOM)")
            print("   4. page.set_content() не чекає на ресурси")
        else:
            print(f"\n📊 Різниця в результатах:")
            print(f"   Image-alt passes: {stats_1['image_alt_passes']} -> {stats_2['image_alt_passes']} ({stats_2['image_alt_passes'] - stats_1['image_alt_passes']:+d})")
            print(f"   Contrast passes: {stats_1['contrast_passes']} -> {stats_2['contrast_passes']} ({stats_2['contrast_passes'] - stats_1['contrast_passes']:+d})")


if __name__ == "__main__":
    asyncio.run(main())
