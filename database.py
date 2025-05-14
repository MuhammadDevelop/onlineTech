# database.py

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLite bazasi uchun URL
DATABASE_URL = "sqlite:///./comments.db"

# Ma'lumotlar bazasiga ulanish uchun engine
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# SessionLocal: ma'lumotlar bazasiga aloqalar uchun session yaratish
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base: barcha model uchun asos
Base = declarative_base()

# Baza yaratish (agar bazaning jadvali mavjud bo'lmasa)
Base.metadata.create_all(bind=engine)
