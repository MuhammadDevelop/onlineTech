from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Optional
from typing import List, Dict
import smtplib
import random
from email.mime.text import MIMEText
import hashlib
from fastapi import UploadFile, File, Form
import shutil
import os
app = FastAPI()

class UserOutput(BaseModel):
    email: str
    image: str
    name: Optional[str] = None



# Statik fayllar uchun mount
app.mount("/videos", StaticFiles(directory="videos"), name="videos")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
    name:str
    email: str      
    password: str

class VerifyInput(BaseModel):
    code: str


class Comment(BaseModel):
    name: Optional[str] = None
    email: str
    message: str

# Ma'lumotlar
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
           answer="Dizayn bo‘limida foydalanuvchi interfeysi, ranglar, shriftlar, tugmalar va sahifa ko‘rinishi yaratiladi.Maket bo‘limida esa bu dizaynlar tartiblanadi, elementlar joylashuvi va o‘lchamlari aniqlanadi (ya’ni, dizayn qanday ko‘rinishda bo‘lishi kerakligi chiziladi",
           video_url="https://onlinetech.onrender.com/videos/word-3.mp4"),

    Lesson(id=4, category="Excel darslari", title="Excelga kirish", description="Excel dasturiga kirish.",
           subtitle="Excel Nima uchun kerak?",
           answer="Excel maʼlumotlarni tartiblash, hisoblash va tahlil qilish uchun kerak.",
           video_url="https://onlinetech.onrender.com/videos/excal-1.mp4"),
]

# Foydalanuvchi ro‘yxatlari
TEMP_USERS: Dict[str, dict] = {}
USERS = []
comments: Dict[int, List[Comment]] = {}

# Email sozlamalar
SENDER_EMAIL = "muham20021202@gmail.com"
APP_PASSWORD = "kxnx qmzg qtbc guhm"
ADMIN_EMAIL = "muham20021202@gmail.com"

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
        "code": verify_code
    }

    # Email yuborish
    msg = MIMEText(f"Sizning tasdiqlash kodingiz: {verify_code}")
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
    # Kod orqali emailni topamiz
    for email, user_data in TEMP_USERS.items():
        if user_data["code"] == data.code:
            hashed_password = user_data["password"]

            # Gravatar rasmi
            email_hash = hashlib.md5(email.strip().lower().encode()).hexdigest()
            image_url = f"https://www.gravatar.com/avatar/{email_hash}?d=identicon"

            USERS.append({
                "email": email,
                "password": hashed_password,
                "image": image_url
            })
            del TEMP_USERS[email]

            return {
                "message": "Tasdiqlandi va ro'yxatdan o'tdingiz",
                "image": image_url
            }

    raise HTTPException(status_code=400, detail="Kod noto‘g‘ri")


if not os.path.exists("avatars"):
    os.makedirs("avatars")

app.mount("/avatars", StaticFiles(directory="avatars"), name="avatars")

@app.post("/upload-avatar")
async def upload_avatar(email: str = Form(...), image: UploadFile = File(...)):
    filename = f"avatars/{email.replace('@', '_')}.png"
    with open(filename, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    # Frontend uchun rasm URL qaytariladi
    file_url = f"https://backendthree-sc1q.onrender.com/{filename}"
    return {"message": "Rasm saqlandi", "image": file_url}
@app.post("/lessons/{lesson_id}/comments")
def add_comment(lesson_id: int, comment: Comment):
    lesson_ids = [lesson.id for lesson in lessons]
    if lesson_id not in lesson_ids:
        raise HTTPException(status_code=404, detail="Bunday IDdagi dars topilmadi")

    if lesson_id not in comments:
        comments[lesson_id] = []
    comments[lesson_id].append(comment)

    # Agar name mavjud bo'lsa, aks holda None
    comment_name = comment.name if comment.name else "Ism ko'rsatilmagan"

    # Admin email
    admin_body = f"""
🔔 Yangi izoh keldi!

🆔 Dars ID: {lesson_id}
👤 Ism: {comment_name}
📧 Email: {comment.email}

💬 Xabar:
{comment.message}

➡️ Ushbu emailga "Reply" qilsangiz, foydalanuvchiga javob yuboriladi.
    """
    admin_msg = MIMEText(admin_body)
    admin_msg["Subject"] = f"Dars {lesson_id} uchun yangi izoh"
    admin_msg["From"] = SENDER_EMAIL
    admin_msg["To"] = ADMIN_EMAIL
    admin_msg["Reply-To"] = comment.email

    # Foydalanuvchiga avtomatik javob
    user_body = f"""
Salom {comment_name},

Izohingiz uchun rahmat! Tez orada sizga javob beramiz.

Hurmat bilan,  
Bilim ol jamoasi
    """
    user_msg = MIMEText(user_body)
    user_msg["Subject"] = "Izohingiz qabul qilindi"
    user_msg["From"] = SENDER_EMAIL
    user_msg["To"] = comment.email

    # Email yuborish
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, APP_PASSWORD)
        server.send_message(admin_msg)
        server.send_message(user_msg)

    return {"message": "Izoh saqlandi va email yuborildi"}
@app.get("/users", response_model=List[UserOutput])
def get_users():
    return USERS