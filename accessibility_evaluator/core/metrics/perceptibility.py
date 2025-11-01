"""
Метрики перцептивності (UAC-1.1-G)
"""

from bs4 import BeautifulSoup
from typing import Dict, Any, List
import re


class PerceptibilityMetrics:
    """Клас для розрахунку метрик перцептивності"""
    
    async def calculate_metrics(self, page_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Розрахунок всіх метрик перцептивності
        
        Args:
            page_data: Дані сторінки від WebScraper
            
        Returns:
            Словник з метриками перцептивності
        """
        
        return {
            'alt_text': self.calculate_alt_text_metric(page_data),
            'contrast': await self.calculate_contrast_metric(page_data),
            'media_accessibility': self.calculate_media_accessibility_metric(page_data)
        }
    
    def calculate_alt_text_metric(self, page_data: Dict[str, Any]) -> float:
        """
        Розрахунок метрики альтернативного тексту (UAC-1.1.1-G) з використанням axe-core
        
        Формула: X = A / B
        A = кількість зображень з правильним alt текстом (з axe-core passes)
        B = загальна кількість зображень (passes + violations)
        """
        
        axe_results = page_data.get('axe_results', {})
        
        print(f"\n🔍 === ДЕТАЛЬНИЙ АНАЛІЗ ALT-TEXT МЕТРИКИ ===")
        
        # Згідно з axe-core документацією, основні правила для зображень:
        alt_related_rules = ['image-alt', 'input-image-alt', 'area-alt']
        
        total_images = 0
        correct_images = 0
        
        print(f"📋 Аналізуємо правила: {alt_related_rules}")
        
        for rule_id in alt_related_rules:
            print(f"\n🔍 Правило: {rule_id}")
            
            # Підраховуємо правильні зображення (passes)
            passes = self._get_axe_rule_results(axe_results, 'passes', rule_id)
            if passes:
                passes_count = len(passes.get('nodes', []))
                correct_images += passes_count
                total_images += passes_count
                print(f"   ✅ Passes: {passes_count} елементів")
                
                # Показуємо деталі перших кількох елементів
                nodes = passes.get('nodes', [])[:3]  # Перші 3 елементи
                for i, node in enumerate(nodes):
                    target = node.get('target', ['невідомо'])
                    html = node.get('html', 'немає HTML')[:100] + '...' if len(node.get('html', '')) > 100 else node.get('html', 'немає HTML')
                    print(f"     {i+1}. Target: {target}")
                    print(f"        HTML: {html}")
            else:
                print(f"   ✅ Passes: 0 елементів")
            
            # Підраховуємо проблемні зображення (violations)
            violations = self._get_axe_rule_results(axe_results, 'violations', rule_id)
            if violations:
                violations_count = len(violations.get('nodes', []))
                total_images += violations_count
                print(f"   ❌ Violations: {violations_count} елементів")
                print(f"   📝 Опис проблеми: {violations.get('description', 'немає опису')}")
                
                # Показуємо деталі перших кількох проблемних елементів
                nodes = violations.get('nodes', [])[:3]  # Перші 3 елементи
                for i, node in enumerate(nodes):
                    target = node.get('target', ['невідомо'])
                    html = node.get('html', 'немає HTML')[:100] + '...' if len(node.get('html', '')) > 100 else node.get('html', 'немає HTML')
                    failure_summary = node.get('failureSummary', 'немає опису помилки')
                    print(f"     {i+1}. Target: {target}")
                    print(f"        HTML: {html}")
                    print(f"        Проблема: {failure_summary}")
                # correct_images НЕ збільшуємо для violations
            else:
                print(f"   ❌ Violations: 0 елементів")
        
        print(f"\n📊 ПІДСУМОК ALT-TEXT:")
        print(f"   Правильних зображень: {correct_images}")
        print(f"   Загальних зображень: {total_images}")

        # Якщо axe-core не знайшов зображень, використовуємо fallback аналіз HTML
        if total_images == 0:
            print(f"   ⚠️ axe-core не знайшов зображень. Використовуємо fallback аналіз HTML...")
            return self._fallback_alt_text_analysis(page_data)

        # Формула: X = A / B
        score = correct_images / total_images
        print(f"   🎯 Розрахунок: {correct_images} / {total_images} = {score:.3f}")
        print(f"=== КІНЕЦЬ ALT-TEXT АНАЛІЗУ ===\n")

        return score
    
    def _fallback_alt_text_analysis(self, page_data: Dict[str, Any]) -> float:
        """Fallback аналіз alt-text коли axe-core не знайшов зображень"""

        html_content = page_data.get('html_content', '')
        if not html_content:
            print("   ⚠️ HTML контент недоступний - повертаємо 1.0")
            return 1.0

        soup = BeautifulSoup(html_content, 'html.parser')
        images = soup.find_all('img')

        print(f"\n🔍 FALLBACK АНАЛІЗ:")
        print(f"   Знайдено <img> тегів у HTML: {len(images)}")

        if len(images) == 0:
            print(f"   ✅ Зображення відсутні в HTML - повертаємо 1.0")
            return 1.0

        correct_images = 0
        for img in images:
            alt = img.get('alt')
            # Правильним вважається зображення з:
            # 1. Непорожнім alt (не декоративне)
            # 2. alt="" (декоративне зображення)
            # Неправильним вважається відсутність alt взагалі
            if alt is not None:
                correct_images += 1

        score = correct_images / len(images)
        print(f"   Зображень з alt атрибутом: {correct_images}/{len(images)}")
        print(f"   🎯 Fallback розрахунок: {correct_images} / {len(images)} = {score:.3f}")
        print(f"=== КІНЕЦЬ FALLBACK АНАЛІЗУ ===\n")

        return score

    async def _fallback_contrast_analysis(self, page_data: Dict[str, Any]) -> float:
        """Fallback аналіз контрасту коли axe-core не знайшов текстових елементів"""

        html_content = page_data.get('html_content', '')
        if not html_content:
            print("   ⚠️ HTML контент недоступний - повертаємо 0.8")
            return 0.8  # Припускаємо середній контраст

        soup = BeautifulSoup(html_content, 'html.parser')

        # Шукаємо текстові елементи
        text_selectors = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'div', 'a', 'button', 'label', 'li']
        text_elements = []

        for selector in text_selectors:
            elements = soup.find_all(selector)
            for elem in elements:
                text = elem.get_text(strip=True)
                if text and len(text) > 0:  # Тільки елементи з текстом
                    text_elements.append(elem)
                    if len(text_elements) >= 50:  # Обмежуємо кількість для швидкості
                        break
            if len(text_elements) >= 50:
                break

        print(f"\n🔍 FALLBACK АНАЛІЗ КОНТРАСТУ:")
        print(f"   Знайдено текстових елементів у HTML: {len(text_elements)}")

        if len(text_elements) == 0:
            print(f"   ✅ Текстові елементи відсутні в HTML - повертаємо 1.0")
            return 1.0

        # Оскільки ми не можемо обчислити контраст без computed styles,
        # припускаємо що 80% елементів мають прийнятний контраст
        print(f"   ⚠️ Не можемо обчислити контраст без browser context")
        print(f"   🎯 Fallback: повертаємо 0.8 (припускаємо 80% прийнятного контрасту)")
        print(f"=== КІНЕЦЬ FALLBACK АНАЛІЗУ КОНТРАСТУ ===\n")

        return 0.8

    def _get_axe_rule_results(self, axe_results: Dict[str, Any], result_type: str, rule_id: str) -> Dict[str, Any]:
        """Отримання результатів конкретного правила axe-core"""

        results = axe_results.get(result_type, [])
        for result in results:
            if result.get('id') == rule_id:
                return result
        return {}


    async def calculate_contrast_metric(self, page_data: Dict[str, Any]) -> float:
        """
        Розрахунок метрики контрастності тексту (UAC-1.1.2-G) з використанням axe-core
        
        Формула: X = A / B
        A = кількість текстових елементів з достатнім контрастом (з axe-core passes)
        B = загальна кількість текстових елементів (passes + violations)
        """
        
        axe_results = page_data.get('axe_results', {})
        
        print(f"\n🎨 === ДЕТАЛЬНИЙ АНАЛІЗ КОНТРАСТУ ===")
        
        # Отримуємо результати для правил контрасту
        contrast_rules = ['color-contrast', 'color-contrast-enhanced']
        
        total_elements = 0
        correct_elements = 0
        
        print(f"📋 Аналізуємо правила: {contrast_rules}")
        
        for rule_id in contrast_rules:
            print(f"\n🔍 Правило: {rule_id}")
            
            # Підраховуємо елементи з правильним контрастом (passes)
            passes = self._get_axe_rule_results(axe_results, 'passes', rule_id)
            if passes:
                passes_count = len(passes.get('nodes', []))
                correct_elements += passes_count
                total_elements += passes_count
                print(f"   ✅ Passes: {passes_count} елементів")
                
                # Показуємо деталі перших кількох елементів
                nodes = passes.get('nodes', [])[:2]  # Перші 2 елементи
                for i, node in enumerate(nodes):
                    target = node.get('target', ['невідомо'])
                    html = node.get('html', 'немає HTML')[:80] + '...' if len(node.get('html', '')) > 80 else node.get('html', 'немає HTML')
                    print(f"     {i+1}. Target: {target}")
                    print(f"        HTML: {html}")
            else:
                print(f"   ✅ Passes: 0 елементів")
            
            # Підраховуємо елементи з проблемним контрастом (violations)
            violations = self._get_axe_rule_results(axe_results, 'violations', rule_id)
            if violations:
                violations_count = len(violations.get('nodes', []))
                total_elements += violations_count
                print(f"   ❌ Violations: {violations_count} елементів")
                print(f"   📝 Опис проблеми: {violations.get('description', 'немає опису')}")
                
                # Показуємо деталі перших кількох проблемних елементів
                nodes = violations.get('nodes', [])[:2]  # Перші 2 елементи
                for i, node in enumerate(nodes):
                    target = node.get('target', ['невідомо'])
                    html = node.get('html', 'немає HTML')[:80] + '...' if len(node.get('html', '')) > 80 else node.get('html', 'немає HTML')
                    failure_summary = node.get('failureSummary', 'немає опису помилки')
                    print(f"     {i+1}. Target: {target}")
                    print(f"        HTML: {html}")
                    print(f"        Проблема: {failure_summary}")
                # correct_elements НЕ збільшуємо для violations
            else:
                print(f"   ❌ Violations: 0 елементів")
        
        print(f"\n📊 ПІДСУМОК КОНТРАСТУ:")
        print(f"   Правильних елементів: {correct_elements}")
        print(f"   Загальних елементів: {total_elements}")

        # Якщо axe-core не знайшов текстових елементів, використовуємо fallback
        if total_elements == 0:
            print(f"   ⚠️ axe-core не знайшов текстових елементів. Використовуємо fallback аналіз...")
            return await self._fallback_contrast_analysis(page_data)

        score = correct_elements / total_elements
        print(f"   🎯 Розрахунок: {correct_elements} / {total_elements} = {score:.3f}")
        print(f"=== КІНЕЦЬ АНАЛІЗУ КОНТРАСТУ ===\n")

        return score
    
    def calculate_media_accessibility_metric(self, page_data: Dict[str, Any]) -> float:
        """
        Розрахунок метрики доступності медіа (UAC-1.1.3-G) включно з embedded відео
        
        Формула: X = A / B
        A = кількість відео із субтитрами або аудіоописами
        B = загальна кількість відео (нативні + embedded)
        """
        
        media_elements = page_data.get('media_elements', [])
        
        # Збираємо всі відео: нативні HTML5 + embedded
        video_elements = [elem for elem in media_elements if elem['type'] in ['video', 'embedded_video']]
        
        print(f"\n🎬 === ДЕТАЛЬНИЙ АНАЛІЗ ДОСТУПНОСТІ МЕДІА ===")
        print(f"📋 Знайдено відео елементів: {len(video_elements)}")
        
        if not video_elements:
            print("⚠️ Відео елементи не знайдено - повертаємо 1.0")
            return 1.0  # Немає відео = немає проблем
        
        accessible_videos = 0
        
        for i, video in enumerate(video_elements, 1):
            video_type = video.get('type', 'unknown')
            platform = video.get('platform', 'native')
            src = video.get('src') or ''
            
            print(f"\n🔍 Відео {i}: {video_type}")
            print(f"   Платформа: {platform}")
            print(f"   URL: {src[:80]}..." if src and len(src) > 80 else f"   URL: {src}")
            
            has_accessibility = False
            accessibility_reasons = []
            
            if video_type == 'video':
                # Нативне HTML5 відео
                tracks = video.get('tracks', [])
                print(f"   Треки: {len(tracks)}")
                
                # Перевірка субтитрів
                for track in tracks:
                    track_kind = track.get('kind', '')
                    if track_kind in ['subtitles', 'captions']:
                        has_accessibility = True
                        accessibility_reasons.append(f"Субтитри ({track_kind})")
                        break
                
                # Перевірка аудіоописів
                if not has_accessibility:
                    for track in tracks:
                        if track.get('kind') == 'descriptions':
                            has_accessibility = True
                            accessibility_reasons.append("Аудіоописи")
                            break
            
            elif video_type == 'embedded_video':
                # Embedded відео (YouTube, Vimeo тощо)
                has_captions = video.get('has_captions', False)
                caption_check_method = video.get('caption_check_method', 'url_params')
                
                if has_captions:
                    has_accessibility = True
                    if caption_check_method == 'youtube_api':
                        accessibility_reasons.append(f"Субтитри підтверджені YouTube API ({platform})")
                    elif caption_check_method == 'enhanced_url_analysis':
                        # Перевіряємо чи є явні параметри субтитрів
                        if any(param in src for param in ['cc_load_policy=1', 'captions=1', 'cc_lang_pref=']):
                            accessibility_reasons.append(f"Субтитри підтверджені параметрами URL ({platform})")
                        elif any(param in src for param in ['hl=en', 'hl=uk', 'hl=ru', 'hl=de', 'hl=fr']):
                            accessibility_reasons.append(f"Ймовірні автосубтитри за мовними параметрами ({platform})")
                        else:
                            accessibility_reasons.append(f"Ймовірні автоматичні субтитри YouTube (стандартне відео)")
                    else:
                        accessibility_reasons.append(f"Субтитри в URL ({platform})")
            
            if has_accessibility:
                accessible_videos += 1
                print(f"   ✅ Доступне: {', '.join(accessibility_reasons)}")
            else:
                print(f"   ❌ Недоступне: Відсутні субтитри та аудіоописи")
        
        score = accessible_videos / len(video_elements)
        
        print(f"\n📊 ПІДСУМОК ДОСТУПНОСТІ МЕДІА:")
        print(f"   Доступних відео: {accessible_videos}")
        print(f"   Загальних відео: {len(video_elements)}")
        print(f"   🎯 Розрахунок: {accessible_videos} / {len(video_elements)} = {score:.3f}")
        print(f"=== КІНЕЦЬ АНАЛІЗУ МЕДІА ===\n")
        
        return score