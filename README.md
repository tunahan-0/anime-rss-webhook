# animecix-webhook
Animecix.tv sitesinden yeni bölümleri takip eden ve Discord'a webhook ile bildirim gönderen Python botu. Veritabanı olarak Turso (libSQL) kullanır.

## Özellikler
- Veritabanı ile bölüm takibi, önceden bildirimi yapılmış bölümleri tekrar bildirmenin önüne geçer.
- Discord üzerinden oluşturulmuş bir rolü etiketleyerek hedef kanalda yeni bölüm bildirimi gönderimi.

## Kurulum
1. Repoyu klonlayın: `git clone ...`
2. Gereksinimleri yükleyin: `pip install -r requirements.txt`
3. `.env` dosyasını oluşturun ve şunları ekleyin:
   - `WEBHOOK_URL = <discord-webhook-url>`
   - `ROL_ID = <discord-rol-id>`
   - `TURSO_DATABASE_URL = https://<veritabani-url>`
   - `TURSO_TOKEN = <tokeniniz>`
4. Turso Veritabanı Hazırlığı:
   - Turso Websitesi üzerinden yeni bir grup oluşturun. 
   - Oluşturduğunuz grup içerisinde bir veritabanı oluşturun.
   - Sol menüden grubunuzun üzerine tıklayın ve ekrana gelen yeni oluşturduğunuz veritabanına tıklayın.
   - Önünüze gelecek olan "Overview" sekmesi altında "Connect" kısmına gelin ve Database URL kısmında yazan adresi kopyalayın. Eğer aldığınız URL `libsql://...` şeklinde başlıyorsa bunu `https://...` şeklinde değiştirin. 
   -  "Connect" kısmındaki "Create Token" butonuna basın, önünüze gelen ekranda Token geçerlilik süresini kendi ihtiyaç duyduğunuz şekilde ayarlayın ve "Authorization Level" kısmını "Read & Write" olarak seçerek "Create Token" butonuna basın.
   - Önünüze gelen Token'ı kopyalayın, Token ile birlikte aldığınız URL'yi 3. maddede belirtildiği gibi `.env` dosyanız içerisine doğru yere yapıştırın.

## Github Actions ile Otomatikleştirme
Bu bot, `main` dalına push edildiğinde veya `.github/workflows/` içerisindeki zamanlayıcı ayarına göre otomatik tetiklenir. GitHub repository ayarlarından **Secrets and variables > Actions** kısmına yukarıdaki `.env` değişkenlerini eklemeyi unutmayın.

## NOT
Eğer Github Actions kullanmak yerine VPS veya bir cihazda 7/24 açık bırakmak istiyorsanız, Repoyu forklayıp SQLite veritabanında döngüde çalışacak şekilde veya dilediğiniz başka şekillerde düzenleyebilirsiniz.