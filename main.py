import pandas as pd
import os
from pyvis.network import Network

# Dosya yolu ayarları
current_dir = os.path.dirname(os.path.abspath(__file__))
data_path = os.path.join(current_dir, 'data', 'C:\\Users\\sezer\\OneDrive\\Desktop\\prolab3\\data\\PROLAB 3 - GÜNCEL DATASET.xlsx')

# Yazar sınıfı
class Yazar:
    def __init__(self, orcid):
        self.orcid = orcid
        self.makaleler = []

    def __str__(self):
        return f"Yazar: {self.orcid}, Makaleler: {', '.join(self.makaleler)}"

# Makale sınıfı
class Makale:
    def __init__(self, baslik, yazarlar):
        self.baslik = baslik
        self.yazarlar = yazarlar    

    def __str__(self):
        return f"Makale: {self.baslik}, Yazarlar: {', '.join([yazar.orcid for yazar in self.yazarlar])}"

# Graf sınıfı
class Graf:
    def __init__(self):
        self.dugumler = {}
        self.kenarlar = {}

    def dugum_ekle(self, yazar):
        if yazar.orcid not in self.dugumler:
            self.dugumler[yazar.orcid] = yazar

    def kenar_ekle(self, yazar1, yazar2, agirlik=1):
        if yazar1.orcid not in self.kenarlar:
            self.kenarlar[yazar1.orcid] = []
        if yazar2.orcid not in self.kenarlar:
            self.kenarlar[yazar2.orcid] = []

        self.kenarlar[yazar1.orcid].append((yazar2.orcid, agirlik))
        self.kenarlar[yazar2.orcid].append((yazar1.orcid, agirlik))

    def en_kisa_yol(self, baslangic_orcid, hedef_orcid):
        # Dijkstra benzeri algoritma ile en kısa yol bulma
        mesafeler = {dugum_orcid: float('inf') for dugum_orcid in self.dugumler}
        onceki_dugum = {dugum_orcid: None for dugum_orcid in self.dugumler}
        mesafeler[baslangic_orcid] = 0

        ziyaret_edilenler = set()
        kuyruk = [(0, baslangic_orcid)]  # (mesafe, dugum_orcid)

        while kuyruk:
            kuyruk.sort(reverse=True)  # Kuyruk mesafeye göre sıralanır
            mevcut_mesafe, mevcut_dugum = kuyruk.pop()

            if mevcut_dugum in ziyaret_edilenler:
                continue

            ziyaret_edilenler.add(mevcut_dugum)

            if mevcut_dugum == hedef_orcid:
                break

            for komsu, agirlik in self.kenarlar.get(mevcut_dugum, []):
                if komsu in ziyaret_edilenler:
                    continue

                yeni_mesafe = mevcut_mesafe + agirlik
                if yeni_mesafe < mesafeler[komsu]:
                    mesafeler[komsu] = yeni_mesafe
                    onceki_dugum[komsu] = mevcut_dugum
                    kuyruk.append((yeni_mesafe, komsu))
        
        # En kısa yolun oluşturulması
        yol = []
        mevcut = hedef_orcid
        while mevcut is not None:
            yol.insert(0, mevcut)
            mevcut = onceki_dugum[mevcut]

        if mesafeler[hedef_orcid] == float('inf'):
            return None, []

        return mesafeler[hedef_orcid], yol


# Veri setini okuma
try:
    df = pd.read_excel(data_path) 
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
required_columns = {'paper_title', 'orcid', 'coauthors'}
if not required_columns.issubset(df.columns):
    print(f"Gerekli sütunlar eksik: {required_columns - set(df.columns)}")
    exit()

# Boş verileri temizle
df.dropna(subset=['paper_title', 'orcid', 'coauthors'], inplace=True)

# Graf nesnesi oluştur
graf = Graf()

# DataFrame'deki her satırı işle
for _, row in df.iterrows():
    makale_baslik = row['paper_title']
    orcid = row['orcid'].strip()
    try:
        coauthors = [coauthor.strip() for coauthor in row['coauthors'].strip('[]').replace("'", "").split(',')]
    except AttributeError:
        print(f"Coauthors sütununda çözümleme hatası: {row['coauthors']}")
        continue

    # Yazar nesnesini oluştur ve grafa düğüm olarak ekle
    if orcid not in graf.dugumler:
        yazar_nesne = Yazar(orcid)
        graf.dugum_ekle(yazar_nesne)

    # Eş-yazarları işleme al
    makale_yazarlari = [graf.dugumler[orcid]]
    for coauthor_orcid in coauthors:
        if coauthor_orcid not in graf.dugumler:
            coauthor_nesne = Yazar(coauthor_orcid)
            graf.dugum_ekle(coauthor_nesne)
        makale_yazarlari.append(graf.dugumler[coauthor_orcid])

    # Yazarların makalelere eklenmesi
    for yazar in makale_yazarlari:
        yazar.makaleler.append(makale_baslik)

    # Yazarlar arasındaki ilişkileri (kenarları) ekle
    for i in range(len(makale_yazarlari)):
        for j in range(i + 1, len(makale_yazarlari)):
            graf.kenar_ekle(makale_yazarlari[i], makale_yazarlari[j])

# Kullanıcıdan giriş alma
print("Lütfen A ve B yazarlarının ORCID'lerini giriniz:")
a_orcid = input("A yazarının ORCID'i: ")
b_orcid = input("B yazarının ORCID'i: ")

if a_orcid not in graf.dugumler or b_orcid not in graf.dugumler:
    print("Girilen ORCID'lerden biri graf içerisinde bulunamadı.")
else:
    mesafe, yol = graf.en_kisa_yol(a_orcid, b_orcid)
    if yol:
        print(f"En kısa yol ({mesafe} ağırlık): {' -> '.join(yol)}")
    else:
        print("A ve B arasında bağlantı bulunamadı.")

# Pyvis ile grafi görselleştir
net = Network(height='750px', width='100%', notebook=True, directed=False)

# Yazarların makale sayıları
yazar_makale_sayilari = {yazar.orcid: len(yazar.makaleler) for yazar in graf.dugumler.values()}
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

    net.add_node(
        dugum.orcid,
        label=dugum.orcid,
        title=f"ORCID: {dugum.orcid}\nMakaleler: {', '.join(dugum.makaleler)}",
        size=size,
        color=color
    )

# Kenarları ekle
for yazar1_orcid, komsular in graf.kenarlar.items():
    for yazar2_orcid, agirlik in komsular:
        # Kenar ağırlığı, ortak makale sayısı kadar olacak şekilde belirleniyor
        ortak_makale_sayisi = len(set(graf.dugumler[yazar1_orcid].makaleler).intersection(graf.dugumler[yazar2_orcid].makaleler))
        net.add_edge(
            yazar1_orcid,
            yazar2_orcid,
            weight=ortak_makale_sayisi,
            title=f"Ortak Makale Sayısı: {ortak_makale_sayisi}"
        )

# Grafı kaydet ve göster
output_path = os.path.join(current_dir, 'yazarlar_graf.html')
net.show(output_path)
print(f"Graf başarıyla '{output_path}' olarak kaydedildi ve açıldı.")


