import re
import spacy

class Anonymizer:
    def __init__(self):
        """
        Anonymizer sınıfı, metinlerdeki kişisel ve kurumsal bilgileri anonimleştirmek için kullanılır.
        """
        print("[INFO][anonymizer.py]: Initializing Anonymizer.")

        try:
            self.nlp = spacy.load("xx_ent_wiki_sm")
        except OSError:
            print("[INFO][anonymizer.py]: Model not found. Downloading...")
            spacy.cli.download("xx_ent_wiki_sm")
            self.nlp = spacy.load("xx_ent_wiki_sm")

    def anonymize_email(self, text):
        """
        Metindeki e-posta adreslerini anonimleştirir.
        """
        return re.sub(r'\b[\w\.-]+@[\w\.-]+\.\w+\b', '[EMAIL]', text)

    def anonymize_phone(self, text):
        """
        Metindeki telefon numaralarını anonimleştirir.
        """
       
        phone_patterns = [
            r'\b\+?90?\s*\(?5\d{2}\)?\s*\d{3}\s*\d{2}\s*\d{2}\b',  
            r'\b\+?90?\s*\(?[1-9]\d{2}\)?\s*\d{3}\s*\d{2}\s*\d{2}\b',  
        ]
        for pattern in phone_patterns:
            text = re.sub(pattern, '[TELEFON]', text)
        return text

    def anonymize_tckn(self, text):
        """
        Metindeki TC Kimlik numaralarını anonimleştirir.
        """
        return re.sub(r'\b\d{11}\b', '[TCKN]', text)

    def anonymize_entities(self, text):
        """
        Metindeki kişi ve kurum isimlerini anonimleştirir.
        """
        doc = self.nlp(text)
        new_text = text
        for ent in doc.ents:
            if ent.label_ in {"PER", "PERSON", "ORG"}:  # PER ve PERSON: Kişi, ORG: Kurum
                if not ent.text.isupper():  # Tamamen büyük harfli kelimeleri (kısaltmaları) koru
                    new_text = re.sub(r'\b' + re.escape(ent.text) + r'\b', '', new_text)
        return new_text

    def anonymize(self, text):
        """
        Metindeki tüm hassas bilgileri anonimleştirir.
        """
        print("[INFO][anonymizer.py]: Starting anonymization process.")
        text = self.anonymize_email(text)
        text = self.anonymize_phone(text)
        text = self.anonymize_tckn(text)
        text = self.anonymize_entities(text)
        print("[INFO][anonymizer.py]: Anonymization process completed.")
        return text


# Örnek kullanım
if __name__ == "__main__":
    anonymizer = Anonymizer()
    ornek_metin = """
    Dr. Ahmet Yılmaz ve Prof. Dr. Mehmet Öz, İstanbul Üniversitesi'nde çalışıyor.
    İletişim: ahmet.yilmaz@example.com, +90 532 123 45 67
    TC: 12345678901
    """
    
    anonim_metin = anonymizer.anonymize(ornek_metin)
    print("\nOrijinal metin:")
    print(ornek_metin)
    print("\nAnonimleştirilmiş metin:")
    print(anonim_metin)