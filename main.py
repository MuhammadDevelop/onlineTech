from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional, List, Dict
import smtplib
import random
from email.mime.text import MIMEText
import hashlib
import shutil
import os

app = FastAPI()

# Statik fayllar uchun papkalarni tayyorlash
if not os.path.exists("avatars"):
    os.makedirs("avatars")
if not os.path.exists("videos"):
    os.makedirs("videos")

# Statik fayllarni ulash
app.mount("/avatars", StaticFiles(directory="avatars"), name="avatars")
app.mount("/videos", StaticFiles(directory="videos"), name="videos")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Email sozlamalar
SENDER_EMAIL = "muham20021202@gmail.com"
APP_PASSWORD = "kxnx qmzg qtbc guhm"
ADMIN_EMAIL = "muham20021202@gmail.com"

# Modellar
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

# Ma'lumotlar ombori
lessons = [
    Lesson(id=1, category="Word darslari", title="Word kirish", description="Word dasturiga kirish va Glavnaya bo'limi",
           subtitle="Word Nima uchun kerak?",
           answer="Microsoft Word matn yaratish, tahrirlash va formatlash uchun kerak",
           video_url="https://onlinetech.onrender.com/videos/word-1.mp4"),
    Lesson(id=2, category="Word darslari", title="Vstavka bo'limi bilan tanishish", description="Vstavka bo'limi haqida.",
           subtitle="Vstavka bo'limi bizga nima uchun kerak?",
           answer="Hujjatni boyitish, rasm, jadval va boshqa elementlarni qo‘shish uchun kerak.",
           video_url="https://onlinetech.onrender.com/videos/word-2.mp4"),
    Lesson(id=3, category="Word darslari", title="Dizayn va Maket bo'limlari", description="Dizayn va Maket bo'limlari haqida",
           subtitle="Dizayn va Maket bo'limida nimalar o'rganamiz?",
           answer="Dizayn bo‘limida interfeys, shrift, tugmalar, sahifa ko‘rinishi, Maket bo‘limida esa joylashuv va o‘lchamlar sozlanadi",
           video_url="https://onlinetech.onrender.com/videos/word-3.mp4"),
    Lesson(id=4, category="Excel darslari", title="Excelga kirish", description="Excel dasturiga kirish.",
           subtitle="Excel Nima uchun kerak?",
           answer="Excel maʼlumotlarni tartiblash, hisoblash va tahlil qilish uchun kerak.",
           video_url="https://onlinetech.onrender.com/videos/excal-1.mp4"),
]

TEMP_USERS: Dict[str, dict] = {}
USERS = []
comments: Dict[int, List[Comment]] = {}

# Darslar
@app.get("/lessons", response_model=List[Lesson])
def get_lessons():
    return lessons

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
    verify_code = str(random.randint(100000, 999999))
    TEMP_USERS[user.email] = {
        "password": user.password,
        "code": verify_code,
        "name": user.name
    }
    msg = MIMEText(f"Sizning tasdiqlash kodingiz: {verify_code}")
    msg["Subject"] = "Tasdiqlash kodi"
    msg["From"] = SENDER_EMAIL
    msg["To"] = user.email
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.send_message(msg)
    return {"message": "Kod yuborildi"}

# Email orqali tasdiqlash
@app.post("/verify")
def verify_code(data: VerifyInput):
    for email, user_data in TEMP_USERS.items():
        if user_data["code"] == data.code:
            email_hash = hashlib.md5(email.strip().lower().encode()).hexdigest()
            image_url = f"https://www.gravatar.com/avatar/{email_hash}?d=identicon"
            USERS.append({
                "email": email,
                "password": user_data["password"],
                "image": image_url,
                "name": user_data.get("name")
            })
            del TEMP_USERS[email]
            return {"message": "Tasdiqlandi va ro'yxatdan o'tdingiz", "image": image_url}
    raise HTTPException(status_code=400, detail="Kod noto‘g‘ri")

# Avatar yuklash
# Avatar yuklash
@app.post("/upload-avatar")
async def upload_avatar(email: str = Form(...), image: UploadFile = File(...)):
    filename = f"avatars/{email.replace('@', '_')}.png"
    with open(filename, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    file_url = f"https://backendthree-sc1q.onrender.com/avatars/{email.replace('@', '_')}.png"
    return {"message": "Rasm saqlandi", "image": file_url}

# Komment qo'shish
@app.post("/lessons/{lesson_id}/comments")
def add_comment(lesson_id: int, comment: Comment):
    lesson_ids = [lesson.id for lesson in lessons]
    if lesson_id not in lesson_ids:
        raise HTTPException(status_code=404, detail="Bunday IDdagi dars topilmadi")
    if lesson_id not in comments:
        comments[lesson_id] = []
    comments[lesson_id].append(comment)
    comment_name = comment.name if comment.name else "Ism ko'rsatilmagan"
    admin_body = f"""🔔 Yangi izoh keldi!

🆔 Dars ID: {lesson_id}
👤 Ism: {comment_name}
📧 Email: {comment.email}

💬 Xabar:
{comment.message}

➡️ Ushbu emailga "Reply" qilsangiz, foydalanuvchiga javob yuboriladi.
"""
    user_body = f"""Salom {comment_name},

Izohingiz uchun rahmat! Tez orada sizga javob beramiz.

Hurmat bilan,  
Bilim ol jamoasi
"""
    admin_msg = MIMEText(admin_body)
    admin_msg["Subject"] = f"Dars {lesson_id} uchun yangi izoh"
    admin_msg["From"] = SENDER_EMAIL
    admin_msg["To"] = ADMIN_EMAIL
    admin_msg["Reply-To"] = comment.email
    user_msg = MIMEText(user_body)
    user_msg["Subject"] = "Izohingiz qabul qilindi"
    user_msg["From"] = SENDER_EMAIL
    user_msg["To"] = comment.email
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.send_message(admin_msg)
        server.send_message(user_msg)
    return {"message": "Izoh saqlandi va email yuborildi"}

# Ro'yxatdan o'tgan foydalanuvchilarni olish
@app.get("/users", response_model=List[UserOutput])
def get_users():
    return USERS
