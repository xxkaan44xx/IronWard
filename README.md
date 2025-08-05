# Discord Moderation Bot 🛡️

Türkçe dil desteği ile kapsamlı bir Discord moderasyon botu. Sunucu yönetiminde ihtiyacınız olan tüm araçları sağlar.

## 🌟 Özellikler

### 🔨 Temel Moderasyon
- **Ban/Unban** - Kullanıcıları yasaklama ve yasağı kaldırma
- **Kick** - Kullanıcıları sunucudan atma
- **Mute/Unmute** - Kullanıcıları susturma (zaman sınırlı)
- **Warn** - Kullanıcıları uyarma sistemi
- **Timeout** - Discord'un yerleşik timeout özelliği

### ⚡ Gelişmiş Moderasyon
- **Temporary Ban** - Belirli süreliğine yasaklama
- **Softban** - Mesajları temizleyerek yasaklama
- **Voice Kick/Move** - Ses kanalı yönetimi
- **Nickname** - Kullanıcı adlarını değiştirme
- **Purge** - Mesaj temizleme (genel ve kullanıcı bazlı)

### 📝 Kanal Yönetimi
- **Lock/Unlock** - Kanal kilitleme
- **Slowmode** - Yavaş mod ayarlama
- **Hide/Show Channel** - Kanal görünürlük ayarları
- **Create/Delete/Clone** - Kanal oluşturma ve yönetimi
- **Pin/Unpin Messages** - Mesaj sabitleme
- **Voice Channel Control** - Ses kanalı kilitleme

### 👥 Rol Yönetimi
- **Give/Take Role** - Rol verme ve alma
- **Create/Delete Role** - Rol oluşturma ve silme
- **Role Info** - Rol bilgilerini görüntüleme
- **Role Stats** - Rol dağılım istatistikleri
- **Mass Role** - Toplu rol işlemleri
- **Role Color** - Rol rengi değiştirme

### 🤖 Otomatik Moderasyon
- **Anti-Spam** - Spam koruması
- **Anti-Flood** - Çoklu mesaj engelleme
- **Anti-Link** - Link filtresi
- **Anti-Invite** - Sunucu davet linki engelleme
- **Caps Filter** - Büyük harf spam engelleme
- **Emoji Filter** - Emoji spam engelleme
- **Word Filter** - Kötü kelime filtresi

### 📊 Loglama & Raporlama
- **Mod Logs** - Moderasyon geçmişi
- **Ban List** - Yasaklı kullanıcılar listesi
- **Reports** - Kullanıcı raporlama sistemi
- **Audit Log** - Sunucu aktivite günlüğü

### 🛠️ Sunucu Ayarları
- **Prefix** - Komut ön eki ayarlama
- **Language** - Dil seçimi (TR/EN)
- **Welcome/Goodbye** - Karşılama mesajları
- **Log Channel** - Log kanalı ayarlama
- **Mute Role** - Susturma rolü ayarlama

### ℹ️ Bilgi & Yardımcı
- **User Info** - Kullanıcı bilgileri
- **Server Info** - Sunucu bilgileri
- **Avatar** - Avatar görüntüleme
- **Help** - Komut yardımı
- **Ping** - Bot gecikme bilgisi

## 🚀 Kurulum

### 1. Discord Bot Oluşturma
1. [Discord Developer Portal](https://discord.com/developers/applications)'a gidin
2. "New Application" butonuna tıklayın
3. Bot adını girin ve oluşturun
4. "Bot" sekmesine gidin
5. "Reset Token" yapın ve tokeni kopyalayın

### 2. Bot İzinleri
Botunuz için gerekli izinler:
- Manage Roles
- Manage Channels
- Manage Messages
- Ban Members
- Kick Members
- Mute Members
- View Audit Log
- Send Messages
- Embed Links
- Read Message History

### 3. Token Ayarlama
```bash
# Replit Secrets'a ekleyin:
DISCORD_BOT_TOKEN=your_bot_token_here
```

### 4. Botu Çalıştırma
Replit'te "Run" butonuna tıklayın veya:
```bash
python main.py
```

## 📖 Komut Listesi

### Temel Moderasyon
```
!ban [@kullanıcı] [sebep] - Kullanıcıyı yasakla
!unban [kullanıcı#tag] - Yasağı kaldır
!kick [@kullanıcı] [sebep] - Kullanıcıyı at
!mute [@kullanıcı] [süre] [sebep] - Kullanıcıyı sustur
!unmute [@kullanıcı] - Susturmayı kaldır
!warn [@kullanıcı] [sebep] - Kullanıcıyı uyar
!warnings [@kullanıcı] - Uyarıları göster
!clearwarns [@kullanıcı] - Uyarıları temizle
```

### Gelişmiş Moderasyon
```
!tempban [@kullanıcı] [süre] [sebep] - Geçici yasak
!softban [@kullanıcı] [sebep] - Soft yasak
!timeout [@kullanıcı] [süre] [sebep] - Timeout
!untimeout [@kullanıcı] - Timeout kaldır
!nickname [@kullanıcı] [yeni_ad] - Ad değiştir
!voicekick [@kullanıcı] - Ses kanalından at
!voicemove [@kullanıcı] [kanal] - Kullanıcıyı taşı
```

### Mesaj Yönetimi
```
!purge [sayı] - Mesaj sil
!purgeuser [@kullanıcı] [sayı] - Kullanıcının mesajlarını sil
!lock [kanal] - Kanalı kilitle
!unlock [kanal] - Kilit aç
!slowmode [saniye] - Yavaş mod
```

### Rol Yönetimi
```
!giverole [@kullanıcı] [rol] - Rol ver
!takerole [@kullanıcı] [rol] - Rol al
!createrole [ad] [renk] - Rol oluştur
!deleterole [rol] - Rol sil
!roleinfo [rol] - Rol bilgisi
!rolestats - Rol istatistikleri
```

### Ayarlar
```
!setlanguage [tr/en] - Dil ayarla
!setprefix [prefix] - Prefix ayarla
!setlogchannel [#kanal] - Log kanalı
!setmuterole [rol] - Mute rolü
!setwelcome [#kanal] - Karşılama kanalı
```

### Otomatik Moderasyon
```
!antispam [aç/kapat] - Spam koruması
!antilink [aç/kapat] - Link filtresi
!antiinvite [aç/kapat] - Davet linki filtresi
!autoban [kelime] - Yasaklı kelime ekle
```

## 🔧 Konfigürasyon

Bot ilk kurulumda varsayılan ayarlarla gelir:
- **Dil**: Türkçe
- **Prefix**: `!`
- **Otomatik moderasyon**: Kapalı

Bu ayarları `!settings` komutu ile değiştirebilirsiniz.

## 📁 Proje Yapısı

```
discord-moderation-bot/
├── main.py                 # Ana başlatma dosyası
├── bot.py                  # Bot sınıfı ve temel yapı
├── database.py             # SQLite veritabanı işlemleri
├── cogs/                   # Bot komut modülleri
│   ├── moderation.py       # Temel moderasyon komutları
│   ├── advanced_moderation.py # Gelişmiş moderasyon
│   ├── automod.py          # Otomatik moderasyon
│   ├── settings.py         # Sunucu ayarları
│   ├── utility.py          # Yardımcı komutlar
│   ├── logging.py          # Loglama sistemi
│   ├── channel_management.py # Kanal yönetimi
│   └── role_management.py  # Rol yönetimi
├── utils/                  # Yardımcı modüller
│   ├── embeds.py          # Embed oluşturma
│   ├── helpers.py         # Genel yardımcı fonksiyonlar
│   └── permissions.py     # İzin kontrolleri
└── languages/             # Dil dosyaları
    ├── tr.json            # Türkçe çeviriler
    └── en.json            # İngilizce çeviriler
```

## 🗃️ Veritabanı

Bot SQLite veritabanı kullanır ve şu tabloları içerir:
- **guild_settings** - Sunucu ayarları
- **warnings** - Kullanıcı uyarıları
- **temp_bans** - Geçici yasaklar
- **muted_users** - Susturulan kullanıcılar
- **mod_logs** - Moderasyon günlükleri
- **automod_settings** - Otomatik moderasyon ayarları
- **blacklisted_words** - Yasaklı kelimeler

## 🌍 Çoklu Dil Desteği

Bot şu anda 2 dili destekler:
- 🇹🇷 **Türkçe** (Varsayılan)
- 🇬🇧 **İngilizce**

Dil değiştirmek için: `!setlanguage en` veya `!setlanguage tr`

## 🔒 Güvenlik

- **Hiyerarşi kontrolü**: Bot kendinden yüksek rollere sahip kullanıcılara işlem yapamaz
- **İzin kontrolü**: Her komut için gerekli Discord izinleri kontrol edilir
- **Rate limiting**: Komutlar kullanım sınırına sahiptir
- **Audit logging**: Tüm moderasyon işlemleri kaydedilir

## 🆘 Destek

Sorunlarınız için:
1. `!help` komutu ile yardım alın
2. Bot log kanalını kontrol edin
3. GitHub Issues bölümünden yardım isteyin

## 📝 Lisans

Bu proje MIT lisansı altındadır.

---

**Not**: Bot token'ınızı asla paylaşmayın ve güvenli bir şekilde saklayın!