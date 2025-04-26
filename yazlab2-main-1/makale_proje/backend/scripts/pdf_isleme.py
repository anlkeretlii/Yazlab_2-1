import fitz  # PyMuPDF
from PIL import Image, ImageFilter
import io
from anonymizer import anonimlestir

def blur_images_in_pdf(input_pdf_path, output_pdf_path, blur_radius=5):
    """
    PDF içindeki tüm resimleri bulanıklaştırır.
    
    Her resim için:
      - Resim verisi çıkarılır.
      - PIL ile bulanıklaştırılır.
      - Bulanık resim, orijinal resmin konumuna eklenir.
      
    Not: PDF içerisindeki bazı resimler overlay işlemiyle güncellenir.
    """
    doc = fitz.open(input_pdf_path)
    
    for page in doc:
        # Sayfada yer alan resimleri tespit et
        image_list = page.get_images(full=True)
        for img in image_list:
            xref = img[0]
            # Resmin bulunduğu dikdörtgen bölgeleri
            rects = page.get_image_rects(xref)
            if not rects:
                continue
            # Resmi pixmap olarak elde et
            pix = fitz.Pixmap(doc, xref)
            # Eğer resim CMYK veya alfa kanallıysa RGB'ye çevir
            if pix.n > 3:
                pix = fitz.Pixmap(fitz.csRGB, pix)
            img_data = pix.tobytes("png")
            # PIL ile resmi aç
            image = Image.open(io.BytesIO(img_data))
            # Gaussian blur uygula
            blurred_image = image.filter(ImageFilter.GaussianBlur(radius=blur_radius))
            # Bulanık resim, resmin bulunduğu her alana overlay olarak ekle
            for rect in rects:
                page.insert_image(rect, stream=blurred_image)
            pix = None  # Hafıza temizliği için
    
    doc.save(output_pdf_path)
    doc.close()

def append_reviewer_comments(input_pdf_path, output_pdf_path, comments_text):
    """
    Verilen PDF dosyasının sonuna, hakem yorumlarını içeren yeni bir sayfa ekler.
    
    comments_text: Hakem yorumlarını içeren metin.
    """
    doc = fitz.open(input_pdf_path)
    # Yeni bir boş sayfa oluştur (sayfa boyutu, orijinal PDF'in ilk sayfasının boyutuna göre ayarlanabilir)
    page = doc.new_page()
    # Metin için kutu tanımla
    margin = 50
    rect = fitz.Rect(margin, margin, page.rect.width - margin, page.rect.height - margin)
    # Metni sayfaya yerleştir (varsayılan font ve boyut kullanılmakta)
    page.insert_textbox(rect, comments_text, fontsize=12, fontname="helv")
    doc.save(output_pdf_path)
    doc.close()

def pdf_anonimlestir(input_pdf_path, output_pdf_path):
    """
    PDF dosyasındaki metinleri anonimleştirir ve resimleri bulanıklaştırır.
    """
    print(f"PDF işleme başlıyor: {input_pdf_path}")
    doc = fitz.open(input_pdf_path)
    
    for page_num, page in enumerate(doc, 1):
        print(f"\nSayfa {page_num} işleniyor...")
        
        # Önce resimleri bulanıklaştır
        image_list = page.get_images(full=True)
        print(f"Sayfa {page_num}'de bulunan resim sayısı: {len(image_list)}")
        
        for img_num, img in enumerate(image_list, 1):
            print(f"  Resim {img_num} işleniyor...")
            xref = img[0]
            rects = page.get_image_rects(xref)
            if not rects:
                continue
                
            pix = fitz.Pixmap(doc, xref)
            if pix.n > 3:
                pix = fitz.Pixmap(fitz.csRGB, pix)
            
            img_data = pix.tobytes("png")
            image = Image.open(io.BytesIO(img_data))
            blurred_image = image.filter(ImageFilter.GaussianBlur(radius=5))
            
            buf = io.BytesIO()
            blurred_image.save(buf, format="PNG")
            buf.seek(0)
            blurred_data = buf.getvalue()
            
            for rect in rects:
                page.insert_image(rect, stream=blurred_data)
            
            pix = None
        
        # Metinleri anonimleştir
        text_instances = page.get_text("words")  # Her kelime ve konumunu al
        for inst in text_instances:
            text = inst[4]  # Metin içeriği
            rect = fitz.Rect(inst[0:4])  # Metnin konumu
            font_size = inst[5]  # Orijinal font boyutu
            
            # Metni anonimleştir
            anonymized_text = anonimlestir(text)
            if anonymized_text != text:  # Sadece değişen metinleri güncelle
                # Sansür boyutunu hesapla
                censored_width = rect.width
                censored_height = rect.height
                
                # Sansür dikdörtgenini çiz
                page.draw_rect(rect, 
                             color=(0, 0, 0),  # Siyah çerçeve
                             fill=(0, 0, 0),   # Siyah dolgu
                             width=0.5)        # Çerçeve kalınlığı
                
                # Eğer metin "***" ise, sansür dikdörtgeni yeterli
                if anonymized_text != "***":
                    # Yeni metni ekle
                    text_rect = fitz.Rect(
                        rect.x0,  # Sol
                        rect.y0,  # Üst
                        rect.x1,  # Sağ
                        rect.y1   # Alt
                    )
                    
                    page.insert_text(
                        text_rect.tl,          # Sol üst köşe
                        anonymized_text,
                        fontsize=font_size,    # Orijinal font boyutu
                        color=(1, 1, 1),       # Beyaz renk
                        render_mode=0          # Normal render modu
                    )
    
    print(f"\nPDF kaydediliyor: {output_pdf_path}")
    doc.save(output_pdf_path)
    doc.close()
    print("İşlem tamamlandı!")

# Örnek kullanım
if __name__ == '__main__':
    # Örnek: Resimleri bulanıklaştırma
    input_pdf = "uploads/sample.pdf"
    blurred_pdf = "uploads/sample_blurred.pdf"
    blur_images_in_pdf(input_pdf, blurred_pdf, blur_radius=5)
    
    # Örnek: Hakem yorumlarını PDF'e ekleme
    comments = (
        "Reviewer Comments:\n"
        "- The methodology section needs more details.\n"
        "- Consider improving the clarity of the figures.\n"
        "- Overall, the paper is promising."
    )
    final_pdf = "uploads/sample_final.pdf"
    append_reviewer_comments(blurred_pdf, final_pdf, comments)
