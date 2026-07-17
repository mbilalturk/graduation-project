**SCI Makale Çalışması için Yapılabilecekler (İzmir)**

İzmir için yaptığımız çalışmalar SCI makalesi olma yolunda gidiyor, ancak tam olarak research question kafamda bir türlü oturmuyor.

Burada modeller üzerine eğilmeyeceğimiz net,  oyüzden: “Otobüs seyahat süresi tahminindeki temel problem model seçimi değil, yolculuk bağlamının doğru oluşturulmasıdır.” gibi bir kurguya yakın çalışmamız gerekecek diye düşünüyorum. Bu konuya sizde kafa yorabilirsiniz, buna göre yapacaklarımız da değişecek çünkü.

Burada parlatacağımız katkılar aşağıdakiler olacak:

- scheduled travel time, cumulative deviation ve dwell üçlüsüyle birlikte tanımlanan feature engineering framework  
- Cold-start'ın sistematik analizi (İlk duraklarda neden hata iki katına çıkıyor?, schedule ile neden azalıyor? vb.)  
- Cause-effect analysis (sadece sonuç vermektense, her sonucun nedenini açıklanarak çıkarımlarda bulunuluyor)  

**1\) Feature Contribution Analysis** 

En son ilettiğiniz raporda GTFS, Deviation, Dwell önemli diyoruz.

Ama bunun kanıtı yok, makalede bunu mutlaka kanıtlamamız lazım. Bunun için çeşitli ablation study’ler kurgulamak lazım. Önce bir base sonuç alıp sonra tek tek bunlar eklenip, sonuçları kıyaslamak lazım gibi.

**2\) Error by Trip Progress** 

Cold-start analiziniz güzel, bence çok anlamlı bir çıktı ama burada sadece sayı görmek istemeyiz. Bunu grafikleştirmek ve ön plana çıkarmak gerekir.

**3\) Effect Size**

İstatistiksel test yaptınız ama sadece p-value yeterli olmaz bence. Genelde  Cohen's d veya Cliff's Delta gibi şeyler ekleniyor.

# **4\) Confidence Interval**

Sadece MAE ve RMSE için tek sayı vermektense, güven aralığı da eklenebilir bence.

**5\) Cross Validation**

Şu an 80/20 split var. Burada en az 5 fold-CV çalıştırmayı görmek ister hakemler.

Ayrıca 80/20 split yerine bence bu problemde anlamlı olan Time-based split

Örneğin İlk 50 gün-train; Son 15 gün-test

# **8\) Error by Time of Day**

Bence bu yine güzel bir çıkarım ama bunu  time\_of\_day’e göre yapmışsınız da biraz daha zenginleştirip,sabah, öğlen, akşam performanslarını da görsek harika olur.

**9\) Error analysis** 

Şu an MAE ölçüyoruz. Ama hangi örneklerde hata oluştuğunun daha detay analizleri gerekiyor mutlaka yani örneğin;

* kısa segment/ uzun segment hata farkları  
* pik saat hata durumu  
* gece/gündüz farkı  
* yağmur etkisi  
* hafta sonu etkisi vb.

