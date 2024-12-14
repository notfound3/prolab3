import pandas as pd
import os
from pyvis.network import Network

# Dosya yolu ayarları
current_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(current_dir, 'data', 'C:\\Users\\sezer\\OneDrive\\Desktop\\prolab3\\data\\PROLAB 3 - DATASET.xlsx')

# Yazar ve graf yapısını tanımlamak için sınıflar
class Yazar:
    def __init__(self, isim):
        self.isim = isim
        self.makaleler = []

    def __str__(self):
        return f"Yazar: {self.isim}, Makaleler: {[makale for makale in self.makaleler]}"

class Makale:
    def __init__(self, baslik, yazarlar):
        self.baslik = baslik
        self.yazarlar = yazarlar

    def __str__(self):
        return f"Makale: {self.baslik}, Yazarlar: {', '.join([yazar.isim for yazar in self.yazarlar])}"

class Graf:
    def __init__(self):
        self.dugumler = {}
        self.kenarlar = []

    def dugum_ekle(self, yazar):
        if yazar.isim not in self.dugumler:
            self.dugumler[yazar.isim] = yazar

    def kenar_ekle(self, yazar1, yazar2):
        if (yazar1.isim, yazar2.isim) not in self.kenarlar and (yazar2.isim, yazar1.isim) not in self.kenarlar:
            self.kenarlar.append((yazar1.isim, yazar2.isim))

    def __str__(self):
        return f"Düğümler: {list(self.dugumler.keys())}, Kenarlar: {self.kenarlar}"

# Veri setini okuma
try:
    df = pd.read_excel(data_path)  # Veri setini oku
    print(f"'{data_path}' başarıyla okundu.")
except FileNotFoundError:
    print(f"'{data_path}' dosyası bulunamadı.")
    exit()
except Exception as e:
    print(f"Bir hata oluştu: {e}")
    exit()

# Sütun adlarındaki boşlukları kaldırmak
df.columns = df.columns.str.strip()

# Gerekli sütunların kontrolü
required_columns = {'Makale Adı', 'Yazarlar', 'DOI'}
if not required_columns.issubset(df.columns):
    print(f"Gerekli sütunlar eksik: {required_columns - set(df.columns)}")
    exit()

# Boş verileri temizle
df.dropna(subset=['Makale Adı', 'Yazarlar'], inplace=True)

# Graf nesnesi oluştur
graf = Graf()

# DataFrame'deki her satırı işle
for _, row in df.iterrows():
    makale_baslik = row['Makale Adı']
    try:
        yazarlar = [yazar.strip() for yazar in row['Yazarlar'].strip('[]').split(',')]
    except AttributeError:
        print(f"Yazarlar sütununda çözümleme hatası: {row['Yazarlar']}")
        continue

    # Yazar nesnelerini oluştur ve grafa düğüm olarak ekle
    makale_yazarlari = []
    for yazar_adi in yazarlar:
        if yazar_adi not in graf.dugumler:
            yazar_nesne = Yazar(yazar_adi)
            graf.dugum_ekle(yazar_nesne)
        makale_yazarlari.append(graf.dugumler[yazar_adi])

    # Makale nesnesini oluştur
    makale = Makale(makale_baslik, makale_yazarlari)

    # Yazarın makaleye eklenmesi
    for yazar in makale_yazarlari:
        yazar.makaleler.append(makale_baslik)

    # Yazarlar arasındaki ilişkileri (kenarları) ekle
    for i in range(len(makale_yazarlari)):
        for j in range(i + 1, len(makale_yazarlari)):
            graf.kenar_ekle(makale_yazarlari[i], makale_yazarlari[j])

# Pyvis ile grafi görselleştir
net = Network(height='750px', width='100%', notebook=True, directed=False)

# Yazarların makale sayıları
yazar_makale_sayilari = {yazar.isim: len(yazar.makaleler) for yazar in graf.dugumler.values()}
ortalama_makale_sayisi = sum(yazar_makale_sayilari.values()) / len(yazar_makale_sayilari)

# Düğümleri ekle
for dugum in graf.dugumler.values():
    makale_sayisi = len(dugum.makaleler)
    # Yazarın düğüm boyutunu ve rengini ayarla
    if makale_sayisi > 1.2 * ortalama_makale_sayisi:
        size = 20  # Daha büyük düğüm
        color = 'darkred'  # Koyu renk
    elif makale_sayisi < 0.8 * ortalama_makale_sayisi:
        size = 10  # Daha küçük düğüm
        color = 'lightblue'  # Açık renk
    else:
        size = 15  # Ortalama boyut
        color = 'orange'  # Orta renk
    
    net.add_node(dugum.isim, label=dugum.isim, title=f"{dugum.isim}\nMakaleler: {', '.join(dugum.makaleler)}", size=size, color=color)

# Kenarları ekle
for kenar in graf.kenarlar:
    # Kenar ağırlığı, ortak makale sayısı kadar olacak şekilde belirleniyor
    ortak_makale_sayisi = sum([1 for row in df.itertuples() if kenar[0] in row.Yazarlar and kenar[1] in row.Yazarlar])
    net.add_edge(kenar[0], kenar[1], weight=ortak_makale_sayisi)

# Grafı kaydet ve göster
output_path = os.path.join(current_dir, 'yazarlar_graf.html')
net.show(output_path)
print(f"Graf başarıyla '{output_path}' olarak kaydedildi ve açıldı.")
