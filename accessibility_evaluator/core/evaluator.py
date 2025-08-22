"""
Головний клас для оцінки доступності вебсайтів
"""

from playwright.async_api import async_playwright
from typing import Dict, Any, List
import asyncio
import re

from .metrics.perceptibility import PerceptibilityMetrics
from .metrics.operability import OperabilityMetrics  
from .metrics.understandability import UnderstandabilityMetrics
from .metrics.localization import LocalizationMetrics
from .utils.web_scraper import WebScraper
from .utils.calculator import ScoreCalculator


class AccessibilityEvaluator:
    """Головний клас для оцінки доступності вебсайтів"""
    
    def __init__(self):
        self.weights = {
            'perceptibility': 0.3,
            'operability': 0.3, 
            'understandability': 0.4,
            'localization': 0.4
        }
        
        self.metric_weights = {
            'alt_text': 0.15,
            'contrast': 0.15,
            'media_accessibility': 0.15,
            'keyboard_navigation': 0.05,
            'structured_navigation': 0.05,
            'instruction_clarity': 0.1,
            'input_assistance': 0.1,
            'error_support': 0.1,
            'localization': 0.15
        }
        
        # Ініціалізація аналізаторів метрик
        self.perceptibility = PerceptibilityMetrics()
        self.operability = OperabilityMetrics()
        self.understandability = UnderstandabilityMetrics()
        self.localization = LocalizationMetrics()
        
        self.web_scraper = WebScraper()
        self.calculator = ScoreCalculator(self.weights, self.metric_weights)
    
    async def evaluate_accessibility(self, url: str) -> Dict[str, Any]:
        """
        Головна функція для оцінки доступності вебсайту
        
        Args:
            url: URL вебсайту для аналізу
            
        Returns:
            Словник з результатами аналізу
        """
        try:
            # Отримання даних з вебсайту
            page_data = await self.web_scraper.scrape_page(url)
            
            # Розрахунок всіх метрик
            metrics = await self.calculate_all_metrics(page_data)
            
            # Розрахунок підскорів
            subscores = self.calculator.calculate_subscores(metrics)
            
            # Фінальний скор
            final_score = self.calculator.calculate_final_score(subscores)
            
            # Генерація рекомендацій
            recommendations = self.generate_recommendations(metrics)
            
            return {
                'url': url,
                'metrics': metrics,
                'subscores': subscores,
                'final_score': final_score,
                'recommendations': recommendations,
                'axe_results': page_data.get('axe_results', {}),  # Додаємо axe_results
                'detailed_analysis': await self._generate_detailed_analysis(page_data),  # Додаємо детальний аналіз
                'status': 'success'
            }
            
        except Exception as e:
            return {
                'url': url,
                'error': str(e),
                'status': 'error'
            }
    
    async def calculate_all_metrics(self, page_data: Dict[str, Any]) -> Dict[str, float]:
        """Розрахунок всіх метрик доступності"""
        
        metrics = {}
        
        # Перцептивність
        metrics.update(await self.perceptibility.calculate_metrics(page_data))
        
        # Керованість
        metrics.update(await self.operability.calculate_metrics(page_data))
        
        # Зрозумілість
        metrics.update(await self.understandability.calculate_metrics(page_data))
        
        # Локалізація
        metrics.update(await self.localization.calculate_metrics(page_data))
        
        return metrics
    
    def generate_recommendations(self, metrics: Dict[str, float]) -> List[Dict[str, str]]:
        """Генерація рекомендацій на основі результатів метрик"""
        
        recommendations = []
        
        # Рекомендації для альтернативного тексту
        if metrics.get('alt_text', 0) < 0.8:
            recommendations.append({
                'category': 'Перцептивність',
                'issue': 'Недостатньо альтернативного тексту',
                'recommendation': 'Додайте змістовні alt атрибути до всіх зображень',
                'priority': 'Високий',
                'wcag_reference': 'WCAG 1.1.1'
            })
        
        # Рекомендації для контрасту
        if metrics.get('contrast', 0) < 0.7:
            recommendations.append({
                'category': 'Перцептивність',
                'issue': 'Низький контраст тексту',
                'recommendation': 'Підвищте контраст до мінімум 4.5:1 для основного тексту',
                'priority': 'Високий',
                'wcag_reference': 'WCAG 1.4.3'
            })
        
        # Рекомендації для клавіатурної навігації
        if metrics.get('keyboard_navigation', 0) < 0.9:
            recommendations.append({
                'category': 'Керованість',
                'issue': 'Проблеми з клавіатурною навігацією',
                'recommendation': 'Забезпечте доступність всіх інтерактивних елементів через клавіатуру',
                'priority': 'Високий',
                'wcag_reference': 'WCAG 2.1.1'
            })
        
        # Рекомендації для зрозумілості
        if metrics.get('instruction_clarity', 0) < 0.7:
            recommendations.append({
                'category': 'Зрозумілість',
                'issue': 'Складні або незрозумілі інструкції',
                'recommendation': 'Спростіть мову інструкцій та зробіть їх більш зрозумілими',
                'priority': 'Середній',
                'wcag_reference': 'WCAG 3.1.5'
            })
        
        # Рекомендації для локалізації
        if metrics.get('localization', 0) < 0.6:
            recommendations.append({
                'category': 'Локалізація',
                'issue': 'Недостатня підтримка мов',
                'recommendation': 'Додайте підтримку української та англійської мов',
                'priority': 'Середній',
                'wcag_reference': 'WCAG 3.1.2'
            })
        
        return recommendations
    
    async def evaluate_html_content(self, html_content: str, base_url: str = "http://localhost", title: str = "HTML Document") -> Dict[str, Any]:
        """
        Оцінка доступності HTML контенту без завантаження з URL
        
        Args:
            html_content: HTML контент для аналізу
            base_url: Базовий URL для відносних посилань
            title: Заголовок документа
            
        Returns:
            Словник з результатами аналізу
        """
        try:
            # Створюємо page_data з HTML контенту
            page_data = await self._create_page_data_from_html(html_content, base_url, title)
            
            # Розрахунок всіх метрик
            metrics = await self.calculate_all_metrics(page_data)
            
            # Розрахунок підскорів
            subscores = self.calculator.calculate_subscores(metrics)
            
            # Фінальний скор
            final_score = self.calculator.calculate_final_score(subscores)
            
            # Генерація рекомендацій
            recommendations = self.generate_recommendations(metrics)
            
            return {
                'url': f"{base_url} (HTML контент)",
                'metrics': metrics,
                'subscores': subscores,
                'final_score': final_score,
                'recommendations': recommendations,
                'detailed_analysis': await self._generate_detailed_analysis(page_data),
                'status': 'success'
            }
            
        except Exception as e:
            return {
                'url': f"{base_url} (HTML контент)",
                'error': str(e),
                'status': 'error'
            }
    
    async def _create_page_data_from_html(self, html_content: str, base_url: str, title: str) -> Dict[str, Any]:
        """Створення page_data з HTML контенту для аналізу"""
        
        from playwright.async_api import async_playwright
        
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page()
            
            try:
                print(f"📄 Завантаження HTML контенту...")
                
                # Встановлюємо HTML контент
                await page.set_content(html_content, wait_until="domcontentloaded")
                
                # Збираємо дані аналогічно до web_scraper
                print("🔍 Збір інтерактивних елементів...")
                interactive_elements = await self.web_scraper._get_interactive_elements(page)
                
                print("📝 Збір текстових елементів...")
                text_elements = await self.web_scraper._get_text_elements(page)
                
                print("🎬 Збір медіа елементів...")
                media_elements = await self.web_scraper._get_media_elements(page)
                
                print("📋 Збір форм...")
                form_elements = await self.web_scraper._get_form_elements(page)
                
                print("🎨 Збір стилів...")
                computed_styles = await self.web_scraper._get_computed_styles(page)
                
                print("🔍 Запуск axe-core аналізу...")
                axe_results = await self.web_scraper._run_axe_core(page)
                
                print("⌨️ Тестування клавіатурної навігації...")
                focus_test_results = await self.web_scraper._test_keyboard_focus(page)
                
                page_data = {
                    'url': base_url,
                    'html_content': html_content,
                    'title': title,
                    'page_depth': 0,  # HTML контент не має глибини
                    'interactive_elements': interactive_elements,
                    'text_elements': text_elements,
                    'media_elements': media_elements,
                    'form_elements': form_elements,
                    'computed_styles': computed_styles,
                    'axe_results': axe_results,
                    'focus_test_results': focus_test_results  # Додаємо результати тестування фокусу
                }
                
                print(f"✅ Збір даних з HTML завершено. Знайдено:")
                print(f"   📝 Текстових елементів: {len(text_elements)}")
                print(f"   🔗 Інтерактивних елементів: {len(interactive_elements)}")
                print(f"   🎬 Медіа елементів: {len(media_elements)}")
                print(f"   📋 Форм: {len(form_elements)}")
                
                return page_data
                
            finally:
                await browser.close()
    
    async def _generate_detailed_analysis(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Генерація детального аналізу для UI"""
        
        axe_results = page_data.get('axe_results', {})
        
        detailed_analysis = {
            'alt_text': self._analyze_alt_text_details(axe_results),
            'contrast': self._analyze_contrast_details(axe_results),
            'structured_navigation': self._analyze_headings_details(axe_results),
            'keyboard_navigation': self._analyze_keyboard_details(page_data),  # Передаємо page_data замість axe_results
            'instruction_clarity': self._analyze_instructions_details(page_data),
            'input_assistance': self._analyze_input_assistance_details(page_data),
            'error_support': self._analyze_error_support_details(page_data),
            'media_accessibility': self._analyze_media_details(page_data),  # Передаємо page_data замість axe_results
            'localization': self._analyze_localization_details(page_data)
        }
        
        return detailed_analysis
    
    def _analyze_alt_text_details(self, axe_results: Dict[str, Any]) -> Dict[str, Any]:
        """Детальний аналіз alt-text"""
        
        details = {
            'total_images': 0,
            'correct_images': 0,
            'problematic_images': [],
            'correct_images_list': [],
            'score_explanation': ''
        }
        
        # Аналізуємо image-alt правило
        violations = self._get_axe_rule_results(axe_results, 'violations', 'image-alt')
        passes = self._get_axe_rule_results(axe_results, 'passes', 'image-alt')
        
        # Проблемні зображення
        if violations:
            for node in violations.get('nodes', []):
                details['problematic_images'].append({
                    'selector': node.get('target', ['невідомо'])[0] if node.get('target') else 'невідомо',
                    'html': node.get('html', ''),
                    'issue': node.get('failureSummary', 'Відсутній alt атрибут'),
                    'impact': violations.get('impact', 'unknown')
                })
        
        # Правильні зображення
        if passes:
            for node in passes.get('nodes', []):
                # Витягуємо alt текст з HTML
                html = node.get('html', '')
                import re
                alt_match = re.search(r'alt="([^"]*)"', html) if 'alt=' in html else None
                alt_text = alt_match.group(1) if alt_match else 'Порожній alt=""'
                
                details['correct_images_list'].append({
                    'selector': node.get('target', ['невідомо'])[0] if node.get('target') else 'невідомо',
                    'html': html,
                    'alt_text': alt_text
                })
        
        details['total_images'] = len(details['problematic_images']) + len(details['correct_images_list'])
        details['correct_images'] = len(details['correct_images_list'])
        
        if details['total_images'] > 0:
            score = details['correct_images'] / details['total_images']
            details['score_explanation'] = f"Скор: {details['correct_images']}/{details['total_images']} = {score:.3f}"
        else:
            details['score_explanation'] = "Зображення не знайдено"
        
        return details
    
    def _analyze_contrast_details(self, axe_results: Dict[str, Any]) -> Dict[str, Any]:
        """Детальний аналіз контрасту"""
        
        details = {
            'total_elements': 0,
            'correct_elements': 0,
            'problematic_elements': [],
            'correct_elements_list': [],
            'score_explanation': ''
        }
        
        # Аналізуємо color-contrast правило
        violations = self._get_axe_rule_results(axe_results, 'violations', 'color-contrast')
        passes = self._get_axe_rule_results(axe_results, 'passes', 'color-contrast')
        
        # Проблемні елементи
        if violations:
            for node in violations.get('nodes', []):
                # Витягуємо інформацію про контраст з failureSummary
                failure_summary = node.get('failureSummary', '')
                contrast_info = self._extract_contrast_info(failure_summary)
                
                details['problematic_elements'].append({
                    'selector': node.get('target', ['невідомо'])[0] if node.get('target') else 'невідомо',
                    'html': node.get('html', ''),
                    'issue': failure_summary,
                    'contrast_ratio': contrast_info.get('actual', 'невідомо'),
                    'required_ratio': contrast_info.get('required', 'невідомо'),
                    'foreground': contrast_info.get('foreground', 'невідомо'),
                    'background': contrast_info.get('background', 'невідомо')
                })
        
        # Правильні елементи
        if passes:
            for node in passes.get('nodes', []):
                details['correct_elements_list'].append({
                    'selector': node.get('target', ['невідомо'])[0] if node.get('target') else 'невідомо',
                    'html': node.get('html', ''),
                    'status': 'Контраст відповідає WCAG стандартам'
                })
        
        details['total_elements'] = len(details['problematic_elements']) + len(details['correct_elements_list'])
        details['correct_elements'] = len(details['correct_elements_list'])
        
        if details['total_elements'] > 0:
            score = details['correct_elements'] / details['total_elements']
            details['score_explanation'] = f"Скор: {details['correct_elements']}/{details['total_elements']} = {score:.3f}"
        else:
            details['score_explanation'] = "Текстові елементи не знайдено"
        
        return details
    
    def _extract_contrast_info(self, failure_summary: str) -> Dict[str, str]:
        """Витягує інформацію про контраст з повідомлення про помилку"""
        
        import re
        
        info = {}
        
        # Шукаємо контраст ratio
        ratio_match = re.search(r'contrast of ([\d.]+)', failure_summary)
        if ratio_match:
            info['actual'] = ratio_match.group(1) + ':1'
        
        # Шукаємо необхідний контраст
        required_match = re.search(r'Expected contrast ratio of ([\d.]+):1', failure_summary)
        if required_match:
            info['required'] = required_match.group(1) + ':1'
        
        # Шукаємо кольори
        fg_match = re.search(r'foreground color: (#[a-fA-F0-9]+)', failure_summary)
        if fg_match:
            info['foreground'] = fg_match.group(1)
        
        bg_match = re.search(r'background color: (#[a-fA-F0-9]+)', failure_summary)
        if bg_match:
            info['background'] = bg_match.group(1)
        
        return info
    
    def _analyze_headings_details(self, axe_results: Dict[str, Any]) -> Dict[str, Any]:
        """Детальний аналіз структури заголовків"""
        
        details = {
            'total_headings': 0,
            'correct_headings': 0,
            'problematic_headings': [],
            'correct_headings_list': [],
            'score_explanation': ''
        }
        
        # Аналізуємо правила заголовків
        heading_rules = ['heading-order', 'page-has-heading-one', 'empty-heading']
        
        for rule_id in heading_rules:
            violations = self._get_axe_rule_results(axe_results, 'violations', rule_id)
            passes = self._get_axe_rule_results(axe_results, 'passes', rule_id)
            
            # Проблемні заголовки
            if violations:
                for node in violations.get('nodes', []):
                    details['problematic_headings'].append({
                        'selector': node.get('target', ['невідомо'])[0] if node.get('target') else 'невідомо',
                        'html': node.get('html', ''),
                        'rule': rule_id,
                        'issue': node.get('failureSummary', violations.get('description', 'Невідома проблема'))
                    })
            
            # Правильні заголовки
            if passes:
                for node in passes.get('nodes', []):
                    details['correct_headings_list'].append({
                        'selector': node.get('target', ['невідомо'])[0] if node.get('target') else 'невідомо',
                        'html': node.get('html', ''),
                        'rule': rule_id,
                        'status': 'Правильна структура'
                    })
        
        details['total_headings'] = len(details['problematic_headings']) + len(details['correct_headings_list'])
        details['correct_headings'] = len(details['correct_headings_list'])
        
        if details['total_headings'] > 0:
            score = details['correct_headings'] / details['total_headings']
            details['score_explanation'] = f"Скор: {details['correct_headings']}/{details['total_headings']} = {score:.3f}"
        else:
            details['score_explanation'] = "Заголовки не знайдено"
        
        return details
    
    def _analyze_keyboard_details(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Детальний аналіз клавіатурної навігації з реальним тестуванням фокусу"""
        
        # Отримуємо результати реального тестування фокусу
        focus_test_results = page_data.get('focus_test_results', [])
        
        details = {
            'total_elements': 0,
            'accessible_elements': 0,
            'problematic_elements': [],
            'accessible_elements_list': [],
            'score_explanation': ''
        }
        
        if not focus_test_results:
            details['score_explanation'] = "Результати тестування клавіатурної навігації недоступні"
            return details
        
        # Розділяємо елементи на доступні та проблемні
        for result in focus_test_results:
            element_info = {
                'selector': result.get('selector', 'невідомо'),
                'html': result.get('html', ''),
                'tag': result.get('tag', 'unknown'),
                'rule': 'focus-test',  # Позначаємо як результат реального тестування
            }
            
            if result.get('focusable', False):
                element_info['status'] = result.get('focus_reason', 'Доступний з клавіатури')
                details['accessible_elements_list'].append(element_info)
            else:
                element_info['issue'] = result.get('non_focus_reason', 'Недоступний з клавіатури')
                details['problematic_elements'].append(element_info)
        
        details['total_elements'] = len(focus_test_results)
        details['accessible_elements'] = len(details['accessible_elements_list'])
        
        if details['total_elements'] > 0:
            score = details['accessible_elements'] / details['total_elements']
            details['score_explanation'] = f"Скор: {details['accessible_elements']}/{details['total_elements']} = {score:.3f} (реальне тестування фокусу)"
        else:
            details['score_explanation'] = "Інтерактивні елементи не знайдено"
        
        return details
    
    def _analyze_instructions_details(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Детальний аналіз зрозумілості інструкцій"""
        
        html_content = page_data.get('html_content', '')
        
        # Витягуємо тільки labels для input полів
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        instructions = []
        
        # Шукаємо labels пов'язані з input полями
        labels = soup.find_all('label')
        for label in labels:
            text = label.get_text().strip()
            if text and len(text) >= 2:  # Мінімальна довжина для label
                instructions.append({
                    'text': text,
                    'element': 'label',
                    'for': label.get('for', 'невідомо')
                })
        
        # Також шукаємо aria-label та placeholder в input полях
        inputs = soup.find_all(['input', 'textarea', 'select'])
        for input_elem in inputs:
            # aria-label
            aria_label = input_elem.get('aria-label')
            if aria_label and aria_label.strip():
                instructions.append({
                    'text': aria_label.strip(),
                    'element': 'aria-label',
                    'for': input_elem.get('id', 'невідомо')
                })
            
            # placeholder
            placeholder = input_elem.get('placeholder')
            if placeholder and placeholder.strip():
                instructions.append({
                    'text': placeholder.strip(),
                    'element': 'placeholder',
                    'for': input_elem.get('id', 'невідомо')
                })
        
        # Конвертуємо в простий список текстів для сумісності
        instruction_texts = [instr['text'] for instr in instructions]
        
        clear_instructions = []
        problematic_instructions = []
        
        # Використовуємо існуючий метод для оцінки зрозумілості
        from accessibility_evaluator.core.metrics.understandability import UnderstandabilityMetrics
        understandability_metrics = UnderstandabilityMetrics()
        
        for i, instruction_text in enumerate(instruction_texts):
            instruction_obj = instructions[i]
            
            # Створюємо контекст для оцінки
            context = {
                'field_type': self._get_field_type_for_instruction(instruction_obj, html_content),
                'field_id': instruction_obj.get('for')
            }
            
            # Використовуємо метод з контекстом
            is_clear = understandability_metrics._assess_instruction_clarity_with_context(instruction_text, context)
            
            if is_clear:
                clear_instructions.append({
                    'text': instruction_text,
                    'element_type': instruction_obj['element'],
                    'status': 'Зрозуміла інструкція'
                })
            else:
                # Аналізуємо чому label незрозумілий використовуючи строгі критерії
                issues = self._analyze_instruction_issues_strict(instruction_text)
                
                problematic_instructions.append({
                    'text': instruction_text,
                    'element_type': instruction_obj['element'],
                    'issue': '; '.join(issues) if issues else 'Складний для розуміння'
                })
        
        total_instructions = len(instructions)
        clear_count = len(clear_instructions)
        
        if total_instructions > 0:
            score = clear_count / total_instructions
            score_explanation = f"Скор: {clear_count}/{total_instructions} = {score:.3f} (аналіз labels для полів вводу)"
        else:
            score_explanation = "Labels для полів вводу не знайдено"
        
        return {
            'total_instructions': total_instructions,
            'clear_instructions': clear_count,
            'problematic_instructions': problematic_instructions,
            'clear_instructions_list': clear_instructions,
            'score_explanation': score_explanation
        }
    
    def _assess_label_clarity(self, text: str, element_type: str) -> bool:
        """Оцінка зрозумілості label для поля вводу з реалістичними критеріями"""
        
        # Базові перевірки
        if len(text.strip()) < 2:
            return False
        
        # Для різних типів елементів різні критерії
        if element_type == 'placeholder':
            # Placeholder може бути коротшим
            return len(text) <= 50 and len(text.split()) <= 8
        
        if element_type == 'aria-label':
            # aria-label має бути коротким та зрозумілим
            return len(text) <= 100 and len(text.split()) <= 15
        
        # Для звичайних labels
        word_count = len(text.split())
        
        # Реалістичні критерії для labels
        basic_criteria = (
            2 <= len(text) <= 100 and           # Розумна довжина
            word_count <= 10                    # Не більше 10 слів для label
        )
        
        if not basic_criteria:
            return False
        
        # Для коротких labels (1-3 слова) не перевіряємо складність
        if word_count <= 3:
            return True
        
        # Для довших labels перевіряємо читабельність з м'якшими критеріями
        try:
            import textstat
            flesch_score = textstat.flesch_reading_ease(text)
            grade_level = textstat.flesch_kincaid_grade(text)
            
            # М'якші критерії для labels
            readability_ok = (
                flesch_score >= 30 or           # Значно м'якший критерій
                grade_level <= 12               # До 12 класу замість 8
            )
            
            return readability_ok
            
        except Exception:
            # Якщо не можемо оцінити - вважаємо зрозумілим для коротких текстів
            return word_count <= 6
    
    def _analyze_label_issues(self, text: str, element_type: str) -> list:
        """Аналіз проблем з label"""
        
        issues = []
        word_count = len(text.split())
        
        # Перевірка довжини
        if element_type == 'placeholder' and len(text) > 50:
            issues.append(f"Занадто довгий placeholder ({len(text)} символів)")
        elif element_type == 'aria-label' and len(text) > 100:
            issues.append(f"Занадто довгий aria-label ({len(text)} символів)")
        elif element_type == 'label' and len(text) > 100:
            issues.append(f"Занадто довгий label ({len(text)} символів)")
        
        # Перевірка кількості слів
        if element_type == 'placeholder' and word_count > 8:
            issues.append(f"Занадто багато слів у placeholder ({word_count} слів)")
        elif element_type == 'aria-label' and word_count > 15:
            issues.append(f"Занадто багато слів у aria-label ({word_count} слів)")
        elif element_type == 'label' and word_count > 10:
            issues.append(f"Занадто багато слів у label ({word_count} слів)")
        
        # Перевірка читабельності тільки для довших текстів
        if word_count > 3:
            try:
                import textstat
                flesch_score = textstat.flesch_reading_ease(text)
                grade_level = textstat.flesch_kincaid_grade(text)
                
                if flesch_score < 30:  # Дуже м'який критерій
                    issues.append(f"Дуже низька читабельність (Flesch: {flesch_score:.1f})")
                elif grade_level > 12:  # До 12 класу
                    issues.append(f"Занадто складний (рівень: {grade_level:.1f} клас)")
                    
            except Exception:
                pass
        
        return issues
    
    def _analyze_instruction_issues_strict(self, text: str) -> list:
        """Аналіз проблем з інструкцією використовуючи адаптовані критерії з UnderstandabilityMetrics"""
        
        issues = []
        
        # Базові перевірки
        if len(text.strip()) < 2:
            issues.append("Занадто короткий текст (менше 2 символів)")
            return issues
            
        if len(text) > 200:
            issues.append(f"Занадто довгий текст ({len(text)} символів, максимум 200)")
        
        word_count = len(text.split())
        sentence_count = len(re.split(r'[.!?]+', text.strip()))
        
        if word_count > 25:
            issues.append(f"Занадто багато слів ({word_count}, максимум 25)")
            
        if sentence_count > 3:
            issues.append(f"Занадто багато речень ({sentence_count}, максимум 3)")
        
        # Аналіз залежно від довжини тексту
        if word_count <= 3:
            # Для коротких текстів перевіряємо складні терміни
            if not self._is_simple_short_text_evaluator(text):
                issues.append("Містить складні технічні терміни")
        elif word_count <= 8:
            # Для середніх текстів перевіряємо додаткові критерії
            if not self._is_simple_short_text_evaluator(text):
                issues.append("Містить складні технічні терміни")
            
            words = text.split()
            avg_word_length = sum(len(word) for word in words) / len(words)
            if avg_word_length > 8:
                issues.append(f"Середня довжина слів занадто велика ({avg_word_length:.1f}, максимум 8)")
            
            complex_words = [word for word in words if len(word) > 8]
            if len(complex_words) > 1:
                issues.append(f"Занадто багато складних слів ({len(complex_words)}, максимум 1)")
        else:
            # Для довших текстів використовуємо textstat з м'якшими критеріями
            try:
                import textstat
                flesch_score = textstat.flesch_reading_ease(text)
                grade_level = textstat.flesch_kincaid_grade(text)
                ari_score = textstat.automated_readability_index(text)
                
                # М'якші критерії
                if flesch_score < 30:
                    issues.append(f"Дуже низька читабельність (Flesch: {flesch_score:.1f}, потрібно >= 30)")
                    
                if grade_level > 10:
                    issues.append(f"Занадто складний рівень (Grade: {grade_level:.1f}, потрібно <= 10)")
                    
                if ari_score > 10:
                    issues.append(f"Високий ARI індекс ({ari_score:.1f}, потрібно <= 10)")
                    
            except Exception:
                issues.append("Не вдалося проаналізувати читабельність")
        
        return issues
    
    def _is_simple_short_text_evaluator(self, text: str) -> bool:
        """Перевірка простих коротких текстів для evaluator.py"""
        
        # Список складних/технічних термінів
        complex_terms = [
            'дескриптивний', 'ідентифікація', 'узагальнений', 'субʼєкт', 'параметр',
            'конфігурація', 'аутентифікація', 'авторизація', 'валідація', 'верифікація',
            'інтеграція', 'імплементація', 'оптимізація', 'синхронізація', 'модифікація'
        ]
        
        text_lower = text.lower()
        
        # Якщо містить складні терміни - незрозумілий
        for term in complex_terms:
            if term in text_lower:
                return False
        
        # Якщо довжина слова більше 12 символів - може бути складним
        words = text.split()
        for word in words:
            if len(word) > 12:
                return False
        
        return True
    
    def _get_field_type_for_instruction(self, instruction_obj: Dict[str, Any], html_content: str) -> str:
        """Визначення типу поля для інструкції"""
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        element_type = instruction_obj.get('element', '')
        field_id = instruction_obj.get('for')
        
        # Для label шукаємо пов'язане поле
        if element_type == 'label' and field_id:
            field = soup.find(id=field_id)
            if field:
                return field.get('type', field.name)
        
        # Для placeholder та aria-label тип вже відомий з контексту збору
        # Але якщо потрібно, можемо знайти елемент за текстом
        if element_type in ['placeholder', 'aria-label']:
            # Шукаємо input з таким placeholder або aria-label
            text = instruction_obj.get('text', '')
            
            if element_type == 'placeholder':
                field = soup.find(['input', 'textarea'], placeholder=text)
            else:  # aria-label
                field = soup.find(['input', 'textarea'], attrs={'aria-label': text})
            
            if field:
                return field.get('type', field.name)
        
        return 'unknown'
    
    def _analyze_input_assistance_details(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Детальний аналіз допомоги при введенні"""
        
        html_content = page_data.get('html_content', '')
        
        # Витягуємо поля вводу з HTML самостійно
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Типи input полів, які потребують допомоги при введенні
        text_input_types = [
            'text', 'email', 'password', 'tel', 'url', 'search', 
            'number', 'date', 'datetime-local', 'month', 'week', 'time'
        ]
        
        # Шукаємо тільки звичайні input поля та textarea (не select, checkbox, radio)
        input_elements = soup.find_all(['input', 'textarea'])
        
        fields = []
        for element in input_elements:
            # Для input перевіряємо тип
            if element.name == 'input':
                input_type = element.get('type', 'text').lower()
                # Пропускаємо checkbox, radio, submit, button тощо
                if input_type not in text_input_types:
                    continue
            
            # Для textarea завжди враховуємо
            field_info = {
                'selector': f"{element.name}[type='{element.get('type', 'text')}']" if element.name == 'input' else element.name,
                'html': str(element),
                'type': element.get('type', 'text'),
                'placeholder': element.get('placeholder'),
                'autocomplete': element.get('autocomplete'),
                'aria_label': element.get('aria-label'),
                'aria_describedby': element.get('aria-describedby'),
                'title': element.get('title')
            }
            fields.append(field_info)
        
        assisted_fields = []
        problematic_fields = []
        
        for field in fields:
            has_assistance = (
                field.get('autocomplete') or
                field.get('placeholder') or
                field.get('aria_describedby') or
                field.get('aria_label') or
                field.get('title')
            )
            
            if has_assistance:
                assistance_types = []
                if field.get('placeholder'):
                    assistance_types.append(f"placeholder='{field['placeholder']}'")
                if field.get('autocomplete'):
                    assistance_types.append(f"autocomplete='{field['autocomplete']}'")
                if field.get('aria_label'):
                    assistance_types.append(f"aria-label='{field['aria_label']}'")
                if field.get('title'):
                    assistance_types.append(f"title='{field['title']}'")
                if field.get('aria_describedby'):
                    assistance_types.append(f"aria-describedby='{field['aria_describedby']}'")
                
                assisted_fields.append({
                    'selector': field.get('selector', 'невідомо'),
                    'html': field.get('html', ''),
                    'assistance': '; '.join(assistance_types)
                })
            else:
                problematic_fields.append({
                    'selector': field.get('selector', 'невідомо'),
                    'html': field.get('html', ''),
                    'type': field.get('type', 'text'),
                    'issue': 'Відсутні підказки (placeholder, autocomplete, aria-label, title)'
                })
        
        total_fields = len(fields)
        assisted_count = len(assisted_fields)
        
        if total_fields > 0:
            score = assisted_count / total_fields
            score_explanation = f"Скор: {assisted_count}/{total_fields} = {score:.3f} (аналіз тільки текстових полів: input[text,email,password,etc] та textarea)"
        else:
            score_explanation = "Текстові поля вводу не знайдено (checkbox, radio, select не враховуються)"
        
        return {
            'total_fields': total_fields,
            'assisted_fields': assisted_count,
            'problematic_fields': problematic_fields,
            'assisted_fields_list': assisted_fields,
            'score_explanation': score_explanation
        }
    
    def _analyze_error_support_details(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Детальний аналіз підтримки помилок"""
        
        html_content = page_data.get('html_content', '')
        
        # Витягуємо форми з HTML самостійно
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Шукаємо всі форми
        form_elements = soup.find_all('form')
        
        forms = []
        for form in form_elements:
            # Аналізуємо форму на наявність механізмів обробки помилок
            has_error_elements = bool(form.find_all(class_=lambda x: x and any(word in x.lower() for word in ['error', 'invalid', 'warning'])))
            has_aria_invalid = bool(form.find_all(attrs={'aria-invalid': True}))
            has_required_fields = bool(form.find_all(attrs={'required': True}))
            has_validation = not form.get('novalidate', False)
            has_role_alert = bool(form.find_all(attrs={'role': 'alert'}))
            
            form_info = {
                'selector': 'form',
                'html': str(form)[:200] + '...' if len(str(form)) > 200 else str(form),
                'has_error_elements': has_error_elements,
                'has_aria_invalid': has_aria_invalid,
                'has_required_fields': has_required_fields,
                'has_validation': has_validation,
                'has_role_alert': has_role_alert
            }
            forms.append(form_info)
        
        supported_forms = []
        problematic_forms = []
        
        for form in forms:
            error_support_features = []
            
            # Перевіряємо різні типи підтримки помилок
            if form.get('has_error_elements'):
                error_support_features.append("Елементи для відображення помилок")
            if form.get('has_aria_invalid'):
                error_support_features.append("aria-invalid атрибути")
            if form.get('has_required_fields'):
                error_support_features.append("Обов'язкові поля (required)")
            if form.get('has_validation'):
                error_support_features.append("HTML5 валідація")
            if form.get('has_role_alert'):
                error_support_features.append("role='alert' для повідомлень")
            
            if error_support_features:
                supported_forms.append({
                    'selector': form.get('selector', 'невідомо'),
                    'html': form.get('html', ''),
                    'features': '; '.join(error_support_features)
                })
            else:
                problematic_forms.append({
                    'selector': form.get('selector', 'невідомо'),
                    'html': form.get('html', ''),
                    'issue': 'Відсутня обробка помилок (немає error елементів, aria-invalid, валідації)'
                })
        
        total_forms = len(forms)
        supported_count = len(supported_forms)
        
        if total_forms > 0:
            score = supported_count / total_forms
            score_explanation = f"Скор: {supported_count}/{total_forms} = {score:.3f}"
        else:
            score_explanation = "Форми не знайдено"
        
        return {
            'total_forms': total_forms,
            'supported_forms': supported_count,
            'problematic_forms': problematic_forms,
            'supported_forms_list': supported_forms,
            'score_explanation': score_explanation
        }
    
    def _analyze_media_details(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Детальний аналіз доступності медіа включно з embedded відео"""
        
        media_elements = page_data.get('media_elements', [])
        video_elements = [elem for elem in media_elements if elem['type'] in ['video', 'embedded_video']]
        
        details = {
            'total_media': len(video_elements),
            'accessible_media': 0,
            'problematic_media': [],
            'accessible_media_list': [],
            'score_explanation': ''
        }
        
        if not video_elements:
            details['score_explanation'] = "Відео елементи не знайдено"
            return details
        
        for video in video_elements:
            video_type = video.get('type', 'unknown')
            platform = video.get('platform', 'native')
            src = video.get('src') or ''
            
            selector = f"iframe[src*='{platform}']" if video_type == 'embedded_video' else 'video'
            
            video_info = {
                'type': video_type,
                'platform': platform,
                'src': src,
                'title': video.get('title', 'Без назви'),
                'selector': selector,
                'html': f"<{selector} src=\"{src[:50]}...\">" if src and len(src) > 50 else f"<{selector} src=\"{src}\">"
            }
            
            has_accessibility = False
            accessibility_features = []
            
            if video_type == 'video':
                # Нативне HTML5 відео
                tracks = video.get('tracks', [])
                
                for track in tracks:
                    track_kind = track.get('kind', '')
                    if track_kind in ['subtitles', 'captions']:
                        has_accessibility = True
                        accessibility_features.append(f"Субтитри ({track_kind})")
                    elif track_kind == 'descriptions':
                        has_accessibility = True
                        accessibility_features.append("Аудіоописи")
            
            elif video_type == 'embedded_video':
                # Embedded відео
                has_captions = video.get('has_captions', False)
                caption_check_method = video.get('caption_check_method', 'url_params')
                
                if has_captions:
                    has_accessibility = True
                    if caption_check_method == 'youtube_api':
                        accessibility_features.append(f"Субтитри підтверджені YouTube API ({platform})")
                    elif caption_check_method == 'enhanced_url_analysis':
                        # Перевіряємо чи є явні параметри субтитрів
                        if any(param in src for param in ['cc_load_policy=1', 'captions=1', 'cc_lang_pref=']):
                            accessibility_features.append(f"Субтитри підтверджені параметрами URL ({platform})")
                        elif any(param in src for param in ['hl=en', 'hl=uk', 'hl=ru', 'hl=de', 'hl=fr']):
                            accessibility_features.append(f"Ймовірні автосубтитри за мовними параметрами ({platform})")
                        else:
                            accessibility_features.append(f"Ймовірні автоматичні субтитри YouTube (стандартне відео)")
                    else:
                        accessibility_features.append(f"Субтитри в URL ({platform})")
            
            if has_accessibility:
                video_info['status'] = f"Доступне: {', '.join(accessibility_features)}"
                details['accessible_media_list'].append(video_info)
                details['accessible_media'] += 1
            else:
                video_info['issue'] = "Відсутні субтитри та аудіоописи"
                details['problematic_media'].append(video_info)
        
        if details['total_media'] > 0:
            score = details['accessible_media'] / details['total_media']
            details['score_explanation'] = f"Скор: {details['accessible_media']}/{details['total_media']} = {score:.3f} (аналіз нативних та embedded відео)"
        else:
            details['score_explanation'] = "Відео елементи не знайдено"
        
        return details
    
    def _analyze_localization_details(self, page_data: Dict[str, Any]) -> Dict[str, Any]:
        """Детальний аналіз локалізації"""
        
        html_content = page_data.get('html_content', '')
        url = page_data.get('url', '')
        
        # Використовуємо існуючий метод для визначення мов
        from accessibility_evaluator.core.metrics.localization import LocalizationMetrics
        localization_metrics = LocalizationMetrics()
        
        detected_languages_set = localization_metrics._detect_available_languages(html_content, url)
        
        # Конвертуємо в детальну інформацію
        language_names = {
            'uk': 'Українська',
            'en': 'Англійська', 
            'de': 'Німецька',
            'fr': 'Французька',
            'ru': 'Російська',
            'pl': 'Польська'
        }
        
        detected_languages = []
        for lang_code in detected_languages_set:
            lang_name = language_names.get(lang_code, f'Мова ({lang_code})')
            weight = localization_metrics.weights.get(lang_code, 0.01)
            detected_languages.append({
                'code': lang_code,
                'name': lang_name,
                'weight': weight
            })
        
        # Визначаємо відсутні важливі мови
        important_languages = ['uk', 'en']
        missing_languages = []
        for lang_code in important_languages:
            if lang_code not in detected_languages_set:
                lang_name = language_names.get(lang_code, f'Мова ({lang_code})')
                weight = localization_metrics.weights.get(lang_code, 0.01)
                missing_languages.append({
                    'code': lang_code,
                    'name': lang_name,
                    'weight': weight
                })
        
        # Розрахунок скору
        total_score = 0
        for lang in detected_languages:
            total_score += lang['weight']
        
        score_explanation = f"Скор: {total_score:.3f} (виявлено {len(detected_languages)} мов)"
        
        return {
            'detected_languages': detected_languages,
            'missing_languages': missing_languages,
            'score_explanation': score_explanation
        }
    
    def _get_axe_rule_results(self, axe_results: Dict[str, Any], result_type: str, rule_id: str) -> Dict[str, Any]:
        """Отримання результатів конкретного правила axe-core"""
        
        results = axe_results.get(result_type, [])
        for result in results:
            if result.get('id') == rule_id:
                return result
        return {}