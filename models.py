from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from database import Base
from datetime import datetime

class Comment(Base):
    __tablename__ = "comments"

    id = Column(Integer, primary_key=True, index=True)
    lesson_id = Column(Integer, ForeignKey("lessons.id"))
    name = Column(String, index=True)
    text = Column(Text)
    image = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Bu yerda "Lesson" modelida comments bilan bog'liq relationship bo'lishi kerak
    lesson = relationship("Lesson", back_populates="comments")


class Lesson(Base):
    __tablename__ = "lessons"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(Text)

    # Comment modelidagi "lesson" relationship'iga bog'lanish
    comments = relationship("Comment", back_populates="lesson")
