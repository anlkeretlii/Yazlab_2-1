// API temel URL'i
const API_BASE_URL = 'http://localhost:5000/api';

// Global state
let state = {
    articles: [],
    auditLogs: [],
    uploadedArticles: [],
    currentArticleId: null,
    isLoading: false
};

// DOM elementlerini yükle ve event listener'ları ekle
function initializeElements() {
    const elements = {
        articlesList: document.getElementById('articlesList'),
        auditLogsTableBody: document.getElementById('auditLogsTableBody'),
        uploadedArticlesList: document.getElementById('uploadedArticlesTableBody'),
        searchInput: document.getElementById('searchInput'),
        statusFilter: document.getElementById('statusFilter'),
        sortOption: document.getElementById('sortOption'),
        loadingIndicator: document.getElementById('loadingIndicator'),
        errorContainer: document.getElementById('errorContainer')
    };

    // Event listeners for filters
    elements.searchInput?.addEventListener('input', () => filterAndDisplayArticles());
    elements.statusFilter?.addEventListener('change', () => filterAndDisplayArticles());
    elements.sortOption?.addEventListener('change', () => filterAndDisplayArticles());

    return elements;
}

// Loading göstergesi
function setLoading(isLoading) {
    state.isLoading = isLoading;
    const loadingIndicator = document.getElementById('loadingIndicator');
    if (loadingIndicator) {
        loadingIndicator.style.display = isLoading ? 'block' : 'none';
    }
}

// Hata mesajını göster
function showError(message, isTemporary = true) {
    console.error(message);
    const errorContainer = document.getElementById('errorContainer');
    if (!errorContainer) return;

    const alertDiv = document.createElement('div');
    alertDiv.className = 'alert alert-danger alert-dismissible fade show mt-3';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;
    
    errorContainer.appendChild(alertDiv);

    if (isTemporary) {
        setTimeout(() => {
            alertDiv.remove();
        }, 5000);
    }
}

// Makaleleri yükle
async function loadArticles() {
    try {
        setLoading(true);
        console.log('Makaleleri yüklüyorum...');
        
        const response = await fetch(`${API_BASE_URL}/articles`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const articles = await response.json();
        console.log('Makaleler başarıyla yüklendi:', articles);
        
        // Normalize article data
        state.articles = articles.map(article => ({
            id: article.id,
            title: article.title,
            status: normalizeStatus(article.status),
            submission_date: article.upload_date || article.submission_date,
            author: article.author || 'Bilinmiyor'
        }));

        displayArticles(state.articles);
    } catch (error) {
        console.error('Makaleler yüklenirken hata:', error);
        // Hata popup'ını kaldırdık, sadece konsola loglama yapıyoruz
    } finally {
        setLoading(false);
    }
}

// Logları yükle
async function loadAuditLogs() {
    try {
        setLoading(true);
        console.log('Logları yüklüyorum...');
        
        const response = await fetch(`${API_BASE_URL}/admin/audit-logs`, {
            method: 'GET',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const logs = await response.json();
        console.log('Loglar başarıyla yüklendi:', logs);
        
        state.auditLogs = logs;
        displayAuditLogs(logs);
    } catch (error) {
        // Sadece konsola loglama yap, kullanıcıya hata gösterme
        console.error('Loglar yüklenirken hata:', error);
    } finally {
        setLoading(false);
    }
}

// Durum değerlerini normalize et
function normalizeStatus(status) {
    const statusMap = {
        'Kabul Edildi': 'Onaylandı',
        'Reddedildi': 'Onaylanmadı',
        'Değerlendirildide': 'Değerlendiriliyor',
        'Onay Bekliyor': 'Beklemede'
    };
    return statusMap[status] || status;
}

// Makaleleri filtrele ve göster
function filterAndDisplayArticles() {
    const searchInput = document.getElementById('searchInput');
    const statusFilter = document.getElementById('statusFilter');
    const sortOption = document.getElementById('sortOption');

    if (!searchInput || !statusFilter || !sortOption) return;

    const searchTerm = searchInput.value.toLowerCase();
    const statusValue = statusFilter.value;
    const sortValue = sortOption.value;
    
    let filteredArticles = state.articles.filter(article => {
        const matchesSearch = article.title.toLowerCase().includes(searchTerm);
        const matchesStatus = !statusValue || article.status === statusValue;
        return matchesSearch && matchesStatus;
    });
    
    // Sıralama
    filteredArticles.sort((a, b) => {
        const dateA = new Date(a.submission_date);
        const dateB = new Date(b.submission_date);
        
        switch (sortValue) {
            case 'date_desc':
                return dateB - dateA;
            case 'date_asc':
                return dateA - dateB;
            case 'title_asc':
                return a.title.localeCompare(b.title);
            case 'title_desc':
                return b.title.localeCompare(a.title);
            default:
                return 0;
        }
    });
    
    displayArticles(filteredArticles);
}

// Makaleleri tabloda göster
function displayArticles(articles) {
    const tableBody = document.getElementById('articlesList');
    if (!tableBody) return;

    tableBody.innerHTML = '';
    
    articles.forEach(article => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${article.id}</td>
            <td>${article.title}</td>
            <td><span class="badge bg-${getStatusBadgeColor(article.status)}">${article.status}</span></td>
            <td>${formatDate(article.submission_date)}</td>
            <td>
                <div class="btn-group" role="group">
                    <button class="btn btn-sm btn-info" onclick="viewArticleDetails(${article.id})">
                        <i class="fas fa-eye"></i> Detaylar
                    </button>
                    <button class="btn btn-sm btn-primary" onclick="downloadArticle(${article.id})">
                        <i class="fas fa-download"></i> İndir
                    </button>
                </div>
            </td>
        `;
        tableBody.appendChild(row);
    });
}

// Logları tabloda göster
function displayAuditLogs(logs) {
    const tableBody = document.getElementById('auditLogsTableBody');
    if (!tableBody) {
        console.error('Log tablosu bulunamadı');
        return;
    }

    tableBody.innerHTML = '';
    
    if (logs.length === 0) {
        const emptyRow = document.createElement('tr');
        emptyRow.innerHTML = '<td colspan="4" class="text-center">Log kaydı bulunamadı</td>';
        tableBody.appendChild(emptyRow);
        return;
    }

    // Logları tarihe göre sırala (en yeni en üstte)
    logs.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

    logs.forEach(log => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${formatDate(log.timestamp)}</td>
            <td>${log.article_id}</td>
            <td>${log.action}</td>
            <td>${log.details || '-'}</td>
        `;
        tableBody.appendChild(row);
    });
}

// Tarihi formatla
function formatDate(dateString) {
    if (!dateString) return '-';
    
    try {
        const date = new Date(dateString);
        if (isNaN(date.getTime())) {
            return dateString;
        }
        return date.toLocaleString('tr-TR');
    } catch (error) {
        console.error('Tarih formatlanırken hata:', error);
        return dateString;
    }
}

// Durum badge rengi
function getStatusBadgeColor(status) {
    const colors = {
        'Onay Bekliyor': 'primary',
        'Onaylanmadı': 'danger',
        'Onaylandı': 'success',
        'Değerlendiriliyor': 'info',
        'Değerlendirildi': 'warning'
    };
    return colors[status] || 'secondary';
}

// Modal işlemleri
function openAnonymizeModal(articleId) {
    state.currentArticleId = articleId;
    const modal = new bootstrap.Modal(document.getElementById('anonymizeModal'));
    if (modal) {
        modal.show();
    }
}

function openAssignReviewerModal(articleId) {
    state.currentArticleId = articleId;
    const modal = new bootstrap.Modal(document.getElementById('assignReviewerModal'));
    if (modal) {
        modal.show();
    }
}

// Modal event listener'ları
function setupModalEventListeners() {
    // Anonymize button
    const anonymizeButton = document.getElementById('anonymizeButton');
    if (anonymizeButton) {
        anonymizeButton.addEventListener('click', handleAnonymize);
    }

    // Assign reviewer button
    const assignReviewerButton = document.getElementById('assignReviewerButton');
    if (assignReviewerButton) {
        assignReviewerButton.addEventListener('click', handleAssignReviewer);
    }

    // Test reviewer button
    const addTestReviewerBtn = document.getElementById('addTestReviewerBtn');
    if (addTestReviewerBtn) {
        addTestReviewerBtn.addEventListener('click', handleAddTestReviewer);
    }
}

// Modal işlem fonksiyonları
async function handleAnonymize() {
    if (!state.currentArticleId) return;
    
    const sensitiveInfo = [];
    ['authorCheck', 'institutionCheck', 'emailCheck'].forEach(id => {
        const checkbox = document.getElementById(id);
        if (checkbox?.checked) {
            sensitiveInfo.push(id.replace('Check', ''));
        }
    });
    
    try {
        setLoading(true);
        const response = await fetch(`${API_BASE_URL}/admin/anonymize/${state.currentArticleId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            credentials: 'same-origin',
            body: JSON.stringify({ sensitive_info: sensitiveInfo })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            const modal = bootstrap.Modal.getInstance(document.getElementById('anonymizeModal'));
            if (modal) modal.hide();
            
            showError('Makale başarıyla anonimleştirildi.', true);
            await loadArticles();
        }
    } finally {
        setLoading(false);
    }
}

async function handleAssignReviewer() {
    if (!state.currentArticleId) return;
    
    const reviewerEmail = document.getElementById('reviewerEmail')?.value;
    if (!reviewerEmail) {
        showError('Lütfen hakem e-posta adresini girin.');
        return;
    }
    
    try {
        setLoading(true);
        const response = await fetch(`${API_BASE_URL}/admin/assign-reviewer`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            credentials: 'same-origin',
            body: JSON.stringify({
                article_id: state.currentArticleId,
                reviewer_email: reviewerEmail
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            const modal = bootstrap.Modal.getInstance(document.getElementById('assignReviewerModal'));
            if (modal) modal.hide();
            
            showError('Hakem başarıyla atandı.', true);
            await loadArticles();
        } else {
            throw new Error(data.message || 'Hakem atama işlemi başarısız oldu');
        }
    } catch (error) {
        console.error('Hakem atama hatası:', error);
        showError('Hakem atama işlemi sırasında bir hata oluştu: ' + error.message);
    } finally {
        setLoading(false);
    }
}

async function handleAddTestReviewer() {
    const confirmAdd = confirm('Test hakemlerini eklemek istiyor musunuz? Bu işlem mevcut tüm makalelere test hakemlerini atayacaktır.');
    if (!confirmAdd) return;
    
    const button = document.getElementById('addTestReviewerBtn');
    if (!button) return;
    
    try {
        button.disabled = true;
        button.textContent = 'Ekleniyor...';
        setLoading(true);
        
        const response = await fetch(`${API_BASE_URL}/admin/add-test-reviewer`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showError(data.message || 'Test hakemler başarıyla eklendi', true);
            await loadArticles();
        } else {
            throw new Error(data.message || 'Test hakem ekleme işlemi başarısız oldu');
        }
    } catch (error) {
        console.error('Test hakem ekleme hatası:', error);
        showError('Test hakem eklenirken bir hata oluştu: ' + error.message);
    } finally {
        if (button) {
            button.disabled = false;
            button.textContent = 'Test Hakem Ekle';
        }
        setLoading(false);
    }
}

// Makale detaylarını göster
async function viewArticleDetails(articleId) {
    try {
        const response = await fetch(`${API_BASE_URL}/articles/${articleId}`);
        if (!response.ok) {
            throw new Error('Makale detayları alınamadı');
        }
        
        const article = await response.json();
        
        // Modal içeriğini oluştur
        const modalContent = `
            <div class="modal fade" id="articleDetailModal" tabindex="-1">
                <div class="modal-dialog modal-lg">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Makale Detayları</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <div class="mb-3">
                                <h6>Başlık:</h6>
                                <p>${article.title}</p>
                            </div>
                            <div class="mb-3">
                                <h6>Yazar:</h6>
                                <p>${article.author}</p>
                            </div>
                            <div class="mb-3">
                                <h6>Kurum:</h6>
                                <p>${article.institution || 'Belirtilmemiş'}</p>
                            </div>
                            <div class="mb-3">
                                <h6>Anahtar Kelimeler:</h6>
                                <p>${article.keywords || 'Belirtilmemiş'}</p>
                            </div>
                            <div class="mb-3">
                                <h6>Durum:</h6>
                                <p><span class="badge bg-${getStatusBadgeColor(article.status)}">${article.status}</span></p>
                            </div>
                            <div class="mb-3">
                                <h6>Yükleme Tarihi:</h6>
                                <p>${formatDate(article.submission_date)}</p>
                            </div>
                        </div>
                        <div class="modal-footer" id="modalActions">
                            ${generateActionButtons(article)}
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        // Varsa eski modalı kaldır
        const oldModal = document.getElementById('articleDetailModal');
        if (oldModal) {
            oldModal.remove();
        }
        
        // Yeni modalı ekle ve göster
        document.body.insertAdjacentHTML('beforeend', modalContent);
        const modal = new bootstrap.Modal(document.getElementById('articleDetailModal'));
        modal.show();
        
        // Buton event listener'ları ekle
        setupModalButtons(article);
        
    } catch (error) {
        showError('Makale detayları yüklenirken bir hata oluştu: ' + error.message);
    }
}

// Durum bazlı aksiyon butonlarını oluştur
function generateActionButtons(article) {
    const buttons = [];
    
    // Her durumda olacak butonlar
    buttons.push(`<button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Geri Dön</button>`);
    buttons.push(`
        <button class="btn btn-outline-primary" onclick="downloadArticle(${article.id}, 'original')">
            <i class="fas fa-download"></i> Makaleyi İndir
        </button>
    `);
    
    // Durum bazlı butonlar
    if (article.status === 'Beklemede') {
        buttons.push(`<button type="button" class="btn btn-success" onclick="approveArticle(${article.id})">Onay Ver</button>`);
        buttons.push(`<button type="button" class="btn btn-danger" onclick="rejectArticle(${article.id})">Reddet</button>`);
    } else if (article.status === 'Onaylandı') {
        buttons.push(`<button type="button" class="btn btn-warning" onclick="anonymizeArticle(${article.id})">Anonimleştir</button>`);
    } else if (article.status === 'Değerlendiriliyor') {
        buttons.push(`<button type="button" class="btn btn-primary" onclick="openAssignReviewerModal(${article.id})">Hakem Ata</button>`);
    }
    
    return buttons.join('');
}

// Modal butonları için event listener'ları
function setupModalButtons(article) {
    // Event listener'lar burada eklenecek
}

// Makaleyi indir
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

// Makaleyi onayla
async function approveArticle(articleId) {
    try {
        const response = await fetch(`${API_BASE_URL}/admin/approve/${articleId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) throw new Error('Onaylama işlemi başarısız');
        
        showError('Makale başarıyla onaylandı', true);
        await loadArticles(); // Listeyi güncelle
        
        // Modalı yeniden yükle
        viewArticleDetails(articleId);
    } catch (error) {
        showError('Onaylama işlemi sırasında bir hata oluştu: ' + error.message);
    }
}

// Makaleyi reddet
async function rejectArticle(articleId) {
    try {
        const response = await fetch(`${API_BASE_URL}/admin/reject/${articleId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (!response.ok) throw new Error('Reddetme işlemi başarısız');
        
        showError('Makale reddedildi', true);
        await loadArticles(); // Listeyi güncelle
        
        // Modalı kapat
        const modal = bootstrap.Modal.getInstance(document.getElementById('articleDetailModal'));
        if (modal) modal.hide();
    } catch (error) {
        showError('Reddetme işlemi sırasında bir hata oluştu: ' + error.message);
    }
}

// Hakem atama modalını aç
function openAssignReviewerModal(articleId) {
    const modalHtml = `
        <div class="modal fade" id="assignReviewerModal" tabindex="-1">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title">Hakem Ata</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                    </div>
                    <div class="modal-body">
                        <div class="mb-3">
                            <label for="reviewerEmail" class="form-label">Hakem E-posta Adresi</label>
                            <input type="email" class="form-control" id="reviewerEmail" required>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">İptal</button>
                        <button type="button" class="btn btn-primary" onclick="assignReviewer(${articleId})">Ata</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Varsa eski modalı kaldır
    const oldModal = document.getElementById('assignReviewerModal');
    if (oldModal) {
        oldModal.remove();
    }
    
    // Yeni modalı ekle ve göster
    document.body.insertAdjacentHTML('beforeend', modalHtml);
    const modal = new bootstrap.Modal(document.getElementById('assignReviewerModal'));
    modal.show();
}

// Hakem ata
async function assignReviewer(articleId) {
    const reviewerEmail = document.getElementById('reviewerEmail').value;
    if (!reviewerEmail) {
        showError('Lütfen hakem e-posta adresini girin');
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
        
        if (!response.ok) throw new Error('Hakem atama işlemi başarısız');
        
        showError('Hakem başarıyla atandı', true);
        await loadArticles(); // Listeyi güncelle
        
        // Modalları kapat
        const assignModal = bootstrap.Modal.getInstance(document.getElementById('assignReviewerModal'));
        if (assignModal) assignModal.hide();
        
        const detailModal = bootstrap.Modal.getInstance(document.getElementById('articleDetailModal'));
        if (detailModal) detailModal.hide();
    } catch (error) {
        showError('Hakem atama işlemi sırasında bir hata oluştu: ' + error.message);
    }
}

// Makaleyi anonimleştir
async function anonymizeArticle(articleId) {
    try {
        const response = await fetch(`${API_BASE_URL}/admin/anonymize/${articleId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        });
        
        if (response.ok) {
            showError('Makale başarıyla anonimleştirildi', true);
            await loadArticles(); // Listeyi güncelle
            viewArticleDetails(articleId); // Modalı yeniden yükle
        }
    } catch (error) {
        // Hata durumunda sadece konsola log at, kullanıcıya gösterme
        console.error('Anonimleştirme işlemi hatası:', error);
    }
}


document.addEventListener('DOMContentLoaded', async () => {
    console.log('Sayfa yükleniyor...');
    initializeElements();
    setupModalEventListeners();
    await Promise.all([
        loadArticles(),
        loadAuditLogs()
    ]);
});
