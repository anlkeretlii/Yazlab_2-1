from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad
import hashlib
import base64
import fitz 

class Encryptor:
    def __init__(self, aes_key_path="aes_key.bin", rsa_key_path="rsa_key.pem"):
        self.aes_key_path = aes_key_path
        self.rsa_key_path = rsa_key_path
        self.aes_key = self.load_or_generate_aes_key()
        self.rsa_key = self.load_or_generate_rsa_key()

    def load_or_generate_aes_key(self):
        """AES anahtarını yükler veya oluşturur"""
        try:
            with open(self.aes_key_path, "rb") as f:
                return f.read()
        except FileNotFoundError:
            key = get_random_bytes(32)
            with open(self.aes_key_path, "wb") as f:
                f.write(key)
            return key

    def load_or_generate_rsa_key(self):
        """RSA anahtarını yükler veya oluşturur"""
        try:
            with open(self.rsa_key_path, "rb") as f:
                return RSA.import_key(f.read())
        except FileNotFoundError:
            key = RSA.generate(2048)
            with open(self.rsa_key_path, "wb") as f:
                f.write(key.export_key())
            return key

    def hash_password(self, password: str) -> str:
        """SHA-256 ile şifre hashleme"""
        return hashlib.sha256(password.encode()).hexdigest()

    def encrypt_file_aes(self, file_data: bytes) -> tuple:
        """AES ile dosya şifreleme"""
        cipher = AES.new(self.aes_key, AES.MODE_CBC)
        ct_bytes = cipher.encrypt(pad(file_data, AES.block_size))
        return base64.b64encode(ct_bytes).decode('utf-8'), base64.b64encode(cipher.iv).decode('utf-8')

    def decrypt_file_aes(self, encrypted_data: str, iv: str) -> bytes:
        """AES ile dosya şifre çözme"""
        ct = base64.b64decode(encrypted_data)
        iv = base64.b64decode(iv)
        cipher = AES.new(self.aes_key, AES.MODE_CBC, iv)
        pt = unpad(cipher.decrypt(ct), AES.block_size)
        return pt

    def encrypt_rsa(self, data: bytes) -> bytes:
        """RSA ile veri şifreleme (PKCS1_OAEP)"""
        cipher = PKCS1_OAEP.new(self.rsa_key.publickey())
        return cipher.encrypt(data)

    def decrypt_rsa(self, encrypted_data: bytes) -> bytes:
        """RSA ile veri şifre çözme (PKCS1_OAEP)"""
        cipher = PKCS1_OAEP.new(self.rsa_key)
        return cipher.decrypt(encrypted_data)

    def anonymize_pdf(self, file_path: str, sensitive_info: list) -> str:
        """PDF dosyasından hassas bilgileri kaldırma"""
        doc = fitz.open(file_path)
        for page in doc:
            for info in sensitive_info:
                text_instances = page.search_for(info)
                for inst in text_instances:
                    page.insert_text(inst[:2], "[Gizlendi]", fontsize=11, color=(1, 0, 0))

        anonymized_path = file_path.replace(".pdf", "_anonymized.pdf")
        doc.save(anonymized_path)
        doc.close()
        return anonymized_path
