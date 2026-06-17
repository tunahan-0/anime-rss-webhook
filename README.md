# animecix-webhook
Animecix.tv sitesinden yeni bölümleri takip eden ve Discord'a webhook ile bildirim gönderen Python botu.

## Özellikler
- SQLite veritabanı ile bölüm takibi.
- Discord Webhook entegrasyonu ile yeni bölüm bildirimi gönderimi.
- GitHub Actions ile düzenli aralıklarla otomatik çalışma.

## Kurulum
1. Repoyu klonlayın: `git clone ...`
2. Gereksinimleri yükleyin: `pip install -r requirements.txt`
3. `.env` dosyasını oluşturun ve şunları ekleyin:
   - `WEBHOOK_URL=...`
   - `ROL_ID=...`