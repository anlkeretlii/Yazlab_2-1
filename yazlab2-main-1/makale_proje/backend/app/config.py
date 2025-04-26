import os
from datetime import timedelta

# MongoDB Konfigürasyonu
MONGO_URI = "mongodb://localhost:27017/makale_db"

# Güvenlik ayarları
SECRET_KEY = 'gizli-anahtar-buraya'

# Dosya yükleme ayarları
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max dosya boyutu

ALLOWED_EXTENSIONS = {'pdf'}


# Mail sunucusu ayarları
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
# MAIL_USERNAME = 'your-email@gmail.com'  # Değiştirilmeli
# MAIL_PASSWORD = 'your-email-password'  # Değiştirilmeli
