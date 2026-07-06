# 🤖 GitHub Repository Analyzer AI

Yapay zeka destekli bu proje, verilen bir **GitHub repository bağlantısını** analiz ederek yazılım projesinin kod kalitesini değerlendiren ve geliştiriciye mühendislik odaklı öneriler sunan bir sistemdir.

Bu proje, **Niğde Ömer Halisdemir Üniversitesi Bilgisayar Mühendisliği Bölümü - Yapay Zeka Dersi** kapsamında geliştirilmiştir.

---

# 📌 Proje Amacı

Açık kaynak projelerin kod kalitesini otomatik olarak analiz ederek;

- Yazılım mühendisliği kalitesini değerlendirmek,
- Spagetti kod yapılarının tespit edilmesini sağlamak,
- README ve dokümantasyon eksiklerini belirlemek,
- Kodun sürdürülebilirliği hakkında öneriler sunmak,
- Projeye 0-100 arasında bir **Mühendislik Skor Endeksi** vermek amaçlanmıştır.

---

# 🚀 Özellikler

- GitHub Repository URL analizi
- Çok dilli kaynak kod desteği
- Kod segmentlerine ayırma
- TF-IDF tabanlı özellik çıkarımı
- Eğitilmiş makine öğrenmesi modeli ile tahmin
- Mühendislik kalite puanı (0-100)
- Kod kalitesi önerileri
- README kontrolü
- Spagetti kod tespiti
- Canlı analiz

---

# 🧠 Kullanılan Yapay Zeka Modelleri

Projede toplam **6 farklı makine öğrenmesi algoritması** karşılaştırılmıştır.

| Model | Durum |
|--------|--------|
| TF-IDF + Linear SVM (Calibrated) | 🥇 En başarılı |
| TF-IDF + HistGradient Boosting | 🥈 |
| TF-IDF + Logistic Regression | 🥉 |
| TF-IDF + SGD Classifier | ✔ |
| TF-IDF + Naive Bayes | ✔ |
| TF-IDF + Random Forest | ✔ |

---

# 📊 Model Performansları

| Model | Accuracy | Precision | Recall | F1 Score |
|--------|-----------|-----------|---------|----------|
| Linear SVM | **85.46%** | 83.88% | 80.85% | **82.20%** |
| HistGradient Boosting | 84.42% | 83.85% | 79.50% | 81.35% |
| Logistic Regression | 83.39% | 78.05% | 84.05% | 80.12% |
| SGD Classifier | 82.47% | 77.94% | 81.31% | 79.37% |
| Naive Bayes | 79.68% | 78.94% | 72.20% | 74.16% |
| Random Forest | 70.11% | 67.40% | 74.56% | 66.44% |

En başarılı model **Linear SVM (Calibrated)** olarak belirlenmiştir.

---

# 📂 Veri Seti

Veri seti üç farklı kalite sınıfından oluşmaktadır.

| Sınıf | Açıklama |
|-------|----------|
| 2 | Başarılı / Temiz Kod |
| 1 | Orta Kalite |
| 0 | Geliştirilmesi Gereken Kod |

Yaklaşık dağılım:

- 31.000 Temiz Kod
- 20.000 Orta Seviye Kod
- 6.000 Zayıf Kod

Toplam yaklaşık **57.000 kod örneği** kullanılmıştır.

---

# ⚙️ Kullanılan Teknolojiler

- Python
- Scikit-Learn
- Pandas
- NumPy
- Joblib
- Requests
- GitHub API
- TF-IDF
- Machine Learning

---

# 🛠️ Çalışma Mantığı

1. Kullanıcı GitHub Repository bağlantısını girer.
2. Repository içerisindeki dosyalar indirilir.
3. Kaynak kodlar analiz edilir.
4. Kod blokları segmentlere ayrılır.
5. TF-IDF ile vektörleştirme yapılır.
6. Eğitilmiş model tahmin üretir.
7. Tahminler birleştirilerek Mühendislik Skoru hesaplanır.
8. Sistem kalite önerileri oluşturur.

---

# 📈 Üretilen Çıktılar

Sistem;

- Kod kalite puanı
- Güçlü yönler
- Zayıf yönler
- README analizi
- Dokümantasyon kontrolü
- Spagetti kod uyarıları
- Refactoring önerileri
- Yazılım mühendisliği tavsiyeleri

üretmektedir.

---

# 📚 Akademik Amaç

Bu proje;

- Doğal Dil İşleme (NLP)
- Makine Öğrenmesi
- Yazılım Kalitesi Analizi
- Kod Sınıflandırma
- Yazılım Mühendisliği

alanlarını bir araya getiren akademik bir çalışmadır.

---

# 👨‍💻 Geliştirici

**Yavuz Berke Pektaş**

---

# 📄 Lisans

Bu proje eğitim ve akademik çalışmalar kapsamında geliştirilmiştir.
