const API_BASE_URL = 'http://localhost:5000/api';

let currentArticleId = null;
let currentReviewerEmail = null;

document.addEventListener('DOMContentLoaded', function() {
    checkAuth();
    
    // Get article ID from URL first
    const urlParams = new URLSearchParams(window.location.search);
    currentArticleId = urlParams.get('id');
    
    if (!currentArticleId) {
        alert('Makale ID bulunamadı!');
        window.location.href = 'reviewer_dashboard.html';
        return;
    }

    // Then load article details and other initializations
    loadArticleDetails();
    updateReviewerInfo();
    setupLogout();

    // Retrieve reviewer email from localStorage
    currentReviewerEmail = localStorage.getItem('reviewerEmail');

    // Setup review form submission
    setupReviewForm();
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

// Değerlendirme formunu ayarla
function setupReviewForm() {
    const form = document.getElementById('reviewForm');
    const submitButton = document.getElementById('submitReviewButton');

    if (form) {
        form.addEventListener('submit', handleReviewSubmission);
    }

    if (submitButton) {
        submitButton.addEventListener('click', function(e) {
            e.preventDefault();
            handleReviewSubmission(e);
        });
    }
}

// Değerlendirme gönderme işlemini yönet
async function handleReviewSubmission(e) {
    e.preventDefault();
    
    if (!currentArticleId || !currentReviewerEmail) {
        alert('Makale ID veya hakem email bilgisi eksik');
        return;
    }

    const status = document.getElementById('reviewStatus')?.value;
    const comments = document.getElementById('reviewComments')?.value;

    if (!status || !comments) {
        alert('Lütfen karar ve değerlendirme yorumunuzu giriniz.');
        return;
    }

    try {
        // Gönder butonunu devre dışı bırak
        const submitButton = document.getElementById('submitReviewButton');
        if (submitButton) {
            submitButton.disabled = true;
            submitButton.textContent = 'Gönderiliyor...';
        }

        const response = await fetch(`${API_BASE_URL}/reviewer/submit-review`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                article_id: currentArticleId,
                reviewer_email: currentReviewerEmail,
                status: status,
                comments: comments
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'Değerlendirme gönderilirken bir hata oluştu');
        }

        const result = await response.json();
        alert('Değerlendirmeniz başarıyla kaydedildi.');
        window.location.href = 'reviewer_dashboard.html';
    } catch (error) {
        console.error('Değerlendirme gönderilirken hata:', error);
        alert(error.message || 'Değerlendirme gönderilirken bir hata oluştu. Lütfen tekrar deneyin.');
        
        // Hata durumunda butonu tekrar aktif et
        const submitButton = document.getElementById('submitReviewButton');
        if (submitButton) {
            submitButton.disabled = false;
            submitButton.textContent = 'Değerlendirmeyi Gönder';
        }
    }
}

// Makale detaylarını yükle
async function loadArticleDetails() {
    try {
        if (!currentArticleId) {
            throw new Error('Makale ID bulunamadı');
        }

        const response = await fetch(`${API_BASE_URL}/articles/${currentArticleId}`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) {
            if (response.headers.get('content-type')?.includes('text/html')) {
                throw new Error('Sunucu HTML yanıtı döndürdü. Lütfen daha sonra tekrar deneyin.');
            }
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
        }

        const article = await response.json();
        if (!article || Object.keys(article).length === 0) {
            throw new Error('Makale bulunamadı');
        }

        displayArticleDetails(article);
    } catch (error) {
        console.error('Makale detayları yüklenirken hata:', error);
        showError('Makale detayları yüklenirken bir hata oluştu: ' + error.message);
    }
}

// Makale detaylarını göster
function displayArticleDetails(article) {
    const elements = {
        'articleTitle': article.title || 'Başlık bulunamadı',
        'keywords': article.keywords || '-',
        'institution': article.institution || '-',
        'uploadDate': formatDate(article.upload_date) || '-',
        'trackingCode': article.tracking_code || '-',
        'status': article.review_status || 'Beklemede'
    };

    for (const [id, value] of Object.entries(elements)) {
        const element = document.getElementById(id);
        if (element) {
            element.textContent = value;
        }
    }


    const reviewForm = document.getElementById('reviewForm');
    if (reviewForm && article.review_status === 'Tamamlandı') {
        reviewForm.style.display = 'none';
        showError('Bu makale için değerlendirmeniz tamamlanmıştır.');
    }
}


function viewArticle() {
    if (currentArticleId) {
        window.open(`${API_BASE_URL}/view-pdf/${currentArticleId}`, '_blank');
    } else {
        showError('Makale ID bulunamadı');
    }
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