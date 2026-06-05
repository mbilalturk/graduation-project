# ESHOT Collector — Sunucu Yönetim Rehberi

> **Sunucu IP:** `167.172.163.29`  
> **Bağlantı komutu (kendi bilgisayarından):**
> ```powershell
> ssh root@167.172.163.29
> ```

---

## 1. Servisi Yönetme

| Amaç | Komut |
|---|---|
| Servis durumunu gör | `systemctl status eshot-collector` |
| Servisi başlat | `systemctl start eshot-collector` |
| Servisi durdur | `systemctl stop eshot-collector` |
| Servisi yeniden başlat | `systemctl restart eshot-collector` |

> `systemctl status` ekranından çıkmak için `q` tuşuna bas.

---

## 2. Logları İzleme

| Amaç | Komut |
|---|---|
| Canlı log izle (Ctrl+C ile çık) | `journalctl -u eshot-collector -f` |
| Son 100 satır logu gör | `journalctl -u eshot-collector -n 100` |
| Son 50 satır logu gör | `journalctl -u eshot-collector -n 50` |
| Bugünkü logları gör | `journalctl -u eshot-collector --since today` |

---

## 3. Veritabanı İşlemleri

| Amaç | Komut |
|---|---|
| DB dosyasının boyutunu gör | `du -sh ~/eshot-collector/collected_data/` |
| SQLite'a bağlan | `sqlite3 ~/eshot-collector/collected_data/eshot_buses.db` |
| DB dosyasını sil | `rm ~/eshot-collector/collected_data/eshot_buses.db` |

### SQLite içinde kullanılabilecek sorgular

SQLite'a bağlandıktan sonra (`sqlite3 ...` komutuyla) şunları yazabilirsin:

```sql
-- Kaç satır veri birikmiş
SELECT COUNT(*) FROM bus_positions;

-- Son 10 konum kaydı
SELECT * FROM bus_positions ORDER BY id DESC LIMIT 10;

-- Hangi hatlardan kaç kayıt var
SELECT route_id, COUNT(*) FROM bus_positions GROUP BY route_id;

-- SQLite'dan çık
.quit
```

---

## 4. Dosya İşlemleri

### Sunucudaki bir dosyayı düzenle

```bash
nano ~/eshot-collector/collector.py
```

> `nano` içinde: kaydetmek için `Ctrl+X` → `Y` → `Enter`

### Kendi bilgisayarından sunucuya dosya gönder (PowerShell)

```powershell
scp C:\yerel\dosya\yolu root@167.172.163.29:~/eshot-collector/
```

### Sunucudan kendi bilgisayarına dosya indir (PowerShell)

```powershell
scp root@167.172.163.29:~/eshot-collector/collected_data/route_502_realtime.db C:\Users\Bilal\Desktop\
```

### Klasör yükle (PowerShell)

```powershell
scp -r C:\yerel\klasor\yolu root@167.172.163.29:~/hedef/klasor/
```

---

## 5. Sunucu Genel Durumu

| Amaç | Komut |
|---|---|
| RAM ve CPU kullanımını gör | `htop` |
| Disk kullanımını gör | `df -h` |
| Proje klasörü boyutunu gör | `du -sh ~/eshot-collector/` |
| Çalışan tüm servisleri listele | `systemctl list-units --type=service --state=running` |

> `htop` ekranından çıkmak için `q` tuşuna bas.  
> `htop` kurulu değilse: `apt install htop -y`

---

## 6. Sunucu Yeniden Başlatma

```bash
reboot
```

> Sunucu yeniden başladıktan sonra `eshot-collector` servisi **otomatik olarak başlar** (`systemctl enable` ile ayarlandı).

---

## 7. Değişiklik Yapma Akışı

Herhangi bir `.py` dosyasını güncellemek istersen:

```bash
# 1. Servisi durdur
systemctl stop eshot-collector

# 2. Dosyayı düzenle
nano ~/eshot-collector/collector.py

# 3. Servisi tekrar başlat
systemctl start eshot-collector

# 4. Çalışıyor mu kontrol et
systemctl status eshot-collector
```

---

## 8. Sık Karşılaşılan Durumlar

**Servis çalışmıyor, ne yapmalıyım?**
```bash
journalctl -u eshot-collector -n 50
```
Son logları incele, hata mesajını bul.

**DB dosyası çok büyüdü, sıfırlamak istiyorum:**
```bash
systemctl stop eshot-collector
rm ~/eshot-collector/collected_data/eshot_buses.db
systemctl start eshot-collector
```

**Sunucuya bağlanamıyorum:**
DigitalOcean panelinden (`cloud.digitalocean.com`) droplet'i kontrol et. Kapalıysa "Power On" butonuna bas.
