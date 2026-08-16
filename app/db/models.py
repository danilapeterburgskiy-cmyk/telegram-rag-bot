from sqlalchemy import Column, Integer, BigInteger, String, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    messages = relationship("Message", back_populates="user")

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    sources = Column(Text, nullable=True)  # Храним ссылки на страницы
    created_at = Column(DateTime, default=datetime.utcnow)
    user = relationship("User", back_populates="messages")

class Page(Base):
    __tablename__ = "pages"
    id = Column(Integer, primary_key=True)
    url = Column(String(500), unique=True, nullable=False)
    title = Column(String(500))
    content = Column(Text)
    content_hash = Column(String(64))
    file_id = Column(String(100))          # ID в Yandex File Storage
    search_index_id = Column(String(100))  # ID индекса, в который загружен файл
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    sync_status = Column(String(20), default='pending')  # pending, synced, failed
    chunks = relationship("Chunk", back_populates="page")

class Chunk(Base):
    __tablename__ = "chunks"
    id = Column(Integer, primary_key=True)
    page_id = Column(Integer, ForeignKey("pages.id"))
    text = Column(Text, nullable=False)
    file_id = Column(String(100))
    index_id = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)
    page = relationship("Page", back_populates="chunks")
