import fitz
import re
from typing import List, Tuple, Dict
from collections import defaultdict

class PDFChapterExtractor:
    def __init__(self):
        self.min_chapter_length = 1000
        # Добавляем паттерны для фильтрации
        self.skip_sections = [
            "предисловие",
            "благодарности",
            "об авторе",
            "содержание",
            "оглавление",
            "список литературы",
            "приложение",
            "примечания",
            "copyright",
            "выходные данные",
            "isbn",
        ]
        
        self.technical_patterns = [
            r"©.*?\d{4}",  # копирайты
            r"ISBN.*?\d+",  # ISBN
            r"Издательство.*?\n",  # информация об издательстве
            r"www\..*?\.[a-z]{2,4}",  # веб-сайты
            r"\[.*?\]",  # ссылки в квадратных скобках
            r"\(c\).*?\d{4}",  # еще вариант копирайта
            r"Все права защищены.*?\n",
            r"Подписано в печать.*?\n",
            r"Формат.*?\n",
            r"Тираж.*?\n",
        ]

    def analyze_document_structure(self, doc) -> Dict:
        """Анализирует структуру документа для определения форматирования заголовков"""
        font_stats = defaultdict(int)
        font_samples = defaultdict(list)
        
        for page in doc:
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if "lines" in block:
                    for line in block["lines"]:
                        for span in line["spans"]:
                            font_size = round(span["size"], 1)
                            text = span["text"].strip()
                            if text:
                                font_stats[font_size] += 1
                                if len(font_samples[font_size]) < 5:  # сохраняем примеры текста
                                    font_samples[font_size].append(text)
        
        # Определяем размер шрифта для основного текста (самый частый)
        main_font_size = max(font_stats.items(), key=lambda x: x[1])[0]
        
        # Находим возможные размеры шрифта для заголовков (крупнее основного текста)
        header_font_sizes = [size for size in font_stats.keys() 
                           if size > main_font_size and font_stats[size] < font_stats[main_font_size] * 0.5]
        
        return {
            'main_font_size': main_font_size,
            'header_font_sizes': sorted(header_font_sizes),
            'font_samples': font_samples
        }

    def is_potential_header(self, text: str, font_size: float, doc_structure: Dict) -> bool:
        """Определяет, является ли текст потенциальным заголовком"""
        if font_size not in doc_structure['header_font_sizes']:
            return False
            
        # Проверяем характеристики текста
        text = text.strip()
        if not text:
            return False
            
        # Игнорируем слишком длинный текст
        if len(text.split()) > 20:
            return False
            
        # Проверяем типичные маркеры заголовков
        header_indicators = [
            lambda t: t[0].isupper() if t else False,  # Начинается с заглавной буквы
            lambda t: any(str(i) in t for i in range(10)),  # Содержит цифры
            lambda t: not t.endswith('.'),  # Не заканчивается точкой
            lambda t: len(t.split()) <= 15,  # Не слишком длинный
            lambda t: not any(punct in t for punct in ',:;'),  # Не содержит определенные знаки препинания
        ]
        
        return sum(1 for check in header_indicators if check(text)) >= 3

    def clean_text(self, text: str) -> str:
        """Очищает текст от технической информации"""
        import re
        
        # Приводим к нижнему регистру для проверки
        text_lower = text.lower()
        
        # Пропускаем секции из skip_sections
        lines = text.split('\n')
        cleaned_lines = []
        skip_mode = False
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # Проверяем, не начинается ли секция, которую нужно пропустить
            if any(section in line_lower for section in self.skip_sections):
                skip_mode = True
                continue
                
            # Проверяем, не закончилась ли пропускаемая секция (по пустой строке или новому заголовку)
            if skip_mode and (not line.strip() or line.strip().startswith('#')):
                skip_mode = False
                
            if not skip_mode:
                cleaned_lines.append(line)
        
        text = '\n'.join(cleaned_lines)
        
        # Удаляем техническую информацию по паттернам
        for pattern in self.technical_patterns:
            text = re.sub(pattern, '', text)
        
        # Удаляем множественные пустые строки
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Удаляем номера страниц
        text = re.sub(r'\n\s*\d+\s*\n', '\n', text)
        
        return text.strip()

    def extract_chapters(self, pdf_path: str) -> List[Tuple[str, str]]:
        """Извлекает главы из PDF файла"""
        doc = fitz.open(pdf_path)
        doc_structure = self.analyze_document_structure(doc)
        
        chapters = []
        current_chapter = []
        current_title = None
        
        for page in doc:
            blocks = page.get_text("dict")["blocks"]
            for block in blocks:
                if "lines" not in block:
                    continue
                    
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        font_size = round(span["size"], 1)
                        
                        if self.is_potential_header(text, font_size, doc_structure):
                            # Если нашли заголовок и есть предыдущая глава
                            if current_title and current_chapter:
                                chapter_text = self.clean_text('\n'.join(current_chapter))
                                if len(chapter_text) > self.min_chapter_length:
                                    chapters.append((current_title, chapter_text))
                                current_chapter = []
                            current_title = text
                        else:
                            if current_title:  # Если уже есть заголовок, добавляем текст к текущей главе
                                current_chapter.append(text)
        
        # Добавляем последнюю главу
        if current_title and current_chapter:
            chapter_text = self.clean_text('\n'.join(current_chapter))
            if len(chapter_text) > self.min_chapter_length:
                chapters.append((current_title, chapter_text))
        
        return chapters

    def save_chapters_to_files(self, chapters: List[Tuple[str, str]], output_dir: str):
        """Сохраняет главы в файлы"""
        import os
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        for i, (title, content) in enumerate(chapters, 1):
            filename = f"chapter_{i:02d}.txt"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"Title: {title}\n{'='*50}\n\n")
                f.write(content) 