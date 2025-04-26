const API_BASE_URL = 'http://localhost:5000/api';
let currentArticleId = null;
let currentReviewerEmail = null; // Declare the variable at the top of the file

document.addEventListener('DOMContentLoaded', function() {
    checkAuth();
    loadArticleDetails();
    updateReviewerInfo();
    setupLogout();

    // Retrieve reviewer email from localStorage
    currentReviewerEmail = localStorage.getItem('reviewerEmail');
});

// Hakem girişi
document.getElementById('reviewerLoginForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    currentReviewerEmail = document.getElementById('reviewerEmail').value;
    
    try {
        const response = await fetch(`${API_BASE_URL}/reviewer/articles`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: currentReviewerEmail
            })
        });
        
        if (response.ok) {
            loadAssignedArticles();
        } else {
            throw new Error('Giriş başarısız');
        }
    } catch (error) {
        console.error('Hata:', error);
        alert('Giriş yapılırken bir hata oluştu.');
    }
});

// Atanan makaleleri yükle
async function loadAssignedArticles() {
    if (!currentReviewerEmail) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/reviewer/articles/${currentReviewerEmail}`);
        const articles = await response.json();
        
        const tbody = document.getElementById('assignedArticlesList');
        tbody.innerHTML = '';
        
        articles.forEach(article => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${article.id}</td>
                <td>${article.title}</td>
                <td><span class="badge ${getStatusBadgeClass(article.status)}">${article.status}</span></td>
                <td>
                    <button class="btn btn-sm btn-secondary" onclick="downloadAnonymousArticle('${article.id}')">
                        İndir
                    </button>
                    <button class="btn btn-sm btn-primary" onclick="openReviewModal('${article.id}')">
                        Değerlendir
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('Hata:', error);
        alert('Makaleler yüklenirken bir hata oluştu.');
    }
}

// Değerlendirildi modalını aç
function openReviewModal(articleId) {
    currentArticleId = articleId;
    const modal = new bootstrap.Modal(document.getElementById('reviewModal'));
    modal.show();
}

// Değerlendirildi gönder
document.getElementById('submitReviewButton').addEventListener('click', async function() {
    if (!currentArticleId || !currentReviewerEmail) return;
    
    const status = document.getElementById('reviewStatus').value;
    const comments = document.getElementById('reviewComments').value;
    
    if (!status || !comments) {
        alert('Lütfen tüm alanları doldurun.');
        return;
    }
    
    // Değerlendirme durumunu backend ile uyumlu hale getir
    let decision;
    switch(status) {
        case 'Kabul':
            decision = 'accept';
            break;
        case 'Red':
            decision = 'reject';
            break;
        case 'Revizyon':
            decision = 'revise';
            break;
        default:
            decision = status;
    }
    
    try {
        const response = await fetch(`${API_BASE_URL}/reviewer/submit-review`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                article_id: currentArticleId,
                reviewer_email: currentReviewerEmail,
                decision: decision,
                comments: comments
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('Değerlendirildi başarıyla gönderildi.');
            bootstrap.Modal.getInstance(document.getElementById('reviewModal')).hide();
            loadAssignedArticles();
        } else {
            throw new Error(data.message);
        }
    } catch (error) {
        console.error('Hata:', error);
        alert('Değerlendirildi gönderilirken bir hata oluştu.');
    }
});

// Anonim 
async function downloadAnonymousArticle(articleId) {
    if (!currentReviewerEmail) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/reviewer/download/${articleId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                reviewer_email: currentReviewerEmail
            })
        });
        
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `makale_${articleId}_anonim.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    } catch (error) {
        console.error('Hata:', error);
        alert('Makale indirilirken bir hata oluştu.');
    }
}

// Yardımcı fonksiyonlar
function getStatusBadgeClass(status) {
    const statusMap = {
        'pending': 'badge-pending',
        'accepted': 'badge-approved',
        'rejected': 'badge-rejected',
        'revision': 'badge-pending'
    };
    return statusMap[status] || 'badge-pending';
}