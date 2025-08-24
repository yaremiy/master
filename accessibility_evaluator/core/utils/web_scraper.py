"""
Утиліта для збору даних з вебсайтів
"""

from playwright.async_api import async_playwright, Page
from bs4 import BeautifulSoup
from typing import Dict, Any, List
import asyncio
from .form_tester import FormTester


class WebScraper:
    """Клас для збору даних з вебсайтів за допомогою Playwright"""
    
    def __init__(self):
        self.browser = None
        self.page = None
        self.form_tester = FormTester()
    
    async def scrape_page(self, url: str) -> Dict[str, Any]:
        """
        Збирає всі необхідні дані з вебсторінки
        
        Args:
            url: URL для аналізу
            
        Returns:
            Словник з даними сторінки
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            # Налаштування таймаутів
            page.set_default_timeout(60000)  # 60 секунд
            page.set_default_navigation_timeout(60000)
            
            try:
                # Навігація до сторінки з кількома спробами
                print(f"🌐 Завантаження сторінки: {url}")
                
                try:
                    await page.goto(url, wait_until="networkidle", timeout=60000)
                except Exception as e:
                    print(f"⚠️ Networkidle failed, trying domcontentloaded: {e}")
                    await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                
                # Збір основних даних
                print("📄 Отримання HTML контенту...")
                html_content = await page.content()
                
                print("🔍 Збір інтерактивних елементів...")
                interactive_elements = await self._get_interactive_elements(page)
                
                print("📝 Збір текстових елементів...")
                text_elements = await self._get_text_elements(page)
                
                print("🎬 Збір медіа елементів...")
                media_elements = await self._get_media_elements(page)
                
                print("📋 Збір форм...")
                form_elements = await self._get_form_elements(page)
                
                print("🎨 Збір стилів...")
                computed_styles = await self._get_computed_styles(page)
                
                print("🔍 Запуск axe-core аналізу...")
                axe_results = await self._run_axe_core(page)
                
                print("⌨️ Тестування клавіатурної навігації...")
                focus_test_results = await self._test_keyboard_focus(page)
                
                print("🧪 Динамічне тестування форм...")
                form_error_test_results = await self._test_form_error_behavior(page)
                
                page_data = {
                    'url': url,
                    'html_content': html_content,
                    'title': await page.title(),
                    'page_depth': self._calculate_page_depth(url),
                    'interactive_elements': interactive_elements,
                    'text_elements': text_elements,
                    'media_elements': media_elements,
                    'form_elements': form_elements,
                    'computed_styles': computed_styles,
                    'axe_results': axe_results,  # Додаємо результати axe-core
                    'focus_test_results': focus_test_results,  # Додаємо результати тестування фокусу
                    'form_error_test_results': form_error_test_results,  # Додаємо результати динамічного тестування форм
                    'page_object': page  # Зберігаємо для подальшого використання
                }
                
                print(f"✅ Збір даних завершено. Знайдено:")
                print(f"   📝 Текстових елементів: {len(text_elements)}")
                print(f"   🔗 Інтерактивних елементів: {len(interactive_elements)}")
                print(f"   🎬 Медіа елементів: {len(media_elements)}")
                print(f"   📋 Форм: {len(form_elements)}")
                
                return page_data
                
            except Exception as e:
                raise Exception(f"Помилка при завантаженні сторінки {url}: {str(e)}")
            
            finally:
                await browser.close()
    
    def _calculate_page_depth(self, url: str) -> int:
        """Розрахунок глибини сторінки в ієрархії сайту"""
        from urllib.parse import urlparse
        
        parsed = urlparse(url)
        path_parts = [part for part in parsed.path.split('/') if part]
        return len(path_parts)
    
    async def _get_interactive_elements(self, page: Page) -> List[Dict[str, Any]]:
        """Збір інтерактивних елементів"""
        
        selectors = [
            'button', 'a[href]', 'input', 'select', 'textarea',
            '[tabindex]', '[onclick]', '[role="button"]', '[role="link"]'
        ]
        
        elements = []
        
        for selector in selectors:
            page_elements = await page.query_selector_all(selector)
            
            for element in page_elements:
                element_data = {
                    'tag': await element.evaluate('el => el.tagName.toLowerCase()'),
                    'type': await element.get_attribute('type'),
                    'tabindex': await element.get_attribute('tabindex'),
                    'role': await element.get_attribute('role'),
                    'aria_label': await element.get_attribute('aria-label'),
                    'text': await element.inner_text(),
                    'is_visible': await element.is_visible(),
                    'is_enabled': await element.is_enabled()
                }
                elements.append(element_data)
        
        return elements
    
    async def _get_text_elements(self, page: Page) -> List[Dict[str, Any]]:
        """Збір текстових елементів для аналізу контрасту"""
        
        text_selectors = ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'div', 'a', 'button', 'label']
        elements = []
        
        for selector in text_selectors:
            page_elements = await page.query_selector_all(selector)
            
            for element in page_elements:
                text = await element.inner_text()
                if text.strip():  # Тільки елементи з текстом
                    
                    # Отримання computed styles
                    styles = await element.evaluate('''
                        el => {
                            const computed = window.getComputedStyle(el);
                            return {
                                color: computed.color,
                                backgroundColor: computed.backgroundColor,
                                fontSize: computed.fontSize,
                                fontWeight: computed.fontWeight
                            };
                        }
                    ''')
                    
                    element_data = {
                        'tag': await element.evaluate('el => el.tagName.toLowerCase()'),
                        'text': text,
                        'styles': styles,
                        'is_visible': await element.is_visible()
                    }
                    elements.append(element_data)
        
        return elements
    
    async def _get_media_elements(self, page: Page) -> List[Dict[str, Any]]:
        """Збір медіа елементів"""
        
        elements = []
        
        # Зображення
        images = await page.query_selector_all('img')
        for img in images:
            element_data = {
                'type': 'image',
                'src': await img.get_attribute('src'),
                'alt': await img.get_attribute('alt'),
                'title': await img.get_attribute('title'),
                'aria_label': await img.get_attribute('aria-label'),
                'is_decorative': await img.get_attribute('role') == 'presentation'
            }
            elements.append(element_data)
        
        # Відео
        videos = await page.query_selector_all('video')
        for video in videos:
            tracks = await video.query_selector_all('track')
            track_data = []
            
            for track in tracks:
                track_info = {
                    'kind': await track.get_attribute('kind'),
                    'src': await track.get_attribute('src'),
                    'srclang': await track.get_attribute('srclang')
                }
                track_data.append(track_info)
            
            element_data = {
                'type': 'video',
                'src': await video.get_attribute('src'),
                'tracks': track_data,
                'controls': await video.get_attribute('controls') is not None
            }
            elements.append(element_data)
        
        # Аудіо
        audios = await page.query_selector_all('audio')
        for audio in audios:
            element_data = {
                'type': 'audio',
                'src': await audio.get_attribute('src'),
                'controls': await audio.get_attribute('controls') is not None
            }
            elements.append(element_data)
        
        # Embedded відео (YouTube, Vimeo, тощо)
        iframes = await page.query_selector_all('iframe')
        for iframe in iframes:
            src = await iframe.get_attribute('src') or ''
            
            # Перевіряємо чи це відео платформа
            if self._is_video_embed(src):
                platform = self._detect_video_platform(src)
                iframe_id = await iframe.get_attribute('id')
                
                element_data = {
                    'type': 'embedded_video',
                    'src': src,
                    'title': await iframe.get_attribute('title'),
                    'platform': platform,
                    'tracks': [],  # Embedded відео не мають HTML <track> елементів
                    'has_captions': self._check_embed_captions(src, platform),
                    'width': await iframe.get_attribute('width'),
                    'height': await iframe.get_attribute('height'),
                    'allowfullscreen': await iframe.get_attribute('allowfullscreen') is not None,
                    'iframe_id': iframe_id
                }
                
                # Для YouTube відео використовуємо покращений URL аналіз
                if platform == 'youtube':
                    element_data['caption_check_method'] = 'enhanced_url_analysis'
                    # Покращена перевірка субтитрів
                    enhanced_captions = self._enhanced_youtube_caption_check(src)
                    if enhanced_captions is not None:
                        element_data['has_captions'] = enhanced_captions
                        print(f"   🎬 Покращений URL аналіз: {enhanced_captions}")
                    
                    # YouTube API як експериментальна функція (можна увімкнути при потребі)
                    # api_captions = await self._check_youtube_captions_via_api(page, iframe, src)
                    # if api_captions is not None:
                    #     element_data['has_captions'] = api_captions
                    #     element_data['caption_check_method'] = 'youtube_api'
                
                elements.append(element_data)
        
        return elements
    
    def _is_video_embed(self, src: str) -> bool:
        """Перевіряє чи це embedded відео"""
        if not src:
            return False
        
        video_platforms = [
            'youtube.com', 'youtu.be',
            'vimeo.com',
            'dailymotion.com',
            'twitch.tv',
            'facebook.com/plugins/video',
            'player.vimeo.com'
        ]
        
        return any(platform in src.lower() for platform in video_platforms)
    
    def _detect_video_platform(self, src: str) -> str:
        """Визначає платформу відео"""
        src_lower = src.lower()
        
        if 'youtube.com' in src_lower or 'youtu.be' in src_lower:
            return 'youtube'
        elif 'vimeo.com' in src_lower:
            return 'vimeo'
        elif 'dailymotion.com' in src_lower:
            return 'dailymotion'
        elif 'twitch.tv' in src_lower:
            return 'twitch'
        elif 'facebook.com' in src_lower:
            return 'facebook'
        else:
            return 'unknown'
    
    def _check_embed_captions(self, src: str, platform: str) -> bool:
        """Перевіряє наявність субтитрів в embedded відео за URL параметрами"""
        
        if platform == 'youtube':
            # YouTube параметри для субтитрів
            caption_params = [
                'cc_load_policy=1',  # Автоматично завантажувати субтитри
                'captions=1',        # Увімкнені субтитри
                'cc_lang_pref=',     # Переважна мова субтитрів
            ]
            
            # Перевіряємо точні параметри
            has_captions = any(param in src for param in caption_params)
            
            # Додаткова перевірка: якщо є мовні параметри, ймовірно є субтитри
            if not has_captions:
                language_params = ['hl=uk', 'hl=en', 'hl=ru', 'hl=de', 'hl=fr', 'hl=es']
                has_language = any(param in src for param in language_params)
                if has_language:
                    # Якщо вказана мова, ймовірно є автоматичні субтитри
                    return True
            
            return has_captions
        
        elif platform == 'vimeo':
            # Vimeo параметри для субтитрів
            caption_params = [
                'texttrack=1',       # Увімкнені текстові доріжки
                'captions=1'         # Увімкнені субтитри
            ]
            return any(param in src for param in caption_params)
        
        elif platform == 'dailymotion':
            # Dailymotion параметри
            caption_params = [
                'subtitles-default=',
                'ui-subtitles-available='
            ]
            return any(param in src for param in caption_params)
        
        # Для інших платформ поки що не можемо визначити з URL
        return False
    
    def _enhanced_youtube_caption_check(self, src: str) -> bool:
        """Покращена перевірка субтитрів YouTube з м'яким підходом"""
        
        # Витягуємо video ID
        video_id = self._extract_youtube_video_id(src)
        if not video_id:
            return False
        
        # 1. Перевіряємо явні параметри субтитрів (100% впевненість)
        explicit_caption_params = [
            'cc_load_policy=1',  # Автоматично завантажувати субтитри
            'captions=1',        # Увімкнені субтитри
            'cc_lang_pref=',     # Переважна мова субтитрів
        ]
        
        if any(param in src for param in explicit_caption_params):
            return True
        
        # 2. Перевіряємо мовні параметри (високая ймовірність автосубтитрів)
        language_params = [
            'hl=en', 'hl=uk', 'hl=ru', 'hl=de', 'hl=fr', 'hl=es', 
            'hl=it', 'hl=pt', 'hl=ja', 'hl=ko', 'hl=zh'
        ]
        
        has_language_param = any(param in src for param in language_params)
        if has_language_param:
            return True
        
        # 3. М'який підхід: припускаємо що більшість YouTube відео має автосубтитри
        if len(video_id) == 11:  # Стандартний YouTube video ID
            # YouTube зазвичай генерує автоматичні субтитри для:
            # - Відео англійською мовою
            # - Популярних відео
            # - Відео з чіткою мовою
            # Тому припускаємо наявність субтитрів
            return True
        
        # 4. Якщо video ID нестандартний - консервативний підхід
        return False
    
    async def _check_youtube_captions_via_api(self, page: Page, iframe, src: str) -> bool:
        """Перевірка субтитрів YouTube через YouTube IFrame API"""
        
        try:
            # Витягуємо video ID з URL
            video_id = self._extract_youtube_video_id(src)
            if not video_id:
                return None
            
            # Створюємо унікальний ID для iframe якщо його немає
            iframe_id = await iframe.get_attribute('id')
            if not iframe_id:
                iframe_id = f'youtube_player_{video_id}'
                await iframe.evaluate(f'(element) => element.id = "{iframe_id}"')
            
            # Впроваджуємо YouTube API та перевіряємо субтитри з правильними затримками
            captions_available = await page.evaluate(f"""
                async () => {{
                    return new Promise((resolve) => {{
                        let apiReady = false;
                        let playerReady = false;
                        
                        // Функція для перевірки субтитрів
                        function checkCaptions() {{
                            if (!apiReady) {{
                                console.log('YouTube API not ready yet');
                                return;
                            }}
                            
                            try {{
                                console.log('Creating YouTube player for {iframe_id}');
                                const player = new YT.Player('{iframe_id}', {{
                                    events: {{
                                        'onReady': (event) => {{
                                            console.log('YouTube player ready, checking captions...');
                                            
                                            // Додаємо затримку для повної ініціалізації
                                            setTimeout(() => {{
                                                try {{
                                                    const tracks = event.target.getOption('captions', 'tracklist');
                                                    const hasSubtitles = tracks && tracks.length > 0;
                                                    
                                                    console.log('YouTube captions result:', hasSubtitles, tracks);
                                                    resolve(hasSubtitles);
                                                }} catch (error) {{
                                                    console.log('Error getting captions:', error);
                                                    // Спробуємо альтернативний метод
                                                    try {{
                                                        const availableOptions = event.target.getOptions();
                                                        console.log('Available player options:', availableOptions);
                                                        resolve(null); // Не вдалося визначити
                                                    }} catch (error2) {{
                                                        console.log('Alternative method failed:', error2);
                                                        resolve(null);
                                                    }}
                                                }}
                                            }}, 2000); // Затримка 2 секунди для повної ініціалізації
                                        }},
                                        'onError': (error) => {{
                                            console.log('YouTube player error:', error);
                                            resolve(null);
                                        }},
                                        'onStateChange': (event) => {{
                                            console.log('YouTube player state changed:', event.data);
                                        }}
                                    }}
                                }});
                            }} catch (error) {{
                                console.log('Error creating YouTube player:', error);
                                resolve(null);
                            }}
                        }}
                        
                        // Перевіряємо чи вже завантажений YouTube API
                        if (typeof YT !== 'undefined' && YT.Player) {{
                            console.log('YouTube API already loaded');
                            apiReady = true;
                            checkCaptions();
                        }} else {{
                            console.log('Loading YouTube API...');
                            
                            // Завантажуємо YouTube IFrame API
                            const script = document.createElement('script');
                            script.src = 'https://www.youtube.com/iframe_api';
                            
                            // Глобальний callback для API готовності
                            window.onYouTubeIframeAPIReady = () => {{
                                console.log('YouTube API loaded and ready');
                                apiReady = true;
                                // Додаємо додаткову затримку після завантаження API
                                setTimeout(checkCaptions, 1000);
                            }};
                            
                            script.onerror = () => {{
                                console.log('Failed to load YouTube API');
                                resolve(null);
                            }};
                            
                            document.head.appendChild(script);
                        }}
                        
                        // Загальний таймаут на випадок якщо щось пішло не так
                        setTimeout(() => {{
                            console.log('YouTube API check timeout');
                            resolve(null);
                        }}, 15000); // Збільшуємо таймаут до 15 секунд
                    }});
                }}
            """)
            
            print(f"   🎬 YouTube API перевірка субтитрів: {captions_available}")
            return captions_available
            
        except Exception as e:
            print(f"   ❌ Помилка YouTube API перевірки: {str(e)}")
            return None
    
    def _extract_youtube_video_id(self, url: str) -> str:
        """Витягує video ID з YouTube URL"""
        
        import re
        
        # Різні формати YouTube URL
        patterns = [
            r'youtube\.com/embed/([a-zA-Z0-9_-]+)',
            r'youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
            r'youtu\.be/([a-zA-Z0-9_-]+)',
            r'youtube\.com/v/([a-zA-Z0-9_-]+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    async def _get_form_elements(self, page: Page) -> List[Dict[str, Any]]:
        """Збір елементів форм"""
        
        forms = await page.query_selector_all('form')
        form_data = []
        
        for form in forms:
            # Поля форми
            fields = await form.query_selector_all('input, textarea, select')
            field_data = []
            
            for field in fields:
                field_info = {
                    'tag': await field.evaluate('el => el.tagName.toLowerCase()'),
                    'type': await field.get_attribute('type'),
                    'name': await field.get_attribute('name'),
                    'id': await field.get_attribute('id'),
                    'placeholder': await field.get_attribute('placeholder'),
                    'required': await field.get_attribute('required') is not None,
                    'autocomplete': await field.get_attribute('autocomplete'),
                    'aria_describedby': await field.get_attribute('aria-describedby'),
                    'aria_label': await field.get_attribute('aria-label')
                }
                field_data.append(field_info)
            
            # Labels
            labels = await form.query_selector_all('label')
            label_data = []
            
            for label in labels:
                label_info = {
                    'for': await label.get_attribute('for'),
                    'text': await label.inner_text()
                }
                label_data.append(label_info)
            
            form_info = {
                'action': await form.get_attribute('action'),
                'method': await form.get_attribute('method'),
                'novalidate': await form.get_attribute('novalidate') is not None,
                'fields': field_data,
                'labels': label_data
            }
            form_data.append(form_info)
        
        return form_data
    
    async def _test_form_error_behavior(self, page: Page) -> List[Dict[str, Any]]:
        """Динамічне тестування поведінки форм при помилках"""
        
        print("🧪 Початок динамічного тестування форм...")
        
        # Знаходимо всі форми на сторінці
        forms = await page.query_selector_all('form')
        form_test_results = []
        
        for i, form in enumerate(forms):
            try:
                # Спробуємо знайти ID форми для більш точного селектора
                form_id = await form.get_attribute('id')
                if form_id:
                    form_selector = f'#{form_id}'
                else:
                    form_selector = f'form:nth-child({i+1})'
                
                print(f"🔍 Тестування форми {i+1}: {form_selector}")
                
                # Виконуємо систематичне динамічне тестування
                test_result = await self.form_tester.test_form_error_behavior_systematic(page, form_selector)
                
                # Додаємо метадані
                test_result['form_index'] = i + 1
                test_result['form_selector'] = form_selector
                
                form_test_results.append(test_result)
                
                print(f"✅ Форма {i+1} протестована. Якість: {test_result.get('quality_score', 0):.3f}")
                
            except Exception as e:
                print(f"❌ Помилка тестування форми {i+1}: {str(e)}")
                form_test_results.append({
                    'form_index': i + 1,
                    'form_selector': f'form:nth-of-type({i+1})',
                    'error': str(e),
                    'quality_score': 0.0
                })
        
        if not form_test_results:
            print("⚠️ Форми для тестування не знайдено")
        else:
            avg_quality = sum(result.get('quality_score', 0) for result in form_test_results) / len(form_test_results)
            print(f"📊 Динамічне тестування завершено. Середня якість: {avg_quality:.3f}")
        
        return form_test_results
    
    async def _get_computed_styles(self, page: Page) -> Dict[str, Any]:
        """Збір computed styles для аналізу"""
        
        # Отримання загальних стилів сторінки
        styles = await page.evaluate('''
            () => {
                const computed = window.getComputedStyle(document.body);
                return {
                    backgroundColor: computed.backgroundColor,
                    color: computed.color,
                    fontFamily: computed.fontFamily,
                    fontSize: computed.fontSize
                };
            }
        ''')
        
        return styles
    
    async def _run_axe_core(self, page: Page) -> Dict[str, Any]:
        """Запуск axe-core аналізу доступності"""
        
        try:
            # Перевіряємо наявність axe-core
            axe_path = "node_modules/axe-core/axe.min.js"
            import os
            if not os.path.exists(axe_path):
                print(f"⚠️ axe-core не знайдено за шляхом: {axe_path}")
                return {}
            
            # Завантажуємо axe-core скрипт
            await page.add_script_tag(path=axe_path)
            
            # Запускаємо axe-core аналіз
            axe_results = await page.evaluate("""
                () => {
                    return new Promise((resolve) => {
                        if (typeof axe !== 'undefined') {
                            axe.run().then(results => {
                                resolve(results);
                            }).catch(error => {
                                console.error('Axe-core error:', error);
                                resolve({});
                            });
                        } else {
                            console.error('Axe-core not loaded');
                            resolve({});
                        }
                    });
                }
            """)
            
            print(f"✅ axe-core аналіз завершено:")
            if axe_results:
                violations_count = len(axe_results.get('violations', []))
                passes_count = len(axe_results.get('passes', []))
                print(f"   ❌ Порушення: {violations_count}")
                print(f"   ✅ Пройдено: {passes_count}")
                
                # Детальний вивід всіх правил
                print(f"\n📋 === ПОВНИЙ СПИСОК AXE-CORE РЕЗУЛЬТАТІВ ===")
                
                violations = axe_results.get('violations', [])
                if violations:
                    print(f"\n❌ ПОРУШЕННЯ ({len(violations)}):")
                    for i, violation in enumerate(violations, 1):
                        rule_id = violation.get('id', 'unknown')
                        nodes_count = len(violation.get('nodes', []))
                        impact = violation.get('impact', 'unknown')
                        description = violation.get('description', 'No description')
                        print(f"   {i}. {rule_id} ({impact}): {nodes_count} елементів")
                        print(f"      {description}")
                
                passes = axe_results.get('passes', [])
                if passes:
                    print(f"\n✅ ПРОЙДЕНО ({len(passes)}):")
                    for i, passed in enumerate(passes, 1):
                        rule_id = passed.get('id', 'unknown')
                        nodes_count = len(passed.get('nodes', []))
                        print(f"   {i}. {rule_id}: {nodes_count} елементів")
                
                incomplete = axe_results.get('incomplete', [])
                if incomplete:
                    print(f"\n⚠️ НЕПОВНІ ПЕРЕВІРКИ ({len(incomplete)}):")
                    for i, inc in enumerate(incomplete, 1):
                        rule_id = inc.get('id', 'unknown')
                        nodes_count = len(inc.get('nodes', []))
                        print(f"   {i}. {rule_id}: {nodes_count} елементів")
                
                print(f"=== КІНЕЦЬ СПИСКУ AXE-CORE РЕЗУЛЬТАТІВ ===\n")
            
            return axe_results
            
        except Exception as e:
            print(f"❌ Помилка при запуску axe-core: {str(e)}")
            return {}
    
    async def _test_keyboard_focus(self, page: Page) -> List[Dict[str, Any]]:
        """Реальне тестування клавіатурної навігації з фокусом"""
        
        try:
            # Впроваджуємо JavaScript функцію для тестування фокусу
            focus_test_results = await page.evaluate("""
                () => {
                    function isFocusable(el) {
                        if (!el) return { focusable: false, reason: 'Елемент не існує' };

                        // Відкидаємо відключені або приховані
                        if (el.disabled) return { focusable: false, reason: 'Елемент відключений (disabled)' };
                        
                        const style = window.getComputedStyle(el);
                        if (style.display === "none") return { focusable: false, reason: 'display: none' };
                        if (style.visibility === "hidden") return { focusable: false, reason: 'visibility: hidden' };
                        
                        if (el.hasAttribute("aria-hidden") && el.getAttribute("aria-hidden") === "true") {
                            return { focusable: false, reason: 'aria-hidden="true"' };
                        }

                        // Відкидаємо tabindex="-1"
                        const tabindex = el.getAttribute("tabindex");
                        if (tabindex === "-1") return { focusable: false, reason: 'tabindex="-1"' };

                        // Для <a> перевіряємо href
                        if (el.tagName.toLowerCase() === "a" && !el.hasAttribute("href") && !tabindex) {
                            return { focusable: false, reason: 'Посилання без href та tabindex' };
                        }

                        // Зберігаємо поточний активний елемент
                        const originalActiveElement = document.activeElement;
                        
                        try {
                            // Тестуємо фокус
                            el.focus();
                            const canFocus = document.activeElement === el;
                            
                            // Відновлюємо попередній фокус
                            if (originalActiveElement && originalActiveElement.focus) {
                                originalActiveElement.focus();
                            } else {
                                el.blur();
                            }
                            
                            return { 
                                focusable: canFocus, 
                                reason: canFocus ? 'Пройшов тест фокусу' : 'Не може отримати фокус'
                            };
                        } catch (error) {
                            return { focusable: false, reason: 'Помилка при тестуванні фокусу: ' + error.message };
                        }
                    }

                    function getElementSelector(el) {
                        if (el.id) return '#' + el.id;
                        if (el.className) return el.tagName.toLowerCase() + '.' + el.className.split(' ').join('.');
                        
                        // Генеруємо nth-child селектор
                        let selector = el.tagName.toLowerCase();
                        let parent = el.parentElement;
                        if (parent) {
                            const siblings = Array.from(parent.children).filter(child => child.tagName === el.tagName);
                            if (siblings.length > 1) {
                                const index = siblings.indexOf(el) + 1;
                                selector += ':nth-child(' + index + ')';
                            }
                        }
                        return selector;
                    }

                    // Знаходимо всі потенційно інтерактивні елементи
                    const elements = document.querySelectorAll("a, button, input, textarea, select, [tabindex], [onclick], [role='button'], [role='link']");
                    const results = [];
                    
                    elements.forEach(el => {
                        const focusResult = isFocusable(el);
                        
                        results.push({
                            tag: el.tagName.toLowerCase(),
                            selector: getElementSelector(el),
                            html: el.outerHTML.substring(0, 200),
                            focusable: focusResult.focusable,
                            focus_reason: focusResult.focusable ? focusResult.reason : null,
                            non_focus_reason: !focusResult.focusable ? focusResult.reason : null,
                            tabindex: el.getAttribute('tabindex'),
                            role: el.getAttribute('role'),
                            disabled: el.disabled || false,
                            href: el.getAttribute('href'),
                            type: el.getAttribute('type'),
                            text: el.textContent ? el.textContent.substring(0, 50) : ''
                        });
                    });
                    
                    return results;
                }
            """)
            
            print(f"✅ Тестування фокусу завершено:")
            total_elements = len(focus_test_results)
            focusable_count = sum(1 for r in focus_test_results if r.get('focusable', False))
            print(f"   📋 Знайдено елементів: {total_elements}")
            print(f"   ✅ Доступних з клавіатури: {focusable_count}")
            print(f"   ❌ Недоступних: {total_elements - focusable_count}")
            
            return focus_test_results
            
        except Exception as e:
            print(f"❌ Помилка при тестуванні клавіатурної навігації: {str(e)}")
            return []