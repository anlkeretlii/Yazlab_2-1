const API_BASE_URL = 'http://localhost:5000/api';

// Seçili hakem bilgileri
let selectedReviewer = null;

// Sayfa yüklendiğinde çalışacak kodlar
window.onload = function() {
    console.log('Sayfa yüklendi');
    

    const reviewerEmail = localStorage.getItem('reviewerEmail');
    if (reviewerEmail) {
        window.location.href = 'reviewer_dashboard.html';
        return;
    }

    // Giriş butonunu devre dışı bırak
    const loginButton = document.getElementById('loginButton');
    if (loginButton) {
        loginButton.disabled = true;
    }
};

// Hakem seçme fonksiyonu
window.selectReviewer = function(username, email, reviewerId) {
    console.log('Hakem seçildi:', username);
    
    try {
        // Önceki seçili kartın seçimini kaldır
        const cards = document.querySelectorAll('.reviewer-card');
        cards.forEach(card => card.classList.remove('selected'));
        
        // Tıklanan kartı seç
        const selectedCard = event.currentTarget;
        selectedCard.classList.add('selected');
        
        // Seçilen hakem bilgilerini kaydet
        selectedReviewer = {
            username: username,
            email: email,
            reviewerId: reviewerId
        };
        
        // Giriş butonunu aktif et
        const loginButton = document.getElementById('loginButton');
        if (loginButton) {
            loginButton.disabled = false;
        }
    } catch (error) {
        console.error('Hakem seçme hatası:', error);
        alert('Hakem seçilirken bir hata oluştu. Lütfen sayfayı yenileyip tekrar deneyin.');
    }
};

// Giriş yapma fonksiyonu
window.login = async function() {
    console.log('Giriş denemesi başlatıldı');
    
    try {
        if (!selectedReviewer) {
            alert('Lütfen bir hakem seçin.');
            return;
        }

        // Giriş butonunu devre dışı bırak
        const loginButton = document.getElementById('loginButton');
        if (loginButton) {
            loginButton.disabled = true;
            loginButton.textContent = 'Giriş yapılıyor...';
        }

        console.log('API isteği gönderiliyor...');
        const response = await fetch(`${API_BASE_URL}/reviewer/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({
                email: selectedReviewer.email
            })
        });
        
        if (response.ok) {
            console.log('Giriş başarılı');
            // Hakem bilgilerini localStorage'a kaydet
            localStorage.setItem('reviewerEmail', selectedReviewer.email);
            localStorage.setItem('reviewerName', selectedReviewer.username);
            localStorage.setItem('reviewerId', selectedReviewer.reviewerId);
            
            // Hakem paneline yönlendir
            window.location.href = 'reviewer_dashboard.html';
        } else {
            const data = await response.json();
            throw new Error(data.message || 'Giriş başarısız. Lütfen bilgilerinizi kontrol edin.');
        }
    } catch (error) {
        console.error('Giriş hatası:', error);
        alert(error.message || 'Giriş yapılırken bir hata oluştu. Lütfen tekrar deneyin.');
        
        // Giriş butonunu tekrar aktif et
        const loginButton = document.getElementById('loginButton');
        if (loginButton) {
            loginButton.disabled = false;
            loginButton.textContent = 'Giriş Yap';
        }
    }
}; 