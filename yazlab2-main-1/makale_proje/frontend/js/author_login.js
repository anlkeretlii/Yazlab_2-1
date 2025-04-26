// Form işleme kodları
document.addEventListener('DOMContentLoaded', () => {
    // Form elementlerini seç
    const form = document.querySelector('#trackingForm');
    const trackingInput = document.querySelector('#trackingCode');
    const submitButton = document.querySelector('#submitButton');
    const resultArea = document.querySelector('#resultArea');
    const articleDetails = document.querySelector('#articleDetails');

  
    if (!form || !trackingInput || !submitButton || !resultArea || !articleDetails) {
        console.error('Gerekli form elementleri bulunamadı!');
        return;
    }

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const trackingCode = trackingInput.value.trim();
        
        if (!trackingCode) {
            showError('Lütfen takip numarası giriniz.');
            return;
        }

        submitButton.disabled = true;
        submitButton.textContent = 'Sorgulanıyor...';

        try {
            // API isteği
            const response = await fetch(`http://localhost:5000/api/track/${trackingCode}`);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.message || 'Makale bulunamadı');
            }

            // Başarılı sonuç göster
            showResult(data);

        } catch (error) {
            showError(error.message);
        } finally {
            // Butonu tekrar aktif et
            submitButton.disabled = false;
            submitButton.textContent = 'Sorgula';
        }
    });

    // Hata mesajı göster
    function showError(message) {
        resultArea.classList.remove('d-none');
        articleDetails.innerHTML = `
            <div class="alert alert-danger">
                ${message}
            </div>
        `;
    }

    // Sonuç göster
    function showResult(data) {
        resultArea.classList.remove('d-none');
        
        // Değerlendirmeleri hazırla
        let reviewsHtml = '<p>Henüz değerlendirme yapılmamış.</p>';
        
        if (data.reviews && data.reviews.length > 0) {
            reviewsHtml = `
                <div class="list-group mt-3">
                    ${data.reviews.map(review => `
                        <div class="list-group-item">
                            <div class="d-flex justify-content-between align-items-center">
                                <h6 class="mb-1">${review.reviewer_name || 'Hakem'}</h6>
                                <small class="text-muted">${new Date(review.review_date).toLocaleDateString('tr-TR')}</small>
                            </div>
                            <p class="mb-1"><strong>Karar:</strong> ${review.decision}</p>
                            <p class="mb-1"><strong>Değerlendirme:</strong> ${review.comments}</p>
                        </div>
                    `).join('')}
                </div>
            `;
        }

        articleDetails.innerHTML = `
            <div class="card">
                <div class="card-body">
                    <h5 class="card-title">${data.title}</h5>
                    <div class="card-text">
                        <p>
                            <strong>Durum:</strong> ${data.status}<br>
                            <strong>Yükleme Tarihi:</strong> ${new Date(data.upload_date).toLocaleDateString('tr-TR')}<br>
                            <strong>Takip Kodu:</strong> ${data.tracking_code}
                        </p>
                        
                        <div class="mt-4">
                            <h6 class="mb-3">Hakem Değerlendirmeleri</h6>
                            ${reviewsHtml}
                        </div>
                    </div>
                    <div class="mt-3">
                        <button type="button" class="btn btn-primary" onclick="window.location.reload()">Yeni Sorgu</button>
                    </div>
                </div>
            </div>
        `;

        // Debug için konsola yazdır
        console.log('Makale verileri:', data);
        console.log('Değerlendirmeler:', data.reviews);
    }
}); 