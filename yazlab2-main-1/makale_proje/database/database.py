from pymongo import MongoClient
import gridfs

# MongoDB bağlantısını başlat
client = MongoClient("mongodb://localhost:27017/")
db = client["makale_db"]
fs = gridfs.GridFS(db)  # GridFS için nesne oluştur

# PDF dosyasını yükleme fonksiyonu
def upload_pdf(file):
    if not file.filename.endswith('.pdf'):
        return {"error": "Sadece PDF yükleyebilirsiniz"}, 400

    file_id = fs.put(file, filename=file.filename)
    return {"message": "Dosya başarıyla yüklendi", "file_id": str(file_id)}, 201
