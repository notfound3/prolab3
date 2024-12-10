import pandas as pd
import os
import matplotlib.pyplot as plt

# Dosya yolu ayarları
current_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(current_dir, 'C:\\Users\\sezer\\OneDrive\\Desktop\\prolab3\\data\\PROLAB 3 - DATASET.xlsx')
output_path = os.path.join(current_dir, 'C:\\Users\\sezer\\OneDrive\\Desktop\\prolab3\\output\\output.csv')

# Yazar ve makale nesnelerini tanımlamak için sınıflar
class Yazar:
    def __init__(self, isim, orcid):
        self.isim = isim
        self.orcid = orcid
        self.makaleler = []

    def makale_ekle(self, makale):
        self.makaleler.append(makale)

    def __str__(self):
        return f"Yazar: {self.isim}, ORCID: {self.orcid}, Makaleler: {[makale.baslik for makale in self.makaleler]}"

class Makale:
    def __init__(self, baslik, doi, yazarlar):
        self.baslik = baslik
        self.doi = doi
        self.yazarlar = yazarlar

    def __str__(self):
        return f"Makale: {self.baslik}, DOI: {self.doi}, Yazarlar: {', '.join([yazar.isim for yazar in self.yazarlar])}"

# Veri setini okuma
try:
    df = pd.read_excel(data_path)
    print(f"'{data_path}' başarıyla okundu.")
except FileNotFoundError:
    print(f"'{data_path}' dosyası bulunamadı.")
    exit()

# Sütun adlarındaki boşlukları kaldırmak
df.columns = df.columns.str.strip()

# Yazar ve makale nesneleri için sözlükler
yazar_dict = {}
makale_list = []

# DataFrame'deki her satırı işle
for _, row in df.iterrows():
    makale_baslik = row['paper_title']
    doi = row['doi']
    orcid = row['orcid']
    author_name = row['author_name']
    coauthors = eval(row['coauthors'])  # Coauthors listesini çözümleme

    # Yazarlar listesini oluştur (author_name ve coauthors'ları birleştir)
    yazarlar = [author_name] + coauthors

    # Makale için yazar nesnelerini oluştur veya al
    makale_yazarlari = []
    for yazar_adi in yazarlar:
        if yazar_adi not in yazar_dict:
            yazar_dict[yazar_adi] = Yazar(yazar_adi, orcid)
        makale_yazarlari.append(yazar_dict[yazar_adi])

    # Makale nesnesi oluştur ve yazarlarla ilişkilendir
    makale = Makale(makale_baslik, doi, makale_yazarlari)
    makale_list.append(makale)
    for yazar in makale_yazarlari:
        yazar.makale_ekle(makale)

# Analiz sonuçlarını CSV'ye yazma
output_data = []
for yazar in yazar_dict.values():
    makale_basliklar = []
    for makale in yazar.makaleler:
        # Makale float tipindeyse boş string al
        if isinstance(makale.baslik, float):
            makale_basliklar.append("")
        else:
            makale_basliklar.append(makale.baslik)

    output_data.append({
        "Yazar": yazar.isim,
        "ORCID": yazar.orcid,
        "Makaleler": "; ".join(makale_basliklar)
    })

output_df = pd.DataFrame(output_data)
output_df.to_csv(output_path, index=False)
print(f"Analiz sonuçları '{output_path}' dosyasına kaydedildi.")

# Yazarlar arası ilişki grafiği oluşturma
# Düğümler ve kenarlar için boş listeler
dugumler = {}  # Yazarlar ve ID'leri (düğümler)
kenarlar = []  # Yazarlar arasındaki ilişkiler (kenarlar)

# DataFrame'deki her satırda bulunan yazarlara ilişkin ilişkiler ekle
for _, row in df.iterrows():
    makale_baslik = row['paper_title']
    author_name = row['author_name']
    coauthors = eval(row['coauthors'])  # Coauthors listesini çözümleme

    # Yazarlar listesini oluştur (author_name ve coauthors'ları birleştir)
    yazarlar = [author_name] + coauthors

    # Aynı makalede bulunan yazarlara kenar ekle
    for i in range(len(yazarlar)):
        for j in range(i + 1, len(yazarlar)):
            yazar1 = yazarlar[i]
            yazar2 = yazarlar[j]

            # Düğümleri (yazarları) ekle (ID'leri kontrol ederek)
            if yazar1 not in dugumler:
                dugumler[yazar1] = len(dugumler)
            if yazar2 not in dugumler:
                dugumler[yazar2] = len(dugumler)

            # Yazarlar arasında kenar (ilişki) ekle
            kenarlar.append((dugumler[yazar1], dugumler[yazar2]))

# Grafiği görselleştirme için gerekli veriyi hazırlama
plt.figure(figsize=(12, 12))

# Düğümlerin koordinatlarını manuel olarak ayarla
positions = {dugumler[yazar]: (i % 10, i // 10) for i, yazar in enumerate(dugumler)}

# Yazarlar arasındaki kenarları çiz
for kenar in kenarlar:
    plt.plot([positions[kenar[0]][0], positions[kenar[1]][0]], 
             [positions[kenar[0]][1], positions[kenar[1]][1]], 'bo-', alpha=0.5)

# Düğümleri (yazarları) yerleştir
for dugum, (x, y) in positions.items():
    plt.text(x, y, dugum, fontsize=12, ha='right')

plt.title("Yazarlar Arası İlişkiler Grafiği (Manuel Modelleme)")
plt.axis('off')  # Eksenleri kapat
plt.show()
