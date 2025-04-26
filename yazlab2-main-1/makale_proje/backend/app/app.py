from flask import Flask, send_from_directory, redirect, make_response, request, jsonify, send_file
from flask_cors import CORS
import os
from datetime import datetime
from werkzeug.utils import secure_filename
from io import BytesIO
from pdf_isleme import PDFProcessor
from database import Database
import sqlite3

app = Flask(__name__, static_folder='../frontend')

# CORS ayarlarını güncelle
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:8080", "http://127.0.0.1:8080", "http://127.0.0.1:5000"],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "Accept"],
        "supports_credentials": True
    }
})

# Veritabanı bağlantısı
db = Database()

# Klasör yapılandırmaları
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'uploads')
OUTPUT_FOLDER = os.path.join(BASE_DIR, 'outputs')
PDF_STORAGE = os.path.join(BASE_DIR, 'pdf_storage')

# İzin verilen dosya uzantıları
ALLOWED_EXTENSIONS = {'pdf'}

# Klasörleri oluştur
for folder in [UPLOAD_FOLDER, OUTPUT_FOLDER, PDF_STORAGE]:
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"Klasör oluşturuldu: {folder}")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/api/submit-article', methods=['POST'])
def upload_article():
    try:
        print("[INFO] Makale yükleme isteği alındı")
        print("[INFO] Form verileri:", request.form)
        print("[INFO] Dosya verileri:", request.files)

        # Form verilerini kontrol et
        if not all(field in request.form for field in ['title', 'keywords', 'institution']):
            return jsonify({"message": "Eksik form alanları"}), 400

        title = request.form.get("title")
        keywords = request.form.get("keywords")
        institution = request.form.get("institution")
        
        # Dosya kontrolü
        if "file" not in request.files:
            return jsonify({"message": "Dosya yüklenmedi"}), 400
        
        pdf_file = request.files["file"]
        if pdf_file.filename == '':
            return jsonify({"message": "Dosya seçilmedi"}), 400
            
        if not allowed_file(pdf_file.filename):
            return jsonify({"message": "Sadece PDF dosyaları kabul edilmektedir"}), 400

        # Dosya yollarını tanımla
        original_filename = secure_filename(pdf_file.filename)
        original_path = os.path.join(UPLOAD_FOLDER, original_filename)
        processed_filename = f"processed_{original_filename}"
        anonymized_filename = f"anonymized_{original_filename}"
        processed_path = os.path.join(OUTPUT_FOLDER, processed_filename)
        anonymized_path = os.path.join(PDF_STORAGE, anonymized_filename)

        try:
            # Orijinal PDF'i kaydet
            pdf_file.save(original_path)
            print(f"[INFO] Orijinal PDF kaydedildi: {original_path}")

            # PDF'i işle
            processor = PDFProcessor(original_path, processed_path)
            processor.blur_images()
            processor.save()
            print(f"[INFO] İşlenmiş PDF kaydedildi: {processed_path}")

            # PDF'i anonimleştir
            processor = PDFProcessor(processed_path, anonymized_path)
            processor.anonymize_pdf()
            processor.save()
            print(f"[INFO] Anonimleştirilmiş PDF kaydedildi: {anonymized_path}")

            # Database column debug info
            with sqlite3.connect(db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("PRAGMA table_info(articles)")
                columns = [column[1] for column in cursor.fetchall()]
                print(f"[DEBUG] Available columns in articles table before insert: {columns}")

            # Makaleyi veritabanına kaydet ve takip kodu al
            tracking_code = db.add_article(
                title=title,
                keywords=keywords,
                institution=institution,
                original_filename=original_filename,
                anonymized_filename=anonymized_filename,
                file_path=anonymized_path
            )

            # Başarılı işlem sonrası geçici dosyaları temizle
            if os.path.exists(original_path):
                os.remove(original_path)
            if os.path.exists(processed_path):
                os.remove(processed_path)

            return jsonify({
                "message": "Makale başarıyla yüklendi ve işlendi",
                "tracking_code": tracking_code
            }), 201

        except Exception as e:
            print(f"[ERROR] PDF işleme hatası: {str(e)}")
            # Hata durumunda tüm geçici dosyaları temizle
            for path in [original_path, processed_path]:
                if os.path.exists(path):
                    os.remove(path)
            raise

    except Exception as e:
        print(f"[ERROR] Genel hata: {str(e)}")
        return jsonify({"message": f"Makale yüklenirken bir hata oluştu: {str(e)}"}), 500

@app.route('/api/articles', methods=['GET'])
def get_articles():
    try:
        articles = db.get_all_articles()
        
        # Ensure all dates are properly formatted
        for article in articles:
            if 'upload_date' in article and article['upload_date']:
                # Ensure date is a string in ISO format
                try:
                    if isinstance(article['upload_date'], str):
                        # Try to parse and reformat to ensure it's valid
                        date_obj = datetime.strptime(article['upload_date'], '%Y-%m-%d %H:%M:%S')
                        article['upload_date'] = date_obj.isoformat()
                except Exception as e:
                    print(f"Date conversion error: {e}")
                    # Provide a fallback date if parsing fails
                    article['upload_date'] = datetime.now().isoformat()
            
            # Fix status consistency
            if article.get('status') == 'Kabul Edildi':
                article['status'] = 'Onaylandı'
            elif article.get('status') == 'Reddedildi':
                article['status'] = 'Onaylanmadı'
                
        return jsonify(articles)
    except Exception as e:
        print(f"[ERROR] Error fetching articles: {str(e)}")
        return jsonify({"error": f"Makaleler alınırken hata oluştu: {str(e)}"}), 500

@app.route('/api/articles/<tracking_code>/pdf', methods=['GET'])
def download_pdf(tracking_code):
    try:
        article = db.get_article_by_tracking_code(tracking_code)
        if not article:
            return jsonify({"message": "Makale bulunamadı"}), 404
        
        return send_file(
            article['file_path'],
            mimetype='application/pdf',
            as_attachment=True,
            download_name=article['anonymized_filename']
        )
    except Exception as e:
        return jsonify({"error": "PDF indirilirken hata oluştu"}), 500

@app.route('/api/admin/view/<int:article_id>', methods=['GET'])
def view_article(article_id):
    try:
        article = db.get_article_by_id(article_id)
        if not article:
            return jsonify({"message": "Makale bulunamadı"}), 404
            
        file_path = article.get('file_path')
        if not file_path or not os.path.exists(file_path):
            return jsonify({"message": "Dosya bulunamadı"}), 404

        return send_file(
            file_path,
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({"message": f"Dosya görüntülenirken hata oluştu: {str(e)}"}), 500

@app.route('/api/reviewer/view-pdf/<int:article_id>', methods=['GET'])
def view_article_for_reviewer(article_id):
    try:
        article = db.get_article_by_id(article_id)
        if not article:
            return jsonify({"message": "Makale bulunamadı"}), 404
            
        file_path = article.get('file_path')
        if not file_path or not os.path.exists(file_path):
            return jsonify({"message": "Dosya bulunamadı"}), 404

        return send_file(
            file_path,
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({"message": f"Dosya görüntülenirken hata oluştu: {str(e)}"}), 500
    
@app.route('/api/view-pdf/<tracking_code>', methods=['GET'])
def view_pdf(tracking_code):
    try:
        article = db.get_article_by_tracking_code(tracking_code)
        if not article:
            return jsonify({"message": "Makale bulunamadı"}), 404
        
        return send_file(
            article['file_path'],
            mimetype='application/pdf',
            as_attachment=False
        )
    except Exception as e:
        return jsonify({"error": "PDF görüntülenirken hata oluştu"}), 500

@app.route('/api/track/<tracking_code>', methods=['GET'])
def track_article(tracking_code):
    """Makale takip"""
    try:
        # Makale bilgilerini al
        article = db.get_article_by_tracking_code(tracking_code)
        if not article:
            return jsonify({"message": "Makale bulunamadı"}), 404
            
        # Değerlendirmeleri al
        reviews = db.get_article_reviews(tracking_code)
        
        # Yanıtı hazırla
        response = {
            "title": article['title'],
            "status": article['status'],
            "upload_date": article['upload_date'],
            "tracking_code": article['tracking_code'],
            "reviews": reviews
        }
        
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/reviewer/login', methods=['POST'])
def reviewer_login():
    try:
        data = request.get_json()
        email = data.get('email')
        
        if not email:
            return jsonify({"message": "Email gerekli"}), 400
            
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM reviewers WHERE email = ?', (email,))
            reviewer = cursor.fetchone()
            
            if reviewer:
                return jsonify({
                    "message": "Giriş başarılı",
                    "reviewer": {
                        "email": reviewer[1],
                        "name": reviewer[0]
                    }
                }), 200
            else:
                return jsonify({"message": "Hakem bulunamadı"}), 404
                
    except Exception as e:
        return jsonify({"message": f"Giriş yapılırken hata oluştu: {str(e)}"}), 500

@app.route('/api/reviewer/articles/<email>', methods=['GET'])
def get_reviewer_articles(email):
    try:
        articles = db.get_articles_by_reviewer(email)
        return jsonify(articles), 200
    except Exception as e:
        return jsonify({"message": f"Makaleler alınırken bir hata oluştu: {str(e)}"}), 500

@app.route('/api/reviewer/review', methods=['POST'])
def submit_review_legacy():
    try:
        data = request.get_json()
        article_id = data.get('article_id')
        reviewer_email = data.get('reviewer_email')
        decision = data.get('decision')
        comments = data.get('comments')

        if not all([article_id, reviewer_email, decision, comments]):
            return jsonify({"message": "Eksik bilgi"}), 400

        db.add_review(article_id, reviewer_email, decision, comments)
        return jsonify({"message": "Değerlendirme başarıyla kaydedildi"}), 200
    except Exception as e:
        return jsonify({"message": f"Değerlendirme kaydedilirken bir hata oluştu: {str(e)}"}), 500

@app.route('/api/reviewer/submit-review', methods=['POST'])
def submit_review():
    try:
        data = request.get_json()
        
        # Debug incoming data
        print(f"[DEBUG] Received review data: {data}")
        
        article_id = data.get('article_id')
        reviewer_email = data.get('reviewer_email')
        status = data.get('status')
        comments = data.get('comments')
        
        print(f"[DEBUG] Processed fields: article_id={article_id}, reviewer_email={reviewer_email}, status={status}, comments_length={len(comments) if comments else 0}")

        # Validate required fields
        if not article_id:
            return jsonify({"message": "Eksik bilgi - article_id required"}), 400
        if not reviewer_email:
            return jsonify({"message": "Eksik bilgi - reviewer_email required"}), 400
        if not status:
            return jsonify({"message": "Eksik bilgi - status required"}), 400
        if not comments:
            return jsonify({"message": "Eksik bilgi - comments required"}), 400

        # Convert status to decision
        decision_map = {
            'Kabul': 'accept',
            'Red': 'reject',
            'Revizyon': 'revise'
        }
        decision = decision_map.get(status, status.lower())

        # Make sure article_id is an integer
        try:
            article_id = int(article_id)
        except ValueError:
            print(f"[ERROR] Invalid article_id: {article_id}")
            return jsonify({"message": "Geçersiz makale ID"}), 400

        # Verify article exists
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM articles WHERE id = ?", (article_id,))
            if not cursor.fetchone():
                print(f"[ERROR] Article not found: {article_id}")
                return jsonify({"message": "Makale bulunamadı"}), 404

        # Add the review to the database
        success = db.add_review(article_id, reviewer_email, decision, comments)
        
        if success:
            print(f"[INFO] Review successfully submitted for article_id={article_id}")
            return jsonify({"message": "Değerlendirme başarıyla kaydedildi"}), 201
        else:
            print(f"[ERROR] Failed to submit review for article_id={article_id}")
            return jsonify({"message": "Değerlendirme kaydedilemedi"}), 500
    except Exception as e:
        print(f"[ERROR] Exception during review submission: {str(e)}")
        return jsonify({"message": f"Değerlendirme kaydedilirken bir hata oluştu: {str(e)}"}), 500

@app.route('/api/admin/unassigned-articles', methods=['GET'])
def get_unassigned_articles():
    """Henüz hakeme atanmamış makaleleri listeler"""
    try:
        articles = db.get_unassigned_articles()
        return jsonify(articles)
    except Exception as e:
        return jsonify({"message": f"Makaleler alınırken bir hata oluştu: {str(e)}"}), 500

@app.route('/api/admin/reviewers', methods=['GET'])
def get_reviewers():
    """Tüm hakemleri listeler"""
    try:
        reviewers = db.get_all_reviewers()
        return jsonify(reviewers)
    except Exception as e:
        return jsonify({"message": f"Hakemler alınırken bir hata oluştu: {str(e)}"}), 500

@app.route('/api/admin/assign-reviewer', methods=['POST'])
def assign_reviewer():
    """Makaleye hakem atar"""
    try:
        data = request.get_json()
        article_id = data.get('article_id')
        reviewer_email = data.get('reviewer_email')

        if not article_id or not reviewer_email:
            return jsonify({"message": "Makale ID ve hakem email'i gereklidir"}), 400

        success = db.assign_article_to_reviewer(article_id, reviewer_email)
        if success:
            return jsonify({"message": "Hakem ataması başarıyla yapıldı"}), 200
        else:
            return jsonify({"message": "Bu makale için hakem zaten atanmış"}), 400
    except Exception as e:
        return jsonify({"message": f"Hakem atanırken bir hata oluştu: {str(e)}"}), 500

@app.route('/api/admin/add-test-reviewer', methods=['POST'])
def add_test_reviewer():
    """Test hakemi ekler"""
    try:
        success = db.add_test_reviewer()
        if success:
            return jsonify({"message": "Test hakem başarıyla eklendi"}), 200
        else:
            return jsonify({"message": "Test hakem eklenirken bir hata oluştu"}), 500
    except Exception as e:
        return jsonify({"message": f"Test hakem eklenirken bir hata oluştu: {str(e)}"}), 500

@app.route('/api/admin/approve/<int:article_id>', methods=['POST'])
def approve_article(article_id):
    try:
        article = db.get_article_by_id(article_id)
        if not article:
            return jsonify({"message": "Makale bulunamadı"}), 404
            
        # Makaleyi onayla
        db.update_article_status(article_id, "Onaylandı")
        
        return jsonify({
            "message": "Makale başarıyla onaylandı",
            "article_id": article_id
        }), 200
    except Exception as e:
        print(f"[HATA] Makale onaylama hatası: {str(e)}")
        return jsonify({"message": f"Makale onaylanırken bir hata oluştu: {str(e)}"}), 500

@app.route('/api/admin/reject/<int:article_id>', methods=['POST'])
def reject_article(article_id):
    try:
        article = db.get_article_by_id(article_id)
        if not article:
            return jsonify({"message": "Makale bulunamadı"}), 404
            
        # Makaleyi reddet
        db.update_article_status(article_id, "Onaylanmadı")
        
        return jsonify({
            "message": "Makale başarıyla reddedildi",
            "article_id": article_id
        }), 200
    except Exception as e:
        print(f"[HATA] Makale reddetme hatası: {str(e)}")
        return jsonify({"message": f"Makale reddedilirken bir hata oluştu: {str(e)}"}), 500
    
@app.route('/api/admin/reset-assignments', methods=['POST'])
def reset_assignments():
    try:
        with sqlite3.connect(db.db_path) as conn:
            cursor = conn.cursor()
            # Mevcut atamaları temizle
            cursor.execute('DELETE FROM article_reviewers')
            conn.commit()
        
        # Yeniden ata
        success = db.add_test_reviewer()
        if success:
            return jsonify({'message': 'Makale atamaları başarıyla sıfırlandı ve yeniden atandı'}), 200
        else:
            return jsonify({'error': 'Makale atamaları sıfırlanırken bir hata oluştu'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/articles/<int:article_id>', methods=['GET'])
def get_article_by_id(article_id):
    """ID ile makale detaylarını getirir"""
    try:
        print(f"[INFO] Getting article details for ID: {article_id}")
        
        # Try to get from database
        article = db.get_article_by_id(article_id)
        
        if article:
            print(f"[INFO] Found article in database: {article['title']}")
            
            # Normalize status for frontend
            if article['status'] == 'Kabul Edildi':
                article['status'] = 'Onaylandı'
            elif article['status'] == 'Reddedildi':
                article['status'] = 'Onaylanmadı'
            
            # Ensure response is JSON
            response = jsonify(article)
            response.headers['Content-Type'] = 'application/json'
            return response
            
        # If not found in db, use sample data for testing
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT a.*, ar.status as review_status
                FROM articles a
                LEFT JOIN article_reviewers ar ON a.id = ar.article_id
                WHERE a.id = ?
            ''', (article_id,))
            article = cursor.fetchone()
            
            if article:
                response = jsonify(dict(article))
                response.headers['Content-Type'] = 'application/json'
                return response
                
            # No article found, return sample data
            print(f"[INFO] No article found in DB with id {article_id}, returning sample data")
            
            sample_data = {
                'id': article_id,
                'title': f'Test Makale {article_id}',
                'author': 'Dr. Test Yazar',
                'institution': 'Test Üniversitesi',
                'email': 'test@example.com',
                'abstract': 'Bu bir test makalesidir. Makalenin özeti burada görüntülenecektir.',
                'keywords': 'test, örnek, anahtar kelimeler',
                'status': 'Onaylandı',
                'upload_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'tracking_code': f'TST-{article_id}',
                'reviewers': [
                    {'name': 'Hakem 1', 'email': 'hakem1@example.com'},
                    {'name': 'Hakem 2', 'email': 'hakem2@example.com'}
                ],
                'reviews': [
                    {
                        'reviewer_name': 'Hakem 1',
                        'decision': 'accept',
                        'comments': 'Makale kabul edilebilir durumdadır.',
                        'review_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                ]
            }
            
            response = jsonify(sample_data)
            response.headers['Content-Type'] = 'application/json'
            return response
            
    except Exception as e:
        print(f"[ERROR] Error getting article details: {str(e)}")
        error_response = jsonify({"error": f"Makale detayları alınırken hata oluştu: {str(e)}"})
        error_response.headers['Content-Type'] = 'application/json'
        return error_response, 500

@app.route('/api/articles/<int:article_id>/reviewers', methods=['GET'])
def get_article_reviewers_fallback(article_id):
    """Makaleye atanmış hakemleri getirir (fallback test data)"""
    try:
        # First try to get actual data
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT r.name, r.email
                FROM article_reviewers ar
                JOIN reviewers r ON ar.reviewer_email = r.email
                WHERE ar.article_id = ?
            ''', (article_id,))
            
            reviewers = [dict(row) for row in cursor.fetchall()]
            
            if reviewers:
                return jsonify(reviewers)
                
        # If no data, return sample
        sample_reviewers = [
            {'name': 'Dr. Ali Yılmaz', 'email': 'ali.yilmaz@example.com'},
            {'name': 'Prof. Ayşe Kaya', 'email': 'ayse.kaya@example.com'}
        ]
        
        return jsonify(sample_reviewers)
            
    except Exception as e:
        return jsonify({"error": f"Hakemler alınırken hata oluştu: {str(e)}"}), 500

@app.route('/api/articles/<int:article_id>/reviews', methods=['GET'])
def get_article_reviews_fallback(article_id):
    """Makaleye ait değerlendirmeleri ID ile getirir (fallback test data)"""
    try:
        # First try to get actual data
        with sqlite3.connect(db.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Değerlendirmeleri getir
            cursor.execute('''
                SELECT ar.decision, ar.comments, ar.review_date, r.name as reviewer_name
                FROM article_reviewers ar
                JOIN reviewers r ON ar.reviewer_email = r.email
                WHERE ar.article_id = ? AND ar.status = 'Tamamlandı'
                ORDER BY ar.review_date DESC
            ''', (article_id,))
            
            reviews = [dict(row) for row in cursor.fetchall()]
            
            if reviews:
                return jsonify(reviews)
                
        # If no data, return sample
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        sample_reviews = [
            {
                'reviewer_name': 'Dr. Ali Yılmaz',
                'decision': 'accept',
                'comments': 'Makale kabul edilebilir durumdadır. İyi çalışma.',
                'review_date': now
            }
        ]
        
        return jsonify(sample_reviews)
            
    except Exception as e:
        return jsonify({"error": f"Değerlendirmeler alınırken hata oluştu: {str(e)}"}), 500

@app.route('/api/admin/download/<int:article_id>', methods=['GET'])
def download_article(article_id):
    try:
        article = db.get_article_by_id(article_id)
        if not article:
            return jsonify({"message": "Makale bulunamadı"}), 404
            
        file_path = article.get('file_path')
        if not file_path or not os.path.exists(file_path):
            return jsonify({"message": "Dosya bulunamadı"}), 404

        return send_file(
            file_path,
            as_attachment=True,
            download_name=f"makale_{article_id}.pdf",
            mimetype='application/pdf'
        )
    except Exception as e:
        return jsonify({"message": f"Dosya indirilirken hata oluştu: {str(e)}"}), 500

# Frontend dosyalarını sunmak için route'lar
@app.route('/')
def index():
    return send_from_directory('../../frontend/pages', 'index.html')

@app.route('/<path:path>')
def serve_pages(path):
    try:
        if path.startswith('js/'):
            return send_from_directory('../../frontend', path)
        elif path.startswith('css/'):
            return send_from_directory('../../frontend', path)
        elif path.endswith('.html'):
            return send_from_directory('../../frontend/pages', path)
        else:
            return send_from_directory('../../frontend', path)
    except Exception as e:
        print(f"[ERROR]: {str(e)}")
        return redirect('/')

if __name__ == "__main__":
    app.run(debug=True, port=5000)
