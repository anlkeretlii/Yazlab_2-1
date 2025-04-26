import fitz  
from PIL import Image, ImageFilter
import io
from anonymizer import Anonymizer

anonymizer = Anonymizer()

class PDFProcessor:
    def __init__(self, input_pdf_path, output_pdf_path):
        self.input_pdf_path = input_pdf_path
        self.output_pdf_path = output_pdf_path
        self.doc = fitz.open(input_pdf_path)

    def blur_images(self, blur_radius=5):
        print(f"INFO [pdf_isleme.py]: Starting to blur images in PDF: {self.input_pdf_path}")
        for page in self.doc:
            image_list = page.get_images(full=True)
            print(f"INFO [pdf_isleme.py]: Found {len(image_list)} images on a page.")
            for img in image_list:
                xref = img[0]
                rects = page.get_image_rects(xref)
                if not rects:
                    continue
                pix = fitz.Pixmap(self.doc, xref)
                if pix.n > 3:
                    pix = fitz.Pixmap(fitz.csRGB, pix)
                img_data = pix.tobytes("png")
                image = Image.open(io.BytesIO(img_data))
                blurred_image = image.filter(ImageFilter.GaussianBlur(radius=blur_radius))
                buf = io.BytesIO()
                blurred_image.save(buf, format="PNG")
                buf.seek(0)
                blurred_data = buf.getvalue()
                for rect in rects:
                    page.insert_image(rect, stream=blurred_data)
                pix = None
        print(f"INFO [pdf_isleme.py]: Images blurred successfully.")

    def append_reviewer_comments(self, comments_text):
        print(f"INFO [pdf_isleme.py]: Appending reviewer comments to PDF: {self.input_pdf_path}")
        page = self.doc.new_page()
        margin = 50
        rect = fitz.Rect(margin, margin, page.rect.width - margin, page.rect.height - margin)
        page.insert_textbox(rect, comments_text, fontsize=12, fontname="helv")
        print(f"INFO [pdf_isleme.py]: Reviewer comments added successfully.")

    def anonymize_pdf(self):
        print(f"INFO [pdf_isleme.py]: Starting anonymization process for PDF: {self.input_pdf_path}")
        for page_num, page in enumerate(self.doc, 1):
            print(f"INFO [pdf_isleme.py]: Processing page {page_num}.")
            image_list = page.get_images(full=True)
            print(f"INFO [pdf_isleme.py]: Found {len(image_list)} images on page {page_num}.")
            for img_num, img in enumerate(image_list, 1):
                print(f"INFO [pdf_isleme.py]: Processing image {img_num} on page {page_num}.")
                xref = img[0]
                rects = page.get_image_rects(xref)
                if not rects:
                    continue
                pix = fitz.Pixmap(self.doc, xref)
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

            print(f"INFO [pdf_isleme.py]: Anonymizing text on page {page_num}.")
            text_instances = page.get_text("words")
            for inst in text_instances:
                text = inst[4]
                rect = fitz.Rect(inst[0:4])
                font_size = inst[5]
                anonymized_text = anonymizer.anonymize(text)
                if anonymized_text != text:
                    page.draw_rect(rect, color=(0, 0, 0), fill=(0, 0, 0), width=0.5)
                    if anonymized_text != "***":
                        text_rect = fitz.Rect(rect.x0, rect.y0, rect.x1, rect.y1)
                        page.insert_text(text_rect.tl, anonymized_text, fontsize=font_size, color=(1, 1, 1), render_mode=0)
        print(f"INFO [pdf_isleme.py]: Anonymization process completed.")

    def save(self):
        print(f"INFO [pdf_isleme.py]: Saving PDF to: {self.output_pdf_path}")
        self.doc.save(self.output_pdf_path)
        self.doc.close()
        print(f"INFO [pdf_isleme.py]: PDF saved successfully.")


# Örnek kullanım
if __name__ == '__main__':
    print(f"INFO [pdf_isleme.py]: Example usage started.")
    input_pdf = "uploads/sample.pdf"
    blurred_pdf = "uploads/sample_blurred.pdf"
    final_pdf = "uploads/sample_final.pdf"

    processor = PDFProcessor(input_pdf, blurred_pdf)
    processor.blur_images(blur_radius=5)
    processor.save()

    processor = PDFProcessor(blurred_pdf, final_pdf)
    comments = (
        "Reviewer Comments:\n"
        "- The methodology section needs more details.\n"
        "- Consider improving the clarity of the figures.\n"
        "- Overall, the paper is promising."
    )
    processor.append_reviewer_comments(comments)
    processor.save()
    print(f"INFO [pdf_isleme.py]: Example usage completed.")
