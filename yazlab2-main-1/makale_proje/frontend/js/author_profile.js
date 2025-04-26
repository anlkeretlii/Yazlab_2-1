const API_BASE_URL = 'http://localhost:5000/api';

// Sayfa yüklendiğinde çalışacak fonksiyonlar
document.addEventListener('DOMContentLoaded', () => {
    // Kullanıcı bilgilerini yükle
    loadUserProfile();
    // Son Değerlendirildileri yükle
    loadRecentReviews();
});

// Kullanıcı profil bilgilerini yükle
async function loadUserProfile() {
    try {

        const userEmail = localStorage.getItem('userEmail');
        if (!userEmail) {
            window.location.href = 'author_login.html';
            return;
        }

        const response = await fetch(`${API_BASE_URL}/author/profile/${userEmail}`);
        if (!response.ok) {
            throw new Error('Profil bilgileri alınamadı');
        }

        const data = await response.json();
        
        // Profil bilgilerini doldur
        document.getElementById('firstName').textContent = data.first_name || '-';
        document.getElementById('lastName').textContent = data.last_name || '-';
        document.getElementById('email').textContent = data.email || '-';
        
        // İstatistikleri doldur
        document.getElementById('totalArticles').textContent = data.total_articles || 0;
        document.getElementById('acceptedArticles').textContent = data.accepted_articles || 0;
        document.getElementById('pendingArticles').textContent = data.pending_articles || 0;

    } catch (error) {
        console.error('Profil yükleme hatası:', error);
        alert('Profil bilgileri yüklenirken bir hata oluştu.');
    }
}

// Son Değerlendirildileri yükle
async function loadRecentReviews() {
    try {
        const userEmail = localStorage.getItem('userEmail');
        if (!userEmail) return;

        const response = await fetch(`${API_BASE_URL}/author/reviews/${userEmail}`);
        if (!response.ok) {
            throw new Error('Değerlendirildiler alınamadı');
        }

        const reviews = await response.json();
        const reviewsList = document.getElementById('reviewsList');
        
        // Tabloyu temizle
        reviewsList.innerHTML = '';
        
        // Değerlendirildileri tabloya ekle
        reviews.forEach(review => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${review.article_title}</td>
                <td><span class="badge ${getStatusBadgeClass(review.status)}">${review.status}</span></td>
                <td>${new Date(review.date).toLocaleDateString('tr-TR')}</td>
            `;
            reviewsList.appendChild(row);
        });

    } catch (error) {
        console.error('Değerlendirildiler yükleme hatası:', error);
        alert('Değerlendirildiler yüklenirken bir hata oluştu.');
    }
}

// Durum badge'lerinin CSS sınıflarını belirle
function getStatusBadgeClass(status) {
    switch (status.toLowerCase()) {
        case 'kabul edildi':
            return 'bg-success';
        case 'reddedildi':
            return 'bg-danger';
        case 'revizyon':
            return 'bg-warning';
        case 'Değerlendirildide':
            return 'bg-info';
        default:
            return 'bg-secondary';
    }
} 