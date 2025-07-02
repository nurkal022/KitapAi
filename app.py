import streamlit as st
import streamlit_markmap as markmap
import streamlit.components.v1 as stc
from pdf_mindmap_generator import PDFChapterExtractor
from mindmap_generator import MindMapGenerator, process_chapters_to_mindmaps
import tempfile
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
import hashlib
import json
from database import (
    db_manager, 
    get_user_by_username, 
    create_user, 
    get_user_mindmaps,
    create_mindmap,
    get_mindmap_by_id,
    delete_mindmap,
    update_mindmap
)
from sqlalchemy.orm import Session
from datetime import datetime
import time
import logging
from math import cos, sin, pi
from canvas_exporter import CanvasExporter
from html_exporter import HTMLExporter

# Загружаем переменные окружения
load_dotenv()

# Инициализируем базу данных
db_manager.init_db()

# Добавьте проверку окружения
is_prod = os.environ.get('IS_PRODUCTION', False)

if is_prod:
    # Продакшен настройки
    st.set_page_config(
        page_title="Kitap AI",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Настройка логирования
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

class MindMapApp:
    def __init__(self):
        self.setup_streamlit()
        self.pdf_extractor = PDFChapterExtractor()
        self.canvas_exporter = CanvasExporter()
        self.html_exporter = HTMLExporter()
        self.setup_session_state()
        
    def setup_streamlit(self):
        """Настройка конфигурации Streamlit"""
        st.set_page_config(
            page_title="Kitap AI",
            page_icon="📚",
            layout="wide"
        )
        
        st.markdown("""
            <style>
                /* Основные цвета */
                :root {
                    --primary-color: #004be0;
                    --bg-white: #ffffff;
                    --bg-main: #f4f4f4;
                    --border-radius: 16px;  /* Увеличенное скругление */
                }
                
                /* Общие стили */
                .main {
                    background-color: var(--bg-main);
                    padding: 2rem;
                }
                
                /* Кнопки */
                .stButton>button {
                    width: 100%;
                    background-color: var(--primary-color) !important;
                    color: white !important;
                    border-radius: var(--border-radius) !important;
                    height: 3rem;
                    transition: all 0.2s;
                    border: none !important;
                    font-size: 1.1rem;
                    padding: 0.5rem 1rem;
                    margin: 0.2rem 0;
                }
                
                /* Специальные стили для кнопок в списке */
                [data-testid="stHorizontalBlock"] .stButton>button {
                    min-height: 2.5rem;
                    font-size: 1rem;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 0.5rem;
                }
                
                /* Стили для кнопки удаления */
                [data-testid="stHorizontalBlock"] button[key*="delete_"] {
                    background-color: #dc3545 !important;
                }
                
                /* Стили для кнопки просмотра */
                [data-testid="stHorizontalBlock"] button[key*="view_"] {
                    background-color: #198754 !important;
                }
                
                /* Стили для кнопки экспорта */
                [data-testid="stHorizontalBlock"] button[key*="export_"] {
                    background-color: #6c757d !important;
                }
                
                /* Эффект при наведении */
                .stButton>button:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 8px 15px rgba(0,75,224,0.2);
                    opacity: 0.9;
                }
                
                /* Стили для разделителя */
                hr {
                    border: none;
                    height: 1px;
                    background-color: rgba(0,75,224,0.1);
                }
                
                /* Формы */
                .auth-form {
                    max-width: 400px;
                    margin: 0 auto;
                    padding: 2.5rem;
                    background: var(--bg-white);
                    border-radius: var(--border-radius);
                    box-shadow: 0 4px 20px rgba(0,75,224,0.1);
                }
                
                /* Список майндмапов */
                .mindmap-item {
                    padding: 1.8rem;
                    background: var(--bg-white);
                    border: 1px solid rgba(0,75,224,0.1);
                    margin: 1rem 0;
                    border-radius: var(--border-radius);
                    transition: all 0.3s;
                }
                
                .mindmap-item:hover {
                    box-shadow: 0 8px 25px rgba(0,75,224,0.15);
                    transform: translateY(-3px);
                }
                
                /* Tabs */
                .stTabs [data-baseweb="tab"] {
                    height: 3rem;
                    background-color: var(--bg-white);
                    border-radius: var(--border-radius);
                    color: var(--primary-color);
                    padding: 0 1.5rem;
                }
                
                .stTabs [aria-selected="true"] {
                    background-color: var(--primary-color) !important;
                    color: var(--bg-white) !important;
                }
                
                /* Текстовые поля */
                .stTextInput>div>div {
                    background-color: var(--bg-white);
                    border-radius: var(--border-radius);
                    border: 2px solid rgba(0,75,224,0.2);
                    padding: 0.5rem 1rem;
                }
                
                .stTextInput>div>div:focus-within {
                    border-color: var(--primary-color);
                    box-shadow: 0 0 0 2px rgba(0,75,224,0.2);
                }
                
                /* Заголовки */
                h1, h2, h3 {
                    color: var(--primary-color);
                }
                
                /* Прогресс бар */
                .stProgress > div > div > div {
                    background-color: var(--primary-color);
                    border-radius: var(--border-radius);
                }
                
                /* Сайдбар */
                .css-1d391kg {
                    background-color: var(--bg-white);
                    border-radius: var(--border-radius);
                    padding: 2rem 1rem;
                }
                
                /* Текстовая область */
                .stTextArea textarea {
                    border-radius: var(--border-radius);
                    border: 2px solid rgba(0,75,224,0.2);
                }
                
                .stTextArea textarea:focus {
                    border-color: var(--primary-color);
                    box-shadow: 0 0 0 2px rgba(0,75,224,0.2);
                }
                
                /* Убираем оранжевую обводку у текстовых полей */
                .stTextInput > div > div > input {
                    border-color: #ddd;
                    color: #000;
                }
                .stTextInput > div > div > input:focus {
                    box-shadow: none;
                    border-color: #004be0;
                }
                
                /* Убираем оранжевую обводку у кнопок */
                .stButton > button:focus {
                    box-shadow: none;
                    border-color: #004be0 !important;
                }
                
                /* Изменяем цвет фокуса на вкладках */
                .stTabs [data-baseweb="tab-highlight"] {
                    background-color: #004be0 !important;
                }
                
                /* Изменяем цвет прогресс-бара */
                .stProgress > div > div > div {
                    background-color: #004be0;
                }
                
                /* Изменяем цвет выделения текста */
                ::selection {
                    background-color: rgba(0, 75, 224, 0.2);
                    color: #004be0;
                }
                
                /* Убираем оранжевую обводку у всех элементов */
                *:focus {
                    outline: none !important;
                    box-shadow: none !important;
                }
                
                /* Изменяем цвет ссылок */
                a {
                    color: #004be0 !important;
                }
                
                /* Изменяем цвет подсветки при наведении на кнопки */
                .stButton > button:hover {
                    border-color: #004be0 !important;
                    color: white !important;
                }
                
                /* Изменяем цвет фона активных элементов */
                [data-baseweb="select"] > div:focus {
                    background-color: rgba(0, 75, 224, 0.1) !important;
                }
            </style>
        """, unsafe_allow_html=True)

    def setup_session_state(self):
        """Инициализация состояния сессии"""
        if 'logged_in' not in st.session_state:
            st.session_state.logged_in = False
        if 'user_id' not in st.session_state:
            st.session_state.user_id = None
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'dashboard'
        if 'delete_confirmation' not in st.session_state:
            st.session_state.delete_confirmation = None
        if 'current_mindmap' not in st.session_state:
            st.session_state.current_mindmap = None

    def hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def login_user(self, username: str, password: str) -> bool:
        user = get_user_by_username(username)
        if user and user['password'] == self.hash_password(password):
            st.session_state.logged_in = True
            st.session_state.user_id = user['id']
            return True
        return False

    def register_user(self, username: str, password: str) -> bool:
        if get_user_by_username(username):
            return False
        
        create_user(username, self.hash_password(password))
        return True

    def show_auth_page(self):
        """Страница аутентификации"""
        st.markdown("""
            <div style='text-align: center; padding: 2rem 0;'>
                <h1 style='color: #004be0; font-size: 2.5rem; margin-bottom: 0.5rem;'>📚 Kitap AI</h1>
                <p style='color: #666; font-size: 1.2rem;'>Transform your knowledge into visual mind maps</p>
            </div>
        """, unsafe_allow_html=True)
        
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            with st.form(key="login_form_unique"):
                st.subheader("Login")
                username = st.text_input("Username", key="login_username")
                password = st.text_input("Password", type="password", key="login_password")
                submit = st.form_submit_button("Login")
                
                if submit:
                    if self.login_user(username, password):
                        st.success("Successfully logged in!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
        
        with tab2:
            with st.form(key="register_form_unique"):
                st.subheader("Register")
                new_username = st.text_input("Username", key="register_username")
                new_password = st.text_input("Password", type="password", key="register_password")
                confirm_password = st.text_input("Confirm Password", type="password", key="register_confirm")
                submit = st.form_submit_button("Register")
                
                if submit:
                    if new_password != confirm_password:
                        st.error("Passwords do not match")
                    elif self.register_user(new_username, new_password):
                        st.success("Registration successful! Please login.")
                    else:
                        st.error("Username already exists")

    def show_dashboard(self):
        """Показывает список майндмапов пользователя"""
        st.markdown("""
            <div style='background-color: #ffffff; padding: 2rem; border-radius: 16px; margin-bottom: 2rem; box-shadow: 0 2px 10px rgba(0,75,224,0.1);'>
                <h1 style='margin: 0; color: #004be0;'>My Mind Maps</h1>
                <p style='color: #666; margin-top: 0.5rem; font-size: 1.1rem;'>Organize and visualize your knowledge</p>
            </div>
        """, unsafe_allow_html=True)
        
        # Кнопка создания нового майндмапа
        if st.button("➕ Create New MindMap", use_container_width=True):
            st.session_state.current_page = 'mindmap'
            st.session_state.current_mindmap = None
            st.rerun()
        
        # Добавляем разделитель
        st.markdown("---")
        
        # Список существующих майндмапов
        mindmaps = get_user_mindmaps(st.session_state.user_id)
        
        for mindmap in mindmaps:
            with st.container():
                col1, col2, col3, col4, col5, col6, col7 = st.columns([4, 1, 1, 1, 1, 1, 1])
                
                with col1:
                    st.markdown(f"""
                        <div style='padding: 0.5rem 0;'>
                            <h3 style='margin: 0; color: #004be0;'>{mindmap['name']}</h3>
                            <p style='color: #666; margin: 0.3rem 0;'>
                                Last updated: {datetime.fromisoformat(mindmap['updated_at']).strftime('%Y-%m-%d %H:%M')}
                            </p>
                        </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    if st.button("📝 Edit", key=f"edit_{mindmap['id']}", 
                               help="Edit this mindmap",
                               use_container_width=True):
                        # Очищаем состояние предыдущего майндмапа
                        st.session_state.current_content = None
                        st.session_state.current_mindmap_id = None
                        # Устанавливаем новый майндмап
                        st.session_state.current_mindmap = mindmap['id']
                        st.session_state.current_page = 'mindmap'
                        st.rerun()
                
                with col3:
                    if st.button("👁️ View", key=f"view_{mindmap['id']}", 
                               help="View this mindmap",
                               use_container_width=True):
                        st.session_state.current_mindmap = mindmap['id']
                        st.session_state.current_page = 'view'
                        st.rerun()
                
                with col4:
                    # Кнопка экспорта в Markdown
                    st.download_button(
                        label="📤 MD",
                        data=mindmap['content'],
                        file_name=f"{mindmap['name']}.md",
                        mime="text/markdown",
                        key=f"export_md_{mindmap['id']}",
                        help="Download as Markdown",
                        use_container_width=True
                    )

                with col5:
                    # Кнопка экспорта в HTML
                    content_str = mindmap['content'] if mindmap['content'] is not None else ""
                    html_content = self.html_exporter.markdown_to_html(
                        title=mindmap['name'],
                        content=content_str
                    )
                    st.download_button(
                        label="🌐 HTML",
                        data=html_content,
                        file_name=f"{mindmap['name']}.html",
                        mime="text/html",
                        key=f"export_html_{mindmap['id']}",
                        help="Download as interactive HTML",
                        use_container_width=True
                    )

                # with col6:
                #     # Кнопка экспорта в формат Obsidian Canvas
                #     canvas_data = self.canvas_exporter.markdown_to_canvas(mindmap['content'])
                #     st.download_button(
                #         label="🎨 Canvas",
                #         data=canvas_data,
                #         file_name=f"{mindmap['name']}.canvas",
                #         mime="application/json",
                #         key=f"export_canvas_{mindmap['id']}",
                #         help="Download as Obsidian Canvas format",
                #         use_container_width=True
                #     )
                
                with col6:
                    # Логика удаления
                    if st.session_state.delete_confirmation == mindmap['id']:
                        col7_1, col7_2 = st.columns(2)
                        with col7_1:
                            if st.button("✓", key=f"confirm_yes_{mindmap['id']}", 
                                       help="Confirm deletion",
                                       use_container_width=True):
                                delete_mindmap(mindmap['id'])
                                st.session_state.delete_confirmation = None
                                st.rerun()
                        with col7_2:
                            if st.button("✗", key=f"confirm_no_{mindmap['id']}", 
                                       help="Cancel deletion",
                                       use_container_width=True):
                                st.session_state.delete_confirmation = None
                                st.rerun()
                    else:
                        if st.button("🗑️", key=f"delete_{mindmap['id']}", 
                                   help="Delete this mindmap",
                                   use_container_width=True):
                            st.session_state.delete_confirmation = mindmap['id']
                            st.rerun()
                
                # Добавляем разделитель между майндмапами
                st.markdown("<hr style='margin: 1rem 0; opacity: 0.2;'>", unsafe_allow_html=True)

    def show_mindmap_page(self):
        """Страница работы с майндмапом (создание/редактирование)"""
        if st.session_state.current_mindmap is None:
            st.title("Create New MindMap")
            
            tab1, tab2, tab3 = st.tabs(["Create New", "Import from File", "Generate from Prompt"])
            
            with tab1:
                name = st.text_input("MindMap Name")
                
                # Добавляем выбор языка
                languages = {
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
                target_language = st.selectbox(
                    "Select mindmap language",
                    options=list(languages.keys()),
                    format_func=lambda x: languages[x],
                    index=0
                )
                
                if st.button("Create Empty MindMap"):
                    if name:
                        new_mindmap = create_mindmap(
                            user_id=st.session_state.user_id,
                            name=name,
                            content="# " + name
                        )
                        st.success("MindMap created! Redirecting to editor...")
                        st.session_state.current_mindmap = new_mindmap['id']
                        st.rerun()
                    else:
                        st.error("Please enter a name for your mindmap")
            
            with tab2:
                uploaded_file = st.file_uploader("Choose PDF or Markdown file", type=['pdf', 'md'])
                if uploaded_file:
                    try:
                        # Добавляем выбор языка для загруженного файла
                        target_language = st.selectbox(
                            "Select output language",
                            options=list(languages.keys()),
                            format_func=lambda x: languages[x],
                            index=0,
                            key="upload_language"
                        )
                        
                        if st.button("Process File"):
                            # Создаем генератор с выбранным языком
                            generator = MindMapGenerator(target_language=target_language)
                            
                            # Остальной код обработки файла...
                    except Exception as e:
                        st.error(f"Error processing file: {str(e)}")
            
            with tab3:
                name = st.text_input("MindMap Name", key="prompt_mindmap_name")
                
                # Выбор языка
                languages = {
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
                target_language = st.selectbox(
                    "Select mindmap language",
                    options=list(languages.keys()),
                    format_func=lambda x: languages[x],
                    index=0,
                    key="prompt_language"
                )
                
                # Поля для ввода темы и описания
                topic = st.text_input("Topic", placeholder="Enter the main topic of your mind map")
                description = st.text_area(
                    "Description",
                    placeholder="Describe what you want to include in your mind map. Add key points, concepts, and any specific areas you want to cover.",
                    height=200
                )
                
                if st.button("Generate Mind Map", key="generate_from_prompt"):
                    if not name or not topic or not description:
                        st.error("Please fill in all fields")
                    else:
                        try:
                            with st.spinner("Generating mind map..."):
                                generator = MindMapGenerator(target_language=target_language)
                                
                                # Формируем промпт для генерации
                                prompt = f"""
                                Topic: {topic}
                                
                                Description:
                                {description}
                                
                                Please create a detailed mind map about this topic.
                                """
                                
                                # Генерируем майндмап
                                mindmap_content = generator.generate_mindmap(prompt)
                                
                                # Создаем новый майндмап
                                new_mindmap = create_mindmap(
                                    user_id=st.session_state.user_id,
                                    name=name,
                                    content=mindmap_content
                                )
                                
                                st.success("Mind map generated successfully!")
                                
                                # Показываем предпросмотр
                                with st.expander("Preview Generated Mind Map", expanded=True):
                                    cleaned_content = self.clean_mindmap_content(mindmap_content)
                                    markmap.markmap(cleaned_content)
                                
                                # Автоматически переходим к редактированию
                                st.session_state.current_mindmap = new_mindmap['id']
                                st.session_state.current_content = mindmap_content
                                st.session_state.current_mindmap_id = new_mindmap['id']
                                
                                # Добавляем кнопки действий
                                col1, col2 = st.columns(2)
                                with col1:
                                    if st.button("✏️ Edit Mind Map"):
                                        st.rerun()
                                with col2:
                                    if st.button("📋 Back to Dashboard"):
                                        st.session_state.current_page = 'dashboard'
                                        st.rerun()
                                
                        except Exception as e:
                            st.error(f"Error generating mind map: {str(e)}")
        
        else:
            # Редактирование существующего майндмапа
            mindmap = get_mindmap_by_id(st.session_state.current_mindmap)
            if not mindmap:
                st.error("MindMap not found")
                st.session_state.current_page = 'dashboard'
                st.rerun()
            
            st.title(f"Edit: {mindmap['name']}")
            
            # Добавляем кнопку для полноэкранного просмотра
            if st.button("🔍 Full Screen Preview"):
                st.session_state.show_fullscreen = True
                st.rerun()
            
            # Проверяем режим отображения
            if st.session_state.get('show_fullscreen', False):
                # Кнопка возврата к редактору
                if st.button("← Back to Editor"):
                    st.session_state.show_fullscreen = False
                    st.rerun()
                
                # Показываем майндмап на всю ширину
                st.markdown("### Full Screen Preview")
                cleaned_content = self.clean_mindmap_content(mindmap['content'])
                markmap.markmap(cleaned_content, height=800)
            else:
                # Стандартный режим с двумя колонками
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.subheader("Markdown Editor")
                    
                    # Инициализируем состояние для контента текущего майндмапа
                    if ('current_content' not in st.session_state or 
                        st.session_state.get('current_mindmap_id') != mindmap['id']):
                        st.session_state.current_content = mindmap['content']
                        st.session_state.current_mindmap_id = mindmap['id']
                    
                    # Функция обратного вызова для обновления контента
                    def on_content_change():
                        key = f"markdown_input_{mindmap['id']}"
                        if key in st.session_state:
                            st.session_state.current_content = st.session_state[key]
                            update_mindmap(mindmap['id'], mindmap['name'], st.session_state.current_content)
                    
                    # Редактор markdown с callback
                    content = st.text_area(
                        "Edit Content",
                        value=st.session_state.current_content,
                        height=500,
                        key=f"markdown_input_{mindmap['id']}",  # Уникальный ключ для каждого майндмапа
                        on_change=on_content_change
                    )
                    
                    # Кнопки для импорта дополнительного контента
                    import_tab1, import_tab2 = st.tabs(["Import from PDF", "Import from Markdown"])
                    
                    with import_tab1:
                        if 'processed_pdfs' not in st.session_state:
                            st.session_state.processed_pdfs = set()
                        
                        uploaded_file = st.file_uploader("📄 Add from PDF", type=['pdf'])
                        if uploaded_file:
                            file_id = f"{uploaded_file.name}_{len(uploaded_file.getvalue())}"
                            
                            if file_id not in st.session_state.processed_pdfs:
                                with tempfile.TemporaryDirectory() as temp_dir:
                                    try:
                                        # Сохраняем PDF
                                        pdf_path = os.path.join(temp_dir, uploaded_file.name)
                                        with open(pdf_path, "wb") as f:
                                            f.write(uploaded_file.getvalue())
                                        
                                        # Создаем контейнеры для вывода информации
                                        status_container = st.empty()
                                        progress_container = st.empty()
                                        chapter_status = st.empty()
                                        result_container = st.empty()
                                        
                                        with st.spinner("Analyzing PDF structure..."):
                                            # Извлекаем главы
                                            chapters = self.pdf_extractor.extract_chapters(pdf_path)
                                            
                                            if not chapters:
                                                st.error("❌ No chapters could be extracted from the PDF")
                                                return
                                            
                                            # Показываем информацию о найденных главах
                                            status_container.info(f"📑 Found {len(chapters)} chapters in the document")
                                            
                                            # Создаем директории
                                            chapters_dir = os.path.join(temp_dir, "chapters")
                                            mindmaps_dir = os.path.join(temp_dir, "mindmaps")
                                            os.makedirs(chapters_dir, exist_ok=True)
                                            os.makedirs(mindmaps_dir, exist_ok=True)
                                            
                                            try:
                                                # Сохраняем главы в файлы
                                                self.pdf_extractor.save_chapters_to_files(chapters, chapters_dir)
                                                
                                                # Показываем прогресс-бар
                                                progress_bar = progress_container.progress(0)
                                                total_chapters = len(chapters)
                                                
                                                # Создаем очередь для отслеживания прогресса
                                                processed_chapters = []
                                                
                                                def update_progress():
                                                    progress = len(processed_chapters) / total_chapters
                                                    progress_bar.progress(progress)
                                                    chapter_status.markdown(f"""
                                                        ### Processing Progress:
                                                        - Total Chapters: {total_chapters}
                                                        - Processed: {len(processed_chapters)}
                                                        - Remaining: {total_chapters - len(processed_chapters)}
                                                    """)
                                                
                                                # Добавляем состояние для контроля генерации
                                                if 'is_generating' not in st.session_state:
                                                    st.session_state.is_generating = False
                                                if 'generated_content' not in st.session_state:
                                                    st.session_state.generated_content = None
                                                
                                                # Streamlined generation controls
                                                if st.button("🚀 Start Generation" if not st.session_state.is_generating else "🛑 Stop Generation"):
                                                    st.session_state.is_generating = not st.session_state.is_generating
                                                    st.rerun()
                                                
                                                if st.session_state.is_generating:
                                                    # Обрабатываем каждую главу
                                                    current_content = st.session_state.generated_content
                                                    has_errors = False

                                                    for i, (title, content) in enumerate(chapters, 1):
                                                        if not st.session_state.is_generating:
                                                            st.warning("🛑 Generation stopped by user")
                                                            break

                                                        try:
                                                            # Показываем статус текущей главы
                                                            chapter_status.markdown(f"""
                                                                ### 🔄 Processing Chapter {i}/{total_chapters}
                                                                - Title: **{title}**
                                                            """)

                                                            # Сохраняем текущую главу во временный файл
                                                            chapter_file = os.path.join(chapters_dir, f"chapter_{i:02d}.txt")
                                                            with open(chapter_file, 'w', encoding='utf-8') as f:
                                                                f.write(f"Title: {title}\n{'='*50}\n\n{content}")

                                                            try:
                                                                # Обрабатываем главу
                                                                process_chapters_to_mindmaps(
                                                                    chapters_dir,
                                                                    mindmaps_dir
                                                                )

                                                                # Читаем сгенерированный майндмап
                                                                mindmap_file = os.path.join(mindmaps_dir, f"chapter_{i:02d}_mindmap.md")
                                                                with open(mindmap_file, 'r', encoding='utf-8') as f:
                                                                    chapter_mindmap = f.read()

                                                                # Добавляем к текущему контенту
                                                                current_content = f"{current_content}\n\n{chapter_mindmap}"
                                                                
                                                                # Обновляем майндмап в базе данных после каждой успешной главы
                                                                update_mindmap(mindmap['id'], mindmap['name'], current_content)
                                                                st.session_state.current_content = current_content

                                                                # Удаляем вывод текущего результата
                                                                processed_chapters.append(title)
                                                                progress = min(i / total_chapters, 1.0)
                                                                progress_container.progress(progress)

                                                            except Exception as chapter_error:
                                                                has_errors = True
                                                                st.error(f"❌ Error in Chapter {i}: {title}")
                                                                logger.error(f"Error details: {str(chapter_error)}")
                                                                continue

                                                        except Exception as e:
                                                            has_errors = True
                                                            st.error(f"❌ Error preparing chapter {i}: {title}")
                                                            logger.error(f"Error details: {str(e)}")
                                                            continue

                                                    # После завершения всех глав или остановки
                                                    if st.session_state.is_generating:
                                                        st.session_state.is_generating = False
                                                        
                                                        # Показываем только кнопку подтверждения
                                                        st.success("✅ Generation completed!")
                                                        
                                                        if st.button("✔️ Apply Generated Content"):
                                                            # Применяем сгенерированный контент
                                                            st.session_state.current_content = st.session_state.generated_content
                                                            update_mindmap(mindmap['id'], mindmap['name'], st.session_state.current_content)
                                                            st.session_state.generated_content = None
                                                            st.session_state.is_generating = False
                                                            st.success("✨ Content updated successfully!")
                                                            st.rerun()

                                            except Exception as api_error:
                                                if "insufficient_quota" in str(api_error):
                                                    st.error("❌ OpenAI API quota exceeded. Please contact support or try again later.")
                                                else:
                                                    st.error(f"❌ Error processing PDF: {str(api_error)}")
                                                return
                                                
                                    except Exception as e:
                                        st.error(f"❌ Error processing file: {str(e)}")
                
                    with import_tab2:
                        # Добавляем ключ состояния для отслеживания обработанных файлов
                        if 'processed_files' not in st.session_state:
                            st.session_state.processed_files = set()
                        
                        uploaded_md = st.file_uploader("📄 Add from Markdown", type=['md'], key="md_append")
                        if uploaded_md:
                            # Создаем уникальный идентификатор файла
                            file_id = f"{uploaded_md.name}_{len(uploaded_md.getvalue())}"
                            
                            # Проверяем, не был ли файл уже обработан
                            if file_id not in st.session_state.processed_files:
                                try:
                                    # Читаем новый контент
                                    new_content = uploaded_md.getvalue().decode('utf-8')
                                    
                                    # Собираем весь контент вместе
                                    combined_content = f"{st.session_state.current_content}\n\n{new_content}"
                                    
                                    # Обновляем состояние и базу данных за один раз
                                    st.session_state.current_content = combined_content
                                    update_mindmap(mindmap['id'], mindmap['name'], combined_content)
                                    
                                    # Отмечаем файл как обработанный
                                    st.session_state.processed_files.add(file_id)
                                    
                                    # Показываем сообщение об успехе и обновляем страницу один раз
                                    st.success("Markdown content added successfully!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error importing markdown: {str(e)}")
                
                with col2:
                    st.subheader("Preview")
                    cleaned_content = self.clean_mindmap_content(st.session_state.current_content)

                    # Render Markmap and PNG export button together in a single HTML block
                    import json as _json
                    content_str = st.session_state.current_content if st.session_state.current_content is not None else ""
                    markmap_data = _json.dumps({
                        "content": "Mindmap",
                        "children": HTMLExporter().parse_markdown_to_json(content_str)
                    })
                    stc.html(f'''
                        <div id="markmap-container" style="background:white;border-radius:16px;padding:16px;">
                            <button id="export-png-btn" style="margin-bottom:10px;padding:8px 16px;background:#004be0;color:white;border:none;border-radius:8px;cursor:pointer;font-size:1rem;">🖼️ Export as PNG</button>
                            <button id="export-svg-btn" style="margin-bottom:10px;margin-left:10px;padding:8px 16px;background:#198754;color:white;border:none;border-radius:8px;cursor:pointer;font-size:1rem;">🗺️ Export as SVG</button>
                            <svg id="mindmap-svg" width="900" height="600"></svg>
                        </div>
                        <script src="https://cdn.jsdelivr.net/npm/d3@7.9.0/dist/d3.min.js"></script>
                        <script src="https://cdn.jsdelivr.net/npm/markmap-view@0.17.3-alpha.8/dist/browser/index.js"></script>
                        <script>
                        const data = {markmap_data};
                        const svg = document.getElementById('mindmap-svg');
                        window.mm = window.markmap.Markmap.create(svg, null, data);
                        window.mm.fit();
                        function downloadSVGAsPNG(svgId, filename) {{
                            var svg = document.getElementById(svgId);
                            var serializer = new XMLSerializer();
                            var svgString = serializer.serializeToString(svg);
                            var canvas = document.createElement('canvas');
                            var bbox = svg.getBBox();
                            canvas.width = bbox.width + bbox.x;
                            canvas.height = bbox.height + bbox.y;
                            var ctx = canvas.getContext('2d');
                            var img = new window.Image();
                            img.onload = function() {{
                                ctx.clearRect(0, 0, canvas.width, canvas.height);
                                ctx.drawImage(img, 0, 0);
                                var a = document.createElement('a');
                                a.download = filename;
                                a.href = canvas.toDataURL('image/png');
                                document.body.appendChild(a);
                                a.click();
                                document.body.removeChild(a);
                            }};
                            img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgString)));
                        }}
                        function downloadSVG(svgId, filename) {{
                            var svg = document.getElementById(svgId);
                            var serializer = new XMLSerializer();
                            var svgString = serializer.serializeToString(svg);
                            var blob = new Blob([svgString], {{type: 'image/svg+xml'}});
                            var a = document.createElement('a');
                            a.download = filename;
                            a.href = URL.createObjectURL(blob);
                            document.body.appendChild(a);
                            a.click();
                            document.body.removeChild(a);
                        }}
                        document.getElementById('export-png-btn').onclick = function() {{
                            downloadSVGAsPNG('mindmap-svg', 'mindmap.png');
                        }};
                        document.getElementById('export-svg-btn').onclick = function() {{
                            downloadSVG('mindmap-svg', 'mindmap.svg');
                        }};
                        </script>
                    ''', height=650)

        with st.expander("ℹ️ Tips for editing"):
            st.markdown("""
                - Use `#` for main topics
                - Use `-` for bullet points
                - Double line breaks create new sections
                - Preview updates automatically
            """)

        with st.expander("💡 Tips for better results"):
            st.markdown("""
                ### How to get better results:
                
                1. **Topic**
                   - Be specific and clear
                   - Use descriptive titles
                   - Avoid overly broad topics
                
                2. **Description**
                   - Include key concepts you want to cover
                   - Mention specific areas or subtopics
                   - Add any important relationships between concepts
                   - Include examples if relevant
                   - Specify the desired depth of coverage
                
                3. **Best Practices**
                   - Break complex topics into smaller chunks
                   - Use clear and simple language
                   - Mention specific aspects you want to explore
                   - Include any specific organization preferences
            """)

    def show_mindmap_view(self):
        """Показывает выбранный майндмап"""
        mindmap = get_mindmap_by_id(st.session_state.current_mindmap)
        
        if mindmap:
            st.title(mindmap['name'])
            
            # Кнопка возврата
            if st.button("Back to Dashboard"):
                st.session_state.current_page = 'dashboard'
                st.rerun()
            
            # Показываем очищенный майндмап
            cleaned_content = self.clean_mindmap_content(mindmap['content'])
            markmap.markmap(cleaned_content)
        else:
            st.error("MindMap not found")
            st.session_state.current_page = 'dashboard'
            st.rerun()

    def show_main_page(self):
        """Основная страница после авторизации"""
        with st.sidebar:
            # Создаем два столбца для логотипа и названия
            logo_col, text_col = st.columns([1, 3])
            
            with logo_col:
                # Отображаем логотип через st.image
                st.image("logo.png", width=100)
            
            with text_col:
                st.markdown("""
                    <div style='padding-left: 0.5rem;'>
                        <h2 style='margin: 0; color: #004be0; font-size: 1.5rem;'>Kitap AI</h2>
                        <p style='margin: 0; color: #666; font-size: 0.9rem;'>Mind Map Generator</p>
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            menu_items = {
                "dashboard": "📊 Dashboard",
                "create": "➕ Create New",
                "pricing": "💎 Pricing",
                "settings": "⚙ Settings",
                "logout": "🚪 Logout"
            }
            
            for key, label in menu_items.items():
                if st.button(label, key=f"menu_{key}"):
                    st.session_state.current_page = key
                    st.rerun()
        
        # Показываем соответствующую страницу
        if st.session_state.current_page == 'dashboard':
            self.show_dashboard()
        elif st.session_state.current_page == 'mindmap':
            self.show_mindmap_page()
        elif st.session_state.current_page == 'view':
            self.show_mindmap_view()
        elif st.session_state.current_page == 'pricing':
            self.show_pricing_page()

    def main(self):
        """Основная логика приложения"""
        if not st.session_state.logged_in:
            self.show_auth_page()
        else:
            self.show_main_page()

    def show_pricing_page(self):
        """Страница с информацией о подписках"""
        st.markdown("""
            <div style='text-align: center; padding: 2rem 0;'>
                <h1 style='color: #004be0; font-size: 2.5rem; margin-bottom: 1rem;'>Pricing Plans</h1>
                <p style='color: #666; font-size: 1.2rem; margin-bottom: 3rem;'>
                    Choose the perfect plan for your needs
                </p>
            </div>
        """, unsafe_allow_html=True)

        # Создаем два столбца для планов подписки
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("""
                <div style='background: white; padding: 2rem; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,75,224,0.1);'>
                    <div style='text-align: center;'>
                        <h2 style='color: #004be0; margin-bottom: 0.5rem;'>Personal Plan</h2>
                        <p style='color: #666; font-size: 1.1rem; margin-bottom: 1rem;'>Perfect for individual users</p>
                        <h1 style='color: #004be0; font-size: 3rem; margin: 1.5rem 0;'>$20<span style='font-size: 1rem;'>/month</span></h1>
                    </div>
                    <div style='margin: 2rem 0;'>
                        <p style='margin: 1rem 0; color: #444;'>✓ Unlimited mind maps</p>
                        <p style='margin: 1rem 0; color: #444;'>✓ PDF import feature</p>
                        <p style='margin: 1rem 0; color: #444;'>✓ AI-powered generation</p>
                        <p style='margin: 1rem 0; color: #444;'>✓ Export to multiple formats</p>
                        <p style='margin: 1rem 0; color: #444;'>✓ Basic support</p>
                    </div>
                    <button style='
                        width: 100%;
                        background-color: #004be0;
                        color: white;
                        border: none;
                        padding: 1rem;
                        border-radius: 8px;
                        font-size: 1.1rem;
                        cursor: pointer;
                        transition: all 0.2s;
                    '>Get Started</button>
                </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown("""
                <div style='background: white; padding: 2rem; border-radius: 16px; box-shadow: 0 4px 20px rgba(0,75,224,0.1);'>
                    <div style='text-align: center;'>
                        <h2 style='color: #004be0; margin-bottom: 0.5rem;'>Enterprise Plan</h2>
                        <p style='color: #666; font-size: 1.1rem; margin-bottom: 1rem;'>For teams and organizations</p>
                        <h1 style='color: #004be0; font-size: 3rem; margin: 1.5rem 0;'>$200<span style='font-size: 1rem;'>/month</span></h1>
                    </div>
                    <div style='margin: 2rem 0;'>
                        <p style='margin: 1rem 0; color: #444;'>✓ Everything in Personal Plan</p>
                        <p style='margin: 1rem 0; color: #444;'>✓ Unlimited team members</p>
                        <p style='margin: 1rem 0; color: #444;'>✓ Advanced collaboration tools</p>
                        <p style='margin: 1rem 0; color: #444;'>✓ Custom AI model training</p>
                        <p style='margin: 1rem 0; color: #444;'>✓ Priority 24/7 support</p>
                        <p style='margin: 1rem 0; color: #444;'>✓ API access</p>
                        <p style='margin: 1rem 0; color: #444;'>✓ Custom integration</p>
                    </div>
                    <button style='
                        width: 100%;
                        background-color: #004be0;
                        color: white;
                        border: none;
                        padding: 1rem;
                        border-radius: 8px;
                        font-size: 1.1rem;
                        cursor: pointer;
                        transition: all 0.2s;
                    '>Contact Sales</button>
                </div>
            """, unsafe_allow_html=True)

        # Добавляем FAQ секцию
        st.markdown("""
            <div style='margin-top: 4rem; text-align: center;'>
                <h2 style='color: #004be0; margin-bottom: 2rem;'>Frequently Asked Questions</h2>
            </div>
        """, unsafe_allow_html=True)

        with st.expander("What payment methods do you accept?"):
            st.write("We accept all major credit cards, PayPal, and bank transfers for enterprise customers.")

        with st.expander("Can I switch between plans?"):
            st.write("Yes, you can upgrade or downgrade your plan at any time. Changes will be reflected in your next billing cycle.")

        with st.expander("Is there a free trial?"):
            st.write("Yes, we offer a 14-day free trial for both Personal and Enterprise plans.")

        with st.expander("What kind of support do you provide?"):
            st.write("Personal plan includes email support with 24-hour response time. Enterprise plan includes priority 24/7 support via email, phone, and chat.")

    # Добавим новую функцию для очистки контента майндмапа
    def clean_mindmap_content(self, content: str) -> str:
        """
        Очищает контент майндмапа от лишних символов и форматирования и добавляет параметры markmap
        """
        if not content:
            return ""
        
        # Добавляем параметры markmap в начало контента
        markmap_params = """---
title: markmap
markmap:
  colorFreezeLevel: 2
  maxWidth: 300
  initialExpandLevel: 2
---

"""
        
        # Удаляем блоки кода
        lines = content.split('\n')
        cleaned_lines = []
        in_code_block = False
        
        for line in lines:
            # Проверяем начало/конец блока кода
            if line.strip().startswith('```'):
                in_code_block = not in_code_block
                continue
            
            # Пропускаем строки внутри блока кода
            if not in_code_block:
                cleaned_lines.append(line)
        
        # Собираем очищенный контент
        cleaned_content = '\n'.join(cleaned_lines)
        
        # Удаляем лишние пробелы и пустые строки
        cleaned_content = '\n'.join(line for line in cleaned_content.split('\n') if line.strip())
        
        # Проверяем, что контент начинается с заголовка
        if not cleaned_content.strip().startswith('#'):
            cleaned_content = f"# Mindmap\n{cleaned_content}"
        
        # Добавляем параметры markmap к очищенному контенту
        return markmap_params + cleaned_content

if __name__ == "__main__":
    app = MindMapApp()
    app.main() 