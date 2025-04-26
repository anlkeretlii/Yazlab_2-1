document.addEventListener('DOMContentLoaded', function() {
    const form = document.getElementById('articleUploadForm');
    
    if (!form) {
        console.error('Form elementi bulunamadı!');
        return;}
    
    console.log('Form elementi bulundu:', form);
    
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        console.log('Form gönderiliyor...');
        
        const title = document.getElementById('title').value;
        const keywords = document.getElementById('keywords').value;
        const institution = document.getElementById('institution').value;
        const fileInput = document.getElementById('file');
        const file = fileInput.files[0];
        
        console.log('Form verileri:', { title, keywords, institution });
        
        if (!file) {
            alert('Lütfen bir PDF dosyası seçin');
            return;
        }
        
        if (!file.type.includes('pdf')) {
            alert('Lütfen sadece PDF dosyası yükleyin');
            return;
        }
        
        const formData = new FormData();
        formData.append('title', title);
        formData.append('keywords', keywords);
        formData.append('institution', institution);
        formData.append('file', file);
        
        try {
            console.log('API isteği gönderiliyor...');
            
            const response = await fetch('http://localhost:5000/api/submit-article', {
                method: 'POST',
                body: formData,
                mode: 'cors',
                credentials: 'include',
                headers: {
                    'Accept': 'application/json'
                }
            });
            
            console.log('API yanıtı:', response);
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('API yanıt verisi:', data);
            
            if (data.tracking_code) {
                alert(`Makale başarıyla yüklendi!\nTakip Kodu: ${data.tracking_code}\nTakip kodunuzu not alın ve makale durumunu kontrol etmek için kullanın.`);
                window.location.href = 'author_login.html';
            } else {
                alert(data.message || 'Makale yüklendi ancak takip kodu alınamadı');
            }
        } catch (error) {
            console.error('Hata:', error);
            alert(`Makale yüklenirken bir hata oluştu: ${error.message}`);
        }
    });
}); 