import os
from pathlib import Path
from typing import List, Dict
from openai import OpenAI
from dotenv import load_dotenv
import logging
import json
import time
import hashlib
import tiktoken
import re

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загружаем переменные окружения
load_dotenv()

class MindMapGenerator:
    def __init__(self, target_language='auto'):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key not found in environment variables")
        self.client = OpenAI(api_key=self.api_key)
        
        # Добавляем целевой язык
        self.target_language = target_language
        
        # Поддерживаемые языки
        self.supported_languages = {
            'auto': 'Auto-detect',
            'ru': 'Русский',
            'en': 'English',
            'es': 'Español',
            'fr': 'Français',
            'de': 'Deutsch',
            'it': 'Italiano',
            'pt': 'Português',
            'zh': '中文',
            'ja': '日本語',
        }
        
        # Промпты для разных языков
        self.system_prompts = {
            'ru': "Создавайте четкие и организованные майндмапы на русском языке. Фокусируйтесь на ключевых концепциях и практических выводах.",
            'en': "Create clear and organized mind maps in English. Focus on key concepts and practical insights.",
            'es': "Cree mapas mentales claros y organizados en español. Concéntrese en conceptos clave y perspectivas prácticas.",
            'fr': "Créez des cartes mentales claires et organisées en français. Concentrez-vous sur les concepts clés et les perspectives pratiques.",
            'de': "Erstellen Sie klare und organisierte Mind Maps auf Deutsch. Konzentrieren Sie sich auf Schlüsselkonzepte und praktische Erkenntnisse.",
            'it': "Crea mappe mentali chiare e organizzate in italiano. Concentrati sui concetti chiave e sugli spunti pratici.",
            'pt': "Crie mapas mentais claros e organizados em português. Concentre-se em conceitos-chave e insights práticos.",
            'zh': "用中文创建清晰有条理的思维导图。专注于关键概念和实用见解。",
            'ja': "日本語で明確で体系的なマインドマップを作成します。重要な概念と実践的な洞察に焦点を当てます。",
        }
        
        # Создаем директорию для кэша
        self.cache_dir = Path("cache")
        self.cache_dir.mkdir(exist_ok=True)
        
        # Отслеживание обработанных глав
        self.processed_chapters = set()
        
        # Задержка между запросами (в секундах)
        self.request_delay = 1

    def get_cache_path(self, content: str) -> Path:
        """Генерирует путь к кэшу на основе контента"""
        content_hash = hashlib.md5(content.encode()).hexdigest()
        return self.cache_dir / f"{content_hash}.json"

    def get_from_cache(self, content: str) -> str:
        """Получает результат из кэша"""
        cache_path = self.get_cache_path(content)
        if cache_path.exists():
            try:
                with open(cache_path, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                logger.info(f"Cache hit: {cache_path.name}")
                return cached_data['mindmap']
            except Exception as e:
                logger.warning(f"Error reading cache: {str(e)}")
        return None

    def save_to_cache(self, content: str, mindmap: str):
        """Сохраняет результат в кэш"""
        cache_path = self.get_cache_path(content)
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump({'mindmap': mindmap}, f)
            logger.info(f"Saved to cache: {cache_path.name}")
        except Exception as e:
            logger.warning(f"Error saving to cache: {str(e)}")

    def split_text_into_chunks(self, text: str, max_tokens: int = 12000) -> List[str]:
        """Разделяет текст на части подходящего размера"""
        enc = tiktoken.encoding_for_model("gpt-3.5-turbo-16k")
        
        # Увеличиваем размер чанка для уменьшения количества запросов
        chunks = []
        current_chunk = []
        current_length = 0
        
        # Сначала разбиваем на главы/секции по заголовкам
        sections = re.split(r'(?=\n#+\s)', text)
        
        for section in sections:
            section_tokens = len(enc.encode(section))
            
            if section_tokens > max_tokens:
                # Если секция слишком большая, разбиваем её на параграфы
                paragraphs = section.split('\n\n')
                temp_chunk = []
                temp_length = 0
                
                for para in paragraphs:
                    para_tokens = len(enc.encode(para))
                    if temp_length + para_tokens > max_tokens:
                        if temp_chunk:
                            chunks.append('\n\n'.join(temp_chunk))
                        temp_chunk = [para]
                        temp_length = para_tokens
                    else:
                        temp_chunk.append(para)
                        temp_length += para_tokens
                
                if temp_chunk:
                    chunks.append('\n\n'.join(temp_chunk))
            else:
                # Если секция помещается целиком, добавляем её
                chunks.append(section)
        
        return chunks

    def detect_language(self, text: str) -> str:
        """Определяет язык текста"""
        # Простая проверка на кириллицу
        if any(ord('а') <= ord(c) <= ord('я') for c in text.lower()):
            return 'ru'
        return 'en'

    def generate_mindmap(self, text: str) -> str:
        """Генерирует майндмап из текста с помощью GPT-3.5"""
        try:
            cached_result = self.get_from_cache(text)
            if cached_result:
                return cached_result

            # Определяем язык текста или используем выбранный
            language = self.target_language if self.target_language != 'auto' else self.detect_language(text)
            system_prompt = self.system_prompts.get(language, self.system_prompts['en'])

            chunks = self.split_text_into_chunks(text)
            all_results = []
            
            for i, chunk in enumerate(chunks, 1):
                logger.info(f"Processing chunk {i}/{len(chunks)}")
                
                prompt = {
                    'ru': f"""
                    Создайте раздел майндмапа из этой части текста ({i}/{len(chunks)}).
                    Извлеките и организуйте ключевую информацию в четкую структуру.

                    Требования:
                    1. СТРУКТУРА:
                       - Используйте заголовки H2 для основных тем
                       - Используйте маркированные списки для ключевых деталей
                       - Поддерживайте четкую и организованную структуру
                    
                    2. СОДЕРЖАНИЕ:
                       - Сосредоточьтесь на основных идеях и концепциях
                       - Включите практические выводы и примеры
                       - Избегайте повторений
                       - Пропускайте техническую или издательскую информацию
                    
                    Часть текста {i}/{len(chunks)}:
                    {chunk}
                    """,
                    'en': f"""
                    Create a mind map section from this text part {i}/{len(chunks)}.
                    Extract and organize the key information into a clear structure.

                    Requirements:
                    1. STRUCTURE:
                       - Use H2 headings for main themes
                       - Use bullet points for key details
                       - Keep the structure clean and organized
                    
                    2. CONTENT:
                       - Focus on main ideas and concepts
                       - Include practical insights and examples
                       - Avoid repetition
                       - Skip technical or publishing information
                    
                    Text section {i}/{len(chunks)}:
                    {chunk}
                    """
                }[language]

                max_retries = 3
                retry_delay = self.request_delay
                
                for attempt in range(max_retries):
                    try:
                        time.sleep(retry_delay)
                        
                        response = self.client.chat.completions.create(
                            model="gpt-3.5-turbo-16k",
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.3,
                            max_tokens=2000,
                            presence_penalty=0.6,
                            frequency_penalty=0.7
                        )
                        
                        chunk_result = response.choices[0].message.content
                        all_results.append(chunk_result)
                        break
                        
                    except Exception as e:
                        if "rate_limit" in str(e).lower():
                            retry_delay *= 2
                            logger.warning(f"Rate limit hit, retrying in {retry_delay} seconds...")
                            continue
                        raise

                combined_result = self.combine_chunk_results(all_results)
                self.save_to_cache(text, combined_result)
                
                return combined_result

        except Exception as e:
            logger.error(f"Error generating mindmap: {str(e)}")
            raise

    def combine_chunk_results(self, results: List[str]) -> str:
        """Объединяет результаты обработки чанков в один майндмап"""
        combined_lines = []
        seen_content = set()
        main_title = None
        
        for chunk in results:
            lines = chunk.split('\n')
            for line in lines:
                cleaned_line = line.strip().lower()
                
                # Сохраняем первый заголовок первого уровня
                if line.startswith('# ') and not main_title:
                    main_title = line
                    combined_lines.append(line)
                    continue
                    
                # Пропускаем повторные заголовки первого уровня
                if line.startswith('# '):
                    continue
                    
                # Добавляем уникальные строки
                if cleaned_line and cleaned_line not in seen_content:
                    combined_lines.append(line)
                    seen_content.add(cleaned_line)
        
        return '\n'.join(combined_lines)

    def process_chapter(self, chapter_path: str, output_dir: Path) -> None:
        """Обрабатывает одну главу и создает для нее майндмап"""
        try:
            if chapter_path in self.processed_chapters:
                logger.info(f"Chapter already processed: {chapter_path}")
                return

            with open(chapter_path, 'r', encoding='utf-8') as f:
                content = f.read()
                title = next((line.replace('Title: ', '').strip() 
                             for line in content.split('\n') 
                             if line.startswith('Title: ')), "Untitled")

            logger.info(f"Processing chapter: {title}")
            
            # Проверяем размер главы
            if len(content.split()) > 10000:  # Если глава большая
                # Разбиваем на подсекции по смыслу
                sections = self.split_into_logical_sections(content)
                mindmap_parts = []
                
                for i, section in enumerate(sections):
                    # Генерируем майндмап для каждой секции
                    section_map = self.generate_mindmap(section)
                    mindmap_parts.append(section_map)
                
                # Объединяем результаты с сохранением структуры
                mindmap_content = self.merge_mindmap_sections(mindmap_parts)
            else:
                # Для небольших глав генерируем напрямую
                mindmap_content = self.generate_mindmap(content)

            chapter_filename = Path(chapter_path).stem
            mindmap_filename = output_dir / f"{chapter_filename}_mindmap.md"
            
            if not mindmap_filename.exists():
                with open(mindmap_filename, 'w', encoding='utf-8') as f:
                    f.write(f"# {title}\n\n")
                    f.write(mindmap_content)
                logger.info(f"✓ Created mindmap for: {title}")
            else:
                logger.info(f"Mindmap already exists for: {title}")

            self.processed_chapters.add(chapter_path)

        except Exception as e:
            logger.error(f"Error processing chapter: {title} - {str(e)}")
            raise

    def split_into_logical_sections(self, text: str) -> List[str]:
        """Разбивает текст на логические секции по заголовкам и смыслу"""
        sections = []
        current_section = []
        
        lines = text.split('\n')
        for line in lines:
            # Определяем начало новой секции по заголовкам
            if re.match(r'^#{1,3}\s', line) or len(current_section) > 5000:
                if current_section:
                    sections.append('\n'.join(current_section))
                current_section = [line]
            else:
                current_section.append(line)
        
        if current_section:
            sections.append('\n'.join(current_section))
        
        return sections

    def merge_mindmap_sections(self, sections: List[str]) -> str:
        """Объединяет секции майндмапа с сохранением структуры"""
        merged_lines = []
        seen_headers = set()
        
        for section in sections:
            lines = section.split('\n')
            for line in lines:
                # Пропускаем дубликаты заголовков
                if line.startswith('#'):
                    header = line.strip().lower()
                    if header in seen_headers:
                        continue
                    seen_headers.add(header)
                
                merged_lines.append(line)
        
        return '\n'.join(merged_lines)

def process_chapters_to_mindmaps(chapters_dir: str, output_dir: str) -> None:
    """Обрабатывает все главы в директории и создает майндмапы"""
    try:
        logger.info("Starting mindmap generation process")
        generator = MindMapGenerator()
        chapters_path = Path(chapters_dir)
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        # Собираем все файлы глав
        chapter_files = sorted(list(chapters_path.glob("*.txt")))
        total_chapters = len(chapter_files)
        logger.info(f"Found {total_chapters} chapters to process")
        
        # Сначала проверяем, какие главы нужно обработать
        chapters_to_process = []
        for chapter_file in chapter_files:
            chapter_filename = chapter_file.stem
            mindmap_filename = output_path / f"{chapter_filename}_mindmap.md"
            
            if not mindmap_filename.exists():
                chapters_to_process.append(chapter_file)

        if not chapters_to_process:
            logger.info("All chapters already processed, nothing to do")
            return

        logger.info(f"Need to process {len(chapters_to_process)} chapters")
        
        # Обрабатываем только те главы, для которых нет майндмапов
        for i, chapter_file in enumerate(chapters_to_process, 1):
            try:
                logger.info(f"Processing chapter {i}/{len(chapters_to_process)}")
                generator.process_chapter(str(chapter_file), output_path)
            except Exception as e:
                logger.error(f"Error processing {chapter_file}: {str(e)}")
                continue

        logger.info("Completed mindmap generation process")

    except Exception as e:
        logger.error(f"Error in process_chapters_to_mindmaps: {str(e)}")
        raise