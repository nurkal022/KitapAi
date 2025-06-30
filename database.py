from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from datetime import datetime
from contextlib import contextmanager
import os
from typing import Generator
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Базовые настройки
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, 'mindmap.db')
SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_FILE}"

# Создаем базовый класс для моделей
Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password = Column(String(256), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    mindmaps = relationship("MindMap", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.username}>"

class MindMap(Base):
    __tablename__ = 'mindmaps'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user_id = Column(Integer, ForeignKey('users.id'), index=True)
    
    user = relationship("User", back_populates="mindmaps")
    
    def __repr__(self):
        return f"<MindMap {self.name}>"
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'content': self.content,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

class DatabaseManager:
    def __init__(self):
        self._engine = None
        self._session_factory = None
        self._scoped_session = None

    def init_db(self) -> None:
        """Инициализация базы данных"""
        if not self._engine:
            self._engine = create_engine(
                SQLALCHEMY_DATABASE_URL,
                connect_args={"check_same_thread": False},
                pool_pre_ping=True,
                pool_recycle=3600
            )
            
            self._session_factory = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self._engine
            )
            
            self._scoped_session = scoped_session(self._session_factory)
            
            # Проверяем существование таблиц
            inspector = inspect(self._engine)
            existing_tables = inspector.get_table_names()
            
            # Создаем только отсутствующие таблицы
            for table in Base.metadata.tables.values():
                if table.name not in existing_tables:
                    table.create(self._engine)
                    logger.info(f"Created table: {table.name}")
                else:
                    logger.info(f"Table already exists: {table.name}")

    @contextmanager
    def get_db(self) -> Generator:
        """Получение сессии базы данных"""
        if not self._session_factory:
            self.init_db()
            
        db = self._scoped_session()
        try:
            yield db
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Database error: {str(e)}")
            raise
        finally:
            db.close()
            
    def recreate_db(self) -> None:
        """Пересоздание базы данных"""
        try:
            # Закрываем все соединения
            if self._engine:
                self._engine.dispose()
            
            # Удаляем файл базы данных
            if os.path.exists(DB_FILE):
                os.remove(DB_FILE)
                logger.info("Existing database file removed")
            
            # Пересоздаем базу
            self.init_db()
            logger.info("Database recreated successfully")
        except Exception as e:
            logger.error(f"Error recreating database: {str(e)}")
            raise

# Создаем глобальный экземпляр менеджера базы данных
db_manager = DatabaseManager()

# Функции для работы с пользователями
def get_user_by_username(username: str):
    with db_manager.get_db() as db:
        user = db.query(User).filter(User.username == username).first()
        if user:
            # Загружаем все атрибуты пользователя
            db.refresh(user)
            return {
                'id': user.id,
                'username': user.username,
                'password': user.password
            }
        return None

def create_user(username: str, hashed_password: str) -> dict:
    with db_manager.get_db() as db:
        user = User(username=username, password=hashed_password)
        db.add(user)
        db.flush()  # Чтобы получить id
        return {
            'id': user.id,
            'username': user.username,
            'password': user.password
        }

def get_user_mindmaps(user_id: int) -> list:
    with db_manager.get_db() as db:
        mindmaps = db.query(MindMap).filter(MindMap.user_id == user_id).all()
        return [mindmap.to_dict() for mindmap in mindmaps]

# Функции для работы с майндмапами
def create_mindmap(user_id: int, name: str, content: str) -> dict:
    """Создает новый майндмап"""
    with db_manager.get_db() as db:
        mindmap = MindMap(user_id=user_id, name=name, content=content)
        db.add(mindmap)
        db.flush()  # Чтобы получить id
        return mindmap.to_dict()

def get_mindmap_by_id(mindmap_id: int) -> dict:
    with db_manager.get_db() as db:
        mindmap = db.query(MindMap).filter(MindMap.id == mindmap_id).first()
        if mindmap:
            return mindmap.to_dict()
        return None

def delete_mindmap(mindmap_id: int) -> bool:
    with db_manager.get_db() as db:
        mindmap = db.query(MindMap).filter(MindMap.id == mindmap_id).first()
        if mindmap:
            db.delete(mindmap)
            return True
        return False

def update_mindmap(mindmap_id: int, name: str, content: str) -> dict:
    """Обновляет существующий майндмап"""
    with db_manager.get_db() as db:
        mindmap = db.query(MindMap).filter(MindMap.id == mindmap_id).first()
        if mindmap:
            mindmap.name = name
            mindmap.content = content
            db.flush()  # Обновляем объект в сессии
            return mindmap.to_dict()
        return None