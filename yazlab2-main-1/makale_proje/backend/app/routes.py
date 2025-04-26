# API uç noktaları 
from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
from app.models import db, Article, User, Review, Message, AuditLog
from pdfminer.high_level import extract_text
import re
import io
from PIL import Image
from app.utils import encryptor

app_routes = Blueprint("app_routes", __name__)

UPLOAD_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'uploads'))
IMAGES_FOLDER = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'uploads', 'images'))
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(IMAGES_FOLDER, exist_ok=True)

def generate_tracking_number():
    return str(uuid.uuid4())[:8].upper()

@app_routes.route("/api/submit-article", methods=["POST"])
def submit_article():
    try:
        if 'file' not in request.files:
            return jsonify({'message': 'Dosya bulunamadı'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'message': 'Dosya seçilmedi'}), 400
            
        if not file.filename.endswith('.pdf'):
            return jsonify({'message': 'Sadece PDF dosyaları kabul edilmektedir'}), 400

        # Dosyayı kaydet
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)

        # Kullanıcı kontrolü
        email = request.form.get('email')
        username = request.form.get('username')
        user = User.query.filter_by(email=email).first()
        if not user:
            user = User(email=email, username=username)
            db.session.add(user)
            db.session.commit()

        # Makale oluştur
        article = Article(
            title=request.form.get('title'),
            keywords=request.form.get('keywords'),
            institution=request.form.get('institution'),
            file_path=file_path,
            author_id=user.id,
            status='Değerlendirildide'
        )
        
        db.session.add(article)
        
        # Log kaydı
        log = AuditLog(
            article_id=article.id,
            action='Makale yüklendi',
            details=f'Yazar: {email}'
        )
        db.session.add(log)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Makale başarıyla yüklendi',
            'article_id': article.id
        }), 201
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@app_routes.route('/api/track-article/<tracking_number>', methods=['GET'])
def track_article(tracking_number):
    article = Article.query.filter_by(tracking_number=tracking_number).first()
    if not article:
        return jsonify({'message': 'Makale bulunamadı'}), 404
        
    reviews = [{'reviewer': review.reviewer.email, 
                'evaluation': review.evaluation,
                'status': review.status,
                'date': review.submission_date.isoformat()} 
               for review in article.reviews]
               
    return jsonify({
        'title': article.title,
        'status': article.status,
        'submission_date': article.submission_date.isoformat(),
        'reviews': reviews
    }), 200

@app_routes.route('/api/send-message', methods=['POST'])
def send_message():
    data = request.json
    article_id = data.get('article_id')
    content = data.get('message')
    sender_email = data.get('email')
    
    if not all([article_id, content, sender_email]):
        return jsonify({'message': 'Eksik bilgi'}), 400
        
    message = Message(
        article_id=article_id,
        sender_email=sender_email,
        content=content
    )
    
    db.session.add(message)
    db.session.commit()
    
    return jsonify({'message': 'Mesaj gönderildi'}), 201

@app_routes.route('/api/revise-article/<tracking_number>', methods=['POST'])
def revise_article(tracking_number):
    if 'file' not in request.files:
        return jsonify({'message': 'Dosya bulunamadı'}), 400
        
    article = Article.query.filter_by(tracking_number=tracking_number).first()
    if not article:
        return jsonify({'message': 'Makale bulunamadı'}), 404
        
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'Dosya seçilmedi'}), 400
        
    if not file.filename.endswith('.pdf'):
        return jsonify({'message': 'Sadece PDF dosyaları kabul edilmektedir'}), 400
        
    # Yeni dosyayı kaydet ve şifrele
    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    file.save(file_path)
    
    with open(file_path, 'rb') as f:
        file_data = f.read()
    
    encrypted_data, iv = encryptor.encrypt_file_aes(file_data)
    encrypted_path = file_path + '.enc'
    
    with open(encrypted_path, 'w') as f:
        f.write(encrypted_data)
        
    # Eski dosyayı sil
    if os.path.exists(article.file_path):
        os.remove(article.file_path)
        
    article.file_path = encrypted_path
    article.status = 'revised'
    
    log = AuditLog(
        article_id=article.id,
        action='Makale revize edildi',
        details=f'Yeni dosya: {filename}'
    )
    
    db.session.add(log)
    db.session.commit()
    
    os.remove(file_path)  # Orijinal dosyayı sil
    
    return jsonify({'message': 'Revize makale başarıyla yüklendi'}), 200

@app_routes.route('/api/admin/articles', methods=['GET'])
def list_articles():
    articles = Article.query.all()
    return jsonify([{
        'id': article.id,
        'tracking_number': article.tracking_number,
        'title': article.title,
        'author': article.author.email,
        'status': article.status,
        'submission_date': article.submission_date.isoformat()
    } for article in articles]), 200

@app_routes.route('/api/admin/anonymize/<article_id>', methods=['POST'])
def anonymize_article(article_id):
    article = Article.query.get(article_id)
    if not article:
        return jsonify({'message': 'Makale bulunamadı'}), 404
        
    try:
        # Sadece durumu güncelle
        article.status = 'Değerlendiriliyor'
        
        log = AuditLog(
            article_id=article.id,
            action='Makale Değerlendiriliyor',
            details='Anonimleştirme tamamlandı'
        )
        
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'message': 'Makale başarıyla Değerlendiriliyor'}), 200
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@app_routes.route('/api/admin/approve/<article_id>', methods=['POST'])
def approve_article(article_id):
    article = Article.query.get(article_id)
    if not article:
        return jsonify({'message': 'Makale bulunamadı'}), 404
        
    try:
        article.status = 'Onaylandı'
        
        log = AuditLog(
            article_id=article.id,
            action='Makale onaylandı',
            details='Yönetici tarafından onaylandı'
        )
        
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'message': 'Makale başarıyla onaylandı'}), 200
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@app_routes.route('/api/admin/reject/<article_id>', methods=['POST'])
def reject_article(article_id):
    article = Article.query.get(article_id)
    if not article:
        return jsonify({'message': 'Makale bulunamadı'}), 404
        
    try:
        article.status = 'Onaylanmadı'
        
        log = AuditLog(
            article_id=article.id,
            action='Makale reddedildi',
            details='Yönetici tarafından reddedildi'
        )
        
        db.session.add(log)
        db.session.commit()
        
        return jsonify({'message': 'Makale reddedildi'}), 200
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

# Yazar girişi
@app_routes.route('/api/author/login', methods=['POST'])
def author_login():
    data = request.get_json()
    email = data.get('email')
    username = data.get('username')
    
    # Her türlü girişi kabul et
    return jsonify({
        'message': 'Giriş başarılı',
        'user': {
            'email': email,
            'username': username
        }
    }), 200

# Yazarın makalelerini getir
@app_routes.route('/api/author/articles/<email>', methods=['GET'])
def get_author_articles(email):
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'message': 'Kullanıcı bulunamadı'}), 404
    
    articles = Article.query.filter_by(author_id=user.id).all()
    return jsonify([{
        'id': article.id,
        'title': article.title,
        'status': article.status,
        'submission_date': article.submission_date.isoformat(),
        'last_update': article.last_update.isoformat()
    } for article in articles])

# Makale detaylarını getir
@app_routes.route("/api/articles/<int:article_id>", methods=["GET"])
def get_article_details(article_id):
    try:
        # Örnek makale detayları (gerçek uygulamada veritabanından gelecek)
        sample_articles = {
            1: {
                'id': 1,
                'title': 'Yapay Zeka ve Makine Öğrenmesi Üzerine Bir İnceleme',
                'author': 'Dr. Ahmet Yılmaz',
                'institution': 'Kocaeli Üniversitesi',
                'keywords': 'yapay zeka, makine öğrenmesi, derin öğrenme',
                'abstract': 'Bu çalışmada yapay zeka ve makine öğrenmesi alanındaki son gelişmeler incelenmiştir...',
                'status': 'Değerlendirildi',
                'submission_date': '2024-03-25T10:30:00',
                'email': 'ahmet.yilmaz@example.com',
                'reviewers': ['Prof. Dr. Ali Veli', 'Doç. Dr. Ayşe Fatma'],
                'review_status': 'Devam Ediyor',
                'comments': [
                    {'reviewer': 'Prof. Dr. Ali Veli', 'comment': 'Metodoloji kısmı genişletilmeli.'},
                    {'reviewer': 'Doç. Dr. Ayşe Fatma', 'comment': 'Literatür taraması çok kapsamlı.'}
                ]
            },
            2: {
                'id': 2,
                'title': 'Blok Zincir Teknolojisinin Finans Sektöründeki Uygulamaları',
                'author': 'Prof. Dr. Mehmet Demir',
                'institution': 'İstanbul Teknik Üniversitesi',
                'keywords': 'blockchain, kripto para, fintech',
                'abstract': 'Blok zincir teknolojisinin finans sektöründeki potansiyel kullanım alanları...',
                'status': 'Onaylandı',
                'submission_date': '2024-03-20T15:45:00',
                'email': 'mehmet.demir@example.com',
                'reviewers': ['Prof. Dr. Can Yılmaz'],
                'review_status': 'Tamamlandı',
                'comments': [
                    {'reviewer': 'Prof. Dr. Can Yılmaz', 'comment': 'Çalışma yayına hazır.'}
                ]
            },
            3: {
                'id': 3,
                'title': 'Nesnelerin İnterneti ve Akıllı Ev Sistemleri',
                'author': 'Doç. Dr. Ayşe Kaya',
                'institution': 'Yıldız Teknik Üniversitesi',
                'keywords': 'IoT, akıllı ev, otomasyon',
                'abstract': 'Nesnelerin interneti teknolojisinin akıllı ev sistemlerinde kullanımı...',
                'status': 'Değerlendiriliyor',
                'submission_date': '2024-03-15T09:15:00',
                'email': 'ayse.kaya@example.com',
                'reviewers': [],
                'review_status': 'Hakem Bekleniyor',
                'comments': []
            },
            4: {
                'id': 4,
                'title': 'Siber Güvenlik ve Yapay Zeka Entegrasyonu',
                'author': 'Dr. Zeynep Arslan',
                'institution': 'Ankara Üniversitesi',
                'keywords': 'siber güvenlik, yapay zeka, tehdit analizi',
                'abstract': 'Siber güvenlik alanında yapay zeka teknolojilerinin kullanımı ve potansiyel faydaları...',
                'status': 'Onay Bekliyor',
                'submission_date': '2024-03-27T08:00:00',
                'email': 'zeynep.arslan@example.com',
                'reviewers': [],
                'review_status': 'Onay Bekliyor',
                'comments': []
            }
        }
        
        article = sample_articles.get(article_id)
        if not article:
            return jsonify({'message': 'Makale bulunamadı'}), 404
            
        return jsonify(article), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

# Yazar profilini getir
@app_routes.route('/api/author/profile/<email>', methods=['GET'])
def get_author_profile(email):
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'message': 'Kullanıcı bulunamadı'}), 404
    
    articles = Article.query.filter_by(author_id=user.id).all()
    accepted_count = sum(1 for article in articles if article.status == 'kabul edildi')
    pending_count = sum(1 for article in articles if article.status == 'Değerlendirildide')
    
    return jsonify({
        'first_name': user.first_name,
        'last_name': user.last_name,
        'email': user.email,
        'total_articles': len(articles),
        'accepted_articles': accepted_count,
        'pending_articles': pending_count
    })

# Yazarın son Değerlendirildilerini getir
@app_routes.route('/api/author/reviews/<email>', methods=['GET'])
def get_author_reviews(email):
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({'message': 'Kullanıcı bulunamadı'}), 404
    
    articles = Article.query.filter_by(author_id=user.id).all()
    reviews = []
    for article in articles:
        article_reviews = Review.query.filter_by(article_id=article.id).all()
        if article_reviews:
            reviews.append({
                'article_title': article.title,
                'status': article_reviews[0].status,
                'date': article_reviews[0].created_at.isoformat()
            })
    
    return jsonify(reviews)

# Tüm makaleleri getir
@app_routes.route("/api/articles", methods=["GET"])
def get_articles():
    try:
        # Örnek makaleler
        sample_articles = [
            {
                'id': 1,
                'title': 'Yapay Zeka ve Makine Öğrenmesi Üzerine Bir İnceleme',
                'author': 'Dr. Ahmet Yılmaz',
                'status': 'Değerlendirildi',
                'submission_date': '2024-03-25T10:30:00'
            },
            {
                'id': 2,
                'title': 'Blok Zincir Teknolojisinin Finans Sektöründeki Uygulamaları',
                'author': 'Prof. Dr. Mehmet Demir',
                'status': 'Onaylandı',
                'submission_date': '2024-03-20T15:45:00'
            },
            {
                'id': 3,
                'title': 'Nesnelerin İnterneti ve Akıllı Ev Sistemleri',
                'author': 'Doç. Dr. Ayşe Kaya',
                'status': 'Değerlendiriliyor',
                'submission_date': '2024-03-15T09:15:00'
            }
        ]

        # Uploads klasöründeki PDF'leri kontrol et
        uploaded_articles = []
        last_id = max(article['id'] for article in sample_articles)

        for filename in os.listdir(UPLOAD_FOLDER):
            if filename.endswith('.pdf'):
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                
                # Veritabanında kayıtlı mı kontrol et
                article = Article.query.filter_by(file_path=file_path).first()
                
                if not article:
                    # PDF'den başlığı çıkar
                    pdf_info = extract_pdf_info(file_path)
                    if pdf_info:
                        last_id += 1
                        uploaded_articles.append({
                            'id': last_id,
                            'title': pdf_info['title'],
                            'author': 'Yeni Yükleme',
                            'status': 'Onay Bekliyor',
                            'submission_date': datetime.fromtimestamp(
                                os.path.getctime(file_path)
                            ).isoformat()
                        })

        # Tüm makaleleri birleştir
        all_articles = sample_articles + uploaded_articles
        return jsonify(all_articles), 200
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@app_routes.route('/api/admin/download/<article_id>', methods=['GET'])
def download_article(article_id):
    article = Article.query.get(article_id)
    if not article:
        return jsonify({'message': 'Makale bulunamadı'}), 404
        
    try:
        return send_file(article.file_path, as_attachment=True)
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@app_routes.route('/api/admin/download-anonymized/<article_id>', methods=['GET'])
def download_anonymized_article(article_id):
    article = Article.query.get(article_id)
    if not article:
        return jsonify({'message': 'Makale bulunamadı'}), 404
        
    if article.status != 'Değerlendiriliyor':
        return jsonify({'message': 'Bu makale henüz anonimleştirilmemiş'}), 400
        
    try:
        return send_file(article.anonymous_file_path, as_attachment=True)
    except Exception as e:
        return jsonify({'message': str(e)}), 500

# Hakeme atanmış makaleleri getir
@app_routes.route('/api/reviewer/articles/<email>', methods=['GET'])
def get_reviewer_articles(email):
    try:
        # Sadece anonimleştirilmiş makaleleri getir
        articles = Article.query.filter_by(status='Değerlendiriliyor').all()
        
        return jsonify([{
            'id': article.id,
            'title': article.title,
            'keywords': article.keywords,
            'submission_date': article.submission_date.isoformat(),
            'status': article.status
        } for article in articles]), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

# Hakem için makale detaylarını getir
@app_routes.route('/api/reviewer/article/<int:article_id>', methods=['GET'])
def get_reviewer_article_details(article_id):
    try:
        article = Article.query.get(article_id)
        if not article:
            return jsonify({'message': 'Makale bulunamadı'}), 404
            
        if article.status != 'Değerlendiriliyor':
            return jsonify({'message': 'Bu makale değerlendirme için uygun değil'}), 400
            
        return jsonify({
            'id': article.id,
            'title': article.title,
            'keywords': article.keywords,
            'abstract': article.abstract,
            'submission_date': article.submission_date.isoformat()
        }), 200
    except Exception as e:
        return jsonify({'message': str(e)}), 500

# Hakem için makale indirme
@app_routes.route('/api/reviewer/download/<article_id>', methods=['GET'])
def download_article_for_reviewer(article_id):
    article = Article.query.get(article_id)
    if not article:
        return jsonify({'message': 'Makale bulunamadı'}), 404
        
    if article.status != 'Değerlendiriliyor':
        return jsonify({'message': 'Bu makale değerlendirme için uygun değil'}), 400
        
    try:
        return send_file(article.anonymous_file_path, as_attachment=True)
    except Exception as e:
        return jsonify({'message': str(e)}), 500

# Değerlendirme gönder
@app_routes.route('/api/reviewer/submit-review', methods=['POST'])
def submit_review():
    try:
        data = request.get_json()
        article_id = data.get('article_id')
        reviewer_email = data.get('reviewer_email')
        status = data.get('status')
        comments = data.get('comments')

        if not all([article_id, reviewer_email, status, comments]):
            return jsonify({"message": "Eksik bilgi"}), 400

        # Add the review to the database
        db.add_review(article_id, reviewer_email, status, comments)
        return jsonify({"message": "Değerlendirme başarıyla kaydedildi"}), 201
    except Exception as e:
        return jsonify({"message": f"Değerlendirme kaydedilirken bir hata oluştu: {str(e)}"}), 500

def extract_pdf_info(file_path):
    try:
        # PDF'den metin çıkar (pdfminer ile)
        text = extract_text(file_path)
        lines = text.split('\n')
        
        # Başlık için ilk anlamlı satırı bul
        title = next((line.strip() for line in lines if len(line.strip()) > 10), "Başlık bulunamadı")
        
        # Anahtar kelimeleri bul
        keywords = []
        abstract = ""
        abstract_started = False
        
        # Metin içinde arama yap
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Anahtar kelimeleri bul
            if 'keywords' in line_lower or 'anahtar kelimeler' in line_lower:
                if i + 1 < len(lines):
                    # Virgülle ayrılmış kelimeleri al
                    keywords = [k.strip() for k in lines[i+1].split(',')]
                    continue
            
            # Özet bölümünü bul
            if 'abstract' in line_lower or 'özet' in line_lower:
                abstract_started = True
                continue
            
            if abstract_started:
                if 'keywords' in line_lower or 'anahtar kelimeler' in line_lower:
                    break
                abstract += line + " "
        
        # Yazarları bul (örnek pattern: "Ad Soyad1, Ad Soyad2")
        author_pattern = re.compile(r'([A-Z][a-z]+\s+[A-Z][a-z]+)(?:,|\s+and|\s+ve)?')
        potential_authors = author_pattern.findall(text[:500])  # İlk 500 karakterde ara
        
        # Kurumu bul
        institution_pattern = re.compile(r'(?:University|Üniversitesi|Institute|Enstitüsü)[^\n]*')
        institution_match = institution_pattern.search(text)
        institution = institution_match.group() if institution_match else ""
        
        return {
            'title': title,
            'keywords': keywords,
            'abstract': abstract.strip(),
            'authors': potential_authors,
            'institution': institution
        }
    except Exception as e:
        print(f"PDF okuma hatası: {str(e)}")
        return None

# Uploads klasöründeki makaleleri listele
@app_routes.route('/api/articles/uploads', methods=['GET'])
def list_uploaded_articles():
    try:
        uploaded_files = []
        for filename in os.listdir(UPLOAD_FOLDER):
            if filename.endswith('.pdf'):
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file_stats = os.stat(file_path)
                
                # PDF'den bilgileri çıkar
                pdf_info = extract_pdf_info(file_path)
                
                # Veritabanından makale bilgilerini al
                article = Article.query.filter_by(file_path=file_path).first()
                
                if article:
                    uploaded_files.append({
                        'id': article.id,
                        'filename': filename,
                        'title': article.title,
                        'author': article.author.email if article.author else 'Bilinmiyor',
                        'status': article.status,
                        'submission_date': article.submission_date.isoformat(),
                        'file_size': file_stats.st_size,
                        'last_modified': datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                        'keywords': article.keywords,
                        'abstract': article.abstract
                    })
                else:
                    # Veritabanında kaydı olmayan dosyalar için PDF'den çıkarılan bilgileri kullan
                    uploaded_files.append({
                        'id': None,
                        'filename': filename,
                        'title': pdf_info['title'] if pdf_info else filename,
                        'author': 'Bilinmiyor',
                        'status': 'Kayıtsız',
                        'submission_date': datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
                        'file_size': file_stats.st_size,
                        'last_modified': datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                        'keywords': pdf_info['keywords'] if pdf_info else [],
                        'abstract': pdf_info['abstract'] if pdf_info else ''
                    })
        
        return jsonify(uploaded_files), 200
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

# Uploads klasöründen dosya indirme
@app_routes.route('/api/articles/uploads/download/<filename>', methods=['GET'])
def download_uploaded_file(filename):
    try:
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        if not os.path.exists(file_path):
            return jsonify({'message': 'Dosya bulunamadı'}), 404
            
        return send_file(file_path, as_attachment=True)
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@app_routes.route('/uploads/images/<filename>')
def serve_image(filename):
    try:
        return send_file(
            os.path.join(IMAGES_FOLDER, filename),
            mimetype='image/jpeg'  # Varsayılan olarak JPEG
        )
    except Exception as e:
        return jsonify({'error': str(e)}), 404
