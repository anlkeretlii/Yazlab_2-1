import spacy
import fitz  
import os
from typing import List, Tuple, Dict
import re

class PDFAnonymizer:
    def __init__(self):
        # Türkçe ve İngilizce dil modellerini yükle
        self.nlp_tr = spacy.load("tr_core_news_sm")
        self.nlp_en = spacy.load("en_core_web_sm")
        
        # Özel regex kalıpları
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.phone_pattern = re.compile(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b')
        
    def detect_entities(self, text: str) -> List[Dict]:
        """Metindeki hassas bilgileri tespit et"""
        # Hem Türkçe hem İngilizce NER uygula
        doc_tr = self.nlp_tr(text)
        doc_en = self.nlp_en(text)
        
        entities = []
        
        # Türkçe varlıkları topla
        for ent in doc_tr.ents:
            if ent.label_ in ['PERSON', 'ORG', 'LOC', 'GPE']:
                entities.append({
                    'text': ent.text,
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'type': ent.label_
                })
        
        # İngilizce varlıkları topla
        for ent in doc_en.ents:
            if ent.label_ in ['PERSON', 'ORG', 'LOC', 'GPE']:
                entities.append({
                    'text': ent.text,
                    'start': ent.start_char,
                    'end': ent.end_char,
                    'type': ent.label_
                })
        
        # E-posta adreslerini bul
        for match in self.email_pattern.finditer(text):
            entities.append({
                'text': match.group(),
                'start': match.start(),
                'end': match.end(),
                'type': 'EMAIL'
            })
        
        # Telefon numaralarını bul
        for match in self.phone_pattern.finditer(text):
            entities.append({
                'text': match.group(),
                'start': match.start(),
                'end': match.end(),
                'type': 'PHONE'
            })
        
        return entities
    
    def anonymize_pdf(self, input_path: str, output_path: str = None) -> str:
        """PDF dosyasını anonimleştir"""
        if not output_path:
            filename, ext = os.path.splitext(input_path)
            output_path = f"{filename}_anonymized{ext}"
        
        # PDF'i aç
        pdf_document = fitz.open(input_path)
        
        # Her sayfayı işle
        for page_num in range(len(pdf_document)):
            page = pdf_document[page_num]
            
            # Sayfadaki metni çıkar
            text = page.get_text()
            
            # Hassas bilgileri tespit et
            entities = self.detect_entities(text)
            
            # Her hassas bilgi için
            for entity in entities:
                # Metni PDF'te bul
                text_instances = page.search_for(entity['text'])
                
                # Her bulunduğu yere siyah dikdörtgen çiz
                for inst in text_instances:
                    # Dikdörtgeni biraz genişlet
                    rect = fitz.Rect(inst)
                    rect.x0 -= 1  # Sol kenar
                    rect.x1 += 1  # Sağ kenar
                    rect.y0 -= 1  # Üst kenar
                    rect.y1 += 1  # Alt kenar
                    
                    # Siyah dikdörtgen çiz
                    page.draw_rect(rect, color=(0, 0, 0), fill=(0, 0, 0))
        
        # Değişiklikleri kaydet
        pdf_document.save(output_path)
        pdf_document.close()
        
        return output_path
    
    def get_anonymized_text(self, text: str) -> str:
        """Metni anonimleştir (test amaçlı)"""
        entities = self.detect_entities(text)
        
        # Sondan başa doğru değiştir (indeks karışıklığı olmaması için)
        for entity in sorted(entities, key=lambda x: x['start'], reverse=True):
            replacement = f"[{entity['type']}]"
            text = text[:entity['start']] + replacement + text[entity['end']:]
        
        return text
