const API_BASE_URL = 'http://localhost:5000/api';

// Get these values from the global scope (already defined in HTML)
// const urlParams = new URLSearchParams(window.location.search);
// const articleId = urlParams.get('id');

// Sayfa yüklendiğinde makale detaylarını getir
document.addEventListener('DOMContentLoaded', loadArticleDetails);

async function loadArticleDetails() {
    try {
        // Show loading indicator
        showLoading(true);
        
        console.log("Fetching article data for ID:", articleId);
        
        // First try to get data from backend directly
        const response = await fetch(`${API_BASE_URL}/articles/${articleId}`);
        
        if (!response.ok) {
            console.warn(`API returned ${response.status}. Attempting to use sample data...`);
            
            // Fetch failed, using sample data as fallback
            const sampleData = {
                id: articleId,
                title: `Test Makale ${articleId}`,
                author: 'Dr. Test Yazar',
                institution: 'Test Üniversitesi',
                email: 'test@example.com',
                abstract: 'Bu bir test makalesidir. Makalenin özeti burada görüntülenecektir.',
                keywords: 'test, örnek, anahtar kelimeler',
                status: 'Onaylandı',
                submission_date: new Date().toISOString(),
                reviews: [],
                upload_date: new Date().toISOString(),
                reviewers: [
                    { name: 'Hakem 1', email: 'hakem1@example.com' },
                    { name: 'Hakem 2', email: 'hakem2@example.com' }
                ]
            };
            
            displayArticleData(sampleData);
            
            // Show warning about using sample data
            showError('Gerçek veri alınamadı. Test verisi gösteriliyor.');
            return;
        }
        
        const article = await response.json();
        console.log("Article data received:", article);
        
        if (!article || Object.keys(article).length === 0) {
            throw new Error('No article data returned from server');
        }
        
        displayArticleData(article);
        
    } catch (error) {
        console.error('Error loading article details:', error);
        showError('Makale detayları yüklenirken bir hata oluştu: ' + error.message);
        
        // Show some placeholder data so the page isn't completely empty
        displayArticleData({
            title: 'Veri Yüklenemedi',
            status: 'Hata',
            author: 'Bilinmiyor',
            institution: 'Bilinmiyor',
            email: 'Bilinmiyor',
            submission_date: null,
            keywords: 'Bilinmiyor',
            abstract: 'Makale verisi yüklenirken bir hata oluştu. Lütfen tekrar deneyin.'
        });
    } finally {
        showLoading(false);
    }
}

// New function to separate data processing from API fetching
function displayArticleData(article) {
    // Normalize status values for consistency
    if (article.status === 'Kabul Edildi') {
        article.status = 'Onaylandı';
    } else if (article.status === 'Reddedildi') {
        article.status = 'Onaylanmadı';
    }
    
    // Makale bilgilerini doldur - added null checks and fallbacks
    document.getElementById('articleTitle').textContent = article.title || 'Başlık bilgisi yok';
    document.getElementById('articleStatus').textContent = article.status || 'Durum bilgisi yok';
    document.getElementById('articleStatus').className = `badge bg-${getStatusBadgeColor(article.status)}`;
    document.getElementById('articleAuthor').textContent = article.author || article.institution || 'Yazar bilgisi yok';
    document.getElementById('articleInstitution').textContent = article.institution || 'Kurum bilgisi yok';
    document.getElementById('articleEmail').textContent = article.email || 'E-posta bilgisi yok';
    document.getElementById('articleDate').textContent = formatDate(article.submission_date || article.upload_date);
    document.getElementById('articleKeywords').textContent = article.keywords || 'Anahtar kelime bilgisi yok';
    document.getElementById('articleAbstract').textContent = article.abstract || 'Özet bilgisi yok';
    
    // Review status formatting - use review_status if available
    if (document.getElementById('reviewStatus')) {
        document.getElementById('reviewStatus').textContent = article.review_status || article.status || 'Beklemede';
    }
    
    // Duruma göre butonları güncelle
    updateButtons(article.status);
    
    // Display reviewers
    displayReviewers(article.reviewers || []);
    
    // Display reviews
    displayReviews(article.reviews || article.comments || []);
}

// Display reviewers
async function displayReviewers(reviewers) {
    const reviewersList = document.getElementById('reviewersList');
    reviewersList.innerHTML = '';
    
    // Convert string reviewers to array if needed
    if (typeof reviewers === 'string') {
        reviewers = reviewers.split(',').map(r => ({name: r.trim()}));
    }
    
    // Handle various formats of reviewer data
    const formattedReviewers = Array.isArray(reviewers) ? reviewers : 
                             (reviewers && typeof reviewers === 'object' ? [reviewers] : []);
                             
    if (formattedReviewers.length > 0) {
        formattedReviewers.forEach(reviewer => {
            const item = document.createElement('div');
            item.className = 'list-group-item';
            item.textContent = typeof reviewer === 'string' ? reviewer : 
                             (reviewer.name || reviewer.email || 'İsimsiz Hakem');
            reviewersList.appendChild(item);
        });
    } else {
        // Try fetching reviewers directly as fallback
        try {
            const reviewerResponse = await fetch(`${API_BASE_URL}/articles/${articleId}/reviewers`);
            if (reviewerResponse.ok) {
                const reviewerData = await reviewerResponse.json();
                
                if (reviewerData && reviewerData.length > 0) {
                    reviewerData.forEach(reviewer => {
                        const item = document.createElement('div');
                        item.className = 'list-group-item';
                        item.textContent = reviewer.name || reviewer.email || 'İsimsiz Hakem';
                        reviewersList.appendChild(item);
                    });
                    return;
                }
            }
            throw new Error('No reviewers found');
        } catch (error) {
            console.log("Couldn't fetch reviewers:", error);
            const item = document.createElement('div');
            item.className = 'list-group-item text-muted';
            item.textContent = 'Henüz hakem atanmamış';
            reviewersList.appendChild(item);
        }
    }
}

// Display reviews
async function displayReviews(reviews) {
    // Update heading to correct terminology
    const reviewsHeading = document.querySelector('h5.reviews-heading');
    if (reviewsHeading) {
        reviewsHeading.textContent = 'Değerlendirmeler';
    }
    
    const reviewsList = document.getElementById('reviewsList');
    reviewsList.innerHTML = '';
    
    // Convert to array if not already
    const formattedReviews = Array.isArray(reviews) ? reviews : 
                          (reviews && typeof reviews === 'object' ? [reviews] : []);
    
    if (formattedReviews.length > 0) {
        formattedReviews.forEach(review => {
            const item = document.createElement('div');
            item.className = 'list-group-item';
            item.innerHTML = `
                <h6 class="mb-1">${review.reviewer_name || review.reviewer || 'Hakem'}</h6>
                <p class="mb-1"><strong>Karar:</strong> ${review.decision || ''}</p>
                <p class="mb-1">${review.comment || review.comments || 'Yorum yapılmamış'}</p>
            `;
            reviewsList.appendChild(item);
        });
    } else {
        // Try fetching reviews directly
        try {
            const reviewsResponse = await fetch(`${API_BASE_URL}/articles/${articleId}/reviews`);
            if (reviewsResponse.ok) {
                const reviewsData = await reviewsResponse.json();
                
                if (reviewsData && reviewsData.length > 0) {
                    reviewsData.forEach(review => {
                        const item = document.createElement('div');
                        item.className = 'list-group-item';
                        item.innerHTML = `
                            <h6 class="mb-1">${review.reviewer_name || 'Hakem'}</h6>
                            <p class="mb-1"><strong>Karar:</strong> ${review.decision || ''}</p>
                            <p class="mb-1">${review.comments || 'Yorum yapılmamış'}</p>
                        `;
                        reviewsList.appendChild(item);
                    });
                    return;
                }
            }
            throw new Error('No reviews found');
        } catch (error) {
            console.log("Couldn't fetch reviews:", error);
            const item = document.createElement('div');
            item.className = 'list-group-item text-muted';
            item.textContent = 'Henüz değerlendirme yapılmamış';
            reviewsList.appendChild(item);
        }
    }
}

// Show/hide loading indicator
function showLoading(isLoading) {
    const loadingEl = document.getElementById('loadingIndicator');
    if (loadingEl) {
        loadingEl.style.display = isLoading ? 'block' : 'none';
    }
}

// Show error message
function showError(message) {
    const errorEl = document.getElementById('errorMessage');
    if (errorEl) {
        errorEl.textContent = message;
        errorEl.style.display = 'block';
    } else {
        alert(message);
    }
}

// Durum badge rengi
function getStatusBadgeColor(status) {
    switch (status) {
        case 'Onay Bekliyor':
            return 'primary';
        case 'Onaylanmadı':
            return 'danger';
        case 'Onaylandı':
            return 'success';
        case 'Değerlendiriliyor':
            return 'info';
        case 'Değerlendirildi':
            return 'warning';
        default:
            return 'secondary';
    }
}

// Tarih formatla - enhanced with better error handling
function formatDate(dateString) {
    if (!dateString) return '-';
    
    try {
        // Try to create a date object
        const date = new Date(dateString);
        
        // Check if date is valid
        if (isNaN(date.getTime())) {
            console.warn(`Invalid date format: ${dateString}`);
            return '-';
        }
        
        return date.toLocaleDateString('tr-TR', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });
    } catch (e) {
        console.error('Date formatting error:', e);
        return '-';
    }
}

// İşlem fonksiyonları
async function anonymizeArticle() {
    try {
        const response = await fetch(`${API_BASE_URL}/admin/anonymize/${articleId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                sensitive_info: ['author', 'institution', 'email']
            })
        });

        const data = await response.json();
        
        if (response.ok) {
            alert('Makale başarıyla Değerlendiriliyor.');
            loadArticleDetails(); // Sayfayı yenile
        } else {
            throw new Error(data.message);
        }
    } catch (error) {
        console.error('Hata:', error);
        alert('Anonimleştirme işlemi sırasında bir hata oluştu.');
    }
}

// Hakem atama formunu göster/gizle
function toggleReviewerForm() {
    const form = document.getElementById('reviewerForm');
    form.style.display = form.style.display === 'none' ? 'block' : 'none';
}

// Hakem atama işlemi
async function assignReviewer() {
    const reviewerEmail = document.getElementById('reviewerEmail').value;
    
    if (!reviewerEmail) {
        alert('Lütfen hakem e-posta adresini girin.');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/admin/assign-reviewer`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                article_id: articleId,
                reviewer_email: reviewerEmail
            })
        });

        const data = await response.json();
        
        if (response.ok) {
            alert('Hakem başarıyla atandı.');
            document.getElementById('reviewerEmail').value = ''; // Input'u temizle
            toggleReviewerForm(); // Formu gizle
            loadArticleDetails(); // Sayfayı yenile
        } else {
            throw new Error(data.message);
        }
    } catch (error) {
        console.error('Hata:', error);
        alert('Hakem atama işlemi sırasında bir hata oluştu.');
    }
}

// Makale durumuna göre butonları göster/gizle
function updateButtons(status) {
    const pendingButtons = document.getElementById('pendingButtons');
    const approvedButtons = document.getElementById('approvedButtons');
    const anonymizedButtons = document.getElementById('anonymizedButtons');
    const reviewingButtons = document.getElementById('reviewingButtons');
    const otherButtons = document.getElementById('otherButtons');
    const reviewerForm = document.getElementById('reviewerForm');

    // Tüm buton gruplarını gizle
    pendingButtons.style.display = 'none';
    approvedButtons.style.display = 'none';
    anonymizedButtons.style.display = 'none';
    reviewingButtons.style.display = 'none';
    otherButtons.style.display = 'none';
    reviewerForm.style.display = 'none';

    // Duruma göre ilgili butonları göster
    switch (status) {
        case 'Onay Bekliyor':
            pendingButtons.style.display = 'block';
            break;
        case 'Onaylandı':
            approvedButtons.style.display = 'block';
            break;
        case 'Değerlendiriliyor':
            anonymizedButtons.style.display = 'block';
            break;
        case 'Değerlendirildi':
            reviewingButtons.style.display = 'block';
            break;
        default:
            otherButtons.style.display = 'block';
    }
}


async function downloadArticle(articleId, type = 'original') {
    try {
        const endpoint = type === 'anonymized' ? 
            `${API_BASE_URL}/admin/download-anonymized/${articleId}` :
            `${API_BASE_URL}/admin/download/${articleId}`;

        const response = await fetch(endpoint, {
            method: 'GET',
            headers: {
                'Accept': 'application/pdf'
            }
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.message || 'İndirme işlemi başarısız');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `makale_${articleId}${type === 'anonymized' ? '_anonymized' : ''}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (error) {
        console.error('Hata:', error);
        alert('Makale indirilirken bir hata oluştu: ' + error.message);
    }
}

// Makale onaylama işlemi
async function approveArticle() {
    try {
        const response = await fetch(`${API_BASE_URL}/admin/approve/${articleId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();
        
        if (response.ok) {
            alert('Makale başarıyla onaylandı.');
            loadArticleDetails(); // Sayfayı yenile
        } else {
            throw new Error(data.message);
        }
    } catch (error) {
        console.error('Hata:', error);
        alert('Onaylama işlemi sırasında bir hata oluştu.');
    }
}

// Makale reddetme işlemi
async function rejectArticle() {
    try {
        const response = await fetch(`${API_BASE_URL}/admin/reject/${articleId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });

        const data = await response.json();
        
        if (response.ok) {
            alert('Makale reddedildi.');
            loadArticleDetails(); // Sayfayı yenile
        } else {
            throw new Error(data.message);
        }
    } catch (error) {
        console.error('Hata:', error);
        alert('Reddetme işlemi sırasında bir hata oluştu.');
    }
}