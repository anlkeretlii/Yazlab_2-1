// API endpoint'leri
const API_BASE_URL = 'http://localhost:5000/api';


document.getElementById('articleForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = new FormData();
    formData.append('email', document.getElementById('email').value);
    formData.append('title', document.getElementById('title').value);
    formData.append('keywords', document.getElementById('keywords').value);
    formData.append('institution', document.getElementById('institution').value);
    formData.append('file', document.getElementById('file').files[0]);

    try {
        const response = await fetch(`${API_BASE_URL}/submit-article`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        
        if (response.ok) {
            alert(`Makale başarıyla yüklendi. Takip numaranız: ${data.tracking_number}`);
            document.getElementById('articleForm').reset();
        } else {
            alert(`Hata: ${data.message}`);
        }
    } catch (error) {
        console.error('Hata:', error);
        alert('Bir hata oluştu. Lütfen tekrar deneyiniz.');
    }
});

// Makale takibi
async function trackArticle(trackingNumber) {
    try {
        const response = await fetch(`${API_BASE_URL}/track-article/${trackingNumber}`);
        const data = await response.json();
        
        if (response.ok) {
            return data;
        } else {
            throw new Error(data.message);
        }
    } catch (error) {
        console.error('Hata:', error);
        throw error;
    }
}

// Editöre mesaj gönderme
async function sendMessageToEditor(articleId, message) {
    try {
        const response = await fetch(`${API_BASE_URL}/send-message`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                article_id: articleId,
                message: message
            })
        });

        const data = await response.json();
        
        if (response.ok) {
            return data;
        } else {
            throw new Error(data.message);
        }
    } catch (error) {
        console.error('Hata:', error);
        throw error;
    }
}

// Revize makale yükleme
async function uploadRevisedArticle(trackingNumber, file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch(`${API_BASE_URL}/revise-article/${trackingNumber}`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        
        if (response.ok) {
            return data;
        } else {
            throw new Error(data.message);
        }
    } catch (error) {
        console.error('Hata:', error);
        throw error;
    }
}

// Yardımcı fonksiyonlar
function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('tr-TR');
}

function getStatusBadgeClass(status) {
    const statusMap = {
        'pending': 'badge-pending',
        'approved': 'badge-approved',
        'rejected': 'badge-rejected'
    };
    return statusMap[status] || 'badge-pending';
} 