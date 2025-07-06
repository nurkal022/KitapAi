from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime, inspect, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, scoped_session
from datetime import datetime, timedelta
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
    
    # Subscription fields
    is_subscribed = Column(Boolean, default=False)
    stripe_customer_id = Column(String(100), nullable=True)
    trial_start_date = Column(DateTime, nullable=True)
    trial_end_date = Column(DateTime, nullable=True)
    subscription_end_date = Column(DateTime, nullable=True)
    
    mindmaps = relationship("MindMap", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.username}>"
    
    def is_trial_active(self) -> bool:
        """Check if user's trial is still active"""
        if self.trial_end_date is None:
            return False
        return datetime.utcnow() < self.trial_end_date
    
    def is_subscription_active(self) -> bool:
        """Check if user has active subscription"""
        if self.is_subscribed and self.subscription_end_date is not None:
            return datetime.utcnow() < self.subscription_end_date
        return False
    
    def can_access_service(self) -> bool:
        """Check if user can access the service (paid subscription only)"""
        return bool(self.is_subscription_active())

class Subscription(Base):
    __tablename__ = 'subscriptions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True)
    stripe_subscription_id = Column(String(100), nullable=True)
    stripe_price_id = Column(String(100), nullable=True)
    status = Column(String(20), default='active')  # active, canceled, past_due
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="subscriptions")
    
    def __repr__(self):
        return f"<Subscription {self.id} for user {self.user_id}>"

class PaymentHistory(Base):
    __tablename__ = 'payment_history'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), index=True)
    stripe_payment_intent_id = Column(String(100), nullable=True)
    amount = Column(Integer, nullable=True)  # Amount in cents
    currency = Column(String(3), default='usd')
    status = Column(String(20), default='pending')  # succeeded, failed, pending
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<PaymentHistory {self.id} for user {self.user_id}>"

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

# Subscription and Payment Functions
def start_user_trial(user_id: int) -> bool:
    """Start 14-day trial for user"""
    with db_manager.get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if user and not user.trial_start_date:
            user.trial_start_date = datetime.utcnow()
            user.trial_end_date = datetime.utcnow() + timedelta(days=14)
            return True
        return False

def get_user_subscription_status(user_id: int) -> dict | None:
    """Get user's subscription and trial status"""
    with db_manager.get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            return {
                'user_id': user.id,
                'is_subscribed': user.is_subscribed,
                'trial_start_date': user.trial_start_date.isoformat() if user.trial_start_date else None,
                'trial_end_date': user.trial_end_date.isoformat() if user.trial_end_date else None,
                'subscription_end_date': user.subscription_end_date.isoformat() if user.subscription_end_date else None,
                'can_access_service': user.can_access_service(),
                'is_trial_active': user.is_trial_active(),
                'is_subscription_active': user.is_subscription_active(),
                'stripe_customer_id': user.stripe_customer_id
            }
        return None

def update_user_stripe_customer(user_id: int, stripe_customer_id: str) -> bool:
    """Update user's Stripe customer ID"""
    with db_manager.get_db() as db:
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.stripe_customer_id = stripe_customer_id
            return True
        return False

def create_subscription(user_id: int, stripe_subscription_id: str, stripe_price_id: str, 
                       current_period_start: datetime, current_period_end: datetime, 
                       status: str = 'active') -> dict | None:
    """Create a new subscription record"""
    with db_manager.get_db() as db:
        subscription = Subscription(
            user_id=user_id,
            stripe_subscription_id=stripe_subscription_id,
            stripe_price_id=stripe_price_id,
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            status=status
        )
        db.add(subscription)
        
        # Update user subscription status - treat both 'active' and 'trialing' as active
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.is_subscribed = True
            user.subscription_end_date = current_period_end
        
        db.flush()
        return {
            'id': subscription.id,
            'user_id': subscription.user_id,
            'stripe_subscription_id': subscription.stripe_subscription_id,
            'status': subscription.status
        }

def update_subscription_status(stripe_subscription_id: str, status: str, 
                             current_period_end: datetime = None) -> bool:
    """Update subscription status"""
    with db_manager.get_db() as db:
        subscription = db.query(Subscription).filter(
            Subscription.stripe_subscription_id == stripe_subscription_id
        ).first()
        if subscription:
            subscription.status = status
            if current_period_end:
                subscription.current_period_end = current_period_end
            
            # Update user subscription status - treat both 'active' and 'trialing' as active
            user = db.query(User).filter(User.id == subscription.user_id).first()
            if user:
                if status in ['active', 'trialing']:
                    user.is_subscribed = True
                    user.subscription_end_date = current_period_end
                elif status in ['canceled', 'past_due']:
                    user.is_subscribed = False
                    user.subscription_end_date = current_period_end
            
            return True
        return False

def create_payment_record(user_id: int, stripe_payment_intent_id: str, 
                         amount: int, currency: str = 'usd', status: str = 'pending') -> dict:
    """Create a payment history record"""
    with db_manager.get_db() as db:
        payment = PaymentHistory(
            user_id=user_id,
            stripe_payment_intent_id=stripe_payment_intent_id,
            amount=amount,
            currency=currency,
            status=status
        )
        db.add(payment)
        db.flush()
        return {
            'id': payment.id,
            'user_id': payment.user_id,
            'amount': payment.amount,
            'status': payment.status,
            'created_at': payment.created_at.isoformat()
        }

def update_payment_status(stripe_payment_intent_id: str, status: str) -> bool:
    """Update payment status"""
    with db_manager.get_db() as db:
        payment = db.query(PaymentHistory).filter(
            PaymentHistory.stripe_payment_intent_id == stripe_payment_intent_id
        ).first()
        if payment:
            payment.status = status
            return True
        return False

def get_user_payment_history(user_id: int) -> list:
    """Get user's payment history"""
    with db_manager.get_db() as db:
        payments = db.query(PaymentHistory).filter(
            PaymentHistory.user_id == user_id
        ).order_by(PaymentHistory.created_at.desc()).all()
        return [{
            'id': payment.id,
            'amount': payment.amount,
            'currency': payment.currency,
            'status': payment.status,
            'created_at': payment.created_at.isoformat()
        } for payment in payments]

def get_user_subscriptions(user_id: int) -> list:
    """Get user's subscription records"""
    with db_manager.get_db() as db:
        subscriptions = db.query(Subscription).filter(
            Subscription.user_id == user_id
        ).order_by(Subscription.created_at.desc()).all()
        return [{
            'id': subscription.id,
            'stripe_subscription_id': subscription.stripe_subscription_id,
            'status': subscription.status,
            'current_period_start': subscription.current_period_start.isoformat() if subscription.current_period_start else None,
            'current_period_end': subscription.current_period_end.isoformat() if subscription.current_period_end else None,
            'created_at': subscription.created_at.isoformat()
        } for subscription in subscriptions]