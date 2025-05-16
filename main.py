from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict
from email.mime.text import MIMEText
from translations import translations 
import smtplib
import random
import hashlib
import shutil
import os

app = FastAPI()

# Statik fayllar
app.mount("/videos", StaticFiles(directory="videos"), name="videos")
app.mount("/avatars", StaticFiles(directory="avatars"), name="avatars")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Model
class Lesson(BaseModel):
    id: int
    category: str
    title: str
    description: str
    subtitle: str
    answer: str
    video_url: str

class RegisterInput(BaseModel):
    name: str
    email: str
    password: str

class VerifyInput(BaseModel):
    code: str

class Comment(BaseModel):
    name: Optional[str] = None
    email: str
    message: str

class UserOutput(BaseModel):
    email: str
    image: str
    name: Optional[str] = None

# Darslar
lessons = [
    Lesson(
        id=1,
        category="Word darslari",
        title="Word kirish",
        description="Word dasturiga kirish va Glavnaya bo'limi",
        subtitle="Word Nima uchun kerak?",
        answer="Microsoft Word matn yaratish, tahrirlash va formatlash uchun kerak",
        video_url="https://onlinetech.onrender.com/videos/word-1.mp4"
    ),
    Lesson(
        id=2,
        category="Word darslari",
        title="Vstavka bo'limi bilan tanishish",
        description="Vstavka bo'limi haqida.",
        subtitle="Vstavka bo'limi bizga nima uchun kerak?",
        answer="Hujjatni boyitish, rasm, jadval va boshqa elementlarni qo‘shish uchun kerak.",
        video_url="https://onlinetech.onrender.com/videos/word-2.mp4"
    ),
    Lesson(
        id=3,
        category="Word darslari",
        title="Dizayn va Maket bo'limlari",
        description="Dizayn va Maket bo'limlari haqida",
        subtitle="Dizayn va Maket bo'limida nimalar o'rganamiz?",
        answer="Dizayn bo‘limida foydalanuvchi interfeysi, ranglar, shriftlar, tugmalar va sahifa ko‘rinishi yaratiladi. Maket bo‘limida esa bu dizaynlar tartiblanadi, elementlar joylashuvi va o‘lchamlari aniqlanadi.",
        video_url="https://onlinetech.onrender.com/videos/word-3.mp4"
    ),
    Lesson(
        id=4,
        category="Excel darslari",
        title="Excelga kirish",
        description="Excel dasturiga kirish.",
        subtitle="Excel Nima uchun kerak?",
        answer="Excel maʼlumotlarni tartiblash, hisoblash va tahlil qilish uchun kerak.",
        video_url="https://onlinetech.onrender.com/videos/excal-1.mp4"
    ),
]

# Saqlash joylari
TEMP_USERS: Dict[str, dict] = {}
USERS: List[dict] = []
comments: Dict[int, List[Comment]] = {}

# Email sozlamalar
SENDER_EMAIL = "muham20021202@gmail.com"
APP_PASSWORD = "kxnx qmzg qtbc guhm"
ADMIN_EMAIL = "muham20021202@gmail.com"

# Darslar API
@app.get("/lessons", response_model=List[Lesson])
def get_lessons(lang: str = "uz"):
    localized = []
    for lesson in lessons:
        title = {
            "uz": lesson.title,
            "en": "Introduction to Word" if lesson.id == 1 else lesson.title,
            "ru": "Введение в Word" if lesson.id == 1 else lesson.title
        }.get(lang, lesson.title)

        description = {
            "uz": lesson.description,
            "en": "Intro to Word and Home tab" if lesson.id == 1 else lesson.description,
            "ru": "Введение в Word и раздел Главная" if lesson.id == 1 else lesson.description
        }.get(lang, lesson.description)

        localized.append(Lesson(
            id=lesson.id,
            category=lesson.category,
            title=title,
            description=description,
            subtitle=lesson.subtitle,
            answer=lesson.answer,
            video_url=lesson.video_url
        ))
    return localized

@app.get("/lessons/{lesson_id}", response_model=Lesson)
def get_lesson_by_id(lesson_id: int):
    for lesson in lessons:
        if lesson.id == lesson_id:
            return lesson
    raise HTTPException(status_code=404, detail="Bunday IDdagi dars topilmadi")

# Ro'yxatdan o'tish
@app.post("/register")
def register(user: RegisterInput):
    if user.email in TEMP_USERS:
        raise HTTPException(status_code=400, detail="Bu email allaqachon ro'yxatdan o'tgan.")

    code = str(random.randint(100000, 999999))
    TEMP_USERS[user.email] = {"password": user.password, "code": code}

    msg = MIMEText(f"Sizning tasdiqlash kodingiz: {code}")
    msg["Subject"] = "Tasdiqlash kodi"
    msg["From"] = SENDER_EMAIL
    msg["To"] = user.email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.send_message(msg)

    return {"message": "Kod yuborildi"}

# Tasdiqlash
@app.post("/verify")
def verify_code(data: VerifyInput):
    for email, user in TEMP_USERS.items():
        if user["code"] == data.code:
            hash_pass = user["password"]
            email_hash = hashlib.md5(email.strip().lower().encode()).hexdigest()
            image_url = f"https://www.gravatar.com/avatar/{email_hash}?d=identicon"
            USERS.append({"email": email, "password": hash_pass, "image": image_url})
            del TEMP_USERS[email]
            return {"message": "Tasdiqlandi va ro'yxatdan o'tdingiz", "image": image_url}

    raise HTTPException(status_code=400, detail="Kod noto‘g‘ri")

# Avatar yuklash
@app.post("/upload-avatar")
async def upload_avatar(email: str = Form(...), image: UploadFile = File(...)):
    os.makedirs("avatars", exist_ok=True)
    filename = f"avatars/{email.replace('@', '_')}.png"
    with open(filename, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)
    file_url = f"https://backendthree-sc1q.onrender.com/{filename}"
    return {"message": "Rasm saqlandi", "image": file_url}

# Izoh qo‘shish
@app.post("/lessons/{lesson_id}/comments")
def add_comment(lesson_id: int, comment: Comment):
    if lesson_id not in [l.id for l in lessons]:
        raise HTTPException(status_code=404, detail="Bunday IDdagi dars topilmadi")

    comments.setdefault(lesson_id, []).append(comment)
    name = comment.name if comment.name else "Ism ko'rsatilmagan"

    admin_msg = MIMEText(f"""
🔔 Yangi izoh keldi!

🆔 Dars ID: {lesson_id}
👤 Ism: {name}
📧 Email: {comment.email}

💬 Xabar:
{comment.message}

➡️ Ushbu emailga "Reply" qilsangiz, foydalanuvchiga javob yuboriladi.
    """)
    admin_msg["Subject"] = f"Dars {lesson_id} uchun yangi izoh"
    admin_msg["From"] = SENDER_EMAIL
    admin_msg["To"] = ADMIN_EMAIL
    admin_msg["Reply-To"] = comment.email

    user_msg = MIMEText(f"Salom {name},\n\nIzohingiz uchun rahmat! Tez orada sizga javob beramiz.\n\nHurmat bilan,\nBilim ol jamoasi")
    user_msg["Subject"] = "Izohingiz qabul qilindi"
    user_msg["From"] = SENDER_EMAIL
    user_msg["To"] = comment.email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.send_message(admin_msg)
        server.send_message(user_msg)

    return {"message": "Izoh saqlandi va email yuborildi"}

# Ro‘yxatdan o‘tgan foydalanuvchilar
@app.get("/users", response_model=List[UserOutput])
def get_users():
    return USERS


@app.get("/lessons/{lesson_id}", response_model=Lesson)
def get_lesson_by_id(lesson_id: int, lang: str = "uz"):
    for lesson in lessons:
        if lesson.id == lesson_id:
            lesson_trans = translations["lessons"].get(lesson.id, {})
            title = lesson_trans.get("title", {}).get(lang, lesson.title)
            description = lesson_trans.get("description", {}).get(lang, lesson.description)
            subtitle = lesson_trans.get("subtitle", {}).get(lang, lesson.subtitle)
            answer = lesson_trans.get("answer", {}).get(lang, lesson.answer)

            return Lesson(
                id=lesson.id,
                category=lesson.category,
                title=title,
                description=description,
                subtitle=subtitle,
                answer=answer,
                video_url=lesson.video_url
            )
    raise HTTPException(status_code=404, detail="Bunday IDdagi dars topilmadi")

# Tilga qarab intro title olish
@app.get("/intro-title")
def get_intro_title(lang: str = "uz"):
    title = translations.get("intro_title", {}).get(lang, translations.get("intro_title", {}).get("uz", ""))
    return {"title": title}
