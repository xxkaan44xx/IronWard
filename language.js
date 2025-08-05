// IronWard Dashboard - Dil Yönetimi Sistemi

class LanguageManager {
    constructor() {
        this.currentLanguage = localStorage.getItem('dashboard_language') || 'tr';
        this.translations = {
            'tr': {
                // Genel
                'dashboard': 'Anasayfa',
                'guilds': 'Sunucular',
                'moderation': 'Moderasyon',
                'analytics': 'Analizler',
                'live_monitoring': 'Canlı İzleme',
                'settings': 'Ayarlar',
                'invite_bot': 'Botu Davet Et',
                'language': 'Dil',
                'admin': 'Admin',
                'logout': 'Çıkış Yap',

                // İstatistikler
                'total_servers': 'Toplam Sunucu',
                'total_warnings': 'Toplam Uyarı',
                'active_bans': 'Aktif Banlar',
                'active_mutes': 'Aktif Susturma',

                // Butonlar
                'view_details': 'Detayları Görüntüle',
                'edit_settings': 'Ayarları Düzenle',
                'save': 'Kaydet',
                'cancel': 'İptal',
                'delete': 'Sil',

                // Mesajlar
                'loading': 'Yükleniyor...',
                'no_data': 'Veri bulunmuyor',
                'success': 'Başarılı!',
                'error': 'Hata oluştu!',

                // AI Assistant
                'ai_assistant': 'AI Asistan',

                // Settings Page
                'dashboard_settings': 'Dashboard Ayarları',
                'settings_description': 'Dashboard tercihlerinizi ve genel ayarları yönetin',
                'general_settings': 'Genel Ayarlar',
                'notification_settings': 'Bildirim Ayarları',
                'appearance_settings': 'Görünüm Ayarları',
                'performance_settings': 'Performans Ayarları',
                'theme': 'Tema',
                'dark_theme': 'Koyu Tema',
                'light_theme': 'Açık Tema',
                'auto_theme': 'Otomatik',
                'timezone': 'Zaman Dilimi',
                'date_format': 'Tarih Formatı',
                'auto_refresh': 'Otomatik Yenileme',
                'items_per_page': 'Sayfa Başına Öğe',
                'show_animations': 'Animasyonları Göster',
                'compact_mode': 'Kompakt Mod',
                'save_settings': 'Ayarları Kaydet',
                'reset_settings': 'Sıfırla',
                'notification_preferences': 'Bildirim Tercihleri',
                'notify_warnings': 'Yeni uyarılar için bildirim',
                'notify_bans': 'Yeni banlar için bildirim',
                'notify_bot_offline': 'Bot çevrimdışı bildirimi',
                'test_notification': 'Test Bildirimi'
            },
            'en': {
                // General
                'dashboard': 'Dashboard',
                'guilds': 'Servers',
                'moderation': 'Moderation',
                'analytics': 'Analytics',
                'live_monitoring': 'Live Monitoring',
                'settings': 'Settings',
                'invite_bot': 'Invite Bot',
                'language': 'Language',
                'admin': 'Admin',
                'logout': 'Logout',

                // Statistics
                'total_servers': 'Total Servers',
                'total_warnings': 'Total Warnings',
                'active_bans': 'Active Bans',
                'active_mutes': 'Active Mutes',

                // Buttons
                'view_details': 'View Details',
                'edit_settings': 'Edit Settings',
                'save': 'Save',
                'cancel': 'Cancel',
                'delete': 'Delete',

                // Messages
                'loading': 'Loading...',
                'no_data': 'No data found',
                'success': 'Success!',
                'error': 'Error occurred!',

                // AI Assistant
                'ai_assistant': 'AI Assistant',

                // Settings Page
                'dashboard_settings': 'Dashboard Settings',
                'settings_description': 'Manage your dashboard preferences and general settings',
                'general_settings': 'General Settings',
                'notification_settings': 'Notification Settings',
                'appearance_settings': 'Appearance Settings',
                'performance_settings': 'Performance Settings',
                'theme': 'Theme',
                'dark_theme': 'Dark Theme',
                'light_theme': 'Light Theme',
                'auto_theme': 'Auto',
                'timezone': 'Timezone',
                'date_format': 'Date Format',
                'auto_refresh': 'Auto Refresh',
                'items_per_page': 'Items Per Page',
                'show_animations': 'Show Animations',
                'compact_mode': 'Compact Mode',
                'save_settings': 'Save Settings',
                'reset_settings': 'Reset',
                'notification_preferences': 'Notification Preferences',
                'notify_warnings': 'Notify for new warnings',
                'notify_bans': 'Notify for new bans',
                'notify_bot_offline': 'Bot offline notification',
                'test_notification': 'Test Notification'
            }
        };

        this.init();
    }

    init() {
        this.updateLanguageIndicator();
        this.translatePage();
    }

    changeLanguage(lang) {
        if (this.translations[lang]) {
            this.currentLanguage = lang;
            localStorage.setItem('dashboard_language', lang);
            this.updateLanguageIndicator();
            this.translatePage();

            // Save to server settings if possible
            this.saveLanguageToServer(lang);

            // Trigger custom event for other components
            window.dispatchEvent(new CustomEvent('languageChanged', { 
                detail: { language: lang } 
            }));

            // Show success message
            this.showLanguageChangeMessage(lang);
        }
    }

    async saveLanguageToServer(lang) {
        try {
            // Get current settings first
            const currentResponse = await fetch('/api/settings/general');
            const currentSettings = await currentResponse.json();

            // Update language setting
            const updatedSettings = {
                ...currentSettings,
                language: lang
            };

            // Save to server
            await fetch('/api/settings/general', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(updatedSettings)
            });
        } catch (error) {
            console.error('Dil ayarı sunucuya kaydedilirken hata:', error);
        }
    }

    showLanguageChangeMessage(lang) {
        const message = lang === 'tr' ? 
            'Dil Türkçe olarak değiştirildi!' : 
            'Language changed to English!';
        
        // Create temporary notification
        const notification = document.createElement('div');
        notification.className = 'alert alert-success alert-dismissible fade show position-fixed';
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        // Auto remove after 3 seconds
        setTimeout(() => {
            notification.remove();
        }, 3000);
    }

    updateLanguageIndicator() {
        const indicator = document.getElementById('current-language');
        if (indicator) {
            indicator.textContent = this.currentLanguage.toUpperCase();
        }
    }

    translatePage() {
        const texts = this.translations[this.currentLanguage];
        if (!texts) return;

        // Translate elements with data-translate attribute
        document.querySelectorAll('[data-translate]').forEach(element => {
            const key = element.getAttribute('data-translate');
            if (texts[key]) {
                element.textContent = texts[key];
            }
        });

        // Translate placeholders
        document.querySelectorAll('[data-translate-placeholder]').forEach(element => {
            const key = element.getAttribute('data-translate-placeholder');
            if (texts[key]) {
                element.placeholder = texts[key];
            }
        });

        // Update page title
        const titleElement = document.querySelector('title');
        if (titleElement) {
            const titleKey = titleElement.getAttribute('data-translate');
            if (titleKey && texts[titleKey]) {
                titleElement.textContent = texts[titleKey];
            }
        }
    }

    getText(key) {
        const texts = this.translations[this.currentLanguage];
        return texts[key] || key;
    }

    getCurrentLanguage() {
        return this.currentLanguage;
    }
}

// Global instance
window.languageManager = new LanguageManager();

// Global functions for backward compatibility
function changeLanguage(lang) {
    window.languageManager.changeLanguage(lang);
}

function getText(key) {
    return window.languageManager.getText(key);
}