import sqlite3
import os
from datetime import datetime

class Database:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'makale.db')
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Makaleler tablosu
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS articles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    keywords TEXT,
                    institution TEXT,
                    tracking_code TEXT UNIQUE NOT NULL,
                    file_path TEXT NOT NULL,
                    anonymized_filename TEXT,
                    original_filename TEXT,
                    upload_date TIMESTAMP,
                    status TEXT DEFAULT 'Beklemede'
                )
            ''')
            
            # Check if original_filename column exists, if not add it
            cursor.execute("PRAGMA table_info(articles)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'original_filename' not in columns:
                print("[INFO] Adding original_filename column to articles table")
                cursor.execute("ALTER TABLE articles ADD COLUMN original_filename TEXT")
            
            # Hakemler tablosu
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reviewers (
                    name TEXT NOT NULL,
                    email TEXT PRIMARY KEY,
                    created_at TIMESTAMP
                )
            ''')
            
            # Makale-Hakem ilişki tablosu
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS article_reviewers (
                    article_id INTEGER,
                    reviewer_email TEXT,
                    assigned_date TIMESTAMP,
                    status TEXT DEFAULT 'Beklemede',
                    decision TEXT,
                    comments TEXT,
                    review_date TIMESTAMP,
                    PRIMARY KEY (article_id, reviewer_email),
                    FOREIGN KEY (article_id) REFERENCES articles (id),
                    FOREIGN KEY (reviewer_email) REFERENCES reviewers (email)
                )
            ''')
            
            # Değerlendirmeler tablosu
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_id INTEGER,
                    reviewer_email TEXT,
                    decision TEXT,
                    comments TEXT,
                    review_date TIMESTAMP,
                    FOREIGN KEY (article_id) REFERENCES articles (id),
                    FOREIGN KEY (reviewer_email) REFERENCES reviewers (email)
                )
            ''')
            
            # Kullanıcılar tablosu
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL,
                    created_at TIMESTAMP
                )
            ''')
            
            conn.commit()

    def verify_reviewer_access(self, article_id, reviewer_email):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 1 FROM article_reviewers 
                WHERE article_id = ? AND reviewer_email = ?
            ''', (article_id, reviewer_email))
            return cursor.fetchone() is not None
    
    def generate_tracking_code(self):
        """Benzersiz takip kodu oluşturur"""
        current_time = datetime.now()
        # Format: MKL-YYYYMMDD-XXXX (MKL: Makale, XXXX: Sıralı numara)
        base_code = f"MKL-{current_time.strftime('%Y%m%d')}"
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Bugün oluşturulan son kodu bul
            cursor.execute(
                "SELECT tracking_code FROM articles WHERE tracking_code LIKE ? ORDER BY id DESC LIMIT 1", 
                (f"{base_code}%",)
            )
            last_code = cursor.fetchone()
            
            if last_code:
                last_number = int(last_code[0][-4:])
                new_number = str(last_number + 1).zfill(4)
            else:
                new_number = "0001"
                
            return f"{base_code}-{new_number}"

    def add_article(self, title, keywords, institution, original_filename, anonymized_filename, file_path):
        """Yeni makale ekler ve takip kodunu döndürür"""
        tracking_code = self.generate_tracking_code()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Check if the articles table has the necessary columns
                cursor.execute("PRAGMA table_info(articles)")
                columns = [column[1] for column in cursor.fetchall()]
                print(f"[DEBUG] Available columns in articles table: {columns}")
                
                # Makaleyi ekle
                cursor.execute('''
                    INSERT INTO articles (
                        title, tracking_code, keywords, institution, 
                        original_filename, anonymized_filename, 
                        upload_date, file_path, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    title, tracking_code, keywords, institution,
                    original_filename, anonymized_filename,
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    file_path, 'Beklemede'
                ))
                
                # Yeni eklenen makalenin ID'sini al
                article_id = cursor.lastrowid
                
                # Tüm hakemleri al
                cursor.execute('SELECT email FROM reviewers')
                reviewers = cursor.fetchall()
                
                # Makaleyi tüm hakemlere ata
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                for reviewer in reviewers:
                    cursor.execute('''
                        INSERT INTO article_reviewers 
                        (article_id, reviewer_email, assigned_date, status)
                        VALUES (?, ?, ?, ?)
                    ''', (
                        article_id,
                        reviewer[0],  # reviewer email
                        current_time,
                        'Beklemede'
                    ))
                
                conn.commit()
                print(f"[INFO] Yeni makale eklendi ve hakemlere atandı: {tracking_code}")
                return tracking_code
                
        except Exception as e:
            print(f"[HATA] Makale eklenirken hata: {str(e)}")
            return None

    def get_article_by_tracking_code(self, tracking_code):
        """Takip kodu ile makale bilgilerini getirir"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM articles WHERE tracking_code = ?', (tracking_code,))
            return dict(cursor.fetchone() or {})

    def update_article_status(self, article_id: int, new_status: str) -> bool:
        """Makale durumunu günceller"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE articles 
                    SET status = ? 
                    WHERE id = ?
                ''', (new_status, article_id))
                conn.commit()
                return True
        except Exception as e:
            print(f"[HATA] Makale durumu güncellenirken hata: {str(e)}")
            return False
    
    def get_article_by_id(self, article_id):
        """ID ile makale bilgilerini getirir"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get basic article info
                cursor.execute('''
                    SELECT * FROM articles WHERE id = ?
                ''', (article_id,))
                
                article_data = cursor.fetchone()
                if not article_data:
                    return None
                    
                article = dict(article_data)
                
             
                cursor.execute('''
                    SELECT r.name, r.email, ar.status as review_status
                    FROM article_reviewers ar
                    JOIN reviewers r ON ar.reviewer_email = r.email
                    WHERE ar.article_id = ?
                ''', (article_id,))
                
                reviewers = [dict(row) for row in cursor.fetchall()]
                article['reviewers'] = reviewers
                
                # Get reviews
                cursor.execute('''
                    SELECT ar.decision, ar.comments, ar.review_date, r.name as reviewer_name
                    FROM article_reviewers ar
                    JOIN reviewers r ON ar.reviewer_email = r.email
                    WHERE ar.article_id = ? AND ar.status = 'Tamamlandı'
                ''', (article_id,))
                
                reviews = [dict(row) for row in cursor.fetchall()]
                article['reviews'] = reviews
                
                # Convert dates to ISO format
                if article.get('upload_date'):
                    try:
                        date_obj = datetime.strptime(article['upload_date'], '%Y-%m-%d %H:%M:%S')
                        article['submission_date'] = date_obj.isoformat()
                    except Exception as e:
                        print(f"[ERROR] Date conversion error: {str(e)}")
                
                return article
                
        except Exception as e:
            print(f"[ERROR] get_article_by_id error: {str(e)}")
            return None

    def get_all_articles(self):
        """Tüm makaleleri listeler"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM articles ORDER BY upload_date DESC')
            articles = [dict(row) for row in cursor.fetchall()]
            
            # Convert dates to ISO format for better JavaScript compatibility
            for article in articles:
                try:
                    if article.get('upload_date'):
                        # Ensure date is properly formatted
                        date_obj = datetime.strptime(article['upload_date'], '%Y-%m-%d %H:%M:%S')
                        article['submission_date'] = date_obj.isoformat()
                except Exception as e:
                    print(f"[ERROR] Date conversion error: {str(e)}")
                    # Set current date as fallback
                    article['submission_date'] = datetime.now().isoformat()
            
            return articles

    def add_user(self, name, email, password, role):
        """Yeni kullanıcı ekler"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO users (name, email, password, role, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    name, email, password, role,
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None

    def get_user_by_email(self, email):
        """Email ile kullanıcı bilgilerini getirir"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM users WHERE email = ?', (email,))
            user = cursor.fetchone()
            return dict(user) if user else None

    def get_reviewer_by_email(self, email):
        """Email ile hakem bilgilerini getirir"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM reviewers WHERE email = ?', (email,))
            reviewer = cursor.fetchone()
            return dict(reviewer) if reviewer else None

    def get_articles_by_reviewer(self, email):
        """Hakeme atanmış makaleleri getirir"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT a.*, ar.status as review_status
                FROM articles a
                JOIN article_reviewers ar ON a.id = ar.article_id
                WHERE ar.reviewer_email = ?
                ORDER BY a.upload_date DESC
            ''', (email,))
            return [dict(row) for row in cursor.fetchall()]

    def add_review(self, article_id, reviewer_email, decision, comments):
        """Makale değerlendirmesini ekler"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Önce bu hakemin bu makale için yetkisi var mı kontrol et
                cursor.execute('''
                    SELECT status FROM article_reviewers 
                    WHERE article_id = ? AND reviewer_email = ?
                ''', (article_id, reviewer_email))
                
                reviewer_status = cursor.fetchone()
                if not reviewer_status:
                    print(f"[HATA] Hakem yetkisi bulunamadı: article_id={article_id}, reviewer={reviewer_email}")
                    return False
                    
                # Değerlendirmeyi güncelle
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cursor.execute('''
                    UPDATE article_reviewers 
                    SET status = ?, decision = ?, comments = ?, review_date = ?
                    WHERE article_id = ? AND reviewer_email = ?
                ''', ('Tamamlandı', decision, comments, current_time, article_id, reviewer_email))
                
                # Tüm hakemlerin değerlendirmelerini kontrol et
                cursor.execute('''
                    SELECT COUNT(*) as total, 
                           SUM(CASE WHEN status = 'Tamamlandı' THEN 1 ELSE 0 END) as completed,
                           SUM(CASE WHEN decision = 'accept' THEN 1 
                                   WHEN decision = 'reject' THEN -1 
                                   ELSE 0 END) as decision_sum
                    FROM article_reviewers 
                    WHERE article_id = ?
                ''', (article_id,))
                
                stats = cursor.fetchone()
                if stats[1] == stats[0]:  # Tüm hakemler değerlendirme yaptıysa
                    # Çoğunluk kararına göre makale durumunu güncelle
                    new_status = 'Kabul Edildi' if stats[2] > 0 else 'Reddedildi'
                    cursor.execute('''
                        UPDATE articles 
                        SET status = ? 
                        WHERE id = ?
                    ''', (new_status, article_id))
                
                conn.commit()
                print(f"[INFO] Değerlendirme başarıyla eklendi: article_id={article_id}, reviewer={reviewer_email}")
                return True
                
        except Exception as e:
            print(f"[HATA] Değerlendirme eklenirken hata: {str(e)}")
            return False

    def get_article_reviews(self, tracking_code):
        """Makaleye ait değerlendirmeleri getirir"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT ar.decision, ar.comments, ar.review_date, r.name as reviewer_name
                    FROM articles a
                    JOIN article_reviewers ar ON a.id = ar.article_id
                    JOIN reviewers r ON ar.reviewer_email = r.email
                    WHERE a.tracking_code = ? AND ar.status = 'Tamamlandı'
                    ORDER BY ar.review_date DESC
                ''', (tracking_code,))
                
                reviews = [dict(row) for row in cursor.fetchall()]
                print(f"[INFO] {tracking_code} için bulunan değerlendirme sayısı: {len(reviews)}")
                return reviews
                
        except Exception as e:
            print(f"[HATA] Değerlendirmeler alınırken hata: {str(e)}")
            return []

    def assign_article_to_reviewer(self, article_id, reviewer_email):
        """Makaleyi hakeme atar"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO article_reviewers (article_id, reviewer_email, assigned_date, status)
                    VALUES (?, ?, ?, ?)
                ''', (
                    article_id, 
                    reviewer_email, 
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'Beklemede'
                ))
                conn.commit()
                return True
        except sqlite3.IntegrityError:
            return False

    def get_unassigned_articles(self):
        """Henüz hakeme atanmamış makaleleri getirir"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT a.* FROM articles a
                WHERE NOT EXISTS (
                    SELECT 1 FROM article_reviewers ar
                    WHERE ar.article_id = a.id
                )
                ORDER BY a.upload_date DESC
            ''')
            return [dict(row) for row in cursor.fetchall()]

    def get_all_reviewers(self):
        """Tüm hakemleri listeler"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM reviewers ORDER BY name')
            return [dict(row) for row in cursor.fetchall()]

    def add_test_reviewer(self):
        """Test hakemlerini ekler ve makaleleri atar"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Test hakemleri ekle
                test_reviewers = [
                    ('Hakem-1', 'hakem1@example.com'),
                    ('Hakem-2', 'hakem2@example.com'),
                    ('Hakem-3', 'hakem3@example.com')
                ]
                
                for name, email in test_reviewers:
                    cursor.execute('''
                        INSERT OR IGNORE INTO reviewers (name, email, created_at)
                        VALUES (?, ?, ?)
                    ''', (
                        name,
                        email,
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    ))
                
                # Tüm makaleleri al
                cursor.execute('SELECT id FROM articles')
                all_articles = cursor.fetchall()
                
                # Her makaleyi her hakeme ata
                for article in all_articles:
                    for reviewer in test_reviewers:
                        cursor.execute('''
                            INSERT OR IGNORE INTO article_reviewers 
                            (article_id, reviewer_email, assigned_date, status)
                            VALUES (?, ?, ?, ?)
                        ''', (
                            article[0],
                            reviewer[1],  # reviewer email
                            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                            'Beklemede'
                        ))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"Test hakemler eklenirken hata: {str(e)}")
            return False