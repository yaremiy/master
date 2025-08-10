"""
Утиліта для збору даних з вебсайтів
"""

from playwright.async_api import async_playwright, Page
from bs4 import BeautifulSoup
from typing import Dict, Any, List
import asyncio


class WebScraper:
    """Клас для збору даних з вебсайтів за допомогою Playwright"""
    
    def __init__(self):
        self.browser = None
        self.page = None
    
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
        
        return elements
    
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