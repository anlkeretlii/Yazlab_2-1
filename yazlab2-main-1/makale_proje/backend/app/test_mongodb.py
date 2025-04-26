from app.database import (
    db, articles, create_indexes, ArticleStatus,
    get_article_by_tracking, update_article_status, backup_collection
)
from datetime import datetime

def test_mongodb():
    try:
        # Indexleri oluştur
        create_indexes()
     
        test_article = {
            'tracking_number': 'TEST-12345',
            'email': 'test@example.com',
            'status': ArticleStatus.UPLOADED.value,
            'submission_date': datetime.now(),
            'last_update': datetime.now(),
            'file_path': 'test.pdf',
            'author_info': {'names': ['Test User']}
        }
        
        # Varsa eski test verisini sil
        articles.delete_one({'tracking_number': 'TEST-12345'})
        
        # Yeni test verisini ekle
        result = articles.insert_one(test_article)
        print("Test verisi eklendi:", result.inserted_id)
        
        # Veriyi oku
        found = get_article_by_tracking('TEST-12345')
        print("Veri okundu:", found is not None)
        
        # Durumu güncelle
        update_success = update_article_status('TEST-12345', ArticleStatus.UNDER_REVIEW)
        print("Durum güncellendi:", update_success)
        
        # Yedek al
        backup_name = backup_collection('articles')
        print("Yedek alındı:", backup_name)
        
        # Veriyi sil
        articles.delete_one({'tracking_number': 'TEST-12345'})
        print("Test başarılı!")
        
    except Exception as e:
        print(f"Test hatası: {str(e)}")

if __name__ == "__main__":
    test_mongodb() 