from flask import Flask, send_from_directory, redirect, make_response, request, jsonify, send_file
from flask_pymongo import PyMongo
from flask_cors import CORS
import gridfs
import os
from bson import ObjectId  # ObjectId dönüşümü için gerekli!
from datetime import datetime
from werkzeug.utils import secure_filename
from io import BytesIO  

app = Flask(__name__, static_folder='../frontend')
CORS(app)

# MongoDB yapılandırması
app.config["MONGO_URI"] = "mongodb://localhost:27017/makale_db"
mongo = PyMongo(app)
db = mongo.db
fs = gridfs.GridFS(db)  # PDF dosyaları için GridFS

# 📌 Yükleme klasörü oluştur (gerekirse)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 📌 CORS Middleware
@app.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = make_response()
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        return response

@app.after_request
def add_cors_headers(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
    return response

# 📌 Kullanıcı Kaydı
@app.route('/api/register', methods=['POST'])
def register_user():
    data = request.json
    if not data.get("name") or not data.get("email"):
        return jsonify({"message": "Eksik bilgi"}), 400
    
    if db.users.find_one({"email": data["email"]}):
        return jsonify({"message": "Bu e-posta zaten kayıtlı"}), 400
    
    user_id = db.users.insert_one({
        "name": data["name"],
        "email": data["email"]
    }).inserted_id

    return jsonify({"message": "Kullanıcı başarıyla kaydedildi", "user_id": str(user_id)}), 201

# 📌 Makale Yükleme
@app.route('/api/submit-article', methods=['POST'])
def upload_article():
    title = request.form.get("title")
    keywords = request.form.get("keywords")
    institution = request.form.get("institution")
    email = request.form.get("email")
    
    if "file" not in request.files:
        return jsonify({"message": "Dosya eksik"}), 400
    
    pdf_file = request.files["file"]
    if not pdf_file.filename.endswith('.pdf'):
        return jsonify({"message": "Sadece PDF yükleyebilirsiniz"}), 400

    user = db.users.find_one({"email": email})
    if not user:
        return jsonify({"message": "Kullanıcı bulunamadı"}), 404

    # PDF dosyasını GridFS'e kaydet
    pdf_id = fs.put(pdf_file, filename=pdf_file.filename)

    # Makale kaydı oluştur
    article_id = db.articles.insert_one({
        "title": title,
        "keywords": keywords.split(',') if keywords else [],
        "institution": institution,
        "author_id": user["_id"],
        "pdf_id": pdf_id,
        "status": "Değerlendiriliyor",
        "upload_date": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }).inserted_id

    return jsonify({"message": "Makale başarıyla yüklendi", "article_id": str(article_id)}), 201

# 📌 Makaleleri Listeleme
@app.route('/api/articles', methods=['GET'])
def get_articles():
    articles = list(db.articles.find({}, {'_id': 1, 'title': 1, 'keywords': 1, 'institution': 1, 'author_id': 1, 'upload_date': 1, 'status': 1}))

    # ObjectId'leri string'e çevir
    for article in articles:
        article["_id"] = str(article["_id"])
        article["author_id"] = str(article["author_id"])
    
    return jsonify(articles)

# 📌 PDF Dosyasını İndirme
@app.route('/api/articles/<article_id>/pdf', methods=['GET'])
def download_pdf(article_id):
    try:
        article = db.articles.find_one({"_id": ObjectId(article_id)})
        if not article:
            return jsonify({"message": "Makale bulunamadı"}), 404

        pdf_data = fs.get(ObjectId(article["pdf_id"]))

        # PDF'yi BytesIO üzerinden gönder
        return send_file(BytesIO(pdf_data.read()), mimetype="application/pdf", as_attachment=True, download_name=pdf_data.filename)
    
    except Exception as e:
        return jsonify({"message": "PDF indirilirken hata oluştu", "error": str(e)}), 500

# 📌 Frontend Dosyalarını Sunma
@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_pages(path):
    try:
        return send_from_directory(app.static_folder, path)
    except FileNotFoundError:
        return jsonify({"message": "Dosya bulunamadı"}), 404

if __name__ == "__main__":
    app.run(debug=True, port=5000)
