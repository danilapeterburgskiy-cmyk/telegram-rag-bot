from sqlalchemy.orm import Session
from app.db.models import User, Message

def get_or_create_user(db: Session, telegram_id: int, username: str = None):
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        user = User(telegram_id=telegram_id, username=username)
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

def save_message(db: Session, user_id: int, question: str, answer: str):
    message = Message(user_id=user_id, question=question, answer=answer)
    db.add(message)
    db.commit()
    db.refresh(message)
    return message

def get_user_history(db: Session, telegram_id: int, limit: int = 10):
    user = get_or_create_user(db, telegram_id)
    return db.query(Message).filter(Message.user_id == user.id).order_by(Message.created_at.desc()).limit(limit).all()

def clear_user_history(db: Session, telegram_id: int):
    """Удаляет всю историю пользователя"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if user:
        db.query(Message).filter(Message.user_id == user.id).delete()
        db.commit()
        return True
    return False
