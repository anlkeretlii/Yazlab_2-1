const API_BASE_URL = 'http://localhost:5000/api';

// Sayfa yüklendiğinde çalışacak fonksiyonlar
document.addEventListener('DOMContentLoaded', function() {
    checkAuth();
    loadArticles();
    updateReviewerInfo();
    setupLogout();
});

// Oturum kontrolü
function checkAuth() {
    const reviewerEmail = localStorage.getItem('reviewerEmail');
    if (!reviewerEmail) {
        window.location.href = 'reviewer_login.html';
    }
}

// Hakem bilgilerini güncelle
function updateReviewerInfo() {
    const reviewerName = localStorage.getItem('reviewerName');
    const reviewerInfo = document.getElementById('reviewerInfo');
    if (reviewerInfo) {
        reviewerInfo.textContent = `Hoş geldiniz, ${reviewerName || 'Hakem'}`;
    }
}

// Çıkış yap
function setupLogout() {
    const logoutButton = document.getElementById('logoutButton');
    if (logoutButton) {
        logoutButton.addEventListener('click', function() {
            localStorage.removeItem('reviewerEmail');
            localStorage.removeItem('reviewerName');
            window.location.href = 'reviewer_login.html';
        });
    }
}

// Makaleleri yükle
async function loadArticles() {
    try {
        const reviewerEmail = localStorage.getItem('reviewerEmail');
        const response = await fetch(`${API_BASE_URL}/reviewer/articles/${reviewerEmail}`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const articles = await response.json();
        displayArticles(articles);
    } catch (error) {
        console.error('Makaleler yüklenirken hata:', error);
        showError('Makaleler yüklenirken bir hata oluştu. Lütfen tekrar deneyin.');
    }
}

// Makaleleri tabloya ekle
function displayArticles(articles) {
    const tableBody = document.getElementById('articlesTableBody');
    if (!tableBody) return;

    tableBody.innerHTML = '';
    
    if (articles.length === 0) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="6" class="text-center">Değerlendirilecek makale bulunmamaktadır.</td>
            </tr>
        `;
        return;
    }
    
    articles.forEach(article => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${article.tracking_code}</td>
            <td>${article.title}</td>
            <td>${article.keywords || '-'}</td>
            <td>${formatDate(article.upload_date)}</td>
            <td>${getStatusBadge(article.review_status)}</td>
            <td>
                <div class="btn-group" role="group">
                    <button class="btn btn-primary btn-sm" onclick="viewArticle(${article.id})">
                        Görüntüle
                    </button>
                    <button class="btn btn-success btn-sm" onclick="reviewArticle(${article.id})"
                            ${article.review_status === 'Tamamlandı' ? 'disabled' : ''}>
                        Değerlendir
                    </button>
                </div>
            </td>
        `;
        tableBody.appendChild(row);
    });
}


function viewArticle(articleId) {
    const url = `${API_BASE_URL}/reviewer/view-pdf/${articleId}`;
    window.open(url, '_blank');
}

// Makale değerlendir
function reviewArticle(articleId) {
    window.location.href = `reviewer_review.html?id=${articleId}`;
}

// Durum badge'i oluştur
function getStatusBadge(status) {
    const badges = {
        'Beklemede': 'bg-warning',
        'Değerlendiriliyor': 'bg-info',
        'Tamamlandı': 'bg-success',
        'Reddedildi': 'bg-danger'
    };
    
    return `<span class="badge ${badges[status] || 'bg-secondary'}">${status}</span>`;
}

// Tarih formatla
function formatDate(dateString) {
    if (!dateString) return '-';
    const options = { year: 'numeric', month: 'long', day: 'numeric' };
    return new Date(dateString).toLocaleDateString('tr-TR', options);
}

// Hata mesajı göster
function showError(message) {
    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    const container = document.querySelector('.container');
    if (container) {
        container.insertBefore(alertDiv, container.firstChild);
    }
} 