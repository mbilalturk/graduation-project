# 🎬 Demo Videosu — Konuşma Metni

**Proje:** Toplu Taşımada Otobüs Varış Süresi Tahmini
**Yazarlar:** Muhammed Bilal Türk · Ömer Faruk Koç
**Tahmini süre:** ~3.5–4 dakika
**Ekran:** `demo/index.html` tarayıcıda açık (tam ekran önerilir)

> **Not:** İki kişi olduğunuz için bölümleri aranızda paylaşabilirsiniz (örn. bir kişi 1–3, diğeri 4–6). Aşağıdaki **[EKRAN]** ipuçları neyi göstereceğinizi, **Konuşma:** ne söyleyeceğinizi belirtir.

---

## 1. Açılış (~25 sn)
**[EKRAN] Sayfanın en üstü — başlık ve isimler görünür.**

**Konuşma:**
> Merhaba. Ben Muhammed Bilal Türk, bu da proje arkadaşım Ömer Faruk Koç. Bitirme projemiz, toplu taşımada **otobüs varış sürelerinin tahmini** üzerine. Danışmanımız Prof. Dr. Didem Gözüpek.
>
> Bir durakta herkesin sorduğu basit bir soru var: "Otobüsüm ne zaman gelecek?" Biz bu soruyu, İzmir ESHOT ağında gerçek veriyle ve makine öğrenmesiyle yanıtlamaya çalıştık.

---

## 2. Problem ve Veri (~30 sn)
**[EKRAN] "Veri Kümesi" kartlarını göster (81.575 segment, 73 gün, 48 otobüs).**

**Konuşma:**
> Tahmin etmeye çalıştığımız şey, otobüsün **bir duraktan bir sonraki durağa** geçiş süresi. Bunları topladığımızda tüm rota için varış tahmini elde ediliyor.
>
> Kendi verimizi topladık: İzmir'in açık API'sinden, 30 saniyede bir otobüs konumlarını, hava durumunu ve trafiği yaklaşık üç ay boyunca kaydettik. Hat 502 için bu, **81 binin üzerinde temiz segment** demek. Ortalama segment süresi sadece ~1.2 dakika — yani kısa ve oldukça değişken bir hedef.

---

## 3. Model Karşılaştırması (~40 sn)
**[EKRAN] "Model Karşılaştırması" bölümüne kaydır — bar grafiği.**

**Konuşma:**
> Naif tarife tahmininden derin öğrenmeye kadar birçok model eğittik ve hepsini **aynı test kümesinde** karşılaştırdık.
>
> Sonuç: en iyi modellerimiz yaklaşık **0.43 dakika**, yani **26 saniye** ortalama hatayla tahmin yapıyor — tarifeye dayalı baz çizgisinin çok altında.
>
> İlginç olan şu: yaptığımız istatistiksel testler, klasik **XGBoost ile derin LSTM'in eşdeğer** olduğunu gösterdi — derin model, klasik modeli geçemiyor. İkisi de Random Forest'tan daha iyi. Yani en pratik model aslında basit olan: XGBoost.

---

## 4. Canlı Tahmin Denemesi (~40 sn)
**[EKRAN] "Canlı Tahmin Denemesi" — bir segment seç, zaman dilimi butonlarına bas.**

**Konuşma:**
> Burada sistemi canlı deneyebiliriz. Bir durak segmenti seçiyorum...
>
> *(Bir segment seç, örneğin orta sıralardan biri.)*
>
> ...ve zaman dilimini değiştiriyorum. Görüyorsunuz, **sabah zirvesinde** tahmini süre artıyor, **gece** azalıyor. Model ayrıca GTFS tarife süresini de gösteriyor; ikisi arasındaki fark, otobüsün tarifeden ne kadar saptığını veriyor. Bu sapma, modelimizin en güçlü girdilerinden biri.

---

## 5. Koşul Analizi ve Genelleme (~35 sn)
**[EKRAN] "Koşul Bazlı Analiz" dört kutusu, sonra "Genelleme (3 Hat)" tablosu.**

**Konuşma:**
> Hatayı koşullara göre incelediğimizde anlamlı örüntüler çıkıyor: **sabah zirvesi** en zor zaman dilimi, **yağışlı havada** hata belirgin şekilde artıyor, ve **hattın başında** — yani geçmiş bilgi henüz yokken — tahmin doğal olarak zorlaşıyor.
>
> En önemlisi, yöntemimiz tek hatta özel değil: **268 ve 565 hatlarında da** değiştirmeden, tutarlı sonuçlar verdi. Yani genelleniyor.

---

## 6. Makale Kıyası, Bulgular ve Kapanış (~50 sn)
**[EKRAN] "Referans Makale" ve "Metodolojik Bulgular" bölümleri.**

**Konuşma:**
> Referans aldığımız makale 2.97 dakika hata bildiriyordu; biz segment ölçeğinde çok daha düşük bir hataya ulaştık. Ama burada **dürüst olmak gerekiyor**: biz kısa segmentleri, makale tüm-rota varışlarını tahmin ediyor — ölçekler farklı, bu yüzden doğrudan "geçtik" demiyoruz.
>
> Aslında projemizin en değerli kısmı bu dürüstlük: Her geliştirmeyi kontrollü deneyle test ettik ve üç önemli bulguya ulaştık. Bir: ulaşılabilir doğruluk, **veri örnekleme aralığının** dayattığı bir tabana dayanıyor — daha karmaşık model değil, daha yoğun veri gerekiyor. İki: **daha sofistike, her zaman daha iyi değil** — basit model karmaşığı yakaladı. Üç: **adil karşılaştırma**, "derin öğrenme en iyi" izlenimini düzeltti.
>
> Özetle: tekrarlanabilir, dürüstçe değerlendirilmiş, ve genellenen bir otobüs varış süresi tahmin sistemi geliştirdik. Teşekkür ederiz.

---

## 🎥 Çekim İpuçları
- **Tarayıcıyı tam ekran** yap (F11); sayfayı yavaşça kaydır, konuştuğun bölüm ekranda olsun.
- Konuşurken **canlı tahmin** kısmında 1–2 etkileşim yap (segment + zaman dilimi değiştir) — "çalışan sistem" hissi verir.
- Türkçe karakter ve sayıların doğru göründüğünü çekimden önce bir kez kontrol et.
- `demo/index.html` internet **gerektirmez** (tüm veri gömülü) — çevrimdışı da çalışır.
- Süreyi tutmak için: bölüm 4'ü (canlı tahmin) kısa tutarsan toplam ~3 dk'da biter.
